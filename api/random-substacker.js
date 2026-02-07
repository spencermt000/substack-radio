import chromium from '@sparticuz/chromium';
import playwright from 'playwright-core';

// Substack categories to browse randomly
const CATEGORIES = [
  'technology', 'business', 'finance', 'culture', 'politics',
  'food', 'health', 'sports', 'music', 'science',
  'philosophy', 'history', 'education', 'faith', 'art',
  'climate', 'literature', 'humor', 'travel', 'crypto',
  'fashion', 'parenting', 'gaming', 'design', 'media',
];

export default async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Pick a random category
  const category = CATEGORIES[Math.floor(Math.random() * CATEGORIES.length)];
  const browseUrl = `https://substack.com/browse/${category}`;

  let browser = null;
  try {
    browser = await playwright.chromium.launch({
      args: chromium.args,
      executablePath: await chromium.executablePath(),
      headless: true,
    });

    const context = await browser.newContext({
      userAgent:
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    });

    const page = await context.newPage();
    await page.goto(browseUrl, { waitUntil: 'networkidle', timeout: 15000 });

    // Wait for publication cards to appear
    await page.waitForSelector('a[href*="substack.com"]', { timeout: 8000 }).catch(() => null);
    await page.waitForTimeout(2000);

    // Extract publications from the browse page
    const publications = await page.evaluate(() => {
      const results = [];
      const seen = new Set();

      // Find all publication links
      const links = document.querySelectorAll('a[href]');
      for (const link of links) {
        const href = link.getAttribute('href') || '';

        // Match publication URLs: xxx.substack.com or substack.com/@handle
        let subdomain = null;
        let handle = null;

        const subMatch = href.match(/https?:\/\/(\w[\w-]+)\.substack\.com\/?$/);
        const handleMatch = href.match(/substack\.com\/@([\w-]+)/);

        if (subMatch) {
          subdomain = subMatch[1];
        } else if (handleMatch) {
          handle = handleMatch[1];
        } else {
          continue;
        }

        const key = subdomain || handle;
        if (!key || seen.has(key) || key === 'www' || key === 'substack') continue;
        seen.add(key);

        // Find container for metadata
        const container =
          link.closest('[class*="publication"]') ||
          link.closest('[class*="card"]') ||
          link.closest('[class*="item"]') ||
          link.parentElement?.parentElement;

        let name = '';
        let author = '';
        let description = '';
        let image = '';

        if (container) {
          const nameEl = container.querySelector('h2, h3, h4, [class*="name"], [class*="title"]');
          if (nameEl) name = nameEl.textContent.trim();

          const authorEl = container.querySelector('[class*="author"], [class*="byline"]');
          if (authorEl) author = authorEl.textContent.trim();

          const descEl = container.querySelector('[class*="description"], [class*="hero"], p');
          if (descEl && descEl !== nameEl) description = descEl.textContent.trim().slice(0, 200);

          const img = container.querySelector('img');
          if (img) image = img.src || '';
        }

        if (!name) {
          name = link.textContent.trim() || subdomain || handle || '';
        }

        results.push({
          name,
          author,
          description,
          image_url: image,
          url: subdomain
            ? `https://${subdomain}.substack.com`
            : `https://substack.com/@${handle}`,
          handle: handle || subdomain || '',
          source: 'browse',
        });
      }

      return results;
    });

    if (publications.length === 0) {
      return res.status(200).json({
        substacker: null,
        category,
        message: 'No publications found on browse page.',
      });
    }

    // Pick a random one
    const pick = publications[Math.floor(Math.random() * publications.length)];

    return res.status(200).json({
      substacker: pick,
      category,
      total_found: publications.length,
    });
  } catch (error) {
    console.error('Random substacker error:', error);
    return res.status(500).json({
      error: `Failed to find random substacker: ${error.message}`,
    });
  } finally {
    if (browser) {
      await browser.close().catch(() => {});
    }
  }
}
