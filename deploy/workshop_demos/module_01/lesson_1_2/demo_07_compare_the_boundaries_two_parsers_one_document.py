"""Lesson 1.2: Compare the boundaries: two parsers, one document

See it, page by page

Run order inside this file:
1. See it, page by page (source window 27)

Prerequisites: demo_06_chunk_by_window_an_act_becomes_page_windows.
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


def step_01_see_it_page_by_page(session):
    """Run See it, page by page at this checkpoint.

    See it, page by page

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: lane 67 windows, mirror 65 windows
    pages with a different number of windows: [(7, 3, 2), (23, 3, 2)]
    p2-0 on the lane: 2000 chars, hash 4c19e0b7a2d8
    p2-0 in the mirror: 2000 chars, hash 6a3f7e9c01b5
    lane text starts: 'THE CODE ON WAGES, 2019\\nCHAPTER I\\nPRELIMINARY\\n1. (1) This Code may be called ...'
    mirror text starts: 'THE CODE ON WAGES, 2019 CHAPTER I PRELIMINARY 1. (1) This Code may be called ...'
    """
    import os, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, ".")
    from collections import Counter
    from google.cloud import firestore
    from shared import documind_corpus as dc
    PROJECT = os.environ["PROJECT"]
    db = firestore.Client(project=PROJECT)
    NAME = "code_on_wages_2019"
    
    q = (db.collection("chunks").where("tenant_id", "==", "acme")
         .where("source_uri", "==", f"gs://{PROJECT}-uploads/acme/{NAME}.pdf").where("current", "==", True))
    lane = sorted(q.stream(), key=lambda c: int(c.id.rsplit("#", 1)[1]))
    lane_rows = [c.to_dict() for c in lane]
    text = open(f"evals/corpus/acme/{NAME}.md", encoding="utf-8").read()
    local = dc.chunk_document({"slug": NAME, "doc_type": "act", "source_uri": "gs://x", "text": text}, "acme")
    
    lp = Counter(r["page_start"] for r in lane_rows); mp = Counter(c["page_start"] for c in local)
    print(f"lane {len(lane_rows)} windows, mirror {len(local)} windows")
    diff = [p for p in sorted(set(lp) | set(mp)) if lp[p] != mp[p]]
    print("pages with a different number of windows:", [(p, lp[p], mp[p]) for p in diff])
    a = next(r for r in lane_rows if r["locator"] == "p2-0"); b = next(c for c in local if c["locator"] == "p2-0")
    print(f"p2-0 on the lane: {len(a['text'])} chars, hash {a['chunk_hash'][:12]}")
    print(f"p2-0 in the mirror: {len(b['text'])} chars, hash {b['chunk_hash'][:12]}")
    print("lane text starts:", repr(a["text"][:80]))
    print("mirror text starts:", repr(b["text"][:80]))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_27', step_01_see_it_page_by_page),
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
