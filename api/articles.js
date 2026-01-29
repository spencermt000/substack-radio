// Vercel Serverless Function: GET /api/articles
// Fetches approved articles from Airtable

export default async function handler(req, res) {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { AIRTABLE_API_KEY, AIRTABLE_BASE_ID } = process.env;

  if (!AIRTABLE_API_KEY || !AIRTABLE_BASE_ID) {
    return res.status(500).json({ error: 'Server configuration error' });
  }

  try {
    const { station } = req.query;

    // Build filter formula
    let filterFormula = 'AND({approved} = TRUE())';

    if (station) {
      filterFormula = `AND({approved} = TRUE(), {station_main} = '${station}')`;
    }

    const params = new URLSearchParams({
      filterByFormula: filterFormula,
      sort: [{ field: 'submitted_date', direction: 'desc' }].map(s => JSON.stringify(s)).join(',')
    });

    // Airtable API has specific sort format
    const url = `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/Articles?filterByFormula=${encodeURIComponent(filterFormula)}`;

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${AIRTABLE_API_KEY}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Airtable error:', errorText);
      return res.status(response.status).json({ error: 'Failed to fetch articles' });
    }

    const data = await response.json();

    // Transform records to cleaner format
    const articles = data.records.map(record => ({
      id: record.id,
      title: record.fields.title || '',
      author: record.fields.author || '',
      url: record.fields.link || '',
      station_main: record.fields.station || record.fields.station_main || '',
      subcategory: record.fields.subcategory || '',
      station_code: record.fields.station_code || '',
      description: record.fields.description || '',
      image_url: record.fields.image_url || '',
      submitted_date: record.fields.submitted_date || '',
    }));

    return res.status(200).json({ articles });
  } catch (error) {
    console.error('Error fetching articles:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
