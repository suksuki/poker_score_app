from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
import weakref
import theme as _theme

# registry of widgets that need theme-driven updates (weak refs to avoid leaks)
_THEMED_WIDGETS = weakref.WeakSet()

def _register_themable(obj):
    try:
        _THEMED_WIDGETS.add(obj)
    except Exception:
        pass

def _apply_theme_to_registered():
    """Update known widgets' colors when theme changes."""
    try:
        from kivy.uix.label import Label as _KLabel
        from kivy.uix.textinput import TextInput as _KTI
    except Exception:
        _KLabel = None
        _KTI = None
    for w in list(_THEMED_WIDGETS):
        try:
            # update canvas color instructions if present
            if hasattr(w, '_bg_color_instruction') and getattr(w, '_bg_color_instruction') is not None:
                try:
                    w._bg_color_instruction.rgba = _T('BTN_BG')
                except Exception:
                    pass
            if hasattr(w, '_bg_color_instr') and getattr(w, '_bg_color_instr') is not None:
                try:
                    w._bg_color_instr.rgba = _T('BTN_BG')
                except Exception:
                    pass
            if hasattr(w, '_mark_color_instruction') and getattr(w, '_mark_color_instruction') is not None:
                try:
                    w._mark_color_instruction.rgba = _T('TEXT_COLOR')
                except Exception:
                    pass
            # Labels: update text color
            try:
                if _KLabel is not None and isinstance(w, _KLabel):
                    w.color = _T('TEXT_COLOR')
            except Exception:
                pass
            # TextInput: update background and foreground
            try:
                if _KTI is not None and isinstance(w, _KTI):
                    try:
                        w.background_color = _T('PANEL_BG')
                    except Exception:
                        pass
                    try:
                        w.foreground_color = _T('TEXT_COLOR')
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

# register our theme applier with theme module so it's called on apply_theme
try:
    _theme.register_theme_listener(_apply_theme_to_registered)
except Exception:
    pass

import theme as _theme
FONT_NAME = getattr(_theme, 'FONT_NAME', None)
FA_FONT = getattr(_theme, 'FA_FONT', None)
def _T(name):
    return getattr(_theme, name)

def style_card(widget, *a, **kw):
    return widget

def style_button(btn: Button, *a, **kw):
    try:
        btn.background_normal = ''
        btn.background_down = ''
        btn.background_color = _T('BTN_BG')
    except Exception:
        pass
    try:
        btn.color = _T('TEXT_COLOR')
    except Exception:
        btn.color = (1, 1, 1, 1) if _T('CURRENT_THEME') == 'dark' else _T('TEXT_COLOR')
    try:
        btn.padding = (dp(8), dp(6))
        btn.font_size = sp(13)
    except Exception:
        pass
    return btn

def L(text="", **kw):
    if FONT_NAME:
        kw.setdefault("font_name", FONT_NAME)
    kw.setdefault("font_size", _T('SMALL_FONT'))
    kw.setdefault("color", _T('TEXT_COLOR'))
    kw.setdefault("halign", "center")
    kw.setdefault("valign", "middle")
    lbl = Label(text=text, **kw)
    lbl.bind(size=lambda inst, *_: setattr(inst, "text_size", (inst.width, inst.height)))
    try:
        _register_themable(lbl)
    except Exception:
        pass
    return lbl

def H(text="", **kw):
    if FONT_NAME:
        kw.setdefault("font_name", FONT_NAME)
    kw.setdefault("font_size", sp(16))
    kw.setdefault("color", _T('TEXT_COLOR'))
    kw.setdefault("halign", "center")
    kw.setdefault("valign", "middle")
    lbl = Label(text=text, **kw)
    lbl.bind(size=lambda inst, *_: setattr(inst, "text_size", (inst.width, inst.height)))
    try:
        _register_themable(lbl)
    except Exception:
        pass
    return lbl

