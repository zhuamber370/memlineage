"use client";

import { useEffect, useMemo, useState } from "react";

import { apiGet } from "../src/lib/api";
import {
  buildHomeSnapshot,
  type ChangeSummary,
  type KnowledgeSummary,
  type TaskSummary
} from "../src/lib/home-dashboard";
import { useI18n } from "../src/i18n";

type TaskListResp = { items: TaskSummary[] };
type KnowledgeListResp = { items: KnowledgeSummary[] };
type ChangeListResp = { items: ChangeSummary[] };

export default function HomeDashboardPage() {
  const { t } = useI18n();
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [knowledge, setKnowledge] = useState<KnowledgeSummary[]>([]);
  const [changes, setChanges] = useState<ChangeSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const snapshot = useMemo(() => buildHomeSnapshot({ tasks, knowledge, changes }), [tasks, knowledge, changes]);

  useEffect(() => {
    void loadHomeData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadHomeData() {
    setLoading(true);
    setError("");
    try {
      const [taskRes, knowledgeRes, changeRes] = await Promise.all([
        apiGet<TaskListResp>("/api/v1/tasks?page=1&page_size=100"),
        apiGet<KnowledgeListResp>("/api/v1/knowledge?page=1&page_size=100&status=active"),
        apiGet<ChangeListResp>("/api/v1/changes?page=1&page_size=100")
      ]);
      setTasks(taskRes.items ?? []);
      setKnowledge(knowledgeRes.items ?? []);
      setChanges(changeRes.items ?? []);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card">
      <h1 className="h1">{t("home.title")}</h1>
      <p className="meta">{t("home.subtitle")}</p>
      {error ? <p className="meta" style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div className="badges">
        <span className="badge">{t("tasks.title")}: {snapshot.global.taskTotal}</span>
        <span className="badge">{t("tasks.statusValue.in_progress")}: {snapshot.global.taskInProgress}</span>
        <span className="badge">P0 {t("tasks.statusValue.in_progress")}: {snapshot.global.p0InProgress}</span>
        <span className="badge">{t("knowledge.title")}: {snapshot.global.knowledgeTotal}</span>
        <span className="badge">{t("changes.title")}: {snapshot.global.proposedChanges}</span>
      </div>
      {loading ? <p className="meta">...</p> : null}
    </section>
  );
}
