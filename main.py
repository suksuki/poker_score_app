# -*- coding: utf-8 -*-
import json, os, datetime, shutil
from functools import partial

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import ListProperty, DictProperty
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.animation import Animation
# Try to import KivyMD icon button if available
HAS_KIVYMD = False
MDIconButton = None
try:
	from kivymd.uix.button import MDIconButton
	HAS_KIVYMD = True
except Exception:
	HAS_KIVYMD = False

# 数据文件与常量
DATA_FILE = "score_data.json"
DUN_VALUE = 30

# 全局样式（简化）
# 颜色调色板（Apple-like 亮色主题，用户选择了选项 1）
# 假定用户希望一个干净、浅色的界面：浅灰/近白背景，深色文字，蓝色强调色
COLOR_BG = (0.96, 0.96, 0.98, 1)       # 应用背景（近白，略带冷灰）
PANEL_BG = (1.00, 1.00, 1.00, 1)       # 面板/输入背景（纯白）
HEADER_BG = (0.95, 0.95, 0.97, 1)      # 表头背景（微微区分）
ROW_DARK = (0.98, 0.98, 0.99, 1)       # 行暗色（非常浅的灰）
ROW_LIGHT = (0.99, 0.99, 1.00, 1)      # 行浅色（略亮）
TOTAL_BG = HEADER_BG
BORDER_COLOR = (0, 0, 0, 0.06)         # 细边框，浅色背景下使用较低 alpha
BTN_BG = (0, 0, 0, 0.06)               # 按钮背景：浅色下使用半透明深色以产生对比
ACCENT = (0.00, 0.48, 1.00, 1)         # Apple 风格蓝色强调色

Window.clearcolor = COLOR_BG
TEXT_COLOR = (0.12, 0.12, 0.13, 1)     # 深色文本，便于浅背景下阅读
SMALL_FONT = sp(12)
INPUT_FONT = sp(12)
BTN_HEIGHT = dp(38)
ROW_HEIGHT = dp(48)

# 主题集合：亮/暗两套配色，切换时会把这些值写入模块全局变量
THEMES = {
	'light': {
		'COLOR_BG': (0.96, 0.96, 0.98, 1),
		'PANEL_BG': (1.00, 1.00, 1.00, 1),
		'HEADER_BG': (0.95, 0.95, 0.97, 1),
		'ROW_DARK': (0.98, 0.98, 0.99, 1),
		'ROW_LIGHT': (0.99, 0.99, 1.00, 1),
		'BORDER_COLOR': (0, 0, 0, 0.06),
		'BTN_BG': (0, 0, 0, 0.06),
		'ACCENT': (0.00, 0.48, 1.00, 1),
		'TEXT_COLOR': (0.12, 0.12, 0.13, 1),
	},
	'dark': {
		'COLOR_BG': (0.03, 0.03, 0.04, 1),
		# make panel closer to background in dark mode to reduce glare
		'PANEL_BG': (0.04, 0.04, 0.05, 1),
		'HEADER_BG': (0.12, 0.12, 0.14, 1),
		'ROW_DARK': (0.05, 0.05, 0.06, 1),
		'ROW_LIGHT': (0.09, 0.09, 0.10, 1),
		'BORDER_COLOR': (0, 0, 0, 0.35),
		# use a darker translucent button background in dark mode so white text contrasts
		'BTN_BG': (0, 0, 0, 0.12),
		'ACCENT': (0.10, 0.6, 0.95, 1),
		'TEXT_COLOR': (1, 1, 1, 1),
	}
}

# 当前主题名
CURRENT_THEME = 'light'

def apply_theme(name: str):
	"""将主题名应用到模块全局变量，并更新 Window 背景色。"""
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

# 立即应用初始主题
apply_theme(CURRENT_THEME)

# 尝试注册项目内的中文字体（放在最上层，确保在创建任何 widget 前注册）
FONT_NAME = None
_candidate = os.path.join(os.path.dirname(__file__), "assets", "fonts", "NotoSansSC-Regular.ttf")
if os.path.exists(_candidate):
	try:
		from kivy.core.text import LabelBase
		LabelBase.register(name="AppFont", fn_regular=_candidate)
		FONT_NAME = "AppFont"
	except Exception:
		# 若注册失败，回退为直接使用路径（Kivy 可能接受路径形式）
		FONT_NAME = _candidate

	# 尝试注册系统安装的 Font Awesome（若已通过 apt 安装 fonts-font-awesome）
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
# 取消复杂绘制：空实现，避免任何 canvas 操作导致的问题
def style_card(widget, *a, **kw):
	# no-op: 保留接口兼容性
	return widget

def style_button(btn: Button, *a, **kw):
	# 简单扁平按钮：确保透明背景与白色文字
	try:
			btn.background_normal = ''
			btn.background_down = ''
			# 使用当前主题按钮背景
			btn.background_color = BTN_BG
	except Exception:
		pass
	# 按钮文字统一使用主题的 TEXT_COLOR（暗色主题为白色）
	try:
		btn.color = TEXT_COLOR
	except Exception:
		btn.color = (1, 1, 1, 1) if CURRENT_THEME == 'dark' else TEXT_COLOR
	try:
		btn.padding = (dp(8), dp(6))
		btn.font_size = sp(13)
	except Exception:
		pass
	return btn

# 简易组件工厂
def L(text="", **kw):
	if FONT_NAME:
		kw.setdefault("font_name", FONT_NAME)
	kw.setdefault("font_size", SMALL_FONT)
	kw.setdefault("color", TEXT_COLOR)
	kw.setdefault("halign", "center")
	kw.setdefault("valign", "middle")
	lbl = Label(text=text, **kw)
	lbl.bind(size=lambda inst, *_: setattr(inst, "text_size", (inst.width, inst.height)))
	return lbl


class NameTouchable(Label):
	"""Label that detects long-press on the name area and notifies its owner row.
	It only serves as the trigger; the actual drag/reorder is managed by InputScreen.
	"""
	def __init__(self, row_container=None, **kw):
		# ensure label-like defaults so text is visible (font, size, color, alignment)
		try:
			if FONT_NAME:
				kw.setdefault('font_name', FONT_NAME)
		except Exception:
			pass
		kw.setdefault('font_size', SMALL_FONT)
		kw.setdefault('color', TEXT_COLOR)
		kw.setdefault('halign', 'left')
		kw.setdefault('valign', 'middle')
		super().__init__(**kw)
		self.row_container = row_container
		# ensure text layout updates with size
		try:
			self.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
		except Exception:
			pass
		self._longpress_ev = None
		self._touch = None
		self._start_pos = (0, 0)

	def on_touch_down(self, touch):
		if not self.collide_point(*touch.pos):
			return super().on_touch_down(touch)
		# begin long-press schedule
		try:
			self._touch = touch
			self._start_pos = (touch.x, touch.y)
			self._longpress_ev = Clock.schedule_once(self._do_longpress, 0.28)
			touch.grab(self)
		except Exception:
			pass
		return True

	def on_touch_move(self, touch):
		if touch is not self._touch:
			return super().on_touch_move(touch)
		# if moved too much before longpress, cancel
		try:
			if self._longpress_ev is not None:
				dx = abs(touch.x - self._start_pos[0])
				dy = abs(touch.y - self._start_pos[1])
				if dx > dp(8) or dy > dp(8):
					try:
						self._longpress_ev.cancel()
					except Exception:
						pass
					self._longpress_ev = None
					try:
						touch.ungrab(self)
					except Exception:
						pass
					return super().on_touch_move(touch)
		except Exception:
			pass
		return True

	def on_touch_up(self, touch):
		if touch is not self._touch:
			return super().on_touch_up(touch)
		try:
			if self._longpress_ev is not None:
				try:
					self._longpress_ev.cancel()
				except Exception:
					pass
				self._longpress_ev = None
			try:
				touch.ungrab(self)
			except Exception:
				pass
		except Exception:
			pass
		return True

	def _do_longpress(self, dt):
		try:
			# notify the InputScreen (walk up to find it)
			parent = self
			while parent is not None and not hasattr(parent, 'build_left_inputs'):
				parent = parent.parent
			if parent is not None and hasattr(parent, '_start_row_drag'):
				# pass the owning row container and the original touch
				parent._start_row_drag(self.row_container, self._touch)
		except Exception:
			pass


def H(text="", **kw):
	"""大号标题 Label（用于页眉等）。"""
	if FONT_NAME:
		kw.setdefault("font_name", FONT_NAME)
	kw.setdefault("font_size", sp(16))
	kw.setdefault("color", TEXT_COLOR)
	kw.setdefault("halign", "center")
	kw.setdefault("valign", "middle")
	lbl = Label(text=text, **kw)
	lbl.bind(size=lambda inst, *_: setattr(inst, "text_size", (inst.width, inst.height)))
	return lbl

def TI(**kw):
	if FONT_NAME:
		kw.setdefault("font_name", FONT_NAME)
	kw.setdefault("font_size", INPUT_FONT)
	kw.setdefault("multiline", False)
	kw.setdefault("background_normal", "")
	kw.setdefault("background_active", "")
	# 使用面板背景与主题前景色
	kw.setdefault("background_color", PANEL_BG)
	kw.setdefault("foreground_color", TEXT_COLOR)
	ti = TextInput(**kw)
	# 强制高度和简单 padding，避免文字被裁切
	try:
		ti.size_hint_y = None
		ti.height = dp(40)
		ti.padding = [dp(6), dp(8), dp(6), dp(8)]
	except Exception:
		pass
	return ti


def cell_bg(text, width, height, bg_color):
	"""返回一个带背景色的容器，内部含一个居中的 Label，用于表格单元格显示。
	使用 canvas.before 绘制矩形背景并绑定 pos/size。若绘制失败（某些平台），退回到无背景的普通控件。
	"""
	cont = BoxLayout(size_hint=(None, None), width=width, height=height)
	try:
		# 在 canvas.before 中绘制边框与背景，并保存 Color 指令引用以便运行时修改
		with cont.canvas.before:
			# outer border（使用主题 BORDER_COLOR）
			border_color_instr = Color(*BORDER_COLOR)
			rect_border = Rectangle(pos=cont.pos, size=cont.size)
			# inner background (inset by 1dp to create 1px border effect)
			bg_color_instr = Color(*bg_color)
			rect = Rectangle(pos=(cont.x + dp(1), cont.y + dp(1)), size=(max(0, cont.width - dp(2)), max(0, cont.height - dp(2))))
		# 保持矩形与容器同步，并把指令对象挂到 cont 上以便后续修改
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
		# 如果 canvas 不可用则忽略背景绘制
		cont._rect_border = None
		cont._rect = None
		cont._border_color_instr = None
		cont._bg_color_instr = None
		cont._bg_color = bg_color
		pass
	lbl = L(text=text, size_hint=(1, 1))
	cont.add_widget(lbl)
	return cont

def cell_bg_with_trophy(text, width, height, bg_color, rank=None):
	"""返回一个带背景色的容器，内部含一个居中的 Label 和可选的奖杯图标，用于表格单元格显示。
	rank: 1表示第一名（金色奖杯），'last'表示最后一名（灰色奖杯）
	"""
	cont = BoxLayout(size_hint=(None, None), width=width, height=height)
	try:
		# 在 canvas.before 中绘制边框与背景，并保存 Color 指令引用以便运行时修改
		with cont.canvas.before:
			# outer border（使用主题 BORDER_COLOR）
			border_color_instr = Color(*BORDER_COLOR)
			rect_border = Rectangle(pos=cont.pos, size=cont.size)
			# inner background (inset by 1dp to create 1px border effect)
			bg_color_instr = Color(*bg_color)
			rect = Rectangle(pos=(cont.x + dp(1), cont.y + dp(1)), size=(max(0, cont.width - dp(2)), max(0, cont.height - dp(2))))
		# 保持矩形与容器同步，并把指令对象挂到 cont 上以便后续修改
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
		# 如果 canvas 不可用则忽略背景绘制
		cont._rect_border = None
		cont._rect = None
		cont._border_color_instr = None
		cont._bg_color_instr = None
		cont._bg_color = bg_color
		pass

	# 创建内容容器
	content = BoxLayout(orientation='horizontal', size_hint=(1, 1))
	lbl = L(text=text, size_hint=(1, 1))
	content.add_widget(lbl)

	# 添加奖杯图标（如果需要）
	if rank == 1 or rank == 'last':
		try:
			from kivy.uix.image import Image
			icon_w = None
			# paths to search
			_gold = os.path.join(os.path.dirname(__file__), 'assets', 'icons', 'trophy_gold.png')
			_gray = os.path.join(os.path.dirname(__file__), 'assets', 'icons', 'trophy_gray.png')
			# Prefer Font Awesome glyph if available
			if FA_FONT:
				try:
					# FontAwesome trophy glyph (unicode U+F091)
					glyph = '\uf091'
					if rank == 1:
						icon_w = Label(text=glyph, font_name=FA_FONT, font_size=sp(14), size_hint=(None, 1), width=dp(20))
						try:
							icon_w.color = (1.0, 0.84, 0.0, 1)  # gold
						except Exception:
							pass
					elif rank == 'last':
						icon_w = Label(text=glyph, font_name=FA_FONT, font_size=sp(14), size_hint=(None, 1), width=dp(20))
						try:
							icon_w.color = (0.6, 0.6, 0.63, 1)
						except Exception:
							pass
				except Exception:
					icon_w = None
			else:
				if rank == 1:
					if os.path.exists(_gold):
						icon_w = Image(source=_gold, size_hint=(None, 1), width=dp(20))
					else:
						icon_w = L(text='🏆', size_hint=(None, 1), width=dp(20))
				elif rank == 'last':
					if os.path.exists(_gray):
						icon_w = Image(source=_gray, size_hint=(None, 1), width=dp(20))
					else:
						# gray trophy emoji fallback
						icon_w = L(text='🏆', size_hint=(None, 1), width=dp(20))
			# style fallback emoji color for last-place (make it gray)
			if isinstance(icon_w, Label) and rank == 'last':
				try:
					icon_w.color = (0.6, 0.6, 0.63, 1)
				except Exception:
					pass
			if icon_w is not None:
				content.add_widget(icon_w)
		except Exception:
			pass

	cont.add_widget(content)
	return cont

