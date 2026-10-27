"""Lesson 10.5: One question, two arms, over REST

jn-03 to POST /v1/desk as evalacme: the routed Desk, then one agent with every tool. An eval account may send arm in the body of POST /v1/desk; from anyone else the field is a 403, "arm is for the Desk's eval accounts (desk_eval)". Arm B is the Desk everyone gets. Arm Astar skips the classifier: the router takes the fallback decision, marked arm Astar, and the desk graph answers it with one agent whose retrieve may search any class the person reads, with all seven calculators. The cell sends jn-03 on each arm, in a session of its own, and prints what the arms differ in: each section's desk and mode, its tool calls and refused calls, each calculation with its arguments and where they were found, and the turn's model calls and limits.cost_inr.

Run order inside this file:
1. One question, two arms, over REST (source window 31)

Prerequisites: demo_05_change_it_delete_the_prompt_s_rule.
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


# Original CLI workflow for step_01_one_question_two_arms_over_rest.
COMMANDS_01 = """export CHAT="https://documind-chat-$NUMBER.$REGION.run.app"
sa() { echo "documind-$1-sa@$PROJECT.iam.gserviceaccount.com"; }
etok() { gcloud auth print-identity-token --include-email --audiences="$CHAT" \\
         --impersonate-service-account="$(sa "$1")"; }
T_ACME="$(etok evalacme)" python - <<'PY'
import json, os, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
row = next(r for r in map(json.loads, open("evals/route_arms.jsonl", encoding="utf-8")) if r["id"] == "jn-03")


def post(path, body):
    \"\"\"POST a JSON body to the chat service as evalacme: (status, reply).\"\"\"
    req = urllib.request.Request(os.environ["CHAT"] + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + os.environ["T_ACME"]})
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


for arm in ("B", "Astar"):
    status, b = post("/v1/desk", {"question": row["question"], "session_id": f"lesson105-{arm}", "arm": arm})
    if status != 200:
        print(f"arm {arm}: {status} {b.get('detail')}")
        continue
    print(f"arm {b['arm']}: route {b['route']}  method {b['method']}  outcome {b['outcome']}")
    print(f"  model_calls {b['model_calls']}  limits.cost_inr {b['limits']['cost_inr']}  retrieve_calls {b['retrieve_calls']}")
    for s in b["sections"]:
        print(f"  section {s['desk']}: mode {s['mode']}  tool_calls {s['tool_calls']}  refusals {s['refusals']}")
        for c in s.get("calculations") or []:
            args = ", ".join(f"{k}={v}" for k, v in c["args"].items())
            print(f"    {c['calculator']}({args}) = {c['value']} {c['unit']}  found {c['found']}")
    print(f"  the answer says {row['must_contain']}: {all(w in b['answer'] for w in row['must_contain'])}")
PY

"""

def step_01_one_question_two_arms_over_rest(session):
    """Run One question, two arms, over REST at this checkpoint.

    jn-03 to POST /v1/desk as evalacme: the routed Desk, then one agent with every tool. An eval account may send arm in the body of POST /v1/desk; from anyone else the field is a 403, "arm is for the Desk's eval accounts (desk_eval)". Arm B is the Desk everyone gets. Arm Astar skips the classifier: the router takes the fallback decision, marked arm Astar, and the desk graph answers it with one agent whose retrieve may search any class the person reads, with all seven calculators. The cell sends jn-03 on each arm, in a session of its own, and prints what the arms differ in: each section's desk and mode, its tool calls and refused calls, each calculation with its arguments and where they were found, and the turn's model calls and limits.cost_inr.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — jn-03 to POST /v1/desk as evalacme, on arm B, then arm Astar.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/rest_arms.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_31', step_01_one_question_two_arms_over_rest),
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
