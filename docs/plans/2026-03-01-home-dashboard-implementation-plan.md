# Home Dashboard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为个人用户新增首页看板（Home Dashboard），聚合 `Tasks / Knowledge / Changes` 的全局概览与可行动入口。

**Architecture:** 前端在 `app/page.tsx` 实现客户端看板页面，复用现有 REST API（`/tasks`、`/knowledge`、`/changes`）拉取数据并在前端做轻量聚合。任务区采用“统计 + 焦点列表”混合模式（优先 `P0 in_progress`），其余区域显示核心指标与最近记录。首页指标可跳转到目标页面，目标页面支持 URL 查询参数初始化筛选状态。

**Tech Stack:** Next.js 14 (App Router), React 18, TypeScript, existing REST API wrappers (`apiGet`), existing i18n dictionary.

---

### Task 1: 首页路由与导航入口落地

**Files:**
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/src/components/shell.tsx`
- Modify: `frontend/src/i18n.tsx`

**Step 1: Write the failing check (current behavior)**

Run: `cd frontend && npm run dev`  
Manual check: 打开 `/`，当前会直接跳转 `/tasks`，不满足“首页看板”需求。

**Step 2: Run check to verify failure**

Expected: FAIL（没有看板，仅 redirect）。

**Step 3: Write minimal implementation**

1. `app/page.tsx` 从 redirect 改为 `HomeDashboardPage` 客户端页面（先放骨架和标题）。
2. `shell.tsx` 导航增加 Home 链接：`{ href: "/", key: "nav.home" }`。
3. `i18n.tsx` 增加最小文案键：
   - `nav.home`
   - `home.title`
   - `home.subtitle`

**Step 4: Run verification**

Run: `cd frontend && npm run build`  
Expected: PASS（可进入 `/` 且构建通过）。

**Step 5: Commit**

```bash
git add frontend/app/page.tsx frontend/src/components/shell.tsx frontend/src/i18n.tsx
git commit -m "feat(frontend): scaffold home dashboard route and nav entry"
```

### Task 2: 首页数据聚合层（Task/Knowledge/Changes）

**Files:**
- Create: `frontend/src/lib/home-dashboard.ts`
- Modify: `frontend/app/page.tsx`

**Step 1: Write the failing check**

在 `app/page.tsx` 中临时调用未实现的聚合方法（例如 `buildHomeSnapshot`）并触发构建。

**Step 2: Run check to verify it fails**

Run: `cd frontend && npm run build`  
Expected: FAIL（函数未定义/导出缺失）。

**Step 3: Write minimal implementation**

在 `src/lib/home-dashboard.ts` 新增纯函数和类型：

```ts
export type HomeSnapshot = {
  global: { taskTotal: number; taskInProgress: number; p0InProgress: number; proposedChanges: number; knowledgeTotal: number };
  task: { blockedCount: number; dueTodayCount: number; focus: TaskSummary[] };
  knowledge: { byCategory: Record<string, number>; recent: KnowledgeSummary[] };
  changes: { recentProposed: ChangeSummary[]; latestCommittedAt: string | null };
};

export function buildHomeSnapshot(input: { tasks: TaskSummary[]; knowledge: KnowledgeSummary[]; changes: ChangeSummary[] }): HomeSnapshot { /* ... */ }
export function rankFocusTasks(tasks: TaskSummary[]): TaskSummary[] { /* P0/in_progress 优先 */ }
```

在 `app/page.tsx` 调用该聚合层而不是在 JSX 内散写统计逻辑。

**Step 4: Run verification**

Run: `cd frontend && npm run build`  
Expected: PASS。

**Step 5: Commit**

```bash
git add frontend/src/lib/home-dashboard.ts frontend/app/page.tsx
git commit -m "feat(frontend): add home dashboard aggregation and focus ranking helpers"
```

### Task 3: 首页 UI（全局条 + 任务看板 + 变更看板 + 知识看板）

**Files:**
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/src/i18n.tsx`

**Step 1: Write the failing check**

Manual check目标：`/` 页面需要同时看到三块信息（Task/Knowledge/Changes）和顶部全局条。当前仅骨架，不满足。

**Step 2: Run check to verify it fails**

Run: `cd frontend && npm run dev`  
Expected: FAIL（信息不足，缺少完整板块）。

**Step 3: Write minimal implementation**

1. 在 `page.tsx` 增加四个区块：
   - `Global Snapshot`
   - `Task Board`（统计 + focus list ≤ 5）
   - `Changes Board`（proposed 指标 + 最近 3 条）
   - `Knowledge Board`（总数/分类计数 + 最近 5 条）
2. 补齐 i18n 键（en/zh）：
   - `home.global.*`
   - `home.tasks.*`
   - `home.changes.*`
   - `home.knowledge.*`
   - `home.loading` / `home.empty` / `home.error`
3. 样式落在 `globals.css`，保持现有视觉语言（粗描边、浅底、紧凑卡片）。

**Step 4: Run verification**

Run: `cd frontend && npm run build`  
Expected: PASS。

**Step 5: Commit**

```bash
git add frontend/app/page.tsx frontend/app/globals.css frontend/src/i18n.tsx
git commit -m "feat(frontend): implement home dashboard sections and localized copy"
```

### Task 4: 焦点任务规则与可行动跳转

**Files:**
- Modify: `frontend/src/lib/home-dashboard.ts`
- Modify: `frontend/app/page.tsx`

**Step 1: Write the failing check**

