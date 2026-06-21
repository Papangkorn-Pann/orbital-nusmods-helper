import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent / "database" / "modules.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)

    # ── existing ──────────────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS module_scores (
            module_code TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            module_credits INTEGER,
            department TEXT,
            difficulty_score REAL,
            recommend_score REAL,
            top_positive_comment_message TEXT,
            top_positive_comment_likes INTEGER,
            top_neutral_comment_message TEXT,
            top_neutral_comment_likes INTEGER,
            top_negative_comment_message TEXT,
            top_negative_comment_likes INTEGER,
            comment_count INTEGER,
            expected_gpa REAL,
            actual_gpa REAL
        )
    """)

    # ── users ─────────────────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            display_name TEXT DEFAULT 'Anonymous',
            faculty TEXT,
            year_of_study INTEGER,
            course TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── timetable ─────────────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS timetable_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            module_code TEXT NOT NULL,
            lesson_type TEXT NOT NULL,
            class_no TEXT NOT NULL,
            sem INTEGER DEFAULT 1,
            UNIQUE(user_id, module_code, lesson_type, sem),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # ── study timer ───────────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration_seconds INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS study_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL,
            invite_code TEXT UNIQUE NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS study_group_members (
            group_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            joined_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (group_id, user_id)
        )
    """)

    # ── study plan (SM-2 cards) ───────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS study_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            module_code TEXT NOT NULL,
            topic TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            next_review_date TEXT NOT NULL,
            interval_days INTEGER DEFAULT 1,
            easiness_factor REAL DEFAULT 2.5,
            repetitions INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # ── timetable shares ──────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS timetable_shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            sem INTEGER NOT NULL,
            module_codes_json TEXT NOT NULL,
            selections_json TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── new module analysis columns (silently skip if already present) ──────────
    for col_sql in [
        "ALTER TABLE module_scores ADD COLUMN summary TEXT",
        "ALTER TABLE module_scores ADD COLUMN grade_thresholds_json TEXT",
        "ALTER TABLE module_scores ADD COLUMN workload_json TEXT",
        "ALTER TABLE module_scores ADD COLUMN prerequisite TEXT",
        "ALTER TABLE module_scores ADD COLUMN preclusion TEXT",
        # v1 = pipeline includes workload + prereq; 0 = legacy cached entry
        "ALTER TABLE module_scores ADD COLUMN analysis_version INTEGER DEFAULT 0",
        "ALTER TABLE module_scores ADD COLUMN grade_pairs_json TEXT",
    ]:
        try:
            conn.execute(col_sql)
        except Exception:
            pass

    # ── streak columns (silently skip if already present) ─────────────────────
    for col_sql in [
        "ALTER TABLE users ADD COLUMN review_streak INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN last_review_date TEXT",
    ]:
        try:
            conn.execute(col_sql)
        except Exception:
            pass

    conn.commit()
    conn.close()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── original module cache helpers ─────────────────────────────────────────────

def get_cached_module(module_code: str, conn: sqlite3.Connection):
    row = conn.execute(
        "SELECT * FROM module_scores WHERE module_code = ?",
        (module_code.upper(),)
    ).fetchone()
    if row is None:
        return None
    return dict(row)


def save_module_data(module_code, title, description, module_credits, department,
                     difficulty_score, recommend_score,
                     top_positive_comment, top_neutral_comment, top_negative_comment,
                     comment_count, expected_gpa, actual_gpa,
                     summary, grade_thresholds_json, grade_pairs_json,
                     workload_json, prerequisite, preclusion, conn):
    conn.execute("""
        INSERT OR REPLACE INTO module_scores
        (module_code, title, description, module_credits, department,
         difficulty_score, recommend_score,
         top_positive_comment_message, top_positive_comment_likes,
         top_neutral_comment_message,  top_neutral_comment_likes,
         top_negative_comment_message, top_negative_comment_likes,
         comment_count, expected_gpa, actual_gpa,
         summary, grade_thresholds_json, grade_pairs_json, workload_json, prerequisite, preclusion,
         analysis_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 2)
    """, (
        module_code, title, description, module_credits, department,
        difficulty_score, recommend_score,
        top_positive_comment["message"], top_positive_comment["likes"],
        top_neutral_comment["message"],  top_neutral_comment["likes"],
        top_negative_comment["message"], top_negative_comment["likes"],
        comment_count, expected_gpa, actual_gpa,
        summary, grade_thresholds_json, grade_pairs_json, workload_json, prerequisite, preclusion,
    ))
    conn.commit()


