#!/usr/bin/env python3
"""
Scrape metadata from Substack article URLs.

Extracts:
- Thumbnail image URL
- Post URL
- Post title
- Subtitle/description
- Newsletter name
- Newsletter URL
- Author name
- Author profile URL
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json
import re
import sys


def scrape_substack_article(url: str) -> dict:
    """
    Scrape metadata from a Substack article URL.

    Args:
        url: The Substack article URL to scrape

    Returns:
        Dictionary containing article metadata
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    result = {
        'post_url': url,
        'post_title': None,
        'post_subtitle': None,
        'thumbnail_url': None,
        'newsletter_name': None,
        'newsletter_url': None,
        'author_name': None,
        'author_profile_url': None,
    }

    # Try to extract from JSON-LD structured data first (most reliable)
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                data = data[0]

            if data.get('@type') in ['Article', 'NewsArticle', 'BlogPosting']:
                result['post_title'] = data.get('headline')
                result['post_subtitle'] = data.get('description')

                # Get image
                image = data.get('image')
                if isinstance(image, list) and image:
                    result['thumbnail_url'] = image[0]
                elif isinstance(image, str):
                    result['thumbnail_url'] = image
                elif isinstance(image, dict):
                    result['thumbnail_url'] = image.get('url')

                # Get author info
                author = data.get('author')
                if isinstance(author, dict):
                    result['author_name'] = author.get('name')
                    result['author_profile_url'] = author.get('url')
                elif isinstance(author, list) and author:
                    result['author_name'] = author[0].get('name')
                    result['author_profile_url'] = author[0].get('url')

                # Get publisher (newsletter) info
                publisher = data.get('publisher')
                if isinstance(publisher, dict):
                    result['newsletter_name'] = publisher.get('name')
                    result['newsletter_url'] = publisher.get('url')

        except (json.JSONDecodeError, TypeError, KeyError):
            continue

    # Fallback to Open Graph and meta tags
    if not result['post_title']:
        og_title = soup.find('meta', property='og:title')
        if og_title:
            result['post_title'] = og_title.get('content')

    if not result['post_subtitle']:
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            result['post_subtitle'] = og_desc.get('content')
        else:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                result['post_subtitle'] = meta_desc.get('content')

    if not result['thumbnail_url']:
        og_image = soup.find('meta', property='og:image')
        if og_image:
            result['thumbnail_url'] = og_image.get('content')

    if not result['newsletter_name']:
        og_site = soup.find('meta', property='og:site_name')
        if og_site:
            result['newsletter_name'] = og_site.get('content')

    # Extract newsletter URL from the article URL
    if not result['newsletter_url']:
        parsed = urlparse(url)
        result['newsletter_url'] = f"{parsed.scheme}://{parsed.netloc}"

    # Try to find author from page elements if not in structured data
    if not result['author_name']:
        # Look for author link in the page
        author_link = soup.find('a', class_=re.compile(r'.*author.*', re.I))
        if author_link:
            result['author_name'] = author_link.get_text(strip=True)
            result['author_profile_url'] = author_link.get('href')
        else:
            # Try finding in byline
            byline = soup.find(class_=re.compile(r'.*byline.*', re.I))
            if byline:
                result['author_name'] = byline.get_text(strip=True)

    # Clean up author profile URL to be absolute
    if result['author_profile_url'] and not result['author_profile_url'].startswith('http'):
        parsed = urlparse(url)
        result['author_profile_url'] = f"{parsed.scheme}://{parsed.netloc}{result['author_profile_url']}"

    return result


def format_output(data: dict) -> str:
    """Format the scraped data for display."""
    lines = [
        "=" * 60,
        "SUBSTACK ARTICLE METADATA",
        "=" * 60,
        f"Title:           {data['post_title']}",
        f"Subtitle:        {data['post_subtitle']}",
        f"Post URL:        {data['post_url']}",
        f"Thumbnail:       {data['thumbnail_url']}",
        "-" * 60,
        f"Newsletter:      {data['newsletter_name']}",
        f"Newsletter URL:  {data['newsletter_url']}",
        f"Author:          {data['author_name']}",
        f"Author Profile:  {data['author_profile_url']}",
        "=" * 60,
    ]
    return "\n".join(lines)


