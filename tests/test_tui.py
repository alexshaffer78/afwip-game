"""Terminal visualizer tests: headless watch runs, fog rendering, stepping
controls, and scripted play mode."""

import io
import random
from contextlib import redirect_stdout

from afwip import tui
from afwip.core.rules import RulesEngine
from afwip.core.state import GameState, SquadronState, CardZone
from afwip.core.constants import Side, BandID, Phase, TokenType, TokenOrigin


def _scripted_input(script):
    it = iter(script)

    def fake(prompt=""):
        try:
            return next(it)
        except StopIteration:
            return "q"
    return fake


def _run(fn, *args, **kwargs) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        fn(*args, **kwargs)
    return buf.getvalue()


def test_watch_auto_completes_campaign1():
    out = _run(tui.watch, campaign=1, seed=0, auto=0)
    assert "GAME OVER" in out
    assert "TURN_ACTION" in out
    assert "Traceback" not in out


def test_watch_auto_completes_campaign3_with_node_filter():
    out = _run(tui.watch, campaign=3, seed=3, auto=0,
               node_filter={"TURN_ACTION", "RESPONSE", "ALLOC_POINT"})
    assert "GAME OVER" in out
    assert "POSTURE_PICK" not in out.split("GAME OVER")[0].split("NEXT")[-1]


def test_watch_interactive_step_toggle_skip_quit(monkeypatch):
    # Enter=step, r=fog toggle, 10=skip ten decisions, q=quit — all headless.
    monkeypatch.setattr("builtins.input", _scripted_input(["", "", "r", "10", "", "q"]))
    out = _run(tui.watch, campaign=2, seed=7)
    assert "NEXT" in out and "Traceback" not in out


