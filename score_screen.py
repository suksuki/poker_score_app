from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.clock import Clock

from storage import load_data, save_data
from theme import ROW_DARK, ROW_LIGHT, TOTAL_BG, ACCENT, ROW_HEIGHT
from widgets import cell_bg, cell_bg_with_trophy

class ScoreScreen(Screen):
    CHUNK_SIZE = 20

    def __init__(self, **kw):
        super().__init__(**kw)
        self.board_sv = ScrollView(size_hint=(1, 1))
        self.board_box = GridLayout(cols=1, size_hint_y=None, spacing=dp(6))
        self.board_box.bind(minimum_height=self.board_box.setter('height'))
        self.board_sv.add_widget(self.board_box)
        self.add_widget(self.board_sv)
        self._round_widgets = []
        self._last_round_widgets = None
        self._chunk_ev = None

    def rebuild_board(self):
        # Clear previous widgets
        self.board_box.clear_widgets()
        
        # Cancel any pending chunk render
        if self._chunk_ev:
            self._chunk_ev.cancel()
            self._chunk_ev = None

        data = load_data() or {}
        players = data.get('players', [])
        rounds = data.get('rounds', [])

        if not players:
            return

        # Setup Grid
        cols = len(players) + 1
        self.board_box.cols = cols
        
        first_w = dp(120)
        per_player_w = dp(100)
        total_w = first_w + per_player_w * len(players)
        
        self.board_box.size_hint_x = None
        self.board_box.width = total_w
        
        # Preliminary height estimate (will be adjusted by minimum_height binding)
        # rows = max(1, len(rounds) + 2)
        # self.board_box.height = ROW_HEIGHT * rows

        # Header Row
        header_bg = (0.95, 0.95, 0.97, 1) # Directly use color or define in theme if needed
        self.board_box.add_widget(cell_bg("局/玩家", first_w, ROW_HEIGHT, header_bg))
        for p in players:
            self.board_box.add_widget(cell_bg(p, per_player_w, ROW_HEIGHT, header_bg))

        # Render Rounds (Chunked)
        self._round_widgets = []
        
        current_idx = 0
        total_rounds = len(rounds)
        round_entries = list(enumerate(rounds, start=1))

        def _add_chunk(dt):
            nonlocal current_idx
            end = min(current_idx + self.CHUNK_SIZE, total_rounds)
            
            for j in range(current_idx, end):
                i_round, rd = round_entries[j]
                this_round_widgets = []
                
                # Data extraction
                totals = rd.get('total', {})
                ranks = rd.get('ranks') or rd.get('ranks_by_score') or {}
                breakdown = rd.get('breakdown', {})
                basics = breakdown.get('basic', {}) or {}
                duns_raw = breakdown.get('duns_raw', {}) or {}

                bg = ROW_DARK if (i_round % 2 == 1) else ROW_LIGHT

                # Round Label (Date + Index)
                _date = rd.get('date')
                date_str = self._format_date(_date)
                round_text = f"第{i_round}局\n{date_str}" if date_str else f"第{i_round}局"
                
                w = cell_bg(round_text, first_w, ROW_HEIGHT, bg)
                self.board_box.add_widget(w)
                this_round_widgets.append(w)

                # Player Cells
                for p in players:
                    t = totals.get(p, 0)
                    b = basics.get(p, 0)
                    d = duns_raw.get(p, 0)
                    
                    text = f"{t}\n基:{b:+}  顿:{d}"
                    player_rank = ranks.get(p)
                    
                    if player_rank == 1:
                        w2 = cell_bg_with_trophy(text, per_player_w, ROW_HEIGHT, bg, rank=1)
                    elif player_rank == len(players):
                        w2 = cell_bg_with_trophy(text, per_player_w, ROW_HEIGHT, bg, rank='last')
                    else:
                        w2 = cell_bg(text, per_player_w, ROW_HEIGHT, bg)
                    
                    self.board_box.add_widget(w2)
                    this_round_widgets.append(w2)
                
                self._round_widgets.append(this_round_widgets)

            current_idx = end
            
            if current_idx >= total_rounds:
                # Finished rendering rounds, add Totals row
                self._add_totals_row(players, rounds, first_w, per_player_w)
                
                # Update last round reference
                if self._round_widgets:
                    self._last_round_widgets = self._round_widgets[-1]
                else:
                    self._last_round_widgets = None
                
                return False # Stop scheduling
            
            return True # Continue scheduling

        self._chunk_ev = Clock.schedule_interval(_add_chunk, 0)

    def _format_date(self, date_val):
        if not date_val:
            return ""
        try:
            val_str = str(date_val)
            if 'T' in val_str:
                parts = val_str.split('T')
                date_part = parts[0]
                time_part = parts[1] if len(parts) > 1 else ''
                time_short = ':'.join(time_part.split(':')[:2])
                return f"{date_part} {time_short}"
            elif ' ' in val_str:
                parts = val_str.split(' ')
                date_part = parts[0]
                time_part = parts[1] if len(parts) > 1 else ''
                time_short = ':'.join(time_part.split(':')[:2])
                return f"{date_part} {time_short}"
            return val_str
        except Exception:
            return str(date_val)

    def _add_totals_row(self, players, rounds, first_w, per_player_w):
        if not rounds:
            return
        
        self.board_box.add_widget(cell_bg("合计", first_w, ROW_HEIGHT, TOTAL_BG))
        
        # Prepare sums
        # It's better to do this once, but for simplicity we calculate here.
        # Ideally stats_helpers should provide this.
        sum_total = {p: 0 for p in players}
        sum_basic = {p: 0 for p in players}
        sum_duns = {p: 0 for p in players}
        
        for r in rounds:
            totals = r.get('total', {})
            breakdown = r.get('breakdown', {})
            basics = breakdown.get('basic', {}) or {}
            duns = breakdown.get('duns_raw', {}) or {}
            
            for p in players:
                sum_total[p] += totals.get(p, 0)
                sum_basic[p] += basics.get(p, 0)
                sum_duns[p] += duns.get(p, 0)

        for p in players:
            txt = f"基:{sum_basic[p]:+}  顿:{sum_duns[p]}\n总:{sum_total[p]}"
            self.board_box.add_widget(cell_bg(txt, per_player_w, ROW_HEIGHT, TOTAL_BG))


    def set_players(self, players):
        # Update players in data (persisting is good practice here if invoked from setup)
        data = load_data() or {}
        if players:
            data['players'] = list(players)
            save_data(data)
        self.rebuild_board()

    def highlight_last_round(self, duration=2.0):
        widgets = self._last_round_widgets
        if not widgets:
            return

        # Simple highlighting using color tint
        tint = (ACCENT[0], ACCENT[1], ACCENT[2], 0.18)
        
        orig_colors = []
        for w in widgets:
            # We look for _bg_color_instr in cell_bg
            if hasattr(w, '_bg_color_instr') and w._bg_color_instr:
                orig_colors.append((w._bg_color_instr, w._bg_color_instr.rgba))
                w._bg_color_instr.rgba = tint
        
        def _restore(dt):
            for instr, orig in orig_colors:
                instr.rgba = orig

        Clock.schedule_once(_restore, duration)
