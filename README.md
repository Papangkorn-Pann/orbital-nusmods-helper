# NUSMods Helper

**Team:** Papangkorn Wangchochedkun & Piyaphat Klanprayoon  
**Level:** Gemini  
**Orbital Milestone:** 2  
**Period:** 13 May 2026 – 1 July 2026

**Live Demo:** https://orbital-frontend-i7gq.onrender.com

> The backend runs on Render's free tier and spins down after 15 minutes of inactivity. The first request after a cold start may take up to 30 seconds. Subsequent requests are fast.

---

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher and npm
- Git

---

## Local Setup

Clone the repository:

```bash
git clone https://github.com/orbital-team/orbital-nusmods-helper.git
cd orbital-nusmods-helper
```

Create `backend/.env` with the following environment variables (obtain values from the team):

```
DATABASE_URL=...
GEMINI_API_KEY=...
DISQUS_API_KEY=...
GOOGLE_CLIENT_ID=...
```

Install backend dependencies and start the backend server:

```bash
cd backend
python -m venv ../.venv
source ../.venv/bin/activate     # Windows: ..\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend runs at `http://localhost:8000`. Interactive API docs are at `http://localhost:8000/docs`.

In a separate terminal, install frontend dependencies and start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies all `/api/*` requests to the backend automatically — no CORS configuration needed for local development.

---

## Motivation

Every semester, NUS students face two problems: choosing the right modules, and staying on top of their studies once enrolled.

Module selection, in particular, is a task many find tedious. NUSMods hosts hundreds of free-text reviews from past students, but provides no aggregated review or verdict. There is no difficulty rating, no grade distribution, no recommendation percentage. Students manually read through comment threads to gauge workload, bell curve harshness, and usefulness of the module. This process is slow and highly inconsistent, as many students will only read the topmost comments (only an average of 3 Disqus comments are displayed on a module page initially).

Building a timetable adds further friction. NUSMods provides slot information, but constructing a conflict-free schedule that also avoids early starts, keeps lunch free, and minimises cross-campus travel requires a long trial-and-error process. Students rebuild the same timetable several times before finding one that works.

Once classes start, revision tends to be reactive. Without structure, students cram before exams rather than spacing review over weeks. Study sessions happen in isolation, with no visibility into how peers are performing and no external motivation to stay consistent.

NUSMods Helper addresses all three problems. We extract difficulty scores, recommendation rates, and expected versus actual grades from NUSMods and Disqus reviews using an NLP pipeline. We pair this with a timetable builder that auto-generates conflict-free schedules based on user preferences. A study timer, leaderboard, and spaced-repetition study planner complete the application.

---

## User Stories

**Module Selection**

- As an NUS student, I want to see a difficulty score and recommendation percentage for any module, so that I can quickly compare modules without reading through hundreds of comments.
- As an NUSMods user, I want to view the most helpful positive, neutral, and negative reviews for a module, so that I can understand both the strengths and drawbacks before enrolling.
- As an NUS student, I want to compare two modules side by side, so that I can make an informed decision when choosing between electives.
- As an NUS student, I want to browse a list of the easiest and most-recommended modules, so that I can discover options I would not have considered otherwise.

**Timetable Planning**

- As an NUS student, I want to search for modules, select specific tutorial and lecture slots, and visualise a complete timetable, so that I can build a schedule without conflicts.
- As an NUS student, I want the system to automatically generate a conflict-free timetable based on my preferences for start times, lunch breaks, and campus travel, so that I do not have to do trial-and-error manually.
- As an NUS student, I want to export my timetable as an iCal file, so that I can import it into my calendar app.
- As an NUS student, I want to share my timetable with a link, so that my friends can view it when coordinating schedules.

**Study Timer and Leaderboard**

- As an NUS student, I want to track how long I study each session, so that I can monitor my productivity over time.
- As an NUS student, I want to see a weekly leaderboard of study hours filtered by faculty and year, so that I have a benchmark against peers.
- As an NUS student, I want to create a study group and invite friends with a code, so that we can track and compare our study hours together.

**Exam Revision**

- As an NUS student, I want to create a set of revision cards for each exam topic, so that I have a structured plan for what to study before each exam.
- As an NUS student, I want the system to schedule my revision sessions using spaced repetition, so that I review topics at the right intervals for long-term retention.
- As an NUS student, I want to export my upcoming revision schedule as an iCal file, so that my study plan appears alongside my other commitments in my calendar.

**CourseReg**

