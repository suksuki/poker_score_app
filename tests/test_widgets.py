import pytest
from widgets import _T, TrophyWidget, cell_bg, cell_bg_with_trophy, ScoreInputItem
import theme


def test__T_returns_theme_value():
    # pick a known theme constant
    assert _T('CURRENT_THEME') == getattr(theme, 'CURRENT_THEME')


def test_trophy_widget_ranks():
    w1 = TrophyWidget(rank=1)
    assert hasattr(w1, 'text') or hasattr(w1, 'children')
    w_last = TrophyWidget(rank='last')
    assert hasattr(w_last, 'text') or hasattr(w_last, 'children')
    w_none = TrophyWidget(rank=None)
    # empty trophy should produce a Label-like object with empty text
    assert hasattr(w_none, 'text')


def test_cell_bg_basic():
    c = cell_bg('hello', 120, 40, (0.1, 0.2, 0.3, 1))
    # should expose stored bg color
    assert getattr(c, '_bg_color', None) == (0.1, 0.2, 0.3, 1)
    # contains at least one child label
    assert len(getattr(c, 'children', [])) >= 1


def test_cell_bg_with_trophy_contains_label():
    c = cell_bg_with_trophy('p', 120, 40, (1, 1, 1, 1), rank=1)
    # container should have children; inner label should exist
    found_label = False
    for ch in getattr(c, 'children', []):
        if getattr(ch, 'children', None):
            found_label = True
    assert found_label


def test_score_input_item_plus_minus_and_get_values():
    s = ScoreInputItem(base=100, dun=2, dun_score=30, name='X')
    # initial values
    vals = s.get_values()
    assert vals['base'] == 100
    assert vals['dun'] == 2
    # simulate plus
    s._on_plus()
    vals = s.get_values()
    assert vals['dun'] == 3
    # simulate minus
    s._on_minus()
    s._on_minus()
    vals = s.get_values()
    assert vals['dun'] == 1
