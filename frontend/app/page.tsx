"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { apiGet } from "../src/lib/api";
import { formatDate, formatDateTime } from "../src/lib/datetime";
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
type ChartDatum = { label: string; value: number };

function HomeBarChart({
  title,
  data,
  emptyLabel
}: {
  title: string;
  data: ChartDatum[];
  emptyLabel: string;
}) {
  const maxValue = data.reduce((max, item) => (item.value > max ? item.value : max), 0);

  return (
    <section className="homeChartCard">
      <h3 className="changesGroupTitle">{title}</h3>
      {!data.length || maxValue <= 0 ? <p className="meta">{emptyLabel}</p> : null}
      <div className="homeChartRows">
        {data.map((item) => {
          const pct = maxValue > 0 ? Math.max(4, (item.value / maxValue) * 100) : 0;
          return (
            <div key={item.label} className="homeChartRow">
              <div className="homeChartLabel">{item.label}</div>
              <div className="homeChartTrack">
                <div className="homeChartFill" style={{ width: `${pct}%` }} />
              </div>
              <div className="homeChartValue">{item.value}</div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

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
  const taskStatusSeries = useMemo<ChartDatum[]>(
    () =>
      ["in_progress", "todo", "done", "cancelled", "archived"]
        .map((status) => ({
          label: taskStatusLabel(status),
          value: snapshot.task.statusCounts[status] ?? 0
        }))
        .filter((item) => item.value > 0),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [snapshot.task.statusCounts, lang]
  );
  const inProgressPrioritySeries = useMemo<ChartDatum[]>(
    () =>
      ["P0", "P1", "P2", "P3", "none"]
        .map((priority) => ({
          label: priority === "none" ? t("tasks.none") : priority,
          value: snapshot.task.inProgressPriorityCounts[priority] ?? 0
        }))
        .filter((item) => item.value > 0),
    [snapshot.task.inProgressPriorityCounts, t]
  );
  const categorySeries = useMemo<ChartDatum[]>(
    () =>
      categoryEntries.map(([category, count]) => ({
        label: knowledgeCategoryLabel(category),
        value: count
      })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [categoryEntries, lang]
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

  function taskStudioLink(task: TaskSummary): string {
    const params = new URLSearchParams({ status: "all", workspace: "studio", detail: "open" });
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

      <div className="homeDashboardLayout">
        <div className="homeMainColumn">
        <section className="card homePanel">
          <h2 className="changesSubTitle">{t("home.global.title")}</h2>
          <div className="homeMetricRail">
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
          <div className="homeChartGrid">
            <HomeBarChart
              title={t("home.global.taskStatusChart")}
              data={taskStatusSeries}
              emptyLabel={t("home.chart.empty")}
            />
            <HomeBarChart
              title={t("home.global.inProgressPriorityChart")}
              data={inProgressPrioritySeries}
              emptyLabel={t("home.chart.empty")}
            />
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
          <div className="homeList homeFocusList">
            {tasksLoading ? (
              <p className="meta">{t("home.loading")}</p>
            ) : tasksError ? (
              <p className="meta" style={{ color: "var(--danger)" }}>
                {t("home.error")}: {tasksError}
              </p>
            ) : snapshot.task.focus.length ? (
              snapshot.task.focus.map((task) => (
                <article key={task.id} className="homeFocusItem">
                  <div>
                    <div className="taskTitle">{task.title}</div>
                    <div className="taskMetaLine">
                      <span>{t("tasks.priority")}: {task.priority || "-"}</span>
                      <span>{t("tasks.status")}: {taskStatusLabel(task.status)}</span>
                      <span>{t("tasks.due")}: {formatDate(task.due, lang)}</span>
                      <span>
                        {t("tasks.updated")}: <span className="homeDateFull">{formatDateTime(task.updated_at, lang)}</span>
                        <span className="homeDateCompact">{formatDate(task.updated_at, lang)}</span>
                      </span>
                    </div>
                  </div>
                  <div className="homeFocusActions">
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
        </div>

        <aside className="homeSideColumn">
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
          <HomeBarChart
            title={t("home.knowledge.categoryChart")}
            data={categorySeries}
            emptyLabel={t("home.chart.empty")}
          />
          <h3 className="changesGroupTitle">{t("home.knowledge.byCategoryTitle")}</h3>
          <div className="badges homeCategoryBadges">
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
            <Link href="/knowledge?status=active" className="badge">
              {t("home.knowledge.openKnowledge")}
            </Link>
          </div>
        </section>
        </aside>
      </div>
    </section>
  );
}
