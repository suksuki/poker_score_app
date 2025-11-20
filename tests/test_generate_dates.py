from statistics_screen import StatisticsScreen


def test_generate_test_data_writes_dates(monkeypatch):
    # avoid disk writes by stubbing save_data in module
    monkeypatch.setattr('statistics_screen.save_data', lambda d: None)
    s = StatisticsScreen()
    initial = len(s.data.get('rounds', [])) if isinstance(s.data, dict) else 0
    s.generate_test_data(10)
    new_rounds = s.data.get('rounds', [])[initial:]
    # ensure at least one new round was appended and each new round has a date with time
    assert len(new_rounds) > 0
    for r in new_rounds:
        assert 'date' in r
        v = r['date']
        assert isinstance(v, str)
        assert (('T' in v) or (':' in v))
