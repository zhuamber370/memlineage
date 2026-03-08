export type TaskSummary = {
  id: string;
  title: string;
  status: string;
  priority?: string | null;
  due?: string | null;
  updated_at?: string | null;
  blocked_by_task_id?: string | null;
};

export type KnowledgeSummary = {
  id: string;
  title: string;
  category?: string | null;
  updated_at?: string | null;
};

export type ChangeSummary = {
  change_set_id: string;
  status: string;
  created_at: string;
  committed_at?: string | null;
};

export type NewsSourceSummary = {
  role: "primary" | "reference";
  url: string;
};

export type NewsSummary = {
  id: string;
  title: string;
  status: string;
  published_at?: string | null;
  captured_at?: string | null;
  tags?: string[];
  sources: NewsSourceSummary[];
};

export type HomeSnapshot = {
  global: {
    taskTotal: number;
    taskInProgress: number;
    p0InProgress: number;
    proposedChanges: number;
    knowledgeTotal: number;
    newsTotal: number;
  };
  task: {
    blockedCount: number;
    dueTodayCount: number;
    focus: TaskSummary[];
    statusCounts: Record<string, number>;
    inProgressPriorityCounts: Record<string, number>;
  };
  knowledge: {
    byCategory: Record<string, number>;
    recent: KnowledgeSummary[];
  };
  news: {
    statusCounts: Record<string, number>;
    recent: NewsSummary[];
  };
  changes: {
    recentProposed: ChangeSummary[];
    latestCommittedAt: string | null;
  };
};

function toTime(value?: string | null): number {
  if (!value) return 0;
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function toText(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function isDueToday(due?: string | null): boolean {
  if (!due) return false;
  const d = new Date(due);
  if (Number.isNaN(d.getTime())) return false;
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

export function rankFocusTasks(tasks: TaskSummary[]): TaskSummary[] {
  return [...tasks].sort((a, b) => {
    const aP0InProgress = a.priority === "P0" && a.status === "in_progress";
    const bP0InProgress = b.priority === "P0" && b.status === "in_progress";
    if (aP0InProgress !== bP0InProgress) return aP0InProgress ? -1 : 1;

    const aInProgress = a.status === "in_progress";
    const bInProgress = b.status === "in_progress";
    if (aInProgress !== bInProgress) return aInProgress ? -1 : 1;

    const aDue = toTime(a.due);
    const bDue = toTime(b.due);
    if (aDue !== bDue) {
      if (!aDue) return 1;
      if (!bDue) return -1;
      return aDue - bDue;
    }

    const updatedDiff = toTime(b.updated_at) - toTime(a.updated_at);
    if (updatedDiff !== 0) return updatedDiff;

    return a.title.localeCompare(b.title);
  });
}

export function buildHomeSnapshot(input: {
  tasks: TaskSummary[];
  knowledge: KnowledgeSummary[];
  news: NewsSummary[];
  changes: ChangeSummary[];
}): HomeSnapshot {
  const tasks: TaskSummary[] = (Array.isArray(input.tasks) ? input.tasks : []).map((task) => ({
    id: toText(task?.id),
    title: toText(task?.title),
    status: toText(task?.status),
    priority: toText(task?.priority) || null,
    due: toText(task?.due) || null,
    updated_at: toText(task?.updated_at) || null,
    blocked_by_task_id: toText(task?.blocked_by_task_id) || null
  }));
  const knowledge: KnowledgeSummary[] = (Array.isArray(input.knowledge) ? input.knowledge : []).map((item) => ({
    id: toText(item?.id),
    title: toText(item?.title),
    category: toText(item?.category) || null,
    updated_at: toText(item?.updated_at) || null
  }));
  const news: NewsSummary[] = (Array.isArray(input.news) ? input.news : []).map((item) => ({
    id: toText(item?.id),
    title: toText(item?.title),
    status: toText(item?.status),
    published_at: toText(item?.published_at) || null,
    captured_at: toText(item?.captured_at) || null,
    tags: Array.isArray(item?.tags) ? item.tags.filter((tag): tag is string => typeof tag === "string") : [],
    sources: Array.isArray(item?.sources)
      ? item.sources
          .filter((source): source is NewsSourceSummary => {
            return Boolean(source) && typeof source.url === "string" && typeof source.role === "string";
          })
          .map((source) => ({
            role: source.role === "reference" ? "reference" : "primary",
            url: source.url
          }))
      : []
  }));
  const changes: ChangeSummary[] = (Array.isArray(input.changes) ? input.changes : []).map((item) => ({
    change_set_id: toText(item?.change_set_id),
    status: toText(item?.status),
    created_at: toText(item?.created_at),
    committed_at: toText(item?.committed_at) || null
  }));

  const taskInProgress = tasks.filter((task) => task.status === "in_progress");
  const p0InProgress = taskInProgress.filter((task) => task.priority === "P0");
  const proposed = changes.filter((change) => change.status === "proposed");

  const byCategory = knowledge.reduce<Record<string, number>>((acc, item) => {
    const key = item.category || "unclassified";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});

  const statusCounts = tasks.reduce<Record<string, number>>((acc, task) => {
    const key = task.status || "unknown";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});

  const inProgressPriorityCounts = taskInProgress.reduce<Record<string, number>>((acc, task) => {
    const key = task.priority || "none";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});

  const recentKnowledge = [...knowledge]
    .sort((a, b) => toTime(b.updated_at) - toTime(a.updated_at))
    .slice(0, 5);
  const newsStatusCounts = news.reduce<Record<string, number>>((acc, item) => {
    const key = item.status || "unknown";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});
  const recentNews = [...news]
    .sort((a, b) => toTime(b.published_at) - toTime(a.published_at) || toTime(b.captured_at) - toTime(a.captured_at))
    .slice(0, 5);

  const recentProposed = [...proposed]
    .sort((a, b) => toTime(b.created_at) - toTime(a.created_at))
    .slice(0, 3);

  const latestCommittedAt =
    [...changes]
      .map((item) => item.committed_at || "")
      .filter((value) => Boolean(value))
      .sort((a, b) => toTime(b) - toTime(a))[0] || null;

  return {
    global: {
      taskTotal: tasks.length,
      taskInProgress: taskInProgress.length,
      p0InProgress: p0InProgress.length,
      proposedChanges: proposed.length,
      knowledgeTotal: knowledge.length,
      newsTotal: news.length
    },
    task: {
      blockedCount: tasks.filter((item) => Boolean(item.blocked_by_task_id)).length,
      dueTodayCount: tasks.filter((item) => isDueToday(item.due)).length,
      focus: rankFocusTasks(tasks).slice(0, 5),
      statusCounts,
      inProgressPriorityCounts
    },
    knowledge: {
      byCategory,
      recent: recentKnowledge
    },
    news: {
      statusCounts: newsStatusCounts,
      recent: recentNews
    },
    changes: {
      recentProposed,
      latestCommittedAt
    }
  };
}
