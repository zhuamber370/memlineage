from src.db import build_engine, build_session_local
from src.schemas import EntityLogCreate, EntityLogPatch
from src.services.route_service import RouteGraphService
from tests.helpers import create_test_task, database_url, make_client, uniq


def test_create_active_route_promotes_task_to_in_progress():
    client = make_client()
    task_id = create_test_task(client, prefix="route_active_promote_task")

    created = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('active_promote')}",
            "goal": "start execution",
            "status": "active",
        },
    )
    assert created.status_code == 201

    listed = client.get("/api/v1/tasks?page=1&page_size=100")
    assert listed.status_code == 200
    items = listed.json()["items"]
    task = next((item for item in items if item["id"] == task_id), None)
    assert task is not None
    assert task["status"] == "in_progress"


def test_single_active_route_enforced():
    client = make_client()
    task_id = create_test_task(client, prefix="route_active_task")

    active_list = client.get(f"/api/v1/routes?page=1&page_size=100&status=active&task_id={task_id}")
    assert active_list.status_code == 200
    active_items = active_list.json()["items"]

    seeded_active_id = None
    if not active_items:
        seeded = client.post(
            "/api/v1/routes",
            json={
                "task_id": task_id,
                "name": f"route_test_{uniq('seed')}",
                "goal": "seed active route for test",
                "status": "active",
            },
        )
        assert seeded.status_code == 201
        seeded_active_id = seeded.json()["id"]

    candidate = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('cand')}",
            "goal": "candidate route",
            "status": "candidate",
        },
    )
    assert candidate.status_code == 201
    candidate_id = candidate.json()["id"]

    to_active = client.patch(f"/api/v1/routes/{candidate_id}", json={"status": "active"})
    assert to_active.status_code == 409
    assert to_active.json()["error"]["code"] == "ROUTE_ACTIVE_CONFLICT"

    if seeded_active_id:
        park_seeded = client.patch(f"/api/v1/routes/{seeded_active_id}", json={"status": "parked"})
        assert park_seeded.status_code == 200


def test_route_create_accepts_parent_route():
    client = make_client()
    task_id = create_test_task(client, prefix="route_parent_fields_task")

    parent_route = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('parent')}",
            "goal": "parent route",
            "status": "candidate",
        },
    )
    assert parent_route.status_code == 201
    parent_route_id = parent_route.json()["id"]

    created = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('child')}",
            "goal": "child route",
            "status": "candidate",
            "parent_route_id": parent_route_id,
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["parent_route_id"] == parent_route_id


def test_route_node_create_accepts_parent_node():
    client = make_client()
    task_id = create_test_task(client, prefix="route_node_hierarchy_task")

    route = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('node_parent')}",
            "goal": "nested goals",
            "status": "candidate",
        },
    )
    assert route.status_code == 201
    route_id = route.json()["id"]

    parent_node = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "goal", "title": "Top Goal", "description": "rough objective"},
    )
    assert parent_node.status_code == 201
    parent_node_id = parent_node.json()["id"]

    created = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={
            "node_type": "goal",
            "title": "Child Goal",
            "description": "refined objective",
            "parent_node_id": parent_node_id,
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["parent_node_id"] == parent_node_id


def test_parent_node_must_be_same_route_and_acyclic():
    client = make_client()
    task_id = create_test_task(client, prefix="route_node_parent_guard_task")

    route1 = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('parent_guard_r1')}",
            "goal": "route 1",
            "status": "candidate",
        },
    )
    assert route1.status_code == 201
    route1_id = route1.json()["id"]

    route2 = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('parent_guard_r2')}",
            "goal": "route 2",
            "status": "candidate",
        },
    )
    assert route2.status_code == 201
    route2_id = route2.json()["id"]

    r1_root = client.post(
        f"/api/v1/routes/{route1_id}/nodes",
        json={"node_type": "goal", "title": "Route1 Root", "description": ""},
    )
    assert r1_root.status_code == 201
    r1_root_id = r1_root.json()["id"]

    r2_node = client.post(
        f"/api/v1/routes/{route2_id}/nodes",
        json={"node_type": "goal", "title": "Route2 Root", "description": ""},
    )
    assert r2_node.status_code == 201
    r2_node_id = r2_node.json()["id"]

    cross = client.post(
        f"/api/v1/routes/{route1_id}/nodes",
        json={
            "node_type": "goal",
            "title": "Cross Parent",
            "description": "",
            "parent_node_id": r2_node_id,
        },
    )
    assert cross.status_code == 409
    assert cross.json()["error"]["code"] == "ROUTE_NODE_PARENT_CROSS_ROUTE"

    child = client.post(
        f"/api/v1/routes/{route1_id}/nodes",
        json={
            "node_type": "goal",
            "title": "Route1 Child",
            "description": "",
            "parent_node_id": r1_root_id,
        },
    )
    assert child.status_code == 201
    child_id = child.json()["id"]

    cycle = client.patch(
        f"/api/v1/routes/{route1_id}/nodes/{r1_root_id}",
        json={"parent_node_id": child_id},
    )
    assert cycle.status_code == 409
    assert cycle.json()["error"]["code"] == "ROUTE_NODE_PARENT_CYCLE"


