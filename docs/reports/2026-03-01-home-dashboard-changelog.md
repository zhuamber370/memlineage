# 2026-03-01 Home Dashboard Changelog

## 交付范围
- 新增首页看板路由 `/`，替代原先直接重定向到 `/tasks` 的行为。
- 首页落地四块信息区：
  - Global Snapshot
  - Task Board（统计 + 焦点任务）
  - Changes Board（proposed 指标 + 最近提案）
  - Knowledge Board（总数/分类 + 最近更新）
- 新增聚合层 `frontend/src/lib/home-dashboard.ts`，统一承担首页统计与焦点排序逻辑。
- 导航新增 Home 入口，补齐中英文文案（含 loading/error/empty）。
- 深链筛选初始化：
  - `/tasks` 支持 `status/priority/topic_id/workspace/task_id`
  - `/knowledge` 支持 `status/category`
  - `/changes` 支持 `status`
- 异常韧性：
  - tasks/knowledge/changes 独立加载与错误隔离
  - 任一 API 失败不会导致整页空白

## 跳转策略
- 首页全局卡片跳转并携带筛选语义：
  - 任务总览 -> `/tasks`
  - 进行中任务 -> `/tasks?status=in_progress`
  - P0 进行中 -> `/tasks?status=in_progress&priority=P0`
  - 待处理变更 -> `/changes?status=proposed`
  - 知识总览 -> `/knowledge?status=active`
- 焦点任务行动闭环：
  - 打开任务 -> `/tasks?status=in_progress&priority=P0|...&task_id=<id>`
  - 进入执行 -> `/tasks?status=in_progress&workspace=studio&task_id=<id>`

## 已执行验证命令
- Task 1 失败校验：
  - `cd frontend && npm run dev` + `curl -I http://127.0.0.1:3000/`（确认 `307 Location: /tasks`）
- Task 2 失败校验：
  - `cd frontend && npm run build`（在未实现聚合层时，报 `Module not found`）
- Task 1~6 每任务完成后验证：
  - `cd frontend && npm run build`（均通过）
- Task 7 文档缺失校验：
  - `rg -n "home dashboard|首页看板" docs/reports -S`（更新前无命中）
- Task 7 文档差异校验：
  - `git diff -- docs/reports`

## 提交记录
- `6597d5f` feat(frontend): scaffold home dashboard route and nav entry
- `5fedd5f` feat(frontend): add home dashboard aggregation and focus ranking helpers
- `d4d2e69` feat(frontend): implement home dashboard sections and localized copy
- `7ff1cbe` feat(frontend): enforce deterministic focus task ordering and actions
- `bebcd80` feat(frontend): support query-driven filter hydration for dashboard deep links
- `34f1ddc` fix(frontend): harden home dashboard loading error and empty states
