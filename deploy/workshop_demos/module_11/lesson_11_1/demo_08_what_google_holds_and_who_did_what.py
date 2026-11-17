"""Lesson 11.1: What Google holds, and who did what

Do it: the trust and the binding, from IAM's REST API Do it: the audit trail of step 6's run Do it: zero user-managed keys

Run order inside this file:
1. Do it: the trust and the binding, from IAM's REST API (source window 33)
2. Do it: the audit trail of step 6's run (source window 35)
3. Do it: zero user-managed keys (source window 38)

Prerequisites: demo_07_a_branch_dispatch_refused_at_the_auth_step.
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


def step_01_the_trust_and_the_binding_from_iam_s_rest(session):
    """Run Do it: the trust and the binding, from IAM's REST API at this checkpoint.

    Do it: the trust and the binding, from IAM's REST API

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (three IAM REST reads; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/iam_rest.txt]
    """
    import os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    
    P = os.environ["PROJECT"]
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    iam = AuthorizedSession(creds.with_quota_project(P) if hasattr(creds, "with_quota_project") else creds)
    IAM, CICD = "https://iam.googleapis.com/v1", f"sa-documind-cicd@{P}.iam.gserviceaccount.com"
    
    
    def call(method, path, **kw):
        """One IAM REST call, as JSON; a failure says which call and why.
        
        Example: call('GET', f'projects/{P}/locations/global/workloadIdentityPools/documind-github/providers/github-oidc')
        """
        r = iam.request(method, f"{IAM}/{path}", timeout=30, **kw)
        if r.status_code != 200:
            raise SystemExit(f"{method} {path}: HTTP {r.status_code} {r.text[:200]}")
        return r.json()
    
    
    prov = call("GET", f"projects/{P}/locations/global/workloadIdentityPools/documind-github/providers/github-oidc")
    print("provider", prov["name"].split("/workloadIdentityPools/")[1], "|", prov.get("state"), "| issuer", prov["oidc"]["issuerUri"])
    for clause in prov["attributeCondition"].split("&&"):
        print("  condition ", clause.strip())
    for attr, expr in sorted(prov["attributeMapping"].items()):
        print("  mapping   ", attr, "=", expr)
    for b in call("POST", f"projects/{P}/serviceAccounts/{CICD}:getIamPolicy", json={}).get("bindings", []):
        for m in b["members"]:
            print("sa-documind-cicd:", b["role"], "<-", m.split("/workloadIdentityPools/")[-1] if m.startswith("principalSet:") else m)
    keys = call("GET", f"projects/{P}/serviceAccounts/{CICD}/keys", params={"keyTypes": "USER_MANAGED"})
    print("user-managed keys on sa-documind-cicd:", len(keys.get("keys", [])))

def step_02_the_audit_trail_of_step_6_s_run(session):
    """Run Do it: the audit trail of step 6's run at this checkpoint.

    Do it: the audit trail of step 6's run

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one Cloud Logging read; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/audit.txt]
    """
    import datetime as dt, os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    
    P = os.environ["PROJECT"]
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    logs = AuthorizedSession(creds.with_quota_project(P) if hasattr(creds, "with_quota_project") else creds)
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    FILTER = (f'logName="projects/{P}/logs/cloudaudit.googleapis.com%2Factivity" AND timestamp>="{since}" '
              f'AND protoPayload.authenticationInfo.principalEmail="sa-documind-cicd@{P}.iam.gserviceaccount.com"')
    r = logs.post("https://logging.googleapis.com/v2/entries:list", timeout=60,
                  json={"resourceNames": [f"projects/{P}"], "filter": FILTER, "orderBy": "timestamp asc", "pageSize": 50})
    r.raise_for_status()
    entries = r.json().get("entries", [])
    print(len(entries), "Admin Activity entries by sa-documind-cicd in the last 24 hours")
    for e in entries:
        pp = e["protoPayload"]
        behind = [d.get("principalSubject") for d in pp.get("authenticationInfo", {}).get("serviceAccountDelegationInfo", [])
                  if d.get("principalSubject")]
        print(e["timestamp"][:19], pp.get("methodName"))
        print("   on behalf of", behind[0] if behind else "(no delegation recorded)")

# Original CLI workflow for step_03_zero_user_managed_keys.
COMMANDS_03 = """set +e +o pipefail   # as the page runs it: the cell prints its own exit status, which a failure must reach
make keys-check PROJECT="$PROJECT"; echo "exit $?"
true   # the status it printed is the cell's answer: compare it with the page's prose


"""

def step_03_zero_user_managed_keys(session):
    """Run Do it: zero user-managed keys at this checkpoint.

    Do it: zero user-managed keys

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (gcloud describe and list calls; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/keys.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_33', step_01_the_trust_and_the_binding_from_iam_s_rest),
        ('source_35', step_02_the_audit_trail_of_step_6_s_run),
        ('source_38', step_03_zero_user_managed_keys),
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