def TI(**kw):
    # Avoid forcing a font that may interfere with IME input on some systems.
    # We'll let the system select the input font to improve IME/Chinese support.
    kw.setdefault("font_size", _T('INPUT_FONT'))
    kw.setdefault("multiline", False)
    kw.setdefault("background_normal", "")
    kw.setdefault("background_active", "")
    kw.setdefault("background_color", _T('PANEL_BG'))
    kw.setdefault("foreground_color", _T('TEXT_COLOR'))
    # ensure this is treated as free-form text (helps IME on some platforms)
    kw.setdefault('input_type', 'text')
    # allow tab characters to be written if needed
    kw.setdefault('write_tab', True)

    ti = TextInput(**kw)
    try:
        # If the project registered a Chinese-capable font, apply it to the
        # TextInput so Chinese glyphs render correctly. Use try/except to
        # avoid platform-specific IME issues crashing the app.
        try:
            # On Windows, setting a custom `font_name` on TextInput can break
            # IME composition. Prefer leaving font_name unset so the system
            # IME works correctly. Only set `font_name` on non-Windows
            # platforms where we've observed the custom font improves glyph rendering.
            import sys
            if FONT_NAME and not sys.platform.startswith('win'):
                try:
                    ti.font_name = FONT_NAME
                except Exception:
                    pass
        except Exception:
            pass
        ti.size_hint_y = None
        ti.height = dp(40)
        ti.padding = [dp(6), dp(8), dp(6), dp(8)]
        # try to enable IME mode if available on the platform/backends
        try:
            if hasattr(ti, 'ime_mode'):
                ti.ime_mode = 'default'
        except Exception:
            pass
    except Exception:
        pass
    try:
        _register_themable(ti)
    except Exception:
        pass
    return ti

def cell_bg(text, width, height, bg_color):
    from kivy.uix.boxlayout import BoxLayout
    cont = BoxLayout(size_hint=(None, None), width=width, height=height)
    try:
        with cont.canvas.before:
            border_color_instr = Color(* (0,0,0,0.06))
            rect_border = Rectangle(pos=cont.pos, size=cont.size)
            bg_color_instr = Color(*bg_color)
            rect = Rectangle(pos=(cont.x + dp(1), cont.y + dp(1)), size=(max(0, cont.width - dp(2)), max(0, cont.height - dp(2))))
        cont._rect_border = rect_border
        cont._rect = rect
        cont._border_color_instr = border_color_instr
        cont._bg_color_instr = bg_color_instr
        cont._bg_color = bg_color
        cont.bind(pos=lambda inst, *_: setattr(rect_border, 'pos', inst.pos),
                  size=lambda inst, *_: setattr(rect_border, 'size', inst.size))
        cont.bind(pos=lambda inst, *_: setattr(rect, 'pos', (inst.x + dp(1), inst.y + dp(1))),
                  size=lambda inst, *_: setattr(rect, 'size', (max(0, inst.width - dp(2)), max(0, inst.height - dp(2)))))
    except Exception:
        cont._rect_border = None
        cont._rect = None
        cont._border_color_instr = None
        cont._bg_color_instr = None
        cont._bg_color = bg_color
        pass
    lbl = L(text=text, size_hint=(1, 1))
    cont.add_widget(lbl)
    try:
        _register_themable(cont)
    except Exception:
        pass
    return cont

def cell_bg_with_trophy(text, width, height, bg_color, rank=None):
    from kivy.uix.boxlayout import BoxLayout
    cont = BoxLayout(size_hint=(None, None), width=width, height=height)
    try:
        with cont.canvas.before:
            border_color_instr = Color(* (0,0,0,0.06))
            rect_border = Rectangle(pos=cont.pos, size=cont.size)
            bg_color_instr = Color(*bg_color)
            rect = Rectangle(pos=(cont.x + dp(1), cont.y + dp(1)), size=(max(0, cont.width - dp(2)), max(0, cont.height - dp(2))))
        cont._rect_border = rect_border
        cont._rect = rect
        cont._border_color_instr = border_color_instr
        cont._bg_color_instr = bg_color_instr
        cont._bg_color = bg_color
        cont.bind(pos=lambda inst, *_: setattr(rect_border, 'pos', inst.pos),
                  size=lambda inst, *_: setattr(rect_border, 'size', inst.size))
        cont.bind(pos=lambda inst, *_: setattr(rect, 'pos', (inst.x + dp(1), inst.y + dp(1))),
                  size=lambda inst, *_: setattr(rect, 'size', (max(0, inst.width - dp(2)), max(0, inst.height - dp(2)))))
    except Exception:
        cont._rect_border = None
        cont._rect = None
        cont._border_color_instr = None
        cont._bg_color_instr = None
        cont._bg_color = bg_color
        pass
    content = BoxLayout(orientation='horizontal', size_hint=(1,1))
    lbl = L(text=text, size_hint=(1,1))
    content.add_widget(lbl)
    if rank == 1 or rank == 'last':
        try:
            from kivy.uix.image import Image
            import os
            icon_w = None
            _gold = 'assets/icons/trophy_gold.png'
            _gray = 'assets/icons/trophy_gray.png'
            # Prefer FontAwesome glyph when available
            if FA_FONT:
                try:
                    glyph = '\uf091'
                    icon_w = Label(text=glyph, font_name=FA_FONT, font_size=sp(14), size_hint=(None,1), width=dp(20))
                    icon_w.color = (1.0, 0.84, 0.0, 1) if rank == 1 else (0.6,0.6,0.63,1)
                except Exception:
                    icon_w = None
            # If FontAwesome not available, try bundled PNG icons
            if icon_w is None:
                try:
                    from kivy.resources import resource_find
                    img_src = _gold if rank == 1 else _gray
                    found = resource_find(img_src)
                    if found:
                        icon_w = Image(source=found, size_hint=(None,1), width=dp(20))
                except Exception:
                    icon_w = None
            # final fallback: use emoji label
            if icon_w is None:
                try:
                    icon_w = Label(text='🏆', font_size=sp(14), size_hint=(None,1), width=dp(20))
                    icon_w.color = (1.0, 0.84, 0.0, 1) if rank == 1 else (0.6,0.6,0.63,1)
                except Exception:
                    icon_w = None
            if icon_w is not None:
                content.add_widget(icon_w)
        except Exception:
            pass
    cont.add_widget(content)
    try:
        _register_themable(cont)
    except Exception:
        pass
    return cont


