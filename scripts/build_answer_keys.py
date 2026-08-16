"""Parses every CBSE marking scheme in the corpus into the answer-key store.

Run after the marking-scheme archives have been expanded:

    python scripts/build_answer_keys.py --run

Without --run it reports what it would parse and stops, so a first invocation
cannot quietly rewrite an existing store.
"""
from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from academicos.assessment import answer_key as ak  # noqa: E402
from academicos.config import Config  # noqa: E402

CORPUS = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\cbse-dataset\marking-schemes")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true",
                        help="actually write the store (default: dry run)")
    parser.add_argument("--root", type=Path, default=CORPUS)
    parser.add_argument("--limit", type=int, default=0,
                        help="parse at most N files (for a quick smoke test)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = Config.load()

    files = ak.discover_marking_schemes(args.root)
    if args.limit:
        files = files[: args.limit]
    print(f"found {len(files)} marking-scheme PDFs under {args.root}")

    by_subject = Counter(ak.subject_from_path(p) or "(unknown)" for p in files)
    for subject, n in by_subject.most_common(20):
        print(f"  {subject:<20} {n}")

    if not args.run:
        print("\ndry run — pass --run to write the answer-key store")
        return 0

    store = ak.AnswerKeyStore(ak.default_db(cfg))
    written = variants = failed = 0
    for i, path in enumerate(files, 1):
        try:
            keys = ak.parse_marking_scheme(path)
        except Exception as exc:
            failed += 1
            logging.warning("failed %s: %s", path.name, exc)
            continue
        for key in keys:
            written += store.put(key, source=path.name)
            variants += 1
        if i % 100 == 0:
            print(f"  {i}/{len(files)} files, {written} answers so far")

    stats = store.stats()
    store.close()
    print(f"\nparsed {len(files)} files ({failed} unreadable)")
    print(f"answers:          {stats['total']}")
    print(f"  with a key:     {stats['objective']} objective")
    print(f"paper variants:   {stats['papers']}")
    print(f"store:            {ak.default_db(cfg)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
