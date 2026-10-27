"""Lesson 10.3: The 12 rows on your lane, with the calculator rule taken out

A model that follows the desk's prompt calls a calculator for every figure, so the check rarely fails, verify rarely retries, and the four ways tie. That would be true and would prove nothing about checking. To see the critic at work, these two runs take out the prompt's calculator rule, the three lines from "Work every figure out with a calculator" to "say which one is missing" in services/chat/desk_agent.py, in your clone only. The bench imports desk_agent from your clone in its own process, so the deployed chat service is not touched. Put the rule back as soon as the second run ends. Without it each call reads about 66 tokens fewer, by the script's count of four characters a token. The runs are step 7's without OFFLINE=1: 36 loop turns, then 12 verify runs, each run saved as one JSON line, both with the rule out so that the two arms face the same prompt. A progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in. Do it: side by side, at Rs 0 The same cell as step 7, on your lane's saves.

Run order inside this file:
1. Definition (source window 46)
2. Definition (source window 48)
3. Definition (source window 50)
4. Definition (source window 52)
5. Do it: side by side, at Rs 0 (source window 54)
6. Do it: read the records back, at Rs 0 (source window 56)

Prerequisites: demo_08_your_lane_one_verify_turn.
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


# Original CLI workflow for step_01_definition.
COMMANDS_01 = """sed -i '/Work every figure out with a calculator/,/say which one is missing/d' services/chat/desk_agent.py && git diff --stat

"""

def step_01_definition(session):
    """Run Definition at this checkpoint.

    A model that follows the desk's prompt calls a calculator for every figure, so the check rarely fails, verify rarely retries, and the four ways tie. That would be true and would prove nothing about checking. To see the critic at work, these two runs take out the prompt's calculator rule, the three lines from "Work every figure out with a calculator" to "say which one is missing" in services/chat/desk_agent.py, in your clone only. The bench imports desk_agent from your clone in its own process, so the deployed chat service is not touched. Put the rule back as soon as the second run ends. Without it each call reads about 66 tokens fewer, by the script's count of four characters a token. The runs are step 7's without OFFLINE=1: 36 loop turns, then 12 verify runs, each run saved as one JSON line, both with the rule out so that the two arms face the same prompt. A progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (delete the prompt's calculator rule, for the next two runs only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: services/chat/desk_agent.py | 3 ---
     1 file changed, 3 deletions(-)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_definition.
COMMANDS_02 = """make agent-eval PROJECT="$PROJECT" REGION="$REGION" PATTERNS=loop SLICE=calc,trap RUNS=3 SAVE="$HOME/plain.jsonl"

"""

def step_02_definition(session):
    """Run Definition at this checkpoint.

    A model that follows the desk's prompt calls a calculator for every figure, so the check rarely fails, verify rarely retries, and the four ways tie. That would be true and would prove nothing about checking. To see the critic at work, these two runs take out the prompt's calculator rule, the three lines from "Work every figure out with a calculator" to "say which one is missing" in services/chat/desk_agent.py, in your clone only. The bench imports desk_agent from your clone in its own process, so the deployed chat service is not touched. Put the rule back as soon as the second run ends. Without it each call reads about 66 tokens fewer, by the script's count of four characters a token. The runs are step 7's without OFFLINE=1: 36 loop turns, then 12 verify runs, each run saved as one JSON line, both with the rule out so that the two arms face the same prompt. A progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (36 live turns, about Rs 35.88 before thinking).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/eval_plain.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_definition.
COMMANDS_03 = """make agent-eval PROJECT="$PROJECT" REGION="$REGION" PATTERNS=verify SLICE=calc,trap SAVE="$HOME/verify.jsonl"

"""

def step_03_definition(session):
    """Run Definition at this checkpoint.

    A model that follows the desk's prompt calls a calculator for every figure, so the check rarely fails, verify rarely retries, and the four ways tie. That would be true and would prove nothing about checking. To see the critic at work, these two runs take out the prompt's calculator rule, the three lines from "Work every figure out with a calculator" to "say which one is missing" in services/chat/desk_agent.py, in your clone only. The bench imports desk_agent from your clone in its own process, so the deployed chat service is not touched. Put the rule back as soon as the second run ends. Without it each call reads about 66 tokens fewer, by the script's count of four characters a token. The runs are step 7's without OFFLINE=1: 36 loop turns, then 12 verify runs, each run saved as one JSON line, both with the rule out so that the two arms face the same prompt. A progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (12 live verify runs, about Rs 12.83 before thinking, more for each retry).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/eval_verify.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_definition.
COMMANDS_04 = """git checkout -q -- services/chat/desk_agent.py && git diff --stat && grep -c 'Work every figure out with a calculator' services/chat/desk_agent.py

"""

def step_04_definition(session):
    """Run Definition at this checkpoint.

    A model that follows the desk's prompt calls a calculator for every figure, so the check rarely fails, verify rarely retries, and the four ways tie. That would be true and would prove nothing about checking. To see the critic at work, these two runs take out the prompt's calculator rule, the three lines from "Work every figure out with a calculator" to "say which one is missing" in services/chat/desk_agent.py, in your clone only. The bench imports desk_agent from your clone in its own process, so the deployed chat service is not touched. Put the rule back as soon as the second run ends. Without it each call reads about 66 tokens fewer, by the script's count of four characters a token. The runs are step 7's without OFFLINE=1: 36 loop turns, then 12 verify runs, each run saved as one JSON line, both with the rule out so that the two arms face the same prompt. A progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (put the rule back, at once).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_side_by_side_at_rs_0.
COMMANDS_05 = """make agent-eval REPLAY="$HOME/plain.jsonl $HOME/verify.jsonl" BEST_OF=3 | sed -n '1p;/^  paired (correct)/,$p'

"""

def step_05_side_by_side_at_rs_0(session):
    """Run Do it: side by side, at Rs 0 at this checkpoint.

    Do it: side by side, at Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: your two saves side by side).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/eval_side.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

