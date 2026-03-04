const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

export function apiHeaders(): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json"
  };
  if (API_KEY) {
    headers.Authorization = `Bearer ${API_KEY}`;
  }
  return headers;
}

export async function apiPost<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: apiHeaders(),
    body: JSON.stringify(payload),
    cache: "no-store"
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`POST ${path} failed: ${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    headers: apiHeaders(),
    cache: "no-store"
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GET ${path} failed: ${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function apiPatch<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: apiHeaders(),
    body: JSON.stringify(payload),
    cache: "no-store"
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`PATCH ${path} failed: ${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function apiPut<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: apiHeaders(),
    body: JSON.stringify(payload),
    cache: "no-store"
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`PUT ${path} failed: ${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}


export async function apiDelete(path: string): Promise<void> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: apiHeaders(),
    cache: "no-store"
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`DELETE ${path} failed: ${res.status} ${text}`);
  }
}

export async function apiDeleteJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: apiHeaders(),
    cache: "no-store"
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`DELETE ${path} failed: ${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

function authOnlyHeaders(): HeadersInit {
  if (!API_KEY) return {};
  return { Authorization: `Bearer ${API_KEY}` };
}

export type DbRestoreResult = {
  status: "restored";
  backend: "sqlite" | "postgres";
  restored_at: string;
};

export async function downloadDbBackup(): Promise<{ blob: Blob; filename: string }> {
  const res = await fetch(`${API_BASE}/api/v1/admin/db/backup`, {
    method: "GET",
    headers: authOnlyHeaders(),
    cache: "no-store"
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GET /api/v1/admin/db/backup failed: ${res.status} ${text}`);
  }
  const disposition = res.headers.get("content-disposition") ?? "";
  const match = disposition.match(/filename=(?:\"([^\"]+)\"|([^;]+))/i);
  const filename = (match?.[1] ?? match?.[2] ?? "memlineage-backup.mlbk").trim();
  return { blob: await res.blob(), filename };
}

export async function restoreDbBackup(file: File): Promise<DbRestoreResult> {
  const res = await fetch(`${API_BASE}/api/v1/admin/db/restore`, {
    method: "POST",
    headers: {
      ...authOnlyHeaders(),
      "Content-Type": "application/octet-stream",
      "x-backup-filename": file.name
    },
    body: file,
    cache: "no-store"
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`POST /api/v1/admin/db/restore failed: ${res.status} ${text}`);
  }
  return res.json() as Promise<DbRestoreResult>;
}

export type SkillAgent = "openclaw" | "codex";

export type SkillStatus = {
  agent: SkillAgent;
  detect_status: "unknown" | "ready" | "failed";
  needs_manual_path: boolean;
  manual_path_configured: boolean;
  path_mode: "none" | "auto" | "manual";
  runtime_status: "unknown" | "installed" | "not_installed";
  runtime_version?: string | null;
  skill_status: "unknown" | "installed" | "not_installed";
  skill_enabled: boolean;
  last_checked_at?: string | null;
  last_error?: string | null;
  last_checks: string[];
  last_warnings: Array<Record<string, unknown>>;
  bundled_version?: string | null;
  installed_version?: string | null;
  update_available: boolean;
};

export type SkillStatusList = {
  items: SkillStatus[];
};

export type SkillHealthWarning = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
};

export type SkillHealth = {
  agent: SkillAgent;
  ok: boolean;
  checks: string[];
  warnings: SkillHealthWarning[];
};

export type SkillVersion = {
  agent: SkillAgent;
  bundled_version?: string | null;
  installed_version?: string | null;
  update_available: boolean;
};

export type SkillOperation = {
  action: string;
  status: SkillStatus;
};

export function listSkills(): Promise<SkillStatusList> {
  return apiGet<SkillStatusList>("/api/v1/skills");
}

export function getSkillStatus(agent: SkillAgent): Promise<SkillStatus> {
  return apiGet<SkillStatus>(`/api/v1/skills/${agent}`);
}

export function installSkill(agent: SkillAgent): Promise<SkillOperation> {
  return apiPost<SkillOperation>(`/api/v1/skills/${agent}/install`, { force: false });
}

export function forceInstallSkill(agent: SkillAgent): Promise<SkillOperation> {
  return apiPost<SkillOperation>(`/api/v1/skills/${agent}/install`, { force: true });
}

export function uninstallSkill(agent: SkillAgent): Promise<SkillOperation> {
  return apiDeleteJson<SkillOperation>(`/api/v1/skills/${agent}`);
}

export function enableSkill(agent: SkillAgent): Promise<SkillOperation> {
  return apiPost<SkillOperation>(`/api/v1/skills/${agent}/enable`, {});
}

export function disableSkill(agent: SkillAgent): Promise<SkillOperation> {
  return apiPost<SkillOperation>(`/api/v1/skills/${agent}/disable`, {});
}

export function checkSkillHealth(agent: SkillAgent): Promise<SkillHealth> {
  return apiGet<SkillHealth>(`/api/v1/skills/${agent}/health`);
}

export function getSkillVersion(agent: SkillAgent): Promise<SkillVersion> {
  return apiGet<SkillVersion>(`/api/v1/skills/${agent}/version`);
}

export function updateSkill(agent: SkillAgent): Promise<SkillVersion> {
  return apiPost<SkillVersion>(`/api/v1/skills/${agent}/update`, { force: false });
}

export function forceUpdateSkill(agent: SkillAgent): Promise<SkillVersion> {
  return apiPost<SkillVersion>(`/api/v1/skills/${agent}/update`, { force: true });
}

export function configureSkillPath(agent: SkillAgent, configuredPath: string): Promise<SkillStatus> {
  return apiPut<SkillStatus>(`/api/v1/skills/${agent}/config`, { configured_path: configuredPath });
}

export function detectSkill(agent: SkillAgent): Promise<SkillStatus> {
  return apiPost<SkillStatus>(`/api/v1/skills/${agent}/detect`, {});
}
