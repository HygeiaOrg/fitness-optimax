import logging
import os
import subprocess
import sys

import google.auth
import google.auth.credentials
from google.api_core import exceptions as gcloud_exceptions
from google.auth import impersonated_credentials
from google.cloud import bigquery
from google.oauth2.credentials import Credentials

from api.errors import BigQueryAuthError, BigQueryQueryError, DriveScopeError

logger = logging.getLogger("optimax.bq")

# We force the keyring backend to null to avoid hanging on keyring prompts
os.environ["PYTHON_KEYRING_BACKEND"] = "keyring.backends.null.Keyring"

PROJECT_ID = os.environ.get("BQ_PROJECT_ID", "gen-lang-client-0937519537")
DATASET = os.environ.get("BQ_DATASET", "Optimmax")

BIGQUERY_SCOPE = "https://www.googleapis.com/auth/bigquery"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly"

# BigQuery needs Drive scope to access Google Sheets external tables
SCOPES = [BIGQUERY_SCOPE, DRIVE_SCOPE]

# Cloud Run's metadata server only ever mints `cloud-platform` tokens, and Drive
# is not covered by that scope. Asking google.auth for the Drive scope therefore
# does NOT give us one — queries that touch the Sheets-backed external table come
# back as "Permission denied while getting Drive credentials". The supported way
# out is for the runtime service account to impersonate itself with the Drive
# scope attached, which needs roles/iam.serviceAccountTokenCreator on itself.
DRIVE_ERROR_MARKERS = (
    "drive credentials",
    "drive.readonly",
    "access denied: bigquery bigquery: permission denied while getting drive",
)


def _looks_like_drive_error(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered for marker in DRIVE_ERROR_MARKERS)


