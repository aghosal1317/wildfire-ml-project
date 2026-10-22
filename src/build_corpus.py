"""
Build the text corpora the classifiers run on, from the local-subreddit CSVs.

  data/classifier/lahaina_corpus.csv    fire week   (r/Maui + r/Hawaii, posts + comments)
  data/classifier/lahaina_baseline.csv  normal week (same subreddits, 7 days earlier --
                                        collect_data.py --baseline)

Every normal-week post is "not about the fires" by construction (they hadn't
happened yet), which makes the baseline a free source of correctly labeled
negatives: train_setfit.py adds some as training examples, and
evaluate_classifiers.py measures false alarms on the rest.

Usage:
    python build_corpus.py
"""

import os

import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
OUT = os.path.join(DATA, "classifier")
HST = "Pacific/Honolulu"
SUBS = ["Maui", "Hawaii"]
# the earlier keyword filter, kept as the baseline method to compare against
KEYWORDS = (r"\b(?:fires?|wildfires?|brush ?fires?|smoke|evacuat\w*|burn(?:ed|ing|t|s)?|flames?|embers?|"
            r"shelters?|sirens?|red cross|power (?:is )?out|outages?)\b")


def load(suffix=""):
    parts = []
    for sub in SUBS:
        for kind, name in [("post", f"lahaina_{sub}_reddit_local{suffix}.csv"),
                           ("comment", f"lahaina_{sub}_reddit_local_comments{suffix}.csv")]:
            path = os.path.join(DATA, name)
            if not os.path.exists(path):
                print(f"  (missing {name})")
                continue
            d = pd.read_csv(path, low_memory=False)
            if kind == "post":
                body = d.get("selftext", pd.Series("", index=d.index)).fillna("").astype(str)
                text = d.get("title", pd.Series("", index=d.index)).fillna("").astype(str) + ". " + \
                    body.replace({"[deleted]": "", "[removed]": ""})
            else:
                text = d["body"].fillna("").astype(str)
            parts.append(pd.DataFrame({
                "id": d["id"].astype(str), "sub": sub, "kind": kind,
                "time_hst": pd.to_datetime(d["created_utc"], unit="s", utc=True).dt.tz_convert(HST)
                              .dt.strftime("%Y-%m-%d %H:%M"),
                "text": text.str.replace(r"\s+", " ", regex=True).str.strip(" ."),
            }))
    c = pd.concat(parts)
    c = c[~c["text"].isin(["", "[deleted]", "[removed]"])].drop_duplicates("id")
    c["keyword_match"] = c["text"].str.contains(KEYWORDS, case=False, regex=True)
    return c.sort_values("time_hst").reset_index(drop=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, suffix in [("lahaina_corpus.csv", ""), ("lahaina_baseline.csv", "_baseline")]:
        c = load(suffix)
        c.to_csv(os.path.join(OUT, name), index=False)
        print(f"{name}: {len(c)} posts, {c.keyword_match.sum()} keyword-matched, "
              f"{c.time_hst.min()} -> {c.time_hst.max()} HST")
