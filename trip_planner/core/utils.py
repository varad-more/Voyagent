"""
Utility functions.
"""
import json
import re
from typing import Any, Union
from datetime import datetime, date, time, timezone


def extract_json_blob(text: str) -> str | None:
    """Extract JSON object from text."""
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1 or last <= first:
        return None
    return text[first:last + 1]


def best_effort_json(text: str) -> Union[dict, list]:
    """Parse JSON with best effort extraction."""
    # Try direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # Try extracting object
    candidate = extract_json_blob(text)
    if candidate:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    
    # Try removing markdown fences
    cleaned = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
    
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass
    
    candidate = extract_json_blob(cleaned)
    if candidate:
        return json.loads(candidate)
    
    return json.loads(text)


def build_ics(itinerary_data: dict) -> str:
    """Build ICS calendar file from itinerary data."""
    def format_dt(d: date, t: time) -> str:
        combined = datetime.combine(d, t).replace(tzinfo=timezone.utc)
        return combined.strftime("%Y%m%dT%H%M%SZ")
    
    def escape_text(text: str) -> str:
        if not text:
            return ""
        return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Trip Planner//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    
    itinerary_id = itinerary_data.get("itinerary_id", "trip")
    
    for day in itinerary_data.get("days", []):
        day_date = day.get("date")
        if isinstance(day_date, str):
            day_date = date.fromisoformat(day_date)
        
        for block in day.get("schedule", []):
            start_time = block.get("start_time")
            end_time = block.get("end_time")
            
            if isinstance(start_time, str):
                start_time = time.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = time.fromisoformat(end_time)
            
            title = block.get("title", "Activity")
            location = block.get("location", "")
            description = block.get("description", "")
            uid = f"{itinerary_id}-{day_date}-{title}".replace(" ", "-").replace(",", "")
            
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTART:{format_dt(day_date, start_time)}",
                f"DTEND:{format_dt(day_date, end_time)}",
                f"SUMMARY:{escape_text(title)}",
                f"LOCATION:{escape_text(location)}",
                f"DESCRIPTION:{escape_text(description)}",
                "STATUS:CONFIRMED",
                "END:VEVENT",
            ])
    
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
