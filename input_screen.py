from typing import Dict, List

from kivy.metrics import sp, dp
from theme import ROW_HEIGHT, FONT_NAME
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput

from widgets import L, ScoreInputItem, IconButton, IconTextButton, TrophyWidget, BTN
from storage import load_data, save_data, to_int, DUN_VALUE
from kivy.app import App
from datetime import datetime
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout as KBox
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.metrics import sp
from kivy.uix.button import Button
import os


class InputScreen(Screen):
	"""Minimal Input screen with a top notice and an empty middle area.

	Intentionally minimal: only a top notice is shown per your request. A few
	lightweight placeholders are kept so other parts of the app can call into
	this screen without crashing.
	"""

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		# State containers (kept for future use)
		self.players: List[str] = []
		self.hand_inputs: Dict[str, object] = {}
		self.dun_inputs: Dict[str, object] = {}
		# map player name -> row widget (for robust lookup)
		self.row_by_name: Dict[str, object] = {}

		# Root layout: no padding/spacing so content stacks exactly
		root = BoxLayout(orientation="vertical", spacing=0, padding=(0, 0, 0, 0))
		# make root height controllable so we can anchor it to the top
		root.size_hint_y = None

		# Top notice anchored to the very top of the screen area
		from kivy.uix.anchorlayout import AnchorLayout
		header_anchor = AnchorLayout(anchor_x='center', anchor_y='top', size_hint_y=None)
		self.notice = L(
			"每位玩家基础分100分，每顿30分，扣除100分后，总分应该为0",
			font_size=sp(18),
			size_hint_y=None,
			height=sp(44),
		)
		header_anchor.height = self.notice.height
		header_anchor.add_widget(self.notice)
		root.add_widget(header_anchor)

		# Middle: player rows live inside a ScrollView -> GridLayout
		# Let the ScrollView size be controlled programmatically so it hugs content
		self.middle = ScrollView(size_hint_y=None)
		self.rows_container = GridLayout(cols=1, spacing=8, size_hint_y=None)
		self.rows_container.bind(minimum_height=self.rows_container.setter('height'))
		self.middle.add_widget(self.rows_container)
		root.add_widget(self.middle)

		# Local save bar: the 保存本局 按钮 lives only on the Input screen (visible when this screen is active)
		try:
			self.save_bar = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(4), padding=(dp(4), dp(4)))
			_save_btn = IconTextButton(text='保存本局', icon='save')
			try:
				_save_btn.bind(on_press=self._on_save_round)
			except Exception:
				pass
			# left as single control (can add import/export here later if desired)
			self.save_bar.add_widget(_save_btn)
			root.add_widget(self.save_bar)
		except Exception:
			# if anything goes wrong, fall back to not showing a local save bar
			pass

		# Do not prefill player rows here — names come from SetupScreen via set_players()

		# place root inside an AnchorLayout so the whole input area is top-aligned
		from kivy.uix.anchorlayout import AnchorLayout
		outer = AnchorLayout(anchor_x='center', anchor_y='top')
		outer.add_widget(root)
		self._root_box = root
		self._header_anchor = header_anchor
		self.add_widget(outer)

	def set_players(self, players: List[str]):
		"""Store the players list and clear previous input maps."""
		# store and clear previous inputs
		self.players = list(players) if players else []
		self.hand_inputs.clear()
		self.dun_inputs.clear()
		self.row_by_name.clear()
		# If no players provided, ensure the input area is empty and only the
		# top notice is visible. Hide the local save bar to avoid confusing UI.
		if not self.players:
			# clear any existing rows
			try:
				self.rows_container.clear_widgets()
			except Exception:
				pass
			# hide save bar if present
			try:
				if getattr(self, 'save_bar', None) is not None and getattr(self.save_bar, 'parent', None) is not None:
					try:
						self._root_box.remove_widget(self.save_bar)
					except Exception:
						self.save_bar.opacity = 0
			except Exception:
				pass
			# adjust layout heights
			try:
				self._update_middle_height()
			except Exception:
				pass
			return
		# rebuild rows according to players length and pass the names so they are filled
		self._build_player_rows(len(self.players), names=self.players)
		# ensure save bar is visible when players exist
		try:
			if getattr(self, 'save_bar', None) is not None and getattr(self.save_bar, 'parent', None) is None:
				try:
					# add save bar back to root below rows
					self._root_box.add_widget(self.save_bar)
				except Exception:
					# fallback: ignore
					pass
		except Exception:
			pass
		# ensure the scrollview scrolls to bottom so the save button (under rows) is visible
		try:
			from kivy.clock import Clock
			Clock.schedule_once(lambda dt: setattr(self.middle, 'scroll_y', 0), 0.05)
		except Exception:
			pass


	def _find_row_for_widget(self, widget):
		"""Walk up from `widget` to find the direct child of rows_container.
		Returns the row BoxLayout or None.
		"""
		w = widget
		try:
			while w is not None and getattr(w, 'parent', None) is not None:
				p = w.parent
				if p is self.rows_container:
					return w
				w = p
		except Exception:
			return None
		return None

	def _on_name_long_press_global(self, inst, touch):
		"""Global handler bound to name labels; locate the enclosing row and start drag."""
		row = self._find_row_for_widget(inst)
		# fallback: if we couldn't find row via parent chain, try lookup by name text
		if row is None:
			try:
				name_text = getattr(inst, 'text', '').strip()
				if name_text:
					row = self.row_by_name.get(name_text)
			except Exception:
				row = None
		try:
			name = getattr(getattr(row, 'name_label', None), 'text', '<no-name>') if row is not None else '<no-row>'
			# verbose debug removed
		except Exception:
			pass
		if row is not None:
			self._start_simple_drag(row, touch)

	def _build_player_rows(self, n: int, names: List[str] = None):
		# clear
		self.rows_container.clear_widgets()
		if n <= 0:
			return
		for i in range(1, n + 1):
			# horizontal row: rank | trophy | input container
			row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(56), spacing=8)
			# rank (use styled label so color/font are correct)
			rank_lbl = L(text=str(i), font_size=sp(16), size_hint_x=None, width=dp(36))
			row.add_widget(rank_lbl)

			# trophy: use lightweight TrophyWidget (no gray background)
			if i == 1:
				w = TrophyWidget(rank=1, size=36)
			elif i == n:
				w = TrophyWidget(rank='last', size=36)
			else:
				w = TrophyWidget(rank=None, size=36)
			row.add_widget(w)

			# input container (ScoreInputItem) - name displayed inside the container at first position
			# determine name for this row
			name_text = ''
			if names and len(names) >= i:
				name_text = names[i-1]
			container = ScoreInputItem(name=name_text)
			# remember inputs so they can be queried/saved later. Use a stable key: the provided name if present,
			# otherwise fall back to an index-based key so maps remain usable.
			key = name_text if name_text else f"player{i}"
			try:
				self.hand_inputs[key] = container.base_input
			except Exception:
				pass
			try:
				self.dun_inputs[key] = container.dun_input
			except Exception:
				pass
			row.add_widget(container)

			# expose row attributes for later access
			row.rank_label = rank_lbl
			row.trophy_label = w
			row.name_label = container.name_label
			row.input_container = container
			# remember row by stable key (name or playerN)
			self.row_by_name[key] = row

			self.rows_container.add_widget(row)
		# Debug: show what was rendered and what input mappings we saved
		try:
			rendered = [getattr(r, 'name_label').text if getattr(r, 'name_label', None) is not None else '' for r in self.rows_container.children[::-1]]
			# verbose debug removed
		except Exception:
			pass
		try:
			# verbose debug removed
			pass
		except Exception:
			pass
		try:
			# verbose debug removed
			pass
		except Exception:
			pass

		# bind long-press on name to start a simple overlay drag (no reordering yet)
		try:
			# bind global handler to each name_label so drag can be started regardless of re-renders
			for row in list(self.rows_container.children)[::-1]:
				nl = getattr(row, 'name_label', None)
				if nl is not None and hasattr(nl, 'bind'):
					try:
						nl.bind(on_long_press=self._on_name_long_press_global)
					except Exception:
						pass
		except Exception:
			pass
		# after rendering rows, update the middle ScrollView height so it hugs
		# the content and sits directly under the notice. Schedule on next
		# frame to ensure sizes are computed.
		try:
			Clock.schedule_once(lambda dt: self._update_middle_height(), 0)
		except Exception:
			pass

	def get_current_inputs(self):
		"""Return a mapping player_key -> values dict from the current input rows.

		Each values dict is what ScoreInputItem.get_values() returns: {'base','dun','dun_score'}.
		The keys are the same stable keys used in hand_inputs/dun_inputs (player name if present,
		otherwise 'playerN').
		"""
		res = {}
		# iterate rows top->bottom for stable ordering
		for row in reversed(list(self.rows_container.children)):
			try:
				name_lbl = getattr(row, 'name_label', None)
				container = getattr(row, 'input_container', None)
				if container is None:
					continue
				key = (name_lbl.text.strip() if (name_lbl is not None and getattr(name_lbl, 'text', '').strip()) else None)
				if not key:
					# attempt to find a matching key in hand_inputs by comparing object identity
					for k, v in self.hand_inputs.items():
						if v is getattr(container, 'base_input', None):
							key = k
							break
					if not key:
						# fallback to index-based key
						key = f"player{len(res)+1}"
				res[key] = container.get_values()
			except Exception:
				pass
		return res

	def _update_middle_height(self):
		"""Adjust the ScrollView height to tightly wrap the rows container,
		with a maximum based on available window space so it doesn't cover the
		whole app when many players exist."""
		try:
			# content height is rows_container.height (bound to minimum_height)
			content_h = getattr(self.rows_container, 'height', 0)
			# available space: window minus notice and save_bar and some padding
			avail = Window.height - getattr(self.notice, 'height', dp(0)) - (getattr(getattr(self, 'save_bar', None), 'height', 0) if getattr(self, 'save_bar', None) is not None else dp(0)) - dp(80)
			# ensure a sensible minimum and cap
			h = min(content_h, max(dp(120), avail))
			# apply
			self.middle.height = max(h, dp(80))
			# update overall root box height so the anchored container stays top-aligned
			try:
				header_h = getattr(getattr(self, '_header_anchor', None), 'height', getattr(self.notice, 'height', dp(0)))
				save_h = getattr(getattr(self, 'save_bar', None), 'height', 0) if getattr(self, 'save_bar', None) is not None else 0
				if getattr(self, '_root_box', None) is not None:
					self._root_box.height = header_h + self.middle.height + save_h
			except Exception:
				pass
		except Exception:
			pass

	# helpers to render a given top->bottom order list into rows_container
	def _render_rows_from_order(self, top_down_list: List[object]):
		# verbose debug removed for render order
		# actually render
		try:
			self.rows_container.clear_widgets()
			# add in top->bottom order so children[::-1] yields the same top->bottom
			for w in top_down_list:
				self.rows_container.add_widget(w)
			# ensure each row's name_label is bound to our global handler (survives re-renders)
			for row in list(self.rows_container.children)[::-1]:
				nl = getattr(row, 'name_label', None)
				if nl is not None and hasattr(nl, 'bind'):
					try:
						nl.bind(on_long_press=self._on_name_long_press_global)
					except Exception:
						pass
		except Exception:
			pass
		# verbose post-render diagnostics removed
		# After rendering, enforce rank/trophy visuals to be position-based
		try:
			children_tb = list(self.rows_container.children)[::-1]
			count = len(children_tb)
			for idx, row in enumerate(children_tb):
				# update rank label text to reflect position (1-based)
				rank_lbl = getattr(row, 'rank_label', None)
				if rank_lbl is not None:
					try:
						rank_lbl.text = str(idx + 1)
					except Exception:
						pass
				# update trophy: top gets gold, bottom gets gray, others empty
				trophy_lbl = getattr(row, 'trophy_label', None)
				if trophy_lbl is not None:
					try:
						if idx == 0:
							# gold trophy
							trophy_lbl.text = '🏆'
							trophy_lbl.color = (1.0, 0.84, 0.0, 1)
						elif idx == count - 1:
							# gray trophy for last
							trophy_lbl.text = '🏆'
							trophy_lbl.color = (0.6, 0.6, 0.63, 1)
						else:
							trophy_lbl.text = ''
					except Exception:
						pass
		except Exception:
			pass

	# ---------------- Simple overlay drag (no reordering) ----------------

	def _start_simple_drag(self, row, touch):
		"""Start a simple drag: show a blue placeholder below this row, move
		the row as an overlay following the pointer, on release restore original position.
		This does NOT change ordering permanently.
		"""
		# verbose drag-start diagnostics removed
		# verbose drag-order inspection removed
		if getattr(self, '_simple_drag_active', False):
			return
		self._simple_drag_active = True
		self._simple_drag_row = row

		# capture top->bottom snapshot
		children_tb = list(self.rows_container.children)[::-1]
		try:
			orig_idx = children_tb.index(row)
		except Exception:
			orig_idx = 0
		self._simple_original_order = children_tb
		# also keep a version of the list with the dragged row removed (easier for swaps)
		try:
			self._simple_no_drag_order = [w for w in children_tb if w is not row]
		except Exception:
			self._simple_no_drag_order = [w for w in children_tb]

		# create placeholder to appear below the row (i.e., at orig_idx+1)
		ph = KBox(size_hint_y=None, height=getattr(row, 'height', dp(56)))
		try:
			with ph.canvas.before:
				Color(0.0, 0.45, 0.78, 0.18)
				rect = Rectangle(pos=ph.pos, size=ph.size)
				ph._ph_rect = rect
				ph.bind(pos=lambda inst, *_: setattr(ph._ph_rect, 'pos', inst.pos), size=lambda inst, *_: setattr(ph._ph_rect, 'size', inst.size))
		except Exception:
			pass
		# build new order with placeholder
		new_order = list(children_tb)
		# remove the dragged row from the list first (we'll render it as overlay)
		try:
			if row in new_order:
				new_order.remove(row)
		except Exception:
			pass
		# now insert placeholder where the row used to be: at orig_idx
		if orig_idx is None:
			insert_at = len(new_order)
		else:
			insert_at = min(len(new_order), orig_idx)
		# verbose placeholder insertion debug removed
		new_order.insert(insert_at, ph)
		self._simple_placeholder = ph
		# render with placeholder. The placeholder sits in the same slot as the
		# original row; the dragged row will be shown as an overlay above it.
		self._render_rows_from_order(new_order)

		# compute overlay position (use window coords of original row)
		try:
			win_x, win_y = row.to_window(row.x, row.y)
		except Exception:
			win_x, win_y = (0, 0)

		# remove the row from container and add to app root as overlay
		try:
			try:
				self.rows_container.remove_widget(row)
					# verbose post-remove diagnostics removed
			except Exception:
				pass
			row.size_hint = (None, None)
			row.width = self.rows_container.width
			row.height = getattr(row, 'height', dp(56))
			row.pos = (win_x, win_y)
					# verbose root children before add overlay removed
			# add overlay via app helper so main can manage overlays centrally
			try:
				app = App.get_running_app()
				app.add_overlay(row)
			except Exception:
				# fallback: add directly to root
				try:
					App.get_running_app().root.add_widget(row)
				except Exception:
					pass
					# verbose root children after add overlay removed
		except Exception:
			# abort and restore
			self._render_rows_from_order(self._simple_original_order)
			self._simple_drag_active = False
			return

		# follow pointer via polling
		# poll at up to 60 FPS instead of unbounded (0) to reduce CPU usage
		self._simple_drag_ev = Clock.schedule_interval(self._simple_drag_poll, 1.0 / 60.0)
		Window.bind(on_touch_up=self._simple_drag_release)

	def _simple_drag_poll(self, dt):
		"""Follow pointer: move the overlay row to follow the mouse Y.
		The placeholder remains at the original row's slot (under the overlay).
		"""
		try:
			mx, my = Window.mouse_pos
			row = getattr(self, '_simple_drag_row', None)
			if row is None:
				return
			row.pos = (row.pos[0], my - row.height / 2)
			# --- live-swap behaviour: detect which visible child (non-placeholder)
			# the pointer is over and swap it with the placeholder if needed.
			try:
				ph = getattr(self, '_simple_placeholder', None)
				if ph is None:
					return
				# current children top->bottom
				children_tb = list(self.rows_container.children)[::-1]
				# find current placeholder index
				try:
					ph_idx = children_tb.index(ph)
				except Exception:
					ph_idx = None
				# detect hovered index by checking mouse Y against child bounds
				hovered_idx = None
				for idx, child in enumerate(children_tb):
					# skip placeholder itself
					if child is ph:
						continue
					try:
						wx, wy = child.to_window(child.x, child.y)
						bottom = wy
						top = wy + getattr(child, 'height', 0)
						if my >= bottom and my <= top:
							hovered_idx = idx
							break
					except Exception:
						continue
				# if hovered and different from placeholder, swap in the render order
				if hovered_idx is not None and ph_idx is not None and hovered_idx != ph_idx:
					# build a new order (top->bottom) by swapping ph and hovered child
					new_order = list(children_tb)
					new_order[ph_idx], new_order[hovered_idx] = new_order[hovered_idx], new_order[ph_idx]
					# render only if different
					self._render_rows_from_order(new_order)
			except Exception:
				# be conservative: ignore swap errors during drag
				pass
		except Exception:
			pass

	def _simple_drag_release(self, win, touch):
		# stop poll and unbind
		try:
			if getattr(self, '_simple_drag_ev', None) is not None:
				self._simple_drag_ev.cancel()
		except Exception:
			pass
		try:
			Window.unbind(on_touch_up=self._simple_drag_release)
		except Exception:
			pass
		# remove overlay from app overlay layer (or fallback to root)
		try:
			app = App.get_running_app()
			try:
				app.remove_overlay(widget=self._simple_drag_row)
			except Exception:
				# fallback: direct removal
				try:
					app.root.remove_widget(self._simple_drag_row)
				except Exception:
					pass
		except Exception:
			pass
		# compute final order: replace placeholder with the dragged row (permanent move)
		try:
			# current rows inside rows_container (top->bottom)
			current = list(self.rows_container.children)[::-1]
			ph = getattr(self, '_simple_placeholder', None)
			if ph in current:
				idx = current.index(ph)
				new_order = list(current)
				# insert the dragged row into placeholder slot
				new_order[idx] = self._simple_drag_row
			else:
				# fallback: append to original order
				new_order = list(self._simple_original_order) if getattr(self, '_simple_original_order', None) is not None else list(current)
				# ensure dragged row is present once
				if self._simple_drag_row in new_order:
					# already present: leave as-is
					pass
				else:
					new_order.append(self._simple_drag_row)
			# restore reasonable sizing for the row before re-adding
			try:
				row = self._simple_drag_row
				row.size_hint = (1, None)
			except Exception:
				pass
			# render final order
			self._render_rows_from_order(new_order)
		except Exception:
			# as a last resort, restore original order
			try:
				self._render_rows_from_order(self._simple_original_order)
			except Exception:
				pass
		# clear state and visual
		try:
			if getattr(self._simple_drag_row, 'opacity', None) is not None:
				self._simple_drag_row.opacity = 1.0
		except Exception:
			pass
		self._simple_drag_active = False
		self._simple_drag_row = None
		self._simple_original_order = None
		self._simple_placeholder = None

	def _on_save_round(self, *_):
		"""Collect current inputs and persist a new round to storage."""
		try:
			data = load_data() or {}
		except Exception:
			data = {"players": [], "rounds": []}

		# ensure players list exists and is up-to-date
		try:
			players = data.get('players') or []
		except Exception:
			players = []

		# gather current rows top->bottom
		children_tb = list(self.rows_container.children)[::-1]
		# build ranks mapping and breakdowns
		ranks = {}
		basic = {}
		duns_raw = {}
		dun_vals = {}
		total = {}
		for idx, row in enumerate(children_tb):
			# determine key/name for this row
			name_lbl = getattr(row, 'name_label', None)
			key = None
			if name_lbl is not None:
				key = (getattr(name_lbl, 'text', '') or '').strip()
			if not key:
				# fallback to mapping by input object
				cont = getattr(row, 'input_container', None)
				if cont is not None:
					for k, v in self.hand_inputs.items():
						if v is getattr(cont, 'base_input', None):
							key = k
				if not key:
					key = f"player{idx+1}"
			# rank is 1-based
			ranks[key] = idx + 1
			# gather values from container
			cont = getattr(row, 'input_container', None)
			if cont is None:
				basic[key] = 0
				duns_raw[key] = 0
				dun_vals[key] = 0
				total[key] = 0
				continue
			vals = cont.get_values()
			b = to_int(vals.get('base', 0))
			dr = to_int(vals.get('dun', 0))
			ds = to_int(vals.get('dun_score', DUN_VALUE))
			basic[key] = b
			duns_raw[key] = dr
			dun_vals[key] = dr * ds
			# total: base + dun_value (simple sum)
			total[key] = basic[key] + dun_vals.get(key, 0)

		# build round dict similar to existing format (include timestamp)
		round_obj = {
			"breakdown": {
				"basic": basic,
				"dun": dun_vals,
				"duns_raw": duns_raw,
			},
			"total": total,
			"ranks": ranks,
			"date": datetime.now().isoformat(),
		}

		# append and save
		try:
			if 'rounds' not in data or data.get('rounds') is None:
				data['rounds'] = []
			data['rounds'].append(round_obj)
			# ensure players list exists and contains current known players (preserve order if available)
			try:
				if not data.get('players'):
					data['players'] = [getattr(r, 'text', '').strip() or f"player{i+1}" for i, r in enumerate(children_tb)]
			except Exception:
				pass
			save_data(data)
			try:
				# use unified overlay so the confirmation is always visible
				self._overlay_dialog('保存', '保存本局成功')
			except Exception:
				# as a last resort try safe popup (which itself will call overlay)
				try:
					self._safe_popup('保存', '保存本局成功')
				except Exception:
					pass
		except Exception as e:
			try:
				try:
					self._overlay_dialog('保存失败', str(e))
				except Exception:
					self._safe_popup('保存失败', str(e))
			except Exception:
				pass

	# Lightweight placeholders so global import/export buttons can call these.
	def import_json_dialog(self):
		"""Import JSON file: choose a .json file and either merge or replace current data.
		This uses an overlay-based file chooser to avoid platform popup/titlebar issues.
		"""
		app = App.get_running_app()
		root = getattr(app, 'root', None)
		if root is None:
			raise RuntimeError('App root not available')

		overlay = FloatLayout(size_hint=(1, 1))
		with overlay.canvas:
			Color(0, 0, 0, 0.45)
			_back = Rectangle(pos=overlay.pos, size=overlay.size)
		overlay.bind(pos=lambda inst, *_: setattr(_back, 'pos', inst.pos), size=lambda inst, *_: setattr(_back, 'size', inst.size))

		panel = BoxLayout(orientation='vertical', size_hint=(None, None), width=dp(640), height=dp(420), spacing=dp(8), padding=dp(12))
		with panel.canvas.before:
			Color(1,1,1,1)
			_panel_rect = Rectangle(pos=panel.pos, size=panel.size)
		panel.bind(pos=lambda inst, *_: setattr(_panel_rect, 'pos', inst.pos), size=lambda inst, *_: setattr(_panel_rect, 'size', inst.size))

		_label_kwargs = {'size_hint_y': None, 'height': dp(32), 'color': (0,0,0,1)}
		if FONT_NAME:
			_label_kwargs['font_name'] = FONT_NAME
		header = Label(text='导入 JSON', **_label_kwargs)
		chooser = FileChooserListView(path='.', filters=['*.json'], size_hint=(1,1))
		_info_kwargs = {'size_hint_y': None, 'height': dp(44), 'color': (0,0,0,1)}
		if FONT_NAME:
			_info_kwargs['font_name'] = FONT_NAME
		info = Label(text='选择一个 JSON 文件，然后选择导入方式：合并(追加回合) 或 覆盖(替换当前数据)。', **_info_kwargs)

		btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
		btn_kwargs = {'background_normal': '', 'background_color': (0.9,0.9,0.9,1), 'color': (0,0,0,1)}
		if FONT_NAME:
			btn_kwargs['font_name'] = FONT_NAME
		merge_btn = Button(text='合并导入', **btn_kwargs)
		replace_btn = Button(text='覆盖导入', **btn_kwargs)
		cancel_btn = Button(text='取消', background_normal='', background_color=(0.85,0.85,0.85,1), color=(0,0,0,1), **({'font_name': FONT_NAME} if FONT_NAME else {}))
		btn_row.add_widget(merge_btn)
		btn_row.add_widget(replace_btn)
		btn_row.add_widget(cancel_btn)

		panel.add_widget(header)
		panel.add_widget(chooser)
		panel.add_widget(info)
		panel.add_widget(btn_row)

		# add overlay via app helper so main can centrally manage overlay_layer
		try:
			app = App.get_running_app()
			app.add_overlay(overlay)
		except Exception:
			# if overlay layer isn't available, swallow - overlay cannot be shown
			pass
		overlay.add_widget(panel)

		def _pos(*a):
			w,h = root.size
			panel.x = (w - panel.width)/2
			panel.y = (h - panel.height)/2
		_pos()
		root.bind(size=lambda *_: _pos())

		def _dismiss(*a):
			try:
				# use central overlay manager
				app = App.get_running_app()
				try:
					app.remove_overlay(widget=overlay)
				except Exception:
					# fallback to direct removal
					try:
						root.remove_widget(overlay)
					except Exception:
						pass
			except Exception:
				pass

		def _do_import(mode):
			sel = chooser.selection
			if not sel:
				self._safe_popup('导入失败', '未选择文件')
				return
			path = sel[0]
			from storage import safe_load_json, load_data, save_data
			imp = safe_load_json(path)
			if not isinstance(imp, dict):
				self._safe_popup('导入失败', '文件内容不是合法 JSON 对象')
				return
			if mode == 'merge':
				data = load_data() or {'players': [], 'rounds': []}
				if imp.get('rounds'):
					data.setdefault('rounds', []).extend(imp.get('rounds') or [])
				if imp.get('players') and not data.get('players'):
					data['players'] = imp.get('players')
				try:
					save_data(data)
					self._safe_popup('导入成功', '已合并导入')
				except Exception as e:
					self._safe_popup('导入失败', str(e))
			else:
				try:
					save_data(imp)
					self._safe_popup('导入成功', '已覆盖并导入')
				except Exception as e:
					self._safe_popup('导入失败', str(e))
			_dismiss()

		merge_btn.bind(on_press=lambda *_: _do_import('merge'))
		replace_btn.bind(on_press=lambda *_: _do_import('replace'))
		cancel_btn.bind(on_press=_dismiss)

	def export_json_dialog(self):
		"""Open an export dialog allowing user to pick a directory and filename
		and save current data to that file."""
		app = App.get_running_app()
		root = getattr(app, 'root', None)
		if root is None:
			raise RuntimeError('App root not available')

		overlay = FloatLayout(size_hint=(1, 1))
		with overlay.canvas:
			Color(0, 0, 0, 0.45)
			_back = Rectangle(pos=overlay.pos, size=overlay.size)
		overlay.bind(pos=lambda inst, *_: setattr(_back, 'pos', inst.pos), size=lambda inst, *_: setattr(_back, 'size', inst.size))

		panel = BoxLayout(orientation='vertical', size_hint=(None, None), width=dp(640), height=dp(420), spacing=dp(8), padding=dp(12))
		with panel.canvas.before:
			Color(1,1,1,1)
			_panel_rect = Rectangle(pos=panel.pos, size=panel.size)
		panel.bind(pos=lambda inst, *_: setattr(_panel_rect, 'pos', inst.pos), size=lambda inst, *_: setattr(_panel_rect, 'size', inst.size))

		_label_kwargs = {'size_hint_y': None, 'height': dp(32), 'color': (0,0,0,1)}
		if FONT_NAME:
			_label_kwargs['font_name'] = FONT_NAME
		header = Label(text='导出 JSON', **_label_kwargs)
		chooser = FileChooserListView(path='.', dirselect=True, size_hint=(1,1))
		filename = TextInput(text='export.json', size_hint_y=None, height=dp(36), font_name=FONT_NAME if FONT_NAME else None)
		_info_kwargs = {'size_hint_y': None, 'height': dp(36), 'color': (0,0,0,1)}
		if FONT_NAME:
			_info_kwargs['font_name'] = FONT_NAME
		info = Label(text='选择目录并输入文件名，然后点击保存。', **_info_kwargs)

		btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
		save_btn = Button(text='保存', background_normal='', background_color=(0.8,0.9,1,1), color=(0,0,0,1), **({'font_name': FONT_NAME} if FONT_NAME else {}))
		cancel_btn = Button(text='取消', background_normal='', background_color=(0.85,0.85,0.85,1), color=(0,0,0,1), **({'font_name': FONT_NAME} if FONT_NAME else {}))
		btn_row.add_widget(save_btn)
		btn_row.add_widget(cancel_btn)

		panel.add_widget(header)
		panel.add_widget(chooser)
		panel.add_widget(filename)
		panel.add_widget(info)
		panel.add_widget(btn_row)

		# add overlay via app helper so it's managed centrally
		try:
			app.add_overlay(overlay)
		except Exception:
			pass
		overlay.add_widget(panel)

		def _pos(*a):
			w,h = root.size
			panel.x = (w - panel.width)/2
			panel.y = (h - panel.height)/2
		_pos()
		root.bind(size=lambda *_: _pos())

		def _dismiss(*a):
			try:
				app.remove_overlay(widget=overlay)
			except Exception:
				try:
					root.remove_widget(overlay)
				except Exception:
					pass

		def _do_save(*_a):
			dirpath = chooser.path
			fname = (filename.text or '').strip()
			if not fname:
				self._safe_popup('导出失败', '请输入文件名')
				return
			full = os.path.join(dirpath, fname)
			from storage import load_data, safe_save_json
			try:
				data = load_data() or {}
				safe_save_json(full, data)
				self._safe_popup('导出成功', f'已保存到 {full}')
			except Exception as e:
				self._safe_popup('导出失败', str(e))
			_dismiss()

		save_btn.bind(on_press=_do_save)
		cancel_btn.bind(on_press=_dismiss)

	def _safe_popup(self, title: str, message: str):
		# Use the unified overlay dialog implementation so all popups look the same
		try:
			self._overlay_dialog(title, message)
		except Exception:
			# fallback: attempt to show a basic Popup if overlay fails
			try:
				content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(12))
				_font_path = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'NotoSansSC-Regular.ttf')
				_font_name = _font_path if os.path.exists(_font_path) else None
				header = Label(text=title, size_hint_y=None, height=dp(28), color=(0,0,0,1), font_name=_font_name)
				msg = Label(text=message, halign='center', valign='middle', color=(0,0,0,1), font_name=_font_name)
				msg.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
				btn = Button(text='关闭', size_hint_y=None, height=dp(40), background_normal='', background_color=(0.9,0.9,0.9,1), color=(0,0,0,1))
				p = Popup(title="", content=content, size_hint=(None, None), size=(420, 180), auto_dismiss=False)
				btn.bind(on_press=lambda *_: p.dismiss())
				content.add_widget(header)
				content.add_widget(msg)
				content.add_widget(btn)
				p.open()
			except Exception:
				pass

	def _overlay_dialog(self, title: str, message: str):
		"""Create a modal overlay added to App.root with a semi-transparent
		backdrop and a centered white panel containing title, message and a
		visible close button. This avoids Popup/titlebar issues on some
		environments."""
		app = App.get_running_app()
		root = getattr(app, 'root', None)
		if root is None:
			raise RuntimeError('App root not available')

		overlay = FloatLayout(size_hint=(1, 1))
		# backdrop
		from kivy.graphics import Color, Rectangle
		with overlay.canvas:
			Color(0, 0, 0, 0.45)
			_back = Rectangle(pos=overlay.pos, size=overlay.size)
		# keep rect updated
		overlay.bind(pos=lambda inst, *_: setattr(_back, 'pos', inst.pos), size=lambda inst, *_: setattr(_back, 'size', inst.size))

		# content panel centered
		panel = BoxLayout(orientation='vertical', size_hint=(None, None), width=dp(380), height=dp(180), spacing=dp(8), padding=dp(12))
		# white background for panel
		with panel.canvas.before:
			Color(1, 1, 1, 1)
			_panel_rect = Rectangle(pos=panel.pos, size=panel.size)
		panel.bind(pos=lambda inst, *_: setattr(_panel_rect, 'pos', inst.pos), size=lambda inst, *_: setattr(_panel_rect, 'size', inst.size))

		# header, message, close button (use plain Label/Button with explicit colors)
		_font_path = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'NotoSansSC-Regular.ttf')
		_font_name = _font_path if os.path.exists(_font_path) else None
		header = Label(text=title, size_hint_y=None, height=dp(28), color=(0, 0, 0, 1), font_name=_font_name)
		msg = Label(text=message, halign='center', valign='middle', color=(0, 0, 0, 1), font_name=_font_name)
		msg.bind(size=lambda inst, *_: setattr(inst, 'text_size', (inst.width, inst.height)))
		btn = Button(text='关闭', size_hint_y=None, height=dp(40), background_normal='', background_color=(0.9, 0.9, 0.9, 1), color=(0, 0, 0, 1))
		if _font_name:
			try:
				btn.font_name = _font_name
			except Exception:
				pass

		panel.add_widget(header)
		panel.add_widget(msg)
		panel.add_widget(btn)

		# position panel centered
		overlay.add_widget(panel)
		def _pos_panel(*a):
			w, h = root.size
			panel.x = (w - panel.width) / 2
			panel.y = (h - panel.height) / 2
		_pos_panel()
		root.bind(size=lambda *_: _pos_panel())

		# add overlay to app overlay layer (centralized)
		try:
			app.add_overlay(overlay)
		except Exception:
			pass

		# dismiss action
		def _dismiss(*a):
			try:
				app.remove_overlay(widget=overlay)
			except Exception:
				try:
					root.remove_widget(overlay)
				except Exception:
					pass

		btn.bind(on_press=_dismiss)
		# also dismiss on backdrop touch
		def _on_touch(instance, touch):
			if not panel.collide_point(*touch.pos):
				_dismiss()
				return True
			return False
		overlay.bind(on_touch_down=_on_touch)
		return overlay

