"""
Data collection for the wildfire evacuation alert-failure project.

Pulls free, keyless data sources for both case studies (Lahaina 2023,
Camp Fire 2018) and saves each as a CSV:

  1. GDELT                - news article volume/tone (free, covers 2017-present)
  2. PullPush             - Reddit, site-wide keyword search (mirrors old Pushshift)
     -> *_reddit_submissions.csv / *_reddit_comments.csv
  3. Arctic Shift         - Reddit, subreddit-scoped, no keyword
     -> *_<subreddit>_reddit_local.csv           (posts)
     -> *_<subreddit>_reddit_local_comments.csv  (comments)
     (everything posted in that subreddit in the date window -- the local-
     signal proxy)

Since 2026-10-08 PullPush sits behind a Cloudflare bot challenge (every
request gets HTTP 403 with `cf-mitigated: challenge`), so its site-wide
searches fail until that's lifted; the CSVs already collected are kept.
Arctic Shift, which earlier failed at the TLS handshake on this network, is
reachable again and now handles the subreddit-scoped data. It can't do
site-wide keyword search (it requires a subreddit or author), which is why
PullPush is still used for that.

GDELT is fetched from its raw 15-minute GKG bulk files by default
(--gdelt-source bulk), not the DOC API. The DOC API's rate limiter is far
stricter than its "one request every 5 seconds" message suggests: after a
429 it stays closed for a minute or more and keeps rejecting retries, so a
24-chunk run spends most of its time throttled. The bulk files are static
downloads from data.gdeltproject.org (Google Cloud Storage) with no rate
limit. Each one (~7-9 MB zipped) lists every article GDELT processed in
that 15 minutes with its URL, title, source, locations, names and tone; the
script streams each file, keeps the rows matching the case's terms, and
discards the rest. It's more downloading (~3-4 GB per case, never stored on
disk) but it's complete (no 250-record cap) and finishes in one go. Progress
is checkpointed, so an interrupted run resumes where it stopped.
--gdelt-source api keeps the original DOC API path.

Both sources cap how much a single request can return (GDELT: 250 records
per query, sorted most-recent-first, no offset pagination; PullPush: caps
around 100 rows per request regardless of the `size` requested). Without
handling that, a multi-day window silently returns only a fragment of it --
GDELT returns just the last chunk before `end_date` (missing the ignition/
warning period that matters most), and PullPush returns just the first
~100 matching rows. This script works around both:
  - GDELT is queried in fixed time chunks across the full date range.
  - PullPush is paginated forward using each page's last created_utc+1 as
    the next request's `after`, until a page comes back under the request
    size or the `before` boundary is reached.

Arctic Shift has been dropped: on some networks, TLS connections to
arctic-shift.photon-reddit.com fail at the handshake itself (confirmed with
plain `curl`, not just Python) -- network-level filtering rather than
anything fixable in the script. PullPush's `subreddit` filter parameter
covers the same need from a source that's confirmed reachable.

Twitter/X is not included: its API has required a paid tier since 2023 with
no free historical-search option.

Setup:
    pip install requests pandas

Usage:
    python collect_data.py --case lahaina
    python collect_data.py --case camp_fire
    python collect_data.py --case all          # default
    python collect_data.py --out-dir some/dir  # write CSVs somewhere other than data/
    python collect_data.py --gdelt-chunk-hours 2   # if a chunk warns it hit the cap
    python collect_data.py --gdelt-only --gdelt-sleep 30   # retry just GDELT
    python collect_data.py --local-only        # just the subreddit data (Arctic Shift)
    python collect_data.py --baseline          # same subreddits, an ordinary week earlier
"""

import argparse
import html
import io
import os
import re
import sys
import time
import traceback
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

