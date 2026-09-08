"""Regression tests for the core rules engine (no enabler effects)."""

import random

import pytest

from afwip.core.rules import RulesEngine, RollContext, combine_modes, IllegalAction
from afwip.core.state import GameState, SquadronState, EnablerCardState, CaptureRecord, CardZone
from afwip.core.constants import (
    Side, BandID, TokenType, TokenOrigin, TokenScoreType, RollMode, Phase, MissionType,
)
from tests.helpers import draft_enablers, draft_squadrons


def _mid_turn(active=Side.US):
    gs = GameState.new_game(campaign=1)
    gs.phase = Phase.PLAYER_TURN
    gs.active_side = active
    gs.turn_number = 1
    return gs, RulesEngine(gs, rng=random.Random(1))


def test_combine_modes_cancellation():
    assert combine_modes([RollMode.ADVANTAGE, RollMode.DISADVANTAGE]) == RollMode.NORMAL
    assert combine_modes([RollMode.ADVANTAGE, RollMode.ADVANTAGE, RollMode.DISADVANTAGE]) == RollMode.ADVANTAGE
    assert combine_modes([RollMode.DISADVANTAGE]) == RollMode.DISADVANTAGE
    assert combine_modes([]) == RollMode.NORMAL


def test_offensive_ew_and_prc_space_based_ew_cancel_on_us_attacks():
    """US Offensive EW (28, advantage) and PRC Space-Based EW (90, disadvantage)
    are both enduring biases on US attack rolls; with both active they cancel
    one-for-one to NORMAL across every attack context (air/surface/base)."""
    gs, eng = _mid_turn(Side.US)
    tok = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_A,
                         TokenOrigin.SQUADRON_CARD, source_card_id=5)
    contexts = (RollContext.AIR_ATTACK, RollContext.SURF_ATTACK, RollContext.BASE_ATTACK)

    def endure(side, cid):
        gs.player(side).enablers[cid] = EnablerCardState(
            card_id=cid, side=side, zone=CardZone.ACTIVE, enduring=True)

    def mode(ctx):
        return eng.attack_mode(tok, ctx, target_side=Side.PRC, target_band=BandID.BAND_A)

    assert all(mode(c) == RollMode.NORMAL for c in contexts)          # baseline
    endure(Side.PRC, 90)                                              # PRC Space-Based EW
    assert all(mode(c) == RollMode.DISADVANTAGE for c in contexts)
    endure(Side.US, 28)                                              # + US Offensive EW
    assert all(mode(c) == RollMode.NORMAL for c in contexts)          # cancel
    gs.player(Side.PRC).enablers.pop(90)                             # only Offensive EW
    assert mode(RollContext.AIR_ATTACK) == RollMode.ADVANTAGE


def test_air_attack_requires_acquisition_then_destroys():
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True, location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True, location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    f22 = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C, TokenOrigin.SQUADRON_CARD, source_card_id=5)
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D, TokenOrigin.SQUADRON_CARD, source_card_id=60)

    with pytest.raises(IllegalAction):
        eng.shoot_air(Side.US, f22.uid, j10.uid)   # not acquired yet

    j10.acquired = True
    eng._d4 = lambda: 4                              # guaranteed hit, no Winchester
    result = eng.shoot_air(Side.US, f22.uid, j10.uid)
    assert result.hit and j10.uid in result.destroyed_token_uids
    assert gs.get_token(j10.uid) is None
    assert len(gs.us.captures) == 1


