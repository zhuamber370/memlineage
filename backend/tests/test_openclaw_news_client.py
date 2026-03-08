from pathlib import Path
import sys


repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))

from skill.openclaw_skill import KmsClient  # noqa: E402


def test_kms_client_list_and_get_news_delegate_to_news_endpoints():
    client = KmsClient(base_url="http://localhost:8000", api_key="dummy")
    calls: list[tuple[str, dict | None]] = []

    def fake_get(path: str, params=None):
        calls.append((path, params))
        return {"ok": True}

    client._get = fake_get  # type: ignore[method-assign]

    listed = client.list_news(page=1, page_size=20, status="new", q="openai")
    detail = client.get_news("nws_123")

    assert listed == {"ok": True}
    assert detail == {"ok": True}
    assert calls == [
        ("/api/v1/news", {"page": 1, "page_size": 20, "status": "new", "q": "openai"}),
        ("/api/v1/news/nws_123", None),
    ]


def test_kms_client_propose_capture_news_batch_expands_create_news_actions():
    client = KmsClient(base_url="http://localhost:8000", api_key="dummy")
    captured: dict = {}

    def fake_propose_changes(*, actions, actor, tool="openclaw-skill"):
        captured["actions"] = actions
        captured["actor"] = actor
        captured["tool"] = tool
        return {"change_set_id": "chg_news"}

    client.propose_changes = fake_propose_changes  # type: ignore[method-assign]

    out = client.propose_capture_news_batch(
        items=[
            {
                "title": "OpenAI robotics lead resigns",
                "summary": "summary",
                "opportunity": "opportunity",
                "risk": "risk",
                "primary_source_url": "https://example.com/primary",
                "reference_urls": ["https://example.com/ref"],
                "published_at": "2026-03-07T10:00:00Z",
                "captured_at": "2026-03-08T08:00:00Z",
                "tags": ["ai"],
                "raw_payload_json": {"id": "evt_1"},
            }
        ],
        actor={"type": "agent", "id": "openclaw"},
    )

    assert out["change_set_id"] == "chg_news"
    assert captured["tool"] == "openclaw-skill"
    assert captured["actions"][0]["type"] == "create_news"
    payload = captured["actions"][0]["payload"]
    assert payload["sources"] == [
        {"role": "primary", "url": "https://example.com/primary"},
        {"role": "reference", "url": "https://example.com/ref"},
    ]
