import re
import nlp
import database_access
import api
import sqlite3

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

import timetable_routes
import timer_routes
import studyplan_routes

database_access.init_db()

app = FastAPI(title="NUSMods Helper API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(timetable_routes.router)
app.include_router(timer_routes.router)
app.include_router(studyplan_routes.router)

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
                     top_positive_comment_message: str,
                     top_positive_comment_likes: int,
                     top_neutral_comment_message: str,
                     top_neutral_comment_likes: int,
                     top_negative_comment_message: str,
                     top_negative_comment_likes: int,
                     comment_count: int,
                     expected_gpa: float,
                     actual_gpa: float):
    return {
        "module": module_code,
        "title": course_data.get("title"),
        "description": course_data.get("description"),
        "module_credits": course_data.get("moduleCredit"),
        "department": course_data.get("department"),
        "difficulty_score": difficulty_score,
        "recommend_score": recommend_score,
        "top_positive_comment_message": top_positive_comment_message if top_positive_comment_likes >= 0 else None,
        "top_positive_comment_likes": top_positive_comment_likes if top_positive_comment_likes >= 0 else None,
        "top_neutral_comment_message": top_neutral_comment_message if top_neutral_comment_likes >= 0 else None,
        "top_neutral_comment_likes": top_neutral_comment_likes if top_neutral_comment_likes >= 0 else None,
        "top_negative_comment_message": top_negative_comment_message if top_negative_comment_likes >= 0 else None,
        "top_negative_comment_likes": top_negative_comment_likes if top_negative_comment_likes >= 0 else None,
        "comment_count": comment_count,
        "expected_gpa": expected_gpa,
        "actual_gpa": actual_gpa
        }

@app.get("/course/{module_code}")
def get_course(module_code: str, conn: sqlite3.Connection = Depends(get_conn)):

    module_code = module_code.upper()

    if not MODULE_CODE_RE.match(module_code):
        raise HTTPException(status_code=400, detail="Invalid module code format")

    cached = database_access.get_cached_module(module_code, conn)

    if cached:
        print("Using cached result...")
        return {
            "module": module_code,
            "title": cached["title"],
            "description": cached["description"],
            "module_credits": cached["module_credits"],
            "department": cached["department"],
            "difficulty_score": cached["difficulty_score"],
            "recommend_score": cached["recommend_score"],
            "top_positive_comment_message": cached["top_positive_comment_message"],
            "top_positive_comment_likes": cached["top_positive_comment_likes"],
            "top_neutral_comment_message": cached["top_neutral_comment_message"],
            "top_neutral_comment_likes": cached["top_neutral_comment_likes"],
            "top_negative_comment_message": cached["top_negative_comment_message"],
            "top_negative_comment_likes": cached["top_negative_comment_likes"],
            "comment_count": cached["comment_count"],
            "expected_gpa": cached["expected_gpa"],
            "actual_gpa": cached["actual_gpa"]
        }
    
    #-------------------------------------------------------------------------------------

    #Data is not yet cached. Fetch from API, throw it thru NLP pipeline, then store in DB

    #nusmods API Fetch
    course_data = api.fetch_nusmods(module_code)

    if course_data is None:
        raise HTTPException(status_code=404, detail="Invalid module code")

    #Disqus Fetch
    thread_id = api.get_disqus_thread_id(module_code)

    comments = []

    if thread_id:
        comments = api.fetch_disqus_comments(thread_id)

    #No comments case
    if not comments:
       comments = []


    #--------------------------------------------------------------------------------------
    #SENTIMENT ANALYSIS
    #--------------------------------------------------------------------------------------
    curr_max_positive_comment = {"message": "", "sentiment": "positive", "likes": -1}
    curr_max_neutral_comment = {"message": "", "sentiment": "neutral", "likes": -1}
    curr_max_negative_comment = {"message": "", "sentiment": "negative", "likes": -1}

    for comment in comments:
        comment["sentiment"] = nlp.analyze_sentiment(comment)
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
    top_comments = top_comments[:30]  # Only analyze top 30 comments because BART is computationally expensive
    if top_comments:
        difficulty_score = 0.0
        recommend_score = 0.0
        for comment in top_comments:
            result = nlp.analyze_diff_recc(comment)
            difficulty_score += float(result["difficulty_score"])
            recommend_score += float(result["recommend_score"])
        difficulty_score /= len(top_comments)
        recommend_score /= len(top_comments)
    else:
        difficulty_score = None
        recommend_score = None

    #---------------------------------------------------------------------------------------
    # GRADE ANALYSIS
    #---------------------------------------------------------------------------------------
    total_expected_gpa = 0.0
    total_expected_gpa_count = 0
    for comment in comments:
        expected_gpa = nlp.extract_expected_gpa(comment)
        if expected_gpa is not None: #gpa = 0.0 is somehow still valid
            total_expected_gpa += expected_gpa
            total_expected_gpa_count += 1
    expected_gpa = total_expected_gpa / total_expected_gpa_count if total_expected_gpa_count > 0 else None

    total_actual_gpa = 0.0
    total_actual_gpa_count = 0
    for comment in comments:
        actual_gpa = nlp.extract_actual_gpa(comment)
        if actual_gpa is not None: #gpa = 0.0 is valid
            total_actual_gpa += actual_gpa
            total_actual_gpa_count += 1
    actual_gpa = total_actual_gpa / total_actual_gpa_count if total_actual_gpa_count > 0 else None

    #---------------------------------------------------------------------------------------
    #SAVE TO DB
    #---------------------------------------------------------------------------------------
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
        conn
    )

    #Return as python dictionary object
    return return_formatter(module_code,
                            course_data,
                            difficulty_score,
                            recommend_score,
                            curr_max_positive_comment["message"],
                            curr_max_positive_comment["likes"],
                            curr_max_neutral_comment["message"],
                            curr_max_neutral_comment["likes"],
                            curr_max_negative_comment["message"],
                            curr_max_negative_comment["likes"],
                            len(comments),
                            expected_gpa,
                            actual_gpa
                            )



#----------------------------
#From below onwards
# functions only work with courses that have already been cached in DB (courses which have been looked up at least once)



#list top 30 courses with lowest difficulty, subject to minimum number of comments threshold
@app.get("/difficulty/{comment_count}")
def get_lowest_difficulty_courses(comment_count: int, conn: sqlite3.Connection = Depends(get_conn)):

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
            AND comment_count >= ?
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
def get_highest_recommend_courses(comment_count: int, conn: sqlite3.Connection = Depends(get_conn)):

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
            AND comment_count >= ?
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