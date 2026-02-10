"""
Tests for utility functions: best_effort_json, extract_json_blob, build_ics.
"""
import pytest
from datetime import date, time

from trip_planner.core.utils import best_effort_json, extract_json_blob, build_ics


# ---------------------------------------------------------------------------
# extract_json_blob
# ---------------------------------------------------------------------------

class TestExtractJsonBlob:
    def test_simple_object(self):
        assert extract_json_blob('{"key": "value"}') == '{"key": "value"}'

    def test_embedded_in_text(self):
        text = 'Here is the result: {"answer": 42} end.'
        assert extract_json_blob(text) == '{"answer": 42}'

    def test_no_json(self):
        assert extract_json_blob("no json here") is None

    def test_only_opening_brace(self):
        assert extract_json_blob("{ no closing") is None

    def test_nested_objects(self):
        text = '{"outer": {"inner": true}}'
        result = extract_json_blob(text)
        assert result == '{"outer": {"inner": true}}'


# ---------------------------------------------------------------------------
# best_effort_json
# ---------------------------------------------------------------------------

class TestBestEffortJson:
    def test_direct_json(self):
        result = best_effort_json('{"name": "Paris"}')
        assert result == {"name": "Paris"}

    def test_json_with_whitespace(self):
        result = best_effort_json('  \n  {"name": "Paris"}  \n  ')
        assert result == {"name": "Paris"}

    def test_markdown_fenced_json(self):
        text = '```json\n{"name": "Paris"}\n```'
        result = best_effort_json(text)
        assert result == {"name": "Paris"}

    def test_markdown_fenced_no_lang(self):
        text = '```\n{"name": "Paris"}\n```'
        result = best_effort_json(text)
        assert result == {"name": "Paris"}

    def test_embedded_json(self):
        text = 'Here is the output:\n{"cities": ["Paris", "London"]}\nDone.'
        result = best_effort_json(text)
        assert result == {"cities": ["Paris", "London"]}

    def test_invalid_json_raises(self):
        with pytest.raises(Exception):
            best_effort_json("completely invalid")

    def test_json_array(self):
        result = best_effort_json('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_nested_json(self):
        text = '{"a": {"b": {"c": 1}}}'
        result = best_effort_json(text)
        assert result["a"]["b"]["c"] == 1


# ---------------------------------------------------------------------------
# build_ics
# ---------------------------------------------------------------------------

class TestBuildIcs:
    def test_valid_ics_output(self):
        data = {
            "itinerary_id": "test-123",
            "days": [
                {
                    "date": "2026-04-01",
                    "schedule": [
                        {
                            "start_time": "09:00",
                            "end_time": "11:00",
                            "title": "Morning Visit",
                            "location": "Eiffel Tower",
                            "description": "Visit the tower",
                        }
                    ]
                }
            ]
        }
        ics = build_ics(data)
        assert "BEGIN:VCALENDAR" in ics
        assert "END:VCALENDAR" in ics
        assert "BEGIN:VEVENT" in ics
        assert "SUMMARY:Morning Visit" in ics
        assert "LOCATION:Eiffel Tower" in ics
        assert "20260401T" in ics

    def test_empty_days(self):
        ics = build_ics({"days": []})
        assert "BEGIN:VCALENDAR" in ics
        assert "BEGIN:VEVENT" not in ics

    def test_no_days_key(self):
        ics = build_ics({})
        assert "BEGIN:VCALENDAR" in ics

    def test_special_characters_escaped(self):
        data = {
            "itinerary_id": "test-esc",
            "days": [{
                "date": "2026-05-01",
                "schedule": [{
                    "start_time": "10:00",
                    "end_time": "12:00",
                    "title": "Café; brunch, time",
                    "location": "Le Marais, Paris",
                    "description": "Enjoy a meal\nwith friends",
                }]
            }]
        }
        ics = build_ics(data)
        assert "\\;" in ics
        assert "\\," in ics
        assert "\\n" in ics

    def test_multiple_days_multiple_blocks(self):
        data = {
            "itinerary_id": "multi",
            "days": [
                {"date": "2026-06-01", "schedule": [
                    {"start_time": "09:00", "end_time": "11:00", "title": "A", "location": "X", "description": ""},
                    {"start_time": "14:00", "end_time": "16:00", "title": "B", "location": "Y", "description": ""},
                ]},
                {"date": "2026-06-02", "schedule": [
                    {"start_time": "10:00", "end_time": "12:00", "title": "C", "location": "Z", "description": ""},
                ]},
            ]
        }
        ics = build_ics(data)
        assert ics.count("BEGIN:VEVENT") == 3
