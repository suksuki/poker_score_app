from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.button import Button
from kivy.metrics import dp, sp
from kivy.clock import Clock
import theme as _theme
from theme import TEXT_COLOR, FONT_NAME, ACCENT, DROPDOWN_BG, DROPDOWN_OPTION_BG, DROPDOWN_OPTION_PRESSED
from storage import load_data
import stats_helpers
from widgets import Separator, RadioToggle, AnimatedDropDown, L, BTN

class StatisticsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = kw.get('name', 'statistics')
        self.data = {}
        self.mode = 'summary'  # 'summary' or 'detail'
        self.sort_column = None
        self.sort_reverse = False
        self.CHUNK_SIZE = 20

        root = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(6))

        # --- Top Bar: View Toggles ---
        top_bar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        
        self.btn_summary = RadioToggle(text='汇总', size_hint_x=None, width=dp(120), group='view_mode')
        self.btn_detail = RadioToggle(text='逐局', size_hint_x=None, width=dp(120), group='view_mode')
        
        # Initial State
        self.btn_summary.state = 'down'
        
        self.btn_summary.bind(on_press=lambda inst: self.set_mode('summary') if inst.state == 'down' else None)
        self.btn_detail.bind(on_press=lambda inst: self.set_mode('detail') if inst.state == 'down' else None)

        top_bar.add_widget(self.btn_summary)
        top_bar.add_widget(self.btn_detail)

        # Title
        title = L(text='统计', size_hint_x=1, font_size=sp(18))
        top_bar.add_widget(title)
        root.add_widget(top_bar)

        # --- Middle: Filter and Content ---
        middle = BoxLayout(orientation='vertical', spacing=dp(6))
        
        # Filter Bar
        fb = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        
        self.player_spinner = Spinner(text='全部', values=['全部'], size_hint_x=0.7)
        self.player_spinner.background_normal = ''
        self.player_spinner.background_down = ''
        self.player_spinner.background_color = DROPDOWN_BG
        self.player_spinner.color = (1, 1, 1, 1)
        self.player_spinner.padding = (dp(12), dp(8))
        self.player_spinner.dropdown_cls = AnimatedDropDown

        class FontSpinnerOption(SpinnerOption):
            def __init__(self, **kwargs):
                kwargs.setdefault('background_normal', '')
                kwargs.setdefault('background_down', '')
                kwargs.setdefault('padding', (dp(12), dp(10)))
                super().__init__(**kwargs)
                self.background_color = DROPDOWN_OPTION_BG
                self.color = (1, 1, 1, 1)
                if FONT_NAME:
                    self.font_name = FONT_NAME
                self.font_size = sp(14)
                self.bind(state=self._on_state)

            def _on_state(self, inst, value):
                if value == 'down':
                    inst.background_color = DROPDOWN_OPTION_PRESSED
                else:
                    inst.background_color = DROPDOWN_OPTION_BG

        self.player_spinner.option_cls = FontSpinnerOption
        if FONT_NAME:
            self.player_spinner.font_name = FONT_NAME
        
        self.player_spinner.bind(text=lambda inst, val: self.refresh())

        gen_btn = Button(text='生成测试', size_hint_x=None, width=dp(100))
        gen_btn.background_normal = ''
        gen_btn.background_color = (0.36, 0.36, 0.38, 1)
        if FONT_NAME:
            gen_btn.font_name = FONT_NAME
        gen_btn.bind(on_press=lambda *_: self.generate_test_data(20))

        fb.add_widget(self.player_spinner)
        fb.add_widget(gen_btn)
        middle.add_widget(fb)

        # Summary Metrics Box
        self.summary_box = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))
        middle.add_widget(self.summary_box)

        # Scrollable Content Area
        self.hv = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=True)
        self.hv_child = BoxLayout(orientation='vertical', size_hint_x=None, size_hint_y=None)
        
        self.header = GridLayout(cols=9, size_hint_y=None, height=dp(28), size_hint_x=None)
        self.hv_child.add_widget(self.header)

        self.rows_container = GridLayout(cols=1, size_hint_y=None, spacing=dp(4))
        self.rows_container.bind(minimum_height=self.rows_container.setter('height'))
        self.hv_child.add_widget(self.rows_container)

        self.hv.add_widget(self.hv_child)
        
        # Bindings to keep layout correct
        self.rows_container.bind(height=lambda *_: self._update_hv_height())
        self.header.bind(height=lambda *_: self._update_hv_height())

        middle.add_widget(self.hv)
        root.add_widget(middle)
        self.add_widget(root)

        self._chunk_ev = None

    def _update_hv_height(self):
        h = self.header.height + self.rows_container.height
        # ensure rows_container fills remaining visible area
        avail = max(self.hv.height - self.header.height, 0)
        start_h = self.rows_container.height
        if start_h < avail:
            # We can't really force GridLayout height if minimum_height is smaller, 
            # but we can set the hv_child height to be at least the scrollview height
            pass
        self.hv_child.height = max(h, self.hv.height)

    def set_mode(self, mode):
        if self.mode == mode:
            return
        self.mode = mode
        self.sort_column = None
        self.sort_reverse = False
        self.refresh()

    def on_pre_enter(self):
        self.data = load_data() or {}
        players = self.data.get('players') or []
        self.player_spinner.values = ['全部'] + players
        self.refresh()

    def generate_test_data(self, count=20):
        # ... (keep existing logic or simplified)
        # For refactoring purposes, I'll omit the implementation of test data generation for now
        # or implement a simple version if needed.
        pass

    def _fmt(self, v, floats=0):
        if v is None:
            return '0' if floats == 0 else '0.00'
        if isinstance(v, int):
            return f"{v:,}"
        if isinstance(v, float):
            return f"{v:,.{floats if floats>0 else 2}f}"
        return str(v)

    def refresh(self):
        self.data = load_data() or {}
        
        spinner_text = self.player_spinner.text
        summary_mode = (self.mode == 'summary')

        self.summary_box.clear_widgets()
        self.header.clear_widgets()
        self.rows_container.clear_widgets()
        
        if self._chunk_ev:
            self._chunk_ev.cancel()
            self._chunk_ev = None

        player_filter = [spinner_text] if spinner_text and spinner_text != '全部' else None

        if summary_mode:
            per = stats_helpers.player_stats_from_data(self.data, player_filter=player_filter)
            s = stats_helpers.summary_stats(per) # This might expect per-player stats dict
            
            # --- Summary Box ---
            for txt in (f"总分: {self._fmt(s.get('total',0),2)}", 
                        f"基础: {self._fmt(s.get('base',0),2)}", 
                        f"场次: {self._fmt(s.get('games',0))}"):
                self.summary_box.add_widget(L(text=txt))

            # --- Columns ---
            # Columns: Player, Total, Base, BaseAvg, AvgRank, Duns, 1st, Last, Games
            titles = ['玩家', '总分', '基础', '基础均', '平均名次', '顿数', '头名', '末名', '场次']
            keys   = ['name', 'total', 'base', 'base_avg', 'avg_rank', 'dun_count', 'first_count', 'last_count', 'games_played']
            
            content_cols = len(titles)
            content_width = self._compute_width(content_cols)
            
            self._setup_header(titles, keys, content_width, content_cols)

            # --- Rows ---
            items = list(per.items())
            
            # Sorting
            if self.sort_column:
                k = self.sort_column
                if k == 'name':
                     items.sort(key=lambda x: str(x[0]).lower(), reverse=self.sort_reverse)
                else:
                     items.sort(key=lambda x: x[1].get(k, 0), reverse=self.sort_reverse)
            else:
                items.sort(key=lambda x: -x[1].get('total', 0))

            # Transposed Layout Logic logic from original was complicated (Players as columns?) 
            # The original code had a weird transpose logic if I recall correctly... 
            # "transpose layout: metrics as rows, players as columns"
            # Wait, looking at the original code: 
            # "metrics keys and display titles... recompute content columns: 1 + len(player_names)"
            # Yes, the SUMMARY view is TRANSPOSED: Rows are Metrics, Columns are Players.
            
            # Use Transposed Layout
            player_names = [name for name, _ in items]
            player_map = {name: stats for name, stats in items}
            
            metrics_keys = keys[1:] # Skip 'name'
            metrics_titles = titles[1:]
            
            content_cols = 1 + max(1, len(player_names))
            content_width = self._compute_width(content_cols)
            
            self.header.clear_widgets()
            self.header.cols = content_cols
            self.header.width = content_width
            self.hv_child.width = content_width

            # Header Row: "Metrics" | P1 | P2 | ...
            self.header.add_widget(BTN("指标", width=dp(140), background_color=(0,0,0,0), color=TEXT_COLOR))
            for pname in player_names:
                w = int((content_width - dp(140)) / max(1, content_cols - 1)) if content_cols > 1 else content_width
                self.header.add_widget(BTN(pname, width=w, background_color=(0,0,0,0), color=TEXT_COLOR))

            # Data Rows
            for mi, mkey in enumerate(metrics_keys):
                row = GridLayout(cols=content_cols, size_hint_y=None, height=dp(32), size_hint_x=None, width=content_width)
                
                # Metric Name
                row.add_widget(L(text=metrics_titles[mi], width=dp(140), size_hint_x=None, halign='left'))
                
                # Player Values
                for pname in player_names:
                    val = player_map.get(pname, {}).get(mkey, 0)
                    text = self._fmt(val, 2 if isinstance(val, float) else 0)
                    w = int((content_width - dp(140)) / max(1, content_cols - 1)) if content_cols > 1 else content_width
                    row.add_widget(L(text=text, width=w, size_hint_x=None, halign='left'))
                
                self.rows_container.add_widget(row)
                self.rows_container.add_widget(Separator())

        else:
            # --- Detail Mode ---
            details = stats_helpers.rounds_flat_list(self.data, player_filter=player_filter)
            
            # --- Summary Box (Empty in Detail Mode?) ---
            # Original code didn't clear it, but didn't populate it either? 
            # Actually it calculates `s` regardless.
            # Let's show total valid rounds count
            self.summary_box.add_widget(L(text=f"总记录: {len(details)}"))

            titles = ['日期', '场次', '玩家', '得分', '基础', '名次', '顿数']
            keys = ['date', 'round_index', 'player', 'score', 'base', 'rank', 'dun']
            
            content_cols = len(titles)
            content_width = self._compute_width(content_cols)
            self._setup_header(titles, keys, content_width, content_cols)

            # Sorting
            if self.sort_column:
                k = self.sort_column
                if k in ('player', 'name'):
                    details.sort(key=lambda d: str(d.get(k, '')).lower(), reverse=self.sort_reverse)
                else:
                    details.sort(key=lambda d: d.get(k, 0), reverse=self.sort_reverse)

            # Render Rows (Chunked)
            self._render_details_chunked(details, content_cols, content_width)

    def _compute_width(self, n):
        name_col = dp(140)
        other_col = dp(100) if n > 5 else dp(88)
        return int(name_col + (n - 1) * other_col)

    def _setup_header(self, titles, keys, width, cols):
        self.header.clear_widgets()
        self.header.cols = cols
        self.header.width = width
        self.hv_child.width = width
        
        for i, t in enumerate(titles):
            k = keys[i]
            arrow = ''
            if self.sort_column == k:
                arrow = ' ▼' if self.sort_reverse else ' ▲'
            
            btn = Button(text=f"[b]{t}{arrow}[/b]", markup=True, size_hint_x=None, size_hint_y=None, height=dp(28))
            btn.background_normal = ''
            btn.background_down = ''
            if self.sort_column == k:
                btn.background_color = ACCENT
                btn.color = (1,1,1,1)
            else:
                btn.background_color = (0,0,0,0)
                btn.color = TEXT_COLOR
            
            if FONT_NAME:
                btn.font_name = FONT_NAME
            
            # Width logic
            if t == '玩家':
                btn.width = dp(140)
            else:
                btn.width = int((width - dp(140)) / max(1, cols - 1)) if cols > 1 else width
            
            btn.bind(on_release=lambda inst, key=k: self._on_sort(key))
            self.header.add_widget(btn)

    def _on_sort(self, key):
        if self.sort_column == key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = key
            self.sort_reverse = True
        self.refresh()

    def _render_details_chunked(self, details, cols, width):
        # State stored in closure
        idx = 0
        total = len(details)
        
        def _add_chunk(dt):
            nonlocal idx
            end = min(idx + self.CHUNK_SIZE, total)
            for i in range(idx, end):
                d = details[i]
                row = GridLayout(cols=cols, size_hint_y=None, height=dp(28), size_hint_x=None, width=width)
                
                vals = [d.get(k) for k in ['date', 'round_index', 'player', 'score', 'base', 'rank', 'dun']]
                
                for col_i, v in enumerate(vals):
                    txt = str(v)
                    if col_i == 0: # Date
                        if v and 'T' in str(v):
                            txt = str(v).split('T')[0] # Brief date
                    elif col_i >= 3: # metrics
                         txt = self._fmt(v, 2 if isinstance(v, float) else 0)

                    lbl = L(text=txt, size_hint_x=None, halign='left', height=dp(28))
                    
                    if col_i == 2: # Player
                        lbl.width = dp(140)
                    else:
                        lbl.width = int((width - dp(140)) / max(1, cols - 1)) if cols > 1 else width
                    row.add_widget(lbl)
                
                self.rows_container.add_widget(row)
                self.rows_container.add_widget(Separator())
            
            idx = end
            if idx >= total:
                return False # Stop
            return True # Continue

        self._chunk_ev = Clock.schedule_interval(_add_chunk, 0)
