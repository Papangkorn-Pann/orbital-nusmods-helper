"""
Backtracking timetable generator.

Explores all conflict-free slot combinations for a set of modules and returns
the top N results ranked by a weighted 5-dimensional score:
  • latest_start  – prefer classes that begin late
  • earliest_end  – prefer classes that finish early
  • lunch_break   – keep 12:00–14:00 free each day
  • compact_days  – fewer days with any classes
  • minimal_gaps  – minimise idle time between first and last class each day
"""

import heapq
import time
from typing import List, Dict, Any
import api


def _to_min(t: str) -> int:
    """'HHMM' → minutes since midnight."""
    return int(t[:2]) * 60 + int(t[2:])


def _score(flat_slots: List[Dict], prefs: Dict) -> float:
    """Weighted preference score in [0, 1] for a complete slot assignment."""
    if not flat_slots:
        return 0.0

    days: Dict[str, List[tuple]] = {}
    for s in flat_slots:
        start = _to_min(s["startTime"])
        end   = _to_min(s["endTime"])
        days.setdefault(s["day"], []).append((start, end))

    n = len(days)

    # Latest start: prefer classes that begin as late as possible
    avg_first = sum(min(p[0] for p in segs) for segs in days.values()) / n
    latest_start = max(0.0, min(1.0, (avg_first - 480) / max(720 - 480, 1)))  # 8am→0, 12pm→1

    # Earliest end: prefer classes that finish as early as possible
    avg_last = sum(max(p[1] for p in segs) for segs in days.values()) / n
    earliest_end = max(0.0, min(1.0, 1 - (avg_last - 720) / max(1200 - 720, 1)))  # 12pm→1, 8pm→0

    # Lunch break: fraction of days where 12:00–14:00 (720–840 min) is free
    lunch_free = sum(
        1 for segs in days.values()
        if not any(s < 840 and e > 720 for s, e in segs)
    )
    lunch = lunch_free / n

    # Compact days: 1 day → 1.0, 5 days → 0.0
    compact = max(0.0, min(1.0, 1 - (n - 1) / 4))

    # Minimal gaps: ratio of actual class time to total daily span
    total_class = sum(e - s for segs in days.values() for s, e in segs)
    total_span  = sum(
        max(e for _, e in segs) - min(s for s, _ in segs)
        for segs in days.values()
    )
    gap_score = total_class / total_span if total_span > 0 else 1.0

    w_ls = prefs.get("latest_start", 0.2)
    w_ee = prefs.get("earliest_end", 0.2)
    w_lb = prefs.get("lunch_break",  0.2)
    w_cd = prefs.get("compact_days", 0.2)
    w_mg = prefs.get("minimal_gaps", 0.2)
    total_w = (w_ls + w_ee + w_lb + w_cd + w_mg) or 1.0

    return round(
        (w_ls * latest_start + w_ee * earliest_end +
         w_lb * lunch + w_cd * compact + w_mg * gap_score) / total_w,
        4,
    )


def generate_timetables(
    module_codes: List[str],
    sem: int,
    preferences: Dict,
    top_n: int = 5,
    timeout: float = 8.0,
) -> List[Dict[str, Any]]:
    """
    Return up to top_n best timetable combinations (by weighted score).

    Uses backtracking with incremental conflict pruning.  A per-call timeout
    (default 8 s) ensures the endpoint always responds promptly.

    Each result dict: {"score": float, "selections": [...], "rendered_slots": [...]}
    """

    # ── build task list: one entry per (module, lessonType) ───────────────────
    tasks: List[tuple] = []
    for code in module_codes:
        slots = api.fetch_module_slots(code.upper(), sem)
        if not slots:
            continue
        by_lt: Dict[str, Dict[str, list]] = {}
        for slot in slots:
            lt = slot["lessonType"]
            cn = slot["classNo"]
            by_lt.setdefault(lt, {}).setdefault(cn, []).append(slot)
        for lt, by_class in sorted(by_lt.items()):
            tasks.append((code.upper(), lt, by_class))

    if not tasks:
        return []

    # Fewest choices first → better conflict pruning
    tasks.sort(key=lambda t: len(t[2]))

    heap: List = []      # min-heap: (score, counter, sel, flat)
    ctr = [0]
    deadline = time.time() + timeout

    def _bt(idx: int, sel: List[Dict], flat: List[Dict]) -> None:
        if time.time() > deadline:
            return

        if idx == len(tasks):
            sc = _score(flat, preferences)
            entry = (sc, ctr[0], [dict(s) for s in sel], [dict(f) for f in flat])
            if len(heap) < top_n:
                heapq.heappush(heap, entry)
            elif sc > heap[0][0]:
                heapq.heapreplace(heap, entry)
            ctr[0] += 1
            return

        code, lt, by_class = tasks[idx]
        for cn, cn_slots in by_class.items():
            if time.time() > deadline:
                return

            # Incremental conflict check against already-placed slots
            conflict = False
            for ex in flat:
                if conflict:
                    break
                ex_s = _to_min(ex["startTime"])
                ex_e = _to_min(ex["endTime"])
                for ns in cn_slots:
                    if ex["day"] == ns["day"]:
                        ns_s = _to_min(ns["startTime"])
                        ns_e = _to_min(ns["endTime"])
                        if ex_s < ns_e and ns_s < ex_e:
                            conflict = True
                            break

            if conflict:
                continue

            tagged = [{**s, "moduleCode": code} for s in cn_slots]
            sel.append({"module_code": code, "lesson_type": lt, "class_no": cn})
            flat.extend(tagged)
            _bt(idx + 1, sel, flat)
            sel.pop()
            del flat[-len(cn_slots):]

    _bt(0, [], [])

    results = sorted(heap, key=lambda x: x[0], reverse=True)
    return [
        {"score": r[0], "selections": r[2], "rendered_slots": r[3]}
        for r in results
    ]
