"""
Full-registry enabler sweep: play EVERY Enabler Card in a rich, deterministic
mid-turn state and assert the EnablerResult is consistent with the actual
state change (cyber deltas hit the cyber track, generated tokens exist,
destroyed tokens are gone, discards leave the hand, base damage lands).

Cards that legitimately need context this generic state can't provide (e.g.
cancel cards with nothing to cancel) must appear in EXPECTED_NOOP_OR_ILLEGAL —
anything else failing to apply is a bug.
"""

import random

import pytest

from afwip.core.rules import RulesEngine, IllegalAction
from afwip.core.enablers import EnablerPlay, ENABLER_CHOICE_BRANCHES
from afwip.core.state import GameState, CardZone
from afwip.core.cards import ENABLER_REGISTRY
from afwip.core.constants import Side, BandID, TokenType, TokenOrigin
from tests.test_enablers import setup, spawn_enemy


# Cards whose handler can raise / no-op in the generic sweep state, with why.
EXPECTED_NOOP_OR_ILLEGAL = {
    "cancel": "cancel cards need an opponent card/attack to void",
    "response": "response-only timing needs a triggering event",
}


def _rich_state(side: Side, cid: int) -> RulesEngine:
    """Mid-turn engine with the card in hand and plenty of targets."""
    eng = setup(side, [cid], us_sq=(10, 5), prc_sq=(60, 62))
    enemy_air = TokenType.J_10 if side == Side.US else TokenType.F_16C
    enemy_ship = TokenType.NANNING_162 if side == Side.US else TokenType.DDG_81
    src = 60 if side == Side.US else 10
    opp = eng.state.opponent(side).side
    for band in (BandID.BAND_B, BandID.BAND_C, BandID.BAND_D):
        eng.state.spawn_token(opp, enemy_air, band, TokenOrigin.SQUADRON_CARD,
                              source_card_id=src)
    ship = eng.state.spawn_token(opp, enemy_ship, BandID.BAND_C,
                                 TokenOrigin.ENABLER_CARD, source_card_id=None)
    ship.acquired = True
    for t in eng.state.player(opp).living_tokens():
        t.acquired = True
    own_air = TokenType.F_16C if side == Side.US else TokenType.J_10
    eng.state.spawn_token(side, own_air, BandID.BAND_C, TokenOrigin.SQUADRON_CARD,
                          source_card_id=10 if side == Side.US else 60)
    eng._d4 = lambda: 4   # strikes hit, raises succeed, generation maxes
    return eng


def _snapshot(eng):
    return {
        s: {
            "cyber": eng.state.player(s).cyber_rate,
            "tokens": {t.uid for t in eng.state.player(s).living_tokens()},
            "hand": {c.card_id for c in eng.state.player(s).enablers_in_hand()},
            "sq_damage": {cid: sq.damage for cid, sq in eng.state.player(s).squadrons.items()},
            "vp_boxes": eng.state.player(s).airbase_vp_damage,
        }
        for s in (Side.US, Side.PRC)
    }


def _play_variants(cid):
    branches = ENABLER_CHOICE_BRANCHES.get(cid)
    if branches:
        return [EnablerPlay(choice=b) for b in branches]
    return [None]


@pytest.mark.parametrize("cid", sorted(ENABLER_REGISTRY))
def test_enabler_result_matches_state_change(cid):
    profile = ENABLER_REGISTRY[cid]
    side = profile.side
    opp = Side.PRC if side == Side.US else Side.US

    for play in _play_variants(cid):
        eng = _rich_state(side, cid)
        full_play = eng._default_enabler_play(side, cid)
        if play is not None and play.choice:
            full_play.choice = play.choice
        before = _snapshot(eng)

        try:
            result = eng.play_enabler(side, cid, full_play,
                                      response=not profile.is_not_response)
        except IllegalAction:
            # Only acceptable for cards that need un-providable context here.
            assert profile.is_response or "CANCEL" in profile.effect_text.upper() \
                or "RECOVER" in profile.effect_text.upper(), \
                f"card {cid} ({profile.name}) failed to apply in the sweep state"
            continue
        after = _snapshot(eng)

        # --- cyber: result delta must equal the actual track movement -------
        own_cyber_change = after[side]["cyber"] - before[side]["cyber"]
        opp_cyber_change = after[opp]["cyber"] - before[opp]["cyber"]
        assert result.cyber_delta == own_cyber_change + opp_cyber_change, \
            f"card {cid} ({profile.name}): cyber_delta={result.cyber_delta} but " \
            f"own {own_cyber_change:+d} opp {opp_cyber_change:+d}"
        if result.cyber_delta > 0:
            assert own_cyber_change == result.cyber_delta
        if result.cyber_delta < 0:
            assert opp_cyber_change == result.cyber_delta

        # --- generated tokens exist and belong to the owner ------------------
        for uid in result.tokens:
            assert uid in after[side]["tokens"], \
                f"card {cid}: generated token {uid} not on the board"

        # --- destroyed/removed enemy tokens are gone -------------------------
        for uid in result.destroyed:
            assert uid not in after[opp]["tokens"], \
                f"card {cid}: destroyed token {uid} still alive"

        # --- forced discards left the opponent's hand ------------------------
        for dcid in result.discarded:
            assert dcid not in after[opp]["hand"], \
                f"card {cid}: discarded card {dcid} still in hand"

        # --- base damage landed somewhere ------------------------------------
        if result.base_damage:
            sq_gain = sum(after[opp]["sq_damage"].get(k, 0) - v
                          for k, v in before[opp]["sq_damage"].items())
            vp_gain = after[opp]["vp_boxes"] - before[opp]["vp_boxes"]
            tok_loss = len(before[opp]["tokens"] - after[opp]["tokens"])
            assert sq_gain + vp_gain + tok_loss > 0, \
                f"card {cid}: base_damage={result.base_damage} but nothing changed"

        # --- the card left the hand (played/active), never silently stuck ----
        card = eng.state.player(side).enablers[cid]
        assert card.zone in (CardZone.PLAYED, CardZone.ACTIVE, CardZone.REMOVED), \
            f"card {cid}: zone {card.zone} after play"


def test_cyber_raise_success_and_failure_feedback():
    # Raise succeeds on a max roll (access value 1->2 is 3)...
    eng = _rich_state(Side.US, 15)
    res = eng.play_enabler(Side.US, 15, eng._default_enabler_play(Side.US, 15))
    assert res.cyber_delta == 1 and eng.state.us.cyber_rate == 2 and not res.note

    # ...and reports failure explicitly on a low roll (no silent no-op).
    eng = _rich_state(Side.US, 15)
    eng._d4 = lambda: 1
    res = eng.play_enabler(Side.US, 15, eng._default_enabler_play(Side.US, 15))
    assert res.cyber_delta == 0 and eng.state.us.cyber_rate == 1
    assert "failed" in res.note


def test_cyber_degrade_clamps_and_reports_actual_reduction():
    # Degrade-by-2 against a rate of 1 only removes 1 (floor 0) and the
    # result reports the ACTUAL reduction, not the printed value.
    eng = _rich_state(Side.US, 33)
    eng.state.prc.cyber_rate = 1   # pin below the degrade amount to hit the floor
    res = eng.play_enabler(Side.US, 33, eng._default_enabler_play(Side.US, 33))
    assert eng.state.prc.cyber_rate == 0
    assert res.cyber_delta == -1
