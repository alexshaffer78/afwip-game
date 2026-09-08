"""Regression tests for rules-fidelity fixes made against the AFWIP docs:
Player Guide, Overview transcript, token sheets, and card references."""

import random

import pytest

from afwip.core.rules import RulesEngine, IllegalAction
from afwip.core.enablers import EnablerPlay
from afwip.core.state import GameState, SquadronState, EnablerCardState, CardZone
from afwip.core.campaigns import get_campaign
from afwip.core.cards import POSTURE_REGISTRY, SQUADRON_REGISTRY
from afwip.core.tokens import TOKEN_REGISTRY
from afwip.core.board import valid_spawn_locations, ON_MAP_BANDS
from afwip.core.constants import (
    Side, BandID, TokenType, TokenOrigin, TokenScoreType, RollMode, Phase,
    PostureType, IntelTrack,
)
from tests.helpers import draft_enablers, draft_squadrons


def _mid_turn(active=Side.US, campaign=1):
    gs = GameState.new_game(campaign=campaign)
    gs.phase = Phase.PLAYER_TURN
    gs.active_side = active
    gs.turn_number = 1
    return gs, RulesEngine(gs, rng=random.Random(1))


def _setup(active: Side, us_en=(), prc_en=(), us_sq=(10,), prc_sq=(60,), campaign=3, seed=0):
    eng = RulesEngine(GameState.new_game(campaign), rng=random.Random(seed))
    eng.setup_missions(51, 105)
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, us_sq, camp=eng.campaign),
                   draft_enablers(Side.US, us_en))
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, prc_sq, camp=eng.campaign),
                   draft_enablers(Side.PRC, prc_en))
    eng.bid_for_initiative(first_player=active)
    eng.play_intel()
    eng.begin_player_turns()
    assert eng.state.active_side == active
    return eng


def _mode_log(eng):
    """Wrap eng.roll to record the RollMode of every roll made."""
    modes = []
    orig = eng.roll
    eng.roll = lambda mode=RollMode.NORMAL, bonus=0, note=None: (modes.append(mode), orig(mode, bonus))[1]
    return modes


# --- token data (docs) --------------------------------------------------------

def test_flotilla_has_exploding_die():
    # Confirmed against the physical token: the Flotilla's surface attack
    # uses an exploding die (the PRC token sheet's notes omit it).
    assert TOKEN_REGISTRY[TokenType.FLOTILLA].surf_exploding_die


def test_confirmed_token_generation_counts():
    # Confirmed against the physical game: 1 B-52 per bomb squadron, 4 J-20Bs
    # per air brigade (the card reference tables say "4x"/"1x" — typos).
    assert TOKEN_REGISTRY[TokenType.B_52].token_count == 1
    assert TOKEN_REGISTRY[TokenType.J_20B].token_count == 4


def test_prc_attack_uas_spawns_any_band():
    # Player Guide: "You may place your UAS Tokens on any range band."
    assert TOKEN_REGISTRY[TokenType.ATTACK_UAS_PRC].spawn_bands == ON_MAP_BANDS


def test_us_ada_may_spawn_at_cl_without_ace():
    # Card 36: "Generate: 1x ADA token on the US Airbase or Contingency Location."
    bands = valid_spawn_locations(TokenType.ADA_US, Side.US, PostureType.STANDARD)
    assert BandID.US_CONTINGENCY_LOCATION in bands
    # SURGE: Contingency Locations cannot be used.
    bands = valid_spawn_locations(TokenType.ADA_US, Side.US, PostureType.SURGE)
    assert BandID.US_CONTINGENCY_LOCATION not in bands


def test_campaign4_bans_tomahawk():
    # "No long-range missile ... Enabler Cards permitted."
    assert not get_campaign(4).enabler_allowed(42)


# --- winchester return / landing ----------------------------------------------

def test_winchester_return_attaches_to_squadron_card():
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    f16 = gs.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_B,
                         TokenOrigin.SQUADRON_CARD, source_card_id=10)
    f16.winchester = True
    eng._start_turn(Side.US)
    assert f16.grounded and f16.location == BandID.US_AIRBASE
    assert f16.uid in gs.us.squadrons[10].grounded_token_uids
    # Destroying the squadron now destroys the returned token with it.
    gs.destroy_squadron(Side.US, 10, destroyed_by=Side.PRC)
    assert gs.get_token(f16.uid) is None


def test_airborne_token_of_destroyed_squadron_lost_at_ato_end():
    # "Any airborne unit that lands on a destroyed squadron is destroyed upon landing."
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE,
                                        damage=2)   # destroyed
    f16 = gs.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_B,
                         TokenOrigin.SQUADRON_CARD, source_card_id=10)
    eng.end_ato_cycle()
    assert f16.destroyed
    assert any(not c.is_squadron_card for c in gs.prc.captures)


# --- setup: persistence, postures, placement ------------------------------------

def _end_cycle_with_pass(eng):
    eng.pass_turn(eng.state.active_side)
    eng.pass_turn(eng.state.active_side)


def test_roster_persists_into_new_ato_enablers_redraft():
    # Across ATOs: a completely destroyed squadron stays out (scored), a survivor
    # redeploys with its partial CARD damage RESET (ruling 2026-07-31) but its
    # TOKEN losses persisting; enablers re-draft EVERY cycle (ruling 2026-07-17):
    # played single-use cards are gone for the campaign. Squadrons re-draft too
    # (ruling 2026-07-22) but the count floor still applies (ruling 2026-07-31).
    eng = _setup(Side.US, us_sq=(10, 5), us_en=(19,), campaign=2)
    eng.play_enabler(Side.US, 19)                       # Improved Munitions: single use
    eng.state.us.squadrons[10].damage = 2               # F-16 squadron destroyed
    eng.state.us.squadrons[5].damage = 1                # F-22 squadron dinged
    eng.end_turn(Side.US)
    _end_cycle_with_pass(eng)
    assert eng.state.ato_cycle == 2 and eng.state.phase == Phase.ATO_SETUP

    with pytest.raises(IllegalAction):                  # 1 < the Standard floor of 3
        eng.select_posture(Side.US, 49, [5], draft_enablers(Side.US))
    with pytest.raises(IllegalAction):                  # played single-use is gone
        eng.select_posture_only(
            Side.US, 49, draft_enablers(Side.US, include=(19,), camp=eng.campaign))

    eng.select_posture_only(Side.US, 49)                # auto-draft: fresh hand
    us = eng.state.us
    assert us.squadrons[10].zone == CardZone.DESTROYED  # stays out
    assert us.squadrons[5].zone == CardZone.SELECTED    # survivor redeploys
    assert us.squadrons[5].damage == 0                  # partial card damage reset
    hand = {c.card_id for c in us.enablers_in_hand()}
    assert 19 not in hand                               # single-use stays REMOVED
    assert len(hand) == POSTURE_REGISTRY[49].enablers   # full fresh draft


def test_plaaf_posture_requires_plaaf_enablers():
    eng = RulesEngine(GameState.new_game(campaign=3))
    eng.setup_missions(51, 105)
    with pytest.raises(IllegalAction):                  # Ballistic Missile is PLARF
        eng.select_posture(Side.PRC, 99, draft_squadrons(Side.PRC, (60,),
                           n=POSTURE_REGISTRY[99].squadrons), [75, 69, 70, 71, 72])
    # Five PLAAF cards (the posture's exact enabler count).
    eng.select_posture(Side.PRC, 99, draft_squadrons(Side.PRC, (60,),
                       n=POSTURE_REGISTRY[99].squadrons), [69, 70, 71, 72, 73])


def test_joint_operations_requires_flying_squadrons():
    eng = RulesEngine(GameState.new_game(campaign=3))
    eng.setup_missions(51, 105)
    nine = draft_enablers(Side.PRC, n=9)                # Joint Ops: 9 enablers
    with pytest.raises(IllegalAction):
        bad = [56] + draft_squadrons(Side.PRC, flying_only=True, n=2, exclude=(56,))
        eng.select_posture(Side.PRC, 100, bad, nine)   # Mid-Range ADA is not flying
    eng.select_posture(Side.PRC, 100,
                       draft_squadrons(Side.PRC, (60,), n=3, flying_only=True), nine)


def test_cl_deployment_rolls_for_generation():
    eng = RulesEngine(GameState.new_game(campaign=3), rng=random.Random(0))
    eng.setup_missions(51, 105)
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (10,)), draft_enablers(Side.US),
                       squadron_locations={10: BandID.US_CONTINGENCY_LOCATION})
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, (60,)), draft_enablers(Side.PRC))
    eng.bid_for_initiative(first_player=Side.US)
    eng.play_intel()
    eng.begin_player_turns()
    eng._d4 = lambda: 2                                 # 2 of 4 F-16s generate
    tokens = eng.activate_squadron(Side.US, 10)
    flying = [t for t in tokens if not t.grounded]
    grounded = [t for t in tokens if t.grounded]
    assert len(flying) == 2 and len(grounded) == 2
    assert all(t.location == BandID.US_CONTINGENCY_LOCATION for t in grounded)
    assert set(eng.state.us.squadrons[10].grounded_token_uids) == {t.uid for t in grounded}


def test_surge_posture_forbids_cl_deployment():
    eng = RulesEngine(GameState.new_game(campaign=3))
    eng.setup_missions(51, 105)
    with pytest.raises(IllegalAction):
        eng.select_posture(Side.US, 46, [10], [],
                           squadron_locations={10: BandID.US_CONTINGENCY_LOCATION})


# --- bid for initiative ----------------------------------------------------------

def test_bid_sacrifice_returns_cards_to_deck_and_adds_modifier():
    eng = RulesEngine(GameState.new_game(campaign=3), rng=random.Random(0))
    eng.setup_missions(51, 105)
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (10,)), draft_enablers(Side.US, [21, 31]))
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, (60,)), draft_enablers(Side.PRC))
    rolls = iter([1, 1, 1])                             # US bid, PRC bid, cyber raise
    eng._d4 = lambda: next(rolls)
    winner = eng.bid_for_initiative(us_sacrifice=[21, 31])
    assert winner == Side.US                            # 1+2 beats 1
    assert eng.state.us.enablers[21].zone == CardZone.DECK
    assert eng.state.us.enablers[31].zone == CardZone.DECK
    assert len(eng.state.us.enablers_in_hand()) == 4    # 6 drafted - 2 sacrificed


def test_tournament_forbids_bid_sacrifice():
    eng = RulesEngine(GameState.new_game(campaign=2), rng=random.Random(0))
    eng.setup_missions(51, 105)
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (10,)), draft_enablers(Side.US, [21]))
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, (60,)), draft_enablers(Side.PRC))
    with pytest.raises(IllegalAction):
        eng.bid_for_initiative(us_sacrifice=[21])


# --- enabler strikes and missile defense ------------------------------------------

def test_enabler_damage_roll_ignores_ew_it_is_a_single_die():
    # (FAQ 2026-07-24) For an Enabler Card, advantage/disadvantage applies only to
    # the hit roll; the damage roll is a single die. Hypersonic (78) auto-hits (no
    # hit roll), so US Space-Based EW (35) has nothing to bias — the damage roll
    # is plain (reverses the old "EW applies to the damage roll" behavior).
    eng = _setup(Side.PRC, prc_en=(78,))
    eng.state.us.enablers[35] = EnablerCardState(35, Side.US, zone=CardZone.ACTIVE, enduring=True)
    modes = _mode_log(eng)
    eng.play_enabler(Side.PRC, 78)
    assert RollMode.DISADVANTAGE not in modes


def test_enabler_disadvantage_applies_to_the_hit_roll_only():
    # (FAQ 2026-07-24) PRC Long-Range ADA covers the PRC airbase: US HIMARS rolls
    # the 2+ hit gate at disadvantage, but the damage roll is a single plain die —
    # exactly ONE disadvantaged roll, not two.
    eng = _setup(Side.US, us_en=(41,))
    eng.state.spawn_token(Side.PRC, TokenType.LONG_RANGE_ADA_PRC, BandID.PRC_AIRBASE,
                          TokenOrigin.SQUADRON_CARD, source_card_id=59)
    modes = _mode_log(eng)
    eng.play_enabler(Side.US, 41)
    assert modes.count(RollMode.DISADVANTAGE) == 1     # hit gate only; damage is plain


