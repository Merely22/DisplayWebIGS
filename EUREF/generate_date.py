from __future__ import annotations
from datetime import date, datetime, timedelta, timezone

__all__ = [
    "calculate_date",
    "is_within_range",
    "doy_from_date",
    "parse_iso_date",
]

def calculate_date(year: int, month: int, day: int) -> int:
    """Devuelve el día del año (DOY) para una fecha (1..366)."""
    return int(date(year, month, day).strftime("%j"))

def doy_from_date(dt: date | datetime) -> int:
    """Devuelve DOY para `date` o `datetime`."""
    if isinstance(dt, datetime):
        dt = dt.date()
    return int(dt.strftime("%j"))

def is_within_range(dt: date | datetime, max_days: int = 182) -> tuple[bool, int]:
    """
    Indica si `dt` está dentro de los últimos `max_days` días respecto a hoy (UTC).
    Retorna (en_rango, dias_diff) donde dias_diff es la diferencia absoluta en días.
    """
    if isinstance(dt, datetime):
        dt = dt.date()
    today = datetime.now(timezone.utc).date()
    delta = abs(today - dt)
    return delta.days <= max_days, delta.days

def parse_iso_date(iso_str: str) -> date:
    """Parses 'YYYY-MM-DD' a date (sin timezone)."""
    return datetime.strptime(iso_str, "%Y-%m-%d").date()
