from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.button import Button
from kivy.metrics import dp, sp
from kivy.clock import Clock
from theme import TEXT_COLOR, FONT_NAME, ACCENT, BTN_BG
from storage import load_data, save_data, safe_save_json, safe_load_json
import stats_helpers
import os
import random
from datetime import datetime, timedelta


class StatisticsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = kw.get('name', 'statistics')
        self.data = {}
        self.mode = 'summary'  # 'summary' or 'detail'

        root = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(6))

        # Top: page buttons
        top_bar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        btn_summary = Button(text='汇总', size_hint_x=None, width=dp(100))
        btn_detail = Button(text='逐局', size_hint_x=None, width=dp(100))
        try:
            # layered gray primary and secondary buttons (dark gray background, white text)
            primary_gray = (0.28, 0.28, 0.30, 1)
            secondary_gray = (0.34, 0.34, 0.36, 1)
            btn_summary.background_normal = ''
            btn_summary.background_down = ''
            btn_summary.background_color = primary_gray
            btn_summary.color = (1, 1, 1, 1)

            btn_detail.background_normal = ''
            btn_detail.background_down = ''
            btn_detail.background_color = secondary_gray
            btn_detail.color = (1, 1, 1, 1)

            if FONT_NAME:
                btn_summary.font_name = FONT_NAME
                btn_detail.font_name = FONT_NAME
        except Exception:
            pass
        btn_summary.bind(on_press=lambda *_: self.set_mode('summary'))
        btn_detail.bind(on_press=lambda *_: self.set_mode('detail'))
        top_bar.add_widget(btn_summary)
        top_bar.add_widget(btn_detail)
        root.add_widget(top_bar)

        # Title (kept for clarity)
        title = Label(text='统计', size_hint_y=None, height=dp(36))
        try:
            title.font_size = sp(18)
            title.color = TEXT_COLOR
            if FONT_NAME:
                title.font_name = FONT_NAME
        except Exception:
            pass
        root.add_widget(title)

        # Middle: filter and content
        middle = BoxLayout(orientation='vertical', spacing=dp(6))
        fb = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        # create spinner with layered gray appearance matching buttons
        self.player_spinner = Spinner(text='全部', values=['全部'], size_hint_x=0.7)
        try:

            # lighter, layered grays for spinner and options
            dark_gray = (0.30, 0.30, 0.32, 1)
            mid_gray = (0.44, 0.44, 0.46, 1)  # spinner base (lighter)
            opt_light = (0.54, 0.54, 0.56, 1)  # option normal (even lighter)
            opt_pressed = (0.40, 0.40, 0.42, 1)  # option when pressed

            # spinner base: mid gray background, white text
            self.player_spinner.background_normal = ''
            self.player_spinner.background_down = ''
            self.player_spinner.background_color = mid_gray
            self.player_spinner.color = (1, 1, 1, 1)

            class FontSpinnerOption(SpinnerOption):
                def __init__(self, **kwargs):
                    # SpinnerOption is a Button; apply layered gray style for option rows
                    kwargs.setdefault('background_normal', '')
                    kwargs.setdefault('background_down', '')
                    super().__init__(**kwargs)
                    try:
                        # option backgrounds: use lighter gray and white text
                        self.background_color = opt_light
                        self.color = (1, 1, 1, 1)
                        if FONT_NAME:
                            self.font_name = FONT_NAME
                        # add state binding to give press feedback
                        def _on_state(inst, value):
                            try:
                                if value == 'down':
                                    inst.background_color = opt_pressed
                                else:
                                    inst.background_color = opt_light
                            except Exception:
                                pass
                        self.bind(state=_on_state)
                    except Exception:
                        pass

            self.player_spinner.option_cls = FontSpinnerOption
            if FONT_NAME:
                self.player_spinner.font_name = FONT_NAME
        except Exception:
            pass
        refresh_btn = Button(text='刷新', size_hint_x=0.3)
        try:
            # refresh as mid-gray with white text for contrast
            refresh_gray = (0.42, 0.42, 0.44, 1)
            refresh_btn.background_normal = ''
            refresh_btn.background_down = ''
            refresh_btn.background_color = refresh_gray
            refresh_btn.color = (1, 1, 1, 1)
            if FONT_NAME:
                refresh_btn.font_name = FONT_NAME
        except Exception:
            pass
        refresh_btn.bind(on_press=lambda *_: self.refresh())
        # generate test data button
        gen_btn = Button(text='生成100条测试', size_hint_x=None, width=dp(140))
        try:
            g_gray = (0.36, 0.36, 0.38, 1)
            gen_btn.background_normal = ''
            gen_btn.background_down = ''
            gen_btn.background_color = g_gray
            gen_btn.color = (1, 1, 1, 1)
            if FONT_NAME:
                gen_btn.font_name = FONT_NAME
        except Exception:
            pass
        gen_btn.bind(on_press=lambda *_: self.generate_test_data(100))
        fb.add_widget(self.player_spinner)
        fb.add_widget(refresh_btn)
        fb.add_widget(gen_btn)
        middle.add_widget(fb)

        # summary box
        self.summary_box = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))
        middle.add_widget(self.summary_box)

        # Create a ScrollView that allows horizontal and vertical scrolling for the
        # header + rows content. We place a vertical BoxLayout (size_hint_x=None)
        # inside so we can control the total content width and allow horizontal
        # scrolling on narrow screens.
        self.hv = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=True)
        # hv_child should have no vertical size hint so ScrollView can size it
        self.hv_child = BoxLayout(orientation='vertical', size_hint_x=None, size_hint_y=None)

        # header will be created with dynamic cols later in refresh; keep a ref
        self.header = GridLayout(cols=9, size_hint_y=None, height=dp(28), size_hint_x=None)
        self.hv_child.add_widget(self.header)

        # rows container: vertical BoxLayout that grows in height
        self.rows_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4))
        self.rows_container.bind(minimum_height=self.rows_container.setter('height'))
        self.hv_child.add_widget(self.rows_container)

        self.hv.add_widget(self.hv_child)
        # keep hv_child height in sync with header + rows so there is no
        # large empty region inside the ScrollView
        try:
            def _update_hv_height(*a):
                try:
                    h = 0
                    if getattr(self, 'header', None) is not None:
                        h += self.header.height
                    if getattr(self, 'rows_container', None) is not None:
                        h += self.rows_container.height
                    # ensure at least visible area
                    self.hv_child.height = max(h, self.hv.height)
                except Exception:
                    pass

            # bind to changes
            try:
                self.rows_container.bind(height=lambda inst, *_: _update_hv_height())
            except Exception:
                pass
            try:
                self.header.bind(height=lambda inst, *_: _update_hv_height())
            except Exception:
                pass
            # initial update
            Clock.schedule_once(lambda dt: _update_hv_height(), 0)
        except Exception:
            pass
        middle.add_widget(self.hv)

        root.add_widget(middle)

        # Bottom: import/export JSON buttons
        footer = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(6), padding=(dp(6), dp(6)))
        btn_import = Button(text='导入 JSON', size_hint_x=None, width=dp(140))
        btn_export = Button(text='导出 JSON', size_hint_x=None, width=dp(140))
        try:
            # import/export layered gray styles
            import_gray = (0.44, 0.44, 0.46, 1)
            export_gray = (0.26, 0.26, 0.28, 1)
            btn_import.background_normal = ''
            btn_import.background_down = ''
            btn_import.background_color = import_gray
            btn_import.color = (1, 1, 1, 1)

            btn_export.background_normal = ''
            btn_export.background_down = ''
            btn_export.background_color = export_gray
            btn_export.color = (1, 1, 1, 1)

            if FONT_NAME:
                btn_import.font_name = FONT_NAME
                btn_export.font_name = FONT_NAME
        except Exception:
            pass
        btn_import.bind(on_press=lambda *_: self.import_json())
        btn_export.bind(on_press=lambda *_: self.export_json())
        footer.add_widget(Label(text=''))
        footer.add_widget(btn_import)
        footer.add_widget(btn_export)
        root.add_widget(footer)

        self.add_widget(root)

    def on_pre_enter(self):
        try:
            self.data = load_data() or {}
        except Exception:
            self.data = {}
        # sorting state
        self.sort_column = None  # column key
        self.sort_reverse = False  # True => descending
        players = self.data.get('players') or []
        try:
            self.player_spinner.values = ['全部'] + players
            self.player_spinner.text = '全部'
        except Exception:
            pass
        self.refresh()

    def _fmt(self, v, floats=0):
        try:
            if v is None:
                return '0' if floats == 0 else '0.00'
            if isinstance(v, int):
                return f"{v:,}"
            if isinstance(v, float):
                return f"{v:,.{floats if floats>0 else 2}f}"
            return str(v)
        except Exception:
            return str(v)

    def refresh(self):
        try:
            self.data = load_data() or {}
        except Exception:
            pass

        spinner_text = getattr(self.player_spinner, 'text', None)
        summary_mode = (self.mode == 'summary')

        self.summary_box.clear_widgets()
        self.header.clear_widgets()
        self.rows_container.clear_widgets()

        try:
            # decide player filter: None means all players, otherwise list of player name
            if spinner_text in (None, '全部'):
                player_filter = None
            else:
                player_filter = [spinner_text]

            per = stats_helpers.player_stats_from_data(self.data, player_filter=player_filter)
            s = stats_helpers.summary_stats(per)
        except Exception:
            per = {}
            s = {}

        try:
            for txt in (f"总分: {self._fmt(s.get('total',0),2)}", f"基础: {self._fmt(s.get('base',0),2)}", f"场次: {self._fmt(s.get('games',0))}"):
                lbl = Label(text=txt)
                try:
                    lbl.color = TEXT_COLOR
                    if FONT_NAME:
                        lbl.font_name = FONT_NAME
                except Exception:
                    pass
                self.summary_box.add_widget(lbl)
        except Exception:
            pass

        if summary_mode:
            titles = ['玩家', '总分', '基础', '基础均', '平均名次', '顿数', '头名', '末名', '场次']
        else:
            titles = ['场次', '得分', '基础', '名次', '顿数']
        # compute content width based on columns so smaller screens can scroll
        def compute_width_for_columns(n_cols):
            name_col = dp(140)
            other_col = dp(100)
            # if very few columns, shrink the other_col
            if n_cols <= 5:
                other_col = dp(88)
            return int(name_col + (n_cols - 1) * other_col)

        content_cols = len(titles)
        content_width = compute_width_for_columns(content_cols)

        # update header sizing
        self.header.clear_widgets()
        self.header.cols = content_cols
        self.header.size_hint_x = None
        self.header.width = content_width
        # ensure the hv child width matches content width so vertical layout
        # doesn't center unexpectedly
        try:
            self.hv_child.width = content_width
        except Exception:
            pass
        # build header as clickable buttons to allow sorting
        summary_keys = ['name', 'total', 'base', 'base_avg', 'avg_rank', 'dun_count', 'first_count', 'last_count', 'games_played']
        detail_keys = ['round_index', 'score', 'base', 'rank', 'dun']
        for t in titles:
            # map display title to column key
            try:
                col_key = summary_keys[titles.index(t)] if summary_mode else detail_keys[titles.index(t)]
            except Exception:
                col_key = None

            # determine arrow indicator
            arrow = ''
            if col_key and self.sort_column == col_key:
                arrow = ' ▼' if self.sort_reverse else ' ▲'

            btn = Button(text=f"[b]{t}{arrow}[/b]", markup=True, size_hint_x=None, size_hint_y=None, height=dp(28))
            try:
                # highlight active sorted column with ACCENT background
                if col_key and self.sort_column == col_key:
                    btn.background_color = ACCENT if ACCENT else (0.2, 0.5, 0.8, 1)
                    btn.color = (1, 1, 1, 1)
                else:
                    btn.color = TEXT_COLOR
                    btn.background_color = (0, 0, 0, 0)
                if FONT_NAME:
                    btn.font_name = FONT_NAME
                btn.background_normal = ''
                btn.background_down = ''
                # bind sorting action
                def _on_header_press(instance, key=col_key):
                    try:
                        if not key:
                            return
                        # toggle behaviour: first click -> descending, next -> toggle
                        if self.sort_column == key:
                            self.sort_reverse = not self.sort_reverse
                        else:
                            self.sort_column = key
                            # default to descending (high->low)
                            self.sort_reverse = True
                        self.refresh()
                    except Exception:
                        pass
                btn.bind(on_release=_on_header_press)
            except Exception:
                pass

            # width for header cell
            if t == '玩家' and summary_mode:
                btn.width = dp(140)
            else:
                btn.width = int((content_width - dp(140)) / max(1, content_cols - 1)) if content_cols > 1 else content_width
            self.header.add_widget(btn)

        if summary_mode:
            items = list(per.items()) if per else []
            # apply sort if requested
            if self.sort_column:
                key = self.sort_column
                if key == 'name':
                    items.sort(key=lambda x: str(x[0]).lower(), reverse=self.sort_reverse)
                else:
                    items.sort(key=lambda x: x[1].get(key, 0), reverse=self.sort_reverse)
            else:
                items = sorted(items, key=lambda x: -x[1].get('total', 0)) if items else []
            for name, stats in items:
                # each row is a horizontal GridLayout so columns align with header
                row = GridLayout(cols=content_cols, size_hint_y=None, height=dp(32), size_hint_x=None)
                row.width = content_width
                # name column
                lbl_name = Label(text=str(name), halign='left', valign='top', size_hint_x=None, size_hint_y=None, height=dp(32))
                try:
                    lbl_name.color = TEXT_COLOR
                    if FONT_NAME:
                        lbl_name.font_name = FONT_NAME
                except Exception:
                    pass
                lbl_name.width = dp(140)
                row.add_widget(lbl_name)

                nums = [stats.get('total',0), stats.get('base',0), stats.get('base_avg',0), stats.get('avg_rank',0), stats.get('dun_count',0), stats.get('first_count',0), stats.get('last_count',0), stats.get('games_played',0)]
                for n in nums:
                    lbl = Label(text=self._fmt(n,2 if isinstance(n,float) else 0), size_hint_x=None, size_hint_y=None, halign='left', valign='top', height=dp(32))
                    try:
                        lbl.color = TEXT_COLOR
                        if FONT_NAME:
                            lbl.font_name = FONT_NAME
                        lbl.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
                    except Exception:
                        pass
                    lbl.width = int((content_width - dp(140)) / max(1, content_cols - 1)) if content_cols > 1 else content_width
                    row.add_widget(lbl)
                self.rows_container.add_widget(row)
        else:
            # detail view: if '全部' selected, show all rounds; otherwise filter by player
            if spinner_text in (None, '全部'):
                details = stats_helpers.rounds_flat_list(self.data)
            else:
                details = stats_helpers.rounds_flat_list(self.data, player_filter=[spinner_text])
            # apply sort for detail view if requested
            if self.sort_column:
                try:
                    details.sort(key=lambda d: d.get(self.sort_column, 0), reverse=self.sort_reverse)
                except Exception:
                    pass
            # for detail view, use content_cols as len(titles)
            for d in details:
                row = GridLayout(cols=content_cols, size_hint_y=None, height=dp(28), size_hint_x=None)
                row.width = content_width
                vals = [d.get('round_index'), d.get('score'), d.get('base'), d.get('rank'), d.get('dun')]
                for v in vals:
                    lbl = Label(text=self._fmt(v,2 if isinstance(v,float) else 0), size_hint_x=None, size_hint_y=None, halign='left', valign='top', height=dp(28))
                    try:
                        lbl.color = TEXT_COLOR
                        if FONT_NAME:
                            lbl.font_name = FONT_NAME
                        lbl.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
                    except Exception:
                        pass
                    lbl.width = int(content_width / content_cols) if content_cols else content_width
                    row.add_widget(lbl)
                self.rows_container.add_widget(row)

        try:
            # ensure vertical scroll starts at top
            Clock.schedule_once(lambda dt: setattr(self.hv, 'scroll_y', 1.0), 0)
        except Exception:
            pass

    def export_csv(self):
        try:
            path = os.path.join(os.getcwd(), 'statistics_export.csv')
            spinner_text = getattr(self.player_spinner, 'text', None)
            if spinner_text in (None, '全部'):
                # build a sorted list matching UI order
                per = stats_helpers.player_stats_from_data(self.data)
                items = list(per.items())
                if self.sort_column:
                    key = self.sort_column
                    if key == 'name':
                        items.sort(key=lambda x: str(x[0]).lower(), reverse=self.sort_reverse)
                    else:
                        items.sort(key=lambda x: x[1].get(key, 0), reverse=self.sort_reverse)
                else:
                    items = sorted(items, key=lambda x: -x[1].get('total', 0)) if items else []
                # write CSV preserving this order
                import csv
                headers = ['player', 'total', 'base', 'base_avg', 'avg_rank', 'dun_count', 'avg_dun', 'first_count', 'last_count', 'games_played']
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    w = csv.writer(f)
                    w.writerow(headers)
                    for p, stats in items:
                        w.writerow([
                            p,
                            stats.get('total', 0),
                            stats.get('base', 0),
                            stats.get('base_avg', 0),
                            stats.get('avg_rank', ''),
                            stats.get('dun_count', 0),
                            stats.get('avg_dun', 0),
                            stats.get('first_count', 0),
                            stats.get('last_count', 0),
                            stats.get('games_played', 0),
                        ])
            else:
                # detail view: export rounds respecting current filter and sort
                details = stats_helpers.rounds_flat_list(self.data, player_filter=[spinner_text])
                if self.sort_column:
                    try:
                        details.sort(key=lambda d: d.get(self.sort_column, 0), reverse=self.sort_reverse)
                    except Exception:
                        pass
                import csv
                headers = ['round_index', 'player', 'score', 'base', 'rank', 'dun']
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    w = csv.writer(f)
                    w.writerow(headers)
                    for r in details:
                        w.writerow([
                            r.get('round_index'),
                            r.get('player'),
                            r.get('score'),
                            r.get('base'),
                            r.get('rank') if r.get('rank') is not None else '',
                            r.get('dun'),
                        ])
            print('Exported statistics to', path)
        except Exception as e:
            print('Failed to export CSV', e)

    def export_json(self):
        try:
            path = os.path.join(os.getcwd(), 'score_data_export.json')
            safe_save_json(path, self.data or {})
            print('Exported JSON to', path)
        except Exception as e:
            print('Failed to export JSON', e)

    def generate_test_data(self, n=100):
        """Generate n random rounds each containing results for all players.

        For each round:
        - base values are integers where sum(base - 100) == 0 (so bases center on 100)
        - score is base-100 plus a small random jitter, then adjusted so scores sum to 0
        - dun is derived from base offsets (players with lower base get slightly higher dun)
        - rank is computed from score (1 = highest)
        The generated rounds are appended to `self.data['rounds']`, players ensured in `self.data['players']`.
        """
        try:
            # ensure data structure
            if not isinstance(self.data, dict):
                self.data = load_data() or {}
            if 'rounds' not in self.data or not isinstance(self.data['rounds'], list):
                self.data['rounds'] = []
            if 'players' not in self.data or not isinstance(self.data['players'], list):
                self.data['players'] = []

            # determine players list: use existing players or create 4 default players
            players = list(self.data.get('players') or [])
            if not players:
                players = [f'玩家{i+1}' for i in range(4)]
                self.data['players'] = players[:]

            now = datetime.now()
            num_players = len(players)

            for i in range(n):
                # timestamp spacing for realism
                dt = now - timedelta(minutes=i)

                # generate random offsets that sum to zero
                # use normal-distributed floats, remove mean, round to ints and ensure sum zero
                while True:
                    samples = [random.gauss(0, 25) for _ in range(num_players)]
                    mean = sum(samples) / num_players
                    offsets = [int(round(s - mean)) for s in samples]
                    if sum(offsets) == 0:
                        break

                bases = [100 + off for off in offsets]
                # ensure non-negative bases; if negative, retry
                if any(b < 0 for b in bases):
                    # fallback regenerate
                    continue

                # raw scores = offset + small random jitter
                raw_scores = [off + random.randint(-10, 10) for off in offsets]
                total_raw = sum(raw_scores)
                # integer mean and remainder to normalize to sum zero
                mean_q, rem = divmod(total_raw, num_players)
                scores = [rs - mean_q for rs in raw_scores]
                # distribute remainder to first `rem` players (subtract 1 to remove extra)
                for j in range(rem):
                    scores[j] -= 1

                # compute duns correlated with negative offset (players who lost more get more duns)
                duns = []
                for off in offsets:
                    base_dun = max(0, int(round((-off) / 10)))
                    noise = random.choice([0, 0, 1])
                    duns.append(base_dun + noise)

                # compute ranks (1 = highest score)
                indexed = list(enumerate(scores))
                # sort by score desc, tie-breaker by random to avoid deterministic ties
                sorted_idx = sorted(indexed, key=lambda x: (-x[1], random.random()))
                ranks = [0] * num_players
                for rank_pos, (orig_idx, _) in enumerate(sorted_idx, start=1):
                    ranks[orig_idx] = rank_pos

                results = []
                totals_map = {}
                ranks_map = {}
                basics_map = {}
                duns_map = {}
                for p_idx, pname in enumerate(players):
                    sc = int(scores[p_idx])
                    ba = int(bases[p_idx])
                    du = int(duns[p_idx])
                    rk = int(ranks[p_idx])
                    results.append({
                        'player': pname,
                        'score': sc,
                        'base': ba,
                        'rank': rk,
                        'dun': du,
                    })
                    totals_map[pname] = sc
                    ranks_map[pname] = rk
                    # store basic as delta from 100 to match ScoreScreen's expectation
                    basics_map[pname] = ba - 100
                    duns_map[pname] = du

                rnd = {
                    'date': dt.isoformat(),
                    'results': results,
                    # legacy fields used by ScoreScreen
                    'total': totals_map,
                    'ranks': ranks_map,
                    'breakdown': {
                        'basic': basics_map,
                        'duns_raw': duns_map,
                    }
                }
                self.data['rounds'].append(rnd)

            # save and refresh
            try:
                save_data(self.data)
            except Exception:
                try:
                    safe_save_json(os.path.join(os.getcwd(), 'score_data_export.json'), self.data)
                except Exception:
                    pass
            print(f'Generated {n} test rounds for players: {players}')
            self.refresh()
        except Exception as e:
            print('Failed to generate test data', e)

    def import_json(self):
        try:
            path = os.path.join(os.getcwd(), 'score_data_import.json')
            js = safe_load_json(path)
            if js:
                save_data(js)
                self.data = js
                print('Imported JSON from', path)
                self.refresh()
            else:
                print('No data found in', path)
        except Exception as e:
            print('Failed to import JSON', e)

    def set_mode(self, m):
        try:
            if m in ('summary', 'detail'):
                self.mode = m
                self.refresh()
        except Exception:
            pass
