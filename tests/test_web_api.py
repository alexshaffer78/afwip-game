"""FastAPI endpoint tests: lifecycle, staleness 409s, invalid requests, and
the hotseat handoff flow — via the in-process TestClient."""

import pytest
from fastapi.testclient import TestClient

from afwip.web.app import create_app


@pytest.fixture()
def client():
    return TestClient(create_app())


def _create(client, **overrides):
    body = {"campaign": 1, "mode": "human_v_agent", "human_side": "US", "seed": 0}
    body.update(overrides)
    r = client.post("/api/games", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def test_human_v_human_two_device(client):
    """Two devices join one game: per-side fog, per-client viewer, and a device
    can only act for its own side."""
    g = _create(client, mode="human_v_human", campaign=1, seed=0)
    gid = g["game_id"]
    # each device fetches its own fogged view
    us = client.get(f"/api/games/{gid}?viewer=US").json()
    prc = client.get(f"/api/games/{gid}?viewer=PRC").json()
    assert us["viewer"] == "US" and prc["viewer"] == "PRC"
    # the acting side is US first; PRC acting on a US node is rejected
    assert us["decision"] is not None and prc["decision"] is None
    bad = client.post(f"/api/games/{gid}/choices",
                      json={"index": 0, "revision": us["revision"],
                            "node_id": us["node_id"], "viewer": "PRC"})
    assert bad.status_code == 400
    # US acts for US -> ok, revision advances (the other device polls to catch it)
    ok = client.post(f"/api/games/{gid}/choices",
                     json={"index": 0, "revision": us["revision"],
                           "node_id": us["node_id"], "viewer": "US"})
    assert ok.status_code == 200, ok.text
    assert ok.json()["revision"] == us["revision"] + 1


def test_config(client):
    cfg = client.get("/api/config").json()
    assert cfg["campaigns"] == [1, 2, 3, 4, 5]
    assert set(cfg["modes"]) == {"agent_v_agent", "human_v_agent", "hotseat",
                                 "human_v_human"}
    assert "random" in cfg["agents"]


def test_create_get_delete(client):
    view = _create(client)
    gid = view["game_id"]
    assert view["decision"]["side"] == "US" and view["viewer"] == "US"
    assert client.get(f"/api/games/{gid}").json()["revision"] == view["revision"]
    assert client.delete(f"/api/games/{gid}").json() == {"deleted": gid}
    assert client.get(f"/api/games/{gid}").status_code == 404
    assert client.delete(f"/api/games/{gid}").status_code == 404


def test_choice_flow_and_staleness(client):
    view = _create(client)
    gid = view["game_id"]
    ok = client.post(f"/api/games/{gid}/choices",
                     json={"index": 0, "revision": view["revision"],
                           "node_id": view["node_id"]})
    assert ok.status_code == 200
    assert ok.json()["revision"] > view["revision"]
    # Replaying the same submission is stale -> 409.
    dup = client.post(f"/api/games/{gid}/choices",
                      json={"index": 0, "revision": view["revision"],
                            "node_id": view["node_id"]})
    assert dup.status_code == 409
    # Out-of-range index -> 400.
    bad = client.post(f"/api/games/{gid}/choices", json={"index": 9999})
    assert bad.status_code == 400


def test_agent_v_agent_step_to_completion(client):
    view = _create(client, mode="agent_v_agent", seed=4)
    gid = view["game_id"]
    for _ in range(30000):
        if view["terminal"]:
            break
        view = client.post(f"/api/games/{gid}/step").json()
    assert view["terminal"]
    assert view["winner"] in ("US", "PRC", None)
    # Stepping a finished game -> 400; posting a choice in spectator mode -> 400.
    assert client.post(f"/api/games/{gid}/step").status_code == 400


def test_spectator_cannot_post_choices(client):
    view = _create(client, mode="agent_v_agent", seed=4)
    r = client.post(f"/api/games/{view['game_id']}/choices", json={"index": 0})
    assert r.status_code == 400


def test_hotseat_handoff_flow(client):
    view = _create(client, mode="hotseat", campaign=1, seed=2)
    gid = view["game_id"]
    for _ in range(30000):
        if view["terminal"]:
            break
        if view["handoff_required"]:
            assert view["decision"] is None          # private state withheld
            view = client.post(f"/api/games/{gid}/handoff").json()
            assert not view["handoff_required"]
            continue
        view = client.post(f"/api/games/{gid}/choices", json={"index": 0}).json()
    assert view["terminal"]


def test_handoff_only_for_hotseat(client):
    view = _create(client)
    r = client.post(f"/api/games/{view['game_id']}/handoff")
    assert r.status_code == 400


def test_validation_errors(client):
    assert client.post("/api/games", json={"campaign": 9}).status_code == 422
    assert client.post("/api/games", json={"mode": "nope"}).status_code == 422
    assert client.post("/api/games",
                       json={"human_side": "FR"}).status_code == 422
    assert client.post("/api/games", json={"agent": "skynet"}).status_code == 422