def BTN(text, **kw):
	kw.setdefault("size_hint_y", None)
	kw.setdefault("height", BTN_HEIGHT)
	# 确保按钮也使用项目内注册的中文字体
	if FONT_NAME:
		kw.setdefault("font_name", FONT_NAME)
		kw.setdefault("font_size", SMALL_FONT)
	btn = Button(text=text, **kw)
	style_button(btn)
	return btn

class IconButton(ButtonBehavior, Widget):
	"""不依赖字体的矢量图标按钮：在 canvas 绘制圆形背景与 +/- 标记。
	使用 symbol='plus' 或 'minus' 指定要绘制的标记。
	"""
	def __init__(self, symbol: str = 'plus', **kw):
		# Remove common font/text/bg kwargs that are valid for Buttons/Labels
		# but not for a bare Widget; passing them to super().__init__ causes
		# EventDispatcher to raise TypeError about invalid properties.
		for _k in ('font_size', 'font_name', 'text', 'markup',
				   'background_normal', 'background_down', 'background_color', 'color'):
			if _k in kw:
				kw.pop(_k, None)

		kw.setdefault('size_hint', (None, None))
		kw.setdefault('width', dp(36))
		kw.setdefault('height', dp(36))
		super().__init__(**kw)
		self.symbol = symbol
		# 背景与标记指令引用
		self._bg_color_instruction = None
		self._bg_ellipse = None
		self._mark_graphics = []  # generic list for Line/Shape instructions
		self._mark_color_instruction = None
		try:
			with self.canvas.before:
				self._bg_color_instruction = Color(*BTN_BG)
				# 画圆作为背景（当宽高不等时为椭圆）
				self._bg_ellipse = Ellipse(pos=self.pos, size=self.size)
			with self.canvas:
				# 使用显式颜色绘制图标，防止继承到浅色导致线条过浅
				self._mark_color_instruction = Color(*TEXT_COLOR)
				lw = dp(2.5)
				# We'll create one or more Line instructions and position them in _update_graphics
				# Create up to 3 placeholders (most icons need <=3 lines)
				for _ in range(3):
					self._mark_graphics.append(Line(points=[], width=lw))
		except Exception:
			self._bg_color_instruction = None
			self._bg_ellipse = None
			self._mark_graphics = []

		# 绑定位置与尺寸更新绘制
		self.bind(pos=self._update_graphics, size=self._update_graphics)

	def _update_graphics(self, *a):
		try:
			if self._bg_ellipse is not None:
				self._bg_ellipse.pos = self.pos
				self._bg_ellipse.size = self.size
			# draw different icon shapes depending on self.symbol
			cx = self.x + self.width / 2.0
			cy = self.y + self.height / 2.0
			w = self.width
			h = self.height
			pad = min(w, h) * 0.28
			sym = (self.symbol or '').lower()
			# Helper coordinates
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

			# clear by default
			for i in range(len(self._mark_graphics)):
				set_line(i, [])

			# support multiple possible names for same icon
			if sym in ('minus', '−', '➖', 'minus_sign', '−') or self.symbol in ('-', '－'):
				# horizontal line center
				set_line(0, [left, cy, right, cy])
			elif sym in ('plus', '+', '➕', '＋') or self.symbol in ('+',):
				set_line(0, [left, cy, right, cy])
				set_line(1, [cx, bottom, cx, top])
			elif sym in ('check', 'ok', 'tick', '✔', '✓'):
				# check mark: two segments
				x1 = self.x + w * 0.22
				y1 = self.y + h * 0.45
				x2 = self.x + w * 0.42
				y2 = self.y + h * 0.30
				x3 = self.x + w * 0.78
				y3 = self.y + h * 0.70
				set_line(0, [x1, y1, x2, y2, x3, y3])
			elif sym in ('x', 'cross', 'close', '✖', '×'):
				set_line(0, [left, bottom, right, top])
				set_line(1, [left, top, right, bottom])
			elif sym in ('play', 'triangle'):
				# triangle outline (play)
				x1 = self.x + w * 0.30
				y1 = self.y + h * 0.20
				x2 = self.x + w * 0.30
				y2 = self.y + h * 0.80
				x3 = self.x + w * 0.78
				y3 = self.y + h * 0.50
				set_line(0, [x1, y1, x2, y2, x3, y3, x1, y1])
			elif sym in ('trash', 'delete'):
				# trash can: lid and body
				bx1 = self.x + w * 0.28
				bx2 = self.x + w * 0.72
				by1 = self.y + h * 0.28
				by2 = self.y + h * 0.68
				# body rectangle
				set_line(0, [bx1, by1, bx2, by1, bx2, by2, bx1, by2, bx1, by1])
				# lid
				set_line(1, [self.x + w * 0.22, by2, self.x + w * 0.78, by2])
			elif sym in ('save', 'floppy'):
				# floppy-ish: outer square and inner notch
				sx1 = self.x + w * 0.22
				sx2 = self.x + w * 0.78
				sy1 = self.y + h * 0.22
				sy2 = self.y + h * 0.72
				set_line(0, [sx1, sy1, sx2, sy1, sx2, sy2, sx1, sy2, sx1, sy1])
				set_line(1, [sx1, sy2, sx1 + (sx2 - sx1) * 0.5, sy2 + h * 0.08])
			elif sym in ('import', 'in'):
				# down arrow into a box
				ax = cx
				ay1 = self.y + h * 0.72
				ay2 = self.y + h * 0.38
				set_line(0, [ax, ay1, ax, ay2])
				set_line(1, [ax - w * 0.12, ay2 + h * 0.12, ax, ay2, ax + w * 0.12, ay2 + h * 0.12])
			elif sym in ('export', 'out'):
				ax = cx
				ay1 = self.y + h * 0.28
				ay2 = self.y + h * 0.62
				set_line(0, [ax, ay1, ax, ay2])
				set_line(1, [ax - w * 0.12, ay2 - h * 0.12, ax, ay2, ax + w * 0.12, ay2 - h * 0.12])
			elif sym in ('wrench', 'tool', '扳手'):
				# simple wrench: diagonal handle + small claw at the tip
				hx1 = self.x + w * 0.15
				hy1 = self.y + h * 0.15
				hx2 = self.x + w * 0.70
				hy2 = self.y + h * 0.70
				set_line(0, [hx1, hy1, hx2, hy2])
				# claw at the handle end (V-like shape)
				cx1 = self.x + w * 0.60
				cy1 = self.y + h * 0.82
				cx2 = self.x + w * 0.82
				cy2 = self.y + h * 0.60
				cx3 = self.x + w * 0.90
				cy3 = self.y + h * 0.72
				set_line(1, [cx1, cy1, cx2, cy2, cx3, cy3])
			else:
				# default: if symbol is a one-character Unicode like '➕'/'➖', try plus/minus handling
				if self.symbol in ('➕', '+', '＋'):
					set_line(0, [left, cy, right, cy]); set_line(1, [cx, bottom, cx, top])
				elif self.symbol in ('➖', '-', '－'):
					set_line(0, [left, cy, right, cy])
				else:
					# unknown: draw a small dot to indicate presence
					set_line(0, [cx, cy, cx + 0.01, cy + 0.01])
		except Exception:
			pass

		# apply initial styling and react to disabled state changes
		try:
			if hasattr(self, 'restyle') and callable(getattr(self, 'restyle')):
				try:
					self.restyle()
				except Exception:
					pass
		except Exception:
			pass
		try:
			self.bind(disabled=lambda inst, val: getattr(inst, 'restyle', lambda: None)())
		except Exception:
			pass

	def on_press(self):
		try:
			if self._bg_color_instruction is not None:
				r, g, b, a = BTN_BG
				# 加深或亮化以示反馈
				self._bg_color_instruction.rgba = (r, g, b, max(0.06, a * 1.8))
		except Exception:
			pass

	def on_release(self):
		try:
			if self._bg_color_instruction is not None:
				self._bg_color_instruction.rgba = BTN_BG
		except Exception:
			pass


class IconTextButton(ButtonBehavior, BoxLayout):
	"""组合图标 + 文本的按钮。
	优先使用 KivyMD 的 MDIconButton（若已安装），否则使用项目内的 IconButton 绘制简洁图标。
	支持和普通 Button 相同的 on_press/on_release 事件绑定。
	可通过 icon 参数传入 KivyMD 图标名或本地 symbol 名称。
	"""
	def __init__(self, text: str = '', icon: str = None, **kwargs):
		# 支持接收常见 Button kwargs：size_hint_x, size_hint_y, height
		h = kwargs.pop('height', BTN_HEIGHT)
		size_hint_y = kwargs.pop('size_hint_y', None)
		super().__init__(orientation='horizontal', spacing=dp(8), padding=(dp(8), dp(6)), **kwargs)
		# store original text for safe markup toggling when updating selected state
		self._raw_text = text or ''
	# background rectangle to mimic Button look
		try:
			with self.canvas.before:
				self._bg_color_instr = Color(*BTN_BG)
				self._bg_rect = Rectangle(pos=self.pos, size=self.size)
			self.bind(pos=lambda inst, *_: setattr(self._bg_rect, 'pos', inst.pos),
					  size=lambda inst, *_: setattr(self._bg_rect, 'size', inst.size))
		except Exception:
			self._bg_color_instr = None
			self._bg_rect = None

		# creation log removed (was used for debugging label/texture issues)

		# icon widget (decorative, disabled so touches pass to outer ButtonBehavior)
		if icon:
			# map common KivyMD icon names to our internal simple symbols when KivyMD is not available
			def _map_icon(name: str):
				if not name:
					return None
				n = name.lower().replace('_', '-')
				# direct mappings
				mapping = {
					'content-save': 'save', 'save': 'save', 'file-download': 'save',
					'file-upload': 'import', 'import': 'import', 'export': 'export',
					'playlist-plus': 'plus', 'playlist_add': 'plus', 'plus': 'plus',
					'close': 'x', 'cancel': 'x', 'delete': 'trash', 'trash': 'trash',
					'check': 'check', 'check-circle': 'check', 'brightness-6': 'play',
					'settings': 'play', 'playlist-play': 'play', 'format-list-bulleted': 'plus'
				}
				if n in mapping:
					return mapping[n]
				# heuristics
				if 'save' in n or 'download' in n or 'file' in n:
					return 'save'
				if 'upload' in n or 'import' in n:
					return 'import'
				if 'export' in n or 'out' in n:
					return 'export'
				if 'trash' in n or 'delete' in n:
					return 'trash'
				if 'close' in n or 'cancel' in n or 'x' in n:
					return 'x'
				if 'plus' in n or 'add' in n:
					return 'plus'
				if 'minus' in n or 'remove' in n:
					return 'minus'
				if 'check' in n or 'done' in n:
					return 'check'
				if 'play' in n or 'triangle' in n:
					return 'play'
				return None

			mapped = _map_icon(icon)
			icon_w = None
			# Prefer Font Awesome glyphs when available (mapped to our simple symbols)
			try:
				if FA_FONT and mapped:
					glyph_map = {
						'save': '\uf0c7',   # floppy disk
						'import': '\uf093', # arrow down (approx)
						'export': '\uf093', # reuse arrow glyph
						'plus': '\uf067',
						'minus': '\uf068',
						'trash': '\uf1f8',
						'x': '\uf00d',
						'check': '\uf00c',
						'play': '\uf04b',
					}
					glyph = glyph_map.get(mapped)
					if glyph:
						icon_w = Label(text=glyph, font_name=FA_FONT, font_size=sp(16), size_hint=(None, None), size=(dp(28), dp(28)))
						try:
							icon_w.color = TEXT_COLOR
						except Exception:
							pass
			except Exception:
				icon_w = None

			if icon_w is None:
				if HAS_KIVYMD:
					try:
						icon_w = MDIconButton(icon=icon, user_font_size=sp(16), size_hint=(None, None), size=(dp(28), dp(28)))
						icon_w.disabled = True
					except Exception:
						icon_w = IconButton(mapped or (icon or '+'), width=dp(28), height=dp(28))
						try:
							icon_w.disabled = True
						except Exception:
							pass
				else:
					icon_w = IconButton(mapped or (icon or '+'), width=dp(28), height=dp(28))
					try:
						icon_w.disabled = True
					except Exception:
						pass
			self.add_widget(icon_w)

		# label part
		# ensure label takes remaining horizontal space and has correct text layout
		self._label = Label(text=self._raw_text, halign='left', valign='middle', size_hint_x=1)
		# allow simple markup (for bold when selected)
		try:
			self._label.markup = True
		except Exception:
			pass
		try:
			if FONT_NAME:
				self._label.font_name = FONT_NAME
			self._label.font_size = SMALL_FONT
			self._label.color = TEXT_COLOR
			# bind size -> text_size for proper halign/valign wrapping
			self._label.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
			# ensure initial text_size is set (some Kivy versions won't trigger bind immediately)
			try:
				self._label.text_size = (self._label.width, self._label.height)
			except Exception:
				pass
		except Exception:
			pass
		self.add_widget(self._label)

		# sizing
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
		"""Apply current theme colors to this IconTextButton instance."""
		try:
			# label color: white in dark theme for contrast, otherwise theme text color
			if getattr(self, 'disabled', False):
				# disabled visual: slightly faded but still visible
				lbl_color = (1, 1, 1, 0.8) if CURRENT_THEME == 'dark' else (0.45, 0.45, 0.45, 1)
			else:
				lbl_color = (1, 1, 1, 1) if CURRENT_THEME == 'dark' else TEXT_COLOR
			try:
				self._label.color = lbl_color
			except Exception:
				pass
			# ensure label has proper text layout and texture (fix cases where text_size not set)
			try:
				if hasattr(self, '_label'):
					if not getattr(self._label, 'text_size', None) or (isinstance(getattr(self._label, 'text_size', None), (list, tuple)) and None in getattr(self._label, 'text_size', (None, None))):
						try:
							self._label.text_size = (self._label.width, self._label.height)
						except Exception:
							pass
					try:
						# force texture update so texture_size becomes available immediately
						if hasattr(self._label, 'texture_update'):
							try:
								self._label.texture_update()
							except Exception:
								pass
					except Exception:
						pass
			except Exception:
				pass
			# background rect
			if getattr(self, '_bg_color_instr', None) is not None:
				try:
					self._bg_color_instr.rgba = BTN_BG
				except Exception:
					pass
			# icon mark color if underlying IconButton used
			for ch in getattr(self, 'children', []):
				if hasattr(ch, '_mark_color_instruction') and ch._mark_color_instruction is not None:
					try:
						ch._mark_color_instruction.rgba = ACCENT if CURRENT_THEME == 'dark' else TEXT_COLOR
					except Exception:
						pass
			# debug logging removed to reduce noisy console output
		except Exception:
			pass