CASES = {
    "lahaina": {
        "gdelt_query": '"Lahaina" fire',
        "reddit_query": "Lahaina fire",
        # GKG bulk matching: an article is kept if every term appears somewhere
        # in its URL, title, locations, names or themes (case-insensitive).
        "gdelt_bulk_terms": ["lahaina", "fire"],
        "subreddits": ["Hawaii", "Maui"],
        "start": "2023-08-08",
        "end": "2023-08-11",
    },
    "camp_fire": {
        "gdelt_query": '"Camp Fire" Paradise California',
        "reddit_query": "Paradise Camp Fire California",
        "gdelt_bulk_terms": ["camp fire", "paradise"],
        "subreddits": ["California", "Chico"],
        "start": "2018-11-08",
        "end": "2018-11-12",
    },
}

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_MAX_RECORDS = 250

GDELT_GKG_URL = "https://data.gdeltproject.org/gdeltv2/{stamp}.gkg.csv.zip"
GDELT_GKG_WORKERS = 8  # parallel downloads; it's static file hosting, not the rate-limited API

PULLPUSH_SUBMISSION_URL = "https://api.pullpush.io/reddit/search/submission/"
PULLPUSH_COMMENT_URL = "https://api.pullpush.io/reddit/search/comment/"

ARCTIC_SHIFT_URL = "https://arctic-shift.photon-reddit.com/api/{kind}/search"  # kind: posts | comments
ARCTIC_SHIFT_PAGE_SIZE = 100
ARCTIC_SHIFT_PAGE_SLEEP = 3  # seconds between pages; it throttles bursts
PULLPUSH_PAGE_SIZE = 100
PULLPUSH_MAX_PAGES = 500  # safety cap, not expected to be hit in normal use

# CSVs live in <project root>/data, next to this script's src/ folder.
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# Every source/chunk that failed this run, so the script can exit non-zero and
# the overnight runner (run_collection.sh) knows another pass is worthwhile.
FAILURES = []

HEADERS = {"User-Agent": "wildfire-evac-research/0.5 (student research project)"}


def _get(url, params, max_retries=5, base_wait=10, max_wait=60):
    """GET with the request URL and HTTP status printed, and automatic
    retry-with-backoff on 429 (rate limited) or 5xx (server error)
    responses. GDELT's public API runs at "archive scale" with very little
    headroom and rate-limits based on overall system load, not anything
    specific to one caller -- a 429 there can happen even when nothing
    about this script is wrong, especially around high-traffic news
    events. Backoff doubles each attempt up to `max_wait`, then holds
    there (10s, 20s, 40s, 60s, 60s... by default) so a stretch of
    congestion gets ridden out instead of escalating to absurd waits. If
    the last attempt is still failing, it raises and lets the caller's
    try/except handle it so one bad chunk doesn't take down the whole run.
    """
    wait = base_wait
    resp = None
    for attempt in range(1, max_retries + 1):
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        print(f"    GET {resp.url}")
        print(f"    -> HTTP {resp.status_code}")
        if resp.status_code == 429 or resp.status_code >= 500:
            if attempt == max_retries:
                break  # fall through to raise_for_status() below
            print(f"    rate limited / server error -- retrying in {wait}s "
                  f"(attempt {attempt}/{max_retries})")
            time.sleep(wait)
            wait = min(wait * 2, max_wait)
            continue
        resp.raise_for_status()
        return resp
    resp.raise_for_status()
    return resp


