// Vercel Serverless Function: POST /api/submit
// Sends submission as email for manual review (instead of direct database write)

import nodemailer from 'nodemailer';

export default async function handler(req, res) {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, REPORT_EMAIL } = process.env;

  if (!SMTP_HOST || !SMTP_USER || !SMTP_PASS || !REPORT_EMAIL) {
    console.error('Missing SMTP configuration');
    return res.status(500).json({ error: 'Server configuration error' });
  }

  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
    const { type, data } = body;

    if (!type || !data) {
      return res.status(400).json({ error: 'Missing type or data' });
    }

    if (type !== 'article' && type !== 'newsletter') {
      return res.status(400).json({ error: 'Invalid type. Must be "article" or "newsletter"' });
    }

    let jsonData;
    let displayTitle;

    if (type === 'article') {
      // Validate required fields
      if (!data.title || !data.url || !data.station_main || !data.subcategory) {
        return res.status(400).json({ error: 'Missing required fields: title, url, station_main, subcategory' });
      }

      // Extract newsletter URL from post URL (e.g., https://foo.substack.com/p/bar -> https://foo.substack.com)
      let newsletterUrl = '';
      try {
        const urlObj = new URL(data.url);
        newsletterUrl = `${urlObj.protocol}//${urlObj.host}`;
      } catch (e) {
        // If URL parsing fails, leave empty
      }

      jsonData = {
        post_url: data.url,
        post_title: data.title,
        post_subtitle: data.description || '',
        thumbnail_url: data.image_url || '',
        newsletter_name: '',
        newsletter_url: newsletterUrl,
        author_name: data.author || '',
        author_profile_url: '',
        _station: data.station_main,
        _subcategory: data.subcategory
      };
      displayTitle = data.title;

    } else {
      // Newsletter
      if (!data.name || !data.url || !data.station_main) {
        return res.status(400).json({ error: 'Missing required fields: name, url, station_main' });
      }

      jsonData = {
        name: data.name,
        url: data.url,
        author_name: data.author || '',
        bio: data.bio || '',
        image_url: data.image_url || '',
        _station: data.station_main
      };
      displayTitle = data.name;
    }

    // Create transporter
    const transporter = nodemailer.createTransport({
      host: SMTP_HOST,
      port: parseInt(SMTP_PORT || '587'),
      secure: SMTP_PORT === '465',
      auth: {
        user: SMTP_USER,
        pass: SMTP_PASS,
      },
    });

    const timestamp = new Date().toISOString();
    const jsonString = JSON.stringify(jsonData, null, 2);

    // Build summary list
    let summaryHtml = `
      <li><strong>Type:</strong> ${type}</li>
      <li><strong>Title/Name:</strong> ${displayTitle}</li>
      <li><strong>URL:</strong> <a href="${data.url}">${data.url}</a></li>
      <li><strong>Station:</strong> ${data.station_main}</li>
    `;
    if (type === 'article') {
      summaryHtml += `<li><strong>Subcategory:</strong> ${data.subcategory}</li>`;
      if (data.author) summaryHtml += `<li><strong>Author:</strong> ${data.author}</li>`;
      if (data.description) summaryHtml += `<li><strong>Description:</strong> ${data.description}</li>`;
    } else {
      if (data.author) summaryHtml += `<li><strong>Author:</strong> ${data.author}</li>`;
      if (data.bio) summaryHtml += `<li><strong>Bio:</strong> ${data.bio}</li>`;
    }

    // Send email
    await transporter.sendMail({
      from: SMTP_USER,
      to: REPORT_EMAIL,
      subject: `[Substack Radio Submission] ${type.charAt(0).toUpperCase() + type.slice(1)}: ${displayTitle}`,
      text: `New ${type} submission:\n\n${jsonString}\n\nSubmitted at: ${timestamp}`,
      html: `
        <div style="font-family: monospace; max-width: 700px; background: #0a0a0f; color: #e0e0e0; padding: 20px; border-radius: 8px;">
          <h2 style="color: #eab308; margin-top: 0;">Substack Radio ${type.charAt(0).toUpperCase() + type.slice(1)} Submission</h2>
          <hr style="border: 1px solid #333;" />

          <h3 style="color: #888;">Summary</h3>
          <ul style="line-height: 1.8;">
            ${summaryHtml}
          </ul>

          <hr style="border: 1px solid #333;" />

          <h3 style="color: #888;">JSON (Copy/Paste Ready)</h3>
          <pre style="background: #1a1a2e; padding: 16px; border-radius: 8px; overflow-x: auto; color: #00ff00; white-space: pre-wrap; word-wrap: break-word;">${jsonString}</pre>

          <hr style="border: 1px solid #333;" />
          <p style="color: #666; font-size: 12px;">
            Submitted at: ${timestamp}
          </p>
        </div>
      `,
    });

    return res.status(201).json({
      success: true,
      message: 'Submission received! It will be reviewed and added soon.',
    });
  } catch (error) {
    console.error('Error submitting:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
