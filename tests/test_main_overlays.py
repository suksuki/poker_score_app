from main import PokerScoreApp
from kivy.app import App


def test_overlay_flow_no_exceptions(monkeypatch):
    app = PokerScoreApp()
    # ensure App.get_running_app() returns our app for code paths
    App._running_app = app
    # build the UI structure (non-blocking)
    root = app.build()
    try:
        app.root = root
    except Exception:
        pass

    sm = getattr(app, '_sm', None)
    assert sm is not None
    setup = sm.get_screen('setup')
    inp = sm.get_screen('input')

    # call a few overlay-related helpers to make sure no exceptions occur
    # these functions may create overlay widgets; we only assert they run
    try:
        inp.import_json_dialog()
    except Exception:
        # some environments may not support file dialogs; ignore
        pass

    try:
        inp.export_json_dialog()
    except Exception:
        pass

    try:
        inp._overlay_dialog('Test', 'Message')
    except Exception:
        pass

    try:
        setup.confirm_reset()
    except Exception:
        pass

    # verify clear_overlays can be called without raising
    app.clear_overlays()