def TrophyWidget(rank=None, size=36):
    """Return a simple trophy widget without background for inline use.

    If `rank` is 1 or 'last' the widget shows a colored trophy glyph; else empty.
    """
    try:
        font_size = sp(14)
    except Exception:
        font_size = 14
    # Prefer FontAwesome glyph when available (matches score page), fall back to emoji
    try:
        if FA_FONT:
            glyph = '\uf091'
            if rank == 1:
                lbl = Label(text=glyph, font_name=FA_FONT, font_size=font_size, size_hint=(None, 1), width=dp(size), halign='center', valign='middle')
                try:
                    lbl.color = (1.0, 0.84, 0.0, 1)
                except Exception:
                    pass
                try:
                    lbl.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
                except Exception:
                    pass
                try:
                    _register_themable(lbl)
                except Exception:
                    pass
                return lbl
            elif rank == 'last':
                lbl = Label(text=glyph, font_name=FA_FONT, font_size=font_size, size_hint=(None, 1), width=dp(size), halign='center', valign='middle')
                try:
                    lbl.color = (0.6, 0.6, 0.63, 1)
                except Exception:
                    pass
                try:
                    lbl.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
                except Exception:
                    pass
                try:
                    _register_themable(lbl)
                except Exception:
                    pass
                return lbl
            else:
                lbl = Label(text='', size_hint=(None, 1), width=dp(size))
                try:
                    lbl.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
                except Exception:
                    pass
                try:
                    _register_themable(lbl)
                except Exception:
                    pass
                return lbl
        else:
            # No FontAwesome available; use emoji which may rely on system fallback fonts
            if rank == 1:
                lbl = Label(text='🏆', font_size=font_size, color=(1.0, 0.84, 0.0, 1), size_hint=(None, 1), width=dp(size), halign='center', valign='middle')
            elif rank == 'last':
                lbl = Label(text='🏆', font_size=font_size, color=(0.6, 0.6, 0.63, 1), size_hint=(None, 1), width=dp(size), halign='center', valign='middle')
            else:
                lbl = Label(text='', size_hint=(None, 1), width=dp(size))
            try:
                lbl.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
            except Exception:
                pass
            try:
                _register_themable(lbl)
            except Exception:
                pass
            return lbl
    except Exception:
        # ultimate fallback: plain empty L()
        return L(text='' if rank is None else '🏆' if rank == 1 else '🏆', size_hint_x=None, width=dp(size))

def BTN(text, **kw):
    kw.setdefault("size_hint_y", None)
    kw.setdefault("height", _T('BTN_HEIGHT'))
    if FONT_NAME:
        kw.setdefault("font_name", FONT_NAME)
        kw.setdefault("font_size", _T('SMALL_FONT'))
    btn = Button(text=text, **kw)
    style_button(btn)
    return btn

