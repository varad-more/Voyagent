from __future__ import annotations

import datetime as dt

from app.agents.base import AgentResult, BaseAgent
from app.schemas.agents import ValidatorOutput
from app.schemas.itinerary import TripRequest, ValidationResult


class ValidatorAgent(BaseAgent):
    name = "validator"

    async def run(self, *, trip: TripRequest, scheduler_output) -> AgentResult:
        validations: list[ValidationResult] = []
        warnings: list[str] = []

        for day in scheduler_output.days:
            last_end: dt.time | None = None
            for block in day.schedule:
                if block.start_time >= block.end_time:
                    validations.append(
                        ValidationResult(
                            check="block_time_order",
                            status="fail",
                            details=f"{day.date} block '{block.title}' has invalid times.",
                        )
                    )
                if block.start_time < trip.daily_start_time or block.end_time > trip.daily_end_time:
                    validations.append(
                        ValidationResult(
                            check="daily_window",
                            status="warn",
                            details=f"{day.date} block '{block.title}' outside daily window.",
                        )
                    )
                if last_end and block.start_time < last_end:
                    validations.append(
                        ValidationResult(
                            check="overlap",
                            status="fail",
                            details=f"{day.date} block '{block.title}' overlaps prior item.",
                        )
                    )
                last_end = block.end_time

        if not validations:
            validations.append(
                ValidationResult(
                    check="schedule_consistency",
                    status="pass",
                    details="Schedule timing validated with no overlaps.",
                )
            )
        else:
            warnings.append("Review flagged schedule items for timing conflicts.")

        output = ValidatorOutput(validation=validations, warnings=warnings)
        return AgentResult(data=output, drafts=[], issues=[])
