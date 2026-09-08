"""
PettingZoo environment tests: API compliance, full-decision-surface random
rollouts across all campaigns, seed determinism, fog-of-war observation
masking, node coverage, and the engine's two-phase intel / deferred
base-allocation APIs the env is built on.
"""

import random

import numpy as np
import pytest
from pettingzoo.test import api_test

from afwip.env import (
    AFWIPEnv, NodeType, MAX_TOKENS, N_TT, N_BANDS, N_SCORE, N_PHASE, N_ROLL_CTX,
    POSTURE_SCALAR_OFFSET, MISSION_SCALAR_OFFSET, CAPTURES_SCALAR_OFFSET,
    SCALAR_OFF, POSTURE_SLOT_W, ROLL_SUMMARY_CONTEXTS, PHASE_IDX,
    SQUADRON_SLOTS,
)
from afwip.harness import auto_draft
from afwip.core.rules import RulesEngine, IllegalAction
from afwip.core.state import GameState, SquadronState, CardZone
from afwip.core.cards import SQUADRON_REGISTRY
from afwip.core.constants import (
    Side, Phase, BandID, TokenType, TokenOrigin, DAMAGE_TO_DESTROY_SQUADRON,
)
from afwip.core.tokens import TOKEN_REGISTRY
from afwip.core import board


def _random_game(campaign, seed, reveal=False, vp_shaping=0.0, on_obs=None):
    """Play one full random-policy game; returns (env, terminal_rewards, steps, trace)."""
    env = AFWIPEnv(campaign=campaign, reveal=reveal, vp_shaping=vp_shaping)
    env.reset(seed=seed)
    rng = random.Random(seed)
    terminal, trace, steps = {}, [], 0
    for agent in env.agent_iter():
        obs, reward, term, trunc, info = env.last()
        if term or trunc:
            terminal[agent] = reward
            env.step(None)
            continue
        legal = np.flatnonzero(obs["action_mask"])
        assert legal.size > 0, "live agent presented with an empty action mask"
        assert legal.size == info["num_choices"]
        if on_obs is not None:
            on_obs(env, agent, obs, info)
        action = int(rng.choice(legal))
        trace.append((agent, info["node"], int(legal.size), action))
        env.step(action)
        steps += 1
    return env, terminal, steps, trace


def test_api_compliance():
    api_test(AFWIPEnv(campaign=3), num_cycles=1500, verbose_progress=False)


def test_timed_turn_cap_ends_game_by_vp():
    """A timed game ends the instant the turn cap is reached: game_over is set,
    the leader on VP wins (tie -> draw), and terminal rewards are zero-sum ±1 —
    a real win/loss, never a draw-truncation."""
    for seed in range(12):
        env, terminal, _, _ = _random_game(2, seed=seed)  # default max_turns=150
        gs = env.engine.state
        assert gs.game_over
        assert gs.total_turns <= env.max_turns
        us_vp = env.engine.total_victory_points(Side.US)
        prc_vp = env.engine.total_victory_points(Side.PRC)
        # If the cap bit exactly, the winner is decided by VP at that moment.
        if gs.total_turns == env.max_turns and gs.winner is not None:
            assert gs.winner == (Side.US if us_vp > prc_vp else Side.PRC)
        assert terminal["US"] + terminal["PRC"] == pytest.approx(0.0)
        assert abs(terminal["US"]) in (0.0, 1.0)

    # A tight cap forces the cap to bite on essentially every game.
    capped = 0
    for seed in range(8):
        env = AFWIPEnv(campaign=2, max_turns=12)
        env.reset(seed=seed)
        rng = random.Random(seed)
        for agent in env.agent_iter():
            obs, r, term, trunc, info = env.last()
            if term or trunc:
                env.step(None)
                continue
            env.step(int(rng.choice(np.flatnonzero(obs["action_mask"]))))
        gs = env.engine.state
        assert gs.game_over and gs.total_turns <= 12
        if gs.total_turns == 12:
            capped += 1
    assert capped > 0, "tight cap never triggered"


def test_uncapped_engine_state_has_no_cap():
    """Direct-engine games (harness / TUI) stay uncapped by default; only the
    env opts into the timed cap (default 150)."""
    from afwip.core.state import GameState
    assert GameState.new_game(campaign=2).max_turns is None
    assert AFWIPEnv(campaign=2).max_turns == 150


