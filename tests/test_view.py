"""View-layer tests: fog fidelity (locked to the TUI's rendering), JSON
contract safety, choice render-metadata coverage, and structured scoring."""

import math
import random

import pytest

from afwip import tui
from afwip.core.rules import RulesEngine
from afwip.core.state import (
    CardZone, EnablerCardState, GameState, SquadronState,
)
from afwip.core.constants import Side, BandID, Phase, TokenType, TokenOrigin
from afwip.script import GameScript, NodeType
from afwip.view import serializer
from afwip.view.events import EventRecorder, score_report
from afwip.view.layout import BOARD_BANDS


# -- fixtures -----------------------------------------------------------------

def _fog_state():
    """One unacquired PRC J-20B on the board (mirrors tests/test_tui.py)."""
    gs = GameState.new_game(campaign=3)
    gs.phase = Phase.PLAYER_TURN
    gs.active_side = Side.US
    gs.us.posture_card_id, gs.prc.posture_card_id = 49, 103
    eng = RulesEngine(gs, rng=random.Random(0))
    gs.prc.squadrons[62] = SquadronState(62, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE,
                                         zone=CardZone.ACTIVE, ever_activated=True)
    tok = gs.spawn_token(Side.PRC, TokenType.J_20B, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=62)
    return eng, tok


def _walk_json(value, path="$"):
    """Assert a decoded structure is strictly JSON-safe."""
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        assert math.isfinite(value), f"non-finite float at {path}"
        return
    if isinstance(value, list):
        for i, v in enumerate(value):
            _walk_json(v, f"{path}[{i}]")
        return
    if isinstance(value, dict):
        for k, v in value.items():
            assert isinstance(k, str), f"non-string key {k!r} at {path}"
            _walk_json(v, f"{path}.{k}")
        return
    raise AssertionError(f"non-JSON type {type(value).__name__} at {path}")


# -- fog ------------------------------------------------------------------------

def test_layout_matches_tui_board_columns():
    assert BOARD_BANDS == tui.BOARD_COLUMNS


def test_fogged_enemy_token_masks_identity():
    eng, tok = _fog_state()
    tv = serializer.token_view(tok, viewer=Side.US, reveal=False)
    assert tv.fogged and tv.type is None and tv.winchester is None
    assert tv.label == f"?#{tok.uid}(av{tok.profile.acquisition_value})"
    assert tv.av == tok.profile.acquisition_value       # av stays public
    # Own view / omniscient / acquisition all lift the fog.
    assert not serializer.token_view(tok, Side.PRC, False).fogged
    assert serializer.token_view(tok, Side.US, True).type == "J-20B"
    tok.acquired = True
    tv = serializer.token_view(tok, Side.US, False)
    assert not tv.fogged and tv.label == f"J-20B#{tok.uid}*"


def test_public_view_masks_both_sides():
    eng, tok = _fog_state()
    us_tok = eng.state.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_B,
                                   TokenOrigin.SQUADRON_CARD)
    assert serializer.token_view(tok, None, False).fogged
    assert serializer.token_view(us_tok, None, False).fogged


def test_fog_lockstep_with_tui_over_full_game():
    """At every decision of a seeded game, the view's fog verdict for every
    token must match the TUI board string (the pinned fidelity oracle)."""
    eng = RulesEngine(GameState.new_game(campaign=2), rng=random.Random(7))
    agent = random.Random(8)
    gen = GameScript(eng).run()
    node = next(gen)
    checked = 0
    while node is not None:
        board_str = tui.render_board(eng, viewer=Side.US, reveal=False)
        bv = serializer.board_view(eng, Side.US, reveal=False)
        for band in bv.bands:
            for t in band.tokens:
                if t.fogged:
                    assert f"?#{t.uid}(av" in board_str
                else:
                    assert t.label in board_str
                checked += 1
        try:
            node = gen.send(agent.choice(node.choices))
        except StopIteration:
            node = None
    assert checked > 100


def test_enemy_hand_fog():
    eng, _ = _fog_state()
    p = eng.state.prc
    p.enablers[65] = EnablerCardState(65, Side.PRC, zone=CardZone.SELECTED)
    p.enablers[66] = EnablerCardState(66, Side.PRC, zone=CardZone.SELECTED,
                                      revealed_to_opponent=True)
    hv = serializer.hand_view(eng, Side.PRC, viewer=Side.US, reveal=False)
    assert hv.hidden_count == 1
    assert [c.card_id for c in hv.cards] == [66]        # only the revealed card
    own = serializer.hand_view(eng, Side.PRC, viewer=Side.PRC, reveal=False)
    assert own.hidden_count == 0 and len(own.cards) == 2


