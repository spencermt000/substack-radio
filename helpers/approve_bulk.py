#!/usr/bin/env python3
"""
Bulk approve all articles in Airtable.
Sets approved = TRUE for all records.
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


def approve_records(table: str, record_ids: list) -> int:
    """Approve records in batches of 10 (Airtable limit)."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}"
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json',
    }

    approved_count = 0
    batch_size = 10

    for i in range(0, len(record_ids), batch_size):
        batch = record_ids[i:i + batch_size]

        payload = {
            'records': [
                {'id': rid, 'fields': {'approved': True}}
                for rid in batch
            ]
        }

        response = requests.patch(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        approved_count += len(batch)
        print(f"  Approved {approved_count}/{len(record_ids)} records...")

    return approved_count


def main():
    check_config()

    print("=" * 50)
    print("Bulk Approve - Airtable")
    print("=" * 50)

    # Determine which table to approve
    table = 'Articles'
    if '--newsletters' in sys.argv:
        table = 'Newsletters'

    print(f"\nFetching {table}...")
    records = fetch_all_records(table)

    # Find unapproved records
    unapproved = [
        r['id'] for r in records
        if not r.get('fields', {}).get('approved', False)
    ]

    total = len(records)
    already_approved = total - len(unapproved)

    print(f"\nFound {total} total records:")
    print(f"  - Already approved: {already_approved}")
    print(f"  - Unapproved: {len(unapproved)}")

    if not unapproved:
        print("\nNo records to approve!")
        return

    # Confirm
    confirm = input(f"\nApprove {len(unapproved)} records? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    # Approve records
    print(f"\nApproving {len(unapproved)} records...")
    approved = approve_records(table, unapproved)

    print(f"\nDone! Approved {approved} records.")


if __name__ == "__main__":
    main()
