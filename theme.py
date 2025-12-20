import os
from kivy.event import EventDispatcher
from kivy.properties import ColorProperty, NumericProperty, StringProperty, DictProperty, ListProperty
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.metrics import sp, dp
from utils.logger import logger

# Constants for default values (keeping some for fallback)
DEFAULT_SMALL_FONT = sp(12)
DEFAULT_ROW_HEIGHT = dp(48)
DEFAULT_BTN_HEIGHT = dp(38)

class ThemeManager(EventDispatcher):
    # Mode
    current_theme = StringProperty('light')

    # Colors
    color_bg = ColorProperty((0.96, 0.96, 0.98, 1))
    panel_bg = ColorProperty((1.0, 1.0, 1.0, 1))
    header_bg = ColorProperty((0.95, 0.95, 0.97, 1))
    row_dark = ColorProperty((0.98, 0.98, 0.99, 1))
    row_light = ColorProperty((0.99, 0.99, 1.0, 1))
    total_bg = ColorProperty((0.95, 0.95, 0.97, 1))
    border_color = ColorProperty((0, 0, 0, 0.06))
    btn_bg = ColorProperty((0, 0, 0, 0.06))
    accent = ColorProperty((0.20, 0.20, 0.22, 1))
    text_color = ColorProperty((0.12, 0.12, 0.13, 1))
    
    # Dropdown
    dropdown_bg = ColorProperty((0.44, 0.44, 0.46, 1))
    dropdown_option_bg = ColorProperty((0.54, 0.54, 0.56, 1))
    dropdown_option_pressed = ColorProperty((0.40, 0.40, 0.42, 1))
    dropdown_separator_color = ColorProperty((0.36, 0.36, 0.38, 1))
    
    # Card
    card_bg = ColorProperty((1.0, 1.0, 1.0, 1))
    card_border = ColorProperty((0.9, 0.9, 0.92, 1))
    card_shadow = ColorProperty((0, 0, 0, 0.06))
    
    # Suits (Dictionary needs to be a DictProperty or just generic Object)
    suit_colors = DictProperty({
        '♠': (0.12, 0.12, 0.13, 1), 
        '♣': (0.12, 0.12, 0.13, 1), 
        '♥': (0.12, 0.12, 0.13, 1), 
        '♦': (0.12, 0.12, 0.13, 1)
    })

    # Metrics (Properties for reactivity if needed, though rarely changes)
    small_font = NumericProperty(DEFAULT_SMALL_FONT)
    input_font = NumericProperty(DEFAULT_SMALL_FONT)
    btn_height = NumericProperty(DEFAULT_BTN_HEIGHT)
    row_height = NumericProperty(DEFAULT_ROW_HEIGHT)
    
    # Fonts
    font_name = StringProperty('Roboto')
    fa_font = StringProperty('Roboto')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.themes = {
            'light': {
                'color_bg': (0.96, 0.96, 0.98, 1),
                'panel_bg': (1.00, 1.00, 1.00, 1),
                'header_bg': (0.95, 0.95, 0.97, 1),
                'row_dark': (0.98, 0.98, 0.99, 1),
                'row_light': (0.99, 0.99, 1.00, 1),
                'border_color': (0, 0, 0, 0.06),
                'btn_bg': (0, 0, 0, 0.06),
                'accent': (0.20, 0.20, 0.22, 1),
                'text_color': (0.12, 0.12, 0.13, 1),
                'card_bg': (1.0, 1.0, 1.0, 1),
                'card_border': (0.9, 0.9, 0.92, 1),
                'card_shadow': (0, 0, 0, 0.06),
                'suit_colors': {'♠': (0.12, 0.12, 0.13, 1), '♣': (0.12, 0.12, 0.13, 1), 
                                '♥': (0.12, 0.12, 0.13, 1), '♦': (0.12, 0.12, 0.13, 1)}
            },
            'dark': {
                'color_bg': (0.03, 0.03, 0.04, 1),
                'panel_bg': (0.04, 0.04, 0.05, 1),
                'header_bg': (0.12, 0.12, 0.14, 1),
                'row_dark': (0.05, 0.05, 0.06, 1),
                'row_light': (0.09, 0.09, 0.10, 1),
                'border_color': (0, 0, 0, 0.35),
                'btn_bg': (0, 0, 0, 0.12),
                'accent': (0.20, 0.20, 0.22, 1),
                'text_color': (1, 1, 1, 1),
                'card_bg': (0.06, 0.06, 0.07, 1),
                'card_border': (0.08, 0.08, 0.09, 1),
                'card_shadow': (0, 0, 0, 0.3),
                'suit_colors': {'♠': (0.12, 0.12, 0.13, 1), '♣': (0.12, 0.12, 0.13, 1), 
                                '♥': (0.12, 0.12, 0.13, 1), '♦': (0.12, 0.12, 0.13, 1)},
                'dropdown_bg': (0.44, 0.44, 0.46, 1),
                'dropdown_option_bg': (0.54, 0.54, 0.56, 1),
                'dropdown_option_pressed': (0.40, 0.40, 0.42, 1),
                'dropdown_separator_color': (0.36, 0.36, 0.38, 1),
            }
        }
        self.init_fonts()
        self.switch_theme(self.current_theme)

    def init_fonts(self):
        # Register AppFont
        candidate = os.path.join(os.path.dirname(__file__), "assets", "fonts", "NotoSansSC-Regular.ttf")
        if os.path.exists(candidate):
            try:
                LabelBase.register(name="AppFont", fn_regular=candidate)
                # On Windows, keep default for IME compatibility, else use AppFont
                import sys
                if not sys.platform.startswith('win'):
                    self.font_name = "AppFont"
                else:
                    self.font_name = "Roboto"
            except Exception as e:
                logger.error(f"Failed to register font: {e}")
        
        # Register FontAwesome
        fa_candidates = [
            os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'fontawesome-webfont.ttf'),
            os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'FontAwesome.otf'),
            'assets/fonts/fontawesome-webfont.ttf',
        ]
        
        # Try resource find
        try:
             from kivy.resources import resource_find
             for c in fa_candidates:
                 found = resource_find(c)
                 if found and os.path.exists(found):
                     try:
                         LabelBase.register(name='FA', fn_regular=found)
                         self.fa_font = 'FA'
                         logger.info(f"Loaded FontAwesome from {found}")
                         return
                     except Exception:
                         pass
        except Exception:
            pass

        # Try direct paths
        for fp in fa_candidates:
            if os.path.exists(fp):
                try:
                    LabelBase.register(name='FA', fn_regular=fp)
                    self.fa_font = 'FA'
                    return
                except Exception:
                    pass

    def switch_theme(self, name):
        if name not in self.themes:
            name = 'light'
        self.current_theme = name
        
        cfg = self.themes[name]
        for key, val in cfg.items():
            if hasattr(self, key):
                setattr(self, key, val)
        
        # Common secondary derivations
        self.total_bg = self.header_bg
        
        try:
            Window.clearcolor = self.color_bg
        except Exception:
            pass
        
        logger.info(f"Switched theme to {name}")

# Global Instance
theme_manager = ThemeManager()
