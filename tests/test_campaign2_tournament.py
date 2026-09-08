"""
Campaign 2 (Tournament) — the RL MVP target — tested thoroughly:
mission/posture restrictions, the no-sacrifice bid, the ATO-2 initiative flip
(no re-bid, no cyber-raise reward), intel advantage following the initiative
holder (with an actual advantage roll), and full env games staying clean.
"""

import random

import numpy as np
import pytest

from afwip.core.rules import RulesEngine, IllegalAction, RollMode
from afwip.core.state import GameState, CardZone
from afwip.core.cards import MISSION_REGISTRY, POSTURE_REGISTRY
from afwip.core.constants import (
    Side, IntelTrack, MissionType, PostureType, CAMPAIGN_ATO_CYCLES,
)
from afwip.core import board
from afwip.env import AFWIPEnv
from tests.helpers import draft_enablers, draft_squadrons


def _drafted(seed=0):
    eng = RulesEngine(GameState.new_game(campaign=2), rng=random.Random(seed))
    eng.setup_missions(51, 105)                    # both Attrition
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (10,)), draft_enablers(Side.US))
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, (60,)), draft_enablers(Side.PRC))
    return eng


def test_c2_has_two_ato_cycles():
    assert CAMPAIGN_ATO_CYCLES[2] == 2
    assert GameState.new_game(campaign=2).total_ato_cycles == 2


def test_c2_missions_restricted_to_attrition():
    eng = RulesEngine(GameState.new_game(campaign=2))
    assert eng.campaign.mission_allowed(MissionType.ATTRITION)
    for mt in MissionType:
        if mt != MissionType.ATTRITION:
            assert not eng.campaign.mission_allowed(mt)
    us_non_attrition = next(cid for cid, m in MISSION_REGISTRY.items()
                            if m.side == Side.US and m.mission_type != MissionType.ATTRITION)
    with pytest.raises(IllegalAction):
        eng.setup_missions(us_non_attrition, 105)


def test_c2_postures_restricted_to_standard_and_repeatable():
    eng = _drafted()
    non_standard = next(cid for cid, p in POSTURE_REGISTRY.items()
                        if p.side == Side.US and p.posture_type != PostureType.STANDARD)
    with pytest.raises(IllegalAction):
        eng.select_posture(Side.US, non_standard, [10], draft_enablers(Side.US))
    # Standard is exempt from the no-repeat rule: cycle 2 re-selects it and
    # re-drafts squadrons + enablers (ruling 2026-07-22).
    eng.bid_for_initiative(first_player=Side.US)
    eng.play_intel()
    eng.begin_player_turns()
    eng.pass_turn(Side.US)
    eng.pass_turn(eng.state.active_side)           # double pass ends ATO 1
    assert eng.state.ato_cycle == 2
    eng.select_posture_only(Side.US, 49)           # convenience auto-draft: no raise
    # A full re-draft in a later cycle is now legal (squadrons are re-drafted).
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (10,)), draft_enablers(Side.US))
    assert eng.state.us.squadrons[10].zone == CardZone.SELECTED


def test_c2_bid_sacrifices_forbidden():
    eng = _drafted()
    hand = [c.card_id for c in eng.state.us.enablers_in_hand()]
    with pytest.raises(IllegalAction):
        eng.bid_for_initiative(us_sacrifice=hand[:1])


def test_c2_ato2_initiative_flips_without_reroll_or_cyber_raise():
    eng = _drafted(seed=0)
    w1 = eng.bid_for_initiative()
    cyber_after_bid1 = {s: eng.state.player(s).cyber_rate for s in Side}

    eng.state.ato_cycle = 2
    eng._d4 = lambda: 4        # if ATO 2 attempted any bid/raise roll, it would succeed
    w2 = eng.bid_for_initiative()
    assert w2 == board.opponent(w1)                # initiative flips to the non-holder
    for s in Side:                                 # no cyber-raise reward on auto-assign
        assert eng.state.player(s).cyber_rate == cyber_after_bid1[s]


