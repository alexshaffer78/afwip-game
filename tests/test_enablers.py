"""One test per enabler-effect taxonomy row (enablers.py handlers)."""

import random

import pytest

from afwip.core.rules import RulesEngine, IllegalAction
from afwip.core.enablers import EnablerPlay
from afwip.core.state import GameState, SquadronState, EnablerCardState, CardZone
from afwip.core.cards import ENABLER_REGISTRY, SQUADRON_REGISTRY
from afwip.core.tokens import TOKEN_REGISTRY
from afwip.core import board
from afwip.core.constants import Side, BandID, Phase, TokenType, TokenOrigin
from tests.helpers import draft_enablers, draft_squadrons


def setup(active: Side, enabler_ids, *, us_sq=(10,), prc_sq=(60,), campaign=3, seed=0):
    """
    Build a game mid-turn with `active` to move and the given enablers in hand.
    Hands are padded to the posture's exact enabler count (6 for Standard).
    """
    eng = RulesEngine(GameState.new_game(campaign), rng=random.Random(seed))
    eng.setup_missions(51, 105)
    us_en = [e for e in enabler_ids if ENABLER_REGISTRY[e].side == Side.US]
    prc_en = [e for e in enabler_ids if ENABLER_REGISTRY[e].side == Side.PRC]
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, us_sq, camp=eng.campaign),
                       draft_enablers(Side.US, us_en))
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, prc_sq, camp=eng.campaign),
                       draft_enablers(Side.PRC, prc_en))
    eng.bid_for_initiative(first_player=active)
    eng.play_intel()
    eng.begin_player_turns()
    assert eng.state.active_side == active
    return eng


def spawn_enemy(eng, side, token_type, band, n=1):
    """Spawn n enemy tokens of the given type, return uids."""
    enemy = eng.state.opponent(side).side
    return [eng.state.spawn_token(enemy, token_type, band, TokenOrigin.SQUADRON_CARD, source_card_id=60).uid
            for _ in range(n)]


# --- token generation --------------------------------------------------------

def test_generate_token():
    eng = setup(Side.US, [37])  # Maritime Missile Defense -> DDG 81
    res = eng.play_enabler(Side.US, 37, EnablerPlay(spawn_band=BandID.BAND_C))
    assert len(res.tokens) == 1
    tok = eng.state.get_token(res.tokens[0])
    assert tok.token_type == TokenType.DDG_81 and tok.origin == TokenOrigin.ENABLER_CARD


# --- acquisition -------------------------------------------------------------

def test_acquire_roll():
    eng = setup(Side.US, [31])  # Space Recon: roll d4, acquire that many
    uids = spawn_enemy(eng, Side.US, TokenType.J_10, BandID.BAND_D, n=3)
    eng._d4 = lambda: 2
    res = eng.play_enabler(Side.US, 31)
    assert len(res.acquired) == 2
    assert all(eng.state.get_token(u).acquired for u in res.acquired)


def test_acquire_by_cyber():
    eng = setup(Side.US, [21])  # Cyber Recon: acquire = cyber rate
    eng.state.us.cyber_rate = 2
    spawn_enemy(eng, Side.US, TokenType.J_10, BandID.BAND_D, n=3)
    res = eng.play_enabler(Side.US, 21)
    assert len(res.acquired) == 2


def test_acquire_roll_cyber_on_four():
    eng = setup(Side.US, [14])  # SOF Recon: on nat-4, +1 cyber
    eng.state.us.cyber_rate = 1
    spawn_enemy(eng, Side.US, TokenType.J_10, BandID.BAND_D, n=4)
    eng._d4 = lambda: 4
    res = eng.play_enabler(Side.US, 14)
    assert len(res.acquired) == 4 and res.cyber_delta == 1
    assert eng.state.us.cyber_rate == 2


# --- cyber -------------------------------------------------------------------

def test_cyber_raise():
    eng = setup(Side.US, [22])  # Cyber Infiltration
    eng.state.us.cyber_rate = 1
    eng._d4 = lambda: 4
    res = eng.play_enabler(Side.US, 22)
    assert res.cyber_delta == 1 and eng.state.us.cyber_rate == 2


def test_cyber_degrade():
    eng = setup(Side.US, [33])  # Joint Defensive Cyber: -2 PRC
    eng.state.prc.cyber_rate = 3
    res = eng.play_enabler(Side.US, 33)
    assert res.cyber_delta == -2 and eng.state.prc.cyber_rate == 1


# --- token removal / discard -------------------------------------------------

def test_offensive_cyber_remove():
    eng = setup(Side.US, [24])
    eng.state.us.cyber_rate = 2
    spawn_enemy(eng, Side.US, TokenType.J_10, BandID.BAND_D, n=3)
    res = eng.play_enabler(Side.US, 24, EnablerPlay(choice="remove"))
    assert len(res.destroyed) == 2
    assert len(eng.state.prc.living_tokens()) == 1


def test_offensive_cyber_discard():
    eng = setup(Side.US, [24, 81, 89])  # give PRC hand cards to discard
    eng.state.us.cyber_rate = 2
    res = eng.play_enabler(Side.US, 24, EnablerPlay(choice="discard"))
    assert len(res.discarded) == 2


def test_counter_uas():
    eng = setup(Side.US, [25])
    eng.state.us.cyber_rate = 2
    spawn_enemy(eng, Side.US, TokenType.ATTACK_UAS_PRC, BandID.BAND_D, n=3)
    spawn_enemy(eng, Side.US, TokenType.J_10, BandID.BAND_D, n=1)  # not a UAS
    res = eng.play_enabler(Side.US, 25)
    assert len(res.destroyed) == 2
    survivors = eng.state.prc.living_tokens()
    assert sum(1 for t in survivors if t.score_type.value == "UAS") == 1  # 1 UAS left
    assert any(t.token_type == TokenType.J_10 for t in survivors)          # fighter untouched


# --- base strikes ------------------------------------------------------------

def test_strike_gated_hits_and_damages():
    # HIMARS names the "Airbase": its rolled damage fills only the 3 VP boxes,
    # never the Squadron Cards deployed there (FAQ 2026-07-24).
    eng = setup(Side.US, [41])  # HIMARS: roll 2+ then d4 damage
    eng._d4 = lambda: 3         # gate passes; damage roll 3
    res = eng.play_enabler(Side.US, 41, EnablerPlay(target_squadron_id=60))
    assert res.base_damage == 3
    assert eng.state.prc.airbase_vp_damage == 3          # VP boxes filled
    assert not eng.state.prc.squadrons[60].is_destroyed  # squadron untouched


def test_strike_gated_can_miss():
    eng = setup(Side.US, [41])
    eng._d4 = lambda: 1         # gate fails
    res = eng.play_enabler(Side.US, 41)
    assert res.base_damage == 0


def test_strike_unblockable():
    eng = setup(Side.PRC, [78])  # Hypersonic Missile (PRC), unblockable vs US base
    eng._d4 = lambda: 4
    res = eng.play_enabler(Side.PRC, 78)
    assert res.base_damage == 4


def test_tomahawk_generates_and_strikes():
    eng = setup(Side.US, [42])
    eng._d4 = lambda: 3
    res = eng.play_enabler(Side.US, 42, EnablerPlay(spawn_band=BandID.BAND_C))
    assert len(res.tokens) == 1 and res.base_damage == 3


# --- ship kills --------------------------------------------------------------

def test_marine_littoral_auto_kill():
    eng = setup(Side.US, [44])
    ship = spawn_enemy(eng, Side.US, TokenType.NANNING_162, BandID.BAND_C)[0]
    res = eng.play_enabler(Side.US, 44)
    assert res.destroyed == [ship] and eng.state.get_token(ship) is None


def test_maritime_cruise_unblockable_kill():
    eng = setup(Side.PRC, [77])
    ship = spawn_enemy(eng, Side.PRC, TokenType.DDG_81, BandID.BAND_C)[0]
    res = eng.play_enabler(Side.PRC, 77)
    assert res.destroyed == [ship]


# --- recovery / regeneration -------------------------------------------------

def test_recover_aircraft_after_loss():
    eng = setup(Side.PRC, [12])  # PRC active; US holds Personnel Recovery
    us_f22 = eng.state.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C, TokenOrigin.SQUADRON_CARD, source_card_id=10)
    us_f22.acquired = True
    j10 = eng.state.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D, TokenOrigin.SQUADRON_CARD, source_card_id=60)
    eng._d4 = lambda: 4
    eng.shoot_air(Side.PRC, j10.uid, us_f22.uid)
    assert eng.state.get_token(us_f22.uid) is None      # destroyed
    res = eng.play_enabler(Side.US, 12, response=True)   # recover
    assert res.recovered == [us_f22.uid]
    revived = eng.state.get_token(us_f22.uid)
    assert revived is not None and revived.location == BandID.BAND_A
    # A recovered sortie re-enters FRESH: even though it was acquired before it
    # was shot down, it comes back face-down so the enemy must re-acquire it.
    assert not revived.acquired


def test_recover_card():
    eng = setup(Side.US, [18, 22])
    eng.state.us.enablers[22].zone = CardZone.DISCARDED
    res = eng.play_enabler(Side.US, 18, EnablerPlay(target_squadron_id=22),
                           response=True)   # 18 is response-only (2026-07-17)
    assert eng.state.us.enablers[22].zone == CardZone.SELECTED and res.recovered == [22]