def test_parent_route_rewire_forbidden_when_non_candidate():
    client = make_client()
    task_id = create_test_task(client, prefix="route_parent_rewire_task")

    parent_route = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('rewire_parent')}",
            "goal": "parent route",
            "status": "candidate",
        },
    )
    assert parent_route.status_code == 201
    parent_route_id = parent_route.json()["id"]

    active_route = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('rewire_active')}",
            "goal": "active route",
            "status": "active",
        },
    )
    assert active_route.status_code == 201
    active_route_id = active_route.json()["id"]

    patched = client.patch(
        f"/api/v1/routes/{active_route_id}",
        json={"parent_route_id": parent_route_id},
    )
    assert patched.status_code == 409
    assert patched.json()["error"]["code"] == "ROUTE_PARENT_REWIRE_FORBIDDEN"


def test_append_typed_node_log():
    client = make_client()
    task_id = create_test_task(client, prefix="route_typed_log_task")

    route = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('typed_log_route')}",
            "goal": "typed logs",
            "status": "candidate",
        },
    )
    assert route.status_code == 201
    route_id = route.json()["id"]

    node = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "goal", "title": "Collect evidence", "description": ""},
    )
    assert node.status_code == 201
    node_id = node.json()["id"]

    appended = client.post(
        f"/api/v1/routes/{route_id}/nodes/{node_id}/logs",
        json={
            "content": f"benchmark report {uniq('evidence')}",
            "log_type": "evidence",
            "source_ref": "https://example.com/report",
            "actor_type": "human",
            "actor_id": "tester",
        },
    )
    assert appended.status_code == 201
    assert appended.json()["log_type"] == "evidence"
    assert appended.json()["source_ref"] == "https://example.com/report"

    listed = client.get(f"/api/v1/routes/{route_id}/nodes/{node_id}/logs")
    assert listed.status_code == 200
    item = next(row for row in listed.json()["items"] if row["id"] == appended.json()["id"])
    assert item["log_type"] == "evidence"
    assert item["source_ref"] == "https://example.com/report"


def test_node_log_compatibility_get_still_readable():
    client = make_client()
    task_id = create_test_task(client, prefix="node_log_compat_get_task")

    route = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('node_log_compat_get')}",
            "goal": "node log compatibility",
            "status": "candidate",
        },
    )
    assert route.status_code == 201
    route_id = route.json()["id"]

    node = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "goal", "title": "Compat Node", "description": ""},
    )
    assert node.status_code == 201
    node_id = node.json()["id"]

    created = client.post(
        f"/api/v1/routes/{route_id}/nodes/{node_id}/logs",
        json={
            "content": f"compat-log-{uniq('entry')}",
            "log_type": "evidence",
            "source_ref": "https://example.com/compat",
            "actor_type": "human",
            "actor_id": "tester",
        },
    )
    assert created.status_code == 201

    listed = client.get(f"/api/v1/routes/{route_id}/nodes/{node_id}/logs")
    assert listed.status_code == 200
    item = next(row for row in listed.json()["items"] if row["id"] == created.json()["id"])
    assert item["log_type"] == "evidence"
    assert item["source_ref"] == "https://example.com/compat"


