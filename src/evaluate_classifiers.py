"""
Compare the keyword filter, zero-shot DeBERTa and SetFit on the held-out
*test* split of the hand labels (data/classifier/gold_labels.csv).

Also measures FALSE ALARMS on held-out normal-week posts (7 days before the
fire; by construction none are about it), which the test split alone can't
show well: it has few ordinary-chatter posts.

None of the methods saw the test posts: the zero-shot hypotheses were tuned
and SetFit was trained on the train split only. With ~110 test posts the
scores are noisy, so each comes with a 95% bootstrap interval (resample the
test posts with replacement 1000 times, recompute, take the 2.5-97.5th
percentiles).

Usage:
    python evaluate_classifiers.py
"""

import os

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_recall_fscore_support

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "classifier")
rng = np.random.default_rng(0)


def bootstrap(y, p, metric, n=1000):
    y, p = np.asarray(y), np.asarray(p)
    vals = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        vals.append(metric(y[i], p[i]))
    return np.percentile(vals, [2.5, 97.5])


def main():
    gold = pd.read_csv(os.path.join(DATA_DIR, "gold_labels.csv"), dtype={"id": str})
    zs = pd.read_csv(os.path.join(DATA_DIR, "zeroshot_gold.csv"), dtype={"id": str})[["id", "zs_relevant", "zs_category"]]
    sf = pd.read_csv(os.path.join(DATA_DIR, "setfit_gold.csv"), dtype={"id": str})[["id", "sf_relevant", "sf_category"]]
    df = gold.merge(zs, on="id").merge(sf, on="id")
    te = df[df.split == "test"]
    print(f"Test split: {len(te)} posts, {te.relevant.sum()} relevant\n")

    print("RELEVANCE -- is the post about the fires?")
    print(f"  {'method':15s} {'precision':>9} {'recall':>7} {'F1':>5}   F1 95% interval")
    f1 = lambda y, p: f1_score(y, p, zero_division=0)
    for name, col in [("keyword filter", "keyword_match"), ("zero-shot", "zs_relevant"), ("SetFit", "sf_relevant")]:
        p, r, f, _ = precision_recall_fscore_support(te.relevant, te[col], average="binary", zero_division=0)
        lo, hi = bootstrap(te.relevant, te[col], f1)
        print(f"  {name:15s} {p:9.2f} {r:7.2f} {f:5.2f}   [{lo:.2f}, {hi:.2f}]")
    print("  (the sample over-represents keyword matches, so keyword precision/recall here\n"
          "   aren't the corpus-wide values -- compare methods against each other)\n")

    rel = te[te.relevant]
    print(f"CATEGORY -- on the {len(rel)} relevant test posts (keyword filter can't do this)")
    macro = lambda y, p: f1_score(y, p, average="macro", zero_division=0)
    for name, col in [("zero-shot", "zs_category"), ("SetFit", "sf_category")]:
        lo, hi = bootstrap(rel.label, rel[col], macro)
        print(f"  {name:10s} accuracy {accuracy_score(rel.label, rel[col]):.2f}   "
              f"macro-F1 {macro(rel.label, rel[col]):.2f} [{lo:.2f}, {hi:.2f}]")
    for name, col in [("zero-shot", "zs_category"), ("SetFit", "sf_category")]:
        print(f"\n  per-category, {name}:")
        print(classification_report(rel.label, rel[col], zero_division=0, digits=2))


def false_alarms():
    path = os.path.join(DATA_DIR, "setfit_baseline_holdout.csv")
    if not os.path.exists(path):
        return
    b = pd.read_csv(path, dtype={"id": str})
    zs_path = os.path.join(DATA_DIR, "zeroshot_baseline_holdout.csv")
    if os.path.exists(zs_path):
        b = b.merge(pd.read_csv(zs_path, dtype={"id": str})[["id", "zs_relevant"]], on="id", how="left")
    print(f"\nFALSE ALARMS -- share of {len(b)} held-out normal-week posts (Jul 31-Aug 4) flagged as fire-related")
    for name, col in [("keyword filter", "keyword_match"), ("zero-shot", "zs_relevant"), ("SetFit", "sf_relevant")]:
        if col in b:
            print(f"  {name:15s} {b[col].mean():6.1%}  ({int(b[col].sum())} posts)")


if __name__ == "__main__":
    main()
    false_alarms()
