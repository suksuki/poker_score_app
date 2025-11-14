from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window

# Lightweight entry that restores theme/meta on startup and saves them on exit.
from screens import SetupScreen, InputScreen, ScoreScreen, StatisticsScreen
from storage import load_data, save_data
from theme import apply_theme, CURRENT_THEME


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

        return sm

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
            meta['last_tab'] = (self.root.current if getattr(self, 'root', None) is not None else meta.get('last_tab'))
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
