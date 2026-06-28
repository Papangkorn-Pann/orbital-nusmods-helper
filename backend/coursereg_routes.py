"""
CourseReg slot competition analyser.

Uses NUSMods slot capacity data and dynamic user-selection counts from our own
database to estimate relative competition for each tutorial/lab/lecture slot.

Since actual NUS CORS bidding data is not publicly accessible via API, the
model uses three signals:
  • capacity (size):      smaller slots → scarcer → more competitive
  • timing desirability:  popular days/times attract more bids
  • platform demand:      how many users on this platform chose each slot (dynamic)

Round probability formula is a heuristic calibrated to typical NUS participation
patterns (R0: special, R1A: final-year priority, R1B: all undergrads, R2: leftovers).
"""

import math
#import sqlite3
import psycopg2
import psycopg2.extras
from fastapi import APIRouter, HTTPException, Query, Depends
import api as nusmods_api
import database_access

router = APIRouter(tags=["coursereg"])


def get_conn():
    conn = database_access.get_connection()
    try:
        yield conn
    finally:
        conn.close()


_DAY_DESIRABILITY = {
    "Monday":    0.65,
    "Tuesday":   0.90,
    "Wednesday": 0.70,
    "Thursday":  0.90,
    "Friday":    0.50,
    "Saturday":  0.20,
}


def _time_desirability(start: str) -> float:
    """Score 0–1 for how desirable a start time is (1 = most in-demand)."""
    hour = int(start[:2])
    if hour < 8:    return 0.20
    if hour <= 9:   return 0.80
    if hour <= 11:  return 1.00
    if hour <= 13:  return 0.55   # lunch slots — less desirable
    if hour <= 15:  return 0.80
    if hour <= 17:  return 0.65
    return 0.25                   # evening classes


def _slot_demand_counts(module_code: str, sem: int, conn: psycopg2.extensions.connection) -> dict:
    """Return {(lesson_type, class_no): count} of user selections from the DB."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    rows = cur.execute("""
        SELECT lesson_type, class_no, COUNT(*) AS cnt
        FROM timetable_slots
        WHERE module_code = %s AND sem = %s
        GROUP BY lesson_type, class_no
    """, (module_code.upper(), sem))
    rows = cur.fetchall()
    return {(r["lesson_type"], r["class_no"]): r["cnt"] for r in rows}


def _analyse_slots(slots: list, demand_counts: dict) -> dict:
    """
    Group slots by lessonType, score each class option, and return a
    competition score [0, 1] normalised within each lessonType.
    """
    by_lt: dict[str, dict[str, list]] = {}
    for s in slots:
        lt = s.get("lessonType", "")
        cn = s.get("classNo", "")
        by_lt.setdefault(lt, {}).setdefault(cn, []).append(s)

    results: dict[str, list] = {}
    for lt, by_class in by_lt.items():
        class_scores = []
        for cn, cn_slots in by_class.items():
            sizes = [s.get("size", 30) for s in cn_slots if s.get("size")]
            capacity = min(sizes) if sizes else 30

            # Combined timing + day desirability per slot, then averaged
            desirability = sum(
                _time_desirability(s.get("startTime", "0900")) * 0.6 +
                _DAY_DESIRABILITY.get(s.get("day", "Wednesday"), 0.6) * 0.4
                for s in cn_slots
            ) / len(cn_slots)

            user_demand = demand_counts.get((lt, cn), 0)

            # Raw competition score (unnormalised)
            capacity_factor = 1.0 / math.log(max(capacity, 2) + 1)
            raw = (
                0.40 * capacity_factor * 10 +
                0.35 * desirability +
                0.25 * min(1.0, user_demand / 10.0)
            )

            class_scores.append({
                "class_no":        cn,
                "lesson_type":     lt,
                "capacity":        capacity,
                "desirability":    round(desirability, 3),
                "platform_demand": user_demand,
                "_raw":            raw,
                "slots":           cn_slots,
            })

        # Normalise competition_score within this lessonType
        raws = [c["_raw"] for c in class_scores]
        lo, hi = min(raws), max(raws)
        span = hi - lo if hi - lo > 0.001 else 1.0
        for c in class_scores:
            c["competition_score"] = round((c["_raw"] - lo) / span, 3)
            del c["_raw"]

        results[lt] = sorted(class_scores, key=lambda x: x["competition_score"], reverse=True)

    return results


def _round_probabilities(score: float) -> dict:
    """
    Map a normalised competition score [0, 1] to estimated bid-success
    probabilities for each CourseReg round.

    Round 0  — special circumstances / LOA only (very restricted)
    Round 1A — final-year students / most AUs (higher priority)
    Round 1B — all eligible undergrads (largest participation)
    Round 2  — leftover vacancies (easiest for low-demand slots)
    """
    p0  = round(max(0.05, 0.30 - score * 0.25), 2)
    p1a = round(max(0.20, 0.75 - score * 0.50), 2)
    p1b = round(max(0.30, 0.88 - score * 0.55), 2)
    p2  = round(max(0.45, 0.97 - score * 0.50), 2)
    return {
        "round_0":  p0,
        "round_1a": p1a,
        "round_1b": p1b,
        "round_2":  p2,
    }


def _recommendation(score: float) -> str:
    if score > 0.65:
        return "High demand — bid in Round 1A or 1B to be safe"
    if score > 0.35:
        return "Moderate demand — Round 1B is usually sufficient"
    return "Low demand — Round 2 should be fine"


@router.get("/coursereg/{module_code}")
def get_coursereg_analysis(
    module_code: str,
    sem: int = Query(1, ge=1, le=2),
    conn: psycopg2.extensions.connection = Depends(get_conn),
):
    """
    Return competition scores and estimated bid-success probabilities for every
    slot of a given module in the specified semester.
    Incorporates real platform-user demand as a dynamic signal.
    """
    module_code = module_code.upper()

    slots = nusmods_api.fetch_module_slots(module_code, sem)
    if slots is None:
        raise HTTPException(404, f"Module {module_code} not found")
    if not slots:
        raise HTTPException(404, f"{module_code} has no timetable data for Sem {sem}")

    demand_counts = _slot_demand_counts(module_code, sem, conn)
    analysis = _analyse_slots(slots, demand_counts)

    by_lt_out: dict = {}
    for lt, classes in analysis.items():
        by_lt_out[lt] = []
        for c in classes:
            probs = _round_probabilities(c["competition_score"])
            by_lt_out[lt].append({
                "class_no":            c["class_no"],
                "lesson_type":         lt,
                "capacity":            c["capacity"],
                "competition_score":   c["competition_score"],
                "platform_demand":     c["platform_demand"],
                "recommendation":      _recommendation(c["competition_score"]),
                "round_probabilities": probs,
                "slots": [
                    {
                        "day":       s.get("day"),
                        "startTime": s.get("startTime"),
                        "endTime":   s.get("endTime"),
                        "venue":     s.get("venue"),
                    }
                    for s in c["slots"]
                ],
            })

    return {
        "module_code": module_code,
        "sem": sem,
        "note": (
            "Estimates based on slot capacity, timing desirability, and live platform-user "
            "demand. Actual success also depends on your priority round and cohort size."
        ),
        "by_lesson_type": by_lt_out,
    }
