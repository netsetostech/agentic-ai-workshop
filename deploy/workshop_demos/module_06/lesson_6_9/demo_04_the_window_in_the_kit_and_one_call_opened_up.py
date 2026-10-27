"""Lesson 6.9: The window in the kit, and one call opened up

Do it: the venv Do it: one call, opened up

Run order inside this file:
1. Do it: the venv (source window 15)
2. Do it: one call, opened up (source window 17)

Prerequisites: demo_03_on_your_lane_today_every_turn_sends_more.
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
COMMANDS_01 = """bash commands/graph-venv.sh -c 'import langchain, langgraph; print("graph-venv ok: langchain", langchain.__version__)'

"""

def step_01_the_venv(session):
    """Run Do it: the venv at this checkpoint.

    Do it: the venv

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (lesson 5.4's ~/graph-venv with the chat image's pins, made if it is missing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: graph-venv ok: langchain 1.4.0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_one_call_opened_up.
COMMANDS_02 = """~/graph-venv/bin/python - <<'PY'
import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["commands", "services/chat", "."]
from langgraph.checkpoint.memory import InMemorySaver
import brains, context_window as cw, thread_replay as rp, window_check as wc
import shared.documind_tools as dt
BUDGET, CARD = 600, "4111 1111 1111 1111"
def passages(query, **kw):
    \"\"\"A stand-in search with no corpus behind it: three passages, the same for every question.\"\"\"
    return {"answerable": True, "confidence": "high", "citations": [
        {"chunk_id": f"acme:stand_in#{i}", "source_uri": "gs://bucket/acme/stand_in.md", "page": 1, "score": 1.0,
         "quote": f"Stand-in passage {i}. " + "The policy text a real search would return. " * 9} for i in (1, 2, 3)]}
class Seen(type(rp.scripted([]))):
    \"\"\"Lesson 6.8's script (search for the question, answer from the first passage), keeping what each call is sent.\"\"\"
    sent: list = []
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        \"\"\"Record this call's messages, then answer as the script does.\"\"\"
        self.sent.append(list(messages))
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
dt.retrieve = passages                                      # tools.search() calls documind_tools.retrieve()
seen = Seen(play=[])
model = cw.windowed(seen, history_tokens=BUDGET)            # the window in front of the model; the brain is the kit's own
brain = brains.LangChainBrain(InMemorySaver(), llm=model)
config = wc.config_for("opened-up")
for question in wc.QUESTIONS[:10]:                          # make window-check's first ten questions
    brain.answer(question, config=config, context={"tenant_id": "acme", "user_id": "you", "assertion": "", "brain": "langchain"})
thread = brain.agent.get_state(config).values["messages"]
print(f"10 turns, {len(seen.sent)} model calls, the window's budget for earlier turns {BUDGET} tokens")
print(f"the checkpoint: {len(thread)} messages, {cw.tokens(thread):,} tokens; question 6 kept as typed: "
      f"{any(CARD in cw.text_of(m.content) for m in thread)}")
print(f"the card number in what the model was sent, all {len(seen.sent)} calls: "
      f"{sum(CARD in cw.text_of(m.content) for call in seen.sent for m in call)} times")
last, report = seen.sent[-1], model.calls[-1]
print(f"turn 10's answering call, as the model received it: {len(last)} messages, {cw.tokens(last):,} tokens, "
      f"its ceiling {report['ceiling']:,} (the floor {report['floor_tokens']:,} + {BUDGET})")
for i, m in enumerate(last, 1):
    calls = ", ".join(c["name"] for c in getattr(m, "tool_calls", None) or [])
    text = "asks " + calls if calls else " ".join(cw.text_of(m.content).split())
    print(f"  {i:>2}  {m.type:6} {cw.tokens([m]):>4}  {text[:78] + ('...' if len(text) > 78 else '')}")
print(f"the line: {report['line']}")
asked = [cw.text_of(m.content).rsplit(chr(10) * 2, 1)[-1] for m in last if m.type == "human"]
print(f"turn 9's question, as this call carries it: {len(asked[-2])} characters of {len(wc.QUESTIONS[8])}")
PY

"""

def step_02_one_call_opened_up(session):
    """Run Do it: one call, opened up at this checkpoint.

    Do it: one call, opened up

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (ten turns of the kit's brain behind the window; a stand-in search, no network, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 10 turns, 20 model calls, the window's budget for earlier turns 600 tokens
    the checkpoint: 40 messages, 5,654 tokens; question 6 kept as typed: True
    the card number in what the model was sent, all 20 calls: 0 times
    turn 10's answering call, as the model received it: 12 messages, 1,179 tokens, its ceiling 1,201 (the floor 601 + 600)
       1  system  111  You are DocuMind AI, a document intelligence assistant. Use the tools for docu...
       2  human   150  [Earlier in this conversation, not shown here: turns 1 to 7. The person asked,...
       3  ai       43  asks retrieve
       4  tool     33  {"cleared": true, "reason": "evidence from an earlier turn: search again if yo...
       5  ai       56  (offline, s
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_15', step_01_the_venv),
        ('source_17', step_02_one_call_opened_up),
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
