# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A free, zero-backend Garmin running tracker. A daily GitHub Actions cron runs `garmin_pull.py`,
which fetches running activities from Garmin Connect and writes static data files into `docs/`.
GitHub Pages serves `docs/index.html`, a self-contained mobile web page that reads those files.
There is no server, no database, and no build step — the data files committed in the repo *are* the
backend. Deployed at `https://sirimak-w.github.io/garmin-runs/`. `SETUP.md` is the end-user guide (Thai).

## Architecture & data flow

```
.github/workflows/pull.yml  (cron daily 01:00 UTC + manual workflow_dispatch)
  └─ garmin_pull.py          reads GARMIN_EMAIL/PASSWORD (or GARMIN_TOKEN) from Actions Secrets
       └─ writes docs/runs.json + runs.csv + meta.json, commits them back to the repo
            └─ GitHub Pages serves docs/index.html which fetch()es runs.json + meta.json
```

The contract between the two halves is the **flat per-run record schema** produced by `to_run()`
(plus HR-zone fields merged in by `hr_zones()`) in `garmin_pull.py`. `index.html` reads those exact
snake_case keys. **If you add/rename a field in `to_run()`/`hr_zones()`, update `index.html` too**
(table columns in `renderTable`, `downloadCsv` column list) — and remember new fields only appear on
the page after the next data pull overwrites `runs.json`.

Key Garmin specifics:
- `get_activities_by_date(..., activitytype="running")` returns a summary that does **not** include
  HR-zone breakdown; `hr_zones()` makes a separate per-activity `get_activity_hr_in_timezones()` call.
- Many metrics (VO2max, power, running dynamics) are device/condition dependent and come back missing
  (e.g. VO2max is null for treadmill runs). `_r()` coerces non-numbers to `None`; the page renders
  missing values as "—" via `nz()`. Don't assume any optional metric is present.
- Speeds from Garmin are m/s and are converted to km/h.

`index.html` is vanilla JS, no framework, no bundler. Its core pattern: `RUNS` holds all loaded runs;
`view()` returns the date-filtered + sorted subset; every renderer (`renderSummary`, `renderTable`,
`renderAnalysis`, `renderJson`) derives from `view()` and is re-run via `rerender()`. The "Sub-60"
analysis targets a 10K under 60 min (`GOAL_PACE = 6.0`) and only counts real runs (`distance_km >= MIN_KM`)
so warmup/cooldown laps don't skew the estimate.

## Common commands

Run the pull locally (writes into `docs/`):
```bash
pip install garminconnect pandas
export GARMIN_EMAIL="you@example.com" GARMIN_PASSWORD="..."
python garmin_pull.py --days 120                 # last N days
python garmin_pull.py --start 2026-01-01 --end 2026-03-31   # explicit range
```

Trigger / watch the cloud pull (auth as the repo owner via `gh`):
```bash
gh workflow run pull.yml -f days=120
gh run watch "$(gh run list --workflow pull.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
```

Preview the site locally — it must be over HTTP because the page `fetch()`es JSON (`file://` fails):
```bash
python -m http.server -d docs 8000   # then open http://localhost:8000/
```

## Verifying changes to `index.html`

There is no committed test suite. The browser logic is best checked by running it under jsdom with
real data: stub `fetch` to return the local `docs/runs.json`/`meta.json`, eval the inline `<script>`,
`await load()`, then assert the table populates, `view()`/filter/sort behave, and the JSON tab matches.
`node --check` only catches syntax, not runtime errors in the renderers — render it for real.

## Notes

- `reference_source/` is the original blueprint the project was assembled from; it's gitignored, not
  part of the app — don't treat it as source of truth over the live files.
- The `garminconnect` library is unofficial and pinned-by-install; a Garmin API change can break the
  pull. MFA accounts can't log in with email/password on CI — use a `GARMIN_TOKEN` Secret instead
  (handled in `authenticate()`).
- Pages serves from branch `main`, folder `/docs`. A public repo is required for free Pages; switching
  the repo to private disables the site unless the account has GitHub Pro.
