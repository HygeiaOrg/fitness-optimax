#!/usr/bin/env python3
"""
Deploy all BigQuery views and config tables for Fitness OptiMax SPC pipeline.
Runs SQL files in order from the sql/ directory.

Usage:
    PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring .venv/bin/python deploy_views.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from google.api_core import exceptions as gcloud_exceptions
from google.cloud import bigquery
from google.oauth2.credentials import Credentials

os.environ["PYTHON_KEYRING_BACKEND"] = "keyring.backends.null.Keyring"

PROJECT_ID = "gen-lang-client-0937519537"
DATASET = "Optimmax"
SQL_DIR = Path(__file__).parent / "sql"
CONFIG_FILE = Path(__file__).parent / "config" / "bigquery.json"

# The workout log lives in a Google Sheet (Google Form responses). BigQuery reads
# it through an external table, which every view in sql/ is built on. It used to
# be created by hand in the console, so it could go missing without anyone
# noticing; it is now (re)created here from the URL in config/bigquery.json.
SHEET_TABLE = "Fitness OptiMax"
SHEET_COLUMNS = 8  # string_field_0 .. string_field_7, read by sql/01_stg_workouts.sql

# Ordered list of SQL files to execute
SQL_FILES = [
    "00_native_workouts_table.sql",
    "01_stg_workouts.sql",
    "02_workout_metrics.sql",
    "03_spc_rolling_averages.sql",
    "04_spc_charts.sql",
    "05a_training_goals_table.sql",
    "05b_exercise_taxonomy_table.sql",
    "06_rpe_calibration.sql",
    "07_plateau_detection.sql",
    "08_workout_targets.sql",
    "09_one_rep_maxes_table.sql",
]


def get_client():
    """Create a BigQuery client using gcloud access token.

    In CI (GitHub Actions with Workload Identity Federation) use Application
    Default Credentials with Drive scope as well, because 05a reads the
    Google-Sheet-backed source table. The sheet must be shared with the
    deployer service account.
    """
    if os.environ.get("CI") and os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        import google.auth

        creds, _ = google.auth.default(scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/drive.readonly",
        ])
        return bigquery.Client(project=PROJECT_ID, credentials=creds)

    env = os.environ.copy()
    result = subprocess.run(
        ["gcloud", "auth", "print-access-token", "--quiet"],
        capture_output=True, text=True, stdin=subprocess.DEVNULL, env=env
    )
    if result.returncode != 0:
        print(f"Error getting gcloud token: {result.stderr}")
        sys.exit(1)
    credentials = Credentials(result.stdout.strip())
    return bigquery.Client(project=PROJECT_ID, credentials=credentials)


def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def ensure_sheet_table(client):
    """Make sure the external table over the workout log Sheet exists."""
    table_id = f"{PROJECT_ID}.{DATASET}.{SHEET_TABLE}"
    try:
        client.get_table(table_id)
        print(f"    `{SHEET_TABLE}` already exists.")
        return
    except gcloud_exceptions.NotFound:
        pass

    config = load_config()
    url = os.environ.get("WORKOUT_LOG_SHEET_URL") or config.get("workout_log_sheet_url")
    if not url:
        raise RuntimeError(
            f"`{SHEET_TABLE}` is missing and no workout log Sheet URL is configured. "
            f"Set workout_log_sheet_url in {CONFIG_FILE.relative_to(Path(__file__).parent)} "
            "(or the WORKOUT_LOG_SHEET_URL environment variable) and re-run."
        )

    external = bigquery.ExternalConfig("GOOGLE_SHEETS")
    external.source_uris = [url]
    external.autodetect = False
    # The header row is kept and filtered out in stg_workouts (string_field_0 != 'Timestamp').
    external.options.skip_leading_rows = 0
    # Read the named tab (e.g. "Form responses 1"); without it BigQuery reads the first tab.
    if config.get("workout_log_sheet_range"):
        external.options.range = config["workout_log_sheet_range"]
    # A column added to the form later must not break every query.
    external.ignore_unknown_values = True
    table = bigquery.Table(table_id, schema=[
        bigquery.SchemaField(f"string_field_{i}", "STRING") for i in range(SHEET_COLUMNS)
    ])
    table.external_data_configuration = external
    client.create_table(table, exists_ok=True)
    print(f"    Created `{SHEET_TABLE}` over {url}")


def execute_sql_file(client, filepath):
    """Execute a SQL file containing one or more statements."""
    # Drop full-line `--` comments first: a semicolon inside a comment would
    # otherwise split off a comment-only fragment, which BigQuery rejects as
    # "Unexpected end of statement".
    sql = "\n".join(
        line for line in filepath.read_text().splitlines()
        if not line.lstrip().startswith("--")
    )

    # Split on semicolons for files with multiple statements (config tables)
    statements = [s.strip() for s in sql.split(";") if s.strip()]

    for i, statement in enumerate(statements):
        try:
            job = client.query(statement)
            job.result()  # Wait for completion
            if len(statements) > 1:
                print(f"    Statement {i+1}/{len(statements)} completed.")
        except Exception as e:
            # Config table inserts may fail if data already exists — that's OK
            if "Already Exists" in str(e) or "duplicate" in str(e).lower():
                print(f"    Statement {i+1} skipped (already exists).")
            else:
                raise


def main():
    print("=" * 60)
    print("Fitness OptiMax — BigQuery View Deployment")
    print("=" * 60)
    print(f"Project: {PROJECT_ID}")
    print(f"SQL Dir: {SQL_DIR}")
    print()

    client = get_client()
    print("✅ BigQuery client authenticated.\n")

    failed = []

    def handle_failure(step, error):
        print(f"   ❌ FAILED: {error}\n")
        failed.append(step)
        # No prompt in CI (no stdin): fail the deploy instead.
        user_input = "n" if os.environ.get("CI") else input("   Continue? (y/n): ").strip().lower()
        if user_input != "y":
            print("Deployment aborted.")
            sys.exit(1)

    print(f"🔧 Checking workout log Sheet table `{SHEET_TABLE}`...")
    try:
        ensure_sheet_table(client)
        print("   ✅ Done.\n")
    except Exception as e:
        handle_failure(f"Sheet table `{SHEET_TABLE}`", e)

    for filename in SQL_FILES:
        filepath = SQL_DIR / filename
        if not filepath.exists():
            print(f"⚠️  Skipping {filename} (file not found)")
            continue

        print(f"🔧 Deploying {filename}...")
        try:
            execute_sql_file(client, filepath)
            print(f"   ✅ Done.\n")
        except Exception as e:
            handle_failure(filename, e)

    print("=" * 60)
    if failed:
        print(f"⚠️  Deployment finished with {len(failed)} failed step(s):")
        for step in failed:
            print(f"   - {step}")
        print("Fix the errors above and re-run; every step is safe to repeat.")
        print("=" * 60)
        sys.exit(1)
    print("🎉 Deployment complete — all steps succeeded.")
    print()
    print("Validation queries you can run:")
    print(f"  SELECT * FROM `{PROJECT_ID}.Optimmax.stg_workouts` LIMIT 5;")
    print(f"  SELECT * FROM `{PROJECT_ID}.Optimmax.spc_charts` WHERE exercise_group = 'Upper Body, Chest' ORDER BY session_rank LIMIT 10;")
    print(f"  SELECT * FROM `{PROJECT_ID}.Optimmax.rpe_calibration` WHERE rpe IS NOT NULL ORDER BY session_rank LIMIT 10;")
    print(f"  SELECT * FROM `{PROJECT_ID}.Optimmax.plateau_detection` WHERE is_plateau = TRUE;")
    print("=" * 60)


if __name__ == "__main__":
    main()
