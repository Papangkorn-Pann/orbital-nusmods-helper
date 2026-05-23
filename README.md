# orbital-nusmods-helper
Papangkorn's and Piyaphat's project for NUS Orbital 2026

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/orbital-nusmods-helper.git
cd orbital-nusmods-helper
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your Disqus API key:

```
DISQUS_API_KEY=your_disqus_api_key_here
```

---

## Backend

### Install dependencies

```bash
cd backend
python -m venv ../.venv
source ../.venv/bin/activate      # Windows: ..\.venv\Scripts\activate
pip install -r requirements.txt
```

> **Note:** Installing `torch` and `transformers` may take several minutes and requires ~2 GB of disk space.

### Run the backend

```bash
# From the backend/ directory, with .venv activated
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs are at `http://localhost:8000/docs`.

---

## Frontend

### Install dependencies

```bash
cd frontend
npm install
```

### Run the frontend

```bash
npm run dev
```

The app will be available at `http://localhost:5173`.

> The frontend proxies all `/api` requests to the backend at `http://localhost:8000`, so both servers must be running at the same time.

---

## Running both together

Open two terminal windows:

**Terminal 1 — Backend:**
```bash
cd backend
source ../.venv/bin/activate      # Windows: ..\.venv\Scripts\activate
uvicorn main:app --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Then open `http://localhost:5173` in your browser.