- As an NUS student, I want to see how competitive each tutorial slot is before bidding, so that I can identify slots that are easier to secure during CourseReg.

---

## Project Vision

Our primary goal is to give NUS students a single platform that assists course planning by providing structured, data-driven academic insights of NUS modules. NUSMods Helper targets students who spend unnecessary time manually reading reviews, rebuilding timetables, and cramming before exams without a revision plan.

By using NLP, a backtracking algorithm for timetable optimisation, and SM-2 spaced repetition, we aim to turn the course planning process from hours of manual effort into minutes of guided decision-making. Students are not only helped at the selection stage, but supported throughout the semester with tools that build consistent study habits.

We envision NUSMods Helper as the standard companion for every NUS student each semester, from the moment they choose their modules to the day they sit their final exam.

---

## Target Users

- **Students planning their semester:** want structured, data-driven insights from peer reviews before committing to a module
- **Students who struggle with timetable building:** spend hours in trial-and-error trying to construct a conflict-free schedule
- **Students who want to study more consistently:** tend to cram before exams and want a structured revision plan that spaces out review over weeks
- **Students motivated by social accountability:** want to track and compare their study hours against peers

---

## Features

### 1. Module Analysis

Enter a module code (e.g. `CS2040S`) in the Module Analysis page. The backend fetches the module description from the NUSMods API and student reviews from Disqus, then runs three NLP layers: VADER sentiment analysis, Gemini AI difficulty scoring (1–5), and regex grade extraction. Returns a one-screen summary — difficulty score, recommendation %, expected/actual GPA averages, the most-liked positive/neutral/negative comments, and an AI-generated summary. Results are cached so repeat lookups are instant. A Top Modules discovery panel lists the easiest and most-recommended modules from the cache.

**Key components:**
- VADER sentiment analysis classifies each comment as positive, neutral, or negative
- Gemini AI summarises the top 30 most-liked comments and produces a difficulty score
- Regex grade extraction pulls expected vs. actual GPA from contextual phrases in comments
- Results cache in PostgreSQL — repeat lookups are served instantly
- Top Modules panel for browsing easiest and most-recommended cached modules
- Module Comparison page for side-by-side analysis of two modules

### 2. Conflict-Aware Timetable Builder

Search for modules, pick a lesson type, and choose a class slot. The grid renders Monday–Friday from 08:00 to 22:00 in 30-minute rows and prevents conflicting slots. Auto-Generate runs a backtracking algorithm across all added modules, scores up to 5 conflict-free timetables by seven weighted preferences (latest start, earliest end, lunch break, compact days, minimal gaps, travel, slot popularity), and lets you apply the result in one click. Share creates a 30-day shareable link. The timetable can also be exported as an iCal file or printed.

**Key components:**
- Manual slot selection with conflict detection
- Backtracking auto-generator returning the top 5 conflict-free timetables ranked by preference score
- 30-day shareable link with read-only view
- iCal export (RFC 5545) and print support

### 3. Study Timer with Leaderboard

Start and stop a session; the backend computes duration server-side from ISO timestamps to avoid client clock skew. A 7-day bar chart shows daily study history. A weekly leaderboard ranks users by study time, optionally filtered by faculty, year, and course. Users can create or join study groups via a six-character invite code for a private group leaderboard.

**Key components:**
- Server-side duration computation to prevent clock drift
- 7-day history chart
- Global leaderboard with faculty/year/course filters
- Study groups with 6-character invite codes

### 4. CourseReg Advisor

Search a module and select a semester. Each lesson slot shows a competition bar, a probability badge for each CourseReg round (R0, R1A, R1B, R2), and a plain-language recommendation. Competition is computed from three signals: slot capacity (inverse log), timing desirability (day-of-week and time-of-day weights), and live platform demand (how many app users have selected that slot in their timetable).

```
raw_score = 0.40 × capacity_factor + 0.35 × timing_desirability + 0.25 × platform_demand
```

Scores are normalised within each lesson type so the most competitive slot scores 1.0.

### 5. Study Plan (Spaced Repetition)

Add an exam with a list of topics. The backend creates one SM-2 card per topic with `next_review_date` set to today. Each day, return to the Review tab to see due cards. Rate recall 0–5; the SM-2 algorithm adjusts intervals: cards rated below 3 reset to 1 day, cards rated 3 or above grow exponentially. A streak counter tracks consecutive review days. The full schedule exports to iCal.

