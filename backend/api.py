import time
import requests
from config import DISQUS_API_KEY

ACAD_YEAR = "2025-2026"
NUSMODS_BASE = "https://api.nusmods.com/v2"

# in-memory cache for the full module list (refreshed every hour)
_module_list: list = []
_module_list_fetched_at: float = 0
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
    if not DISQUS_API_KEY:
        return None

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
    if not DISQUS_API_KEY:
        return []

    url = "https://disqus.com/api/3.0/threads/listPosts.json"
    all_comments = []
    cursor = None

    while len(all_comments) < 500:
        params = {
            "api_key": DISQUS_API_KEY,
            "forum": DISQUS_FORUM,
            "thread": thread_id,
            "limit": 100,
        }
        if cursor:
            params["cursor"] = cursor

        r = requests.get(url, params=params, headers=FUNCTION_HEADERS, timeout=10)
        if r.status_code != 200:
            break

        data = r.json()
        posts = data.get("response", [])
        all_comments.extend([
            {
                "author": (p.get("author") or {}).get("name", "Anonymous"),
                "message": p.get("message") or "",
                "likes": p.get("likes", 0),
            }
            for p in posts
            if not p.get("isDeleted") and not p.get("isSpam") and p.get("message")
        ])

        c = data.get("cursor", {})
        if not c.get("hasNext"):
            break
        cursor = c.get("next")

    return all_comments


# ----------------------------
# Helper: module list search
# ----------------------------
def _refresh_module_list():
    global _module_list, _module_list_fetched_at
    if _module_list and time.time() - _module_list_fetched_at < 3600:
        return
    r = requests.get(f"{NUSMODS_BASE}/{ACAD_YEAR}/moduleList.json", timeout=15)
    if r.status_code == 200:
        _module_list = r.json()
        _module_list_fetched_at = time.time()


def search_modules(query: str, limit: int = 10) -> list:
    """Return modules whose code or title contains the query string."""
    _refresh_module_list()
    q = query.upper()
    results = [
        m for m in _module_list
        if q in m["moduleCode"].upper() or q in m["title"].upper()
    ]
    return results[:limit]


# ----------------------------
# Helper: fetch timetable slots
# ----------------------------
def fetch_module_slots(module_code: str, sem: int = 1) -> list | None:
    """Return the timetable slot list for a given module and semester."""
    data = fetch_nusmods(module_code.upper())
    if data is None:
        return None
    for sem_data in data.get("semesterData", []):
        if sem_data["semester"] == sem:
            return sem_data.get("timetable", [])
    return []

