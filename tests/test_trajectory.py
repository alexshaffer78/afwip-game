"""
Trajectory data-generation tests: recorder wiring, replay determinism, per-side
materialization + rewards, schema round-trip, fog-safety of the copy-state, the
context-pack staging script, and the record/export API endpoints.
"""

import json
import random
from dataclasses import replace

import numpy as np
import pytest
from fastapi.testclient import TestClient

from afwip.env import AFWIPEnv
from afwip.web.app import create_app
from afwip.web.session import GameSession, GameMode
from afwip.rl.trajectory import (
    Trajectory, TapeStep, Outcome, TrajectoryRecorder,
    write_trajectory, read_trajectories, materialize, materialize_both,
)


# ---------------------------------------------------------------------------
# Helpers — drive a full hotseat game deterministically through the session
# ---------------------------------------------------------------------------

def _play_hotseat(seed, choice_seed, tmp_path, campaign=2, **kwargs):
    s = GameSession("g", campaign=campaign, mode=GameMode.HOTSEAT, seed=seed,
                    trajectory_dir=tmp_path, **kwargs)
    rng = random.Random(choice_seed)
    guard = 0
    while not s.terminal and guard < 20000:
        if s.handoff_required:
            s.handoff()
        node = s._node
        s.apply_human(rng.randrange(len(node.choices)))
        guard += 1
    assert s.terminal, "hotseat game did not finish"
    return s


# ---------------------------------------------------------------------------
# Recording + auto-save
# ---------------------------------------------------------------------------

def test_hotseat_records_but_saves_only_on_demand(tmp_path):
    s = _play_hotseat(123, 0, tmp_path)
    path = tmp_path / "g.jsonl"
    # Recording is automatic, but NOTHING is written until the user chooses.
    assert s.recording and s.trajectory_saved_path is None
    assert not path.exists()

    saved = s.save_trajectory()
    assert saved == path and path.exists() and s.trajectory_saved_path == path
    traj = read_trajectories(path)[0]
    assert traj.campaign == 2 and traj.seed == 123 and traj.max_turns == 150
    assert len(traj.tape) == s.decision_no
    # Outcome mirrors the engine at game end.
    gs = s.env.engine.state
    assert traj.outcome.winner == (gs.winner.value if gs.winner else None)
    assert traj.outcome.total_turns == gs.total_turns


def test_mid_game_save_and_resave(tmp_path):
    # Save is allowed any time, and re-saving overwrites the same file.
    s = GameSession("m", campaign=2, mode=GameMode.HOTSEAT, seed=7,
                    trajectory_dir=tmp_path)

    def play_one():
        if s.handoff_required:
            s.handoff()
        s.apply_human(0)

    for _ in range(6):
        play_one()
    p1 = s.save_trajectory()
    assert p1.exists() and len(read_trajectories(p1)[0].tape) == 6
    play_one()
    p2 = s.save_trajectory()
    assert p2 == p1 and len(read_trajectories(p2)[0].tape) == 7   # overwritten


def test_recording_gating():
    # Hotseat records by default; human_v_agent does not; flags override.
    assert GameSession("a", mode=GameMode.HOTSEAT, seed=1).trajectory is not None
    assert GameSession("b", mode=GameMode.HUMAN_V_AGENT, seed=1).trajectory is None
    assert GameSession("c", mode=GameMode.HOTSEAT, seed=1,
                       record=False).trajectory is None
    assert GameSession("d", mode=GameMode.HUMAN_V_AGENT, seed=1,
                       record=True).trajectory is not None


def test_justification_is_captured(tmp_path):
    s = GameSession("j", campaign=2, mode=GameMode.HOTSEAT, seed=5,
                    trajectory_dir=tmp_path)
    if s.handoff_required:
        s.handoff()
    s.apply_human(0, justification="doctrine: seek control of the air")
    assert s.trajectory.tape[0].justification == "doctrine: seek control of the air"
    assert s.trajectory.tape[0].index == 0


# ---------------------------------------------------------------------------
# Replay determinism + materialization
# ---------------------------------------------------------------------------