def test_enemy_facedown_squadron_hidden_until_ever_activated():
    eng, _ = _fog_state()
    p = eng.state.prc
    p.squadrons[60] = SquadronState(60, Side.PRC, zone=CardZone.SELECTED,
                                    location=BandID.PRC_AIRBASE)
    panel = serializer.squadron_panel(eng, Side.PRC, viewer=Side.US, reveal=False)
    assert panel.face_down == 1
    assert 60 not in [s.card_id for s in panel.squadrons]
    assert 62 in [s.card_id for s in panel.squadrons]   # ever_activated: public
    p.squadrons[60].ever_activated = True
    panel = serializer.squadron_panel(eng, Side.PRC, viewer=Side.US, reveal=False)
    assert panel.face_down == 0
    assert 60 in [s.card_id for s in panel.squadrons]


# -- JSON contract ---------------------------------------------------------------

def test_views_are_json_safe_through_a_game():
    from afwip.web.session import GameMode, GameSession
    s = GameSession("t1", campaign=2, mode=GameMode.AGENT_V_AGENT, seed=11)
    steps = 0
    while not s.terminal:
        if steps % 25 == 0:
            _walk_json(s.state().model_dump(mode="json"))
        s.step_once()
        steps += 1
    _walk_json(s.state().model_dump(mode="json"))
    assert s.terminal and steps > 50


# -- choice render metadata --------------------------------------------------------

@pytest.mark.parametrize("campaign,seed", [(2, 0), (2, 5), (3, 3)])
def test_choice_metadata_coverage(campaign, seed):
    """Every choice kind carries the metadata the frontend highlights need."""
    eng = RulesEngine(GameState.new_game(campaign=campaign),
                      rng=random.Random(seed))
    agent = random.Random(seed + 1)
    gen = GameScript(eng).run()
    node = next(gen)
    seen = set()
    while node is not None:
        for c in node.choices:
            seen.add(c.kind)
            if c.kind == "move":
                assert c.actor_uid is not None and c.band is not None
            elif c.kind in ("acquire", "shoot_air"):
                # A target is always named — the UI highlights it. An ACTOR is
                # only present for token-vs-token actions: enabler target
                # pickers (Space Recon, Offensive Cyber, Joint Offensive
                # Cyber...) reuse these kinds, and there the CARD acts, so
                # there is no acting token.
                assert c.target_uid is not None
            elif c.kind == "shoot_surface":     # ship strike XOR base strike
                assert c.actor_uid is not None
                assert (c.target_uid is not None) ^ (c.band is not None)
            elif c.kind == "activate":
                assert c.card_id is not None
            elif c.kind == "play_enabler":
                assert c.card_id is not None
        try:
            node = gen.send(agent.choice(node.choices))
        except StopIteration:
            node = None
    assert {"pass", "move", "activate"} <= seen


# -- events & scoring ----------------------------------------------------------------

def test_strike_dice_are_labeled_hit_and_damage():
    # A base strike rolls a hit die then (for an exploding-die token) a damage
    # die; the event carries a per-die `role` so the UI can label them rather
    # than showing an ambiguous bare "3 2" (2026-07-31).
    gs = GameState.new_game(campaign=2)
    gs.phase = Phase.PLAYER_TURN
    gs.active_side = Side.US
    eng = RulesEngine(gs, rng=random.Random(1))
    rec = EventRecorder(eng)
    gs.us.squadrons[7] = SquadronState(7, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.squadrons[55] = SquadronState(55, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    b52 = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_STANDOFF,
                         TokenOrigin.SQUADRON_CARD, source_card_id=7)
    eng.shoot_surface(Side.US, b52.uid, target_band=BandID.PRC_AIRBASE, target_vp_boxes=True)
    rec.flush_dice(0)
    ev = next(e for e in reversed(rec.events) if e.type == "dice")
    assert [r.get("role") for r in ev.data["rolls"]] == ["hit", "damage"]


def test_flush_setup_labels_setup_dice_and_suppresses_the_raw_blob():
    gs = GameState.new_game(campaign=2)
    eng = RulesEngine(gs, rng=random.Random(0))
    rec = EventRecorder(eng)
    eng.setup_roll_log = [
        {"kind": "initiative", "winner": "US", "auto": False,
         "us": {"natural": 3, "bonus": 0, "value": 3, "mode": "NORMAL", "dice": [3]},
         "prc": {"natural": 2, "bonus": 0, "value": 2, "mode": "NORMAL", "dice": [2]}},
        {"kind": "cyber_raise", "side": "US", "natural": 3, "needed": 2,
         "success": True, "from": 1, "to": 2},
        {"kind": "play_intel",
         "us": {"roll": {"natural": 4, "value": 4, "bonus": 0, "mode": "ADVANTAGE",
                         "dice": [4, 1]}, "sees": 3},
         "prc": {"roll": {"natural": 2, "value": 2, "bonus": 0, "mode": "NORMAL",
                          "dice": [2]}, "sees": 1}},
    ]
    rec._dice = [("d4", 3), ("d4", 2), ("d4", 3)]   # the tap also captured them

    rec.flush_setup(0)
    labels = [e.data["label"] for e in rec.events if e.data.get("label")]
    assert any("Initiative bid" in l and "US wins" in l for l in labels)
    assert any("cyber raise" in l and "1→2" in l for l in labels)
    assert any("Play Intel" in l and "sees 3" in l for l in labels)
    # Each carries die-face payloads and is public (both players see the table).
    dice_evs = [e for e in rec.events if e.type == "dice"]
    assert all(e.public and e.data.get("rolls") for e in dice_evs)
    # The raw dice were consumed, so flush_dice adds NO unlabeled blob.
    assert rec._dice == []
    n = len(rec.events)
    rec.flush_dice(0)
    assert len(rec.events) == n


def test_recorder_distinguishes_recycled_from_destroyed():
    """Structured mirror of the TUI's kill-vs-recycle event distinction."""
    gs = GameState.new_game(campaign=3)
    gs.phase = Phase.PLAYER_TURN
    gs.active_side = Side.US
    eng = RulesEngine(gs, rng=random.Random(0))
    rec = EventRecorder(eng)
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True,
                                        location=BandID.US_AIRBASE,
                                        zone=CardZone.ACTIVE)
    survivor = gs.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_B,
                              TokenOrigin.SQUADRON_CARD, source_card_id=10)
    victim = gs.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_B,
                            TokenOrigin.SQUADRON_CARD, source_card_id=10)
    ship = gs.spawn_token(Side.US, TokenType.DDG_81, BandID.BAND_C,
                          TokenOrigin.ENABLER_CARD)
    ship.air_salvos_remaining = ship.surf_salvos_remaining = 0

    before = rec.snapshot()
    gs.destroy_token(victim.uid, destroyed_by=Side.PRC)
    eng._start_turn(Side.US)
    eng.end_ato_cycle()
    rec.emit_diff(0, before)

    by_type = {}
    for ev in rec.events:
        by_type.setdefault(ev.type, []).append(ev)
    assert any(e.data["uid"] == victim.uid for e in by_type["token_destroyed"])
    assert any(e.data["uid"] == survivor.uid for e in by_type["token_recycled"])
    assert any(e.data["uid"] == ship.uid for e in by_type["token_off_board"])
    # Kills are public; an unacquired survivor's identity is not.
    assert all(e.public for e in by_type["token_destroyed"])
    recycle = next(e for e in by_type["token_recycled"]
                   if e.data["uid"] == survivor.uid)
    assert not recycle.public and "F-16C" not in recycle.redacted