def test_naval_md_against_enabler_strike_must_be_declared_and_spends_salvo():
    eng = _setup(Side.PRC, prc_en=(75,))
    ddg = eng.state.spawn_token(Side.US, TokenType.DDG_81, BandID.BAND_C,
                                TokenOrigin.ENABLER_CARD, source_card_id=37)
    modes = _mode_log(eng)
    eng.play_enabler(Side.PRC, 75, EnablerPlay(missile_defense_uid=ddg.uid))
    assert ddg.air_salvos_remaining == 3                # declaring covered a salvo block
    assert RollMode.DISADVANTAGE in modes


def test_naval_md_is_not_automatic_against_enabler_strike():
    eng = _setup(Side.PRC, prc_en=(75,))
    eng.state.spawn_token(Side.US, TokenType.DDG_81, BandID.BAND_C,
                          TokenOrigin.ENABLER_CARD, source_card_id=37)
    modes = _mode_log(eng)
    eng.play_enabler(Side.PRC, 75)                      # no declaration
    assert RollMode.DISADVANTAGE not in modes


def test_decoy_warheads_cancels_declared_md_but_salvo_is_spent():
    eng = _setup(Side.PRC, prc_en=(75, 79))
    ddg = eng.state.spawn_token(Side.US, TokenType.DDG_81, BandID.BAND_C,
                                TokenOrigin.ENABLER_CARD, source_card_id=37)
    eng.play_enabler(Side.PRC, 79, response=True)       # cancel the coming MD
    modes = _mode_log(eng)
    eng.play_enabler(Side.PRC, 75, EnablerPlay(missile_defense_uid=ddg.uid))
    assert ddg.air_salvos_remaining == 3                # marker placed on declaration
    assert RollMode.DISADVANTAGE not in modes           # ...but no disadvantage


def test_missile_defense_still_disadvantages_the_token_damage_roll():
    # User ruling 2026-07-31: advantage/disadvantage applies to the attack roll,
    # not the damage roll — EXCEPT Missile Defense, which the Player Guide keeps
    # on BOTH rolls. A PRC H-6K striking the US airbase through a covering US ADA
    # rolls the to-hit gate AND the exploding-die damage roll at disadvantage.
    gs, eng = _mid_turn(Side.PRC)
    gs.prc.squadrons[61] = SquadronState(61, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    h6 = gs.spawn_token(Side.PRC, TokenType.H_6K, BandID.PRC_STANDOFF,
                        TokenOrigin.SQUADRON_CARD, source_card_id=61)
    gs.spawn_token(Side.US, TokenType.ADA_US, BandID.US_AIRBASE,
                   TokenOrigin.ENABLER_CARD)   # WEZ 1 covers a strike on the airbase
    modes = _mode_log(eng)
    eng._d4 = lambda: 3   # 3 >= H-6K surface threshold (2): hits, so a damage roll happens
    r = eng.shoot_surface(Side.PRC, h6.uid, target_band=BandID.US_AIRBASE)
    assert r.hit
    assert modes == [RollMode.DISADVANTAGE, RollMode.DISADVANTAGE]   # hit AND damage


def test_auto_hit_strike_never_winchesters():
    # User ruling 2026-08-06: Winchester is set by the HIT roll only. An auto-hit
    # strike (Forward Observers) has no hit roll — it counts as a clean hit (like
    # a natural 4) — so the attacker NEVER goes Winchester, regardless of the
    # damage roll. (Reverses the earlier "damage roll drives Winchester" reading.)
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[7] = SquadronState(7, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    b52 = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_STANDOFF,
                         TokenOrigin.SQUADRON_CARD, source_card_id=7)
    gs.us.pending_auto_hit = True
    eng._d4 = lambda: 1                                 # damage roll 1 would have
    res = eng.shoot_surface(Side.US, b52.uid, target_band=BandID.PRC_AIRBASE)
    assert res.hit and res.hit_roll is None
    assert not res.attacker_winchester and not b52.winchester


# --- individual enabler effects -----------------------------------------------------

def test_uas_proliferation_rolls_for_the_extra_acquisition():
    eng = _setup(Side.PRC, prc_en=(68,))
    f22 = eng.state.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C,
                                TokenOrigin.SQUADRON_CARD, source_card_id=5)
    eng._d4 = lambda: 3                                 # F-22 acquisition value is 4
    res = eng.play_enabler(Side.PRC, 68, EnablerPlay(target_uids=[f22.uid]), response=True)
    assert res.acquired == [] and not f22.acquired      # 3 < 4: the roll can fail


def test_rapid_resupply_revives_destroyed_squadron_and_voids_its_scoring():
    eng = _setup(Side.US, us_en=(18,), us_sq=(10, 5))
    eng.state.destroy_squadron(Side.US, 5, destroyed_by=Side.PRC)
    assert any(c.is_squadron_card for c in eng.state.prc.captures)
    res = eng.play_enabler(Side.US, 18, EnablerPlay(target_squadron_id=5),
                           response=True)   # 18 is response-only (2026-07-17)
    assert res.recovered == [5]
    squad = eng.state.us.squadrons[5]
    assert not squad.is_destroyed and squad.zone == CardZone.SELECTED
    assert not any(c.is_squadron_card for c in eng.state.prc.captures)


def test_constellation_reconstitution_returns_plassf_card_to_deck():
    eng = _setup(Side.PRC, prc_en=(91, 80))
    eng.state.prc.enablers[80].zone = CardZone.PLAYED   # spent PLASSF cyber card
    res = eng.play_enabler(Side.PRC, 91, EnablerPlay(target_squadron_id=80))
    assert res.recovered == [80]
    assert eng.state.prc.enablers[80].zone == CardZone.DECK   # next ATO, not hand


def test_cancel_card_respects_card_class():
    # AC-130 (11) cancels SOF cards only — it cannot void a PRC space card.
    eng = _setup(Side.PRC, prc_en=(94,), us_en=(11,))
    eng.play_enabler(Side.PRC, 94)                      # Space Reconnaissance
    res = eng.play_enabler(Side.US, 11, response=True)
    assert not res.cancelled
    assert 94 in eng.state.prc.enablers_played_log


def test_munitions_upgrade_requires_own_fighter_squadron():
    eng = _setup(Side.PRC, prc_en=(74,), prc_sq=(61,))  # only the H-6K bomber squadron
    with pytest.raises(IllegalAction):
        eng.play_enabler(Side.PRC, 74, EnablerPlay(target_squadron_id=61))


# --- base attacks: tokens, infantry battalion, standoff strikes -----------------------

