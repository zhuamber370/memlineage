# Skill (Legacy Python Helpers)

This directory contains legacy Python helper scripts used during early integration.
It is not the current production skill bundle used by Codex or OpenClaw.
If you need the active runtime bundle, use `skills/memlineage`.

Current production bundle:
- `<repo_root>/skills/memlineage`

OpenClaw install/uninstall commands:
- `bash <repo_root>/scripts/install_openclaw_memlineage_skill.sh`
- `bash <repo_root>/scripts/uninstall_openclaw_memlineage_skill.sh`

OpenClaw install target:
- OpenClaw workspace `skills` directory (`<workspace>/skills/memlineage`)

Codex install target:
- `~/.codex/skills/memlineage`
- copy from `<repo_root>/skills/memlineage` into that directory.

Legacy files kept for reference:
- `openclaw_skill.py`
- `actions/*.py`
