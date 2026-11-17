"""Lesson 4.9: The doors by hand: one attack in the UI, two at the API

The cell sends two requests to /v1/query: atk-13's body, which names tenant_id in its filters, as the member; and atk-15's, the outsider's token with x-user-email naming the member. Neither reaches retrieval, the guard or the model, so neither costs anything.

Run order inside this file:
1. Do it: two structural doors (source window 40)

Prerequisites: demo_07_the_attack_set_offline_15_rows_6_controls_and_the_vacuity_check.
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


# Original CLI workflow for step_01_two_structural_doors.
COMMANDS_01 = """TOKEN="$(tok "$API")" OUTSIDER="$(otok)" python - <<'PY'
import json, os, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
API, MEMBER = os.environ["API"], f"documind-ui-sa@{os.environ['PROJECT']}.iam.gserviceaccount.com"


def post(body, token, email=None):
    \"\"\"POST one body to /v1/query with this token, and this x-user-email if given; return the status and the detail.\"\"\"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    if email:
        headers["x-user-email"] = email
    req = urllib.request.Request(API + "/v1/query", data=json.dumps(body).encode(), method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read()).get("answer", "")[:70]
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}").get("detail")


filtered = {"query": "What termination notice does the agreement set?", "tenant_id": "acme", "top_k": 6,
            "filters": {"tenant_id": "globex"}}
print("atk-13, the member, a body filter naming globex:", *post(filtered, os.environ["TOKEN"]))
plain = {"query": "What is the notice period for a confirmed E3?", "tenant_id": "acme", "top_k": 6}
print("atk-15, the outsider's token, the member's email:", *post(plain, os.environ["OUTSIDER"], MEMBER))
PY

"""

def step_01_two_structural_doors(session):
    """Run Do it: two structural doors at this checkpoint.

    The cell sends two requests to /v1/query: atk-13's body, which names tenant_id in its filters, as the member; and atk-15's, the outsider's token with x-user-email naming the member. Neither reaches retrieval, the guard or the model, so neither costs anything.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two requests, both refused before any retrieval).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: atk-13, the member, a body filter naming globex: 400 unknown filter key(s) tenant_id; allowed: doc_type, kind
    atk-15, the outsider's token, the member's email: 403 not a member of this tenant
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_40', step_01_two_structural_doors),
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
