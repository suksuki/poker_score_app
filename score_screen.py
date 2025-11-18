from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp

from storage import load_data, save_data
import theme as _theme
from widgets import cell_bg, cell_bg_with_trophy


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
        # use runtime theme values
        self.board_box.height = _theme.ROW_HEIGHT * rows
        header_bg = _theme.HEADER_BG
        self.board_box.add_widget(cell_bg("局/玩家", first_w, _theme.ROW_HEIGHT, header_bg))
        for p in players:
            self.board_box.add_widget(cell_bg(p, per_player_w, _theme.ROW_HEIGHT, header_bg))
        for i, rd in enumerate(rounds, start=1):
            this_round_widgets = []
            totals = rd.get('total', {})
            ranks = rd.get('ranks', {})
            breakdown = rd.get('breakdown', {})
            basics = breakdown.get('basic', {}) if isinstance(breakdown.get('basic', {}), dict) else {}
            duns_raw = breakdown.get('duns_raw', {}) if isinstance(breakdown.get('duns_raw', {}), dict) else {}
            bg = _theme.ROW_DARK if (i % 2 == 1) else _theme.ROW_LIGHT
            round_text = f"第{i}局"
            w = cell_bg(round_text, first_w, _theme.ROW_HEIGHT, bg)
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
                    w2 = cell_bg_with_trophy(text, per_player_w, _theme.ROW_HEIGHT, bg, rank=1)
                elif player_rank == len(players):
                    w2 = cell_bg_with_trophy(text, per_player_w, _theme.ROW_HEIGHT, bg, rank='last')
                else:
                    w2 = cell_bg(text, per_player_w, _theme.ROW_HEIGHT, bg)
                self.board_box.add_widget(w2)
                this_round_widgets.append(w2)
            self._round_widgets.append(this_round_widgets)
        if rounds:
            total_bg = _theme.TOTAL_BG
            self.board_box.add_widget(cell_bg("合计", first_w, _theme.ROW_HEIGHT, total_bg))
            sum_total = {p: sum(r.get('total', {}).get(p, 0) for r in rounds) for p in players}
            sum_basic = {p: sum((r.get('breakdown', {}).get('basic', {}) or {}).get(p, 0) for r in rounds) for p in players}
            sum_duns_raw = {p: sum((r.get('breakdown', {}).get('duns_raw', {}) or {}).get(p, 0) for r in rounds) for p in players}
            for p in players:
                txt = f"基:{sum_basic.get(p,0):+}  顿:{sum_duns_raw.get(p,0)}\n总:{sum_total.get(p,0)}"
                self.board_box.add_widget(cell_bg(txt, per_player_w, _theme.ROW_HEIGHT, total_bg))
        try:
            self._last_round_widgets = self._round_widgets[-1] if self._round_widgets else None
        except Exception:
            self._last_round_widgets = None

    def set_players(self, players):
        try:
            data = load_data() or {}
            if players:
                data['players'] = list(players)
                save_data(data)
        except Exception:
            pass
        try:
            self.rebuild_board()
        except Exception:
            pass

    def highlight_last_round(self, duration=2.0):
        widgets = getattr(self, '_last_round_widgets', None)
        if not widgets:
            return
        saved_bg = []
        saved_label = []
        try:
            tint = (_theme.ACCENT[0], _theme.ACCENT[1], _theme.ACCENT[2], 0.18)
        except Exception:
            tint = _theme.ACCENT
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
                                ch.color = _theme.ACCENT
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

        from kivy.clock import Clock
        Clock.schedule_once(_restore, duration)
