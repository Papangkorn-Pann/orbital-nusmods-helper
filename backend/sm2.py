from datetime import date, timedelta


def review_card(interval: int, easiness_factor: float, repetitions: int, quality: int):
    """
    SM-2 spaced repetition algorithm.
    quality: 0-5  (5 = perfect recall, 0 = complete blackout)
    Returns (new_interval, new_easiness_factor, new_repetitions, next_review_date_iso)
    """
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
