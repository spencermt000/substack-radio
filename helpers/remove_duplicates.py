#!/usr/bin/env python3
"""
Remove duplicate articles from Airtable.

Duplicates are identified by URL + subcategory combination
(same URL can appear in multiple subcategories, so only URL+subcategory makes it a duplicate).

Also removes empty rows (rows with no title/url).
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')


def check_config():
    """Verify Airtable credentials are configured."""
    if not AIRTABLE_API_KEY:
        print("Error: AIRTABLE_API_KEY not found in environment variables")
        sys.exit(1)
    if not AIRTABLE_BASE_ID:
        print("Error: AIRTABLE_BASE_ID not found in environment variables")
        sys.exit(1)


def fetch_all_records(table: str) -> list:
    """Fetch all records from a table."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}"
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json',
    }

    all_records = []
    offset = None

    while True:
        params = {}
        if offset:
            params['offset'] = offset

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        all_records.extend(data.get('records', []))

        offset = data.get('offset')
        if not offset:
            break

    return all_records


def find_empty_records(records: list) -> list:
    """Find records with no title and no URL."""
    empty = []
    for record in records:
        fields = record.get('fields', {})
        title = fields.get('title', '') or fields.get('name', '')
        url = fields.get('link', '') or fields.get('url', '')

        if not title.strip() and not url.strip():
            empty.append({
                'id': record['id'],
                'reason': 'Empty (no title or URL)'
            })

    return empty


def find_duplicates(records: list) -> list:
    """
    Find duplicate records based on URL + subcategory combination.
    Returns list of record IDs to delete (keeps first occurrence).
    """
    seen = {}
    duplicates = []

    for record in records:
        fields = record.get('fields', {})
        url = fields.get('link', '') or fields.get('url', '')
        subcategory = fields.get('subcategory', '')

        if not url:
            continue

        # Create composite key from URL + subcategory
        key = f"{url}|{subcategory}"

        if key in seen:
            # This is a duplicate - mark for deletion
            duplicates.append({
                'id': record['id'],
                'key': key,
                'title': fields.get('title', fields.get('name', 'Unknown')),
                'subcategory': subcategory,
                'reason': 'Duplicate URL+subcategory'
            })
        else:
            seen[key] = record['id']

    return duplicates


def delete_records(table: str, record_ids: list) -> int:
    """Delete records in batches of 10 (Airtable limit)."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}"
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    }

    deleted_count = 0
    batch_size = 10

    for i in range(0, len(record_ids), batch_size):
        batch = record_ids[i:i + batch_size]

        # Airtable delete uses query params
        params = '&'.join([f'records[]={rid}' for rid in batch])
        delete_url = f"{url}?{params}"

        response = requests.delete(delete_url, headers=headers, timeout=30)
        response.raise_for_status()

        deleted_count += len(batch)
        print(f"  Deleted {deleted_count}/{len(record_ids)} records...")

    return deleted_count


def main():
    check_config()

    print("=" * 50)
    print("Remove Duplicates & Empty Rows - Airtable")
    print("=" * 50)

    # Determine which table
    table = 'Articles'
    if '--newsletters' in sys.argv:
        table = 'Newsletters'

    print(f"\nFetching {table}...")
    records = fetch_all_records(table)
    print(f"Found {len(records)} total records")

    # Find empty records
    print("\nSearching for empty records...")
    empty_records = find_empty_records(records)
    print(f"  Found {len(empty_records)} empty records")

    # Find duplicates (excluding empty records we'll already delete)
    empty_ids = set(r['id'] for r in empty_records)
    non_empty = [r for r in records if r['id'] not in empty_ids]

    print("\nSearching for duplicates (by URL + subcategory)...")
    duplicates = find_duplicates(non_empty)
    print(f"  Found {len(duplicates)} duplicates")

    # Combine lists
    to_delete = empty_records + duplicates

    if not to_delete:
        print("\nNo records to delete!")
        return

    # Show summary
    print(f"\n{'=' * 50}")
    print(f"SUMMARY: {len(to_delete)} records to delete")
    print(f"{'=' * 50}")
    print(f"  - Empty records: {len(empty_records)}")
    print(f"  - Duplicates: {len(duplicates)}")

    # Show preview
    print("\nPreview (first 15):")
    for i, record in enumerate(to_delete[:15], 1):
        title = record.get('title', 'N/A')[:35] if record.get('title') else 'N/A'
        reason = record.get('reason', '')
        subcat = record.get('subcategory', '')
        if subcat:
            print(f"  {i}. [{subcat}] {title}... ({reason})")
        else:
            print(f"  {i}. {title}... ({reason})")

    if len(to_delete) > 15:
        print(f"  ... and {len(to_delete) - 15} more")

    # Confirm
    confirm = input(f"\nDelete {len(to_delete)} records? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    # Delete records
    print(f"\nDeleting {len(to_delete)} records...")
    record_ids = [d['id'] for d in to_delete]
    deleted = delete_records(table, record_ids)

    print(f"\nDone! Deleted {deleted} records.")
    print(f"Remaining records: {len(records) - deleted}")


if __name__ == "__main__":
    main()
