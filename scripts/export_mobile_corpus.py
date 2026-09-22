"""Exports the real, already-extracted question corpus (all subjects/grades)
into a single compact JSON file for bundling as a Flutter asset -- the
on-device data source for the standalone Android build. Only the final
extracted questions + marking schemes are exported, not raw source PDFs or
parse artifacts, so this is a small fraction of academicos-data's 1.24GB.

Retired as a writer. It discovered subject/grade pairs from the registry's
question papers -- only grades X and XII exist there -- and wrote that
board-only export over frontend/assets/corpus/questions.json. Once the served
bank merged CBE and SQP questions (4,475 served: 3,286 board, 386 CBE, 803
SQP), running it would silently strip every CBE/SQP item from the offline app.
It now refuses and names the scripts that own the APK copy.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "export_mobile_corpus.py no longer writes the APK corpus.\n"
        "It rebuilt it from registry question papers only -- grades X and XII -- and\n"
        "wrote that straight over frontend/assets/corpus/questions.json, which would\n"
        "silently delete every merged CBE and SQP question from the offline app.\n"
        "The APK copy is now written by scripts/merge_question_banks.py (and kept in\n"
        "step by scripts/enrich_question_bank.py). Run those instead.",
        file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
