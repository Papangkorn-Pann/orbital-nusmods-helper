"""
Backtracking timetable generator.

Explores all conflict-free slot combinations for a set of modules and returns
the top N results ranked by a weighted 7-dimensional score:
  • latest_start     – prefer classes that begin late
  • earliest_end     – prefer classes that finish early
  • lunch_break      – keep 12:00–14:00 free each day
  • compact_days     – fewer days with any classes
  • minimal_gaps     – minimise idle time between first and last class each day
  • minimize_travel  – avoid back-to-back classes in distant campus zones
  • peer_avoidance   – prefer slots chosen by fewer peers (easier to get in CourseReg)
"""

import heapq
import random
import time
from typing import List, Dict, Any
import api

# ── NUS campus zone lookup ────────────────────────────────────────────────────
# Each zone is an integer index into _ZONE_TRAVEL.
# Venue strings from NUSMods look like "COM1-0210", "AS4-0602", "LT27", etc.

_ZONE_NAMES = ["Computing", "Arts/FASS", "Science", "Engineering",
               "Business", "UTown", "Bukit Timah", "Medicine", "Central/LT"]

_ZONE_TRAVEL = [
    #  COM  AS  SCI  ENG  BIZ  UTW   BT  MED  CTR
    [   2,   8,   5,  12,  10,  15,  30,  20,   8],  # 0 Computing
    [   8,   2,   8,  15,  12,  12,  25,  20,   5],  # 1 Arts/FASS
    [   5,   8,   2,  15,  12,  18,  30,  20,   8],  # 2 Science
    [  12,  15,  15,   2,  12,  25,  35,  25,  15],  # 3 Engineering
    [  10,  12,  12,  12,   2,  15,  25,  20,  10],  # 4 Business
    [  15,  12,  18,  25,  15,   2,  20,  25,  12],  # 5 UTown
    [  30,  25,  30,  35,  25,  20,   2,  30,  25],  # 6 Bukit Timah
    [  20,  20,  20,  25,  20,  25,  30,   2,  20],  # 7 Medicine
    [   8,   5,   8,  15,  10,  12,  25,  20,   2],  # 8 Central/LT
]


def _venue_zone(venue: str) -> int:
    """Map a NUSMods venue string to a campus zone index."""
    if not venue:
        return 8
    b = venue.upper().split("-")[0]
    if b.startswith("COM") or b.startswith("I3"):
        return 0
    if b.startswith("AS"):
        return 1
    if b.startswith("FASS") or b.startswith("UT-"):
        return 1
    if b.startswith("S") and len(b) <= 4 and b[1:].isdigit():
        return 2
    if b.startswith("E") and len(b) <= 3 and b[1:].isdigit():
        return 3
    if b in ("EA", "EW", "E-LR1", "E-LR2"):
        return 3
    if b.startswith("BIZ"):
        return 4
    if b.startswith("UTW") or b.startswith("ERC") or b in ("RC4", "RVRC", "CAPT"):
        return 5
    if b.startswith("BSPR") or b.startswith("BTAP"):
        return 6
    if b.startswith("MD") or b.startswith("NUHS") or b.startswith("CRC"):
        return 7
    return 8  # LT, YIH, CLB, MPSH, unknown → Central


def _to_min(t: str) -> int:
    """'HHMM' → minutes since midnight."""
    return int(t[:2]) * 60 + int(t[2:])


def _score(flat_slots: List[Dict], prefs: Dict, slot_demand: Dict = None) -> float:
    """Weighted preference score in [0, 1] for a complete slot assignment."""
    if not flat_slots:
        return 0.0

    days: Dict[str, List[tuple]] = {}         # day → [(start, end)]
    days_v: Dict[str, List[tuple]] = {}       # day → [(start, end, venue)]
    for s in flat_slots:
        start = _to_min(s["startTime"])
        end   = _to_min(s["endTime"])
        venue = s.get("venue", "")
        days.setdefault(s["day"], []).append((start, end))
        days_v.setdefault(s["day"], []).append((start, end, venue))

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

    # Minimize travel: penalise consecutive classes in distant campus zones.
    # Score = fraction of back-to-back pairs where gap ≥ required travel time.
    travel_pairs = 0
    travel_ok    = 0
    for segs in days_v.values():
        ordered = sorted(segs, key=lambda x: x[0])
        for i in range(len(ordered) - 1):
            _, end1, v1 = ordered[i]
            start2, _, v2 = ordered[i + 1]
            gap_min     = start2 - end1
            needed      = _ZONE_TRAVEL[_venue_zone(v1)][_venue_zone(v2)]
            travel_pairs += 1
            if gap_min >= needed:
                travel_ok += 1
    travel_score = travel_ok / travel_pairs if travel_pairs else 1.0

    # Day preference: fraction of school days that fall on a user-preferred day
    preferred_days = set(prefs.get("preferred_days", []))
    if preferred_days:
        days_on_pref = sum(1 for d in days if d in preferred_days)
        day_pref_score = days_on_pref / n
        w_dp = prefs.get("day_preference", 0.0)
    else:
        day_pref_score = 1.0
        w_dp = 0.0

    # Peer avoidance: prefer slots selected by fewer peers (easier to get in CourseReg)
    if slot_demand:
        max_demand = max(slot_demand.values()) or 1
        fractions = [
            min(slot_demand.get(f"{s['moduleCode']}|{s['lessonType']}|{s['classNo']}", 0) / max_demand, 1.0)
            for s in flat_slots
        ]
        peer_avoidance = 1.0 - (sum(fractions) / len(fractions))
    else:
        peer_avoidance = 1.0

    w_ls = prefs.get("latest_start",    0.2)
    w_ee = prefs.get("earliest_end",    0.2)
    w_lb = prefs.get("lunch_break",     0.2)
    w_cd = prefs.get("compact_days",    0.2)
    w_mg = prefs.get("minimal_gaps",    0.2)
    w_mt = prefs.get("minimize_travel", 0.0)
    w_pa = prefs.get("peer_avoidance",  0.0)
    total_w = (w_ls + w_ee + w_lb + w_cd + w_mg + w_mt + w_dp + w_pa) or 1.0

    return round(
        (w_ls * latest_start + w_ee * earliest_end +
         w_lb * lunch + w_cd * compact + w_mg * gap_score +
         w_mt * travel_score + w_dp * day_pref_score +
         w_pa * peer_avoidance) / total_w,
        4,
    )


def generate_timetables(
    module_codes: List[str],
    sem: int,
    preferences: Dict,
    top_n: int = 5,
    timeout: float = 8.0,
    slot_demand: Dict = None,
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
            # Shuffle class options so that when multiple classes share the same
            # timeslot pattern no single class number is always favoured in results.
            items = list(by_class.items())
            random.shuffle(items)
            tasks.append((code.upper(), lt, items))

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
            sc = _score(flat, preferences, slot_demand)
            entry = (sc, ctr[0], [dict(s) for s in sel], [dict(f) for f in flat])
            if len(heap) < top_n:
                heapq.heappush(heap, entry)
            elif sc > heap[0][0]:
                heapq.heapreplace(heap, entry)
            ctr[0] += 1
            return

        code, lt, by_class = tasks[idx]
        for cn, cn_slots in by_class:
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