# 存取
def load_data():
	if os.path.exists(DATA_FILE):
		try:
			with open(DATA_FILE, "r", encoding="utf-8") as f:
				return json.load(f)
		except Exception:
			pass
	return {"players": [], "rounds": []}

def save_data(data):
	with open(DATA_FILE, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)

def to_int(s, default=0):
	try:
		if isinstance(s, (int, float)):
			return int(s)
		s = (s or "").strip()
		if s == "":
			return default
		return int(s)
	except Exception:
		return default


# 辅助：备份与安全的 JSON 读写，集中处理以消除重复代码
def ensure_backup(file_path):
	"""如果 file_path 存在，复制为带时间戳的备份并返回备份路径，失败时返回 None。"""
	try:
		if os.path.exists(file_path):
			bak = file_path + ".bak_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
			shutil.copyfile(file_path, bak)
			return bak
	except Exception:
		pass
	return None


def safe_load_json(path):
	try:
		with open(path, "r", encoding="utf-8") as f:
			return json.load(f)
	except Exception:
		return {}


def safe_save_json(path, data):
	with open(path, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)

class InputScreen(Screen):
	players = ListProperty([])
	hand_inputs = DictProperty({})
	dun_inputs = DictProperty({})
	_basic_ok = False

	def __init__(self, **kw):
		super().__init__(**kw)
		root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
		# 顶部信息使用自适应高度的 Label，以便在手机上能自动换行并完整显示
		from kivy.uix.label import Label as _KLabel
		self.info = _KLabel(text="基础=手上分-100；顿=每顿30分；基础差额需为0", size_hint_y=None, halign='left', valign='middle')
		try:
			if FONT_NAME:
				self.info.font_name = FONT_NAME
		except Exception:
			pass
		try:
			self.info.font_size = sp(13)
		except Exception:
			pass
		try:
			self.info.color = TEXT_COLOR
		except Exception:
			pass
		# 当宽度变化时让 text_size 的宽度更新为控件宽度，从而启用换行；根据 texture_size 调整高度
		def _update_info_height(inst, *a):
			try:
				w = inst.width or (Window.width - dp(20))
				# 留出一些内边距用于视觉间隔
				inst.text_size = (max(0, w - dp(8)), None)
				h = (inst.texture_size[1] if getattr(inst, 'texture_size', None) else 0) + dp(12)
				inst.height = max(dp(36), h)
			except Exception:
				pass

		# 绑定宽度和纹理变化以实时调整高度
		try:
			self.info.bind(width=_update_info_height)
			self.info.bind(texture_size=_update_info_height)
		except Exception:
			pass
		# 安排短延迟以初始化高度
		try:
			Clock.schedule_once(lambda dt: _update_info_height(self.info), 0)
		except Exception:
			pass
		root.add_widget(self.info)

		self.inputs_sv = ScrollView(size_hint=(1, 0.8))
		self.inputs_box = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
		self.inputs_box.bind(minimum_height=self.inputs_box.setter("height"))
		self.inputs_sv.add_widget(self.inputs_box)

		# 创建一个背景的 panel，把所有录入相关的控件放到该 panel 中（便于在手机上突出显示）
		# 使用主题变量 PANEL_BG，确保暗色主题下不会出现纯白的刺眼面板
		panel = BoxLayout(orientation='vertical', size_hint=(1, 0.8), padding=dp(8))
		try:
			with panel.canvas.before:
				# 在暗色主题中略微加深面板颜色以提高与背景的对比，但仍保持统一主题色
				panel._panel_color_instr = Color(*PANEL_BG)
				panel._panel_rect = Rectangle(pos=panel.pos, size=panel.size)
			panel.bind(pos=lambda inst, *_: setattr(panel._panel_rect, 'pos', inst.pos),
					   size=lambda inst, *_: setattr(panel._panel_rect, 'size', inst.size))
		except Exception:
			# 如果 canvas 不可用则忽略背景绘制
			pass

		panel.add_widget(self.inputs_sv)
		root.add_widget(panel)

		ops = BoxLayout(size_hint_y=None, height=ROW_HEIGHT, spacing=dp(6))
		self.save_btn = IconTextButton(text="保存本局", icon='content-save', disabled=True)
		# ensure old binding style continues to work
		try:
			self.save_btn.bind(on_press=self.save_round)
		except Exception:
			pass
		try:
			# 使三个操作按钮在行内自适应宽度（平均分配可用空间）
			self.save_btn.size_hint_x = 1
		except Exception:
			pass
		ops.add_widget(self.save_btn)
		imp_btn = IconTextButton(text="导入 JSON", icon='file-upload')
		try:
			imp_btn.bind(on_press=lambda *_: self.import_json_dialog())
		except Exception:
			pass
		exp_btn = IconTextButton(text="导出 JSON", icon='file-download')
		try:
			exp_btn.bind(on_press=lambda *_: self.export_json_dialog())
		except Exception:
			pass
		# Defensive: ensure import/export buttons have enough width and visible labels
		try:
			# give them a fixed minimum width so label isn't compressed
			try:
				imp_btn.size_hint_x = 1
			except Exception:
				pass
			try:
				exp_btn.size_hint_x = 1
			except Exception:
				pass
			# force label color/opacity and initialize text_size/texture to avoid missing text
			try:
				if hasattr(imp_btn, '_label'):
					imp_btn._label.color = (1,1,1,1) if CURRENT_THEME == 'dark' else TEXT_COLOR
					imp_btn._label.opacity = 1.0
					try:
						imp_btn._label.text_size = (imp_btn._label.width or dp(80), imp_btn._label.height or dp(24))
					except Exception:
						pass
					try:
						if hasattr(imp_btn._label, 'texture_update'):
							imp_btn._label.texture_update()
					except Exception:
						pass
			except Exception:
				pass
			try:
				if hasattr(exp_btn, '_label'):
					exp_btn._label.color = (1,1,1,1) if CURRENT_THEME == 'dark' else TEXT_COLOR
					exp_btn._label.opacity = 1.0
					try:
						exp_btn._label.text_size = (exp_btn._label.width or dp(80), exp_btn._label.height or dp(24))
					except Exception:
						pass
					try:
						if hasattr(exp_btn._label, 'texture_update'):
							exp_btn._label.texture_update()
					except Exception:
						pass
			except Exception:
				pass
		except Exception:
			pass
		# keep references for later enforcement when screen becomes visible
		try:
			self.imp_btn = imp_btn
			self.exp_btn = exp_btn
		except Exception:
			pass
		ops.add_widget(imp_btn)
		ops.add_widget(exp_btn)
		# Ensure these IconTextButton instances have correct colors in current theme
		try:
			for b in (self.save_btn, imp_btn, exp_btn):
				try:
					if hasattr(b, 'restyle') and callable(b.restyle):
						b.restyle()
				except Exception:
					pass
				try:
					# Force label color to be clearly visible in dark theme (always white) and
					# ensure export/import labels are not accidentally hidden by later overrides.
					if hasattr(b, '_label'):
						if CURRENT_THEME == 'dark':
							# For dark theme make labels full white regardless of disabled (ensures visibility)
							b._label.color = (1, 1, 1, 1)
							b._label.opacity = 1.0
						else:
							b._label.color = TEXT_COLOR
							b._label.opacity = 1.0
				except Exception:
					pass
				try:
					# some Kivy versions use disabled_color property
					setattr(b, 'disabled_color', (1, 1, 1, 0.7) if CURRENT_THEME == 'dark' else (0.6, 0.6, 0.6, 1))
				except Exception:
					pass
		except Exception:
			pass
		# 查看积分页面
	# 已移除显式的“查看积分”按钮；保存后会自动跳转到积分页
		root.add_widget(ops)

		self.add_widget(root)

		# schedule a short delayed enforcement to ensure buttons' internal labels are visible
		try:
			from kivy.clock import Clock
			Clock.schedule_once(lambda dt: getattr(self, '_ensure_ops_labels', lambda: None)(), 0.12)
		except Exception:
			pass

		# Drag overlay layer (used to show a floating dragged row on top of the inputs)
		try:
			self._drag_layer = FloatLayout(size_hint=(1, 1))
			# put on top
			self.add_widget(self._drag_layer)
		except Exception:
			self._drag_layer = None
	def on_enter(self, *a):
		# when the Screen becomes visible, re-ensure labels/colors
		try:
			self._ensure_ops_labels()
		except Exception:
			pass
		# extra: schedule a short delayed enforcement for import/export labels (covers late overrides)
		try:
			from kivy.clock import Clock
			def _ensure_ops(dt):
				try:
					for name in ('imp_btn', 'exp_btn'):
						b = getattr(self, name, None)
						if b is None:
							continue
						try:
							if hasattr(b, '_label'):
								if CURRENT_THEME == 'dark':
									b._label.color = (1,1,1,1)
									b._label.opacity = 1.0
								else:
									b._label.color = TEXT_COLOR
									b._label.opacity = 1.0
								try:
									b._label.text_size = (b._label.width or b.width or dp(80), b._label.height or b.height or dp(24))
								except Exception:
									pass
								try:
									if hasattr(b._label, 'texture_update'):
										b._label.texture_update()
								except Exception:
									pass
						except Exception:
							pass
				except Exception:
					pass
			Clock.schedule_once(_ensure_ops, 0.06)
		except Exception:
			pass

	def _ensure_ops_labels(self):
		try:
			for b in (getattr(self, 'save_btn', None),):
				if b is None:
					continue
				try:
					if hasattr(b, '_label'):
						if CURRENT_THEME == 'dark':
							b._label.color = (1, 1, 1, 1)
							b._label.opacity = 1.0
						else:
							b._label.color = TEXT_COLOR
							b._label.opacity = 1.0
				except Exception:
					pass
			# find local imp/exp buttons by scanning ops children
			try:
				for child in getattr(self, 'children', []):
					# descend to find ops box
					try:
						for c in getattr(child, 'children', []):
							# search for our IconTextButton instances
							if hasattr(c, '_label'):
								try:
									if CURRENT_THEME == 'dark':
										c._label.color = (1, 1, 1, 1)
										c._label.opacity = 1.0
									else:
										c._label.color = TEXT_COLOR
										c._label.opacity = 1.0
								except Exception:
									pass
					except Exception:
						pass
			except Exception:
				pass
		except Exception:
			pass

	def set_players(self, players):
		self.players = players[:]
		self.build_left_inputs()

	def build_left_inputs(self):
		self.inputs_box.clear_widgets()
		self.hand_inputs.clear()
		self.dun_inputs.clear()

		hdr = BoxLayout(size_hint_y=None, height=ROW_HEIGHT)
		hdr.add_widget(L(text="玩家", size_hint_x=0.4))
		hdr.add_widget(L(text="手上分", size_hint_x=0.3))
		hdr.add_widget(L(text="顿", size_hint_x=0.3))
		self.inputs_box.add_widget(hdr)

		for idx, p in enumerate(self.players, start=1):
			# 外层容器用于提供行间距，使条状控件在视觉上独立
			container = BoxLayout(size_hint_y=None, height=ROW_HEIGHT + dp(8), padding=(dp(4), dp(4)))
			# 左侧序号：纯文本标签，宽度固定（去掉圆形背景）
			try:
				index_lbl = L(text=str(idx), size_hint_x=None)
				index_lbl.width = dp(36)
				index_lbl.halign = 'center'
				index_lbl.valign = 'middle'
				index_lbl.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
				try:
					index_lbl.color = (1, 1, 1, 1) if CURRENT_THEME == 'dark' else TEXT_COLOR
				except Exception:
					pass
			except Exception:
				index_lbl = L(text=str(idx), size_hint_x=None)
				index_lbl.width = dp(36)
			# left group: fixed-width box containing the index square and (optional) trophy icon
			try:
				left_group = BoxLayout(orientation='horizontal', size_hint_x=None, spacing=dp(6))
				# fixed width: index(36) + spacing(6) + trophy(24) + padding allowance(8)
				left_group.width = dp(36 + 6 + 24 + 8)
				# index square (pure text inside fixed box)
				index_box = BoxLayout(size_hint=(None, None), size=(dp(36), ROW_HEIGHT))
				with index_box.canvas.before:
					# subtle background matching PANEL_BG for consistency
					index_box._bg_instr = Color(*PANEL_BG)
					index_box._rect = Rectangle(pos=index_box.pos, size=index_box.size)
				index_box.bind(pos=lambda inst, *_: setattr(index_box._rect, 'pos', inst.pos))
				index_box.bind(size=lambda inst, *_: setattr(index_box._rect, 'size', inst.size))
				# index label centered
				index_lbl_box = L(text=str(idx), size_hint=(1, 1))
				index_lbl_box.halign = 'center'; index_lbl_box.valign = 'middle'
				index_lbl_box.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
				try:
					index_lbl_box.color = (1, 1, 1, 1) if CURRENT_THEME == 'dark' else TEXT_COLOR
				except Exception:
					pass
				index_box.add_widget(index_lbl_box)
				left_group.add_widget(index_box)
				# placeholder for trophy (keeps width consistent when no trophy)
				left_icon_placeholder = L(text='', size_hint_x=None)
				left_icon_placeholder.width = dp(24)
				left_group.add_widget(left_icon_placeholder)
			except Exception:
				# fallback to simple index label if anything fails
				left_group = None
				container.add_widget(index_lbl)

			# bar 是真正的“横条”控件，带有阴影与主背景矩形，提供微妙的立体感
			bar = BoxLayout(size_hint_y=None, height=ROW_HEIGHT, spacing=dp(6), padding=(dp(8), dp(6)))
			try:
				# Use theme-aware colors for the row background/shadow so dark mode remains readable.
				shadow_alpha = 0.08 if CURRENT_THEME == 'light' else 0.18
				with bar.canvas.before:
					# shadow（在背景下方，向下偏移以制造悬浮效果）
					bar._shadow_color_instr = Color(0, 0, 0, shadow_alpha)
					bar._shadow_rect = Rectangle(pos=(bar.x, bar.y - dp(3)), size=(bar.width, bar.height))
					# 主背景：使用主题提供的 ROW_LIGHT（亮主题为偏白，暗主题为深灰）
					bar._bg_color_instruction = Color(*ROW_LIGHT)
					bar._bg_rect = Rectangle(pos=bar.pos, size=bar.size)
				# 标记为行条以便在 theme 切换时能识别并更新颜色
				bar._is_row_bar = True
				# 绑定以保持矩形与控件同步
				bar.bind(pos=lambda inst, *_: setattr(getattr(inst, '_bg_rect', inst), 'pos', inst.pos))
				bar.bind(size=lambda inst, *_: setattr(getattr(inst, '_bg_rect', inst), 'size', inst.size))
				# shadow 更新
				bar.bind(pos=lambda inst, *_: setattr(getattr(inst, '_shadow_rect', inst), 'pos', (inst.x, inst.y - dp(3))))
				bar.bind(size=lambda inst, *_: setattr(getattr(inst, '_shadow_rect', inst), 'size', inst.size))
			except Exception:
				# 如果 canvas 不可用则忽略立体化绘制
				pass

			# 内容：玩家名、手上分、顿控制
			# 使用可触碰的名称触发区域（长按触发整行拖拽），但显示样式与原来一致
			name_lbl = NameTouchable(row_container=container, text=p, size_hint_x=0.4)
			bar.add_widget(name_lbl)
			# store mapping from container to player name for reorder
			container._player_name = p

			ti_hand = TI(text="100")
			ti_hand.size_hint_x = 0.3
			ti_hand.bind(text=lambda *_: self.update_delta())
			self.hand_inputs[p] = ti_hand
			bar.add_widget(ti_hand)

			ti_dun = TI(text="0")
			dun_container = BoxLayout(size_hint_x=0.45, spacing=dp(6))
			ti_dun.size_hint_x = 1
			ti_dun.bind(text=lambda *_: self.update_delta())
			self.dun_inputs[p] = ti_dun
			btn_dec = IconButton("➖", width=dp(36), height=dp(36))
			btn_dec.bind(on_press=partial(self._change_dun, p, -1))
			btn_inc = IconButton("➕", width=dp(36), height=dp(36))
			btn_inc.bind(on_press=partial(self._change_dun, p, 1))
			dun_container.add_widget(btn_dec)
			dun_container.add_widget(ti_dun)
			dun_container.add_widget(btn_inc)
			bar.add_widget(dun_container)

			# add left group then bar; bar should take remaining horizontal space
			try:
				if left_group is not None:
					container.add_widget(left_group)
			except Exception:
				container.add_widget(index_lbl)
			# make bar expand to fill remaining width
			try:
				bar.size_hint_x = 1
			except Exception:
				pass
			container.add_widget(bar)
			# 右侧：若为第一或最后一名，显示小奖杯图标（优先使用 assets 中的图片，否则回退到 emoji）
			try:
				from kivy.uix.image import Image
				icon_w = None
				# paths to search
				_gold = os.path.join(os.path.dirname(__file__), 'assets', 'icons', 'trophy_gold.png')
				_gray = os.path.join(os.path.dirname(__file__), 'assets', 'icons', 'trophy_gray.png')
				# Prefer Font Awesome glyph if available
				if FA_FONT:
					try:
						# FontAwesome trophy glyph (unicode U+F091)
						glyph = '\uf091'
						if idx == 1:
							icon_w = Label(text=glyph, font_name=FA_FONT, font_size=sp(18), size_hint_x=None, width=dp(24))
							try:
								icon_w.color = (1.0, 0.84, 0.0, 1)  # gold
							except Exception:
								pass
						elif idx == len(self.players):
							icon_w = Label(text=glyph, font_name=FA_FONT, font_size=sp(18), size_hint_x=None, width=dp(24))
							try:
								icon_w.color = (0.6, 0.6, 0.63, 1)
							except Exception:
								pass
					except Exception:
						icon_w = None
				else:
					if idx == 1:
						if os.path.exists(_gold):
							icon_w = Image(source=_gold, size_hint_x=None, width=dp(24))
						else:
							icon_w = L(text='🏆', size_hint_x=None, width=dp(24))
					elif idx == len(self.players):
						if os.path.exists(_gray):
							icon_w = Image(source=_gray, size_hint_x=None, width=dp(24))
						else:
							# gray trophy emoji fallback
							icon_w = L(text='🏆', size_hint_x=None, width=dp(24))
				# style fallback emoji color for last-place (make it gray)
				if isinstance(icon_w, Label) and idx == len(self.players):
					try:
						icon_w.color = (0.6, 0.6, 0.63, 1)
					except Exception:
						pass
				if icon_w is not None:
					# prefer inserting the trophy into left_group (to the right of the index box)
					try:
						if left_group is not None:
							try:
								# remove placeholder and add icon
								left_group.remove_widget(left_icon_placeholder)
							except Exception:
								pass
							left_group.add_widget(icon_w)
						else:
							# fallback: add to bar's right
							bar.add_widget(icon_w)
					except Exception:
						try:
							bar.add_widget(icon_w)
						except Exception:
							container.add_widget(icon_w)
			except Exception:
				pass
			self.inputs_box.add_widget(container)
		self.update_delta()

	def _change_dun(self, player, delta, *args):
		try:
			cur = to_int(self.dun_inputs[player].text, 0)
			cur = max(0, cur + int(delta))
			self.dun_inputs[player].text = str(cur)
			self.update_delta()
		except Exception:
			pass

	def update_delta(self):
		delta = sum(to_int(self.hand_inputs[p].text, 100) - 100 for p in self.players)
		self._basic_ok = (delta == 0)
		self.save_btn.disabled = not self._basic_ok


	# --- drag / reorder support ---

	def _start_row_drag(self, container, touch):
		"""Begin dragging the given row container. Called by NameTouchable after long-press."""
		try:
			if getattr(self, '_drag_layer', None) is None:
				return
			# ensure container is in inputs_box
			if container not in self.inputs_box.children:
				return
			# record original window pos
			wx, wy = container.to_window(container.x, container.y)
			orig_idx = self.inputs_box.children.index(container)
			# placeholder (visible spacer with subtle tint)
			from kivy.uix.boxlayout import BoxLayout as _Box
			ph = _Box(size_hint_y=None, height=container.height)
			try:
				with ph.canvas.before:
					Color(ACCENT[0], ACCENT[1], ACCENT[2], 0.10)
					ph._rect = Rectangle(pos=ph.pos, size=ph.size)
					ph.bind(pos=lambda inst, *_: setattr(ph._rect, 'pos', inst.pos))
					ph.bind(size=lambda inst, *_: setattr(ph._rect, 'size', inst.size))
			except Exception:
				pass
			# remove container and insert placeholder at same index
			self.inputs_box.remove_widget(container)
			self.inputs_box.add_widget(ph, index=orig_idx)
			# prepare floating container
			container.size_hint_y = None
			container.height = ph.height
			# make floating semi-transparent to indicate dragging
			try:
				container.opacity = 0.6
			except Exception:
				pass
			# add to drag layer
			self._drag_layer.add_widget(container)
			# convert window coord to drag_layer local
			local = self._drag_layer.to_widget(wx, wy, relative=False)
			container.pos = local
			# save drag info
			self._drag_info = {'container': container, 'placeholder': ph, 'orig_index': orig_idx}
			# grab touch so we receive move/up
			touch.grab(self)
			self._drag_touch = touch
		except Exception:
			pass

	def on_touch_move(self, touch):
		# intercept drag touch
		try:
			if getattr(self, '_drag_touch', None) is touch and getattr(self, '_drag_info', None):
				self._on_drag_move(touch)
		except Exception:
			pass
		return super().on_touch_move(touch)

	def _on_drag_move(self, touch):
		"""Update floating container position and move placeholder according to touch.y"""
		try:
			d = self._drag_info
			cont = d['container']
			ph = d['placeholder']
			# keep width aligned with inputs_box
			try:
				win_x, win_y = self.inputs_box.to_window(0, 0, relative=False)
				lx = self._drag_layer.to_widget(win_x, win_y, relative=False)[0]
				cont.width = self.inputs_box.width
				cont.x = lx
			except Exception:
				pass
			# position floating by touch (centered vertically at touch)
			try:
				local_x, local_y = self._drag_layer.to_widget(touch.x, touch.y, relative=False)
				cont.y = local_y - cont.height / 2.0
			except Exception:
				pass
			# record last touch y (window coords) for final placement
			try:
				self._last_drag_y = touch.y
			except Exception:
				self._last_drag_y = None
			# compute new placeholder position based on touch.y among row children
			try:
				# use visual top-to-bottom order when computing centers so we pick the correct
				# row to insert before. inputs_box.children is bottom-to-top, so reverse it.
				visual_children = list(reversed(self.inputs_box.children))
				centers = []
				for c in visual_children:
					# skip header row (height == ROW_HEIGHT) to avoid moving above header
					if abs(getattr(c, 'height', 0) - ROW_HEIGHT) < 1e-6:
						continue
					# include placeholder in comparisons so it can move relative to others
					try:
						wx, wy = c.to_window(c.x, c.y)
						centers.append((c, wy + c.height / 2.0))
					except Exception:
						centers.append((c, getattr(c, 'y', 0) + getattr(c, 'height', 0) / 2.0))
				# find first visual child whose center is below the touch (touch.y greater)
				new_before = None
				for c, cy in centers:
					if touch.y > cy:
						new_before = c
						break
				if new_before is None:
					# put at bottom (index 0)
					new_idx = 0
				else:
					# map back to inputs_box.children index
					new_idx = self.inputs_box.children.index(new_before)
				# move placeholder if index changed
				cur_idx = self.inputs_box.children.index(ph)
				if new_idx != cur_idx:
					# animate affected rows: capture previous window Y positions
					try:
						prev_pos = {}
						for w in self.inputs_box.children:
							if w is ph:
								continue
							try:
								wx, wy = w.to_window(w.x, w.y)
							except Exception:
								wy = getattr(w, 'y', 0)
							prev_pos[w] = wy
					except Exception:
						prev_pos = {}
					# perform placeholder move
					try:
						self.inputs_box.remove_widget(ph)
						self.inputs_box.add_widget(ph, index=new_idx)
					except Exception:
						pass
					# schedule an animation step on next frame to compute new positions and animate
					def _animate_placeholder(dt):
						# compute new positions and animate deltas
						try:
							from kivy.graphics import PushMatrix, PopMatrix, Translate
							new_pos = {}
							for w in list(self.inputs_box.children):
								if w is ph:
									continue
								if not hasattr(w, '_player_name'):
									continue
								try:
									wx, wy = w.to_window(w.x, w.y)
								except Exception:
									wy = getattr(w, 'y', 0)
								new_pos[w] = wy

							# determine affected widgets where position changed
							affected = [w for w in new_pos.keys() if w in prev_pos and abs((prev_pos.get(w,0) - new_pos.get(w,0))) > 1e-3]

							# apply a simple canvas Translate for visual movement and animate back to 0
							for w in affected:
								try:
									dy = prev_pos.get(w, 0) - new_pos.get(w, 0)
									# add transform instructions
									with w.canvas.before:
										w._pm = PushMatrix()
										w._translate = Translate(0, dy)
									with w.canvas.after:
										w._pop = PopMatrix()

									# animate translate.y -> 0
									try:
										anim = Animation(y=0, duration=0.12, t='out_quad')
										anim.start(w._translate)

										# cleanup after animation ends
										def _cleanup(dt, widget=w):
											try:
												if hasattr(widget, '_pm') and widget._pm in widget.canvas.before:
													widget.canvas.before.remove(widget._pm)
												if hasattr(widget, '_translate') and widget._translate in widget.canvas.before:
													widget.canvas.before.remove(widget._translate)
												if hasattr(widget, '_pop') and widget._pop in widget.canvas.after:
													widget.canvas.after.remove(widget._pop)
											except Exception:
												pass

										Clock.schedule_once(_cleanup, 0.14)
									except Exception:
										pass
								except Exception:
									pass
						except Exception:
							pass

					# end _animate_placeholder
					Clock.schedule_once(_animate_placeholder, 0)
				# end placeholder move handling
			except Exception:
				pass
		except Exception:
			pass

	def on_touch_up(self, touch):
		# finalize drag if this is our drag touch
		try:
			if getattr(self, '_drag_touch', None) is touch and getattr(self, '_drag_info', None):
				# finalize
				self._end_row_drag()
				try:
					touch.ungrab(self)
				except Exception:
					pass
				self._drag_touch = None
		except Exception:
			pass
		return super().on_touch_up(touch)

	def _end_row_drag(self):
		"""Finish dragging: insert container back at placeholder position and rebuild players order."""
		try:
			d = self._drag_info
			cont = d['container']
			ph = d['placeholder']
			# Rebuild players order without re-adding cont first to avoid duplication.
			try:
				entries = []
				# gather existing rows (these do not include the dragged container)
				for w in self.inputs_box.children:
					# skip placeholder and header
					if w is ph:
						continue
					if hasattr(w, '_player_name'):
						try:
							wx, wy = w.to_window(w.x, w.y)
							center = wy + w.height / 2.0
						except Exception:
							center = getattr(w, 'y', 0) + getattr(w, 'height', 0) / 2.0
						entries.append((w._player_name, center))
				# include the dragged row at the last known touch Y
				drag_name = getattr(cont, '_player_name', None)
				last_y = getattr(self, '_last_drag_y', None)
				if drag_name is not None:
					if last_y is None:
						# fallback: put at bottom
						entries.append((drag_name, -1e9))
					else:
						entries.append((drag_name, last_y))
				# sort by Y (descending => top to bottom)
				entries_sorted = sorted(entries, key=lambda e: e[1], reverse=True)
				new_players = [name for name, _ in entries_sorted]
				if new_players:
					# preserve current input values so they survive rebuild
					saved_vals = {}
					try:
						for p in list(self.hand_inputs.keys()):
							h = getattr(self.hand_inputs.get(p), 'text', None)
							d = getattr(self.dun_inputs.get(p), 'text', None)
							saved_vals[p] = (h, d)
					except Exception:
						pass
					# update players order
					self.players = new_players
					# cleanup: remove placeholder and dragged widget from overlay
					try:
						if ph.parent is self.inputs_box:
							self.inputs_box.remove_widget(ph)
					except Exception:
						pass
					try:
						# restore opacity before removing
						try:
							cont.opacity = 1.0
						except Exception:
							pass
						if cont.parent is self._drag_layer:
							self._drag_layer.remove_widget(cont)
					except Exception:
						pass
					# rebuild inputs to reflect new order
					self.build_left_inputs()
					# restore saved values where possible
					try:
						for p, (h, d) in saved_vals.items():
							if p in self.hand_inputs and h is not None:
								try:
									self.hand_inputs[p].text = h
								except Exception:
									pass
							if p in self.dun_inputs and d is not None:
								try:
									self.dun_inputs[p].text = d
								except Exception:
									pass
					except Exception:
						pass
			except Exception:
				pass
			# clear drag info
			self._drag_info = None
		except Exception:
			pass

	def save_round(self, *_):
		if not self._basic_ok:
			return
		players = self.players
		basics = {p: to_int(self.hand_inputs[p].text, 100) - 100 for p in players}
		duns_raw = {p: to_int(self.dun_inputs[p].text, 0) for p in players}
		n = len(players)
		dun_scores = {p: 0 for p in players}
		for p in players:
			gain = (n - 1) * duns_raw[p] * DUN_VALUE
			dun_scores[p] += gain
			for q in players:
				if q != p:
					dun_scores[q] -= duns_raw[p] * DUN_VALUE
		total = {p: basics[p] + dun_scores[p] for p in players}
		# 计算名次：
		# - ranks_by_order 使用当前 players 列表顺序（即拖拽后的顺序）作为名次（第一个为名次1）
		# - ranks_by_score 根据 total 分数从高到低计算名次（相同分数名次相同）
		ranks_by_order = {player: idx + 1 for idx, player in enumerate(players)}
		# 计算按分数排序的名次（保留原有按分数计算的逻辑）
		sorted_players = sorted(total.items(), key=lambda x: x[1], reverse=True)
		ranks_by_score = {}
		current_rank = 1
		for i, (player, score) in enumerate(sorted_players):
			if i > 0 and score < sorted_players[i-1][1]:
				current_rank = i + 1
			ranks_by_score[player] = current_rank
		# 兼容性：保留原来的 "ranks" 字段作为按拖拽顺序的名次
		ranks = ranks_by_order
		data = load_data()
		data.setdefault("players", players)
		data.setdefault("rounds", []).append({
			"breakdown": {"basic": basics, "dun": dun_scores, "duns_raw": duns_raw},
			"total": total,
			"ranks": ranks,  # 按拖拽顺序
			"ranks_by_score": ranks_by_score  # 按分数计算的名次
		})
		save_data(data)
		for p in players:
			self.dun_inputs[p].text = "0"
		# 刷新积分页面
		try:
			scr = self.manager.get_screen('score')
			scr.rebuild_board()
		except Exception:
			pass
		# 自动切换到积分页面以便查看刚保存的结果
		try:
			self.manager.current = 'score'
		except Exception:
			pass
		# 尝试高亮刚保存的那一局（若 ScoreScreen 提供该方法）
		try:
			scr = self.manager.get_screen('score')
			try:
				scr.highlight_last_round()
				# 并把 ScrollView 滚动到最右侧以显示新局（若存在）
				try:
					# 优先使用平滑滚动方法（若存在），否则回退为直接设置 scroll_x
					if hasattr(scr, 'smooth_scroll_to_last'):
						try:
							Clock.schedule_once(lambda dt: scr.smooth_scroll_to_last(), 0.06)
						except Exception:
							try:
								if hasattr(scr, 'board_sv') and getattr(scr, 'board_sv') is not None:
									scr.board_sv.scroll_x = 1.0
							except Exception:
								pass
					else:
						if hasattr(scr, 'board_sv') and getattr(scr, 'board_sv') is not None:
							scr.board_sv.scroll_x = 1.0
				except Exception:
					pass
			except Exception:
				pass
		except Exception:
			pass

	# 复用之前的导入/导出/合并逻辑（简化调用路径）
	def export_json_dialog(self):
		self._open_save_popup("导出 JSON", default_name=self._suggest_filename(".json"), on_save=self._export_json_to)

	def _suggest_filename(self, ext):
		now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		return f"poker_scores_{now}{ext}"

	def _open_save_popup(self, title, default_name, on_save):
		content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
		fc = FileChooserListView(path=os.getcwd(), filters=['*'], dirselect=True)
		name_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
		name_row.add_widget(L(text="文件名：", size_hint_x=None, width=dp(64)))
		name_input = TI(text=default_name)
		name_row.add_widget(name_input)
		btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
		popup = Popup(title=title, content=content, size_hint=(0.9, 0.9))
		btn_ok = IconTextButton(text="保存", icon='content-save')
		btn_cancel = IconTextButton(text="取消", icon='close')
		try:
			btn_ok.bind(on_press=lambda *_: self._do_save_file(popup, fc.path, name_input.text, on_save))
		except Exception:
			pass
		try:
			btn_cancel.bind(on_press=lambda *_: popup.dismiss())
		except Exception:
			pass
		content.add_widget(fc); content.add_widget(name_row); content.add_widget(btn_row)
		btn_row.add_widget(btn_ok); btn_row.add_widget(btn_cancel)
		popup.open()

	def _do_save_file(self, popup, folder, filename, on_save):
		folder = folder or os.getcwd()
		filename = (filename or "").strip()
		if not filename:
			return
		if on_save == self._export_json_to and not filename.lower().endswith(".json"):
			filename += ".json"
		full = os.path.join(folder, filename)
		try:
			on_save(full)
		finally:
			popup.dismiss()

	def _export_json_to(self, full_path):
		data = load_data()
		with open(full_path, "w", encoding="utf-8") as f:
			json.dump(data, f, ensure_ascii=False, indent=2)

	def import_json_dialog(self):
		content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
		fc = FileChooserListView(path=os.getcwd(), filters=['*.json'])
		btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
		popup = Popup(title="导入 JSON", content=content, size_hint=(0.9, 0.9))
		btn_import = IconTextButton(text="导入", icon='file-upload')
		btn_cancel = IconTextButton(text="取消", icon='close')
		try:
			btn_import.bind(on_press=lambda *_: self._confirm_import(fc.selection, popup))
		except Exception:
			pass
		try:
			btn_cancel.bind(on_press=lambda *_: popup.dismiss())
		except Exception:
			pass
		content.add_widget(fc)
		content.add_widget(btn_row)
		btn_row.add_widget(btn_import)
		btn_row.add_widget(btn_cancel)
		popup.open()

	def _import_json_from(self, selection, popup):
		if not selection:
			return
		full = selection[0]
		try:
			with open(full, 'r', encoding='utf-8') as f:
				data = json.load(f)
			if not isinstance(data, dict):
				raise ValueError("文件内容不是有效的 JSON 对象")
			try:
				ensure_backup(DATA_FILE)
			except Exception:
				pass
			safe_save_json(DATA_FILE, data)
			popup.dismiss()
			# 刷新界面
			try:
				self.set_players(data.get('players', []))
				scr = self.manager.get_screen('score')
				scr.rebuild_board()
			except Exception:
				pass
		except Exception as e:
			try:
				err_popup = Popup(title='导入失败', content=L(text=f'导入失败: {e}'), size_hint=(0.8, 0.3))
				err_popup.open()
			except Exception:
				pass

	def _merge_import(self, selection, popup):
		if not selection:
			return
		full = selection[0]
		try:
			with open(full, 'r', encoding='utf-8') as f:
				imp = json.load(f)
			if not isinstance(imp, dict):
				raise ValueError("导入文件不是有效的 JSON 对象")
			data = load_data()
			try:
				ensure_backup(DATA_FILE)
			except Exception:
				pass
			orig_players = data.get('players', [])[:]
			imp_players = imp.get('players', []) if isinstance(imp.get('players', []), list) else []
			merged_players = orig_players[:]
			for p in imp_players:
				if p not in merged_players:
					merged_players.append(p)
			data['players'] = merged_players
			data.setdefault('rounds', [])
			if isinstance(imp.get('rounds', []), list):
				data['rounds'].extend(imp.get('rounds', []))
			save_data(data)
			popup.dismiss()
			try:
				self.set_players(data.get('players', []))
				scr = self.manager.get_screen('score')
				scr.rebuild_board()
			except Exception:
				pass
		except Exception as e:
			try:
				err_popup = Popup(title='导入失败', content=L(text=f'导入失败: {e}'), size_hint=(0.8, 0.3))
				err_popup.open()
			except Exception:
				pass

	def _confirm_import(self, selection, popup):
		if not selection:
			return
		confirm_content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
		# 明确内容高度，防止在某些 Kivy 版本/主题下被压缩为 0 高度导致看不到控件
		try:
			confirm_content.size_hint_y = None
			# msg.height + btn_row.height + vertical paddings + spacing
			confirm_content.height = dp(64 + 44 + 16 + 8)
		except Exception:
			pass
		confirm_content.add_widget(L(text='导入将覆盖当前存档，确定要继续吗？'))
		btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
		btn_yes = IconTextButton(text='覆盖', icon='file-download')
		btn_merge = IconTextButton(text='合并', icon='playlist-plus')
		btn_no = IconTextButton(text='取消', icon='close')

		def _do_confirm_overwrite(*_):
			try:
				self._import_json_from(selection, popup)
			finally:
				confirm_popup.dismiss()

		def _do_confirm_merge(*_):
			try:
				self._merge_import(selection, popup)
			finally:
				confirm_popup.dismiss()

		try:
			btn_yes.bind(on_press=_do_confirm_overwrite)
		except Exception:
			pass
		try:
			btn_merge.bind(on_press=_do_confirm_merge)
		except Exception:
			pass
		try:
			btn_no.bind(on_press=lambda *_: confirm_popup.dismiss())
		except Exception:
			pass

		confirm_content.add_widget(btn_row)
		btn_row.add_widget(btn_yes)
		btn_row.add_widget(btn_merge)
		btn_row.add_widget(btn_no)
		confirm_popup = Popup(title='确认导入', content=confirm_content, size_hint=(0.8, 0.4))
		confirm_popup.open()