def fetch_gdelt_range(query, start_date, end_date, chunk_hours=8, max_records=GDELT_MAX_RECORDS,
                       chunk_sleep=10, save_path=None):
    """News articles from GDELT DOC 2.0, fetched in fixed time chunks across
    the whole [start_date, end_date] window instead of one query for the
    whole range. GDELT has no offset-based pagination and caps each query
    at `max_records`, sorted most-recent-first -- a single query over a
    multi-day window would silently return only the tail end of it, missing
    the ignition/warning period. Chunking keeps each query's result well
    under the cap so the full range comes back complete.

    chunk_hours defaults to 8 (not smaller) deliberately: GDELT's public API
    rate-limits on overall load, so fewer, larger requests mean less
    exposure to that congestion. If a chunk warns it hit the max_records
    cap, lower --gdelt-chunk-hours for that case specifically.

    If save_path is given, each chunk is appended to that CSV as soon as it
    arrives, so progress survives a crash or Ctrl-C. A chunk that still fails
    after all retries is skipped (and listed at the end) rather than throwing
    away every chunk already fetched -- rerun later to fill the gaps; rows
    already saved are deduplicated by URL.
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # end_date inclusive

    all_articles = []
    failed_chunks = []
    chunk_start = start_dt
    first_request = True
    while chunk_start < end_dt:
        chunk_end = min(chunk_start + timedelta(hours=chunk_hours), end_dt)
        if not first_request:
            time.sleep(chunk_sleep)
        first_request = False

        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "startdatetime": chunk_start.strftime("%Y%m%d%H%M%S"),
            "enddatetime": chunk_end.strftime("%Y%m%d%H%M%S"),
            "maxrecords": max_records,
            "sort": "dateasc",
        }
        try:
            resp = _get(GDELT_URL, params, max_retries=8, base_wait=10, max_wait=60)
            articles = resp.json().get("articles", [])
        except Exception as e:
            print(f"    ! chunk {chunk_start}-{chunk_end} failed after retries ({e}) -- skipping")
            failed_chunks.append((chunk_start, chunk_end))
            chunk_start = chunk_end
            continue
        if len(articles) >= max_records:
            print(f"    ! chunk {chunk_start}-{chunk_end} returned the {max_records}-record "
                  f"cap -- likely still truncated; rerun with a smaller --gdelt-chunk-hours")
        if save_path and articles:
            save_or_append(pd.DataFrame(articles), save_path, dedup_col="url", label="GDELT chunk")
        all_articles.extend(articles)
        chunk_start = chunk_end

    if failed_chunks:
        FAILURES.append(f"GDELT API: {len(failed_chunks)} chunk(s)")
        print(f"    ! {len(failed_chunks)} GDELT chunk(s) never got through -- rerun with "
              f"--gdelt-only (and maybe a higher --gdelt-sleep) to fill them in:")
        for a, b in failed_chunks:
            print(f"        {a} to {b}")
    return pd.DataFrame(all_articles)


# GKG 2.1 column positions (tab-separated, no header)
_GKG_DATE, _GKG_COLLECTION, _GKG_SOURCE, _GKG_URL = 1, 2, 3, 4
_GKG_THEMES, _GKG_LOCATIONS, _GKG_TONE, _GKG_NAMES, _GKG_TRANSLATION, _GKG_EXTRAS = 8, 10, 15, 23, 25, 26
_PAGE_TITLE_RE = re.compile(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>", re.S)


def _normalize(text):
    """Lowercase and turn URL punctuation into spaces, so 'camp-fire' in a
    URL matches the term 'camp fire'."""
    return re.sub(r"[-_/+.]+", " ", text.lower())


def _fetch_gkg_slot(stamp, terms):
    """Download one 15-minute GKG file and return (status, matching rows).
    status is "ok", "missing" (GDELT has a gap here; permanent), or
    "error" (network trouble; worth retrying on a later run)."""
    url = GDELT_GKG_URL.format(stamp=stamp)
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=120)
            if resp.status_code == 404:
                return "missing", []
            resp.raise_for_status()
            break
        except Exception:
            if attempt == 2:
                return "error", []
            time.sleep(5 * (attempt + 1))

    rows = []
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        raw = zf.read(zf.namelist()[0]).decode("utf-8", errors="replace")
    for line in raw.splitlines():
        f = line.split("\t")
        if len(f) <= _GKG_EXTRAS or f[_GKG_COLLECTION] != "1":  # 1 = web articles
            continue
        title_match = _PAGE_TITLE_RE.search(f[_GKG_EXTRAS])
        title = html.unescape(title_match.group(1)).strip() if title_match else ""
        haystack = _normalize(" ".join([f[_GKG_URL], title, f[_GKG_LOCATIONS],
                                        f[_GKG_NAMES], f[_GKG_THEMES]]))
        if not all(term in haystack for term in terms):
            continue
        d = f[_GKG_DATE]
        translation = f[_GKG_TRANSLATION]
        rows.append({
            "url": f[_GKG_URL],
            "title": title,
            "seendate": f"{d[:8]}T{d[8:14]}Z",  # same format as the DOC API's seendate
            "domain": f[_GKG_SOURCE],
            "language": translation.split(";")[0].replace("srclc:", "") if translation else "English",
            "tone": f[_GKG_TONE].split(",")[0],
        })
    return "ok", rows


def fetch_gdelt_bulk(terms, start_date, end_date, save_path, workers=GDELT_GKG_WORKERS):
    """Every GDELT-monitored web article in [start_date, end_date] (UTC,
    end inclusive) whose metadata matches all of `terms`, read from the raw
    15-minute GKG files instead of the rate-limited DOC API.

    Matches are appended to save_path as each batch finishes, and the slots
    already processed are listed in a checkpoint file next to it
    (.<name>.gkg_done), so rerunning after an interruption only downloads
    what's left. Delete the checkpoint to force a full re-scan (e.g. after
    changing the terms).
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    stamps = []
    t = start_dt
    while t < end_dt:
        stamps.append(t.strftime("%Y%m%d%H%M%S"))
        t += timedelta(minutes=15)

    done_path = os.path.join(os.path.dirname(save_path),
                             "." + os.path.basename(save_path).replace(".csv", ".gkg_done"))
    done = set()
    if os.path.exists(done_path):
        with open(done_path) as fh:
            done = {line.strip() for line in fh if line.strip()}
    todo = [s for s in stamps if s not in done]
    print(f"    {len(stamps)} fifteen-minute files in range, {len(stamps) - len(todo)} already "
          f"done, {len(todo)} to download (terms: {terms})")

    total_matches, missing, errors = 0, [], []
    batch, batch_stamps = [], []
    with ThreadPoolExecutor(max_workers=workers) as pool, open(done_path, "a") as done_fh:
        futures = {pool.submit(_fetch_gkg_slot, s, terms): s for s in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            stamp = futures[fut]
            status, rows = fut.result()
            if status == "error":
                errors.append(stamp)
            else:
                if status == "missing":
                    missing.append(stamp)
                batch.extend(rows)
                batch_stamps.append(stamp)
                total_matches += len(rows)
            # flush every 24 files (~6 hours of news) so progress survives an interruption
            if len(batch_stamps) >= 24 or i == len(todo):
                if batch:
                    save_or_append(pd.DataFrame(batch), save_path, dedup_col="url",
                                   label=f"GDELT bulk [{i}/{len(todo)} files]")
                else:
                    print(f"    GDELT bulk [{i}/{len(todo)} files]: no new matches in this batch")
                done_fh.write("".join(s + "\n" for s in batch_stamps))
                done_fh.flush()
                batch, batch_stamps = [], []

    print(f"    GDELT bulk: {total_matches} matching articles this run")
    if missing:
        print(f"    ({len(missing)} slot(s) don't exist on GDELT's side -- normal, small gaps)")
    if errors:
        FAILURES.append(f"GDELT bulk: {len(errors)} file(s)")
        print(f"    ! {len(errors)} file(s) failed to download -- rerun with --gdelt-only "
              f"to retry just those")


def _paginate_pullpush(url, base_params, page_size=PULLPUSH_PAGE_SIZE, max_pages=PULLPUSH_MAX_PAGES):
    """Loop a PullPush search endpoint forward through the full date range.
    Each page's request size is clamped by the server to something around
    100 regardless of what's requested, so a single call over a multi-day
    window only returns its first page. This pages forward using the last
    row's created_utc + 1 as the next `after`, until a page comes back
    smaller than requested (end of data) or `before` is reached.
    """
    all_rows = []
    seen_ids = set()
    after = base_params["after"]
    before = base_params["before"]

    for page in range(max_pages):
        params = dict(base_params, after=after, size=page_size)
        resp = _get(url, params)
        rows = resp.json().get("data", [])
        if not rows:
            break

        new_rows = [r for r in rows if r.get("id") not in seen_ids]
        for r in new_rows:
            seen_ids.add(r.get("id"))
        all_rows.extend(new_rows)

        last_ts = max(r["created_utc"] for r in rows)
        reached_end_of_page = len(rows) < page_size
        reached_before_bound = last_ts >= before
        if reached_end_of_page or reached_before_bound:
            break
        after = last_ts + 1
        time.sleep(1)
    else:
        print(f"    ! hit the {max_pages}-page safety cap -- results may still be truncated")

    return pd.DataFrame(all_rows)


def _utc_window(start_date, end_date):
    """Epoch seconds for [start_date 00:00 UTC, end_date + 1 day 00:00 UTC):
    the same window the GDELT fetchers use, with end_date included. (These
    used to be built in the Mac's local time zone with end_date excluded, so
    Reddit data stopped ~04:00 UTC on end_date while GDELT ran to the end of
    it.)"""
    start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
    return int(start.timestamp()), int(end.timestamp())


def fetch_pullpush(query, start_date, end_date, kind="submission", page_size=PULLPUSH_PAGE_SIZE):
    """Reddit posts or comments matching a keyword, searched site-wide,
    paginated across the full date range."""
    url = PULLPUSH_SUBMISSION_URL if kind == "submission" else PULLPUSH_COMMENT_URL
    after, before = _utc_window(start_date, end_date)
    base_params = {"q": query, "after": after, "before": before, "sort": "asc"}
    return _paginate_pullpush(url, base_params, page_size=page_size)


def _get_arctic_shift(url, params, max_retries=8):
    """GET for Arctic Shift. When it's overloaded it answers HTTP 422 with
    {"error": "Timeout. Maybe slow down a bit"} rather than a 429, so that
    (plus 429/5xx, timeouts and dropped connections) is retried, waiting for its X-RateLimit-Reset header when
    sent, else backing off 10s, 20s, 40s... capped at 120s."""
    for attempt in range(max_retries + 1):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=60)
        except (requests.Timeout, requests.ConnectionError) as e:
            # also what a request in flight looks like after the Mac slept
            if attempt == max_retries:
                raise
            wait = min(10 * 2 ** attempt, 120)
            print(f"    network error ({type(e).__name__}) -- retrying in {wait}s "
                  f"(attempt {attempt + 1}/{max_retries})")
            time.sleep(wait)
            continue
        print(f"    GET {resp.url}")
        print(f"    -> HTTP {resp.status_code}")
        throttled = (resp.status_code == 422 and "slow down" in resp.text.lower()) \
            or resp.status_code == 429 or resp.status_code >= 500
        if not throttled:
            break
        if attempt == max_retries:
            break
        reset = resp.headers.get("X-RateLimit-Reset", "")
        wait = min(max(int(reset) if reset.isdigit() else 0, 10 * 2 ** attempt), 120)
        print(f"    throttled ({resp.text[:60].strip()}) -- retrying in {wait}s "
              f"(attempt {attempt + 1}/{max_retries})")
        time.sleep(wait)
    resp.raise_for_status()
    return resp


