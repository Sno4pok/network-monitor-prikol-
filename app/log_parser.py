import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime

LOG_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (INFO|WARNING|ERROR) (.+)$"
)


@dataclass
class LogEntry:
    """One parsed line of a log file."""

    timestamp: datetime
    level: str
    message: str


def parse_line(line: str) -> LogEntry | None:
    """Parse one log line. Return None if the line does not match."""
    match = LOG_PATTERN.match(line.strip())
    if match is None:
        return None
    timestamp_text, level, message = match.groups()
    return LogEntry(
        timestamp=datetime.strptime(timestamp_text, "%Y-%m-%d %H:%M:%S"),
        level=level,
        message=message,
    )


def parse_file(path: str) -> list[LogEntry]:
    """Read a log file and return all valid entries."""
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            entry = parse_line(line)
            if entry is not None:
                entries.append(entry)
    return entries


def count_by_level(entries: list[LogEntry]) -> Counter:
    """Count entries per level (INFO, WARNING, ERROR)."""
    return Counter(e.level for e in entries)


def errors_by_hour(entries: list[LogEntry]) -> dict[int, int]:
    """Count ERROR entries per hour of the day."""
    return dict(Counter(e.timestamp.hour for e in entries if e.level == "ERROR"))


if __name__ == "__main__":
    entries = parse_file("sample_logs/app.log")
    print(f"Parsed {len(entries)} entries")
    print("By level:", dict(count_by_level(entries)))
    print("Errors by hour:", errors_by_hour(entries))