def test_base_strike_hits_acquired_ada_only():
    # (User ruling 2026-08-10, reversing the 2026-07-24 FAQ) A base strike CAN
    # hit ADA sitting on the base — but only once it has been ACQUIRED. An
    # unacquired ADA is still invisible to the strike.
    gs, eng = _mid_turn(Side.PRC)
    gs.prc.squadrons[61] = SquadronState(61, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    h6 = gs.spawn_token(Side.PRC, TokenType.H_6K, BandID.PRC_STANDOFF,
                        TokenOrigin.SQUADRON_CARD, source_card_id=61)
    ada = gs.spawn_token(Side.US, TokenType.ADA_US, BandID.US_AIRBASE,
                         TokenOrigin.ENABLER_CARD, source_card_id=36)
    eng._d4 = lambda: 3
    # Unacquired: not an allocation target.
    assert ("token", ada.uid) not in eng._base_allocation_targets(Side.US, BandID.US_AIRBASE)
    # Acquired: now a target, and a base strike destroys it.
    ada.acquired = True
    assert ("token", ada.uid) in eng._base_allocation_targets(Side.US, BandID.US_AIRBASE)
    r = eng.shoot_surface(Side.PRC, h6.uid, target_band=BandID.US_AIRBASE,
                          damage_allocator=lambda amt, tg: [("token", ada.uid, 1)])
    assert r.hit and gs.get_token(ada.uid) is None      # acquired ADA destroyed


def test_destroying_ada_squadron_card_destroys_its_ada_token():
    # (User ruling 2026-08-10) ADA is a ground asset — it does NOT "keep flying"
    # like an airborne aircraft. Destroying its Squadron Card destroys the
    # deployed ADA token immediately, scored for the destroyer.
    from afwip.core.cards import SQUADRON_REGISTRY
    gs, eng = _mid_turn(Side.US)
    ada_type = SQUADRON_REGISTRY[56].token_type          # 3rd Air Defense Brigade (Mid Range ADA)
    gs.prc.squadrons[56] = SquadronState(56, Side.PRC, activated=True, damage=1,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    ada = gs.spawn_token(Side.PRC, ada_type, BandID.PRC_AIRBASE,
                         TokenOrigin.SQUADRON_CARD, source_card_id=56)
    assert not ada.grounded                              # deployed, not on the card
    gs.destroy_squadron(Side.PRC, 56, destroyed_by=Side.US, on_ground=True)
    assert gs.get_token(ada.uid) is None                 # ADA dies with the card
    assert any(c.score_type == TokenScoreType.ADA for c in gs.us.captures)


def test_ada_cannot_be_hit_air_to_air():
    # (User ruling 2026-08-10, reverses FAQ 2026-07-24's "shot like an aircraft")
    # ADA is a ground asset: a fighter's air-to-air CANNOT target it. It is
    # killed only by a surface / base strike (see
    # test_base_strike_hits_acquired_ada_only) or with its Squadron Card.
    gs, eng = _mid_turn(Side.PRC)
    gs.prc.squadrons[62] = SquadronState(62, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    j20 = gs.spawn_token(Side.PRC, TokenType.J_20B, BandID.BAND_A,
                         TokenOrigin.SQUADRON_CARD, source_card_id=62)
    ada = gs.spawn_token(Side.US, TokenType.ADA_US, BandID.US_AIRBASE,
                         TokenOrigin.ENABLER_CARD, source_card_id=36)
    eng._d4 = lambda: 4
    eng.acquire(Side.PRC, j20.uid, ada.uid)
    assert ada.acquired                                 # acquirable, still
    # Not offered as an air-to-air target, and a direct call is rejected.
    assert not any(a.kind == "shoot_air" and a.target_uid == ada.uid
                   for a in eng.legal_actions(Side.PRC))
    with pytest.raises(IllegalAction):
        eng.shoot_air(Side.PRC, j20.uid, ada.uid)
    assert gs.get_token(ada.uid) is not None             # ADA survives the fighter


def test_fighters_cannot_move_into_standoff():
    # Standoff bands are for bombers / AEW only — a fighter can never move there
    # (the engine excludes it; not offered and a direct move raises).
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[1] = SquadronState(1, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    f22 = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_A,
                         TokenOrigin.SQUADRON_CARD, source_card_id=1)
    dests = {a.dest_band for a in eng.legal_actions(Side.US)
             if a.kind == "move" and a.token_uid == f22.uid}
    assert BandID.US_STANDOFF not in dests and BandID.PRC_STANDOFF not in dests
    with pytest.raises(IllegalAction):
        eng.move(Side.US, f22.uid, BandID.US_STANDOFF)


def test_standoff_aircraft_reachable_by_air_to_air_from_adjacent_band():
    # Standoff is a 6th band adjacent to the front band (US_STANDOFF~BAND_A): a
    # fighter within air-attack range may engage a standoff aircraft air-to-air
    # (user ruling 2026-08-14, reverses 2026-08-10). Surface/standoff strike into
    # standoff still works too — both are offered.
    gs, eng = _mid_turn(Side.PRC)
    gs.us.squadrons[8] = SquadronState(8, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    bomber = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_STANDOFF,
                            TokenOrigin.SQUADRON_CARD, source_card_id=8)
    bomber.acquired = True
    jh7 = gs.spawn_token(Side.PRC, TokenType.JH_7, BandID.BAND_A,      # adjacent, r1
                         TokenOrigin.SQUADRON_CARD, source_card_id=99)
    la = eng.legal_actions(Side.PRC)
    assert any(a.kind == "shoot_air" and a.target_uid == bomber.uid for a in la)
    assert any(a.kind == "shoot_surface" and a.target_uid == bomber.uid for a in la)
    # The air-to-air shot resolves as a single-hit kill (force a hitting roll).
    eng._d4 = lambda: 4
    eng.shoot_air(Side.PRC, jh7.uid, bomber.uid)
    assert gs.get_token(bomber.uid) is None


def test_standoff_air_to_air_is_range_gated():
    # Reach into standoff still obeys air-attack range: an r1 fighter two bands
    # out (BAND_B is distance 2 from US_STANDOFF) cannot shoot into it — standoff
    # is the 6th band, one step beyond the adjacent front band.
    gs, eng = _mid_turn(Side.PRC)
    gs.us.squadrons[8] = SquadronState(8, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    bomber = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_STANDOFF,
                            TokenOrigin.SQUADRON_CARD, source_card_id=8)
    bomber.acquired = True
    jh7 = gs.spawn_token(Side.PRC, TokenType.JH_7, BandID.BAND_B,      # r1, distance 2
                         TokenOrigin.SQUADRON_CARD, source_card_id=99)
    assert not any(a.kind == "shoot_air" and a.target_uid == bomber.uid
                   for a in eng.legal_actions(Side.PRC))
    with pytest.raises(IllegalAction):
        eng.shoot_air(Side.PRC, jh7.uid, bomber.uid)


def test_killing_all_tokens_does_not_destroy_or_score_the_card():
    # Killing every TOKEN of a squadron (bomber = 1 token) does NOT destroy or
    # score its Squadron Card — the card is destroyed only by base-strike damage.
    from afwip.core.cards import SQUADRON_REGISTRY
    bcid = next(c for c, p in SQUADRON_REGISTRY.items()
                if p.side == Side.PRC
                and TOKEN_REGISTRY[p.token_type].token_score_type == TokenScoreType.BOMBER)
    btype = SQUADRON_REGISTRY[bcid].token_type
    gs, eng = _mid_turn(Side.US)
    gs.prc.squadrons[bcid] = SquadronState(bcid, Side.PRC, activated=True,
                                           location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    bomber = gs.spawn_token(Side.PRC, btype, BandID.BAND_C,
                            TokenOrigin.SQUADRON_CARD, source_card_id=bcid)
    f22 = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=1)
    eng._d4 = lambda: 4
    eng.acquire(Side.US, f22.uid, bomber.uid)
    eng.shoot_air(Side.US, f22.uid, bomber.uid)
    sq = gs.prc.squadrons[bcid]
    assert gs.get_token(bomber.uid) is None                     # token dead
    assert not sq.is_destroyed and sq.zone == CardZone.ACTIVE    # card survives
    assert not any(c.is_squadron_card for c in gs.us.captures)   # no +2 card capture


def test_multirole_fighter_surface_strikes_ada_air_only_cannot():
    # (User ruling 2026-08-10) A SURFACE-capable fighter (F-35, surf_atk) may
    # surface-strike an acquired ADA; an air-only fighter (F-22) cannot — the
    # gate is surface-attack capability.
    from afwip.core.cards import SQUADRON_REGISTRY
    from afwip.core import board
    gs, eng = _mid_turn(Side.US)
    ada_type = SQUADRON_REGISTRY[56].token_type
    gs.prc.squadrons[56] = SquadronState(56, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    ada = gs.spawn_token(Side.PRC, ada_type, BandID.PRC_AIRBASE,
                         TokenOrigin.SQUADRON_CARD, source_card_id=56)
    band = next(b for b in BandID if board.is_on_map(b)
                and board.in_range(b, BandID.PRC_AIRBASE, 1))
    f35 = gs.spawn_token(Side.US, TokenType.F_35A, band,
                         TokenOrigin.SQUADRON_CARD, source_card_id=1)
    eng._d4 = lambda: 4
    eng.acquire(Side.US, f35.uid, ada.uid)
    assert any(a.kind == "shoot_surface" and a.target_uid == ada.uid
               for a in eng.legal_actions(Side.US))            # surface, not air
    r = eng.shoot_surface(Side.US, f35.uid, target_uid=ada.uid)
    assert r.hit and gs.get_token(ada.uid) is None
    assert any(c.token_type == ada_type for c in gs.us.captures)

    # An air-only F-22 has no surface attack and cannot target the ADA at all.
    gs2, eng2 = _mid_turn(Side.US)
    gs2.prc.squadrons[56] = SquadronState(56, Side.PRC, activated=True,
                                          location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    ada2 = gs2.spawn_token(Side.PRC, ada_type, BandID.PRC_AIRBASE,
                           TokenOrigin.SQUADRON_CARD, source_card_id=56)
    f22 = gs2.spawn_token(Side.US, TokenType.F_22, band,
                          TokenOrigin.SQUADRON_CARD, source_card_id=2)
    eng2._d4 = lambda: 4
    eng2.acquire(Side.US, f22.uid, ada2.uid)
    assert not any(a.target_uid == ada2.uid and a.kind in ("shoot_air", "shoot_surface")
                   for a in eng2.legal_actions(Side.US))
    with pytest.raises(IllegalAction):
        eng2.shoot_surface(Side.US, f22.uid, target_uid=ada2.uid)


def test_air_to_air_missile_defense_applies_disadvantage():
    # (FAQ 2026-07-24) An air-to-air attack crossing an enemy ADA's WEZ is rolled
    # at disadvantage — enemy ADA coverage is automatic, no declaration needed.
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.squadrons[59] = SquadronState(59, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    f22 = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_D,
                         TokenOrigin.SQUADRON_CARD, source_card_id=5)
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_E,
                         TokenOrigin.SQUADRON_CARD, source_card_id=60)
    gs.spawn_token(Side.PRC, TokenType.LONG_RANGE_ADA_PRC, BandID.PRC_AIRBASE,
                   TokenOrigin.SQUADRON_CARD, source_card_id=59)   # WEZ 3 covers BAND_E
    j10.acquired = True
    eng._d4 = lambda: 4
    r = eng.shoot_air(Side.US, f22.uid, j10.uid)
    assert r.hit_roll.mode == RollMode.DISADVANTAGE
    assert r.hit                                        # a 4 at disadvantage still hits


def test_naval_md_against_air_shot_must_be_declared_and_spends_a_salvo():
    # (FAQ 2026-07-24) A naval missile-defense ship may be DECLARED against an
    # air-to-air shot crossing its WEZ; declaring spends one air salvo and rolls
    # the attacker's hit at disadvantage.
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    f22 = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=5)
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D,
                         TokenOrigin.SQUADRON_CARD, source_card_id=60)
    ship = gs.spawn_token(Side.PRC, TokenType.NANNING_162, BandID.BAND_E,
                          TokenOrigin.ENABLER_CARD, source_card_id=87)  # WEZ 3 covers BAND_D
    j10.acquired = True
    salvos = ship.air_salvos_remaining
    assert eng.eligible_missile_defenders(Side.PRC, BandID.BAND_C, Side.US, BandID.BAND_D)
    eng._d4 = lambda: 4
    r = eng.shoot_air(Side.US, f22.uid, j10.uid, missile_defense_uid=ship.uid)
    assert r.hit_roll.mode == RollMode.DISADVANTAGE
    assert ship.air_salvos_remaining == salvos - 1      # one air salvo spent


def _strike_infantry(points: int, start_damage: int = 0):
    """One base attack allocating `points` onto a US Infantry Battalion."""
    gs, eng = _mid_turn(Side.PRC)
    gs.prc.squadrons[61] = SquadronState(61, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    h6 = gs.spawn_token(Side.PRC, TokenType.H_6K, BandID.PRC_STANDOFF,
                        TokenOrigin.SQUADRON_CARD, source_card_id=61)
    gs.us.infantry_battalions[BandID.US_AIRBASE] = start_damage
    eng._d4 = lambda: 3
    r = eng.shoot_surface(Side.PRC, h6.uid, target_band=BandID.US_AIRBASE,
                          damage_allocator=lambda amt, tg: [("infantry", None, points)])
    return gs, eng, r


def test_base_attack_can_destroy_infantry_battalion():
    # Card 40: "This card may be a target of a base attack" — and it has TWO
    # printed damage boxes, so one hit only wounds it (user ruling 2026-07-17).
    gs, eng, r = _strike_infantry(1)
    assert r.hit and not r.infantry_destroyed
    assert gs.us.infantry_battalions[BandID.US_AIRBASE] == 1     # survives, wounded

    gs, eng, r = _strike_infantry(2)
    assert r.hit and r.infantry_destroyed
    assert BandID.US_AIRBASE not in gs.us.infantry_battalions    # both boxes filled

    # A single point finishes an already-wounded card.
    gs, eng, r = _strike_infantry(1, start_damage=1)
    assert r.infantry_destroyed
    assert BandID.US_AIRBASE not in gs.us.infantry_battalions


def test_cancel_restores_destroyed_infantry_battalion():
    gs, eng = _mid_turn(Side.PRC)
    gs.prc.squadrons[61] = SquadronState(61, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    h6 = gs.spawn_token(Side.PRC, TokenType.H_6K, BandID.PRC_STANDOFF,
                        TokenOrigin.SQUADRON_CARD, source_card_id=61)
    gs.us.infantry_battalions[BandID.US_AIRBASE] = 1     # one box already filled
    eng._d4 = lambda: 3
    eng.shoot_surface(Side.PRC, h6.uid, target_band=BandID.US_AIRBASE,
                      damage_allocator=lambda amt, tg: [("infantry", None, 1)])
    assert BandID.US_AIRBASE not in gs.us.infantry_battalions   # second box: dead
    assert eng._cancel_last_attack(Side.US)
    # Cancelling revives the card with the damage it had BEFORE the strike.
    assert gs.us.infantry_battalions[BandID.US_AIRBASE] == 1


def test_cl_attack_limited_to_one_squadron_and_its_assets():
    # "only one Squadron Card (and its assets) may be targeted per attack."
    gs, eng = _mid_turn(Side.PRC)
    eng._d4 = lambda: 4
    gs.prc.squadrons[61] = SquadronState(61, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True,
                                       location=BandID.US_CONTINGENCY_LOCATION, zone=CardZone.ACTIVE)
    gs.us.squadrons[8] = SquadronState(8, Side.US, activated=True,
                                       location=BandID.US_CONTINGENCY_LOCATION, zone=CardZone.ACTIVE)
    other = gs.spawn_token(Side.US, TokenType.F_35A, BandID.US_CONTINGENCY_LOCATION,
                           TokenOrigin.SQUADRON_CARD, source_card_id=8, grounded=True)
    h6 = gs.spawn_token(Side.PRC, TokenType.H_6K, BandID.PRC_STANDOFF,
                        TokenOrigin.SQUADRON_CARD, source_card_id=61)
    # Try to hit squadron 5 AND squadron 8's grounded token: only 5 may be hit.
    eng.shoot_surface(Side.PRC, h6.uid, target_band=BandID.US_CONTINGENCY_LOCATION,
                      damage_allocator=lambda amt, tg: [("squadron", 5, 2),
                                                        ("token", other.uid, 1)])
    assert gs.us.squadrons[5].is_destroyed
    assert gs.get_token(other.uid) is not None        # other squadron's asset untouched


def test_standoff_surface_attack_damages_squadron_card():
    # Walkthrough turns 8/10: J-15 ground-attacks the B-52 in the standoff —
    # 1 damage point on the squadron card, second hit destroys card and token.
    gs, eng = _mid_turn(Side.PRC)
    gs.us.squadrons[7] = SquadronState(7, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    b52 = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_STANDOFF,
                         TokenOrigin.SQUADRON_CARD, source_card_id=7)
    b52.acquired = True
    j15 = gs.spawn_token(Side.PRC, TokenType.J_15, BandID.BAND_A,
                         TokenOrigin.ENABLER_CARD, source_card_id=85)
    eng._d4 = lambda: 3
    r = eng.shoot_surface(Side.PRC, j15.uid, target_uid=b52.uid)
    assert r.hit and r.damage == 1                    # J-15: no exploding die
    assert gs.us.squadrons[7].damage == 1
    assert gs.get_token(b52.uid) is not None          # token survives the first hit
    assert r.attacker_winchester                      # rolled 3 (< 4)

    gs.prc.reset_turn()
    j15b = gs.spawn_token(Side.PRC, TokenType.J_15, BandID.BAND_A,
                          TokenOrigin.ENABLER_CARD, source_card_id=85)
    r2 = eng.shoot_surface(Side.PRC, j15b.uid, target_uid=b52.uid)
    assert gs.us.squadrons[7].is_destroyed            # second point destroys the card
    assert gs.get_token(b52.uid) is None              # ...and its aircraft in the container
    assert 7 in r2.destroyed_squadron_ids and b52.uid in r2.destroyed_token_uids


def test_standoff_attack_requires_acquisition():
    gs, eng = _mid_turn(Side.PRC)
    gs.us.squadrons[7] = SquadronState(7, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    b52 = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_STANDOFF,
                         TokenOrigin.SQUADRON_CARD, source_card_id=7)
    j15 = gs.spawn_token(Side.PRC, TokenType.J_15, BandID.BAND_A,
                         TokenOrigin.ENABLER_CARD, source_card_id=85)
    with pytest.raises(IllegalAction):
        eng.shoot_surface(Side.PRC, j15.uid, target_uid=b52.uid)


def test_surge_bans_cl_for_the_rest_of_the_campaign():
    # Card 46: "Contingency Locations cannot be used during this campaign."
    eng = RulesEngine(GameState.new_game(campaign=3), rng=random.Random(0))
    eng.setup_missions(51, 105)
    eng.select_posture(Side.US, 46, draft_squadrons(Side.US, (10,), n=6),
                       draft_enablers(Side.US, n=7))   # SURGE in ATO 1
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, (60,)), draft_enablers(Side.PRC))
    eng.bid_for_initiative(first_player=Side.US)
    eng.play_intel()
    eng.begin_player_turns()
    eng.pass_turn(Side.US)
    eng.pass_turn(eng.state.active_side)
    assert eng.state.ato_cycle == 2
    eng.select_posture_only(Side.US, 49)               # roster redeploys...
    assert eng.state.us.cl_banned_campaign             # ...with the ban still live
    assert eng.state.us.squadrons[10].location == BandID.US_AIRBASE   # never at a CL


# --- manual-testing bug fixes ---------------------------------------------------------

def test_mas_actions_any_order_once_each():
    # Move, Acquire and Shoot may be taken in ANY order within one turn, each at
    # most once (user ruling 2026-07-31, reverting the 2026-07-13 forward-order
    # ruling to the Player Guide's "Actions may be in any order"). Here the
    # player shoots, THEN acquires, THEN moves — all legal.
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    f22 = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=5)
    j10a = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_C,
                          TokenOrigin.SQUADRON_CARD, source_card_id=60)
    j10b = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_C,
                          TokenOrigin.SQUADRON_CARD, source_card_id=60)
    j10a.acquired = True
    eng._d4 = lambda: 4                                  # hit + no Winchester

    eng.shoot_air(Side.US, f22.uid, j10a.uid)           # shoot FIRST
    result = eng.acquire(Side.US, f22.uid, j10b.uid)    # acquire after shoot: now legal
    assert result.success
    eng.move(Side.US, f22.uid, BandID.BAND_D)           # move after acquire+shoot: now legal

    # ...but each action only once.
    assert not any(a.kind in ("move", "acquire", "shoot_air")
                   for a in eng.legal_actions(Side.US))
    with pytest.raises(IllegalAction):
        eng.move(Side.US, f22.uid, BandID.BAND_C)
    with pytest.raises(IllegalAction):
        eng.acquire(Side.US, f22.uid, j10b.uid)
    with pytest.raises(IllegalAction):
        eng.shoot_air(Side.US, f22.uid, j10b.uid)


