import os
from zoneinfo import ZoneInfo, available_timezones
from datetime import timezone

def get_timezone():
    """
    Returns the configured timezone or UTC if not available
    """
    try:
        tz_key = os.environ.get("TZ") or "Etc/UTC"
        return ZoneInfo(tz_key)
    except (ImportError, Exception):
        return timezone.utc