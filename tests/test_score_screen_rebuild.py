import score_screen
from score_screen import ScoreScreen


def test_rebuild_board_synchronous_fallback_and_totals(monkeypatch):
    # prepare fake data with 1 round and 2 players
    data = {
        'players': ['P1', 'P2'],
        'rounds': [
            {
                'total': {'P1': 10, 'P2': -10},
                'breakdown': {'basic': {'P1': 1, 'P2': -1}, 'duns_raw': {'P1': 0, 'P2': 0}},
                'ranks': {'P1': 1, 'P2': 2}
            }
        ]
    }

    monkeypatch.setattr(score_screen, 'load_data', lambda: data)
    # force schedule_interval to raise so fallback synchronous path is used
    monkeypatch.setattr(score_screen.Clock, 'schedule_interval', lambda *a, **k: (_ for _ in ()).throw(Exception('no clock')))

    ss = ScoreScreen(name='score')
    ss.rebuild_board()

    # expected children: header (1 + 2 players) + for 1 round (1 round label + 2 player cells) + totals row (1 + 2)
    expected = (1 + 2) + (1 + 2) + (1 + 2)
    assert len(ss.board_box.children) == expected
    # last round widgets should be set
    assert ss._last_round_widgets is not None


def test_highlight_last_round_applies_tint(monkeypatch):
    data = {
        'players': ['P1', 'P2'],
        'rounds': [
            {
                'total': {'P1': 5, 'P2': -5},
                'breakdown': {'basic': {'P1': 0, 'P2': 0}, 'duns_raw': {'P1': 0, 'P2': 0}},
                'ranks': {'P1': 1, 'P2': 2}
            }
        ]
    }
    monkeypatch.setattr(score_screen, 'load_data', lambda: data)
    # force synchronous fallback again
    monkeypatch.setattr(score_screen.Clock, 'schedule_interval', lambda *a, **k: (_ for _ in ()).throw(Exception('no clock')))
    # prevent restoration from running (no-op schedule_once)
    monkeypatch.setattr(score_screen.Clock, 'schedule_once', lambda cb, dt: None)

    ss = ScoreScreen(name='score')
    ss.rebuild_board()
    # ensure last widgets populated
    assert ss._last_round_widgets is not None
    # pick first widget in last round and check bg change on highlight
    cont = ss._last_round_widgets[0]
    orig_bg = getattr(cont, '_bg_color', None)
    orig_instr = getattr(getattr(cont, '_bg_color_instr', None), 'rgba', None)
    ss.highlight_last_round(duration=0.1)
    # check either canvas instruction rgba changed, or stored _bg_color changed
    new_instr = getattr(getattr(cont, '_bg_color_instr', None), 'rgba', None)
    new_bg = getattr(cont, '_bg_color', None)
    if orig_instr is not None:
        assert new_instr is not None and new_instr != orig_instr
    else:
        assert new_bg is not None and new_bg != orig_bg