def test_reserves_regenerates_squadron():
    # Reserves plays only after the opponent destroyed ALL of a squadron's
    # tokens (user ruling 2026-07-14); regeneration restores the full complement.
    import pytest
    from afwip.core.rules import IllegalAction
    eng = setup(Side.PRC, [67])
    squad = eng.state.prc.squadrons[60]
    squad.activated = True
    squad.zone = CardZone.ACTIVE
    j10 = eng.state.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D,
                                TokenOrigin.SQUADRON_CARD, source_card_id=60)
    # Squadron still has a living token -> Reserves is not playable (card kept).
    with pytest.raises(IllegalAction):
        eng.play_enabler(Side.PRC, 67, EnablerPlay(target_squadron_id=60), response=True)
    assert eng.state.prc.enablers[67].zone == CardZone.SELECTED
    eng.state.destroy_token(j10.uid, destroyed_by=Side.US)
    eng.play_enabler(Side.PRC, 67, EnablerPlay(target_squadron_id=60), response=True)
    assert not squad.activated and squad.zone == CardZone.SELECTED
    assert squad.tokens_lost == 0   # fully regenerated: full complement returns


def test_reserves_unscores_the_regenerated_squadron():
    # "The squadron is fully regenerated" — the opponent loses every point it
    # scored for emptying the squadron, air kills included (ruling 2026-07-22).
    eng = setup(Side.PRC, [67])
    squad = eng.state.prc.squadrons[60]
    squad.activated = True
    squad.zone = CardZone.ACTIVE
    j10 = eng.state.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D,
                                TokenOrigin.SQUADRON_CARD, source_card_id=60)
    eng.state.destroy_token(j10.uid, destroyed_by=Side.US)
    assert eng.state.us.captures                       # US scored the air kill
    play = eng._default_enabler_play(Side.PRC, 67)     # real default (UI) path
    assert play.target_squadron_id == 60
    eng.play_enabler(Side.PRC, 67, play, response=True)
    assert eng.state.us.captures == []                 # refunded on regeneration
    assert squad.tokens_lost == 0


def test_reserves_regenerates_a_base_struck_squadron():
    # A squadron whose CARD was destroyed by a base strike is still a Reserves
    # target (ruling 2026-07-22): it comes back and the opponent loses the kill.
    eng = setup(Side.US, [67], prc_sq=(60,))           # US active; PRC holds Reserves
    ps = eng.state.prc.squadrons[60]
    ps.activated = True
    ps.zone = CardZone.ACTIVE
    ps.location = BandID.PRC_AIRBASE
    tok = eng.state.spawn_token(Side.PRC, TokenType.J_10, BandID.PRC_AIRBASE,
                                TokenOrigin.SQUADRON_CARD, source_card_id=60)
    ps.grounded_token_uids = [tok.uid]
    eng._strike_base(Side.US, BandID.PRC_AIRBASE, roll_gate=None, bypass_md=True,
                     fixed_damage=2, target_squadron_id=60)
    assert ps.is_destroyed and eng.state.us.captures    # card destroyed + scored
    assert eng.reserves_playable(Side.PRC)              # base strike opens the window
    play = eng._default_enabler_play(Side.PRC, 67)      # real default (UI) path
    assert play.target_squadron_id == 60
    eng.play_enabler(Side.PRC, 67, play, response=True)
    assert not ps.is_destroyed and ps.zone == CardZone.SELECTED and ps.damage == 0
    assert ps.tokens_lost == 0
    assert eng.state.us.captures == []                  # opponent no longer profits


def test_card_65_a2ad_cancel_reverses_a_recovered_aircraft():
    # Anti-Access/Area Denial must undo the mobility card's EFFECT, not merely
    # un-log it: the recovered aircraft goes back down, the opponent regains the
    # kill, and the cancelled card scores nothing.
    eng = setup(Side.US, [12, 65], us_sq=(10,), prc_sq=(60,))
    f = eng.state.spawn_token(Side.US, TokenType.F_35A, BandID.BAND_A,
                              TokenOrigin.SQUADRON_CARD, source_card_id=10)
    eng._remove_tokens(Side.PRC, 1, [f.uid])                 # PRC kills it
    eng.play_enabler(Side.US, 12, eng._default_enabler_play(Side.US, 12), response=True)
    assert f.uid in eng.state.us.tokens and not eng.state.prc.captures   # recovered
    res = eng.play_enabler(Side.PRC, 65, eng._default_enabler_play(Side.PRC, 65),
                           response=True)
    assert res.cancelled
    assert f.uid not in eng.state.us.tokens                  # sent back down
    assert len(eng.state.prc.captures) == 1                  # kill restored
    assert 12 not in eng.state.us.enablers_played_log        # scores nothing


def test_card_65_a2ad_responds_to_a_mobility_card_played_as_a_response():
    # The response-to-a-response window: US plays Personnel Recovery as a
    # response, PRC then plays A2/AD to cancel it.
    from afwip.script import GameScript, Choice
    from afwip.core.constants import EnablerTrigger
    eng = setup(Side.US, [12, 65], us_sq=(10,), prc_sq=(60,))
    f = eng.state.spawn_token(Side.US, TokenType.F_35A, BandID.BAND_A,
                              TokenOrigin.SQUADRON_CARD, source_card_id=10)
    eng._remove_tokens(Side.PRC, 1, [f.uid])
    gs = GameScript(eng)
    gen = gs._response_window(Side.US, {EnablerTrigger.OWN_AIRCRAFT_LOST})
    node = next(gen)                                          # US may respond
    assert node.side == Side.US
    node2 = gen.send(Choice("PR", value=12))                 # US plays Personnel Recovery
    assert node2.side == Side.PRC                             # nested window for PRC
    assert any(c.value == 65 for c in node2.choices)          # A2/AD offered
    try:
        gen.send(Choice("A2/AD", value=65))                  # PRC cancels PR
    except StopIteration:
        pass
    assert f.uid not in eng.state.us.tokens                   # PR cancelled
    assert 12 not in eng.state.us.enablers_played_log


def test_card_68_uas_proliferation_offered_after_a_uas_acquire():
    from afwip.script import GameScript, NodeType
    from afwip.core.rules import LegalAction
    eng = setup(Side.PRC, [68], prc_sq=(60,))
    uas = eng.state.spawn_token(Side.PRC, TokenType.RECON_UAS_PRC, BandID.BAND_D,
                                TokenOrigin.SQUADRON_CARD, source_card_id=60)
    tgt = eng.state.spawn_token(Side.US, TokenType.F_35A, BandID.BAND_D,
                                TokenOrigin.SQUADRON_CARD, source_card_id=10)
    gs = GameScript(eng)
    gen = gs._apply_turn_action(
        Side.PRC, LegalAction("acquire", token_uid=uas.uid, target_uid=tgt.uid))
    node = next(gen)
    assert node.node_type == NodeType.RESPONSE and node.side == Side.PRC
    assert any(c.value == 68 for c in node.choices)           # UAS Proliferation offered


def test_air_to_air_missile_defense_node_offered_to_the_defender():
    # (FAQ 2026-07-24) The script opens an MD_DECLARE window for the defender when
    # a naval ship covers an air-to-air shot's WEZ, so the defender may activate it.
    from afwip.script import GameScript, NodeType
    from afwip.core.rules import LegalAction
    eng = setup(Side.US, [], prc_sq=(60,))
    f22 = eng.state.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C,
                                TokenOrigin.SQUADRON_CARD, source_card_id=10)
    j10 = eng.state.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D,
                                TokenOrigin.SQUADRON_CARD, source_card_id=60)
    ship = eng.state.spawn_token(Side.PRC, TokenType.NANNING_162, BandID.BAND_E,
                                 TokenOrigin.ENABLER_CARD, source_card_id=87)
    j10.acquired = True
    gen = GameScript(eng)._shoot_air(
        Side.US, LegalAction("shoot_air", token_uid=f22.uid, target_uid=j10.uid))
    node = next(gen)
    assert node.node_type == NodeType.MD_DECLARE and node.side == Side.PRC
    assert any(c.value == ship.uid for c in node.choices)     # the ship may defend


def test_card_65_reverses_rapid_resupply_squadron_recovery():
    # A2/AD cancelling Rapid Resupply (18) re-loses the squadron it recovered
    # and restores every capture (including value-identical ungenerated ones).
    eng = setup(Side.US, [18, 65], us_sq=(10, 5), prc_sq=(60,))
    eng.state.destroy_squadron(Side.US, 5, destroyed_by=Side.PRC)
    caps = len(eng.state.prc.captures)
    assert caps and eng.state.us.squadrons[5].is_destroyed
    eng.play_enabler(Side.US, 18, eng._default_enabler_play(Side.US, 18), response=True)
    assert not eng.state.us.squadrons[5].is_destroyed and not eng.state.prc.captures
    res = eng.play_enabler(Side.PRC, 65, eng._default_enabler_play(Side.PRC, 65),
                           response=True)
    assert res.cancelled
    assert eng.state.us.squadrons[5].is_destroyed                 # re-lost
    assert len(eng.state.prc.captures) == caps                    # captures restored
    assert 18 not in eng.state.us.enablers_played_log


