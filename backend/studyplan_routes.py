import sqlite3
from datetime import date, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List
import database_access
import sm2

router = APIRouter(tags=["studyplan"])


def get_conn():
    conn = database_access.get_connection()
    try:
        yield conn
    finally:
        conn.close()


class AddExamRequest(BaseModel):
    user_id: str
    module_code: str
    topics: List[str]
    exam_date: str   # YYYY-MM-DD


class ReviewRequest(BaseModel):
    quality: int   # 0–5


# ── cards ─────────────────────────────────────────────────────────────────────

@router.post("/studyplan/exams")
def add_exam(body: AddExamRequest, conn: sqlite3.Connection = Depends(get_conn)):
    """Create one SM-2 card per topic, all starting review today."""
    if not database_access.get_user(body.user_id, conn):
        database_access.create_user(body.user_id, "Anonymous", None, None, None, conn)

    today = date.today().isoformat()
    created_ids = []
    for topic in body.topics:
        topic = topic.strip()
        if not topic:
            continue
        cid = database_access.create_study_card(
            body.user_id, body.module_code, topic, body.exam_date, today, conn
        )
        created_ids.append(cid)

    return {"created": len(created_ids), "card_ids": created_ids}


@router.get("/studyplan/{user_id}/today")
def get_today_cards(user_id: str, conn: sqlite3.Connection = Depends(get_conn)):
    today = date.today().isoformat()
    cards = database_access.get_due_cards(user_id, today, conn)
    return {"date": today, "due_count": len(cards), "cards": cards}


@router.put("/studyplan/cards/{card_id}/review")
def review_card(card_id: int, body: ReviewRequest,
                conn: sqlite3.Connection = Depends(get_conn)):
    if not 0 <= body.quality <= 5:
        raise HTTPException(400, "quality must be 0–5")

    card = database_access.get_card(card_id, conn)
    if not card:
        raise HTTPException(404, "Card not found")

    new_interval, new_ef, new_reps, next_date = sm2.review_card(
        card["interval_days"],
        card["easiness_factor"],
        card["repetitions"],
        body.quality,
    )
    database_access.update_study_card(card_id, new_interval, new_ef, new_reps, next_date, conn)

    # ── streak tracking ───────────────────────────────────────────────────────
    today_str = date.today().isoformat()
    user = database_access.get_user(card["user_id"], conn)
    if user:
        last_review   = user.get("last_review_date")
        streak        = user.get("review_streak") or 0
        yesterday_str = (date.today() - timedelta(days=1)).isoformat()
        if last_review == today_str:
            pass  # already reviewed today, keep current streak
        elif last_review == yesterday_str:
            streak += 1  # consecutive day → continue streak
        else:
            streak = 1   # gap → start fresh
        database_access.update_user_streak(card["user_id"], streak, today_str, conn)

    return {
        "card_id": card_id,
        "next_review_date": next_date,
        "interval_days": new_interval,
        "easiness_factor": round(new_ef, 3),
        "repetitions": new_reps,
    }


@router.get("/studyplan/{user_id}/schedule")
def get_schedule(user_id: str, conn: sqlite3.Connection = Depends(get_conn)):
    cards = database_access.get_upcoming_cards(user_id, conn)
    return {"cards": cards}


# ── delete endpoints ──────────────────────────────────────────────────────────

@router.delete("/studyplan/cards/{card_id}")
def delete_card(card_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    """Delete a single study card."""
    if not database_access.get_card(card_id, conn):
        raise HTTPException(404, "Card not found")
    database_access.delete_study_card(card_id, conn)
    return {"ok": True}


@router.delete("/studyplan/{user_id}/exams/{module_code}")
def delete_exam(user_id: str, module_code: str,
                conn: sqlite3.Connection = Depends(get_conn)):
    """Delete all study cards for a given module (exam)."""
    database_access.delete_exam_cards(user_id, module_code.upper(), conn)
    return {"ok": True}


# ── iCal export ───────────────────────────────────────────────────────────────

@router.get("/studyplan/{user_id}/export.ics")
def export_ical(user_id: str, conn: sqlite3.Connection = Depends(get_conn)):
    """Download all upcoming study cards as an RFC 5545 iCalendar file."""
    cards = database_access.get_upcoming_cards(user_id, conn)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//NUSMods Helper//Study Plan//EN",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:NUSMods Study Plan",
        "X-WR-TIMEZONE:Asia/Singapore",
    ]

    for card in cards:
        d_start = card["next_review_date"].replace("-", "")
        d_end   = (
            date.fromisoformat(card["next_review_date"]) + timedelta(days=1)
        ).strftime("%Y%m%d")
        safe_topic = (
            card["topic"].replace("\\", "\\\\").replace(",", "\\,").replace("\n", "\\n")
        )
        lines += [
            "BEGIN:VEVENT",
            f"DTSTART;VALUE=DATE:{d_start}",
            f"DTEND;VALUE=DATE:{d_end}",
            f"SUMMARY:Review: {card['module_code']} — {safe_topic}",
            f"DESCRIPTION:Exam on {card['exam_date']}. "
            f"Interval: {card['interval_days']} days. Reps: {card['repetitions']}.",
            f"UID:card-{card['id']}@nusmods-helper",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    return PlainTextResponse(
        "\r\n".join(lines),
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=study-plan.ics"},
    )
