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

export type HomeSnapshot = {
  global: {
    taskTotal: number;
    taskInProgress: number;
    p0InProgress: number;
    proposedChanges: number;
    knowledgeTotal: number;
  };
  task: {
    blockedCount: number;
    dueTodayCount: number;
    focus: TaskSummary[];
  };
  knowledge: {
    byCategory: Record<string, number>;
    recent: KnowledgeSummary[];
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

    if (aInProgress && bInProgress) {
      const aDue = toTime(a.due);
      const bDue = toTime(b.due);
      if (aDue !== bDue) {
        if (!aDue) return 1;
        if (!bDue) return -1;
        return aDue - bDue;
      }
    }

    const updatedDiff = toTime(b.updated_at) - toTime(a.updated_at);
    if (updatedDiff !== 0) return updatedDiff;

    return a.title.localeCompare(b.title);
  });
}

export function buildHomeSnapshot(input: {
  tasks: TaskSummary[];
  knowledge: KnowledgeSummary[];
  changes: ChangeSummary[];
}): HomeSnapshot {
  const tasks = Array.isArray(input.tasks) ? input.tasks : [];
  const knowledge = Array.isArray(input.knowledge) ? input.knowledge : [];
  const changes = Array.isArray(input.changes) ? input.changes : [];

  const taskInProgress = tasks.filter((task) => task.status === "in_progress");
  const p0InProgress = taskInProgress.filter((task) => task.priority === "P0");
  const proposed = changes.filter((change) => change.status === "proposed");

  const byCategory = knowledge.reduce<Record<string, number>>((acc, item) => {
    const key = item.category || "unclassified";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});

  const recentKnowledge = [...knowledge]
    .sort((a, b) => toTime(b.updated_at) - toTime(a.updated_at))
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
      knowledgeTotal: knowledge.length
    },
    task: {
      blockedCount: tasks.filter((item) => Boolean(item.blocked_by_task_id)).length,
      dueTodayCount: tasks.filter((item) => isDueToday(item.due)).length,
      focus: rankFocusTasks(tasks).slice(0, 5)
    },
    knowledge: {
      byCategory,
      recent: recentKnowledge
    },
    changes: {
      recentProposed,
      latestCommittedAt
    }
  };
}