def test_card_65_reapplies_red_horse_cancelled_base_damage():
    # A2/AD cancelling Red Horse (38) re-applies the base damage Red Horse voided
    # — up to and including re-destroying a squadron it had saved.
    eng = setup(Side.PRC, [38, 65], us_sq=(10,), prc_sq=(60,))
    sq = eng.state.us.squadrons[10]
    sq.location, sq.activated, sq.zone = BandID.US_AIRBASE, True, CardZone.ACTIVE
    tok = eng.state.spawn_token(Side.US, TokenType.F_15E, BandID.US_AIRBASE,
                                TokenOrigin.SQUADRON_CARD, source_card_id=10)
    sq.grounded_token_uids = [tok.uid]
    eng._strike_base(Side.PRC, BandID.US_AIRBASE, roll_gate=None, bypass_md=True,
                     fixed_damage=2, target_squadron_id=10)
    caps = len(eng.state.prc.captures)
    assert sq.is_destroyed and caps
    eng.play_enabler(Side.US, 38, eng._default_enabler_play(Side.US, 38), response=True)
    assert not sq.is_destroyed and not eng.state.prc.captures     # Red Horse saved it
    res = eng.play_enabler(Side.PRC, 65, eng._default_enabler_play(Side.PRC, 65),
                           response=True)
    assert res.cancelled
    assert sq.is_destroyed                                        # damage re-applied
    assert len(eng.state.prc.captures) == caps                    # kills restored
    assert 38 not in eng.state.us.enablers_played_log


def test_card_72_acquire_branch_rolls_then_lets_owner_choose():
    from afwip.script import GameScript, NodeType
    eng = setup(Side.PRC, [72], prc_sq=(60,))
    for _ in range(2):
        eng.state.spawn_token(Side.US, TokenType.F_35A, BandID.BAND_C,
                              TokenOrigin.SQUADRON_CARD, source_card_id=10)
    gs = GameScript(eng)
    gen = gs._build_enabler_play(Side.PRC, 72)
    node = next(gen)                                              # ENABLER_BRANCH
    assert node.node_type == NodeType.ENABLER_BRANCH
    node = gen.send(next(c for c in node.choices if c.value == "acquire"))
    # The acquire branch now rolls first, then offers a per-token pick.
    assert node.node_type == NodeType.TURN_ACTION and node.choices[0].kind == "acquire"
    try:
        while True:
            node = gen.send(node.choices[0])
    except StopIteration as e:
        play = e.value
    assert play.choice == "acquire" and play.rolled_count is not None
    assert play.target_uids                                       # owner-chosen targets


def test_card_72_advantage_branch_grants_air_advantage():
    from afwip.core.constants import RollMode
    eng = setup(Side.PRC, [72], prc_sq=(60,))
    j10 = eng.state.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_C,
                                TokenOrigin.SQUADRON_CARD, source_card_id=60)
    f22 = eng.state.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C,
                                TokenOrigin.SQUADRON_CARD, source_card_id=5)
    f22.acquired = True
    eng.play_enabler(Side.PRC, 72, EnablerPlay(choice="advantage"))
    assert eng.state.prc.pending_air_advantage
    eng._d4 = lambda: 4                                           # deterministic hit
    r = eng.shoot_air(Side.PRC, j10.uid, f22.uid)
    assert r.hit_roll.mode == RollMode.ADVANTAGE                  # advantage applied
    assert not eng.state.prc.pending_air_advantage               # one-shot consumed


def test_card_74_lets_owner_choose_the_fighter_squadron():
    from afwip.script import GameScript, NodeType
    # Squadron 60 (J-10) and 62 are PRC fighter squadrons.
    eng = setup(Side.PRC, [74], prc_sq=(60, 62))
    gs = GameScript(eng)
    gen = gs._build_enabler_play(Side.PRC, 74)
    node = next(gen)
    assert node.node_type == NodeType.SQUADRON_PICK
    assert {c.value for c in node.choices} == {60, 62}            # both fighters offered
    try:
        gen.send(next(c for c in node.choices if c.value == 62))
    except StopIteration as e:
        play = e.value
    assert play.target_squadron_id == 62
    eng.play_enabler(Side.PRC, 74, play)
    assert eng.state.prc.air_range_override.get(62) == 4          # range 4 applied to 62


@pytest.mark.parametrize("active, card, enemy, uas0, uas1, fighter", [
    (Side.US, 25, Side.PRC, TokenType.ATTACK_UAS_PRC, TokenType.RECON_UAS_PRC, TokenType.J_10),
    (Side.PRC, 84, Side.US, TokenType.ATTACK_UAS_US, TokenType.RECON_UAS_US, TokenType.F_35A),
])
def test_counter_uas_lets_owner_choose_the_uas(active, card, enemy, uas0, uas1, fighter):
    # 25/84 destroy Cyber-Rate enemy UAS; the owner now picks WHICH UAS, and a
    # non-UAS token is never eligible.
    from afwip.script import GameScript, NodeType
    eng = setup(active, [card], us_sq=(10,), prc_sq=(60,))
    eng.state.player(active).cyber_rate = 1
    src = 10 if enemy == Side.US else 60
    u0 = eng.state.spawn_token(enemy, uas0, BandID.BAND_C, TokenOrigin.SQUADRON_CARD, source_card_id=src)
    u1 = eng.state.spawn_token(enemy, uas1, BandID.BAND_C, TokenOrigin.SQUADRON_CARD, source_card_id=src)
    fj = eng.state.spawn_token(enemy, fighter, BandID.BAND_C, TokenOrigin.SQUADRON_CARD, source_card_id=src)
    gs = GameScript(eng)
    gen = gs._build_enabler_play(active, card)
    node = next(gen)
    assert node.node_type == NodeType.TURN_ACTION
    assert {c.target_uid for c in node.choices} == {u0.uid, u1.uid}   # UAS only, no fighter
    try:
        gen.send(next(c for c in node.choices if c.value == u1.uid))
    except StopIteration as e:
        play = e.value
    assert play.target_uids == [u1.uid]
    eng.play_enabler(active, card, play)
    enemy_tokens = eng.state.opponent(active).tokens
    assert u1.uid not in enemy_tokens                                 # chosen UAS destroyed
    assert u0.uid in enemy_tokens and fj.uid in enemy_tokens          # others spared


def test_card_91_constellation_returns_a_spent_plassf_card_via_default():
    # The real (UI) path: _default_enabler_play must target a SPENT PLASSF card,
    # not a live squadron — the earlier default silently no-oped the card.
    eng = setup(Side.PRC, [91, 80], prc_sq=(60,))
    eng.state.prc.enablers[80].zone = CardZone.PLAYED        # spent PLASSF cyber card
    play = eng._default_enabler_play(Side.PRC, 91)
    assert play.target_squadron_id == 80
    res = eng.play_enabler(Side.PRC, 91, play)
    assert res.recovered == [80]
    assert eng.state.prc.enablers[80].zone == CardZone.DECK  # returned for next ATO


def test_card_91_constellation_lets_owner_choose_the_plassf_card():
    from afwip.script import GameScript, NodeType
    eng = setup(Side.PRC, [91, 80, 82], prc_sq=(60,))
    eng.state.prc.enablers[80].zone = CardZone.PLAYED
    eng.state.prc.enablers[82].zone = CardZone.PLAYED
    gs = GameScript(eng)
    gen = gs._build_enabler_play(Side.PRC, 91)
    node = next(gen)
    assert node.node_type == NodeType.ENABLER_PICK
    assert {c.value for c in node.choices} == {80, 82}       # only spent PLASSF cards
    try:
        gen.send(next(c for c in node.choices if c.value == 82))
    except StopIteration as e:
        play = e.value
    assert play.target_squadron_id == 82
    eng.play_enabler(Side.PRC, 91, play)
    assert eng.state.prc.enablers[82].zone == CardZone.DECK      # chosen returned
    assert eng.state.prc.enablers[80].zone == CardZone.PLAYED    # other untouched


# --- markers / setup ---------------------------------------------------------

def test_aerial_refueling_deploys_extra_squadron():
    eng = setup(Side.US, [16])
    assert 5 not in eng.state.us.squadrons                 # F-22 squadron not drafted
    eng.play_enabler(Side.US, 16, EnablerPlay(target_squadron_id=5))
    assert eng.state.us.extra_squadron_slots == 1
    assert 5 in eng.state.us.squadrons                     # extra squadron now deployed
    assert eng.state.us.squadrons[5].zone == CardZone.SELECTED


def test_infantry_battalion_shields_squadrons_from_sof():
    # PRC Sea Dragons (95, SOF) strikes the US airbase, but Infantry Battalion
    # protects it -> damage lands on VP boxes, squadrons untouched.
    eng = setup(Side.PRC, [95], us_sq=(10,))
    eng._d4 = lambda: 3
    eng.state.us.squadrons[10].location = BandID.US_AIRBASE
    eng.state.us.squadrons[10].zone = CardZone.ACTIVE
    eng.state.us.infantry_battalions[BandID.US_AIRBASE] = 0
    res = eng.play_enabler(Side.PRC, 95)
    assert res.base_damage == 3
    # "Squadrons on that base may not be attacked by SOF": the Infantry
    # Battalion is the ONLY thing the SOF strike can damage. It soaks its two
    # boxes and dies; the excess is lost rather than spilling to squadrons or
    # VP boxes (user ruling 2026-07-17).
    assert not eng.state.us.squadrons[10].is_destroyed      # squadron shielded
    assert BandID.US_AIRBASE not in eng.state.us.infantry_battalions   # card died
    assert eng.state.us.airbase_vp_damage == 0             # no spill to VP boxes


