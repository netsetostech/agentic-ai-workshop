"""Lesson 4.1: Ask the two rows once: the live half's own functions, and the outsider's 403

Do it

Run order inside this file:
1. Do it (source window 31)

Prerequisites: demo_05_an_isolation_row_the_marker_that_cannot_work_the_list_it_must_join_and_the_gate.
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


# Original CLI workflow for step_01_ask_the_two_rows_once_the_live_half_s_own.
COMMANDS_01 = """TOKEN="$(tok "$API")" OUTSIDER="$(otok)" python - <<'PY'
import os, sys; sys.path.insert(0, "evals")
from run_eval import ask, contains, load_golden
api, rows = os.environ["API"], {r["id"]: r for r in load_golden()}
for rid in ("lk-32", "iso-11"):
    r = rows[rid]
    status, body, ms = ask(api, r["question"], r["tenant"], "eval@documind.in", os.environ["TOKEN"])
    answer, cites = body.get("answer", ""), body.get("citations") or []
    print(f"{rid} as {r['tenant']}: HTTP {status}, answerable {body.get('answerable')}, {len(cites)} citation(s), {ms} ms")
    print("   " + answer[:120])
    for w in r["must_contain"]:
        print(f"   must_contain {w!r}: {'found' if contains(answer, w) else 'MISSING'}")
    for w in r.get("must_not_contain", []):
        print(f"   must_not_contain {w!r}: {'LEAKED' if contains(answer, w) else 'absent'}")
    print("   cites " + ", ".join(sorted({c["source_uri"].split("/", 3)[-1] for c in cites})))
status, _, _ = ask(api, rows["iso-11"]["question"], "zeta", "outsider@not-a-tenant.invalid", os.environ["OUTSIDER"])
print(f"iso-11 asked by documind-outsider-sa: HTTP {status} (the isolation gate requires 403)")
PY

"""

def step_01_ask_the_two_rows_once_the_live_half_s_own(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (three requests to the API; under a rupee).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: lk-32 as acme: HTTP 200, answerable True, 1 citation(s), 2410 ms
       An account unused for 45 days is disabled automatically and must be re-approved to restore it [1].
       must_contain '45 days': found
       cites acme/hr_policy_2026.md
    iso-11 as zeta: HTTP 200, answerable True, 1 citation(s), 2230 ms
       Earned leave is encashed on exit at basic pay, capped at 20 days [1].
       must_contain '20 days': found
       must_not_contain 'capped at 45 days': absent
       cites zeta/hr_policy_zeta_2026.md
    iso-11 asked by documind-outsider-sa: HTTP 403 (the isolation gate requires 403)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_31', step_01_ask_the_two_rows_once_the_live_half_s_own),
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