def test_node_log_compatibility_snapshot_include_logs_survives_fetch_error():
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    from skill.openclaw_skill import KmsClient

    client = KmsClient(base_url="http://localhost:8000", api_key="dummy")
    client.list_routes = lambda **_: {  # type: ignore[method-assign]
        "items": [{"id": "rte_active", "status": "active"}]
    }
    client.get_route_graph = lambda _route_id: {  # type: ignore[method-assign]
        "nodes": [
            {"id": "n1", "node_type": "goal", "status": "execute"},
            {"id": "n2", "node_type": "goal", "status": "waiting"},
        ],
        "edges": [],
    }

    def _get_node_logs(_route_id: str, node_id: str):
        if node_id == "n1":
            raise RuntimeError("temporary node log failure")
        return {"items": [{"id": "nlg_ok", "content": "ok"}]}

    client.get_node_logs = _get_node_logs  # type: ignore[method-assign]

    snapshot = client.get_task_execution_snapshot(task_id="tsk_snapshot", include_logs=True)
    selected = snapshot["route_snapshots"][0]["node_logs"]
    assert selected["n1"] == []
    assert selected["n2"][0]["id"] == "nlg_ok"


def test_route_edge_logs_routes_not_exposed():
    client = make_client()
    task_id = create_test_task(client, prefix="route_edge_log_placeholder_task")

    route = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('edge_log_placeholder')}",
            "goal": "edge logs placeholder",
            "status": "candidate",
        },
    )
    assert route.status_code == 201
    route_id = route.json()["id"]

    from_node = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "idea", "title": "From", "description": ""},
    )
    assert from_node.status_code == 201
    from_node_id = from_node.json()["id"]

    to_node = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "goal", "title": "To", "description": ""},
    )
    assert to_node.status_code == 201
    to_node_id = to_node.json()["id"]

    edge = client.post(
        f"/api/v1/routes/{route_id}/edges",
        json={"from_node_id": from_node_id, "to_node_id": to_node_id},
    )
    assert edge.status_code == 201
    edge_id = edge.json()["id"]

    listed = client.get(f"/api/v1/routes/{route_id}/edges/{edge_id}/logs")
    assert listed.status_code == 404


def test_entity_log_response_shape():
    client = make_client()
    task_id = create_test_task(client, prefix="entity_log_shape_task")

    route = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('entity_log_shape')}",
            "goal": "entity log response shape",
            "status": "candidate",
        },
    )
    assert route.status_code == 201
    route_id = route.json()["id"]

    node = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "goal", "title": "Shape Node", "description": ""},
    )
    assert node.status_code == 201
    node_id = node.json()["id"]

    appended = client.post(
        f"/api/v1/routes/{route_id}/nodes/{node_id}/logs",
        json={"content": f"shape_{uniq('log')}", "actor_type": "human", "actor_id": "tester"},
    )
    assert appended.status_code == 201
    body = appended.json()
    assert "entity_type" in body
    assert "entity_id" in body
    assert "updated_at" in body
    assert body["entity_type"] == "route_node"
    assert body["entity_id"] == node_id


