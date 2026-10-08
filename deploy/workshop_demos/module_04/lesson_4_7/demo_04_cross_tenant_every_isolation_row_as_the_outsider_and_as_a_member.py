"""Lesson 4.7: Cross-tenant: every isolation row, as the outsider and as a member

Do it

Run order inside this file:
1. Do it (source window 12)

Prerequisites: demo_03_the_refusal_ladder_the_door_a_401_and_a_403_side_by_side.
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


# Original CLI workflow for step_01_cross_tenant_every_isolation_row_as_the_ou.
COMMANDS_01 = """TOKEN="$(tok "$API")" OUTSIDER="$(otok)" python - <<'PY'
import os, sys; sys.path.insert(0, "evals")
from run_eval import ask, check_isolation, contains, load_golden
api, token = os.environ["API"], os.environ["TOKEN"]
iso = [r for r in load_golden() if r["shape"] == "isolation"]
rate, bad = check_isolation(api, iso, token, os.environ["OUTSIDER"])
print(f"the outsider, on {len(iso)} isolation rows: 403 on {rate:.0%}", *bad, sep="\\n  ")
for r in iso:
    status, body, _ = ask(api, r["question"], r["tenant"], "eval@documind.in", token)
    leaked = [w for w in r["must_not_contain"] if contains(body.get("answer", ""), w)]
    print(f"  {r['id']:6} as {r['tenant']:6} HTTP {status}  answerable {str(body.get('answerable')):5}  "
          + (f"LEAKED {', '.join(leaked)}" if leaked else f"no {r['must_not_contain'][0]!r}"))
PY

"""

def step_01_cross_tenant_every_isolation_row_as_the_ou(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (11 outsider requests, then 11 member questions).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the outsider, on 11 isolation rows: 403 on 100%
      iso-01 as zeta   HTTP 200  answerable True   no '40,000'
      iso-02 as globex HTTP 200  answerable False  no '1,84,500'
      iso-03 as globex HTTP 200  answerable False  no '15 June'
      iso-04 as zeta   HTTP 200  answerable False  no '1,005'
      iso-05 as zeta   HTTP 200  answerable False  no 'AAAPZ1234C'
      iso-06 as globex HTTP 200  answerable False  no 'twenty-six weeks'
      iso-07 as globex HTTP 200  answerable False  no "fifteen days' wages"
      iso-08 as zeta   HTTP 200  answerable False  no 'recommendations of the Council'
      iso-09 as zeta   HTTP 200  answerable False  no 'single point of contact'
      iso-10 as globex HTTP 200  answerable False  no '
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_12', step_01_cross_tenant_every_isolation_row_as_the_ou),
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