def test_mas_actions_survive_enabler_play_in_between():
    # An Enabler Card played mid-turn does not consume the remaining MAS actions:
    # after shooting, the player may still move (any order, user ruling 2026-07-31).
    from afwip.core.cards import ENABLER_REGISTRY
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    f22 = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=5)
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=60)
    j10.acquired = True
    eng._d4 = lambda: 4

    eng.shoot_air(Side.US, f22.uid, j10.uid)            # shoot first
    # Play a token-generating enabler (always applicable with default params).
    cid = next(c for c, p in ENABLER_REGISTRY.items()
               if p.side == Side.US and p.generates_token is not None and p.is_not_response)
    gs.us.enablers[cid] = EnablerCardState(cid, Side.US, zone=CardZone.SELECTED)
    eng.play_enabler(Side.US, cid, eng._default_enabler_play(Side.US, cid))
    eng.move(Side.US, f22.uid, BandID.BAND_D)           # move after shoot: still legal
    with pytest.raises(IllegalAction):                  # each action only once
        eng.shoot_air(Side.US, f22.uid, j10.uid)


def test_enabler_origin_kills_score_captures():
    # Shooting down a token generated by an Enabler Card (e.g. the Shandong's
    # J-15s) scores like any other kill — Attrition awards its VP (user
    # ruling 2026-07-13; previously enabler-origin tokens did not score).
    gs, eng = _mid_turn(Side.US)
    j15 = gs.spawn_token(Side.PRC, TokenType.J_15, BandID.BAND_C,
                         TokenOrigin.ENABLER_CARD, source_card_id=85)
    gs.us.mission_card_id = 51                          # US Attrition
    rec = gs.destroy_token(j15.uid, destroyed_by=Side.US)
    assert rec is not None and len(gs.us.captures) == 1
    assert eng.score_captures(Side.US) == 1             # fighter kill: +1 Attrition VP


def test_token_losses_persist_across_atos():
    # FAQ 2026-07-24 (reverses the 2026-07-22 reset): destroyed tokens stay
    # destroyed and scored for the opponent; only surviving tokens return to the
    # card, so a surviving squadron re-fields with FEWER tokens next ATO. Only a
    # specific enabler (e.g. Rapid Resupply) can bring lost tokens back.
    eng = _setup(Side.US, campaign=2)                   # squadron 10: 4x F-16C
    toks = eng.activate_squadron(Side.US, 10)           # ends the US turn
    assert len(toks) == 4
    eng.state.destroy_token(toks[0].uid, destroyed_by=Side.PRC)
    eng.state.destroy_token(toks[1].uid, destroyed_by=Side.PRC)
    assert eng.state.us.squadrons[10].tokens_lost == 2
    prc_captures = len(eng.state.prc.captures)
    assert prc_captures == 2                            # two kills scored this ATO
    eng.pass_turn(Side.PRC)
    eng.pass_turn(Side.US)                              # double pass ends ATO 1
    assert eng.state.ato_cycle == 2
    assert eng.state.us.squadrons[10].tokens_lost == 2  # losses PERSIST across cleanup

    eng.select_posture_only(Side.US, 49)
    eng.select_posture_only(Side.PRC, 103)
    eng.bid_for_initiative(first_player=Side.US)
    eng.play_intel()
    eng.begin_player_turns()
    toks2 = eng.activate_squadron(Side.US, 10)
    assert len(toks2) == 2                              # FEWER tokens: 4 total - 2 lost
    assert all(not t.is_winchester for t in toks2)
    assert len(eng.state.prc.captures) == prc_captures  # ATO-1 kills stay scored


def test_destroyed_squadron_never_returns_next_ato():
    # Ruling 2026-07-22: destroying a squadron CARD is permanent — unlike token
    # losses (which reset), its tokens never come back and it cannot be
    # re-drafted; the points scored for it persist.
    eng = _setup(Side.US, campaign=2)                   # US squadron 10
    eng.activate_squadron(Side.US, 10)
    eng.state.destroy_squadron(Side.US, 10, destroyed_by=Side.PRC)
    assert eng.state.us.squadrons[10].is_destroyed
    assert eng.state.prc.captures                        # card + tokens scored
    eng.pass_turn(Side.PRC)
    eng.pass_turn(Side.US)
    assert eng.state.ato_cycle == 2
    eng.select_posture_only(Side.US, 49)                 # won't field a destroyed card
    eng.select_posture_only(Side.PRC, 103)
    assert eng.state.us.squadrons[10].zone == CardZone.DESTROYED
    eng.bid_for_initiative(first_player=Side.US)
    eng.play_intel()
    eng.begin_player_turns()
    prc_caps = len(eng.state.prc.captures)               # scoring persisted into ATO 2
    assert prc_caps
    with pytest.raises(IllegalAction):
        eng.activate_squadron(Side.US, 10)               # destroyed: cannot generate tokens
    assert len(eng.state.prc.captures) == prc_caps       # scoring unchanged


def test_set_aside_squadron_is_off_board_for_base_strikes():
    # Ruling 2026-07-22: a squadron fielded in an earlier ATO but NOT selected
    # this cycle (set aside — zone DECK) is off the board. A base strike cannot
    # damage it, even though it keeps its old location and card damage.
    eng = _setup(Side.PRC, us_sq=(10, 5), campaign=3)     # US 10 & 5 fielded at airbase
    s10 = eng.state.us.squadrons[10]
    s10.zone = CardZone.DECK                              # set aside this cycle
    s10.location = BandID.US_AIRBASE                       # stale location retained
    s10.damage = 0
    targets = eng._base_allocation_targets(Side.US, BandID.US_AIRBASE)
    squad_ids = {ref for kind, ref in targets if kind == "squadron"}
    assert 10 not in squad_ids                            # off the board — not a target
    assert 5 in squad_ids                                 # a fielded card is targetable
    eng._strike_base(Side.PRC, BandID.US_AIRBASE, roll_gate=None, bypass_md=True,
                     fixed_damage=1, target_squadron_id=10)
    assert s10.damage == 0                                # took no damage


def test_cancelled_kill_refunds_the_token_loss():
    # A response that cancels the hit revives the token AND refunds the
    # squadron's permanent-loss counter.
    gs, eng = _mid_turn(Side.PRC)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=60)
    f22 = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=5)
    f22.acquired = True
    gs.us.enablers[29] = EnablerCardState(29, Side.US, zone=CardZone.SELECTED)
    eng._d4 = lambda: 4
    eng.shoot_air(Side.PRC, j10.uid, f22.uid)
    assert gs.us.squadrons[5].tokens_lost == 1
    eng.play_enabler(Side.US, 29, EnablerPlay(choice="cancel_hit"), response=True)
    assert gs.us.squadrons[5].tokens_lost == 0          # loss refunded


def test_token_moved_back_to_base_is_done_for_the_ato():
    # Landing rule: a token that moves back to its base grounds on its card
    # and cannot act again this ATO — but it is NOT a loss, so the squadron
    # returns at full strength next cycle.
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    f16 = gs.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_A,
                         TokenOrigin.SQUADRON_CARD, source_card_id=10)
    eng.move(Side.US, f16.uid, BandID.US_AIRBASE)
    assert f16.grounded and f16.uid in gs.us.squadrons[10].grounded_token_uids
    assert gs.us.squadrons[10].tokens_lost == 0
    eng.end_turn(Side.US)
    eng.pass_turn(Side.PRC)
    with pytest.raises(IllegalAction):                  # grounded: no more actions
        eng.move(Side.US, f16.uid, BandID.BAND_A)
    assert not any(a.token_uid == f16.uid for a in eng.legal_actions(Side.US)
                   if a.kind in ("move", "acquire", "shoot_air", "shoot_surface"))


def test_orphaned_airborne_token_surrendered_at_ato_end():
    # An orphaned airborne token keeps flying (ruling 2026-07-17) but any that
    # never went Winchester are turned over to the opponent at end of ATO —
    # "all associated tokens are considered destroyed by the end of the ATO."
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True, damage=2,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    f16 = gs.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_A,
                         TokenOrigin.SQUADRON_CARD, source_card_id=10)
    assert any(a.token_uid == f16.uid for a in eng.legal_actions(Side.US)
               if a.kind in ("move", "acquire", "shoot_air", "shoot_surface"))  # still acts
    eng.end_ato_cycle()                                 # never Winchester: reaped at ATO end
    assert f16.destroyed
    assert any(not c.is_squadron_card for c in gs.prc.captures)   # enemy scores it


