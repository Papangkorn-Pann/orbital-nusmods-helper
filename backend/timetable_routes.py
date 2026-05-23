import sqlite3
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import api
import database_access

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


@router.delete("/timetable/{user_id}/modules/{module_code}")
def remove_module(user_id: str, module_code: str, sem: int = 1,
                  conn: sqlite3.Connection = Depends(get_conn)):
    database_access.delete_timetable_module(user_id, module_code.upper(), sem, conn)
    return {"ok": True}
