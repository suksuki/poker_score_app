from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.properties import StringProperty, ColorProperty, NumericProperty, ObjectProperty
from theme import theme_manager
from utils.logger import logger
import os
import sys
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.dropdown import DropDown

# ----------------------------------------------------------------------
# Resource Helper
# ----------------------------------------------------------------------
def _find_resource_file(relative_path):
    if not relative_path:
        return None
    try:
        from kivy.resources import resource_find
        found = resource_find(relative_path)
        if found:
            return found
    except Exception:
        pass
    
    candidates = [
        lambda: os.path.abspath(relative_path),
        lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path),
        lambda: os.path.join(os.getcwd(), relative_path),
    ]
    
    for c in candidates:
        try:
            p = c()
            if os.path.exists(p):
                return p
        except Exception:
            continue
            
    return relative_path

# ----------------------------------------------------------------------
# Base Styled Widgets
# ----------------------------------------------------------------------

class L(Label):
    """Themed Label."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Bind properties to ThemeManager
        self.bind_theme()
        
    def bind_theme(self):
        # Font
        self.font_size = theme_manager.small_font
        if theme_manager.font_name:
            self.font_name = theme_manager.font_name
        
        # Color
        self.color = theme_manager.text_color
        
        # Reactive Bindings
        theme_manager.bind(small_font=self.setter('font_size'))
        theme_manager.bind(font_name=self.setter('font_name'))
        theme_manager.bind(text_color=self.setter('color'))
        
        # Ensure text size follows size for wrapping if needed
        self.bind(size=self._update_text_size)

    def _update_text_size(self, *args):
        self.text_size = (self.width, self.height)


class H(Label):
    """Header Label."""
    def __init__(self, **kwargs):
        kwargs.setdefault('font_size', sp(16))
        super().__init__(**kwargs)
        self.color = theme_manager.text_color
        if theme_manager.font_name:
            self.font_name = theme_manager.font_name
            
        theme_manager.bind(text_color=self.setter('color'))
        theme_manager.bind(font_name=self.setter('font_name'))
        self.bind(size=self._update_text_size)

    def _update_text_size(self, *args):
        self.text_size = (self.width, self.height)


class TI(TextInput):
    """Themed TextInput."""
    def __init__(self, **kwargs):
        kwargs.setdefault('multiline', False)
        kwargs.setdefault('background_normal', "")
        kwargs.setdefault('background_active', "")
        kwargs.setdefault('write_tab', True)
        super().__init__(**kwargs)
        
        self.padding = [dp(6), dp(8), dp(6), dp(8)]
        self.size_hint_y = None
        self.height = dp(40)
        
        # Initial Colors
        self.background_color = theme_manager.panel_bg
        self.foreground_color = theme_manager.text_color
        self.cursor_color = theme_manager.accent
        
        # Bindings
        theme_manager.bind(panel_bg=self.setter('background_color'))
        theme_manager.bind(text_color=self.setter('foreground_color'))
        theme_manager.bind(accent=self.setter('cursor_color'))
        theme_manager.bind(input_font=self.setter('font_size'))

        # Font handling (win32 IME safe)
        if not sys.platform.startswith('win'):
            self.font_name = theme_manager.font_name
            theme_manager.bind(font_name=self.setter('font_name'))

class BTN(Button):
    """Themed Button."""
    def __init__(self, **kwargs):
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', theme_manager.btn_height)
        super().__init__(**kwargs)
        
        self.background_normal = ''
        self.background_down = ''
        self.background_color = theme_manager.btn_bg
        self.color = theme_manager.text_color
        self.font_size = sp(13)
        
        theme_manager.bind(btn_bg=self.setter('background_color'))
        theme_manager.bind(text_color=self.setter('color'))
        theme_manager.bind(font_name=self.setter('font_name'))


# ----------------------------------------------------------------------
# Complex Components
# ----------------------------------------------------------------------

class IconButton(ButtonBehavior, Widget):
    symbol = StringProperty('plus')
    
    def __init__(self, symbol='plus', **kwargs):
        # Clean kwargs
        for k in ['text', 'markup', 'background_normal', 'background_color']:
            kwargs.pop(k, None)
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('width', dp(36))
        kwargs.setdefault('height', dp(36))
        super().__init__(**kwargs)
        self.symbol = symbol
        
        with self.canvas.before:
            self._bg_color = Color(*theme_manager.btn_bg)
            self._bg_ellipse = Ellipse(pos=self.pos, size=self.size)
        with self.canvas:
            self._mark_color = Color(*theme_manager.text_color)
            self._lines = [Line(width=dp(2.5)) for _ in range(3)]

        self.bind(pos=self._update_graphics, size=self._update_graphics)
        self.bind(symbol=self._update_graphics)
        
        # Theme Bindings
        theme_manager.bind(btn_bg=lambda _, v: setattr(self._bg_color, 'rgba', v))
        theme_manager.bind(text_color=lambda _, v: setattr(self._mark_color, 'rgba', v))

    def _update_graphics(self, *args):
        self._bg_ellipse.pos = self.pos
        self._bg_ellipse.size = self.size
        
        # Draw Symbol Logic
        w, h = self.size
        cx, cy = self.x + w/2, self.y + h/2
        pad = min(w, h) * 0.28
        left, right = self.x + (w-pad)/2, self.x + (w+pad)/2
        top, bottom = self.y + (h+pad)/2, self.y + (h-pad)/2

        # Clear lines
        for l in self._lines: l.points = []

        sym = self.symbol.lower()
        if sym in ('minus', '-'):
            self._lines[0].points = [left, cy, right, cy]
        elif sym in ('plus', '+'):
            self._lines[0].points = [left, cy, right, cy]
            self._lines[1].points = [cx, bottom, cx, top]
        elif sym in ('x', 'close'):
            self._lines[0].points = [left, bottom, right, top]
            self._lines[1].points = [left, top, right, bottom]
        # ... Add other symbols as needed

    def on_press(self):
        r,g,b,a = theme_manager.btn_bg
        self._bg_color.rgba = (r, g, b, max(0.1, a*2))

    def on_release(self):
        self._bg_color.rgba = theme_manager.btn_bg


class IconTextButton(ButtonBehavior, BoxLayout):
    text = StringProperty('')
    
    def __init__(self, text='', icon=None, **kwargs):
        kwargs.setdefault('height', theme_manager.btn_height)
        super().__init__(orientation='horizontal', spacing=dp(8), padding=(dp(8), dp(6)), **kwargs)
        self.text = text
        
        # Background
        with self.canvas.before:
            self._bg_color = Color(*theme_manager.btn_bg)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
            
        self.bind(pos=lambda _,v: setattr(self._bg_rect, 'pos', v),
                  size=lambda _,v: setattr(self._bg_rect, 'size', v))

        # Icon
        if icon:
            self.add_widget(self._create_icon_widget(icon))
            
        # Label
        self._label = Label(text=text, halign='left', valign='middle', size_hint_x=1, markup=True)
        self._label.color = theme_manager.text_color
        self._label.font_size = theme_manager.small_font
        if theme_manager.font_name:
            self._label.font_name = theme_manager.font_name
        
        self.add_widget(self._label)
        
        # Bindings
        theme_manager.bind(btn_bg=lambda _,v: setattr(self._bg_color, 'rgba', v))
        theme_manager.bind(text_color=self.setter_label_color)
        self.bind(text=lambda _,v: setattr(self._label, 'text', v))

    def setter_label_color(self, _, color):
        self._label.color = color

    def _create_icon_widget(self, icon_name):
        # Simplified icon mapping
        fa_map = {'save': '\uf0c7', 'import': '\uf093', 'plus': '\uf067', 'delete': '\uf1f8'}
        mapped = icon_name.lower()
        if 'save' in mapped: code = fa_map['save']
        elif 'import' in mapped: code = fa_map['import']
        elif 'delete' in mapped: code = fa_map['delete']
        elif 'plus' in mapped: code = fa_map['plus']
        else: code = None

        if code and theme_manager.fa_font:
            l = Label(text=code, font_name=theme_manager.fa_font, font_size=sp(16), 
                      size_hint=(None,None), size=(dp(28),dp(28)))
            theme_manager.bind(text_color=l.setter('color'))
            return l
        
        return IconButton(symbol=icon_name, width=dp(28), height=dp(28))


class NameTouchable(Label):
    """Long-press aware Label."""
    __events__ = ('on_long_press',)
    
    def __init__(self, **kw):
        super().__init__(**kw)
        self.color = theme_manager.text_color
        self.font_size = theme_manager.small_font
        theme_manager.bind(text_color=self.setter('color'))
        self._lp_ev = None

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._lp_ev = Clock.schedule_once(lambda dt: self.dispatch('on_long_press', touch), 0.5)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._lp_ev: self._lp_ev.cancel()
        return super().on_touch_up(touch)
        
    def on_long_press(self, touch):
        pass


class ScoreInputItem(BoxLayout):
    """Combines Name, Base Input, Buttons, Dun Input."""
    def __init__(self, base=100, dun=0, dun_score=30, name='', **kw):
        super().__init__(orientation='horizontal', spacing=dp(8), **kw)
        
        # Name
        self.name_label = NameTouchable(text=name, size_hint_x=None, width=dp(120), halign='left', valign='middle')
        self.name_label.bind(size=lambda *_: setattr(self.name_label, 'text_size', self.name_label.size))
        self.add_widget(self.name_label)
        
        # Base
        self.base_input = TI(text=str(base))
        self.base_input.width = dp(80)
        self.base_input.size_hint_x = None
        self.add_widget(self.base_input)
        
        # Controls (Minus/Plus Dun)
        self.dun_val = dun
        self.dun_score = dun_score
        
        btn_minus = IconButton('minus', width=dp(36))
        btn_minus.bind(on_release=self._dec_dun)
        self.add_widget(btn_minus)
        
        self.dun_input = TI(text=str(dun))
        self.dun_input.width = dp(50)
        self.dun_input.size_hint_x = None
        self.add_widget(self.dun_input)
        
        btn_plus = IconButton('plus', width=dp(36))
        btn_plus.bind(on_release=self._inc_dun)
        self.add_widget(btn_plus)

    def _dec_dun(self, *a):
        try:
            v = int(self.dun_input.text)
            self.dun_input.text = str(v - 1)
        except: pass

    def _inc_dun(self, *a):
        try:
            v = int(self.dun_input.text)
            self.dun_input.text = str(v + 1)
        except: pass
        
    def get_values(self):
        return {
            'base': self.base_input.text,
            'dun': self.dun_input.text,
            'dun_score': self.dun_score
        }

# ----------------------------------------------------------------------
# Helper Cells for Scoreboard (Functional style replacement)
# ----------------------------------------------------------------------

def CellWithBg(text, w, h, bg_prop_name):
    """
    Returns a configured BoxLayout with background bound to theme property.
    """
    box = BoxLayout(size_hint=(None, None), width=w, height=h)
    
    with box.canvas.before:
        # Border
        Color(*theme_manager.border_color)
        border = Rectangle(pos=box.pos, size=box.size)
        
        # Background
        c_bg = Color(*getattr(theme_manager, bg_prop_name))
        rect = Rectangle(pos=(box.x+dp(1), box.y+dp(1)), 
                         size=(max(0, box.width-dp(2)), max(0, box.height-dp(2))))
    
    # Bindings
    def update_graphics(*_):
        border.pos = box.pos
        border.size = box.size
        rect.pos = (box.x+dp(1), box.y+dp(1))
        rect.size = (max(0, box.width-dp(2)), max(0, box.height-dp(2)))
        
    box.bind(pos=update_graphics, size=update_graphics)
    
    # Theme binding
    theme_manager.bind(**{bg_prop_name: lambda _,v: setattr(c_bg, 'rgba', v)})
    
    l = L(text=str(text), size_hint=(1,1))
    box.add_widget(l)
    return box

def TrophyWidget(rank=None, size=36):
    """Returns just the label/icon for trophy."""
    txt = ''
    color = (0,0,0,0)
    
    if rank == 1:
        txt = '\uf091' if theme_manager.fa_font else '🏆'
        color = (1.0, 0.84, 0.0, 1)
    elif rank == 'last':
        txt = '\uf091' if theme_manager.fa_font else '🏆'
        color = (0.6, 0.6, 0.63, 1)

    l = Label(text=txt, font_size=sp(14), size_hint=(None, 1), width=dp(size))
    l.color = color
    
    if theme_manager.fa_font and rank:
        l.font_name = theme_manager.fa_font
        
    l.bind(size=lambda *_: setattr(l, 'text_size', l.size))
    return l


class Separator(Widget):
    def __init__(self, **kwargs):
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', dp(1))
        super().__init__(**kwargs)
        with self.canvas:
            self._color = Color(*theme_manager.border_color)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._update, size=self._update)
        theme_manager.bind(border_color=lambda _,v: setattr(self._color, 'rgba', v))

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class RadioToggle(ToggleButton):
    """Themed ToggleButton."""
    def __init__(self, **kwargs):
        kwargs.setdefault('height', theme_manager.btn_height)
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = theme_manager.btn_bg
        self.color = theme_manager.text_color
        self.font_size = sp(13)
        
        # We need to handle state visually if we remove background_normal/down
        # But ToggleButton usually handles 'down' state by itself if we kept defaults.
        # Since we removed them, we rely on background_color.
        # But background_color doesn't automatically change on state 'down' unless we bind.
        
        self.bind(state=self._on_state)
        theme_manager.bind(btn_bg=self._update_colors)
        theme_manager.bind(accent=self._update_colors)
        theme_manager.bind(text_color=self.setter('color'))
        theme_manager.bind(font_name=self.setter('font_name'))
        
    def _on_state(self, instance, value):
        self._update_colors()
        
    def _update_colors(self, *args):
        if self.state == 'down':
             self.background_color = theme_manager.accent
             self.color = (1,1,1,1) # Force white on accent? Or theme_manager.text_color?
             # Usually accent is dark -> white text.
        else:
             self.background_color = theme_manager.btn_bg
             self.color = theme_manager.text_color


class AnimatedDropDown(DropDown):
    """Simple DropDown placeholder."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Assuming no special animation logic needed for MVP reset, just standard behavior.

