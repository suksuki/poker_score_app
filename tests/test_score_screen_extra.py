from score_screen import ScoreScreen
import storage


def test_set_players_saves_and_rebuilds(monkeypatch):
    ss = ScoreScreen(name='score')
    saved = {}

    def fake_save(data):
        saved['data'] = data

    called = {'rebuild': False}

    def fake_rebuild():
        called['rebuild'] = True

    import score_screen
    monkeypatch.setattr(score_screen, 'save_data', fake_save)
    monkeypatch.setattr(score_screen, 'load_data', lambda: {})
    # monkeypatch rebuild_board to avoid heavy UI work
    monkeypatch.setattr(ScoreScreen, 'rebuild_board', lambda self: fake_rebuild())

    players = ['A', 'B', 'C']
    ss.set_players(players)

    # ensure save_data was called with players updated
    assert 'data' in saved
    assert saved['data'].get('players') == players
    # ensure rebuild_board (patched) was invoked
    assert called['rebuild'] is True
