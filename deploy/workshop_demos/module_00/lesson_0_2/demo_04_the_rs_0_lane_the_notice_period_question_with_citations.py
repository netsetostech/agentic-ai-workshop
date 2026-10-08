"""Lesson 0.2: The Rs 0 lane: the notice-period question, with citations

The lane gets a venv of its own, ~/rag-local-venv. Its packages are the chat service's, LangChain, LangGraph, Chroma and the Ollama client among them, installed on top of the service's image pins as services/chat/requirements-local.txt asks. Keeping them out of ~/rag-shell-venv leaves the operator pins exactly where rag_check_python_dependencies expects them, and every later session runs that check; the kit's CI keeps the chat service's pins in a venv of their own for the same reason. Then Ollama pulls the model, once. Start it in the second terminal, so the first stays free for questions. One line in this block matters more than it looks. The recipe seeds from the kit's root and serves from services/chat, and the store's default path, ./documind_chroma, is relative, so the two commands would open two different directories: the service would find an empty store and answer local corpus is empty. Exporting one absolute path as DOCUMIND_CHROMA_DIR gives both commands the same directory. From the first terminal. The health check first: it names the profile, and the brains this service can run. From the first terminal. The health check first: it names the profile, and the brains this service can run. The service has 4 brains (langchain, langgraph, adk and direct), and langchain is the default: a tool loop in which the model decides when to search. This lesson asks the direct brain, which has no loop at all: one retrieve() for the top 5, then one call to the model with those quotes as its only context. It does not depend on a small model choosing the right tool, which the comment in profile.py warns it sometimes will not. Module 5 compares the brains. Press Ctrl+C in the second terminal. The directory stays on disk, and a Python cell can open it the way the service does, with the same build_store() and the same retrieve():

Run order inside this file:
1. Install the lane, once (source window 11)
2. Start the lane (source window 12)
3. Ask it (source window 14)
4. Ask it (source window 16)
5. Stop the lane, then read the store directly (source window 21)

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


# Original CLI workflow for step_01_install_the_lane_once.
COMMANDS_01 = """cd "${DEMO_ROOT:-$HOME/deploy_module_rag}"                                 # a new terminal: the clone's default place
[ -d "$HOME/rag-local-venv" ] || python3.12 -m venv "$HOME/rag-local-venv"   # the Rs 0 lane's venv, made once
"$HOME/rag-local-venv/bin/python" -m pip install -q -r services/chat/requirements.txt -r services/chat/requirements-local.txt
ollama pull gemma3:4b                                                   # the model, once

"""

def step_01_install_the_lane_once(session):
    """Run Install the lane, once at this checkpoint.

    The lane gets a venv of its own, ~/rag-local-venv. Its packages are the chat service's, LangChain, LangGraph, Chroma and the Ollama client among them, installed on top of the service's image pins as services/chat/requirements-local.txt asks. Keeping them out of ~/rag-shell-venv leaves the operator pins exactly where rag_check_python_dependencies expects them, and every later session runs that check; the kit's CI keeps the chat service's pins in a venv of their own for the same reason. Then Ollama pulls the model, once.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run once, in a second terminal, which the lane will keep: its own venv and its model.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_start_the_lane.
COMMANDS_02 = """cd "${DEMO_ROOT:-$HOME/deploy_module_rag}" && source "$HOME/rag-local-venv/bin/activate"
export DOCUMIND_CHROMA_DIR="$PWD/documind_chroma"     # one directory for the seed and the service
make chat-local                                       # seeds acme, then serves until Ctrl+C

"""

def step_02_start_the_lane(session):
    """Run Start the lane at this checkpoint.

    Start it in the second terminal, so the first stays free for questions. One line in this block matters more than it looks. The recipe seeds from the kit's root and serves from services/chat, and the store's default path, ./documind_chroma, is relative, so the two commands would open two different directories: the service would find an empty store and answer local corpus is empty. Exporting one absolute path as DOCUMIND_CHROMA_DIR gives both commands the same directory.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the second terminal, and leave it running.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/chat_local.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_ask_it.
COMMANDS_03 = """curl -s localhost:8081/health | python -m json.tool

