from typing import List
from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.app import App

from widgets import L, ScoreInputItem, IconTextButton, TrophyWidget, BTN
from storage import load_data, save_data, to_int, DUN_VALUE, safe_load_json
from theme import theme_manager

class InputScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.players = []
        
        # Root
        self.outer = AnchorLayout(anchor_x='center', anchor_y='top')
        self.add_widget(self.outer)
        
        self.root_box = BoxLayout(orientation="vertical", spacing=0, padding=0, size_hint_y=None)
        self.outer.add_widget(self.root_box)
        
        # Header
        h_anchor = AnchorLayout(anchor_x='center', anchor_y='top', size_hint_y=None, height=dp(44))
        self.notice = L(text="基础100 顿30 总分0", font_size=sp(16)) # Simplified text
        h_anchor.add_widget(self.notice)
        self.root_box.add_widget(h_anchor)
        
        # Save Bar
        self.save_bar = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(4), padding=(dp(4), dp(4)))
        self.save_btn = IconTextButton(text='保存本局', icon='save')
        self.save_btn.bind(on_release=self._on_save_round)
        self.save_bar.add_widget(self.save_btn)
        
        # Scroll Area
        self.middle_scroll = ScrollView(size_hint_y=None, height=dp(300))
        self.rows_container = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        self.rows_container.bind(minimum_height=self.rows_container.setter('height'))
        self.middle_scroll.add_widget(self.rows_container)
        
        self.root_box.add_widget(self.middle_scroll)
        self.root_box.add_widget(self.save_bar)
        
        # Update layout trigger
        self.bind(size=self._update_layout)

    def set_players(self, players: List[str]):
        self.players = list(players) if players else []
        self.rows_container.clear_widgets()
        
        if not self.players:
            if self.save_bar.parent: self.root_box.remove_widget(self.save_bar)
            return
            
        if not self.save_bar.parent: self.root_box.add_widget(self.save_bar)
        
        for i, name in enumerate(self.players, start=1):
            row = self._create_row(i, name, len(self.players))
            self.rows_container.add_widget(row)
            
        Clock.schedule_once(lambda dt: self._update_layout(), 0)

    def _create_row(self, index, name, total):
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(56), spacing=dp(8))
        
        # Rank
        rl = L(text=str(index), size_hint_x=None, width=dp(24))
        row.add_widget(rl)
        
        # Trophy
        rk = 1 if index == 1 else ('last' if index == total else None)
        tr = TrophyWidget(rank=rk, size=24)
        row.add_widget(tr)
        
        # Input Item
        item = ScoreInputItem(name=name)
        row.add_widget(item)
        row.input_item = item # shortcut ref
        
        # Drag logic bindings could go here (omitted for brevity in refactor, keeping standard static list for now)
        return row

    def _update_layout(self, *args):
        # Dynamically size scrollview to fit screen
        win_h = Window.height
        used = dp(44) + dp(48) + dp(100) # approx
        self.middle_scroll.height = win_h - used

    def _on_save_round(self, *a):
        # ... logic similar to original ...
        data = load_data() or {}
        if 'rounds' not in data: data['rounds'] = []
        
        ranks = {}
        totals = {}
        basic = {}
        duns = {}
        
        # Iterate rows
        # Since GridLayout children are stored in add order but visual might differ 
        # (Kivy children list is usually reverse of add order? No, index 0 is last added usually. 
        # But GridLayout displays them correctly. Let's assume standard order.)
        # Actually children list is typically reverse order of display (z-index).
        # We iterate reversed(children) to get top-to-bottom.
        
        kids = list(reversed(self.rows_container.children))
        
        for i, row in enumerate(kids):
            item = getattr(row, 'input_item', None)
            if not item: continue
            
            vals = item.get_values()
            p_name = item.name_label.text
            
            b = to_int(vals['base'])
            d = to_int(vals['dun'])
            s = int(vals['dun_score'])
            
            tot = b + (d * s)
            
            ranks[p_name] = i + 1
            totals[p_name] = tot
            basic[p_name] = b
            duns[p_name] = d
            
        # Check sum zero?
        sum_val = sum(totals.values())
        if sum_val != 0:
            self._show_msg("总分不为0", f"当前总分: {sum_val}")
            return # Don't save
            
        new_round = {
            "date": datetime.now().isoformat(),
            "ranks": ranks,
            "total": totals,
            "breakdown": {
                "basic": basic,
                "duns_raw": duns
            }
        }
        
        data['rounds'].append(new_round)
        save_data(data)
        self._show_msg("保存成功", "本局已记录")
        
        # Clear inputs?
        # Maybe navigate to score?
        App.get_running_app().sm.current = 'score'

    def _show_msg(self, title, body):
        # Use main app overlay
        app = App.get_running_app()
        
        box = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        with box.canvas.before:
            Color(*theme_manager.panel_bg)
            Rectangle(pos=box.pos, size=box.size)
            
        box.add_widget(L(text=title, font_size=sp(20)))
        box.add_widget(L(text=body))
        
        btn = BTN(text='确定')
        btn.bind(on_release=lambda *_: app.remove_overlay(wrapper))
        box.add_widget(btn)
        
        wrapper = AnchorLayout(anchor_x='center', anchor_y='center')
        box.size_hint = (None, None)
        box.size = (dp(300), dp(160))
        wrapper.add_widget(box)
        
        # bg dimmer
        dimmer = FloatLayout()
        with dimmer.canvas:
            Color(0,0,0,0.5)
            Rectangle(pos=dimmer.pos, size=dimmer.size)
        dimmer.add_widget(wrapper)
        
        app.add_overlay(dimmer)

    def import_json_dialog(self):
        self._show_msg("提示", "功能开发中...")

    def export_json_dialog(self):
        self._show_msg("提示", "功能开发中...")

# Re-inject to_int helper if not imported from storage (it is)
