import json, os, datetime, shutil

DATA_FILE = "score_data.json"
DUN_VALUE = 30

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

def ensure_backup(file_path):
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
