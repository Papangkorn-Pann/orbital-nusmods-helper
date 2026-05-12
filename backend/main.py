import nlp
import database_access
import api

from fastapi import FastAPI, HTTPException

app = FastAPI()

def return_formatter(module_code: str,
                     course_data: dict,
                     difficulty_score: float,
                     recommendation_score: float,
                     top_positive_comment_message: int,
                     top_positive_comment_likes: int,
                     top_neutral_comment_message: int,
                     top_neutral_comment_likes: int,
                     top_negative_comment_message: int,
                     top_negative_comment_likes: int,
                     comment_count: int):
    return {
        "module": module_code,
        "title": course_data.get("title"),
        "description": course_data.get("description"),
        "semesterData": course_data.get("semesterData", []),
        "difficulty_score": difficulty_score,
        "recommendation_score": recommendation_score,
        "top_positive_comment_message": top_positive_comment_message if top_positive_comment_likes >= 0 else None,
        "top_positive_comment_likes": top_positive_comment_likes if top_positive_comment_likes >= 0 else None,
        "top_neutral_comment_message": top_neutral_comment_message if top_neutral_comment_likes >= 0 else None,
        "top_neutral_comment_likes": top_neutral_comment_likes if top_neutral_comment_likes >= 0 else None,
        "top_negative_comment_message": top_negative_comment_message if top_negative_comment_likes >= 0 else None,
        "top_negative_comment_likes": top_negative_comment_likes if top_negative_comment_likes >= 0 else None,
        "comment_count": comment_count
        }

@app.get("/course/{module_code}")
def get_course(module_code: str):

    module_code = module_code.upper() 

    cached = database_access.get_cached_module(module_code)

    #API Fetch
    course_data = api.fetch_nusmods(module_code)

    if course_data is None:
        raise HTTPException(status_code=404, detail="Invalid module code")

    if cached:
        print("Using cached result...")
        return return_formatter(module_code,
                                course_data,
                                cached["difficulty_score"],
                                cached["recommend_score"],
                                cached["top_positive_comment_message"],
                                cached["top_positive_comment_likes"],
                                cached["top_neutral_comment_message"],
                                cached["top_neutral_comment_likes"],
                                cached["top_negative_comment_message"],
                                cached["top_negative_comment_likes"],
                                cached["comment_count"])
    
    #-------------------------------------------------------------------------------------

    #Data is not yet cached. Fetch from API, throw it thru NLP pipeline, then store in DB

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
        recommendation_score = 0.0
        for comment in top_comments:
            result = nlp.analyze_diff_recc(comment["message"])
            difficulty_score += float(result["difficulty_score"])
            recommendation_score += float(result["recommendation_score"])
        difficulty_score /= len(top_comments)
        recommendation_score /= len(top_comments)
    else:
        difficulty_score = None
        recommendation_score = None

    #---------------------------------------------------------------------------------------
    #SAVE TO DB
    #---------------------------------------------------------------------------------------
    database_access.save_module_data(
        module_code,
        difficulty_score,
        recommendation_score,
        curr_max_positive_comment,
        curr_max_neutral_comment,
        curr_max_negative_comment,
        len(comments)
    )

    #Return as python dictionary object
    return return_formatter(module_code,
                            course_data,
                            difficulty_score,
                            recommendation_score,
                            curr_max_positive_comment["message"],
                            curr_max_positive_comment["likes"],
                            curr_max_neutral_comment["message"],
                            curr_max_neutral_comment["likes"],
                            curr_max_negative_comment["message"],
                            curr_max_negative_comment["likes"],
                            len(comments))

print(get_course("CS2040S"))