**Key components:**
- SM-2 scheduling (same algorithm as Anki) in `backend/sm2.py` as a pure function
- Daily review queue, quality rating (0–5), interval adjustment
- Review streak tracking
- iCal export for the upcoming revision schedule

---

## Features to Be Implemented

- **Reddit integration:** Pull NUSMods discussion from r/NUSWhispers and r/nus to supplement Disqus comments, improving NLP coverage for modules with few Disqus reviews.
- **Timetable import/export:** Import a NUSMods share URL to load existing slot selections; export app-built timetables back to a NUSMods-compatible link.
- **Friends system:** Add connections by display name or invite code. View friends' timetables in read-only mode; filter leaderboards to friends only.
- **Profile customisation:** Profile picture and a gamified progression system with XP and level badges on the leaderboard.
- **Timetable comparison:** Side-by-side view of two students' timetables to identify shared free windows for group study.

---

## User Guide

**Signing In**

Open the app and click "Sign in with Google". Select your Google account. On first sign-in, a profile is created automatically. You will be redirected to the home page.

**Module Analysis**

1. Click "Module Analysis" from the navigation bar.
2. Type a module code (e.g. CS2040S) into the search bar and select the module from the dropdown.
3. The page displays the difficulty score (1–5), recommendation percentage, expected and actual GPA from student comments, and an AI-generated summary of the top reviews.
4. Scroll down to view the most-liked positive, neutral, and negative student comment.
5. Repeat lookups are served instantly from the results cache.

**Timetable Builder**

1. Click "Timetable" from the navigation bar.
2. Search for a module by code or name and click Add.
3. Click a lesson slot on the weekly grid to select it. Conflicting slots are shown in grey and cannot be selected.
4. To auto-generate: click Generate and set preference sliders for start time, end time, lunch break, and travel. The top 5 conflict-free timetables ranked by your preferences are displayed.
5. Click Share to generate a public link (valid for 30 days), or Export iCal to download a calendar file.

**Study Timer and Leaderboard**

1. Click "Timer" from the navigation bar.
2. Fill in your profile (display name, faculty, year, course) in the left panel.
3. Click Start to begin a study session. Click Stop when done. Duration is computed server-side.
4. The 7-day bar chart updates automatically to show your daily study hours for the past week.
5. The right panel shows the global leaderboard for the current week. Use the faculty, year, and course filters to narrow the ranking.
6. To use study groups: click Create group and share the 6-character code with friends. Or enter a friend's code and click Join. The group leaderboard shows only members' hours.

**CourseReg Advisor**

1. Click "CourseReg" from the navigation bar.
2. Search for a module by code and select Semester 1 or Semester 2.
3. Slots are organised by lesson type. Each slot card shows capacity, timing, a competition bar, and probability badges for rounds R0, R1A, R1B, and R2.
4. Green badges indicate a high chance of success; red badges indicate high competition. The recommendation text summarises the safest round to bid in.

**Study Plan**

1. Click "Study Plan" from the navigation bar.
2. Go to the Add Exam tab. Enter the module code, exam date, and a list of topics (one per line).
3. Return to the Review tab each day. Cards due today are shown one at a time. Click Reveal to see the content, then click a quality rating from 0 (Blackout) to 5 (Perfect).
4. The SM-2 algorithm adjusts each card's next review date based on your rating. Difficult cards reappear in 1 day; well-known cards space out to weeks.
5. The Upcoming tab shows all future review dates grouped by exam.
6. Click Export iCal to add your revision schedule to your calendar app.

**Module Comparison**

1. Click "Compare" from the navigation bar.
2. Search and select a module in the left column, then another in the right column.
3. The table shows difficulty, recommendation percentage, expected and actual GPA, workload breakdown, and AI summary side by side. Green and red indicators show which module scores better on each metric.

---

## System Architecture

| Layer | Description | Tech |
|---|---|---|
| Frontend | React SPA: module analysis, timetable builder, study timer, study plan, CourseReg advisor | React 18, React Router 6, Vite 5 |
| Backend | FastAPI server: NLP analysis, timetable generation, session tracking, spaced repetition, CourseReg scoring | Python, FastAPI, Uvicorn |
| NLP | Three-layer review analysis | VADER, BART-large-MNLI, Regex, Google Gemini |
| Algorithms | Timetable auto-generation; spaced repetition scheduling | Backtracking (Python), SM-2 (Python) |
| Database | NLP cache, user profiles, timetable slots, sessions, study groups, SM-2 cards | PostgreSQL (Supabase) |
| External APIs | Module data, reviews, AI | NUSMods, Disqus, Google Gemini |

