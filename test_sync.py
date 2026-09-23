import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

from icalendar import Calendar

from sync import refresh, transform


def feed(
    extra="",
    title="Could all vector spaces be reflexive?",
    start="20260924T130000",
    end="20260924T140000",
):
    return (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Test//EN\r\n"
        "BEGIN:VEVENT\r\nUID:event19413+0@math.princeton.edu\r\n"
        f"SUMMARY:{title}\r\nSPEAKER:Peter Scholze, Bonn &amp; MPI\r\n"
        "LOCATION:Fine Hall 314\r\nDTSTAMP:20260923T120000\r\n"
        f"DTSTART:{start}\r\nDTEND:{end}\r\n{extra}"
        "END:VEVENT\r\nEND:VCALENDAR\r\n"
    ).encode()


class FeedTests(unittest.TestCase):
    def test_speaker_title_and_identity(self):
        result, count = transform(feed())
        event = Calendar.from_ical(result).walk("VEVENT")[0]
        self.assertEqual(count, 1)
        self.assertEqual(
            str(event["SUMMARY"]),
            "Peter Scholze, Bonn & MPI — Could all vector spaces be reflexive?",
        )
        self.assertEqual(str(event["UID"]), "event19413+0@math.princeton.edu")
        self.assertEqual(str(event["LOCATION"]), "Fine Hall 314")
        self.assertIn("Peter Scholze, Bonn & MPI", str(event["DESCRIPTION"]))

    def test_local_times_follow_daylight_saving(self):
        for start, end, hour in [
            ("20260924T130000", "20260924T140000", 17),
            ("20261124T130000", "20261124T140000", 18),
        ]:
            with self.subTest(start=start):
                result, _ = transform(feed(start=start, end=end))
                event = Calendar.from_ical(result).walk("VEVENT")[0]
                self.assertEqual(event.decoded("DTSTART").hour, hour)
                self.assertEqual(event.decoded("DTEND").hour, hour + 1)
                self.assertEqual(
                    event.decoded("DTSTART").utcoffset().total_seconds(), 0
                )

    def test_utc_and_all_day_events_are_preserved(self):
        result, _ = transform(feed(start="20260924T170000Z", end="20260924T180000Z"))
        event = Calendar.from_ical(result).walk("VEVENT")[0]
        self.assertEqual(
            event.decoded("DTSTART"), datetime(2026, 9, 24, 17, tzinfo=UTC)
        )
        source = (
            feed()
            .replace(b"DTSTART:20260924T130000", b"DTSTART;VALUE=DATE:20260924")
            .replace(b"DTEND:20260924T140000", b"DTEND;VALUE=DATE:20260925")
        )
        result, _ = transform(source)
        event = Calendar.from_ical(result).walk("VEVENT")[0]
        self.assertEqual(event.decoded("DTSTART").isoformat(), "2026-09-24")

    def test_unicode_escaping_folding_and_existing_description(self):
        title = "Café, cohomology; " * 12
        result, _ = transform(
            feed(extra="DESCRIPTION:Existing abstract\\nSecond line\r\n", title=title)
        )
        event = Calendar.from_ical(result).walk("VEVENT")[0]
        self.assertTrue(str(event["SUMMARY"]).endswith(title.strip()))
        self.assertIn("Existing abstract\nSecond line", str(event["DESCRIPTION"]))
        self.assertTrue(all(len(line) <= 75 for line in result.split(b"\r\n")))
        self.assertIn(b"\\,", result)

    def test_no_speaker_and_duplicate_title(self):
        source = feed().replace(b"SPEAKER:Peter Scholze, Bonn &amp; MPI\r\n", b"")
        result, _ = transform(source)
        self.assertEqual(
            str(Calendar.from_ical(result).walk("VEVENT")[0]["SUMMARY"]),
            "Could all vector spaces be reflexive?",
        )
        result, _ = transform(feed(title="Peter Scholze, Bonn &amp; MPI"))
        self.assertEqual(
            str(Calendar.from_ical(result).walk("VEVENT")[0]["SUMMARY"]),
            "Peter Scholze, Bonn & MPI",
        )

    def test_rejects_bad_feeds(self):
        for source in [
            b"<html>Server error</html>",
            feed().replace(b"END:VCALENDAR", b""),
            feed().replace(b"20260924T130000", b"invalid"),
            feed().replace(b"UID:event19413+0@math.princeton.edu\r\n", b""),
            feed() + feed(),
        ]:
            with self.subTest(source=source[:30]), self.assertRaises(ValueError):
                transform(source)

    def test_empty_calendar_is_valid(self):
        result, count = transform(
            b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Test//EN\r\nEND:VCALENDAR\r\n"
        )
        self.assertEqual(count, 0)
        self.assertEqual(Calendar.from_ical(result).walk("VEVENT"), [])

    def test_failed_refresh_preserves_calendar_and_status(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            refresh(output, Mock(return_value=feed()))
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            status = json.loads(before["sync-status.json"])
            self.assertEqual(status["event_count"], 1)
            self.assertIn("last_successful_fetch", status)
            for fetch in [
                Mock(side_effect=OSError("Network failed")),
                Mock(return_value=b"Invalid feed"),
            ]:
                with self.assertRaises((OSError, ValueError)):
                    refresh(output, fetch)
                self.assertEqual(
                    {p.name: p.read_bytes() for p in output.iterdir()}, before
                )


if __name__ == "__main__":
    unittest.main()