def format_json(data: dict) -> str:
    """Format the scraped data as JSON."""
    return json.dumps(data, indent=2)


def scrape_from_json(json_path: str, output_path: str = None) -> list:
    """
    Scrape multiple URLs from a JSON file.

    Args:
        json_path: Path to JSON file containing URLs
        output_path: Optional path to save results (defaults to input_scraped.json)

    JSON file format options:
        1. Simple array of URLs:
           ["https://example.substack.com/p/article1", "https://..."]

        2. Array of objects with url field:
           [{"url": "https://...", "note": "optional metadata"}, ...]

    Returns:
        List of scraped article data
    """
    import time

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Normalize to list of URLs
    urls = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                urls.append(item)
            elif isinstance(item, dict) and 'url' in item:
                urls.append(item['url'])
    elif isinstance(data, dict) and 'urls' in data:
        # Support {"urls": [...]} format
        for item in data['urls']:
            if isinstance(item, str):
                urls.append(item)
            elif isinstance(item, dict) and 'url' in item:
                urls.append(item['url'])

    print(f"Found {len(urls)} URLs to scrape")
    print("=" * 60)

    results = []
    errors = []

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Scraping: {url}")
        try:
            article_data = scrape_substack_article(url)
            results.append(article_data)
            print(f"  ✓ {article_data['post_title'][:50]}..." if article_data['post_title'] else "  ✓ Scraped")

            # Small delay to be nice to servers
            if i < len(urls):
                time.sleep(0.5)

        except Exception as e:
            print(f"  ✗ Error: {e}")
            errors.append({'url': url, 'error': str(e)})

    print("\n" + "=" * 60)
    print(f"Completed: {len(results)} successful, {len(errors)} failed")

    # Determine output path
    if not output_path:
        base_name = json_path.rsplit('.', 1)[0]
        output_path = f"{base_name}_scraped.json"

    # Save results
    output_data = {
        'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total': len(urls),
        'successful': len(results),
        'failed': len(errors),
        'articles': results,
        'errors': errors
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Results saved to: {output_path}")

    return results


def main():
    # Check for --file flag for batch processing
    if '--file' in sys.argv:
        try:
            file_idx = sys.argv.index('--file')
            json_path = sys.argv[file_idx + 1]
        except (IndexError, ValueError):
            print("Error: --file requires a path to a JSON file")
            print("Usage: python scrape_substack_links.py --file urls.json [--output results.json]")
            sys.exit(1)

        # Check for optional output path
        output_path = None
        if '--output' in sys.argv:
            try:
                out_idx = sys.argv.index('--output')
                output_path = sys.argv[out_idx + 1]
            except (IndexError, ValueError):
                pass

        scrape_from_json(json_path, output_path)
        return

    # Single URL mode
    if len(sys.argv) < 2:
        # Interactive mode - prompt for URL
        print("Substack Article Scraper")
        print("-" * 40)
        print("Modes:")
        print("  Single URL:  python scrape_substack_links.py <url>")
        print("  Batch mode:  python scrape_substack_links.py --file urls.json")
        print("-" * 40)
        url = input("Paste Substack article URL: ").strip()
    else:
        url = sys.argv[1]

    if not url:
        print("Error: No URL provided")
        sys.exit(1)

    # Validate it looks like a Substack URL
    if 'substack.com' not in url and not url.endswith('.substack.com'):
        parsed = urlparse(url)
        if not parsed.netloc:
            print("Error: Invalid URL")
            sys.exit(1)
        print(f"Warning: URL doesn't appear to be a Substack domain, attempting anyway...")

    try:
        print(f"\nScraping: {url}\n")
        data = scrape_substack_article(url)

        # Check for --json flag
        if '--json' in sys.argv:
            print(format_json(data))
        else:
            print(format_output(data))

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing page: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
