from bs4 import BeautifulSoup #for formatting (turning html into plain text)

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer #sorting comments positive/neutral/negative
analyzer = SentimentIntensityAnalyzer()

import re

def clean_comment_message(comment):
    #Convert HTML to plain text
    comment_message_plaintext = BeautifulSoup(comment["message"], "html.parser").get_text(separator="\n")

    #Remove extra        whitespace (lol)
    comment_message_cleaned = re.sub(r'\s+', ' ', comment_message_plaintext).strip()

    return comment_message_cleaned.strip()

#sentiment value breakpoints obtained from
#https://ak1adyous.medium.com/sentiment-analysis-using-vader-c56bcffe6f24
def analyze_sentiment(comment):
    cleaned = clean_comment_message(comment)

    score = analyzer.polarity_scores(cleaned)["compound"]
    if score >= 0.05:
        return "positive"
    elif score <= -0.05:
        return "negative"
    else:
        return "neutral"

_GEMINI_MODELS = ["models/gemini-2.5-flash-lite", "models/gemini-2.5-flash"]


def _gemini_generate(client, prompt, retries=3):
    """
    Call Gemini, retrying transient 503/429 overload errors with exponential
    backoff. If the primary model stays overloaded, fall back to the next model.
    Raises the last error if every attempt fails.
    """
    import time
    last_err = None
    for model in _GEMINI_MODELS:
        for attempt in range(retries):
            try:
                return client.models.generate_content(model=model, contents=prompt)
            except Exception as e:
                last_err = e
                msg = str(e)
                transient = any(t in msg for t in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"))
                if not transient:
                    raise
                time.sleep(2 ** attempt)  # 1s, 2s, 4s
    raise last_err


def analyze_difficulty_gemini(texts: list) -> float | None:
    """
    Send up to 50 review texts to Gemini and return a difficulty score 1.0–5.0.
    Returns None if the API call fails or no texts are provided.
    """
    if not texts:
        return None
    from config import GEMINI_API_KEY as api_key
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        combined = "\n\n---\n\n".join(texts[:50])
        if len(combined) > 8000:
            combined = combined[:8000]
        prompt = (
            "You are rating the difficulty of an NUS university module based on student reviews. "
            "Read ALL the reviews below carefully. "
            "Return ONLY a single decimal number between 1.0 and 5.0 representing overall difficulty "
            "(1.0=very easy, 2.0=easy, 3.0=moderate, 4.0=hard, 5.0=very hard). "
            "No explanation, no units, just the number.\n\n"
            f"Reviews:\n{combined}"
        )
        response = _gemini_generate(client, prompt)
        import re as _re
        m = _re.search(r'\d+\.?\d*', response.text or "")
        if not m:
            return None
        return max(1.0, min(5.0, float(m.group())))
    except Exception as e:
        print(f"Gemini difficulty scoring failed: {e}")
        return None

grade_map = {
    "A+": 5.0,
    "A": 5.0,
    "A-": 4.5,
    "B+": 4.0,
    "B": 3.5,
    "B-": 3.0,
    "C+": 2.5,
    "C": 2.0,
    "D+": 1.5,
    "D": 1.0,
    "F": 0.0
}

# Keywords that indicate a sentence is about a specific component, not the overall grade
_COMPONENT_RE = re.compile(
    r'\b(?:midterm|midterms?|finals?\s+exam|finals?|quiz(?:zes)?|assignment|'
    r'lab(?:\s+report)?|project\s+component|CA\d?|homework|hw|'
    r'problem\s+set|pset|tutorial\s+part|participation|oral)\b',
    re.IGNORECASE
)

def _has_component_context(text):
    return bool(_COMPONENT_RE.search(text))

def extract_expected_gpa(comment):

    pattern = r"""
    (?:expected\s*grade|
    predicted\s*grade|
    expecting|
    expect|
    predicting|
    projected\s*grade|
    estimated\s*grade|
    anticipated\s*grade|
    forecasted\s*grade
    )
    \s*[:\-]?\s* #account for symbols
    (A\+|A-|A|B\+|B-|B|C\+|C-|C|D\+|D|F)
    """

    cleaned = clean_comment_message(comment)
    for sent in re.split(r'[.!?\n]', cleaned):
        if _has_component_context(sent):
            continue
        match = re.search(pattern, sent, re.IGNORECASE | re.VERBOSE)
        if match:
            letter_grade = match.group(1).upper()
            return grade_map.get(letter_grade)

    return None #no match found

def extract_actual_gpa(comment):
    # Only match clear overall-grade patterns; "scored", "achieved", bare "grade" removed
    # to avoid picking up component scores like "scored A on midterm"
    pattern = r"""
    (?:got|
    received|
    ended\s*up\s*with|
    final\s*grade|
    ended\s*with|
    came\s*out\s*with
    )
    \s*[:\-]?\s*
    (A\+|A-|A|B\+|B-|B|C\+|C-|C|D\+|D|F)
    """

    cleaned = clean_comment_message(comment)
    for sent in re.split(r'[.!?\n]', cleaned):
        if _has_component_context(sent):
            continue
        match = re.search(pattern, sent, re.IGNORECASE | re.VERBOSE)
        if match:
            letter_grade = match.group(1).upper()
            return grade_map.get(letter_grade)

    return None #no match found


def extract_expected_grade_letter(comment):
    """Return the expected letter grade ('A-', 'B+', …) or None."""
    # F excluded: "expecting F" is colloquial for "expecting to fail", not a grade prediction
    pattern = r"""
    \b(?:expected\s*grade|
    predicted\s*grade|
    expecting|
    expect(?:ed)?|
    predicting|
    projected\s*grade|
    estimated\s*grade|
    anticipated\s*grade
    )
    \s*[:\-]?\s*
    (?:an?\s+)?
    (A\+|A-|A|B\+|B-|B|C\+|C-|C|D\+|D)
    (?![-+\w])
    """
    cleaned = clean_comment_message(comment)
    for sent in re.split(r'[.!?\n]', cleaned):
        if _has_component_context(sent):
            continue
        match = re.search(pattern, sent, re.IGNORECASE | re.VERBOSE)
        if match:
            return match.group(1).upper().replace(' ', '')
    return None


def extract_actual_grade_letter(comment):
    """Return the actual final letter grade or None."""
    pattern = r"""
    \b(?:got|
    received|
    ended\s*up\s*with|
    final\s*grade|
    ended\s*with|
    came\s*out\s*with
    )
    \s*[:\-]?\s*
    (?:an?\s+)?
    (A\+|A-|A|B\+|B-|B|C\+|C-|C|D\+|D|F)
    (?![-+\w])
    """
    cleaned = clean_comment_message(comment)
    for sent in re.split(r'[.!?\n]', cleaned):
        if _has_component_context(sent):
            continue
        match = re.search(pattern, sent, re.IGNORECASE | re.VERBOSE)
        if match:
            return match.group(1).upper().replace(' ', '')
    return None


# ── Summarisation ─────────────────────────────────────────────────────────────

from collections import Counter

_STOPWORDS = {
    'the','a','an','is','it','in','of','and','to','i','for','that','this','was',
    'are','with','as','at','be','by','from','or','but','not','have','has','had',
    'my','me','we','you','he','she','they','so','if','do','did','will','can','on',
    'its','also','very','your','our','their','which','who','what','just','been',
    'when','would','could','should','than','then','there','some','more','about',
    'one','all','up','out','module','course','class','sem','semester','nus',
}

def extractive_summarize(texts, num_sentences=5):
    if not texts:
        return None
    combined = ' '.join(texts)
    raw_sentences = re.split(r'(?<=[.!?])\s+', combined)
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 40]
    if not sentences:
        return None
    words = re.findall(r'\b[a-z]+\b', combined.lower())
    freq = Counter(w for w in words if w not in _STOPWORDS and len(w) > 2)
    if not freq:
        return None
    def score(sent):
        ws = re.findall(r'\b[a-z]+\b', sent.lower())
        return sum(freq.get(w, 0) for w in ws) / max(len(ws), 1)
    scored = sorted(enumerate(sentences), key=lambda x: score(x[1]), reverse=True)
    top_idx = sorted([i for i, _ in scored[:num_sentences]])
    return ' '.join(sentences[i] for i in top_idx)



