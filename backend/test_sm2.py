from datetime import date, timedelta
import pytest
from sm2 import review_card


def test_low_quality_resets_to_interval_1():
    interval, ef, reps, next_date = review_card(10, 2.5, 5, 2)
    assert interval == 1
    assert reps == 0


def test_low_quality_resets_repetitions():
    for q in (0, 1, 2):
        interval, ef, reps, _ = review_card(10, 2.5, 5, q)
        assert reps == 0, f"quality {q} should reset reps"
        assert interval == 1, f"quality {q} should reset interval to 1"


def test_first_repetition_interval():
    interval, ef, reps, _ = review_card(1, 2.5, 0, 5)
    assert interval == 1
    assert reps == 1


def test_second_repetition_interval():
    interval, ef, reps, _ = review_card(1, 2.5, 1, 5)
    assert interval == 6
    assert reps == 2


def test_third_repetition_multiplies_by_ef():
    ef_val = 2.5
    prev_interval = 6
    interval, new_ef, reps, _ = review_card(prev_interval, ef_val, 2, 5)
    assert interval == round(prev_interval * ef_val)
    assert reps == 3


def test_ef_clamped_to_minimum_1_3():
    # quality=0 causes maximum EF decrease
    _, ef, _, _ = review_card(1, 1.3, 1, 0)
    assert ef >= 1.3


def test_ef_increases_with_perfect_quality():
    _, ef, _, _ = review_card(1, 2.5, 1, 5)
    assert ef > 2.5


def test_ef_decreases_with_quality_3():
    _, ef, _, _ = review_card(1, 2.5, 1, 3)
    assert ef < 2.5


def test_next_review_date_is_today_plus_interval():
    interval, _, _, next_date = review_card(1, 2.5, 0, 5)
    expected = (date.today() + timedelta(days=interval)).isoformat()
    assert next_date == expected


def test_next_review_date_quality_5_second_rep():
    interval, _, _, next_date = review_card(1, 2.5, 1, 5)
    assert interval == 6
    expected = (date.today() + timedelta(days=6)).isoformat()
    assert next_date == expected


def test_ef_formula_quality_4():
    # EF change = 0.1 - (5-4)*(0.08 + (5-4)*0.02) = 0.1 - 0.10 = 0.0
    _, ef, _, _ = review_card(1, 2.5, 1, 4)
    assert abs(ef - 2.5) < 1e-9
