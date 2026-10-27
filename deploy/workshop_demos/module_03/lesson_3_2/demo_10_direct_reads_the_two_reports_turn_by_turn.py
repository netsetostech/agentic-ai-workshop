"""Lesson 3.2: Direct reads: the two reports, turn by turn

Do it: the paired read, and the turns that flipped

Run order inside this file:
1. Do it: the paired read, and the turns that flipped (source window 50)

Prerequisites: demo_09_few_shot_measured_the_examples_taken_out_and_put_back_on_your_lane.
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


def step_01_the_paired_read_and_the_turns_that_flipped(session):
    """Run Do it: the paired read, and the turns that flipped at this checkpoint.

    Do it: the paired read, and the turns that flipped

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell; reads the two reports, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/exemplar_flips.txt]
    """
    import json, os, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, "evals")
    import paired
    import route_eval
    rows = {r["id"]: r for r in route_eval.load_rows()}
    
    
    def read(arm):
        """One arm's report: its examples, L1's route on each turn it was asked, and whether each row's route was right.
        
        Example: read(arm)
        """
        report = json.load(open(os.path.expanduser(f"~/exemplars_{arm}.json"), encoding="utf-8"))
        l1 = {d["id"]: (d["l1"] or {}).get("route") for d in report["decisions"]
              if d.get("l1") is not None or d.get("l1_error") is not None}
        return len(report["exemplars"]["examples"]), l1, {v["id"]: v["route_ok"] for v in report["rows"]}
    
    
    arms = {arm: read(arm) for arm in ("kit", "none")}
    l1_right = {arm: {i: got in rows[i]["acceptable_routes"] for i, got in arms[arm][1].items()} for arm in arms}
    for arm, (examples, l1, route) in arms.items():
        print(f"{arm:4} {examples} examples | L1 alone {route_eval.rate(sum(l1_right[arm].values()), len(l1))} "
              f"| top-1 route {route_eval.rate(sum(route.values()), len(route))}")
    for what, a, b in (("L1 alone", l1_right["kit"], l1_right["none"]), ("top-1 route", arms["kit"][2], arms["none"][2])):
        both, kit_only, none_only, neither = paired.pairs(a, b)
        diff, lo, hi = paired.newcombe(both, kit_only, none_only, neither)
        print(f"{what}, paired over {both + kit_only + none_only + neither} rows: both right {both}, kit only {kit_only}, "
              f"none only {none_only}, neither {neither}")
        print(f"   none - kit = {100 * diff:+.1f} points [{100 * lo:+.1f}, {100 * hi:+.1f}] (Newcombe), "
              f"exact McNemar p = {paired.mcnemar(kit_only, none_only):.3f}")
    kit_l1, none_l1 = arms["kit"][1], arms["none"][1]
    flips = sorted(i for i in set(kit_l1) & set(none_l1) if kit_l1[i] != none_l1[i])
    print(f"turns where L1's route changed with the examples out: {len(flips)}")
    for i in flips:
        r = rows[i]
        print(f"  {i:8} expects {r['expected_route']:12} kit {str(kit_l1[i]):12} none {str(none_l1[i]):12} {r['question'][:58]}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_50', step_01_the_paired_read_and_the_turns_that_flipped),
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
