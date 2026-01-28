from __future__ import annotations

import datetime as dt

from app.schemas.itinerary import ItineraryResponse


def _format_dt(date: dt.date, time: dt.time) -> str:
    combined = dt.datetime.combine(date, time).replace(tzinfo=dt.timezone.utc)
    return combined.strftime("%Y%m%dT%H%M%SZ")


def build_ics(itinerary: ItineraryResponse) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Agentic Trip Planner//EN",
    ]
    for day in itinerary.days:
        for block in day.schedule:
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{itinerary.itinerary_id}-{day.date}-{block.title}".replace(" ", ""),
                    f"DTSTART:{_format_dt(day.date, block.start_time)}",
                    f"DTEND:{_format_dt(day.date, block.end_time)}",
                    f"SUMMARY:{block.title}",
                    f"LOCATION:{block.location}",
                    f"DESCRIPTION:{block.description}",
                    "END:VEVENT",
                ]
            )
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
