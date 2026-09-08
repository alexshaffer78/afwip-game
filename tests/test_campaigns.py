"""Setup-legality enforcement, legal_actions enumeration, and autoplay smoke."""

import random

import pytest

from afwip.core.rules import RulesEngine, IllegalAction
from afwip.core.state import GameState
from afwip.core.constants import Side, BandID, TokenType, TokenOrigin, Phase
from afwip.harness import autoplay_game
from tests.helpers import draft_enablers, draft_squadrons


# --- setup-legality enforcement ---------------------------------------------

def test_campaign1_mission_restricted_to_attrition():
    eng = RulesEngine(GameState.new_game(campaign=1))
    eng.setup_missions(51, 105)                 # Attrition ok
    with pytest.raises(IllegalAction):
        eng.setup_missions(52, 106)             # Interdiction banned


def test_campaign1_requires_forced_squadron_and_bans_enablers():
    # Campaign 1: normal Standard-posture squadron draft, but the forced card
    # (US F-16 #10 / PRC J-10 #60) must be INCLUDED; no enablers.
    eng = RulesEngine(GameState.new_game(campaign=1))
    eng.setup_missions(51, 105)
    with pytest.raises(IllegalAction):
        eng.select_posture(Side.US, 49, [5, 8, 9], [])     # roster without F-16 (10)
    with pytest.raises(IllegalAction):
        eng.select_posture(Side.US, 49, [10], [])          # includes F-16 but too few (near-max 3)
    with pytest.raises(IllegalAction):
        eng.select_posture(Side.US, 49, [10, 5, 8], [11])  # enablers not used in campaign 1
    eng.select_posture(Side.US, 49, [10, 5, 8], [])        # F-16 + a normal roster: ok
    assert set(eng.state.us.squadrons) == {10, 5, 8}
    # PRC must include the J-10 squadron (60).
    with pytest.raises(IllegalAction):
        eng.select_posture(Side.PRC, 103, [61, 62, 63], [])  # roster without J-10
    eng.select_posture(Side.PRC, 103, [60, 61, 62], [])
    assert 60 in eng.state.prc.squadrons


def test_campaign5_bans_fifth_gen_bomber_and_long_range_ada():
    eng = RulesEngine(GameState.new_game(campaign=5))
    eng.setup_missions(51, 105)
    for banned in ([5], [2], [59]):   # F-22, B-52, Long-Range ADA squadrons
        with pytest.raises(IllegalAction):
            eng.select_posture(Side.US, 49, banned, []) if banned != [59] \
                else eng.select_posture(Side.PRC, 103, banned, [])
    # F-16 + a full hand including the refuel enabler is fine.
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (10,), camp=eng.campaign),
                       draft_enablers(Side.US, [16], camp=eng.campaign))


def test_campaign4_bans_missile_sof_enablers_and_long_range_bombers():
    eng = RulesEngine(GameState.new_game(campaign=4))
    eng.setup_missions(51, 105)
    with pytest.raises(IllegalAction):
        eng.select_posture(Side.PRC, 103, [60], [78])  # Hypersonic (MISSILE) banned
    with pytest.raises(IllegalAction):
        eng.select_posture(Side.US, 49, [2], [])       # B-52 long-range bomber banned
    # A full hand including Cyber Recon (from the campaign-legal pool) is fine.
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (10,), camp=eng.campaign),
                       draft_enablers(Side.US, [21], camp=eng.campaign))


def test_posture_card_count_limits():
    eng = RulesEngine(GameState.new_game(campaign=3))
    eng.setup_missions(51, 105)
    with pytest.raises(IllegalAction):
        eng.select_posture(Side.US, 49, [5, 6, 8, 9, 10], [])  # 5 > Standard limit 4
    with pytest.raises(IllegalAction):
        eng.select_posture(Side.US, 49, [10], [11, 12, 13, 14, 15, 16, 17])  # 7 > limit 6


def test_ada_posture_bonus_slots_only_absorb_ada():
    # PRC ADA posture (101): base 4 squadrons + 2 ADA-only bonus slots.
    # ADA squadrons = 56 (Mid), 59 (Long); others are fighters/bomber.
    eng = RulesEngine(GameState.new_game(campaign=3))
    eng.setup_missions(51, 105)
    eng.select_posture(Side.PRC, 101, [60, 62, 63, 64, 56, 59],
                       draft_enablers(Side.PRC))   # 4 fighters + 2 ADA: OK
    with pytest.raises(IllegalAction):
        eng.select_posture(Side.PRC, 101, [60, 62, 63, 64, 61, 64], [])  # 6 non-ADA: illegal
    with pytest.raises(IllegalAction):
        eng.select_posture(Side.PRC, 101, [60, 62, 63, 64, 61, 56], [])  # 5 general + 1 ADA: illegal