def _fog_state():
    gs = GameState.new_game(campaign=3)
    gs.phase = Phase.PLAYER_TURN
    gs.active_side = Side.US
    gs.us.posture_card_id, gs.prc.posture_card_id = 49, 103
    eng = RulesEngine(gs, rng=random.Random(0))
    gs.prc.squadrons[62] = SquadronState(62, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    tok = gs.spawn_token(Side.PRC, TokenType.J_20B, BandID.BAND_C,
                         TokenOrigin.SQUADRON_CARD, source_card_id=62)
    return eng, tok


def test_board_fog_masks_unacquired_enemy():
    eng, tok = _fog_state()
    fogged = tui.render_board(eng, viewer=Side.US, reveal=False)
    assert f"?#{tok.uid}(av{tok.profile.acquisition_value})" in fogged
    assert "J-20B" not in fogged                      # identity hidden
    revealed = tui.render_board(eng, viewer=Side.US, reveal=True)
    assert f"J-20B#{tok.uid}" in revealed
    tok.acquired = True                               # acquisition lifts the fog
    assert f"J-20B#{tok.uid}*" in tui.render_board(eng, viewer=Side.US, reveal=False)


def test_play_quit_is_clean(monkeypatch):
    monkeypatch.setattr("builtins.input", _scripted_input(["q"]))
    out = _run(tui.play, Side.US, campaign=1, seed=0)
    assert "Quit." in out


def test_play_scripted_game_completes(monkeypatch):
    # Human (US) always picks choice 0; random agent plays PRC. Campaign 1 is
    # short (forced squadrons, no enablers) and must reach GAME OVER.
    monkeypatch.setattr("builtins.input", _scripted_input(["0"] * 300))
    out = _run(tui.play, Side.US, campaign=1, seed=0)
    assert "GAME OVER" in out
    assert "US choice #>" not in out                  # prompt goes to stdin, not stdout
    assert "Traceback" not in out


def test_cli_parses_watch_flags():
    import pytest
    with pytest.raises(SystemExit):                   # bad node type rejected
        tui.main(["watch", "--node-filter", "NOT_A_NODE"])


def test_watch_log_exposes_dice_rolls():
    out = _run(tui.watch, campaign=2, seed=7, auto=0)
    assert "dice:" in out and "D4=" in out
    assert "advantage" in out          # intel/MD advantage rolls show their mode


def test_end_of_ato_scoring_report():
    # At the end of each ATO cycle the log shows per-side VP attribution:
    # every capture by name with its mission value, plus accrued entries.
    out = _run(tui.watch, campaign=2, seed=5, auto=0)
    assert "===== ATO 1 SCORING =====" in out
    assert "===== ATO 2 SCORING =====" in out
    assert "tokens destroyed:" in out
    assert "campaign total" in out
    # Seed 5: both sides play Attrition; a ship/AEW token kill is +3. (Re-baselined
    # whenever the decision stream changes — random agents then diverge; here the
    # 2026-08-14 standoff air-to-air fix shifted the trajectory.)
    assert "DDG 115#15 (+3)" in out                     # heavy-token (ship) capture
    assert "AEW (PRC)#5 [ground] (+3)" in out           # heavy-token (AEW) capture
    assert "enemy airbase VP boxes: +3" in out          # accrued base-strike VP


def test_score_report_direct():
    # Unit-level: capture identity and accrued vp_log entries both appear.
    gs = GameState.new_game(campaign=1)
    gs.phase = Phase.PLAYER_TURN
    eng = RulesEngine(gs, rng=random.Random(0))
    gs.us.mission_card_id, gs.prc.mission_card_id = 51, 105   # both Attrition
    gs.prc.squadrons[60] = SquadronState(60, Side.PRC, activated=True,
                                         location=BandID.PRC_AIRBASE, zone=CardZone.ACTIVE)
    j10 = gs.spawn_token(Side.PRC, TokenType.J_10, BandID.BAND_D,
                         TokenOrigin.SQUADRON_CARD, source_card_id=60)
    gs.destroy_token(j10.uid, destroyed_by=Side.US)
    gs.us.vp_log.append((1, "enemy airbase VP boxes", 2))
    report = "\n".join(tui._score_report(eng, 1))
    assert f"J-10#{j10.uid} (+1)" in report
    assert "enemy airbase VP boxes: +2" in report


def test_event_log_distinguishes_recycled_from_destroyed():
    # ATO cleanup recycles surviving tokens to their Squadron Cards — the log
    # must not report them "destroyed" (user report 2026-07-15, C2 seed 22:
    # survivors regenerating next ATO looked like destroyed tokens returning).
    gs = GameState.new_game(campaign=3)
    gs.phase = Phase.PLAYER_TURN
    gs.active_side = Side.US
    eng = RulesEngine(gs, rng=random.Random(0))
    gs.us.squadrons[10] = SquadronState(10, Side.US, activated=True,
                                        location=BandID.US_AIRBASE, zone=CardZone.ACTIVE)
    survivor = gs.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_B,
                              TokenOrigin.SQUADRON_CARD, source_card_id=10)
    victim = gs.spawn_token(Side.US, TokenType.F_16C, BandID.BAND_B,
                            TokenOrigin.SQUADRON_CARD, source_card_id=10)
    ship = gs.spawn_token(Side.US, TokenType.DDG_81, BandID.BAND_C,
                          TokenOrigin.ENABLER_CARD)
    ship.air_salvos_remaining = ship.surf_salvos_remaining = 0   # winchester

    before = tui._snapshot(eng)
    gs.destroy_token(victim.uid, destroyed_by=Side.PRC)          # real kill
    eng._start_turn(Side.US)      # winchester ship moves off-board; survivor stays
    eng.end_ato_cycle()           # survivor recycles to its card
    msgs = tui._diff(before, tui._snapshot(eng))

    assert any(f"F-16C#{victim.uid} destroyed" in m for m in msgs)
    assert any(f"F-16C#{survivor.uid} recycles" in m for m in msgs)
    assert any(f"DDG 81#{ship.uid} moves off-board" in m for m in msgs)
    assert not any(f"#{survivor.uid} destroyed" in m for m in msgs)
    assert not any(f"#{ship.uid} destroyed" in m for m in msgs)
