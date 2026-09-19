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
import google.auth
import google.auth.exceptions
from google.cloud import bigquery
from google.oauth2.credentials import Credentials

os.environ["PYTHON_KEYRING_BACKEND"] = "keyring.backends.null.Keyring"

PROJECT_ID = "gen-lang-client-0937519537"
SQL_DIR = Path(__file__).parent / "sql"

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
]


def get_client():
    """Create a BigQuery client.

    Tries Application Default Credentials first (`gcloud auth application-default
    login`, a service account key in GOOGLE_APPLICATION_CREDENTIALS, or the
    metadata server) and only falls back to shelling out to the gcloud binary.
    That way the script still works on a machine where the gcloud CLI is not
    installed but credentials are available.
    """
    try:
        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/bigquery"]
        )
        print("Auth: Application Default Credentials")
        return bigquery.Client(project=PROJECT_ID, credentials=credentials)
    except google.auth.exceptions.DefaultCredentialsError:
        pass

    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token", "--quiet"],
            capture_output=True, text=True, stdin=subprocess.DEVNULL,
            env=os.environ.copy(),
        )
    except FileNotFoundError:
        print(
            "ERROR: no credentials found.\n"
            "  Either install the Google Cloud CLI and run:\n"
            "      gcloud auth application-default login\n"
            "  or point GOOGLE_APPLICATION_CREDENTIALS at a service account key file."
        )
        sys.exit(1)

    if result.returncode != 0:
        print(f"Error getting gcloud token: {result.stderr}")
        sys.exit(1)

    print("Auth: gcloud access token")
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

    # Non-interactive by default: keep going after a failure and report a
    # summary at the end. A partial deployment used to be easy to miss, which
    # is how the dashboard ended up querying a view that was never created.
    interactive = "--interactive" in sys.argv and sys.stdin.isatty()

    client = get_client()
    print("✅ BigQuery client authenticated.\n")

    failures = []

    for filename in SQL_FILES:
        filepath = SQL_DIR / filename
        if not filepath.exists():
            print(f"⚠️  Skipping {filename} (file not found)")
            failures.append((filename, "file not found"))
            continue

        print(f"🔧 Deploying {filename}...")
        try:
            execute_sql_file(client, filepath)
            print("   ✅ Done.\n")
        except Exception as e:
            print(f"   ❌ FAILED: {e}\n")
            failures.append((filename, str(e).split("\n")[0]))
            if interactive:
                try:
                    if input("   Continue? (y/n): ").strip().lower() != "y":
                        print("Deployment aborted.")
                        sys.exit(1)
                except EOFError:
                    pass

    print("=" * 60)
    if failures:
        print(f"❌ Deployment INCOMPLETE — {len(failures)} of {len(SQL_FILES)} layers failed:")
        for filename, reason in failures:
            print(f"   • {filename}: {reason}")
        print()
        print("Later layers build on earlier ones, so fix the FIRST failure above;")
        print("the rest usually follow from it.")
        print("=" * 60)
        sys.exit(1)

    # The dashboard reads this one view. Confirm it actually exists and
    # answers, rather than assuming the CREATE statements worked.
    print("🔎 Verifying `workout_targets` (the view the dashboard reads)...")
    try:
        rows = list(
            client.query(
                f"SELECT COUNT(*) AS n FROM `{PROJECT_ID}.Optimmax.workout_targets`"
            ).result()
        )
        print(f"   ✅ workout_targets is queryable — {rows[0].n} exercise groups.\n")
    except Exception as e:
        print(f"   ❌ workout_targets is NOT queryable: {e}\n")
        sys.exit(1)

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