def test_flying_crew_chief_targets_a_chosen_cl_squadron():
    # (Ruling 2026-07-17) The owner names WHICH Contingency Location squadron
    # generates max aircraft; only un-activated CL squadrons are eligible, and
    # the chosen one skips the D4 generation roll.
    eng = setup(Side.US, [20], us_sq=(10, 5))
    eng.state.us.squadrons[10].location = BandID.US_CONTINGENCY_LOCATION
    assert eng.flying_crew_chief_candidates(Side.US) == [10]   # only the CL card
    with pytest.raises(IllegalAction):                         # 5 sits on the airbase
        eng.play_enabler(Side.US, 20, EnablerPlay(target_squadron_id=5))
    eng.play_enabler(Side.US, 20, EnablerPlay(target_squadron_id=10))
    assert eng.state.us.cl_max_squadron_id == 10

    # The named squadron generates its FULL complement with no roll (a D4 of 1
    # would otherwise ground all but one).
    eng._d4 = lambda: 1
    eng.state.us.reset_turn()
    toks = eng.activate_squadron(Side.US, 10)
    assert len(toks) == TOKEN_REGISTRY[eng.state.us.squadrons[10].token_type].token_count
    assert not any(t.grounded for t in toks)
    assert eng.state.us.cl_max_squadron_id is None             # consumed


def test_munitions_upgrade_range_override():
    eng = setup(Side.PRC, [74])
    eng.play_enabler(Side.PRC, 74, EnablerPlay(target_squadron_id=60))
    assert eng.state.prc.air_range_override[60] == 4


def test_infantry_battalion_is_placed_on_a_chosen_own_base():
    # "Place on any base or contingency location" — the owner picks which of
    # THEIR bases, and the card starts undamaged.
    eng = setup(Side.US, [40])
    assert eng.infantry_battalion_bases(Side.US) == [
        BandID.US_AIRBASE, BandID.US_CONTINGENCY_LOCATION]
    eng.play_enabler(Side.US, 40,
                     EnablerPlay(target_band=BandID.US_CONTINGENCY_LOCATION))
    assert eng.state.us.infantry_battalions == {BandID.US_CONTINGENCY_LOCATION: 0}


def test_infantry_battalion_default_lands_on_an_own_base():
    # Regression: the generic default handed the card the ENEMY airbase, so it
    # protected nothing at all.
    eng = setup(Side.US, [40])
    play = eng._default_enabler_play(Side.US, 40)
    assert play.target_band in eng.infantry_battalion_bases(Side.US)
    eng.play_enabler(Side.US, 40, play)
    assert set(eng.state.us.infantry_battalions) <= set(board.own_base_locations(Side.US))


# --- one-shot buffs ----------------------------------------------------------

def test_forward_observers_auto_hit():
    eng = setup(Side.US, [13])
    gs = eng.state
    gs.us.squadrons[7] = SquadronState(7, Side.US, activated=True, location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    b52 = gs.spawn_token(Side.US, TokenType.B_52, BandID.US_STANDOFF, TokenOrigin.SQUADRON_CARD, source_card_id=7)
    eng.play_enabler(Side.US, 13, response=True)
    assert gs.us.pending_auto_hit
    eng._d4 = lambda: 1  # would miss, but auto-hit forces the hit
    res = eng.shoot_surface(Side.US, b52.uid, target_band=BandID.PRC_AIRBASE)
    assert res.hit and res.hit_roll is None
    assert not gs.us.pending_auto_hit
    # Auto-hit = clean hit: never Winchester, even with a damage roll of 1.
    assert not res.attacker_winchester and not b52.winchester


def test_elite_pilots_pending_advantage_consumed():
    eng = setup(Side.PRC, [69])
    gs = eng.state
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True, location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D, TokenOrigin.SQUADRON_CARD, source_card_id=60)
    us = gs.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_C, TokenOrigin.SQUADRON_CARD, source_card_id=10)
    us.acquired = True
    eng.play_enabler(Side.PRC, 69)
    assert gs.prc.pending_air_advantage
    eng._d4 = lambda: 3
    res = eng.shoot_air(Side.PRC, j10.uid, us.uid)
    assert res.hit_roll.mode.value == "ADVANTAGE"
    assert not gs.prc.pending_air_advantage


# --- cancels (response) ------------------------------------------------------

def test_cancel_base_damage_restores_squadron():
    eng = setup(Side.PRC, [38])  # PRC active attacks; US holds Red Horse
    gs = eng.state
    gs.prc.squadrons[61] = SquadronState(61, Side.PRC, activated=True, location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    h6 = gs.spawn_token(Side.PRC, TokenType.H_6K, BandID.PRC_STANDOFF, TokenOrigin.SQUADRON_CARD, source_card_id=61)
    eng._d4 = lambda: 4  # hit + 4 damage
    eng.shoot_surface(Side.PRC, h6.uid, target_band=BandID.US_AIRBASE, target_squadron_id=10)
    assert gs.us.squadrons[10].is_destroyed
    ok = eng.play_enabler(Side.US, 38, response=True)
    assert ok.cancelled
    assert not gs.us.squadrons[10].is_destroyed and gs.us.squadrons[10].damage == 0


def test_red_horse_cancels_an_unblockable_hypersonic_strike():
    # (FAQ 2026-07-24) "Unblockable" only defeats Missile Defense, not a
    # damage-cancel response. Red Horse (38) still cancels ALL damage from an
    # unblockable Hypersonic Missile (78): the attack hits, but no damage sticks,
    # and the Hypersonic card is still spent.
    gs, eng = _audit_engine(active=Side.PRC)
    gs.prc.enablers[78] = EnablerCardState(78, Side.PRC, zone=CardZone.SELECTED)
    gs.us.enablers[38] = EnablerCardState(38, Side.US, zone=CardZone.SELECTED)
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    eng._d4 = lambda: 3
    res = eng.play_enabler(Side.PRC, 78, EnablerPlay())
    assert res.base_damage == 3                             # unblockable: the attack hits
    assert gs.us.airbase_vp_damage + gs.us.squadrons[10].damage > 0   # damage applied
    eng.play_enabler(Side.US, 38, EnablerPlay(), response=True)
    assert gs.us.airbase_vp_damage == 0                     # all damage cancelled
    assert gs.us.squadrons[10].damage == 0 and not gs.us.squadrons[10].is_destroyed
    assert gs.prc.captures == []                            # kill / captures reversed too
    assert 78 in gs.prc.enablers_played_log                # Hypersonic still spent (it hit)


def test_cancel_air_hit_revives_token():
    eng = setup(Side.PRC, [29])  # US holds Air Launched Decoy
    gs = eng.state
    us = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C, TokenOrigin.SQUADRON_CARD, source_card_id=5)
    us.acquired = True
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True, location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D, TokenOrigin.SQUADRON_CARD, source_card_id=60)
    eng._d4 = lambda: 4
    eng.shoot_air(Side.PRC, j10.uid, us.uid)
    assert gs.get_token(us.uid) is None
    ok = eng.play_enabler(Side.US, 29, response=True)
    assert ok.cancelled and gs.get_token(us.uid) is not None
    assert len(gs.prc.captures) == 0


def test_cancel_card_removes_from_log():
    eng = setup(Side.PRC, [94, 32])  # PRC plays Space Recon; US cancels with Counter Space
    spawn_enemy(eng, Side.PRC, TokenType.F_16C, BandID.BAND_C, n=2)  # US tokens for 94 to acquire
    eng._d4 = lambda: 2
    eng.play_enabler(Side.PRC, 94)
    assert 94 in eng.state.prc.enablers_played_log
    ok = eng.play_enabler(Side.US, 32, response=True)
    assert ok.cancelled and 94 not in eng.state.prc.enablers_played_log


# --- card-by-card audit (user, 2026-07-17) -------------------------------------

def _audit_engine(active=Side.PRC, campaign=3):
    gs = GameState.new_game(campaign=campaign)
    gs.phase = Phase.PLAYER_TURN
    gs.active_side = active
    gs.us.posture_card_id, gs.prc.posture_card_id = 49, 103
    gs.us.mission_card_id, gs.prc.mission_card_id = 51, 105
    return gs, RulesEngine(gs, rng=random.Random(0))


def test_cyber_cancel_of_a_cancel_restores_the_acquire():
    # (User bug 2026-08-10) PRC cyber-acquire -> US Defensive Cyber cancels it
    # -> PRC Defensive Cyber cancels THAT: the tokens must end up acquired after
    # all (cancelling a cyber cancel-card re-applies the acquisition it voided).
    gs, eng = _audit_engine(active=Side.PRC)
    gs.prc.cyber_rate = 1
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    f16 = gs.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=10)
    gs.prc.enablers[83] = EnablerCardState(83, Side.PRC, zone=CardZone.SELECTED)  # Cyber Recon
    gs.us.enablers[23] = EnablerCardState(23, Side.US, zone=CardZone.SELECTED)    # Defensive Cyber
    gs.prc.enablers[82] = EnablerCardState(82, Side.PRC, zone=CardZone.SELECTED)  # Defensive Cyber

    eng.play_enabler(Side.PRC, 83, EnablerPlay(target_uids=[f16.uid]))
    assert f16.acquired
    eng.play_enabler(Side.US, 23, EnablerPlay(choice="cancel"), response=True)
    assert not f16.acquired                               # US cancel voids the acquire
    eng.play_enabler(Side.PRC, 82, EnablerPlay(choice="cancel"), response=True)
    assert f16.acquired                                   # cancel-of-cancel restores it


