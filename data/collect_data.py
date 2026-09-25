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

Arctic Shift has been dropped: on this machine's network, TLS connections to
arctic-shift.photon-reddit.com fail at the SSL handshake itself (confirmed
with plain `curl`, not just Python) -- something between this machine and
that specific host, likely network-level filtering rather than anything
fixable in the script. PullPush's API supports a `subreddit` filter
parameter on the same submission-search endpoint already in use, so the
same local-subreddit data is available from a source that's confirmed
reachable, without depending on the blocked host at all.

Re-running this script is safe: each source's CSV is loaded, new rows are
appended, and duplicates are dropped (by article URL for GDELT, by post/
comment id for Reddit) before saving -- so running it daily just grows the
same file instead of overwriting it.

Twitter/X is not included: its API has required a paid tier since 2023 with
no free historical-search option.

Setup:
    pip install requests pandas

Usage:
    python collect_data.py --case lahaina
    python collect_data.py --case camp_fire
    python collect_data.py --case all          # default
"""

import argparse
import os
import time
import traceback
from datetime import datetime

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
PULLPUSH_SUBMISSION_URL = "https://api.pullpush.io/reddit/search/submission/"
PULLPUSH_COMMENT_URL = "https://api.pullpush.io/reddit/search/comment/"

HEADERS = {"User-Agent": "wildfire-evac-research/0.4 (student research project)"}


def _get(url, params):
    """GET with the request URL and HTTP status printed, so a failure is
    diagnosable (and the printed URL can be pasted into a browser to check
    directly) instead of disappearing into a generic error message."""
    resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
    print(f"    GET {resp.url}")
    print(f"    -> HTTP {resp.status_code}")
    resp.raise_for_status()
    return resp


def fetch_gdelt(query, start_date, end_date, max_records=250):
    """News articles from GDELT DOC 2.0. Rate limit: 1 request per 5 seconds."""
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "startdatetime": start_date.replace("-", "") + "000000",
        "enddatetime": end_date.replace("-", "") + "235959",
        "maxrecords": max_records,
        "sort": "datedesc",
    }
    resp = _get(GDELT_URL, params)
    articles = resp.json().get("articles", [])
    return pd.DataFrame(articles)


def fetch_pullpush(query, start_date, end_date, kind="submission", size=250):
    """Reddit posts or comments matching a keyword, searched site-wide."""
    url = PULLPUSH_SUBMISSION_URL if kind == "submission" else PULLPUSH_COMMENT_URL
    after = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    before = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    params = {"q": query, "after": after, "before": before, "size": size, "sort": "asc"}
    resp = _get(url, params)
    data = resp.json().get("data", [])
    return pd.DataFrame(data)


def fetch_pullpush_subreddit(subreddit, start_date, end_date, size=250):
    """All submissions from one specific subreddit in the date range (no
    keyword) -- the local-signal proxy, now via PullPush's `subreddit`
    filter instead of Arctic Shift."""
    after = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    before = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    params = {"subreddit": subreddit, "after": after, "before": before,
              "size": size, "sort": "asc"}
    resp = _get(PULLPUSH_SUBMISSION_URL, params)
    data = resp.json().get("data", [])
    return pd.DataFrame(data)


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


def collect_case(case_name):
    case = CASES[case_name]
    print(f"\n=== Collecting: {case_name} ({case['start']} to {case['end']}) ===")

    print("  GDELT news coverage...")
    try:
        gdelt_df = fetch_gdelt(case["gdelt_query"], case["start"], case["end"])
        save_or_append(gdelt_df, f"{case_name}_gdelt.csv", dedup_col="url", label="GDELT")
    except Exception:
        print("    ! GDELT failed:")
        print(traceback.format_exc())
    time.sleep(5)  # GDELT's rate limit is 1 request per 5 seconds

    print("  Reddit submissions (site-wide, PullPush)...")
    try:
        sub_df = fetch_pullpush(case["reddit_query"], case["start"], case["end"], "submission")
        save_or_append(sub_df, f"{case_name}_reddit_submissions.csv", dedup_col="id",
                        label="PullPush submissions")
    except Exception:
        print("    ! PullPush submissions failed:")
        print(traceback.format_exc())

    print("  Reddit comments (site-wide, PullPush)...")
    try:
        com_df = fetch_pullpush(case["reddit_query"], case["start"], case["end"], "comment")
        save_or_append(com_df, f"{case_name}_reddit_comments.csv", dedup_col="id",
                        label="PullPush comments")
    except Exception:
        print("    ! PullPush comments failed:")
        print(traceback.format_exc())

    for sub in case["subreddits"]:
        print(f"  r/{sub} (subreddit-scoped, PullPush)...")
        try:
            local_df = fetch_pullpush_subreddit(sub, case["start"], case["end"])
            save_or_append(local_df, f"{case_name}_{sub}_reddit_local.csv", dedup_col="id",
                            label=f"r/{sub} local")
        except Exception:
            print(f"    ! r/{sub} local failed:")
            print(traceback.format_exc())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=list(CASES) + ["all"], default="all")
    args = parser.parse_args()

    for name in (list(CASES) if args.case == "all" else [args.case]):
        collect_case(name)

    print("\nDone. Each CSV has a timestamp column you can feed into analyze_burst.py:")
    print("  GDELT      -> 'seendate'")
    print("  Reddit (all sources) -> 'created_utc'")