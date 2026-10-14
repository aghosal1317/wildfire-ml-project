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

# Same subreddits for an ordinary week (7 days before each fire) -> *_baseline.csv -- HOME network
src/run_collection.sh 3 --baseline

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
| **Arctic Shift** | Everything posted in local subreddits (posts + comments) | Works on the home network; **blocked on the school network**. Throttles heavily, so runs can take hours. The notebook filters these to fire-related posts (see Findings). |
| **FSRI Lahaina timeline** (`data/lahaina_official_timeline_fsri.csv`) | Official minute-by-minute timeline: 12,140 entries from dispatch audio, emergency management logs, WEA/EAS alerts, county social media | Published by the [Hawaii AG](https://ag.hawaii.gov/maui-wildfire-investigation-resources-page/) with the FSRI Phase One report. Times are HST. |
| **Cal OES Camp Fire After Action Report** | Official Camp Fire events and findings | [Report PDF](https://www.caloes.ca.gov/wp-content/uploads/Preparedness/Documents/FINAL-AAR-2018-Camp-Fire-508-Clean-Copy-11.17.25.pdf). Far less detailed than the Lahaina timeline; NIST TN 2135 (fire progression) and TN 2252 (notification/evacuation) are the next sources to check. |

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

**Headline:** public online activity did **not** come before the official warnings in either fire. In Lahaina, Reddit was almost silent while the town burned, and fire talk only took off about 5 hours after the flare-up. In both fires, local Reddit still came before national news.

Times below are local (HST for Lahaina, PST for Camp Fire). "Fire-related" means the local subreddit posts filtered by keyword in the notebook. The notebook's "Readable timeline figure" section draws all of this.

### Lahaina (Aug 8, 2023)

Official timeline (FSRI):

| Time (HST) | Event | Channel |
|---|---|---|
| 6:37 AM | Morning fire reported on Lahainaluna Rd; evacuations nearby at 6:40 | police door-to-door |
| 9:55 AM | County posts that the fire is 100% contained | Facebook |
| **2:55 PM** | **Fire flares up again (Kuʻialua St)** | |
| 3:07 PM | Police start evacuating homes west of Kuʻialua | police door-to-door |
| 4:16 PM | **First WEA/EAS for any Lahaina area**, one subdivision (Kelawea Mauka) | WEA + EAS |
| 4:24 PM | Fire jumps the highway toward Front Street | |
| 4:45 PM | County update: bypass closed, "shelter in place encouraged" | Facebook |
| 6:01 PM | ~100 people in the ocean off Front Street | |
| 8:46 PM | WEA for Wahikuli Subdivision | WEA + EAS |

No record of the outdoor sirens being sounded was found in the timeline (verify against the Phase Two findings).

What the public data shows:
- **2–8 PM: almost no fire talk on Reddit.** r/Maui had 0 fire-related comments in nearly every hour. This isn't missing data: r/Hawaii was being archived at 20–50 comments an hour all afternoon, just not about the fire.
- **~8 PM: local Reddit reacts.** Fire-related r/Maui comments jump to 7, 15, then 18 an hour, with a first burst at 8 PM. That's **5.1 h after the flare-up, 3.7 h after the first Lahaina WEA, and 2 h after people were already in the ocean.**
- **Overnight into the next morning: news follows.** GDELT's first burst is about 1 AM Aug 9, roughly 5 h after local Reddit, and coverage peaks around 10–11 AM.
- Order: **fire → official alerts → local Reddit (evening) → Reddit-wide and news (next morning).**

### Camp Fire (Nov 8, 2018)

Official timeline (Cal OES AAR unless noted):

| Time (PST) | Event |
|---|---|
| 6:33 AM | First reports of fire near Poe Creek Dam |
| 7:13 AM | First evacuation notice (Pulga) |
| by 8:00 AM | Concow and Paradise notified (other sources give 7:54 or 8:03 for Paradise; check NIST TN 2252) |
| ~8:30 AM | Fire begins consuming Paradise (NIST TN 2135; verify) |

- The AAR reports that the link sending CodeRED messages out as federal phone alerts (IPAWS) **failed**, and that only about **7,000 of the 52,000 evacuees** received a CodeRED notification.
- **Public response came ~2–3 h after the first reports.** Fire-related r/California comments and news coverage both start around 9–10 AM, while Paradise was burning.
- The local signal is thin: fewer than 10 Camp Fire comments an hour, too few for burst detection (max z 1.75).

### Corrections to earlier results

Filtering to fire-related posts showed two earlier "early bursts" were not about the fires:
- The r/Hawaii comment spike at 8 AM HST Aug 8 was ordinary morning activity. The fire-related first burst is 10 PM HST.
- The r/California comment spike at 6 AM PST Nov 8 came *before* the Camp Fire was reported. With Camp Fire terms only, there's no burst.

### Caveats

- **Who could post:** power and cell service in West Maui were failing that afternoon, and locals may have used Facebook, texts or calls instead of Reddit. So the silence may say more about communications failing than about awareness. That's still relevant to the research question.
- **Two different first-day fires in Lahaina:** the 6:37 AM fire was declared contained before the deadly 2:55 PM flare-up. Lags are measured from 2:55 PM.
- **First-burst timing** depends on the detection settings (24 h baseline, z ≥ 3). The figure is the more robust view.
- **Case study only:** with two fires, this is a descriptive case-study analysis, not a trained prediction model.

## Progress log

Newest first. Add one entry per week.

### Week of Oct 13
- Wrote this README.
- **Official timelines:** found the FSRI minute-by-minute Lahaina timeline (12,140 entries) and saved it to `data/`. Took the Camp Fire events from the Cal OES After Action Report and entered both in the notebook's `OFFICIAL_TIMELINE`.
- **Keyword filter:** added fire-related versions of the local subreddit sources (`*_fire`). This showed the early r/Hawaii and r/California spikes weren't about the fires.
- **Lag results:** in Lahaina, local Reddit reacted ~5 h after the flare-up and ~3.7 h after the first Lahaina WEA, and was nearly silent from 2–8 PM. Camp Fire public activity started ~2–3 h after the first reports.
- **Readable figure:** added a cleaner timeline figure (local time, one panel per source type, numbered key events). Fixed "(nan)" labels on the old plot.
- Added `--baseline` to `collect_data.py` to download an ordinary week for comparison.

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
- [ ] Then the ordinary-week download: `src/run_collection.sh 3 --baseline`, and a notebook cell comparing the fire week with the normal week
- [x] Build the official timeline for Lahaina (FSRI) and enter it in `OFFICIAL_TIMELINE`
- [ ] Verify the Camp Fire timeline against NIST TN 2252 (exact Paradise evacuation time, channels used) and TN 2135 (when fire reached Paradise)
- [ ] Confirm in the FSRI Phase Two findings that Lahaina's sirens were not activated
- [x] Filter local subreddit data to fire-related posts

**By end of October**
- [x] Measure the lag between public bursts and each official warning (first pass done for both fires; redo after the home-network data run)
- [ ] Find when cell service and power failed in West Maui (FSRI timeline, HECO, FCC outage reports), to test whether the Reddit silence matches the outages
- [ ] Write the failure timeline and taxonomy for Lahaina (what failed, when, through which channel)
- [ ] Start planning the simulation: agents, grid, alert module

**Later (from the proposal)**
- [ ] Build the baseline simulation environment and calibrate it against Lahaina's documented outcome
- [ ] Run interventions (earlier alerts, working sirens, etc.) and record the change in simulated casualties
- [ ] Repeat the timeline and simulation for the Camp Fire
- [ ] *Optional:* add more fires (GDELT-only) to generalize. The map-based "quiet area" analysis is Track 2, which is my partner's part of the project.
- [ ] Combine the taxonomy and simulation results into final recommendations

## Limitations

- Two case studies, so findings are descriptive and won't necessarily generalize.
- Social media is a stand-in for public awareness. Many people affected, especially in Lahaina where cell service went down, may not have posted at all.
- Archive coverage varies: r/Chico has no data, and the Reddit-wide searches only include posts that matched the keywords.
- Simulation results describe what *could have* happened in these past events, not predictions.
