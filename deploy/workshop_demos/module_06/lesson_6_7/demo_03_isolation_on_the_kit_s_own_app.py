"""Lesson 6.7: Isolation, on the kit's own app

Do it: the venv Do it: eight callers

Run order inside this file:
1. Do it: the venv (source window 9)
2. Do it: eight callers (source window 11)

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


# Original CLI workflow for step_01_the_venv.
COMMANDS_01 = """[ -x ~/graph-venv/bin/python ] || python -m venv ~/graph-venv   # lesson 5.4's venv, made here if it is missing
~/graph-venv/bin/pip install -q "langchain==1.4.0" "langchain-core==1.6.2" "requests==2.34.2" "google-auth==2.57.1" "fastapi==0.141.1" \\
  "cloud-sql-python-connector[pg8000]==1.22.0" "pg8000==1.31.5"   # the chat image's pins, and 6.6's connector
~/graph-venv/bin/python -c 'import fastapi.testclient, google.cloud.sql.connector; print("graph-venv ok: fastapi", fastapi.__version__)'

"""

def step_01_the_venv(session):
    """Run Do it: the venv at this checkpoint.

    Do it: the venv

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (lesson 5.4's venv, with the web layer and 6.6's connector).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: graph-venv ok: fastapi 0.141.1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_eight_callers.
COMMANDS_02 = """~/graph-venv/bin/python - <<'PY'
import logging, os, sys, warnings
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
os.environ.update(CHECKPOINT_DSN="memory", SELF_URL="https://documind-chat.example")   # the app's own start-up, in memory
sys.path[:0] = [".", "services/chat"]
from fastapi.testclient import TestClient
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from shared import iap
import agent, brains
class Recall(BaseChatModel):                       # a model that can answer only from the history it is sent
    @property
    def _llm_type(self): return "recall"
    def bind_tools(self, tools, **kw): return self
    def _generate(self, messages, stop=None, run_manager=None, **kw):
        asked = [str(m.content) for m in messages if m.type == "human"]
        text = ("Got it: saffron." if "Remember" in asked[-1] else "You asked me to remember saffron."
                if any("saffron" in a for a in asked[:-1]) else "I have no word from you in this conversation.")
        return ChatResult(generations=[ChatGeneration(message=AIMessage(text))])
PEOPLE = {"alice": ("alice@acme.example", "acme"), "bob": ("bob@acme.example", "acme"),
          "carol": ("carol@zeta.example", "zeta"), "outsider": ("outsider@example.com", None)}
def identity(headers, bearer_audience=None):       # stands in for the token check: the bearer names the person
    who = headers.get("authorization", "").removeprefix("Bearer ")
    if who not in PEOPLE:
        raise iap.IapError("the bearer token carries no verified email")
    return {"email": PEOPLE[who][0], "via": "iam", "aud": bearer_audience}
iap.identity, brains.build_llm = identity, Recall
agent.tenant_for = lambda email: next((t for e, t in PEOPLE.values() if e == email), None)   # stands in for the roster
def ask(c, who, question, session="lesson113", **extra):
    r = c.post("/v1/chat", headers={"Authorization": f"Bearer {who}"},
               json={"question": question, "session_id": session, "brain": "langchain", **extra})
    said = r.json().get("answer") or r.json().get("detail")
    return f"{r.status_code}  {said[0]['msg'] if isinstance(said, list) else said}"
WORD, ASK = "Remember this word for me: saffron.", "Which word did I ask you to remember?"
with TestClient(agent.app) as c:                   # one instance of the kit's chat service
    print(f"  alice gives the word, lesson113        {ask(c, 'alice', WORD)}")
    print(f"  alice asks for it                      {ask(c, 'alice', ASK)}")
    print(f"  alice, a new session                   {ask(c, 'alice', ASK, session='lesson113-b')}")
    print(f"  bob, her tenant, same session name     {ask(c, 'bob', ASK)}")
    print(f"  carol, another tenant, the same name   {ask(c, 'carol', ASK)}")
    print(f"  alice, the body naming zeta            {ask(c, 'alice', ASK, tenant_id='zeta')}")
    print(f"  alice, a session id with a colon       {ask(c, 'alice', ASK, session='lesson113:x')}")
    print(f"  the outsider                           {ask(c, 'outsider', ASK)}")
    print(f"  a token that names nobody              {ask(c, 'nobody', ASK)}")
    print("  the threads the checkpointer holds:")
    for t in sorted({t.config["configurable"]["thread_id"] for t in agent.app.state.checkpointer.list(None)}):
        print("    " + t)
with TestClient(agent.app) as c:                   # a restart: the lifespan builds a new checkpointer
    print(f"  after a restart, alice asks again      {ask(c, 'alice', ASK)}")
PY

"""

def step_02_eight_callers(session):
    """Run Do it: eight callers at this checkpoint.

    Do it: eight callers

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's chat app on your machine; no model, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: alice gives the word, lesson113        200  Got it: saffron.
      alice asks for it                      200  You asked me to remember saffron.
      alice, a new session                   200  I have no word from you in this conversation.
      bob, her tenant, same session name     200  I have no word from you in this conversation.
      carol, another tenant, the same name   200  I have no word from you in this conversation.
      alice, the body naming zeta            200  You asked me to remember saffron.
      alice, a session id with a colon       422  String should match pattern '^[A-Za-z0-9_-]{1,64}$'
      the outsider                           403  not a member of any tenant
      a token that names nobody     
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_the_venv),
        ('source_11', step_02_eight_callers),
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
