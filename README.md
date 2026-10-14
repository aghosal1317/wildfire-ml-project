# Wildfire Evacuation Alert Failures

Why do evacuation warnings fail to reach people during deadly wildfires? This project studies two U.S. disasters, the **2023 Lahaina fire** (Maui) and the **2018 Camp Fire** (Paradise, CA). It compares *when* public awareness spiked on news and social media against *when* official warnings went out, to find where the official response lagged. Those timelines will then calibrate a simulation that tests how much specific changes (earlier alerts, working sirens) could have reduced casualties.

**Research question:** Across documented U.S. wildfire disasters, what in the alert and evacuation process contributed most to deaths, and how much would specific interventions have reduced casualties?

> **Keeping this updated:** at the end of each week, add an entry to the [Progress log](#progress-log) (same idea as the weekly journal), tick off finished items in [Next steps](#next-steps), and update the [Data status](#data-status) table if any data changed. Last updated: **Oct 14, 2026**.

---

## Repository layout

```
data/     collected CSVs (one file per case and source) + burst-detection outputs
src/      code: data collection, burst detection, analysis notebook
school/   proposal, plan, milestones, weekly journals (Markdown + PDF)
logs/     timestamped logs from collection runs (not committed)
```

| File | What it does |
|---|---|
| `src/collect_data.py` | Downloads news (GDELT) and Reddit data for both fires into `data/` |
| `src/run_collection.sh` | Runs `collect_data.py` in the background with the Mac kept awake, retrying until it succeeds or time runs out, and logging to `logs/` |
| `src/analyze_burst.py` | Finds the first hour each source "bursts" (spikes above its recent baseline) and writes `*_burst.csv` files |
| `src/wildfire_analysis.ipynb` | Main analysis: loads the data, runs burst detection, plots activity over time against the official timeline, and computes lag tables |
| `src/GDELT-test.ipynb` | Early scratch test of the GDELT API |

## How to run

All commands run from the project folder.

```bash
# Collect everything (GDELT + Reddit) into data/
.venv/bin/python src/collect_data.py

# Only the subreddit data (Arctic Shift) -- needs the HOME network
.venv/bin/python src/collect_data.py --local-only

# Long run in the background (Mac must stay plugged in with the lid open); logs to logs/
src/run_collection.sh 3 --local-only

# Burst detection from the command line
.venv/bin/python src/analyze_burst.py
```

Then open `src/wildfire_analysis.ipynb` and run all cells.

**Journal PDFs:** in VS Code, open a journal `.md` file and run the default build task (Cmd+Shift+B), which runs pandoc. Image paths in journals are relative to the project folder (e.g. `data/lahaina-bursts.png`), and the settings block at the bottom of a journal needs a blank line above its first `---`.

## Data sources

| Source | What | Notes |
|---|---|---|
| **GDELT** (bulk 15-minute files) | News articles mentioning the fire: URL, title, outlet, tone | The GDELT search API rate-limits too heavily to use (HTTP 429), so the script scans GDELT's raw bulk files instead. These have no rate limit or 250-article cap. Matched on metadata (URL, title, places, names), not full article text. |
| **PullPush** | Reddit-wide keyword search ("Lahaina fire", etc.) | Behind a Cloudflare bot check since Oct 8, 2026, so it can't be updated for now. Existing files are kept. |
| **Arctic Shift** | Everything posted in local subreddits (posts + comments) | Works on the home network; **blocked on the school network**. Throttles heavily, so runs can take hours. |

## Data status

Times are UTC.

| Case | Source | Rows | Coverage |
|---|---|---:|---|
| Lahaina | GDELT news | 3,875 | Aug 8 17:00 → Aug 12 00:45 |
| Lahaina | Reddit-wide posts / comments | 212 / 445 | Aug 9 → Aug 11 04:00 |
| Lahaina | r/Hawaii posts / comments | 187 / 4,163 | Aug 8 04:00 → Aug 11 04:00 |
| Lahaina | r/Maui posts / comments | 333 / 3,900 | comments stop Aug 10 20:17 (incomplete) |
| Camp Fire | GDELT news | 1,641 | Nov 8 18:00 → Nov 13 00:45 |
| Camp Fire | Reddit-wide posts / comments | 72 / 55 | Nov 8 → Nov 12 |
| Camp Fire | r/California posts / comments | 230 / 2,903 | Nov 8 05:00 → Nov 12 05:00 |
| Camp Fire | r/Chico | 0 | No data for that week in either archive |

Known gaps:
- **Reddit windows end about 4 hours into the last day.** The code now uses the same UTC window as GDELT (last day included), but the existing files were collected with the old window. A `--local-only` run on the home network fills this in for the subreddit files. The Reddit-wide files can't be extended while PullPush is blocked.
- **r/Maui comments are incomplete**, stopping at Aug 10 20:17 after a dropped connection. The same home-network run fixes this.

## Findings so far

Burst detection compares each hour with the 24 hours before it (z ≥ 3). **10 of the 12 sources with data** show a burst.

| Source | Lahaina first burst (UTC) | Camp Fire first burst (UTC) |
|---|---|---|
| GDELT news | Aug 9 11:00 | Nov 9 04:00 |
| Reddit-wide comments | Aug 9 08:00 | Nov 9 20:00 |
| Reddit-wide posts | Aug 9 21:00 | no burst |
| Local posts | r/Hawaii Aug 9 08:00, r/Maui Aug 9 10:00 | r/California: no burst |
| Local comments | r/Hawaii Aug 8 18:00, r/Maui Aug 9 06:00 | r/California Nov 8 14:00 |

- For Lahaina, **r/Maui comments spiked about 5 hours before national news (GDELT)**. That's early evidence that local social media picked up on the fire before national coverage did.
- **Caveats:** the local subreddit files include *all* posts, not just fire-related ones, so some bursts may be normal daily activity. For example, the r/Hawaii spike is at 8am Hawaii time. Also, GDELT only starts at Aug 8 17:00 and needs 6 hours of history, so it can't show a burst before about 23:00.
- **Not yet measured:** how these bursts compare with the **official warnings**. That needs the official timeline (see Next steps).
- With only two fires, this is a case-study analysis, not a trained prediction model.

## Progress log

Newest first. Add one entry per week.

### Week of Oct 13
- Wrote this README.

### Week of Oct 6
- **GDELT fixed:** switched from the rate-limited API to GDELT's bulk files. Lahaina went from 250 articles (covering only the last 5 hours) to 3,875 covering the whole fire. Camp Fire: 1,641.
- **Reddit:** PullPush started blocking automated requests (Cloudflare). Switched local-subreddit collection to Arctic Shift and pulled r/Hawaii, r/Maui and r/California posts and comments. Found that the school network blocks Arctic Shift.
- Added `run_collection.sh` for long background runs with logs.
- **Burst detection fixed:** the old version included each hour in its own baseline, which capped the z-score at about 2.04, so real spikes never counted. After the fix, 10 of 12 sources show bursts.
- Set up the official-timeline section of the notebook (enter local times; they're converted to UTC) and a lag table.

### Week of Sep 29
- Got GDELT and PullPush collection running; added retry-with-backoff for HTTP 429 errors.
- Reddit collection now pages past the 100-row limit.
- Created the GitHub repository.

### Week of Sep 22
- Organized the repo into `data/`, `school/` and `src/`, and pointed all scripts at `data/`.

## Next steps

**Short term (by Oct 15–20)**
- [ ] Home-network run to finish r/Maui comments and fill in the full Reddit windows: `src/run_collection.sh 3 --local-only`
- [ ] Build the official timelines from the Hawaii AG report and Camp Fire reports (ignition, first warning and its channel, evacuation orders, fire arrival, casualties) and enter them in the notebook's `OFFICIAL_TIMELINE`
- [ ] Filter local subreddit data to fire-related posts (fire, smoke, evacuate, Lahaina, Paradise…) so bursts reflect fire talk, not normal daily activity

**By end of October**
- [ ] Measure the lag between public bursts and each official warning, for both fires
- [ ] Write the failure timeline and taxonomy for Lahaina (what failed, when, through which channel)
- [ ] Start planning the simulation: agents, grid, alert module

**Later (from the proposal)**
- [ ] Build the baseline simulation environment and calibrate it against Lahaina's documented outcome
- [ ] Run interventions (earlier alerts, working sirens, etc.) and record the change in simulated casualties
- [ ] Repeat the timeline and simulation for the Camp Fire
- [ ] *Optional:* keep GDELT's place tags for a map-based "quiet area" analysis, and add more fires (GDELT-only) to generalize
- [ ] Combine the taxonomy and simulation results into final recommendations

## Limitations

- Two case studies, so findings are descriptive and won't necessarily generalize.
- Social media is a stand-in for public awareness. Many people affected, especially in Lahaina where cell service went down, may not have posted at all.
- Archive coverage varies: r/Chico has no data, and the Reddit-wide searches only include posts that matched the keywords.
- Simulation results describe what *could have* happened in these past events, not predictions.
