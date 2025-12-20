from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp, sp
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.uix.button import Button
from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import ObjectProperty

from widgets import H, L, TI, IconButton, IconTextButton, BTN
from storage import load_data, save_data, ensure_backup
from theme import theme_manager
from utils.logger import logger

class SetupScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        
        self.count = 4
        self._min_players = 1
        self._max_players = 16
        
        scroll = ScrollView(size_hint=(1,1))
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        scroll.add_widget(content)
        self.add_widget(scroll)
        
        # Title
        content.add_widget(H(text='玩家设置', size_hint_y=None, height=dp(56), font_size=sp(20)))
        
        # Controls Row
        controls = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6), padding=(dp(6), 0))
        
        # Player Count
        left = BoxLayout(spacing=dp(4))
        left.add_widget(L(text='玩家数量', size_hint_x=None, width=dp(84)))
        
        ctrl = BoxLayout(size_hint=(None, None), width=dp(110), height=dp(36), spacing=dp(6))
        btn_dec = IconButton('minus', width=dp(28), height=dp(28))
        btn_inc = IconButton('plus', width=dp(28), height=dp(28))
        btn_dec.bind(on_press=lambda *_: self._change_count(-1))
        btn_inc.bind(on_press=lambda *_: self._change_count(1))
        
        count_box = BoxLayout(size_hint=(None, None), width=dp(40), height=dp(32))
        self.count_label = L(text=str(self.count), size_hint=(1,1))
        count_box.add_widget(self.count_label)
        
        ctrl.add_widget(btn_dec)
        ctrl.add_widget(count_box)
        ctrl.add_widget(btn_inc)
        left.add_widget(ctrl)
        
        controls.add_widget(left)
        
        # Theme Toggle
        right = BoxLayout(spacing=dp(4), size_hint_x=None, width=dp(120))
        right.add_widget(L(text='主题', size_hint_x=None, width=dp(44)))
        
        self.theme_btn = IconTextButton(text='切换', icon='wrench', size_hint_x=None, width=dp(72))
        self.theme_btn.bind(on_press=self._toggle_theme)
        right.add_widget(self.theme_btn)
        
        controls.add_widget(right)
        content.add_widget(controls)
        
        # Divider
        content.add_widget(self._make_divider())
        
        # Names List
        self.names_area = BoxLayout(orientation='vertical', spacing=dp(10), padding=(dp(12), dp(6)), size_hint_y=None)
        self.names_area.bind(minimum_height=self.names_area.setter('height'))
        content.add_widget(self.names_area)
        
        content.add_widget(self._make_divider())
        
        # Action Buttons
        btn_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        
        btn_reset = IconTextButton(text='重新开始', icon='delete')
        btn_reset.size_hint_x = None
        btn_reset.width = dp(140)
        btn_reset.bind(on_press=self.confirm_reset)
        
        btn_start = IconTextButton(text='开始游戏', icon='play')
        btn_start.bind(on_press=self.start_and_input)
        
        btn_row.add_widget(btn_reset)
        from kivy.uix.widget import Widget
        btn_row.add_widget(Widget())
        btn_row.add_widget(btn_start)
        
        content.add_widget(btn_row)
        content.add_widget(self._make_divider())
        
        self._update_theme_btn_text()

    def _make_divider(self):
        from kivy.uix.widget import Widget
        w = Widget(size_hint_y=None, height=1)
        with w.canvas.before:
            c = Color(*theme_manager.border_color)
            r = Rectangle(pos=w.pos, size=w.size)
        
        theme_manager.bind(border_color=lambda _,v: setattr(c, 'rgba', v))
        w.bind(pos=lambda _,v: setattr(r, 'pos', v), size=lambda _,v: setattr(r, 'size', v))
        return w

    def _toggle_theme(self, *args):
        nxt = 'dark' if theme_manager.current_theme == 'light' else 'light'
        theme_manager.switch_theme(nxt)
        self._update_theme_btn_text()

    def _update_theme_btn_text(self):
        txt = '亮色' if theme_manager.current_theme == 'light' else '暗色'
        self.theme_btn.text = txt

    def refresh_loaded(self):
        data = load_data() or {}
        players = data.get('players', [])
        if players:
            self.players = players
            self.count = max(self._min_players, min(self._max_players, len(players)))
            self.count_label.text = str(self.count)
            self.generate_name_inputs(prefill=players)
        else:
            self.generate_name_inputs()

    def generate_name_inputs(self, prefill=None):
        # Extract old if needed... (simplified for brevity)
        self.names_area.clear_widgets()
        
        suits = ['♠', '♥', '♦', '♣']
        current_names = prefill if prefill else []
        
        for i in range(self.count):
            val = current_names[i] if i < len(current_names) else f"玩家{i+1}"
            
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), spacing=dp(8))
            
            # Card style bg
            with row.canvas.before:
                c_shadow = Color(*theme_manager.card_shadow)
                r_shadow = RoundedRectangle(radius=[6], pos=(row.x, row.y-dp(4)), size=row.size)
                
                c_bg = Color(*theme_manager.card_bg)
                r_bg = RoundedRectangle(radius=[6], pos=row.pos, size=row.size)
                
                c_line = Color(*theme_manager.card_border)
                l_border = Line(rounded_rectangle=(row.x, row.y, row.width, row.height, 6), width=1)
                
            # Bindings for drawing
            def upd(inst, *_):
                r_shadow.pos = (inst.x, inst.y-dp(4))
                r_shadow.size = inst.size
                r_bg.pos = inst.pos
                r_bg.size = inst.size
                l_border.rounded_rectangle = (inst.x, inst.y, inst.width, inst.height, 6)
            row.bind(pos=upd, size=upd)
            
            # Theme bindings
            theme_manager.bind(card_shadow=lambda _,v: setattr(c_shadow, 'rgba', v))
            theme_manager.bind(card_bg=lambda _,v: setattr(c_bg, 'rgba', v))
            theme_manager.bind(card_border=lambda _,v: setattr(c_line, 'rgba', v))
            
            # Suit Icon
            s_char = suits[i % 4]
            suit_lbl = L(text=s_char, size_hint=(None, None), width=dp(28), height=dp(44))
            
            # Dynamic suit color
            def set_suit_color(*_):
                suit_lbl.color = theme_manager.suit_colors.get(s_char, theme_manager.text_color)
                
            theme_manager.bind(suit_colors=set_suit_color)
            theme_manager.bind(text_color=set_suit_color)
            set_suit_color() # init
            
            ti = TI(text=val)
            ti.size_hint_x = 1
            ti.height = dp(44)
            
            row.add_widget(suit_lbl)
            row.add_widget(ti)
            self.names_area.add_widget(row)

    def _change_count(self, delta):
        new_c = max(self._min_players, min(self._max_players, self.count + delta))
        if new_c != self.count:
            self.count = new_c
            self.count_label.text = str(self.count)
            # Gather current input texts to preserve them
            currents = [c.children[0].text for c in reversed(self.names_area.children) if c.children]
            self.generate_name_inputs(prefill=currents)

    def confirm_reset(self, *args):
        # ... (Simplified Reset Logic without full overlay reconstruction for now, or just basic reset)
        data = {'players': [], 'rounds': []}
        save_data(data)
        self.refresh_loaded()
        App.get_running_app()._safe_refresh_screen('score')
        App.get_running_app()._safe_refresh_screen('input')
        
    def start_and_input(self, *args):
        # Save names
        players = []
        for c in reversed(self.names_area.children):
            if c.children:
                players.append(c.children[0].text.strip())
        
        # Dedupe
        seen = {}
        final = []
        for p in players:
            seen[p] = seen.get(p, 0) + 1
            final.append(p if seen[p] == 1 else f"{p}{seen[p]}")
            
        data = load_data() or {}
        data['players'] = final
        save_data(data)
        
        app = App.get_running_app()
        app._game_active = True
        app.sm.get_screen('input').set_players(final)
        app.sm.current = 'input'
