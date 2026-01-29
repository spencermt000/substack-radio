



#
# Helper Scripts

Scripts for scraping Substack articles and writing them to Airtable.

## Setup

```bash
cd helpers
pip install -r requirements.txt
```

Make sure your `.env` file in the project root has:
```
AIRTABLE_API_KEY=your_api_key_here
AIRTABLE_BASE_ID=your_base_id_here
```

---

## 1. scrape_substack_links.py

Scrapes metadata from Substack article URLs.

### Single URL

```bash
# Basic usage
python scrape_substack_links.py "https://example.substack.com/p/article-slug"

# Output as JSON
python scrape_substack_links.py "https://example.substack.com/p/article-slug" --json

# Interactive mode (prompts for URL)
python scrape_substack_links.py
```

### Batch Mode (from JSON file)

**Recommended format** - Include station and subcategory to skip prompts during import:

```json
{
  "station": "CAPITAL94",
  "subcategory": "Markets & Investing",
  "urls": [
    "https://example.substack.com/p/article-one",
    "https://another.substack.com/p/article-two",
    "https://third.substack.com/p/article-three"
  ]
}
```

**Simple format** - Just URLs (you'll be prompted for station/subcategory during import):

```json
[
  "https://example.substack.com/p/article-one",
  "https://another.substack.com/p/article-two"
]
```

**Run the scraper:**

```bash
# Scrape all URLs (outputs to urls_scraped.json)
python scrape_substack_links.py --file urls.json

# Custom output path
python scrape_substack_links.py --file urls.json --output results.json
```

### Output Format

The scraped JSON contains:
```json
{
  "scraped_at": "2026-01-28 12:00:00",
  "station": "CAPITAL94",
  "subcategory": "Markets & Investing",
  "total": 10,
  "successful": 9,
  "failed": 1,
  "articles": [
    {
      "post_url": "https://...",
      "post_title": "Article Title",
      "post_subtitle": "Description...",
      "thumbnail_url": "https://...",
      "newsletter_name": "Newsletter Name",
      "newsletter_url": "https://...",
      "author_name": "Author Name",
      "author_profile_url": "https://..."
    }
  ],
  "errors": []
}
```

---

## 2. write_to_airtable.py

Writes articles and newsletters to Airtable.

### Interactive Mode

```bash
python write_to_airtable.py
```

Shows menu:
1. Add single article
2. Add single newsletter
3. Import from scraped JSON

### Single Article

```bash
# Pass URL directly (prompts for station/subcategory)
python write_to_airtable.py "https://example.substack.com/p/article-slug"
```

### Single Newsletter

```bash
# Pass any article URL from the newsletter
python write_to_airtable.py --newsletter "https://example.substack.com/p/any-article"
```

### Import from Scraped JSON

This is the recommended workflow for bulk imports.

```bash
# Import articles (uses station/subcategory from JSON, or prompts if missing)
python write_to_airtable.py --import urls_scraped.json

# Import newsletters (extracts unique newsletters from articles)
python write_to_airtable.py --import urls_scraped.json --newsletters
```

---

## Complete Workflow Example

### Adding Articles to a Station (No Prompts)

```bash
# 1. Create a file with URLs AND station/subcategory
cat > money_markets.json << 'EOF'
{
  "station": "CAPITAL94",
  "subcategory": "Markets & Investing",
  "urls": [
    "https://newsletter1.substack.com/p/market-analysis",
    "https://newsletter2.substack.com/p/startup-trends",
    "https://newsletter3.substack.com/p/investing-guide"
  ]
}
EOF

# 2. Scrape all the articles
python scrape_substack_links.py --file money_markets.json

# 3. Import to Airtable (no prompts - uses station/subcategory from JSON)
python write_to_airtable.py --import money_markets_scraped.json
```

### Adding Newsletters

```bash
# After scraping articles, extract and import unique newsletters
python write_to_airtable.py --import money_markets_scraped.json --newsletters

# Uses station from JSON, newsletters don't have subcategories
```

---

## Stations Reference

| Station | Description | Subcategories |
|---------|-------------|---------------|
| MONEY94 | Business, Finance & Innovation | Markets & Investing, Startups & Entrepreneurship, Technology & Innovation, Economics & Business, Personal Finance |
| PULSE95 | Media, Culture & Current Events | News & Current Events, Pop Culture & Entertainment, Film & TV, Music, Politics & Policy, Sports |
| GROWTH96 | Life, Mind & Wellness | Self-Help & Productivity, Food Travel & Lifestyle, Health & Wellness, Sciences |
| CREATE97 | Essays, Stories & Ideas | Essays & Commentary, Writing & Storytelling, Arts & Crafts, Philosophy, Miscellaneous |

---

## Tips

- **All imports are unapproved by default.** Go to Airtable and set `approved=true` to make articles visible on the site.

- **Import logs** are saved automatically (e.g., `urls_scraped_import_log.json`) so you can track what was added.

- **Rate limiting:** Scripts add small delays between requests to avoid overwhelming servers.

- **Duplicate handling:** The scripts don't check for duplicates. Make sure you're not importing the same URLs twice.

- **Organize by category:** Create separate JSON files for each station/subcategory combo (e.g., `money_markets.json`, `pulse_news.json`).