class IconButton(ButtonBehavior, Widget):
    def __init__(self, symbol: str = 'plus', **kw):
        for _k in ('font_size', 'font_name', 'text', 'markup',
                   'background_normal', 'background_down', 'background_color', 'color'):
            if _k in kw:
                kw.pop(_k, None)
        kw.setdefault('size_hint', (None, None))
        kw.setdefault('width', dp(36))
        kw.setdefault('height', dp(36))
        super().__init__(**kw)
        self.symbol = symbol
        self._bg_color_instruction = None
        self._bg_ellipse = None
        self._mark_graphics = []
        self._mark_color_instruction = None
        try:
            with self.canvas.before:
                self._bg_color_instruction = Color(*_T('BTN_BG'))
                self._bg_ellipse = Ellipse(pos=self.pos, size=self.size)
            with self.canvas:
                self._mark_color_instruction = Color(*_T('TEXT_COLOR'))
                lw = dp(2.5)
                for _ in range(3):
                    self._mark_graphics.append(Line(points=[], width=lw))
        except Exception:
            self._bg_color_instruction = None
            self._bg_ellipse = None
            self._mark_graphics = []
        self.bind(pos=self._update_graphics, size=self._update_graphics)
        try:
            _register_themable(self)
        except Exception:
            pass

    def _update_graphics(self, *a):
        try:
            if self._bg_ellipse is not None:
                self._bg_ellipse.pos = self.pos
                self._bg_ellipse.size = self.size
            cx = self.x + self.width / 2.0
            cy = self.y + self.height / 2.0
            w = self.width
            h = self.height
            pad = min(w, h) * 0.28
            left = self.x + (w - pad) / 2.0
            right = self.x + (w + pad) / 2.0
            top = self.y + (h + pad) / 2.0
            bottom = self.y + (h - pad) / 2.0

            def set_line(i, pts):
                try:
                    if i < len(self._mark_graphics):
                        self._mark_graphics[i].points = pts
                except Exception:
                    pass

            for i in range(len(self._mark_graphics)):
                set_line(i, [])
            sym = (self.symbol or '').lower()
            if sym in ('minus', '−', '➖'):
                set_line(0, [left, cy, right, cy])
            elif sym in ('plus', '+', '➕'):
                set_line(0, [left, cy, right, cy]); set_line(1, [cx, bottom, cx, top])
            elif sym in ('check', 'ok'):
                x1 = self.x + w * 0.22; y1 = self.y + h * 0.45
                x2 = self.x + w * 0.42; y2 = self.y + h * 0.30
                x3 = self.x + w * 0.78; y3 = self.y + h * 0.70
                set_line(0, [x1, y1, x2, y2, x3, y3])
            elif sym in ('x', 'close'):
                set_line(0, [left, bottom, right, top]); set_line(1, [left, top, right, bottom])
            elif sym in ('play', 'triangle'):
                x1 = self.x + w * 0.30; y1 = self.y + h * 0.20
                x2 = self.x + w * 0.30; y2 = self.y + h * 0.80
                x3 = self.x + w * 0.78; y3 = self.y + h * 0.50
                set_line(0, [x1, y1, x2, y2, x3, y3, x1, y1])
            else:
                if self.symbol in ('➕','+'):
                    set_line(0, [left, cy, right, cy]); set_line(1, [cx, bottom, cx, top])
                elif self.symbol in ('➖','-'):
                    set_line(0, [left, cy, right, cy])
                else:
                    set_line(0, [cx, cy, cx + 0.01, cy + 0.01])
        except Exception:
            pass

    def on_press(self):
        try:
            if self._bg_color_instruction is not None:
                r,g,b,a = _T('BTN_BG')
                self._bg_color_instruction.rgba = (r,g,b,max(0.06, a * 1.8))
        except Exception:
            pass

    def on_release(self):
        try:
            if self._bg_color_instruction is not None:
                self._bg_color_instruction.rgba = _T('BTN_BG')
        except Exception:
            pass