def test_card_11_ac130_reverses_sof_cyber_gain():
    # AC-130 Gunship Attack "cancels that SOF card" — the PRC's cyber gain from
    # SOF Cyber Infiltration (97) must be given back, not merely un-logged.
    gs, eng = _audit_engine()
    gs.prc.enablers[97] = EnablerCardState(97, Side.PRC, zone=CardZone.SELECTED)
    gs.us.enablers[11] = EnablerCardState(11, Side.US, zone=CardZone.SELECTED)
    before = gs.prc.cyber_rate
    eng._d4 = lambda: 4
    eng.play_enabler(Side.PRC, 97, EnablerPlay())
    assert gs.prc.cyber_rate > before                      # SOF card worked
    eng.play_enabler(Side.US, 11, EnablerPlay(), response=True)
    assert gs.prc.cyber_rate == before                     # ...and was undone


def test_card_11_ac130_reverses_sof_strike():
    # Cancelling Sea Dragons Strike (95) must rewind its base damage. Sea Dragons
    # names the "Airbase", so (FAQ 2026-07-24) its damage lands on the 3 VP boxes;
    # the cancel gives those boxes back.
    gs, eng = _audit_engine()
    gs.prc.enablers[95] = EnablerCardState(95, Side.PRC, zone=CardZone.SELECTED)
    gs.us.enablers[11] = EnablerCardState(11, Side.US, zone=CardZone.SELECTED)
    eng._d4 = lambda: 3
    eng.play_enabler(Side.PRC, 95, EnablerPlay(target_band=BandID.US_AIRBASE))
    assert gs.us.airbase_vp_damage == 3                    # strike hit the VP boxes
    eng.play_enabler(Side.US, 11, EnablerPlay(), response=True)
    assert gs.us.airbase_vp_damage == 0                    # fully reversed


def test_cancel_card_only_voids_its_named_card_type():
    # A cancel card may only void the type its text names: AC-130 (SOF) must
    # not reverse a CYBER-class card.
    gs, eng = _audit_engine()
    gs.prc.enablers[80] = EnablerCardState(80, Side.PRC, zone=CardZone.SELECTED)  # CYBER
    gs.us.enablers[11] = EnablerCardState(11, Side.US, zone=CardZone.SELECTED)
    eng._d4 = lambda: 4
    eng.play_enabler(Side.PRC, 80, EnablerPlay())
    raised = gs.prc.cyber_rate
    eng.play_enabler(Side.US, 11, EnablerPlay(), response=True)
    assert gs.prc.cyber_rate == raised                     # untouched


def test_card_12_personnel_recovery_returns_winchester_aircraft():
    # Personnel Recovery: "Recover aircraft in US band 1. It does not count as
    # destroyed." A Winchester aircraft comes back rearmed in BAND_A.
    gs, eng = _audit_engine(active=Side.PRC)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=60)
    f22 = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=5)
    f22.acquired = True
    f22.winchester = True
    gs.us.enablers[12] = EnablerCardState(12, Side.US, zone=CardZone.SELECTED)
    eng._d4 = lambda: 4
    assert eng.shoot_air(Side.PRC, j10.uid, f22.uid).hit
    assert len(gs.prc.captures) == 1
    # Drive it exactly as the UI does — through _default_enabler_play. Passing a
    # bare EnablerPlay() here hid a real bug: the generic default handed the card
    # the OPPONENT's token uids, so it silently recovered nothing.
    play = eng._default_enabler_play(Side.US, 12)
    assert play.target_uids == [f22.uid]                   # own lost aircraft
    eng.play_enabler(Side.US, 12, play, response=True)
    assert f22.uid in gs.us.tokens                         # recovered
    assert f22.location == BandID.BAND_A                   # US band 1
    assert not f22.is_winchester                           # rearmed
    assert not gs.us.squadrons[5].tokens_lost              # loss refunded
    assert gs.prc.captures == []                           # does not count as destroyed


def test_card_16_aerial_refueling_offers_a_squadron_choice():
    # "Place ONE squadron card in addition to the Posture limit" — the owner
    # picks which; the engine must offer every undrafted campaign-legal card.
    gs, eng = _audit_engine(active=Side.US, campaign=2)
    cands = eng.aerial_refuel_candidates(Side.US)
    assert len(cands) > 1                                  # a real choice
    assert all(SQUADRON_REGISTRY[c].side == Side.US for c in cands)
    chosen = cands[-1]                                     # not the auto-pick
    gs.us.enablers[16] = EnablerCardState(16, Side.US, zone=CardZone.SELECTED)
    eng.play_enabler(Side.US, 16, EnablerPlay(target_squadron_id=chosen))
    assert chosen in gs.us.squadrons                       # placed on the airbase
    assert gs.us.squadrons[chosen].location == BandID.US_AIRBASE
    assert gs.us.squadrons[chosen].zone == CardZone.SELECTED   # ready to generate
    assert chosen not in eng.aerial_refuel_candidates(Side.US)  # no longer offered


def test_card_23_defensive_cyber_branch_is_forced_by_context():
    # (Ruling 2026-07-17) Defensive Cyber's branch is context-fixed, not chosen:
    # CANCEL only as a response to the PRC's cyber card, DEGRADE on the owner's
    # own turn. No ENABLER_BRANCH node is offered for it.
    from afwip.core.enablers import DEFENSIVE_CYBER_CARDS, ENABLER_CHOICE_BRANCHES
    assert 23 in DEFENSIVE_CYBER_CARDS and 82 in DEFENSIVE_CYBER_CARDS
    assert 23 not in ENABLER_CHOICE_BRANCHES and 82 not in ENABLER_CHOICE_BRANCHES

    # Own turn -> DEGRADE the PRC cyber rate by 1.
    gs, eng = _audit_engine(active=Side.US)
    gs.us.enablers[23] = EnablerCardState(23, Side.US, zone=CardZone.SELECTED)
    gs.prc.cyber_rate = 3
    eng.play_enabler(Side.US, 23, EnablerPlay(choice="degrade"))
    assert gs.prc.cyber_rate == 2

    # Response -> CANCEL the PRC's just-played cyber card (its gain is undone).
    gs, eng = _audit_engine(active=Side.PRC)
    gs.prc.enablers[80] = EnablerCardState(80, Side.PRC, zone=CardZone.SELECTED)  # CYBER
    gs.us.enablers[23] = EnablerCardState(23, Side.US, zone=CardZone.SELECTED)
    before = gs.prc.cyber_rate
    eng._d4 = lambda: 4
    eng.play_enabler(Side.PRC, 80, EnablerPlay())
    assert gs.prc.cyber_rate > before
    eng.play_enabler(Side.US, 23, EnablerPlay(choice="cancel"), response=True)
    assert gs.prc.cyber_rate == before

    # A cancel with nothing to void aborts without spending the card.
    gs, eng = _audit_engine(active=Side.US)
    gs.us.enablers[23] = EnablerCardState(23, Side.US, zone=CardZone.SELECTED)
    with pytest.raises(IllegalAction):
        eng.play_enabler(Side.US, 23, EnablerPlay(choice="cancel"), response=True)
    assert gs.us.enablers[23].zone == CardZone.SELECTED     # still in hand


def test_card_17_quick_turn_matches_personnel_recovery():
    # (User 2026-07-17) Quick-Turn Mobility works exactly like Personnel
    # Recovery: the owner's just-lost aircraft returns to band 1, rearmed, and
    # the enemy loses the kill. Driven through _default_enabler_play like the UI.
    gs, eng = _audit_engine(active=Side.PRC)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=60)
    gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D,      # enemy tokens alive
                   TokenOrigin.SQUADRON_CARD, source_card_id=60)
    f22 = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=5)
    f22.acquired = True
    f22.winchester = True
    gs.us.enablers[17] = EnablerCardState(17, Side.US, zone=CardZone.SELECTED)
    eng._d4 = lambda: 4
    eng.shoot_air(Side.PRC, j10.uid, f22.uid)
    play = eng._default_enabler_play(Side.US, 17)
    assert play.target_uids == [f22.uid]                 # own jet, not enemy tokens
    eng.play_enabler(Side.US, 17, play, response=True)
    assert f22.uid in gs.us.tokens and f22.location == BandID.BAND_A
    assert not f22.is_winchester and gs.prc.captures == []


def test_card_18_rapid_resupply_is_an_immediate_response_that_voids_scoring():
    # (User 2026-07-17) Rapid Resupply is played the moment one of your cards is
    # discarded; the revived card is no longer destroyed, so the opponent loses
    # its VP (card + everything that went down with it).
    from afwip.core.constants import EnablerTrigger
    gs, eng = _audit_engine(active=Side.US, campaign=2)
    uas = 55                                              # UAS AIR REGIMENT (4 drones)
    full = TOKEN_REGISTRY[SQUADRON_REGISTRY[uas].token_type].token_count
    gs.prc.squadrons[uas] = SquadronState(uas, Side.PRC, activated=False,
                                          location=BandID.PRC_AIRBASE, zone=CardZone.SELECTED)
    gs.prc.enablers[18] = EnablerCardState(18, Side.PRC, zone=CardZone.SELECTED)
    gs.prc.squadrons[uas].damage = 2
    gs.destroy_squadron(Side.PRC, uas, destroyed_by=Side.US, on_ground=True)
    assert eng.total_victory_points(Side.US) == 2 + full  # card + ungenerated drones

    # It is offered only on the card-discarded trigger, and only as a response.
    assert 18 in eng.legal_responses(Side.PRC, {EnablerTrigger.OWN_CARD_DISCARDED})
    assert 18 not in eng.legal_responses(Side.PRC, {EnablerTrigger.OPP_ROLLS_HIT})
    assert eng.rapid_resupply_targets(Side.PRC) == [uas]

    eng.play_enabler(Side.PRC, 18, EnablerPlay(target_squadron_id=uas), response=True)
    assert not gs.prc.squadrons[uas].is_destroyed         # card is back
    assert gs.prc.squadrons[uas].tokens_lost == 0         # and can generate again
    assert eng.total_victory_points(Side.US) == 0         # opponent scores nothing