def test_ada_forces_disadvantage_on_base_attack():
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[7] = SquadronState(7, Side.US, activated=True, location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.squadrons[62] = SquadronState(62, Side.PRC, activated=True, location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.squadrons[59] = SquadronState(59, Side.PRC, activated=True, location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    b52 = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_STANDOFF, TokenOrigin.SQUADRON_CARD, source_card_id=7)
    gs.spawn_token(Side.PRC, TokenType.LONG_RANGE_ADA_PRC, BandID.PRC_AIRBASE, TokenOrigin.SQUADRON_CARD, source_card_id=59)

    result = eng.shoot_surface(Side.US, b52.uid, target_band=BandID.PRC_AIRBASE, target_squadron_id=62)
    assert result.hit_roll.mode == RollMode.DISADVANTAGE


def test_capture_scoring_attrition_vs_interdiction():
    from afwip.core.state import CaptureRecord
    gs, eng = _mid_turn()
    gs.us.captures = [
        CaptureRecord(1, is_squadron_card=False, destroyed_on_ground=False, score_type=TokenScoreType.BOMBER),
        CaptureRecord(1, is_squadron_card=False, destroyed_on_ground=False, score_type=TokenScoreType.FIGHTER),
        CaptureRecord(1, is_squadron_card=True, destroyed_on_ground=True),
    ]
    gs.us.mission_card_id = 51  # Attrition: 3 + 1 + 2
    assert eng.score_captures(Side.US) == 6
    gs.us.mission_card_id = 52  # Interdiction: 4 + 2 + 4
    assert eng.score_captures(Side.US) == 10


def test_full_ato_advances_and_finalizes():
    eng = RulesEngine(GameState.new_game(campaign=2), rng=random.Random(11))
    eng.setup_missions(51, 105)
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (10,)), draft_enablers(Side.US))
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, (60,)), draft_enablers(Side.PRC))
    eng.bid_for_initiative(first_player=Side.US)
    eng.play_intel()
    eng.begin_player_turns()
    eng.pass_turn(Side.US)
    eng.pass_turn(eng.state.active_side)
    assert eng.state.ato_cycle == 2 and eng.state.phase == Phase.ATO_SETUP

    eng.select_posture_only(Side.US, 49)     # ATO 2: posture only, roster redeploys
    eng.select_posture_only(Side.PRC, 103)
    eng.bid_for_initiative(first_player=Side.US)
    eng.play_intel()
    eng.begin_player_turns()
    eng.pass_turn(Side.US)
    eng.pass_turn(eng.state.active_side)
    assert eng.state.game_over


def test_cyber_rate_four_instant_win():
    gs, eng = _mid_turn()
    gs.set_cyber_rate(Side.PRC, 4)
    assert gs.game_over and gs.winner == Side.PRC


def _hedgehog_setup(ada_location=None):
    eng = RulesEngine(GameState.new_game(campaign=3), rng=random.Random(0))
    eng.setup_missions(51, 105)
    eng.select_posture(Side.US, 47, draft_squadrons(Side.US, (10,)), draft_enablers(Side.US))       # Hedgehog
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, (60,)), draft_enablers(Side.PRC))
    if ada_location is not None:
        eng.state.us.posture_bonus_ada_location = ada_location
    eng.bid_for_initiative(first_player=Side.US)
    eng.play_intel()
    eng.begin_player_turns()
    return [t for t in eng.state.us.living_tokens() if t.token_type == TokenType.ADA_US]


def test_hedgehog_posture_generates_bonus_ada():
    # US HEDGEHOG (card 47) grants 1x ADA token — the Airbase is the default.
    ada = _hedgehog_setup()
    assert len(ada) == 1 and ada[0].location == BandID.US_AIRBASE


def test_hedgehog_ada_can_be_placed_at_the_contingency_location():
    # The US owner may choose to place the Hedgehog ADA at the Contingency
    # Location instead (user ruling 2026-07-22).
    ada = _hedgehog_setup(ada_location=BandID.US_CONTINGENCY_LOCATION)
    assert len(ada) == 1 and ada[0].location == BandID.US_CONTINGENCY_LOCATION


def test_one_enabler_per_turn():
    eng = RulesEngine(GameState.new_game(campaign=3), rng=random.Random(0))
    eng.setup_missions(51, 105)
    # Hand includes two non-response cyber/space cards (21, 31).
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (10,)), draft_enablers(Side.US, [21, 31]))
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, (60,)), draft_enablers(Side.PRC))
    eng.bid_for_initiative(first_player=Side.US)
    eng.play_intel()
    eng.begin_player_turns()
    eng.play_enabler(Side.US, 21)                      # first enabler: OK
    with pytest.raises(IllegalAction):
        eng.play_enabler(Side.US, 31)                 # second enabler same turn: rejected
    # legal_actions should no longer offer any enabler play this turn.
    assert not any(a.kind == "play_enabler" for a in eng.legal_actions(Side.US))