class ScoreScreen(Screen):
	"""仅显示积分表的屏幕（可横向滚动网格）。"""
	def __init__(self, **kw):
		super().__init__(**kw)
		self.board_sv = ScrollView(size_hint=(1, 1))
		self.board_box = GridLayout(cols=1, size_hint_y=None, spacing=dp(6))
		self.board_box.bind(minimum_height=self.board_box.setter("height"))
		self.board_sv.add_widget(self.board_box)
		self.add_widget(self.board_sv)
		# 保存每一局对应的 widget 列表（用于高亮/滚动）
		self._round_widgets = []
		self._last_round_widgets = None

	def rebuild_board(self):
		self.board_box.clear_widgets()
		data = load_data()
		players = data.get("players", [])
		rounds = data.get("rounds", [])
		if not players:
			return

		cols = len(players) + 1
		self.board_box.cols = cols
		first_w = dp(120)
		per_player_w = dp(100)
		total_w = first_w + per_player_w * len(players)
		self.board_box.size_hint_x = None
		self.board_box.width = total_w

		rows = max(1, len(rounds) + 2)
		self.board_box.size_hint_y = None
		self.board_box.height = ROW_HEIGHT * rows

		header_bg = HEADER_BG
		self.board_box.add_widget(cell_bg("局/玩家", first_w, ROW_HEIGHT, header_bg))
		for p in players:
			self.board_box.add_widget(cell_bg(p, per_player_w, ROW_HEIGHT, header_bg))

		for i, rd in enumerate(rounds, start=1):
			# 为该局收集创建的 widget 引用，便于后续高亮
			this_round_widgets = []
			totals = rd.get("total", {})
			ranks = rd.get("ranks", {})
			breakdown = rd.get("breakdown", {})
			basics = breakdown.get("basic", {}) if isinstance(breakdown.get("basic", {}), dict) else {}
			duns_raw = breakdown.get("duns_raw", {}) if isinstance(breakdown.get("duns_raw", {}), dict) else {}
			bg = ROW_DARK if (i % 2 == 1) else ROW_LIGHT
			# 显示局数和排名信息
			round_text = f"第{i}局"
			if ranks:
				# 找到第一名和第二名
				first_place = [p for p, r in ranks.items() if r == 1]
				second_place = [p for p, r in ranks.items() if r == 2]
				if first_place and second_place:
					round_text += f"\n冠军:{first_place[0]} 亚军:{second_place[0]}"
				elif first_place:
					round_text += f"\n冠军:{first_place[0]}"
			w = cell_bg(round_text, first_w, ROW_HEIGHT, bg)
			self.board_box.add_widget(w)
			this_round_widgets.append(w)
			# determine ranks mapping for this round: prefer explicit 'ranks', fallback to 'ranks_by_score'
			ranks_map = rd.get('ranks') or rd.get('ranks_by_score') or {}
			for idx, p in enumerate(players, start=1):
				t = totals.get(p, 0)
				b = basics.get(p, 0)
				d = duns_raw.get(p, 0)
				text = f"{t}\n基:{b:+}  顿:{d}"
				# show trophy based on saved ranks for this round (not just column position)
				try:
					player_rank = ranks_map.get(p)
				except Exception:
					player_rank = None
				if player_rank == 1:
					w2 = cell_bg_with_trophy(text, per_player_w, ROW_HEIGHT, bg, rank=1)
				elif player_rank == len(players):
					w2 = cell_bg_with_trophy(text, per_player_w, ROW_HEIGHT, bg, rank='last')
				else:
					w2 = cell_bg(text, per_player_w, ROW_HEIGHT, bg)
				self.board_box.add_widget(w2)
				this_round_widgets.append(w2)
			# 记录本局 widgets
			self._round_widgets.append(this_round_widgets)

		if rounds:
			total_bg = TOTAL_BG
			self.board_box.add_widget(cell_bg("合计", first_w, ROW_HEIGHT, total_bg))
			sum_total = {p: sum(r.get("total", {}).get(p, 0) for r in rounds) for p in players}
			sum_basic = {p: sum((r.get("breakdown", {}).get("basic", {}) or {}).get(p, 0) for r in rounds) for p in players}
			sum_duns_raw = {p: sum((r.get("breakdown", {}).get("duns_raw", {}) or {}).get(p, 0) for r in rounds) for p in players}
			for p in players:
				txt = f"基:{sum_basic.get(p,0):+}  顿:{sum_duns_raw.get(p,0)}\n总:{sum_total.get(p,0)}"
				self.board_box.add_widget(cell_bg(txt, per_player_w, ROW_HEIGHT, total_bg))
		# 更新最后一局引用
		try:
			self._last_round_widgets = self._round_widgets[-1] if self._round_widgets else None
		except Exception:
			self._last_round_widgets = None

	def highlight_last_round(self, duration=2.0):
		"""短暂高亮最后一局的单元格（改变单元格背景色），随后恢复。
		优先修改 cell_bg 创建时保存在容器上的 _bg_color_instr；如果不存在则回退到修改内部 Label 的 color。
		"""
		widgets = getattr(self, '_last_round_widgets', None)


		if not widgets:
			return
		saved_bg = []
		saved_label = []
		# highlight tint: 使用强调色并降低 alpha，作为背景高亮覆盖
		try:
			tint = (ACCENT[0], ACCENT[1], ACCENT[2], 0.18)
		except Exception:
			tint = ACCENT

		for cont in widgets:
			try:
				if hasattr(cont, '_bg_color_instr') and cont._bg_color_instr is not None:
					# 保存原始 rgba，应用高亮 tint
					try:
						orig = tuple(getattr(cont._bg_color_instr, 'rgba', cont._bg_color or (1,1,1,1)))
					except Exception:
						orig = tuple(getattr(cont, '_bg_color', (1,1,1,1)))
					saved_bg.append((cont, orig))
					try:
						cont._bg_color_instr.rgba = tint
					except Exception:
						# fallback: try setting stored bg attr
						try:
							cont._bg_color = tint
						except Exception:
							pass
				else:
					# 回退：修改内部 Label 的文字颜色
					for ch in getattr(cont, 'children', []):
						if hasattr(ch, 'color'):
							saved_label.append((ch, ch.color))
							try:
								ch.color = ACCENT
							except Exception:
								pass
			except Exception:
				pass

		def _restore(dt):
			for cont, orig in saved_bg:
				try:
					if hasattr(cont, '_bg_color_instr') and cont._bg_color_instr is not None:
						cont._bg_color_instr.rgba = orig
					else:
						try:
							cont._bg_color = orig
						except Exception:
							pass
				except Exception:
					pass
			for ch, col in saved_label:
				try:
					ch.color = col
				except Exception:
					pass

		Clock.schedule_once(_restore, duration)