def test_card_18_fully_restores_a_destroyed_squadron_including_air_kills():
    # (FAQ 2026-07-24) Recovering a destroyed squadron returns it full strength,
    # like the start of the ATO, and the opponent loses ALL points for it — even
    # a drone shot down in the air earlier. Points only count if it is destroyed
    # a SECOND time.
    gs, eng = _audit_engine(active=Side.US, campaign=2)
    uas = 55
    gs.prc.squadrons[uas] = SquadronState(uas, Side.PRC, activated=True,
                                          location=BandID.PRC_AIRBASE,
                                          zone=CardZone.ACTIVE, ever_activated=True)
    flyer = gs.spawn_token(Side.PRC, SQUADRON_REGISTRY[uas].token_type, BandID.BAND_C,
                           TokenOrigin.SQUADRON_CARD, source_card_id=uas)
    gs.destroy_token(flyer.uid, destroyed_by=Side.US, on_ground=False)   # air kill
    assert eng.total_victory_points(Side.US) == 1
    gs.prc.squadrons[uas].damage = 2
    gs.destroy_squadron(Side.PRC, uas, destroyed_by=Side.US, on_ground=True)
    gs.prc.enablers[18] = EnablerCardState(18, Side.PRC, zone=CardZone.SELECTED)
    eng.play_enabler(Side.PRC, 18, EnablerPlay(target_squadron_id=uas), response=True)
    assert eng.total_victory_points(Side.US) == 0            # every point voided
    assert gs.prc.squadrons[uas].tokens_lost == 0           # full complement returns


def test_card_18_recovered_squadron_is_usable_the_same_ato_at_full_strength():
    # (FAQ 2026-07-24) A squadron recovered by Rapid Resupply may be re-activated
    # the same ATO and fields its FULL complement — tokens placed on top like the
    # start of the ATO — with all the opponent's points for it voided.
    gs, eng = _audit_engine(active=Side.US)
    sq = 5                                                # 90th FIGHTER SQUADRON: 4x F-22
    full = TOKEN_REGISTRY[SQUADRON_REGISTRY[sq].token_type].token_count
    gs.us.squadrons[sq] = SquadronState(sq, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE,
                                        ever_activated=True)
    gs.us.enablers[18] = EnablerCardState(18, Side.US, zone=CardZone.SELECTED)
    flyer = gs.spawn_token(Side.US, SQUADRON_REGISTRY[sq].token_type, BandID.BAND_A,
                           TokenOrigin.SQUADRON_CARD, source_card_id=sq)
    gs.destroy_token(flyer.uid, destroyed_by=Side.PRC, on_ground=False)   # air kill
    gs.us.squadrons[sq].damage = 2
    gs.destroy_squadron(Side.US, sq, destroyed_by=Side.PRC, on_ground=True)   # card killed
    assert gs.prc.captures                                # opponent has points for it

    eng.play_enabler(Side.US, 18, EnablerPlay(target_squadron_id=sq), response=True)
    squad = gs.us.squadrons[sq]
    assert not squad.is_destroyed and squad.zone == CardZone.SELECTED
    assert [c for c in gs.prc.captures if c.card_id == sq] == []          # all points voided
    eng._d4 = lambda: 2                                   # reactivation roll succeeds (2-4)
    toks = eng.activate_squadron(Side.US, sq)            # re-activate the same ATO
    assert len(toks) == full                              # full complement returns


def test_card_18_recovered_squadron_breaks_on_a_reactivation_roll_of_one():
    # (FAQ 2026-07-24) Reactivating a recovered squadron rolls a D4; on a 1 every
    # aircraft it would field is "broken" — scored for the opponent as on-ground
    # kills — but the Squadron Card itself is NOT scored, and it leaves play.
    gs, eng = _audit_engine(active=Side.US)
    sq = 5                                                # 90th FIGHTER SQUADRON: 4x F-22
    full = TOKEN_REGISTRY[SQUADRON_REGISTRY[sq].token_type].token_count
    gs.us.squadrons[sq] = SquadronState(sq, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE,
                                        ever_activated=True)
    gs.us.enablers[18] = EnablerCardState(18, Side.US, zone=CardZone.SELECTED)
    gs.us.squadrons[sq].damage = 2
    gs.destroy_squadron(Side.US, sq, destroyed_by=Side.PRC, on_ground=True)
    eng.play_enabler(Side.US, 18, EnablerPlay(target_squadron_id=sq), response=True)
    assert gs.us.squadrons[sq].recovered and gs.prc.captures == []    # recovered, points voided

    eng._d4 = lambda: 1                                   # reactivation fails
    assert eng.activate_squadron(Side.US, sq) == []      # nothing fielded
    caps = gs.prc.captures
    assert len(caps) == full                              # every aircraft scored...
    assert all(c.destroyed_on_ground and not c.is_squadron_card for c in caps)  # ...as ground kills, no card
    assert gs.us.squadrons[sq].is_destroyed              # card removed (destroyed a 2nd time)
    assert eng.score_captures(Side.PRC) == full          # Attrition: +1 per fighter, no +2 card


def test_card_18_recovered_squadron_activates_normally_on_a_roll_above_one():
    # On a 2-4 the recovered squadron activates as normal, at full strength, and
    # the flag clears.
    gs, eng = _audit_engine(active=Side.US)
    sq = 5
    full = TOKEN_REGISTRY[SQUADRON_REGISTRY[sq].token_type].token_count
    gs.us.squadrons[sq] = SquadronState(sq, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE,
                                        ever_activated=True)
    gs.us.enablers[18] = EnablerCardState(18, Side.US, zone=CardZone.SELECTED)
    gs.us.squadrons[sq].damage = 2
    gs.destroy_squadron(Side.US, sq, destroyed_by=Side.PRC, on_ground=True)
    eng.play_enabler(Side.US, 18, EnablerPlay(target_squadron_id=sq), response=True)
    eng._d4 = lambda: 2
    assert len(eng.activate_squadron(Side.US, sq)) == full
    assert not gs.us.squadrons[sq].recovered and gs.prc.captures == []


def test_a_normal_squadron_activation_takes_no_reactivation_roll():
    # Only recovered squadrons roll on reactivation; a never-destroyed squadron
    # activates without any roll even when the D4 would show a 1.
    gs, eng = _audit_engine(active=Side.US)
    sq = 10                                               # 480th FS: 4x F-16C, never destroyed
    full = TOKEN_REGISTRY[SQUADRON_REGISTRY[sq].token_type].token_count
    gs.us.squadrons[sq] = SquadronState(sq, Side.US, activated=False,
                                        location=BandID.US_AIRBASE, zone=CardZone.SELECTED)
    eng._d4 = lambda: 1                                   # would break a recovered squad
    assert len(eng.activate_squadron(Side.US, sq)) == full   # normal squad ignores the roll
    assert gs.prc.captures == []


def test_card_21_cyber_recon_acquires_the_chosen_tokens():
    # (User 2026-07-17) The owner chooses WHICH enemy tokens to acquire, one per
    # point of Cyber Rate — not simply the lowest-uid ones.
    gs, eng = _audit_engine(active=Side.US)
    gs.us.cyber_rate = 2
    for band in (BandID.BAND_B, BandID.BAND_C, BandID.BAND_D):
        gs.spawn_token(Side.PRC, TokenType.J_10, band,
                       TokenOrigin.SQUADRON_CARD, source_card_id=60)
    cands = eng.acquirable_enemy_tokens(Side.US)
    assert len(cands) == 3
    gs.us.enablers[21] = EnablerCardState(21, Side.US, zone=CardZone.SELECTED)
    chosen = [cands[2], cands[0]]                        # deliberately not the first two
    eng.play_enabler(Side.US, 21, EnablerPlay(target_uids=chosen))
    assert sorted(u for u in cands if gs.get_token(u).acquired) == sorted(chosen)
    assert not gs.get_token(cands[1]).acquired           # the unchosen one is untouched


def test_card_24_offensive_cyber_remove_targets_are_the_players_choice():
    # (User 2026-07-17) The "remove" branch destroys enemy tokens the PLAYER
    # picks — not simply the lowest-uid ones.
    gs, eng = _audit_engine(active=Side.US)
    gs.us.cyber_rate = 2
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    toks = [gs.spawn_token(Side.PRC, TokenType.J_10, b,
                           TokenOrigin.SQUADRON_CARD, source_card_id=60).uid
            for b in (BandID.BAND_B, BandID.BAND_C, BandID.BAND_D)]
    gs.us.enablers[24] = EnablerCardState(24, Side.US, zone=CardZone.SELECTED)
    assert eng.removable_enemy_tokens(Side.US) == sorted(toks)
    chosen = [toks[2], toks[0]]                        # deliberately not the first two
    res = eng.play_enabler(Side.US, 24,
                           EnablerPlay(choice="remove", target_uids=chosen))
    assert sorted(res.destroyed) == sorted(chosen)
    assert gs.get_token(toks[1]) is not None            # the unchosen one survives