_TOPIC_PATTERNS = {
    'difficulty': r'\b(?:hard|difficult|challenging|easy|manageable|tough|demanding|doable|not\s+easy|very\s+hard)\b',
    'workload':   r'\b(?:workload|hours?\s+(?:per\s+week|a\s+week)|time-consuming|heav[yi]|rush(?:ed)?|deadline)\b',
    'content':    r'\b(?:interesting|boring|relevant|useful|fascinating|enjoyable|fun|content|topic|concept)\b',
    'teaching':   r'\b(?:prof(?:essor)?|lecturer|tutor|explain|helpful|clear|engaging|well.taught|good\s+teach)\b',
    'recommend':  r'\b(?:recommend|worth|take\s+it|avoid|must.take|would\s+(?:take|recommend)|don.t\s+take)\b',
    'assessment': r'\b(?:exam|test|assignment|project|grading|bell\s+curve|CA|quiz|problem\s+set|homework)\b',
    'tips':       r'\b(?:tip|advice|suggest|make\s+sure|don.t\s+skip|attend|read\s+ahead|prepare|pro\s+tip)\b',
}

def _collect_topic_sentences(texts, max_per_topic=3, max_total=15):
    """
    Collect up to max_per_topic sentences per topic from across all reviews.
    Returns sentences grouped by topic order, no duplicates.
    """
    topic_sents = {t: [] for t in _TOPIC_PATTERNS}
    used_sents = set()
    for text in texts[:50]:
        sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if 40 <= len(s.strip()) <= 220]
        for sent in sents:
            sent = re.sub(r'^\s*(?:\(?\d+[.)]\s*|[a-zA-Z][.)]\s*)', '', sent).strip()
            if not sent or sent in used_sents:
                continue
            for topic, pat in _TOPIC_PATTERNS.items():
                if len(topic_sents[topic]) < max_per_topic and re.search(pat, sent, re.IGNORECASE):
                    topic_sents[topic].append(sent)
                    used_sents.add(sent)
                    break
        if sum(len(v) for v in topic_sents.values()) >= max_total:
            break
    order = ['difficulty', 'content', 'workload', 'teaching', 'assessment', 'recommend', 'tips']
    result = []
    for t in order:
        result.extend(topic_sents[t])
    return result[:max_total]