def fetch_arctic_shift_subreddit(subreddit, start_date, end_date, kind="posts",
                                 page_size=ARCTIC_SHIFT_PAGE_SIZE, max_pages=PULLPUSH_MAX_PAGES):
    """All posts or comments from one subreddit in the date range (no
    keyword) via Arctic Shift -- the local-signal proxy. Same date-window
    convention as the PullPush fetchers so the files line up. Pages forward
    using the last row's created_utc as the next `after`, deduplicating by
    id, until a short page, a page with nothing new, or `before` is reached.
    If a page still fails after retries, the rows fetched so far are returned
    (and the failure recorded) rather than thrown away; rerunning fills the
    rest, deduplicated by id.
    """
    url = ARCTIC_SHIFT_URL.format(kind=kind)
    after, before = _utc_window(start_date, end_date)

    all_rows, seen_ids = [], set()
    for page in range(max_pages):
        params = {"subreddit": subreddit, "after": after, "before": before,
                  "limit": page_size, "sort": "asc"}
        try:
            body = _get_arctic_shift(url, params).json()
            if body.get("error"):
                raise RuntimeError(f"Arctic Shift error: {body['error']}")
        except Exception as e:
            FAILURES.append(f"r/{subreddit} {kind} (partial: {len(all_rows)} rows kept)")
            print(f"    ! r/{subreddit} {kind} stopped early ({e}); keeping {len(all_rows)} rows")
            break
        rows = body.get("data") or []
        new_rows = [r for r in rows if r.get("id") not in seen_ids]
        if not new_rows:
            break
        seen_ids.update(r.get("id") for r in new_rows)
        all_rows.extend(new_rows)

        last_ts = max(int(r["created_utc"]) for r in rows)
        if len(rows) < page_size or last_ts >= before:
            break
        after = last_ts
        time.sleep(ARCTIC_SHIFT_PAGE_SLEEP)
    else:
        print(f"    ! hit the {max_pages}-page safety cap -- results may still be truncated")

    return pd.DataFrame(all_rows)


