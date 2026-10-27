"""Lesson 6.1: Change it: TOP_K, and which part of the bill moves

make context-sources prints its breakdown; with JSON=1 it prints the turn as one record instead, the command's --json. Write one record with TOP_K unset and one with TOP_K 3, then compare them source by source. Compare this one with step 7's langgraph output: Compare this one with step 7's langgraph output: And this one with step 7's desk output:

Run order inside this file:
1. Do it: offline, the two records side by side (source window 37)
2. Do it: offline, the two records side by side (source window 38)
3. Do it: on your lane, a chat brain and the Desk (source window 40)
4. Do it: on your lane, a chat brain and the Desk (source window 42)

Prerequisites: demo_07_five_brains_one_question_on_your_lane.
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


# Original CLI workflow for step_01_offline_the_two_records_side_by_side.
COMMANDS_01 = """make context-sources OFFLINE=1 BRAIN=langgraph JSON=1 > ~/cs_default.json
make context-sources OFFLINE=1 BRAIN=langgraph TOP_K=3 JSON=1 > ~/cs_top3.json

"""

def step_01_offline_the_two_records_side_by_side(session):
    """Run Do it: offline, the two records side by side at this checkpoint.

    make context-sources prints its breakdown; with JSON=1 it prints the turn as one record instead, the command's --json. Write one record with TOP_K unset and one with TOP_K 3, then compare them source by source.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two offline turns, written as records: Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_offline_the_two_records_side_by_side(session):
    """Run Do it: offline, the two records side by side at this checkpoint.

    make context-sources prints its breakdown; with JSON=1 it prints the turn as one record instead, the command's --json. Write one record with TOP_K unset and one with TOP_K 3, then compare them source by source.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the two records; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: TOP_K unset   TOP_K=3
    system prompt                212       212
    tool declarations            480       480
    thread so far                  0         0
    question                      30        30
    the model's calls             21        21
    tool results                 761       435   moved
    rag-api, inside            1,957     1,095   moved: 5 chunks packed, then 3
    the model calls, Rs       0.2370    0.1955
    rag-api, Rs               0.2648    0.1549
    the turn, Rs              0.5018    0.3504
    """
    import json, os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    NAMES = {"system": "system prompt", "tools": "tool declarations", "thread": "thread so far", "question": "question",
             "calls": "the model's calls", "results": "tool results"}
    
    
    def load(name):
        """One record, as context_sources.py --json printed it.
        
        Example: load('cs_default')
        """
        with open(os.path.expanduser(f"~/{name}.json"), encoding="utf-8") as f:
            return json.load(f)
    
    
    def rag(rec):
        """rag-api's own calls inside the turn's searches: their tokens in, and the chunks packed when the record knows.
        
        Example: rag(a)
        """
        calls = [s["rag"] for s in rec["searches"] if s.get("rag")]
        packed = [r["prompt"]["packed"] for r in calls if r.get("prompt")]
        return sum(int(r["tokens_in"] or 0) for r in calls), (sum(packed) if packed else None)
    
    
    a, b = load("cs_default"), load("cs_top3")
    print(f"{'':20}{'TOP_K unset':>12}{'TOP_K=3':>10}")
    for key, name in NAMES.items():
        x, y = a["totals"]["tokens"][key], b["totals"]["tokens"][key]
        print(f"{name:20}{x:>12,}{y:>10,}" + ("   moved" if x != y else ""))
    (ra, ka), (rb, kb) = rag(a), rag(b)
    print(f"{'rag-api, inside':20}{ra:>12,}{rb:>10,}   moved" + (f": {ka} chunks packed, then {kb}" if ka is not None else ""))
    print(f"{'the model calls, Rs':20}{a['totals']['model_inr']:>12.4f}{b['totals']['model_inr']:>10.4f}")
    print(f"{'rag-api, Rs':20}{a['totals']['rag_inr']:>12.4f}{b['totals']['rag_inr']:>10.4f}")
    print(f"{'the turn, Rs':20}{a['totals']['turn_inr']:>12.4f}{b['totals']['turn_inr']:>10.4f}")

# Original CLI workflow for step_03_on_your_lane_a_chat_brain_and_the_desk.
COMMANDS_03 = """make context-sources PROJECT=$PROJECT BRAIN=langgraph TOP_K=3

"""

def step_03_on_your_lane_a_chat_brain_and_the_desk(session):
    """Run Do it: on your lane, a chat brain and the Desk at this checkpoint.

    Compare this one with step 7's langgraph output:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one real turn, every search sent top_k 3).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/lane_langgraph_topk3.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_on_your_lane_a_chat_brain_and_the_desk.
COMMANDS_04 = """make context-sources PROJECT=$PROJECT BRAIN=desk TOP_K=3

"""

def step_04_on_your_lane_a_chat_brain_and_the_desk(session):
    """Run Do it: on your lane, a chat brain and the Desk at this checkpoint.

    Compare this one with step 7's langgraph output: And this one with step 7's desk output:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one real turn on the statute desk, top_k 3).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/lane_desk_topk3.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_37', step_01_offline_the_two_records_side_by_side),
        ('source_38', step_02_offline_the_two_records_side_by_side),
        ('source_40', step_03_on_your_lane_a_chat_brain_and_the_desk),
        ('source_42', step_04_on_your_lane_a_chat_brain_and_the_desk),
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
