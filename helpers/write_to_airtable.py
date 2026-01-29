#!/usr/bin/env python3
"""
Write scraped Substack data to Airtable.

Uses scrape_substack_links.py to fetch article metadata,
then writes it to the appropriate Airtable table.
"""

import os
import sys
import requests
from datetime import date
from dotenv import load_dotenv

from scrape_substack_links import scrape_substack_article

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
ARTICLES_TABLE = 'Articles'
NEWSLETTERS_TABLE = 'Newsletters'

# Station configuration matching CLAUDE.md
STATIONS = {
    'CAPITAL94': {
        'name': 'CAPITAL94',
        'display': 'Business, Finance & Innovation',
        'subcategories': [
            'The Capital Mix',
            'Markets & Investing',
            'Startups & Tech',
            'Economics & Business',
            'Personal Finance & Indie',
        ]
    },
    'PULSE95': {
        'name': 'PULSE95',
        'display': 'Media, Culture & Current Events',
        'subcategories': [
            'The Pulse Mix',
            'News & Current Events',
            'Pop Culture & Entertainment',
            'Politics & Society',
            'Sports & Competition',
        ]
    },
    'GROWTH96': {
        'name': 'GROWTH96',
        'display': 'Life, Mind & Wellness',
        'subcategories': [
            'The Growth Mix',
            'Psychology & Self-Help',
            'Food, Travel & Lifestyle',
            'Productivity & Learning',
            'Health & Wellness',
        ]
    },
    'CREATE97': {
        'name': 'CREATE97',
        'display': 'Essays, Stories & Ideas',
        'subcategories': [
            'The Creative Mix',
            'Essays & Commentary',
            'Fiction & Storytelling',
            'Philosophy & Big Ideas',
            'Art & Craft',
        ]
    },
}


def check_config():
    """Verify Airtable credentials are configured."""
    if not AIRTABLE_API_KEY:
        print("Error: AIRTABLE_API_KEY not found in environment variables")
        print("Make sure your .env file contains AIRTABLE_API_KEY=your_key_here")
        sys.exit(1)
    if not AIRTABLE_BASE_ID:
        print("Error: AIRTABLE_BASE_ID not found in environment variables")
        print("Make sure your .env file contains AIRTABLE_BASE_ID=your_base_id_here")
        sys.exit(1)


