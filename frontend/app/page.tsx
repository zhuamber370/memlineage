"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { apiGet } from "../src/lib/api";
import { formatDateTime } from "../src/lib/datetime";
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
  const { t, lang } = useI18n();
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [knowledge, setKnowledge] = useState<KnowledgeSummary[]>([]);
  const [changes, setChanges] = useState<ChangeSummary[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [knowledgeLoading, setKnowledgeLoading] = useState(false);
  const [changesLoading, setChangesLoading] = useState(false);
  const [tasksError, setTasksError] = useState("");
  const [knowledgeError, setKnowledgeError] = useState("");
  const [changesError, setChangesError] = useState("");

  const snapshot = useMemo(() => buildHomeSnapshot({ tasks, knowledge, changes }), [tasks, knowledge, changes]);
  const categoryEntries = useMemo(
    () => Object.entries(snapshot.knowledge.byCategory).sort(([a], [b]) => a.localeCompare(b)),
    [snapshot.knowledge.byCategory]
  );

  useEffect(() => {
    void loadHomeData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function messageFromError(error: unknown): string {
    if (error instanceof Error) return error.message;
    return String(error ?? "");
  }

  async function loadHomeData() {
    setTasksLoading(true);
    setKnowledgeLoading(true);
    setChangesLoading(true);
    setTasksError("");
    setKnowledgeError("");
    setChangesError("");

    const [taskRes, knowledgeRes, changeRes] = await Promise.allSettled([
      apiGet<TaskListResp>("/api/v1/tasks?page=1&page_size=100"),
      apiGet<KnowledgeListResp>("/api/v1/knowledge?page=1&page_size=100&status=active"),
      apiGet<ChangeListResp>("/api/v1/changes?page=1&page_size=100")
    ]);

    if (taskRes.status === "fulfilled") {
      setTasks(taskRes.value.items ?? []);
    } else {
      setTasks([]);
      setTasksError(messageFromError(taskRes.reason));
    }
    setTasksLoading(false);

    if (knowledgeRes.status === "fulfilled") {
      setKnowledge(knowledgeRes.value.items ?? []);
    } else {
      setKnowledge([]);
      setKnowledgeError(messageFromError(knowledgeRes.reason));
    }
    setKnowledgeLoading(false);

    if (changeRes.status === "fulfilled") {
      setChanges(changeRes.value.items ?? []);
    } else {
      setChanges([]);
      setChangesError(messageFromError(changeRes.reason));
    }
    setChangesLoading(false);
  }

  function taskStatusLabel(status: string): string {
    const key = `tasks.statusValue.${status}`;
    const value = t(key);
    return value === key ? status : value;
  }

  function knowledgeCategoryLabel(category: string): string {
    if (category === "unclassified") return t("knowledge.unclassified");
    const key = `knowledge.category.${category}`;
    const value = t(key);
    return value === key ? category : value;
  }

  function changeStatusLabel(status: string): string {
    if (status === "proposed") return t("home.changes.status.proposed");
    if (status === "committed") return t("home.changes.status.committed");
    if (status === "rejected") return t("home.changes.status.rejected");
    return status;
  }

  function taskDeepLink(task: TaskSummary): string {
    const params = new URLSearchParams({ status: "in_progress" });
    if (task.priority === "P0") {
      params.set("priority", "P0");
    }
    params.set("task_id", task.id);
    return `/tasks?${params.toString()}`;
  }

  function taskStudioLink(task: TaskSummary): string {
    const params = new URLSearchParams({ status: "in_progress", workspace: "studio" });
    if (task.priority === "P0") {
      params.set("priority", "P0");
    }
    params.set("task_id", task.id);
    return `/tasks?${params.toString()}`;
  }

  const isAnyLoading = tasksLoading || knowledgeLoading || changesLoading;

  return (
    <section className="homeDashboard">
      <header className="card homeHero">
        <h1 className="h1">{t("home.title")}</h1>
        <p className="meta">{t("home.subtitle")}</p>
        <div className="badges">
          <button className="badge" onClick={() => void loadHomeData()} disabled={isAnyLoading}>
            {isAnyLoading ? t("home.loading") : t("tasks.refresh")}
          </button>
        </div>
      </header>

      <div className="homeDashboardGrid">
        <section className="card homePanel">
          <h2 className="changesSubTitle">{t("home.global.title")}</h2>
          <div className="homeMetricGrid">
            <Link href="/tasks" className="homeMetricCard">
              <div className="changesSummaryKey">{t("home.global.taskTotal")}</div>
              <div className="changesSummaryValue">{snapshot.global.taskTotal}</div>
            </Link>
            <Link href="/tasks?status=in_progress" className="homeMetricCard">
              <div className="changesSummaryKey">{t("home.global.taskInProgress")}</div>
              <div className="changesSummaryValue">{snapshot.global.taskInProgress}</div>
            </Link>
            <Link href="/tasks?status=in_progress&priority=P0" className="homeMetricCard">
              <div className="changesSummaryKey">{t("home.global.p0InProgress")}</div>
              <div className="changesSummaryValue">{snapshot.global.p0InProgress}</div>
            </Link>
            <Link href="/changes?status=proposed" className="homeMetricCard">
              <div className="changesSummaryKey">{t("home.global.proposedChanges")}</div>
              <div className="changesSummaryValue">{snapshot.global.proposedChanges}</div>
            </Link>
            <Link href="/knowledge?status=active" className="homeMetricCard">
              <div className="changesSummaryKey">{t("home.global.knowledgeTotal")}</div>
              <div className="changesSummaryValue">{snapshot.global.knowledgeTotal}</div>
            </Link>
          </div>
        </section>

        <section className="card homePanel">
          <h2 className="changesSubTitle">{t("home.tasks.title")}</h2>
          <div className="changesSummaryGrid">
            <div className="changesSummaryCard">
              <div className="changesSummaryKey">{t("home.tasks.blockedCount")}</div>
              <div className="changesSummaryValue">{snapshot.task.blockedCount}</div>
            </div>
            <div className="changesSummaryCard">
              <div className="changesSummaryKey">{t("home.tasks.dueTodayCount")}</div>
              <div className="changesSummaryValue">{snapshot.task.dueTodayCount}</div>
            </div>
          </div>
          <h3 className="changesGroupTitle">{t("home.tasks.focusTitle")}</h3>
          <div className="homeList">
            {tasksLoading ? (
              <p className="meta">{t("home.loading")}</p>
            ) : tasksError ? (
              <p className="meta" style={{ color: "var(--danger)" }}>
                {t("home.error")}: {tasksError}
              </p>
            ) : snapshot.task.focus.length ? (
              snapshot.task.focus.map((task) => (
                <article key={task.id} className="homeListItem">
                  <div className="taskTitle">{task.title}</div>
                  <div className="taskMetaLine">
                    <span>{t("tasks.priority")}: {task.priority || "-"}</span>
                    <span>{t("tasks.status")}: {taskStatusLabel(task.status)}</span>
                    <span>{t("tasks.updated")}: {formatDateTime(task.updated_at, lang)}</span>
                  </div>
                  <div className="badges">
                    <Link href={taskDeepLink(task)} className="badge">
                      {t("home.tasks.openTask")}
                    </Link>
                    <Link href={taskStudioLink(task)} className="badge">
                      {t("home.tasks.openStudio")}
                    </Link>
                  </div>
                </article>
              ))
            ) : (
              <p className="meta">{t("home.empty")}</p>
            )}
          </div>
        </section>

        <section className="card homePanel">
          <h2 className="changesSubTitle">{t("home.changes.title")}</h2>
          <div className="changesSummaryGrid">
            <div className="changesSummaryCard">
              <div className="changesSummaryKey">{t("home.changes.proposedCount")}</div>
              <div className="changesSummaryValue">{snapshot.global.proposedChanges}</div>
            </div>
            <div className="changesSummaryCard">
              <div className="changesSummaryKey">{t("home.changes.latestCommittedAt")}</div>
              <div className="changesSummaryValue">{formatDateTime(snapshot.changes.latestCommittedAt, lang)}</div>
            </div>
          </div>
          <h3 className="changesGroupTitle">{t("home.changes.recentTitle")}</h3>
          <div className="homeList">
            {changesLoading ? (
              <p className="meta">{t("home.loading")}</p>
            ) : changesError ? (
              <p className="meta" style={{ color: "var(--danger)" }}>
                {t("home.error")}: {changesError}
              </p>
            ) : snapshot.changes.recentProposed.length ? (
              snapshot.changes.recentProposed.map((item) => (
                <article key={item.change_set_id} className="homeListItem">
                  <div className="taskTitle">{item.change_set_id}</div>
                  <div className="taskMetaLine">
                    <span>{t("changes.proposalCreatedAt")}: {formatDateTime(item.created_at, lang)}</span>
                    <span>{changeStatusLabel(item.status)}</span>
                  </div>
                  <div className="badges">
                    <Link href="/changes?status=proposed" className="badge">
                      {t("home.changes.openChanges")}
                    </Link>
                  </div>
                </article>
              ))
            ) : (
              <p className="meta">{t("home.empty")}</p>
            )}
          </div>
        </section>

        <section className="card homePanel">
          <h2 className="changesSubTitle">{t("home.knowledge.title")}</h2>
          <div className="changesSummaryGrid">
            <div className="changesSummaryCard">
              <div className="changesSummaryKey">{t("home.knowledge.total")}</div>
              <div className="changesSummaryValue">{snapshot.global.knowledgeTotal}</div>
            </div>
            <div className="changesSummaryCard">
              <div className="changesSummaryKey">{t("home.knowledge.categoryCount")}</div>
              <div className="changesSummaryValue">{categoryEntries.length}</div>
            </div>
          </div>
          <h3 className="changesGroupTitle">{t("home.knowledge.byCategoryTitle")}</h3>
          <div className="badges">
            {knowledgeLoading ? (
              <span className="meta">{t("home.loading")}</span>
            ) : knowledgeError ? (
              <span className="meta" style={{ color: "var(--danger)" }}>
                {t("home.error")}: {knowledgeError}
              </span>
            ) : categoryEntries.length ? (
              categoryEntries.map(([category, count]) => (
                <span key={category} className="badge">
                  {knowledgeCategoryLabel(category)}: {count}
                </span>
              ))
            ) : (
              <span className="meta">{t("home.empty")}</span>
            )}
          </div>
          <h3 className="changesGroupTitle">{t("home.knowledge.recentTitle")}</h3>
          <div className="homeList">
            {knowledgeLoading ? (
              <p className="meta">{t("home.loading")}</p>
            ) : knowledgeError ? (
              <p className="meta" style={{ color: "var(--danger)" }}>
                {t("home.error")}: {knowledgeError}
              </p>
            ) : snapshot.knowledge.recent.length ? (
              snapshot.knowledge.recent.map((item) => (
                <article key={item.id} className="homeListItem">
                  <div className="taskTitle">{item.title}</div>
                  <div className="taskMetaLine">
                    <span>{knowledgeCategoryLabel(item.category || "unclassified")}</span>
                    <span>{t("knowledge.updated")}: {formatDateTime(item.updated_at, lang)}</span>
                  </div>
                  <div className="badges">
                    <Link href="/knowledge?status=active" className="badge">
                      {t("home.knowledge.openKnowledge")}
                    </Link>
                  </div>
                </article>
              ))
            ) : (
              <p className="meta">{t("home.empty")}</p>
            )}
          </div>
        </section>
      </div>
    </section>
  );
}