def test_timed_progress_scalar_is_monotonic_and_bounded():
    """The timed_progress scalar tracks total_turns/max_turns in [0, 1] and only
    increases as the game advances toward the deadline."""
    off = SCALAR_OFF["timed_progress"]
    env = AFWIPEnv(campaign=2, max_turns=40)
    env.reset(seed=1)
    rng = random.Random(1)
    last = -1.0
    for agent in env.agent_iter():
        obs, r, term, trunc, info = env.last()
        if term or trunc:
            env.step(None)
            continue
        p = float(obs["observation"]["scalars"][off])
        assert 0.0 <= p <= 1.0
        assert p + 1e-6 >= last          # non-decreasing
        last = p
        env.step(int(rng.choice(np.flatnonzero(obs["action_mask"]))))
    assert last > 0.0


def test_random_rollouts_all_campaigns():
    """Full games on every campaign: no exceptions, zero-sum terminal rewards
    consistent with the engine's winner / VP comparison."""
    for campaign in (1, 2, 3, 4, 5):
        for g in range(6):
            env, terminal, steps, _ = _random_game(campaign, seed=campaign * 1000 + g)
            eng = env.engine
            assert eng.state.game_over, f"C{campaign} game did not finish ({steps} steps)"
            assert set(terminal) == {"US", "PRC"}
            assert terminal["US"] + terminal["PRC"] == pytest.approx(0.0)
            us_vp = eng.total_victory_points(Side.US)
            prc_vp = eng.total_victory_points(Side.PRC)
            if eng.state.winner is not None:
                expected_us = 1.0 if eng.state.winner == Side.US else -1.0
            elif us_vp != prc_vp:
                expected_us = 1.0 if us_vp > prc_vp else -1.0
            else:
                expected_us = 0.0
            assert terminal["US"] == pytest.approx(expected_us)


def test_seed_determinism():
    a = _random_game(3, seed=42)
    b = _random_game(3, seed=42)
    assert a[3] == b[3]          # identical (agent, node, n_choices, action) sequence
    assert a[1] == b[1]          # identical terminal rewards
    c = _random_game(3, seed=43)
    assert c[3] != a[3]          # a different seed diverges


def test_fog_hides_unacquired_enemy_identity():
    """Under fog, an unacquired enemy token's row shows band + acquisition value
    but a zeroed type block; with reveal=True types are always visible."""
    hidden_rows = revealed_rows = 0

    def check_fog(env, agent, obs, info):
        nonlocal hidden_rows, revealed_rows
        for row in obs["observation"]["enemy_tokens"]:
            present, acquired = row[N_TT + N_BANDS], row[N_TT + N_BANDS + 1]
            if present and not acquired:
                hidden_rows += 1
                assert row[:N_TT].sum() == 0.0          # identity masked
                assert row[N_TT:N_TT + N_BANDS].sum() == 1.0   # position public
                assert row[N_TT + N_BANDS + 4] > 0.0    # acquisition value public

    _random_game(3, seed=7, on_obs=check_fog)
    assert hidden_rows > 0, "fog test never saw a hidden enemy token"

    def check_reveal(env, agent, obs, info):
        nonlocal revealed_rows
        for row in obs["observation"]["enemy_tokens"]:
            if row[N_TT + N_BANDS]:
                revealed_rows += 1
                assert row[:N_TT].sum() == 1.0

    _random_game(3, seed=7, reveal=True, on_obs=check_reveal)
    assert revealed_rows > 0


def test_node_coverage_full_decision_surface():
    """Every decision-node type is exercised by random play across campaigns."""
    seen = set()

    def collect(env, agent, obs, info):
        seen.add(info["node"])

    rng_games = [(camp, camp * 100 + g) for camp in (1, 2, 3, 4, 5) for g in range(8)]
    for camp, seed in rng_games:
        _random_game(camp, seed=seed, on_obs=collect)
        if len(seen) == len(NodeType):
            break
    missing = {n.name for n in NodeType} - seen
    assert not missing, f"decision nodes never visited: {missing}"


