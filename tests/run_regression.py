# Minimal regression script to exercise overlay APIs without running the GUI loop
import sys, os
# ensure project root is on sys.path so we can import modules when running from tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import PokerScoreApp
from kivy.app import App
import traceback

def safe_call(fn, name):
    try:
        print(f"CALL: {name}")
        res = fn()
        print(f"OK: {name}")
        return res
    except Exception as e:
        print(f"ERR: {name}: {e}")
        traceback.print_exc()
        return None

if __name__ == '__main__':
    app = PokerScoreApp()
    # ensure App.get_running_app() returns our app
    App._running_app = app
    root = safe_call(app.build, 'build')
    # ensure App.root is populated like run() would do
    try:
        app.root = root
    except Exception:
        pass
    sm = getattr(app, '_sm', None)
    print('SM current after build:', getattr(sm, 'current', None))

    setup = sm.get_screen('setup')
    inp = sm.get_screen('input')

    print('\n-- Overlay layer children before any dialogs --')
    layer = getattr(app, '_overlay_layer', None)
    print('overlay_layer present:', layer is not None)
    if layer is not None:
        print('children count:', len(layer.children))

    # call input import dialog
    safe_call(lambda: inp.import_json_dialog(), 'input.import_json_dialog')
    if layer is not None:
        print('after import dialog children:', len(layer.children))

    # call input export dialog
    safe_call(lambda: inp.export_json_dialog(), 'input.export_json_dialog')
    if layer is not None:
        print('after export dialog children:', len(layer.children))

    # call overlay dialog directly
    safe_call(lambda: inp._overlay_dialog('Test', 'Message'), 'input._overlay_dialog')
    if layer is not None:
        print('after _overlay_dialog children:', len(layer.children))

    # call setup confirm_reset
    safe_call(lambda: setup.confirm_reset(), 'setup.confirm_reset')
    if layer is not None:
        print('after confirm_reset children:', len(layer.children))

    # clear overlays explicitly
    safe_call(lambda: app.clear_overlays(), 'app.clear_overlays')
    if layer is not None:
        print('after clear_overlays children:', len(layer.children))

    # test start_and_input flow
    safe_call(lambda: setup.start_and_input(), 'setup.start_and_input')
    print('game_active:', getattr(app, '_game_active', None))
    print('sm.current after start_and_input:', sm.current)
    if layer is not None:
        print('final overlay children:', len(layer.children))

    print('\nRegression script completed')