def test_replay_is_deterministic(tmp_path):
    a = _play_hotseat(77, 3, tmp_path)
    b = _play_hotseat(77, 3, tmp_path)
    ta = [(t.side, t.index) for t in a.trajectory.tape]
    tb = [(t.side, t.index) for t in b.trajectory.tape]
    assert ta == tb
    assert a.build_trajectory().outcome == b.build_trajectory().outcome


def test_materialize_shapes_and_split(tmp_path):
    traj = _play_hotseat(202, 1, tmp_path).build_trajectory()
    ref = AFWIPEnv(campaign=2)          # shapes to validate against
    for side in ("US", "PRC"):
        samples = materialize(traj, side, reward="sparse")
        # Per-side split matches the tape.
        assert len(samples) == len(traj.side_steps(side))
        space = ref.observation_space(side)["observation"]
        for smp in samples:
            for key, box in space.spaces.items():
                assert smp.observation[key].shape == box.shape
            # The taken action is legal under the regenerated mask.
            assert smp.action_mask[smp.action_index] == 1
            assert smp.outcome_label in ("win", "loss", "draw")


def test_sparse_reward_is_terminal_and_zero_sum(tmp_path):
    traj = _play_hotseat(202, 1, tmp_path).build_trajectory()
    us = materialize(traj, "US", reward="sparse")
    prc = materialize(traj, "PRC", reward="sparse")
    for samples in (us, prc):
        assert all(s.reward == 0.0 for s in samples[:-1])   # 0 until terminal
        assert samples[-1].done and not any(s.done for s in samples[:-1])
        assert abs(samples[-1].reward) in (0.0, 1.0)
    assert us[-1].reward + prc[-1].reward == pytest.approx(0.0)


def test_vp_recorded_at_each_step_for_reward_rederivation(tmp_path):
    # VP is captured at every decision so rewards + action sequences are fully
    # re-derivable from the tape alone (no replay, robust to scoring changes).
    traj = _play_hotseat(202, 1, tmp_path).build_trajectory()
    assert traj.tape and all(t.us_vp is not None and t.prc_vp is not None
                             for t in traj.tape)
    assert traj.outcome.us_vp is not None and traj.outcome.prc_vp is not None


def test_attrition_reward_telescopes_to_vp_margin(tmp_path):
    traj = _play_hotseat(202, 1, tmp_path).build_trajectory()
    for side, margin in (("US", traj.outcome.us_vp - traj.outcome.prc_vp),
                         ("PRC", traj.outcome.prc_vp - traj.outcome.us_vp)):
        samples = materialize(traj, side, reward="attrition_vp")
        assert sum(s.reward for s in samples) == pytest.approx(float(margin))


def test_materialize_detects_choice_ordering_drift(tmp_path):
    """The stored index is a position into a regenerated choice list, so replay
    must hard-fail if the recorded label/node_type no longer matches (engine
    choice ordering drifted) — never silently mislabel the action."""
    traj = _play_hotseat(31, 4, tmp_path).build_trajectory()
    materialize(traj, "US")                      # clean record replays fine

    bad_label = replace(traj, tape=[replace(t, label="TAMPERED") if i == 5 else t
                                    for i, t in enumerate(traj.tape)])
    with pytest.raises(AssertionError, match="replay drift"):
        materialize(bad_label, bad_label.tape[5].side)

    bad_node = replace(traj, tape=[replace(t, node_type="SPAWN_BAND") if i == 5 else t
                                   for i, t in enumerate(traj.tape)])
    with pytest.raises(AssertionError, match="replay drift"):
        materialize(bad_node, bad_node.tape[5].side)


def test_materialize_both_covers_both_seats(tmp_path):
    traj = _play_hotseat(9, 9, tmp_path).build_trajectory()
    both = materialize_both(traj)
    assert set(both) == {"US", "PRC"}
    assert len(both["US"]) + len(both["PRC"]) == len(traj.tape)


# ---------------------------------------------------------------------------
# Schema round-trip
# ---------------------------------------------------------------------------

