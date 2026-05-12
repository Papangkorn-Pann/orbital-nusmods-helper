import sqlite3

conn = sqlite3.connect("database/modules.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS module_scores (
    module_code TEXT PRIMARY KEY,
    difficulty_score REAL,
    recommend_score REAL,
    top_positive_comment_message TEXT,
    top_positive_comment_likes INTEGER,
    top_neutral_comment_message TEXT,
    top_neutral_comment_likes INTEGER,
    top_negative_comment_message TEXT,
    top_negative_comment_likes INTEGER,
    comment_count INTEGER
)
""")

conn.commit()


# GET MODULE FROM DB IF EXISTS
def get_cached_module(module_code: str):

    module_code = module_code.upper() 

    cursor.execute(
        """
        SELECT
            module_code,
            difficulty_score,
            recommend_score,
            top_positive_comment_message,
            top_positive_comment_likes,
            top_neutral_comment_message,
            top_neutral_comment_likes,
            top_negative_comment_message,
            top_negative_comment_likes,
            comment_count
        FROM module_scores
        WHERE module_code = ?
        """,
        (module_code,)
    )

    row = cursor.fetchone()

    # No cached result found
    if row is None:
        return None

    # Convert SQL row into Python dictionary
    return {
        "module_code": row[0],
        "difficulty_score": row[1],
        "recommend_score": row[2],
        "top_positive_comment_message": row[3],
        "top_positive_comment_likes": row[4],
        "top_neutral_comment_message": row[5],
        "top_neutral_comment_likes": row[6],
        "top_negative_comment_message": row[7],
        "top_negative_comment_likes": row[8],
        "comment_count": row[9]
    }

#save module scores to DB, even if it already exists
#should not be called unless row doesnt exist anyway
def save_module_data(
    module_code,
    difficulty_score,
    recommend_score,
    top_positive_comment,
    top_neutral_comment,
    top_negative_comment,
    comment_count
):
    cursor.execute("""
        INSERT OR REPLACE INTO module_scores
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        module_code,
        difficulty_score,
        recommend_score,
        top_positive_comment["message"],
        top_positive_comment["likes"],
        top_neutral_comment["message"],
        top_neutral_comment["likes"],
        top_negative_comment["message"],
        top_negative_comment["likes"],
        comment_count  # Initialize comment_count to the provided value
    ))

    conn.commit()
