"""Fit the topic tagger's confidence model and pick its thresholds on the gold set.

The tagger's raw scores are cosine similarities; they say which node is best,
not how likely the best is right. This turns them into a probability per level
(a logistic model on best score, margin over the runner-up, whether there
was a runner-up, and for the chapter how well the whole Exemplar chapter --
or the pooled existing chapterIds -- matched it, and which of the two the
prior came from), and picks for each level the lowest confidence whose
accepted tags are still at least 90% right -- the rule is that a tag below
it goes to the review queue, not onto the question.

Measured honestly. The thresholds are chosen on OUT-OF-FOLD confidences
(5 folds, seed 703): each gold item's confidence comes from a model that never
saw it. Those out-of-fold numbers are the estimate to quote. The model that is
written is then refitted on every item, and its in-sample numbers are written
alongside -- they are what `tests/test_topic_tagger.py` re-measures, and they
flatter the tagger, which is why they are not the headline.

Gold: ``academicos-data/syllabus/taxonomy/_tag_gold.json`` (labelled by an AI
reviewer, not a teacher): 328 questions drawn at random, counted at every
level, and 61 audit items drawn from the subtopic tags the tagger wrote,
counted at the subtopic level only (``levels``). The audit was added because
the random sample held too few accepted subtopics (11/12 right) to measure
them, and the tags it let through were 24/30 and 34/40 right when checked.
``_tag_audit.json`` is a further, held-out check of the written tags; nothing
here reads it.

Run:  python scripts/calibrate_topic_tagger.py [--check]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.syllabus import tagger as tg  # noqa: E402

TAXONOMY = REPO / "academicos-data" / "syllabus" / "taxonomy"
GOLD = TAXONOMY / "_tag_gold.json"
OUT = TAXONOMY / "_tagger_model.json"
BANKS = {
    "exemplar": REPO / "academicos-data" / "corpus" / "ncert-exemplar" / "questions.json",
    "cbe": REPO / "academicos-data" / "corpus" / "cbse-cbe" / "questions.json",
    "board": REPO / "academicos-data" / "syllabus" / "questions.json",
}
TARGET = 0.90
# A threshold must be shown on at least this many accepted gold tags. Without
# it the subtopic level "passed" on 1 or 2 out-of-fold tags -- a 100% that
# says nothing -- and would have accepted subtopics across the bank on that.
MIN_SUPPORT = 10
FOLDS = 5
SEED = 703
L2 = 1.0


def fit_logistic(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """L2-regularised logistic regression by Newton's method, returned as
    weights on the RAW features (bias first).

    The features are standardised before fitting and the weights mapped back:
    cosine scores and margins live around 0.01-0.3, and an L2 penalty on the
    raw scale shrank the margin -- on the gold set the single best separator of
    right from wrong topics -- almost to nothing."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    A = np.hstack([np.ones((len(Z), 1)), Z])
    w = np.zeros(A.shape[1])
    reg = np.full(A.shape[1], L2)
    reg[0] = 0.0
    for _ in range(100):
        p = 1.0 / (1.0 + np.exp(-A @ w))
        grad = A.T @ (p - y) + reg * w
        H = (A * (p * (1 - p))[:, None]).T @ A + np.diag(reg) + 1e-9 * np.eye(A.shape[1])
        step = np.linalg.solve(H, grad)
        w -= step
        if np.abs(step).max() < 1e-10:
            break
    raw = w[1:] / sd
    return np.concatenate([[w[0] - float(raw @ mu)], raw])


FEATURES = {"chapter": ("best", "margin", "heading", "prior", "hasPrior", "idPrior"),
            "topic": ("best", "margin", "heading", "single"),
            # no "single": the topic-level candidate means a subtopic always
            # has a runner-up, so the feature is constant
            "subtopic": ("best", "margin", "heading")}


def as_coef(level: str, w: np.ndarray) -> dict:
    return {"bias": float(w[0]), **{k: float(x) for k, x in zip(FEATURES[level], w[1:])}}


