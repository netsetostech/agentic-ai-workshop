"""Lesson 3.3: The failing rows, read with their passages, and where each fix lives

Do it: the failing rows

Run order inside this file:
1. Do it: the failing rows (source window 21)

Prerequisites: demo_05_the_live_eval_with_every_answerable_row_s_pool_read_again.
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


# Original CLI workflow for step_01_the_failing_rows.
COMMANDS_01 = """DOCUMIND_ID_TOKEN="$(tok "$API")" python - <<'PY'
import json, os, re, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "evals")
import run_eval as rv                    # the gate's own pieces: the golden rows, contains(), passages()

API, TOKEN = os.environ["API"], os.environ.get("DOCUMIND_ID_TOKEN")
EMAIL = os.environ.get("DOCUMIND_USER_EMAIL", "eval@documind.in")    # who eval-live asked as
report = json.load(open("evals/reports/lesson33.json", encoding="utf-8"))
golden = {r["id"]: r for r in rv.load_golden()}


def address(row, rec):
    \"\"\"Where the fix for one eval row lives, from its golden row and its report record: (place, reason).\"\"\"
    why = rec.get("why") or ""
    if rec.get("outcome") != "ok":
        return "the code", "no answer came back to judge: " + (why or rec.get("outcome", ""))
    if why.startswith("answer contained"):
        return ("the ledger" if row["shape"] == "version" else "tenancy"), why
    if not row["answerable"]:
        if rec.get("pass"):
            return "none", "refused, as it should"
        return "the prompt", "answered a question no document answers"
    flags = sorted({c.get("check") for c in rec.get("cites") or []} & {"elsewhere", "absent", "substituted"})
    if rec.get("pass"):
        return ("the prompt", "passed, but a quote is " + " and ".join(flags)) if flags else ("none", "passed")
    anchors = rec.get("anchors")
    if anchors is None:
        return "unread", "no pool was read for it"
    missing = [a for a, found in anchors.items() if not found]
    if missing:
        return "retrieval", "not in the pool: " + ", ".join(missing)
    if why.startswith("cited no "):
        return "media", why
    if "ledger" in why:
        return "the ledger", why
    if why == "refused" or why.startswith("answered without"):
        return "the prompt", why + ", every anchor in the pool"
    return "tenancy", why


def sentence(text, figure):
    \"\"\"The first sentence of a passage that holds the figure, matched as the gate matches it (contains()). A line break
    ends a sentence only when the next line does not go on in lower case: documind_tools._snippet's rule for pypdf text.\"\"\"
    parts = re.split(r"(?<=[.;])\\s+|\\n+(?=[^a-z\\s])", text)
    return next((" ".join(s.split())[:130] for s in parts if rv.contains(s, figure)), None)


records = report["records"]
failing = [r for r in records if not r["pass"]]
print(f"{len(records)} rows asked, {len(failing)} did not pass; a pool read for {sum(r.get('anchors') is not None for r in records)}")
places, fix = {}, {}
for rec in failing:
    row = golden[rec["id"]]
    place, reason = address(row, rec)
    places.setdefault(place, []).append(rec["id"])
    print(f"\\n{rec['id']:7} {row['shape']:9} {row['tenant']:7} {rec['why'] or rec['outcome']}")
    print(f"  asked   {row['question']}")
    if rec["outcome"] == "ok":
        said = " ".join((rec.get("answer") or "").split())
        print(f"  said    answerable {rec['answerable']}, {rec['confidence']}: {said[:150]!r}")
        for c in rec.get("cites") or []:
            where = c["source_uri"].rsplit("/", 1)[-1] + (f" p.{c['page']}" if c.get("page") else "")
            print(f"  cited   {where}, quote {c.get('check', 'not checked')}: {' '.join((c.get('quote') or '').split())[:90]!r}")
    if row["answerable"] and rec.get("anchors") is not None:
        print("  wants   " + ", ".join(row["must_contain"]) + " | anchors: "
              + ", ".join(f"{a} {'in the pool' if ok else 'NOT in the pool'}" for a, ok in rec["anchors"].items()))
        pool = rv.passages(API, row["question"], row["tenant"], EMAIL, TOKEN) or []
        for fig in row["must_contain"]:
            hit = next(((p, s) for p in pool if (s := sentence(p.get("text") or "", fig))), None)
            print(f"  passage {fig!r}: " + (f"[{hit[0]['n']}] {hit[0]['source_uri'].rsplit('/', 1)[-1]}: {hit[1]!r}"
                                            if hit else f"in none of the {len(pool)} passages"))
    print(f"  -> {place}: {reason}")
    if place == "the prompt" and row["answerable"]:
        kind = ("refused" if rec["why"] == "refused" else ("join" if row["shape"] == "join" else "lookup")
                if rec["why"].startswith("answered without [") else None)
        if kind and kind not in fix:
            fix[kind] = rec["id"]
print("\\nby address: " + "; ".join(f"{p} {len(ids)} ({', '.join(ids)})" for p, ids in places.items()))
quiet = [r["id"] for r in records if r["pass"] and address(golden[r["id"]], r)[0] == "the prompt"]
print("passing rows whose quotes the passage check flags: " + (", ".join(quiet) or "none"))
pairs = [f"{var}={fix[kind]}" for var, kind in (("FIX1", "refused"), ("FIX2", "join"), ("FIX3", "lookup")) if kind in fix]
print("to bench, one rule each: " + ("export " + " ".join(pairs) if pairs else "no row the prompt can fix"))
if len(pairs) < 3:
    print("  (fewer than three: step 9 finds more with the cheap model)")
PY

"""

def step_01_the_failing_rows(session):
    """Run Do it: the failing rows at this checkpoint.

    Do it: the failing rows

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the report, and each failing row's pool from /v1/passages: no model, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/failing_rows.txt]
    """
    session.shell(COMMANDS_01)
    import os, re
    log = sorted(session.attempt.glob("command_*.log"))[-1].read_text(encoding="utf-8")
    found = re.search(r"to bench, one rule each: export ((?:FIX[123]=\S+ ?)+)", log)
    for pair in (found[1].split() if found else []):
        key, _, value = pair.partition("=")
        os.environ[key] = value
    print("For step 7:", found[1] if found else "no row the prompt can fix")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_21', step_01_the_failing_rows),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
