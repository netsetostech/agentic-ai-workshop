"""Lesson 3.1: Change it: send a temperature of 2.0, and read what went out

generator.py sends no temperature; the bench can. --temperature 2.0 adds a second arm, edit: the kit's prompt, the kit's level and a temperature of 2.0 on every call. The kit arm runs beside it, interleaved, so the two share the lane's conditions, and both print one prompt sha256, because the text is the same: the only difference the run can show is the knob. Without --levels the bench runs at LOW, so this run's kit arm is a third sample of the request steps 6 and 7 already asked. The table cannot prove that 2.0 was sent: it prints each arm's settings, not its requests. The recorder's log can. Every call in the report carries its config as sent (the thinking level, the temperature, None when none was sent, and the cap) and what came back.

Run order inside this file:
1. Definition (source window 30)
2. Read what went out (source window 32)

Prerequisites: demo_07_make_bench_five_runs_at_low_and_five_at_high.
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
COMMANDS_01 = """make bench PROJECT="$PROJECT" REGION="$REGION" BENCH_ARGS="--rows jn-03 --runs 5 --temperature 2.0 --report evals/reports/bench-temperature.json"

"""

def step_01_definition(session):
    """Run Definition at this checkpoint.

    generator.py sends no temperature; the bench can. --temperature 2.0 adds a second arm, edit: the kit's prompt, the kit's level and a temperature of 2.0 on every call. The kit arm runs beside it, interleaved, so the two share the lane's conditions, and both print one prompt sha256, because the text is the same: the only difference the run can show is the knob. Without --levels the bench runs at LOW, so this run's kit arm is a third sample of the request steps 6 and 7 already asked.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (ten answers at LOW, five with a temperature of 2.0: about Rs 2.02 of input, at most Rs 15.08 at the cap).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/bench_temperature.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_read_what_went_out(session):
    """Run Read what went out at this checkpoint.

    The table cannot prove that 2.0 was sent: it prints each arm's settings, not its requests. The recorder's log can. Every call in the report carries its config as sent (the thinking level, the temperature, None when none was sent, and the cap) and what came back.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the report step 8's run wrote).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/bench_temperature.json]
    """
    import json
    rep = json.load(open("evals/reports/bench-temperature.json", encoding="utf-8"))
    print(f"{rep['model']} | levels {', '.join(rep['levels'])} | {rep['runs']} runs | arms: "
          + "; ".join(f"{a['name']} with temperature {a['temperature']}, prompt sha256 {a['prompt_sha256'][:12]}" for a in rep["arms"]))
    for a in rep["answers"]:
        for c in a["calls"]:
            print(f"  {a['arm']:4} run {a['run']} | sent thinking_level {c['thinking_level']}, temperature {c['temperature']}, "
                  f"max_output_tokens {c['max_output_tokens']} | thought {c.get('thought', 0):>5} visible {c.get('visible', 0):>4} "
                  f"| {c.get('ms', 0):>6} ms | {c.get('finish') or c.get('error')} | {'pass' if a['pass'] else 'FAIL'}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_30', step_01_definition),
        ('source_32', step_02_read_what_went_out),
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