def get_session_history(user_id: str, days: int, conn):
    """Return per-day study totals for the last N days."""
    rows = conn.execute("""
        SELECT date(start_time, 'localtime') AS day,
               SUM(duration_seconds) AS seconds
        FROM study_sessions
        WHERE user_id = ?
          AND duration_seconds IS NOT NULL
          AND start_time >= datetime('now', ?, 'localtime')
        GROUP BY date(start_time, 'localtime')
        ORDER BY day
    """, (user_id, f'-{days} days')).fetchall()
    return [{"day": r["day"], "seconds": r["seconds"]} for r in rows]


# ── users ─────────────────────────────────────────────────────────────────────

def create_user(user_id: str, display_name: str, faculty: str,
                year_of_study: int, course: str, conn: sqlite3.Connection):
    conn.execute("""
        INSERT OR IGNORE INTO users (user_id, display_name, faculty, year_of_study, course)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, display_name, faculty, year_of_study, course))
    conn.commit()


def get_user(user_id: str, conn: sqlite3.Connection):
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def update_user(user_id: str, display_name: str, faculty: str,
                year_of_study: int, course: str, conn: sqlite3.Connection):
    conn.execute("""
        UPDATE users SET display_name=?, faculty=?, year_of_study=?, course=?
        WHERE user_id=?
    """, (display_name, faculty, year_of_study, course, user_id))
    conn.commit()


# ── timetable ─────────────────────────────────────────────────────────────────

def upsert_timetable_slot(user_id, module_code, lesson_type, class_no, sem, conn):
    conn.execute("""
        INSERT INTO timetable_slots (user_id, module_code, lesson_type, class_no, sem)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, module_code, lesson_type, sem)
        DO UPDATE SET class_no = excluded.class_no
    """, (user_id, module_code.upper(), lesson_type, class_no, sem))
    conn.commit()


def delete_timetable_module(user_id, module_code, sem, conn):
    conn.execute("""
        DELETE FROM timetable_slots
        WHERE user_id=? AND module_code=? AND sem=?
    """, (user_id, module_code.upper(), sem))
    conn.commit()


def get_user_timetable(user_id, sem, conn):
    rows = conn.execute("""
        SELECT module_code, lesson_type, class_no
        FROM timetable_slots
        WHERE user_id=? AND sem=?
    """, (user_id, sem)).fetchall()
    return [dict(r) for r in rows]


# ── study timer ───────────────────────────────────────────────────────────────

def create_session(user_id, start_time, conn):
    cur = conn.execute(
        "INSERT INTO study_sessions (user_id, start_time) VALUES (?, ?)",
        (user_id, start_time)
    )
    conn.commit()
    return cur.lastrowid


def complete_session(session_id, end_time, duration_seconds, conn):
    conn.execute("""
        UPDATE study_sessions SET end_time=?, duration_seconds=?
        WHERE id=?
    """, (end_time, duration_seconds, session_id))
    conn.commit()


def get_user_timer_stats(user_id, conn):
    today = conn.execute("""
        SELECT COALESCE(SUM(duration_seconds), 0)
        FROM study_sessions
        WHERE user_id=? AND date(start_time)=date('now') AND duration_seconds IS NOT NULL
    """, (user_id,)).fetchone()[0]

    week = conn.execute("""
        SELECT COALESCE(SUM(duration_seconds), 0)
        FROM study_sessions
        WHERE user_id=? AND date(start_time)>=date('now','-6 days') AND duration_seconds IS NOT NULL
    """, (user_id,)).fetchone()[0]

    return {"today_seconds": today, "week_seconds": week}


def get_leaderboard(faculty, year_of_study, course, conn, limit=10):
    conditions = []
    params: list = []
    if faculty:
        conditions.append("u.faculty = ?")
        params.append(faculty)
    if year_of_study:
        conditions.append("u.year_of_study = ?")
        params.append(int(year_of_study))
    if course:
        conditions.append("LOWER(u.course) LIKE ?")
        params.append(f"%{course.lower()}%")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)

    rows = conn.execute(f"""
        SELECT u.user_id, u.display_name, u.faculty, u.year_of_study, u.course,
               COALESCE(SUM(s.duration_seconds), 0) AS week_seconds
        FROM users u
        LEFT JOIN study_sessions s
          ON u.user_id=s.user_id
         AND date(s.start_time) >= date('now', '-6 days')
         AND s.duration_seconds IS NOT NULL
        {where}
        GROUP BY u.user_id
        ORDER BY week_seconds DESC
        LIMIT ?
    """, params).fetchall()
    return [dict(r) for r in rows]


# ── study groups ──────────────────────────────────────────────────────────────

def create_group(group_name, invite_code, created_by, conn):
    cur = conn.execute(
        "INSERT INTO study_groups (group_name, invite_code, created_by) VALUES (?, ?, ?)",
        (group_name, invite_code, created_by)
    )
    conn.execute(
        "INSERT INTO study_group_members (group_id, user_id) VALUES (?, ?)",
        (cur.lastrowid, created_by)
    )
    conn.commit()
    return cur.lastrowid


def get_group_by_code(invite_code, conn):
    row = conn.execute(
        "SELECT * FROM study_groups WHERE invite_code=?", (invite_code,)
    ).fetchone()
    return dict(row) if row else None


def join_group(group_id, user_id, conn):
    conn.execute("""
        INSERT OR IGNORE INTO study_group_members (group_id, user_id) VALUES (?, ?)
    """, (group_id, user_id))
    conn.commit()


def leave_group(invite_code: str, user_id: str, conn):
    conn.execute("""
        DELETE FROM study_group_members
        WHERE group_id = (SELECT id FROM study_groups WHERE invite_code=?)
          AND user_id=?
    """, (invite_code, user_id))
    conn.commit()


def get_group_leaderboard(group_id, conn):
    rows = conn.execute("""
        SELECT u.user_id, u.display_name,
               COALESCE(SUM(s.duration_seconds), 0) AS week_seconds
        FROM study_group_members m
        JOIN users u ON m.user_id=u.user_id
        LEFT JOIN study_sessions s
          ON u.user_id=s.user_id
          AND date(s.start_time)>=date('now','-6 days')
          AND s.duration_seconds IS NOT NULL
        WHERE m.group_id=?
        GROUP BY u.user_id
        ORDER BY week_seconds DESC
    """, (group_id,)).fetchall()
    return [dict(r) for r in rows]


# ── study plan ────────────────────────────────────────────────────────────────

def create_study_card(user_id, module_code, topic, exam_date,
                      next_review_date, conn):
    cur = conn.execute("""
        INSERT INTO study_cards
          (user_id, module_code, topic, exam_date, next_review_date)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, module_code.upper(), topic, exam_date, next_review_date))
    conn.commit()
    return cur.lastrowid