def test_score_report_structured():
    """Structured mirror of tests/test_tui.py::test_score_report_direct."""
    gs = GameState.new_game(campaign=1)
    gs.phase = Phase.PLAYER_TURN
    eng = RulesEngine(gs, rng=random.Random(0))
    gs.us.mission_card_id, gs.prc.mission_card_id = 51, 105   # both Attrition
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE,
                                         zone=CardZone.ACTIVE)
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D,
                         TokenOrigin.SQUADRON_CARD, source_card_id=60)
    gs.destroy_token(j10.uid, destroyed_by=Side.US)
    gs.us.vp_log.append((1, "enemy airbase VP boxes", 2))
    report = score_report(eng, 1)
    us = next(s for s in report.sides if s.side == "US")
    assert us.token_captures[0].label == f"J-10#{j10.uid}"
    assert us.token_captures[0].vp == 1
    assert us.accrued[0].reason == "enemy airbase VP boxes"
    assert us.accrued[0].points == 2
    assert us.ato_total == 3


def test_captures_and_base_damage_exposed():
    """Score piles and airbase damage boxes are public view data."""
    from afwip.view.serializer import captures_panel, status_view
    gs = GameState.new_game(campaign=1)
    gs.phase = Phase.PLAYER_TURN
    eng = RulesEngine(gs, rng=random.Random(0))
    gs.us.mission_card_id, gs.prc.mission_card_id = 51, 105   # both Attrition
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE,
                                         zone=CardZone.ACTIVE)
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D,
                         TokenOrigin.SQUADRON_CARD, source_card_id=60)
    gs.destroy_token(j10.uid, destroyed_by=Side.US)
    gs.destroy_squadron(Side.PRC, 60, destroyed_by=Side.US)
    gs.prc.airbase_vp_damage = 2

    us = captures_panel(eng, Side.US)
    kinds = {e.kind for e in us.entries}
    assert kinds == {"token", "squadron"}
    tok = next(e for e in us.entries if e.kind == "token")
    assert tok.label == f"J-10#{j10.uid}" and tok.victim_side == "PRC" and tok.vp == 1
    sq = next(e for e in us.entries if e.kind == "squadron")
    assert sq.card_id == 60 and sq.vp == 2                    # Attrition: card +2
    assert captures_panel(eng, Side.PRC).entries == []

    status = status_view(eng)
    assert status.base_damage == {"US": 0, "PRC": 2}
    from afwip.core.constants import IntelTrack
    gs.us.intel_track = IntelTrack.ADVANTAGE
    status = status_view(eng)
    assert status.intel == {"US": "ADVANTAGE", "PRC": "NORMAL"}
