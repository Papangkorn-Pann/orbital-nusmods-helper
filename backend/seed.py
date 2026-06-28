"""
Pre-warm the module analysis cache for popular NUS modules.

Usage (backend must already be running on port 8000):
    # From the project root:
    .venv/bin/python3 backend/seed.py

    # Or from inside backend/:
    ../.venv/bin/python3 seed.py

Each module takes ~2-5 s on first run (Gemini API call for difficulty + summary).
Modules already cached at analysis_version >= 2 are skipped instantly.
Total time for a fully cold run: ~5-10 minutes.
"""

import time
import requests

BASE = "http://localhost:8000"

# 25 high-enrolment NUS modules across faculties likely to have Disqus reviews
MODULES = [
    # Computing core
    "CS1231S",  # Discrete Structures
    "CS2030S",  # Programming Methodology II
    "CS2040S",  # Data Structures & Algorithms
    "CS2100",   # Computer Organisation
    "CS2101",   # Effective Communication for Computing Professionals
    "CS2103T",  # Software Engineering
    "CS2105",   # Introduction to Computer Networks
    "CS2106",   # Introduction to Operating Systems
    "CS3230",   # Design and Analysis of Algorithms
    "CS3243",   # Introduction to Artificial Intelligence
    # Mathematics / Stats
    "MA1521",   # Calculus for Computing
    "MA1522",   # Linear Algebra for Computing
    "ST2334",   # Probability and Statistics
    # General Education
    "GEA1000",  # Quantitative Reasoning with Data
    "GEC1015",  # Pros and Cons of Globalisation
    "IS1108",   # Digital Ethics and Data Privacy
    # Science
    "LSM1301",  # General Biology
    "PC1432",   # Physics IIE
    # Business / Economics
    "BT1101",   # Introduction to Business Analytics
    "EC1301",   # Principles of Economics
    # FASS
    "PH1102E",  # Introduction to Philosophy
    "EL1101E",  # The Nature of Language
    # Engineering
    "EE2026",   # Digital Design
    # Language
    "LAJ1201",  # Japanese 1
    # Cross-faculty popular
    "CS4248",   # Natural Language Processing
]


def seed():
    print(f"Seeding {len(MODULES)} modules. Backend must be running at {BASE}.\n")

    for i, code in enumerate(MODULES, 1):
        print(f"[{i:2}/{len(MODULES)}] {code} ... ", end="", flush=True)
        try:
            r = requests.get(f"{BASE}/course/{code}", timeout=180)
            if r.status_code == 200:
                data = r.json()
                reviews = data.get("comment_count", 0)
                cached  = "(cached)" if reviews > 0 else "(no reviews)"
                print(f"OK  {reviews} reviews {cached}")
            elif r.status_code == 503:
                # Analyser busy — wait and retry once
                print("busy, retrying in 10 s ... ", end="", flush=True)
                time.sleep(10)
                r = requests.get(f"{BASE}/course/{code}", timeout=180)
                print("OK" if r.status_code == 200 else f"failed ({r.status_code})")
            else:
                print(f"failed ({r.status_code})")
        except requests.exceptions.Timeout:
            print("timed out (>180 s) — skipping")
        except Exception as e:
            print(f"error: {e}")

        # Small pause to be polite to the Disqus API
        time.sleep(3)

    print("\nDone. All modules are now cached.")


if __name__ == "__main__":
    seed()
