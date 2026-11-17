"""Lesson 10.8: The doors by hand: two brains, the router, the lane's peer

Do it

Run order inside this file:
1. Do it (source window 41)

Prerequisites: demo_07_the_attack_set_six_rows_on_three_surfaces_judged_offline.
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


# Original CLI workflow for step_01_the_doors_by_hand_two_brains_the_router_th.
COMMANDS_01 = """CHAT_TOKEN="$(tok "$CHAT")" AGENT_TOKEN="$(tok "$AGENT")" python - <<'PY'
import json, os, sys, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "evals")
import run_attacks as ra                      # the runner's own request bodies and judge, nothing else from it
CHAT, AGENT = os.environ["CHAT"], os.environ["AGENT"]
TOKENS = {CHAT: os.environ["CHAT_TOKEN"], AGENT: os.environ["AGENT_TOKEN"]}
rows = {r["id"]: r for r in ra.load_set()}


def send(base, door, body):
    \"\"\"POST one body to a door with the token minted for that service; return the status, the content type and the bytes.\"\"\"
    req = urllib.request.Request(base + door, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKENS[base]}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, (e.headers.get("Content-Type", "") if e.headers else ""), e.read()


def judged(label, row, base, door, body):
    \"\"\"Send one attack row through one door and print the runner's own reading of the reply: outcome and verdict.\"\"\"
    status, ctype, raw = send(base, door, body)
    got = ra.judge(row, status, ctype, raw)
    held, word = ra.verdict(row, got["outcome"], got["tenant_leak"])
    print(f"{label:30} HTTP {status}  {got['outcome']:9} {word:8} {got['detail'] or ''}".rstrip())
    print(f"{'':30} said: {(got['answer'] or '')[:120]!r}")


for brain in ("direct", "adk"):               # atk-20, the note's cap, through the brains the runner does not ask
    judged(f"/v1/chat brain={brain}", rows["atk-20"], CHAT, "/v1/chat", {**ra.request_of(rows["atk-20"]), "brain": brain})
status, ctype, raw = send(CHAT, "/v1/route", {"question": rows["atk-18"]["question"]})
print(f"{'/v1/route the invented cap':30} HTTP {status}  {json.dumps(json.loads(raw))[:140]}")
judged("A2A message/send, GLOBEX", rows["atk-17"], AGENT, "/", ra.request_of(rows["atk-17"]))
PY

"""

def step_01_the_doors_by_hand_two_brains_the_router_th(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the doors the runner does not reach: two brains, the router, the lane's peer).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/doors.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_41', step_01_the_doors_by_hand_two_brains_the_router_th),
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
