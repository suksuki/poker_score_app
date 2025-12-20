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

# Configure Kivy keyboard mode early
if sys.platform.startswith('win'):
    Config.set('kivy', 'keyboard_mode', 'system')

from screens import SetupScreen, InputScreen, ScoreScreen, StatisticsScreen
from storage import load_data, save_data
from theme import theme_manager
from widgets import IconTextButton
from utils.logger import logger

class PokerScoreApp(App):
    def build(self):
        Window.minimum_width = 360
        Window.minimum_height = 640
        self.title = "Poker Score"

        # Load saved data first
        data = load_data() or {}
        meta = data.get('meta', {}) if isinstance(data, dict) else {}
        
        # Apply theme
        theme_name = meta.get('theme', 'light')
        theme_manager.switch_theme(theme_name)

        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(SetupScreen(name='setup'))
        self.sm.add_widget(InputScreen(name='input'))
        self.sm.add_widget(ScoreScreen(name='score'))
        self.sm.add_widget(StatisticsScreen(name='statistics'))

        self.sm.current = 'setup'

        # Refresh Setup Screen
        self._safe_refresh_screen('setup')

        self.root_layout = FloatLayout()
        self.content = BoxLayout(orientation='vertical', size_hint=(1, 1))

        # Footer (Tab Bar)
        footer = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(4), padding=(dp(4), dp(4)))
        self.tabs = [
            ('setup', '设置'),
            ('input', '录入'),
            ('score', '记分'),
            ('statistics', '统计'),
        ]
        self.tab_buttons = {}

        for tab_name, tab_label in self.tabs:
            btn = IconTextButton(text=tab_label, icon='')
            btn._raw_text = tab_label
            btn.bind(on_press=lambda inst, n=tab_name: self._on_tab_press(n, inst))
            footer.add_widget(btn)
            self.tab_buttons[tab_name] = btn

        # Bind theme changes to update tab styles
        theme_manager.bind(current_theme=self._update_tab_styles)
        theme_manager.bind(accent=self._update_tab_styles)
        theme_manager.bind(text_color=self._update_tab_styles)
        self._update_tab_styles()

        self.content.add_widget(footer)
        self.content.add_widget(self.sm)
        self.root_layout.add_widget(self.content)

        # Overlay Layer
        self.overlay_layer = FloatLayout(size_hint=(1, 1))
        self.overlays = {}
        self.overlay_queue = []

        # Global operations (Import/Export)
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

    def _safe_refresh_screen(self, name):
        try:
            scr = self.sm.get_screen(name)
            if hasattr(scr, 'refresh_loaded'):
                scr.refresh_loaded()
            elif hasattr(scr, 'rebuild_board'):
                scr.rebuild_board()
        except Exception as e:
            logger.error(f"Error refreshing screen {name}: {e}")

    def _on_tab_press(self, name, btn):
        # Debounce
        last = getattr(self, '_last_tab_press', 0)
        if time.time() - last < 0.25 and getattr(self, '_last_tab_name', None) == name:
            return
        self._last_tab_press = time.time()
        self._last_tab_name = name

        # Clear focus
        if self.root:
            self._clear_focus(self.root)
        Window.release_all_keyboards()

        # Remove Overlays
        self.clear_overlays()

        # Switch
        self.sm.current = name
        self._update_tab_styles()
        
        # Init screen
        Clock.schedule_once(lambda dt: self._do_init_screen(name), 0)

    def _clear_focus(self, widget):
        from kivy.uix.textinput import TextInput
        if isinstance(widget, TextInput):
            widget.focus = False
        for c in getattr(widget, 'children', []):
            self._clear_focus(c)

    def _do_init_screen(self, name):
        if name == 'setup':
            self._safe_refresh_screen('setup')
        elif name == 'input':
            scr = self.sm.get_screen('input')
            active = getattr(self, '_game_active', False)
            if active and hasattr(scr, 'set_players'):
                data = load_data() or {}
                scr.set_players(data.get('players', []))
            elif hasattr(scr, 'set_players'):
                scr.set_players([])
                self.clear_overlays()
        elif name == 'score':
            self._safe_refresh_screen('score')

    def _update_tab_styles(self, *args):
        current = self.sm.current
        for nm, btn in self.tab_buttons.items():
            if nm == current:
                btn._label.color = theme_manager.accent
                btn._label.text = f"[b]{btn._raw_text}[/b]"
                btn._label.font_size = sp(16)
            else:
                btn._label.color = theme_manager.text_color
                btn._label.text = btn._raw_text
                btn._label.font_size = theme_manager.small_font
    
    # Overlay Methods
    def add_overlay(self, widget, name: str = None):
        if not self.overlay_layer: return
        if not self.overlay_layer.parent:
            self.root_layout.add_widget(self.overlay_layer)
        
        self.overlay_layer.add_widget(widget)
        if name: self.overlays[name] = widget

    def remove_overlay(self, widget=None, name: str = None):
        if not self.overlay_layer: return
        
        target = None
        if name and name in self.overlays:
            target = self.overlays.pop(name)
        elif widget:
            target = widget
            
        if target and target.parent == self.overlay_layer:
            self.overlay_layer.remove_widget(target)
            
        if not self.overlay_layer.children and self.overlay_layer.parent:
            self.root_layout.remove_widget(self.overlay_layer)

    def clear_overlays(self):
        if not self.overlay_layer: return
        self.overlay_layer.clear_widgets()
        self.overlays.clear()
        if self.overlay_layer.parent:
            self.root_layout.remove_widget(self.overlay_layer)

    def on_stop(self):
        # Save meta
        data = load_data() or {}
        if not isinstance(data, dict): data = {}
        meta = data.setdefault('meta', {})
        meta['theme'] = theme_manager.current_theme
        save_data(data)
        logger.info("App stopped, data saved.")

if __name__ == '__main__':
    PokerScoreApp().run()
