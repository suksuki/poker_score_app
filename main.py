import sys
import os
import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.config import Config

# Configure Kivy keyboard mode early on Windows so IME composition works
if sys.platform.startswith('win'):
    Config.set('kivy', 'keyboard_mode', 'system')

# Lightweight entry that restores theme/meta on startup and saves them on exit.
from screens import SetupScreen, InputScreen, ScoreScreen, StatisticsScreen
from storage import load_data, save_data
from theme import apply_theme
import theme as _theme
from widgets import IconTextButton


class PokerScoreApp(App):
    def build(self):
        Window.minimum_width = 360
        Window.minimum_height = 640

        # Load saved data first so we can apply theme before creating screens
        data = load_data() or {}
        meta = data.get('meta', {}) if isinstance(data, dict) else {}
        theme_name = meta.get('theme')
        if theme_name:
            apply_theme(theme_name)

        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(SetupScreen(name='setup'))
        self.sm.add_widget(InputScreen(name='input'))
        self.sm.add_widget(ScoreScreen(name='score'))
        self.sm.add_widget(StatisticsScreen(name='statistics'))

        # Always start at the Setup screen on application launch per user request
        self.sm.current = 'setup'

        # Give screens a chance to initialize from loaded data
        scr = self.sm.get_screen('setup')
        if hasattr(scr, 'refresh_loaded'):
            scr.refresh_loaded()

        scr_score = self.sm.get_screen('score')
        if hasattr(scr_score, 'rebuild_board'):
            scr_score.rebuild_board()

        # Build a root FloatLayout so we can place an overlay above the main content
        self.root_layout = FloatLayout()
        self.content = BoxLayout(orientation='vertical', size_hint=(1, 1))

        # place tab bar at the top (added after the ScreenManager so it's visually on top)
        footer = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(4), padding=(dp(4), dp(4)))
        tabs = [
            ('setup', '设置'),
            ('input', '录入'),
            ('score', '记分'),
            ('statistics', '统计'),
        ]
        self.tab_buttons = {}

        for tab_name, tab_label in tabs:
            btn = IconTextButton(text=tab_label, icon='')
            btn._raw_text = tab_label
            btn.bind(on_press=lambda inst, n=tab_name: self._on_tab_press(n, inst))
            footer.add_widget(btn)
            self.tab_buttons[tab_name] = btn

        _theme.register_theme_listener(self._on_theme_change)
        # call once to ensure initial application
        self._on_theme_change()

        # add footer first so it appears at the top, then ScreenManager fills remaining space
        self.content.add_widget(footer)
        self.content.add_widget(self.sm)
        self.root_layout.add_widget(self.content)

        # overlay_layer sits above `content` and receives all temporary overlays
        self.overlay_layer = FloatLayout(size_hint=(1, 1))
        # mapping of named overlays currently attached to the layer
        self.overlays = {}
        # queued overlays (added before layer attached)
        self.overlay_queue = []
        self.queued_overlays = {}

        # Create a global import/export bar at the bottom of the page container
        self.global_ops = BoxLayout(size_hint=(1, None), height=dp(48), spacing=dp(6), padding=(dp(4), dp(4)))
        imp_btn = IconTextButton(text='导入 JSON', icon='file-upload')
        exp_btn = IconTextButton(text='导出 JSON', icon='file-download')

        imp_btn.bind(on_release=lambda *_: self.sm.get_screen('input').import_json_dialog())
        exp_btn.bind(on_release=lambda *_: self.sm.get_screen('input').export_json_dialog())

        imp_btn.size_hint_x = 1
        exp_btn.size_hint_x = 1

        self.global_ops.add_widget(imp_btn)
        self.global_ops.add_widget(exp_btn)
        self.content.add_widget(self.global_ops)

        return self.root_layout

    def _on_tab_press(self, name, btn):
        # debounce fast repeated clicks to the SAME tab (ignore if same tab within 250ms)
        last = getattr(self, '_last_tab_press', 0)
        last_name = getattr(self, '_last_tab_name', None)
        now = time.time()
        if now - last < 0.25 and name == last_name:
            return
        self._last_tab_press = now
        self._last_tab_name = name

        # clear focus from any TextInput to avoid focus/keyboard blocking navigation
        from kivy.uix.textinput import TextInput
        def _clear_focus(w):
            if isinstance(w, TextInput):
                w.focus = False
            for c in getattr(w, 'children', []):
                _clear_focus(c)
        
        if self.root:
             _clear_focus(self.root)
        
        if hasattr(Window, 'release_all_keyboards'):
            Window.release_all_keyboards()

        # remove any overlays or stray widgets above main content that may block touches
        if self.root_layout and self.content:
            for ch in list(self.root_layout.children):
                if ch is self.content:
                    continue
                # if this is the overlay_layer, clear its children instead of removing the layer
                if self.overlay_layer and ch is self.overlay_layer:
                    self.clear_overlays()
                    continue
                self.root_layout.remove_widget(ch)

        # switch screen immediately; run heavier init on next frame
        self.sm.current = name

        Clock.schedule_once(lambda dt: self._do_init_screen(name), 0)

    def _do_init_screen(self, name):
        # after switching, ensure the target screen initializes
        if name == 'setup':
            scr = self.sm.get_screen('setup')
            if hasattr(scr, 'refresh_loaded'):
                # if the screen isn't yet mounted to parent, retry a few times
                def _attempt_refresh(attempts_left=6):
                    if not scr.children and attempts_left > 0:
                        Clock.schedule_once(lambda dt: _attempt_refresh(attempts_left-1), 0.06)
                        return
                    scr.refresh_loaded()
                _attempt_refresh()

        elif name == 'input':
            scr = self.sm.get_screen('input')
            active = getattr(App.get_running_app(), '_game_active', False)
            if active:
                if hasattr(scr, 'rows_container') and hasattr(scr, 'set_players'):
                    data = load_data() or {}
                    players = data.get('players') or []
                    scr.set_players(players)
            else:
                if hasattr(scr, 'set_players'):
                    scr.set_players([])
                # Cleanup overlays if any
                self.clear_overlays()

        elif name == 'score':
            scr = self.sm.get_screen('score')
            active = getattr(App.get_running_app(), '_game_active', False)
            if active:
                 if hasattr(scr, 'rebuild_board'):
                    scr.rebuild_board()
            else:
                # Always rebuild the score board when navigating to the score
                # page so previously saved rounds are visible even if no
                # active game is running.
                if hasattr(scr, 'rebuild_board'):
                    scr.rebuild_board()
                else:
                    scr.board_box.clear_widgets()

        # update tab label colors immediately for the newly selected tab
        self._on_theme_change()

    def _on_theme_change(self):
        # update tab label colors according to current tab
        current_tab = self.sm.current
        for nm, b in self.tab_buttons.items():
            if nm == current_tab:
                b._label.color = _theme.ACCENT
                b._label.text = f"[b]{b._raw_text}[/b]"
                b._label.font_size = sp(16)
            else:
                b._label.color = _theme.TEXT_COLOR
                b._label.text = b._raw_text
                b._label.font_size = _theme.SMALL_FONT

        # update global ops buttons colors if present
        if self.global_ops:
            for ch in self.global_ops.children:
                if hasattr(ch, '_label'):
                    ch._label.color = _theme.TEXT_COLOR

        # refresh score board (rebuild uses theme constants)
        try:
            scr_score = self.sm.get_screen('score')
            if hasattr(scr_score, 'rebuild_board'):
                scr_score.rebuild_board()
        except Exception:
            pass # Screen might not be ready

        # let setup screen refresh any loaded UI
        try:
            scr_setup = self.sm.get_screen('setup')
            if hasattr(scr_setup, 'refresh_loaded'):
                scr_setup.refresh_loaded()
        except Exception:
             pass

        # re-render input rows so ranks/trophy colors update
        try:
            scr_input = self.sm.get_screen('input')
            if hasattr(scr_input, 'rows_container') and hasattr(scr_input, '_render_rows_from_order'):
                children_tb = list(scr_input.rows_container.children)[::-1]
                scr_input._render_rows_from_order(children_tb)
        except Exception:
             pass

    # Overlay management helpers
    def add_overlay(self, widget, name: str = None):
        # if layer not yet created, queue the overlay for later
        if not hasattr(self, 'overlay_layer') or self.overlay_layer is None:
            self.overlay_queue.append((widget, name))
            if name:
                self.queued_overlays[name] = widget
            return

        # ensure the overlay layer is attached to root so it is visible and can host widgets
        if self.overlay_layer.parent is None:
            self.root_layout.add_widget(self.overlay_layer)

        # layer exists: add immediately
        self.overlay_layer.add_widget(widget)
        if name:
            self.overlays[name] = widget

    def remove_overlay(self, widget=None, name: str = None):
        if not hasattr(self, 'overlay_layer') or self.overlay_layer is None:
            # if layer not created yet, try to remove from queue
            if name and name in self.queued_overlays:
                self.queued_overlays.pop(name, None)
            
            # remove matching widget(s) from queue
            newq = []
            for w, n in self.overlay_queue:
                if (name and n == name) or (widget is not None and w is widget):
                    continue
                newq.append((w, n))
            self.overlay_queue = newq
            return
            
        target = None
        if name and name in self.overlays:
            target = self.overlays.pop(name, None)
        if widget is not None:
             target = widget
        
        if target is not None:
             if target.parent == self.overlay_layer:
                self.overlay_layer.remove_widget(target)
                
                # if layer now has no children, detach it from root to restore underlying touch handling
                if len(self.overlay_layer.children) == 0:
                    if self.overlay_layer in self.root_layout.children:
                        self.root_layout.remove_widget(self.overlay_layer)

    def clear_overlays(self):
        # clear any queued overlays first
        self.overlay_queue = []
        self.queued_overlays = {}
        
        if not hasattr(self, 'overlay_layer') or self.overlay_layer is None:
            self.overlays = {}
            return

        self.overlay_layer.clear_widgets()
        self.overlays = {}
        
        # if layer is now empty, detach it from root to restore touch handling
        if len(self.overlay_layer.children) == 0:
            if self.overlay_layer in self.root_layout.children:
                self.root_layout.remove_widget(self.overlay_layer)

    def on_stop(self):
        # persist last viewed tab and theme
        data = load_data() or {}
        if not isinstance(data, dict):
            data = {}
        meta = data.setdefault('meta', {})
        
        meta['last_tab'] = self.sm.current if hasattr(self, 'sm') else meta.get('last_tab')
        meta['theme'] = getattr(_theme, 'CURRENT_THEME', None)
        
        save_data(data)
        
        # best-effort cleanup: cancel known scheduled events on screens and clear overlays
        # cancel any lingering drag poll or other Clock events stored on screens
        for screen_name in ('input', 'setup', 'score', 'statistics'):
            try:
                scr = self.sm.get_screen(screen_name)
                # common event attribute used by input drag logic
                ev = getattr(scr, '_simple_drag_ev', None)
                if ev is not None:
                    ev.cancel()
            except Exception:
                pass

        self.clear_overlays()


if __name__ == '__main__':
    PokerScoreApp().run()
