from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.dropdown import DropDown
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButtonBehavior
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.metrics import dp, sp
from kivy.clock import Clock
from theme import TEXT_COLOR, FONT_NAME, ACCENT, BTN_BG, DROPDOWN_BG, DROPDOWN_OPTION_BG, DROPDOWN_OPTION_PRESSED, DROPDOWN_SEPARATOR_COLOR
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
        # sorting state defaults (ensure methods that call refresh can run
        # even when on_pre_enter hasn't executed during tests)
        self.sort_column = None
        self.sort_reverse = False

        root = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(6))

        # Top: page buttons
        top_bar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))

        # custom radio-like Toggle with a small selectable dot and press animation
        class RadioToggle(ToggleButtonBehavior, BoxLayout):
            _dot_alpha = NumericProperty(0.0)
            _dot_size = NumericProperty(dp(10))

            def __init__(self, text='', group=None, **kwargs):
                super().__init__(orientation='horizontal', spacing=dp(8), padding=(dp(8), dp(8)), **kwargs)
                if group:
                    try:
                        self.group = group
                    except Exception:
                        pass

                # label
                self.lbl = Label(text=text, valign='middle', size_hint_x=1)
                try:
                    if FONT_NAME:
                        self.lbl.font_name = FONT_NAME
                    self.lbl.color = TEXT_COLOR
                    self.lbl.font_size = sp(15)
                except Exception:
                    pass

                # draw dot in this widget's canvas so we can position it centered vertically
                try:
                    with self.canvas:
                        self._dot_color = Color(ACCENT[0], ACCENT[1], ACCENT[2], 0)
                        self._dot_ellipse = Ellipse(pos=(self.x + dp(6), self.y + (self.height - self._dot_size)/2), size=(self._dot_size, self._dot_size))
                    # update when layout changes
                    self.bind(pos=self._update_dot_canvas, size=self._update_dot_canvas, _dot_size=self._update_dot_canvas, _dot_alpha=self._update_dot_alpha)
                except Exception:
                    pass

                # add a spacer (left) and the label; spacer size accounts for dot
                try:
                    spacer = Widget(size_hint_x=None, width=dp(18))
                    self.add_widget(spacer)
                except Exception:
                    pass
                self.add_widget(self.lbl)

            def _update_dot_canvas(self, *a):
                try:
                    size = (self._dot_size, self._dot_size)
                    x = self.x + dp(6)
                    y = self.y + (self.height - self._dot_size) / 2
                    try:
                        self._dot_ellipse.pos = (x, y)
                        self._dot_ellipse.size = size
                    except Exception:
                        pass
                except Exception:
                    pass

            def _update_dot_alpha(self, *a):
                try:
                    self._dot_color.a = float(self._dot_alpha)
                except Exception:
                    pass

            def on_state(self, widget, value):
                # animate dot alpha and size to give press feedback
                try:
                    if value == 'down':
                        Animation.cancel_all(self)
                        Animation(_dot_size=dp(12), _dot_alpha=1.0, d=0.12).start(self)
                    else:
                        Animation.cancel_all(self)
                        Animation(_dot_size=dp(10), _dot_alpha=0.0, d=0.12).start(self)
                except Exception:
                    pass

        btn_summary = RadioToggle(text='汇总', size_hint_x=None, width=dp(120), group='view_mode')
        btn_detail = RadioToggle(text='逐局', size_hint_x=None, width=dp(120), group='view_mode')
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
                try:
                    btn_summary.lbl.font_name = FONT_NAME
                    btn_detail.lbl.font_name = FONT_NAME
                except Exception:
                    pass
        except Exception:
            pass
        # set initial state according to current mode
        try:
            if self.mode == 'summary':
                btn_summary.state = 'down'
                btn_detail.state = 'normal'
            else:
                btn_summary.state = 'normal'
                btn_detail.state = 'down'
        except Exception:
            pass

        btn_summary.bind(on_press=lambda inst, *_: self.set_mode('summary') if inst.state == 'down' else None)
        btn_detail.bind(on_press=lambda inst, *_: self.set_mode('detail') if inst.state == 'down' else None)
        top_bar.add_widget(btn_summary)
        top_bar.add_widget(btn_detail)

        # Title placed to the right of toggles, centered vertically
        title = Label(text='统计', size_hint_x=1)
        try:
            title.font_size = sp(18)
            title.color = TEXT_COLOR
            title.valign = 'middle'
            title.halign = 'center'
            if FONT_NAME:
                title.font_name = FONT_NAME
            # ensure text_size so valign works
            def _upd_title_txt_size(*a):
                try:
                    title.text_size = (title.width, title.height)
                except Exception:
                    pass
            title.bind(size=lambda *_: _upd_title_txt_size())
        except Exception:
            pass

        top_bar.add_widget(title)
        root.add_widget(top_bar)

        # Middle: filter and content
        middle = BoxLayout(orientation='vertical', spacing=dp(6))
        fb = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        # create spinner with nicer padded options and an animated dropdown
        self.player_spinner = Spinner(text='全部', values=['全部'], size_hint_x=0.7)
        try:
            # color palette for spinner and options (from theme)
            mid_gray = DROPDOWN_BG
            opt_light = DROPDOWN_OPTION_BG
            opt_pressed = DROPDOWN_OPTION_PRESSED

            # spinner base styling
            self.player_spinner.background_normal = ''
            self.player_spinner.background_down = ''
            self.player_spinner.background_color = mid_gray
            self.player_spinner.color = (1, 1, 1, 1)
            try:
                self.player_spinner.padding = (dp(12), dp(8))
            except Exception:
                pass

            # separator (1px) between dropdown options
            class Separator(BoxLayout):
                def __init__(self, color=DROPDOWN_SEPARATOR_COLOR, **kwargs):
                    super().__init__(**kwargs)
                    self.size_hint_y = None
                    self.height = dp(1)
                    try:
                        with self.canvas:
                            Color(*color)
                            self._rect = Rectangle(pos=self.pos, size=self.size)
                        self.bind(pos=lambda *_: setattr(self._rect, 'pos', self.pos))
                        self.bind(size=lambda *_: setattr(self._rect, 'size', self.size))
                    except Exception:
                        pass

            # animated dropdown class: fade in when opened and insert separators
            class AnimatedDropDown(DropDown):
                def open(self, widget):
                    try:
                        # start invisible then let super create and position
                        self.opacity = 0
                    except Exception:
                        pass
                    try:
                        super().open(widget)
                        try:
                            Animation.cancel_all(self)
                            Animation(opacity=1.0, d=0.16).start(self)
                        except Exception:
                            pass
                    except Exception:
                        try:
                            super().open(widget)
                        except Exception:
                            pass

                def add_widget(self, widget, *a, **kw):
                    # insert a 1px separator between SpinnerOption items
                    try:
                        from kivy.uix.spinner import SpinnerOption as _SO
                        if isinstance(widget, _SO) and len(self.children) > 0:
                            try:
                                super().add_widget(Separator())
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        super().add_widget(widget, *a, **kw)
                    except Exception:
                        # fallback without separator
                        try:
                            super().add_widget(widget)
                        except Exception:
                            pass

            # nicer options with padding and press feedback
            class FontSpinnerOption(SpinnerOption):
                def __init__(self, **kwargs):
                    kwargs.setdefault('background_normal', '')
                    kwargs.setdefault('background_down', '')
                    # padding and size to make options airy
                    kwargs.setdefault('padding', (dp(12), dp(10)))
                    super().__init__(**kwargs)
                    try:
                        self.background_color = opt_light
                        self.color = (1, 1, 1, 1)
                        if FONT_NAME:
                            self.font_name = FONT_NAME
                        self.font_size = sp(14)
                        # press feedback
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
            # use AnimatedDropDown for nicer open animation
            try:
                self.player_spinner.dropdown_cls = AnimatedDropDown
            except Exception:
                pass
            if FONT_NAME:
                try:
                    self.player_spinner.font_name = FONT_NAME
                except Exception:
                    pass
        except Exception:
            pass
        # refresh button removed: automatically refresh when spinner value changes
        try:
            # bind spinner selection change to refresh automatically
            self.player_spinner.bind(text=lambda inst, val: self.refresh())
        except Exception:
            pass
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

        # rows container: use a GridLayout (single column) so we can bind minimum_height
        # to its height and let it grow as rows are added. BoxLayout does not provide
        # a reliable minimum_height property for this use case on all Kivy versions.
        self.rows_container = GridLayout(cols=1, size_hint_y=None, spacing=dp(4))
        # bind minimum_height (GridLayout) to the actual height so ScrollView can size
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
                    # ensure rows_container fills remaining visible area so rows start
                    # directly under header and we don't get large empty gaps.
                    try:
                        if getattr(self, 'header', None) is not None and getattr(self, 'rows_container', None) is not None:
                            avail = int(max(self.hv.height - self.header.height, 0))
                            # only increase rows_container height when available space is larger
                            if self.rows_container.height < avail:
                                self.rows_container.height = avail
                    except Exception:
                        pass
                    # ensure hv_child is at least the visible area
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

    # unified chunk size for incremental rendering
    CHUNK_SIZE = 20

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
        import time
        start = time.perf_counter()
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

        # cancel any previous chunked render in progress
        try:
            if getattr(self, '_chunk_ev', None) is not None:
                try:
                    self._chunk_ev.cancel()
                except Exception:
                    pass
                self._chunk_ev = None
        except Exception:
            pass

        if summary_mode:
            titles = ['玩家', '总分', '基础', '基础均', '平均名次', '顿数', '头名', '末名', '场次']
        else:
            # include a date column for the detail view
            titles = ['日期', '场次', '玩家', '得分', '基础', '名次', '顿数']
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
        detail_keys = ['date', 'round_index', 'player', 'score', 'base', 'rank', 'dun']
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

            # width for header cell: reserve wider column for player name in both modes
            if t == '玩家':
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

            # prepare data entries (do not create widgets for all rows at once)
            summary_entries = [(name, stats) for name, stats in items]

            # chunked renderer: create and add up to `chunk_size` rows per frame
            chunk_size = getattr(self, 'CHUNK_SIZE', 20)
            total_entries = len(summary_entries)
            idx_state = {'i': 0}

            def _add_summary_chunk(dt):
                try:
                    i = idx_state['i']
                    end = min(i + chunk_size, total_entries)
                    for j in range(i, end):
                        name, stats = summary_entries[j]
                        row = GridLayout(cols=content_cols, size_hint_y=None, height=dp(32), size_hint_x=None)
                        row.width = content_width
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
                    idx_state['i'] = end
                    if end >= total_entries:
                        try:
                            if getattr(self, '_chunk_ev', None) is not None:
                                try:
                                    self._chunk_ev.cancel()
                                except Exception:
                                    pass
                                self._chunk_ev = None
                        except Exception:
                            pass
                        return
                except Exception:
                    pass

            # start chunked rendering (schedule at ~60FPS)
            try:
                self._chunk_ev = Clock.schedule_interval(_add_summary_chunk, 1.0 / 60.0)
            except Exception:
                # fallback: render all at once
                for name, stats in summary_entries:
                    row = GridLayout(cols=content_cols, size_hint_y=None, height=dp(32), size_hint_x=None)
                    row.width = content_width
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
                    if self.sort_column in ('player', 'name'):
                        details.sort(key=lambda d: str(d.get(self.sort_column, '')).lower(), reverse=self.sort_reverse)
                    else:
                        details.sort(key=lambda d: d.get(self.sort_column, 0), reverse=self.sort_reverse)
                except Exception:
                    pass

            # chunked rendering for details
            detail_entries = list(details)
            chunk_size = getattr(self, 'CHUNK_SIZE', 20)
            total_entries = len(detail_entries)
            idx_state = {'i': 0}

            def _add_detail_chunk(dt):
                try:
                    i = idx_state['i']
                    end = min(i + chunk_size, total_entries)
                    for j in range(i, end):
                        d = detail_entries[j]
                        row = GridLayout(cols=content_cols, size_hint_y=None, height=dp(28), size_hint_x=None)
                        row.width = content_width
                        vals = [d.get('date'), d.get('round_index'), d.get('player'), d.get('score'), d.get('base'), d.get('rank'), d.get('dun')]
                        for col_i, v in enumerate(vals):
                            # date column: show short yyyy-mm-dd when possible
                            if col_i == 0:
                                if v is None:
                                    text = ''
                                else:
                                    try:
                                        if isinstance(v, str) and 'T' in v:
                                            # ISO format: keep date and hour:minute
                                            parts = v.split('T')
                                            date_part = parts[0]
                                            time_part = parts[1] if len(parts) > 1 else ''
                                            time_short = time_part.split(':')[:2]
                                            text = f"{date_part} {':'.join(time_short)}"
                                        elif isinstance(v, str) and ' ' in v:
                                            parts = v.split(' ')
                                            date_part = parts[0]
                                            time_part = parts[1] if len(parts) > 1 else ''
                                            time_short = time_part.split(':')[:2]
                                            text = f"{date_part} {':'.join(time_short)}"
                                        elif hasattr(v, 'strftime'):
                                            text = v.strftime('%Y-%m-%d %H:%M')
                                        else:
                                            text = str(v)
                                    except Exception:
                                        text = str(v)
                            elif col_i == 2:
                                # player/name column
                                text = str(v)
                            else:
                                text = self._fmt(v, 2 if isinstance(v, float) else 0)
                            lbl = Label(text=text, size_hint_x=None, size_hint_y=None, halign='left', valign='top', height=dp(28))
                            try:
                                lbl.color = TEXT_COLOR
                                if FONT_NAME:
                                    lbl.font_name = FONT_NAME
                                lbl.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
                            except Exception:
                                pass
                            if col_i == 1:
                                lbl.width = dp(140)
                            else:
                                lbl.width = int((content_width - dp(140)) / max(1, content_cols - 1)) if content_cols > 1 else content_width
                            row.add_widget(lbl)
                        self.rows_container.add_widget(row)
                    idx_state['i'] = end
                    if end >= total_entries:
                        try:
                            if getattr(self, '_chunk_ev', None) is not None:
                                try:
                                    self._chunk_ev.cancel()
                                except Exception:
                                    pass
                                self._chunk_ev = None
                        except Exception:
                            pass
                        return
                except Exception:
                    pass

            try:
                self._chunk_ev = Clock.schedule_interval(_add_detail_chunk, 1.0 / 60.0)
            except Exception:
                for d in detail_entries:
                    row = GridLayout(cols=content_cols, size_hint_y=None, height=dp(28), size_hint_x=None)
                    row.width = content_width
                    vals = [d.get('date'), d.get('round_index'), d.get('player'), d.get('score'), d.get('base'), d.get('rank'), d.get('dun')]
                    for col_i, v in enumerate(vals):
                        # date column: show short yyyy-mm-dd HH:MM when possible
                        if col_i == 0:
                            if v is None:
                                text = ''
                            else:
                                try:
                                    if isinstance(v, str) and 'T' in v:
                                        parts = v.split('T')
                                        date_part = parts[0]
                                        time_part = parts[1] if len(parts) > 1 else ''
                                        time_short = ':'.join((time_part.split(':')[:2]))
                                        text = f"{date_part} {time_short}"
                                    elif isinstance(v, str) and ' ' in v:
                                        parts = v.split(' ')
                                        date_part = parts[0]
                                        time_part = parts[1] if len(parts) > 1 else ''
                                        time_short = ':'.join((time_part.split(':')[:2]))
                                        text = f"{date_part} {time_short}"
                                    elif hasattr(v, 'strftime'):
                                        text = v.strftime('%Y-%m-%d %H:%M')
                                    else:
                                        text = str(v)
                                except Exception:
                                    text = str(v)
                        elif col_i == 2:
                            # player/name column
                            text = str(v)
                        else:
                            text = self._fmt(v, 2 if isinstance(v, float) else 0)
                        lbl = Label(text=text, size_hint_x=None, size_hint_y=None, halign='left', valign='top', height=dp(28))
                        try:
                            lbl.color = TEXT_COLOR
                            if FONT_NAME:
                                lbl.font_name = FONT_NAME
                            lbl.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
                        except Exception:
                            pass
                        if col_i == 1:
                            lbl.width = dp(140)
                        else:
                            lbl.width = int((content_width - dp(140)) / max(1, content_cols - 1)) if content_cols > 1 else content_width
                        row.add_widget(lbl)
                    self.rows_container.add_widget(row)

        try:
            # ensure vertical scroll starts at top
            Clock.schedule_once(lambda dt: setattr(self.hv, 'scroll_y', 1.0), 0)
        except Exception:
            pass
        try:
            elapsed = (time.perf_counter() - start) * 1000.0
            print(f"statistics.refresh: rendered rows={len(self.rows_container.children)} in {elapsed:.1f} ms (mode={self.mode})")
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
                headers = ['date', 'round_index', 'player', 'score', 'base', 'rank', 'dun']
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    w = csv.writer(f)
                    w.writerow(headers)
                    for r in details:
                        # format date to short form (YYYY-MM-DD HH:MM) when possible
                        d_raw = r.get('date')
                        try:
                            if d_raw is None:
                                d_text = ''
                            elif isinstance(d_raw, str) and 'T' in d_raw:
                                parts = d_raw.split('T')
                                date_part = parts[0]
                                time_part = parts[1] if len(parts) > 1 else ''
                                time_short = ':'.join((time_part.split(':')[:2]))
                                d_text = f"{date_part} {time_short}"
                            elif isinstance(d_raw, str) and ' ' in d_raw:
                                parts = d_raw.split(' ')
                                date_part = parts[0]
                                time_part = parts[1] if len(parts) > 1 else ''
                                time_short = ':'.join((time_part.split(':')[:2]))
                                d_text = f"{date_part} {time_short}"
                            elif hasattr(d_raw, 'strftime'):
                                d_text = d_raw.strftime('%Y-%m-%d %H:%M')
                            else:
                                d_text = str(d_raw)
                        except Exception:
                            d_text = str(d_raw)
                        w.writerow([
                            d_text,
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
                # use normal-distributed floats, remove mean, round to ints and then
                # deterministically adjust any rounding difference so the sum is zero.
                samples = [random.gauss(0, 25) for _ in range(num_players)]
                mean = sum(samples) / num_players
                offsets = [int(round(s - mean)) for s in samples]
                diff = sum(offsets)
                if diff != 0:
                    # distribute the difference across players to make sum zero
                    for k in range(abs(diff)):
                        idx = k % num_players
                        if diff > 0:
                            offsets[idx] -= 1
                        else:
                            offsets[idx] += 1

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

                # enforce scores to be multiples of 5 while keeping sum == 0
                # round each score to nearest multiple of 5, then rebalance
                scores_5 = [int(round(s / 5.0)) * 5 for s in scores]
                diff = sum(scores_5)
                if diff != 0:
                    # diff is multiple of 5; distribute adjustments of -5 or +5
                    step = 5 if diff < 0 else -5
                    need = abs(diff) // 5
                    for k in range(need):
                        idx = k % num_players
                        scores_5[idx] += step
                # use the adjusted multiples-of-5 scores
                scores = scores_5

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
            # generated test data (quiet): do not print noisy debug lines
            # refresh score screen if present so the记分 page shows generated rounds
            try:
                from kivy.app import App as _App
                app = _App.get_running_app()
                if app is not None and getattr(app, '_sm', None) is not None:
                    try:
                        scr = app._sm.get_screen('score')
                        if hasattr(scr, 'rebuild_board'):
                            scr.rebuild_board()
                    except Exception:
                        pass
            except Exception:
                pass
            # also refresh statistics screen view if running inside the app
            try:
                from kivy.app import App as _App
                app = _App.get_running_app()
                if app is not None:
                    self.refresh()
            except Exception:
                pass
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
