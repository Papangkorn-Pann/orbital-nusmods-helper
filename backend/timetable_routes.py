import json
import secrets
import sqlite3
import uuid
from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel
import api
import database_access
import timetable_generator

# ── iCal helpers ──────────────────────────────────────────────────────────────

# AY2025-2026 teaching week start dates (Monday of week 1)
_SEM_STARTS = {1: date(2025, 8, 11), 2: date(2026, 1, 12)}
# Recess week falls between academic week 6 and 7 (skip one calendar week)
_DAY_OFFSET = {"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,"Friday":4,"Saturday":5,"Sunday":6}

def _week_monday(sem: int, week: int) -> date:
    base = _SEM_STARTS.get(sem, _SEM_STARTS[1])
    # Academic weeks 1-6 are contiguous; recess after week 6 adds +1 calendar week
    offset = week - 1 if week <= 6 else week  # +1 skips recess week
    return base + timedelta(weeks=offset)

def _slots_to_ical(rendered_slots: list, sem: int) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//NUSMods Helper//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for slot in rendered_slots:
        day_off = _DAY_OFFSET.get(slot.get("day","Monday"), 0)
        st = slot.get("startTime","0800")
        et = slot.get("endTime","0900")
        sh, sm = int(st[:2]), int(st[2:])
        eh, em = int(et[:2]), int(et[2:])
        weeks = slot.get("weeks", list(range(1,14)))
        mc    = slot.get("moduleCode","")
        lt    = slot.get("lessonType","")
        cn    = slot.get("classNo","")
        venue = slot.get("venue","")
        for wk in weeks:
            d = _week_monday(sem, wk) + timedelta(days=day_off)
            uid = str(uuid.uuid4()).replace("-","")
            lines += [
                "BEGIN:VEVENT",
                f"UID:{uid}@nusmods-helper",
                f"DTSTART:{d.strftime('%Y%m%d')}T{sh:02d}{sm:02d}00",
                f"DTEND:{d.strftime('%Y%m%d')}T{eh:02d}{em:02d}00",
                f"SUMMARY:{mc} {lt} [{cn}]",
                f"LOCATION:{venue}",
                "END:VEVENT",
            ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)

router = APIRouter(tags=["timetable"])


def get_conn():
    conn = database_access.get_connection()
    try:
        yield conn
    finally:
        conn.close()


class SlotSelection(BaseModel):
    module_code: str
    lesson_type: str
    class_no: str
    sem: int = 1


class GenerateRequest(BaseModel):
    module_codes: List[str]
    sem: int = 1
    preferences: dict = {}
    top_n: int = 5


class ShareRequest(BaseModel):
    user_id: str
    sem: int = 1
    module_codes: Optional[List[str]] = None


# ── module search ──────────────────────────────────────────────────────────────

@router.get("/modules")
def search_modules(q: str = Query("", min_length=0), limit: int = 10):
    results = api.search_modules(q, limit)
    return results


# ── timetable slot data (from NUSMods) ────────────────────────────────────────

@router.get("/modules/{module_code}/slots")
def get_module_slots(module_code: str, sem: int = 1):
    slots = api.fetch_module_slots(module_code.upper(), sem)
    if slots is None:
        raise HTTPException(status_code=404, detail="Module not found")
    # Group by lessonType for easier consumption on the frontend
    grouped: dict[str, list] = {}
    for slot in slots:
        lt = slot["lessonType"]
        grouped.setdefault(lt, [])
        grouped[lt].append(slot)
    return {"module_code": module_code.upper(), "sem": sem, "by_lesson_type": grouped}


# ── user timetable CRUD ────────────────────────────────────────────────────────

@router.get("/timetable/{user_id}")
def get_timetable(user_id: str, sem: int = 1, conn: sqlite3.Connection = Depends(get_conn)):
    """
    Returns the user's saved slot selections together with the full
    NUSMods slot details so the frontend can render the grid immediately.
    """
    selections = database_access.get_user_timetable(user_id, sem, conn)

    # Build a set of (module_code, lesson_type, class_no) for quick lookup
    selected_map: dict[str, dict[str, str]] = {}
    module_codes = set()
    for s in selections:
        mc = s["module_code"]
        module_codes.add(mc)
        selected_map.setdefault(mc, {})[s["lesson_type"]] = s["class_no"]

    # Fetch slot details from NUSMods and filter to only selected slots
    rendered_slots = []
    for mc in module_codes:
        slots = api.fetch_module_slots(mc, sem) or []
        lesson_map = selected_map.get(mc, {})
        for slot in slots:
            chosen = lesson_map.get(slot["lessonType"])
            if chosen and slot["classNo"] == chosen:
                rendered_slots.append({**slot, "moduleCode": mc})

    return {
        "user_id": user_id,
        "sem": sem,
        "selections": selections,
        "rendered_slots": rendered_slots,
    }


@router.put("/timetable/{user_id}/slots")
def update_slot(user_id: str, body: SlotSelection,
                conn: sqlite3.Connection = Depends(get_conn)):
    """Add or change a module slot selection."""
    # Ensure user exists (create a stub if first visit)
    if not database_access.get_user(user_id, conn):
        database_access.create_user(user_id, "Anonymous", None, None, None, conn)

    database_access.upsert_timetable_slot(
        user_id, body.module_code, body.lesson_type, body.class_no, body.sem, conn
    )
    return {"ok": True}


@router.get("/timetable/{user_id}/export.ics")
def export_timetable_ical(user_id: str, sem: int = 1,
                           conn: sqlite3.Connection = Depends(get_conn)):
    """Download the user's timetable as an iCalendar (.ics) file."""
    timetable = get_timetable(user_id, sem, conn)
    ical = _slots_to_ical(timetable["rendered_slots"], sem)
    return Response(
        content=ical,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=timetable-sem{sem}.ics"},
    )


@router.delete("/timetable/{user_id}/modules/{module_code}")
def remove_module(user_id: str, module_code: str, sem: int = 1,
                  conn: sqlite3.Connection = Depends(get_conn)):
    database_access.delete_timetable_module(user_id, module_code.upper(), sem, conn)
    return {"ok": True}


# ── timetable generation ──────────────────────────────────────────────────────

@router.post("/timetable/generate")
def generate_timetable(body: GenerateRequest):
    """Run backtracking to find the top N conflict-free timetables."""
    if not body.module_codes:
        raise HTTPException(400, "No module codes provided")
    codes = [c.upper() for c in body.module_codes]

    # Compute peer slot demand so popular slots get down-weighted in scoring
    demand_conn = database_access.get_connection()
    try:
        rows = demand_conn.execute("""
            SELECT module_code, lesson_type, class_no, COUNT(*) as cnt
            FROM timetable_slots WHERE sem=?
            GROUP BY module_code, lesson_type, class_no
        """, (body.sem,)).fetchall()
        slot_demand = {
            f"{r['module_code']}|{r['lesson_type']}|{r['class_no']}": r['cnt']
            for r in rows
        }
    finally:
        demand_conn.close()

    try:
        results = timetable_generator.generate_timetables(
            codes, body.sem, body.preferences, min(body.top_n, 10),
            slot_demand=slot_demand,
        )
    except Exception as exc:
        raise HTTPException(500, str(exc))
    return {"count": len(results), "timetables": results}


# ── timetable sharing ─────────────────────────────────────────────────────────

@router.post("/timetable/share")
def share_timetable(body: ShareRequest,
                    conn: sqlite3.Connection = Depends(get_conn)):
    """Snapshot the user's current selections and return a shareable token."""
    all_selections = database_access.get_user_timetable(body.user_id, body.sem, conn)

    if body.module_codes:
        codes = [c.upper() for c in body.module_codes]
        filtered = [s for s in all_selections if s["module_code"] in codes]
    else:
        filtered = all_selections
        codes = list({s["module_code"] for s in all_selections})

    token = secrets.token_urlsafe(9)
    database_access.create_timetable_share(
        token, body.user_id, body.sem,
        json.dumps(codes), json.dumps(filtered), conn,
    )
    return {"token": token, "url": f"/shared/{token}"}


@router.get("/timetable/shared/{token}")
def get_shared_timetable(token: str,
                         conn: sqlite3.Connection = Depends(get_conn)):
    """Return a previously shared timetable snapshot (read-only)."""
    share = database_access.get_timetable_share(token, conn)
    if not share:
        raise HTTPException(404, "Share link not found")

    module_codes = json.loads(share["module_codes_json"])
    selections   = json.loads(share["selections_json"])
    sem          = share["sem"]

    selected_map: dict = {}
    for s in selections:
        selected_map.setdefault(s["module_code"], {})[s["lesson_type"]] = s["class_no"]

    rendered_slots = []
    for mc in module_codes:
        slots = api.fetch_module_slots(mc, sem) or []
        lesson_map = selected_map.get(mc, {})
        for slot in slots:
            chosen = lesson_map.get(slot["lessonType"])
            if chosen and slot["classNo"] == chosen:
                rendered_slots.append({**slot, "moduleCode": mc})

    return {
        "token": token,
        "sem": sem,
        "module_codes": module_codes,
        "selections": selections,
        "rendered_slots": rendered_slots,
        "created_at": share["created_at"],
    }
