"""
Booking Deep Link Generator.

Constructs pre-filled URLs for popular booking platforms
based on trip parameters (destination, dates, travelers).
No API keys required — just smart URL construction.
"""
from urllib.parse import quote_plus, urlencode
from datetime import date


def _fmt_date(d) -> str:
    """Format a date to YYYY-MM-DD string."""
    if isinstance(d, str):
        return d
    if isinstance(d, date):
        return d.isoformat()
    return str(d)


def _fmt_date_compact(d) -> str:
    """Format a date without dashes: YYYYMMDD (for Google Flights)."""
    return _fmt_date(d).replace("-", "")


def google_flights_url(origin: str, destination: str, depart: str, return_date: str = "",
                       adults: int = 1, children: int = 0) -> str:
    """Build a Google Flights deep link."""
    base = "https://www.google.com/travel/flights"
    params = {
        "q": f"flights from {origin} to {destination}",
        "curr": "USD",
    }
    # Google Flights search URL — the simplest way that auto-fills
    return f"{base}?{urlencode(params)}"


def skyscanner_url(origin: str, destination: str, depart: str, return_date: str = "",
                   adults: int = 1, children: int = 0) -> str:
    """Build a Skyscanner deep link."""
    dep = _fmt_date_compact(depart)
    ret = _fmt_date_compact(return_date) if return_date else ""
    dest_slug = quote_plus(destination.split(",")[0].strip().lower())
    origin_slug = quote_plus(origin.split(",")[0].strip().lower()) if origin else "anywhere"
    date_part = f"{dep}/{ret}" if ret else dep
    return f"https://www.skyscanner.com/transport/flights/{origin_slug}/{dest_slug}/{date_part}/"


def google_hotels_url(destination: str, checkin: str, checkout: str,
                      adults: int = 1, children: int = 0) -> str:
    """Build a Google Hotels deep link."""
    base = "https://www.google.com/travel/hotels"
    params = {
        "q": f"hotels in {destination}",
        "g2lb": "",
    }
    ci = _fmt_date(checkin)
    co = _fmt_date(checkout)
    return f"{base}?{urlencode(params)}&dates={ci},{co}&adults={adults}"


def booking_com_url(destination: str, checkin: str, checkout: str,
                    adults: int = 1, children: int = 0) -> str:
    """Build a Booking.com deep link."""
    base = "https://www.booking.com/searchresults.html"
    params = {
        "ss": destination,
        "checkin": _fmt_date(checkin),
        "checkout": _fmt_date(checkout),
        "group_adults": adults,
        "group_children": children,
        "no_rooms": 1,
    }
    return f"{base}?{urlencode(params)}"


def trainline_url(origin: str, destination: str, depart: str) -> str:
    """Build a Trainline deep link."""
    base = "https://www.thetrainline.com/book/results"
    params = {
        "origin": origin,
        "destination": destination,
        "outwardDate": _fmt_date(depart) + "T09:00:00",
        "journeySearchType": "single",
    }
    return f"{base}?{urlencode(params)}"


def rome2rio_url(origin: str, destination: str) -> str:
    """Build a Rome2Rio deep link (multi-modal transport search)."""
    o = quote_plus(origin) if origin else ""
    d = quote_plus(destination)
    return f"https://www.rome2rio.com/map/{o}/{d}" if o else f"https://www.rome2rio.com/s/{d}"


def generate_booking_links(trip: dict) -> dict:
    """
    Generate all booking deep links for a trip.

    Returns a dict with categorized links:
      - flights: list of {provider, url, label}
      - hotels: list of {provider, url, label}
      - trains: list of {provider, url, label}
      - transport: list of {provider, url, label}
    """
    dest = trip.get("destination", "")
    origin = trip.get("origin_location", "") or ""
    start = trip.get("start_date", "")
    end = trip.get("end_date", "")
    travelers = trip.get("travelers", {})
    adults = travelers.get("adults", 1) if isinstance(travelers, dict) else 1
    children = travelers.get("children", 0) if isinstance(travelers, dict) else 0

    # For multi-city trips, use first/last city
    cities = [c.strip() for c in dest.split("->")]
    first_city = cities[0] if cities else dest
    last_city = cities[-1] if len(cities) > 1 else first_city

    links = {
        "flights": [],
        "hotels": [],
        "trains": [],
        "transport": [],
    }

    # Flight links
    if origin:
        links["flights"].append({
            "provider": "Google Flights",
            "url": google_flights_url(origin, first_city, start, end, adults, children),
            "label": f"Search flights {origin} to {first_city}",
        })
        links["flights"].append({
            "provider": "Skyscanner",
            "url": skyscanner_url(origin, first_city, start, end, adults, children),
            "label": f"Compare on Skyscanner",
        })

    # Hotel links
    links["hotels"].append({
        "provider": "Google Hotels",
        "url": google_hotels_url(first_city, start, end, adults, children),
        "label": f"Hotels in {first_city}",
    })
    links["hotels"].append({
        "provider": "Booking.com",
        "url": booking_com_url(first_city, start, end, adults, children),
        "label": f"Hotels on Booking.com",
    })
    # If multi-city, add hotel links for the last city too
    if last_city != first_city:
        links["hotels"].append({
            "provider": "Google Hotels",
            "url": google_hotels_url(last_city, start, end, adults, children),
            "label": f"Hotels in {last_city}",
        })

    # Train links
    if origin:
        links["trains"].append({
            "provider": "Trainline",
            "url": trainline_url(origin, first_city, start),
            "label": f"Trains {origin} to {first_city}",
        })

    # General transport
    links["transport"].append({
        "provider": "Rome2Rio",
        "url": rome2rio_url(origin, first_city),
        "label": f"All transport options to {first_city}",
    })

    return links