class IconTextButton(ButtonBehavior, BoxLayout):
    def __init__(self, text: str = '', icon: str = None, **kwargs):
        h = kwargs.pop('height', _T('BTN_HEIGHT'))
        size_hint_y = kwargs.pop('size_hint_y', None)
        super().__init__(orientation='horizontal', spacing=dp(8), padding=(dp(8), dp(6)), **kwargs)
        self._raw_text = text or ''
        try:
            with self.canvas.before:
                self._bg_color_instr = Color(*_T('BTN_BG'))
                self._bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=lambda inst, *_: setattr(self._bg_rect, 'pos', inst.pos), size=lambda inst, *_: setattr(self._bg_rect, 'size', inst.size))
        except Exception:
            self._bg_color_instr = None
            self._bg_rect = None
        try:
            _register_themable(self)
        except Exception:
            pass
        if icon:
            def _map_icon(name: str):
                if not name:
                    return None
                n = name.lower().replace('_','-')
                mapping = {'content-save':'save','file-download':'save','file-upload':'import','import':'import','plus':'plus','close':'x','delete':'trash','trash':'trash','check':'check','play':'play','wrench':'wrench','cog':'wrench'}
                if n in mapping:
                    return mapping[n]
                if 'save' in n or 'download' in n or 'file' in n:
                    return 'save'
                if 'upload' in n or 'import' in n:
                    return 'import'
                if 'trash' in n or 'delete' in n:
                    return 'trash'
                if 'close' in n or 'cancel' in n or 'x' in n:
                    return 'x'
                if 'plus' in n or 'add' in n:
                    return 'plus'
                return None
            mapped = _map_icon(icon)
            icon_w = None
            try:
                if FA_FONT and mapped:
                    glyph_map = {'save':'\uf0c7','import':'\uf093','export':'\uf093','plus':'\uf067','minus':'\uf068','trash':'\uf1f8','x':'\uf00d','check':'\uf00c','play':'\uf04b','wrench':'\uf0ad'}
                    glyph = glyph_map.get(mapped)
                    if glyph:
                        icon_w = Label(text=glyph, font_name=FA_FONT, font_size=sp(16), size_hint=(None,None), size=(dp(28), dp(28)))
                        try:
                            icon_w.color = _T('TEXT_COLOR')
                        except Exception:
                            pass
                        try:
                            _register_themable(icon_w)
                        except Exception:
                            pass
            except Exception:
                icon_w = None
            if icon_w is None:
                icon_w = IconButton(mapped or (icon or '+'), width=dp(28), height=dp(28))
                try:
                    icon_w.disabled = True
                except Exception:
                    pass
            self.add_widget(icon_w)
        self._label = Label(text=self._raw_text, halign='left', valign='middle', size_hint_x=1)
        try:
            self._label.markup = True
        except Exception:
            pass
        try:
            if FONT_NAME:
                self._label.font_name = FONT_NAME
            self._label.font_size = _T('SMALL_FONT')
            self._label.color = _T('TEXT_COLOR')
            self._label.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
            try:
                self._label.text_size = (self._label.width, self._label.height)
            except Exception:
                pass
        except Exception:
            pass
        try:
            _register_themable(self._label)
        except Exception:
            pass
        self.add_widget(self._label)
        try:
            if size_hint_y is not None:
                self.size_hint_y = size_hint_y
            else:
                self.size_hint_y = None
                self.height = h
        except Exception:
            pass

    @property
    def text(self):
        return self._label.text

    @text.setter
    def text(self, v):
        try:
            self._label.text = v
        except Exception:
            pass

    def restyle(self):
        try:
            if getattr(self, 'disabled', False):
                lbl_color = (1,1,1,0.8) if _T('CURRENT_THEME') == 'dark' else (0.45,0.45,0.45,1)
            else:
                lbl_color = (1,1,1,1) if _T('CURRENT_THEME') == 'dark' else _T('TEXT_COLOR')
            try:
                self._label.color = lbl_color
            except Exception:
                pass
            try:
                if hasattr(self, '_label'):
                    if not getattr(self._label, 'text_size', None) or (isinstance(getattr(self._label, 'text_size', None), (list, tuple)) and None in getattr(self._label, 'text_size', (None, None))):
                        try:
                            self._label.text_size = (self._label.width, self._label.height)
                        except Exception:
                            pass
                    try:
                        if hasattr(self._label, 'texture_update'):
                            try:
                                self._label.texture_update()
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass
            if getattr(self, '_bg_color_instr', None) is not None:
                try:
                    self._bg_color_instr.rgba = _T('BTN_BG')
                except Exception:
                    pass
            for ch in getattr(self, 'children', []):
                if hasattr(ch, '_mark_color_instruction') and ch._mark_color_instruction is not None:
                    try:
                        ch._mark_color_instruction.rgba = _T('ACCENT') if _T('CURRENT_THEME') == 'dark' else _T('TEXT_COLOR')
                    except Exception:
                        pass
        except Exception:
            pass

