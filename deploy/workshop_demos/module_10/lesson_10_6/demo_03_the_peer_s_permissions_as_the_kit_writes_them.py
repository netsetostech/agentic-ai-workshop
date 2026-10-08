"""Lesson 10.6: The peer's permissions, as the kit writes them

Do it

Run order inside this file:
1. Do it (source window 10)

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


def step_01_the_peer_s_permissions_as_the_kit_writes_t(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the peer's permissions, as the kit writes them; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: documind-agent, as commands/lesson-8.4.sh deploys it:
      runs as documind-agent-sa  model gemini-3.6-flash  knows one URL: MCP_URL
      who may call it: documind-ui-sa, documind-chat-sa
      documind-agent-sa may call documind-mcp: True
      its project roles: aiplatform.user, logging.logWriter, cloudtrace.agent
      the rosters it is on: acme
      agent.py imports: __future__, google, logging, os, starlette, urllib, uvicorn
      the image copies: services/agent/requirements.txt, services/agent/
    """
    import ast, re, sys
    sys.path[:0] = [".", "commands"]
    from lane import roster_plan
    deploy = open("commands/lesson-8.4.sh").read().split("# ---- DEPLOY ----")[1].split("# ---- SMOKE ----")[0]
    env = dict(kv.split("=", 1) for kv in re.search(r'--set-env-vars="\^\|\^([^"]+)"', deploy).group(1).split("|"))
    print("documind-agent, as commands/lesson-8.4.sh deploys it:")
    print("  runs as", re.search(r"--service-account=([\w-]+)@", deploy).group(1), " model", env["AGENT_MODEL"], " knows one URL: MCP_URL")
    print("  who may call it:", ", ".join(re.search(r"for sa in ([\w\- ]+); do", deploy).group(1).split()))
    mcp = open("commands/lesson-7.2.sh").read()
    print("  documind-agent-sa may call documind-mcp:", "documind-agent-sa" in re.search(r"for who in ([\w\- ]+); do", mcp).group(1))
    roles = re.search(r"agent_roles = \[(.*?)\]", open("terraform/sa.tf").read(), re.S).group(1)
    print("  its project roles:", ", ".join(re.findall(r'"roles/([\w.]+)"', roles)))
    tenants = [t for t, e in roster_plan("PROJECT", "acme", [])[0] if e.startswith("documind-agent-sa@")]
    print("  the rosters it is on:", ", ".join(tenants))
    tree = ast.parse(open("services/agent/agent.py").read())
    mods = sorted({(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
                  | {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names})
    print("  agent.py imports:", ", ".join(m for m in mods if m))
    print("  the image copies:", ", ".join(l.split()[-2] for l in open("services/agent/Dockerfile") if l.startswith("COPY")))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_10', step_01_the_peer_s_permissions_as_the_kit_writes_t),
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
