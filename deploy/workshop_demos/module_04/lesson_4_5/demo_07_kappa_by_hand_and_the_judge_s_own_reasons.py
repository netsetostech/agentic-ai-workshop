"""Lesson 4.5: Kappa by hand, and the judge's own reasons

Two standard-library cells over the files themselves, with no kit function between you and the count. The first cell reads your sheet and the author's with Python's csv module, counts p_o and p_e by hand, and checks the result against the kit's cohen_kappa(). It is this lesson's arithmetic in a screenful, and it runs anywhere Python does. The first cell reads your sheet and the author's with Python's csv module, counts p_o and p_e by hand, and checks the result against the kit's cohen_kappa(). It is this lesson's arithmetic in a screenful, and it runs anywhere Python does. The second reads the judge's ratings file directly and prints each row where the judge and you disagree, with the judge's score and its own explanation. It is lesson 4.2's advice made concrete: where they disagree, read the row. It skips judge_agree.py's row_sha check, because both files come from the same frozen set.

Run order inside this file:
1. Kappa by hand, and the judge's own reasons (source window 40)
2. Kappa by hand, and the judge's own reasons (source window 42)

Prerequisites: demo_06_your_lane_s_judge_on_the_frozen_rows_the_ratings_step_5_reads_until_the_author_s.
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


def step_01_kappa_by_hand_and_the_judge_s_own_reasons(session):
    """Run Kappa by hand, and the judge's own reasons at this checkpoint.

    Two standard-library cells over the files themselves, with no kit function between you and the count. The first cell reads your sheet and the author's with Python's csv module, counts p_o and p_e by hand, and checks the result against the kit's cohen_kappa(). It is this lesson's arithmetic in a screenful, and it runs anywhere Python does.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a Python cell; Rs 0: it reads two sheets).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/judge_labels.L1.csv]
    """
    import collections, csv, io, os, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, "evals")
    from agreement import cohen_kappa            # the kit's, only to check the count by hand below
    
    MINE, THEIRS = "evals/reports/judge_labels.csv", "evals/judge_labels.L1.csv"
    if not os.path.exists(THEIRS):                # no author's sheet in the kit yet: your colleague's (step 4)
        THEIRS = "evals/reports/judge_labels.peer.csv"
    
    
    def sheet(path):
        """{id: row} of a filled label sheet: UTF-8 as make label-sheet writes it, or a spreadsheet's cp1252.
        
        Example: sheet(MINE)
        """
        raw = open(path, "rb").read()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("cp1252", errors="replace")
        return {r["id"].strip(): r for r in csv.DictReader(io.StringIO(text, newline=""))}
    
    
    def by_hand(a, b):
        """Raw agreement, chance agreement and Cohen's kappa of two readers' labels, from counts alone.
        
        Example: by_hand(a, b)
        """
        n = len(a)
        p_o = sum(x == y for x, y in zip(a, b)) / n
        ca, cb = collections.Counter(a), collections.Counter(b)
        p_e = sum(ca[k] * cb[k] for k in ca) / (n * n)
        return p_o, p_e, None if p_e == 1 else (p_o - p_e) / (1 - p_e)
    
    
    mine, theirs = sheet(MINE), sheet(THEIRS)
    ids = sorted(mine)
    me, them = mine[ids[0]]["reader"].strip(), theirs[ids[0]]["reader"].strip()
    print(f"{len(ids)} rows: {me} ({MINE}) against {them} ({THEIRS})")
    for rubric in ("groundedness", "answers_the_question"):
        a = [mine[i][rubric].strip().lower() for i in ids]
        b = [theirs[i][rubric].strip().lower() for i in ids]
        p_o, p_e, k = by_hand(a, b)
        kit = cohen_kappa(a, b)
        same = k == kit if k is None or kit is None else abs(k - kit) < 1e-12
        print(f"  {rubric}: {me} says yes {a.count('yes')} times, {them} {b.count('yes')}; p_o {p_o:.2f}, p_e {p_e:.2f}, "
              f"kappa {'undefined' if k is None else f'{k:.2f}'} (agreement.cohen_kappa: {'the same' if same else 'DIFFERENT'})")
        split = [f"{i} ({me} {x}, {them} {y})" for i, x, y in zip(ids, a, b) if x != y]
        print(f"    split on {len(split)}: {', '.join(split) or 'no row'}")

def step_02_kappa_by_hand_and_the_judge_s_own_reasons(session):
    """Run Kappa by hand, and the judge's own reasons at this checkpoint.

    The first cell reads your sheet and the author's with Python's csv module, counts p_o and p_e by hand, and checks the result against the kit's cohen_kappa(). It is this lesson's arithmetic in a screenful, and it runs anywhere Python does. The second reads the judge's ratings file directly and prints each row where the judge and you disagree, with the judge's score and its own explanation. It is lesson 4.2's advice made concrete: where they disagree, read the row. It skips judge_agree.py's row_sha check, because both files come from the same frozen set.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a Python cell; Rs 0: it reads your sheet and the judge's ratings).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/judge_set.ratings.jsonl]
    """
    import csv, io, json, os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    MINE, RATINGS, CUT = "evals/reports/judge_labels.csv", "evals/judge_set.ratings.jsonl", 4
    if not os.path.exists(RATINGS):               # no author's ratings in the kit yet: your lane's (step 6)
        RATINGS = "evals/reports/judge_set.ratings.jsonl"
    SECOND = ("fulfillment", "instruction_following", "question_answering_quality")   # judge.py's names, in its order
    
    
    def sheet(path):
        """{id: row} of a filled label sheet: UTF-8 as make label-sheet writes it, or a spreadsheet's cp1252.
        
        Example: sheet(MINE)
        """
        raw = open(path, "rb").read()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("cp1252", errors="replace")
        return {r["id"].strip(): r for r in csv.DictReader(io.StringIO(text, newline=""))}
    
    
    mine = sheet(MINE)
    rated = [json.loads(line) for line in open(RATINGS, encoding="utf-8") if line.strip()]
    second = next(m for m in SECOND if any(m in x["ratings"] for x in rated))
    me = next(iter(mine.values()))["reader"].strip()
    for rubric, metric in (("groundedness", "groundedness"), ("answers_the_question", second)):
        print(f"{rubric}: the judge's {metric}, a pass at {1 if metric == 'groundedness' else CUT} or more")
        for x in rated:
            i, got = x["id"], x["ratings"].get(metric) or {}
            if i not in mine or got.get("score") is None:
                continue
            judge = got["score"] >= (1 if metric == "groundedness" else CUT)
            person = mine[i][rubric].strip().lower() == "yes"
            if judge != person:
                why = " ".join((got.get("explanation") or "").split())
                print(f"  {i}: {me} {'pass' if person else 'fail'}, the judge {got['score']:g}: {why[:140]}{'...' if len(why) > 140 else ''}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_40', step_01_kappa_by_hand_and_the_judge_s_own_reasons),
        ('source_42', step_02_kappa_by_hand_and_the_judge_s_own_reasons),
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
