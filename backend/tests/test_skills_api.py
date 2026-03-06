import json
from pathlib import Path

import pytest

from tests.helpers import make_client


class _FakeRunResult:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _mock_cli_success(monkeypatch: pytest.MonkeyPatch):
    def _fake_run(cmd, *args, **kwargs):
        tokens = [str(part) for part in cmd]
        if tokens[:2] == ["openclaw", "--version"]:
            return _FakeRunResult(stdout="OpenClaw 2026.2.26")
        if tokens[:2] == ["codex", "--version"]:
            return _FakeRunResult(stdout="Codex CLI 0.0.0")
        if tokens[:3] == ["openclaw", "skills", "info"]:
            return _FakeRunResult(stdout='{"eligible": true}')
        if tokens[:3] == ["openclaw", "skills", "check"]:
            return _FakeRunResult(stdout='{"ok": true}')
        return _FakeRunResult(stdout="")

    monkeypatch.setattr("src.services.skill_service.subprocess.run", _fake_run)


def _mock_cli_openclaw_env_missing(monkeypatch: pytest.MonkeyPatch):
    def _fake_run(cmd, *args, **kwargs):
        tokens = [str(part) for part in cmd]
        if tokens[:2] == ["openclaw", "--version"]:
            return _FakeRunResult(stdout="OpenClaw 2026.2.26")
        if tokens[:2] == ["codex", "--version"]:
            return _FakeRunResult(stdout="Codex CLI 0.0.0")
        if tokens[:3] == ["openclaw", "skills", "info"]:
            return _FakeRunResult(
                stdout=json.dumps(
                    {
                        "name": "memlineage",
                        "eligible": False,
                        "requirements": {"env": ["KMS_BASE_URL", "KMS_API_KEY"]},
                        "missing": {"env": ["KMS_BASE_URL", "KMS_API_KEY"]},
                    }
                )
            )
        if tokens[:3] == ["openclaw", "skills", "check"]:
            return _FakeRunResult(stdout='{"ok": false}')
        return _FakeRunResult(stdout="")

    monkeypatch.setattr("src.services.skill_service.subprocess.run", _fake_run)


def _read_version(package_json: Path) -> str:
    payload = json.loads(package_json.read_text(encoding="utf-8"))
    return str(payload.get("version", "")).strip()


def _configure_manual_path(client, agent: str, path: Path):
    resp = client.put(f"/api/v1/skills/{agent}/config", json={"configured_path": str(path)})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["manual_path_configured"] is True
    assert body["detect_status"] == "unknown"
    assert "configured_path" not in body
    return body


def _detect(client, agent: str):
    resp = client.post(f"/api/v1/skills/{agent}/detect")
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture
def isolated_skill_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "skills_runtime.sqlite"
    monkeypatch.setenv("AFKMS_DATABASE_URL", f"sqlite:///{db_path}")

    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    openclaw_home = home / ".openclaw"
    openclaw_home.mkdir(parents=True, exist_ok=True)
    workspace = openclaw_home / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    codex_home = home / ".codex"
    codex_home.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("OPENCLAW_WORKSPACE_DIR", raising=False)
    monkeypatch.delenv("OPENCLAW_CONFIG_PATH", raising=False)
    monkeypatch.delenv("CODEX_HOME", raising=False)

    return {
        "home": home,
        "workspace": workspace,
        "codex_home": codex_home,
        "codex_skill_dir": codex_home / "skills" / "memlineage",
        "codex_disabled_dir": codex_home / "skills" / ".disabled" / "memlineage",
        "openclaw_skill_dir": workspace / "skills" / "memlineage",
    }


def test_list_skill_targets_schema(isolated_skill_env):
    client = make_client()
    resp = client.get("/api/v1/skills")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert "items" in body
    agents = {item["agent"] for item in body["items"]}
    assert agents == {"openclaw", "codex"}

    codex = next(item for item in body["items"] if item["agent"] == "codex")
    for field in [
        "agent",
        "detect_status",
        "needs_manual_path",
        "manual_path_configured",
        "path_mode",
        "runtime_status",
        "runtime_version",
        "skill_status",
        "skill_enabled",
        "last_checked_at",
        "last_error",
        "last_checks",
        "last_warnings",
        "bundled_version",
        "installed_version",
        "update_available",
    ]:
        assert field in codex

    assert "configured_path" not in codex
    assert "target_dir" not in codex
    assert codex["runtime_status"] in {"unknown", "installed", "not_installed"}
    assert codex["skill_status"] in {"unknown", "installed", "not_installed"}


