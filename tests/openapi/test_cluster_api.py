import requests

from .helpers.settings import QDRANT_HOST
from .helpers.helpers import qdrant_host_headers


def test_cluster_recover_standalone_returns_4xx():
    """In standalone (non-distributed) mode, POST /cluster/recover is not applicable
    and must return a 4xx client error, not a 5xx server error."""
    response = requests.post(
        url=f"{QDRANT_HOST}/cluster/recover",
        headers=qdrant_host_headers(),
    )

    assert 400 <= response.status_code < 500, (
        f"Expected a 4xx status in standalone mode, got {response.status_code}: {response.text}"
    )

    error = response.json()["status"]["error"]
    assert "standalone mode" in error