def save_or_append(new_df, path, dedup_col=None, label=""):
    """Merge new_df into whatever's already at `path`, drop duplicate rows,
    and write the combined result. Safe to call repeatedly across reruns."""
    if new_df is None:
        new_df = pd.DataFrame()

    if os.path.exists(path):
        try:
            existing_df = pd.read_csv(path)
        except Exception:
            existing_df = pd.DataFrame()
    else:
        existing_df = pd.DataFrame()

    combined = pd.concat([existing_df, new_df], ignore_index=True)
    if dedup_col and dedup_col in combined.columns:
        combined = combined.drop_duplicates(subset=[dedup_col], keep="first")

    combined.to_csv(path, index=False)
    written = os.path.exists(path) and os.path.getsize(path) > 0
    print(f"    {label}: fetched {len(new_df)} rows this run, "
          f"{len(combined)} total rows now in {path} (file written: {written})")


BASELINE_DAYS_BEFORE = 7  # a whole week earlier, so each day lines up with the same weekday


def collect_local(case_name, out, baseline=False):
    """Subreddit-scoped posts and comments for every subreddit in the case.

    baseline=True fetches the same subreddits for the same window shifted
    BASELINE_DAYS_BEFORE days earlier -- an ordinary week, to show the normal
    daily rhythm (e.g. a regular morning rise in activity) that the fire
    week's bursts should be judged against. Saved as *_baseline.csv so it
    never mixes with the fire-week files."""
    case = CASES[case_name]
    start, end = case["start"], case["end"]
    tag = ""
    if baseline:
        shift = timedelta(days=BASELINE_DAYS_BEFORE)
        start = (datetime.strptime(start, "%Y-%m-%d") - shift).strftime("%Y-%m-%d")
        end = (datetime.strptime(end, "%Y-%m-%d") - shift).strftime("%Y-%m-%d")
        tag = "_baseline"
        print(f"  (baseline week: {start} to {end})")
    for sub in case["subreddits"]:
        for kind, suffix in [("posts", "reddit_local"), ("comments", "reddit_local_comments")]:
            print(f"  r/{sub} {kind}{' baseline' if baseline else ''} (subreddit-scoped, Arctic Shift)...")
            try:
                local_df = fetch_arctic_shift_subreddit(sub, start, end, kind)
                save_or_append(local_df, out(f"{case_name}_{sub}_{suffix}{tag}.csv"), dedup_col="id",
                                label=f"r/{sub} local {kind}{tag}")
            except Exception:
                FAILURES.append(f"{case_name} r/{sub} {kind}")
                print(f"    ! r/{sub} local {kind} failed:")
                print(traceback.format_exc())


