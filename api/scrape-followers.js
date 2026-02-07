import chromium from '@sparticuz/chromium';
import playwright from 'playwright-core';

export default async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { url } = req.body || {};
  if (!url || typeof url !== 'string') {
    return res.status(400).json({ error: 'Missing "url" field' });
  }

  // Parse the input to get a followers page URL
  const handle = resolveHandle(url.trim());
  if (!handle) {
    return res.status(400).json({
      error: 'Could not parse Substack URL. Try: substack.com/@handle or example.substack.com',
    });
  }

  const followersUrl = `https://substack.com/@${handle}/followers`;

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
    await page.goto(followersUrl, { waitUntil: 'networkidle', timeout: 15000 });

    // Wait for follower elements to appear (Substack renders profile cards)
    await page.waitForSelector(
      '[class*="profile-card"], [class*="follower"], a[href*="/@"]',
      { timeout: 8000 }
    ).catch(() => null);

    // Give a bit more time for content to render
    await page.waitForTimeout(1500);

    // Extract follower data from the DOM
    const followers = await page.evaluate(() => {
      const results = [];
      const seen = new Set();

      // Strategy 1: Look for profile links with @handle pattern
      const profileLinks = document.querySelectorAll('a[href*="/@"]');
      for (const link of profileLinks) {
        const href = link.getAttribute('href') || '';
        const match = href.match(/@([\w-]+)/);
        if (!match) continue;

        const handle = match[1];
        // Skip the page owner and common nav links
        if (seen.has(handle)) continue;
        seen.add(handle);

        // Find the closest container that might have name/image
        const container =
          link.closest('[class*="profile"]') ||
          link.closest('[class*="card"]') ||
          link.closest('[class*="subscriber"]') ||
          link.closest('[class*="follower"]') ||
          link.closest('[class*="user"]') ||
          link.parentElement?.parentElement;

        let name = '';
        let photo = '';
        let bio = '';

        if (container) {
          // Find name - usually in a heading or strong element
          const nameEl =
            container.querySelector('h3, h4, [class*="name"], [class*="title"], strong');
          if (nameEl) {
            name = nameEl.textContent.trim();
          }

          // Find image
          const img = container.querySelector('img');
          if (img) {
            photo = img.src || '';
          }

          // Find bio/description
          const bioEl = container.querySelector(
            '[class*="bio"], [class*="description"], [class*="text"], p'
          );
          if (bioEl && bioEl !== nameEl) {
            bio = bioEl.textContent.trim().slice(0, 200);
          }
        }

        if (!name) {
          name = link.textContent.trim() || handle;
        }

        results.push({
          name,
          handle,
          photo_url: photo,
          bio,
          profile_url: `https://substack.com/@${handle}`,
          publication_url: '',
          publication_name: '',
        });
      }

      // Strategy 2: Look for any user/profile card divs with data attributes
      if (results.length === 0) {
        const cards = document.querySelectorAll(
          '[data-testid*="profile"], [data-testid*="follower"], [data-testid*="user"]'
        );
        for (const card of cards) {
          const link = card.querySelector('a[href*="/@"]');
          const href = link?.getAttribute('href') || '';
          const match = href.match(/@([\w-]+)/);
          if (!match) continue;

          const handle = match[1];
          if (seen.has(handle)) continue;
          seen.add(handle);

          const nameEl = card.querySelector('h3, h4, [class*="name"], strong');
          const img = card.querySelector('img');
          const bioEl = card.querySelector('[class*="bio"], p');

          results.push({
            name: nameEl?.textContent.trim() || handle,
            handle,
            photo_url: img?.src || '',
            bio: bioEl?.textContent.trim().slice(0, 200) || '',
            profile_url: `https://substack.com/@${handle}`,
            publication_url: '',
            publication_name: '',
          });
        }
      }

      return results;
    });

    // Filter out the page owner's own handle
    const filtered = followers.filter(
      (f) => f.handle.toLowerCase() !== handle.toLowerCase()
    );

    return res.status(200).json({
      handle,
      followers: filtered,
      count: filtered.length,
    });
  } catch (error) {
    console.error('Scraping error:', error);
    return res.status(500).json({
      error: `Scraping failed: ${error.message}`,
    });
  } finally {
    if (browser) {
      await browser.close().catch(() => {});
    }
  }
}

function resolveHandle(input) {
  // Handle @username format
  if (input.startsWith('@')) {
    return input.slice(1).split('/')[0];
  }

  // Handle bare username (no dots, no slashes, no protocol)
  if (!input.includes('.') && !input.includes('/') && !input.includes(':')) {
    return input;
  }

  try {
    const url = new URL(input.startsWith('http') ? input : `https://${input}`);
    const hostname = url.hostname;
    const path = url.pathname.replace(/^\/+|\/+$/g, '');

    // substack.com/@handle
    if (
      (hostname === 'substack.com' || hostname === 'www.substack.com') &&
      path.startsWith('@')
    ) {
      return path.split('/')[0].slice(1);
    }

    // example.substack.com -> use subdomain as handle
    if (hostname.endsWith('.substack.com')) {
      return hostname.replace('.substack.com', '');
    }

    // Custom domain - can't resolve without extra fetch
    return null;
  } catch {
    return null;
  }
}
