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
                # set current immediately so UI switches; run heavier init on next frame
                try:
                    try:
                        setattr(sm, 'current', name)
                    except Exception:
                        sm.current = name
                except Exception:
                    pass
                try:
                    def _do_init(dt):
                        try:
                            # after switching, ensure the target screen initializes
                            if name == 'setup':
                                scr = sm.get_screen('setup')
                                if hasattr(scr, 'refresh_loaded'):
                                    try:
                                        scr.refresh_loaded()
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
                                            # load players from storage only when game active
                                            from storage import load_data
                                            data = load_data() or {}
                                            players = data.get('players') or []
                                            scr.set_players(players)
                                        except Exception:
                                            pass
                                else:
                                    # ensure input screen is empty if game not started
                                    try:
                                        if hasattr(scr, 'set_players'):
                                            scr.set_players([])
                                    except Exception:
                                        pass
                                    # also remove any overlays or leftover widgets added to root
                                    try:
                                        root_ref = getattr(self, '_root', None)
                                        content_ref = getattr(self, '_content', None)
                                        if root_ref is not None and content_ref is not None:
                                            for ch in list(root_ref.children):
                                                if ch is not content_ref:
                                                    try:
                                                        root_ref.remove_widget(ch)
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
                                    # clear board when game not started
                                    try:
                                        scr.board_box.clear_widgets()
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                    Clock.schedule_once(_do_init, 0)
                except Exception:
                    pass
            except Exception:
                pass
            try:
                # debug: confirm current changed
                print(f"[DEBUG] requested tab change to {name}, sm.current now={getattr(sm, 'current', None)}")
            except Exception:
                pass
            for nm, b in tab_buttons.items():
                try:
                    if nm == name:
                        try:
                            b._label.color = _theme.ACCENT
                            try:
                                b._label.text = f"[b]{b._raw_text}[/b]"
                                b._label.font_size = sp(16)
                            except Exception:
                                pass
                        except Exception:
                            pass
                    else:
                        try:
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

        for name, label in tabs:
            try:
                btn = IconTextButton(text=label)
                btn.size_hint_x = 1
                # bind both press and release to improve responsiveness across platforms
                btn.bind(on_press=lambda inst, n=name: _on_tab_press(n, inst))
                try:
                    btn.bind(on_release=lambda inst, n=name: _on_tab_press(n, inst))
                except Exception:
                    pass
                footer.add_widget(btn)
                tab_buttons[name] = btn
            except Exception:
                pass

        # apply initial active style
        try:
            cur = sm.current
            for nm, b in tab_buttons.items():
                try:
                    # selected tab: larger bold label
                    if nm == cur:
                        try:
                            b._label.color = _theme.ACCENT
                            b._label.text = f"[b]{b._raw_text}[/b]"
                            b._label.font_size = sp(16)
                        except Exception:
                            pass
                    else:
                        try:
                            b._label.color = _theme.TEXT_COLOR
                            b._label.text = b._raw_text
                            b._label.font_size = _theme.SMALL_FONT
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

        # register a theme-change listener to refresh dynamic visuals when theme changes
        try:
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

            try:
                _theme.register_theme_listener(_on_theme_change)
                # call once to ensure initial application
                _on_theme_change()
            except Exception:
                pass
        except Exception:
            pass

        # add footer first so it appears at the top, then ScreenManager fills remaining space
        content.add_widget(footer)
        content.add_widget(sm)
        root.add_widget(content)
        # keep references to main content and root for overlay cleanup
        try:
            self._root = root
            self._content = content
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
        # Diagnostic output to help track widget tree at startup
        try:
            print(f"[DEBUG] ScreenManager has {len(sm.screens)} screens; current={sm.current}")
            for s in sm.screens:
                try:
                    print(f"[DEBUG] screen {s.name} children={len(s.children)} types={[type(c).__name__ for c in s.children]}")
                except Exception:
                    pass
            try:
                print(f"[DEBUG] global_ops children={len(global_ops.children)}")
            except Exception:
                pass
        except Exception:
            pass

        return root

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


if __name__ == '__main__':
    PokerScoreApp().run()
