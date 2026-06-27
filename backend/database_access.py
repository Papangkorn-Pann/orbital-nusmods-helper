import psycopg2
import psycopg2.extras

DATABASE_URL = "postgresql://postgres:Vhallfolks55@db.dzmtwhiuqvlrlqbfvmvw.supabase.co:5432/postgres"


def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            display_name TEXT DEFAULT 'Anonymous',
            faculty TEXT,
            year_of_study INTEGER,
            course TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            email TEXT,
            picture TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS timetable_slots (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            module_code TEXT NOT NULL,
            lesson_type TEXT NOT NULL,
            class_no TEXT NOT NULL,
            sem INTEGER DEFAULT 1,
            UNIQUE(user_id, module_code, lesson_type, sem),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            start_time TIMESTAMPTZ NOT NULL,
            end_time TIMESTAMPTZ,
            duration_seconds INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS study_groups (
            id SERIAL PRIMARY KEY,
            group_name TEXT NOT NULL,
            invite_code TEXT UNIQUE NOT NULL,
            created_by TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS study_group_members (
            group_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            joined_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY (group_id, user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS study_cards (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            module_code TEXT NOT NULL,
            topic TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            next_review_date TEXT NOT NULL,
            interval_days INTEGER DEFAULT 1,
            easiness_factor REAL DEFAULT 2.5,
            repetitions INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS timetable_shares (
            id SERIAL PRIMARY KEY,
            token TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            sem INTEGER NOT NULL,
            module_codes_json TEXT NOT NULL,
            selections_json TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Use savepoints to silently skip columns that already exist
    for col_sql in [
        "ALTER TABLE module_scores ADD COLUMN summary TEXT",
        "ALTER TABLE module_scores ADD COLUMN grade_thresholds_json TEXT",
        "ALTER TABLE module_scores ADD COLUMN workload_json TEXT",
        "ALTER TABLE module_scores ADD COLUMN prerequisite TEXT",
        "ALTER TABLE module_scores ADD COLUMN preclusion TEXT",
        "ALTER TABLE module_scores ADD COLUMN analysis_version INTEGER DEFAULT 0",
        "ALTER TABLE module_scores ADD COLUMN grade_pairs_json TEXT",
        "ALTER TABLE users ADD COLUMN review_streak INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN last_review_date TEXT",
    ]:
        try:
            cur.execute("SAVEPOINT sp")
            cur.execute(col_sql)
            cur.execute("RELEASE SAVEPOINT sp")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT sp")

    conn.commit()
    cur.close()
    conn.close()


def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


# ── module cache helpers ──────────────────────────────────────────────────────

def get_cached_module(module_code: str, conn: psycopg2.extensions.connection):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM module_scores WHERE module_code = %s",
        (module_code.upper(),)
    )
    row = cur.fetchone()
    return dict(row) if row else None


def save_module_data(module_code, title, description, module_credits, department,
                     difficulty_score, recommend_score,
                     top_positive_comment, top_neutral_comment, top_negative_comment,
                     comment_count, expected_gpa, actual_gpa,
                     summary, grade_thresholds_json, grade_pairs_json,
                     workload_json, prerequisite, preclusion, conn):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO module_scores
        (module_code, title, description, module_credits, department,
         difficulty_score, recommend_score,
         top_positive_comment_message, top_positive_comment_likes,
         top_neutral_comment_message,  top_neutral_comment_likes,
         top_negative_comment_message, top_negative_comment_likes,
         comment_count, expected_gpa, actual_gpa,
         summary, grade_thresholds_json, grade_pairs_json, workload_json, prerequisite, preclusion,
         analysis_version)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 2)
        ON CONFLICT (module_code) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            module_credits = EXCLUDED.module_credits,
            department = EXCLUDED.department,
            difficulty_score = EXCLUDED.difficulty_score,
            recommend_score = EXCLUDED.recommend_score,
            top_positive_comment_message = EXCLUDED.top_positive_comment_message,
            top_positive_comment_likes = EXCLUDED.top_positive_comment_likes,
            top_neutral_comment_message = EXCLUDED.top_neutral_comment_message,
            top_neutral_comment_likes = EXCLUDED.top_neutral_comment_likes,
            top_negative_comment_message = EXCLUDED.top_negative_comment_message,
            top_negative_comment_likes = EXCLUDED.top_negative_comment_likes,
            comment_count = EXCLUDED.comment_count,
            expected_gpa = EXCLUDED.expected_gpa,
            actual_gpa = EXCLUDED.actual_gpa,
            summary = EXCLUDED.summary,
            grade_thresholds_json = EXCLUDED.grade_thresholds_json,
            grade_pairs_json = EXCLUDED.grade_pairs_json,
            workload_json = EXCLUDED.workload_json,
            prerequisite = EXCLUDED.prerequisite,
            preclusion = EXCLUDED.preclusion,
            analysis_version = 2
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
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT DATE(start_time) AS day,
               SUM(duration_seconds) AS seconds
        FROM study_sessions
        WHERE user_id = %s
          AND duration_seconds IS NOT NULL
          AND start_time >= NOW() - INTERVAL '1 day' * %s
        GROUP BY DATE(start_time)
        ORDER BY day
    """, (user_id, days))
    rows = cur.fetchall()
    return [{"day": str(r["day"]), "seconds": r["seconds"]} for r in rows]


# ── users ─────────────────────────────────────────────────────────────────────

def create_user(user_id: str, display_name: str, faculty: str,
                year_of_study: int, course: str, conn: psycopg2.extensions.connection):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (user_id, display_name, faculty, year_of_study, course)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING
    """, (user_id, display_name, faculty, year_of_study, course))
    conn.commit()


def get_user(user_id: str, conn: psycopg2.extensions.connection):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def update_user(user_id: str, display_name: str, faculty: str,
                year_of_study: int, course: str, conn: psycopg2.extensions.connection):
    cur = conn.cursor()
    cur.execute("""
        UPDATE users SET display_name=%s, faculty=%s, year_of_study=%s, course=%s
        WHERE user_id=%s
    """, (display_name, faculty, year_of_study, course, user_id))
    conn.commit()


# ── timetable ─────────────────────────────────────────────────────────────────

def upsert_timetable_slot(user_id, module_code, lesson_type, class_no, sem, conn):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO timetable_slots (user_id, module_code, lesson_type, class_no, sem)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT(user_id, module_code, lesson_type, sem)
        DO UPDATE SET class_no = EXCLUDED.class_no
    """, (user_id, module_code.upper(), lesson_type, class_no, sem))
    conn.commit()


def delete_timetable_module(user_id, module_code, sem, conn):
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM timetable_slots
        WHERE user_id=%s AND module_code=%s AND sem=%s
    """, (user_id, module_code.upper(), sem))
    conn.commit()


def get_user_timetable(user_id, sem, conn):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT module_code, lesson_type, class_no
        FROM timetable_slots
        WHERE user_id=%s AND sem=%s
    """, (user_id, sem))
    rows = cur.fetchall()
    return [dict(r) for r in rows]


# ── study timer ───────────────────────────────────────────────────────────────

def create_session(user_id, start_time, conn):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO study_sessions (user_id, start_time) VALUES (%s, %s) RETURNING id",
        (user_id, start_time)
    )
    conn.commit()
    return cur.fetchone()[0]


def complete_session(session_id, end_time, duration_seconds, conn):
    cur = conn.cursor()
    cur.execute("""
        UPDATE study_sessions SET end_time=%s, duration_seconds=%s
        WHERE id=%s
    """, (end_time, duration_seconds, session_id))
    conn.commit()


def get_user_timer_stats(user_id, conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(duration_seconds), 0)
        FROM study_sessions
        WHERE user_id=%s AND DATE(start_time)=CURRENT_DATE AND duration_seconds IS NOT NULL
    """, (user_id,))
    today = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(duration_seconds), 0)
        FROM study_sessions
        WHERE user_id=%s AND DATE(start_time)>=CURRENT_DATE - INTERVAL '6 days' AND duration_seconds IS NOT NULL
    """, (user_id,))
    week = cur.fetchone()[0]

    return {"today_seconds": today, "week_seconds": week}


def get_leaderboard(faculty, year_of_study, course, conn, limit=10):
    conditions = []
    params: list = []
    if faculty:
        conditions.append("u.faculty = %s")
        params.append(faculty)
    if year_of_study:
        conditions.append("u.year_of_study = %s")
        params.append(int(year_of_study))
    if course:
        conditions.append("LOWER(u.course) LIKE %s")
        params.append(f"%{course.lower()}%")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"""
        SELECT u.user_id, u.display_name, u.faculty, u.year_of_study, u.course,
               COALESCE(SUM(s.duration_seconds), 0) AS week_seconds
        FROM users u
        LEFT JOIN study_sessions s
          ON u.user_id=s.user_id
         AND DATE(s.start_time) >= CURRENT_DATE - INTERVAL '6 days'
         AND s.duration_seconds IS NOT NULL
        {where}
        GROUP BY u.user_id
        ORDER BY week_seconds DESC
        LIMIT %s
    """, params)
    rows = cur.fetchall()
    return [dict(r) for r in rows]


# ── study groups ──────────────────────────────────────────────────────────────

def create_group(group_name, invite_code, created_by, conn):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO study_groups (group_name, invite_code, created_by) VALUES (%s, %s, %s) RETURNING id",
        (group_name, invite_code, created_by)
    )
    group_id = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO study_group_members (group_id, user_id) VALUES (%s, %s)",
        (group_id, created_by)
    )
    conn.commit()
    return group_id


def get_group_by_code(invite_code, conn):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM study_groups WHERE invite_code=%s", (invite_code,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


def join_group(group_id, user_id, conn):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO study_group_members (group_id, user_id) VALUES (%s, %s)
        ON CONFLICT (group_id, user_id) DO NOTHING
    """, (group_id, user_id))
    conn.commit()


