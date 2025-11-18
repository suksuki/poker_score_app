# theme.py -- 提供主题变量与 apply_theme
from kivy.core.window import Window
from kivy.metrics import sp, dp
import os
from kivy.core.text import LabelBase

# 颜色与尺寸常量
COLOR_BG = (0.96, 0.96, 0.98, 1)
PANEL_BG = (1.00, 1.00, 1.00, 1)
HEADER_BG = (0.95, 0.95, 0.97, 1)
ROW_DARK = (0.98, 0.98, 0.99, 1)
ROW_LIGHT = (0.99, 0.99, 1.00, 1)
TOTAL_BG = HEADER_BG
BORDER_COLOR = (0, 0, 0, 0.06)
BTN_BG = (0, 0, 0, 0.06)
ACCENT = (0.00, 0.48, 1.00, 1)
TEXT_COLOR = (0.12, 0.12, 0.13, 1)
SMALL_FONT = sp(12)
INPUT_FONT = sp(12)
BTN_HEIGHT = dp(38)
ROW_HEIGHT = dp(48)

THEMES = {
    'light': {
        'COLOR_BG': COLOR_BG,
        'PANEL_BG': PANEL_BG,
        'HEADER_BG': HEADER_BG,
        'ROW_DARK': ROW_DARK,
        'ROW_LIGHT': ROW_LIGHT,
        'BORDER_COLOR': BORDER_COLOR,
        'BTN_BG': BTN_BG,
        'ACCENT': ACCENT,
        'TEXT_COLOR': TEXT_COLOR,
    },
    'dark': {
        'COLOR_BG': (0.03, 0.03, 0.04, 1),
        'PANEL_BG': (0.04, 0.04, 0.05, 1),
        'HEADER_BG': (0.12, 0.12, 0.14, 1),
        'ROW_DARK': (0.05, 0.05, 0.06, 1),
        'ROW_LIGHT': (0.09, 0.09, 0.10, 1),
        'BORDER_COLOR': (0, 0, 0, 0.35),
        'BTN_BG': (0, 0, 0, 0.12),
        'ACCENT': (0.10, 0.6, 0.95, 1),
        'TEXT_COLOR': (1, 1, 1, 1),
    }
}

CURRENT_THEME = 'light'

def apply_theme(name: str):
    global CURRENT_THEME, COLOR_BG, PANEL_BG, HEADER_BG, ROW_DARK, ROW_LIGHT, TOTAL_BG
    global BORDER_COLOR, BTN_BG, ACCENT, TEXT_COLOR
    theme = THEMES.get(name, THEMES['light'])
    CURRENT_THEME = name
    COLOR_BG = theme['COLOR_BG']
    PANEL_BG = theme['PANEL_BG']
    HEADER_BG = theme['HEADER_BG']
    ROW_DARK = theme['ROW_DARK']
    ROW_LIGHT = theme['ROW_LIGHT']
    BORDER_COLOR = theme['BORDER_COLOR']
    BTN_BG = theme['BTN_BG']
    ACCENT = theme['ACCENT']
    TEXT_COLOR = theme['TEXT_COLOR']
    TOTAL_BG = HEADER_BG
    try:
        Window.clearcolor = COLOR_BG
    except Exception:
        pass
    # notify any registered listeners so UI can refresh dynamic graphics
    try:
        for cb in _THEME_LISTENERS:
            try:
                cb()
            except Exception:
                pass
    except Exception:
        pass

# 立即应用
apply_theme(CURRENT_THEME)

# 字体注册（尝试项目内中文字体与系统 FontAwesome）
FONT_NAME = None
_candidate = os.path.join(os.path.dirname(__file__), "assets", "fonts", "NotoSansSC-Regular.ttf")
if os.path.exists(_candidate):
    try:
        LabelBase.register(name="AppFont", fn_regular=_candidate)
        # Also register/override the common default 'Roboto' font so Kivy widgets
        # that rely on the default font will render Chinese glyphs without
        # needing to set `font_name` everywhere.
        try:
            LabelBase.register(name="Roboto", fn_regular=_candidate)
        except Exception:
            pass
        FONT_NAME = "AppFont"
    except Exception:
        FONT_NAME = _candidate

FA_FONT = None
_fa_candidates = [
    '/usr/share/fonts/opentype/font-awesome/FontAwesome.otf',
    '/usr/share/fonts/truetype/font-awesome/fontawesome-webfont.ttf',
    '/usr/share/fonts/truetype/font-awesome/FontAwesome.otf',
    '/usr/share/fonts/truetype/fontawesome-webfont.ttf',
]
for _fp in _fa_candidates:
    try:
        if os.path.exists(_fp):
            try:
                LabelBase.register(name='FA', fn_regular=_fp)
                FA_FONT = 'FA'
                break
            except Exception:
                FA_FONT = None
    except Exception:
        pass

# simple listener registry so other modules can refresh visuals when theme changes
_THEME_LISTENERS = []

def register_theme_listener(cb):
    try:
        if cb not in _THEME_LISTENERS:
            _THEME_LISTENERS.append(cb)
    except Exception:
        pass

def unregister_theme_listener(cb):
    try:
        if cb in _THEME_LISTENERS:
            _THEME_LISTENERS.remove(cb)
    except Exception:
        pass


# Global widget style injection:
# Apply the project's `FONT_NAME` and `TEXT_COLOR` to common widget classes so
# newly created pages don't need to set `font_name` individually.
def _inject_global_widget_defaults():
    try:
        from kivy.uix.label import Label
        from kivy.uix.textinput import TextInput

        # Limit injection to Label and TextInput only to avoid overwriting
        # explicit icon fonts set on Buttons/Spinners (e.g. FontAwesome).
        classes = [Label, TextInput]

        for cls in classes:
            # avoid double-injection
            if getattr(cls, '_theme_injected', False):
                continue

            orig_init = getattr(cls, '__init__', None)
            if not orig_init:
                continue

            def make_init(orig):
                def new_init(self, *args, **kwargs):
                    # Call original initializer
                    orig(self, *args, **kwargs)
                    # Apply font and color when available. Only set font_name
                    # if it's not already set or equals Kivy's DEFAULT_FONT so
                    # we don't overwrite explicit icon fonts (e.g. FA).
                    try:
                        from kivy.core.text import DEFAULT_FONT
                        cur = getattr(self, 'font_name', None)
                        if FONT_NAME and (not cur or cur == DEFAULT_FONT):
                            self.font_name = FONT_NAME
                    except Exception:
                        pass
                    try:
                        if hasattr(self, 'color') and TEXT_COLOR and getattr(self, 'color', None) != TEXT_COLOR:
                            self.color = TEXT_COLOR
                    except Exception:
                        pass
                return new_init

            try:
                setattr(cls, '__init__', make_init(orig_init))
                setattr(cls, '_theme_injected', True)
            except Exception:
                pass
    except Exception:
        pass


# perform injection at import time
_inject_global_widget_defaults()