def test_observation_completeness():
    """The observation must fully describe the destruction state: every living
    token carries exactly one band, the active-side flag is set on turn nodes,
    and after the game each side's obs matches the engine — destroyed squadron
    flags, permanent token losses, and capture (scoring-pile) counts."""
    ACTIVE_FLAG = CAPTURES_SCALAR_OFFSET - 3

    def during(env, agent, obs, info):
        o = obs["observation"]
        for key in ("own_tokens", "enemy_tokens"):
            for row in o[key]:
                if row[N_TT + N_BANDS]:                      # token present
                    assert row[N_TT:N_TT + N_BANDS].sum() == 1.0, \
                        f"{key} row lacks a band"
        if info["node"] == "TURN_ACTION":
            assert o["scalars"][ACTIVE_FLAG] == 1.0

    checked_games = 0
    for camp, seed in ((2, 21), (3, 33), (2, 22)):
        env, _, _, _ = _random_game(camp, seed=seed, on_obs=during)
        eng = env.engine
        for agent in env.possible_agents:
            side = Side(agent)
            o = env.observe(agent)["observation"]
            me = eng.state.player(side)
            opp = eng.state.opponent(side)
            # Own squadrons: destroyed flag and permanent losses match engine.
            for i, cid in enumerate(SQUADRON_SLOTS[side]):
                squad = me.squadrons.get(cid)
                if squad is None:
                    continue
                row = o["own_squadrons"][i]
                assert row[N_TT + 2] == float(squad.is_destroyed)
                assert row[N_TT + 6] == pytest.approx(squad.tokens_lost / 4.0)
            # Enemy destroyed squadrons are public.
            for i, cid in enumerate(SQUADRON_SLOTS[opp.side]):
                squad = opp.squadrons.get(cid)
                if squad is not None and squad.is_destroyed:
                    assert o["enemy_squadrons"][i][N_TT + 2] == 1.0
            # Capture (scoring-pile) counts, both sides, are in the scalars.
            scal = o["scalars"]
            own_block = scal[CAPTURES_SCALAR_OFFSET:CAPTURES_SCALAR_OFFSET + N_SCORE + 1]
            opp_block = scal[CAPTURES_SCALAR_OFFSET + N_SCORE + 1:
                             CAPTURES_SCALAR_OFFSET + 2 * (N_SCORE + 1)]
            assert own_block.sum() == pytest.approx(len(me.captures) * 0.25)
            assert opp_block.sum() == pytest.approx(len(opp.captures) * 0.25)
            checked_games += 1
    assert checked_games == 6


def test_squadron_surviving_tokens_encoded():
    """Each squadron row carries its surviving/re-fieldable token count
    (full complement - permanent losses; 0 once destroyed) — needed to draft
    later ATOs when squadrons have been gutted."""
    from afwip.core.tokens import TOKEN_REGISTRY
    env = AFWIPEnv(campaign=2)
    env.reset(seed=1)
    eng = env.engine
    me = eng.state.us
    cid = SQUADRON_SLOTS[Side.US][0]
    from afwip.core.state import SquadronState, CardZone
    me.squadrons[cid] = SquadronState(cid, Side.US, activated=True,
                                      zone=CardZone.ACTIVE, tokens_lost=1)
    full = TOKEN_REGISTRY[me.squadrons[cid].token_type].token_count
    row = env.observe("US")["observation"]["own_squadrons"][0]
    assert row[N_TT + 9] == pytest.approx((full - 1) / 4.0)
    # A destroyed card has zero survivors.
    me.squadrons[cid].zone = CardZone.DESTROYED
    row = env.observe("US")["observation"]["own_squadrons"][0]
    assert row[N_TT + 9] == 0.0


def test_base_strike_vp_counts_live_in_obs_and_score():
    """Airbase VP boxes count the instant they land (user ruling 2026-08-10):
    the score, and thus the RL vp scalar, reflect a base strike immediately —
    not only at end of ATO."""
    env = AFWIPEnv(campaign=3)
    env.reset(seed=2)
    eng = env.engine
    off = SCALAR_OFF["vp"]
    base_before = eng.total_victory_points(Side.US)
    eng.state.prc.airbase_vp_damage = 2                  # US hits 2 boxes on the PRC base
    assert eng.total_victory_points(Side.US) == base_before + 2   # counted live
    vp_scalar = env.observe("US")["observation"]["scalars"][off]
    assert vp_scalar == pytest.approx(eng.total_victory_points(Side.US) / 50.0)


