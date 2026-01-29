// Vercel Serverless Function: POST /api/contact
// Sends an email via SMTP

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
    const { subject, message } = body;

    if (!subject || !message) {
      return res.status(400).json({ error: 'Subject and message are required' });
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

    // Send email
    await transporter.sendMail({
      from: SMTP_USER,
      to: REPORT_EMAIL,
      subject: `[Substack Radio] ${subject}`,
      text: message,
      html: `
        <div style="font-family: sans-serif; max-width: 600px;">
          <h2 style="color: #eab308;">Substack Radio Contact</h2>
          <hr style="border: 1px solid #333;" />
          <p><strong>Subject:</strong> ${subject}</p>
          <hr style="border: 1px solid #333;" />
          <div style="white-space: pre-wrap;">${message}</div>
          <hr style="border: 1px solid #333;" />
          <p style="color: #666; font-size: 12px;">
            Sent from Substack Radio contact form
          </p>
        </div>
      `,
    });

    return res.status(200).json({
      success: true,
      message: 'Message sent successfully',
    });
  } catch (error) {
    console.error('Error sending email:', error);
    return res.status(500).json({ error: 'Failed to send message' });
  }
}