def test_standoff_bomber_bonus_only_absorbs_bombers():
    # US Standoff (48): base 3 + both B-52 cards (2, 7) free.
    eng = RulesEngine(GameState.new_game(campaign=3))
    eng.setup_missions(51, 105)
    eng.select_posture(Side.US, 48, [5, 6, 8, 2, 7],
                       draft_enablers(Side.US))   # 3 fighters + 2 B-52: OK
    with pytest.raises(IllegalAction):
        eng.select_posture(Side.US, 48, [5, 6, 8, 9, 10], [])  # 5 fighters: illegal


# --- legal_actions / apply_action -------------------------------------------

def _started(campaign=3, seed=0):
    eng = RulesEngine(GameState.new_game(campaign=campaign), rng=random.Random(seed))
    eng.setup_missions(51, 105)
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (5, 10)), draft_enablers(Side.US, [31]))
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, (60,)), draft_enablers(Side.PRC))
    eng.bid_for_initiative(first_player=Side.US)
    eng.play_intel()
    eng.begin_player_turns()
    return eng


def test_legal_actions_enumerates_and_masks_off_turn():
    eng = _started()
    eng.state.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C, TokenOrigin.SQUADRON_CARD, source_card_id=5)
    eng.state.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D, TokenOrigin.SQUADRON_CARD, source_card_id=60)
    acts = eng.legal_actions(Side.US)
    kinds = {a.kind for a in acts}
    assert "pass" in kinds and "activate" in kinds and "move" in kinds and "acquire" in kinds
    assert eng.legal_actions(Side.PRC) == []          # not PRC's turn


def test_apply_action_executes_move():
    eng = _started()
    tok = eng.state.spawn_token(Side.US, TokenType.F_22, BandID.BAND_C, TokenOrigin.SQUADRON_CARD, source_card_id=5)
    move = next(a for a in eng.legal_actions(Side.US) if a.kind == "move")
    eng.apply_action(move)
    assert eng.state.get_token(move.token_uid).location == move.dest_band


# --- autoplay smoke ----------------------------------------------------------

def test_campaign2_initiative_alternates_no_rebid():
    from afwip.core.state import CardZone
    eng = RulesEngine(GameState.new_game(campaign=2), rng=random.Random(0))
    eng.setup_missions(51, 105)
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (10,)), draft_enablers(Side.US))
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, (60,)), draft_enablers(Side.PRC))
    w1 = eng.bid_for_initiative()
    eng.state.ato_cycle = 2                    # advance to ATO 2
    w2 = eng.bid_for_initiative()
    assert w2 != w1                            # initiative passes to the other side


def test_campaign4_initiative_goes_to_the_side_that_lost_more_tokens():
    from afwip.core.state import CaptureRecord
    from afwip.core.constants import TokenScoreType
    eng = RulesEngine(GameState.new_game(campaign=4), rng=random.Random(0))
    eng.setup_missions(51, 105)
    # us.captures = US tokens the PRC destroyed (US's OWN losses); vice versa.
    eng.state.us.captures = [CaptureRecord(1, False, False, score_type=TokenScoreType.FIGHTER)]      # PRC lost 1
    eng.state.prc.captures = [CaptureRecord(1, False, False, score_type=TokenScoreType.FIGHTER) for _ in range(3)]  # US lost 3
    eng.state.ato_cycle = 2
    # The US lost more of its own tokens in ATO 1, so it gets ATO-2 initiative
    # (a shift in international opinion toward the side taking losses).
    assert eng.bid_for_initiative() == Side.US


@pytest.mark.parametrize("campaign", [1, 2, 3, 4, 5])
def test_autoplay_runs_clean(campaign):
    rng = random.Random(campaign)
    for _ in range(6):
        out = autoplay_game(campaign, rng, max_turns=1500)
        assert out.winner != "ERROR", out.error
        assert out.winner != "CAPPED"               # games terminate naturally


@pytest.mark.parametrize("campaign", [1, 2, 3, 4, 5])
def test_autoplay_no_voluntary_pass_is_crash_free(campaign):
    """
    With pass_prob=0 agents pass only when forced, so games play out deeply
    instead of ending on early random double-passes. Capping is expected here
    (a mobile token can always move); we only require no crashes.
    """
    rng = random.Random(100 + campaign)
    for _ in range(4):
        out = autoplay_game(campaign, rng, pass_prob=0.0, max_turns=400)
        assert out.winner != "ERROR", out.error
