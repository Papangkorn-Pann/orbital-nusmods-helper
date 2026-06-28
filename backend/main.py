import re
import json
import nlp
import database_access
import api
#import sqlite3
import psycopg2

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import timetable_routes
import timer_routes
import studyplan_routes
import coursereg_routes
import auth_routes

database_access.init_db()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="NUSMods Helper API", version="0.2.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(timetable_routes.router)
app.include_router(timer_routes.router)
app.include_router(studyplan_routes.router)
app.include_router(coursereg_routes.router)
app.include_router(auth_routes.router)


MODULE_CODE_RE = re.compile(r'^[A-Z]{2,3}\d{4}[A-Z]{0,2}$')

#function to always close connection after work is done
def get_conn():
    conn = database_access.get_connection()
    try:
        yield conn
    finally:
        conn.close()

def return_formatter(module_code: str,
                     course_data: dict,
                     difficulty_score: float,
                     recommend_score: float,
                     comment_count: int,
                     expected_gpa: float,
                     actual_gpa: float,
                     summary: str,
                     grade_thresholds: dict,
                     grade_pairs: list,
                     workload: list,
                     prerequisite: str,
                     preclusion: str):
    return {
        "module": module_code,
        "title": course_data.get("title"),
        "description": course_data.get("description"),
        "module_credits": course_data.get("moduleCredit"),
        "department": course_data.get("department"),
        "difficulty_score": difficulty_score,
        "recommend_score": recommend_score,
        "comment_count": comment_count,
        "expected_gpa": expected_gpa,
        "actual_gpa": actual_gpa,
        "summary": summary,
        "grade_thresholds": grade_thresholds,
        "grade_pairs": grade_pairs,
        "workload": workload,
        "prerequisite": prerequisite,
        "preclusion": preclusion,
    }