def test_entity_logs_crud_for_node_only():
    client = make_client()
    task_id = create_test_task(client, prefix="entity_logs_service_task")

    route = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('entity_logs_service')}",
            "goal": "service entity logs",
            "status": "candidate",
        },
    )
    assert route.status_code == 201
    route_id = route.json()["id"]

    node = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "goal", "title": "Node", "description": ""},
    )
    assert node.status_code == 201
    node_id = node.json()["id"]

    route2 = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('entity_logs_service_r2')}",
            "goal": "cross route guard",
            "status": "candidate",
        },
    )
    assert route2.status_code == 201
    route2_id = route2.json()["id"]

    route2_node = client.post(
        f"/api/v1/routes/{route2_id}/nodes",
        json={"node_type": "goal", "title": "R2 Node", "description": ""},
    )
    assert route2_node.status_code == 201
    route2_node_id = route2_node.json()["id"]

    engine = build_engine(database_url())
    session_local = build_session_local(engine)
    db = session_local()
    service = RouteGraphService(db)

    node_log = service.append_entity_log(
        route_id,
        "route_node",
        node_id,
        EntityLogCreate(content=f"node-log-{uniq('entry')}", actor_type="human", actor_id="tester"),
    )
    assert node_log.entity_type == "route_node"
    assert node_log.entity_id == node_id

    node_logs = service.list_entity_logs(route_id, "route_node", node_id)
    assert any(item.id == node_log.id for item in node_logs)

    patched_node_log = service.patch_entity_log(
        route_id,
        "route_node",
        node_id,
        node_log.id,
        EntityLogPatch(content="node-log-updated"),
    )
    assert patched_node_log is not None
    assert patched_node_log.content == "node-log-updated"

    assert service.delete_entity_log(route_id, "route_node", node_id, node_log.id) is True

    try:
        service.append_entity_log(
            route_id,
            "route_group",  # type: ignore[arg-type]
            node_id,
            EntityLogCreate(content="invalid", actor_type="human", actor_id="tester"),
        )
        assert False, "expected ROUTE_ENTITY_TYPE_UNSUPPORTED"
    except ValueError as exc:
        assert str(exc) == "ROUTE_ENTITY_TYPE_UNSUPPORTED"

    try:
        service.append_entity_log(
            route_id,
            "route_node",
            route2_node_id,
            EntityLogCreate(content="cross-route", actor_type="human", actor_id="tester"),
        )
        assert False, "expected ROUTE_ENTITY_CROSS_ROUTE"
    except ValueError as exc:
        assert str(exc) == "ROUTE_ENTITY_CROSS_ROUTE"

    try:
        service.append_entity_log(
            route_id,
            "route_node",
            node_id,
            EntityLogCreate(content="   ", actor_type="human", actor_id="tester"),
        )
        assert False, "expected ROUTE_LOG_CONTENT_EMPTY"
    except ValueError as exc:
        assert str(exc) == "ROUTE_LOG_CONTENT_EMPTY"

    try:
        service.patch_entity_log(
            route_id,
            "route_node",
            node_id,
            "elg_missing",
            EntityLogPatch(content="x"),
        )
        assert False, "expected ROUTE_ENTITY_LOG_NOT_FOUND"
    except ValueError as exc:
        assert str(exc) == "ROUTE_ENTITY_LOG_NOT_FOUND"

    db.close()
    engine.dispose()


