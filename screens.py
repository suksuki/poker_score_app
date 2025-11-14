"""Compatibility shim: re-export screen classes from their dedicated modules.

This keeps existing imports like `from screens import InputScreen` working
after we split each screen into its own file.
"""
from input_screen import InputScreen
from score_screen import ScoreScreen
from setup_screen import SetupScreen
from statistics_screen import StatisticsScreen

__all__ = [
    'InputScreen', 'ScoreScreen', 'SetupScreen', 'StatisticsScreen'
]