def test_response_card_does_not_transfer_turn():
    # An opponent's mid-turn response (here: Air Launched Decoy cancelling a
    # rolled hit) never transfers the turn — the actor resumes exactly where
    # they left off, with their MAS flags and legal actions intact.
    gs, eng = _mid_turn(Side.PRC)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=60)
    f22 = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=5)
    f22.acquired = True
    gs.us.enablers[29] = EnablerCardState(29, Side.US, zone=CardZone.SELECTED)
    eng._d4 = lambda: 4

    r = eng.shoot_air(Side.PRC, j10.uid, f22.uid)
    assert r.hit and f22.uid not in gs.us.tokens

    eng.play_enabler(Side.US, 29, EnablerPlay(choice="cancel_hit"), response=True)
    assert f22.uid in gs.us.tokens                       # hit cancelled, token back

    # PRC's turn resumed where it left off.
    assert eng.state.active_side == Side.PRC
    assert eng.state.turn_number == 1
    assert gs.prc.has_shot and not gs.prc.has_moved
    assert gs.prc.acted_this_turn                        # not converted to a pass
    assert any(a.kind == "pass" for a in eng.legal_actions(Side.PRC))
    eng.end_turn(Side.PRC)                               # normal hand-off afterwards
    assert eng.state.active_side == Side.US


def test_activation_and_mas_are_mutually_exclusive():
    # "Do one or the other": a squadron may not be activated in a turn where
    # any Move-Acquire-Shoot action was taken (and activation ends the turn,
    # so MAS-after-activation is impossible by construction).
    eng = _setup(Side.US, us_sq=(10, 5))
    f16 = eng.state.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_A,
                                TokenOrigin.SQUADRON_CARD, source_card_id=10)
    eng.move(Side.US, f16.uid, BandID.BAND_B)
    with pytest.raises(IllegalAction):
        eng.activate_squadron(Side.US, 5)
    assert not any(a.kind == "activate" for a in eng.legal_actions(Side.US))
    # Activation on a fresh turn ends it immediately (no MAS afterwards).
    eng.end_turn(Side.US)
    eng.pass_turn(Side.PRC)
    eng.activate_squadron(Side.US, 5)
    assert eng.state.active_side == Side.PRC


def test_play_intel_owner_chooses_which_cards_to_show():
    gs, eng = _mid_turn()
    gs.us.enablers[21] = EnablerCardState(21, Side.US, zone=CardZone.SELECTED)
    gs.us.enablers[31] = EnablerCardState(31, Side.US, zone=CardZone.SELECTED)
    seen = eng.play_intel(reveal_selectors={Side.US: lambda ids, n: [31]})
    assert seen[Side.PRC] == 1                          # 2 in hand, 1 always hidden
    assert gs.us.enablers[31].revealed_to_opponent
    assert not gs.us.enablers[21].revealed_to_opponent


def test_squadron_count_may_go_one_below_the_posture():
    # User ruling 2026-07-31 (reverts the 2026-07-13 exact ruling): you may field
    # ONE BELOW the posture's squadron count. Standard (49) allots 4, so 3 is
    # legal but 2 (two below, with a deep pool) is not; the full 4 is fine too.
    eng = RulesEngine(GameState.new_game(campaign=2), rng=random.Random(0))
    eng.setup_missions(51, 105)
    full = draft_squadrons(Side.US, camp=eng.campaign)   # a legal 4-squadron draft
    with pytest.raises(IllegalAction):                   # 2 < 3 (one below 4), pool deep
        eng.select_posture(Side.US, 49, full[:2], draft_enablers(Side.US))
    eng.select_posture(Side.US, 49, full[:3], draft_enablers(Side.US))    # one below (3): OK
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC), draft_enablers(Side.PRC))  # full: OK


def test_squadron_count_falls_back_to_all_when_pool_is_short():
    # If you can't reach one-below the posture count, you field ALL that remain
    # (2026-07-31). With all but two PRC squadrons destroyed (pool 2 < 3), two is
    # legal and one is not.
    eng = RulesEngine(GameState.new_game(campaign=2), rng=random.Random(0))
    eng.setup_missions(51, 105)
    survivors = draft_squadrons(Side.PRC, n=2)
    for cid, p in SQUADRON_REGISTRY.items():
        if p.side == Side.PRC and cid not in survivors:
            eng.state.prc.squadrons[cid] = SquadronState(
                cid, Side.PRC, zone=CardZone.DESTROYED, damage=2)
    with pytest.raises(IllegalAction):                   # 1 < all-remaining (2)
        eng.select_posture(Side.PRC, 103, survivors[:1], draft_enablers(Side.PRC))
    eng.select_posture(Side.PRC, 103, survivors, draft_enablers(Side.PRC))   # all remaining: OK


def test_enabler_count_is_exact_not_a_maximum():
    eng = RulesEngine(GameState.new_game(campaign=3), rng=random.Random(0))
    eng.setup_missions(51, 105)
    with pytest.raises(IllegalAction):                  # 2 < the Standard posture's 6
        eng.select_posture(Side.US, 49, [10], [21, 31])
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (10,)), draft_enablers(Side.US))   # exactly 6: OK


def test_personnel_recovery_after_enabler_kill():
    # PRC Cyber Counter-UAS destroys a US UAS; Personnel Recovery ("play
    # immediately after a US aircraft is lost") recovers it to US band 1.
    eng = _setup(Side.PRC, prc_en=(84,), us_en=(12,))
    eng.state.us.squadrons[1] = SquadronState(1, Side.US, activated=True,
                                              location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    uas = eng.state.spawn_token(Side.US, TokenType.ATTACK_UAS_US, BandID.BAND_B,
                                TokenOrigin.SQUADRON_CARD, source_card_id=1)
    res = eng.play_enabler(Side.PRC, 84)
    assert res.destroyed == [uas.uid] and eng.state.get_token(uas.uid) is None
    rec = eng.play_enabler(Side.US, 12, response=True)
    assert rec.recovered == [uas.uid]
    revived = eng.state.get_token(uas.uid)
    assert revived is not None and revived.location == BandID.BAND_A
    assert len(eng.state.prc.captures) == 0             # does not count as destroyed


# --- scoring -----------------------------------------------------------------------

def test_nk_dominance_counts_us_sof_cards():
    gs, eng = _mid_turn(campaign=3)
    gs.us.mission_card_id = 53                          # N-K Dominance
    gs.us.enablers_played_log = [14]                    # SOF Reconnaissance (AIR_FORCE class)
    eng._score_end_of_ato(Side.US)
    assert gs.us.victory_points == 3 * gs.us.cyber_rate + 1


def test_three_dominances_counts_naval_air_enabler():
    gs, eng = _mid_turn(campaign=3)
    gs.prc.mission_card_id = 107                        # Three Dominances
    gs.prc.enablers_played_log = [85]                   # Shandong J-15 (NAVAL_AIR)
    eng._score_end_of_ato(Side.PRC)
    assert gs.prc.victory_points == 2 * gs.prc.cyber_rate + 1


def test_three_dominances_naval_units_and_intact_squadrons():
    # +3 per naval unit on the board includes the Shandong J-15, not just
    # surface combatants; intact = fielded this ATO with no destroyed tokens, so
    # a set-aside (DECK) or token-losing squadron does not count (2026-07-22).
    from afwip.core.constants import TokenType, TokenOrigin
    eng = RulesEngine(GameState.new_game(campaign=3))
    eng.setup_missions(51, 107)
    eng.state.prc.cyber_rate = 0                        # isolate the naval + intact terms
    eng.state.spawn_token(Side.PRC, TokenType.NANNING_162, BandID.BAND_C, TokenOrigin.ENABLER_CARD)  # surface
    eng.state.spawn_token(Side.PRC, TokenType.J_15, BandID.BAND_C, TokenOrigin.ENABLER_CARD)         # carrier air
    eng.state.prc.squadrons = {
        60: SquadronState(60, Side.PRC, zone=CardZone.SELECTED, tokens_lost=0),                 # intact
        63: SquadronState(63, Side.PRC, zone=CardZone.ACTIVE, activated=True, tokens_lost=0),   # intact
        64: SquadronState(64, Side.PRC, zone=CardZone.ACTIVE, activated=True, tokens_lost=1),   # lost a token
        55: SquadronState(55, Side.PRC, zone=CardZone.DECK, tokens_lost=0),                     # set aside
    }
    assert sorted(s.card_id for s in eng.state.prc.intact_squadrons()) == [60, 63]
    eng._score_end_of_ato(Side.PRC)
    assert eng.state.prc.victory_points == 6 + 2        # 2 naval units *3 + 2 intact squadrons *1


def test_campaign5_intact_bonus_is_awarded_once_at_end_of_campaign():
    eng = RulesEngine(GameState.new_game(campaign=5))
    eng.setup_missions(51, 105)
    # US legal squadrons under Campaign 5: no F-22/F-35A, no B-52s -> 6 of 10;
    # counts undrafted cards too.
    assert eng._intact_squadron_count(Side.US) == 6
    eng.state.us.squadrons[10] = SquadronState(10, Side.US, zone=CardZone.DESTROYED)
    assert eng._intact_squadron_count(Side.US) == 5
    # The bonus must NOT inflate the running total mid-campaign — it is awarded
    # once, at end of campaign (a distinct, visible end-of-game accrual).
    assert eng.total_victory_points(Side.US) == 0        # nothing scored yet
    eng.state.ato_cycle = eng.state.total_ato_cycles     # final ATO
    eng._finalize_game()
    assert eng.total_victory_points(Side.US) == 5        # +5 intact awarded at end
    assert (eng.state.total_ato_cycles, "intact Squadron Cards (Campaign 5)", 5) \
        in eng.state.us.vp_log


def test_economy_of_force_counts_only_fielded_units():
    # Only DRAFTED units fielded this ATO score (+2 each): a squadron ON THE
    # BOARD (SELECTED) that was not activated, and an unplayed token-deploying
    # Enabler Card still in hand. A set-aside squadron (DECK), an activated
    # squadron, a non-unit enabler, and a played enabler all score nothing
    # (user ruling 2026-07-22). Scored per ATO, keyed on mission type (so US 50
    # and PRC 104 behave identically).
    eng = RulesEngine(GameState.new_game(campaign=3))
    eng.setup_missions(50, 104)
    eng.state.us.squadrons = {
        10: SquadronState(10, Side.US, zone=CardZone.SELECTED, activated=False),  # fielded, idle -> +2
        5:  SquadronState(5,  Side.US, zone=CardZone.ACTIVE,   activated=True),    # activated -> 0
        1:  SquadronState(1,  Side.US, zone=CardZone.DECK,     activated=False),   # set aside -> 0
    }
    eng.state.us.enablers = {
        36: EnablerCardState(36, Side.US, zone=CardZone.SELECTED),   # deploys ADA, in hand -> +2
        13: EnablerCardState(13, Side.US, zone=CardZone.SELECTED),   # no token deployed -> 0
        37: EnablerCardState(37, Side.US, zone=CardZone.PLAYED),     # deploys a DDG but played -> 0
    }
    eng._score_end_of_ato(Side.US)
    assert eng.state.us.victory_points == 4          # squad 10 (+2) + enabler 36 (+2)


def test_squadron_killed_by_damage_scores_card_and_full_complement():
    # Destroying a squadron via accumulated damage removes the card AND scores
    # its WHOLE complement (ruling 2026-07-17): the 2 grounded J-10s on the
    # card PLUS the 2 that never generated (124th AIR BRIGADE fields 4). Under
    # Attrition that is +2 card and +1 per J-10 = +6. Regression: the old
    # destroy_squadron guard keyed on is_destroyed (damage-based), which the
    # damage paths had already made true — so the card capture was skipped.
    gs, eng = _mid_turn(Side.US, campaign=2)
    gs.us.mission_card_id, gs.prc.mission_card_id = 51, 105     # Attrition
    full = TOKEN_REGISTRY[SQUADRON_REGISTRY[60].token_type].token_count  # 4
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True, damage=1,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    on_card = [gs.spawn_token(Side.PRC, TokenType.J_10, BandID.PRC_AIRBASE,
                              TokenOrigin.SQUADRON_CARD, source_card_id=60,
                              grounded=True) for _ in range(2)]
    gs.us.squadrons[7] = SquadronState(7, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    b52 = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_STANDOFF,
                         TokenOrigin.SQUADRON_CARD, source_card_id=7)
    eng._d4 = lambda: 4

    r = eng.shoot_surface(Side.US, b52.uid, target_band=BandID.PRC_AIRBASE,
                          target_squadron_id=60)
    assert 60 in r.destroyed_squadron_ids
    assert gs.prc.squadrons[60].zone == CardZone.DESTROYED     # card off the board
    assert all(gs.get_token(t.uid) is None for t in on_card)   # its tokens too
    assert sum(1 for c in gs.us.captures if c.is_squadron_card) == 1
    assert sum(1 for c in gs.us.captures if not c.is_squadron_card) == full  # 2 on-card + 2 ungenerated
    assert eng.score_captures(Side.US) == 2 + full            # +2 card, +1 per J-10


# --- rules clarifications (user, 2026-07-14) -----------------------------------

def test_ground_attack_targets_cards_not_grounded_tokens():
    # Ground attacks hit Squadron CARDS; grounded flight tokens are not
    # separately targetable (they die with their card), and (FAQ 2026-07-24) ADA
    # is excluded too — it must be acquired and shot. Only VP boxes remain.
    gs, eng = _mid_turn(Side.US)
    prc_base = BandID.PRC_AIRBASE
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=prc_base, zone=CardZone.ACTIVE)
    grounded = gs.spawn_token(Side.PRC, TokenType.J_10, prc_base,
                              TokenOrigin.SQUADRON_CARD, source_card_id=60,
                              grounded=True)
    ada = gs.spawn_token(Side.PRC, TokenType.MID_RANGE_ADA_PRC, prc_base,
                         TokenOrigin.ENABLER_CARD, source_card_id=None)
    targets = eng._base_allocation_targets(Side.PRC, prc_base)
    assert ("squadron", 60) in targets
    assert ("token", ada.uid) not in targets           # ADA: acquire + shoot only
    assert ("token", grounded.uid) not in targets      # grounded flight: not
    assert ("vp", None) in targets


