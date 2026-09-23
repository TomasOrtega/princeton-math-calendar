"""Publish Princeton's calendar with speakers in standard event fields."""

import argparse
import hashlib
import html
import json
import re
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from icalendar import Calendar

SOURCE = "https://www.math.princeton.edu/events-feed.ics"
EASTERN = ZoneInfo("America/New_York")


def replace(component, key, value):
    component.pop(key, None)
    component.add(key, value)


def transform(source: bytes) -> tuple[bytes, int]:
    if not source.strip().endswith(b"END:VCALENDAR"):
        raise ValueError("Incomplete calendar response")
    calendar = Calendar.from_ical(source)
    if calendar.name != "VCALENDAR" or str(calendar.get("VERSION")) != "2.0":
        raise ValueError("Expected an iCalendar 2.0 feed")
    if any(component.errors for component in calendar.walk()):
        raise ValueError("Calendar contains invalid properties")

    events = calendar.walk("VEVENT")
    if len(events) != len(re.findall(rb"(?m)^BEGIN:VEVENT\r?$", source)):
        raise ValueError("Calendar contains incomplete events")
    seen = set()
    for event in events:
        for key in ("UID", "SUMMARY", "DTSTART", "DTSTAMP"):
            if key not in event or isinstance(event[key], list):
                raise ValueError(f"Missing or repeated {key}")
        identity = (str(event["UID"]), str(event.get("RECURRENCE-ID", "")))
        if not identity[0].strip() or identity in seen:
            raise ValueError("Empty or duplicate event UID")
        seen.add(identity)

        title = html.unescape(str(event["SUMMARY"])).strip()
        speaker = html.unescape(str(event.pop("SPEAKER", ""))).strip()
        replace(
            event,
            "SUMMARY",
            f"{speaker} — {title}" if speaker and speaker != title else title,
        )
        if speaker:
            description = str(event.get("DESCRIPTION", "")).strip()
            replace(
                event,
                "DESCRIPTION",
                f"Speaker: {speaker}" + (f"\n\n{description}" if description else ""),
            )

        # Princeton exports floating local times; make their time zone unambiguous.
        for key in (
            "DTSTART",
            "DTEND",
            "DTSTAMP",
            "CREATED",
            "LAST-MODIFIED",
            "RECURRENCE-ID",
        ):
            if key not in event:
                continue
            value = event.decoded(key)
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    value = value.replace(tzinfo=EASTERN)
                replace(event, key, value.astimezone(UTC))
            elif not isinstance(value, date) or key in (
                "DTSTAMP",
                "CREATED",
                "LAST-MODIFIED",
            ):
                raise ValueError(f"Invalid {key}")
        if "DTEND" in event and event.decoded("DTEND") <= event.decoded("DTSTART"):
            raise ValueError("Event ends before it starts")

    replace(calendar, "X-WR-CALNAME", "Princeton Math — Speakers & Talks")
    replace(calendar, "X-WR-TIMEZONE", "America/New_York")
    return calendar.to_ical(), len(events)


def download() -> bytes:
    request = Request(
        SOURCE,
        headers={
            "User-Agent": "princeton-math-calendar/0.1",
            "Accept": "text/calendar",
        },
    )
    with urlopen(request, timeout=60) as response:
        return response.read()


def refresh(output: Path, fetch=download) -> None:
    calendar, count = transform(fetch())
    status = {
        "last_successful_fetch": datetime.now(UTC).isoformat(timespec="seconds"),
        "event_count": count,
        "source": SOURCE,
        "sha256": hashlib.sha256(calendar).hexdigest(),
    }
    output.mkdir(parents=True, exist_ok=True)
    for name, content in {
        "calendar.ics": calendar,
        "sync-status.json": (json.dumps(status, indent=2) + "\n").encode(),
    }.items():
        temporary = output / f".{name}.tmp"
        temporary.write_bytes(content)
        temporary.replace(output / name)
    print(f"Published {count} events to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("site"))
    parser.add_argument(
        "--source-file", type=Path, help="Use a saved feed instead of downloading"
    )
    args = parser.parse_args()
    refresh(args.output, args.source_file.read_bytes if args.source_file else download)
