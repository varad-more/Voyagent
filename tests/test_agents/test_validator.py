"""
Tests for the ValidatorAgent (rule-based, no AI needed).
"""
import pytest

from trip_planner.agents.validator import ValidatorAgent


class TestValidatorScheduleChecks:
    def test_valid_schedule_passes(self, sample_trip):
        agent = ValidatorAgent()

        schedule = {
            "days": [{
                "date": "2026-04-01",
                "schedule": [
                    {"start_time": "09:00", "end_time": "11:30", "title": "Morning"},
                    {"start_time": "12:00", "end_time": "13:30", "title": "Lunch"},
                    {"start_time": "14:00", "end_time": "17:00", "title": "Afternoon"},
                ]
            }]
        }

        result = agent.run(trip=sample_trip, scheduler_output=schedule)
        statuses = [v["status"] for v in result.data["validation"]]
        assert "fail" not in statuses
        assert "pass" in statuses

    def test_overlapping_blocks_detected(self, sample_trip):
        agent = ValidatorAgent()

        schedule = {
            "days": [{
                "date": "2026-04-01",
                "schedule": [
                    {"start_time": "09:00", "end_time": "11:30", "title": "Morning"},
                    {"start_time": "11:00", "end_time": "13:00", "title": "Overlapping"},  # overlaps!
                ]
            }]
        }

        result = agent.run(trip=sample_trip, scheduler_output=schedule)
        overlap_issues = [v for v in result.data["validation"] if v["check"] == "overlap"]
        assert len(overlap_issues) == 1
        assert overlap_issues[0]["status"] == "fail"

    def test_outside_daily_window_warned(self, sample_trip):
        agent = ValidatorAgent()

        schedule = {
            "days": [{
                "date": "2026-04-01",
                "schedule": [
                    {"start_time": "06:00", "end_time": "08:00", "title": "Too Early"},  # before 09:00
                ]
            }]
        }

        result = agent.run(trip=sample_trip, scheduler_output=schedule)
        window_issues = [v for v in result.data["validation"] if v["check"] == "daily_window"]
        assert len(window_issues) == 1
        assert window_issues[0]["status"] == "warn"

    def test_invalid_time_order_detected(self, sample_trip):
        agent = ValidatorAgent()

        schedule = {
            "days": [{
                "date": "2026-04-01",
                "schedule": [
                    {"start_time": "14:00", "end_time": "12:00", "title": "Backwards"},  # end before start!
                ]
            }]
        }

        result = agent.run(trip=sample_trip, scheduler_output=schedule)
        order_issues = [v for v in result.data["validation"] if v["check"] == "block_time_order"]
        assert len(order_issues) == 1
        assert order_issues[0]["status"] == "fail"

    def test_empty_schedule(self, sample_trip):
        agent = ValidatorAgent()
        result = agent.run(trip=sample_trip, scheduler_output={"days": []})
        assert any(v["status"] == "pass" for v in result.data["validation"])

    def test_multiple_days_validated(self, sample_trip):
        agent = ValidatorAgent()

        schedule = {
            "days": [
                {"date": "2026-04-01", "schedule": [
                    {"start_time": "09:00", "end_time": "12:00", "title": "Day 1"},
                ]},
                {"date": "2026-04-02", "schedule": [
                    {"start_time": "09:00", "end_time": "12:00", "title": "Day 2 Morning"},
                    {"start_time": "13:00", "end_time": "17:00", "title": "Day 2 Afternoon"},
                ]},
            ]
        }

        result = agent.run(trip=sample_trip, scheduler_output=schedule)
        statuses = [v["status"] for v in result.data["validation"]]
        assert "fail" not in statuses

    def test_warnings_counted(self, sample_trip):
        agent = ValidatorAgent()

        schedule = {
            "days": [{
                "date": "2026-04-01",
                "schedule": [
                    {"start_time": "14:00", "end_time": "12:00", "title": "Bad Order"},  # fail
                    {"start_time": "11:00", "end_time": "13:00", "title": "Overlap"},     # overlap with prev end
                ]
            }]
        }

        result = agent.run(trip=sample_trip, scheduler_output=schedule)
        assert len(result.data["warnings"]) > 0
        assert "timing issues" in result.data["warnings"][0].lower()

    def test_end_after_daily_window(self, sample_trip):
        agent = ValidatorAgent()

        schedule = {
            "days": [{
                "date": "2026-04-01",
                "schedule": [
                    {"start_time": "19:00", "end_time": "22:00", "title": "Late Night"},  # after 20:00
                ]
            }]
        }

        result = agent.run(trip=sample_trip, scheduler_output=schedule)
        window_issues = [v for v in result.data["validation"] if v["check"] == "daily_window"]
        assert len(window_issues) == 1