def test_base_strike_can_target_vp_boxes():
    gs, eng = _mid_turn(Side.US)
    eng._d4 = lambda: 3
    gs.us.squadrons[7] = SquadronState(7, Side.US, activated=True, location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True, location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    b52 = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_STANDOFF, TokenOrigin.SQUADRON_CARD, source_card_id=7)
    # Direct all damage to the VP boxes even though a squadron sits at the base.
    r = eng.shoot_surface(Side.US, b52.uid, target_band=BandID.PRC_AIRBASE, target_vp_boxes=True)
    assert r.hit and r.base_vp_damage == 3
    assert gs.prc.airbase_vp_damage == 3
    assert not gs.prc.squadrons[60].is_destroyed      # squadron untouched


def test_damage_roll_ignores_enabler_advantage():
    # User ruling 2026-07-31: advantage/disadvantage applies to the ATTACK roll,
    # NOT the damage roll. Badger Surge advantages the H-6K's to-hit roll, but its
    # exploding-die damage roll is a plain single die (reverses the earlier
    # "carries to the damage roll" behavior; Missile Defense stays the exception).
    gs, eng = _mid_turn(Side.PRC)
    gs.prc.enablers[71] = EnablerCardState(71, Side.PRC, zone=CardZone.ACTIVE, enduring=True)
    gs.prc.squadrons[61] = SquadronState(61, Side.PRC, activated=True, location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True, location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    h6 = gs.spawn_token(Side.PRC, TokenType.H_6K, BandID.PRC_STANDOFF, TokenOrigin.SQUADRON_CARD, source_card_id=61)
    modes = []
    orig = eng.roll
    eng.roll = lambda mode=RollMode.NORMAL, bonus=0, note=None: (modes.append(mode), orig(mode, bonus))[1]
    eng._d4 = lambda: 3   # 3 >= H-6K surface threshold (2): hits, so a damage roll happens
    eng.shoot_surface(Side.PRC, h6.uid, target_band=BandID.US_AIRBASE, target_squadron_id=10)
    assert modes == [RollMode.ADVANTAGE, RollMode.NORMAL]   # to-hit advantaged; damage plain


def test_free_base_damage_distribution():
    gs, eng = _mid_turn(Side.US)
    eng._d4 = lambda: 3   # B-52 rolls 3 damage
    gs.us.squadrons[7] = SquadronState(7, Side.US, activated=True, location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True, location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.squadrons[62] = SquadronState(62, Side.PRC, activated=True, location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    b52 = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_STANDOFF, TokenOrigin.SQUADRON_CARD, source_card_id=7)
    eng.shoot_surface(Side.US, b52.uid, target_band=BandID.PRC_AIRBASE,
                      damage_allocator=lambda amount, targets: [("squadron", 60, 2), ("squadron", 62, 1)])
    assert gs.prc.squadrons[60].is_destroyed          # 2 points -> destroyed
    assert gs.prc.squadrons[62].damage == 1           # 1 point -> not destroyed


def test_cl_damage_limited_to_one_squadron():
    gs, eng = _mid_turn(Side.PRC)
    eng._d4 = lambda: 4
    gs.prc.squadrons[61] = SquadronState(61, Side.PRC, activated=True, location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True, location=BandID.US_CONTINGENCY_LOCATION, zone=CardZone.ACTIVE)
    gs.us.squadrons[8] = SquadronState(8, Side.US, activated=True, location=BandID.US_CONTINGENCY_LOCATION, zone=CardZone.ACTIVE)
    h6 = gs.spawn_token(Side.PRC, TokenType.H_6K, BandID.PRC_STANDOFF, TokenOrigin.SQUADRON_CARD, source_card_id=61)
    # Try to split across both CL squadrons; the rule permits only one to be hit.
    eng.shoot_surface(Side.PRC, h6.uid, target_band=BandID.US_CONTINGENCY_LOCATION,
                      damage_allocator=lambda amount, targets: [("squadron", 5, 2), ("squadron", 8, 2)])
    assert gs.us.squadrons[5].is_destroyed
    assert gs.us.squadrons[8].damage == 0             # CL: only one squadron may be targeted


def test_winchester_naval_goes_off_board_not_destroyed():
    gs, eng = _mid_turn(Side.US)
    ship = gs.spawn_token(Side.US, TokenType.DDG_81, BandID.BAND_C, TokenOrigin.ENABLER_CARD, source_card_id=37)
    ship.air_salvos_remaining = 0
    ship.surf_salvos_remaining = 0
    assert ship.is_winchester
    eng._start_turn(Side.US)
    assert ship.off_board and not ship.destroyed
    assert ship not in gs.us.living_tokens()
    assert len(gs.prc.captures) == 0                  # off-board != destroyed => no score


def test_airbase_vp_boxes_award_victory_points():
    eng = RulesEngine(GameState.new_game(campaign=3))
    eng.setup_missions(51, 105)
    eng.state.prc.airbase_vp_damage = 3               # US hit all 3 VP boxes on the PRC airbase
    eng._score_end_of_ato(Side.US)
    assert eng.state.us.victory_points == 3


def test_campaign4_air_unit_kill_bonus_per_squadron_and_capped():
    # Campaign 4: +1 VP per ENEMY SQUADRON wiped out entirely in the air this
    # ATO (every token shot down airborne, none on the ground, none surviving),
    # capped at +2 (user ruling 2026-07-22).
    from afwip.core.state import SquadronState
    from afwip.core.constants import Side, BandID, TokenType, TokenOrigin
    eng = RulesEngine(GameState.new_game(campaign=4))
    eng.setup_missions(51, 105)

    def wipe(cid, ground=False, survivor=False):
        eng.state.prc.squadrons[cid] = SquadronState(cid, Side.PRC)
        eng.state.us.captures.append(CaptureRecord(
            1, is_squadron_card=False, destroyed_on_ground=ground,
            score_type=TokenScoreType.FIGHTER, card_id=cid))
        if survivor:
            eng.state.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_C,
                                  TokenOrigin.SQUADRON_CARD, source_card_id=cid)
        eng._maybe_award_air_unit_kill(Side.US, cid)

    wipe(55, survivor=True)     # a token survived -> unit not destroyed in the air
    wipe(56, ground=True)       # a token died on the ground -> not "in the air"
    assert eng.state.us.victory_points == 0
    wipe(60); wipe(63); wipe(64)   # three wiped in the air, but the cap is +2/ATO
    assert eng.state.us.victory_points == 2
    assert eng.state.us.air_units_killed == {60, 63}       # third blocked by the cap


def test_campaign4_air_unit_bonus_fires_on_the_last_killing_shot():
    # The +1 lands on the air-to-air shot that empties the enemy squadron, not
    # before, and not at end of ATO.
    from afwip.core.state import SquadronState
    from afwip.core.constants import Side, BandID, TokenType, TokenOrigin
    gs = GameState.new_game(campaign=4)
    gs.phase = Phase.PLAYER_TURN
    gs.active_side = Side.US
    gs.turn_number = 1
    gs.us.mission_card_id, gs.prc.mission_card_id = 51, 105
    eng = RulesEngine(gs, rng=random.Random(1))
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    f22 = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=5)
    j1 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_C,
                        TokenOrigin.SQUADRON_CARD, source_card_id=60)
    j2 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_C,
                        TokenOrigin.SQUADRON_CARD, source_card_id=60)
    eng._d4 = lambda: 4                        # guaranteed hits, no Winchester
    j1.acquired = True
    eng.shoot_air(Side.US, f22.uid, j1.uid)
    assert gs.us.victory_points == 0           # squadron still has j2 -> no bonus yet
    gs.us.has_shot = False                      # next turn's shot
    j2.acquired = True
    eng.shoot_air(Side.US, f22.uid, j2.uid)
    assert gs.us.victory_points == 1           # the LAST killing shot wiped the unit
    assert 60 in gs.us.air_units_killed