def leave_group(invite_code: str, user_id: str, conn):
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM study_group_members
        WHERE group_id = (SELECT id FROM study_groups WHERE invite_code=%s)
          AND user_id=%s
    """, (invite_code, user_id))
    conn.commit()


def get_group_leaderboard(group_id, conn):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT u.user_id, u.display_name,
               COALESCE(SUM(s.duration_seconds), 0) AS week_seconds
        FROM study_group_members m
        JOIN users u ON m.user_id=u.user_id
        LEFT JOIN study_sessions s
          ON u.user_id=s.user_id
          AND DATE(s.start_time) >= CURRENT_DATE - INTERVAL '6 days'
          AND s.duration_seconds IS NOT NULL
        WHERE m.group_id=%s
        GROUP BY u.user_id
        ORDER BY week_seconds DESC
    """, (group_id,))
    rows = cur.fetchall()
    return [dict(r) for r in rows]


# ── study plan ────────────────────────────────────────────────────────────────

def create_study_card(user_id, module_code, topic, exam_date,
                      next_review_date, conn):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO study_cards
          (user_id, module_code, topic, exam_date, next_review_date)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (user_id, module_code.upper(), topic, exam_date, next_review_date))
    conn.commit()
    return cur.fetchone()[0]


def get_due_cards(user_id, today_str, conn):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT * FROM study_cards
        WHERE user_id=%s AND next_review_date<=%s
        ORDER BY next_review_date ASC
    """, (user_id, today_str))
    rows = cur.fetchall()
    return [dict(r) for r in rows]


def get_upcoming_cards(user_id, conn):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT * FROM study_cards
        WHERE user_id=%s
        ORDER BY next_review_date ASC
    """, (user_id,))
    rows = cur.fetchall()
    return [dict(r) for r in rows]


