"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const skill = require("./index");
const { createMemlineageClient } = require("./lib/client");

test("memlineage skill exposes comprehensive read actions", () => {
  const actionNames = Object.keys(skill.actions);
  const expected = [
    "list_topics",
    "list_ideas",
    "list_news",
    "get_news",
    "list_changes",
    "get_change",
    "list_audit_events",
    "list_task_views_summary",
    "list_note_topic_summary",
    "list_routes",
    "list_route_node_logs",
    "list_links",
    "list_inbox",
    "list_knowledge",
    "list_journal_items",
    "list_task_sources",
    "list_note_sources",
    "propose_create_idea",
    "propose_create_route",
    "propose_create_route_node",
    "propose_create_knowledge",
    "propose_capture_news_batch",
    "propose_patch_news",
    "propose_archive_news",
    "propose_delete_news",
    "propose_create_link",
    "propose_capture_inbox",
    "api_get",
  ];

  for (const action of expected) {
    assert.ok(actionNames.includes(action), `missing action: ${action}`);
  }
});

test("route edge skill actions use connector-only contract", () => {
  const actionNames = Object.keys(skill.actions);
  assert.ok(actionNames.includes("propose_create_route_edge"));
  assert.ok(actionNames.includes("propose_delete_route_edge"));
  assert.ok(!actionNames.includes("propose_patch_route_edge"));

  const createProps = skill.actions.propose_create_route_edge.parameters.properties;
  assert.ok(Object.prototype.hasOwnProperty.call(createProps, "route_id"));
  assert.ok(Object.prototype.hasOwnProperty.call(createProps, "from_node_id"));
  assert.ok(Object.prototype.hasOwnProperty.call(createProps, "to_node_id"));
  assert.ok(!Object.prototype.hasOwnProperty.call(createProps, "relation"));
  assert.ok(!Object.prototype.hasOwnProperty.call(createProps, "description"));
});

test("list_tasks supports full backend query filters", () => {
  const properties = skill.actions.list_tasks.parameters.properties;
  const expectedFilters = ["archived", "stale_days", "due_before", "updated_before", "view"];
  for (const key of expectedFilters) {
    assert.ok(Object.prototype.hasOwnProperty.call(properties, key), `missing list_tasks filter: ${key}`);
  }
});

test("get_task_execution_snapshot supports natural-language task query fields", () => {
  const properties = skill.actions.get_task_execution_snapshot.parameters.properties;
  const queryFields = ["task_query", "task_title", "q"];
  for (const key of queryFields) {
    assert.ok(Object.prototype.hasOwnProperty.call(properties, key), `missing query field: ${key}`);
  }
  const required = skill.actions.get_task_execution_snapshot.parameters.required || [];
  assert.ok(!required.includes("task_id"), "task_id should not be a hard requirement");
});

test("api_get enforces relative /api/v1 path and forwards params", async () => {
  const oldBaseUrl = process.env.KMS_BASE_URL;
  const oldApiKey = process.env.KMS_API_KEY;
  const oldFetch = global.fetch;

  process.env.KMS_BASE_URL = "http://127.0.0.1:8000";
  process.env.KMS_API_KEY = "test-key";
  global.fetch = async (url) => ({
    ok: true,
    status: 200,
    json: async () => ({ url }),
    text: async () => "",
  });

  try {
    const client = createMemlineageClient({});
    await assert.rejects(
      async () => client.apiGet("http://example.com/api/v1/tasks", {}),
      /path must start with '\/'/
    );
    await assert.rejects(async () => client.apiGet("/health", {}), /path must start with \/api\/v1\//);

    const out = await client.apiGet("/api/v1/tasks", { page: 1, page_size: 20 });
    assert.equal(out.url, "http://127.0.0.1:8000/api/v1/tasks?page=1&page_size=20");
  } finally {
    process.env.KMS_BASE_URL = oldBaseUrl;
    process.env.KMS_API_KEY = oldApiKey;
    global.fetch = oldFetch;
  }
});

test("getTaskExecutionSnapshot resolves task from natural-language query", async () => {
  const oldBaseUrl = process.env.KMS_BASE_URL;
  const oldApiKey = process.env.KMS_API_KEY;
  const oldFetch = global.fetch;

  process.env.KMS_BASE_URL = "http://127.0.0.1:8000";
  process.env.KMS_API_KEY = "test-key";
  const calls = [];
  global.fetch = async (url) => {
    const u = String(url);
    calls.push(u);
    if (u.includes("/api/v1/tasks?")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          items: [
            {
              id: "tsk_1",
              title: "agent-first saas",
              status: "in_progress",
              updated_at: "2026-02-27T12:00:00Z",
            },
          ],
        }),
        text: async () => "",
      };
    }
    if (u.includes("/api/v1/routes?")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({ items: [{ id: "rte_1", status: "active" }] }),
        text: async () => "",
      };
    }
    if (u.includes("/api/v1/routes/rte_1/graph")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          route_id: "rte_1",
          nodes: [
            { id: "n1", node_type: "goal", title: "开源推广", status: "execute", order_hint: 1 },
            { id: "n0", node_type: "start", title: "Start", status: "done", order_hint: 0 },
          ],
          edges: [{ id: "e1", from_node_id: "n0", to_node_id: "n1" }],
        }),
        text: async () => "",
      };
    }
    throw new Error(`unexpected url: ${u}`);
  };

  try {
    const client = createMemlineageClient({});
    const out = await client.getTaskExecutionSnapshot({ task_query: "agent-first saas" });
    assert.equal(out.needs_disambiguation, false);
    assert.equal(out.task_id, "tsk_1");
    assert.equal(out.selected_route_id, "rte_1");
    assert.equal(out.selected_route_state.current_node.title, "开源推广");
    assert.ok(calls.some((u) => u.includes("/api/v1/tasks?")), "should query tasks by natural language");
  } finally {
    process.env.KMS_BASE_URL = oldBaseUrl;
    process.env.KMS_API_KEY = oldApiKey;
    global.fetch = oldFetch;
  }
});