def test_face_down_card_targetable_without_acquisition():
    # A never-activated (face-down) Squadron Card at a base can be ground
    # attacked with no acquisition step anywhere — identity stays hidden but
    # the hits land.
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[7] = SquadronState(7, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    b52 = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_STANDOFF,
                         TokenOrigin.SQUADRON_CARD, source_card_id=7)
    gs.prc.squadrons[62] = SquadronState(62, Side.PRC, activated=False,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.SELECTED)
    eng._d4 = lambda: 4
    r = eng.shoot_surface(Side.US, b52.uid, target_band=BandID.PRC_AIRBASE,
                          target_squadron_id=62)
    assert r.hit and gs.prc.squadrons[62].is_destroyed
    assert not gs.prc.squadrons[62].ever_activated     # died face-down


def test_cl_strike_has_no_spillover():
    # At a Contingency Location only the first-targeted entry takes hits —
    # excess damage does NOT spill to other Squadron Cards there.
    gs, eng = _mid_turn(Side.PRC)
    cl = BandID.US_CONTINGENCY_LOCATION
    gs.us.squadrons[10] = SquadronState(10, Side.US, location=cl, zone=CardZone.SELECTED)
    gs.us.squadrons[5] = SquadronState(5, Side.US, location=cl, zone=CardZone.SELECTED)
    from afwip.core.rules import ShootResult, RollContext, _AttackUndo
    result = ShootResult(attacker_uid=-1, context=RollContext.BASE_ATTACK,
                         hit_roll=None, hit=True, damage=4)
    eng._apply_base_damage(Side.US, cl, 4, Side.PRC, None, result,
                           _AttackUndo(attacker_side=Side.PRC),
                           allocation=[("squadron", 10, 2), ("squadron", 5, 2)])
    assert gs.us.squadrons[10].is_destroyed            # first target absorbs
    assert gs.us.squadrons[5].damage == 0              # no spillover at a CL
    assert not gs.us.squadrons[5].is_destroyed


def test_contingency_location_has_no_vp_damage_track():
    # (FAQ 2026-07-24) Only the main airbase has the three VP damage boxes; a
    # Contingency Location has NO independent infrastructure-damage track, so a
    # strike there offers no VP target and scores no base-damage boxes.
    from afwip.core.rules import ShootResult, RollContext, _AttackUndo
    gs, eng = _mid_turn(Side.PRC)
    cl = BandID.US_CONTINGENCY_LOCATION
    gs.us.squadrons[10] = SquadronState(10, Side.US, location=cl, zone=CardZone.SELECTED)
    assert ("vp", None) not in eng._base_allocation_targets(Side.US, cl)
    result = ShootResult(attacker_uid=-1, context=RollContext.BASE_ATTACK,
                         hit_roll=None, hit=True, damage=3)
    eng._apply_base_damage(Side.US, cl, 3, Side.PRC, None, result,
                           _AttackUndo(attacker_side=Side.PRC), allocation=[("vp", None, 3)])
    assert gs.us.airbase_vp_damage == 0                # no VP damage track at a CL
    assert result.base_vp_damage == 0


def test_airbase_vp_boxes_cap_at_three_and_base_keeps_functioning():
    # (FAQ 2026-07-24) The airbase's three damage boxes are each a one-time VP
    # target; once all three are filled, further attacks score no additional
    # base-damage boxes (and the airbase keeps functioning — no basing loss).
    from afwip.core.rules import ShootResult, RollContext, _AttackUndo
    gs, eng = _mid_turn(Side.PRC)
    ab = BandID.US_AIRBASE
    r1 = ShootResult(attacker_uid=-1, context=RollContext.BASE_ATTACK,
                     hit_roll=None, hit=True, damage=4)
    eng._apply_base_damage(Side.US, ab, 4, Side.PRC, None, r1,
                           _AttackUndo(attacker_side=Side.PRC), allocation=[("vp", None, 4)])
    assert gs.us.airbase_vp_damage == 3 and r1.base_vp_damage == 3   # 4th point is lost
    r2 = ShootResult(attacker_uid=-1, context=RollContext.BASE_ATTACK,
                     hit_roll=None, hit=True, damage=2)
    eng._apply_base_damage(Side.US, ab, 2, Side.PRC, None, r2,
                           _AttackUndo(attacker_side=Side.PRC), allocation=[("vp", None, 2)])
    assert gs.us.airbase_vp_damage == 3 and r2.base_vp_damage == 0   # no further boxes
    # The base still functions: a squadron may still be deployed there.
    gs.us.squadrons[10] = SquadronState(10, Side.US, location=ab, zone=CardZone.SELECTED)
    assert ("squadron", 10) in eng._base_allocation_targets(Side.US, ab)


def test_base_damage_stays_local_between_airbase_and_cl():
    # (FAQ 2026-07-24) Squadron cards ARE part of the airbase site for targeting,
    # but damage does not transfer between the Airbase and the Contingency
    # Location — each strike is confined to the site it targets.
    gs, eng = _mid_turn(Side.PRC)
    gs.us.squadrons[7] = SquadronState(7, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True,
                                       location=BandID.US_CONTINGENCY_LOCATION, zone=CardZone.ACTIVE)
    ab = eng._base_allocation_targets(Side.US, BandID.US_AIRBASE)
    cl = eng._base_allocation_targets(Side.US, BandID.US_CONTINGENCY_LOCATION)
    assert ("squadron", 7) in ab and ("squadron", 5) not in ab   # airbase strike: airbase only
    assert ("squadron", 5) in cl and ("squadron", 7) not in cl   # CL strike: CL only


def _winchester_fighter_returned(side=Side.US, sq=10, tt=TokenType.F_16C):
    # A live squadron with one of its fighters Winchester and returned to base.
    gs, eng = _mid_turn(side)
    gs.player(side).squadrons[sq] = SquadronState(sq, side, activated=True,
                                                  location=board_airbase(side), zone=CardZone.ACTIVE)
    f = gs.spawn_token(side, tt, front_band(side), TokenOrigin.SQUADRON_CARD, source_card_id=sq)
    f.winchester = True
    eng._start_turn(side)          # Winchester air token returns to base and grounds
    assert f.grounded and f.winchester
    return gs, eng, f


def board_airbase(side):
    return BandID.US_AIRBASE if side == Side.US else BandID.PRC_AIRBASE


def front_band(side):
    return BandID.BAND_A if side == Side.US else BandID.BAND_E


def test_winchester_fighter_relaunches_on_a_roll_above_one():
    # (FAQ 2026-07-24) A Winchester fighter that returned to a live squadron may
    # relaunch on a D4 roll of 2-4: rearmed (Winchester cleared) at the front band.
    gs, eng, f = _winchester_fighter_returned()
    f.acquired = True                                   # it had been acquired before
    assert f.uid in eng.relaunch_candidates(Side.US)
    eng._d4 = lambda: 2
    assert eng.relaunch_fighter(Side.US, f.uid) == 2
    # A fresh sortie: not grounded, not Winchester, not acquired, at the front band.
    assert not f.grounded and not f.winchester and not f.acquired
    assert f.location == BandID.BAND_A
    assert gs.get_token(f.uid) is not None and gs.prc.captures == []   # not lost


def test_winchester_fighter_broken_on_a_roll_of_one_scores_on_the_ground():
    # (FAQ 2026-07-24) A relaunch roll of 1 "breaks" the fighter: destroyed on the
    # ground and surrendered to the opponent for points (PRC Counter-Intervention
    # scores a ground air-kill as +3), and it is a permanent loss.
    gs, eng, f = _winchester_fighter_returned()
    gs.prc.mission_card_id = 108                     # PRC Counter-Intervention
    eng._d4 = lambda: 1
    assert eng.relaunch_fighter(Side.US, f.uid) == 1
    assert gs.get_token(f.uid) is None               # broken: removed from play
    caps = gs.prc.captures
    assert len(caps) == 1 and caps[0].destroyed_on_ground
    assert eng.score_captures(Side.PRC) == 3          # +3 ground air kill
    assert gs.us.squadrons[10].tokens_lost == 1       # permanent loss


def test_only_fighters_can_relaunch():
    # (FAQ 2026-07-24) All other aircraft cannot be regenerated once Winchester —
    # a bomber that returned Winchester is not a relaunch candidate.
    gs, eng, b52 = _winchester_fighter_returned(sq=2, tt=TokenType.B_52)
    assert eng.relaunch_candidates(Side.US) == []
    with pytest.raises(IllegalAction):
        eng.relaunch_fighter(Side.US, b52.uid)


def test_relaunch_is_offered_in_legal_actions_and_ends_the_turn():
    # It is the player's turn action (like activating): offered in the turn menu
    # and it ends the turn.
    gs, eng, f = _winchester_fighter_returned()
    offered = [a for a in eng.legal_actions(Side.US)
               if a.kind == "relaunch" and a.token_uid == f.uid]
    assert offered
    eng._d4 = lambda: 3
    eng.apply_action(offered[0])
    assert eng.state.active_side == Side.PRC          # the relaunch ended the turn


def test_broken_fighter_cannot_be_personnel_recovered():
    # (User-confirmed 2026-07-24) A fighter "broken" on a relaunch is gone for
    # good: it is not a revivable attack loss, so Personnel Recovery has nothing
    # to recover — no recovery window is opened for it.
    gs, eng, f = _winchester_fighter_returned()
    eng._d4 = lambda: 1                               # the relaunch breaks the fighter
    eng.relaunch_fighter(Side.US, f.uid)
    assert gs.get_token(f.uid) is None                # broken, surrendered to the opponent
    assert eng.recoverable_aircraft(Side.US) == []    # nothing for Personnel Recovery / Quick-Turn


def test_broken_reactivation_is_not_a_rule_of_law_activation():
    # (User-confirmed 2026-07-24) A recovered squadron that "breaks" on
    # reactivation (roll of 1) is NOT counted as an activation for Enforce Rule of
    # Law (US 54: +2 per squadron activated) — it failed to field anything.
    gs, eng = _mid_turn(Side.US)
    gs.us.mission_card_id = 54                         # Enforce Rule of Law
    sq = 5
    gs.us.squadrons[sq] = SquadronState(sq, Side.US, location=BandID.US_AIRBASE,
                                        zone=CardZone.SELECTED, recovered=True)
    eng._d4 = lambda: 1                               # reactivation breaks
    eng.activate_squadron(Side.US, sq)               # ends the turn -> scores Rule of Law
    assert eng.state.us.victory_points == 0           # no +2 for a failed activation