def ai_summarize(texts):
    """
    Send all reviews to Gemini for a comprehensive AI-written summary.
    Returns (summary_text, gemini_succeeded: bool).
    Falls back to extractive sentence collection if the API call fails.
    """
    if not texts:
        return None, False

    from config import GEMINI_API_KEY as api_key
    from google import genai
    client = genai.Client(api_key=api_key)

    try:
        # Use all reviews, capped at ~8000 chars to stay within free-tier limits
        combined = "\n\n---\n\n".join(texts[:50])
        if len(combined) > 8000:
            combined = combined[:8000]

        prompt = (
            "You are summarising student reviews for an NUS university module. "
            "Read ALL the reviews below carefully. "
            "Write a comprehensive 5–8 sentence summary paragraph ENTIRELY IN THIRD PERSON — "
            "use language like 'Students find...', 'The module is...', 'Many reviewers note...'. "
            "NEVER use first-person pronouns (I, we, my, our). "
            "Cover: overall difficulty, course content and key topics, weekly workload, "
            "teaching quality, assessment structure (exams, assignments, projects), "
            "and whether students recommend the module. "
            "Be specific and factual — mention concrete details students raised. "
            "Do not use bullet points. Write in flowing prose.\n\n"
            f"Reviews:\n{combined}"
        )

        response = _gemini_generate(client, prompt)
        summary = (response.text or "").strip()
        if summary:
            return summary, True
    except Exception as e:
        print(f"Gemini summarisation failed: {type(e).__name__}: {e}")

    # No extractive copy-paste fallback: return None so the frontend shows a
    # placeholder. The module stays uncached (version 2) and re-runs next view.
    return None, False