def test_entity_log_routes_exposed_for_nodes_only():
    client = make_client()
    task_id = create_test_task(client, prefix="entity_log_routes_task")

    route = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('entity_log_routes')}",
            "goal": "entity log route exposure",
            "status": "candidate",
        },
    )
    assert route.status_code == 201
    route_id = route.json()["id"]

    node1 = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "goal", "title": "N1", "description": ""},
    )
    assert node1.status_code == 201
    node1_id = node1.json()["id"]

    node2 = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "goal", "title": "N2", "description": ""},
    )
    assert node2.status_code == 201
    node2_id = node2.json()["id"]

    edge = client.post(
        f"/api/v1/routes/{route_id}/edges",
        json={"from_node_id": node1_id, "to_node_id": node2_id},
    )
    assert edge.status_code == 201
    edge_id = edge.json()["id"]

    node_log = client.post(
        f"/api/v1/routes/{route_id}/nodes/{node1_id}/logs",
        json={"content": f"node-log-{uniq('route')}", "actor_type": "human", "actor_id": "tester"},
    )
    assert node_log.status_code == 201
    node_log_id = node_log.json()["id"]

    patched_node_log = client.patch(
        f"/api/v1/routes/{route_id}/nodes/{node1_id}/logs/{node_log_id}",
        json={"content": "node-log-updated"},
    )
    assert patched_node_log.status_code == 200
    assert patched_node_log.json()["content"] == "node-log-updated"

    listed_edge_logs = client.get(f"/api/v1/routes/{route_id}/edges/{edge_id}/logs")
    assert listed_edge_logs.status_code == 404

    created_edge_log = client.post(
        f"/api/v1/routes/{route_id}/edges/{edge_id}/logs",
        json={"content": "edge-log-created", "actor_type": "human", "actor_id": "tester"},
    )
    assert created_edge_log.status_code == 404

    deleted_node_log = client.delete(f"/api/v1/routes/{route_id}/nodes/{node1_id}/logs/{node_log_id}")
    assert deleted_node_log.status_code == 204

    empty_content = client.post(
        f"/api/v1/routes/{route_id}/edges/{edge_id}/logs",
        json={"content": "   ", "actor_type": "human", "actor_id": "tester"},
    )
    assert empty_content.status_code == 404


def test_route_graph_marks_has_logs_for_node_only():
    client = make_client()
    task_id = create_test_task(client, prefix="graph_has_logs_task")

    route = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('graph_has_logs')}",
            "goal": "graph has_logs markers",
            "status": "candidate",
        },
    )
    assert route.status_code == 201
    route_id = route.json()["id"]

    node1 = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "goal", "title": "N1", "description": ""},
    )
    assert node1.status_code == 201
    node1_id = node1.json()["id"]

    node2 = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "goal", "title": "N2", "description": ""},
    )
    assert node2.status_code == 201
    node2_id = node2.json()["id"]

    edge = client.post(
        f"/api/v1/routes/{route_id}/edges",
        json={"from_node_id": node1_id, "to_node_id": node2_id},
    )
    assert edge.status_code == 201
    edge_id = edge.json()["id"]

    graph_before = client.get(f"/api/v1/routes/{route_id}/graph")
    assert graph_before.status_code == 200
    node_before = next(item for item in graph_before.json()["nodes"] if item["id"] == node1_id)
    edge_before = next(item for item in graph_before.json()["edges"] if item["id"] == edge_id)
    assert node_before["has_logs"] is False
    assert "has_logs" not in edge_before

    node_log = client.post(
        f"/api/v1/routes/{route_id}/nodes/{node1_id}/logs",
        json={"content": "node graph log", "actor_type": "human", "actor_id": "tester"},
    )
    assert node_log.status_code == 201

    graph_after = client.get(f"/api/v1/routes/{route_id}/graph")
    assert graph_after.status_code == 200
    node_after = next(item for item in graph_after.json()["nodes"] if item["id"] == node1_id)
    edge_after = next(item for item in graph_after.json()["edges"] if item["id"] == edge_id)
    assert node_after["has_logs"] is True
    assert "has_logs" not in edge_after


