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
# ACCENT kept neutral gray per user preference (no bright blue)
ACCENT = (0.20, 0.20, 0.22, 1)
TEXT_COLOR = (0.12, 0.12, 0.13, 1)
# Dropdown / Spinner palette
DROPDOWN_BG = (0.44, 0.44, 0.46, 1)
DROPDOWN_OPTION_BG = (0.54, 0.54, 0.56, 1)
DROPDOWN_OPTION_PRESSED = (0.40, 0.40, 0.42, 1)
DROPDOWN_SEPARATOR_COLOR = (0.36, 0.36, 0.38, 1)
# card-specific styling (for poker-like visuals)
CARD_BG = (1.0, 1.0, 1.0, 1)
CARD_BORDER = (0.9, 0.9, 0.92, 1)
CARD_SHADOW = (0, 0, 0, 0.06)
SUIT_COLORS = {'♠': (0.12, 0.12, 0.13, 1), '♣': (0.12, 0.12, 0.13, 1), '♥': (0.12, 0.12, 0.13, 1), '♦': (0.12, 0.12, 0.13, 1)}
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
        'CARD_BG': CARD_BG,
        'CARD_BORDER': CARD_BORDER,
        'CARD_SHADOW': CARD_SHADOW,
        'SUIT_COLORS': SUIT_COLORS,
    },
    'dark': {
        'COLOR_BG': (0.03, 0.03, 0.04, 1),
        'PANEL_BG': (0.04, 0.04, 0.05, 1),
        'HEADER_BG': (0.12, 0.12, 0.14, 1),
        'ROW_DARK': (0.05, 0.05, 0.06, 1),
        'ROW_LIGHT': (0.09, 0.09, 0.10, 1),
        'BORDER_COLOR': (0, 0, 0, 0.35),
        'BTN_BG': (0, 0, 0, 0.12),
        'ACCENT': ACCENT,
        'TEXT_COLOR': (1, 1, 1, 1),
        'CARD_BG': (0.06, 0.06, 0.07, 1),
        'CARD_BORDER': (0.08, 0.08, 0.09, 1),
        'CARD_SHADOW': (0, 0, 0, 0.3),
        'SUIT_COLORS': SUIT_COLORS,
        'DROPDOWN_BG': DROPDOWN_BG,
        'DROPDOWN_OPTION_BG': DROPDOWN_OPTION_BG,
        'DROPDOWN_OPTION_PRESSED': DROPDOWN_OPTION_PRESSED,
        'DROPDOWN_SEPARATOR_COLOR': DROPDOWN_SEPARATOR_COLOR,
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
    # dropdown related
    try:
        global DROPDOWN_BG, DROPDOWN_OPTION_BG, DROPDOWN_OPTION_PRESSED, DROPDOWN_SEPARATOR_COLOR
        DROPDOWN_BG = theme.get('DROPDOWN_BG', DROPDOWN_BG)
        DROPDOWN_OPTION_BG = theme.get('DROPDOWN_OPTION_BG', DROPDOWN_OPTION_BG)
        DROPDOWN_OPTION_PRESSED = theme.get('DROPDOWN_OPTION_PRESSED', DROPDOWN_OPTION_PRESSED)
        DROPDOWN_SEPARATOR_COLOR = theme.get('DROPDOWN_SEPARATOR_COLOR', DROPDOWN_SEPARATOR_COLOR)
    except Exception:
        pass
    # card-specific values (optional)
    try:
        global CARD_BG, CARD_BORDER, CARD_SHADOW, SUIT_COLORS
        CARD_BG = theme.get('CARD_BG', CARD_BG)
        CARD_BORDER = theme.get('CARD_BORDER', CARD_BORDER)
        CARD_SHADOW = theme.get('CARD_SHADOW', CARD_SHADOW)
        SUIT_COLORS = theme.get('SUIT_COLORS', SUIT_COLORS)
    except Exception:
        pass
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
        # Do not override the built-in 'Roboto' registration — on Windows
        # overriding the default font can interfere with IME/composition input
        # behavior. Apps can still opt into `FONT_NAME='AppFont'` for labels.
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
# Also look for bundled FontAwesome in project assets (useful for APK builds)
# Try using resource_find first (works in APK), then fall back to direct paths
try:
    from kivy.resources import resource_find
    _asset_fa_candidates = [
        'assets/fonts/fontawesome-webfont.ttf',
        'assets/fonts/FontAwesome.otf',
        'assets/fonts/fa-solid-900.ttf',
    ]
    for _rel_path in _asset_fa_candidates:
        try:
            _fp = resource_find(_rel_path)
            if _fp and os.path.exists(_fp):
                try:
                    LabelBase.register(name='FA', fn_regular=_fp)
                    FA_FONT = 'FA'
                    break
                except Exception:
                    pass
        except Exception:
            pass
except Exception:
    pass

# Fallback: try direct paths relative to this file
if not FA_FONT:
    _local_fa_candidates = [
        os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'fontawesome-webfont.ttf'),
        os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'FontAwesome.otf'),
        os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'fa-solid-900.ttf'),
    ]
    for _fp in _local_fa_candidates:
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
        # Avoid injecting into TextInput: forcing a font on TextInput can
        # interfere with system IME/input methods (especially for CJK input).
        # We'll limit injection to Label only and let TextInput widgets be
        # styled via the widgets module's theming hooks.
        classes = [Label]

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
