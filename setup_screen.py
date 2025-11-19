from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp, sp

from widgets import H, L, TI, IconButton, IconTextButton
from storage import load_data, save_data, ensure_backup
from theme import ROW_HEIGHT, CURRENT_THEME, ACCENT, FONT_NAME, BTN_BG, TEXT_COLOR, SUIT_COLORS, CARD_BG, CARD_BORDER, BORDER_COLOR
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
import os


class SetupScreen(Screen):
    players = []
    def __init__(self, **kw):
        super().__init__(**kw)
        scroll = ScrollView(size_hint=(1,1))
        # tighter padding/spacing for a more compact, card-like layout
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        scroll.add_widget(content)
        self.add_widget(scroll)
        # slightly larger, centered title for personality
        content.add_widget(H(text='玩家设置', size_hint_y=None, height=dp(56), font_size=sp(20)))
        self.count = 4
        self._min_players = 1
        self._max_players = 16
        # compact horizontal row: centered player count controls, theme toggle on right
        # make the control row slightly shorter and tighter
        combined = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6), padding=(dp(6), 0))
        left = BoxLayout(spacing=dp(4))
        # make label fixed width so controls align predictably on small screens
        left.add_widget(L(text='玩家数量', size_hint_x=None, width=dp(84)))
        # control box centered (dec, count, inc)
        ctrl = BoxLayout(size_hint=(None, None), width=dp(140), height=dp(36), spacing=dp(6))
        btn_dec = IconButton('➖', width=dp(32), height=dp(32))
        btn_inc = IconButton('➕', width=dp(32), height=dp(32))
        btn_dec.bind(on_press=lambda *_: self._change_count(-1))
        btn_inc.bind(on_press=lambda *_: self._change_count(1))
        # count label wrapped in a small box for consistent sizing
        from kivy.uix.boxlayout import BoxLayout as _Box
        count_box = _Box(size_hint=(None, None), width=dp(50), height=dp(32))
        self.count_label = L(text=str(self.count), size_hint=(1, 1), halign='center', valign='middle')
        self.count_label.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
        count_box.add_widget(self.count_label)
        ctrl.add_widget(btn_dec)
        ctrl.add_widget(count_box)
        ctrl.add_widget(btn_inc)
        left.add_widget(ctrl)
        # right side: theme label + button, right aligned and compact
        right = BoxLayout(spacing=dp(4), size_hint_x=None, width=dp(140))
        right.add_widget(L(text='主题', size_hint_x=None, width=dp(50)))
        current_text = '亮色' if CURRENT_THEME == 'light' else '暗色'
        self.theme_btn = IconTextButton(text=current_text, icon='wrench', size_hint_x=None)
        try:
            self.theme_btn.width = dp(86)
        except Exception:
            pass
        def _on_theme_toggle(*_):
            try:
                import theme as _theme
                next_theme = 'dark' if _theme.CURRENT_THEME == 'light' else 'light'
                from theme import apply_theme
                apply_theme(next_theme)
                try:
                    # update label to reflect the current theme after applying
                    self.theme_btn._label.text = '亮色' if _theme.CURRENT_THEME == 'light' else '暗色'
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
            # add a small spacer before right to keep alignment tight
            from kivy.uix.widget import Widget
            combined.add_widget(Widget(size_hint_x=None, width=dp(6)))
            combined.add_widget(right)
        content.add_widget(combined)

        # tiny horizontal divider factory
        def _make_divider():
            from kivy.uix.widget import Widget as _W
            w = _W(size_hint_y=None, height=1)
            try:
                with w.canvas.before:
                    Color(*BORDER_COLOR)
                    _r = Rectangle(pos=w.pos, size=w.size)
                def _upd(inst, *_):
                    try:
                        _r.pos = inst.pos
                        _r.size = inst.size
                    except Exception:
                        pass
                w.bind(pos=_upd, size=_upd)
            except Exception:
                pass
            return w

        # divider after controls
        content.add_widget(_make_divider())
        # the list of name rows: add padding so each row can be inset, and increase spacing
        self.names_area = BoxLayout(orientation='vertical', spacing=dp(10), padding=(dp(12), dp(6)), size_hint_y=None)
        self.names_area.bind(minimum_height=self.names_area.setter('height'))
        content.add_widget(self.names_area)
        # divider between name list and buttons
        content.add_widget(_make_divider())
        btn_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        btn_reset = IconTextButton(text='重新开始', icon='delete')
        try:
            btn_reset.bind(on_press=self.confirm_reset)
            # use neutral text color (black/gray) instead of red
            try:
                btn_reset._label.color = TEXT_COLOR
            except Exception:
                pass
        except Exception:
            pass
        try:
            btn_reset.size_hint_x = None
            btn_reset.width = dp(140)
        except Exception:
            pass

        start_btn = IconTextButton(text='开始游戏', icon='play')
        try:
            start_btn.bind(on_press=self.start_and_input)
        except Exception:
            pass
        try:
            start_btn.size_hint_x = None
            start_btn.width = dp(160)
            # emphasize primary action visually
            try:
                # prefer neutral button background and neutral text color
                if hasattr(start_btn, '_bg_color_instr') and start_btn._bg_color_instr is not None:
                    start_btn._bg_color_instr.rgba = BTN_BG
                try:
                    start_btn._label.color = TEXT_COLOR
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass

        btn_row.add_widget(btn_reset)
        # spacer so reset is left and start is right-aligned
        from kivy.uix.widget import Widget
        btn_row.add_widget(Widget())
        btn_row.add_widget(start_btn)
        content.add_widget(btn_row)
        # divider above footer/import-export area
        content.add_widget(_make_divider())
        # no overall background here — each row draws its own card background so
        # rows remain visually separated and don't appear connected.
        self.refresh_loaded()

    def confirm_reset(self, *_):
        """Show a confirmation overlay and, if confirmed, backup and reset data file."""
        app = App.get_running_app()
        root = getattr(app, 'root', None)
        if root is None:
            # fallback: perform reset without UI
            try:
                ensure_backup('score_data.json')
            except Exception:
                pass
            try:
                save_data({'players': [], 'rounds': []})
            except Exception:
                pass
            self.refresh_loaded()
            return

        overlay = FloatLayout(size_hint=(1, 1))
        with overlay.canvas:
            Color(0, 0, 0, 0.45)
            _back = Rectangle(pos=overlay.pos, size=overlay.size)
        overlay.bind(pos=lambda inst, *_: setattr(_back, 'pos', inst.pos), size=lambda inst, *_: setattr(_back, 'size', inst.size))

        panel = BoxLayout(orientation='vertical', size_hint=(None, None), width=dp(480), height=dp(180), spacing=dp(8), padding=dp(12))
        with panel.canvas.before:
            Color(1, 1, 1, 1)
            _panel_rect = Rectangle(pos=panel.pos, size=panel.size)
        panel.bind(pos=lambda inst, *_: setattr(_panel_rect, 'pos', inst.pos), size=lambda inst, *_: setattr(_panel_rect, 'size', inst.size))

        # ensure labels and buttons use the bundled Chinese font if available
        header_kwargs = {'size_hint_y': None, 'height': dp(28)}
        msg_kwargs = {'size_hint_y': None, 'height': dp(64)}
        if FONT_NAME:
            header_kwargs['font_name'] = FONT_NAME
            msg_kwargs['font_name'] = FONT_NAME
        header = L(text='确认重置', **header_kwargs)
        msg = L(text='确定要重新开始？这将清除所有回合记录和玩家设置。', **msg_kwargs)
        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        # use neutral gray backgrounds and neutral text color for both actions
        btn_cancel_kwargs = {'text': '取消', 'background_normal': '', 'background_color': BTN_BG, 'color': TEXT_COLOR}
        btn_confirm_kwargs = {'text': '确定', 'background_normal': '', 'background_color': BTN_BG, 'color': TEXT_COLOR}
        if FONT_NAME:
            btn_cancel_kwargs['font_name'] = FONT_NAME
            btn_confirm_kwargs['font_name'] = FONT_NAME
        btn_cancel = Button(**btn_cancel_kwargs)
        btn_confirm = Button(**btn_confirm_kwargs)
        btn_row.add_widget(btn_cancel)
        btn_row.add_widget(btn_confirm)

        panel.add_widget(header)
        panel.add_widget(msg)
        panel.add_widget(btn_row)

        # add overlay via central manager so main can clear it safely
        try:
            app.add_overlay(overlay)
        except Exception:
            # if overlay layer isn't available, swallow - overlay cannot be shown
            pass
        overlay.add_widget(panel)

        def _pos(*a):
            w, h = root.size
            panel.x = (w - panel.width) / 2
            panel.y = (h - panel.height) / 2
        _pos()
        root.bind(size=lambda *_: _pos())

        def _dismiss(*_a):
            try:
                app.remove_overlay(widget=overlay)
            except Exception:
                try:
                    root.remove_widget(overlay)
                except Exception:
                    pass

        btn_cancel.bind(on_press=lambda *_: _dismiss())

        def _do_reset(*_):
            try:
                # backup existing file if present
                try:
                    ensure_backup('score_data.json')
                except Exception:
                    pass
                # prefer to initialize default player names so UI shows editable
                # placeholders immediately after reset. Use current `count`.
                try:
                    cur_count = max(self._min_players, min(self._max_players, int(getattr(self, 'count', 4))))
                except Exception:
                    cur_count = 4
                default_players = [f'玩家{i+1}' for i in range(cur_count)]
                save_data({'players': default_players, 'rounds': []})
            except Exception:
                pass
            # Refresh setup inputs
            try:
                self.refresh_loaded()
            except Exception:
                pass
            # Also clear other screens (score and input) so they reflect empty data immediately
            try:
                if getattr(self, 'manager', None):
                    try:
                        scr = self.manager.get_screen('score')
                        try:
                            scr.rebuild_board()
                        except Exception:
                            pass
                    except Exception:
                        pass
                    try:
                        scr_in = self.manager.get_screen('input')
                        try:
                            scr_in.set_players([])
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass
            _dismiss()

        btn_confirm.bind(on_press=_do_reset)

    def refresh_loaded(self):
        # setup refresh called; verbose debug removed
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
        # debug snapshot after attempting to load
        try:
            # verbose debug removed
            pass
        except Exception:
            pass

    def _extract_text(self, widget):
        """Safely extract a text value from a widget or its immediate children.

        Many name rows wrap the actual `TI` input inside a horizontal BoxLayout
        (suit label + TI). This helper returns the first `text` attribute found.
        """
        try:
            # If the widget itself has text, prefer it
            if hasattr(widget, 'text'):
                return widget.text
        except Exception:
            pass
        # Prefer to return text from a TextInput child if present (TI -> TextInput)
        try:
            from kivy.uix.textinput import TextInput
            for c in getattr(widget, 'children', []) or []:
                try:
                    if isinstance(c, TextInput) and hasattr(c, 'text'):
                        return c.text
                except Exception:
                    continue
        except Exception:
            pass
        # Fallback: return the first child's text if any (iterate in normal order)
        try:
            for c in getattr(widget, 'children', []) or []:
                try:
                    if hasattr(c, 'text'):
                        return c.text
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def generate_name_inputs(self, *_args, prefill=None):
        old = []
        try:
            for w in reversed(self.names_area.children):
                txt = self._extract_text(w)
                if txt:
                    old.append(txt)
        except Exception:
            old = []
        self.names_area.clear_widgets()
        n = max(self._min_players, min(self._max_players, int(getattr(self, 'count', 4))))
        suits = ['♠', '♥', '♦', '♣']
        for i in range(n):
            pre = None
            if prefill and i < len(prefill):
                pre = prefill[i]
            elif i < len(old):
                pre = old[i]
            ti = TI(text=(pre if pre is not None else f"玩家{i+1}"))
            ti.size_hint_y = None
            ti.height = dp(44)
            # wrap with a horizontal row showing a suit icon and the input
            from kivy.uix.boxlayout import BoxLayout as _Box
            row = _Box(orientation='horizontal', size_hint_y=None, height=dp(44), spacing=dp(8))
            try:
                row.padding = (dp(8), dp(6))
            except Exception:
                pass
            suit_lbl = L(text=suits[i % len(suits)], size_hint=(None, None), width=dp(28), halign='center', valign='middle')
            try:
                suit_lbl.height = dp(44)
                suit_lbl.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
            except Exception:
                pass
            # draw a subtle card-like background for each row plus a shadow and lift animation
            try:
                from kivy.graphics import Color, RoundedRectangle, Line
                # shadow color object so we can animate its alpha
                _shadow_color = Color(*CARD_BORDER)
                # shadow rectangle (offset downwards)
                _s = RoundedRectangle(radius=[6], pos=(row.x, row.y - dp(4)), size=(row.width, row.height))
                # card background on top of shadow
                _bg_color = Color(*CARD_BG)
                _r = RoundedRectangle(radius=[6], pos=row.pos, size=row.size)
                # faint border line drawn after
                _border_color = Color(*CARD_BORDER)
                _l = Line(rectangle=(row.x, row.y, row.width, row.height), width=1)

                def _update_graphics(inst, *_a):
                    try:
                        _s.pos = (inst.x, inst.y - dp(4))
                        _s.size = (inst.width, inst.height)
                        _r.pos = inst.pos
                        _r.size = inst.size
                        _l.rectangle = (inst.x, inst.y, inst.width, inst.height)
                    except Exception:
                        pass

                # bind so rectangles follow layout
                row.bind(pos=_update_graphics, size=_update_graphics)

                # Add simple press/release animation: lift row and fade shadow
                def _on_touch_down(inst, touch):
                    if inst.collide_point(*touch.pos):
                        try:
                            Animation.cancel_all(inst)
                        except Exception:
                            pass
                        try:
                            anim = Animation(y=inst.y + dp(6), d=0.12, t='out_quad')
                            anim.start(inst)
                            try:
                                Animation(a=0.02, d=0.12).start(_shadow_color)
                            except Exception:
                                pass
                        except Exception:
                            pass
                    return False

                def _on_touch_up(inst, touch):
                    try:
                        Animation.cancel_all(inst)
                    except Exception:
                        pass
                    try:
                        Animation(y=inst.y - dp(6), d=0.12, t='out_quad').start(inst)
                        try:
                            Animation(a=CARD_BORDER[3] if len(CARD_BORDER) > 3 else 0.06, d=0.12).start(_shadow_color)
                        except Exception:
                            pass
                    except Exception:
                        pass
                    return False

                row.bind(on_touch_down=_on_touch_down, on_touch_up=_on_touch_up)
            except Exception:
                pass
            try:
                # use theme suit colors (now neutral gray)
                suit_lbl.color = SUIT_COLORS.get(suits[i % len(suits)], TEXT_COLOR)
            except Exception:
                try:
                    suit_lbl.color = TEXT_COLOR
                except Exception:
                    pass
            # give the TI a flex width
            ti.size_hint_x = 1
            row.add_widget(suit_lbl)
            row.add_widget(ti)
            self.names_area.add_widget(row)

        # debug and handle case where names_area isn't attached to widget tree yet
        try:
            parent_now = getattr(self.names_area, 'parent', None)
            # if not mounted, retry a few times to allow the screen to be attached
            retries = getattr(self, '_generate_retry', 0)
            if parent_now is None and retries < 6:
                self._generate_retry = retries + 1
                Clock.schedule_once(lambda dt: self.generate_name_inputs(prefill=prefill), 0.06)
        except Exception:
            pass

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
        for w in reversed(self.names_area.children):
            txt = (self._extract_text(w) or "").strip()
            names.append(txt or f"玩家{len(names)+1}")
        seen, uniq = {}, []
        for nm in names:
            seen[nm] = seen.get(nm, 0) + 1
            uniq.append(nm if seen[nm] == 1 else f"{nm}{seen[nm]}")
        data = load_data()
        data['players'] = uniq
        save_data(data)
        # mark game active in running app so other screens may initialize
        try:
            from kivy.app import App
            App.get_running_app()._game_active = True
        except Exception:
            pass
        try:
            self.manager.get_screen('score').set_players(uniq)
        except Exception:
            pass
        self.manager.current = 'score'

    def start_and_input(self, *_):
        names = []
        for w in reversed(self.names_area.children):
            txt = (self._extract_text(w) or "").strip()
            names.append(txt or f"玩家{len(names)+1}")
        seen, uniq = {}, []
        for nm in names:
            seen[nm] = seen.get(nm, 0) + 1
            uniq.append(nm if seen[nm] == 1 else f"{nm}{seen[nm]}")
        data = load_data()
        data['players'] = uniq
        save_data(data)
        try:
            from kivy.app import App
            App.get_running_app()._game_active = True
        except Exception:
            pass
        try:
            self.manager.get_screen('input').set_players(uniq)
        except Exception:
            pass
        try:
            self.manager.current = 'input'
        except Exception:
            pass
