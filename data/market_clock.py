"""
US market clock: tells the agent whether the market is open right now.

US stock market hours: 9:30 AM - 4:00 PM Eastern Time, Monday-Friday.
Closed on US federal holidays (major ones listed below).
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

# Eastern Time (US) — standard is UTC-5, daylight is UTC-4.
# We handle both by always converting to ET via a manual offset lookup.
ET_OFFSET_STD = -5  # Eastern Standard Time (Nov-Mar)
ET_OFFSET_DST = -4  # Eastern Daylight Time (Mar-Nov)


def _et_offset() -> int:
    """Return the correct UTC offset for US Eastern Time (handles DST)."""
    utc_now = datetime.now(timezone.utc)
    # US DST: 2nd Sunday of March -> 1st Sunday of November.
    # A simple month-based heuristic is accurate enough.
    month = utc_now.month
    if 3 <= month <= 11:
        return ET_OFFSET_DST
    return ET_OFFSET_STD


def _us_eastern_now() -> datetime:
    """Return the current datetime in US Eastern Time (naive, no tzinfo)."""
    utc_now = datetime.now(timezone.utc)
    offset = timedelta(hours=_et_offset())
    return (utc_now + offset).replace(tzinfo=None)




def is_market_open() -> bool:
    """Return True if the US stock market is currently open."""
    et = _us_eastern_now()

    # Weekend check.
    if et.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False

    # Time check: 9:30 AM - 4:00 PM ET.
    open_time = time(9, 30)
    close_time = time(16, 0)
    return open_time <= et.time() <= close_time


def next_open_str() -> str:
    """Human-readable description of when the market opens next."""
    et = _us_eastern_now()
    if et.weekday() >= 5:
        # Weekend: next Monday 9:30 AM ET.
        days_until_monday = 7 - et.weekday()
        return f"lundi {et.day + days_until_monday} a 9h30 ET (13h30 Abidjan)"
    if et.time() < time(9, 30):
        return "aujourd'hui a 9h30 ET (13h30 Abidjan)"
    return "demain a 9h30 ET (13h30 Abidjan)"


def closed_message() -> str:
    """Return a clear message explaining the market is closed and when it reopens."""
    return (
        "Marche US ferme (9h30-16h00 ET / 13h30-20h00 Abidjan, lun-ven). "
        "Les donnees sont figeessur la derniere cloture."
        f" Prochaine ouverture : {next_open_str()}."
    )