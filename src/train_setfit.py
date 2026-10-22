"""
Few-shot classification of local Reddit posts with SetFit.

SetFit (Tunstall et al., 2022) has two stages:
  1. Contrastive fine-tuning of a sentence-embedding model: pairs of training
     posts with the same label are pulled together, different labels pushed
     apart. Generating many pairs from few posts is why it works with small
     labeled sets.
  2. A logistic-regression head trained on the tuned embeddings.

Trains two models on the hand-labeled *train* split (data/classifier/gold_labels.csv):
  - relevance: about the fires or not, plus BASELINE_NEGATIVES posts from the
    normal week (lahaina_baseline.csv, built by build_corpus.py) labeled
    not_relevant. Without them the model flagged ordinary chatter (Safeway
    rats, Honolulu car crashes) as fire-related across the whole corpus. A
    separate BASELINE_HOLDOUT of normal-week posts is predicted for
    evaluate_classifiers.py to measure false alarms.
  - category:  the 8 information types, trained on relevant posts only

Usage:
    python train_setfit.py            # train both, predict the gold set
    python train_setfit.py --all      # also predict the whole corpus
    python train_setfit.py --retrain relevance   # retrain one model (relevance|category|both)

Models are saved to models/setfit_relevance and models/setfit_category (not committed);
predictions to data/classifier/setfit_<gold|all>.csv
"""

import argparse
import os

import pandas as pd
import torch
from datasets import Dataset
from setfit import SetFitModel, Trainer, TrainingArguments

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA_DIR = os.path.join(ROOT, "data", "classifier")
MODEL_DIR = os.path.join(ROOT, "models")
BASE_MODEL = "sentence-transformers/paraphrase-mpnet-base-v2"
SEED = 42
BASELINE_NEGATIVES = 150   # normal-week posts added to relevance training as not_relevant
BASELINE_HOLDOUT = 500     # other normal-week posts, never trained on, for the false-alarm rate


def train(texts, labels, out_name):
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = SetFitModel.from_pretrained(BASE_MODEL, device=device)
    ds = Dataset.from_dict({"text": [t[:2000] for t in texts], "label": labels})
    args = TrainingArguments(batch_size=16, num_epochs=1, num_iterations=20, seed=SEED)
    Trainer(model=model, args=args, train_dataset=ds).train()
    path = os.path.join(MODEL_DIR, out_name)
    model.save_pretrained(path)
    print(f"  saved {path}")
    return model


def predict(model, texts):
    return list(model.predict([t[:2000] for t in texts], batch_size=64, show_progress_bar=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true", help="also classify the whole corpus")
    parser.add_argument("--retrain", choices=["relevance", "category", "both"],
                        help="retrain these models even if saved ones exist")
    args = parser.parse_args()

    gold = pd.read_csv(os.path.join(DATA_DIR, "gold_labels.csv"), dtype={"id": str})
    tr = gold[gold.split == "train"]
    print(f"Training on {len(tr)} posts ({tr.relevant.sum()} relevant)")

    def load_or_train(name, texts, labels):
        path = os.path.join(MODEL_DIR, name)
        if os.path.exists(os.path.join(path, "model_head.pkl")) and args.retrain not in (name.split("_")[1], "both"):
            print(f"  loading saved {path} (use --retrain to train again)")
            return SetFitModel.from_pretrained(path)
        return train(texts, labels, name)

    base = pd.read_csv(os.path.join(DATA_DIR, "lahaina_baseline.csv"), dtype={"id": str}).sample(frac=1, random_state=SEED)
    base_train = base.iloc[:BASELINE_NEGATIVES]
    base_holdout = base.iloc[BASELINE_NEGATIVES:BASELINE_NEGATIVES + BASELINE_HOLDOUT]

    print(f"Relevance model ... (+{len(base_train)} normal-week posts as not_relevant)")
    rel_model = load_or_train("setfit_relevance",
                              tr.text.fillna("").tolist() + base_train.text.fillna("").tolist(),
                              tr.relevant.map({True: "relevant", False: "not_relevant"}).tolist()
                              + ["not_relevant"] * len(base_train))
    print("Category model ...")
    trr = tr[tr.relevant]
    cat_model = load_or_train("setfit_category", trr.text.fillna("").tolist(), trr.label.tolist())

    targets = [("gold", gold), ("baseline_holdout", base_holdout)]
    if args.all:
        targets.append(("all", pd.read_csv(os.path.join(DATA_DIR, "lahaina_corpus.csv"), dtype={"id": str})))
    for name, df in targets:
        texts = df.text.fillna("").tolist()
        df = df.copy()
        df["sf_relevant"] = [p == "relevant" for p in predict(rel_model, texts)]
        df["sf_category"] = predict(cat_model, texts)
        path = os.path.join(DATA_DIR, f"setfit_{name}.csv")
        df.to_csv(path, index=False)
        print(f"Saved {path}")
