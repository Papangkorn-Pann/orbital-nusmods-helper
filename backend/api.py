import requests

ACAD_YEAR = "2024-2025"
NUSMODS_BASE = "https://api.nusmods.com/v2"

DISQUS_API_KEY = "wIgxYPvH9Qx6Aef53CpO0LQ1DGx4l3vmtyf9OgQ18z6ZWxLRhEV7GQf8ozAXFCuJ"
DISQUS_FORUM = "nusmods-prod"

FUNCTION_HEADERS = {
    #"User-Agent": "Mozilla/5.0",
    "Connection": "close"
}


# ----------------------------
# Helper: fetch NUSMods data
# ----------------------------
def fetch_nusmods(module_code: str):

    module_code = module_code.upper() 

    url = f"{NUSMODS_BASE}/{ACAD_YEAR}/modules/{module_code}.json"
    r = requests.get(url)

    #headers = FUNCTION_HEADERS
    
    if r.status_code == 404:
        return None  # invalid module

    if r.status_code != 200:
        raise Exception("NUSMods API error")

    return r.json()


# ----------------------------
# Helper: get Disqus thread ID
# ----------------------------

def get_disqus_thread_id(module_code: str):

    module_code = module_code.upper() 

    url = "https://disqus.com/api/3.0/threads/details.json"

    headers = FUNCTION_HEADERS

    params = {
        "api_key": DISQUS_API_KEY,
        "forum": DISQUS_FORUM,
        "thread:ident": module_code,
        "thread:link": f"https://nusmods.com/courses/{module_code}/reviews"
    }

    r = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10
    )

    if r.status_code != 200:
        return None

    data = r.json()

    response = data.get("response")

    if not response:
        return None

    return response.get("id")


# ----------------------------
# Helper: fetch comments
# ----------------------------
def fetch_disqus_comments(thread_id: str):
    url = "https://disqus.com/api/3.0/threads/listPosts.json"

    params = {
        "api_key": DISQUS_API_KEY,
        "forum": DISQUS_FORUM,
        "thread": thread_id,
    }

    headers = FUNCTION_HEADERS

    r = requests.get(url, params=params, headers=headers)

    if r.status_code != 200:
        return []

    data = r.json()

    return [
        {
            "author": p["author"]["name"],
            "message": p["message"],
            "likes": p.get("likes", 0)
        }
        for p in data.get("response", [])
    ]

