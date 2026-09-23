# Princeton Math Calendar

Adds speaker names to [Princeton's math calendar](https://www.math.princeton.edu/events/calendar).
Events appear as `Speaker — Talk title`, with the speaker's affiliation in the description.

**[Subscribe](https://tomasortega.net/princeton-math-calendar/)** ·
**[Calendar feed](https://tomasortega.net/princeton-math-calendar/calendar.ics)**

GitHub Actions refreshes the feed daily at 09:17 UTC and publishes it to GitHub Pages.
Each successful run commits a timestamp to keep the scheduled workflow active.

## Subscribe

Use this URL:

```text
https://tomasortega.net/princeton-math-calendar/calendar.ics
```

- **Google Calendar:** Other calendars → + → From URL.
- **Outlook:** Add calendar → Subscribe from web.

Your calendar app decides when to fetch updates. Remove the original Princeton
subscription to avoid duplicates.

## Run locally

```sh
uv run --locked python sync.py
uv run --locked python -m unittest -q
```
