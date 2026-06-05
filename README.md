## NUSMods Helper — Milestone 1 Readme

Team: Papangkorn & Piyaphat  
Level: Apollo  
Period covered: 13 May 2026 — 1 June 2026

---

### Motivation

NUS students face two recurring problems every semester: picking the right modules, and managing their studies once enrolled. Module reviews on NUSMods exist but are unstructured — hundreds of free-text comments with no aggregated signal. Students are left manually reading through threads hoping to gauge difficulty, grade expectations, or whether a module is worth taking.

NUSMods Helper addresses this by pulling those reviews and running them through an NLP pipeline that surfaces the key signals automatically. We then extended the project into a broader student productivity suite: a conflict-aware timetable builder, a study timer with a leaderboard, and a spaced-repetition study planner.

### User Stories

As an NUSMods user, I want to reap the information from the comment section of various modules, especially data-intensive information like average projected and actual grades obtained by previous students.

I then want to use that information to choose appropriate modules and automatically generate a timetable that aligns with my tastes and interests.

---

## Features

The current build implements four feature groups. Each section below explains what the feature does and which files implement it.

**1. Module Review Aggregator** — `backend/main.py`, `backend/nlp.py`, `backend/api.py`  
Enter a module code (e.g. `CS2040S`) on the Home page. The backend fetches the module description from the NUSMods API and student reviews from Disqus, runs three NLP layers over the comments (VADER sentiment, BART zero-shot classification for difficulty and recommendation, regex grade extraction), and returns a one-screen summary: difficulty score, recommendation score, expected/actual GPA averages, and the most-liked positive, neutral, and negative comments. Results are cached in SQLite so repeat lookups are instant.

**2. Conflict-Aware Timetable Builder** — `backend/timetable_routes.py`, `frontend/src/pages/Timetable.jsx`, `frontend/src/components/timetable/`  
Search for modules, pick a lesson type, and choose a class slot. The grid renders Monday–Friday from 08:00 to 22:00 in 30-minute rows and prevents overlapping slots. Slot selections are persisted per user in `timetable_slots`.

**3. Study Timer with Leaderboard** — `backend/timer_routes.py`, `frontend/src/pages/Timer.jsx`, `frontend/src/components/timer/`  
Start and stop a session; the backend computes duration server-side from ISO timestamps to avoid client clock skew. A weekly leaderboard (`GET /timer/leaderboard`) ranks users by study time, optionally filtered by faculty. Users can also create or join study groups via a six-character invite code.

**4. Spaced-Repetition Study Plan** — `backend/studyplan_routes.py`, `backend/sm2.py`, `frontend/src/pages/StudyPlan.jsx`, `frontend/src/components/studyplan/`  
Submit an exam, list its topics, and the backend creates one SM-2 card per topic. Each day `GET /studyplan/{user_id}/today` returns all cards due. The student rates recall 0–5; topics they know drift to reviews every few weeks while difficult topics stay daily.

**Anonymous identity** — `frontend/src/App.jsx`, `backend/timer_routes.py`  
There is no login screen. On first visit, `crypto.randomUUID()` mints a UUID, stores it in `localStorage`, and silently registers it with `POST /users`. Subsequent visits read the same UUID, giving each user persistent identity across sessions without an account. The user can set a display name, faculty, year, and course via `PUT /users/{user_id}` — these surface on the leaderboard.

> Features yet to be implemented in later milestones: backtracking-based timetable optimisation (search for the best timetable across a set of modules by user-supplied preferences), richer review aggregation (topic clustering across modules), and friend-only leaderboards. Buttons for the timetable optimiser are present and show an "under development" message when clicked.

---

## Setup

Two ways to run the project. Hosted/zipped link is preferred for evaluators.

**Option A — Download the zipped codebase** (no GitHub access needed)  
Google Drive: *[link to be added before submission]*  
Unzip and follow the steps below.

**Option B — Clone the repo**

```bash
git clone https://github.com/<username>/orbital-nusmods-helper.git
cd orbital-nusmods-helper
cp .env.example .env
# open .env and fill in DISQUS_API_KEY
```

**Backend**

```bash
cd backend
python -m venv ../.venv
source ../.venv/bin/activate     # Windows: ..\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`. Interactive docs at `/docs`.

> First install downloads `torch` and `transformers` (~2 GB). First module lookup is slow while BART loads into memory; subsequent lookups hit the SQLite cache and return instantly.

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The frontend proxies `/api` to the backend, so both must run together.