def test_codex_detect_uses_default_path(isolated_skill_env, monkeypatch: pytest.MonkeyPatch):
    _mock_cli_success(monkeypatch)
    client = make_client()

    detected = _detect(client, "codex")
    assert detected["detect_status"] == "ready"
    assert detected["runtime_status"] == "installed"
    assert detected["skill_status"] == "not_installed"
    assert detected["path_mode"] == "auto"
    assert detected["needs_manual_path"] is False


def test_codex_detect_fallback_when_env_path_invalid(isolated_skill_env, monkeypatch: pytest.MonkeyPatch):
    _mock_cli_success(monkeypatch)
    client = make_client()

    monkeypatch.setenv("CODEX_HOME", str(isolated_skill_env["home"] / "missing-codex-home"))
    detected = _detect(client, "codex")

    assert detected["detect_status"] == "ready"
    assert detected["runtime_status"] == "installed"
    warning_codes = {item.get("code") for item in detected["last_warnings"]}
    assert "SKILL_ENV_PATH_INVALID" in warning_codes


def test_openclaw_manual_path_fallback(isolated_skill_env, monkeypatch: pytest.MonkeyPatch):
    _mock_cli_success(monkeypatch)
    client = make_client()

    workspace: Path = isolated_skill_env["workspace"]
    workspace.rmdir()
    monkeypatch.setenv("OPENCLAW_WORKSPACE_DIR", str(isolated_skill_env["home"] / "bad-openclaw-workspace"))

    failed = _detect(client, "openclaw")
    assert failed["detect_status"] == "failed"
    assert failed["runtime_status"] == "installed"
    assert failed["needs_manual_path"] is True

    manual_workspace = isolated_skill_env["home"] / "custom-openclaw-workspace"
    manual_workspace.mkdir(parents=True, exist_ok=True)
    _configure_manual_path(client, "openclaw", manual_workspace)

    ready = _detect(client, "openclaw")
    assert ready["detect_status"] == "ready"
    assert ready["runtime_status"] == "installed"
    assert ready["path_mode"] == "manual"
    assert ready["needs_manual_path"] is False


def test_codex_install_disable_enable_uninstall_roundtrip(isolated_skill_env, monkeypatch: pytest.MonkeyPatch):
    _mock_cli_success(monkeypatch)
    client = make_client()
    codex_skill_dir: Path = isolated_skill_env["codex_skill_dir"]
    codex_disabled_dir: Path = isolated_skill_env["codex_disabled_dir"]

    detected = _detect(client, "codex")
    assert detected["detect_status"] == "ready"

    install = client.post("/api/v1/skills/codex/install", json={"force": False})
    assert install.status_code == 200, install.text
    assert codex_skill_dir.is_dir()
    assert install.json()["status"]["skill_status"] == "installed"
    assert install.json()["status"]["skill_enabled"] is True

    disable = client.post("/api/v1/skills/codex/disable")
    assert disable.status_code == 200, disable.text
    assert not codex_skill_dir.exists()
    assert codex_disabled_dir.is_dir()
    assert disable.json()["status"]["skill_status"] == "installed"
    assert disable.json()["status"]["skill_enabled"] is False

    enable = client.post("/api/v1/skills/codex/enable")
    assert enable.status_code == 200, enable.text
    assert codex_skill_dir.is_dir()
    assert not codex_disabled_dir.exists()
    assert enable.json()["status"]["skill_enabled"] is True

    uninstall = client.delete("/api/v1/skills/codex")
    assert uninstall.status_code == 200, uninstall.text
    assert not codex_skill_dir.exists()
    assert uninstall.json()["status"]["skill_status"] == "not_installed"