test("getTaskExecutionSnapshot returns disambiguation candidates when task query is ambiguous", async () => {
  const oldBaseUrl = process.env.KMS_BASE_URL;
  const oldApiKey = process.env.KMS_API_KEY;
  const oldFetch = global.fetch;

  process.env.KMS_BASE_URL = "http://127.0.0.1:8000";
  process.env.KMS_API_KEY = "test-key";
  global.fetch = async (url) => {
    const u = String(url);
    if (u.includes("/api/v1/tasks?")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          items: [
            { id: "tsk_a", title: "route upgrade", status: "in_progress", updated_at: "2026-02-27T12:00:00Z" },
            { id: "tsk_b", title: "route upgrade", status: "todo", updated_at: "2026-02-26T12:00:00Z" },
          ],
        }),
        text: async () => "",
      };
    }
    throw new Error(`unexpected url: ${u}`);
  };

  try {
    const client = createMemlineageClient({});
    const out = await client.getTaskExecutionSnapshot({ task_query: "route upgrade" });
    assert.equal(out.needs_disambiguation, true);
    assert.equal(out.task_id, null);
    assert.equal(out.selected_route_id, null);
    assert.equal(out.task_resolution.candidates.length, 2);
  } finally {
    process.env.KMS_BASE_URL = oldBaseUrl;
    process.env.KMS_API_KEY = oldApiKey;
    global.fetch = oldFetch;
  }
});

test("news skill actions expose batch capture and maintenance contract", () => {
  const actions = skill.actions;
  assert.ok(actions.list_news);
  assert.ok(actions.get_news);
  assert.ok(actions.propose_capture_news_batch);
  assert.ok(actions.propose_patch_news);
  assert.ok(actions.propose_archive_news);
  assert.ok(actions.propose_delete_news);
  assert.ok(!actions.propose_promote_news_to_task);
  assert.ok(!actions.propose_promote_news_to_knowledge);

  assert.ok(!Object.prototype.hasOwnProperty.call(actions.list_news.parameters.properties, "topic_id"));

  const batchItems = actions.propose_capture_news_batch.parameters.properties.items;
  assert.equal(batchItems.type, "array");
  assert.ok(batchItems.items);
  assert.ok(batchItems.items.properties.primary_source_url);
  assert.ok(batchItems.items.properties.reference_urls);
  assert.ok(batchItems.items.properties.raw_payload_json);
  assert.ok(!batchItems.items.properties.topic_id);

  const patchProps = actions.propose_patch_news.parameters.properties;
  assert.ok(!Object.prototype.hasOwnProperty.call(patchProps, "topic_id"));
});

test("proposeCaptureNewsBatch expands into one dry-run with multiple create_news actions", async () => {
  const oldBaseUrl = process.env.KMS_BASE_URL;
  const oldApiKey = process.env.KMS_API_KEY;
  const oldFetch = global.fetch;

  process.env.KMS_BASE_URL = "http://127.0.0.1:8000";
  process.env.KMS_API_KEY = "test-key";

  let body = null;
  global.fetch = async (_url, options) => {
    body = JSON.parse(String(options && options.body));
    return {
      ok: true,
      status: 200,
      json: async () => ({ change_set_id: "chg_news_batch" }),
      text: async () => "",
    };
  };

  try {
    const client = createMemlineageClient({});
    const out = await client.proposeCaptureNewsBatch({
      items: [
        {
          title: "news A",
          summary: "summary A",
          opportunity: "opp A",
          risk: "risk A",
          primary_source_url: "https://example.com/a",
          reference_urls: ["https://example.com/a-2"],
          published_at: "2026-03-07T10:00:00Z",
          captured_at: "2026-03-08T08:00:00Z",
          tags: ["ai"],
          raw_payload_json: { id: "a" },
        },
        {
          title: "news B",
          summary: "summary B",
          opportunity: "opp B",
          risk: "risk B",
          primary_source_url: "https://example.com/b",
          reference_urls: [],
          published_at: "2026-03-07T11:00:00Z",
          captured_at: "2026-03-08T08:05:00Z",
          tags: ["agents"],
          raw_payload_json: { id: "b" },
        },
      ],
    });

    assert.equal(out.change_set_id, "chg_news_batch");
    assert.equal(body.actions.length, 2);
    assert.equal(body.actions[0].type, "create_news");
    assert.equal(body.actions[1].type, "create_news");
    assert.equal(body.actions[0].payload.sources[0].role, "primary");
    assert.equal(body.actions[0].payload.sources[1].role, "reference");
    assert.ok(!Object.prototype.hasOwnProperty.call(body.actions[1].payload, "topic_id"));
  } finally {
    process.env.KMS_BASE_URL = oldBaseUrl;
    process.env.KMS_API_KEY = oldApiKey;
    global.fetch = oldFetch;
  }
});
