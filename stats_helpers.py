"""Statistics helpers for Poker Score App.

Provides robust functions to compute per-player statistics from storage data.
"""
from collections import defaultdict
from statistics import mean
from datetime import datetime
from typing import Optional, Iterable, Dict, Any


def _parse_date(d):
    if d is None:
        return None
    if isinstance(d, datetime):
        return d
    try:
        # assume ISO format
        return datetime.fromisoformat(d)
    except Exception:
        try:
            # fallback: try common formats
            return datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None


def collect_rounds(data: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """Return a list-like iterable of rounds/games from data.
    Accept several common keys (`rounds`, `games`, `matches`).
    """
    if not isinstance(data, dict):
        return []
    for key in ('rounds', 'games', 'matches'):
        if key in data and isinstance(data[key], list):
            return data[key]
    # fallback: if data itself looks like a list-of-rounds
    if isinstance(data, list):
        return data
    return []


def player_stats_from_data(data: Dict[str, Any], player_filter: Optional[Iterable[str]] = None,
                           date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Compute per-player statistics.

    Returns a dict mapping player->stats where stats contains:
      total, base, base_avg, avg_rank, dun_count, avg_dun, first_count, last_count, games_played

    `player_filter` if provided restricts to those players (iterable of names).
    `date_from` / `date_to` are ISO date strings (inclusive)
    """
    rounds = list(collect_rounds(data))
    date_from_dt = _parse_date(date_from) if date_from else None
    date_to_dt = _parse_date(date_to) if date_to else None
    pf = set(player_filter) if player_filter is not None else None

    per = defaultdict(lambda: {
        'total': 0.0,
        'base': 0.0,
        'ranks': [],
        'duns': 0,
        'first_count': 0,
        'last_count': 0,
        'games_played': 0,
    })

    for r in rounds:
        # optional date filtering
        rd = None
        try:
            rd = _parse_date(r.get('date')) if isinstance(r, dict) else None
        except Exception:
            rd = None
        if date_from_dt and rd and rd < date_from_dt:
            continue
        if date_to_dt and rd and rd > date_to_dt:
            continue

        results = None
        if isinstance(r, dict):
            results = r.get('results') or r.get('players') or r.get('player_results')
            # compatibility: older saved format may store per-round dicts under
            # keys like 'total' (player->score) and 'ranks' (player->rank) and
            # breakdown.basic / breakdown.duns_raw for base/dun values. Normalize
            # that into the `results` list form if present.
            if results is None:
                # try total + ranks
                total_map = r.get('total') if isinstance(r.get('total'), dict) else None
                ranks_map = r.get('ranks') if isinstance(r.get('ranks'), dict) else None
                breakdown = r.get('breakdown') if isinstance(r.get('breakdown'), dict) else None
                if total_map or ranks_map or breakdown:
                    normalized = []
                    players_keys = set()
                    if total_map:
                        players_keys |= set(total_map.keys())
                    if ranks_map:
                        players_keys |= set(ranks_map.keys())
                    if breakdown:
                        # breakdown may contain 'basic' and 'duns_raw'
                        basic = breakdown.get('basic') if isinstance(breakdown.get('basic'), dict) else {}
                        duns_raw = breakdown.get('duns_raw') if isinstance(breakdown.get('duns_raw'), dict) else {}
                        players_keys |= set(basic.keys()) | set(duns_raw.keys())
                    for pname in players_keys:
                        entry = {'player': pname}
                        if total_map and pname in total_map:
                            entry['score'] = total_map.get(pname)
                        if ranks_map and pname in ranks_map:
                            entry['rank'] = ranks_map.get(pname)
                        if breakdown:
                            basic = breakdown.get('basic') if isinstance(breakdown.get('basic'), dict) else {}
                            duns_raw = breakdown.get('duns_raw') if isinstance(breakdown.get('duns_raw'), dict) else {}
                            if pname in basic:
                                entry['base'] = basic.get(pname)
                            if pname in duns_raw:
                                entry['dun'] = duns_raw.get(pname)
                        normalized.append(entry)
                    results = normalized
        else:
            results = None
        if results is None:
            continue

        # Normalize results into list of dicts
        if isinstance(results, dict):
            # mapping player -> score or mapping
            normalized = []
            for k, v in results.items():
                if isinstance(v, dict):
                    entry = {'player': k}
                    entry.update(v)
                else:
                    entry = {'player': k, 'score': v}
                normalized.append(entry)
            results = normalized
        elif isinstance(results, list):
            # ensure each item is a dict
            norm = []
            for item in results:
                if isinstance(item, dict):
                    norm.append(item)
                else:
                    # unknown item, skip
                    continue
            results = norm
        else:
            continue

        # compute max rank in this round if rank present
        ranks_present = [res.get('rank') for res in results if isinstance(res, dict) and res.get('rank') is not None]
        max_rank = max(ranks_present) if ranks_present else None

        for res in results:
            if not isinstance(res, dict):
                continue
            name = res.get('player') or res.get('name')
            if name is None:
                continue
            if pf is not None and name not in pf:
                continue
            score = res.get('score') or res.get('points') or 0
            base = res.get('base') or 0
            rank = res.get('rank')
            dun = res.get('dun') or res.get('tuns') or res.get('dots') or 0

            s = per[name]
            try:
                s['total'] += float(score)
            except Exception:
                try:
                    s['total'] += int(score)
                except Exception:
                    pass
            try:
                s['base'] += float(base)
            except Exception:
                try:
                    s['base'] += int(base)
                except Exception:
                    pass
            if rank is not None:
                try:
                    s['ranks'].append(int(rank))
                except Exception:
                    pass
                try:
                    if int(rank) == 1:
                        s['first_count'] += 1
                except Exception:
                    pass
                if max_rank is not None:
                    try:
                        if int(rank) == int(max_rank):
                            s['last_count'] += 1
                    except Exception:
                        pass
            try:
                s['duns'] += int(dun)
            except Exception:
                pass
            s['games_played'] += 1

    # finalize
    out = {}
    for name, s in per.items():
        gp = s['games_played']
        base_avg = (s['base'] / gp) if gp else 0
        avg_rank = mean(s['ranks']) if s['ranks'] else None
        avg_dun = (s['duns'] / gp) if gp else 0
        out[name] = {
            'total': s['total'],
            'base': s['base'],
            'base_avg': base_avg,
            'avg_rank': avg_rank,
            'dun_count': s['duns'],
            'avg_dun': avg_dun,
            'first_count': s['first_count'],
            'last_count': s['last_count'],
            'games_played': gp,
        }
    return out


def summary_stats(per_player_stats: Dict[str, Dict[str, Any]], selected_players: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    """Aggregate summary numbers across selected players (or all if not specified)."""
    names = set(selected_players) if selected_players is not None else set(per_player_stats.keys())
    total = 0
    base = 0
    games = 0
    for n in names:
        v = per_player_stats.get(n)
        if not v:
            continue
        total += v.get('total', 0)
        base += v.get('base', 0)
        games += v.get('games_played', 0)
    base_avg = (base / games) if games else 0
    return {'total': total, 'base': base, 'base_avg': base_avg, 'games': games}


def export_stats_csv(per_player_stats: Dict[str, Dict[str, Any]], path: str) -> None:
    import csv
    headers = ['player', 'total', 'base', 'base_avg', 'avg_rank', 'dun_count', 'avg_dun', 'first_count', 'last_count', 'games_played']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(headers)
        for p, stats in per_player_stats.items():
            w.writerow([
                p,
                stats.get('total', 0),
                stats.get('base', 0),
                stats.get('base_avg', 0),
                stats.get('avg_rank', ''),
                stats.get('dun_count', 0),
                stats.get('avg_dun', 0),
                stats.get('first_count', 0),
                stats.get('last_count', 0),
                stats.get('games_played', 0),
            ])


def rounds_flat_list(data: Dict[str, Any], player_filter: Optional[Iterable[str]] = None) -> list:
    """Return a flat list of per-round, per-player entries.

    Each item is a dict with keys: 'round_index', 'player', 'score', 'base', 'rank', 'dun'.
    If `player_filter` is provided, only include those players.
    """
    rounds = list(collect_rounds(data))
    pf = set(player_filter) if player_filter is not None else None
    out = []
    for i, r in enumerate(rounds, start=1):
        results = None
        if isinstance(r, dict):
            results = r.get('results') or r.get('players') or r.get('player_results')
            if results is None:
                total_map = r.get('total') if isinstance(r.get('total'), dict) else None
                ranks_map = r.get('ranks') if isinstance(r.get('ranks'), dict) else None
                breakdown = r.get('breakdown') if isinstance(r.get('breakdown'), dict) else None
                if total_map or ranks_map or breakdown:
                    normalized = []
                    players_keys = set()
                    if total_map:
                        players_keys |= set(total_map.keys())
                    if ranks_map:
                        players_keys |= set(ranks_map.keys())
                    if breakdown:
                        basic = breakdown.get('basic') if isinstance(breakdown.get('basic'), dict) else {}
                        duns_raw = breakdown.get('duns_raw') if isinstance(breakdown.get('duns_raw'), dict) else {}
                        players_keys |= set(basic.keys()) | set(duns_raw.keys())
                    for pname in players_keys:
                        entry = {'player': pname}
                        if total_map and pname in total_map:
                            entry['score'] = total_map.get(pname)
                        if ranks_map and pname in ranks_map:
                            entry['rank'] = ranks_map.get(pname)
                        if breakdown:
                            basic = breakdown.get('basic') if isinstance(breakdown.get('basic'), dict) else {}
                            duns_raw = breakdown.get('duns_raw') if isinstance(breakdown.get('duns_raw'), dict) else {}
                            if pname in basic:
                                entry['base'] = basic.get(pname)
                            if pname in duns_raw:
                                entry['dun'] = duns_raw.get(pname)
                        normalized.append(entry)
                    results = normalized
        if results is None:
            continue

        # normalize mapping -> list
        if isinstance(results, dict):
            normalized = []
            for k, v in results.items():
                if isinstance(v, dict):
                    entry = {'player': k}
                    entry.update(v)
                else:
                    entry = {'player': k, 'score': v}
                normalized.append(entry)
            results = normalized
        elif isinstance(results, list):
            norm = [item for item in results if isinstance(item, dict)]
            results = norm
        else:
            continue

        for res in results:
            name = res.get('player') or res.get('name')
            if name is None:
                continue
            if pf is not None and name not in pf:
                continue
            out.append({
                'round_index': i,
                'date': r.get('date') if isinstance(r, dict) else None,
                'player': name,
                'score': res.get('score') or res.get('points') or 0,
                'base': res.get('base') or 0,
                'rank': res.get('rank'),
                'dun': res.get('dun') or res.get('tuns') or 0,
            })
    return out


def export_rounds_csv(data: Dict[str, Any], path: str, player_filter: Optional[Iterable[str]] = None) -> None:
    """Export per-round, per-player flat rows to CSV.

    Columns: round_index, player, score, base, rank, dun
    If player_filter is provided, only include those players.
    """
    rows = rounds_flat_list(data, player_filter=player_filter)
    import csv
    headers = ['date', 'round_index', 'player', 'score', 'base', 'rank', 'dun']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in rows:
            w.writerow([
                r.get('date', ''),
                r.get('round_index'),
                r.get('player'),
                r.get('score'),
                r.get('base'),
                r.get('rank') if r.get('rank') is not None else '',
                r.get('dun'),
            ])