def test_card_24_offensive_cyber_discard_is_the_victims_choice():
    # The "discard" branch makes the OPPONENT give up cards — and THEY choose
    # which of their own enablers go, not hand order.
    gs, eng = _audit_engine(active=Side.US)
    gs.us.cyber_rate = 2
    gs.us.enablers[24] = EnablerCardState(24, Side.US, zone=CardZone.SELECTED)
    for cid in (65, 66, 67, 68):
        gs.prc.enablers[cid] = EnablerCardState(cid, Side.PRC, zone=CardZone.SELECTED)
    victim_choice = [68, 66]
    res = eng.play_enabler(Side.US, 24,
                           EnablerPlay(choice="discard", discard_card_ids=victim_choice))
    assert sorted(res.discarded) == sorted(victim_choice)
    assert sorted(c.card_id for c in gs.prc.enablers_in_hand()) == [65, 67]


def test_card_25_counter_uas_removes_only_uas():
    # (User 2026-07-17, verify) Counter-UAS removes UAS equal to the Cyber Rate
    # and never touches other token types.
    gs, eng = _audit_engine(active=Side.US)
    gs.us.cyber_rate = 2
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    uas = [gs.spawn_token(Side.PRC, TokenType.ATTACK_UAS_PRC, BandID.BAND_C,
                          TokenOrigin.SQUADRON_CARD, source_card_id=60).uid
           for _ in range(3)]
    fighter = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_C,
                             TokenOrigin.SQUADRON_CARD, source_card_id=60).uid
    gs.us.enablers[25] = EnablerCardState(25, Side.US, zone=CardZone.SELECTED)
    res = eng.play_enabler(Side.US, 25, EnablerPlay())
    assert len(res.destroyed) == 2                                   # = cyber rate
    assert sum(1 for u in uas if gs.get_token(u) is not None) == 1    # one UAS left
    assert gs.get_token(fighter) is not None                         # fighter untouched


def test_response_windows_do_not_fire_on_a_stale_attack():
    # (User report 2026-07-17: Reserves offered in response to an unrelated
    # Defensive EW play.) "Immediately after" response cards must be scoped to
    # the action just resolved — a new own-turn action clears the attack undo.
    gs, eng = _audit_engine(active=Side.US)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.us.squadrons[5] = SquadronState(5, Side.US, activated=True,
                                       location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=60)
    f22 = gs.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=5)
    j10.acquired = True
    eng._d4 = lambda: 4
    eng.shoot_air(Side.US, f22.uid, j10.uid)          # empties PRC squadron 60
    assert eng.reserves_playable(Side.PRC)            # legitimate window, right now

    eng.end_turn(Side.US)
    eng.pass_turn(Side.PRC)
    gs.us.enablers[27] = EnablerCardState(27, Side.US, zone=CardZone.SELECTED)
    eng.play_enabler(Side.US, 27, EnablerPlay())      # unrelated, non-attack card
    assert not eng.reserves_playable(Side.PRC)        # window must be closed now


def test_card_31_space_recon_rolls_then_lets_the_owner_choose():
    # (User 2026-07-17) The D4 sets HOW MANY tokens are acquired; the owner then
    # chooses WHICH. The script rolls before offering the choice and the handler
    # reuses that roll rather than rolling again.
    gs, eng = _audit_engine(active=Side.US)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    toks = [gs.spawn_token(Side.PRC, TokenType.J_10, b,
                           TokenOrigin.SQUADRON_CARD, source_card_id=60).uid
            for b in (BandID.BAND_A, BandID.BAND_B, BandID.BAND_C, BandID.BAND_D)]
    gs.us.enablers[31] = EnablerCardState(31, Side.US, zone=CardZone.SELECTED)
    chosen = [toks[3], toks[1]]                       # deliberately not the first two
    res = eng.play_enabler(Side.US, 31,
                           EnablerPlay(rolled_count=2, target_uids=chosen))
    assert sorted(res.acquired) == sorted(chosen)
    assert not gs.get_token(toks[0]).acquired         # unchosen tokens untouched
    assert not gs.get_token(toks[2]).acquired


def test_roll_acquire_still_rolls_when_no_count_supplied():
    # Back-compat: with no pre-made roll the handler rolls for itself, so the
    # engine stays usable without the script's two-phase flow.
    gs, eng = _audit_engine(active=Side.US)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    for b in (BandID.BAND_A, BandID.BAND_B, BandID.BAND_C, BandID.BAND_D):
        gs.spawn_token(Side.PRC, TokenType.J_10, b,
                       TokenOrigin.SQUADRON_CARD, source_card_id=60)
    gs.us.enablers[31] = EnablerCardState(31, Side.US, zone=CardZone.SELECTED)
    eng._d4 = lambda: 3
    assert len(eng.play_enabler(Side.US, 31, EnablerPlay()).acquired) == 3


def test_card_14_pre_rolled_four_still_grants_the_cyber_bonus():
    # SOF Recon shares the roll-acquire handler: a pre-made natural 4 must still
    # trigger its +1 Cyber, exactly as an internally-rolled 4 would.
    gs, eng = _audit_engine(active=Side.US)
    gs.us.cyber_rate = 1
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    toks = [gs.spawn_token(Side.PRC, TokenType.J_10, b,
                           TokenOrigin.SQUADRON_CARD, source_card_id=60).uid
            for b in (BandID.BAND_A, BandID.BAND_B, BandID.BAND_C, BandID.BAND_D)]
    gs.us.enablers[14] = EnablerCardState(14, Side.US, zone=CardZone.SELECTED)
    res = eng.play_enabler(Side.US, 14,
                           EnablerPlay(rolled_count=4, target_uids=toks))
    assert len(res.acquired) == 4 and res.cyber_delta == 1
    assert gs.us.cyber_rate == 2


def test_card_34_joint_offensive_cyber_targets_are_the_players_choice():
    # (User 2026-07-17) Removes 2x Cyber Rate enemy tokens — the owner picks which.
    gs, eng = _audit_engine(active=Side.US)
    gs.us.cyber_rate = 2                              # up to 4 removals
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    toks = [gs.spawn_token(Side.PRC, TokenType.J_10, b,
                           TokenOrigin.SQUADRON_CARD, source_card_id=60).uid
            for b in (BandID.BAND_A, BandID.BAND_B, BandID.BAND_C, BandID.BAND_D)]
    gs.us.enablers[34] = EnablerCardState(34, Side.US, zone=CardZone.SELECTED)
    kill = [toks[3], toks[0]]                         # fewer than the max, and not in order
    res = eng.play_enabler(Side.US, 34, EnablerPlay(target_uids=kill))
    assert sorted(res.destroyed) == sorted(kill)
    assert gs.get_token(toks[1]) is not None and gs.get_token(toks[2]) is not None


def test_infantry_battalion_soaks_sof_damage_for_squadrons():
    # (User 2026-07-17) A base holding an Infantry Battalion IS attackable by
    # SOF, but the battalion is the only thing that can take damage: it absorbs
    # up to its two boxes and the squadrons are untouched.
    gs, eng = _audit_engine(active=Side.PRC)
    gs.us.infantry_battalions[BandID.US_AIRBASE] = 0
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    eng._strike_base(Side.PRC, BandID.US_AIRBASE, roll_gate=None,
                     bypass_md=True, fixed_damage=1, sof=True)
    assert gs.us.infantry_battalions[BandID.US_AIRBASE] == 1   # one box filled
    assert gs.us.squadrons[10].damage == 0                     # squadron shielded

    eng._strike_base(Side.PRC, BandID.US_AIRBASE, roll_gate=None,
                     bypass_md=True, fixed_damage=1, sof=True)
    assert BandID.US_AIRBASE not in gs.us.infantry_battalions  # second box: destroyed
    assert gs.us.squadrons[10].damage == 0


def test_sof_overkill_does_not_spill_past_the_infantry_battalion():
    # "Squadrons on that base may not be attacked by SOF" — damage beyond the
    # battalion's remaining boxes is lost, never spilling to squadrons or VP.
    gs, eng = _audit_engine(active=Side.PRC)
    gs.us.infantry_battalions[BandID.US_AIRBASE] = 0
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    eng._strike_base(Side.PRC, BandID.US_AIRBASE, roll_gate=None,
                     bypass_md=True, fixed_damage=4, sof=True)
    assert BandID.US_AIRBASE not in gs.us.infantry_battalions
    assert gs.us.squadrons[10].damage == 0            # no spill to the squadron
    assert gs.us.airbase_vp_damage == 0               # and none to the VP boxes


def test_sof_hits_the_vp_boxes_once_the_battalion_is_gone():
    # With no battalion the shield is gone, and a SOF strike — which names the
    # "Airbase" — lands on the VP boxes, never the squadrons (FAQ 2026-07-24).
    gs, eng = _audit_engine(active=Side.PRC)
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    eng._strike_base(Side.PRC, BandID.US_AIRBASE, roll_gate=None,
                     bypass_md=True, fixed_damage=1, sof=True, airbase_only=True)
    assert gs.us.squadrons[10].damage == 0            # squadron never hit
    assert gs.us.airbase_vp_damage == 1               # VP box filled


