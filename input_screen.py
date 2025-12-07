from typing import List, Dict, Optional
from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.app import App

from widgets import L, ScoreInputItem, IconTextButton, TrophyWidget, BTN
from storage import load_data, save_data, to_int, DUN_VALUE, safe_load_json
from theme import  FONT_NAME

class InputScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # State
        self.players: List[str] = []
        self.hand_inputs = {} # map player name -> base input widget
        self.dun_inputs = {}  # map player name -> dun input widget
        self.row_by_name = {} # map player name -> row widget
        
        # Root Container (Top-Aligned)
        self.outer = AnchorLayout(anchor_x='center', anchor_y='top')
        self.add_widget(self.outer)
        
        self.root_box = BoxLayout(orientation="vertical", spacing=0, padding=0, size_hint_y=None)
        self.outer.add_widget(self.root_box)

        # 1. Header Notice
        header_anchor = AnchorLayout(anchor_x='center', anchor_y='top', size_hint_y=None, height=dp(44))
        self.notice = L("每位玩家基础分100分，每顿30分，扣除100分后，总分应该为0", font_size=sp(18), size_hint_y=None, height=dp(44))
        header_anchor.add_widget(self.notice)
        self.root_box.add_widget(header_anchor)
        self.header_height = dp(44)

        # 2. Start Game / Save Bar (Initially, or maybe bottom?)
        # Original design had a save bar that appears when players exist.
        self.save_bar = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(4), padding=(dp(4), dp(4)))
        self.save_btn = IconTextButton(text='保存本局', icon='save')
        self.save_btn.bind(on_release=self._on_save_round)
        self.save_bar.add_widget(self.save_btn)
        
        # 3. Middle Area (Scrollable Rows)
        self.middle_scroll = ScrollView(size_hint_y=None, height=dp(100)) # Height updated dynamically
        self.rows_container = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        self.rows_container.bind(minimum_height=self.rows_container.setter('height'))
        self.middle_scroll.add_widget(self.rows_container)
        
        self.root_box.add_widget(self.middle_scroll)
        # Save bar goes below rows
        self.root_box.add_widget(self.save_bar)
        
        # Drag State
        self._simple_drag_active = False
        self._simple_drag_row = None
        self._simple_placeholder = None
        self._simple_drag_ev = None


    def set_players(self, players: List[str]):
        self.players = list(players) if players else []
        self.hand_inputs.clear()
        self.dun_inputs.clear()
        self.row_by_name.clear()
        self.rows_container.clear_widgets()

        if not self.players:
            # Hide save bar
            if self.save_bar.parent:
                self.root_box.remove_widget(self.save_bar)
            self._update_layout()
            return

        # Show save bar
        if not self.save_bar.parent:
            self.root_box.add_widget(self.save_bar)

        # Build Rows
        for i, name in enumerate(self.players, start=1):
            row = self._create_player_row(i, name, total_count=len(self.players))
            self.rows_container.add_widget(row)
            
            # Index Logic for maps (using name as key)
            key = name
            self.row_by_name[key] = row
            if hasattr(row, 'input_container'):
                self.hand_inputs[key] = row.input_container.base_input
                self.dun_inputs[key] = row.input_container.dun_input

        # Update Layout after build
        Clock.schedule_once(lambda dt: self._update_layout(), 0)
        # Scroll to top (or bottom?)
        self.middle_scroll.scroll_y = 1

    def _create_player_row(self, index, name, total_count):
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(56), spacing=dp(8))
        
        # Rank
        rank_lbl = L(text=str(index), font_size=sp(16), size_hint_x=None, width=dp(36))
        row.add_widget(rank_lbl)
        row.rank_label = rank_lbl
        
        # Trophy
        t_rank = None
        if index == 1: t_rank = 1
        elif index == total_count: t_rank = 'last'
        
        trophy = TrophyWidget(rank=t_rank, size=36)
        row.add_widget(trophy)
        row.trophy_label = trophy

        # Input Item
        item = ScoreInputItem(name=name)
        row.add_widget(item)
        row.input_container = item
        
        # Bind Name Long Press for Drag
        if item.name_label:
            item.name_label.bind(on_long_press=lambda inst, t: self._start_drag(row, t))
            
        return row

    def _update_layout(self):
        # Calculate height for scrollview to hug content but not exceed screen
        content_h = self.rows_container.height
        
        # Available height = Window - Header - SaveBar - Padding
        win_h = Window.height
        header_h = self.header_height
        save_h = self.save_bar.height if self.save_bar.parent else 0
        padding_reserve = dp(80) 
        
        avail_h = win_h - header_h - save_h - padding_reserve
        final_h = min(content_h, max(dp(120), avail_h))
        
        self.middle_scroll.height = max(final_h, dp(80))
        self.root_box.height = header_h + self.middle_scroll.height + save_h


    # --- Drag & Drop Interface ---

    def _start_drag(self, row, touch):
        if self._simple_drag_active: return
        self._simple_drag_active = True
        self._simple_drag_row = row
        
        # Original Order Snapshot
        self.original_children = list(self.rows_container.children)[::-1] # top-to-bottom
        
        # Placeholder
        self._simple_placeholder = BoxLayout(size_hint_y=None, height=row.height)
        with self._simple_placeholder.canvas.before:
            Color(0.0, 0.45, 0.78, 0.18)
            Rectangle(pos=self._simple_placeholder.pos, size=self._simple_placeholder.size)
            # Bind pos/size if needed, but for simple placeholder it might just work if added to layout
        
        # Replace row with placeholder in valid children list
        idx = self.original_children.index(row)
        
        # Remove row from layout
        self.rows_container.remove_widget(row)
        
        # Add overlay
        win_x, win_y = row.to_window(row.x, row.y)
        row.size_hint = (None, None)
        row.width = self.rows_container.width
        row.pos = (win_x, win_y)
        
        App.get_running_app().add_overlay(row)
        
        # Re-render container with placeholder
        new_children = list(self.original_children)
        new_children[idx] = self._simple_placeholder
        self._refill_container(new_children)

        # Start Drag Loop
        self._simple_drag_ev = Clock.schedule_interval(self._drag_update, 1/60)
        Window.bind(on_touch_up=self._drag_end)

    def _drag_update(self, dt):
        row = self._simple_drag_row
        if not row: return
        
        mx, my = Window.mouse_pos
        row.pos = (row.x, my - row.height/2)
        
        # Swap logic
        ph = self._simple_placeholder
        current_children = list(self.rows_container.children)[::-1]
        if ph not in current_children: return
        
        ph_idx = current_children.index(ph)
        
        # Find hovered child
        for i, child in enumerate(current_children):
            if child is ph: continue
            # Simple Y-axis check
            wy = child.to_window(0, child.y)[1]
            if my > wy and my < wy + child.height:
                # Hovered! Swap.
                if i != ph_idx:
                    current_children[ph_idx], current_children[i] = current_children[i], current_children[ph_idx]
                    self._refill_container(current_children)
                    break
    
    def _drag_end(self, win, touch):
        if self._simple_drag_ev:
            self._simple_drag_ev.cancel()
            self._simple_drag_ev = None
        Window.unbind(on_touch_up=self._drag_end)
        
        row = self._simple_drag_row
        ph = self._simple_placeholder
        
        # Remove overlay
        App.get_running_app().remove_overlay(row)
        
        # Restore Row to Placeholder position
        current_children = list(self.rows_container.children)[::-1]
        
        if ph in current_children:
            idx = current_children.index(ph)
            current_children[idx] = row
        else:
            current_children.append(row) # Fallback
            
        row.size_hint = (1, None)
        self._refill_container(current_children)
        
        self._simple_drag_active = False
        self._simple_drag_row = None
        self._simple_placeholder = None
        
        self._refresh_rank_labels() # Update numbers

    def _refill_container(self, children_top_to_bottom):
        self.rows_container.clear_widgets()
        for c in children_top_to_bottom:
            self.rows_container.add_widget(c)

    def _refresh_rank_labels(self):
        children = list(self.rows_container.children)[::-1]
        total = len(children)
        for i, child in enumerate(children):
            if hasattr(child, 'rank_label'):
                child.rank_label.text = str(i+1)
            if hasattr(child, 'trophy_label'):
                # Reset
                child.trophy_label.text = ''
                if i == 0:
                     child.trophy_label.text = '🏆'
                     child.trophy_label.color = (1.0, 0.84, 0.0, 1)
                elif i == total - 1:
                     child.trophy_label.text = '🏆'
                     child.trophy_label.color = (0.6, 0.6, 0.63, 1)

    # --- Saving ---

    def _on_save_round(self, *args):
        data = load_data() or {"players": [], "rounds": []}
        
        # Gather inputs
        children = list(self.rows_container.children)[::-1]
        
        ranks = {}
        basic = {}
        duns_raw = {}
        dun_vals = {}
        total = {}
        
        current_player_names = []
        
        for i, row in enumerate(children):
            cont = getattr(row, 'input_container', None)
            if not cont: continue
            
            # Identify player
            name = cont.name_label.text if cont.name_label else f"Player{i+1}"
            current_player_names.append(name)
            
            # Values
            res = cont.get_values()
            b = to_int(res.get('base', 0))
            dr = to_int(res.get('dun', 0))
            ds = to_int(res.get('dun_score', DUN_VALUE))
            
            dv = dr * ds
            tot = b + dv
            
            ranks[name] = i + 1
            basic[name] = b
            duns_raw[name] = dr
            dun_vals[name] = dv
            total[name] = tot
            
        # Create Round Object
        round_obj = {
            "date": datetime.now().isoformat(),
            "ranks": ranks,
            "total": total,
            "breakdown": {
                "basic": basic,
                "duns_raw": duns_raw,
                "dun": dun_vals
            }
        }
        
        # Save
        if 'rounds' not in data: data['rounds'] = []
        data['rounds'].append(round_obj)
        
        # Update players order if needed? (Maybe keep Setup order or update to match this round?)
        # Let's keep existing players list but maybe ensure names are there
        if not data.get('players'):
            data['players'] = current_player_names
            
        save_data(data)
        
        self._show_overlay_msg('保存成功', '本局数据已保存')


    def _show_overlay_msg(self, title, msg):
        # Using a simple overlay to show message
        overlay = FloatLayout(size_hint=(1,1))
        with overlay.canvas:
            Color(0,0,0,0.5)
            Rectangle(pos=overlay.pos, size=overlay.size)
            
        box = BoxLayout(orientation='vertical', size_hint=(None, None), size=(dp(300), dp(160)), padding=dp(20), spacing=dp(20))
        with box.canvas.before:
            Color(1,1,1,1)
            Rectangle(pos=box.pos, size=box.size)
        
        box.add_widget(L(title, font_size=sp(20), bold=True))
        box.add_widget(L(msg))
        
        btn = Button(text='确定', size_hint_y=None, height=dp(40))
        if FONT_NAME: btn.font_name = FONT_NAME
        
        def _close(*_):
            App.get_running_app().remove_overlay(overlay)
            
        btn.bind(on_release=_close)
        box.add_widget(btn)
        
        center_anchor = AnchorLayout(anchor_x='center', anchor_y='center')
        center_anchor.add_widget(box)
        overlay.add_widget(center_anchor)
        
        App.get_running_app().add_overlay(overlay)


    # --- Import / Export Dialogs ---
    # Simplified version reusing overlay
    
    def import_json_dialog(self):
        self._file_dialog('import')
        
    def export_json_dialog(self):
        # For export, we usually just share/save. But here let's just show a "Exported to..." msg 
        # or reuse the filechooser to pick WHERE to save? 
        # The original code just exported to a fixed file usually or had a dialog.
        # Let's keep it simple: Export to distinct file.
        from storage import export_data_json
        try:
            path = export_data_json()
            self._show_overlay_msg("导出成功", f"文件已保存至:\n{path}")
        except Exception as e:
            self._show_overlay_msg("导出失败", str(e))

    def _file_dialog(self, mode):
        # File Chooser Overlay
        overlay = FloatLayout(size_hint=(1,1))
        with overlay.canvas:
            Color(0,0,0,0.5)
            Rectangle(pos=overlay.pos, size=overlay.size)
            
        panel = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10), size_hint=(0.9, 0.8), pos_hint={'center_x':0.5, 'center_y':0.5})
        with panel.canvas.before:
            Color(1,1,1,1)
            Rectangle(pos=panel.pos, size=panel.size)
            
        chooser = FileChooserListView(path='.', filters=['*.json'])
        panel.add_widget(chooser)
        
        btns = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        
        if mode == 'import':
            b_merge = Button(text='合并', on_release=lambda *_: self._do_import(chooser.selection, 'merge', overlay))
            b_replace = Button(text='覆盖', on_release=lambda *_: self._do_import(chooser.selection, 'replace', overlay))
            btns.add_widget(b_merge)
            btns.add_widget(b_replace)
        
        b_cancel = Button(text='取消', on_release=lambda *_: App.get_running_app().remove_overlay(overlay))
        btns.add_widget(b_cancel)
        
        panel.add_widget(btns)
        overlay.add_widget(panel)
        App.get_running_app().add_overlay(overlay)

    def _do_import(self, selection, mode, overlay):
        if not selection: return
        path = selection[0]
        try:
            imp = safe_load_json(path)
            if mode == 'merge':
                current_data = load_data() or {'rounds': [], 'players': []}
                if imp.get('rounds'):
                    current_data.setdefault('rounds', []).extend(imp['rounds'])
                if imp.get('players'):
                     # naive merge of players
                     for p in imp['players']:
                         if p not in current_data['players']:
                             current_data['players'].append(p)
                save_data(current_data)
            else:
                save_data(imp)
            
            App.get_running_app().remove_overlay(overlay)
            self._show_overlay_msg('导入成功', '数据已更新')
            # Refresh app? Main app handles theme changes but maybe we need to trigger a refresh
            # In Main.py navigate to Setup or refresh screens?
            # Actually Main.py doesn't auto-detect data changes unless triggered.
            # But the user can navigate to Setup/Score and it will reload.
            
        except Exception as e:
            self._show_overlay_msg('导入错误', str(e))
