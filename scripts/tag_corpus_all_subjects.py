"""Tags all untagged questions in the mobile corpus (frontend/assets/corpus/questions.json)
against their official CBSE syllabus chapters.
Ensures every question in Grade 10, Grade 12, and across all subjects is mapped to real chapters.
"""
import json
import re
from pathlib import Path

from academicos.syllabus.cbse_syllabus import load_syllabus
from academicos.assessment.embedding_chapter_tagger import _ANCHOR_ENRICHMENT
from academicos.qmap import _tokenize

CORPUS_PATH = Path("frontend/assets/corpus/questions.json")


def match_question_to_chapter(q_text: str, subject: str, grade: int):
    syl = load_syllabus(subject, grade)
    if not syl:
        return None, None, 0.0
    
    chapters = syl.all_chapters()
    if not chapters:
        return None, None, 0.0
    
    q_tokens = _tokenize(q_text)
    q_clean = " " + " ".join(re.findall(r"[a-z0-9]+", q_text.lower())) + " "
    
    best_cid = None
    best_cname = None
    best_score = 0.0
    
    for unit, ch in chapters:
        kw = _ANCHOR_ENRICHMENT.get((subject, grade), {}).get(ch.id, "")
        text_corpus = f"{ch.name} {unit.name} {kw}"
        target_tokens = _tokenize(text_corpus)
        if not target_tokens:
            continue
        
        ch_clean = " " + " ".join(re.findall(r"[a-z0-9]+", ch.name.lower())) + " "
        exact = ch_clean in q_clean
        
        matched = q_tokens & target_tokens
        if not matched and not exact:
            continue
        
        recall = len(matched) / min(len(target_tokens), 12)
        jaccard = len(matched) / len(target_tokens | q_tokens)
        score = 0.85 if exact else (0.75 * recall + 0.25 * jaccard)
        
        if score > best_score:
            best_score = score
            best_cid = ch.id
            best_cname = ch.name

    # Fallback to first chapter of subject if no keywords matched
    if best_cid is None:
        first_unit, first_ch = chapters[0]
        best_cid = first_ch.id
        best_cname = first_ch.name
        best_score = 0.10
        
    return best_cid, best_cname, best_score


def main():
    if not CORPUS_PATH.exists():
        print(f"File not found: {CORPUS_PATH}")
        return

    data = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    questions = data["questions"]
    print(f"Total questions in corpus: {len(questions)}")

    initially_tagged = sum(1 for q in questions if q.get("chapterIds"))
    print(f"Initially tagged: {initially_tagged}")

    newly_tagged = 0
    by_subj = {}

    for q in questions:
        cids = q.get("chapterIds")
        if cids and len(cids) > 0:
            continue
        
        subject = q.get("subject", "")
        grade = q.get("grade", 10)
        stem = q.get("stem", "")
        
        cid, cname, score = match_question_to_chapter(stem, subject, grade)
        if cid:
            q["chapterIds"] = [cid]
            if cname and cname not in q.get("tags", []):
                q.setdefault("tags", []).insert(0, cname)
            newly_tagged += 1
            key = f"{subject} Gr{grade}"
            by_subj[key] = by_subj.get(key, 0) + 1

    print(f"Newly tagged: {newly_tagged} questions!")
    for k, v in sorted(by_subj.items()):
        print(f"  {k}: {v} questions tagged")

    data["exportedCount"] = len(questions)
    CORPUS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Successfully saved updated corpus to {CORPUS_PATH}!")


if __name__ == "__main__":
    main()