@app.get("/course/{module_code}")
@limiter.limit("10/minute")
def get_course(request: Request, module_code: str, conn: psycopg2.extensions.connection = Depends(get_conn)):

    module_code = module_code.upper()

    if not MODULE_CODE_RE.match(module_code):
        raise HTTPException(status_code=400, detail="Invalid module code format")

    cached = database_access.get_cached_module(module_code, conn)

    # Only use cache if it already has the summary field (new schema)
    if cached and cached.get("analysis_version", 0) >= 3:
        print("Using cached result...")
        return {
            "module": module_code,
            "title": cached["title"],
            "description": cached["description"],
            "module_credits": cached["module_credits"],
            "department": cached["department"],
            "difficulty_score": cached["difficulty_score"],
            "recommend_score": cached["recommend_score"],
            "comment_count": cached["comment_count"],
            "expected_gpa": cached["expected_gpa"],
            "actual_gpa": cached["actual_gpa"],
            "summary": cached["summary"],
            "grade_thresholds": json.loads(cached["grade_thresholds_json"]) if cached.get("grade_thresholds_json") else None,
            "grade_pairs": json.loads(cached["grade_pairs_json"]) if cached.get("grade_pairs_json") else None,
            "workload": json.loads(cached["workload_json"]) if cached.get("workload_json") else None,
            "prerequisite": cached.get("prerequisite"),
            "preclusion": cached.get("preclusion"),
        }
    
    # Data is not yet cached — run Gemini analysis pipeline.

    #nusmods API Fetch
    course_data = api.fetch_nusmods(module_code)

    if course_data is None:
        raise HTTPException(status_code=404, detail="Invalid module code")

    #Disqus Fetch
    thread_id = api.get_disqus_thread_id(module_code)

    comments = []

    if thread_id:
        comments = api.fetch_disqus_comments(thread_id)

    if not comments:
        comments = []

    #--------------------------------------------------------------------------------------
    #SENTIMENT ANALYSIS
    #--------------------------------------------------------------------------------------
    curr_max_positive_comment = {"message": "", "sentiment": "positive", "likes": -1}
    curr_max_neutral_comment = {"message": "", "sentiment": "neutral", "likes": -1}
    curr_max_negative_comment = {"message": "", "sentiment": "negative", "likes": -1}

    cleaned_texts = []
    for comment in comments:
        comment["sentiment"] = nlp.analyze_sentiment(comment)
        cleaned = nlp.clean_comment_message(comment)
        comment["_cleaned"] = cleaned
        cleaned_texts.append(cleaned)
        if comment["sentiment"] == "positive":
            if comment["likes"] > curr_max_positive_comment["likes"]:
                curr_max_positive_comment = comment.copy()
        elif comment["sentiment"] == "neutral":
            if comment["likes"] > curr_max_neutral_comment["likes"]:
                curr_max_neutral_comment = comment.copy()
        elif comment["sentiment"] == "negative":
            if comment["likes"] > curr_max_negative_comment["likes"]:
                curr_max_negative_comment = comment.copy()

    #--------------------------------------------------------------------------------------
    #DIFFICULTY AND RECOMMENDATION ANALYSIS
    #--------------------------------------------------------------------------------------
    top_comments = sorted(comments, key=lambda c: c["likes"], reverse=True)
    top_comments = top_comments[:50]
    top_cleaned = [nlp.clean_comment_message(c) for c in top_comments]
    difficulty_score = nlp.analyze_difficulty_gemini(top_cleaned)

    # Recommendation: % of ALL comments with positive VADER sentiment
    # (sentiment already computed above for every comment)
    positive_count = sum(1 for c in comments if c.get("sentiment") == "positive")
    negative_count = sum(1 for c in comments if c.get("sentiment") == "negative")
    rated_count = positive_count + negative_count
    recommend_score = positive_count / rated_count if rated_count > 0 else None

    #---------------------------------------------------------------------------------------
    # GRADE ANALYSIS
    #---------------------------------------------------------------------------------------
    total_expected_gpa = 0.0
    total_expected_gpa_count = 0
    for comment in comments:
        expected_gpa = nlp.extract_expected_gpa(comment)
        if expected_gpa is not None:
            total_expected_gpa += expected_gpa
            total_expected_gpa_count += 1
    expected_gpa = total_expected_gpa / total_expected_gpa_count if total_expected_gpa_count > 0 else None

    total_actual_gpa = 0.0
    total_actual_gpa_count = 0
    for comment in comments:
        actual_gpa = nlp.extract_actual_gpa(comment)
        if actual_gpa is not None:
            total_actual_gpa += actual_gpa
            total_actual_gpa_count += 1
    actual_gpa = total_actual_gpa / total_actual_gpa_count if total_actual_gpa_count > 0 else None

    #---------------------------------------------------------------------------------------
    # SUMMARY, GRADE THRESHOLDS, GRADE PAIRS, WORKLOAD, PREREQUISITES
    #---------------------------------------------------------------------------------------
    summary, gemini_summary_ok = nlp.ai_summarize(top_cleaned) if top_cleaned else (None, False)
    grade_thresholds = nlp.extract_grade_thresholds(cleaned_texts) if cleaned_texts else None
    grade_thresholds_json = json.dumps(grade_thresholds) if grade_thresholds else None

    # Per-person expected vs actual grade pairs
    grade_pairs = []
    for comment in comments:
        exp = nlp.extract_expected_grade_letter(comment)
        act = nlp.extract_actual_grade_letter(comment)
        if exp or act:
            grade_pairs.append({"expected": exp, "actual": act})
    grade_pairs_json = json.dumps(grade_pairs) if grade_pairs else None

    workload     = course_data.get("workload")
    prerequisite = course_data.get("prerequisite")
    preclusion   = course_data.get("preclusion")
    workload_json = json.dumps(workload) if workload else None

    #---------------------------------------------------------------------------------------
    #SAVE TO DB
    #---------------------------------------------------------------------------------------
    # Only cache at version 3 if Gemini actually produced the summary.
    # If Gemini failed (503 etc.), save at version 2 so the next request retries.
    cache_version = 3 if gemini_summary_ok else 2

    database_access.save_module_data(
        module_code,
        course_data.get("title"),
        course_data.get("description"),
        course_data.get("moduleCredit"),
        course_data.get("department"),
        difficulty_score,
        recommend_score,
        curr_max_positive_comment,
        curr_max_neutral_comment,
        curr_max_negative_comment,
        len(comments),
        expected_gpa,
        actual_gpa,
        summary,
        grade_thresholds_json,
        grade_pairs_json,
        workload_json,
        prerequisite,
        preclusion,
        conn,
        analysis_version=cache_version,
    )

    return return_formatter(
        module_code, course_data,
        difficulty_score, recommend_score,
        len(comments), expected_gpa, actual_gpa,
        summary, grade_thresholds, grade_pairs,
        workload, prerequisite, preclusion,
    )



#----------------------------
#From below onwards
# functions only work with courses that have already been cached in DB (courses which have been looked up at least once)



#list top 30 courses with lowest difficulty, subject to minimum number of comments threshold
@app.get("/difficulty/{comment_count}")
def get_lowest_difficulty_courses(comment_count: int, conn: psycopg2.extensions.connection = Depends(get_conn)):

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            module_code,
            title,
            difficulty_score,
            recommend_score,
            comment_count
        FROM module_scores
        WHERE
            difficulty_score IS NOT NULL
            AND comment_count >= %s
        ORDER BY difficulty_score ASC
        LIMIT 30
    """, (comment_count,))

    rows = cursor.fetchall()

    results = []

    for row in rows:
        results.append({
            "module_code": row[0],
            "title": row[1],
            "difficulty_score": row[2],
            "recommendation_score": row[3],
            "comment_count": row[4]
        })

    return results


#list top 30 courses with highest recommendation score, subject to minimum number of comments threshold
@app.get("/recommendation/{comment_count}")
def get_highest_recommend_courses(comment_count: int, conn: psycopg2.extensions.connection = Depends(get_conn)):

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            module_code,
            title,
            difficulty_score,
            recommend_score,
            comment_count
        FROM module_scores
        WHERE
            recommend_score IS NOT NULL
            AND comment_count >= %s
        ORDER BY recommend_score DESC
        LIMIT 30
    """, (comment_count,))

    rows = cursor.fetchall()

    results = []

    for row in rows:
        results.append({
            "module_code": row[0],
            "title": row[1],
            "difficulty_score": row[2],
            "recommendation_score": row[3],
            "comment_count": row[4]
        })

    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)