class BQClient:
    _instance = None

    def __new__(cls):
        # NOTE: only cache the singleton once it is fully initialised. Previously
        # the instance was cached *before* _init_client() ran, so one failed cold
        # start left a permanently broken client (no `.client` attribute) and
        # every later request 500'd until the revision was redeployed.
        if cls._instance is None:
            instance = super(BQClient, cls).__new__(cls)
            instance._init_client()
            cls._instance = instance
        return cls._instance

    @classmethod
    def reset(cls):
        """Drop the cached client so the next request re-authenticates."""
        cls._instance = None

    def _init_client(self):
        self.project_id = PROJECT_ID
        self.dataset = DATASET
        self.auth_mode = "unknown"
        self.service_account_email = None
        self.credential_scopes = None
        self._impersonated_client = None

        try:
            # Use Application Default Credentials (ADC) with Drive scope. On a
            # developer machine (gcloud auth application-default login --scopes=...)
            # this really does carry Drive; on Cloud Run it silently will not.
            credentials, _ = google.auth.default(scopes=SCOPES)
            self.credentials = credentials
            self.client = bigquery.Client(project=self.project_id, credentials=credentials)
            self.auth_mode = f"adc:{type(credentials).__name__}"
            self.credential_scopes = list(getattr(credentials, "scopes", None) or [])
            self.service_account_email = self._resolve_service_account(credentials)
            logger.info(
                "BigQuery client ready (mode=%s, sa=%s, scopes=%s)",
                self.auth_mode, self.service_account_email, self.credential_scopes,
            )
            return
        except Exception as adc_error:  # noqa: BLE001 - we retry with gcloud below
            logger.warning("ADC authentication failed: %s", adc_error)

        # Fallback for local development using gcloud if ADC is not set up
        env = os.environ.copy()
        try:
            result = subprocess.run(
                ["gcloud", "auth", "print-access-token", "--quiet"],
                capture_output=True, text=True, stdin=subprocess.DEVNULL, env=env,
            )
            if result.returncode != 0:
                print(f"Error getting gcloud token: {result.stderr}", file=sys.stderr)
                raise BigQueryAuthError(
                    "Could not authenticate to BigQuery via ADC or gcloud.",
                    hint=f"gcloud said: {result.stderr.strip()[:300]}",
                )
            self.credentials = Credentials(result.stdout.strip())
            self.client = bigquery.Client(project=self.project_id, credentials=self.credentials)
            self.auth_mode = "gcloud-cli"
            logger.info("BigQuery client ready (mode=%s)", self.auth_mode)
        except FileNotFoundError as exc:
            raise BigQueryAuthError(
                "Cannot authenticate to BigQuery: no Application Default Credentials and gcloud is not installed.",
                hint="On Cloud Run, check the service account attached to the revision.",
                cause=exc,
            ) from exc

    @staticmethod
    def _resolve_service_account(credentials) -> str | None:
        for attribute in ("service_account_email", "signer_email"):
            value = getattr(credentials, attribute, None)
            if isinstance(value, str) and "@" in value:
                return value
        return os.environ.get("RUNTIME_SERVICE_ACCOUNT")

    def _drive_scoped_client(self):
        """Build (once) a BigQuery client whose token carries the Drive scope."""
        if self._impersonated_client is not None:
            return self._impersonated_client

        principal = os.environ.get("IMPERSONATE_SERVICE_ACCOUNT") or self.service_account_email
        if not principal:
            return None

        try:
            source, _ = google.auth.default()
            drive_credentials = impersonated_credentials.Credentials(
                source_credentials=source,
                target_principal=principal,
                target_scopes=SCOPES,
                lifetime=3600,
            )
            self._impersonated_client = bigquery.Client(
                project=self.project_id, credentials=drive_credentials
            )
            logger.info("Built Drive-scoped client by impersonating %s", principal)
            return self._impersonated_client
        except Exception as exc:  # noqa: BLE001 - fallback is best-effort
            logger.warning("Could not impersonate %s for Drive scope: %s", principal, exc)
            return None

    def query(self, query: str, job_config: bigquery.QueryJobConfig | None = None):
        """Run a query, translating BigQuery failures into explainable errors."""
        try:
            return self.client.query(query, job_config=job_config).result()
        except gcloud_exceptions.GoogleAPIError as exc:
            message = str(exc)
            if not _looks_like_drive_error(message):
                raise BigQueryQueryError(
                    f"BigQuery query failed: {message}", cause=exc
                ) from exc

            logger.warning("Drive-scope failure, retrying with impersonated credentials: %s", message)
            drive_client = self._drive_scoped_client()
            if drive_client is None:
                raise DriveScopeError(
                    "BigQuery cannot read the Google Sheet behind `stg_workouts`: "
                    f"{message}",
                    hint=(
                        "Cloud Run tokens only carry the cloud-platform scope, which excludes Drive. "
                        f"Grant roles/iam.serviceAccountTokenCreator on {self.service_account_email or 'the runtime service account'} "
                        "to itself so it can mint a Drive-scoped token, and share the source Google Sheet with that account."
                    ),
                    cause=exc,
                ) from exc

            try:
                return drive_client.query(query, job_config=job_config).result()
            except gcloud_exceptions.GoogleAPIError as retry_exc:
                raise DriveScopeError(
                    "BigQuery still cannot read the Google Sheet after impersonation: "
                    f"{retry_exc}",
                    hint=(
                        f"Share the source Google Sheet with {os.environ.get('IMPERSONATE_SERVICE_ACCOUNT') or self.service_account_email} "
                        "and confirm it holds roles/iam.serviceAccountTokenCreator on itself."
                    ),
                    cause=retry_exc,
                ) from retry_exc

    def auth_info(self) -> dict:
        """Non-secret description of how this instance authenticated."""
        return {
            "project_id": self.project_id,
            "dataset": self.dataset,
            "auth_mode": self.auth_mode,
            "service_account": self.service_account_email,
            "credential_scopes": self.credential_scopes,
            "has_drive_scope": bool(self.credential_scopes and DRIVE_SCOPE in self.credential_scopes),
        }
