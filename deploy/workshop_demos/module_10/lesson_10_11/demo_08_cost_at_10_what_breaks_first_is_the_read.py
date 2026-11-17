"""Lesson 10.11: Cost at 10×: what breaks first is the read

Do it: the limits from the kit's files

Run order inside this file:
1. Do it: the limits from the kit's files (source window 59)

Prerequisites: demo_07_cost_an_incident_priced_and_a_model_priced_at_three_scales.
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


def step_01_the_limits_from_the_kit_s_files(session):
    """Run Do it: the limits from the kit's files at this checkpoint.

    Do it: the limits from the kit's files

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the read: the newest 2000 lines, 1000 turns at 2 lines a turn | a failure: 2 bad lines and a share | the window: 1h
        1,000 turns a month:     1.4 turns an hour | the read covers 60.0 of its 60 minutes | under the router's 100-turn floor
       10,000 turns a month:    13.7 turns an hour | the read covers 60.0 of its 60 minutes | under the router's 100-turn floor
      100,000 turns a month:   137.0 turns an hour | the read covers 60.0 of its 60 minutes | reaches the router's 100-turn floor
    1,000,000 turns a month:  1369.9 turns an hour | the read covers 43.8 of its 60 minutes | reaches the router's 100-turn floor
    the read stops covering an average hour at 730,000 turns a month; the router's floor
    """
    import importlib.util, re, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    spec = importlib.util.spec_from_file_location("remediate", "commands/remediate.py")
    rm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rm)
    desk = open("terraform/desk_alerts.tf", encoding="utf-8").read()
    hour = int(re.search(r'desk_router_promql\}\[1h\]\)\) >= (\d+)"', desk).group(1))     # a router share policy's floor
    gate = int(re.search(r'desk_gate_check_promql\}\[30m\]\)\) >= (\d+)"', desk).group(1))  # the gate check's floor
    per_turn = 2                                                  # a request line and a chat row, at the defaults
    print(f"the read: the newest {rm.LIMIT} lines, {rm.LIMIT // per_turn} turns at {per_turn} lines a turn | a failure: "
          f"{rm.MIN_BAD} bad lines and a share | the window: {rm.build_parser().get_default('since')}")
    for turns in (1_000, 10_000, 100_000, 1_000_000):
        hourly = turns / 730                                      # an average hour of the price pages' 730-hour month
        covered = min(60.0, 60 * rm.LIMIT / (hourly * per_turn))
        print(f"{turns:>9,} turns a month: {hourly:7.1f} turns an hour | the read covers {covered:4.1f} of its 60 minutes | "
              f"{'reaches' if hourly >= hour else 'under'} the router's {hour}-turn floor")
    print(f"the read stops covering an average hour at {rm.LIMIT // per_turn * 730:,} turns a month; the router's floor is "
          f"reached at {hour * 730:,}, and the gate check's {gate} in 30 minutes at {gate * 2 * 730:,} checks a month")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_59', step_01_the_limits_from_the_kit_s_files),
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