class NameTouchable(Label):
    """Label that supports long-press detection.

    Dispatches an 'on_long_press' event with signature (self, touch).
    """
    __events__ = ('on_long_press',)

    def __init__(self, row_container=None, long_press_time=0.5, **kw):
        try:
            if FONT_NAME:
                kw.setdefault('font_name', FONT_NAME)
        except Exception:
            pass
        kw.setdefault('font_size', _T('SMALL_FONT'))
        kw.setdefault('color', _T('TEXT_COLOR'))
        kw.setdefault('halign', 'left')
        kw.setdefault('valign', 'middle')
        super().__init__(**kw)
        from kivy.clock import Clock
        self._lp_time = float(long_press_time)
        self._lp_ev = None
        self._touch = None
        self._long_pressed = False
        try:
            _register_themable(self)
        except Exception:
            pass

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        try:
            from kivy.clock import Clock
            self._touch = touch
            self._lp_ev = Clock.schedule_once(lambda dt: self._do_long_press(touch), self._lp_time)
        except Exception:
            self._lp_ev = None
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._lp_ev is not None and touch is self._touch and not self.collide_point(*touch.pos):
            try:
                self._lp_ev.cancel()
            except Exception:
                pass
            self._lp_ev = None
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._lp_ev is not None:
            try:
                self._lp_ev.cancel()
            except Exception:
                pass
            self._lp_ev = None
        self._touch = None
        return super().on_touch_up(touch)

    def _do_long_press(self, touch):
        self._lp_ev = None
        self._long_pressed = True
        try:
            self.dispatch('on_long_press', touch)
        except Exception:
            pass

    def on_long_press(self, touch):
        pass


# ---------------------- Score input item (new) ----------------------
class ScoreInputItem(BoxLayout):
    """A reusable container for per-player score inputs.

    Layout (horizontal): [base_input] [minus_btn] [dun_input] [plus_btn]

    Designed so the whole widget can be treated as a single draggable
    container in the future.
    """

    def __init__(self, base: int = 100, dun: int = 0, dun_score: int = 30, name: str = '', **kw):
        super().__init__(orientation='horizontal', spacing=dp(8), **kw)

        self.base_value = base
        self.dun_value = dun
        self.dun_score = dun_score

        # optional player name label at the start
        try:
            # use a touchable name widget so long-press can be detected safely
            self.name_label = NameTouchable(text=(name or ''), size_hint_x=None, width=dp(120), halign='left', valign='middle')
            try:
                self.name_label.bind(on_long_press=self._on_name_long_press)
            except Exception:
                pass
            try:
                self.name_label.bind(on_touch_up=self._on_name_touch_up)
            except Exception:
                pass
            self.add_widget(self.name_label)
        except Exception:
            self.name_label = None

        # base score input
        self.base_input = TI(text=str(self.base_value))
        self.base_input.size_hint_x = None
        self.base_input.width = dp(80)
        self.add_widget(self.base_input)

        # minus button
        self.minus_btn = IconButton(symbol='minus', width=dp(36), height=dp(36))
        self.minus_btn.bind(on_release=self._on_minus)
        self.add_widget(self.minus_btn)

        # dun count input
        self.dun_input = TI(text=str(self.dun_value))
        self.dun_input.size_hint_x = None
        self.dun_input.width = dp(60)
        self.add_widget(self.dun_input)

        # plus button
        self.plus_btn = IconButton(symbol='plus', width=dp(36), height=dp(36))
        self.plus_btn.bind(on_release=self._on_plus)
        self.add_widget(self.plus_btn)

    def _on_plus(self, *_):
        try:
            v = int(self.dun_input.text or '0')
            v += 1
            self.dun_input.text = str(v)
        except Exception:
            self.dun_input.text = '0'

    def _on_minus(self, *_):
        try:
            v = int(self.dun_input.text or '0')
            v = max(0, v - 1)
            self.dun_input.text = str(v)
        except Exception:
            self.dun_input.text = '0'

    # long-press handlers
    def _on_name_long_press(self, inst, touch):
        try:
            # visual cue: make the whole input item semi-transparent
            self._long_pressed = True
            self.opacity = 0.5
        except Exception:
            pass

    def _on_name_touch_up(self, inst, touch):
        try:
            if getattr(self, '_long_pressed', False):
                self._long_pressed = False
                self.opacity = 1.0
        except Exception:
            pass

    def get_values(self):
        try:
            base = int(self.base_input.text or '0')
        except Exception:
            base = self.base_value
        try:
            dun = int(self.dun_input.text or '0')
        except Exception:
            dun = self.dun_value
        return {'base': base, 'dun': dun, 'dun_score': self.dun_score}
        return {'base': base, 'dun': dun, 'dun_score': self.dun_score}
