"use client";

import { useEffect, useMemo, useState } from "react";

import {
  checkSkillHealth,
  configureSkillPath,
  detectSkill,
  disableSkill,
  enableSkill,
  forceInstallSkill,
  forceUpdateSkill,
  getSkillStatus,
  installSkill,
  listSkills,
  type SkillAgent,
  type SkillHealth,
  type SkillStatus,
  uninstallSkill,
  updateSkill
} from "../../src/lib/api";
import { useI18n } from "../../src/i18n";

type AgentState = {
  status: SkillStatus | null;
  health: SkillHealth | null;
  pathInput: string;
  advancedMode: boolean;
  loading: boolean;
  pendingAction: string;
  error: string;
  lastAction: string;
};

const AGENTS: SkillAgent[] = ["openclaw", "codex"];

function emptyAgentState(): AgentState {
  return {
    status: null,
    health: null,
    pathInput: "",
    advancedMode: false,
    loading: true,
    pendingAction: "",
    error: "",
    lastAction: ""
  };
}

export default function SkillsPage() {
  const { t } = useI18n();
  const [states, setStates] = useState<Record<SkillAgent, AgentState>>({
    openclaw: emptyAgentState(),
    codex: emptyAgentState()
  });
  const [refreshingAll, setRefreshingAll] = useState(false);
  const [globalError, setGlobalError] = useState("");

  const hasAnyLoading = useMemo(
    () => refreshingAll || AGENTS.some((agent) => states[agent].loading || Boolean(states[agent].pendingAction)),
    [refreshingAll, states]
  );

  useEffect(() => {
    void refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function messageFromError(error: unknown): string {
    if (error instanceof Error) return error.message;
    return String(error ?? "");
  }

  function agentLabel(agent: SkillAgent): string {
    return t(`skills.agent.${agent}`);
  }

  function updateAgentState(agent: SkillAgent, patch: Partial<AgentState>) {
    setStates((prev) => ({
      ...prev,
      [agent]: { ...prev[agent], ...patch }
    }));
  }

  function applyStatus(agent: SkillAgent, status: SkillStatus) {
    updateAgentState(agent, {
      status,
      loading: false
    });
  }

  async function refreshAgent(agent: SkillAgent, presetStatus?: SkillStatus | null) {
    updateAgentState(agent, { loading: true, error: "" });
    try {
      const status = presetStatus ?? (await getSkillStatus(agent));
      applyStatus(agent, status);
    } catch (error) {
      updateAgentState(agent, {
        loading: false,
        error: messageFromError(error)
      });
    }
  }

  async function refreshAll() {
    setRefreshingAll(true);
    setGlobalError("");
    try {
      const listed = await listSkills();
      const byAgent = new Map<SkillAgent, SkillStatus>();
      for (const row of listed.items) byAgent.set(row.agent, row);
      await Promise.all(AGENTS.map((agent) => refreshAgent(agent, byAgent.get(agent) ?? null)));
    } catch (error) {
      setGlobalError(messageFromError(error));
      await Promise.all(AGENTS.map((agent) => refreshAgent(agent)));
    } finally {
      setRefreshingAll(false);
    }
  }

  async function savePath(agent: SkillAgent) {
    const pathValue = states[agent].pathInput.trim();
    if (!pathValue) return;
    updateAgentState(agent, { pendingAction: "savePath", error: "" });
    try {
      const status = await configureSkillPath(agent, pathValue);
      applyStatus(agent, status);
      updateAgentState(agent, {
        pendingAction: "",
        pathInput: "",
        lastAction: t("skills.action.savePath")
      });
    } catch (error) {
      updateAgentState(agent, { pendingAction: "", error: messageFromError(error) });
    }
  }

  async function runDetect(agent: SkillAgent) {
    updateAgentState(agent, { pendingAction: "detect", error: "" });
    try {
      const status = await detectSkill(agent);
      applyStatus(agent, status);
      updateAgentState(agent, { pendingAction: "", lastAction: t("skills.action.detect") });
    } catch (error) {
      updateAgentState(agent, { pendingAction: "", error: messageFromError(error) });
    }
  }

  async function runAction(
    agent: SkillAgent,
    action: "install" | "uninstall" | "enable" | "disable" | "update" | "checkHealth"
  ) {
    const actionLabel = action === "checkHealth" ? t("skills.action.checkHealth") : t(`skills.action.${action}`);
    if (action === "uninstall" && !window.confirm(t("skills.confirm.uninstall"))) return;
    if (action === "disable" && !window.confirm(t("skills.confirm.disable"))) return;
    if (action === "update" && !window.confirm(t("skills.confirm.update"))) return;

    const advancedMode = states[agent].advancedMode;
    updateAgentState(agent, { pendingAction: action, error: "" });
    try {
      if (action === "install") {
        if (advancedMode) await forceInstallSkill(agent);
        else await installSkill(agent);
      }
      if (action === "uninstall") await uninstallSkill(agent);
      if (action === "enable") await enableSkill(agent);
      if (action === "disable") await disableSkill(agent);
      if (action === "update") {
        if (advancedMode) await forceUpdateSkill(agent);
        else await updateSkill(agent);
      }
      if (action === "checkHealth") {
        const health = await checkSkillHealth(agent);
        updateAgentState(agent, { health });
      }
      await refreshAgent(agent);
      updateAgentState(agent, { pendingAction: "", lastAction: actionLabel });
    } catch (error) {
      updateAgentState(agent, {
        pendingAction: "",
        error: messageFromError(error)
      });
    }
  }

  function detectStatusLabel(status: SkillStatus | null): string {
    const detectStatus = status?.detect_status ?? "unknown";
    return t(`skills.detect.${detectStatus}`);
  }

  function runtimeStatusLabel(status: SkillStatus | null): string {
    const runtimeStatus = status?.runtime_status ?? "unknown";
    return t(`skills.runtime.${runtimeStatus}`);
  }

  function skillStatusLabel(status: SkillStatus | null): string {
    const skillStatus = status?.skill_status ?? "unknown";
    return t(`skills.skill.${skillStatus}`);
  }

  function pathModeLabel(status: SkillStatus | null): string {
    const mode = status?.path_mode ?? "none";
    return t(`skills.pathMode.${mode}`);
  }

  function detectReady(status: SkillStatus | null): boolean {
    return status?.detect_status === "ready";
  }

  return (
    <section className="skillsPage">
      <header className="card skillsHero">
        <div className="skillsHeroHead">
          <div>
            <h1 className="h1">{t("skills.title")}</h1>
            <p className="meta">{t("skills.subtitle")}</p>
          </div>
          <div className="badges">
            <button className="badge" onClick={() => void refreshAll()} disabled={hasAnyLoading}>
              {hasAnyLoading ? t("skills.loading") : t("skills.refreshAll")}
            </button>
          </div>
        </div>
        <p className="meta skillsLocalOnly">{t("skills.localOnly")}</p>
        {globalError ? (
          <p className="meta" style={{ color: "var(--danger)" }}>
            {t("skills.error")}: {globalError}
          </p>
        ) : null}
      </header>

      <div className="skillsGrid">
        {AGENTS.map((agent) => {
          const state = states[agent];
          const status = state.status;
          const health = state.health;
          const skillInstalled = status?.skill_status === "installed";
          const skillEnabled = status?.skill_enabled ?? false;
          const hasUpdate = status?.update_available ?? false;
          const runtimeInstalled = status?.runtime_status === "installed";
          const pending = state.pendingAction;
          const actionBusy = Boolean(pending);
          const runtimeReady = detectReady(status);

          return (
            <article key={agent} className="card skillsCard">
              <div className="skillsCardHeader">
                <h2 className="changesSubTitle">{agentLabel(agent)}</h2>
                <div className="badges">
                  <span className="badge">{runtimeStatusLabel(status)}</span>
                  <span className="badge">{skillStatusLabel(status)}</span>
                  <span className="badge">{detectStatusLabel(status)}</span>
                </div>
              </div>

              <section className="changesBlock">
                <h3 className="changesGroupTitle">{t("skills.section.status")}</h3>
                <p className="meta">{t("skills.runtimeVersion")}: {status?.runtime_version ?? t("skills.version.unknown")}</p>
                <p className="meta">{t("skills.pathSource")}: {pathModeLabel(status)}</p>
                <p className="meta">{t("skills.manualPathSaved")}: {status?.manual_path_configured ? t("skills.yes") : t("skills.no")}</p>
                <p className="meta">{t("skills.lastChecked")}: {status?.last_checked_at || t("skills.none")}</p>
                {status?.last_error ? (
                  <p className="meta" style={{ color: "var(--danger)" }}>
                    {status.last_error}
                  </p>
                ) : null}
              </section>

              <div className="skillsActions">
                <button className="badge" onClick={() => void runDetect(agent)} disabled={actionBusy}>
                  {t("skills.action.detect")}
                </button>
                <button
                  className="badge"
                  onClick={() => void runAction(agent, "install")}
                  disabled={actionBusy || !runtimeInstalled || (!runtimeReady && !state.advancedMode)}
                >
                  {skillInstalled ? t("skills.action.reinstall") : t("skills.action.install")}
                </button>
                <button
                  className="badge"
                  onClick={() => void runAction(agent, "uninstall")}
                  disabled={actionBusy || !skillInstalled}
                >
                  {t("skills.action.uninstall")}
                </button>
                <button
                  className="badge"
                  onClick={() => void runAction(agent, skillEnabled ? "disable" : "enable")}
                  disabled={actionBusy || !runtimeReady || !skillInstalled}
                >
                  {skillEnabled ? t("skills.action.disable") : t("skills.action.enable")}
                </button>
                <button
                  className="badge"
                  onClick={() => void runAction(agent, "checkHealth")}
                  disabled={actionBusy || !skillInstalled}
                >
                  {t("skills.action.checkHealth")}
                </button>
                <button
                  className="badge"
                  onClick={() => void runAction(agent, "update")}
                  disabled={actionBusy || !skillInstalled || !hasUpdate || (!runtimeReady && !state.advancedMode)}
                >
                  {t("skills.action.update")}
                </button>
                <button className="badge" onClick={() => void refreshAgent(agent)} disabled={actionBusy}>
                  {t("skills.action.refresh")}
                </button>
              </div>

              <label className="skillsAdvancedToggle">
                <input
                  type="checkbox"
                  checked={state.advancedMode}
                  onChange={(event) => updateAgentState(agent, { advancedMode: event.target.checked })}
                  disabled={actionBusy}
                />
                {t("skills.advancedMode")}
              </label>

              {status?.needs_manual_path ? (
                <section className="changesBlock">
                  <h3 className="changesGroupTitle">{t("skills.section.manualPath")}</h3>
                  <p className="meta">{t("skills.manualPathHint")}</p>
                  <div className="skillsPathEditor">
                    <input
                      className="skillsPathInput"
                      value={state.pathInput}
                      onChange={(event) => updateAgentState(agent, { pathInput: event.target.value })}
                      placeholder={t("skills.path.placeholder")}
                      disabled={actionBusy}
                    />
                    <button
                      className="badge"
                      onClick={() => void savePath(agent)}
                      disabled={actionBusy || !state.pathInput.trim()}
                    >
                      {t("skills.action.savePath")}
                    </button>
                  </div>
                </section>
              ) : null}

              {state.loading ? <p className="meta">{t("skills.loading")}</p> : null}
              {pending ? <p className="meta">{t(`skills.action.${pending}`)}...</p> : null}
              {state.error ? (
                <p className="meta" style={{ color: "var(--danger)" }}>
                  {t("skills.error")}: {state.error}
                </p>
              ) : null}

              <section className="changesBlock">
                <h3 className="changesGroupTitle">{t("skills.section.version")}</h3>
                <div className="skillsVersionGrid">
                  <div className="changesSummaryCard">
                    <div className="changesSummaryKey">{t("skills.version.bundled")}</div>
                    <div className="changesSummaryValue">{status?.bundled_version ?? t("skills.version.unknown")}</div>
                  </div>
                  <div className="changesSummaryCard">
                    <div className="changesSummaryKey">{t("skills.version.installed")}</div>
                    <div className="changesSummaryValue">{status?.installed_version ?? t("skills.version.unknown")}</div>
                  </div>
                  <div className="changesSummaryCard">
                    <div className="changesSummaryKey">{hasUpdate ? t("skills.version.updateAvailable") : t("skills.version.upToDate")}</div>
                    <div className="changesSummaryValue">{hasUpdate ? t("skills.yes") : t("skills.no")}</div>
                  </div>
                </div>
              </section>

              <section className="changesBlock">
                <h3 className="changesGroupTitle">{t("skills.section.health")}</h3>
                <div className="skillsHealthGrid">
                  <div>
                    <div className="changesSummaryKey">{t("skills.health.checks")}</div>
                    <ul className="skillsList">
                      {(health?.checks ?? []).length ? (
                        (health?.checks ?? []).map((item) => <li key={item}>{item}</li>)
                      ) : (
                        <li>{t("skills.none")}</li>
                      )}
                    </ul>
                  </div>
                  <div>
                    <div className="changesSummaryKey">{t("skills.health.warnings")}</div>
                    <ul className="skillsList">
                      {(health?.warnings ?? []).length ? (
                        (health?.warnings ?? []).map((warning) => (
                          <li key={`${warning.code}-${warning.message}`}>
                            <strong>{warning.code}</strong>: {warning.message}
                          </li>
                        ))
                      ) : (
                        <li>{t("skills.none")}</li>
                      )}
                    </ul>
                  </div>
                </div>
              </section>

              <p className="meta">
                {t("skills.lastAction")}: {state.lastAction || t("skills.none")}
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
