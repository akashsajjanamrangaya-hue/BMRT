from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
from pathlib import Path
import re

LOG_LINE_PATTERN = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\]\s+keyword=.*?\s+classification=(?P<classification>\w+)\s+target=.*$"
)


def _month_key(timestamp_text: str) -> str | None:
    """Convert timestamp string to YYYY-MM month key."""
    try:
        dt = datetime.strptime(timestamp_text, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m")
    except ValueError:
        return None


def read_abnormal_monthly_counts(log_path: Path) -> OrderedDict[str, int]:
    """
    Parse logs.txt and return month-wise abnormal counts.
    Only entries with classification=abnormal are aggregated.
    """
    monthly: dict[str, int] = {}

    if not log_path.exists():
        return OrderedDict()

    for line in log_path.read_text(encoding="utf-8").splitlines():
        match = LOG_LINE_PATTERN.match(line.strip())
        if not match:
            continue

        if match.group("classification").lower() != "abnormal":
            continue

        month = _month_key(match.group("timestamp"))
        if month is None:
            continue

        monthly[month] = monthly.get(month, 0) + 1

    return OrderedDict(sorted(monthly.items(), key=lambda item: item[0]))
