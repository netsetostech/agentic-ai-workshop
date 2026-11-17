"""Lesson 10.2: When a plan pays, what each costs, the libraries' forms, and what the kit does not do yet

The planner is set on the agent after it is built, so the constructor lessons 5.7 and 6.1 show is unchanged: ADK's flow reads root.planner on every model request, and LlmAgent's pydantic config lets the field be assigned (commands/tests/test_adk_planner.py checks both on the pinned ADK). The other half is the answer, which is the text not marked thought: a plan or a line of reasoning never reaches it, and a reply that was all plan says so instead of answering nothing. Offline, at Rs 0: the kit's own ADK brain with the switch on, on a scripted model, with the search stood in. The plan is stored marked as thought, goes back to the model as plain text with the next call, and stays out of the answer.

Run order inside this file:
1. ADK's form, on the ADK brain behind a switch (source window 61)

Prerequisites: demo_09_the_3_rows_on_your_lane_and_the_plans_they_saved.
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
COMMANDS_01 = """~/graph-venv/bin/python - <<'PY'
import asyncio, logging, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
logging.disable(logging.WARNING)                    # ADK's notes on a scripted model's missing usage
os.environ["ADK_PLANNER"] = "plan_react"           # the switch, as the chat service reads it at import
os.environ["CHECKPOINT_DSN"] = ""                  # the ADK brain's sessions in memory
sys.path[:0] = ["services/chat", "."]
import brains
from shared import documind_tools
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types as gt

QUOTE = "A confirmed employee serves 60 days' notice."
documind_tools.retrieve = lambda query, **kw: {"answerable": True, "confidence": "high", "citations": [
    {"chunk_id": "acme:handbook#4", "source_uri": "gs://bucket/acme/handbook.pdf", "page": 4, "quote": QUOTE, "score": 0.9}]}
PLAN = "/*PLANNING*/\\n1. Search the handbook for the notice period.\\n2. Answer with the figure and its source."


class Script(BaseLlm):
    \"\"\"Gemini, scripted: each call returns the next reply, and keeps the request it was sent.\"\"\"
    model: str = "scripted"
    replies: list = []
    sent: list = []

    async def generate_content_async(self, llm_request, stream=False):
        \"\"\"The next scripted reply.\"\"\"
        self.sent.append(llm_request.model_copy(deep=True))
        yield self.replies.pop(0)


def reply(*parts):
    \"\"\"A model reply: a string is a text part, a (name, args) pair a tool call.\"\"\"
    return LlmResponse(content=gt.Content(role="model", parts=[gt.Part(text=p) if isinstance(p, str) else
                                                               gt.Part(function_call=gt.FunctionCall(name=p[0], args=p[1])) for p in parts]))


def turn(session, *replies):
    \"\"\"One turn of the kit's ADK brain on the scripted replies: the brain, its model, and what answer() returned.\"\"\"
    brain = brains.AdkBrain(None)
    brain.runner.agent.model = model = Script(replies=list(replies), sent=[])
    out = brain.answer("What notice does a confirmed employee serve?",
                       config={"configurable": {"thread_id": f"acme:you:{session}"}},
                       context={"tenant_id": "acme", "user_id": "you", "assertion": ""})
    return brain, model, out


brain, model, out = turn("plan", reply(PLAN, ("retrieve", {"query": "notice period confirmed employee"})),
                         reply("/*REASONING*/\\nThe handbook says 60 days.\\n/*FINAL_ANSWER*/\\nSixty days of notice [1]."))
print("ADK_PLANNER:", brains.ADK_PLANNER, "| the agent's planner:", type(brain.runner.agent.planner).__name__)
told = str(model.sent[0].config.system_instruction)
print("call 1 is told to plan:", "/*PLANNING*/" in told and "/*FINAL_ANSWER*/" in told)
sess = asyncio.run(brain.svc.get_session(app_name="documind", user_id="you", session_id="acme:you:plan"))
for ev in sess.events:
    for p in (ev.content.parts if ev.content and ev.content.parts else []):
        if ev.author == "documind_adk" and p.text:
            print(f"  stored, thought={p.thought}: {p.text.strip()!r}")
        elif p.function_call:
            print(f"  stored, a tool call: {p.function_call.name}({dict(p.function_call.args)})")
resent = [p.thought for c in model.sent[1].contents for p in (c.parts or []) if p.text and "Search the handbook" in p.text]
print("call 2 is sent the plan back, thought =", resent)
print("the answer:", repr(out["answer"]), "| tool calls:", out["tool_calls"], "| citations:", len(out["citations"]))
_, _, out = turn("all-plan", reply(PLAN))
print("a reply that is all plan answers:")
print(out["answer"])
PY

"""

def step_01_adk_s_form_on_the_adk_brain_behind_a_switc(session):
    """Run ADK's form, on the ADK brain behind a switch at this checkpoint.

    The planner is set on the agent after it is built, so the constructor lessons 5.7 and 6.1 show is unchanged: ADK's flow reads root.planner on every model request, and LlmAgent's pydantic config lets the field be assigned (commands/tests/test_adk_planner.py checks both on the pinned ADK). The other half is the answer, which is the text not marked thought: a plan or a line of reasoning never reaches it, and a reply that was all plan says so instead of answering nothing. Offline, at Rs 0: the kit's own ADK brain with the switch on, on a scripted model, with the search stood in. The plan is stored marked as thought, goes back to the model as plain text with the next call, and stays out of the answer.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a Python cell in ~/graph-venv; Rs 0: the kit's ADK brain with ADK_PLANNER on, on a scripted model).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ADK_PLANNER: plan_react | the agent's planner: PlanReActPlanner
    call 1 is told to plan: True
      stored, thought=True: '1. Search the handbook for the notice period.\\n2. Answer with the figure and its source.'
      stored, a tool call: retrieve({'query': 'notice period confirmed employee'})
      stored, thought=True: 'The handbook says 60 days.'
      stored, thought=None: 'Sixty days of notice [1].'
    call 2 is sent the plan back, thought = [None]
    the answer: 'Sixty days of notice [1].' | tool calls: ['retrieve'] | citations: 1
    a reply that is all plan answers:
    The model wrote a plan but no final answer. Its plan:
    1. Search the handbook for the notice period.
    2. Answer with the figure and its source.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_61', step_01_adk_s_form_on_the_adk_brain_behind_a_switc),
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