def test_ace_disadvantage_applies_to_hit_not_damage():
    # User ruling 2026-07-14: advantage/disadvantage do NOT apply to damage
    # rolls unless from missile defense or an enabler. The ACE posture's
    # base-defense disadvantage biases the to-hit roll only.
    gs, eng = _mid_turn(Side.PRC)
    gs.us.posture_card_id = 45                          # US ACE posture
    gs.prc.squadrons[61] = SquadronState(61, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    h6 = gs.spawn_token(Side.PRC, TokenType.H_6K, BandID.PRC_STANDOFF,
                        TokenOrigin.SQUADRON_CARD, source_card_id=61)
    modes = _mode_log(eng)
    eng._d4 = lambda: 4
    r = eng.shoot_surface(Side.PRC, h6.uid, target_band=BandID.US_AIRBASE)
    assert r.hit
    assert modes[0] == RollMode.DISADVANTAGE            # to-hit: ACE applies
    assert modes[1] == RollMode.NORMAL                  # damage: no posture bias


# --- rules clarifications (user rulings 2026-07-14) ----------------------------


def test_setup_rolls_are_recorded_for_the_ui():
    # The initiative bid, the winner's cyber-raise, and Play Intel roll
    # automatically (no decision node), so the engine records them as structured
    # facts for the UI to surface as clearly-labeled events (2026-07-31).
    eng = _setup(Side.US)   # _setup runs bid_for_initiative + play_intel
    kinds = [e["kind"] for e in eng.setup_roll_log]
    assert kinds[0] == "initiative"        # the bid is first
    assert "cyber_raise" in kinds          # a real bid grants a cyber-raise roll
    assert kinds[-1] == "play_intel"       # intel is last
    init = eng.setup_roll_log[0]
    assert init["winner"] in ("US", "PRC") and not init["auto"]
    assert set(init["us"]) >= {"natural", "value", "bonus", "mode", "dice"}
    intel = eng.setup_roll_log[-1]
    assert intel["us"]["sees"] >= 0 and intel["prc"]["sees"] >= 0
    assert intel["us"]["roll"]["value"] >= 1


def test_tournament_ato2_initiative_is_auto_and_has_no_bid_dice():
    # Campaign 2 ATO 2 auto-assigns initiative (no bid, no cyber raise); the
    # setup log still records it, as an auto entry carrying no dice.
    eng = _setup(Side.US, campaign=2)      # ATO-1 bid sets _initiative_by_ato[1]
    eng.setup_roll_log.clear()
    eng.state.ato_cycle = 2                 # Tournament auto-assigns ATO-2 initiative
    eng.bid_for_initiative()
    init = next(e for e in eng.setup_roll_log if e["kind"] == "initiative")
    assert init["auto"] and "us" not in init
    assert not any(e["kind"] == "cyber_raise" for e in eng.setup_roll_log)


def test_intel_advantage_side_rolls_at_advantage():
    # (1) The player with Intel Advantage rolls their Play Intel check with
    # advantage; the other side rolls a normal single die.
    gs, eng = _mid_turn()
    gs.us.intel_track = IntelTrack.ADVANTAGE
    modes = _mode_log(eng)
    eng.play_intel_roll()
    assert modes == [RollMode.ADVANTAGE, RollMode.NORMAL]   # US viewer, PRC viewer


def test_marine_littoral_requires_enemy_surface_combatant():
    # (2) Marine Littoral Regiment is only an option while enemy surface
    # combatants are on the board; an illegal play does not spend the card.
    eng = _setup(Side.US, us_en=(44,))
    assert not any(a.kind == "play_enabler" and a.card_id == 44
                   for a in eng.legal_actions(Side.US))
    with pytest.raises(IllegalAction):
        eng.play_enabler(Side.US, 44)
    assert eng.state.us.enablers[44].zone == CardZone.SELECTED
    eng.state.spawn_token(Side.PRC, TokenType.NANNING_162, BandID.BAND_C,
                          TokenOrigin.ENABLER_CARD)
    assert any(a.kind == "play_enabler" and a.card_id == 44
               for a in eng.legal_actions(Side.US))


def test_grounded_tokens_cannot_be_acquired_or_engaged():
    # (3)/(7) Tokens on the ground cannot be acquired — even if they were
    # acquired in the air — and die only with their squadron. ADA is the
    # exception: it is engaged on its base.
    gs, eng = _mid_turn(Side.PRC)
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    f16 = gs.spawn_token(Side.US, TokenType.F_16C, BandID.US_AIRBASE,
                         TokenOrigin.SQUADRON_CARD, source_card_id=10, grounded=True)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    j20 = gs.spawn_token(Side.PRC, TokenType.J_20B, BandID.BAND_A,
                         TokenOrigin.SQUADRON_CARD, source_card_id=60)
    with pytest.raises(IllegalAction):
        eng.acquire(Side.PRC, j20.uid, f16.uid)
    f16.acquired = True                                 # acquired while airborne
    with pytest.raises(IllegalAction):
        eng.shoot_air(Side.PRC, j20.uid, f16.uid)
    f16.acquired = False
    assert eng._acquire_n(Side.PRC, 4) == []            # enabler acquisition skips it
    assert eng._remove_tokens(Side.PRC, 4) == []        # enabler removal skips it
    assert not any(a.kind in ("acquire", "shoot_air") and a.target_uid == f16.uid
                   for a in eng.legal_actions(Side.PRC))
    # ADA on a base may still be acquired (and destroyed by base attacks).
    ada = gs.spawn_token(Side.US, TokenType.ADA_US, BandID.US_AIRBASE,
                         TokenOrigin.ENABLER_CARD)
    eng.acquire(Side.PRC, j20.uid, ada.uid)             # legal: no exception


def test_submarine_cancel_only_responds_to_opponent_submarine_card():
    # (4) The Submarine Strike CANCEL branch plays only as a response to the
    # opponent's just-played submarine enabler.
    eng = _setup(Side.US, us_en=(43,), prc_en=(89,))
    with pytest.raises(IllegalAction):                   # own turn: branch barred
        eng.play_enabler(Side.US, 43, EnablerPlay(choice="cancel"))
    with pytest.raises(IllegalAction):                   # no submarine play to cancel
        eng.play_enabler(Side.US, 43, EnablerPlay(choice="cancel"), response=True)
    assert eng.state.us.enablers[43].zone == CardZone.SELECTED   # card kept
    eng.pass_turn(Side.US)
    eng.play_enabler(Side.PRC, 89)                       # PRC submarine (attack branch)
    res = eng.play_enabler(Side.US, 43, EnablerPlay(choice="cancel"), response=True)
    assert res.cancelled
    assert 89 not in eng.state.prc.enablers_played_log   # PRC card voided


def test_reserves_window_opens_only_when_last_token_destroyed():
    # (6) Reserves plays only immediately after the opponent destroyed ALL of
    # a squadron's tokens.
    gs, eng = _mid_turn(Side.US)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    j10a = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D,
                          TokenOrigin.SQUADRON_CARD, source_card_id=60)
    j10b = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D,
                          TokenOrigin.SQUADRON_CARD, source_card_id=60)
    eng._remove_tokens(Side.US, 1, [j10a.uid])
    assert not eng.reserves_playable(Side.PRC)           # a token survives
    eng._remove_tokens(Side.US, 1, [j10b.uid])
    assert eng.reserves_playable(Side.PRC)               # squadron just emptied
    assert eng.reserves_eligible(Side.PRC) == [60]
    # A later, unrelated kill does not reopen the window.
    uas = gs.spawn_token(Side.PRC, TokenType.ATTACK_UAS_PRC, BandID.BAND_D,
                         TokenOrigin.ENABLER_CARD)
    eng._remove_tokens(Side.US, 1, [uas.uid])
    assert not eng.reserves_playable(Side.PRC)


def test_tokens_of_destroyed_squadron_keep_flying():
    # (Ruling 2026-07-17, reverses 2026-07-14 item 9) A squadron's surviving
    # airborne tokens keep flying and attacking after the card is destroyed;
    # they are turned over to the opponent the instant they go Winchester (or
    # ground, or are shot down), else at end of ATO.
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True, damage=2,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    f16 = gs.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_A,
                         TokenOrigin.SQUADRON_CARD, source_card_id=10)
    # Still a legal actor: it can move despite its squadron being destroyed.
    moves = [a for a in eng.legal_actions(Side.US)
             if a.token_uid == f16.uid and a.kind == "move"]
    assert moves
    eng.move(Side.US, f16.uid, moves[0].dest_band)      # no raise
    assert f16.uid in gs.us.tokens                       # not reaped while it can fly
    # Once Winchester it is surrendered to the opponent at the turn boundary.
    f16.winchester = True
    eng.end_turn(Side.US)
    assert f16.destroyed
    assert any(c.uid == f16.uid and not c.is_squadron_card for c in gs.prc.captures)


def test_destroying_bomber_squadron_scores_card_and_bomber():
    # User-reported scoring bug (2026-07-17): destroying a bomber Squadron Card
    # whose B-52 is airborne+Winchester must score BOTH the card (+2) and the
    # bomber (+3) under Attrition — total +5 — turned over at the turn boundary,
    # not deferred to end of ATO.
    gs, eng = _mid_turn(Side.US)
    gs.us.mission_card_id, gs.prc.mission_card_id = 51, 105          # both Attrition
    bomb = next(c for c, s in SQUADRON_REGISTRY.items()
                if s.side == Side.PRC
                and TOKEN_REGISTRY[s.token_type].token_score_type == TokenScoreType.BOMBER)
    gs.prc.squadrons[bomb] = SquadronState(bomb, Side.PRC, activated=True,
                                           location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE,
                                           ever_activated=True)
    b = gs.spawn_token(Side.PRC, SQUADRON_REGISTRY[bomb].token_type, BandID.BAND_C,
                       TokenOrigin.SQUADRON_CARD, source_card_id=bomb)
    b.winchester = True                                              # bomber has bombed
    gs.prc.squadrons[bomb].damage = 2                               # US destroys the card
    gs.destroy_squadron(Side.PRC, bomb, destroyed_by=Side.US, on_ground=True)
    assert eng.total_victory_points(Side.US) == 2                    # card only, so far
    eng.end_turn(Side.US)
    assert b.destroyed
    assert eng.total_victory_points(Side.US) == 5                    # +2 card, +3 bomber


def test_destroying_unactivated_squadron_scores_ungenerated_tokens():
    # User-reported bug (2026-07-17): destroying a Squadron Card whose tokens
    # have NOT generated must score the whole complement — they can never
    # generate now. An unactivated UAS Air Regiment (4 Attack UAS) under
    # Attrition scores +2 card and +1 per drone = +6.
    gs, eng = _mid_turn(Side.US)
    gs.us.mission_card_id, gs.prc.mission_card_id = 51, 105          # both Attrition
    uas = next(c for c, s in SQUADRON_REGISTRY.items()
               if s.side == Side.PRC
               and TOKEN_REGISTRY[s.token_type].token_score_type == TokenScoreType.UAS)
    full = TOKEN_REGISTRY[SQUADRON_REGISTRY[uas].token_type].token_count
    gs.prc.squadrons[uas] = SquadronState(uas, Side.PRC, activated=False,
                                          location=BandID.PRC_AIRBASE, zone=CardZone.SELECTED)
    gs.prc.squadrons[uas].damage = 2                                # US destroys the card
    gs.destroy_squadron(Side.PRC, uas, destroyed_by=Side.US, on_ground=True)
    assert eng.total_victory_points(Side.US) == 2 + full            # card + every drone
    assert gs.prc.squadrons[uas].tokens_lost == full               # cannot regenerate
    # Invariant: never field more than the complement.
    alive = sum(1 for t in gs.prc.living_tokens() if t.source_card_id == uas)
    assert alive + gs.prc.squadrons[uas].tokens_lost <= full


