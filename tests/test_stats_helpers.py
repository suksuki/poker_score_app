import json
from stats_helpers import player_stats_from_data, summary_stats


def test_basic_counts():
    data = {
        'rounds': [
            {
                'id': 'r1',
                'date': '2025-11-01T10:00:00',
                'results': [
                    {'player': 'A', 'score': 100, 'base': 10, 'rank': 1, 'dun': 2},
                    {'player': 'B', 'score': 50, 'base': 5, 'rank': 2, 'dun': 1},
                    {'player': 'C', 'score': -20, 'base': 0, 'rank': 3, 'dun': 0},
                ],
            },
            {
                'id': 'r2',
                'date': '2025-11-02T10:00:00',
                'results': [
                    {'player': 'A', 'score': -30, 'base': 0, 'rank': 2, 'dun': 0},
                    {'player': 'B', 'score': 10, 'base': 1, 'rank': 1, 'dun': 1},
                    {'player': 'C', 'score': 20, 'base': 2, 'rank': 3, 'dun': 0},
                ],
            },
        ]
    }

    out = player_stats_from_data(data)
    assert out['A']['total'] == 70
    assert out['A']['base'] == 10
    assert out['A']['base_avg'] == 5
    assert out['A']['first_count'] == 1
    assert out['A']['last_count'] == 0
    assert out['A']['games_played'] == 2

    assert out['B']['total'] == 60
    assert out['B']['first_count'] == 1
    assert out['B']['last_count'] == 0

    s = summary_stats(out)
    assert s['total'] == 70 + 60 + 0


def test_date_filter():
    data = {
        'rounds': [
            {
                'id': 'r1',
                'date': '2025-10-01T10:00:00',
                'results': [
                    {'player': 'A', 'score': 10, 'rank': 1},
                    {'player': 'B', 'score': 0, 'rank': 2},
                ],
            },
            {
                'id': 'r2',
                'date': '2025-11-10T10:00:00',
                'results': [
                    {'player': 'A', 'score': 20, 'rank': 1},
                    {'player': 'B', 'score': 5, 'rank': 2},
                ],
            },
        ]
    }

    out = player_stats_from_data(data, date_from='2025-11-01T00:00:00')
    assert out['A']['total'] == 20
    assert out['B']['total'] == 5
