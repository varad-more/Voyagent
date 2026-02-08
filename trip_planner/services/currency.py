"""
Currency exchange rate service.
"""
import logging
import requests
from django.conf import settings
from trip_planner.core.cache import cache_client

logger = logging.getLogger(__name__)


def get_currency_rate(base: str, target: str) -> dict:
    """Get exchange rate between currencies."""
    if base.upper() == target.upper():
        return {"rate": 1.0}
    
    cached = cache_client.get_currency_rate(base, target)
    if cached is not None:
        return {"rate": cached}
    
    api_key = settings.CURRENCY_API_KEY
    if not api_key:
        cache_client.set_currency_rate(base, target, 1.0)
        return {"rate": 1.0}
    
    try:
        resp = requests.get(
            "https://api.exchangerate.host/latest",
            params={"base": base.upper(), "symbols": target.upper(), "access_key": api_key},
            timeout=10
        )
        resp.raise_for_status()
        rate = resp.json().get("rates", {}).get(target.upper(), 1.0)
        cache_client.set_currency_rate(base, target, rate)
        return {"rate": rate}
    except Exception as e:
        logger.error(f"Currency API failed: {e}")
        cache_client.set_currency_rate(base, target, 1.0)
        return {"rate": 1.0}


def convert_amount(amount: float, from_curr: str, to_curr: str) -> float:
    """Convert amount between currencies."""
    if from_curr.upper() == to_curr.upper():
        return amount
    rate = get_currency_rate(from_curr, to_curr).get("rate", 1.0)
    return round(amount * rate, 2)
