"""Lesson 11.5: Four questions, four rows

Do it

Run order inside this file:
1. Do it (source window 11)

Prerequisites: demo_03_the_readers_as_the_kit_writes_them_down.
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


# Original CLI workflow for step_01_four_questions_four_rows.
COMMANDS_01 = """python - <<'PY'
import json, os, subprocess, urllib.request
P, API = os.environ["PROJECT"], os.environ["API"]
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                      f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com"],
                     capture_output=True, text=True, check=True).stdout.strip()
ASKS = [('acme', 'What is the per-trip cap on domestic travel reimbursement?'), ('acme', 'What is the notice period for a confirmed E3?'), ('acme', "What is ACME's sabbatical policy?"), ('zeta', 'What is the per-trip cap on travel reimbursement?')]
for tenant, question in ASKS:
    body = json.dumps({"query": question, "tenant_id": tenant}).encode()
    req = urllib.request.Request(API + "/v1/query", data=body, headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    a = json.load(urllib.request.urlopen(req, timeout=120))
    print(f"  {tenant:5} {'answered' if a['answerable'] else 'refused':8} {a['tokens_in']:>5} in {a['tokens_out']:>3} out  "
          f"cost_usd {a['cost_usd']}  {question}")
PY
sleep 20      # Cloud Logging needs a moment to show the rows
make usage PROJECT="$PROJECT" HOURS=1

"""

def step_01_four_questions_four_rows(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (four questions, then make usage).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme  answered   839 in  46 out  cost_usd None  What is the per-trip cap on domestic travel reimbursement?
      acme  answered   399 in  44 out  cost_usd None  What is the notice period for a confirmed E3?
      acme  refused    915 in  39 out  cost_usd None  What is ACME's sabbatical policy?
      zeta  answered   843 in  46 out  cost_usd None  What is the per-trip cap on travel reimbursement?
    python evals/usage_rows.py --project documind-ai-YOUR-ID --hours ${HOURS:-24}
    4 answers from documind-api in the last 1 h; USD_INR=85

    by tenant
    tenant                 answers    tok_in  tok_out       USD       INR  p95 ms  unans
    -----------------------------------------------------------------------------------
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_11', step_01_four_questions_four_rows),
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
