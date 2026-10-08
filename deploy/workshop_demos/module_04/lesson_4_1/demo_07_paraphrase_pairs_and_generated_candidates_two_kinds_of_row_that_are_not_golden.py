"""Lesson 4.1: Paraphrase pairs and generated candidates: two kinds of row that are not golden

The answer cache of Module 6 serves an earlier answer when a new question's embedding has a cosine similarity of at least 0.95 with an earlier one. That number was chosen, not measured. paraphrases.jsonl is what measures it. Each pair rewords a golden question. A pair marked same asks the same fact in other words, so a cache hit would be right. A pair marked different is a few words away with a different answer: E3 against E2, minimum against maximum, probation against confirmed. A cache hit there is a wrong answer served fast. cache_threshold.py embeds both sides and prints, for each candidate threshold, the hit rate on the same pairs and the false-hit rate on the different ones. The cache stays off until a threshold has no false hit on this set. The labels are yours to get right: the self-test checks that each pair names a real golden row and differs from its question, not that its label is true. Add two pairs against lk-32. One asks the same fact in other words. The other asks the clause's other fact, the kind of near miss a loose threshold would answer with 45 days. make make-evalset asks Gemini for one question and answer per chunk of the quality-gated feed. The feed is rag_data.index_feed, joined to the chunks the worker mirrors into BigQuery, so a chunk the quality scan held back never becomes a question. Each pair is scanned by the one PII list, shared/pii.py, and dropped on any finding, never rewritten. What comes out is a candidate: a question with no figure it must contain, and the chunk's id as its only anchor. A golden row is a contract a person writes, and a generated question inherits the blind spots of the model that wrote it. So the file is golden_generated.jsonl, and the gate never reads it. What would the gate say if a candidate were merged as it is? The cell builds one for SEC-09 the way make_evalset.py writes it. Its chunk id is the worker's own: the tenant, the hash of the handbook's bytes, and #8, SEC-09's position after the preamble and seven clauses. Then the cell judges the reviewed version.

Run order inside this file:
1. Paraphrase pairs (source window 34)
2. Generated candidates (source window 39)

Prerequisites: demo_06_ask_the_two_rows_once_the_live_half_s_own_functions_and_the_outsider_s_403.
Use the existing rag-shell-venv interpreter; Run or Debug this file.
The functions below contain the lesson examples in source order. Helpers
supply configuration, authentication, state and CLI execution. See README.md
for expected observations, effects and the next file; GUIDE.md retains prose.
Example: open this file at the matching HTML heading, Run once, then inspect
the observations below before continuing to the next numbered section.
A successful process is not proof that a live result matched the sample.

"""
from workshop_helpers.session import DemoSession
from workshop_helpers.steps import manual_checkpoint, run_steps

# REPEAT replays the whole file; use only after reviewing its effects.
REPEAT = False
# A failed function may have partial effects. Inspect its saved attempt first.
RETRY_FAILED_STEP = False


# Original CLI workflow for step_01_paraphrase_pairs.
COMMANDS_01 = """python - <<'PY'
import json
from pathlib import Path
p = Path("evals/paraphrases.jsonl")
new = [{"id": "pp-43", "of": "lk-32", "question": "After how many days without use is an account switched off?",
        "same": True, "why": "reworded", "tenant": "acme"},
       {"id": "pp-44", "of": "lk-32", "question": "How often is production access reviewed?",
        "same": False, "why": "the same clause, another fact: quarterly, not 45 days", "tenant": "acme"}]
keep = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and json.loads(l)["id"] not in ("pp-43", "pp-44")]
p.write_text("\\n".join(keep + [json.dumps(r, ensure_ascii=False) for r in new]) + "\\n", encoding="utf-8", newline="\\n")
print(len(keep) + len(new), "pairs; the last two are against lk-32")
PY
python evals/cache_threshold.py --selftest

"""

def step_01_paraphrase_pairs(session):
    """Run Paraphrase pairs at this checkpoint.

    The answer cache of Module 6 serves an earlier answer when a new question's embedding has a cosine similarity of at least 0.95 with an earlier one. That number was chosen, not measured. paraphrases.jsonl is what measures it. Each pair rewords a golden question. A pair marked same asks the same fact in other words, so a cache hit would be right. A pair marked different is a few words away with a different answer: E3 against E2, minimum against maximum, probation against confirmed. A cache hit there is a wrong answer served fast. cache_threshold.py embeds both sides and prints, for each candidate threshold, the hit rate on the same pairs and the false-hit rate on the different ones. The cache stays off until a threshold has no false hit on this set. The labels are yours to get right: the self-test checks that each pair names a real golden row and differs from its question, not that its label is true. Add two pairs against lk-32. One asks the same fact in other words. The other asks the clause's other fact, the kind of near miss a loose threshold would answer with 45 days.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two lines appended to evals/paraphrases.jsonl, then the offline self-test).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 44 pairs; the last two are against lk-32
    selftest OK - 44 pairs (25 same, 19 different) name real golden rows and differ from them; the curve counts hits and false hits per threshold; the recommendation is the lowest threshold with no false hit
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_generated_candidates(session):
    """Run Generated candidates at this checkpoint.

    make make-evalset asks Gemini for one question and answer per chunk of the quality-gated feed. The feed is rag_data.index_feed, joined to the chunks the worker mirrors into BigQuery, so a chunk the quality scan held back never becomes a question. Each pair is scanned by the one PII list, shared/pii.py, and dropped on any finding, never rewritten. What comes out is a candidate: a question with no figure it must contain, and the chunk's id as its only anchor. A golden row is a contract a person writes, and a generated question inherits the blind spots of the model that wrote it. So the file is golden_generated.jsonl, and the gate never reads it. What would the gate say if a candidate were merged as it is? The cell builds one for SEC-09 the way make_evalset.py writes it. Its chunk id is the worker's own: the tenant, the hash of the handbook's bytes, and #8, SEC-09's position after the preamble and seven clauses. Then the cell judges the reviewed version.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a candidate for SEC-09 as make-evalset writes one, judged in memory).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: gen-001  REFUSED
        gen-001: an answerable row with no must_contain accepts any answer at all
        gen-001: anchor 'acme:497809ffbaa6...#8' matches nothing in acme's corpus (slug? clause id? typo?)
    lk-32    accepted
    """
    import hashlib, sys; sys.path.insert(0, "evals")
    from run_eval import load_corpus, check_falsifiable, check_anchors
    corpus = load_corpus()
    sha = hashlib.sha256(open("evals/corpus/acme/hr_policy_2026.md", "rb").read()).hexdigest()
    candidate = {"id": "gen-001", "shape": "generated", "question": "How long can an account stay unused before it is disabled?",
                 "tenant": "acme", "must_contain": [], "must_retrieve": [f"acme:{sha}#8"], "answerable": True}
    reviewed = {**candidate, "id": "lk-32", "shape": "lookup", "must_contain": ["45 days"], "must_retrieve": ["SEC-09", "hr_policy_2026"]}
    for row in (candidate, reviewed):
        found = check_falsifiable([row], corpus) + check_anchors([row], corpus)
        print(f"{row['id']:8} {'REFUSED' if found else 'accepted'}")
        for f in found:
            print("   ", f.replace(sha, sha[:12] + "..."))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_34', step_01_paraphrase_pairs),
        ('source_39', step_02_generated_candidates),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