---

## User Guide

1. **Look up a module.** Open the Home page, type a code like `CS2040S`, hit search. You'll see difficulty (1–5), recommendation (0–1), expected/actual GPA, and three representative reviews. First lookup of a module takes 30–60 seconds; cached lookups are instant.
2. **Build a timetable.** Go to Timetable, search for a module, click a lesson type, pick a class. The grid updates. Add more modules; the picker prevents conflicts.
3. **Start a study session.** Go to Timer, click Start. Stop when done. Visit the Leaderboard tab to see where you rank this week.
4. **Plan for an exam.** Go to Study Plan, enter the module code, exam date, and a list of topics. Each day, return and review whichever cards are due.

---

## System Architecture

```
+----------------+       /api/*        +----------------+
|                | <-----------------> |                |
|  React + Vite  |   (HTTP via Vite    |   FastAPI      |
|  frontend      |    dev proxy)       |   backend      |
|                |                     |                |
+----------------+                     +-------+--------+
                                               |
                          +--------------------+--------------------+
                          |                    |                    |
                          v                    v                    v
                   +-------------+     +---------------+     +--------------+
                   |  NUSMods    |     |   Disqus      |     |   SQLite     |
                   |  API        |     |   API         |     |  modules.db  |
                   +-------------+     +---------------+     +--------------+
```

**Frontend (React 18 + Vite).** Pages under `frontend/src/pages/` map to routes via React Router; reusable widgets live in `frontend/src/components/`. Vite's dev proxy forwards `/api/*` to `localhost:8000`, avoiding CORS during development.

**Backend (FastAPI).** `main.py` registers three routers (`timetable_routes`, `timer_routes`, `studyplan_routes`) and the module-lookup endpoint. A shared `get_conn()` dependency yields a SQLite connection per request and closes it in `finally`, guaranteeing no leaked connections.

**Data (SQLite, `database/modules.db`).** Six tables: `module_scores` (NLP cache), `users`, `timetable_slots`, `study_sessions`, `study_groups` + `study_group_members`, and `study_cards`. Schema lives in `database_access.init_db()` using `CREATE TABLE IF NOT EXISTS`, safe to run on every startup.

---

## How It Works

Each subsection below explains the underlying technique briefly and points to where it lives in the codebase.

### Backend framework — FastAPI

FastAPI generates OpenAPI docs from type hints, validates request bodies with Pydantic, and supports generator-based dependencies. `get_conn()` in every router yields a connection and tears it down via `finally`, mirroring `try/with` semantics for request lifecycle. Routers are mounted with `app.include_router(...)` so each feature group keeps its routes in a focused file.

### Sentiment — VADER

`vaderSentiment.SentimentIntensityAnalyzer` returns a compound score in [−1, +1]; ≥ 0.05 is positive, ≤ −0.05 is negative. VADER is lexicon-based, runs in-process with no GPU, and is tuned for short informal text — a fit for student reviews. Comments are pre-cleaned via BeautifulSoup (strip HTML) and a whitespace regex before scoring. See `backend/nlp.py::analyze_sentiment`.

### Difficulty and recommendation — BART zero-shot classification

`facebook/bart-large-mnli` is fine-tuned on natural language inference; given a piece of text and candidate labels, it scores how well each label describes the text. We use five ordinal labels for difficulty (`very easy` → `very hard`, mapped to 1–5) and two for recommendation (`recommend` → 1.0, `not recommend` → 0.0). The implementation takes a confidence-weighted average across labels rather than a hard top-1 pick, so a comment scoring 60% "hard" / 40% "moderate" yields `4×0.6 + 3×0.4 = 3.6`. Only the top 30 most-liked comments are processed per module, because BART CPU inference is slow. See `backend/nlp.py::analyze_diff_recc`.

### Grade extraction — verbose regex

Two patterns scan each comment for a trigger phrase followed by a letter grade. Trigger sets distinguish *expected* grades (`expecting`, `predicted grade`, `projected`) from *actual* grades (`got`, `received`, `scored`, `final grade`). Letter grades are mapped to a 5-point GPA scale. An explicit `None` check is used instead of falsy checks because GPA = 0.0 (an `F`) is a valid result. See `backend/nlp.py::extract_expected_gpa`, `extract_actual_gpa`.

### Spaced repetition — SM-2

