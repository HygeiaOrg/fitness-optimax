#!/usr/bin/env python3
"""
Ingest workout data from Google Sheet into BigQuery native table.

This script reads from the Google Sheet (OptiMax_log tab) and loads all rows
into a new BigQuery table called `sheet_workouts`. Once verified, you can:
1. Update sql/01_stg_workouts.sql to read from sheet_workouts instead of the external table
2. Delete the external table

Usage:
    source .venv/bin/activate
    python ingest_sheet_to_bigquery.py
"""

import json
import os
import sys
from pathlib import Path
import subprocess
import google.auth
from google.cloud import bigquery
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime

PROJECT_ID = "gen-lang-client-0937519537"
DATASET = "Optimmax"
CONFIG_FILE = Path(__file__).parent / "config" / "bigquery.json"

# Destination table for sheet data (will be created/replaced)
SHEET_TABLE = "sheet_workouts"


def get_credentials():
    """Get Google Cloud credentials using gcloud access token."""
    # Use gcloud to get an access token with the needed scopes
    env = os.environ.copy()
    result = subprocess.run(
        ["gcloud", "auth", "print-access-token", "--quiet"],
        capture_output=True, text=True, stdin=subprocess.DEVNULL, env=env
    )
    if result.returncode != 0:
        print(f"Error getting gcloud token: {result.stderr}")
        print("Make sure you're authenticated with gcloud:")
        print("  gcloud auth login")
        sys.exit(1)

    return Credentials(result.stdout.strip())


def load_config():
    """Load sheet URL from config."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def extract_sheet_id(url):
    """Extract sheet ID from Google Sheets URL."""
    # Format: https://docs.google.com/spreadsheets/d/{SHEET_ID}/...
    if "/spreadsheets/d/" in url:
        return url.split("/spreadsheets/d/")[1].split("/")[0]
    raise ValueError(f"Invalid Sheet URL: {url}")


def read_sheet_data(creds, sheet_id, sheet_range):
    """Read data from Google Sheet using Sheets API."""
    service = build("sheets", "v4", credentials=creds)

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=sheet_range
        ).execute()

        values = result.get("values", [])
        if not values:
            print(f"No data found in sheet range: {sheet_range}")
            return []

        print(f"✅ Read {len(values)} rows from Sheet (including headers)")
        return values
    except Exception as e:
        print(f"Error reading sheet: {e}")
        sys.exit(1)


def create_table_schema():
    """Create BigQuery table schema matching the sheet structure."""
    return [
        bigquery.SchemaField("string_field_0", "STRING", description="Timestamp"),
        bigquery.SchemaField("string_field_1", "STRING", description="Date"),
        bigquery.SchemaField("string_field_2", "STRING", description="Athlete Name"),
        bigquery.SchemaField("string_field_3", "STRING", description="Exercise"),
        bigquery.SchemaField("string_field_4", "STRING", description="Sets"),
        bigquery.SchemaField("string_field_5", "STRING", description="Total Reps"),
        bigquery.SchemaField("string_field_6", "STRING", description="Total Weight"),
        bigquery.SchemaField("string_field_7", "STRING", description="RPE"),
    ]


def load_to_bigquery(creds, rows):
    """Load rows into BigQuery table."""
    client = bigquery.Client(project=PROJECT_ID, credentials=creds)
    table_id = f"{PROJECT_ID}.{DATASET}.{SHEET_TABLE}"

    # Create table reference
    table = bigquery.Table(table_id, schema=create_table_schema())

    # Delete if exists (fresh import)
    try:
        client.delete_table(table_id)
        print(f"Deleted existing table `{SHEET_TABLE}`")
    except Exception:
        pass

    # Create table
    table = client.create_table(table)
    print(f"✅ Created table `{SHEET_TABLE}`")

    # Convert rows to proper format (skip header row)
    if rows and rows[0] and rows[0][0] == "Timestamp":
        print(f"Skipping header row")
        rows = rows[1:]

    # Pad rows to 8 columns
    formatted_rows = []
    for i, row in enumerate(rows):
        while len(row) < 8:
            row.append("")
        formatted_rows.append({
            "string_field_0": row[0] if len(row) > 0 else "",
            "string_field_1": row[1] if len(row) > 1 else "",
            "string_field_2": row[2] if len(row) > 2 else "",
            "string_field_3": row[3] if len(row) > 3 else "",
            "string_field_4": row[4] if len(row) > 4 else "",
            "string_field_5": row[5] if len(row) > 5 else "",
            "string_field_6": row[6] if len(row) > 6 else "",
            "string_field_7": row[7] if len(row) > 7 else "",
        })

    if not formatted_rows:
        print("No data rows to insert")
        return 0

    # Insert rows in batches
    batch_size = 1000
    total_inserted = 0

    for i in range(0, len(formatted_rows), batch_size):
        batch = formatted_rows[i : i + batch_size]
        errors = client.insert_rows_json(table_id, batch)

        if errors:
            print(f"Errors inserting batch {i//batch_size + 1}:")
            for error in errors:
                print(f"  {error}")
        else:
            total_inserted += len(batch)
            print(f"  ✓ Inserted {len(batch)} rows ({total_inserted} total)")

    return total_inserted


def main():
    print("=" * 60)
    print("Ingest Google Sheet → BigQuery")
    print("=" * 60)
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET}")
    print(f"Table: {SHEET_TABLE}")
    print()

    # Get credentials and config
    creds = get_credentials()
    config = load_config()

    sheet_url = config.get("workout_log_sheet_url")
    sheet_range = config.get("workout_log_sheet_range", "OptiMax_log")

    if not sheet_url:
        print("❌ Error: workout_log_sheet_url not configured in config/bigquery.json")
        sys.exit(1)

    print(f"Sheet URL: {sheet_url}")
    print(f"Sheet range: {sheet_range}")
    print()

    # Extract sheet ID and read data
    sheet_id = extract_sheet_id(sheet_url)
    print("🔧 Reading data from Google Sheet...")
    rows = read_sheet_data(creds, sheet_id, sheet_range)
    print()

    # Load to BigQuery
    print("🔧 Loading data to BigQuery...")
    inserted = load_to_bigquery(creds, rows)
    print()

    print("=" * 60)
    print(f"✅ Successfully loaded {inserted} rows into `{SHEET_TABLE}`")
    print()
    print("Next steps:")
    print("1. Verify the data: SELECT * FROM `{}.{}.{}` LIMIT 10;".format(
        PROJECT_ID, DATASET, SHEET_TABLE))
    print("2. Update sql/01_stg_workouts.sql to read from `sheet_workouts`")
    print("   instead of the external `Fitness OptiMax` table")
    print("3. Redeploy views: python deploy_views.py")
    print("4. Delete the external table (optional):")
    print(f"   bq rm {DATASET}.\"Fitness OptiMax\"")
    print("=" * 60)


if __name__ == "__main__":
    main()
