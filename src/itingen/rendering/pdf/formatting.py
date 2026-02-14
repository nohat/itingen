"""Time formatting utilities for PDF rendering."""

import datetime as dt
from typing import Optional


def fmt_time(
    time_local: Optional[str],
    suppress_tz: bool = False,
    timezone: Optional[str] = None,
) -> str:
    """Format a time_local string into human-readable 12-hour format.

    Examples: "7am", "3:30pm", "12:15am NZ"
    """
    if not time_local:
        return "TBD"

    try:
        value = time_local.strip()
        if " " in value:
            value = value.rsplit(" ", 1)[-1]
        t = dt.datetime.strptime(value, "%H:%M")
        s = t.strftime("%I:%M %p").lstrip("0")
        time_str = s.lower().replace(" ", "").replace(":00", "")

        if timezone and not suppress_tz:
            time_str += f" {timezone}"
        return time_str
    except Exception:
        return "TBD"
