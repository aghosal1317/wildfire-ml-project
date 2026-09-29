"""
Data collection for the wildfire evacuation alert-failure project.

Pulls two free, keyless data sources for both case studies (Lahaina 2023,
Camp Fire 2018) and saves each as a CSV:

  1. GDELT DOC 2.0 API   - news article volume/tone (free, covers 2017-present)
  2. PullPush            - Reddit posts/comments (free, mirrors old Pushshift)
     - site-wide keyword search -> *_reddit_submissions.csv / *_reddit_comments.csv
     - subreddit-scoped, no keyword -> *_<subreddit>_reddit_local.csv
       (everything posted in that subreddit in the date window -- the local-
       signal proxy that Arctic Shift used to provide)

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
    python collect_data.py --out-dir ../data   # write CSVs to a different folder than cwd
    python collect_data.py --gdelt-chunk-hours 2   # if a chunk warns it hit the cap
"""

import argparse
import os
import time
import traceback
from datetime import datetime, timedelta

import pandas as pd
import requests

CASES = {
    "lahaina": {
        "gdelt_query": '"Lahaina" fire',
        "reddit_query": "Lahaina fire",
        "subreddits": ["Hawaii", "Maui"],
        "start": "2023-08-08",
        "end": "2023-08-11",
    },
    "camp_fire": {
        "gdelt_query": '"Camp Fire" Paradise California',
        "reddit_query": "Paradise Camp Fire California",
        "subreddits": ["California", "Chico"],
        "start": "2018-11-08",
        "end": "2018-11-12",
    },
}

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_MAX_RECORDS = 250

PULLPUSH_SUBMISSION_URL = "https://api.pullpush.io/reddit/search/submission/"
PULLPUSH_COMMENT_URL = "https://api.pullpush.io/reddit/search/comment/"
PULLPUSH_PAGE_SIZE = 100
PULLPUSH_MAX_PAGES = 500  # safety cap, not expected to be hit in normal use

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
                       chunk_sleep=10):
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
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # end_date inclusive

    all_articles = []
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
        resp = _get(GDELT_URL, params, max_retries=8, base_wait=10, max_wait=60)
        articles = resp.json().get("articles", [])
        if len(articles) >= max_records:
            print(f"    ! chunk {chunk_start}-{chunk_end} returned the {max_records}-record "
                  f"cap -- likely still truncated; rerun with a smaller --gdelt-chunk-hours")
        all_articles.extend(articles)
        chunk_start = chunk_end

    return pd.DataFrame(all_articles)


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


def fetch_pullpush(query, start_date, end_date, kind="submission", page_size=PULLPUSH_PAGE_SIZE):
    """Reddit posts or comments matching a keyword, searched site-wide,
    paginated across the full date range."""
    url = PULLPUSH_SUBMISSION_URL if kind == "submission" else PULLPUSH_COMMENT_URL
    after = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    before = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    base_params = {"q": query, "after": after, "before": before, "sort": "asc"}
    return _paginate_pullpush(url, base_params, page_size=page_size)


def fetch_pullpush_subreddit(subreddit, start_date, end_date, page_size=PULLPUSH_PAGE_SIZE):
    """All submissions from one specific subreddit in the date range (no
    keyword), paginated across the full range -- the local-signal proxy,
    via PullPush's `subreddit` filter instead of Arctic Shift."""
    after = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    before = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    base_params = {"subreddit": subreddit, "after": after, "before": before, "sort": "asc"}
    return _paginate_pullpush(PULLPUSH_SUBMISSION_URL, base_params, page_size=page_size)


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


def collect_case(case_name, out_dir=".", gdelt_chunk_hours=4, gdelt_sleep=10):
    case = CASES[case_name]
    print(f"\n=== Collecting: {case_name} ({case['start']} to {case['end']}) ===")

    def out(filename):
        return os.path.join(out_dir, filename)

    print("  GDELT news coverage...")
    try:
        gdelt_df = fetch_gdelt_range(case["gdelt_query"], case["start"], case["end"],
                                      chunk_hours=gdelt_chunk_hours, chunk_sleep=gdelt_sleep)
        save_or_append(gdelt_df, out(f"{case_name}_gdelt.csv"), dedup_col="url", label="GDELT")
    except Exception:
        print("    ! GDELT failed:")
        print(traceback.format_exc())

    print("  Reddit submissions (site-wide, PullPush)...")
    try:
        sub_df = fetch_pullpush(case["reddit_query"], case["start"], case["end"], "submission")
        save_or_append(sub_df, out(f"{case_name}_reddit_submissions.csv"), dedup_col="id",
                        label="PullPush submissions")
    except Exception:
        print("    ! PullPush submissions failed:")
        print(traceback.format_exc())

    print("  Reddit comments (site-wide, PullPush)...")
    try:
        com_df = fetch_pullpush(case["reddit_query"], case["start"], case["end"], "comment")
        save_or_append(com_df, out(f"{case_name}_reddit_comments.csv"), dedup_col="id",
                        label="PullPush comments")
    except Exception:
        print("    ! PullPush comments failed:")
        print(traceback.format_exc())

    for sub in case["subreddits"]:
        print(f"  r/{sub} (subreddit-scoped, PullPush)...")
        try:
            local_df = fetch_pullpush_subreddit(sub, case["start"], case["end"])
            save_or_append(local_df, out(f"{case_name}_{sub}_reddit_local.csv"), dedup_col="id",
                            label=f"r/{sub} local")
        except Exception:
            print(f"    ! r/{sub} local failed:")
            print(traceback.format_exc())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--case", choices=list(CASES) + ["all"], default="all")
    parser.add_argument("--out-dir", default=".",
                         help="folder to write CSVs into (default: current directory). "
                              "E.g. --out-dir ../data if running from a src/ folder.")
    parser.add_argument("--gdelt-chunk-hours", type=float, default=4,
                         help="size of each GDELT time chunk in hours (default: 4). "
                              "Lower this if a chunk warns that it hit the 250-record cap.")
    parser.add_argument("--gdelt-sleep", type=float, default=10,
                         help="seconds to wait between GDELT chunk requests (default: 10). "
                              "Raise this if you're seeing repeated 429 rate-limit retries.")
    args = parser.parse_args()

    for name in (list(CASES) if args.case == "all" else [args.case]):
        collect_case(name, out_dir=args.out_dir, gdelt_chunk_hours=args.gdelt_chunk_hours,
                     gdelt_sleep=args.gdelt_sleep)

    print("\nDone. Each CSV has a timestamp column you can feed into analyze_burst.py:")
    print("  GDELT      -> 'seendate'")
    print("  Reddit (all sources) -> 'created_utc'")