def test_route_edges_are_plain_connectors():
    client = make_client()
    task_id = create_test_task(client, prefix="route_edge_connectors_task")

    route = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('edge_conn')}",
            "goal": "edge connector semantics",
            "status": "candidate",
        },
    )
    assert route.status_code == 201
    route_id = route.json()["id"]

    idea1 = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "idea", "title": "Idea 1", "description": ""},
    )
    assert idea1.status_code == 201
    idea1_id = idea1.json()["id"]

    idea2 = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "idea", "title": "Idea 2", "description": ""},
    )
    assert idea2.status_code == 201
    idea2_id = idea2.json()["id"]

    goal1 = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "goal", "title": "Goal 1", "description": ""},
    )
    assert goal1.status_code == 201
    goal1_id = goal1.json()["id"]

    first_edge = client.post(
        f"/api/v1/routes/{route_id}/edges",
        json={
            "from_node_id": idea1_id,
            "to_node_id": idea2_id,
        },
    )
    assert first_edge.status_code == 201
    assert set(first_edge.json()) >= {"id", "route_id", "from_node_id", "to_node_id", "created_at"}
    assert "relation" not in first_edge.json()
    assert "description" not in first_edge.json()
    assert "has_logs" not in first_edge.json()

    second_edge = client.post(
        f"/api/v1/routes/{route_id}/edges",
        json={
            "from_node_id": idea2_id,
            "to_node_id": goal1_id,
        },
    )
    assert second_edge.status_code == 201

    graph = client.get(f"/api/v1/routes/{route_id}/graph")
    assert graph.status_code == 200
    edges = graph.json()["edges"]
    assert any(edge["from_node_id"] == idea1_id and edge["to_node_id"] == idea2_id for edge in edges)
    assert any(edge["from_node_id"] == idea2_id and edge["to_node_id"] == goal1_id for edge in edges)
    assert all("relation" not in edge for edge in edges)
    assert all("description" not in edge for edge in edges)
    assert all("has_logs" not in edge for edge in edges)

    goal2 = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "goal", "title": "Goal 2", "description": ""},
    )
    assert goal2.status_code == 201
    goal2_id = goal2.json()["id"]

    goal_to_goal = client.post(
        f"/api/v1/routes/{route_id}/edges",
        json={
            "from_node_id": goal1_id,
            "to_node_id": goal2_id,
        },
    )
    assert goal_to_goal.status_code == 201

    mismatch = client.post(
        f"/api/v1/routes/{route_id}/edges",
        json={
            "from_node_id": idea1_id,
            "to_node_id": goal2_id,
        },
    )
    assert mismatch.status_code == 201


