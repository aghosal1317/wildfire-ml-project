"""
Zero-shot classification of local Reddit posts with a DeBERTa NLI model.

The model (MoritzLaurer/deberta-v3-large-zeroshot-v2.0) was trained on
natural-language inference: given a "premise" (the post) and a "hypothesis"
(a sentence we write), it outputs how likely the premise entails the
hypothesis. Classification = writing one hypothesis per class and picking
the one the model finds most entailed. No training data needed.

Two questions per post:
  1. relevance: RELEVANCE_HYPOTHESIS -> probability; relevant if >= RELEVANCE_THRESHOLD
  2. category (asked for every post, used for the relevant ones): which of
     the CATEGORY_HYPOTHESES the post most entails

Usage:
    python classify_zeroshot.py                      # gold set only (fast, for evaluation)
    python classify_zeroshot.py --all                # whole corpus (slower)
    python classify_zeroshot.py --input setfit_baseline_holdout.csv --name baseline_holdout
                                                     # any CSV in data/classifier with a text column

Outputs go to data/classifier/zeroshot_<gold|all>.csv
"""

import argparse
import os

import pandas as pd
import torch
from transformers import pipeline

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "classifier")
MODEL = "MoritzLaurer/deberta-v3-large-zeroshot-v2.0"
# Hypotheses and threshold were tuned on the *train* split of the hand labels only
# (gold_labels.csv, split == "train"); the test split is kept for the final comparison.
# "...the August 2023 wildfires on Maui" scored recall 0.01 -- posts never name the
# event that precisely -- while the broader wording below scored F1 0.91 on train.
RELEVANCE_THRESHOLD = 0.1
RELEVANCE_HYPOTHESIS = "This text is about a disaster or its aftermath."
CATEGORY_HYPOTHESES = {
    # a looser "warning people to ... take safety action" was predicted for 28 of 2 true warnings
    "warning": "In this text, the writer tells other people that they need to evacuate or leave right now.",
    "eyewitness": "In this text, the writer describes something they personally saw or experienced.",
    "secondhand": "In this text, the writer passes on information they heard from others or saw in photos or videos.",
    "info_request": "In this text, the writer is asking for information or updates.",
    "news_or_official": "In this text, the writer is sharing a news article, a link, or an official announcement.",
    "help": "In this text, the writer is offering or organizing help, donations, or supplies.",
    "sympathy": "In this text, the writer is expressing sympathy, prayers, or support.",
    "discussion": "In this text, the writer is giving an opinion or arguing about causes or the response.",
}


def classify(texts, batch_size=16):
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    clf = pipeline("zero-shot-classification", model=MODEL, device=device)
    texts = [t[:2000] for t in texts]  # long posts: the first ~2000 chars carry the gist

    # Relevance: one hypothesis, scored on its own (multi_label=True -> independent probability)
    rel = clf(texts, candidate_labels=[RELEVANCE_HYPOTHESIS], hypothesis_template="{}",
              multi_label=True, batch_size=batch_size)
    rel_prob = [r["scores"][0] for r in rel]

    # Category: hypotheses compete; scores are a softmax over the 8 categories
    names = list(CATEGORY_HYPOTHESES)
    hyp_to_name = {h: n for n, h in CATEGORY_HYPOTHESES.items()}
    cat = clf(texts, candidate_labels=list(CATEGORY_HYPOTHESES.values()), hypothesis_template="{}",
              multi_label=False, batch_size=batch_size)
    rows = []
    for p, c in zip(rel_prob, cat):
        scores = {hyp_to_name[label]: s for label, s in zip(c["labels"], c["scores"])}
        rows.append({"zs_relevance_prob": round(p, 4),
                     "zs_relevant": p >= RELEVANCE_THRESHOLD,
                     "zs_category": max(scores, key=scores.get),
                     **{f"zs_{n}": round(scores[n], 4) for n in names}})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true", help="classify the whole corpus, not just the gold set")
    parser.add_argument("--input", help="classify this CSV (in data/classifier) instead")
    parser.add_argument("--name", help="output name with --input: zeroshot_<name>.csv")
    args = parser.parse_args()

    if args.input:
        src, name = args.input, args.name or os.path.splitext(args.input)[0]
    else:
        name = "all" if args.all else "gold"
        src = "lahaina_corpus.csv" if args.all else "gold_labels.csv"
    df = pd.read_csv(os.path.join(DATA_DIR, src), dtype={"id": str})
    print(f"Classifying {len(df)} posts from {src} with {MODEL} ...")
    out = pd.concat([df.reset_index(drop=True), classify(df["text"].fillna("").tolist())], axis=1)
    path = os.path.join(DATA_DIR, f"zeroshot_{name}.csv")
    out.to_csv(path, index=False)
    print(f"Saved {path}")