class StatisticsScreen(Screen):
	"""统计页面（目前为空白，占位用）。"""
	def __init__(self, **kw):
		super().__init__(**kw)
		# 暂时一个空白容器，可后续加入统计视图
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

	def smooth_scroll_to_last(self, duration=0.32):
		"""平滑滚动到最右（显示最后一局）。使用 Animation 动画 ScrollView.scroll_x。
		如果不存在 board_sv，静默返回。
		"""
		try:
			sv = getattr(self, 'board_sv', None)
			if sv is None:
				return
			# 动画到 scroll_x=1.0
			try:
				anim = Animation(scroll_x=1.0, duration=duration, t='out_quad')
				anim.start(sv)
			except Exception:
				# 回退到直接设置
				try:
					sv.scroll_x = 1.0
				except Exception:
					pass
		except Exception:
			pass


class SetupScreen(Screen):
	players = ListProperty([])

	def __init__(self, **kw):
		super().__init__(**kw)
		scroll = ScrollView(size_hint=(1, 1))
		content = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8), size_hint_y=None)
		content.bind(minimum_height=content.setter("height"))
		scroll.add_widget(content)
		self.add_widget(scroll)

		content.add_widget(H(text="玩家设置", size_hint_y=None, height=dp(40)))
		# 人数控制：使用 - / 数字 / + 的按钮组合，默认 4 人
		self.count = 4
		self._min_players = 1
		self._max_players = 16
		# 将“玩家数量”与“主题”放在同一行，左侧是人数控制，右侧是主题切换
		# 使用左右锚点布局：左侧左对齐，右侧右对齐
		combined = BoxLayout(size_hint_y=None, height=ROW_HEIGHT, spacing=dp(8))

		# 左侧：玩家数量（保持原有布局）
		left = BoxLayout(spacing=dp(6))
		left.add_widget(L(text="玩家数量", size_hint_x=0.4))
		ctrl = BoxLayout(size_hint_x=0.6, spacing=dp(6))
		btn_dec = IconButton('➖', width=dp(36), height=dp(36))
		btn_inc = IconButton('➕', width=dp(36), height=dp(36))
		btn_dec.bind(on_press=lambda *_: self._change_count(-1))
		btn_inc.bind(on_press=lambda *_: self._change_count(1))
		self.count_label = L(text=str(self.count), size_hint=(None, None), width=dp(48), height=dp(36), halign='center', valign='middle')
		self.count_label.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
		ctrl.add_widget(btn_dec)
		ctrl.add_widget(self.count_label)
		ctrl.add_widget(btn_inc)
		left.add_widget(ctrl)

		# 右侧：主题切换（单按钮）——显示当前主题
		right = BoxLayout(spacing=dp(6))
		right.add_widget(L(text="主题", size_hint_x=0.4))
		current_text = '亮色' if CURRENT_THEME == 'light' else '暗色'
		# 使用更语义化的图标 'palette' 表示颜色/主题
		self.theme_btn = IconTextButton(text=current_text, icon='wrench', size_hint_x=0.6)

		def _on_theme_toggle(*_):
			try:
				next_theme = 'dark' if CURRENT_THEME == 'light' else 'light'
				App.get_running_app().switch_theme(next_theme)
				# 切换后显示当前主题
				try:
					self.theme_btn.text = '亮色' if CURRENT_THEME == 'light' else '暗色'
				except Exception:
					pass
			except Exception:
				pass

		self.theme_btn.bind(on_press=_on_theme_toggle)
		right.add_widget(self.theme_btn)

		# 将 left 放入左锚，right 放入右锚，使两侧分别贴边
		try:
			from kivy.uix.anchorlayout import AnchorLayout
			left_anchor = AnchorLayout(anchor_x='left')
			right_anchor = AnchorLayout(anchor_x='right')
			left_anchor.add_widget(left)
			right_anchor.add_widget(right)
			combined.add_widget(left_anchor)
			combined.add_widget(right_anchor)
		except Exception:
			# 回退到简单的左右并列
			combined.add_widget(left)
			combined.add_widget(right)
		content.add_widget(combined)

		self.names_area = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
		self.names_area.bind(minimum_height=self.names_area.setter("height"))
		content.add_widget(self.names_area)

		# 行：重置 与 开始游戏 按钮
		btn_row = BoxLayout(size_hint_y=None, height=ROW_HEIGHT, spacing=dp(6))
		# 重新开始（危险操作）按钮文字为红色以示警示
		btn_reset = IconTextButton(text="重新开始", icon='delete')
		try:
			btn_reset.bind(on_press=self.confirm_reset)
			btn_reset._label.color = (1, 0, 0, 1)
		except Exception:
			pass
		# make reset and start share the row fairly (avoid one button becoming very wide)
		try:
			# make it a compact fixed-width button
			btn_reset.size_hint_x = None
			btn_reset.width = dp(140)
		except Exception:
			pass
		btn_row.add_widget(btn_reset)
		# 新增：开始游戏按钮，保存当前玩家设置并跳转到录入页
		start_btn = IconTextButton(text="开始游戏", icon='play')
		try:
			start_btn.bind(on_press=self.start_and_input)
		except Exception:
			pass
		try:
			# make start button compact and fixed width to avoid overly long button
			start_btn.size_hint_x = None
			start_btn.width = dp(140)
		except Exception:
			pass
		btn_row.add_widget(start_btn)
		content.add_widget(btn_row)

		self.refresh_loaded()

	def refresh_loaded(self):
		data = load_data()
		if data.get("players"):
			self.players = data["players"]
			# 更新 count 并同步标签
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

	def generate_name_inputs(self, *_args, prefill=None):
		"""根据当前 self.count 重建名字输入框，尽量保留已有名字。"""
		# 读取已有输入以便保留内容
		old = []
		try:
			for ti in reversed(self.names_area.children):
				if hasattr(ti, 'text'):
					old.append(ti.text)
		except Exception:
			old = []
		self.names_area.clear_widgets()
		n = max(self._min_players, min(self._max_players, int(getattr(self, 'count', 4))))
		for i in range(n):
			pre = None
			if prefill and i < len(prefill):
				pre = prefill[i]
			elif i < len(old):
				pre = old[i]
			ti = TI(text=(pre if pre is not None else f"玩家{i+1}"))
			ti.size_hint_y = None
			ti.height = dp(40)
			self.names_area.add_widget(ti)

	def _change_count(self, delta):
		"""调整玩家数量并重建名字输入框，尽量保留已有名字。"""
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
			# 重建名字输入（保留已有输入）
			self.generate_name_inputs()
		except Exception:
			pass

	def start_game(self, *_):
		names = []
		for ti in reversed(self.names_area.children):
			names.append((ti.text or "").strip() or f"玩家{len(names)+1}")
		# 去重序列化处理
		seen, uniq = {}, []
		for nm in names:
			seen[nm] = seen.get(nm, 0) + 1
			uniq.append(nm if seen[nm] == 1 else f"{nm}{seen[nm]}")
		data = load_data()
		data["players"] = uniq
		save_data(data)
		self.manager.get_screen("score").set_players(uniq)
		self.manager.current = "score"

	def start_and_input(self, *_):
		"""保存玩家设置并切换到录入页面（用于“开始游戏”按钮）。"""
		names = []
		for ti in reversed(self.names_area.children):
			names.append((ti.text or "").strip() or f"玩家{len(names)+1}")
		# 去重序列化处理
		seen, uniq = {}, []
		for nm in names:
			seen[nm] = seen.get(nm, 0) + 1
			uniq.append(nm if seen[nm] == 1 else f"{nm}{seen[nm]}")
		data = load_data()
		data["players"] = uniq
		save_data(data)
		try:
			self.manager.get_screen("input").set_players(uniq)
		except Exception:
			pass
		try:
			self.manager.current = "input"
		except Exception:
			pass

	def confirm_reset(self, *_):
		"""弹出确认对话框，确认后执行重置。"""
		# 改为提示：确认后清空所有分数（保留玩家名单）
		# 先构建内容（确保消息与按钮均已加入），再创建并打开 Popup
		confirm_content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
		# 为避免在某些 Kivy 版本/主题下内容被压缩，给 content 一个显式高度
		try:
			confirm_content.size_hint_y = None
			# msg.height (64) + btn_row.height (44) + paddings/spacing 大约
			confirm_content.height = dp(64 + 44 + 16 + 8)
		except Exception:
			pass

		# 显式设置消息容器：带不透明面板背景以确保文字可见
		try:
			msg_container = BoxLayout(size_hint_y=None, height=dp(64), padding=dp(8))
			# canvas 背景确保对比（即使 popup 半透明也能看到文字）
			try:
				with msg_container.canvas.before:
					Color(*PANEL_BG)
					_rect = Rectangle(pos=msg_container.pos, size=msg_container.size)
				# 绑定以保持背景矩形与容器同步
				msg_container.bind(pos=lambda inst, *_: setattr(_rect, 'pos', inst.pos),
								   size=lambda inst, *_: setattr(_rect, 'size', inst.size))
			except Exception:
				pass
			msg_lbl = Label(text='确认后将清空所有分数（保留玩家名单）。是否继续？', halign='left', valign='middle')
			try:
				if FONT_NAME:
					msg_lbl.font_name = FONT_NAME
				msg_lbl.font_size = sp(14)
				msg_lbl.color = TEXT_COLOR
				msg_lbl.size_hint_y = None
				msg_lbl.height = dp(64 - 16)
				msg_lbl.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
			except Exception:
				pass
			msg_container.add_widget(msg_lbl)
			confirm_content.add_widget(msg_container)
		except Exception:
			# fallback to simple label
			msg = L(text='确认后将清空所有分数（保留玩家名单）。是否继续？')
			try:
				msg.size_hint_y = None
				msg.height = dp(64)
				msg.color = TEXT_COLOR
			except Exception:
				pass
			confirm_content.add_widget(msg)

		btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
		btn_ok = IconTextButton('清空分数', icon='delete')
		# 强制设置确认按钮为红色文字并给出较为明显的浅红背景，确保在任何主题下可见
		try:
			# IconTextButton 使用内部 label 和 canvas 背景指令，直接修改其属性以保证可见性
			if hasattr(btn_ok, '_label'):
				btn_ok._label.color = (1, 0, 0, 1)
			if getattr(btn_ok, '_bg_color_instr', None) is not None:
				try:
					btn_ok._bg_color_instr.rgba = (1, 0.9, 0.9, 1)
				except Exception:
					pass
		except Exception:
			pass
		btn_cancel = IconTextButton('取消', icon='close')
		try:
			# 使用面板背景作为取消按钮底色，确保对比
			if hasattr(btn_cancel, '_label'):
				btn_cancel._label.color = TEXT_COLOR
			if getattr(btn_cancel, '_bg_color_instr', None) is not None:
				try:
					btn_cancel._bg_color_instr.rgba = PANEL_BG
				except Exception:
					pass
		except Exception:
			pass

		# 在执行清空之前先关闭确认弹窗，避免弹窗重叠导致透明/不可见问题
		def _do_clear_scores(*_):
			try:
				popup.dismiss()
			except Exception:
				pass
			try:
				self.clear_scores()
			except Exception:
				pass

		btn_ok.bind(on_press=_do_clear_scores)
		# 取消直接关闭确认弹窗
		btn_cancel.bind(on_press=lambda *_: popup.dismiss())
		btn_row.add_widget(btn_ok)
		btn_row.add_widget(btn_cancel)
		confirm_content.add_widget(btn_row)

		popup = Popup(title='确认清空分数', content=confirm_content, size_hint=(0.8, 0.4))
		popup.open()

	def clear_scores(self, *_):
		"""仅清空分数（rounds），保留 players 列表，并刷新界面。"""
		try:
			# 先备份旧存档
			try:
				ensure_backup(DATA_FILE)
			except Exception:
				pass
			data = load_data()
			if not isinstance(data, dict):
				data = {'players': [], 'rounds': []}
			# 只清空 rounds
			data['rounds'] = []
			save_data(data)
		except Exception:
			pass
		# 刷新积分页显示
		try:
			scr = self.manager.get_screen('score')
			try:
				scr.rebuild_board()
			except Exception:
				pass
		except Exception:
			pass
		# 显式构建提示内容并设置可见颜色/高度，避免白底白字或高度为 0 导致不可见
		try:
			# 显式的消息容器，带背景，避免字体/颜色问题导致不可见
			msg_container = BoxLayout(size_hint_y=None, height=dp(48), padding=dp(8))
			try:
				with msg_container.canvas.before:
					Color(*PANEL_BG)
					_r2 = Rectangle(pos=msg_container.pos, size=msg_container.size)
				msg_container.bind(pos=lambda inst, *_: setattr(_r2, 'pos', inst.pos),
								   size=lambda inst, *_: setattr(_r2, 'size', inst.size))
			except Exception:
				pass
			msg_lbl = Label(text='所有分数已清零，玩家名单已保留。', halign='center', valign='middle')
			try:
				if FONT_NAME:
					msg_lbl.font_name = FONT_NAME
				msg_lbl.font_size = sp(13)
				msg_lbl.color = TEXT_COLOR
				msg_lbl.size_hint_y = None
				msg_lbl.height = dp(32)
				msg_lbl.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
			except Exception:
				pass
			msg_container.add_widget(msg_lbl)
			# 把消息和按钮放在一个竖直布局中，确保用户可以点击“确定”关闭弹窗
			content_v = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
			content_v.add_widget(msg_container)
			btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
			btn_ok = IconTextButton('确定', icon='check')
			try:
				# 高亮为强调色并确保文字为白色，便于对比
				btn_ok.background_color = ACCENT
				btn_ok.color = (1, 1, 1, 1)
			except Exception:
				pass
			btn_row.add_widget(btn_ok)
			content_v.add_widget(btn_row)
			popup = Popup(title='已清空分数', content=content_v, size_hint=(0.6, 0.25), auto_dismiss=True)
			try:
				btn_ok.bind(on_press=lambda *_: popup.dismiss())
			except Exception:
				pass
			# 2 秒后自动关闭，防止用户无按钮可操作时卡住
			try:
				Clock.schedule_once(lambda dt: popup.dismiss(), 2.0)
			except Exception:
				pass
			popup.open()
		except Exception:
			pass

	def do_reset(self):
		"""执行重置：备份旧数据，写入空存档，重置界面。"""
		try:
			ensure_backup(DATA_FILE)
		except Exception:
			pass
		try:
			safe_save_json(DATA_FILE, {"players": [], "rounds": []})
		except Exception:
			# 最后手段：删除文件
			try:
				if os.path.exists(DATA_FILE):
					os.remove(DATA_FILE)
			except Exception:
				pass
		# 重置 UI
		try:
			self.count = 4
			try:
				self.count_label.text = str(self.count)
			except Exception:
				pass
			self.generate_name_inputs(prefill=None)
		except Exception:
			pass
		# 通知并重置记分页
		try:
			scr = self.manager.get_screen('score')
			scr.set_players([])
			scr.rebuild_board()
		except Exception:
			pass
		try:
			Popup(title='已重置', content=L(text='所有数据已清除并备份（若存在）。'), size_hint=(0.6, 0.3)).open()
		except Exception:
			pass