def test_install_requires_detect_unless_forced(isolated_skill_env):
    client = make_client()

    blocked = client.post("/api/v1/skills/codex/install", json={"force": False})
    assert blocked.status_code == 422, blocked.text
    assert blocked.json()["error"]["code"] == "SKILL_DETECT_REQUIRED"

    forced = client.post("/api/v1/skills/codex/install", json={"force": True})
    assert forced.status_code == 200, forced.text
    assert forced.json()["status"]["skill_status"] == "installed"


def test_codex_version_and_update_after_detect(isolated_skill_env, monkeypatch: pytest.MonkeyPatch):
    _mock_cli_success(monkeypatch)
    client = make_client()
    codex_skill_dir: Path = isolated_skill_env["codex_skill_dir"]
    package_json = codex_skill_dir / "package.json"

    detected = _detect(client, "codex")
    assert detected["detect_status"] == "ready"

    install = client.post("/api/v1/skills/codex/install", json={"force": False})
    assert install.status_code == 200, install.text
    assert package_json.exists()

    payload = json.loads(package_json.read_text(encoding="utf-8"))
    payload["version"] = "0.0.1"
    package_json.write_text(json.dumps(payload), encoding="utf-8")

    version = client.get("/api/v1/skills/codex/version")
    assert version.status_code == 200, version.text
    body = version.json()
    assert body["update_available"] is True
    assert body["installed_version"] == "0.0.1"

    update = client.post("/api/v1/skills/codex/update", json={"force": False})
    assert update.status_code == 200, update.text
    updated = update.json()
    assert updated["update_available"] is False
    assert updated["installed_version"] == _read_version(package_json)


def test_health_warns_when_openclaw_cli_missing(isolated_skill_env, monkeypatch: pytest.MonkeyPatch):
    _mock_cli_success(monkeypatch)
    client = make_client()

    detected = _detect(client, "openclaw")
    assert detected["detect_status"] == "ready"

    install = client.post("/api/v1/skills/openclaw/install", json={"force": False})
    assert install.status_code == 200, install.text

    def _missing_openclaw(cmd, *args, **kwargs):
        tokens = [str(part) for part in cmd]
        if tokens and tokens[0] == "openclaw":
            raise FileNotFoundError("openclaw not found")
        return _FakeRunResult(stdout="")

    monkeypatch.setattr("src.services.skill_service.subprocess.run", _missing_openclaw)
    health = client.get("/api/v1/skills/openclaw/health")
    assert health.status_code == 200, health.text
    body = health.json()
    warning_codes = {item.get("code") for item in body["warnings"]}
    assert "SKILL_CLI_NOT_FOUND" in warning_codes


def test_health_warns_when_openclaw_gateway_launchd_env_missing(
    isolated_skill_env, monkeypatch: pytest.MonkeyPatch
):
    _mock_cli_openclaw_env_missing(monkeypatch)
    client = make_client()

    detected = _detect(client, "openclaw")
    assert detected["detect_status"] == "ready"

    install = client.post("/api/v1/skills/openclaw/install", json={"force": False})
    assert install.status_code == 200, install.text

    launch_agent = isolated_skill_env["home"] / "Library" / "LaunchAgents" / "ai.openclaw.gateway.plist"
    launch_agent.parent.mkdir(parents=True, exist_ok=True)
    launch_agent.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>ai.openclaw.gateway</string>
    <key>EnvironmentVariables</key>
    <dict>
      <key>PATH</key>
      <string>/usr/bin:/bin</string>
    </dict>
  </dict>
</plist>
""",
        encoding="utf-8",
    )

    health = client.get("/api/v1/skills/openclaw/health")
    assert health.status_code == 200, health.text
    body = health.json()
    warning = next(item for item in body["warnings"] if item["code"] == "SKILL_OPENCLAW_GATEWAY_ENV_MISSING")
    assert "LaunchAgent" in warning["message"]
    assert "KMS_BASE_URL" in warning["message"]
    assert warning["details"]["missing_env"] == ["KMS_BASE_URL", "KMS_API_KEY"]
    assert warning["details"]["launch_agent_path"].endswith("ai.openclaw.gateway.plist")


def test_invalid_skill_target_returns_validation_error(isolated_skill_env):
    client = make_client()
    resp = client.post("/api/v1/skills/unknown/install", json={"force": False})
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
