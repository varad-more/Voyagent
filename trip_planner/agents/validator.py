"""
Validator Agent - Validates schedule consistency.
"""
import logging
from datetime import time
from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class ValidatorAgent(BaseAgent):
    """Rule-based schedule validation (no AI needed)."""
    name = "validator"
    
    def run(self, trip: dict, scheduler_output: dict) -> AgentResult:
        validations = []
        warnings = []
        
        daily_start = trip.get("daily_start_time", "09:00")
        daily_end = trip.get("daily_end_time", "20:00")
        
        if isinstance(daily_start, str):
            daily_start = time.fromisoformat(daily_start)
        if isinstance(daily_end, str):
            daily_end = time.fromisoformat(daily_end)
        
        for day in scheduler_output.get("days", []):
            day_date = day.get("date")
            last_end = None
            
            for block in day.get("schedule", []):
                start = block.get("start_time")
                end = block.get("end_time")
                title = block.get("title", "Untitled")
                
                if isinstance(start, str):
                    start = time.fromisoformat(start)
                if isinstance(end, str):
                    end = time.fromisoformat(end)
                
                # Check: start < end
                if start >= end:
                    validations.append({
                        "check": "block_time_order", "status": "fail",
                        "details": f"{day_date}: '{title}' has invalid times."
                    })
                
                # Check: within daily window
                if start < daily_start or end > daily_end:
                    validations.append({
                        "check": "daily_window", "status": "warn",
                        "details": f"{day_date}: '{title}' outside daily window."
                    })
                
                # Check: overlap
                if last_end and start < last_end:
                    validations.append({
                        "check": "overlap", "status": "fail",
                        "details": f"{day_date}: '{title}' overlaps previous item."
                    })
                
                last_end = end
        
        if not validations:
            validations.append({
                "check": "schedule_consistency", "status": "pass",
                "details": "Schedule validated successfully."
            })
        else:
            failures = [v for v in validations if v["status"] == "fail"]
            if failures:
                warnings.append(f"Found {len(failures)} timing issues.")
        
        return AgentResult(data={"validation": validations, "warnings": warnings}, drafts=[], issues=[])
