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

**Step 1:** Create a JSON file with URLs:

```json
[
  "https://example.substack.com/p/article-one",
  "https://another.substack.com/p/article-two",
  "https://third.substack.com/p/article-three"
]
```

**Step 2:** Run the scraper:

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
# Import articles (prompts for station/subcategory)
python write_to_airtable.py --import urls_scraped.json

# Import newsletters (extracts unique newsletters from articles)
python write_to_airtable.py --import urls_scraped.json --newsletters
```

---

## Complete Workflow Example

### Adding Articles to a Station

```bash
# 1. Create a file with URLs you want to add
cat > capital_articles.json << 'EOF'
[
  "https://newsletter1.substack.com/p/market-analysis",
  "https://newsletter2.substack.com/p/startup-trends",
  "https://newsletter3.substack.com/p/investing-guide"
]
EOF

# 2. Scrape all the articles
python scrape_substack_links.py --file capital_articles.json

# 3. Import to Airtable
python write_to_airtable.py --import capital_articles_scraped.json

# You'll be prompted to select:
#   - Station (e.g., CAPITAL94)
#   - Subcategory (e.g., Markets & Investing)
# Then confirm the import
```

### Adding Newsletters

```bash
# After scraping articles, extract and import unique newsletters
python write_to_airtable.py --import capital_articles_scraped.json --newsletters

# You'll be prompted to select a station
# Newsletters don't have subcategories
```

---

## Stations Reference

| Station | Description | Subcategories |
|---------|-------------|---------------|
| CAPITAL94 | Business, Finance & Innovation | Markets & Investing, Startups & Tech, Economics & Business, Personal Finance & Indie |
| PULSE95 | Media, Culture & Current Events | News & Current Events, Pop Culture & Entertainment, Politics & Society, Sports & Competition |
| GROWTH96 | Life, Mind & Wellness | Psychology & Self-Help, Food Travel & Lifestyle, Productivity & Learning, Health & Wellness |
| CREATE97 | Essays, Stories & Ideas | Essays & Commentary, Fiction & Storytelling, Philosophy & Big Ideas, Art & Craft |

---

## Tips

- **All imports are unapproved by default.** Go to Airtable and set `approved=true` to make articles visible on the site.

- **Import logs** are saved automatically (e.g., `urls_scraped_import_log.json`) so you can track what was added.

- **Rate limiting:** Scripts add small delays between requests to avoid overwhelming servers.

- **Duplicate handling:** The scripts don't check for duplicates. Make sure you're not importing the same URLs twice.
