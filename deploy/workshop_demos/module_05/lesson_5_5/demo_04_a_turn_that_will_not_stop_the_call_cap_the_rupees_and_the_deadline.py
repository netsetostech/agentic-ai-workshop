"""Lesson 5.5: A turn that will not stop: the call cap, the rupees and the deadline

Do it: a model that never stops asking Do it: every brain, offline Do it: your lane's limits Do it: a capped turn on your lane

Run order inside this file:
1. Do it: a model that never stops asking (source window 17)
2. Do it: every brain, offline (source window 19)
3. Do it: your lane's limits (source window 21)
4. Do it: a capped turn on your lane (source window 23)

Prerequisites: demo_03_five_failures_through_the_kit_s_langchain_brain.
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


# Original CLI workflow for step_01_a_model_that_never_stops_asking.
COMMANDS_01 = """~/graph-venv/bin/python - <<'PY'
import sys, warnings
warnings.filterwarnings("ignore")                  # the framework warns about a dict context; harmless
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.checkpoint.memory import InMemorySaver
import brains, limits
class Model(BaseChatModel):                        # loop=True: asks for the cost tool again, every call
    loop: bool = True
    calls: int = 0
    @property
    def _llm_type(self): return "scripted"
    def bind_tools(self, tools, **kw): return self
    def _generate(self, messages, stop=None, run_manager=None, **kw):
        self.calls += 1
        ask = [{"name": "calculate_processing_cost", "args": {"total_pages": 283, "processing_type": "priority"}, "id": f"c{self.calls}"}]
        msg = AIMessage("", tool_calls=ask) if self.loop else AIMessage("USD 33.96 at the priority tier, about Rs 2,886.60.")
        return ChatResult(generations=[ChatGeneration(message=msg)])
saver, cfg = InMemorySaver(), {"configurable": {"thread_id": "acme:you:loop"}}
for n, question, model in ((1, "What would 283 pages cost at the priority tier?", Model(loop=True)),
                          (2, "Just give me the priority price, then.", Model(loop=False))):
    brain, meter = brains.LangChainBrain(saver, llm=model), limits.Meter(max_model_calls=3)   # a cap of 3, for a short run
    out = brain.answer(question, config=cfg, context={"tenant_id": "acme", "meter": meter})
    lim = meter.summary()
    print(f"  turn {n}  model calls {lim['model_calls']} of {lim['max_model_calls']}  tool calls {len(out['tool_calls'])}"
          f"  stopped_by {lim['stopped_by']}")
    print(f"          answer: {out['answer']}")
msgs = saver.get(cfg)["channel_values"]["messages"]
answered = {m.tool_call_id for m in msgs if isinstance(m, ToolMessage)}
asked = [c["id"] for m in msgs for c in getattr(m, "tool_calls", None) or []]
print(f"  the thread: {len(msgs)} messages, {len(asked)} tool calls, {len([c for c in asked if c not in answered])} left open")
PY

"""

def step_01_a_model_that_never_stops_asking(session):
    """Run Do it: a model that never stops asking at this checkpoint.

    Do it: a model that never stops asking

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a model that never stops asking, then the next turn on its thread; offline).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: turn 1  model calls 3 of 3  tool calls 3  stopped_by model_calls
              answer: I stopped this turn at one of its limits before I could finish, so this answer is incomplete. Ask again, or ask a narrower question.
      turn 2  model calls 1 of 3  tool calls 0  stopped_by None
              answer: USD 33.96 at the priority tier, about Rs 2,886.60.
      the thread: 10 messages, 3 tool calls, 0 left open
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_every_brain_offline.
COMMANDS_02 = """make limits-check   # the kit's own test file, in ~/graph-venv with the chat image's pins: no credential, no cost

"""

def step_02_every_brain_offline(session):
    """Run Do it: every brain, offline at this checkpoint.

    Do it: every brain, offline

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every agent brain against the limits, offline).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: test_a_forced_recursion_limit_leaves_a_whole_thread (commands.tests.test_chat_limits.BrainsStop.test_a_forced_recursion_limit_leaves_a_whole_thread)
    The framework's backstop, tripped before the Meter: the open call is answered, the turn ends with the stop, ... ok
    test_a_hung_model_call_ends_in_the_stop_not_an_exception (commands.tests.test_chat_limits.BrainsStop.test_a_hung_model_call_ends_in_the_stop_not_an_exception) ... ok
    test_a_looping_model_stops_at_the_call_cap_and_the_next_turn_answers (commands.tests.test_chat_limits.BrainsStop.test_a_looping_model_stops_at_the_call_cap_and_the_next_turn_answers) ... ok
    test_a_looping_model_stops_at_the_deadline (commands.tests.test_chat_limits.Brai
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_your_lane_s_limits.
COMMANDS_03 = """make limits PROJECT="$PROJECT" REGION="$REGION"   # what the deployed chat publishes on /health

"""

def step_03_your_lane_s_limits(session):
    """Run Do it: your lane's limits at this checkpoint.

    Do it: your lane's limits

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads /health as documind-ui-sa; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: documind-chat  https://documind-chat-NUMBER.asia-south1.run.app
      model calls a turn    12
      rupees a turn         Rs 5
      deadline              100 s; each model call min(30 s, time left / 2), none started with under 5 s left
      tool budgets          retrieve 95 s, calculate_processing_cost 10 s
    documind-agent  https://documind-agent-NUMBER.asia-south1.run.app
      model calls a task    not on its /health (ADK defaults to 500)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_a_capped_turn_on_your_lane.
COMMANDS_04 = """make limits-drill PROJECT="$PROJECT" REGION="$REGION" STOP=model_calls   # a minute or two; every chat turn stops meanwhile

"""

def step_04_a_capped_turn_on_your_lane(session):
    """Run Do it: a capped turn on your lane at this checkpoint.

    Do it: a capped turn on your lane

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (caps the deployed chat at one model call, smokes it, and puts it back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> documind-chat: CHAT_MAX_MODEL_CALLS=1 (STOP=model_calls)

      DocuMind chat - live smoke test
      target: https://documind-chat-NUMBER.asia-south1.run.app
      --------------------------------------------------------
      [PASS] health  profile=gcp default=langchain limits=1 calls, Rs 5.0, 100.0 s
      [PASS] brain direct  3120 ms  tools=['retrieve']  citations=5  calls=0 Rs 0.2831  'Gratuity becomes payable after not less than five years of c'
      [PASS] brain langchain stopped  stopped_by=model_calls calls=1 Rs 0.5445  'I stopped this turn at one of its limits before I could fini'
      [PASS] brain langgraph stopped  stopped_by=model_calls calls=1 Rs 0.5445  'I stopped this turn at one of its limits befo
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_17', step_01_a_model_that_never_stops_asking),
        ('source_19', step_02_every_brain_offline),
        ('source_21', step_03_your_lane_s_limits),
        ('source_23', step_04_a_capped_turn_on_your_lane),
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
