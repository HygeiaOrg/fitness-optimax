#!/usr/bin/env python3
"""
Deploy all BigQuery views and config tables for Fitness OptiMax SPC pipeline.
Runs SQL files in order from the sql/ directory.

Usage:
    PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring .venv/bin/python deploy_views.py
"""
import os
import subprocess
import sys
from pathlib import Path
from google.cloud import bigquery
from google.oauth2.credentials import Credentials

os.environ["PYTHON_KEYRING_BACKEND"] = "keyring.backends.null.Keyring"

PROJECT_ID = "gen-lang-client-0937519537"
SQL_DIR = Path(__file__).parent / "sql"

# Ordered list of SQL files to execute
SQL_FILES = [
    "01_stg_workouts.sql",
    "02_workout_metrics.sql",
    "03_spc_rolling_averages.sql",
    "04_spc_charts.sql",
    "05a_training_goals_table.sql",
    "05b_exercise_taxonomy_table.sql",
    "06_rpe_calibration.sql",
    "07_plateau_detection.sql",
    "08_workout_targets.sql",
]


def get_client():
    """Create a BigQuery client using gcloud access token."""
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


def execute_sql_file(client, filepath):
    """Execute a SQL file containing one or more statements."""
    sql = filepath.read_text()

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
            print(f"   ❌ FAILED: {e}\n")
            user_input = input("   Continue? (y/n): ").strip().lower()
            if user_input != "y":
                print("Deployment aborted.")
                sys.exit(1)

    print("=" * 60)
    print("🎉 Deployment complete!")
    print()
    print("Validation queries you can run:")
    print(f"  SELECT * FROM `{PROJECT_ID}.Optimmax.stg_workouts` LIMIT 5;")
    print(f"  SELECT * FROM `{PROJECT_ID}.Optimmax.spc_charts` WHERE exercise_group = 'Upper Body, Chest' ORDER BY session_rank LIMIT 10;")
    print(f"  SELECT * FROM `{PROJECT_ID}.Optimmax.rpe_calibration` WHERE rpe IS NOT NULL ORDER BY session_rank LIMIT 10;")
    print(f"  SELECT * FROM `{PROJECT_ID}.Optimmax.plateau_detection` WHERE is_plateau = TRUE;")
    print("=" * 60)


if __name__ == "__main__":
    main()
