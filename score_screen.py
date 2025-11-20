from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp

from storage import load_data, save_data
from theme import ROW_DARK, ROW_LIGHT, TOTAL_BG, ACCENT, ROW_HEIGHT
from kivy.clock import Clock
from widgets import cell_bg, cell_bg_with_trophy


class ScoreScreen(Screen):
    CHUNK_SIZE = 20
    def __init__(self, **kw):
        super().__init__(**kw)
        self.board_sv = ScrollView(size_hint=(1,1))
        self.board_box = GridLayout(cols=1, size_hint_y=None, spacing=dp(6))
        self.board_box.bind(minimum_height=self.board_box.setter('height'))
        self.board_sv.add_widget(self.board_box)
        self.add_widget(self.board_sv)
        self._round_widgets = []
        self._last_round_widgets = None
        self._chunk_ev = None

    def rebuild_board(self):
        # clear previous widgets
        self.board_box.clear_widgets()
        # cancel any previously scheduled chunk event to avoid duplicate renderings
        try:
            if getattr(self, '_chunk_ev', None) is not None:
                try:
                    self._chunk_ev.cancel()
                except Exception:
                    pass
                self._chunk_ev = None
        except Exception:
            pass
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
        self.board_box.height = ROW_HEIGHT * rows
        header_bg = ROW_HEIGHT and (0.95,0.95,0.97,1)
        self.board_box.add_widget(cell_bg("局/玩家", first_w, ROW_HEIGHT, header_bg))
        for p in players:
            self.board_box.add_widget(cell_bg(p, per_player_w, ROW_HEIGHT, header_bg))
        # prepare for chunked addition of rounds to avoid blocking UI
        round_entries = list(enumerate(rounds, start=1))
        chunk_size = getattr(self, 'CHUNK_SIZE', 20)
        total_entries = len(round_entries)
        idx_state = {'i': 0}
        self._round_widgets = []

        def _add_chunk(dt):
            try:
                i = idx_state['i']
                end = min(i + chunk_size, total_entries)
                for j in range(i, end):
                    i_round, rd = round_entries[j]
                    this_round_widgets = []
                    totals = rd.get('total', {})
                    ranks = rd.get('ranks', {})
                    breakdown = rd.get('breakdown', {})
                    basics = breakdown.get('basic', {}) if isinstance(breakdown.get('basic', {}), dict) else {}
                    duns_raw = breakdown.get('duns_raw', {}) if isinstance(breakdown.get('duns_raw', {}), dict) else {}
                    bg = ROW_DARK if (i_round % 2 == 1) else ROW_LIGHT
                    # include short date if available
                    _date = rd.get('date') if isinstance(rd, dict) else None
                    if _date:
                        try:
                            if isinstance(_date, str) and 'T' in _date:
                                parts = _date.split('T')
                                date_part = parts[0]
                                time_part = parts[1] if len(parts) > 1 else ''
                                time_short = ':'.join((time_part.split(':')[:2]))
                                date_short = f"{date_part} {time_short}"
                            elif isinstance(_date, str) and ' ' in _date:
                                parts = _date.split(' ')
                                date_part = parts[0]
                                time_part = parts[1] if len(parts) > 1 else ''
                                time_short = ':'.join((time_part.split(':')[:2]))
                                date_short = f"{date_part} {time_short}"
                            elif hasattr(_date, 'strftime'):
                                date_short = _date.strftime('%Y-%m-%d %H:%M')
                            else:
                                date_short = str(_date)
                        except Exception:
                            date_short = str(_date)
                        round_text = f"第{i_round}局\n{date_short}"
                    else:
                        round_text = f"第{i_round}局"
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
                idx_state['i'] = end
                if end >= total_entries:
                    # finished: add totals row and cleanup
                    try:
                        if rounds:
                            total_bg = TOTAL_BG
                            self.board_box.add_widget(cell_bg("合计", first_w, ROW_HEIGHT, total_bg))
                            sum_total = {p: sum(r.get('total', {}).get(p, 0) for r in rounds) for p in players}
                            sum_basic = {p: sum((r.get('breakdown', {}).get('basic', {}) or {}).get(p, 0) for r in rounds) for p in players}
                            sum_duns_raw = {p: sum((r.get('breakdown', {}).get('duns_raw', {}) or {}).get(p, 0) for r in rounds) for p in players}
                            for p in players:
                                txt = f"基:{sum_basic.get(p,0):+}  顿:{sum_duns_raw.get(p,0)}\n总:{sum_total.get(p,0)}"
                                self.board_box.add_widget(cell_bg(txt, per_player_w, ROW_HEIGHT, total_bg))
                    except Exception:
                        pass
                    try:
                        if getattr(self, '_chunk_ev', None) is not None:
                            try:
                                self._chunk_ev.cancel()
                            except Exception:
                                pass
                            self._chunk_ev = None
                    except Exception:
                        pass
                    try:
                        self._last_round_widgets = self._round_widgets[-1] if self._round_widgets else None
                    except Exception:
                        self._last_round_widgets = None
            except Exception:
                pass

        try:
            # schedule at ~60FPS
            self._chunk_ev = Clock.schedule_interval(_add_chunk, 1.0 / 60.0)
        except Exception:
            # fallback: render synchronously
            for i, rd in enumerate(rounds, start=1):
                this_round_widgets = []
                totals = rd.get('total', {})
                ranks = rd.get('ranks', {})
                breakdown = rd.get('breakdown', {})
                basics = breakdown.get('basic', {}) if isinstance(breakdown.get('basic', {}), dict) else {}
                duns_raw = breakdown.get('duns_raw', {}) if isinstance(breakdown.get('duns_raw', {}), dict) else {}
                bg = ROW_DARK if (i % 2 == 1) else ROW_LIGHT
                # include short date if available
                _date = rd.get('date') if isinstance(rd, dict) else None
                if _date:
                    try:
                        if isinstance(_date, str) and 'T' in _date:
                            parts = _date.split('T')
                            date_part = parts[0]
                            time_part = parts[1] if len(parts) > 1 else ''
                            time_short = ':'.join((time_part.split(':')[:2]))
                            date_short = f"{date_part} {time_short}"
                        elif isinstance(_date, str) and ' ' in _date:
                            parts = _date.split(' ')
                            date_part = parts[0]
                            time_part = parts[1] if len(parts) > 1 else ''
                            time_short = ':'.join((time_part.split(':')[:2]))
                            date_short = f"{date_part} {time_short}"
                        elif hasattr(_date, 'strftime'):
                            date_short = _date.strftime('%Y-%m-%d %H:%M')
                        else:
                            date_short = str(_date)
                    except Exception:
                        date_short = str(_date)
                    round_text = f"第{i}局\n{date_short}"
                else:
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
            # in synchronous fallback, append totals after all rounds
            try:
                if rounds:
                    total_bg = TOTAL_BG
                    self.board_box.add_widget(cell_bg("合计", first_w, ROW_HEIGHT, total_bg))
                    sum_total = {p: sum(r.get('total', {}).get(p, 0) for r in rounds) for p in players}
                    sum_basic = {p: sum((r.get('breakdown', {}).get('basic', {}) or {}).get(p, 0) for r in rounds) for p in players}
                    sum_duns_raw = {p: sum((r.get('breakdown', {}).get('duns_raw', {}) or {}).get(p, 0) for r in rounds) for p in players}
                    for p in players:
                        txt = f"基:{sum_basic.get(p,0):+}  顿:{sum_duns_raw.get(p,0)}\n总:{sum_total.get(p,0)}"
                        self.board_box.add_widget(cell_bg(txt, per_player_w, ROW_HEIGHT, total_bg))
            except Exception:
                pass
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

        from kivy.clock import Clock
        Clock.schedule_once(_restore, duration)