def test_mission_and_posture_encoded_in_scalars():
    """Once drafting is done, both sides' mission and posture one-hots must be
    set in the scalar observation (needed to condition/initialize policies)."""
    checked = 0

    def check(env, agent, obs, info):
        nonlocal checked
        if info["node"] != "TURN_ACTION":
            return
        scalars = obs["observation"]["scalars"]
        for base in (POSTURE_SCALAR_OFFSET, MISSION_SCALAR_OFFSET):
            own = scalars[base:base + 6]
            opp = scalars[base + 6:base + 12]
            assert own.sum() == 1.0 and opp.sum() == 1.0, \
                f"{info['node']}: posture/mission one-hot missing at {base}"
        checked += 1

    _random_game(2, seed=9, on_obs=check)
    assert checked > 0


def test_phase_one_hot_always_set():
    """The scalar phase one-hot must have exactly one active bit at every live
    decision node (a Markov requirement — node type alone doesn't fix phase)."""
    off = SCALAR_OFF["phase"]
    seen = 0

    def check(env, agent, obs, info):
        nonlocal seen
        block = obs["observation"]["scalars"][off:off + N_PHASE]
        assert block.sum() == 1.0, f"{info['node']}: phase one-hot not set"
        seen += 1

    _random_game(3, seed=4, on_obs=check)
    assert seen > 0


def test_markov_completeness_fields_encoded_and_fog_safe():
    """Intel, primed buffs, seat identity, derived roll mode, spent postures,
    infantry placement and the airbase-scoring delta are all encoded — and read
    as PUBLIC opponent state from the other seat (no hidden-info leak)."""
    from afwip.core.constants import Side, IntelTrack, BandID, PostureType
    from afwip.core.state import EnablerCardState, CardZone

    env = AFWIPEnv(campaign=2)
    env.reset(seed=3)
    gs = env.engine.state
    us, prc = gs.us, gs.prc
    off = SCALAR_OFF

    us.intel_track = IntelTrack.ADVANTAGE
    us.pending_air_advantage = True
    prc.pending_auto_hit = True
    # Offensive EW (28): US attack rolls at advantage, acquisition unaffected.
    us.enablers[28] = EnablerCardState(card_id=28, side=Side.US,
                                       zone=CardZone.ACTIVE, enduring=True)
    us.postures_used.add(PostureType.ACE)
    us.infantry_battalions[BandID.US_AIRBASE] = 1     # 1 of 2 damage boxes
    us.airbase_vp_damage, us.airbase_vp_scored = 2, 1  # one box unrealized

    v = env.observe("US")["observation"]["scalars"]
    assert v[off["side_is_us"]] == 1.0
    assert v[off["intel"]] == 1.0 and v[off["intel"] + 1] == 0.0
    assert v[off["pending_air_adv"]] == 1.0
    assert v[off["pending_auto_hit"] + 1] == 1.0          # opp (PRC) primed
    rs = v[off["roll_summary"]:off["roll_summary"] + N_ROLL_CTX]
    ctx = {c.name: rs[i] for i, c in enumerate(ROLL_SUMMARY_CONTEXTS)}
    assert ctx["AIR_ATTACK"] == 1.0 and ctx["BASE_ATTACK"] == 1.0
    assert ctx["ACQUIRE"] == 0.0                           # EW is attack-only
    pu = v[off["postures_used"]:off["postures_used"] + POSTURE_SLOT_W]
    assert pu.sum() == 1.0
    assert v[off["airbase_unscored"]] == pytest.approx(1 / 3)
    inf = v[off["infantry"]:off["infantry"] + 4]           # US block: 3 bands + dmg
    assert inf[0] == 1.0 and inf[3] == pytest.approx(0.5)

    # From the PRC seat the same facts are PUBLIC opponent state, never leaked
    # as PRC's own; seat identity flips.
    v2 = env.observe("PRC")["observation"]["scalars"]
    assert v2[off["side_is_us"]] == 0.0
    assert v2[off["intel"]] == 0.0 and v2[off["intel"] + 1] == 1.0  # US adv seen as opp
    assert v2[off["pending_air_adv"] + 1] == 1.0                    # US buff seen as opp