def step_06_read_the_records_back_at_rs_0(session):
    """Run Do it: read the records back, at Rs 0 at this checkpoint.

    The same cell as step 7, on your lane's saves.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a Python cell; Rs 0: your lane's saved runs read back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/records_read.txt]
    """
    import json, os, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = ["evals", "commands", "."]
    import agent_eval as ae          # the scorer, the figure check and best-of: the standard library and shared/ only
    
    SAVED = ["~/plain.jsonl", "~/verify.jsonl"]      # the files make agent-eval's SAVE= wrote
    rows = {r["id"]: r for r in ae.load_tasks()}
    runs = [json.loads(line) for name in SAVED for line in open(os.path.expanduser(name), encoding="utf-8") if line.strip()]
    word = {True: "pass", False: "fail"}
    for rid in dict.fromkeys(r["row"] for r in runs):
        loop = sorted((r for r in runs if r["row"] == rid and r["arm"]["pattern"] == "loop"), key=lambda r: r["run"])
        ver = next((r for r in runs if r["row"] == rid and r["arm"]["pattern"] == "verify"), None)
        print(rid)
        if loop:
            good = ["yes" if ae.passed(ae.score(rows[rid], r), "verified") else "no" for r in loop]
            print(f"  loop runs: check {'/'.join(word[ae.passes(r)] for r in loop)}, verified {'/'.join(good)}; "
                  f"best-of-{len(loop)} ships run {ae.best_of(loop, len(loop))['run'] + 1}")
        if ver:
            good = "yes" if ae.passed(ae.score(rows[rid], ver), "verified") else "no"
            print(f"  verify: check {' -> '.join(word[a['check']['passed']] for a in ver['attempts'])}; "
                  f"ships attempt {ver['shipped']}, verified {good}")
            for a in ver["attempts"][1:]:
                print(f"    the note before attempt {a['n']}: {a['note'] or '(none: the reflect call wrote nothing)'}")
                print(f"    figures it writes: {', '.join(a['note_figures']) or 'none'}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_46', step_01_definition),
        ('source_48', step_02_definition),
        ('source_50', step_03_definition),
        ('source_52', step_04_definition),
        ('source_54', step_05_side_by_side_at_rs_0),
        ('source_56', step_06_read_the_records_back_at_rs_0),
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
