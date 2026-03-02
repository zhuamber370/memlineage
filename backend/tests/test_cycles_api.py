from tests.helpers import make_client


def test_cycles_endpoints_not_exposed():
    client = make_client()
    create = client.post("/api/v1/cycles", json={})
    assert create.status_code == 404
    listed = client.get("/api/v1/cycles")
    assert listed.status_code == 404