人工构造场景检查：存在 `P0 + in_progress` 与普通 `in_progress` 时，当前排序/展示若不稳定则视为失败。

**Step 2: Run check to verify it fails**

Run: `cd frontend && npm run dev`  
Expected: FAIL（焦点列表排序未明确保障或不可解释）。

**Step 3: Write minimal implementation**

`rankFocusTasks` 明确排序规则（稳定且可解释）：
1. `priority === P0 && status === in_progress`
2. `status === in_progress && due 最近`
3. `updated_at` 最近
4. `title` 作为最终稳定 tie-break

并在 UI 中固定展示字段：标题、优先级、状态、更新时间、按钮（打开任务/进入执行）。

**Step 4: Run verification**

Run: `cd frontend && npm run build`  
Expected: PASS。

**Step 5: Commit**

```bash
git add frontend/src/lib/home-dashboard.ts frontend/app/page.tsx
git commit -m "feat(frontend): enforce deterministic focus task ordering and actions"
```

### Task 5: 目标页面筛选参数初始化（深链）

**Files:**
- Modify: `frontend/app/tasks/page.tsx`
- Modify: `frontend/app/knowledge/page.tsx`
- Optional: `frontend/app/changes/page.tsx`（如需支持 query 初始化）

**Step 1: Write the failing check**

手动打开深链：
- `/tasks?status=in_progress&priority=P0`
- `/knowledge?status=active&category=ops_manual`

当前页面通常不会按 query 初始化筛选（或行为不稳定）。

**Step 2: Run check to verify it fails**

Run: `cd frontend && npm run dev`  
Expected: FAIL（筛选未按 URL 生效）。

**Step 3: Write minimal implementation**

在对应页面 mount 时读取 `URLSearchParams` 并安全映射到 filter state，仅接受白名单值：

```ts
const allowedStatus = new Set(["all","todo","in_progress","done","cancelled","archived"]);
const next = params.get("status");
if (next && allowedStatus.has(next)) setFilterStatus(next as FilterStatus);
```

首页跳转使用上述 query 形成行动闭环。

**Step 4: Run verification**

Run: `cd frontend && npm run build`  
Expected: PASS。

**Step 5: Commit**

```bash
git add frontend/app/tasks/page.tsx frontend/app/knowledge/page.tsx frontend/app/changes/page.tsx
git commit -m "feat(frontend): support query-driven filter hydration for dashboard deep links"
```

### Task 6: 异常态与空态统一、性能护栏

**Files:**
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/src/lib/home-dashboard.ts`
- Modify: `frontend/src/i18n.tsx`

**Step 1: Write the failing check**

模拟任一 API 失败（断开后端或改错 URL），当前页面若出现整屏崩溃/空白则为失败。

**Step 2: Run check to verify it fails**

Run: `cd frontend && npm run dev`  
Expected: FAIL（异常态处理不完整）。

**Step 3: Write minimal implementation**

1. 每个版块独立 loading/error/empty，不让单点失败拖垮首页。
2. 聚合函数对缺字段兜底（例如 `blocked_by_task_id` 不存在时按 `0` 处理）。
3. 控制列表上限（focus ≤ 5，changes ≤ 3，knowledge ≤ 5）避免首页过长。

**Step 4: Run verification**

Run: `cd frontend && npm run build`  
Expected: PASS。

**Step 5: Commit**

```bash
git add frontend/app/page.tsx frontend/src/lib/home-dashboard.ts frontend/src/i18n.tsx
git commit -m "fix(frontend): harden home dashboard loading error and empty states"
```

### Task 7: 文档同步与验收记录

**Files:**
- Modify: `docs/reports/mvp-release-notes.md`
- Create: `docs/reports/2026-03-01-home-dashboard-changelog.md`

**Step 1: Write the failing check**

检查文档：当前尚无首页看板交付说明与验收记录。

**Step 2: Run check to verify it fails**

Run: `rg -n "home dashboard|首页看板" docs/reports -S`  
Expected: 无或不完整。

**Step 3: Write minimal implementation**

1. 在 `mvp-release-notes.md` 增补 Home Dashboard 交付项。
2. 新增本次变更日志，记录：
   - 交付范围
   - 跳转策略
   - 已执行验证命令

**Step 4: Run verification**

Run: `git diff -- docs/reports`  
Expected: 文档更新项完整且可读。

**Step 5: Commit**

```bash
git add docs/reports/mvp-release-notes.md docs/reports/2026-03-01-home-dashboard-changelog.md
git commit -m "docs: add home dashboard release notes and changelog"
```

## Final Verification & Handoff

1. Frontend build:
   - `cd frontend && npm run build`
2. Backend regression guard (avoid dashboard改动误伤后端):
   - `cd backend && python3 -m pytest tests/test_routes_api.py -q`
3. Manual acceptance checklist:
   - `/` 展示 Task/Knowledge/Changes 三块
   - 任务焦点列表排序符合规则
   - 点击首页卡片可跳转并带筛选语义
   - 中英文切换无混语（尤其分类与时间格式）

## Plan Constraints & Guidance

1. DRY: 聚合与排序逻辑统一放在 `src/lib/home-dashboard.ts`，页面只做展示。
2. YAGNI: V1 不新增后端接口，先用现有 API 前端聚合。
3. i18n-first: 不允许硬编码可见文案。
4. Verification-first: 每个 Task 完成后先跑验证再提交。
5. Skills 建议：`@verification-before-completion`、`@requesting-code-review`。