def test_new_ato_cycle_redrafts_squadrons_and_enablers():
    """Cycle 2 re-selects a posture and RE-DRAFTS squadrons + enablers (ruling
    2026-07-22), re-choosing placement. Missions stay a once-per-game choice."""
    env = AFWIPEnv(campaign=2)   # Tournament: exactly 2 ATO cycles
    env.reset(seed=11)
    rng = random.Random(11)
    nodes_by_cycle: dict[int, set] = {}   # ATO_SETUP (drafting) nodes only
    all_nodes: dict[int, set] = {}
    roster_checked = False
    for agent in env.agent_iter():
        obs, r, term, trunc, info = env.last()
        if term or trunc:
            env.step(None)
            continue
        eng = env.engine
        cyc = eng.state.ato_cycle
        # Record DRAFTING nodes only. Several node types (SQUADRON_PICK,
        # SQUADRON_BASE, ENABLER_PICK) are deliberately reused by enabler-card
        # target pickers during a turn — see DEV_CONTEXT §4.4 — so the phase,
        # not the node type, is what distinguishes a draft from a card choice.
        if eng.state.phase == Phase.ATO_SETUP:
            nodes_by_cycle.setdefault(cyc, set()).add(info["node"])
        all_nodes.setdefault(cyc, set()).add(info["node"])
        if info["node"] == "TURN_ACTION" and cyc == 2 and not roster_checked:
            roster_checked = True
            for s in (Side.US, Side.PRC):
                for cid, card in eng.state.player(s).enablers.items():
                    # Played single-use cards stay REMOVED; the fresh draft is
                    # in hand (SELECTED); undrafted survivors wait in DECK.
                    assert card.zone in (CardZone.REMOVED, CardZone.SELECTED,
                                         CardZone.DECK), \
                        f"{s.value} enabler {cid} in zone {card.zone} at cycle 2"
                assert eng.state.player(s).enablers_in_hand(), \
                    f"{s.value} has no fresh hand at cycle 2"
        env.step(int(rng.choice(np.flatnonzero(obs["action_mask"]))))

    assert env.engine.state.game_over and len(nodes_by_cycle) == 2
    assert roster_checked
    for required in ("MISSION_PICK", "POSTURE_PICK", "SQUADRON_PICK",
                     "ENABLER_PICK"):
        assert required in nodes_by_cycle[1], \
            f"cycle 1 missing {required} draft node: {sorted(nodes_by_cycle[1])}"
    assert "TURN_ACTION" in all_nodes[1]
    # Posture, squadrons AND enablers are all re-drafted per-cycle (ruling
    # 2026-07-22); placement is re-chosen too.
    for required in ("POSTURE_PICK", "SQUADRON_PICK", "ENABLER_PICK"):
        assert required in nodes_by_cycle[2], \
            f"cycle 2 must re-draft {required}: {sorted(nodes_by_cycle[2])}"
    # Missions are chosen once per game, never re-drafted.
    assert "MISSION_PICK" not in nodes_by_cycle[2], \
        "missions are a once-per-game choice, not re-drafted"


def test_turn_resumes_after_response_windows():
    """A response window (opponent reaction card, MD-cancel, self-response)
    never transfers the turn: the next TURN_ACTION after any RESPONSE node
    belongs to the same side as the TURN_ACTION that triggered it."""
    responses_seen = 0
    for camp in (2, 3, 4):
        for g in range(6):
            _, _, _, trace = _random_game(camp, seed=camp * 77 + g)
            last_actor = None
            pending_since_response = None
            for agent, node, _n, _a in trace:
                if node == "TURN_ACTION":
                    if pending_since_response is not None:
                        assert agent == pending_since_response, (
                            f"C{camp} seed {camp*77+g}: turn jumped from "
                            f"{pending_since_response} to {agent} after a RESPONSE")
                        pending_since_response = None
                    last_actor = agent
                elif node == "RESPONSE" and last_actor is not None:
                    responses_seen += 1
                    pending_since_response = last_actor
    assert responses_seen > 0, "no response windows exercised"


