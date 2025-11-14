from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.popup import Popup

from widgets import L, H, TI, IconButton, IconTextButton, cell_bg, cell_bg_with_trophy, BTN
from storage import load_data, save_data, ensure_backup, safe_load_json, safe_save_json, to_int
from theme import PANEL_BG, TEXT_COLOR, BTN_BG, ACCENT, ROW_DARK, ROW_LIGHT, TOTAL_BG, CURRENT_THEME, ROW_HEIGHT

from kivy.properties import ListProperty, DictProperty


class InputScreen(Screen):
    players = ListProperty([])
    hand_inputs = DictProperty({})
    dun_inputs = DictProperty({})
    _basic_ok = False

    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        from kivy.uix.label import Label as _KLabel
        self.info = _KLabel(text="基础=手上分-100；顿=每顿30分；基础差额需为0", size_hint_y=None, halign='left', valign='middle')
        try:
            self.info.font_size = sp(13)
            self.info.color = TEXT_COLOR
        except Exception:
            pass
        def _update_info_height(inst, *a):
            try:
                w = inst.width or (Clock and 0)
                inst.text_size = (max(0, w - dp(8)), None)
                h = (inst.texture_size[1] if getattr(inst, 'texture_size', None) else 0) + dp(12)
                inst.height = max(dp(36), h)
            except Exception:
                pass
        try:
            self.info.bind(width=_update_info_height)
            self.info.bind(texture_size=_update_info_height)
        except Exception:
            pass
        try:
            Clock.schedule_once(lambda dt: _update_info_height(self.info), 0)
        except Exception:
            pass
        root.add_widget(self.info)

        self.inputs_sv = ScrollView(size_hint=(1, 0.8))
        self.inputs_box = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        self.inputs_box.bind(minimum_height=self.inputs_box.setter("height"))
        self.inputs_sv.add_widget(self.inputs_box)

        panel = BoxLayout(orientation='vertical', size_hint=(1, 0.8), padding=dp(8))
        try:
            with panel.canvas.before:
                panel._panel_color_instr = None
            panel.bind(pos=lambda inst, *_: None, size=lambda inst, *_: None)
        except Exception:
            pass
        panel.add_widget(self.inputs_sv)
        root.add_widget(panel)

        ops = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        self.save_btn = IconTextButton(text="保存本局", icon='content-save', disabled=True)
        try:
            self.save_btn.bind(on_press=self.save_round)
        except Exception:
            pass
        try:
            self.save_btn.size_hint_x = 1
        except Exception:
            pass
        ops.add_widget(self.save_btn)
        imp_btn = IconTextButton(text="导入 JSON", icon='file-upload')
        try:
            imp_btn.bind(on_press=lambda *_: self.import_json_dialog())
        except Exception:
            pass
        exp_btn = IconTextButton(text="导出 JSON", icon='file-download')
        try:
            exp_btn.bind(on_press=lambda *_: self.export_json_dialog())
        except Exception:
            pass
        try:
            imp_btn.size_hint_x = 1
        except Exception:
            pass
        try:
            exp_btn.size_hint_x = 1
        except Exception:
            pass
        ops.add_widget(imp_btn)
        ops.add_widget(exp_btn)
        root.add_widget(ops)

        self.add_widget(root)

        try:
            self._drag_layer = FloatLayout(size_hint=(1, 1))
            self.add_widget(self._drag_layer)
        except Exception:
            self._drag_layer = None

    def on_enter(self, *a):
        try:
            pass
        except Exception:
            pass

    # placeholder methods used by main app; full implementations kept in original project
    def save_round(self, *a):
        try:
            # minimal safe implementation: append an empty round
            d = load_data()
            d.setdefault('rounds', [])
            d['rounds'].append({'total': {}, 'breakdown': {}, 'ranks': {}})
            save_data(d)
        except Exception:
            pass

    def import_json_dialog(self):
        try:
            pass
        except Exception:
            pass

    def export_json_dialog(self):
        try:
            pass
        except Exception:
            pass


class ScoreScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.board_sv = ScrollView(size_hint=(1,1))
        self.board_box = GridLayout(cols=1, size_hint_y=None, spacing=dp(6))
        self.board_box.bind(minimum_height=self.board_box.setter('height'))
        self.board_sv.add_widget(self.board_box)
        self.add_widget(self.board_sv)
        self._round_widgets = []
        self._last_round_widgets = None

    def rebuild_board(self):
        self.board_box.clear_widgets()
        data = load_data()
        players = data.get('players', [])
        rounds = data.get('rounds', [])
        if not players:
            return
        cols = len(players) + 1
        self.board_box.cols = cols
        first_w = dp(120)
        per_player_w = dp(100)
        total_w = first_w + per_player_w * len(players)
        self.board_box.size_hint_x = None
        self.board_box.width = total_w
        rows = max(1, len(rounds) + 2)
        self.board_box.size_hint_y = None
        from theme import ROW_HEIGHT
        self.board_box.height = ROW_HEIGHT * rows
        header_bg = ROW_HEIGHT and (0.95,0.95,0.97,1)
        self.board_box.add_widget(cell_bg("局/玩家", first_w, ROW_HEIGHT, header_bg))
        for p in players:
            self.board_box.add_widget(cell_bg(p, per_player_w, ROW_HEIGHT, header_bg))
        for i, rd in enumerate(rounds, start=1):
            this_round_widgets = []
            totals = rd.get('total', {})
            ranks = rd.get('ranks', {})
            breakdown = rd.get('breakdown', {})
            basics = breakdown.get('basic', {}) if isinstance(breakdown.get('basic', {}), dict) else {}
            duns_raw = breakdown.get('duns_raw', {}) if isinstance(breakdown.get('duns_raw', {}), dict) else {}
            bg = ROW_DARK if (i % 2 == 1) else ROW_LIGHT
            round_text = f"第{i}局"
            w = cell_bg(round_text, first_w, ROW_HEIGHT, bg)
            self.board_box.add_widget(w)
            this_round_widgets.append(w)
            ranks_map = rd.get('ranks') or rd.get('ranks_by_score') or {}
            for idx, p in enumerate(players, start=1):
                t = totals.get(p, 0)
                b = basics.get(p, 0)
                d = duns_raw.get(p, 0)
                text = f"{t}\n基:{b:+}  顿:{d}"
                player_rank = ranks_map.get(p)
                if player_rank == 1:
                    w2 = cell_bg_with_trophy(text, per_player_w, ROW_HEIGHT, bg, rank=1)
                elif player_rank == len(players):
                    w2 = cell_bg_with_trophy(text, per_player_w, ROW_HEIGHT, bg, rank='last')
                else:
                    w2 = cell_bg(text, per_player_w, ROW_HEIGHT, bg)
                self.board_box.add_widget(w2)
                this_round_widgets.append(w2)
            self._round_widgets.append(this_round_widgets)
        if rounds:
            total_bg = TOTAL_BG
            self.board_box.add_widget(cell_bg("合计", first_w, ROW_HEIGHT, total_bg))
            sum_total = {p: sum(r.get('total', {}).get(p, 0) for r in rounds) for p in players}
            sum_basic = {p: sum((r.get('breakdown', {}).get('basic', {}) or {}).get(p, 0) for r in rounds) for p in players}
            sum_duns_raw = {p: sum((r.get('breakdown', {}).get('duns_raw', {}) or {}).get(p, 0) for r in rounds) for p in players}
            for p in players:
                txt = f"基:{sum_basic.get(p,0):+}  顿:{sum_duns_raw.get(p,0)}\n总:{sum_total.get(p,0)}"
                self.board_box.add_widget(cell_bg(txt, per_player_w, ROW_HEIGHT, total_bg))
        try:
            self._last_round_widgets = self._round_widgets[-1] if self._round_widgets else None
        except Exception:
            self._last_round_widgets = None

    def highlight_last_round(self, duration=2.0):
        widgets = getattr(self, '_last_round_widgets', None)
        if not widgets:
            return
        saved_bg = []
        saved_label = []
        try:
            tint = (ACCENT[0], ACCENT[1], ACCENT[2], 0.18)
        except Exception:
            tint = ACCENT
        for cont in widgets:
            try:
                if hasattr(cont, '_bg_color_instr') and cont._bg_color_instr is not None:
                    try:
                        orig = tuple(getattr(cont._bg_color_instr, 'rgba', cont._bg_color or (1,1,1,1)))
                    except Exception:
                        orig = tuple(getattr(cont, '_bg_color', (1,1,1,1)))
                    saved_bg.append((cont, orig))
                    try:
                        cont._bg_color_instr.rgba = tint
                    except Exception:
                        try:
                            cont._bg_color = tint
                        except Exception:
                            pass
                else:
                    for ch in getattr(cont, 'children', []):
                        if hasattr(ch, 'color'):
                            saved_label.append((ch, ch.color))
                            try:
                                ch.color = ACCENT
                            except Exception:
                                pass
            except Exception:
                pass

        def _restore(dt):
            for cont, orig in saved_bg:
                try:
                    if hasattr(cont, '_bg_color_instr') and cont._bg_color_instr is not None:
                        cont._bg_color_instr.rgba = orig
                    else:
                        try:
                            cont._bg_color = orig
                        except Exception:
                            pass
                except Exception:
                    pass
            for ch, col in saved_label:
                try:
                    ch.color = col
                except Exception:
                    pass

        Clock.schedule_once(_restore, duration)


class StatisticsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical', padding=dp(8))
        try:
            lbl = Label(text='统计', halign='center', valign='middle')
            try:
                lbl.font_size = sp(18)
            except Exception:
                pass
            try:
                lbl.color = TEXT_COLOR
            except Exception:
                pass
            root.add_widget(lbl)
        except Exception:
            pass
        self.add_widget(root)


class SetupScreen(Screen):
    players = ListProperty([])

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
        combined = BoxLayout(size_hint_y=None, height=ROW_HEIGHT, spacing=dp(8))
        left = BoxLayout(spacing=dp(6))
        left.add_widget(L(text='玩家数量', size_hint_x=0.4))
        ctrl = BoxLayout(size_hint_x=0.6, spacing=dp(6))
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
        right = BoxLayout(spacing=dp(6))
        right.add_widget(L(text='主题', size_hint_x=0.4))
        current_text = '亮色' if CURRENT_THEME == 'light' else '暗色'
        self.theme_btn = IconTextButton(text=current_text, icon='wrench', size_hint_x=0.6)
        def _on_theme_toggle(*_):
            try:
                next_theme = 'dark' if CURRENT_THEME == 'light' else 'light'
                from theme import apply_theme
                apply_theme(next_theme)
                try:
                    self.theme_btn.text = '亮色' if CURRENT_THEME == 'light' else '暗色'
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

    def confirm_reset(self, *_):
        confirm_content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
        try:
            confirm_content.size_hint_y = None
            confirm_content.height = dp(64 + 44 + 16 + 8)
        except Exception:
            pass
        try:
            msg_container = BoxLayout(size_hint_y=None, height=dp(64), padding=dp(8))
            try:
                with msg_container.canvas.before:
                    from kivy.graphics import Color, Rectangle
                    Color(*PANEL_BG)
                    _rect = Rectangle(pos=msg_container.pos, size=msg_container.size)
                msg_container.bind(pos=lambda inst, *_: setattr(_rect, 'pos', inst.pos), size=lambda inst, *_: setattr(_rect, 'size', inst.size))
            except Exception:
                pass
            msg_lbl = Label(text='确认后将清空所有分数（保留玩家名单）。是否继续？', halign='left', valign='middle')
            try:
                msg_lbl.font_size = sp(14)
                msg_lbl.color = TEXT_COLOR
                msg_lbl.size_hint_y = None
                msg_lbl.height = dp(64 - 16)
                msg_lbl.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
            except Exception:
                pass
            msg_container.add_widget(msg_lbl)
            confirm_content.add_widget(msg_container)
        except Exception:
            msg = L(text='确认后将清空所有分数（保留玩家名单）。是否继续？')
            try:
                msg.size_hint_y = None
                msg.height = dp(64)
                msg.color = TEXT_COLOR
            except Exception:
                pass
            confirm_content.add_widget(msg)
        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        btn_ok = IconTextButton('清空分数', icon='delete')
        try:
            if hasattr(btn_ok, '_label'):
                btn_ok._label.color = (1,0,0,1)
            if getattr(btn_ok, '_bg_color_instr', None) is not None:
                try:
                    btn_ok._bg_color_instr.rgba = (1,0.9,0.9,1)
                except Exception:
                    pass
        except Exception:
            pass
        btn_cancel = IconTextButton('取消', icon='close')
        try:
            if hasattr(btn_cancel, '_label'):
                btn_cancel._label.color = TEXT_COLOR
            if getattr(btn_cancel, '_bg_color_instr', None) is not None:
                try:
                    btn_cancel._bg_color_instr.rgba = PANEL_BG
                except Exception:
                    pass
        except Exception:
            pass
        def _do_clear_scores(*_):
            try:
                popup.dismiss()
            except Exception:
                pass
            try:
                self.clear_scores()
            except Exception:
                pass
        btn_ok.bind(on_press=_do_clear_scores)
        btn_cancel.bind(on_press=lambda *_: popup.dismiss())
        btn_row.add_widget(btn_ok)
        btn_row.add_widget(btn_cancel)
        confirm_content.add_widget(btn_row)
        popup = Popup(title='确认清空分数', content=confirm_content, size_hint=(0.8, 0.4))
        popup.open()

    def clear_scores(self, *_):
        try:
            try:
                ensure_backup('score_data.json')
            except Exception:
                pass
            data = load_data()
            if not isinstance(data, dict):
                data = {'players': [], 'rounds': []}
            data['rounds'] = []
            save_data(data)
        except Exception:
            pass
        try:
            scr = self.manager.get_screen('score')
            try:
                scr.rebuild_board()
            except Exception:
                pass
        except Exception:
            pass
        try:
            msg_container = BoxLayout(size_hint_y=None, height=dp(48), padding=dp(8))
            try:
                from kivy.graphics import Color, Rectangle
                Color(*PANEL_BG)
                _r2 = Rectangle(pos=msg_container.pos, size=msg_container.size)
                msg_container.bind(pos=lambda inst, *_: setattr(_r2, 'pos', inst.pos), size=lambda inst, *_: setattr(_r2, 'size', inst.size))
            except Exception:
                pass
            msg_lbl = Label(text='所有分数已清零，玩家名单已保留。', halign='center', valign='middle')
            try:
                msg_lbl.font_size = sp(13)
                msg_lbl.color = TEXT_COLOR
                msg_lbl.size_hint_y = None
                msg_lbl.height = dp(32)
                msg_lbl.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
            except Exception:
                pass
            msg_container.add_widget(msg_lbl)
            content_v = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
            content_v.add_widget(msg_container)
            btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
            btn_ok = IconTextButton('确定', icon='check')
            try:
                btn_ok.background_color = ACCENT
                btn_ok.color = (1,1,1,1)
            except Exception:
                pass
            btn_row.add_widget(btn_ok)
            content_v.add_widget(btn_row)
            popup = Popup(title='已清空分数', content=content_v, size_hint=(0.6, 0.25), auto_dismiss=True)
            try:
                btn_ok.bind(on_press=lambda *_: popup.dismiss())
            except Exception:
                pass
            try:
                Clock.schedule_once(lambda dt: popup.dismiss(), 2.0)
            except Exception:
                pass
            popup.open()
        except Exception:
            pass