def update_study_card(card_id, interval_days, easiness_factor,
                      repetitions, next_review_date, conn):
    cur = conn.cursor()
    cur.execute("""
        UPDATE study_cards
        SET interval_days=%s, easiness_factor=%s, repetitions=%s, next_review_date=%s
        WHERE id=%s
    """, (interval_days, easiness_factor, repetitions, next_review_date, card_id))
    conn.commit()


def get_card(card_id, conn):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT * FROM study_cards WHERE id=%s
    """, (card_id,))
    row = cur.fetchone()
    return dict(row) if row else None


# ── timetable shares ──────────────────────────────────────────────────────────

def create_timetable_share(token: str, user_id: str, sem: int,
                           module_codes_json: str, selections_json: str,
                           conn: psycopg2.extensions.connection):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO timetable_shares
            (token, user_id, sem, module_codes_json, selections_json)
        VALUES (%s, %s, %s, %s, %s)
    """, (token, user_id, sem, module_codes_json, selections_json))
    conn.commit()


def get_timetable_share(token: str, conn: psycopg2.extensions.connection):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM timetable_shares WHERE token=%s AND created_at >= NOW() - INTERVAL '30 days'",
        (token,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


# ── study card deletion ───────────────────────────────────────────────────────

def delete_study_card(card_id: int, conn: psycopg2.extensions.connection):
    cur = conn.cursor()
    cur.execute("DELETE FROM study_cards WHERE id=%s", (card_id,))
    conn.commit()


def delete_exam_cards(user_id: str, module_code: str, conn: psycopg2.extensions.connection):
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM study_cards WHERE user_id=%s AND module_code=%s",
        (user_id, module_code),
    )
    conn.commit()


# ── streak tracking ───────────────────────────────────────────────────────────

def update_user_streak(user_id: str, streak: int, last_date: str,
                       conn: psycopg2.extensions.connection):
    cur = conn.cursor()
    cur.execute("""
        UPDATE users SET review_streak=%s, last_review_date=%s
        WHERE user_id=%s
    """, (streak, last_date, user_id))
    conn.commit()
