from unittest.mock import patch
import timetable_generator
from timetable_generator import _to_min, generate_timetables


# ── _to_min ───────────────────────────────────────────────────────────────────

def test_to_min_0900():
    assert _to_min("0900") == 540


def test_to_min_1400():
    assert _to_min("1400") == 840


def test_to_min_midnight():
    assert _to_min("0000") == 0


def test_to_min_1730():
    assert _to_min("1730") == 17 * 60 + 30


# ── generate_timetables: empty / no slots ─────────────────────────────────────

def test_empty_module_list():
    results = generate_timetables([], sem=1, preferences={})
    assert results == []


def test_no_slots_from_api():
    with patch("timetable_generator.api.fetch_module_slots", return_value=[]):
        results = generate_timetables(["CS1010"], sem=1, preferences={})
    assert results == []


# ── generate_timetables: conflict detection ───────────────────────────────────

def _make_slot(module, lesson_type, class_no, day, start, end, venue="LT27"):
    return {
        "moduleCode": module,
        "lessonType": lesson_type,
        "classNo": class_no,
        "day": day,
        "startTime": start,
        "endTime": end,
        "venue": venue,
    }


def test_non_conflicting_slots_produce_result():
    # CS1010 Lecture on Monday 08:00-10:00, CS2040 Lecture on Monday 10:00-12:00
    slots_cs1010 = [_make_slot("CS1010", "Lecture", "1", "Monday", "0800", "1000")]
    slots_cs2040 = [_make_slot("CS2040", "Lecture", "1", "Monday", "1000", "1200")]

    def fake_fetch(code, sem):
        return slots_cs1010 if code == "CS1010" else slots_cs2040

    with patch("timetable_generator.api.fetch_module_slots", side_effect=fake_fetch):
        results = generate_timetables(["CS1010", "CS2040"], sem=1, preferences={})

    assert len(results) >= 1


def test_conflicting_slots_produce_no_result():
    # Both modules want Monday 09:00-11:00 — only one class option each, they clash
    slots_cs1010 = [_make_slot("CS1010", "Lecture", "1", "Monday", "0900", "1100")]
    slots_cs2040 = [_make_slot("CS2040", "Lecture", "1", "Monday", "0900", "1100")]

    def fake_fetch(code, sem):
        return slots_cs1010 if code == "CS1010" else slots_cs2040

    with patch("timetable_generator.api.fetch_module_slots", side_effect=fake_fetch):
        results = generate_timetables(["CS1010", "CS2040"], sem=1, preferences={})

    assert results == []


def test_conflicting_and_non_conflicting_options():
    # CS2040 has two tutorial options: one conflicts with CS1010 lecture, one doesn't
    slots_cs1010 = [_make_slot("CS1010", "Lecture", "1", "Monday", "1000", "1200")]
    slots_cs2040 = [
        _make_slot("CS2040", "Tutorial", "1", "Monday", "1000", "1100"),  # conflict
        _make_slot("CS2040", "Tutorial", "2", "Monday", "1400", "1500"),  # no conflict
    ]

    def fake_fetch(code, sem):
        return slots_cs1010 if code == "CS1010" else slots_cs2040

    with patch("timetable_generator.api.fetch_module_slots", side_effect=fake_fetch):
        results = generate_timetables(["CS1010", "CS2040"], sem=1, preferences={})

    assert len(results) == 1
    # The result should have picked tutorial group 2
    sels = results[0]["selections"]
    tutorial = next(s for s in sels if s["lesson_type"] == "Tutorial")
    assert tutorial["class_no"] == "2"


def test_result_contains_required_keys():
    slots = [_make_slot("CS1010", "Lecture", "1", "Tuesday", "1000", "1200")]

    with patch("timetable_generator.api.fetch_module_slots", return_value=slots):
        results = generate_timetables(["CS1010"], sem=1, preferences={})

    assert len(results) >= 1
    r = results[0]
    assert "score" in r
    assert "selections" in r
    assert "rendered_slots" in r
