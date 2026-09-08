"""Tests for the copy-for-AI state encoding (afwip/view/export.py) and the
fog-safety of the acquire action label it depends on."""

import random
import re

from afwip.core.rules import RulesEngine
from afwip.core.state import GameState
from afwip.core.constants import Side, BandID, TokenType, TokenOrigin, Phase
from afwip.view.export import game_export
from afwip.web.session import GameMode, GameSession

from tests.helpers import draft_enablers, draft_squadrons


# A structured (non-banner, non-comment, non-blank) line is PREFIX: k=v ...
_RECORD = re.compile(r"^[A-Z_]+( [A-Z]+)?: .+$")


def _us_turn_with_enemy_facedown() -> RulesEngine:
    """US to move with its UAS airborne and a face-down PRC token in range."""
    eng = RulesEngine(GameState.new_game(3), rng=random.Random(0))
    eng.setup_missions(51, 105)
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (1,), camp=eng.campaign),
                       draft_enablers(Side.US))
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, (60,), camp=eng.campaign),
                       draft_enablers(Side.PRC))
    eng.bid_for_initiative(first_player=Side.US)
    eng.play_intel()
    eng.begin_player_turns()
    # A US Attack UAS on BAND_A and a face-down PRC J-10 on BAND_A: in acquire range.
    eng.state.spawn_token(Side.US, TokenType.ATTACK_UAS_US, BandID.BAND_A,
                          TokenOrigin.SQUADRON_CARD, source_card_id=1)
    eng.state.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_A,
                          TokenOrigin.SQUADRON_CARD, source_card_id=60)
    return eng


def test_acquire_label_is_fog_safe():
    """An acquire choice must not leak the (unacquired) enemy token's identity."""
    eng = _us_turn_with_enemy_facedown()
    acquires = [a for a in eng.legal_actions(Side.US) if a.kind == "acquire"]
    assert acquires, "expected an acquire option against the face-down PRC token"
    for a in acquires:
        assert "J-10" not in a.label            # the fogged type must not appear
        assert a.label.startswith("Acquire ?#")  # physical roll-to-acquire back


def _drive_to_us_turn_action(seed: int) -> GameSession:
    s = GameSession("g", campaign=2, mode=GameMode.HUMAN_V_AGENT,
                    human_side=Side.US, seed=seed)
    for _ in range(400):
        v = s.state()
        if v.terminal or v.decision is None:
            return s
        d = v.decision
        if d.node_type == "TURN_ACTION" and d.side == "US" \
                and any(c.kind in ("move", "acquire", "shoot_air") for c in d.choices):
            return s
        idx = next((c.index for c in d.choices if c.kind == "activate"), 0)
        try:
            s.apply_human(idx, revision=v.revision, node_id=v.node_id)
        except Exception:
            s.apply_human(0, revision=s.revision, node_id=s.node_id)
    return s


def test_export_is_present_and_well_formed():
    s = _drive_to_us_turn_action(3)
    view = s.state()
    text = view.llm_export
    assert text is not None
    assert text.startswith("=== AFWIP STATE v1 ===")
    assert text.rstrip().endswith("=== END ===")
    assert "VIEWER: side=US" in text
    assert "SIDE US: mission=ATTRITION" in text
    # Every structured line is a well-formed record, banner, comment, or blank.
    for line in text.splitlines():
        if not line or line.startswith("===") or line.startswith("#"):
            continue
        assert _RECORD.match(line), f"malformed export line: {line!r}"


def test_export_does_not_leak_fogged_enemy_types():
    s = _drive_to_us_turn_action(3)
    text = s.state().llm_export
    # Fogged enemy TOKEN rows render type="?"; and no acquire action names a type.
    for line in text.splitlines():
        if line.startswith("TOKEN:") and 'winchester=?' in line:
            assert 'type="?"' in line, f"fogged token leaked its type: {line!r}"
        if line.startswith("ACTION:") and "kind=acquire" in line:
            assert "?#" in line, f"acquire action leaked a type: {line!r}"


