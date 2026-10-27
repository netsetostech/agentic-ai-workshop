"""Lesson 10.2: When a plan pays, what each costs, the libraries' forms, and what the kit does not do yet

Offline, at Rs 0: the kit's own ADK brain with the switch on, on a scripted model, with the search stood in. The plan is stored marked as thought, goes back to the model as plain text with the next call, and stays out of the answer. On your lane the switch needs the chat service's image to carry this kit, so the run starts with a redeploy (Cloud Build, no model call). It then asks the ADK brain the same question with the switch off and on, and takes the switch off again whatever happens. It is optional for you, at most Rs 10 (two turns, each stopped at the chat service's Rs 5); the author's run is below. It shows what the script cannot: whether Gemini still calls retrieve as a function when the instruction asks for tool code under /*ACTION*/, and what a written plan adds to a turn's calls and rupees.

Run order inside this file:
1. ADK's form, on the ADK brain behind a switch (source window 63)

Prerequisites: demo_10_when_a_plan_pays_what_each_costs_the_libraries_forms_and_what_the_kit_does_not_d.
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


# Original CLI workflow for step_01_adk_s_form_on_the_adk_brain_behind_a_switc.
COMMANDS_01 = """make build deploy-services SERVICES=chat SCRIPTS=commands/lesson-12.8.sh PROJECT="$PROJECT" REGION="$REGION"
export CHAT="https://documind-chat-$NUMBER.$REGION.run.app"
CHAT_TOKEN="$(tok "$CHAT")" python - <<'PY'
import json, os, subprocess, time, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
SVC = ["gcloud", "run", "services", "update", "documind-chat", "--region", os.environ["REGION"],
       "--project", os.environ["PROJECT"], "--quiet"]
Q = "What notice period does a confirmed E3 employee at ACME serve?"


def ask(label):
    \"\"\"One ADK turn on /v1/chat, printed: its tool calls, model calls, rupees and answer.\"\"\"
    body = {"question": Q, "session_id": f"lesson102-planner-{label}-{int(time.time())}", "brain": "adk"}
    req = urllib.request.Request(os.environ["CHAT"] + "/v1/chat", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + os.environ["CHAT_TOKEN"], "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=180))
    used = r["limits"]
    print(f"ADK_PLANNER {label}: tool calls {r['tool_calls']}, {used['model_calls']} model calls, Rs {used['cost_inr']}, "
          f"stopped by {used['stopped_by']}")
    print("  answer:", " ".join(r["answer"].split())[:400])


ask("off")
subprocess.run(SVC + ["--update-env-vars", "ADK_PLANNER=plan_react"], check=True, capture_output=True)
try:
    ask("on")
finally:                                             # the switch goes back off, whatever the turn did
    subprocess.run(SVC + ["--remove-env-vars", "ADK_PLANNER"], check=True, capture_output=True)
    print("ADK_PLANNER removed from documind-chat again")
PY

"""

def step_01_adk_s_form_on_the_adk_brain_behind_a_switc(session):
    """Run ADK's form, on the ADK brain behind a switch at this checkpoint.

    Offline, at Rs 0: the kit's own ADK brain with the switch on, on a scripted model, with the search stood in. The plan is stored marked as thought, goes back to the model as plain text with the next call, and stays out of the answer. On your lane the switch needs the chat service's image to carry this kit, so the run starts with a redeploy (Cloud Build, no model call). It then asks the ADK brain the same question with the switch off and on, and takes the switch off again whatever happens. It is optional for you, at most Rs 10 (two turns, each stopped at the chat service's Rs 5); the author's run is below. It shows what the script cannot: whether Gemini still calls retrieve as a function when the instruction asks for tool code under /*ACTION*/, and what a written plan adds to a turn's calls and rupees.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (optional: a chat redeploy, then two ADK turns, the switch off and on; at most Rs 10).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/adk_planner.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_63', step_01_adk_s_form_on_the_adk_brain_behind_a_switc),
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
