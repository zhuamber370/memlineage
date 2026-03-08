from tests.helpers import make_client, uniq


def _payload(marker: str, **extra) -> dict:
    payload = {
        "title": f"OpenAI news {marker}",
        "summary": f"summary {marker}",
        "opportunity": f"opportunity {marker}",
        "risk": f"risk {marker}",
        "published_at": "2026-03-07T10:00:00Z",
        "captured_at": "2026-03-08T08:00:00Z",
        "tags": ["ai", "governance"],
        "sources": [
            {"role": "primary", "url": f"https://example.com/{marker}/primary"},
            {"role": "reference", "url": f"https://example.com/{marker}/reference-a"},
            {"role": "reference", "url": f"https://example.com/{marker}/reference-b"},
        ],
        "raw_payload_json": {"marker": marker},
    }
    payload.update(extra)
    return payload


def test_create_get_and_delete_news():
    client = make_client()
    marker = uniq("news_create")

    created = client.post("/api/v1/news", json=_payload(marker))
    assert created.status_code == 201, created.text
    body = created.json()
    news_id = body["id"]
    assert body["title"] == f"OpenAI news {marker}"
    assert body["status"] == "new"
    assert len(body["sources"]) == 3
    assert body["sources"][0]["role"] == "primary"
    assert "topic_id" not in body
    assert "links" not in body

    fetched = client.get(f"/api/v1/news/{news_id}")
    assert fetched.status_code == 200, fetched.text
    fetched_body = fetched.json()
    assert fetched_body["id"] == news_id
    assert fetched_body["raw_payload_json"] == {"marker": marker}
    assert "topic_id" not in fetched_body
    assert "links" not in fetched_body

    deleted = client.delete(f"/api/v1/news/{news_id}")
    assert deleted.status_code == 204, deleted.text

    missing = client.get(f"/api/v1/news/{news_id}")
    assert missing.status_code == 404, missing.text


def test_list_news_filters_by_status_and_query_only():
    client = make_client()
    keep_marker = uniq("news_keep")
    archive_marker = uniq("news_archive")

    keep = client.post(
        "/api/v1/news",
        json=_payload(
            keep_marker,
            published_at="2026-03-07T10:00:00Z",
            captured_at="2026-03-08T08:00:00Z",
        ),
    )
    archive_me = client.post(
        "/api/v1/news",
        json=_payload(
            archive_marker,
            published_at="2026-03-07T11:00:00Z",
            captured_at="2026-03-08T09:00:00Z",
        ),
    )
    assert keep.status_code == 201, keep.text
    assert archive_me.status_code == 201, archive_me.text

    archived = client.post(f"/api/v1/news/{archive_me.json()['id']}/archive")
    assert archived.status_code == 200, archived.text

    active_list = client.get(f"/api/v1/news?page=1&page_size=100&status=new&q={keep_marker}")
    assert active_list.status_code == 200, active_list.text
    active_items = active_list.json()["items"]
    assert len(active_items) == 1
    assert active_items[0]["id"] == keep.json()["id"]

    archived_list = client.get(f"/api/v1/news?page=1&page_size=100&status=archived&q={archive_marker}")
    assert archived_list.status_code == 200, archived_list.text
    archived_items = archived_list.json()["items"]
    assert len(archived_items) == 1
    assert archived_items[0]["id"] == archive_me.json()["id"]


def test_patch_news_updates_content_management_fields_and_sources():
    client = make_client()
    marker = uniq("news_patch")

    created = client.post("/api/v1/news", json=_payload(marker))
    assert created.status_code == 201, created.text
    news_id = created.json()["id"]

    patched = client.patch(
        f"/api/v1/news/{news_id}",
        json={
            "title": f"updated {marker}",
            "summary": f"updated summary {marker}",
            "opportunity": f"updated opportunity {marker}",
            "risk": f"updated risk {marker}",
            "published_at": "2026-03-09T10:00:00Z",
            "captured_at": "2026-03-09T11:00:00Z",
            "tags": ["robotics"],
            "status": "tracking",
            "sources": [
                {"role": "primary", "url": f"https://example.com/{marker}/updated-primary"},
                {"role": "reference", "url": f"https://example.com/{marker}/updated-reference"},
            ],
        },
    )
    assert patched.status_code == 200, patched.text
    body = patched.json()
    assert body["title"] == f"updated {marker}"
    assert body["status"] == "tracking"
    assert body["tags"] == ["robotics"]
    assert len(body["sources"]) == 2
    assert body["sources"][0]["url"].endswith("updated-primary")
    assert "topic_id" not in body
    assert "links" not in body