def row(level: str, f: dict) -> list[float]:
    return [float(f[k]) for k in FEATURES[level]]


def training_sets(rows: list[dict]) -> dict:
    """Per level, (index into rows, features, right?) -- a level is trained only
    on items whose levels above it were right, since its probability is
    conditional on them."""
    sets = {lv: [] for lv in tg.LEVELS}
    for i, r in enumerate(rows):
        tag, j = r["tag"], r["judged"]
        levels = tg.gold_levels(r["item"])
        if "chapter" in levels:
            sets["chapter"].append((i, row("chapter", tag.features["chapter"]), j["chapter"]))
        if "topic" in levels and j["chapter"] and tag.features["topic"] is not None:
            sets["topic"].append((i, row("topic", tag.features["topic"]), j["topic"]))
        if j["topic"] and tag.features["subtopic"] is not None:
            sets["subtopic"].append((i, row("subtopic", tag.features["subtopic"]), j["subtopics"][0]))
    return sets


def fit_all(sets: dict, keep=None) -> dict:
    coef = {}
    for lv, data in sets.items():
        data = [d for d in data if keep is None or d[0] in keep]
        X = np.array([d[1] for d in data], dtype=float)
        y = np.array([1.0 if d[2] else 0.0 for d in data])
        coef[lv] = as_coef(lv, fit_logistic(X, y))
    return coef


def confidences(tag: tg.TagResult, coef: dict) -> dict:
    conf, running = {}, 1.0
    for lv in tg.LEVELS:
        if tag.features[lv] is None:
            conf[lv] = None
            continue
        running *= tg.level_probability(coef[lv], tag.features[lv])
        conf[lv] = running
    return conf


def pick_thresholds(rows: list[dict], conf: list[dict]) -> tuple[dict, dict]:
    """Lowest threshold per level whose accepted tags are >= TARGET right on at
    least MIN_SUPPORT tags, level by level (a topic can only be accepted under
    an accepted chapter). A gold item counts only at its `tg.gold_levels`; a
    subtopic-only audit item still has to clear the chapter and topic
    thresholds to be counted at the subtopic. A level where no threshold does gets 1.01: nothing
    at that level is accepted, everything goes to review."""
    thresholds, measured = {}, {}
    alive = set(range(len(rows)))
    for lv in tg.LEVELS:
        cands = sorted({conf[i][lv] for i in alive if conf[i][lv] is not None}, reverse=True)
        best = (1.01, 0, 0)
        for t in cands:
            right = tags = 0
            for i in alive:
                c = conf[i][lv]
                if c is None or c < t or lv not in tg.gold_levels(rows[i]["item"]):
                    continue
                j = rows[i]["judged"]
                if lv == "subtopic":
                    right += sum(j["subtopics"])
                    tags += len(j["subtopics"])
                else:
                    right += j[lv]
                    tags += 1
            if tags >= MIN_SUPPORT and right / tags >= TARGET and tags >= best[2]:
                best = (t, right, tags)
        thresholds[lv] = round(best[0] - 1e-9, 6) if best[2] else 1.01
        measured[lv] = {"right": best[1], "tags": best[2],
                        "precision": round(best[1] / best[2], 4) if best[2] else None}
        alive = {i for i in alive if conf[i][lv] is not None and conf[i][lv] >= thresholds[lv]}
    return thresholds, measured


