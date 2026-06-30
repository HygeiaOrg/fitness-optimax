from google.cloud import bigquery
from google.oauth2.credentials import Credentials
import subprocess
import os
import sys

# We force the keyring backend to null to avoid hanging on keyring prompts
os.environ["PYTHON_KEYRING_BACKEND"] = "keyring.backends.null.Keyring"

class BQClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BQClient, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        # We use gcloud auth print-access-token to get a token
        env = os.environ.copy()
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token", "--quiet"],
            capture_output=True, text=True, stdin=subprocess.DEVNULL, env=env
        )
        if result.returncode != 0:
            print(f"Error getting gcloud token: {result.stderr}", file=sys.stderr)
            raise Exception("Could not authenticate BigQuery client via gcloud")
        
        credentials = Credentials(result.stdout.strip())
        self.project_id = "gen-lang-client-0937519537"
        self.client = bigquery.Client(project=self.project_id, credentials=credentials)

    def query(self, query: str):
        job = self.client.query(query)
        return job.result()
