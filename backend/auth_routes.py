import os
#import sqlite3
import psycopg2

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

import database_access

router = APIRouter(tags=["auth"])

GOOGLE_CLIENT_ID = '983645078516-1hoft0efmob4tncjlfl2ec7hnbor3dpu.apps.googleusercontent.com'

def get_conn():
    conn = database_access.get_connection()
    try:
        yield conn
    finally:
        conn.close()


class GoogleAuthRequest(BaseModel):
    credential: str


@router.post("/auth/google")
def google_login(body: GoogleAuthRequest, conn: psycopg2.extensions.connection = Depends(get_conn)):
    try:
        idinfo = id_token.verify_oauth2_token(
            body.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except Exception as e:
        print(f"Token verification error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    user_id = idinfo["sub"]
    email   = idinfo.get("email", "")
    name    = idinfo.get("name", "")
    picture = idinfo.get("picture", "")

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        INSERT INTO users (user_id, display_name, email, picture)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(user_id) DO UPDATE SET
            display_name = excluded.display_name,
            email        = excluded.email,
            picture      = excluded.picture
    """, (user_id, name, email, picture))
    conn.commit()

    return {
        "user_id": user_id,
        "name":    name,
        "email":   email,
        "picture": picture,
    }