```
+----------------+       /api/*        +----------------+
|                | <-----------------> |                |
|  React + Vite  |   (Vite dev proxy)  |   FastAPI      |
|  frontend      |                     |   backend      |
|                |                     |                |
+----------------+                     +-------+--------+
                                               |
                          +--------------------+--------------------+
                          |                    |                    |
                          v                    v                    v
                   +-------------+     +---------------+     +--------------+
                   |  NUSMods    |     |   Disqus      |     |  PostgreSQL  |
                   |  API        |     |   API         |     |  (Supabase)  |
                   +-------------+     +---------------+     +--------------+
```

**Frontend (React 18 + Vite).** Pages under `frontend/src/pages/` map to routes via React Router. Reusable widgets live in `frontend/src/components/`. Vite's dev proxy forwards `/api/*` to `localhost:8000`, avoiding CORS during development.

**Backend (FastAPI).** `main.py` registers four routers (`timetable_routes`, `timer_routes`, `studyplan_routes`, `coursereg_routes`) and the module-lookup endpoint. A shared `get_conn()` dependency yields a PostgreSQL connection per request and closes it in `finally`, guaranteeing no leaked connections.

**Database (PostgreSQL via Supabase).** Seven tables: `module_scores` (NLP cache), `users`, `timetable_slots`, `timetable_shares` (30-day TTL), `study_sessions`, `study_groups` + `study_group_members`, and `study_cards`. Schema lives in `database_access.init_db()` using `CREATE TABLE IF NOT EXISTS`, safe to run on every startup.

---

## How It Works

### Sentiment Analysis — VADER

`vaderSentiment.SentimentIntensityAnalyzer` returns a compound score in [−1, +1]. Scores above 0.05 are positive; below −0.05 are negative. VADER is lexicon-based, runs in-process with no GPU, and is tuned for informal short text — a good fit for student reviews. Comments are pre-cleaned via BeautifulSoup (strip HTML) and a whitespace regex before scoring. See `backend/nlp.py`.

### Difficulty Scoring — Gemini AI

`analyze_difficulty_gemini` in `backend/nlp.py` sends the top 50 most-liked student reviews (capped at 8,000 chars) to `gemini-2.5-flash-lite` in a single API call and asks for a 1.0–5.0 difficulty score. This replaced a 50-iteration BART loop, cutting first-lookup time from ~60 s to ~2 s and eliminating the 2 GB torch dependency. The recommendation score is derived separately from VADER sentiment ratios across all comments.

### Grade Extraction — Regex

Two patterns scan each comment for a trigger phrase followed by a letter grade. Trigger sets distinguish expected grades (`expecting`, `predicted grade`, `projected`) from actual grades (`got`, `received`, `scored`, `final grade`). Letter grades are mapped to a 5-point GPA scale. An explicit `None` check is used instead of falsy checks because GPA = 0.0 (an F) is a valid result. See `backend/nlp.py`.

### Timetable Auto-Generation — Backtracking

`timetable_generator.py` explores all valid slot combinations across the selected modules, discarding any combination the moment a time conflict is detected. Each conflict-free timetable is scored across seven dimensions: latest daily start time, earliest daily end time, free lunch window (12:00–14:00), fewest days with classes, minimal gaps between classes, campus travel distance between back-to-back classes, and slot popularity from CourseReg data. The top 5 scoring timetables are returned.

### Spaced Repetition — SM-2

SM-2 models each topic with an interval, an easiness factor, and a repetition count. After each review, the user rates recall 0–5. Quality below 3 resets the card to 1 day. Ratings of 3 or above grow the interval (1 day → 6 days → exponential thereafter). The easiness factor adjusts after each review so consistently well-recalled topics drift to reviews every few weeks while difficult ones stay on short cycles. The algorithm is a pure function in `backend/sm2.py` with no I/O or database access.

### Storage — PostgreSQL

Hosted on Supabase. Every connection sets `row_factory` so results are accessed by column name. `INSERT OR REPLACE INTO module_scores` caches NLP results. `ON CONFLICT(...) DO UPDATE` makes timetable slot writes an upsert. ACID compliance is provided by PostgreSQL: every write is wrapped in psycopg2's default transaction handling with commit on success and automatic rollback on exception.

### Frontend — React + Vite

