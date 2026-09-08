"""Drive the interactive harness with scripted stdin to confirm it plays a full
game (drafting -> turns -> game over) without crashing, and that placement,
missile defense, and response windows are wired into the turn flow."""

import random

import io
from contextlib import redirect_stdout

from afwip import harness
from afwip.core.rules import RulesEngine, LegalAction
from afwip.core.state import GameState, SquadronState, EnablerCardState, CardZone
from afwip.core.cards import ENABLER_REGISTRY
from afwip.core.constants import Side, BandID, TokenType, TokenOrigin, Phase, EnablerTrigger


def _mid_turn(active, campaign=3, seed=0):
    gs = GameState.new_game(campaign=campaign)
    gs.phase = Phase.PLAYER_TURN
    gs.active_side = active
    gs.turn_number = 1
    gs.us.posture_card_id = 49
    gs.prc.posture_card_id = 103
    return gs, RulesEngine(gs, rng=random.Random(seed))


def _scripted_input(script):
    """A fake input() that yields scripted answers, then 'q' to bail out safely."""
    it = iter(script)

    def fake(prompt=""):
        try:
            return next(it)
        except StopIteration:
            return "q"
    return fake


def test_base_damage_allocator_drops_saturated_targets(monkeypatch, capsys):
    # Point-by-point distribution over the NEW target set (Squadron Cards +
    # cardless tokens only): a squadron at max damage stops absorbing, full VP
    # boxes never appear, leftover damage is lost, and a face-down enemy card
    # is offered without its identity.
    gs, eng = _mid_turn(Side.US)
    prc_base = BandID.PRC_AIRBASE
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, damage=1,
                                         location=prc_base, zone=CardZone.SELECTED)
    ada = gs.spawn_token(Side.PRC, TokenType.MID_RANGE_ADA_PRC, prc_base,
                         TokenOrigin.ENABLER_CARD, source_card_id=None)
    targets = [("squadron", 60), ("token", ada.uid), ("vp", None)]
    gs.prc.airbase_vp_damage = 3                       # VP boxes already full

    monkeypatch.setattr("builtins.input", _scripted_input(["0"] * 4))
    allocation = harness._base_damage_allocator(eng, Side.PRC, prc_base)(4, targets)

    # 1 point kills the face-down squadron (damage 1 -> 2), the cardless ADA
    # takes 1 as the only remaining target, then everything saturates.
    assert allocation == [("squadron", 60, 1), ("token", ada.uid, 1)]
    out = capsys.readouterr().out
    assert "face-down Squadron Card" in out            # identity masked
    assert "J-10" not in out
    assert "remaining damage is lost" in out
    assert "Airbase VP damage boxes" not in out        # full boxes never offered


def test_interactive_manual_draft_completes(monkeypatch, capsys):
    # Campaign 1: mission (US,PRC), US posture, US squadron draft (F-16 forced +
    # more) and placement, PRC posture + draft, first-mover, then End-turn passes.
    # Picking index 0 throughout drafts a roster and then passes to a natural end.
    monkeypatch.setattr("builtins.input", _scripted_input(["0"] * 40))
    harness.interactive(campaign=1, seed=0)
    out = capsys.readouterr().out
    assert "US mission:" in out          # manual drafting was exercised
    assert "US squadrons" in out         # squadrons are now drafted, not fixed
    assert "required by campaign" in out # Campaign 1's forced card is pre-selected
    assert "?#" in out or "face-down" in out  # fog-of-war rendering present
    assert "GAME OVER" in out            # reached a natural end


def test_interactive_auto_draft_completes(monkeypatch, capsys):
    # --auto-draft skips card selection; two passes end the single-ATO campaign.
    monkeypatch.setattr("builtins.input", _scripted_input(["0", "0"]))
    harness.interactive(campaign=1, seed=0, auto_draft_setup=True)
    out = capsys.readouterr().out
    assert "GAME OVER" in out


