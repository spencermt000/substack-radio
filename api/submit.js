// Vercel Serverless Function: POST /api/submit
// Submits new articles or newsletters to Airtable

export default async function handler(req, res) {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { AIRTABLE_API_KEY, AIRTABLE_BASE_ID } = process.env;

  if (!AIRTABLE_API_KEY || !AIRTABLE_BASE_ID) {
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

    const table = type === 'article' ? 'Articles' : 'Newsletters';
    const today = new Date().toISOString().split('T')[0];

    let fields;

    if (type === 'article') {
      // Validate required fields
      if (!data.title || !data.url || !data.station_main || !data.subcategory) {
        return res.status(400).json({ error: 'Missing required fields: title, url, station_main, subcategory' });
      }

      fields = {
        title: data.title,
        author: data.author || '',
        url: data.url,
        station_main: data.station_main,
        subcategory: data.subcategory,
        description: data.description || '',
        image_url: data.image_url || '',
        submitted_date: today,
        approved: false, // Always starts unapproved
      };
    } else {
      // Newsletter
      if (!data.name || !data.url || !data.station_main) {
        return res.status(400).json({ error: 'Missing required fields: name, url, station_main' });
      }

      fields = {
        name: data.name,
        author: data.author || '',
        url: data.url,
        station_main: data.station_main,
        bio: data.bio || '',
        image_url: data.image_url || '',
        submitted_date: today,
        approved: false, // Always starts unapproved
      };
    }

    const url = `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${table}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${AIRTABLE_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ fields }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Airtable error:', errorText);
      return res.status(response.status).json({ error: 'Failed to submit' });
    }

    const result = await response.json();

    return res.status(201).json({
      success: true,
      id: result.id,
      message: 'Submission received! It will be reviewed and eligible in 24 hours.',
    });
  } catch (error) {
    console.error('Error submitting:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
