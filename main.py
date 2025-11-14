from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout

# Lightweight entry that restores theme/meta on startup and saves them on exit.
from screens import SetupScreen, InputScreen, ScoreScreen, StatisticsScreen
from storage import load_data, save_data
from theme import apply_theme, CURRENT_THEME, ACCENT, TEXT_COLOR
from widgets import IconTextButton


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

        # restore last tab if present
        last_tab = meta.get('last_tab') if isinstance(meta, dict) else None
        try:
            if last_tab and last_tab in ('setup', 'input', 'score', 'statistics'):
                sm.current = last_tab
        except Exception:
            pass

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
                sm.current = name
            except Exception:
                pass
            for nm, b in tab_buttons.items():
                try:
                    if nm == name:
                        try:
                            b._label.color = ACCENT
                        except Exception:
                            pass
                    else:
                        try:
                            b._label.color = TEXT_COLOR
                        except Exception:
                            pass
                except Exception:
                    pass

        for name, label in tabs:
            try:
                btn = IconTextButton(text=label)
                btn.size_hint_x = 1
                btn.bind(on_press=lambda inst, n=name: _on_tab_press(n, inst))
                footer.add_widget(btn)
                tab_buttons[name] = btn
            except Exception:
                pass

        # apply initial active style
        try:
            cur = sm.current
            for nm, b in tab_buttons.items():
                try:
                    b._label.color = ACCENT if nm == cur else TEXT_COLOR
                except Exception:
                    pass
        except Exception:
            pass

        # add footer first so it appears at the top, then ScreenManager fills remaining space
        content.add_widget(footer)
        content.add_widget(sm)
        root.add_widget(content)

        # Create a global import/export bar at the bottom of the page container
        try:
            global_ops = BoxLayout(size_hint=(1, None), height=dp(48), spacing=dp(6), padding=(dp(4), dp(4)))
            imp_btn = IconTextButton(text='导入 JSON', icon='file-upload')
            exp_btn = IconTextButton(text='导出 JSON', icon='file-download')
            try:
                imp_btn.bind(on_press=lambda *_: sm.get_screen('input').import_json_dialog())
            except Exception:
                pass
            try:
                exp_btn.bind(on_press=lambda *_: sm.get_screen('input').export_json_dialog())
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
            meta['theme'] = CURRENT_THEME
        except Exception:
            pass
        try:
            save_data(data)
        except Exception:
            pass


if __name__ == '__main__':
    PokerScoreApp().run()