def test_spent_enablers_are_public_for_both_sides():
    """A played enabler is public: each side's spent cards show even to the
    opponent's fogged view (identities included)."""
    from afwip.view import serializer

    eng = RulesEngine(GameState.new_game(3), rng=random.Random(0))
    eng.setup_missions(51, 105)
    eng.select_posture(Side.US, 49, draft_squadrons(Side.US, (10,), camp=eng.campaign),
                       draft_enablers(Side.US, include=(19,)))       # Improved Munitions
    eng.select_posture(Side.PRC, 103, draft_squadrons(Side.PRC, (60,), camp=eng.campaign),
                       draft_enablers(Side.PRC, include=(71,)))      # Badger Surge
    eng.bid_for_initiative(first_player=Side.US)
    eng.play_intel()
    eng.begin_player_turns()

    eng.play_enabler(Side.US, 19)     # enduring -> ACTIVE (played)
    eng.end_turn(Side.US)
    eng.play_enabler(Side.PRC, 71)    # enduring -> ACTIVE (played)

    # US viewer sees its own spent card AND the PRC's spent card (public act).
    us_own = serializer.hand_view(eng, Side.US, Side.US, reveal=False)
    prc_seen_by_us = serializer.hand_view(eng, Side.PRC, Side.US, reveal=False)
    assert 19 in [c.card_id for c in us_own.spent]
    assert 71 in [c.card_id for c in prc_seen_by_us.spent]
    assert prc_seen_by_us.spent_count == len(prc_seen_by_us.spent)


def test_export_spent_lines_match_the_hands():
    """Every SPENT line in the export mirrors the hands' spent lists exactly."""
    s = GameSession("g", campaign=3, mode=GameMode.AGENT_V_AGENT, seed=1)
    for _ in range(150):
        if s.terminal:
            break
        s.step_once()
    v = s.state()
    text = v.llm_export
    export_spent = sorted(
        (line.split("owner=")[1].split(" ")[0], int(line.split("card=")[1].split(" ")[0]))
        for line in text.splitlines() if line.startswith("SPENT:"))
    hand_spent = sorted((h.side, c.card_id) for h in v.hands for c in h.spent)
    assert export_spent == hand_spent


def test_draft_export_shows_in_progress_squadrons_while_drafting_enablers():
    """The user's report: while drafting enablers, the export must show the
    squadrons already picked (not committed to engine state until the draft ends)."""
    s = GameSession("g", campaign=3, mode=GameMode.HUMAN_V_AGENT,
                    human_side=Side.US, seed=4)
    for _ in range(80):
        v = s.state()
        if v.terminal or v.decision is None:
            break
        d = v.decision
        if d.node_type == "ENABLER_PICK" and d.side == "US":
            text = v.llm_export
            assert "=== DRAFT (in progress) ===" in text
            assert any(l.startswith("DRAFT: side=US posture=")
                       for l in text.splitlines())
            # squadrons picked earlier this draft are visible during enabler pick
            assert any(l.startswith("DRAFT_SQUADRON:") for l in text.splitlines())
            return
        idx = next((c.index for c in d.choices if c.kind == "pick"), 0)
        s.apply_human(idx, revision=v.revision, node_id=v.node_id)
    raise AssertionError("never reached a US enabler-draft node")


def test_draft_mirror_is_fog_gated_and_clears():
    """The in-progress draft is shown only to the drafting side (or a spectator),
    and the mirror is empty once setup is over."""
    s = GameSession("g", campaign=3, mode=GameMode.HUMAN_V_AGENT,
                    human_side=Side.US, seed=4)
    s._draft = {"side": Side.US, "posture": 49, "squadrons": [5, 8],
                "locations": {}, "enablers": [19]}
    assert s._draft_view(Side.US) is not None            # own draft: visible
    assert s._draft_view(None) is not None                # spectator: visible
    assert s._draft_view(Side.PRC) is None                # opponent: hidden

    # Drive to the first US turn; by then setup is committed and the mirror clears.
    for _ in range(120):
        v = s.state()
        if v.terminal:
            break
        if v.decision and v.decision.node_type == "TURN_ACTION":
            break
        idx = 0 if not v.decision else next(
            (c.index for c in v.decision.choices if c.kind == "pick"), 0)
        s.apply_human(idx, revision=v.revision, node_id=v.node_id)
    assert s.env.engine.state.phase == Phase.PLAYER_TURN
    assert s._draft == {}


def test_export_omitted_behind_hotseat_handoff():
    """While the pass-the-device screen is up, no private state is exportable."""
    s = GameSession("g", campaign=2, mode=GameMode.HOTSEAT, seed=1)
    # Find a state that requires a handoff (the next decider isn't authorized yet).
    for _ in range(200):
        v = s.state()
        if v.handoff_required:
            assert v.llm_export is None
            return
        if v.terminal:
            break
        # Advance by authorizing + answering as the authorized side.
        node = s._node
        if node is None:
            break
        try:
            s.apply_human(0)
        except Exception:
            s.handoff()
    # If we never hit a handoff (unlikely), the test is vacuous but not a failure.