def test_schema_round_trip(tmp_path):
    traj = Trajectory(
        campaign=2, seed=42, max_turns=150,
        outcome=Outcome(winner="US", us_vp=7, prc_vp=3, total_turns=88, capped=False),
        tape=[TapeStep(0, "US", "MISSION_PICK", 1, 0, "Attrition", None),
              TapeStep(1, "PRC", "TURN_ACTION", 4, 2, "move", "flank")],
        env_git_commit="deadbee", created_at="2026-08-10T00:00:00+00:00",
        source="human")
    assert Trajectory.from_dict(traj.to_dict()) == traj
    path = write_trajectory(traj, tmp_path / "rt.jsonl")
    assert read_trajectories(path)[0] == traj


# ---------------------------------------------------------------------------
# Fog-safety of the copy-state a human pastes into the project chat
# ---------------------------------------------------------------------------

def test_copy_state_is_fog_safe(tmp_path):
    """The llm_export block (the 'Copy state for AI' payload) never reveals an
    unacquired enemy token's type — same guarantee as the browser."""
    s = GameSession("f", campaign=3, mode=GameMode.HOTSEAT, seed=4,
                    trajectory_dir=tmp_path)
    rng = random.Random(4)
    saw_fogged = False
    for _ in range(400):
        if s.terminal:
            break
        if s.handoff_required:
            s.handoff()
        export = s.state().llm_export or ""
        for line in export.splitlines():
            if line.startswith("TOKEN:") and "acquired=0" in line:
                # An unacquired token is fogged only when it is the OPPONENT's.
                if f'owner={s.authorized_viewer.value}' not in line:
                    saw_fogged = True
                    assert 'type="?"' in line, f"fog leak: {line}"
        node = s._node
        s.apply_human(rng.randrange(len(node.choices)))
    assert saw_fogged, "test never observed a fogged enemy token"


# ---------------------------------------------------------------------------
# API: record flag + trajectory export endpoint
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    return TestClient(create_app())


def test_trajectory_endpoint(client):
    # Hotseat game records; the endpoint returns the (snapshot) trajectory.
    r = client.post("/api/games", json={"campaign": 2, "mode": "hotseat", "seed": 1})
    gid = r.json()["game_id"]
    traj = client.get(f"/api/games/{gid}/trajectory")
    assert traj.status_code == 200
    body = traj.json()
    assert body["campaign"] == 2 and body["seed"] == 1 and "tape" in body

    # human_v_agent is not recorded -> 404.
    r2 = client.post("/api/games", json={"campaign": 2, "mode": "human_v_agent",
                                         "human_side": "US", "seed": 1,
                                         "record": False})
    gid2 = r2.json()["game_id"]
    assert client.get(f"/api/games/{gid2}/trajectory").status_code == 404


def test_save_endpoint_writes_on_demand(client, tmp_path, monkeypatch):
    # Redirect the default save dir so the test never writes into the repo.
    monkeypatch.setattr("afwip.web.session.DEFAULT_TRAJECTORY_DIR", tmp_path)
    r = client.post("/api/games", json={"campaign": 2, "mode": "hotseat", "seed": 3})
    view = r.json()
    gid = view["game_id"]
    assert view["recording"] is True and view["trajectory_saved"] is False
    # Explicit save writes the file and flips trajectory_saved.
    saved = client.post(f"/api/games/{gid}/trajectory/save")
    assert saved.status_code == 200 and saved.json()["saved"].endswith(f"{gid}.jsonl")
    assert client.get(f"/api/games/{gid}").json()["trajectory_saved"] is True

    # A non-recording game has no save.
    r2 = client.post("/api/games", json={"campaign": 2, "mode": "human_v_agent",
                                         "human_side": "US", "seed": 1,
                                         "record": False})
    gid2 = r2.json()["game_id"]
    assert client.post(f"/api/games/{gid2}/trajectory/save").status_code == 404


def test_choice_endpoint_accepts_justification(client):
    r = client.post("/api/games", json={"campaign": 2, "mode": "hotseat", "seed": 2})
    view = r.json()
    gid = view["game_id"]
    resp = client.post(f"/api/games/{gid}/choices",
                       json={"index": 0, "revision": view["revision"],
                             "node_id": view["node_id"],
                             "justification": "control of the air"})
    assert resp.status_code == 200, resp.text
    body = client.get(f"/api/games/{gid}/trajectory").json()
    assert body["tape"][0]["justification"] == "control of the air"
