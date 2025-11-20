import types
from main import PokerScoreApp
import theme as _theme


class DummyCancel:
    def __init__(self):
        self.cancelled = False

    def cancel(self):
        self.cancelled = True


class DummyScreen:
    def __init__(self):
        self._simple_drag_ev = DummyCancel()


class DummySM:
    def __init__(self, current='score'):
        self._screens = {n: DummyScreen() for n in ('input', 'setup', 'score', 'statistics')}
        self.current = current

    def get_screen(self, name):
        return self._screens.get(name)


def test_add_overlay_queue_and_remove():
    app = PokerScoreApp()
    # ensure no overlay layer exists
    try:
        delattr(app, '_overlay_layer')
    except Exception:
        pass
    # add overlay while layer is None -> should queue
    w = object()
    app.add_overlay(w, name='x')
    assert getattr(app, '_overlay_queue', None) is not None
    assert getattr(app, '_queued_overlays', {}).get('x') is w

    # remove by name should remove from queued map
    app.remove_overlay(name='x')
    assert 'x' not in getattr(app, '_queued_overlays', {})


def test_on_stop_cancels_events_and_saves_meta(monkeypatch):
    app = PokerScoreApp()
    # set fake ScreenManager with screens that have cancelable events
    sm = DummySM(current='input')
    app._sm = sm

    saved = {}

    def fake_save(data):
        saved['data'] = data

    monkeypatch.setattr('main.save_data', fake_save)
    # set theme
    _theme.CURRENT_THEME = 'dark-test'

    # monkeypatch clear_overlays to mark called
    called = {'cleared': False}

    def fake_clear():
        called['cleared'] = True

    app.clear_overlays = fake_clear

    app.on_stop()

    # ensure save_data was called and meta contains expected keys
    assert 'data' in saved
    meta = saved['data'].get('meta', {})
    assert meta.get('theme') == 'dark-test'
    # last_tab should reflect current screen
    assert meta.get('last_tab') == 'input'
    # ensure clear_overlays was invoked
    assert called['cleared'] is True
    # ensure each dummy screen's cancel was called
    for s in sm._screens.values():
        assert s._simple_drag_ev.cancelled is True
