from tests.helpers import make_client, uniq


def _commit_change(client, change_set_id: str) -> dict:
    resp = client.post(
        f"/api/v1/changes/{change_set_id}/commit",
        json={
            "approved_by": {"type": "user", "id": "usr_local"},
            "client_request_id": f"idem-{uniq('commit')}",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _news_payload(marker: str, **extra) -> dict:
    payload = {
        "title": f"news title {marker}",
        "summary": f"news summary {marker}",
        "opportunity": f"opportunity {marker}",
        "risk": f"risk {marker}",
        "published_at": "2026-03-07T10:00:00Z",
        "captured_at": "2026-03-08T08:00:00Z",
        "tags": ["ai"],
        "sources": [
            {"role": "primary", "url": f"https://example.com/{marker}/primary"},
            {"role": "reference", "url": f"https://example.com/{marker}/reference"},
        ],
        "raw_payload_json": {"marker": marker},
    }
    payload.update(extra)
    return payload


def test_create_news_batch_action_commit_and_undo():
    client = make_client()
    marker_a = uniq("news_batch_a")
    marker_b = uniq("news_batch_b")

    dry = client.post(
        "/api/v1/changes/dry-run",
        json={
            "actions": [
                {"type": "create_news", "payload": _news_payload(marker_a)},
                {"type": "create_news", "payload": _news_payload(marker_b)},
            ],
            "actor": {"type": "agent", "id": "openclaw"},
            "tool": "openclaw-skill",
        },
    )
    assert dry.status_code == 200, dry.text
    body = dry.json()
    assert body["summary"]["news_create"] == 2
    _commit_change(client, body["change_set_id"])

    listed = client.get(f"/api/v1/news?page=1&page_size=100&q={marker_a}")
    assert listed.status_code == 200, listed.text
    assert any(item["title"] == f"news title {marker_a}" for item in listed.json()["items"])

    listed_b = client.get(f"/api/v1/news?page=1&page_size=100&q={marker_b}")
    assert listed_b.status_code == 200, listed_b.text
    assert any(item["title"] == f"news title {marker_b}" for item in listed_b.json()["items"])

    undo = client.post(
        "/api/v1/commits/undo-last",
        json={"requested_by": {"type": "user", "id": "usr_local"}, "reason": "undo news batch"},
    )
    assert undo.status_code == 200, undo.text

    after_undo = client.get(f"/api/v1/news?page=1&page_size=100&q={marker_a}")
    assert after_undo.status_code == 200
    assert all(item["title"] != f"news title {marker_a}" for item in after_undo.json()["items"])