SM-2 (the algorithm underlying Anki) models each topic with an interval, an easiness factor, and a repetition count. After each review, the user rates recall on 0–5; quality < 3 resets the card to one day, otherwise the interval grows by the easiness factor. The whole algorithm lives in `backend/sm2.py::review_card` as a pure function — no I/O, no database access — so it can be unit-tested in isolation.

### Storage — SQLite

Single-file relational database. Every connection sets `conn.row_factory = sqlite3.Row` so query results are accessed by column name. `INSERT OR REPLACE INTO module_scores` is used to cache module lookups; `ON CONFLICT(...) DO UPDATE` makes timetable slot writes an upsert. File-level locking is fine at this scale.

### Frontend — React + Vite

State via `useState`, side effects via `useEffect`, mutable references (e.g. the timer's `setInterval` handle) via `useRef`. Vite's HMR re-evaluates only the changed module so application state persists across edits. Anonymous identity is bootstrapped in `App.jsx` with `crypto.randomUUID()` → `localStorage` → silent `POST /users`.

---

## Software Engineering Concepts

The architecture relies on a few standard principles. Each is illustrated by code already in the repo, not aspirational.

**Separation of concerns.** Backend routes are split by feature into `timetable_routes.py`, `timer_routes.py`, `studyplan_routes.py`; cross-cutting concerns (DB schema, queries) live in `database_access.py`; NLP logic lives in `nlp.py`. The frontend mirrors this with `pages/` (full views) and `components/<feature>/` (reusable widgets per feature).

**Dependency injection.** FastAPI's `Depends(get_conn)` injects a fresh SQLite connection per request and tears it down via `finally`. Handlers never construct connections themselves, which centralises lifecycle management and makes per-request resource leaks impossible.

**Single responsibility.** Each module owns one concern: `sm2.review_card` is a pure function with no I/O; `clean_comment_message` strips HTML; `analyze_sentiment`, `analyze_diff_recc`, and the two `extract_*_gpa` functions each do exactly one thing. This makes them individually testable.

**Caching as a first-class boundary.** Expensive NLP work runs once per module; results land in `module_scores`. The lookup endpoint checks the cache first and only falls through to the BART pipeline on a miss. This is invisible to the frontend but turns 30-second lookups into instant ones for previously seen modules.

**Input validation at the edge.** Module codes are rejected immediately if they fail `^[A-Z]{2,3}\d{4}[A-Z]{0,2}$` (see `main.py`), preventing wasted Disqus/NUSMods calls on malformed input.

**Secrets out of source.** `DISQUS_API_KEY` is loaded from `.env` via `python-dotenv`; `.env` is gitignored and `.env.example` documents the expected variables.

---

## Project Management

**Sprints.** Two-week cycles aligned with the Orbital milestones. Each sprint starts with a planning session (scope and acceptance criteria for each feature), runs as solo work in parallel, and ends with a review where we demo to each other and write the milestone document together.

**Kanban.** A four-column GitHub Project board: `Backlog → In Progress → Review → Done`. Each card is a feature or a bug, linked to the relevant commit or pull request. We move cards in real time; if a feature spans more than three days, it's broken into smaller cards.

**Division of work.** Piyaphat owns the NLP pipeline, the FastAPI backend, and the database layer. Papangkorn owns the React frontend, routing, and the component library. Schema changes and API contracts are reviewed by both before merging.

**Communication.** Daily async standups in a shared notes document; weekly sync over voice. Anything that touches both halves of the stack is paired in person.

> Kanban and sprint board screenshots will be inserted here once the team has migrated from the temporary tracking sheet to GitHub Projects.

---

## Project Log

The full sprint-by-sprint log is in `docs/project-log.md` (link will be added when the file is committed). Summary of work done in this milestone period:

- **Week 1 (13–19 May):** project proposal, repo bootstrap, NUSMods + Disqus API exploration, sentiment pipeline (VADER) prototyped.
- **Week 2 (20–26 May):** BART zero-shot integration, grade-extraction regex, SQLite schema and caching layer, FastAPI router split.
- **Week 3 (27 May – 1 June):** React frontend, timetable grid, timer + leaderboard, SM-2 study planner, anonymous identity via `localStorage`, README and Milestone 1 document.

---

## Links

- **Code (zipped):** *[Google Drive link — TBA]*
- **GitHub repo:** *[private — invite sent to evaluators on request]*
- **Demo video:** *[YouTube link — TBA]*
- **Poster:** *[link — TBA]*
- **Project log:** `docs/project-log.md`