def test_vp_shaping_is_zero_sum_and_telescopes():
    coeff = 0.1
    env = AFWIPEnv(campaign=3, vp_shaping=coeff)
    env.reset(seed=5)
    rng = random.Random(5)
    totals = {a: 0.0 for a in env.possible_agents}
    for agent in env.agent_iter():
        obs, r, term, trunc, info = env.last()
        if term or trunc:
            env.step(None)
        else:
            env.step(int(rng.choice(np.flatnonzero(obs["action_mask"]))))
        for a, rew in env.rewards.items():
            totals[a] += rew
    assert totals["US"] + totals["PRC"] == pytest.approx(0.0, abs=1e-6)
    # Potential-based shaping telescopes to coeff * final VP differential,
    # plus the terminal +-1 (0 on a draw).
    eng = env.engine
    diff = eng.total_victory_points(Side.US) - eng.total_victory_points(Side.PRC)
    terminal = 0.0 if diff == 0 and eng.state.winner is None else \
        (1.0 if (eng.state.winner or (Side.US if diff > 0 else Side.PRC)) == Side.US else -1.0)
    assert totals["US"] == pytest.approx(coeff * diff + terminal, abs=1e-6)


# ---------------------------------------------------------------------------
# Engine APIs added for the env
# ---------------------------------------------------------------------------

def test_two_phase_intel_matches_rules():
    rng = random.Random(3)
    eng = RulesEngine(GameState.new_game(campaign=3), rng=rng)
    auto_draft(eng, rng)
    eng.bid_for_initiative()
    counts = eng.play_intel_roll()
    assert set(counts) == {Side.US, Side.PRC}
    for side in (Side.US, Side.PRC):
        hand = [c.card_id for c in eng.state.player(side).enablers_in_hand()]
        n = counts[side]
        assert 0 <= n <= max(0, len(hand) - 1)   # at least one card stays hidden
        with pytest.raises(IllegalAction):        # wrong count rejected
            eng.play_intel_reveal(side, hand[:n] + [9999])
        eng.play_intel_reveal(side, hand[:n])
        revealed = {c.card_id for c in eng.state.player(side).enablers_in_hand()
                    if c.revealed_to_opponent}
        assert revealed == set(hand[:n])
        with pytest.raises(IllegalAction):        # pending entry consumed
            eng.play_intel_reveal(side, hand[:n])


def _deferred_strike_setup():
    """US bomber in surface range of the PRC airbase, defender squadron there,
    auto-hit primed so the deferred-allocation path is deterministic."""
    gs = GameState.new_game(campaign=3)
    gs.phase = Phase.PLAYER_TURN
    gs.active_side = Side.US
    gs.turn_number = 1
    gs.us.posture_card_id = 49
    gs.prc.posture_card_id = 103
    eng = RulesEngine(gs, rng=random.Random(0))

    tok_type = TokenType.B_52
    prof = TOKEN_REGISTRY[tok_type]
    prc_base = board.own_airbase(Side.PRC)
    band = next(b for b in BandID if board.is_on_map(b)
                and board.in_range(b, prc_base, prof.surf_atk_range))
    attacker = gs.spawn_token(Side.US, tok_type, band, TokenOrigin.ENABLER_CARD)

    cid = next(c for c, s in SQUADRON_REGISTRY.items() if s.side == Side.PRC)
    gs.prc.squadrons[cid] = SquadronState(card_id=cid, side=Side.PRC,
                                          zone=CardZone.SELECTED, location=prc_base)
    gs.us.pending_auto_hit = True   # Forward Observers: strike auto-hits
    return eng, attacker, cid, prc_base


def test_deferred_base_allocation():
    eng, attacker, cid, prc_base = _deferred_strike_setup()
    squad = eng.state.prc.squadrons[cid]

    r = eng.shoot_surface(Side.US, attacker.uid, target_band=prc_base,
                          defer_allocation=True)
    assert r.hit and r.damage >= 1
    pending = r.pending_allocation
    assert pending is not None and pending.amount == r.damage
    assert ("squadron", cid) in pending.targets
    assert ("vp", None) in pending.targets
    assert squad.damage == 0 and eng.state.prc.airbase_vp_damage == 0  # not applied yet

    with pytest.raises(IllegalAction):   # no other action until resolved
        eng.end_turn(Side.US)

    done = eng.resolve_base_allocation([("squadron", cid, pending.amount)])
    assert done is r
    assert squad.damage == min(pending.amount, DAMAGE_TO_DESTROY_SQUADRON)
    with pytest.raises(IllegalAction):   # one resolution only
        eng.resolve_base_allocation([("vp", None, 1)])
    eng.end_turn(Side.US)                # turn flow unblocked
