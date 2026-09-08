"""GameSession tests: full games in every mode, determinism, revision/staleness
guards, and hotseat handoff privacy — all without HTTP."""

import pytest

from afwip.core.constants import Side
from afwip.web.session import (
    GameMode, GameSession, SessionError, StaleStateError, MAX_AUTO_STEPS,
)

# Session-level guard for scripted human loops in tests.
GUARD = MAX_AUTO_STEPS


def _drive_to_terminal_agent_v_agent(campaign: int, seed: int) -> GameSession:
    s = GameSession("g", campaign=campaign, mode=GameMode.AGENT_V_AGENT, seed=seed)
    for _ in range(GUARD):
        if s.terminal:
            return s
        s.step_once()
    raise AssertionError("game did not terminate")


# -- agent vs agent ------------------------------------------------------------

@pytest.mark.parametrize("campaign,seed", [(1, 0), (2, 7), (3, 3)])
def test_agent_v_agent_full_game(campaign, seed):
    s = _drive_to_terminal_agent_v_agent(campaign, seed)
    assert s.terminal
    view = s.state()
    assert view.terminal and view.decision is None
    assert view.winner in ("US", "PRC", None)
    assert view.revision == s.decision_no > 10
    assert view.score_report is not None            # end of game closes an ATO
    assert any(e.type == "decision" for e in view.event_log)


def test_agent_v_agent_is_deterministic():
    a = _drive_to_terminal_agent_v_agent(2, 22)
    b = _drive_to_terminal_agent_v_agent(2, 22)
    assert a.decision_no == b.decision_no
    assert a.state().status.vp == b.state().status.vp
    assert [e.message for e in a.recorder.events] \
        == [e.message for e in b.recorder.events]


def test_spectator_sees_every_decision():
    s = GameSession("g", campaign=2, mode=GameMode.AGENT_V_AGENT, seed=1)
    seen_sides = set()
    for _ in range(60):
        if s.terminal:
            break
        view = s.state()
        assert view.decision is not None            # omniscient spectator
        seen_sides.add(view.decision.side)
        s.step_once()
    assert seen_sides == {"US", "PRC"}


# -- human vs agent -------------------------------------------------------------

def test_human_v_agent_full_game_scripted():
    """Human (US) always picks choice 0 vs the random agent — must finish
    (mirrors tests/test_tui.py::test_play_scripted_game_completes)."""
    s = GameSession("g", campaign=1, mode=GameMode.HUMAN_V_AGENT,
                    human_side=Side.US, seed=0)
    for _ in range(GUARD):
        if s.terminal:
            break
        view = s.state()
        assert view.decision is not None and view.decision.side == "US"
        assert view.viewer == "US"
        s.apply_human(0, revision=view.revision, node_id=view.node_id)
    assert s.terminal


def test_human_v_agent_fog_applied():
    s = GameSession("g", campaign=2, mode=GameMode.HUMAN_V_AGENT,
                    human_side=Side.US, seed=3)
    # Play a while, then check every enemy-token row is properly masked.
    for _ in range(40):
        if s.terminal:
            break
        s.apply_human(0)
    view = s.state()
    for band in view.board.bands:
        for t in band.tokens:
            if t.side == "PRC" and not t.acquired:
                assert t.fogged and t.type is None
    prc_hand = next(h for h in view.hands if h.side == "PRC")
    assert all(c.revealed for c in prc_hand.cards)   # only Intel-revealed shown


def test_stale_revision_and_node_rejected():
    s = GameSession("g", campaign=1, mode=GameMode.HUMAN_V_AGENT,
                    human_side=Side.US, seed=0)
    view = s.state()
    with pytest.raises(StaleStateError):
        s.apply_human(0, revision=view.revision + 1)
    with pytest.raises(StaleStateError):
        s.apply_human(0, node_id="g:99999")
    s.apply_human(0, revision=view.revision, node_id=view.node_id)   # fresh: fine
    with pytest.raises(StaleStateError):                             # replay: stale
        s.apply_human(0, revision=view.revision, node_id=view.node_id)


def test_bad_index_and_agent_side_rejected():
    s = GameSession("g", campaign=1, mode=GameMode.HUMAN_V_AGENT,
                    human_side=Side.US, seed=0)
    with pytest.raises(SessionError):
        s.apply_human(9999)
    with pytest.raises(SessionError):
        s.step_once()          # current node is the human's, not an agent's


# -- hotseat ---------------------------------------------------------------------

def test_hotseat_handoff_gates_private_state():
    s = GameSession("g", campaign=2, mode=GameMode.HOTSEAT, seed=5)
    assert s.authorized_viewer == Side.US            # US decides first
    # Play US decisions until the node passes to PRC.
    for _ in range(GUARD):
        if s.terminal or s.handoff_required:
            break
        view = s.state()
        assert view.decision is not None
        s.apply_human(0)
    assert s.handoff_required
    # Handoff screen: public view only — no decision, no side's hidden info.
    view = s.state()
    assert view.handoff_required and view.decision is None
    assert view.viewer is None
    for band in view.board.bands:
        for t in band.tokens:
            assert t.fogged or t.acquired            # both sides masked
    for hand in view.hands:
        assert not any(not c.revealed for c in hand.cards)
    # Acting before handoff is rejected; after handoff PRC plays.
    with pytest.raises(SessionError):
        s.apply_human(0)
    s.handoff()
    view = s.state()
    assert not view.handoff_required
    assert view.viewer == "PRC" and view.decision.side == "PRC"
    s.apply_human(0)


def test_hotseat_full_game_with_handoffs():
    s = GameSession("g", campaign=1, mode=GameMode.HOTSEAT, seed=2)
    for _ in range(GUARD):
        if s.terminal:
            break
        if s.handoff_required:
            s.handoff()
        s.apply_human(0)
    assert s.terminal


# -- event fog ----------------------------------------------------------------------

def test_event_log_redacts_enemy_hidden_decisions():
    s = GameSession("g", campaign=2, mode=GameMode.HUMAN_V_AGENT,
                    human_side=Side.US, seed=9)
    for _ in range(30):
        if s.terminal:
            break
        s.apply_human(0)
    view = s.state()
    hidden = [e for e in view.event_log
              if e.side == "PRC" and e.type == "decision" and not e.public]
    assert hidden, "expected redacted PRC decisions in the log"
    assert all(e.message.endswith("(hidden)") for e in hidden)
    # The omniscient recorder still holds the full detail.
    full = [e for e in s.recorder.events
            if e.side == "PRC" and e.type == "decision" and not e.public]
    assert any(not e.message.endswith("(hidden)") for e in full)
