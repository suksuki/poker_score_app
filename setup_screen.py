from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp

from widgets import H, L, TI, IconButton, IconTextButton
from storage import load_data, save_data, ensure_backup
from theme import ROW_HEIGHT, CURRENT_THEME, ACCENT, FONT_NAME
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.app import App
import os


class SetupScreen(Screen):
    players = []
    def __init__(self, **kw):
        super().__init__(**kw)
        scroll = ScrollView(size_hint=(1,1))
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        scroll.add_widget(content)
        self.add_widget(scroll)
        content.add_widget(H(text='玩家设置', size_hint_y=None, height=dp(40)))
        self.count = 4
        self._min_players = 1
        self._max_players = 16
        # compact horizontal row: left-aligned player count controls, right-aligned theme toggle
        combined = BoxLayout(size_hint_y=None, height=ROW_HEIGHT, spacing=dp(6), padding=(dp(6), 0))
        left = BoxLayout(spacing=dp(4), size_hint_x=0.6)
        # make label fixed width so controls align predictably on small screens
        left.add_widget(L(text='玩家数量', size_hint_x=None, width=dp(84)))
        # control box with fixed compact width (dec, count, inc) left-aligned
        ctrl = BoxLayout(size_hint_x=None, width=dp(140), spacing=dp(4))
        btn_dec = IconButton('➖', width=dp(36), height=dp(36))
        btn_inc = IconButton('➕', width=dp(36), height=dp(36))
        btn_dec.bind(on_press=lambda *_: self._change_count(-1))
        btn_inc.bind(on_press=lambda *_: self._change_count(1))
        self.count_label = L(text=str(self.count), size_hint=(None, None), width=dp(48), height=dp(36), halign='center', valign='middle')
        self.count_label.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
        ctrl.add_widget(btn_dec)
        ctrl.add_widget(self.count_label)
        ctrl.add_widget(btn_inc)
        left.add_widget(ctrl)
        # right side: theme label + button, right aligned and compact
        right = BoxLayout(spacing=dp(4), size_hint_x=0.4)
        right.add_widget(L(text='主题', size_hint_x=None, width=dp(50)))
        current_text = '亮色' if CURRENT_THEME == 'light' else '暗色'
        self.theme_btn = IconTextButton(text=current_text, icon='wrench', size_hint_x=None)
        try:
            self.theme_btn.width = dp(86)
        except Exception:
            pass
        def _on_theme_toggle(*_):
            try:
                import theme as _theme
                next_theme = 'dark' if _theme.CURRENT_THEME == 'light' else 'light'
                from theme import apply_theme
                apply_theme(next_theme)
                try:
                    # update label to reflect the current theme after applying
                    self.theme_btn._label.text = '亮色' if _theme.CURRENT_THEME == 'light' else '暗色'
                except Exception:
                    pass
            except Exception:
                pass
        self.theme_btn.bind(on_press=_on_theme_toggle)
        right.add_widget(self.theme_btn)
        try:
            from kivy.uix.anchorlayout import AnchorLayout
            left_anchor = AnchorLayout(anchor_x='left')
            right_anchor = AnchorLayout(anchor_x='right')
            left_anchor.add_widget(left)
            right_anchor.add_widget(right)
            combined.add_widget(left_anchor)
            combined.add_widget(right_anchor)
        except Exception:
            combined.add_widget(left)
            # add a small spacer before right to keep alignment tight
            from kivy.uix.widget import Widget
            combined.add_widget(Widget(size_hint_x=None, width=dp(6)))
            combined.add_widget(right)
        content.add_widget(combined)
        self.names_area = BoxLayout(orientation='vertical', spacing=dp(6), size_hint_y=None)
        self.names_area.bind(minimum_height=self.names_area.setter('height'))
        content.add_widget(self.names_area)
        btn_row = BoxLayout(size_hint_y=None, height=ROW_HEIGHT, spacing=dp(6))
        btn_reset = IconTextButton(text='重新开始', icon='delete')
        try:
            btn_reset.bind(on_press=self.confirm_reset)
            btn_reset._label.color = (1,0,0,1)
        except Exception:
            pass
        try:
            btn_reset.size_hint_x = None
            btn_reset.width = dp(140)
        except Exception:
            pass
        btn_row.add_widget(btn_reset)
        start_btn = IconTextButton(text='开始游戏', icon='play')
        try:
            start_btn.bind(on_press=self.start_and_input)
        except Exception:
            pass
        try:
            start_btn.size_hint_x = None
            start_btn.width = dp(140)
        except Exception:
            pass
        btn_row.add_widget(start_btn)
        content.add_widget(btn_row)
        self.refresh_loaded()

    def confirm_reset(self, *_):
        """Show a confirmation overlay and, if confirmed, backup and reset data file."""
        app = App.get_running_app()
        root = getattr(app, 'root', None)
        if root is None:
            # fallback: perform reset without UI
            try:
                ensure_backup('score_data.json')
            except Exception:
                pass
            try:
                save_data({'players': [], 'rounds': []})
            except Exception:
                pass
            self.refresh_loaded()
            return

        overlay = FloatLayout(size_hint=(1, 1))
        with overlay.canvas:
            Color(0, 0, 0, 0.45)
            _back = Rectangle(pos=overlay.pos, size=overlay.size)
        overlay.bind(pos=lambda inst, *_: setattr(_back, 'pos', inst.pos), size=lambda inst, *_: setattr(_back, 'size', inst.size))

        panel = BoxLayout(orientation='vertical', size_hint=(None, None), width=dp(480), height=dp(180), spacing=dp(8), padding=dp(12))
        with panel.canvas.before:
            Color(1, 1, 1, 1)
            _panel_rect = Rectangle(pos=panel.pos, size=panel.size)
        panel.bind(pos=lambda inst, *_: setattr(_panel_rect, 'pos', inst.pos), size=lambda inst, *_: setattr(_panel_rect, 'size', inst.size))

        # ensure labels and buttons use the bundled Chinese font if available
        header_kwargs = {'size_hint_y': None, 'height': dp(28)}
        msg_kwargs = {'size_hint_y': None, 'height': dp(64)}
        if FONT_NAME:
            header_kwargs['font_name'] = FONT_NAME
            msg_kwargs['font_name'] = FONT_NAME
        header = L(text='确认重置', **header_kwargs)
        msg = L(text='确定要重新开始？这将清除所有回合记录和玩家设置。', **msg_kwargs)
        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_cancel_kwargs = {'text': '取消', 'background_normal': '', 'background_color': (0.85,0.85,0.85,1), 'color': (0,0,0,1)}
        btn_confirm_kwargs = {'text': '确定', 'background_normal': '', 'background_color': (1,0.2,0.2,1), 'color': (1,1,1,1)}
        if FONT_NAME:
            btn_cancel_kwargs['font_name'] = FONT_NAME
            btn_confirm_kwargs['font_name'] = FONT_NAME
        btn_cancel = Button(**btn_cancel_kwargs)
        btn_confirm = Button(**btn_confirm_kwargs)
        btn_row.add_widget(btn_cancel)
        btn_row.add_widget(btn_confirm)

        panel.add_widget(header)
        panel.add_widget(msg)
        panel.add_widget(btn_row)

        root.add_widget(overlay)
        overlay.add_widget(panel)

        def _pos(*a):
            w, h = root.size
            panel.x = (w - panel.width) / 2
            panel.y = (h - panel.height) / 2
        _pos()
        root.bind(size=lambda *_: _pos())

        def _dismiss(*_a):
            try:
                root.remove_widget(overlay)
            except Exception:
                pass

        btn_cancel.bind(on_press=lambda *_: _dismiss())

        def _do_reset(*_):
            try:
                # backup existing file if present
                try:
                    ensure_backup('score_data.json')
                except Exception:
                    pass
                save_data({'players': [], 'rounds': []})
            except Exception:
                pass
            # Refresh setup inputs
            try:
                self.refresh_loaded()
            except Exception:
                pass
            # Also clear other screens (score and input) so they reflect empty data immediately
            try:
                if getattr(self, 'manager', None):
                    try:
                        scr = self.manager.get_screen('score')
                        try:
                            scr.rebuild_board()
                        except Exception:
                            pass
                    except Exception:
                        pass
                    try:
                        scr_in = self.manager.get_screen('input')
                        try:
                            scr_in.set_players([])
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass
            _dismiss()

        btn_confirm.bind(on_press=_do_reset)

    def refresh_loaded(self):
        data = load_data()
        if data.get('players'):
            self.players = data['players']
            try:
                self.count = max(self._min_players, min(self._max_players, int(len(self.players))))
            except Exception:
                self.count = 4
            try:
                self.count_label.text = str(self.count)
            except Exception:
                pass
            self.generate_name_inputs(prefill=self.players)
        else:
            self.generate_name_inputs(prefill=None)

    def generate_name_inputs(self, *_args, prefill=None):
        old = []
        try:
            for ti in reversed(self.names_area.children):
                if hasattr(ti, 'text'):
                    old.append(ti.text)
        except Exception:
            old = []
        self.names_area.clear_widgets()
        n = max(self._min_players, min(self._max_players, int(getattr(self, 'count', 4))))
        for i in range(n):
            pre = None
            if prefill and i < len(prefill):
                pre = prefill[i]
            elif i < len(old):
                pre = old[i]
            ti = TI(text=(pre if pre is not None else f"玩家{i+1}"))
            ti.size_hint_y = None
            ti.height = dp(40)
            self.names_area.add_widget(ti)

    def _change_count(self, delta):
        try:
            new = int(getattr(self, 'count', 4)) + int(delta)
            new = max(self._min_players, min(self._max_players, new))
            if new == getattr(self, 'count', None):
                return
            self.count = new
            try:
                self.count_label.text = str(self.count)
            except Exception:
                pass
            self.generate_name_inputs()
        except Exception:
            pass

    def start_game(self, *_):
        names = []
        for ti in reversed(self.names_area.children):
            names.append((ti.text or "").strip() or f"玩家{len(names)+1}")
        seen, uniq = {}, []
        for nm in names:
            seen[nm] = seen.get(nm, 0) + 1
            uniq.append(nm if seen[nm] == 1 else f"{nm}{seen[nm]}")
        data = load_data()
        data['players'] = uniq
        save_data(data)
        self.manager.get_screen('score').set_players(uniq)
        self.manager.current = 'score'

    def start_and_input(self, *_):
        names = []
        for ti in reversed(self.names_area.children):
            names.append((ti.text or "").strip() or f"玩家{len(names)+1}")
        seen, uniq = {}, []
        for nm in names:
            seen[nm] = seen.get(nm, 0) + 1
            uniq.append(nm if seen[nm] == 1 else f"{nm}{seen[nm]}")
        data = load_data()
        data['players'] = uniq
        save_data(data)
        try:
            self.manager.get_screen('input').set_players(uniq)
        except Exception:
            pass
        try:
            self.manager.current = 'input'
        except Exception:
            pass