# ── Grade threshold extraction ────────────────────────────────────────────────

import statistics

_GRADE_ORDER = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D']
_GRADE_PAT   = r'(?:A\+|A-|A|B\+|B-|B|C\+|C-|C|D\+|D)'

# Patterns: each yields (grade_or_score, score_or_grade) pairs
_THRESHOLD_PATTERNS = [
    # "got A with 85", "scored B+ with 75%", "received A- at 88 marks"
    rf'(?:got|scored|received|achieved|obtained|ended\s+up\s+(?:with)?|grade)\s+({_GRADE_PAT})\D{{0,15}}?(\d{{2,3}})',
    # "A: 85", "B+: 75-84", "A- – 88"
    rf'({_GRADE_PAT})\s*[:\-–]\s*(\d{{2,3}})',
    # "85 for A", "78 marks for B+", "need 80 for an A-"
    rf'(\d{{2,3}})\s*(?:%|marks?|points?)?\s+(?:for|to\s+get|gets?)\s+(?:an?\s+)?({_GRADE_PAT})',
    # "cutoff for A is 80", "A cutoff at 85", "A+ requires 90"
    rf'({_GRADE_PAT})\s+(?:cutoff|cut.off|requires?|needs?|minimum)\s+(?:is|was|at|of|around)?\s*(\d{{2,3}})',
    rf'(?:cutoff|cut.off|minimum)\s+(?:for\s+)?(?:an?\s+)?({_GRADE_PAT})\s+(?:is|was|at|around)?\s*(\d{{2,3}})',
    # "above 85 is A", "80 and above gets A-"
    rf'(\d{{2,3}})\s*(?:and\s+above|or\s+above|\+)?\s+(?:is|gets?|for)\s+(?:an?\s+)?({_GRADE_PAT})',
]

def extract_grade_thresholds(texts):
    """
    Parse self-reported overall grade scores from review texts.
    Returns an ordered dict {grade: median_score} for grades with data, or None.
    Sentences that reference individual components (midterm, quiz, lab, etc.) are skipped.
    """
    buckets: dict[str, list[int]] = {}

    for text in texts:
        # Process sentence by sentence; skip sentences about individual components
        for sent in re.split(r'[.!?\n]', text):
            if _has_component_context(sent):
                continue
            sent = re.sub(r'\s+', ' ', sent).strip()
            if not sent:
                continue
            for pat in _THRESHOLD_PATTERNS:
                for m in re.findall(pat, sent, re.IGNORECASE):
                    a, b = m[0].strip(), m[1].strip()
                    try:
                        if re.match(r'^\d+$', a):
                            score_val, grade = int(a), b.upper()
                        else:
                            grade, score_val = a.upper(), int(b)
                        grade = grade.replace(' ', '')
                        if grade in _GRADE_ORDER and 40 <= score_val <= 100:
                            buckets.setdefault(grade, []).append(score_val)
                    except (ValueError, IndexError):
                        continue

    if not buckets:
        return None

    result = {
        g: round(statistics.median(scores), 1)
        for g, scores in buckets.items()
        if scores
    }
    # Return in standard grade order
    ordered = {g: result[g] for g in _GRADE_ORDER if g in result}
    return ordered if ordered else None