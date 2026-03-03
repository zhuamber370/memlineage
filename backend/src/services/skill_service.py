from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.models import SkillRuntime

SKILL_NAME = "memlineage"
TARGET_AGENTS = ("openclaw", "codex")
REQUIRED_SKILL_FILES = ("SKILL.md", "index.js", "lib/client.js", "package.json")

RUNTIME_UNKNOWN = "unknown"
RUNTIME_INSTALLED = "installed"
RUNTIME_NOT_INSTALLED = "not_installed"

SKILL_UNKNOWN = "unknown"
SKILL_INSTALLED = "installed"
SKILL_NOT_INSTALLED = "not_installed"

PATH_NONE = "none"
PATH_AUTO = "auto"
PATH_MANUAL = "manual"


class SkillService:
    def __init__(self, db: Session):
        self.db = db
        # backend/src/services/skill_service.py -> repo root
        self.repo_root = Path(__file__).resolve().parents[3]
        self.source_dir = self.repo_root / "skills" / SKILL_NAME

    def list_status(self) -> List[Dict[str, Any]]:
        return [self.get_status(agent) for agent in TARGET_AGENTS]

    def get_status(self, agent: str) -> Dict[str, Any]:
        self._ensure_supported_agent(agent)
        runtime = self._get_or_create_runtime(agent)
        root_dir = self._resolved_root_dir(runtime)

        installed = False
        enabled = False
        installed_version = None
        if root_dir is not None:
            paths = self._paths_for(agent, root_dir)
            target_installed = paths["target_dir"].is_dir()
            disabled_installed = paths["disabled_dir"].is_dir()
            installed = target_installed or disabled_installed
            enabled = target_installed and not disabled_installed
            if target_installed:
                installed_version = self._read_skill_version(paths["target_dir"])
            elif disabled_installed:
                installed_version = self._read_skill_version(paths["disabled_dir"])

        bundled_version = self._read_skill_version(self.source_dir)
        update_available = bool(
            bundled_version and installed_version and bundled_version != installed_version
        )

        skill_status = SKILL_UNKNOWN
        if root_dir is not None:
            skill_status = SKILL_INSTALLED if installed else SKILL_NOT_INSTALLED

        runtime_status = (runtime.runtime_status or RUNTIME_UNKNOWN).strip() or RUNTIME_UNKNOWN
        needs_manual_path = bool(
            runtime.detect_status == "failed"
            and runtime_status == RUNTIME_INSTALLED
            and root_dir is None
        )

        return {
            "agent": agent,
            "detect_status": runtime.detect_status,
            "needs_manual_path": needs_manual_path,
            "manual_path_configured": bool((runtime.configured_path or "").strip()),
            "path_mode": self._path_mode(runtime),
            "runtime_status": runtime_status,
            "runtime_version": runtime.runtime_version,
            "skill_status": skill_status,
            "skill_enabled": enabled,
            "last_checked_at": runtime.last_checked_at,
            "last_error": runtime.last_error,
            "last_checks": list(runtime.last_checks_json or []),
            "last_warnings": list(runtime.last_warnings_json or []),
            "bundled_version": bundled_version,
            "installed_version": installed_version,
            "update_available": update_available,
        }

    def configure_path(self, agent: str, configured_path: str) -> Dict[str, Any]:
        self._ensure_supported_agent(agent)
        runtime = self._get_or_create_runtime(agent)
        resolved = Path(configured_path).expanduser().resolve()
        runtime.configured_path = str(resolved)
        runtime.detect_status = "unknown"
        runtime.runtime_status = RUNTIME_UNKNOWN
        runtime.runtime_detected = False
        runtime.runtime_version = None
        runtime.resolved_root_path = None
        runtime.resolved_root_source = None
        runtime.last_error = None
        runtime.last_checks_json = []
        runtime.last_warnings_json = []
        runtime.last_checked_at = None
        self.db.add(runtime)
        self.db.commit()
        self.db.refresh(runtime)
        return self.get_status(agent)

    def detect(self, agent: str) -> Dict[str, Any]:
        self._ensure_supported_agent(agent)
        runtime = self._get_or_create_runtime(agent)

        checks: List[str] = []
        warnings: List[Dict[str, Any]] = []

        runtime_status, runtime_version = self._probe_runtime(agent, checks, warnings)
        resolved_root: Optional[Path] = None
        resolved_source: Optional[str] = None

        if runtime_status == RUNTIME_INSTALLED:
            auto_root = self._resolve_auto_root_for_detect(agent, checks, warnings)
            if auto_root is not None:
                resolved_root = auto_root
                resolved_source = PATH_AUTO
            else:
                manual_root = self._resolve_manual_root(runtime)
                if manual_root is not None and manual_root.is_dir():
                    resolved_root = manual_root
                    resolved_source = PATH_MANUAL
                    checks.append("root_source:manual")
                elif manual_root is not None:
                    warnings.append(
                        {
                            "code": "SKILL_MANUAL_PATH_INVALID",
                            "message": "Saved manual path is invalid. Please choose a valid path.",
                        }
                    )

            if resolved_root is None and not self._has_warning_code(warnings, "SKILL_PATH_NOT_FOUND"):
                warnings.append(
                    {
                        "code": "SKILL_PATH_NOT_FOUND",
                        "message": "Could not locate a valid runtime workspace. Please choose a manual path.",
                    }
                )
            if resolved_root is not None:
                warnings = [
                    item for item in warnings if item.get("code") != "SKILL_PATH_NOT_FOUND"
                ]

        runtime.detect_status = (
            "ready"
            if runtime_status == RUNTIME_INSTALLED and resolved_root is not None
            else "failed"
        )
        runtime.runtime_status = runtime_status
        runtime.runtime_detected = runtime_status == RUNTIME_INSTALLED
        runtime.runtime_version = runtime_version
        runtime.resolved_root_path = (
            str(resolved_root.resolve()) if resolved_root is not None else None
        )
        runtime.resolved_root_source = resolved_source
        runtime.last_error = warnings[0]["message"] if warnings else None
        runtime.last_checks_json = checks
        runtime.last_warnings_json = warnings
        runtime.last_checked_at = datetime.now(timezone.utc)
        self.db.add(runtime)
        self.db.commit()
        self.db.refresh(runtime)
        return self.get_status(agent)

    def install(self, agent: str, *, force: bool = False) -> Dict[str, Any]:
        self._ensure_supported_agent(agent)
        self._ensure_source_exists()
        runtime, root_dir, root_source = self._ensure_ready_for_write(agent, force=force)
        paths = self._paths_for(agent, root_dir)

        if not paths["root_dir"].exists():
            if force:
                paths["root_dir"].mkdir(parents=True, exist_ok=True)
            else:
                raise ValueError("SKILL_PATH_NOT_FOUND")

        paths["target_dir"].parent.mkdir(parents=True, exist_ok=True)
        if paths["target_dir"].exists():
            self._backup_existing(paths["target_dir"], paths["backup_root"])
        if paths["disabled_dir"].exists():
            shutil.rmtree(paths["disabled_dir"])

        shutil.copytree(self.source_dir, paths["target_dir"])
        self._persist_root_snapshot(runtime, root_dir, root_source)
        return self.get_status(agent)

    def uninstall(self, agent: str) -> Dict[str, Any]:
        self._ensure_supported_agent(agent)
        runtime, root_dir, _ = self._ensure_ready_for_write(agent, force=False)
        paths = self._paths_for(agent, root_dir)
        if paths["target_dir"].exists():
            shutil.rmtree(paths["target_dir"])
        if paths["disabled_dir"].exists():
            shutil.rmtree(paths["disabled_dir"])
        self._persist_root_snapshot(runtime, root_dir, runtime.resolved_root_source or PATH_AUTO)
        return self.get_status(agent)

    def disable(self, agent: str) -> Dict[str, Any]:
        self._ensure_supported_agent(agent)
        runtime, root_dir, _ = self._ensure_ready_for_write(agent, force=False)
        paths = self._paths_for(agent, root_dir)
        if not paths["target_dir"].is_dir():
            if paths["disabled_dir"].is_dir():
                raise ValueError("SKILL_ALREADY_DISABLED")
            raise ValueError("SKILL_NOT_INSTALLED")
        if paths["disabled_dir"].exists():
            shutil.rmtree(paths["disabled_dir"])
        paths["disabled_dir"].parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(paths["target_dir"]), str(paths["disabled_dir"]))
        self._persist_root_snapshot(runtime, root_dir, runtime.resolved_root_source or PATH_AUTO)
        return self.get_status(agent)

    def enable(self, agent: str) -> Dict[str, Any]:
        self._ensure_supported_agent(agent)
        runtime, root_dir, _ = self._ensure_ready_for_write(agent, force=False)
        paths = self._paths_for(agent, root_dir)
        if paths["target_dir"].is_dir():
            raise ValueError("SKILL_ALREADY_ENABLED")
        if not paths["disabled_dir"].is_dir():
            raise ValueError("SKILL_NOT_INSTALLED")
        paths["target_dir"].parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(paths["disabled_dir"]), str(paths["target_dir"]))
        self._persist_root_snapshot(runtime, root_dir, runtime.resolved_root_source or PATH_AUTO)
        return self.get_status(agent)

    def health(self, agent: str) -> Dict[str, Any]:
        self._ensure_supported_agent(agent)
        status = self.get_status(agent)
        checks: List[str] = []
        warnings: List[Dict[str, Any]] = []

        if status["skill_status"] != SKILL_INSTALLED:
            warnings.append(
                {
                    "code": "SKILL_NOT_INSTALLED",
                    "message": "Skill is not installed.",
                }
            )
            return {"agent": agent, "ok": False, "checks": checks, "warnings": warnings}

        runtime = self._get_or_create_runtime(agent)
        root_dir = self._resolved_root_dir(runtime)
        if root_dir is None:
            warnings.append(
                {
                    "code": "SKILL_PATH_NOT_FOUND",
                    "message": "No detected runtime workspace. Click Detect first.",
                }
            )
            return {"agent": agent, "ok": False, "checks": checks, "warnings": warnings}

        target_dir = self._paths_for(agent, root_dir)["target_dir"]
        for rel_path in REQUIRED_SKILL_FILES:
            expected = target_dir / rel_path
            if expected.exists():
                checks.append(f"found:{rel_path}")
            else:
                warnings.append(
                    {
                        "code": "SKILL_OPERATION_FAILED",
                        "message": f"required file missing: {rel_path}",
                    }
                )

        if agent == "openclaw":
            self._probe_openclaw_skill_cli(checks, warnings)

        return {"agent": agent, "ok": not warnings, "checks": checks, "warnings": warnings}

    def version(self, agent: str) -> Dict[str, Any]:
        status = self.get_status(agent)
        return {
            "agent": agent,
            "bundled_version": status["bundled_version"],
            "installed_version": status["installed_version"],
            "update_available": status["update_available"],
        }

    def update(self, agent: str, *, force: bool = False) -> Dict[str, Any]:
        runtime, root_dir, root_source = self._ensure_ready_for_write(agent, force=force)
        paths = self._paths_for(agent, root_dir)
        if not paths["target_dir"].is_dir() and not paths["disabled_dir"].is_dir():
            raise ValueError("SKILL_NOT_INSTALLED")
        self.install(agent, force=force)
        self._persist_root_snapshot(runtime, root_dir, root_source)
        return self.version(agent)

    def _ensure_ready_for_write(
        self, agent: str, *, force: bool
    ) -> Tuple[SkillRuntime, Path, str]:
        runtime = self._get_or_create_runtime(agent)
        if not force and runtime.detect_status != "ready":
            raise ValueError("SKILL_DETECT_REQUIRED")

        resolved_root = self._resolved_root_dir(runtime)
        if resolved_root is not None:
            source = runtime.resolved_root_source or PATH_AUTO
            return runtime, resolved_root, source

        if not force:
            raise ValueError("SKILL_PATH_NOT_FOUND")

        manual_root = self._resolve_manual_root(runtime)
        if manual_root is not None:
            return runtime, manual_root, PATH_MANUAL

        auto_root = self._resolve_auto_root_for_force(agent)
        if auto_root is None:
            raise ValueError("SKILL_PATH_NOT_FOUND")
        return runtime, auto_root, PATH_AUTO

    def _ensure_supported_agent(self, agent: str) -> None:
        if agent not in TARGET_AGENTS:
            raise ValueError("SKILL_TARGET_UNSUPPORTED")

    def _ensure_source_exists(self) -> None:
        if not self.source_dir.is_dir():
            raise ValueError("SKILL_SOURCE_NOT_FOUND")

    def _get_or_create_runtime(self, agent: str) -> SkillRuntime:
        runtime = self.db.get(SkillRuntime, agent)
        if runtime is not None:
            return runtime
        runtime = SkillRuntime(
            agent=agent,
            detect_status="unknown",
            runtime_status=RUNTIME_UNKNOWN,
            runtime_detected=False,
            last_checks_json=[],
            last_warnings_json=[],
        )
        self.db.add(runtime)
        self.db.commit()
        self.db.refresh(runtime)
        return runtime

    def _persist_root_snapshot(self, runtime: SkillRuntime, root_dir: Path, source: str) -> None:
        runtime.resolved_root_path = str(root_dir.expanduser())
        runtime.resolved_root_source = source
        if runtime.runtime_status == RUNTIME_UNKNOWN:
            runtime.runtime_status = RUNTIME_INSTALLED
        self.db.add(runtime)
        self.db.commit()
        self.db.refresh(runtime)

    def _backup_existing(self, target_dir: Path, backup_root: Path) -> None:
        backup_root.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_dir = backup_root / f"{SKILL_NAME}.{timestamp}"
        shutil.move(str(target_dir), str(backup_dir))

    def _resolved_root_dir(self, runtime: SkillRuntime) -> Optional[Path]:
        raw = (runtime.resolved_root_path or "").strip()
        if not raw:
            return None
        root = Path(raw).expanduser()
        if root.is_dir():
            return root
        return None

    def _resolve_manual_root(self, runtime: SkillRuntime) -> Optional[Path]:
        raw = (runtime.configured_path or "").strip()
        if not raw:
            return None
        return Path(raw).expanduser()

    def _path_mode(self, runtime: SkillRuntime) -> str:
        source = (runtime.resolved_root_source or "").strip()
        if source == PATH_MANUAL:
            return PATH_MANUAL
        if source == PATH_AUTO:
            return PATH_AUTO
        return PATH_NONE

    def _has_warning_code(self, warnings: List[Dict[str, Any]], code: str) -> bool:
        return any(item.get("code") == code for item in warnings)

    def _probe_runtime(
        self, agent: str, checks: List[str], warnings: List[Dict[str, Any]]
    ) -> Tuple[str, Optional[str]]:
        command = ["openclaw", "--version"] if agent == "openclaw" else ["codex", "--version"]
        try:
            probe = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=8,
            )
            if probe.returncode == 0:
                checks.append("runtime_cli:ok")
                return RUNTIME_INSTALLED, self._extract_version_line(probe.stdout)
            warnings.append(
                {
                    "code": "SKILL_RUNTIME_NOT_FOUND",
                    "message": "Runtime CLI command failed.",
                    "details": {"exit_code": probe.returncode},
                }
            )
            return RUNTIME_NOT_INSTALLED, None
        except FileNotFoundError:
            warnings.append(
                {
                    "code": "SKILL_RUNTIME_NOT_FOUND",
                    "message": "Runtime CLI not found in PATH.",
                }
            )
            return RUNTIME_NOT_INSTALLED, None
        except subprocess.TimeoutExpired:
            warnings.append(
                {
                    "code": "SKILL_RUNTIME_TIMEOUT",
                    "message": "Runtime CLI probe timed out.",
                }
            )
            return RUNTIME_UNKNOWN, None

    def _resolve_auto_root_for_detect(
        self, agent: str, checks: List[str], warnings: List[Dict[str, Any]]
    ) -> Optional[Path]:
        home = Path.home()

        if agent == "codex":
            env_path_raw = os.getenv("CODEX_HOME", "").strip()
            if env_path_raw:
                env_path = Path(env_path_raw).expanduser()
                if env_path.is_dir():
                    checks.append("root_source:env")
                    return env_path
                warnings.append(
                    {
                        "code": "SKILL_ENV_PATH_INVALID",
                        "message": "CODEX_HOME is set but invalid. Falling back to default path.",
                    }
                )
            default_root = home / ".codex"
            if default_root.is_dir():
                checks.append("root_source:default")
                return default_root
            warnings.append(
                {
                    "code": "SKILL_PATH_NOT_FOUND",
                    "message": "Default Codex home was not found.",
                }
            )
            return None

        workspace_env = os.getenv("OPENCLAW_WORKSPACE_DIR", "").strip()
        if workspace_env:
            env_path = Path(workspace_env).expanduser()
            if env_path.is_dir():
                checks.append("root_source:env")
                return env_path
            warnings.append(
                {
                    "code": "SKILL_ENV_PATH_INVALID",
                    "message": "OPENCLAW_WORKSPACE_DIR is set but invalid. Falling back to other sources.",
                }
            )

        config_path_env = os.getenv("OPENCLAW_CONFIG_PATH", "").strip()
        config_path = Path(config_path_env).expanduser() if config_path_env else home / ".openclaw" / "openclaw.json"
        cfg_workspace, cfg_warning = self._read_openclaw_workspace_from_config(config_path)
        if cfg_warning is not None:
            warnings.append(cfg_warning)
        if cfg_workspace is not None:
            if cfg_workspace.is_dir():
                checks.append("root_source:config")
                return cfg_workspace
            warnings.append(
                {
                    "code": "SKILL_CONFIG_PATH_INVALID",
                    "message": "Workspace from OpenClaw config is invalid. Falling back to default path.",
                }
            )

        fallback = home / ".openclaw" / "workspace"
        if fallback.is_dir():
            checks.append("root_source:default")
            return fallback
        warnings.append(
            {
                "code": "SKILL_PATH_NOT_FOUND",
                "message": "Default OpenClaw workspace was not found.",
            }
        )
        return None

    def _resolve_auto_root_for_force(self, agent: str) -> Optional[Path]:
        home = Path.home()
        if agent == "codex":
            env_path_raw = os.getenv("CODEX_HOME", "").strip()
            if env_path_raw:
                return Path(env_path_raw).expanduser()
            return home / ".codex"

        workspace_env = os.getenv("OPENCLAW_WORKSPACE_DIR", "").strip()
        if workspace_env:
            return Path(workspace_env).expanduser()

        config_path_env = os.getenv("OPENCLAW_CONFIG_PATH", "").strip()
        config_path = Path(config_path_env).expanduser() if config_path_env else home / ".openclaw" / "openclaw.json"
        cfg_workspace, _ = self._read_openclaw_workspace_from_config(config_path)
        if cfg_workspace is not None:
            return cfg_workspace
        return home / ".openclaw" / "workspace"

    def _read_openclaw_workspace_from_config(
        self, config_path: Path
    ) -> Tuple[Optional[Path], Optional[Dict[str, Any]]]:
        if not config_path.is_file():
            return None, None
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None, {
                "code": "SKILL_CONFIG_PARSE_FAILED",
                "message": "Failed to parse OpenClaw config. Falling back to default path.",
            }

        workspace = payload.get("agents", {}).get("defaults", {}).get("workspace", "")
        if isinstance(workspace, str) and workspace.strip():
            return Path(workspace.strip()).expanduser(), None
        return None, None

    def _read_skill_version(self, skill_dir: Path) -> Optional[str]:
        package_json = skill_dir / "package.json"
        if package_json.is_file():
            try:
                payload = json.loads(package_json.read_text(encoding="utf-8"))
                version = str(payload.get("version", "")).strip()
                if version:
                    return version
            except (json.JSONDecodeError, OSError):
                pass

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            return None
        try:
            lines = skill_md.read_text(encoding="utf-8").splitlines()
        except OSError:
            return None
        in_frontmatter = False
        for line in lines:
            if line.strip() == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                break
            if in_frontmatter and line.strip().startswith("version:"):
                return line.split(":", 1)[1].strip().strip("'\"")
        return None

    def _extract_version_line(self, stdout: str) -> Optional[str]:
        for raw in stdout.splitlines():
            line = raw.strip()
            if line:
                return line[:120]
        return None

    def _probe_openclaw_skill_cli(self, checks: List[str], warnings: List[Dict[str, Any]]) -> None:
        try:
            info = subprocess.run(
                ["openclaw", "skills", "info", SKILL_NAME, "--json"],
                check=False,
                capture_output=True,
                text=True,
                timeout=8,
            )
            checks.append(f"openclaw_info_exit:{info.returncode}")
            if info.returncode != 0:
                warnings.append(
                    {
                        "code": "SKILL_OPERATION_FAILED",
                        "message": "OpenClaw skill info probe failed.",
                        "details": {"exit_code": info.returncode},
                    }
                )

            check = subprocess.run(
                ["openclaw", "skills", "check", "--json"],
                check=False,
                capture_output=True,
                text=True,
                timeout=8,
            )
            checks.append(f"openclaw_check_exit:{check.returncode}")
            if check.returncode != 0:
                warnings.append(
                    {
                        "code": "SKILL_OPERATION_FAILED",
                        "message": "OpenClaw skill check probe failed.",
                        "details": {"exit_code": check.returncode},
                    }
                )
        except FileNotFoundError:
            warnings.append(
                {
                    "code": "SKILL_CLI_NOT_FOUND",
                    "message": "OpenClaw CLI not found in PATH.",
                }
            )
        except subprocess.TimeoutExpired:
            warnings.append(
                {
                    "code": "SKILL_OPERATION_FAILED",
                    "message": "OpenClaw CLI health probe timed out.",
                }
            )

    def _paths_for(self, agent: str, root_dir: Path) -> Dict[str, Path]:
        target_root = root_dir / "skills"
        if agent == "openclaw":
            return {
                "root_dir": root_dir,
                "target_dir": target_root / SKILL_NAME,
                "disabled_dir": target_root / ".disabled" / SKILL_NAME,
                "backup_root": Path.home() / ".openclaw" / "skill-backups" / root_dir.name,
            }
        return {
            "root_dir": root_dir,
            "target_dir": target_root / SKILL_NAME,
            "disabled_dir": target_root / ".disabled" / SKILL_NAME,
            "backup_root": root_dir / "skill-backups",
        }
