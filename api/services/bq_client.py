from google.cloud import bigquery
from google.oauth2.credentials import Credentials
import google.auth
import google.auth.credentials
import subprocess
import os
import sys

# We force the keyring backend to null to avoid hanging on keyring prompts
os.environ["PYTHON_KEYRING_BACKEND"] = "keyring.backends.null.Keyring"

# BigQuery needs Drive scope to access Google Sheets external tables
SCOPES = [
    "https://www.googleapis.com/auth/bigquery",
    "https://www.googleapis.com/auth/drive.readonly",
]

class BQClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BQClient, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        self.project_id = "gen-lang-client-0937519537"
        try:
            # Use Application Default Credentials (ADC) with Drive scope
            # This is native to Cloud Run and includes the drive.readonly scope
            # needed to query Google Sheets-backed external tables.
            credentials, project = google.auth.default(scopes=SCOPES)
            self.client = bigquery.Client(
                project=self.project_id, credentials=credentials
            )
        except Exception as e:
            # Fallback for local development using gcloud if ADC is not set up
            env = os.environ.copy()
            try:
                result = subprocess.run(
                    ["gcloud", "auth", "print-access-token", "--quiet"],
                    capture_output=True, text=True, stdin=subprocess.DEVNULL, env=env
                )
                if result.returncode != 0:
                    print(f"Error getting gcloud token: {result.stderr}", file=sys.stderr)
                    raise Exception("Could not authenticate BigQuery client via gcloud")
                
                credentials = Credentials(result.stdout.strip())
                self.client = bigquery.Client(project=self.project_id, credentials=credentials)
            except FileNotFoundError:
                raise Exception("Cannot authenticate BigQuery. ADC missing and gcloud not found.")

    def query(self, query: str):
        job = self.client.query(query)
        return job.result()