def make_folds(rows: list[dict]) -> list[set]:
    """Seeded folds, dealt separately to the random sample (batches 1-2) and
    to the subtopic-only audit items (batch 3): adding audit items then leaves
    the random sample's folds, and so its chapter and topic estimates, as they
    were."""
    folds = [set() for _ in range(FOLDS)]
    for full in (True, False):
        order = [i for i, r in enumerate(rows)
                 if (tuple(tg.gold_levels(r["item"])) == tg.LEVELS) == full]
        random.Random(SEED).shuffle(order)
        for k in range(FOLDS):
            folds[k].update(order[k::FOLDS])
    return folds


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    args = ap.parse_args(argv)

    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    items = gold["items"]
    banks = {k: json.loads(p.read_text(encoding="utf-8"))["questions"] for k, p in BANKS.items()}
    raw_tagger = tg.TopicTagger(model={}, thresholds={})
    wanted = {it["id"] for it in items}
    tags = {}
    for name, records in banks.items():
        for rec, tag in zip(records, raw_tagger.tag_records(records)):
            if rec.get("id") in wanted and tag is not None:
                tags[rec["id"]] = tag
    rows = [{"item": it, "tag": tags[it["id"]], "judged": tg.judge(tags[it["id"]], it)}
            for it in items]
    sets = training_sets(rows)

    # out-of-fold confidences
    folds = make_folds(rows)
    oof: list[dict] = [None] * len(rows)
    for k, held in enumerate(folds):
        coef = fit_all(sets, keep=set(range(len(rows))) - held)
        for i in held:
            oof[i] = confidences(rows[i]["tag"], coef)
    thresholds, oof_measured = pick_thresholds(rows, oof)

    final = fit_all(sets)
    model = {"method": tg.TAG_METHOD,
             "features": {lv: list(f) for lv, f in FEATURES.items()},
             "coefficients": final, "thresholds": thresholds}
    tagger = tg.TopicTagger(model=model)
    in_sample = tg.score_against_gold(tagger, items, banks)

    # conditional accuracy of the raw picks, for the report
    cond = {}
    for lv in tg.LEVELS:
        data = sets[lv]
        cond[lv] = {"right": sum(1 for d in data if d[2]), "of": len(data)}

    print(f"gold items {len(items)}  (labelled by an AI reviewer, not a teacher)")
    for lv in tg.LEVELS:
        r = in_sample["raw"][lv]
        print(f"raw {lv:9s} end-to-end {r['right']:3d}/{r['of']:3d}  "
              f"given the level above right {cond[lv]['right']:3d}/{cond[lv]['of']:3d}")
    for lv in tg.LEVELS:
        o, s = oof_measured[lv], in_sample["accepted"][lv]
        print(f"accepted {lv:9s} threshold {thresholds[lv]:.4f}  out-of-fold "
              f"{o['right']}/{o['tags']} = {o['precision']}   in-sample "
              f"{s['right']}/{s['tags']} = {s['precision']}")
    bad = [lv for lv in tg.LEVELS
           if in_sample["accepted"][lv]["tags"] and in_sample["accepted"][lv]["precision"] < TARGET]
    for lv in tg.LEVELS:
        if thresholds[lv] > 1:
            print(f"{lv}: no threshold reaches {TARGET} on {MIN_SUPPORT}+ gold tags -- "
                  f"nothing is accepted at this level")
    if bad:
        print(f"in-sample precision below {TARGET} at {bad}: refusing to write", file=sys.stderr)
        return 3
    if args.check:
        return 0
    OUT.write_text(json.dumps({
        "notice": ("Confidence model and thresholds of academicos.syllabus.tagger, fitted by "
                   "scripts/calibrate_topic_tagger.py on _tag_gold.json (AI-reviewer labels, "
                   "not a teacher's). Quote the outOfFold numbers; inSample flatters."),
        "method": tg.TAG_METHOD,
        "builtAt": datetime.now(timezone.utc).isoformat(),
        "target": TARGET,
        "minSupport": MIN_SUPPORT,
        "features": {lv: list(f) for lv, f in FEATURES.items()},
        "coefficients": final,
        "thresholds": thresholds,
        "trainedOn": {lv: {"items": len(sets[lv]), "right": cond[lv]["right"]}
                      for lv in tg.LEVELS},
        "gold": {"items": len(items), "folds": FOLDS, "seed": SEED,
                 "outOfFold": {"accepted": oof_measured},
                 "inSample": in_sample},
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