def test_interactive_quit_is_clean(monkeypatch, capsys):
    # 'q' at the first prompt aborts without raising.
    monkeypatch.setattr("builtins.input", _scripted_input(["q"]))
    harness.interactive(campaign=3, seed=0, auto_draft_setup=True)
    out = capsys.readouterr().out
    assert "Quit." in out


def test_perform_activate_prompts_spawn_band(monkeypatch):
    # A B-52 may deploy to BAND_A or US_STANDOFF; choosing index 1 => US_STANDOFF.
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[2] = SquadronState(2, Side.US, zone=CardZone.SELECTED, location=BandID.US_AIRBASE)
    monkeypatch.setattr("builtins.input", _scripted_input(["1"]))
    harness._perform_action(eng, Side.US, LegalAction("activate", card_id=2), random.Random(0))
    b52 = [t for t in gs.us.tokens.values() if t.token_type == TokenType.B_52]
    assert len(b52) == 1 and b52[0].location == BandID.US_STANDOFF


def test_response_window_cancels_air_hit(monkeypatch):
    # PRC destroys an acquired US F-35; US responds with Air Launched Decoy (29) to revive it.
    gs, eng = _mid_turn(Side.PRC)
    eng._d4 = lambda: 4
    gs.prc.squadrons[62] = SquadronState(62, Side.PRC, activated=True, location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True, location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    jj = gs.spawn_token(Side.PRC, TokenType.J_20B, BandID.BAND_A, TokenOrigin.SQUADRON_CARD, source_card_id=62)
    us = gs.spawn_token(Side.US, TokenType.F_35A, BandID.BAND_A, TokenOrigin.SQUADRON_CARD, source_card_id=5)
    us.acquired = True
    gs.us.enablers[29] = EnablerCardState(29, Side.US, zone=CardZone.SELECTED)
    monkeypatch.setattr("builtins.input", _scripted_input(["0"]))   # US response picks card 29
    harness._perform_action(eng, Side.PRC, LegalAction("shoot_air", token_uid=jj.uid, target_uid=us.uid), random.Random(0))
    assert gs.get_token(us.uid) is not None       # F-35 revived by the response
    assert len(gs.prc.captures) == 0              # capture reversed


def test_missile_defense_declaration(monkeypatch):
    # US B-52 strikes the PRC airbase; PRC declares naval missile defense (consumes an air salvo).
    gs, eng = _mid_turn(Side.US)
    eng._d4 = lambda: 3
    gs.us.squadrons[7] = SquadronState(7, Side.US, activated=True, location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    b52 = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_STANDOFF, TokenOrigin.SQUADRON_CARD, source_card_id=7)
    ship = gs.spawn_token(Side.PRC, TokenType.NANNING_162, BandID.BAND_C, TokenOrigin.ENABLER_CARD, source_card_id=87)
    assert ship.air_salvos_remaining == 4
    # Inputs: declare MD with the ship (0), then aim the damage (blank => default).
    monkeypatch.setattr("builtins.input", _scripted_input(["0", ""]))
    harness._perform_action(eng, Side.US, LegalAction("shoot_surface", token_uid=b52.uid, target_band=BandID.PRC_AIRBASE), random.Random(0))
    assert ship.air_salvos_remaining == 3          # a salvo block was covered => MD fired


def test_resilient_bases_window_opens_after_hypersonic(monkeypatch, capsys):
    # Walkthrough turn 2: PRC Hypersonic Missile hits the US base; US responds
    # with Resilient Bases, cancelling all damage. The window is event-driven
    # (opened because the card dealt base damage), and the turn stays PRC's.
    gs, eng = _mid_turn(Side.PRC)
    eng._d4 = lambda: 3
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.enablers[78] = EnablerCardState(78, Side.PRC, zone=CardZone.SELECTED)
    gs.us.enablers[39] = EnablerCardState(39, Side.US, zone=CardZone.SELECTED)
    monkeypatch.setattr("builtins.input", _scripted_input(["0"]))   # US picks Resilient Bases
    harness._perform_action(eng, Side.PRC, LegalAction("play_enabler", card_id=78,
                                                       play=eng._default_enabler_play(Side.PRC, 78)),
                            random.Random(0))
    out = capsys.readouterr().out
    assert "REACTION WINDOW" in out and "turn continues" in out
    assert not gs.us.squadrons[10].is_destroyed and gs.us.squadrons[10].damage == 0
    assert gs.us.airbase_vp_damage == 0
    assert eng.state.active_side == Side.PRC            # response never moves the turn


def test_response_window_excludes_irrelevant_cards(monkeypatch):
    # Playing Shandong J-15 (85, naval-air) triggers no cancel; US holds cards whose
    # triggers (attack-base / aircraft-lost / anytime) do NOT match -> no prompt shown.
    gs, eng = _mid_turn(Side.PRC)
    for c in (43, 39, 12):   # Submarine Strike, Resilient Bases, Personnel Recovery
        gs.us.enablers[c] = EnablerCardState(c, Side.US, zone=CardZone.SELECTED)
    triggers = harness.card_play_triggers(ENABLER_REGISTRY[85])
    assert triggers == set()

    calls = {"n": 0}
    monkeypatch.setattr("builtins.input", lambda p="": calls.__setitem__("n", calls["n"] + 1) or "")
    harness._response_window(eng, Side.US, "cancel the card", triggers)
    assert calls["n"] == 0   # nothing matched, so no prompt was issued


def test_response_window_includes_matching_card(monkeypatch):
    # PRC plays a SPACE card -> only US Counter Space (32) is offered, not Resilient Bases.
    gs, eng = _mid_turn(Side.PRC)
    gs.us.enablers[32] = EnablerCardState(32, Side.US, zone=CardZone.SELECTED)  # Counter Space
    gs.us.enablers[39] = EnablerCardState(39, Side.US, zone=CardZone.SELECTED)  # Resilient Bases
    triggers = harness.card_play_triggers(ENABLER_REGISTRY[94])  # Space Recon
    assert EnablerTrigger.OPP_PLAYS_SPACE_CARD in triggers

    monkeypatch.setattr("builtins.input", lambda p="": "")   # blank => skip after listing
    buf = io.StringIO()
    with redirect_stdout(buf):
        harness._response_window(eng, Side.US, "cancel the card", triggers)
    out = buf.getvalue()
    assert "COUNTER SPACE" in out and "RESILIENT" not in out


def test_ada_posture_draft_ui_offers_only_ada_after_base(monkeypatch):
    # ADA posture: base 4 + 2 ADA bonus. Pick 4 fighters, then only ADA cards remain offerable.
    from afwip.core.cards import SQUADRON_REGISTRY
    from afwip.core.tokens import TOKEN_REGISTRY
    from afwip.core.constants import TokenScoreType

    prof = harness.POSTURE_REGISTRY[101]
    pool = [c for c in SQUADRON_REGISTRY if SQUADRON_REGISTRY[c].side == Side.PRC]
    bonus = [(lambda c: harness._is_score(c, TokenScoreType.ADA), prof.ada_bonus_squadron),
             (lambda c: harness._is_score(c, TokenScoreType.BOMBER), prof.bomber_bonus)]
    # Greedily pick index 0 each step; the picker itself stops offering once the
    # 4 general + 2 ADA slots are full (exactly 6 picks), so it never asks a 7th time.
    monkeypatch.setattr("builtins.input", _scripted_input(["0"] * 6))
    chosen = harness._pick_conditional("PRC squadrons", pool, lambda c: str(c), prof.squadrons, bonus)
    ada = [c for c in chosen if TOKEN_REGISTRY[SQUADRON_REGISTRY[c].token_type].token_score_type == TokenScoreType.ADA]
    general = [c for c in chosen if c not in ada]
    assert len(chosen) == 6 and len(general) == 4 and len(ada) == 2
