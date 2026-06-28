#import sqlite3
import psycopg2
import psycopg2.extras
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
import database_access

router = APIRouter(tags=["timer"])


def get_conn():
    conn = database_access.get_connection()
    try:
        yield conn
    finally:
        conn.close()


# ── request models ────────────────────────────────────────────────────────────

class CreateUserRequest(BaseModel):
    user_id: str
    display_name: Optional[str] = "Anonymous"
    faculty: Optional[str] = None
    year_of_study: Optional[int] = None
    course: Optional[str] = None


class UpdateUserRequest(BaseModel):
    display_name: Optional[str] = None
    faculty: Optional[str] = None
    year_of_study: Optional[int] = None
    course: Optional[str] = None


class StartSessionRequest(BaseModel):
    user_id: str


class StopSessionRequest(BaseModel):
    end_time: str   # ISO-8601


class CreateGroupRequest(BaseModel):
    group_name: str
    user_id: str


class JoinGroupRequest(BaseModel):
    user_id: str


# ── users ─────────────────────────────────────────────────────────────────────

@router.post("/users")
def create_user(body: CreateUserRequest, conn: psycopg2.extensions.connection = Depends(get_conn)):
    database_access.create_user(
        body.user_id, body.display_name, body.faculty, body.year_of_study, body.course, conn
    )
    return {"ok": True, "user_id": body.user_id}


@router.get("/users/{user_id}")
def get_user(user_id: str, conn: psycopg2.extensions.connection = Depends(get_conn)):
    user = database_access.get_user(user_id, conn)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.put("/users/{user_id}")
def update_user(user_id: str, body: UpdateUserRequest,
                conn: psycopg2.extensions.connection = Depends(get_conn)):
    user = database_access.get_user(user_id, conn)
    if not user:
        raise HTTPException(404, "User not found")
    database_access.update_user(
        user_id,
        body.display_name or user["display_name"],
        body.faculty or user["faculty"],
        body.year_of_study or user["year_of_study"],
        body.course or user["course"],
        conn,
    )
    return {"ok": True}


# ── timer sessions ────────────────────────────────────────────────────────────

@router.post("/timer/sessions")
def start_session(body: StartSessionRequest, conn: psycopg2.extensions.connection = Depends(get_conn)):
    if not database_access.get_user(body.user_id, conn):
        database_access.create_user(body.user_id, "Anonymous", None, None, None, conn)
    start_time = datetime.now(timezone.utc).isoformat()
    session_id = database_access.create_session(body.user_id, start_time, conn)
    return {"session_id": session_id, "start_time": start_time}


@router.put("/timer/sessions/{session_id}")
def stop_session(session_id: int, body: StopSessionRequest,
                 conn: psycopg2.extensions.connection = Depends(get_conn)):
    # Calculate duration from stored start_time
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT start_time FROM study_sessions WHERE id=%s", (session_id,)
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Session not found")

    start_raw = row["start_time"]
    start_dt = start_raw if isinstance(start_raw, datetime) else \
               datetime.fromisoformat(str(start_raw).replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(body.end_time.replace("Z", "+00:00"))
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)
    duration = max(0, int((end_dt - start_dt).total_seconds()))

    database_access.complete_session(session_id, body.end_time, duration, conn)
    return {"ok": True, "duration_seconds": duration}


@router.get("/timer/stats/{user_id}")
def get_stats(user_id: str, conn: psycopg2.extensions.connection = Depends(get_conn)):
    return database_access.get_user_timer_stats(user_id, conn)


@router.get("/timer/history/{user_id}")
def get_history(user_id: str, days: int = 7,
                conn: psycopg2.extensions.connection = Depends(get_conn)):
    return database_access.get_session_history(user_id, days, conn)


@router.get("/timer/leaderboard")
def get_leaderboard(
    faculty: Optional[str] = Query(None),
    year:    Optional[int] = Query(None),
    course:  Optional[str] = Query(None),
    conn:    psycopg2.extensions.connection = Depends(get_conn),
):
    return database_access.get_leaderboard(faculty, year, course, conn)


# ── study groups ──────────────────────────────────────────────────────────────

@router.post("/groups")
def create_group(body: CreateGroupRequest, conn: psycopg2.extensions.connection = Depends(get_conn)):
    if not database_access.get_user(body.user_id, conn):
        database_access.create_user(body.user_id, "Anonymous", None, None, None, conn)
    invite_code = secrets.token_urlsafe(6).upper()
    group_id = database_access.create_group(body.group_name, invite_code, body.user_id, conn)
    return {"group_id": group_id, "invite_code": invite_code}


@router.post("/groups/{invite_code}/join")
def join_group(invite_code: str, body: JoinGroupRequest,
               conn: psycopg2.extensions.connection = Depends(get_conn)):
    group = database_access.get_group_by_code(invite_code, conn)
    if not group:
        raise HTTPException(404, "Group not found")
    if not database_access.get_user(body.user_id, conn):
        database_access.create_user(body.user_id, "Anonymous", None, None, None, conn)
    database_access.join_group(group["id"], body.user_id, conn)
    return {"ok": True, "group_id": group["id"], "group_name": group["group_name"]}


@router.get("/groups/{invite_code}")
def get_group(invite_code: str, conn: psycopg2.extensions.connection = Depends(get_conn)):
    group = database_access.get_group_by_code(invite_code, conn)
    if not group:
        raise HTTPException(404, "Group not found")
    leaderboard = database_access.get_group_leaderboard(group["id"], conn)
    return {**dict(group), "leaderboard": leaderboard}


@router.delete("/groups/{invite_code}/members/{user_id}")
def leave_group(invite_code: str, user_id: str,
                conn: psycopg2.extensions.connection = Depends(get_conn)):
    group = database_access.get_group_by_code(invite_code, conn)
    if not group:
        raise HTTPException(404, "Group not found")
    database_access.leave_group(invite_code, user_id, conn)
    return {"ok": True}