def test_c2_intel_advantage_follows_initiative_holder():
    eng = _drafted(seed=0)
    w1 = eng.bid_for_initiative()
    assert eng.state.player(w1).intel_track == IntelTrack.ADVANTAGE
    assert eng.state.player(board.opponent(w1)).intel_track == IntelTrack.NORMAL

    eng.state.ato_cycle = 2
    w2 = eng.bid_for_initiative()
    assert eng.state.player(w2).intel_track == IntelTrack.ADVANTAGE
    assert eng.state.player(board.opponent(w2)).intel_track == IntelTrack.NORMAL


def test_c2_intel_roll_uses_advantage_for_holder():
    eng = _drafted(seed=0)
    winner = eng.bid_for_initiative()
    modes = []
    orig_roll = eng.roll
    eng.roll = lambda mode=RollMode.NORMAL, bonus=0, note=None: (modes.append(mode), orig_roll(mode, bonus))[1]
    eng.play_intel_roll()
    # play_intel_roll rolls for viewers in (US, PRC) order.
    expected = [RollMode.ADVANTAGE if v == winner else RollMode.NORMAL
                for v in (Side.US, Side.PRC)]
    assert modes == expected


def test_intel_roll_every_cycle_all_campaigns():
    """Play Intel is part of EVERY ATO cycle's setup in EVERY campaign: both
    players roll a D4 (initiative holder at advantage) and the reveal count is
    min(roll, hand-1) — at least one opposing card always stays hidden."""
    from afwip.harness import auto_draft

    for campaign in (1, 2, 3, 4, 5):
        eng = RulesEngine(GameState.new_game(campaign=campaign),
                          rng=random.Random(campaign))
        for cycle in range(1, eng.state.total_ato_cycles + 1):
            auto_draft(eng, random.Random(cycle))
            eng.bid_for_initiative()
            if eng.state.game_over:      # cyber win off the bid raise
                break
            holder = eng.state.initiative_holder
            counts = eng.play_intel_roll()
            assert set(counts) == {Side.US, Side.PRC}, f"C{campaign} cycle {cycle}"
            for viewer in (Side.US, Side.PRC):
                roll = eng.last_intel_rolls[viewer]
                expected_mode = RollMode.ADVANTAGE if viewer == holder else RollMode.NORMAL
                assert roll.mode == expected_mode, f"C{campaign} cycle {cycle}"
                assert 1 <= roll.value <= 4 or roll.mode != RollMode.NORMAL
                owner = board.opponent(viewer)
                hand = len(eng.state.player(owner).enablers_in_hand())
                assert counts[owner] == max(0, min(roll.value, hand - 1)), \
                    f"C{campaign} cycle {cycle}: reveal count wrong"
            for owner in (Side.US, Side.PRC):
                hand_ids = [c.card_id for c in eng.state.player(owner).enablers_in_hand()]
                eng.play_intel_reveal(owner, hand_ids[:counts[owner]])
            eng.begin_player_turns()
            eng.pass_turn(eng.state.active_side)
            if not eng.state.game_over:
                eng.pass_turn(eng.state.active_side)   # double pass -> next cycle


def test_c2_full_env_games_clean():
    """Complete C2 env games: exactly 2 cycles, never a BID_SACRIFICE node,
    FIRST_PLAYER always chosen by the current initiative holder, valid
    zero-sum terminal rewards."""
    for seed in (1, 2, 3, 4):
        env = AFWIPEnv(campaign=2)
        env.reset(seed=seed)
        rng = random.Random(seed)
        first_player_nodes = 0
        terminal = {}
        for agent in env.agent_iter():
            obs, reward, term, trunc, info = env.last()
            if term or trunc:
                terminal[agent] = reward
                env.step(None)
                continue
            assert info["node"] != "BID_SACRIFICE", "Tournament must not offer sacrifices"
            if info["node"] == "FIRST_PLAYER":
                first_player_nodes += 1
                assert agent == env.engine.state.initiative_holder.value
            env.step(int(rng.choice(np.flatnonzero(obs["action_mask"]))))
        eng = env.engine
        assert eng.state.game_over
        cyber_win = max(eng.state.us.cyber_rate, eng.state.prc.cyber_rate) >= 4
        if not cyber_win:                     # cyber wins may end the game early
            assert eng.state.ato_cycle == 2   # otherwise both cycles were played
        assert first_player_nodes >= 1
        assert terminal["US"] + terminal["PRC"] == pytest.approx(0.0)
        assert abs(terminal["US"]) in (0.0, 1.0)