def test_infantry_battalion_scores_no_points_for_the_attacker():
    # (User ruling 2026-07-17) Damaging or destroying the Infantry Battalion
    # earns the opponent NOTHING — it is not a scoring capture, and SOF damage
    # spent on it must not leak into the airbase VP boxes either.
    gs, eng = _audit_engine(active=Side.PRC)
    gs.us.mission_card_id, gs.prc.mission_card_id = 51, 105      # both Attrition
    gs.us.infantry_battalions[BandID.US_AIRBASE] = 0
    eng._strike_base(Side.PRC, BandID.US_AIRBASE, roll_gate=None,
                     bypass_md=True, fixed_damage=2, sof=True)
    assert BandID.US_AIRBASE not in gs.us.infantry_battalions    # destroyed
    assert gs.prc.captures == []                                 # no capture logged
    assert eng.total_victory_points(Side.PRC) == 0               # and no VP
    assert gs.us.airbase_vp_damage == 0                          # no VP-box leak


def test_infantry_battalion_is_removed_at_end_of_ato():
    # (User ruling 2026-07-17) The placed card lasts the ATO cycle only — unlike
    # squadron and airbase damage, it does NOT carry over.
    gs, eng = _audit_engine(active=Side.PRC)
    gs.us.infantry_battalions[BandID.US_AIRBASE] = 1             # damaged but alive
    eng.end_ato_cycle()
    assert gs.us.infantry_battalions == {}


def test_card_41_himars_fills_only_the_vp_boxes():
    # (FAQ 2026-07-24) HIMARS names the "Airbase": its damage fills only the 3 VP
    # damage boxes and never the Squadron Cards there. There is no player
    # allocation choice — the damage is forced onto the boxes (excess is lost).
    gs, eng = _audit_engine(active=Side.US)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.prc.squadrons[61] = SquadronState(61, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.us.enablers[41] = EnablerCardState(41, Side.US, zone=CardZone.SELECTED)
    eng._d4 = lambda: 3
    eng.play_enabler(Side.US, 41, EnablerPlay(defer_allocation=True))
    assert eng._pending_allocation is None            # no allocation choice
    assert gs.prc.airbase_vp_damage == 3              # all 3 points on the VP boxes
    assert gs.prc.squadrons[60].damage == 0
    assert gs.prc.squadrons[61].damage == 0


def test_card_42_tomahawk_generates_its_ddg_and_fills_vp_boxes():
    # Tomahawk still spawns its DDG, but (FAQ 2026-07-24) its rolled damage lands
    # only on the PRC airbase VP boxes, never on the squadrons there.
    gs, eng = _audit_engine(active=Side.US)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.us.enablers[42] = EnablerCardState(42, Side.US, zone=CardZone.SELECTED)
    eng._d4 = lambda: 3
    res = eng.play_enabler(Side.US, 42,
                           EnablerPlay(spawn_band=BandID.BAND_C, defer_allocation=True))
    assert len(res.tokens) == 1                       # DDG 115 generated
    assert eng._pending_allocation is None            # no allocation choice
    assert gs.prc.airbase_vp_damage == 3
    assert gs.prc.squadrons[60].damage == 0           # nothing forced onto the squadron


def test_engine_only_base_strike_still_applies_damage_immediately():
    # Back-compat: without defer_allocation the engine applies damage itself, so
    # autoplay and direct engine use keep working.
    gs, eng = _audit_engine(active=Side.US)
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    gs.us.enablers[41] = EnablerCardState(41, Side.US, zone=CardZone.SELECTED)
    eng._d4 = lambda: 3
    eng.play_enabler(Side.US, 41, EnablerPlay())
    assert eng._pending_allocation is None
    assert gs.prc.squadrons[60].is_destroyed or gs.prc.airbase_vp_damage > 0


@pytest.mark.parametrize("cid", [43, 44])
def test_ship_kill_cards_sink_the_chosen_vessel(cid):
    # (User 2026-07-17) Submarine Strike / Marine Littoral auto-hit — the owner
    # chooses WHICH enemy surface combatant, not simply the first on the board.
    gs, eng = _audit_engine(active=Side.US)
    ships = [gs.spawn_token(Side.PRC, t, BandID.BAND_C, TokenOrigin.ENABLER_CARD).uid
             for t in (TokenType.NANNING_162, TokenType.DALIAN_105, TokenType.FLOTILLA)]
    gs.us.enablers[cid] = EnablerCardState(cid, Side.US, zone=CardZone.SELECTED)
    assert eng.enemy_ship_targets(Side.US) == sorted(ships)
    chosen = ships[2]                                  # deliberately not the first
    res = eng.play_enabler(Side.US, cid,
                           EnablerPlay(choice="attack", target_uids=[chosen]))
    assert res.destroyed == [chosen]
    assert all(gs.get_token(u) is not None for u in ships[:2])   # others survive


def test_air_launched_decoy_window_precedes_damage_allocation():
    # Air Launched Decoy cancels the HIT before the attacker allocates base
    # damage: the defender decides WITHOUT seeing the damage / allocation, and a
    # cancel voids the pending allocation (no ALLOC_POINT nodes, no damage).
    from afwip.core.rules import LegalAction
    from afwip.script import GameScript, NodeType

    def _setup():
        gs = GameState.new_game(campaign=3)
        gs.phase = Phase.PLAYER_TURN
        gs.active_side = Side.PRC
        gs.turn_number = 1
        eng = RulesEngine(gs, rng=random.Random(1))
        eng._d4 = lambda: 3
        gs.prc.squadrons[61] = SquadronState(61, Side.PRC, activated=True,
                                             location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
        h6 = gs.spawn_token(Side.PRC, TokenType.H_6K, BandID.PRC_STANDOFF,
                            TokenOrigin.SQUADRON_CARD, source_card_id=61)
        gs.us.squadrons[8] = SquadronState(8, Side.US, activated=True,
                                           location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
        gs.us.enablers[29] = EnablerCardState(29, Side.US, zone=CardZone.SELECTED)  # ALD
        return gs, eng, h6

    def _drive(play_ald):
        gs, eng, h6 = _setup()
        action = LegalAction("shoot_surface", token_uid=h6.uid,
                             target_band=BandID.US_AIRBASE)
        gen = GameScript(eng)._shoot_surface(Side.PRC, action)
        order, node = [], next(gen)
        while True:
            order.append(node.node_type.name)
            if node.node_type == NodeType.RESPONSE and play_ald \
                    and any(c.card_id == 29 for c in node.choices):
                pick = next(c for c in node.choices if c.card_id == 29)
            else:
                pick = node.choices[0]
            try:
                node = gen.send(pick)
            except StopIteration:
                break
        return order, gs

    order, gs = _drive(play_ald=False)
    assert order.index("RESPONSE") < order.index("ALLOC_POINT")     # ALD before allocation
    assert gs.us.airbase_vp_damage + gs.us.squadrons[8].damage > 0  # damage applied

    order2, gs2 = _drive(play_ald=True)
    assert "ALLOC_POINT" not in order2                              # cancelled before allocation
    assert gs2.us.airbase_vp_damage == 0 and gs2.us.squadrons[8].damage == 0


def test_air_launched_decoy_offered_and_cancels_token_kills():
    # ALD must be offered against TOKEN kills too (air-to-air and surface), not
    # only base strikes — and cancelling revives the destroyed token.
    from afwip.core.rules import LegalAction
    from afwip.script import GameScript, NodeType

    def _drive(eng, gen, play_ald):
        order, node = [], next(gen)
        while True:
            order.append(node.node_type.name)
            if node.node_type == NodeType.RESPONSE and play_ald \
                    and any(c.card_id == 29 for c in node.choices):
                pick = next(c for c in node.choices if c.card_id == 29)
            else:
                pick = node.choices[0]
            try:
                node = gen.send(pick)
            except StopIteration:
                break
        return order

    def _base():
        gs = GameState.new_game(campaign=3)
        gs.phase = Phase.PLAYER_TURN
        gs.active_side = Side.PRC
        gs.turn_number = 1
        eng = RulesEngine(gs, rng=random.Random(1))
        eng._d4 = lambda: 4
        gs.us.enablers[29] = EnablerCardState(29, Side.US, zone=CardZone.SELECTED)  # ALD
        return gs, eng

    # Air-to-air: PRC J-10 downs an acquired US F-16C.
    for play_ald in (False, True):
        gs, eng = _base()
        gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                             location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
        j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_C,
                             TokenOrigin.SQUADRON_CARD, source_card_id=60)
        gs.us.squadrons[3] = SquadronState(3, Side.US, activated=True,
                                           location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
        f16 = gs.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_C,
                             TokenOrigin.SQUADRON_CARD, source_card_id=3)
        f16.acquired = True
        order = _drive(eng, GameScript(eng)._shoot_air(
            Side.PRC, LegalAction("shoot_air", token_uid=j10.uid, target_uid=f16.uid)), play_ald)
        assert "RESPONSE" in order                              # ALD offered
        assert (gs.get_token(f16.uid) is not None) == play_ald  # revived iff ALD played

    # Surface token: PRC Nanning sinks an acquired US DDG.
    for play_ald in (False, True):
        gs, eng = _base()
        nan = gs.spawn_token(Side.PRC, TokenType.NANNING_162, BandID.BAND_C,
                             TokenOrigin.ENABLER_CARD, source_card_id=87)
        ddg = gs.spawn_token(Side.US, TokenType.DDG_115, BandID.BAND_C,
                             TokenOrigin.ENABLER_CARD, source_card_id=37)
        ddg.acquired = True
        order = _drive(eng, GameScript(eng)._shoot_surface(
            Side.PRC, LegalAction("shoot_surface", token_uid=nan.uid, target_uid=ddg.uid)), play_ald)
        assert "RESPONSE" in order                              # ALD offered
        assert (gs.get_token(ddg.uid) is not None) == play_ald  # revived iff ALD played
