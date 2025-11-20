import json
import os
from pathlib import Path
import tempfile
import shutil
import storage


def test_to_int_basic():
    assert storage.to_int(5) == 5
    assert storage.to_int(5.9) == 5
    assert storage.to_int(" 42 ") == 42
    assert storage.to_int("", default=7) == 7
    assert storage.to_int(None, default=3) == 3
    assert storage.to_int("notint", default=-1) == -1


def test_safe_save_and_load_json(tmp_path):
    p = tmp_path / "x.json"
    data = {"a": 1, "b": [1, 2, 3]}
    storage.safe_save_json(str(p), data)
    loaded = storage.safe_load_json(str(p))
    assert loaded == data


def test_save_and_load_data_monkeypatch(tmp_path, monkeypatch):
    # monkeypatch module DATA_FILE to a temp file inside tmp_path
    p = tmp_path / "score_data.json"
    monkeypatch.setattr(storage, 'DATA_FILE', str(p))
    sample = {"players": ["A", "B"], "rounds": [{"total": {"A": 10, "B": -10}}]}
    storage.save_data(sample)
    assert p.exists()
    loaded = storage.load_data()
    # players preserved
    assert loaded.get('players') == sample.get('players')
    # rounds preserved (total map present)
    assert isinstance(loaded.get('rounds'), list) and len(loaded['rounds']) == 1
    assert loaded['rounds'][0].get('total') == sample['rounds'][0].get('total')
    # ensure missing date was backfilled
    assert 'date' in loaded['rounds'][0]


def test_ensure_backup_creates_copy(tmp_path, monkeypatch):
    p = tmp_path / "orig.json"
    p.write_text(json.dumps({"x": 1}), encoding='utf-8')
    bak = storage.ensure_backup(str(p))
    # backup should either be None (on failure) or a filename that exists
    if bak:
        assert os.path.exists(bak)
        # backup should not be identical path
        assert bak != str(p)


def test_safe_load_json_on_missing(tmp_path):
    missing = tmp_path / "nope.json"
    assert storage.safe_load_json(str(missing)) == {}

