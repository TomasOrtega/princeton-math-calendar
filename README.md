# Princeton Math Calendar

Princeton mathematics events with `Speaker, affiliation — Talk title` as the title.
Works as a live subscription in Outlook, Google Calendar, and other iCalendar clients.

**[Subscribe](https://tomasortega.net/princeton-math-calendar/)** ·
**[Calendar feed](https://tomasortega.net/princeton-math-calendar/calendar.ics)**

## How it works

A GitHub Actions workflow fetches [Princeton's public feed](https://www.math.princeton.edu/events-feed.ics)
daily at **09:17 UTC**, validates it, combines speaker and title, and publishes it using GitHub Pages.
It preserves event IDs and locations, puts speakers in descriptions too, and converts Princeton's
floating Eastern times to UTC with daylight saving time accounted for. Already zoned times and
all-day dates retain their meaning. The `icalendar` library handles escaping and line folding.

Each successful run commits `site/calendar.ics` and `site/sync-status.json` as `github-actions[bot]`.
The success timestamp records daily repository activity even when the events do not change.
Download or validation failures stop publication and leave the previous feed online.
The feed mirrors Princeton's current event list; it is not an archive.

## Subscribe

Copy the feed URL from the [subscription page](https://tomasortega.net/princeton-math-calendar/).

- **Google Calendar:** On a computer, select **Other calendars → + → From URL**, paste the URL,
  and select **Add calendar**. [Google instructions](https://support.google.com/calendar/answer/37100)
- **Outlook:** Select **Add calendar → Subscribe from web**, paste the URL, enter a name,
  and select **Import**.

Both apps control their own refresh schedules. Importing a downloaded file produces a snapshot;
subscribe by URL for updates. Remove the original feed subscription to avoid duplicates.
This publishes only Princeton's public events and requires no access to your calendar account.

## Run locally

With [uv](https://docs.astral.sh/uv/getting-started/installation/) installed:

```sh
uv run --locked python -m unittest -q
uv run --locked python sync.py
```

To use a saved feed: `uv run --locked python sync.py --source-file events.ics --output /tmp/calendar-preview`.

## Deploy a copy

1. Push this repository to a public GitHub repository with `main` as its default branch.
2. In **Settings → Pages**, set **Source** to **GitHub Actions**.
3. Run **Actions → Refresh calendar → Run workflow**.

The workflow uses only the built-in `GITHUB_TOKEN` with repository-content and Pages write access;
no personal token is needed. It deploys Pages directly because commits using `GITHUB_TOKEN` do not
trigger another Pages build. Scheduled runs can be delayed; inspect the public status file or
Actions runs if updates stop. GitHub disables public-repository schedules after 60 days without
repository activity; the daily success commits keep this repository active.

Unofficial feed. Event information belongs to its original publishers.
