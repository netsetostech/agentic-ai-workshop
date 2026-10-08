"""Lesson 5.3: One call at each door, and both sides of the answer

Do it: every door Do it: both sides

Run order inside this file:
1. Do it: every door (source window 19)
2. Do it: both sides (source window 21)

Prerequisites: demo_05_the_gate_make_smoke_mcp.
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


def step_01_every_door(session):
    """Run Do it: every door at this checkpoint.

    Do it: every door

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one call at each door).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: no token                              HTTP 403 - Cloud Run, before the server ran
      ui-sa, a token for rag-api's address  HTTP 401 - Cloud Run, before the server ran
      ui-sa, no email in the token          tool error - not authenticated: the bearer token carries no verified email
      the outsider, naming acme             tool error - documind-outsider-sa is not on tenant 'acme''s roster
      ui-sa, naming zeta                    answered - answerable True, 5 citations
    """
    import json, os, subprocess, urllib.error, urllib.request
    MCP, P = os.environ["MCP"], os.environ["PROJECT"]
    def mint(account, email=True, audience=MCP):      # a Google ID token, as gcloud mints it for the smoke test
        """Mint a token for the requested account/audience; varying its email claim tests an admission boundary.
        
        Example: mint('documind-ui-sa', audience=os.environ['API'])
        """
        cmd = ["gcloud", "auth", "print-identity-token", f"--audiences={audience}", f"--impersonate-service-account={account}@{P}.iam.gserviceaccount.com"]
        return subprocess.run(cmd + (["--include-email"] if email else []), capture_output=True, text=True, check=True).stdout.strip()
    def call(token, arguments):                        # one raw tools/call to retrieve; which door answered
        """Perform the current transport request and expose its actual response for the lesson comparison.
        
        Example: call(token, args)
        """
        rpc = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "retrieve", "arguments": arguments}}
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if token:
            headers["Authorization"] = "Bearer " + token
        try:
            with urllib.request.urlopen(urllib.request.Request(MCP + "/mcp", data=json.dumps(rpc).encode(), headers=headers), timeout=180) as r:
                result = json.loads(next(line[6:] for line in r.read().decode().splitlines() if line.startswith("data: ")))["result"]
        except urllib.error.HTTPError as e:
            return f"HTTP {e.code} - Cloud Run, before the server ran"
        if result.get("isError"):
            return "tool error - " + result["content"][0]["text"].replace(f"@{P}.iam.gserviceaccount.com", "")
        return f"answered - answerable {result['structuredContent']['answerable']}, {len(result['structuredContent']['citations'])} citations"
    Q = {"query": "After how many years of continuous service does gratuity become payable?"}
    for label, token, args in (("no token", None, Q),
                               ("ui-sa, a token for rag-api's address", mint("documind-ui-sa", audience=os.environ["API"]), Q),
                               ("ui-sa, no email in the token", mint("documind-ui-sa", email=False), Q),
                               ("the outsider, naming acme", mint("documind-outsider-sa"), {**Q, "tenant": "acme"}),
                               ("ui-sa, naming zeta", mint("documind-ui-sa"), {**Q, "tenant": "zeta"})):
        print(f"  {label:37} {call(token, args)}")

# Original CLI workflow for step_02_both_sides.
COMMANDS_02 = """sleep 20   # Cloud Logging needs a moment to show the lines
python - <<'PY'
import json, os, subprocess
def rows(service, flt):
    f = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="{service}" AND {flt} '
         f'AND timestamp>="{os.environ["SINCE122"]}"')
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "20",
                          "--format", "json"], capture_output=True, text=True, check=True).stdout
    return [e["jsonPayload"] for e in json.loads(out or "[]")]
print("documind-mcp, a line per answered call - who asked:")
for j in rows("documind-mcp", 'jsonPayload.event="mcp_call"'):
    print(f"  {j['tool']:9} tenant {j['tenant']:6} caller {j['caller'].split('@')[0]}")
print("documind-api, a row per retrieval it served for the MCP server - who it served:")
for j in rows("documind-api", 'jsonPayload.brain="mcp"'):
    print(f"  retrieve  tenant {j['tenant']:6} user   {j['user'].split('@')[0]}")
PY

"""

def step_02_both_sides(session):
    """Run Do it: both sides at this checkpoint.

    Do it: both sides

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (both sides of the answered calls).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: documind-mcp, a line per answered call - who asked:
      retrieve  tenant acme   caller documind-ui-sa
      retrieve  tenant zeta   caller documind-ui-sa
    documind-api, a row per retrieval it served for the MCP server - who it served:
      retrieve  tenant acme   user   documind-mcp-sa
      retrieve  tenant zeta   user   documind-mcp-sa
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_19', step_01_every_door),
        ('source_21', step_02_both_sides),
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