class PokerScoreApp(App):
	title = "扑克牌记分（简化版）"
	def build(self):
		Window.minimum_width, Window.minimum_height = 360, 640

		# 中央 ScreenManager（用于页面切换）
		sm = ScreenManager(transition=FadeTransition())
		sm.add_widget(SetupScreen(name="setup"))
		sm.add_widget(InputScreen(name="input"))
		sm.add_widget(ScoreScreen(name="score"))
		sm.add_widget(StatisticsScreen(name="statistics"))

		# 如果已有存档玩家，预先把玩家信息注入到录入与积分页面
		try:
			# 在启动时如果存档里保存了主题或上次页签，恢复它们
			meta = data.get('meta', {}) if isinstance(data, dict) else {}
			mt = meta.get('theme')
			if mt:
				try:
					apply_theme(mt)
				except Exception:
					pass
			last_tab = meta.get('last_tab')
			data = load_data()
			players = data.get('players', []) if isinstance(data.get('players', []), list) else []
			# 若配置中记录了上次页签则先设置 ScreenManager.current
			try:
				if last_tab and isinstance(last_tab, str) and last_tab in ('setup', 'input', 'score', 'statistics'):
					sm.current = last_tab
			except Exception:
				pass
			if players:
				try:
					sm.get_screen('input').set_players(players)
				except Exception:
					pass
				try:
					sm.get_screen('score').set_players(players)
					sm.get_screen('score').rebuild_board()
				except Exception:
					pass
		except Exception:
			pass

		# 底部 TabBar：始终可见，便于在页面间切换
		tab_bar = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(6), padding=dp(6))
		self._tab_setup = IconTextButton(text="设置", size_hint_x=0.25)
		try:
			self._tab_setup.bind(on_press=lambda *_: setattr(sm, 'current', 'setup'))
		except Exception:
			pass
		self._tab_input = IconTextButton(text="录入", size_hint_x=0.25)
		try:
			self._tab_input.bind(on_press=lambda *_: setattr(sm, 'current', 'input'))
		except Exception:
			pass
		self._tab_score = IconTextButton(text="积分", size_hint_x=0.25)
		self._tab_stats = IconTextButton(text="统计", size_hint_x=0.25)
		try:
			self._tab_score.bind(on_press=lambda *_: setattr(sm, 'current', 'score'))
		except Exception:
			pass
		try:
			self._tab_stats.bind(on_press=lambda *_: setattr(sm, 'current', 'statistics'))
		except Exception:
			pass
		tab_bar.add_widget(self._tab_setup)
		tab_bar.add_widget(self._tab_input)
		tab_bar.add_widget(self._tab_score)
		tab_bar.add_widget(self._tab_stats)

		# 根布局：将 TabBar 放在顶部，ScreenManager 在下
		root = BoxLayout(orientation='vertical')
		# 先添加 TabBar（位于顶部），再添加 ScreenManager（在其下方）
		root.add_widget(tab_bar)
		root.add_widget(sm)

		# 监听 ScreenManager 的 current 变化，以更新 Tab 的选中样式
		def _update_tabs(*_):
			cur = sm.current
			try:
				# 设置背景（选中为强调色，否则为按钮背景）
				self._tab_setup.background_color = ACCENT if cur == 'setup' else BTN_BG
				self._tab_input.background_color = ACCENT if cur == 'input' else BTN_BG
				self._tab_score.background_color = ACCENT if cur == 'score' else BTN_BG
				self._tab_stats.background_color = ACCENT if cur == 'statistics' else BTN_BG
			except Exception:
				pass

			# 文本颜色：选中时使用强调色，未选中时使用主题文本色
			for name, b in (('setup', self._tab_setup), ('input', self._tab_input), ('score', self._tab_score), ('statistics', self._tab_stats)):
				try:
					if hasattr(b, '_label'):
						if cur == name:
							# selected
							try:
								b.background_color = ACCENT
							except Exception:
								pass
							try:
								b._label.markup = True
							except Exception:
								pass
							try:
								b._label.font_size = sp(14)
							except Exception:
								pass
							try:
								raw = getattr(b, '_raw_text', None) or b._label.text
								b._label.text = f"[b]{raw}[/b]"
							except Exception:
								pass
							try:
								b._label.color = ACCENT if CURRENT_THEME == 'light' else (1, 1, 1, 1)
							except Exception:
								pass
						else:
							# unselected
							try:
								b.background_color = BTN_BG
							except Exception:
								pass
							try:
								b._label.color = TEXT_COLOR
								b._label.font_size = SMALL_FONT
							except Exception:
								pass
							try:
								raw = getattr(b, '_raw_text', None)
								if raw is not None:
									b._label.text = raw
							except Exception:
								pass
					else:
						try:
							if cur == name:
								b.background_color = ACCENT
							else:
								b.background_color = BTN_BG
							if hasattr(b, 'restyle') and callable(b.restyle):
								b.restyle()
						except Exception:
							pass
				except Exception:
					pass

			# 当切换到录入或积分页时，确保这些页面获取到最新的 players 数据并刷新显示
			try:
				if cur == 'input':
					data = load_data()
					players = data.get('players', []) if isinstance(data.get('players', []), list) else []
					if players:
						try:
							sm.get_screen('input').set_players(players)
						except Exception:
							pass
				if cur == 'score':
					data = load_data()
					players = data.get('players', []) if isinstance(data.get('players', []), list) else []
					try:
						scr = sm.get_screen('score')
						scr.set_players(players)
						scr.rebuild_board()
					except Exception:
						pass
			except Exception:
				pass
			# 持久化当前页签到存档 meta
			try:
				d = load_data()
				if not isinstance(d, dict):
					d = {'players': d.get('players', []), 'rounds': d.get('rounds', [])} if isinstance(d, dict) else {'players': [], 'rounds': []}
				meta = d.setdefault('meta', {}) if isinstance(d, dict) else {}
				meta['last_tab'] = cur
				save_data(d)
			except Exception:
				pass

		sm.bind(current=lambda *_: _update_tabs())
		# 初始选中
		_update_tabs()

		return root

	def switch_theme(self, name: str):
		"""切换主题：应用主题后尝试刷新已有控件的样式，并让页面重建以反映新配色。"""
		# 保存主题到存档 meta
		try:
			d = load_data()
			if not isinstance(d, dict):
				d = {'players': [], 'rounds': []}
			meta = d.setdefault('meta', {})
			meta['theme'] = name
			save_data(d)
		except Exception:
			pass

		try:
			# 先应用主题全局变量（但保持一个小动画过渡）
			old_bg = None
			try:
				old_bg = Window.clearcolor
			except Exception:
				old_bg = None
			apply_theme(name)
			# 淡入动画：轻微改变根视图不透明度以减少突变感
			try:
				if getattr(self, 'root', None) is not None:
					# 把 root 先降一点不透明度再回到 1
					try:
						self.root.opacity = 0.98
						anim = Animation(opacity=1.0, duration=0.14)
						anim.start(self.root)
					except Exception:
						pass
			except Exception:
				pass
		except Exception:
			pass

	# 重新样式化现有 widget（尽可能无破坏地应用颜色/按钮样式）
		def _restyle(w):
			try:
				# Labels: 更新文字颜色
				if hasattr(w, 'color'):
					try:
						w.color = TEXT_COLOR
					except Exception:
						pass
				# Buttons: 重新应用样式
				if isinstance(w, Button):
					try:
						style_button(w)
					except Exception:
						pass
				# IconButton: 更新其 canvas 背景色（如果存在的话）
				try:
					from kivy.uix.label import Label as _KivyLabel
					# 安全检查：若存在 _bg_color_instruction，则根据控件类型选择合适的颜色
					if hasattr(w, '_bg_color_instruction') and w._bg_color_instruction is not None:
						try:
							if getattr(w, '_is_row_bar', False):
								try:
									w._bg_color_instruction.rgba = ROW_LIGHT
								except Exception:
									pass
								try:
									if getattr(w, '_shadow_color_instr', None) is not None:
										w._shadow_color_instr.rgba = (0, 0, 0, 0.08 if CURRENT_THEME == 'light' else 0.18)
								except Exception:
									pass
							else:
								try:
									w._bg_color_instruction.rgba = BTN_BG
								except Exception:
									pass
						except Exception:
							pass
					# Panel background (e.g. InputScreen panel) 更新
					if hasattr(w, '_panel_color_instr') and getattr(w, '_panel_color_instr', None) is not None:
						try:
							w._panel_color_instr.rgba = PANEL_BG
						except Exception:
							pass
					# 同步更新 IconButton 上绘制 +/- 的颜色（如果存在）
					if hasattr(w, '_mark_color_instruction') and w._mark_color_instruction is not None:
						try:
								# 在暗色主题下使用强调色（蓝色），否则使用常规文本色
								w._mark_color_instruction.rgba = ACCENT if CURRENT_THEME == 'dark' else TEXT_COLOR
						except Exception:
							pass
				except Exception:
					pass
				# IconTextButton: if provided, call its restyle method
				try:
					if hasattr(w, 'restyle') and callable(getattr(w, 'restyle')):
						try:
							w.restyle()
						except Exception:
							pass
				except Exception:
					pass
				# TextInput: 更新背景与前景色
				if isinstance(w, TextInput):
					try:
						w.background_color = PANEL_BG
						w.foreground_color = TEXT_COLOR
					except Exception:
						pass
			except Exception:
				pass
			for c in getattr(w, 'children', []):
				_restyle(c)

		try:
			root = self.root
			if root:
				_restyle(root)
		except Exception:
			pass

		# 有些控件可能在 theme 切换后尚未完成布局或随后被别的逻辑覆盖颜色。
		# 为稳妥起见，安排一个短延迟的强制修复：遍历根视图，调用每个 IconTextButton.restyle()
		# 并确保其内部 label 在暗色主题下为白色，在亮色主题下为 TEXT_COLOR。
		try:
			def _enforce_icons(dt):
				try:
					def walk_and_fix(w):
						try:
							# If it's an IconTextButton, call restyle and force label color/opacity
							if hasattr(w, 'restyle') and callable(getattr(w, 'restyle')):
								try:
									w.restyle()
								except Exception:
									pass
								try:
									if hasattr(w, '_label'):
										if CURRENT_THEME == 'dark':
											w._label.color = (1, 1, 1, 1)
											w._label.opacity = 1.0
										else:
											w._label.color = TEXT_COLOR
											w._label.opacity = 1.0
								except Exception:
									pass
							# Also ensure plain Buttons get styled
							try:
								if isinstance(w, Button):
									try:
										style_button(w)
									except Exception:
										pass
							except Exception:
								pass
						except Exception:
							pass
						for c in getattr(w, 'children', []):
							walk_and_fix(c)
					root = getattr(self, 'root', None)
					if root:
						walk_and_fix(root)
						# extra: explicitly find known labels and force color (defensive)
						try:
							targets = {'保存本局', '导入 JSON', '导出 JSON'}
							def find_and_fix(w):
								try:
									if hasattr(w, '_label') and getattr(w, '_label', None) is not None:
										try:
											labtxt = getattr(w, '_label').text or ''
											if any(t in labtxt for t in targets):
												if CURRENT_THEME == 'dark':
													w._label.color = (1,1,1,1)
													w._label.opacity = 1.0
													try:
														w.color = (1,1,1,1)
													except Exception:
														pass
												else:
													w._label.color = TEXT_COLOR
													w._label.opacity = 1.0
													try:
														w.color = TEXT_COLOR
													except Exception:
														pass
										except Exception:
											pass
								except Exception:
									pass
								for ch in getattr(w, 'children', []):
									find_and_fix(ch)
							find_and_fix(root)
						except Exception:
							pass
				except Exception:
					pass
			from kivy.clock import Clock
			Clock.schedule_once(_enforce_icons, 0.08)
		except Exception:
			pass

		# 尝试找到 ScreenManager（root 是一个 BoxLayout，ScreenManager 在其 children 之中）
		sm = None
		try:
			for c in getattr(self.root, 'children', []):
				if isinstance(c, ScreenManager):
					sm = c
					break
		except Exception:
			sm = None

		# 针对各个 screen 做显式修正，确保暗色主题下录入页的文字颜色等被强制应用
		def _apply_theme_to_screen(screen):
			if not screen:
				return
			try:
				# 标题/信息类 Label
				try:
					if hasattr(screen, 'info'):
						screen.info.color = TEXT_COLOR
				except Exception:
					pass
				# 递归修复该屏幕内的控件颜色
				def _fix(w):
					try:
						if isinstance(w, Button):
							try:
								style_button(w)
								w.color = TEXT_COLOR
								try:
									setattr(w, 'disabled_color', TEXT_COLOR)
								except Exception:
									pass
							except Exception:
								pass
						if isinstance(w, TextInput):
							try:
								w.background_color = PANEL_BG
								w.foreground_color = TEXT_COLOR
							except Exception:
								pass
						# IconButton / canvas background: 如果存在 _bg_color_instruction，则按控件类型选择颜色
						if hasattr(w, '_bg_color_instruction') and w._bg_color_instruction is not None:
							try:
								if getattr(w, '_is_row_bar', False):
									try:
										w._bg_color_instruction.rgba = ROW_LIGHT
									except Exception:
										pass
									try:
										if getattr(w, '_shadow_color_instr', None) is not None:
											w._shadow_color_instr.rgba = (0, 0, 0, 0.08 if CURRENT_THEME == 'light' else 0.18)
									except Exception:
										pass
								else:
									try:
										w._bg_color_instruction.rgba = BTN_BG
									except Exception:
										pass
							except Exception:
								pass
						# Panel background (e.g. InputScreen panel) 更新
						if hasattr(w, '_panel_color_instr') and getattr(w, '_panel_color_instr', None) is not None:
							try:
								w._panel_color_instr.rgba = PANEL_BG
							except Exception:
								pass
						if hasattr(w, '_mark_color_instruction') and w._mark_color_instruction is not None:
							try:
								w._mark_color_instruction.rgba = ACCENT if CURRENT_THEME == 'dark' else TEXT_COLOR
							except Exception:
								pass
					except Exception:
						pass
					for ch in getattr(w, 'children', []):
						_fix(ch)
				_fix(screen)
			except Exception:
				pass

		if sm is not None:
			try:
				_apply_theme_to_screen(sm.get_screen('input'))
			except Exception:
				pass
			try:
				_apply_theme_to_screen(sm.get_screen('score'))
			except Exception:
				pass
			try:
				_apply_theme_to_screen(sm.get_screen('setup'))
			except Exception:
				pass

		# 触发页面刷新：重新构建左右输入/表格
		try:
			setup = self.root.get_screen('setup')
			try:
				# 更新主题按钮外观（单一切换按钮 theme_btn）
				if hasattr(setup, 'theme_btn'):
					try:
						# 当主题为暗色时把按钮高亮为强调色，确保文字为白色以保证对比；否则回到普通按钮背景
						if CURRENT_THEME == 'dark':
							setup.theme_btn.background_color = ACCENT
							try:
								setup.theme_btn.color = (1, 1, 1, 1)
							except Exception:
								pass
						else:
							setup.theme_btn.background_color = BTN_BG
							try:
								setup.theme_btn.color = TEXT_COLOR
							except Exception:
								pass
					except Exception:
						pass
				setup.refresh_loaded()
			except Exception:
				pass
		except Exception:
			pass

		try:
			score = self.root.get_screen('score')
			try:
				# 重新构建输入区/表格并显式修正部分控件颜色（确保暗色主题下可读）
				score.build_left_inputs()
				score.rebuild_board()
				try:
					# 顶部提示文字（info）在创建时可能未能被递归 restyle 覆盖，显式设置一次
					if hasattr(score, 'info'):
						# 顶部信息在暗色下使用强调色以提高可见性
						score.info.color = ACCENT if CURRENT_THEME == 'dark' else TEXT_COLOR
				except Exception:
					pass
				try:
					# 操作区按钮（保存/导入/导出/返回）确保使用 style_button，以获得正确背景与文字色
					for child in getattr(score, 'children', []):
						# 在页面布局中查找 ops 区（BoxLayout）并 style 其 direct children
						try:
							for c in getattr(child, 'children', []):
								if isinstance(c, Button):
									style_button(c)
						except Exception:
							pass
				except Exception:
					pass
			except Exception:
				pass
		except Exception:
			pass

		# 确保 InputScreen 的顶部提示与操作按钮在暗色主题下可见
		try:
			inp = self.root.get_screen('input')
			try:
				# 顶部信息使用主题文本色
				if hasattr(inp, 'info'):
					try:
						inp.info.color = TEXT_COLOR
					except Exception:
						pass
				# 递归修复 InputScreen 内的按钮/文本输入颜色与 IconButton 图标颜色
				def _fix_input_children(w):
					try:
						# Buttons
						if isinstance(w, Button):
							try:
								# 重新应用样式并确保禁用/启用状态下文字都是主题色
								style_button(w)
								w.color = TEXT_COLOR
								# 某些 Kivy 版本使用 disabled_color 控制禁用时文字颜色
								try:
									setattr(w, 'disabled_color', TEXT_COLOR)
								except Exception:
									pass
								# 额外强制：Button 可能包含内部 label/子 widget，用于渲染文字，强制它们的颜色也同步
								try:
									for sub in getattr(w, 'children', []):
										# 子 widget 可能是 Label 或其它复合控件
										if hasattr(sub, 'color'):
											try:
												sub.color = TEXT_COLOR
											except Exception:
												pass
										# 有些 Button 实现会把文字画在 canvas 上的指令，尝试强制刷新
										try:
											if hasattr(sub, 'texture'):
												# touch texture to nudge redraw
												_ = getattr(sub, 'texture')
										except Exception:
											pass
								except Exception:
									pass
							except Exception:
								pass
						# TextInputs
						if isinstance(w, TextInput):
							try:
								w.background_color = PANEL_BG
								w.foreground_color = TEXT_COLOR
							except Exception:
								pass
							# IconButton / canvas background: 如果存在 _bg_color_instruction，则按控件类型选择颜色
							if hasattr(w, '_bg_color_instruction') and w._bg_color_instruction is not None:
								try:
									if getattr(w, '_is_row_bar', False):
										try:
											w._bg_color_instruction.rgba = ROW_LIGHT
										except Exception:
											pass
										try:
											if getattr(w, '_shadow_color_instr', None) is not None:
												w._shadow_color_instr.rgba = (0, 0, 0, 0.08 if CURRENT_THEME == 'light' else 0.18)
										except Exception:
											pass
									else:
										try:
											w._bg_color_instruction.rgba = BTN_BG
										except Exception:
											pass
								except Exception:
									pass
						if hasattr(w, '_mark_color_instruction') and w._mark_color_instruction is not None:
							try:
								w._mark_color_instruction.rgba = ACCENT if CURRENT_THEME == 'dark' else TEXT_COLOR
							except Exception:
								pass
					except Exception:
						pass
					for c in getattr(w, 'children', []):
						_fix_input_children(c)

				_fix_input_children(inp)
			except Exception:
				pass
		except Exception:
			pass

if __name__ == "__main__":
	PokerScoreApp().run()
