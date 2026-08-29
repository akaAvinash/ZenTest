from utils.api_client import ApiClient

client = ApiClient()


def test_health_check_endpoint_reachable():
    """API-TC01: GET /api/health returns 200 with a JSON body confirming
    the API is running. (The manual test case PDF references GET / for
    this, which was true before the frontend was mounted at / — the real
    health check now lives at /api/health.)"""
    res = client.health()
    assert res.status_code == 200
    assert "message" in res.json()