def airtable_request(table: str, method: str = 'GET', data: dict = None) -> dict:
    """Make a request to the Airtable API."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}"
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json',
    }

    if method == 'GET':
        response = requests.get(url, headers=headers, timeout=10)
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=data, timeout=10)
    else:
        raise ValueError(f"Unsupported method: {method}")

    response.raise_for_status()
    return response.json()


def create_article(article_data: dict, station: str, subcategory: str) -> dict:
    """
    Create an article record in Airtable.

    Args:
        article_data: Scraped article data from scrape_substack_article()
        station: Station key (e.g., 'CAPITAL94')
        subcategory: Subcategory name (e.g., 'Markets & Investing')

    Returns:
        Created record from Airtable
    """
    fields = {
        'title': article_data['post_title'],
        'author': article_data['author_name'] or '',
        'url': article_data['post_url'],
        'station_main': station,
        'subcategory': subcategory,
        'description': article_data['post_subtitle'] or '',
        'submitted_date': date.today().isoformat(),
        'approved': False,  # Requires manual approval
        'image_url': article_data['thumbnail_url'] or '',
    }

    payload = {'fields': fields}
    result = airtable_request(ARTICLES_TABLE, 'POST', payload)
    return result


def create_newsletter(newsletter_data: dict, station: str) -> dict:
    """
    Create a newsletter record in Airtable.

    Args:
        newsletter_data: Scraped data (newsletter info)
        station: Station key (e.g., 'CAPITAL94')

    Returns:
        Created record from Airtable
    """
    fields = {
        'name': newsletter_data['newsletter_name'],
        'author': newsletter_data['author_name'] or '',
        'url': newsletter_data['newsletter_url'],
        'station_main': station,
        'bio': '',  # User can fill in later
        'submitted_date': date.today().isoformat(),
        'approved': False,  # Requires manual approval
        'image_url': '',  # User can add later
    }

    payload = {'fields': fields}
    result = airtable_request(NEWSLETTERS_TABLE, 'POST', payload)
    return result


def select_station() -> str:
    """Prompt user to select a station."""
    print("\nSelect a station:")
    stations_list = list(STATIONS.keys())
    for i, key in enumerate(stations_list, 1):
        station = STATIONS[key]
        print(f"  {i}. {station['name']} - {station['display']}")

    while True:
        try:
            choice = input("\nEnter number (1-4): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(stations_list):
                return stations_list[idx]
            print("Invalid choice. Please enter 1-4.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def select_subcategory(station: str) -> str:
    """Prompt user to select a subcategory for the given station."""
    subcategories = STATIONS[station]['subcategories']

    print(f"\nSelect a subcategory for {station}:")
    for i, subcat in enumerate(subcategories, 1):
        print(f"  {i}. {subcat}")

    while True:
        try:
            choice = input(f"\nEnter number (1-{len(subcategories)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(subcategories):
                return subcategories[idx]
            print(f"Invalid choice. Please enter 1-{len(subcategories)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def select_record_type() -> str:
    """Prompt user to select article or newsletter."""
    print("\nWhat would you like to add?")
    print("  1. Article")
    print("  2. Newsletter")

    while True:
        choice = input("\nEnter number (1-2): ").strip()
        if choice == '1':
            return 'article'
        elif choice == '2':
            return 'newsletter'
        print("Invalid choice. Please enter 1 or 2.")


def add_article_flow(url: str = None):
    """Interactive flow to add an article."""
    if not url:
        url = input("\nPaste Substack article URL: ").strip()

    if not url:
        print("Error: No URL provided")
        return

    print(f"\nScraping: {url}")
    try:
        data = scrape_substack_article(url)
    except Exception as e:
        print(f"Error scraping URL: {e}")
        return

    print(f"\n  Title: {data['post_title']}")
    print(f"  Author: {data['author_name']}")
    print(f"  Newsletter: {data['newsletter_name']}")

    station = select_station()
    subcategory = select_subcategory(station)

    print(f"\nAdding article to {station} > {subcategory}...")

    try:
        result = create_article(data, station, subcategory)
        print(f"\nSuccess! Article added with ID: {result['id']}")
        print("Note: Article is unapproved. Set approved=true in Airtable to make it eligible.")
    except requests.exceptions.HTTPError as e:
        print(f"Error creating article: {e}")
        if e.response:
            print(f"Response: {e.response.text}")


def add_newsletter_flow(url: str = None):
    """Interactive flow to add a newsletter."""
    if not url:
        url = input("\nPaste any Substack article URL from the newsletter: ").strip()

    if not url:
        print("Error: No URL provided")
        return

    print(f"\nScraping newsletter info from: {url}")
    try:
        data = scrape_substack_article(url)
    except Exception as e:
        print(f"Error scraping URL: {e}")
        return

    print(f"\n  Newsletter: {data['newsletter_name']}")
    print(f"  URL: {data['newsletter_url']}")
    print(f"  Author: {data['author_name']}")

    station = select_station()

    print(f"\nAdding newsletter to {station}...")

    try:
        result = create_newsletter(data, station)
        print(f"\nSuccess! Newsletter added with ID: {result['id']}")
        print("Note: Newsletter is unapproved. Set approved=true in Airtable to make it eligible.")
        print("Tip: Add a bio and image_url in Airtable for a better display.")
    except requests.exceptions.HTTPError as e:
        print(f"Error creating newsletter: {e}")
        if e.response:
            print(f"Response: {e.response.text}")


def batch_add_articles(urls: list[str], station: str, subcategory: str):
    """Add multiple articles to the same station/subcategory."""
    print(f"\nAdding {len(urls)} articles to {station} > {subcategory}...")

    success_count = 0
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Processing: {url}")
        try:
            data = scrape_substack_article(url)
            create_article(data, station, subcategory)
            print(f"  Added: {data['post_title'][:50]}...")
            success_count += 1
        except Exception as e:
            print(f"  Error: {e}")

    print(f"\nDone! Added {success_count}/{len(urls)} articles.")


def import_from_scraped_json(json_path: str, station: str = None, subcategory: str = None):
    """
    Import articles from a scraped JSON file (output from scrape_substack_links.py).

    Args:
        json_path: Path to the scraped JSON file
        station: Optional station key (will prompt if not provided)
        subcategory: Optional subcategory (will prompt if not provided)
    """
    import json as json_module
    import time

    # Load the scraped data
    with open(json_path, 'r') as f:
        data = json_module.load(f)

    # Handle different JSON formats
    if 'articles' in data:
        # Output from scrape_substack_links.py --file
        articles = data['articles']
        print(f"\nLoaded scraped file from: {data.get('scraped_at', 'unknown')}")
        print(f"Total articles: {data.get('successful', len(articles))}")
        if data.get('failed', 0) > 0:
            print(f"Failed scrapes: {data.get('failed', 0)}")

        # Get station/subcategory from JSON if not passed as args
        if not station and data.get('station'):
            station = data['station']
            print(f"Station from JSON: {station}")
        if not subcategory and data.get('subcategory'):
            subcategory = data['subcategory']
            print(f"Subcategory from JSON: {subcategory}")
    elif isinstance(data, list):
        # Direct array of article objects
        articles = data
        print(f"\nLoaded {len(articles)} articles from JSON")
    else:
        print("Error: Unrecognized JSON format")
        print("Expected: output from 'scrape_substack_links.py --file' or array of article objects")
        return

    if not articles:
        print("No articles found in JSON file")
        return

    # Show sample of what we're importing
    print("\n" + "=" * 50)
    print("Sample articles to import:")
    for i, article in enumerate(articles[:3], 1):
        title = article.get('post_title', 'No title')[:50]
        print(f"  {i}. {title}...")
    if len(articles) > 3:
        print(f"  ... and {len(articles) - 3} more")
    print("=" * 50)

    # Get station and subcategory if not provided (prompt if still missing)
    if not station:
        station = select_station()
    if not subcategory:
        subcategory = select_subcategory(station)

    # Confirm before proceeding
    print(f"\nReady to import {len(articles)} articles to:")
    print(f"  Station: {station}")
    print(f"  Subcategory: {subcategory}")
    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    # Import articles
    print(f"\nImporting {len(articles)} articles...")
    print("=" * 50)

    success_count = 0
    error_count = 0
    results = []

    for i, article in enumerate(articles, 1):
        title = article.get('post_title', 'Unknown')[:40]
        print(f"\n[{i}/{len(articles)}] {title}...")

        try:
            result = create_article(article, station, subcategory)
            print(f"  ✓ Added (ID: {result['id']})")
            success_count += 1
            results.append({
                'status': 'success',
                'title': article.get('post_title'),
                'id': result['id']
            })

            # Small delay to avoid rate limiting
            if i < len(articles):
                time.sleep(0.3)

        except requests.exceptions.HTTPError as e:
            print(f"  ✗ Error: {e}")
            error_count += 1
            results.append({
                'status': 'error',
                'title': article.get('post_title'),
                'error': str(e)
            })
        except Exception as e:
            print(f"  ✗ Error: {e}")
            error_count += 1
            results.append({
                'status': 'error',
                'title': article.get('post_title'),
                'error': str(e)
            })

    # Summary
    print("\n" + "=" * 50)
    print("IMPORT COMPLETE")
    print("=" * 50)
    print(f"  Successful: {success_count}")
    print(f"  Failed: {error_count}")
    print(f"  Total: {len(articles)}")

    if success_count > 0:
        print(f"\nNote: All {success_count} articles are unapproved.")
        print("Set approved=true in Airtable to make them eligible.")

    # Save results log
    log_path = json_path.rsplit('.', 1)[0] + '_import_log.json'
    log_data = {
        'imported_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'source_file': json_path,
        'station': station,
        'subcategory': subcategory,
        'successful': success_count,
        'failed': error_count,
        'results': results
    }
    with open(log_path, 'w') as f:
        json_module.dump(log_data, f, indent=2)
    print(f"\nImport log saved to: {log_path}")

    return results


def import_newsletters_from_scraped_json(json_path: str, station: str = None):
    """
    Import newsletters from a scraped JSON file.
    Extracts unique newsletters from the scraped articles.

    Args:
        json_path: Path to the scraped JSON file
        station: Optional station key (will prompt if not provided)
    """
    import json as json_module
    import time

    # Load the scraped data
    with open(json_path, 'r') as f:
        data = json_module.load(f)

    # Handle different JSON formats
    if 'articles' in data:
        articles = data['articles']
        # Get station from JSON if not passed as arg
        if not station and data.get('station'):
            station = data['station']
            print(f"Station from JSON: {station}")
    elif isinstance(data, list):
        articles = data
    else:
        print("Error: Unrecognized JSON format")
        return

    # Extract unique newsletters
    newsletters = {}
    for article in articles:
        nl_url = article.get('newsletter_url')
        if nl_url and nl_url not in newsletters:
            newsletters[nl_url] = {
                'newsletter_name': article.get('newsletter_name'),
                'newsletter_url': nl_url,
                'author_name': article.get('author_name'),
            }

    if not newsletters:
        print("No newsletters found in JSON file")
        return

    print(f"\nFound {len(newsletters)} unique newsletters:")
    for i, nl in enumerate(list(newsletters.values())[:5], 1):
        print(f"  {i}. {nl['newsletter_name']} ({nl['author_name']})")
    if len(newsletters) > 5:
        print(f"  ... and {len(newsletters) - 5} more")

    # Get station if not provided
    if not station:
        station = select_station()

    # Confirm
    print(f"\nReady to import {len(newsletters)} newsletters to {station}")
    confirm = input("Proceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    # Import newsletters
    success_count = 0
    for i, nl in enumerate(newsletters.values(), 1):
        print(f"\n[{i}/{len(newsletters)}] {nl['newsletter_name']}...")
        try:
            result = create_newsletter(nl, station)
            print(f"  ✓ Added (ID: {result['id']})")
            success_count += 1
            if i < len(newsletters):
                time.sleep(0.3)
        except Exception as e:
            print(f"  ✗ Error: {e}")

    print(f"\nDone! Added {success_count}/{len(newsletters)} newsletters.")


def main():
    check_config()

    print("=" * 50)
    print("Substack Radio - Airtable Writer")
    print("=" * 50)

    # Check for --import flag (import from scraped JSON)
    if '--import' in sys.argv:
        try:
            import_idx = sys.argv.index('--import')
            json_path = sys.argv[import_idx + 1]
        except (IndexError, ValueError):
            print("Error: --import requires a path to a scraped JSON file")
            print("Usage: python write_to_airtable.py --import scraped.json")
            print("       python write_to_airtable.py --import scraped.json --newsletters")
            sys.exit(1)

        # Check if importing newsletters instead of articles
        if '--newsletters' in sys.argv:
            import_newsletters_from_scraped_json(json_path)
        else:
            import_from_scraped_json(json_path)
        return

    # Check for command line arguments
    if len(sys.argv) > 1:
        url = sys.argv[1]
        record_type = 'article'

        # Check for --newsletter flag
        if '--newsletter' in sys.argv:
            record_type = 'newsletter'
            if url == '--newsletter':
                url = sys.argv[2] if len(sys.argv) > 2 else None

        if record_type == 'newsletter':
            add_newsletter_flow(url)
        else:
            add_article_flow(url)
    else:
        # Interactive mode
        print("\nModes:")
        print("  1. Add single article")
        print("  2. Add single newsletter")
        print("  3. Import from scraped JSON")

        choice = input("\nSelect mode (1-3): ").strip()

        if choice == '1':
            add_article_flow()
        elif choice == '2':
            add_newsletter_flow()
        elif choice == '3':
            json_path = input("\nPath to scraped JSON file: ").strip()
            if not json_path:
                print("Error: No path provided")
                return

            import_type = input("Import as (a)rticles or (n)ewsletters? [a]: ").strip().lower()
            if import_type == 'n':
                import_newsletters_from_scraped_json(json_path)
            else:
                import_from_scraped_json(json_path)
        else:
            print("Invalid choice")
            return


if __name__ == "__main__":
    main()
