"""Lesson 10.9: What up stages, and what the runtime will import

Do it: stage The image runs adk api_server, which imports the package and serves the root_agent it finds there. The cell makes the same import with ADK's own loader, in a venv holding the peer image's pins. It sets the location ADK's Dockerfile sets and the content setting ADK's deploy adds, and reads no .env, since the image ships none. It makes no call: the model and the tools are reached only when a question arrives.

Run order inside this file:
1. Do it: stage (source window 10)
2. Do it: import the package as the runtime will (source window 12)

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


# Original CLI workflow for step_01_stage.
COMMANDS_01 = """rm -rf /tmp/mp109 && python commands/managed_peer.py stage --dir /tmp/mp109 \\
  --project "$PROJECT" --project-number "$NUMBER" --services-region "$REGION"   # no call, Rs 0

"""

def step_01_stage(session):
    """Run Do it: stage at this checkpoint.

    Do it: stage

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (what up deploys, written out; no call).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: == stage: what make managed-peer-up deploys, written to /tmp/mp109 ==
      documind_peer/__init__.py       byte for byte commands/managed_peer_agent.py
      documind_peer/agent.py          byte for byte services/agent/agent.py
      documind_peer/chain.py          byte for byte services/agent/chain.py
      documind_peer/pins.py           byte for byte services/agent/pins.py
      documind_peer/requirements.txt  byte for byte services/agent/requirements.txt
      documind_peer/tool_pins.json    byte for byte services/agent/tool_pins.json
      deploy_config/.agent_engine_config.json  {"service_account": "documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com", "min_instances": 0, "max_instances": 1}
      deploy_c
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_import_the_package_as_the_runtime_will.
COMMANDS_02 = """[ -x ~/peer-pins-venv/bin/python ] || { python3 -m venv ~/peer-pins-venv && ~/peer-pins-venv/bin/pip install -q -r services/agent/requirements.txt; }   # the peer image's pins, once
~/peer-pins-venv/bin/python - <<'PY'
import json, logging, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
logging.basicConfig(level=logging.WARNING, format="%(message)s", stream=sys.stdout)
logging.getLogger("documind.managed_peer").setLevel(logging.INFO)   # the wrapper's one line, as the runtime logs it
env = dict(line.split("=", 1) for line in open("/tmp/mp109/deploy_config/.env").read().splitlines())
os.environ.update(env, GOOGLE_CLOUD_LOCATION=os.environ["REGION"],  # ADK's Dockerfile sets the region here
                  ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS="false",      # ADK's deploy sets this with telemetry on
                  ADK_DISABLE_LOAD_DOTENV="1")                       # the image ships no .env
from google.adk.agents.run_config import RunConfig
from google.adk.cli.utils.agent_loader import AgentLoader
root = AgentLoader(agents_dir="/tmp/mp109").load_agent("documind_peer")   # as adk api_server loads it
peer = sys.modules["documind_peer.agent"]
print("root_agent is agent.py's own agent:", root is peer.agent, "| name:", root.name)
print("its model:", type(root.model).__name__, root.model.model, "| its tools:", [type(t).__name__ for t in root.tools])
print("model calls a turn, at most:", RunConfig().max_llm_calls)
PY

"""

def step_02_import_the_package_as_the_runtime_will(session):
    """Run Do it: import the package as the runtime will at this checkpoint.

    The image runs adk api_server, which imports the package and serves the root_agent it finds there. The cell makes the same import with ADK's own loader, in a venv holding the peer image's pins. It sets the location ADK's Dockerfile sets and the content setting ADK's deploy adds, and reads no .env, since the image ships none. It makes no call: the model and the tools are reached only when a question arrives.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the staged package, imported as the runtime imports it; no Google call).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS": "false", "ADK_MAX_LLM_CALLS": "12", "GOOGLE_CLOUD_LOCATION": "asia-south1", "agent": "documind_peer", "event": "managed_peer_up", "model": "gemini-3.6-flash", "model_location": "global", "versions": {"a2a-sdk": "1.1.2", "google-adk": "2.8.0", "google-auth": "2.57.1", "google-cloud-aiplatform": null, "google-genai": "2.22.0"}}
    root_agent is agent.py's own agent: True | name: documind_peer
    its model: GlobalGemini gemini-3.6-flash | its tools: ['McpToolset']
    model calls a turn, at most: 12
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_10', step_01_stage),
        ('source_12', step_02_import_the_package_as_the_runtime_will),
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