State via `useState`, side effects via `useEffect`, mutable references (e.g. the timer's `setInterval` handle) via `useRef`. Vite's HMR re-evaluates only the changed module so application state persists across edits. Authentication uses Google OAuth 2.0 (`@react-oauth/google` on the frontend, `google.oauth2.id_token.verify_oauth2_token` on the backend). The `ProtectedRoute` component reads `localStorage` for the user object and redirects to `/login` if absent.

---

## Software Engineering Principles

**Separation of Concerns**

The backend is organised so each file has a single distinct role. Feature-specific routes are split across `timetable_routes.py`, `timer_routes.py`, `studyplan_routes.py`, and `coursereg_routes.py`. NLP logic is isolated in `nlp.py`, the backtracking algorithm in `timetable_generator.py`, the SM-2 algorithm in `sm2.py`, database queries in `database_access.py`, and external API calls in `api.py`. This means changes to one layer do not affect the logic of others.

**Single Responsibility Principle**

Each component has exactly one responsibility. The SM-2 algorithm is isolated entirely in `sm2.py` as a single pure function with no database access or side effects:

```python
def review_card(interval, easiness_factor, repetitions, quality):
    if quality < 3:
        repetitions = 0
        interval = 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * easiness_factor)
        repetitions += 1
    ef = max(1.3, easiness_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    next_date = (date.today() + timedelta(days=interval)).isoformat()
    return interval, ef, repetitions, next_date
```

Route files call this function and write the returned values to the database independently. Similarly, `clean_comment_message()` only strips HTML, and `_slot_demand_counts()` only queries selection counts.

**Don't Repeat Yourself (DRY)**

`get_conn()` is defined once and injected via FastAPI's `Depends()` into every route that needs a database connection:

```python
def get_conn():
    conn = database_access.get_connection()
    try:
        yield conn
    finally:
        conn.close()
```

The `yield` makes this a generator-based dependency: the connection is created before the route handler runs and closed in `finally` regardless of whether the request succeeded or raised an exception.

**Keep It Simple (KISS)**

Input validation is kept minimal. Module codes are validated upfront with a single compiled regex before any external API calls are made:

```python
MODULE_CODE_RE = re.compile(r'^[A-Z]{2,3}\d{4}[A-Z]{0,2}$')
```

This rejects malformed inputs (e.g. `"hello"` or `"CS 2040"`) immediately with a 400 error, avoiding unnecessary downstream calls. Authentication follows the same principle: a single `ProtectedRoute` component reads one `localStorage` key and redirects to `/login` if absent.

**Modularity**

The entire backtracking timetable algorithm is in `timetable_generator.py` and exposed through a single function called by `timetable_routes.py`. The SM-2 algorithm lives entirely in `sm2.py`. Either module can be updated, tested, or replaced without touching the rest of the system.

**Abstraction**

`database_access.py` abstracts all SQL queries behind named functions. Route files call `get_user_timetable()`, `save_study_card()`, `save_module_data()`, and so on rather than writing raw SQL inline. This means the database schema can be changed without touching route files.

**ACID Compliance**

ACID compliance is provided by PostgreSQL via Supabase. Every write is wrapped in psycopg2's default transaction handling: a commit is issued on success and a rollback occurs automatically on exception. The `get_conn()` dependency guarantees every connection is closed in a `finally` block. For the study plan feature, SM-2 card state updates (interval, easiness factor, next review date) are written atomically so a failed review cannot leave a card in a partially-updated state.

---

## Testing

**Manual Functional Testing**

All features were verified through manual end-to-end testing by the development team before each milestone submission.

- **Module Analysis:** Searched a range of modules (CS2040S, CS2030S, MA1521, GEA1000, CFG1002) and verified that difficulty scores, recommendation percentages, GPA figures, and AI summaries rendered correctly. Tested edge cases: modules with no Disqus comments (returns zeros), invalid module codes (returns 400), and repeat lookups of cached modules (returns immediately from cache).

- **Timetable Builder:** Added multiple modules, selected conflicting slots (verified they were blocked), ran the auto-generator for 3–4 module combinations, and confirmed the top 5 results were all conflict-free. Exported to iCal and confirmed the file opened correctly in Apple Calendar. Tested the shareable link on a separate browser without login.

- **Study Timer and Leaderboard:** Started and stopped sessions, refreshed the 7-day chart, and verified session durations matched expected values. Created a study group, joined it from a second browser session using the invite code, and confirmed both users appeared on the group leaderboard.

- **CourseReg Advisor:** Searched modules with varying slot counts and verified that competition scores and probability badges rendered for all lesson types. Confirmed that platform demand counts updated after making timetable slot selections.

- **Study Plan:** Added an exam with multiple topics, stepped through daily review cards, rated cards at different quality levels, and verified that next review dates updated according to SM-2 intervals (1 day → 6 days → exponential growth). Exported the schedule to iCal and confirmed correct dates.

- **Authentication:** Tested Google sign-in from fresh sessions (no localStorage), sign-in from a session with an existing user (upsert path), and attempted access to protected routes without logging in (verified redirect to `/login`).

---

## Project Management

**Division of Labour**

The project is split along the full-stack boundary. Papangkorn is responsible for the backend: FastAPI route files, the NLP pipeline (VADER, BART, Gemini), database schema and queries, the backtracking timetable algorithm, and all external API integrations (NUSMods, Disqus). Piyaphat is responsible for the frontend: all React pages and components, state management, Google OAuth integration, Vite configuration, and deployment setup on Render.

**Communication and Workflow**

Day-to-day coordination uses WhatsApp for task discussion and decision-making. All code is tracked in a single GitHub repository. Both members commit directly to the main branch at natural feature completion points, pulling the latest changes before starting new work. This keeps the integration loop short and avoids prolonged divergence between the backend and frontend.

**Development Process**

Backend and frontend development are sequenced so that API endpoints and database schemas are defined first. The frontend is then built to consume those endpoints. This boundary means both members can work in parallel with minimal merge conflicts. The project log records the specific tasks and hours contributed by each member across all milestones.

---

## Milestone Roadmap

**Milestone 1: Core Features**

1. Sentiment analysis: VADER, BART (later migrated to Gemini)
2. APIs: NUSMods, Disqus
3. Algorithms: Backtracking timetable generation, SM-2 spaced repetition
4. Frontend: React + Vite

**Milestone 2 (current): Minimum Viable Product**

1. CourseReg probability analysis
2. iCal export for timetable and study plan
3. PostgreSQL migration (SQLite → Supabase)
4. Hosting on Render (backend) + Supabase (database)
5. Google OAuth 2.0 login
6. Gemini AI module summary (replaced BART)
7. Module Comparison page
8. Study Timer with global leaderboard and study groups
9. Study Plan with SM-2 spaced repetition
10. Home page dashboard with AY2026/2027 CourseReg countdown

**Milestone 3: Additional Features and Quality of Life**

1. Friends/connections system
2. Timetable import/export (NUSMods URL)
3. Profile customisation (avatar, XP, level badges)
4. Reddit API for broader comment corpus
5. Automated testing

---

## Project Log

- **Week 1 (13–19 May):** Project proposal, repo bootstrap, NUSMods + Disqus API exploration, VADER sentiment pipeline prototyped.
- **Week 2 (20–26 May):** BART zero-shot integration (later migrated to Gemini), grade-extraction regex, PostgreSQL schema and caching layer, FastAPI router split.
- **Week 3 (27 May – 1 June):** React frontend, timetable grid, timer + leaderboard, SM-2 study planner, Google OAuth, Milestone 1 document.
- **Week 4 (2–8 June):** Module Analysis page with autocomplete search, Top Modules discovery panel, no-reviews message, responsive grids.
- **Week 5 (9–15 June):** Backtracking timetable auto-generator (`timetable_generator.py`), preference sliders, Generate modal with apply flow, timetable share links with 30-day TTL, shared timetable read-only view.
- **Week 6 (16–22 June):** Study plan streak tracking, per-card and per-exam deletion, iCal export. BART to Gemini migration (difficulty scoring, summary). Print support for timetable. CourseReg Advisor. Home dashboard. Milestone 2 document.

---

## Production Deployment

The application is live at: **https://orbital-frontend-i7gq.onrender.com**

- **Backend:** Render Web Service (Python, root directory: `backend`, start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`)
- **Frontend:** Render Static Site (root directory: `frontend`, build command: `npm install && npm run build`, publish directory: `dist`)
- **Database:** Supabase PostgreSQL (connection pooler for IPv4 compatibility on free tier)
- **Secrets:** Stored as Render environment variables (`DATABASE_URL`, `GEMINI_API_KEY`, `DISQUS_API_KEY`, `GOOGLE_CLIENT_ID`). Not committed to the repository.

---

## Links

- **Live app:** https://orbital-frontend-i7gq.onrender.com
- **Demo video:** TBA
- **Poster:** TBA
- **GitHub repo:** private — invite sent to evaluators on request