"""

def step_03_ask_it(session):
    """Run Ask it at this checkpoint.

    From the first terminal. The health check first: it names the profile, and the brains this service can run.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the first terminal, while the lane serves.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/chat_health.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_ask_it.
COMMANDS_04 = """curl -s localhost:8081/v1/chat -H 'content-type: application/json' -o /tmp/answer02.json \\
  -d '{"question": "What is the notice period for a confirmed E3?", "brain": "direct", "session_id": "lesson-0-2"}'
python - <<'PY'
import json, warnings; warnings.filterwarnings("ignore", category=UserWarning)
r = json.load(open("/tmp/answer02.json", encoding="utf-8"))
print(r["answer"])
for c in r["citations"]:
    print(f'  {c["score"]:5.3f}  {c["chunk_id"]}  page {c["page"]}')
print("brain", r["brain"], "| tool calls", r["tool_calls"], "| model calls", r["limits"]["model_calls"],
      "| cost Rs", r["limits"]["cost_inr"])
PY

"""

def step_04_ask_it(session):
    """Run Ask it at this checkpoint.

    From the first terminal. The health check first: it names the profile, and the brains this service can run. The service has 4 brains (langchain, langgraph, adk and direct), and langchain is the default: a tool loop in which the model decides when to search. This lesson asks the direct brain, which has no loop at all: one retrieve() for the top 5, then one call to the model with those quotes as its only context. It does not depend on a small model choosing the right tool, which the comment in profile.py warns it sometimes will not. Module 5 compares the brains.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the first terminal: the notice-period question, through the direct brain.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/chat_answer.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_stop_the_lane_then_read_the_store_directly.
COMMANDS_05 = """cd "$DEMO_ROOT" && DOCUMIND_PROFILE=local DOCUMIND_CHROMA_DIR="$PWD/documind_chroma" \\
  "$HOME/rag-local-venv/bin/python" - <<'PY'
import warnings; warnings.filterwarnings("ignore", category=UserWarning)
from shared.profile import CHROMA_COLLECTION, build_store
from shared import documind_tools as dt
store = build_store()                                  # the directory make chat-local seeded
print(store._collection.count(), "chunks in the collection", CHROMA_COLLECTION)
m = store.get(ids=["acme:hr_policy_2026#NP-03"], include=["metadatas"])["metadatas"][0]
print("NP-03:", m["source_uri"], "| page", m["page"], "|", m["section"])
out = dt.retrieve("What is the notice period for a confirmed E3?", tenant_id="acme", top_k=5)
print("answerable", out["answerable"], "| confidence", out["confidence"])
for c in out["citations"]:
    print(f'{c["score"]:5.3f}  {c["chunk_id"]:40}  page {c["page"]}')
print(out["citations"][0]["quote"])
PY

"""

def step_05_stop_the_lane_then_read_the_store_directly(session):
    """Run Stop the lane, then read the store directly at this checkpoint.

    Press Ctrl+C in the second terminal. The directory stays on disk, and a Python cell can open it the way the service does, with the same build_store() and the same retrieve():

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the first terminal after Ctrl+C has stopped the lane: read the store directly.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 1628 chunks in the collection documind_dev
    NP-03: gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md | page 1 | NP-03 — Notice period
    answerable True | confidence high
    1.000  acme:hr_policy_2026#NP-03                 page 1
    0.601  acme:osh_code_2020#p36-0                  page 36
    0.586  acme:cgst_act_2017#p160-0                 page 160
    0.580  acme:maternity_benefit_act_1961#p6-1      page 6
    0.579  acme:cgst_act_2017#p159-0                 page 159
    NP-03 — Notice period
    A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice runs
    from the date the resignation is acknowledged in writing. Unused earned leave may not be
    set off against the notice period.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_11', step_01_install_the_lane_once),
        ('source_12', step_02_start_the_lane),
        ('source_14', step_03_ask_it),
        ('source_16', step_04_ask_it),
        ('source_21', step_05_stop_the_lane_then_read_the_store_directly),
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