def test_cancel_response_refunds_ungenerated_token_scores():
    # A cancelled base strike (Red Horse / Resilient Bases) must revive the
    # squadron AND remove the ungenerated-token captures + restore tokens_lost,
    # so the recovered card regenerates in full.
    gs, eng = _mid_turn(Side.US, campaign=2)
    gs.us.mission_card_id, gs.prc.mission_card_id = 51, 105
    uas = next(c for c, s in SQUADRON_REGISTRY.items()
               if s.side == Side.PRC
               and TOKEN_REGISTRY[s.token_type].token_score_type == TokenScoreType.UAS)
    full = TOKEN_REGISTRY[SQUADRON_REGISTRY[uas].token_type].token_count
    gs.prc.squadrons[uas] = SquadronState(uas, Side.PRC, activated=False, damage=1,
                                          location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.us.squadrons[7] = SquadronState(7, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    b52 = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_STANDOFF,
                         TokenOrigin.SQUADRON_CARD, source_card_id=7)
    eng._d4 = lambda: 4
    eng.shoot_surface(Side.US, b52.uid, target_band=BandID.PRC_AIRBASE,
                      target_squadron_id=uas)
    # card + drones + any leftover damage on the airbase VP boxes (which now
    # count LIVE, user ruling 2026-08-10 — no longer only at end of ATO).
    assert eng.total_victory_points(Side.US) == 2 + full + gs.prc.airbase_vp_damage

    eng._cancel_last_attack(Side.PRC)                              # Red Horse cancels the strike
    assert gs.prc.squadrons[uas].zone != CardZone.DESTROYED        # squadron restored
    assert gs.prc.squadrons[uas].tokens_lost == 0                  # phantom loss undone
    assert eng.total_victory_points(Side.US) == 0                  # captures removed


def test_ship_tokens_move_one_band():
    # (User ruling 2026-07-31, reverting the 2026-07-14 no-move ruling) Surface
    # combatants move like any token, up to their Move Range of 1 among the
    # on-map range bands (their Winchester off-board relocation stays free
    # movement, handled separately at start of turn).
    gs, eng = _mid_turn(Side.US)
    ddg = gs.spawn_token(Side.US, TokenType.DDG_81, BandID.BAND_C,
                         TokenOrigin.ENABLER_CARD)
    dests = {a.dest_band for a in eng.legal_actions(Side.US)
             if a.kind == "move" and a.token_uid == ddg.uid}
    assert BandID.BAND_B in dests and BandID.BAND_D in dests   # 1 band each way
    assert BandID.BAND_A not in dests                          # 2 bands: out of range
    eng.move(Side.US, ddg.uid, BandID.BAND_B)                  # a move action: legal now
    assert ddg.location == BandID.BAND_B


def test_enablers_redraft_each_ato_cycle():
    # (Ruling 2026-07-17) At each ATO start players draft a FRESH enabler
    # hand per their posture: played single-use cards never return; unplayed
    # single-use cards return to the pool and may be drafted again; multi-use
    # cards return regardless of prior play. The count stays exact.
    gs, eng = _mid_turn(campaign=3)
    us = gs.us
    us.enablers[44] = EnablerCardState(44, Side.US, zone=CardZone.PLAYED)    # played single-use
    us.enablers[43] = EnablerCardState(43, Side.US, zone=CardZone.PLAYED)    # played multi-use
    us.enablers[27] = EnablerCardState(27, Side.US, zone=CardZone.SELECTED)  # held, unplayed
    eng.end_ato_cycle()
    assert us.enablers[44].zone == CardZone.REMOVED
    assert us.enablers[43].zone == CardZone.DECK
    assert us.enablers[27].zone == CardZone.DECK

    n = POSTURE_REGISTRY[49].enablers
    with pytest.raises(IllegalAction):                   # played single-use is gone
        eng.select_posture_only(Side.US, 49, draft_enablers(
            Side.US, include=(44,), n=n, camp=eng.campaign))
    with pytest.raises(IllegalAction):                   # count is exact each cycle
        eng.select_posture_only(Side.US, 49, [43])

    redraft = draft_enablers(Side.US, include=(43, 27), exclude=(44,),
                             n=n, camp=eng.campaign)
    eng.select_posture_only(Side.US, 49, redraft)        # fresh draft succeeds
    hand = {c.card_id for c in us.enablers_in_hand()}
    assert hand == set(redraft)
    assert 44 not in hand and {43, 27} <= hand           # re-drafted despite prior use
    assert us.enablers[44].zone == CardZone.REMOVED      # still out for the campaign


def test_activation_never_exceeds_token_count():
    # (Ruling 2026-07-15) A player can never field more tokens than the token
    # count. A revived squadron (Rapid Resupply) whose flights were still
    # airborne re-activates for only the missing complement.
    gs, eng = _mid_turn(Side.US)
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    for _ in range(4):
        gs.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_B,
                       TokenOrigin.SQUADRON_CARD, source_card_id=10)
    gs.us.squadrons[10].damage = 2                       # card destroyed, tokens airborne
    gs.us.enablers[18] = EnablerCardState(18, Side.US, zone=CardZone.SELECTED)
    eng.play_enabler(Side.US, 18, EnablerPlay(target_squadron_id=10),
                     response=True)                                # revive card
    gs.us.reset_turn()
    toks = eng.activate_squadron(Side.US, 10)
    assert len(toks) == 0                                # full complement already up
    assert sum(1 for t in gs.us.living_tokens() if t.source_card_id == 10) == 4


def test_squadron_base_placement_is_rechosen_each_cycle():
    # (Ruling 2026-07-22) Squadrons are re-drafted every ATO cycle, so their
    # Airbase-vs-Contingency-Location placement is chosen fresh each cycle. A
    # squadron at the CL in ATO 1 may redeploy to the Airbase in ATO 2; its
    # partial CARD damage resets across the cycle (ruling 2026-07-31).
    eng = RulesEngine(GameState.new_game(2), rng=random.Random(0))
    eng.setup_missions(51, 105)
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (10, 5), camp=eng.campaign),
                       draft_enablers(Side.US),
                       squadron_locations={10: BandID.US_CONTINGENCY_LOCATION})
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, (60,), camp=eng.campaign),
                       draft_enablers(Side.PRC))
    eng.state.us.squadrons[10].damage = 1              # card damage resets next ATO
    eng.bid_for_initiative(first_player=Side.US)
    eng.play_intel()
    eng.begin_player_turns()
    eng.pass_turn(Side.US)
    eng.pass_turn(Side.PRC)
    assert eng.state.ato_cycle == 2
    # Re-draft the same squadrons, this time placing 10 at the Airbase.
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (10, 5), camp=eng.campaign),
                       draft_enablers(Side.US),
                       squadron_locations={10: BandID.US_AIRBASE})
    assert eng.state.us.squadrons[10].location == BandID.US_AIRBASE   # re-placed
    assert eng.state.us.squadrons[10].damage == 0                     # card damage reset


def test_counter_intervention_plarf_vp_survives_ato_cleanup():
    # PLARF-play VP used to be derived live from enablers_played_log, which
    # resets at cleanup — the points silently vanished after each ATO. Now
    # accrued (with a vp_log entry) at end of cycle.
    gs, eng = _mid_turn(Side.PRC, campaign=2)
    gs.prc.mission_card_id = 108                        # Counter-Intervention
    gs.us.mission_card_id = 51
    gs.prc.enablers_played_log.append(78)               # Hypersonic Missile (PLARF)
    total_before_cleanup = eng.total_victory_points(Side.PRC)
    eng.end_ato_cycle()                                 # ATO 1 -> 2
    assert eng.total_victory_points(Side.PRC) == total_before_cleanup + 1
    assert (1, "Counter-Intervention: PLARF plays", 1) in gs.prc.vp_log


def test_game_end_does_not_double_count_capture_vp():
    # (Bug 2026-07-15, C2 seed 5) _finalize_game folded capture VP into the
    # stored victory_points, so every post-game total_victory_points() read
    # counted captures twice — Attrition scores displayed roughly doubled.
    gs, eng = _mid_turn(Side.US, campaign=1)            # campaign 1: single ATO
    gs.us.mission_card_id, gs.prc.mission_card_id = 51, 105   # both Attrition
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D,
                         TokenOrigin.SQUADRON_CARD, source_card_id=60)
    gs.destroy_token(j10.uid, destroyed_by=Side.US)     # fighter: +1 VP
    total_before = eng.total_victory_points(Side.US)
    assert total_before == 1
    eng.end_ato_cycle()                                 # final ATO -> game over
    assert gs.game_over
    assert eng.total_victory_points(Side.US) == total_before   # stable after finalize
    assert gs.us.victory_points == 0                    # accrued VP untouched


# --- rules clarifications (user, 2026-07-17) ------------------------------------

def test_exploding_die_rerolls_for_damage_only_on_a_hit():
    # The sunburst around a token's die symbol means: if the shot succeeds, roll
    # again to determine how much damage is inflicted. Tokens without it inflict
    # a flat 1 point. A miss rolls no damage die at all.
    gs, eng = _mid_turn(Side.US, campaign=2)
    b52 = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_AIRBASE,
                         TokenOrigin.SQUADRON_CARD, source_card_id=7)
    assert TOKEN_REGISTRY[TokenType.B_52].surf_exploding_die       # sunburst token
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)

    rolls = iter([4, 3])            # hit roll, then the exploding damage roll
    eng._d4 = lambda: next(rolls)
    r = eng.shoot_surface(Side.US, b52.uid, target_band=BandID.PRC_AIRBASE,
                          target_squadron_id=60)
    assert r.hit and r.damage == 3                                # damage = 2nd roll

    # A miss rolls no damage die (the single queued roll is never consumed).
    gs2, eng2 = _mid_turn(Side.US, campaign=2)
    b52b = gs2.spawn_token(Side.US, TokenType.B_52, BandID.US_AIRBASE,
                           TokenOrigin.SQUADRON_CARD, source_card_id=7)
    gs2.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                          location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    only = iter([1])                # hit roll fails; no second roll may be drawn
    eng2._d4 = lambda: next(only)
    r2 = eng2.shoot_surface(Side.US, b52b.uid, target_band=BandID.PRC_AIRBASE,
                            target_squadron_id=60)
    assert not r2.hit and r2.damage == 0


def test_non_exploding_token_inflicts_flat_one_damage():
    # An F-15E has no sunburst: a successful surface shot is a flat 1 point.
    gs, eng = _mid_turn(Side.US, campaign=2)
    assert not TOKEN_REGISTRY[TokenType.F_15E].surf_exploding_die
    f15 = gs.spawn_token(Side.US, TokenType.F_15E, BandID.BAND_E,  # range 1: adjacent
                         TokenOrigin.SQUADRON_CARD, source_card_id=7)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    eng._d4 = lambda: 4             # always hits; damage must NOT become 4
    r = eng.shoot_surface(Side.US, f15.uid, target_band=BandID.PRC_AIRBASE,
                          target_squadron_id=60)
    assert r.hit and r.damage == 1


def test_airbase_damage_persists_across_ato_and_scores_once():
    # (Ruling 2026-07-17) Airbase damage does NOT reset between ATO cycles — the
    # 3 VP boxes are a campaign total. Persisting boxes must not re-score every
    # cycle, so only newly-hit boxes pay out.
    gs, eng = _mid_turn(Side.US, campaign=3)
    gs.prc.airbase_vp_damage = 2                      # US hit 2 boxes in ATO 1
    eng.end_ato_cycle()
    assert gs.prc.airbase_vp_damage == 2              # carried over, not cleared
    assert eng.total_victory_points(Side.US) == 2     # +1 per box

    eng.end_ato_cycle()                               # ATO 2, no new damage
    assert gs.prc.airbase_vp_damage == 2
    assert eng.total_victory_points(Side.US) == 2     # NOT scored again

    gs.prc.airbase_vp_damage = 3                      # a third box this cycle
    eng.end_ato_cycle()
    assert eng.total_victory_points(Side.US) == 3     # only the new box pays


def test_squadron_card_damage_resets_between_atos():
    # User ruling 2026-07-31 (reverses the 2026-07-17 "damage persists"): a
    # squadron card's PARTIAL damage RESETS at the start of the next ATO (a dinged
    # card redeploys fresh). A COMPLETELY destroyed card still stays out (scored),
    # and TOKEN losses still persist — only card damage resets.
    eng = _setup(Side.US, us_sq=(10, 5), campaign=2)
    eng.state.us.squadrons[5].damage = 1
    _end_cycle_with_pass(eng)                         # two passes close the ATO
    assert eng.state.ato_cycle == 2
    eng.select_posture_only(Side.US, 49)
    assert eng.state.us.squadrons[5].damage == 0      # partial CARD damage reset
    assert not eng.state.us.squadrons[5].is_destroyed
