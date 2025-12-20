from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.clock import Clock

from storage import load_data, save_data
from theme import theme_manager
from widgets import CellWithBg, TrophyWidget
# Note: we replaced widgets.py so cell_bg is gone. We must use CellWithBg.

class ScoreScreen(Screen):
    CHUNK_SIZE = 20

    def __init__(self, **kw):
        super().__init__(**kw)
        self.board_sv = ScrollView(size_hint=(1, 1))
        self.board_box = GridLayout(cols=1, size_hint_y=None, spacing=dp(6))
        self.board_box.bind(minimum_height=self.board_box.setter('height'))
        self.board_sv.add_widget(self.board_box)
        self.add_widget(self.board_sv)
        self._chunk_ev = None

    def rebuild_board(self):
        self.board_box.clear_widgets()
        if self._chunk_ev:
            self._chunk_ev.cancel()
            self._chunk_ev = None

        data = load_data() or {}
        players = data.get('players', [])
        rounds = data.get('rounds', [])

        if not players: return

        cols = len(players) + 1
        self.board_box.cols = cols
        
        first_w = dp(120)
        per_w = dp(100)
        total_w = first_w + per_w * len(players)
        
        self.board_box.size_hint_x = None
        self.board_box.width = total_w

        # Header
        # Pass the property NAME 'header_bg' not the value
        self.board_box.add_widget(CellWithBg("局/玩家", first_w, theme_manager.row_height, 'header_bg'))
        for p in players:
            self.board_box.add_widget(CellWithBg(p, per_w, theme_manager.row_height, 'header_bg'))

        # Rounds
        round_entries = list(enumerate(rounds, start=1))
        current_idx = 0
        total_rounds = len(rounds)
        
        def _add_chunk(dt):
            nonlocal current_idx
            end = min(current_idx + self.CHUNK_SIZE, total_rounds)
            
            for j in range(current_idx, end):
                i_round, rd = round_entries[j]
                
                # Logic to get data...
                totals = rd.get('total', {})
                breakdown = rd.get('breakdown', {})
                basics = breakdown.get('basic', {})
                duns = breakdown.get('duns_raw', {})
                ranks = rd.get('ranks', {})
                date_str = str(rd.get('date', '')).split('T')[0]
                
                bg_prop = 'row_dark' if i_round % 2 == 1 else 'row_light'
                
                # Round Cell
                txt = f"第{i_round}局\n{date_str}"
                self.board_box.add_widget(CellWithBg(txt, first_w, theme_manager.row_height, bg_prop))
                
                # Player Cells
                for p in players:
                    t = totals.get(p, 0)
                    b = basics.get(p, 0)
                    d = duns.get(p, 0)
                    r = ranks.get(p)
                    
                    cell_txt = f"{t}\n基:{b:+} 顿:{d}"
                    cell = CellWithBg(cell_txt, per_w, theme_manager.row_height, bg_prop)
                    
                    # Trophy?
                    if r == 1 or r == len(players):
                        # Create horizontal layout for trophy+text
                        # But CellWithBg returns a Box. We can add widget to it?
                        # CellWithBg adds a Label. Let's see if we can hack it or improve CellWithBg.
                        # Actually CellWithBg returns a container with a Label.
                        # We should just add the trophy widget to that container.
                        
                        rank_code = 1 if r == 1 else 'last'
                        trophy = TrophyWidget(rank=rank_code, size=20)
                        
                        # Insert trophy at index 0 (left)
                        cell.add_widget(trophy, index=len(cell.children)) 
                        # Note: children list index 0 is bottom/last added? Kivy default add_widget appends (index 0).
                        # We want it to be left of text? 
                        # CellWithBg is BoxLayout.
                        # Default orientation horizontal? It's default is horizontal.
                        # L is added first. So L is at index 0.
                        # If we add_widget, it becomes index 0, previous becomes index 1.
                        # So trophy is to the RIGHT of text if we just add_widget?
                        # Wait, BoxLayout default adds to "end" (right side).
                        # Let's clean current children.
                        cell.clear_widgets()
                        
                        # Trophy
                        cell.add_widget(trophy)
                        
                        # Text
                        from widgets import L
                        l = L(text=cell_txt, size_hint=(1,1))
                        cell.add_widget(l)
                        
                    self.board_box.add_widget(cell)

            current_idx = end
            if current_idx >= total_rounds:
                self._add_totals(players, rounds, first_w, per_w)
                return False
            return True

        self._chunk_ev = Clock.schedule_interval(_add_chunk, 0)

    def _add_totals(self, players, rounds, first_w, per_w):
        if not rounds: return
        self.board_box.add_widget(CellWithBg("合计", first_w, theme_manager.row_height, 'total_bg'))
        
        sums = {p: 0 for p in players}
        for r in rounds:
            tots = r.get('total', {})
            for p in players:
                sums[p] += tots.get(p, 0)
                
        for p in players:
            CellWithBg(str(sums[p]), per_w, theme_manager.row_height, 'total_bg')
            # Oops forgot to add to box
            self.board_box.add_widget(CellWithBg(str(sums[p]), per_w, theme_manager.row_height, 'total_bg'))