def test_route_nodes_edges_and_logs():
    client = make_client()
    task_id = create_test_task(client, prefix="route_graph_task")

    route1 = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('r1')}",
            "goal": "route graph path 1",
            "status": "candidate",
        },
    )
    assert route1.status_code == 201
    route1_id = route1.json()["id"]

    route2 = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('r2')}",
            "goal": "route graph path 2",
            "status": "candidate",
        },
    )
    assert route2.status_code == 201
    route2_id = route2.json()["id"]

    n1 = client.post(
        f"/api/v1/routes/{route1_id}/nodes",
        json={"node_type": "idea", "title": "Choose direction", "description": "compare options"},
    )
    assert n1.status_code == 201
    n1_id = n1.json()["id"]

    n2 = client.post(
        f"/api/v1/routes/{route1_id}/nodes",
        json={"node_type": "goal", "title": "Build MVP", "description": "ship first version"},
    )
    assert n2.status_code == 201
    n2_id = n2.json()["id"]

    edge = client.post(
        f"/api/v1/routes/{route1_id}/edges",
        json={"from_node_id": n1_id, "to_node_id": n2_id},
    )
    assert edge.status_code == 201

    graph = client.get(f"/api/v1/routes/{route1_id}/graph")
    assert graph.status_code == 200
    graph_body = graph.json()
    assert graph_body["route_id"] == route1_id
    assert any(item["id"] == n1_id for item in graph_body["nodes"])
    assert any(item["id"] == n2_id for item in graph_body["nodes"])
    assert any(item["from_node_id"] == n1_id and item["to_node_id"] == n2_id for item in graph_body["edges"])

    other_node = client.post(
        f"/api/v1/routes/{route2_id}/nodes",
        json={"node_type": "goal", "title": "Cross route node", "description": "cross route"},
    )
    assert other_node.status_code == 201
    other_node_id = other_node.json()["id"]

    cross = client.post(
        f"/api/v1/routes/{route1_id}/edges",
        json={"from_node_id": n1_id, "to_node_id": other_node_id},
    )
    assert cross.status_code == 422
    assert cross.json()["error"]["code"] == "ROUTE_EDGE_CROSS_ROUTE"

    log_append = client.post(
        f"/api/v1/routes/{route1_id}/nodes/{n1_id}/logs",
        json={"content": f"log_test_{uniq('log')}", "actor_type": "human", "actor_id": "tester"},
    )
    assert log_append.status_code == 201

    logs = client.get(f"/api/v1/routes/{route1_id}/nodes/{n1_id}/logs")
    assert logs.status_code == 200
    assert logs.json()["items"]

    rename = client.patch(
        f"/api/v1/routes/{route1_id}/nodes/{n2_id}",
        json={"title": "Build MVP v2"},
    )
    assert rename.status_code == 200
    assert rename.json()["title"] == "Build MVP v2"

    delete_non_leaf = client.delete(f"/api/v1/routes/{route1_id}/nodes/{n1_id}")
    assert delete_non_leaf.status_code == 409
    assert delete_non_leaf.json()["error"]["code"] == "ROUTE_NODE_HAS_SUCCESSORS"

    delete_leaf = client.delete(f"/api/v1/routes/{route1_id}/nodes/{n2_id}")
    assert delete_leaf.status_code == 204

    delete_node = client.delete(f"/api/v1/routes/{route1_id}/nodes/{n1_id}")
    assert delete_node.status_code == 204

    graph_after_delete = client.get(f"/api/v1/routes/{route1_id}/graph")
    assert graph_after_delete.status_code == 200
    body = graph_after_delete.json()
    assert all(item["id"] != n1_id for item in body["nodes"])
    assert all(item["id"] != n2_id for item in body["nodes"])
    assert all(
        item["from_node_id"] not in {n1_id, n2_id} and item["to_node_id"] not in {n1_id, n2_id}
        for item in body["edges"]
    )

    logs_after_delete = client.get(f"/api/v1/routes/{route1_id}/nodes/{n1_id}/logs")
    assert logs_after_delete.status_code == 404
    assert logs_after_delete.json()["error"]["code"] == "ROUTE_NODE_NOT_FOUND"

    delete_again = client.delete(f"/api/v1/routes/{route1_id}/nodes/{n1_id}")
    assert delete_again.status_code == 404
    assert delete_again.json()["error"]["code"] == "ROUTE_NODE_NOT_FOUND"


def test_route_edges_do_not_support_patch_or_logs():
    client = make_client()
    task_id = create_test_task(client, prefix="route_edge_contract_task")

    route = client.post(
        "/api/v1/routes",
        json={
            "task_id": task_id,
            "name": f"route_test_{uniq('edge_contract')}",
            "goal": "edge contract updates",
            "status": "candidate",
        },
    )
    assert route.status_code == 201
    route_id = route.json()["id"]

    idea = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "idea", "title": "Idea", "description": ""},
    )
    assert idea.status_code == 201
    idea_id = idea.json()["id"]

    goal = client.post(
        f"/api/v1/routes/{route_id}/nodes",
        json={"node_type": "goal", "title": "Goal", "description": ""},
    )
    assert goal.status_code == 201
    goal_id = goal.json()["id"]

    edge = client.post(
        f"/api/v1/routes/{route_id}/edges",
        json={"from_node_id": idea_id, "to_node_id": goal_id},
    )
    assert edge.status_code == 201
    edge_id = edge.json()["id"]

    patched = client.patch(
        f"/api/v1/routes/{route_id}/edges/{edge_id}",
        json={"from_node_id": goal_id},
    )
    assert patched.status_code == 405

    create_log = client.post(
        f"/api/v1/routes/{route_id}/edges/{edge_id}/logs",
        json={"content": "obsolete edge log", "actor_type": "human", "actor_id": "tester"},
    )
    assert create_log.status_code == 404

    list_logs = client.get(f"/api/v1/routes/{route_id}/edges/{edge_id}/logs")
    assert list_logs.status_code == 404