def collect_case(case_name, out_dir=DATA_DIR, gdelt_chunk_hours=4, gdelt_sleep=10,
                 gdelt_only=False, gdelt_source="bulk", local_only=False, baseline=False):
    case = CASES[case_name]
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n=== Collecting: {case_name} ({case['start']} to {case['end']}) ===")

    def out(filename):
        return os.path.join(out_dir, filename)

    if baseline:
        collect_local(case_name, out, baseline=True)
        return
    if local_only:
        collect_local(case_name, out)
        return

    print(f"  GDELT news coverage ({gdelt_source})...")
    try:
        if gdelt_source == "bulk":
            fetch_gdelt_bulk(case["gdelt_bulk_terms"], case["start"], case["end"],
                             save_path=out(f"{case_name}_gdelt.csv"))
        else:
            gdelt_df = fetch_gdelt_range(case["gdelt_query"], case["start"], case["end"],
                                          chunk_hours=gdelt_chunk_hours, chunk_sleep=gdelt_sleep,
                                          save_path=out(f"{case_name}_gdelt.csv"))
            print(f"    GDELT: fetched {len(gdelt_df)} articles this run")
    except Exception:
        FAILURES.append(f"{case_name} GDELT")
        print("    ! GDELT failed:")
        print(traceback.format_exc())

    if gdelt_only:
        return

    print("  Reddit submissions (site-wide, PullPush)...")
    try:
        sub_df = fetch_pullpush(case["reddit_query"], case["start"], case["end"], "submission")
        save_or_append(sub_df, out(f"{case_name}_reddit_submissions.csv"), dedup_col="id",
                        label="PullPush submissions")
    except Exception:
        FAILURES.append(f"{case_name} reddit submissions")
        print("    ! PullPush submissions failed:")
        print(traceback.format_exc())

    print("  Reddit comments (site-wide, PullPush)...")
    try:
        com_df = fetch_pullpush(case["reddit_query"], case["start"], case["end"], "comment")
        save_or_append(com_df, out(f"{case_name}_reddit_comments.csv"), dedup_col="id",
                        label="PullPush comments")
    except Exception:
        FAILURES.append(f"{case_name} reddit comments")
        print("    ! PullPush comments failed:")
        print(traceback.format_exc())

    collect_local(case_name, out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--case", choices=list(CASES) + ["all"], default="all")
    parser.add_argument("--out-dir", default=DATA_DIR,
                         help="folder to write CSVs into (default: the project's data/ folder, "
                              "no matter where you run this from)")
    parser.add_argument("--gdelt-chunk-hours", type=float, default=4,
                         help="size of each GDELT time chunk in hours (default: 4). "
                              "Lower this if a chunk warns that it hit the 250-record cap.")
    parser.add_argument("--gdelt-sleep", type=float, default=10,
                         help="seconds to wait between GDELT chunk requests (default: 10). "
                              "Raise this if you're seeing repeated 429 rate-limit retries.")
    parser.add_argument("--gdelt-source", choices=["bulk", "api"], default="bulk",
                         help="bulk (default): scan GDELT's raw 15-minute GKG files -- no rate "
                              "limit, complete. api: the rate-limited DOC 2.0 API.")
    parser.add_argument("--local-only", action="store_true",
                         help="only fetch the subreddit-scoped data (Arctic Shift)")
    parser.add_argument("--baseline", action="store_true",
                         help=f"only fetch the subreddit data for an ordinary week "
                              f"({BASELINE_DAYS_BEFORE} days before each fire) -> *_baseline.csv")
    parser.add_argument("--gdelt-only", action="store_true",
                         help="only fetch GDELT, skip Reddit (handy for re-running failed chunks)")
    args = parser.parse_args()

    for name in (list(CASES) if args.case == "all" else [args.case]):
        collect_case(name, out_dir=args.out_dir, gdelt_chunk_hours=args.gdelt_chunk_hours,
                     gdelt_sleep=args.gdelt_sleep, gdelt_only=args.gdelt_only,
                     gdelt_source=args.gdelt_source, local_only=args.local_only,
                     baseline=args.baseline)

    print("\nDone. Each CSV has a timestamp column you can feed into analyze_burst.py:")
    print("  GDELT      -> 'seendate'")
    print("  Reddit (all sources) -> 'created_utc'")

    if FAILURES:
        print(f"\nRUN INCOMPLETE -- {len(FAILURES)} failure(s): {'; '.join(FAILURES)}")
        sys.exit(1)
    print("\nRUN COMPLETE -- every source succeeded.")