def get_due_cards(user_id, today_str, conn):
    rows = conn.execute("""
        SELECT * FROM study_cards
        WHERE user_id=? AND next_review_date<=?
        ORDER BY next_review_date ASC
    """, (user_id, today_str)).fetchall()
    return [dict(r) for r in rows]


def get_upcoming_cards(user_id, conn):
    rows = conn.execute("""
        SELECT * FROM study_cards
        WHERE user_id=?
        ORDER BY next_review_date ASC
    """, (user_id,)).fetchall()
    return [dict(r) for r in rows]


def update_study_card(card_id, interval_days, easiness_factor,
                      repetitions, next_review_date, conn):
    conn.execute("""
        UPDATE study_cards
        SET interval_days=?, easiness_factor=?, repetitions=?, next_review_date=?
        WHERE id=?
    """, (interval_days, easiness_factor, repetitions, next_review_date, card_id))
    conn.commit()


def get_card(card_id, conn):
    row = conn.execute(
        "SELECT * FROM study_cards WHERE id=?", (card_id,)
    ).fetchone()
    return dict(row) if row else None


# ── timetable shares ──────────────────────────────────────────────────────────

def create_timetable_share(token: str, user_id: str, sem: int,
                           module_codes_json: str, selections_json: str,
                           conn: sqlite3.Connection):
    conn.execute("""
        INSERT INTO timetable_shares
            (token, user_id, sem, module_codes_json, selections_json)
        VALUES (?, ?, ?, ?, ?)
    """, (token, user_id, sem, module_codes_json, selections_json))
    conn.commit()


def get_timetable_share(token: str, conn: sqlite3.Connection):
    row = conn.execute(
        "SELECT * FROM timetable_shares WHERE token=? AND created_at >= datetime('now', '-30 days')",
        (token,)
    ).fetchone()
    return dict(row) if row else None


# ── study card deletion ───────────────────────────────────────────────────────

def delete_study_card(card_id: int, conn: sqlite3.Connection):
    conn.execute("DELETE FROM study_cards WHERE id=?", (card_id,))
    conn.commit()


def delete_exam_cards(user_id: str, module_code: str, conn: sqlite3.Connection):
    conn.execute(
        "DELETE FROM study_cards WHERE user_id=? AND module_code=?",
        (user_id, module_code),
    )
    conn.commit()


# ── streak tracking ───────────────────────────────────────────────────────────

def update_user_streak(user_id: str, streak: int, last_date: str,
                       conn: sqlite3.Connection):
    conn.execute("""
        UPDATE users SET review_streak=?, last_review_date=?
        WHERE user_id=?
    """, (streak, last_date, user_id))
    conn.commit()
