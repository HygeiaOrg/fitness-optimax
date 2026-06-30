from typing import Generator
from api.services.bq_client import BQClient

def get_bq_client() -> Generator[BQClient, None, None]:
    """Dependency to provide the BigQuery client to endpoints."""
    yield BQClient()
