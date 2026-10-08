"""Lesson 5.3: The door, as the kit writes it down

Do it

Run order inside this file:
1. Do it (source window 9)

Prerequisites: setup_prepare.
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


def step_01_the_door_as_the_kit_writes_it_down(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the door as the kit writes it down; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: documind-mcp, as commands/lesson-7.2.sh deploys it:
      --no-allow-unauthenticated  --ingress=all  --min-instances=${MIN_INSTANCES:-0}  --service-account=documind-mcp-sa
      SELF_URL=https://documind-mcp-$PROJECT_NUMBER.${REGION:-us-central1}.run.app
      RAG_API_URL=https://documind-api-$PROJECT_NUMBER.${REGION:-us-central1}.run.app
      FASTMCP_STATELESS_HTTP=true
      RAG_TIMEOUT_S=90
    who may call it (roles/run.invoker): documind-ui-sa, documind-agent-sa, documind-outsider-sa
    the tenants each caller may read through it (lane.py's roster_plan):
      documind-ui-sa         acme, zeta, globex
      documind-agent-sa      acme
      documind-outsider-sa   none
    the account rag-api sees for every MCP retrieval: documi
    """
    import re, sys
    sys.path[:0] = [".", "commands"]
    from lane import roster_plan
    deploy = open("commands/lesson-7.2.sh").read().split("# ---- DEPLOY ----")[1].split("# ---- SMOKE ----")[0]
    print("documind-mcp, as commands/lesson-7.2.sh deploys it:")
    print("  " + "  ".join("--" + f.replace("@$PROJECT.iam.gserviceaccount.com", "") for f in
          re.findall(r"--(no-allow-unauthenticated|ingress=\S+|service-account=\S+|min-instances=\S+)", deploy)))
    env = dict(kv.split("=", 1) for kv in re.search(r'--set-env-vars="\^\|\^([^"]+)"', deploy).group(1).split("|"))
    for k in ("SELF_URL", "RAG_API_URL", "FASTMCP_STATELESS_HTTP", "RAG_TIMEOUT_S"):
        print(f"  {k}={env[k]}")
    callers = re.search(r"for who in ([\w\- ]+); do", deploy).group(1).split()
    print("who may call it (roles/run.invoker):", ", ".join(callers))
    rosters = {}
    for tenant, email in roster_plan("PROJECT", "acme", [])[0]:
        rosters.setdefault(email.split("@")[0], []).append(tenant)
    print("the tenants each caller may read through it (lane.py's roster_plan):")
    for who in callers:
        print(f"  {who:22} {', '.join(rosters.get(who, [])) or 'none'}")
    print(f"the account rag-api sees for every MCP retrieval: documind-mcp-sa, on {', '.join(rosters['documind-mcp-sa'])}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_the_door_as_the_kit_writes_it_down),
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
