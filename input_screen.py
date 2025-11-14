from typing import Dict, List

from kivy.metrics import sp, dp
from theme import ROW_HEIGHT
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

from widgets import L, ScoreInputItem, IconButton, TrophyWidget


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

		root = BoxLayout(orientation="vertical")

		# Top notice (user requested)
		self.notice = L(
			"每位玩家基础分100分，每顿30分，扣除100分后，总分应该为0",
			font_size=sp(18),
			size_hint_y=None,
			height=sp(44),
		)
		root.add_widget(self.notice)

		# Middle: intentionally empty flexible area
		# Middle: player rows live inside a ScrollView -> GridLayout
		self.middle = ScrollView()
		self.rows_container = GridLayout(cols=1, spacing=8, size_hint_y=None)
		self.rows_container.bind(minimum_height=self.rows_container.setter('height'))
		self.middle.add_widget(self.rows_container)
		root.add_widget(self.middle)

		# Do not prefill player rows here — names come from SetupScreen via set_players()

		self.add_widget(root)

	def set_players(self, players: List[str]):
		"""Store the players list and clear previous input maps."""
		# store and clear previous inputs
		self.players = list(players) if players else []
		self.hand_inputs.clear()
		self.dun_inputs.clear()
		# Debug: print received players so we can verify SetupScreen handed them over
		try:
			print(f"[DEBUG] InputScreen.set_players called with: {self.players}")
		except Exception:
			pass
		# rebuild rows according to players length and pass the names so they are filled
		self._build_player_rows(len(self.players), names=self.players)

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

			self.rows_container.add_widget(row)
		# Debug: show what was rendered and what input mappings we saved
		try:
			rendered = [getattr(r, 'name_label').text if getattr(r, 'name_label', None) is not None else '' for r in self.rows_container.children[::-1]]
			print(f"[DEBUG] InputScreen._build_player_rows rendered names (top->bottom): {rendered}")
		except Exception:
			pass
		try:
			print(f"[DEBUG] InputScreen.hand_inputs keys: {list(self.hand_inputs.keys())}")
		except Exception:
			pass
		try:
			print(f"[DEBUG] InputScreen.dun_inputs keys: {list(self.dun_inputs.keys())}")
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

	# Lightweight placeholders so global import/export buttons can call these.
	def import_json_dialog(self):
		p = Popup(title="导入", content=Label(text="导入功能（占位）"), size_hint=(None, None), size=(480, 220))
		p.open()

	def export_json_dialog(self):
		p = Popup(title="导出", content=Label(text="导出功能（占位）"), size_hint=(None, None), size=(480, 220))
		p.open()

