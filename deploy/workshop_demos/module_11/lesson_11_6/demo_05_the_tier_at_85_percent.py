"""Lesson 11.6: The tier at 85 percent

Do it: routing on, the month as it is Do it: the same three at 85 percent Do it: undo the candidate

Run order inside this file:
1. Do it: routing on, the month as it is (source window 13)
2. Do it: the same three at 85 percent (source window 15)
3. Do it: undo the candidate (source window 17)

Prerequisites: demo_04_the_month_so_far.
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


# Original CLI workflow for step_01_routing_on_the_month_as_it_is.
COMMANDS_01 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --update-env-vars ROUTING=on --quiet
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"
ask133() {   # ask133 URL: three acme questions (a lookup, an explanation, a worked sum) as documind-ui-sa - the model that answered each
URL="$1" python - <<'PY'
import json, os, subprocess, urllib.request
P, API, URL = os.environ["PROJECT"], os.environ["API"], os.environ["URL"]
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                      f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com"],
                     capture_output=True, text=True, check=True).stdout.strip()
for q in ['What is the notice period for a confirmed E3?', 'Explain what happens when a trip costs more than the per-trip travel cap.', 'Work out, step by step, the total reimbursed for three domestic trips costing Rs 38,000, Rs 45,000 and Rs 22,000.']:
    body = json.dumps({"query": q, "tenant_id": "acme"}).encode()
    req = urllib.request.Request(URL + "/v1/query", data=body, headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    a = json.load(urllib.request.urlopen(req, timeout=180))
    print(f"  {a['model']:24} {q}")
    print(f"  {'':24} {a['answer'][:132] + ('...' if len(a['answer']) > 132 else '')}")
PY
}
ask133 "$CAND"

"""

def step_01_routing_on_the_month_as_it_is(session):
    """Run Do it: routing on, the month as it is at this checkpoint.

    Do it: routing on, the month as it is

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a candidate revision, no traffic, ROUTING on; three questions).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: gemini-3.1-flash-lite    What is the notice period for a confirmed E3?
                               A confirmed employee at grade E3 or above serves a notice period of 60 days [1].
      gemini-3.6-flash         Explain what happens when a trip costs more than the per-trip travel cap.
                               Travel is capped at Rs 40,000 per trip [1]; a trip above the cap needs the function head's written approval before travel [1].
      gemini-3.1-pro-preview   Work out, step by step, the total reimbursed for three domestic trips costing Rs 38,000, Rs 45,000 and Rs 22,000.
                               Each trip is reimbursed up to the cap of Rs 40,000 [1]: Rs 38,000 + Rs 40,000 + Rs 22,000 = Rs 1,0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_same_three_at_85_percent.
COMMANDS_02 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --update-env-vars SPEND_PCT=85 --quiet     # the replay: the breaker reads 85, the counter is not touched
ask133 "$CAND"

"""

def step_02_the_same_three_at_85_percent(session):
    """Run Do it: the same three at 85 percent at this checkpoint.

    Do it: the same three at 85 percent

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same candidate at 85 percent; the same three questions).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: gemini-3.1-flash-lite    What is the notice period for a confirmed E3?
                               A confirmed employee at grade E3 or above serves a notice period of 60 days [1].
      gemini-3.1-flash-lite    Explain what happens when a trip costs more than the per-trip travel cap.
                               Travel is capped at Rs 40,000 per trip [1]; a trip above the cap needs the function head's written approval before travel [1].
      gemini-3.6-flash         Work out, step by step, the total reimbursed for three domestic trips costing Rs 38,000, Rs 45,000 and Rs 22,000.
                               Each trip is reimbursed up to the cap of Rs 40,000 [1]: Rs 38,000 + Rs 40,000 + Rs 22,000 = Rs 1,0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_undo_the_candidate.
COMMANDS_03 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --update-env-vars ROUTING=off --remove-env-vars SPEND_PCT --quiet     # env vars merge: take them back off the template
gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate --quiet
gcloud run services describe documind-api --region "$REGION" --project "$PROJECT" --format='value(status.traffic[].percent,status.traffic[].revisionName)'

"""

def step_03_undo_the_candidate(session):
    """Run Do it: undo the candidate at this checkpoint.

    Do it: undo the candidate

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the variables off the template, the tag dropped).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 100	documind-api-00031-kez
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_routing_on_the_month_as_it_is),
        ('source_15', step_02_the_same_three_at_85_percent),
        ('source_17', step_03_undo_the_candidate),
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
