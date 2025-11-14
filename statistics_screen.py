from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp, sp
from theme import TEXT_COLOR


class StatisticsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical', padding=dp(8))
        try:
            lbl = Label(text='统计', halign='center', valign='middle')
            try:
                lbl.font_size = sp(18)
            except Exception:
                pass
            try:
                lbl.color = TEXT_COLOR
            except Exception:
                pass
            root.add_widget(lbl)
        except Exception:
            pass
        self.add_widget(root)
