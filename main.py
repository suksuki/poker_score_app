from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.floatlayout import FloatLayout

# Lightweight entry that restores theme/meta on startup and saves them on exit.
from screens import SetupScreen, InputScreen, ScoreScreen, StatisticsScreen
from storage import load_data, save_data
from theme import apply_theme
import theme as _theme
from widgets import IconTextButton
from kivy.clock import Clock
import time
import os


class PokerScoreApp(App):
    def build(self):
        try:
            Window.minimum_width = 360
            Window.minimum_height = 640
        except Exception:
            pass

        # Load saved data first so we can apply theme before creating screens
        try:
            data = load_data() or {}
        except Exception:
            data = {}
        meta = data.get('meta', {}) if isinstance(data, dict) else {}
        theme_name = meta.get('theme')
        try:
            if theme_name:
                apply_theme(theme_name)
        except Exception:
            pass

        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(SetupScreen(name='setup'))
        sm.add_widget(InputScreen(name='input'))
        sm.add_widget(ScoreScreen(name='score'))
        sm.add_widget(StatisticsScreen(name='statistics'))
        # keep a reference to the ScreenManager for diagnostics and on_stop
        try:
            self._sm = sm
        except Exception:
            pass

        # Always start at the Setup screen on application launch per user request
        try:
            sm.current = 'setup'
        except Exception:
            pass

        # Give screens a chance to initialize from loaded data
        try:
            scr = sm.get_screen('setup')
            if hasattr(scr, 'refresh_loaded'):
                try:
                    scr.refresh_loaded()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            scr_score = sm.get_screen('score')
            if hasattr(scr_score, 'rebuild_board'):
                try:
                    scr_score.rebuild_board()
                except Exception:
                    pass
        except Exception:
            pass

        # Note: do not restore last tab; app should always start at Setup

        # Build a root FloatLayout so we can place an overlay above the main content
        # The visible app content (ScreenManager + tab bar) is inside a vertical BoxLayout
        root = FloatLayout()
        content = BoxLayout(orientation='vertical', size_hint=(1, 1))
        # place tab bar at the top (added after the ScreenManager so it's visually on top)
        footer = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(4), padding=(dp(4), dp(4)))
        tabs = [
            ('setup', '设置'),
            ('input', '录入'),
            ('score', '记分'),
            ('statistics', '统计'),
        ]
        tab_buttons = {}

        def _on_tab_press(name, btn):
            try:
                # debounce fast repeated clicks to the SAME tab (ignore if same tab within 250ms)
                last = getattr(self, '_last_tab_press', 0)
                last_name = getattr(self, '_last_tab_name', None)
                now = time.time()
                if now - last < 0.25 and name == last_name:
                    return
                self._last_tab_press = now
                self._last_tab_name = name

                # clear focus from any TextInput to avoid focus/keyboard blocking navigation
                try:
                    from kivy.uix.textinput import TextInput
                    def _clear_focus(w):
                        try:
                            if isinstance(w, TextInput):
                                w.focus = False
                        except Exception:
                            pass
                        try:
                            for c in getattr(w, 'children', []):
                                _clear_focus(c)
                        except Exception:
                            pass
                    try:
                        _clear_focus(App.get_running_app().root)
                    except Exception:
                        pass
                    try:
                        from kivy.core.window import Window
                        if hasattr(Window, 'release_all_keyboards'):
                            try:
                                Window.release_all_keyboards()
                            except Exception:
                                pass
                    except Exception:
                        pass
                except Exception:
                    pass

                # remove any overlays or stray widgets above main content that may block touches
                try:
                    root_ref = getattr(self, '_root', None)
                    content_ref = getattr(self, '_content', None)
                    if root_ref is not None and content_ref is not None:
                        overlay_layer = getattr(self, '_overlay_layer', None)
                        for ch in list(root_ref.children):
                            if ch is content_ref:
                                continue
                            try:
                                # if this is the overlay_layer, clear its children instead of removing the layer
                                if overlay_layer is not None and ch is overlay_layer:
                                    try:
                                        self.clear_overlays()
                                    except Exception:
                                        pass
                                    continue
                                try:
                                    root_ref.remove_widget(ch)
                                except Exception:
                                    pass
                            except Exception:
                                pass
                except Exception:
                    pass

                # switch screen immediately; run heavier init on next frame
                try:
                    sm.current = name
                except Exception:
                    try:
                        setattr(sm, 'current', name)
                    except Exception:
                        pass

                def _do_init(dt):
                    try:
                        # after switching, ensure the target screen initializes
                        if name == 'setup':
                            scr = sm.get_screen('setup')
                            if hasattr(scr, 'refresh_loaded'):
                                try:
                                    # if the screen isn't yet mounted to parent, retry a few times
                                    def _attempt_refresh(attempts_left=6):
                                        try:
                                            parent_now = getattr(scr, 'parent', None)
                                            if parent_now is None and attempts_left > 0:
                                                Clock.schedule_once(lambda dt: _attempt_refresh(attempts_left-1), 0.06)
                                                return
                                            try:
                                                scr.refresh_loaded()
                                            except Exception:
                                                pass
                                        except Exception:
                                            pass
                                    _attempt_refresh()
                                except Exception:
                                    pass
                        elif name == 'input':
                            scr = sm.get_screen('input')
                            try:
                                from kivy.app import App as _App
                                active = getattr(_App.get_running_app(), '_game_active', False)
                            except Exception:
                                active = False
                            if active:
                                if hasattr(scr, 'rows_container') and hasattr(scr, 'set_players'):
                                    try:
                                        from storage import load_data
                                        data = load_data() or {}
                                        players = data.get('players') or []
                                        scr.set_players(players)
                                    except Exception:
                                        pass
                            else:
                                try:
                                    if hasattr(scr, 'set_players'):
                                        scr.set_players([])
                                except Exception:
                                    pass
                                try:
                                    root_ref = getattr(self, '_root', None)
                                    content_ref = getattr(self, '_content', None)
                                    if root_ref is not None and content_ref is not None:
                                        overlay_layer = getattr(self, '_overlay_layer', None)
                                        for ch in list(root_ref.children):
                                            if ch is content_ref:
                                                continue
                                            try:
                                                if overlay_layer is not None and ch is overlay_layer:
                                                    try:
                                                        self.clear_overlays()
                                                    except Exception:
                                                        pass
                                                    continue
                                                try:
                                                    root_ref.remove_widget(ch)
                                                except Exception:
                                                    pass
                                            except Exception:
                                                pass
                                except Exception:
                                    pass
                        elif name == 'score':
                            scr = sm.get_screen('score')
                            try:
                                from kivy.app import App as _App
                                active = getattr(_App.get_running_app(), '_game_active', False)
                            except Exception:
                                active = False
                            if active:
                                if hasattr(scr, 'rebuild_board'):
                                    try:
                                        scr.rebuild_board()
                                    except Exception:
                                        pass
                            else:
                                try:
                                    # Always rebuild the score board when navigating to the score
                                    # page so previously saved rounds are visible even if no
                                    # active game is running.
                                    if hasattr(scr, 'rebuild_board'):
                                        try:
                                            scr.rebuild_board()
                                        except Exception:
                                            # fallback to clearing if rebuild fails for some reason
                                            try:
                                                scr.board_box.clear_widgets()
                                            except Exception:
                                                pass
                                    else:
                                        try:
                                            scr.board_box.clear_widgets()
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                    except Exception:
                        pass

                Clock.schedule_once(_do_init, 0)
            except Exception:
                pass

 
            try:
                # update tab label colors immediately for the newly selected tab
                for nm, b in tab_buttons.items():
                    try:
                        if nm == name:
                            b._label.color = _theme.ACCENT
                            try:
                                b._label.text = f"[b]{b._raw_text}[/b]"
                                b._label.font_size = sp(16)
                            except Exception:
                                pass
                        else:
                            b._label.color = _theme.TEXT_COLOR
                            try:
                                b._label.text = b._raw_text
                                b._label.font_size = _theme.SMALL_FONT
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass
        def _on_theme_change():
            try:
                # update tab label colors according to current tab
                for nm, b in tab_buttons.items():
                    try:
                        if nm == sm.current:
                            b._label.color = _theme.ACCENT
                            try:
                                b._label.text = f"[b]{b._raw_text}[/b]"
                                b._label.font_size = sp(16)
                            except Exception:
                                pass
                        else:
                            b._label.color = _theme.TEXT_COLOR
                            try:
                                b._label.text = b._raw_text
                                b._label.font_size = _theme.SMALL_FONT
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                # update global ops buttons colors if present
                go = getattr(self, '_global_ops', None)
                if go is not None:
                    for ch in go.children:
                        try:
                            if hasattr(ch, '_label'):
                                ch._label.color = _theme.TEXT_COLOR
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                # refresh score board (rebuild uses theme constants)
                scr_score = sm.get_screen('score')
                if hasattr(scr_score, 'rebuild_board'):
                    scr_score.rebuild_board()
            except Exception:
                pass
            try:
                # let setup screen refresh any loaded UI
                scr_setup = sm.get_screen('setup')
                if hasattr(scr_setup, 'refresh_loaded'):
                    scr_setup.refresh_loaded()
            except Exception:
                pass
            try:
                # re-render input rows so ranks/trophy colors update
                scr_input = sm.get_screen('input')
                if hasattr(scr_input, 'rows_container') and hasattr(scr_input, '_render_rows_from_order'):
                    children_tb = list(scr_input.rows_container.children)[::-1]
                    scr_input._render_rows_from_order(children_tb)
            except Exception:
                pass

        # Create tab buttons and bind handlers
        for tab_name, tab_label in tabs:
            btn = IconTextButton(text=tab_label, icon='')
            btn._raw_text = tab_label
            btn.bind(on_press=lambda inst, n=tab_name: _on_tab_press(n, inst))
            footer.add_widget(btn)
            tab_buttons[tab_name] = btn

        try:
            _theme.register_theme_listener(_on_theme_change)
            # call once to ensure initial application
            _on_theme_change()
        except Exception:
            pass

        # add footer first so it appears at the top, then ScreenManager fills remaining space
        content.add_widget(footer)
        content.add_widget(sm)
        root.add_widget(content)
        # overlay_layer sits above `content` and receives all temporary overlays
        try:
            # create overlay layer but do not attach to root yet. We'll attach
            # it on-demand when the first overlay is added to avoid blocking
            # touches when there are no overlays.
            overlay_layer = FloatLayout(size_hint=(1, 1))
            self._overlay_layer = overlay_layer
            # mapping of named overlays currently attached to the layer
            self._overlays = {}
            # queued overlays (added before layer attached)
            if not hasattr(self, '_overlay_queue'):
                self._overlay_queue = []
                self._queued_overlays = {}
        except Exception:
            pass
        # keep references to main content and root for overlay cleanup
        try:
            self._root = root
            self._content = content
        except Exception:
            pass

        # Diagnostic output to help track widget tree at startup
        try:
            # verbose startup diagnostics removed
            pass
        except Exception:
            pass

        # Create a global import/export bar at the bottom of the page container
        try:
            global_ops = BoxLayout(size_hint=(1, None), height=dp(48), spacing=dp(6), padding=(dp(4), dp(4)))
            imp_btn = IconTextButton(text='导入 JSON', icon='file-upload')
            exp_btn = IconTextButton(text='导出 JSON', icon='file-download')
            try:
                imp_btn.bind(on_press=lambda *_: sm.get_screen('input').import_json_dialog())
                try:
                    imp_btn.bind(on_release=lambda *_: sm.get_screen('input').import_json_dialog())
                except Exception:
                    pass
            except Exception:
                pass
            try:
                exp_btn.bind(on_press=lambda *_: sm.get_screen('input').export_json_dialog())
                try:
                    exp_btn.bind(on_release=lambda *_: sm.get_screen('input').export_json_dialog())
                except Exception:
                    pass
            except Exception:
                pass
            try:
                imp_btn.size_hint_x = 1
                exp_btn.size_hint_x = 1
            except Exception:
                pass
            global_ops.add_widget(imp_btn)
            global_ops.add_widget(exp_btn)
            # add to content (bottom of the page container)
            try:
                content.add_widget(global_ops)
            except Exception:
                # fallback: add to root if content not available
                try:
                    root.add_widget(global_ops)
                except Exception:
                    pass
            try:
                # keep a reference for screens if needed
                self._global_ops = global_ops
            except Exception:
                pass
        except Exception:
            pass

        return root

    # Overlay management helpers
    def add_overlay(self, widget, name: str = None):
        try:
            layer = getattr(self, '_overlay_layer', None)
            root_ref = getattr(self, '_root', None)
            # if layer not yet created, queue the overlay for later
            if layer is None:
                try:
                    if not hasattr(self, '_overlay_queue'):
                        self._overlay_queue = []
                        self._queued_overlays = {}
                except Exception:
                    pass
                try:
                    self._overlay_queue.append((widget, name))
                    if name:
                        try:
                            self._queued_overlays[name] = widget
                        except Exception:
                            pass
                except Exception:
                    pass
                return
            # ensure the overlay layer is attached to root so it is visible and can host widgets
            try:
                if getattr(layer, 'parent', None) is None and root_ref is not None:
                    try:
                        root_ref.add_widget(layer)
                    except Exception:
                        pass
            except Exception:
                pass

            # layer exists: add immediately
            layer.add_widget(widget)
            if name:
                try:
                    self._overlays[name] = widget
                except Exception:
                    pass
        except Exception:
            pass

    def remove_overlay(self, widget=None, name: str = None):
        try:
            layer = getattr(self, '_overlay_layer', None)
            # if layer not created yet, try to remove from queue
            if layer is None:
                try:
                    if name and getattr(self, '_queued_overlays', None) is not None:
                        self._queued_overlays.pop(name, None)
                    if getattr(self, '_overlay_queue', None) is not None:
                        # remove matching widget(s) from queue
                        newq = []
                        for w, n in list(self._overlay_queue):
                            if (name and n == name) or (widget is not None and w is widget):
                                continue
                            newq.append((w, n))
                        self._overlay_queue = newq
                except Exception:
                    pass
                return
            target = None
            if name and getattr(self, '_overlays', None) is not None:
                target = self._overlays.pop(name, None)
            if widget is not None:
                target = widget
            if target is not None:
                try:
                    # if target is queued (unlikely here), remove from queued map too
                    if getattr(self, '_queued_overlays', None) is not None:
                        try:
                            # reverse lookup
                            for k, v in list(getattr(self, '_queued_overlays', {}).items()):
                                if v is target:
                                    self._queued_overlays.pop(k, None)
                        except Exception:
                            pass
                    if target.parent is layer:
                        try:
                            layer.remove_widget(target)
                        except Exception:
                            pass
                        # if layer now has no children, detach it from root to restore underlying touch handling
                        try:
                            if len(layer.children) == 0:
                                try:
                                    root_ref = getattr(self, '_root', None)
                                    if root_ref is not None and layer in list(root_ref.children):
                                        root_ref.remove_widget(layer)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    def clear_overlays(self):
        try:
            # clear any queued overlays first
            try:
                if getattr(self, '_overlay_queue', None) is not None:
                    try:
                        self._overlay_queue = []
                    except Exception:
                        pass
                if getattr(self, '_queued_overlays', None) is not None:
                    try:
                        self._queued_overlays = {}
                    except Exception:
                        pass
            except Exception:
                pass
            layer = getattr(self, '_overlay_layer', None)
            if layer is None:
                # nothing attached
                try:
                    self._overlays = {}
                except Exception:
                    pass
                return
            for ch in list(layer.children):
                try:
                    layer.remove_widget(ch)
                except Exception:
                    pass
            try:
                self._overlays = {}
            except Exception:
                pass
            # if layer is now empty, detach it from root to restore touch handling
            try:
                if len(layer.children) == 0:
                    try:
                        root_ref = getattr(self, '_root', None)
                        if root_ref is not None and layer in list(root_ref.children):
                            root_ref.remove_widget(layer)
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass
        

    def on_stop(self):
        # persist last viewed tab and theme
        try:
            data = load_data() or {}
        except Exception:
            data = {}
        if not isinstance(data, dict):
            data = {}
        meta = data.setdefault('meta', {})
        try:
            # persist the last viewed tab from the ScreenManager (not the root BoxLayout)
            meta['last_tab'] = (getattr(self, '_sm', None).current if getattr(self, '_sm', None) is not None else meta.get('last_tab'))
        except Exception:
            pass
        try:
            meta['theme'] = getattr(_theme, 'CURRENT_THEME', None)
        except Exception:
            pass
        try:
            save_data(data)
        except Exception:
            pass
        # best-effort cleanup: cancel known scheduled events on screens and clear overlays
        try:
            # cancel any lingering drag poll or other Clock events stored on screens
            for screen_name in ('input', 'setup', 'score', 'statistics'):
                try:
                    scr = self._sm.get_screen(screen_name)
                    # common event attribute used by input drag logic
                    ev = getattr(scr, '_simple_drag_ev', None)
                    if ev is not None:
                        try:
                            ev.cancel()
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass
        try:
            # remove any overlays to avoid UI elements lingering after exit
            self.clear_overlays()
        except Exception:
            pass


if __name__ == '__main__':
    PokerScoreApp().run()
