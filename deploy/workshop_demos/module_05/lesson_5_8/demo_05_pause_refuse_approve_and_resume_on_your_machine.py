"""Lesson 5.8: Pause, refuse, approve and resume on your machine

The cell builds the kit's approval graph on a scripted model that asks for withdraw_document, with an in-memory checkpointer and an executor that only prints. It streams the turn to its pause and lists what waits. Then it tries Asha's own approval, and Ravi's. The pause is data in the checkpointer, not a request waiting in memory. The first process pauses the turn into a SQLite file, ~/lesson108_threads.db, through SqliteSaver, the local lane's checkpointer, and ends. The second process is a new interpreter: it builds a new graph on the same file, finds the waiting call, and resumes it with Ravi's approval. The same graph, now with a scripted model that asks Asha which rule applies to her. The handbook's NP-03 gives a confirmed employee at grade E3 or above 60 days' notice, and its PB-02 gives 15 days during probation. Ravi tries to answer for her, Asha tries to approve, then Asha answers. A resumed node runs again from its first line. The kit writes its "approval asked" line below interrupt(), so it is written once, at the resume. The first cell defines twice108, which pauses one withdrawal, approves it, and counts that line at each point. The second cell moves the line above interrupt(), from line 364 to line 361, and runs twice108 again. Then it puts the kit's file back with git, so the setup section's git pull next time is not refused.

Run order inside this file:
1. Do it: a withdrawal, paused and approved (source window 25)
2. Do it: a second process resumes it (source window 27)
3. Do it: a question only the asker answers (source window 29)
4. Change it: the approval line above interrupt() (source window 31)
5. Change it: the approval line above interrupt() (source window 33)

Prerequisites: demo_04_the_pause_in_the_kit_approval_py.
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


# Original CLI workflow for step_01_a_withdrawal_paused_and_approved.
COMMANDS_01 = """~/graph-venv/bin/python - <<'PY'
import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
import approval
class Scripted(FakeMessagesListChatModel):
    \"\"\"A model that replies as scripted, in order.\"\"\"
    def bind_tools(self, tools, **kw):
        \"\"\"The graph binds the kit's tools; a scripted model keeps itself.\"\"\"
        return self
import logging
class Show(logging.Handler):
    \"\"\"Prints each line approval.py logs.\"\"\"
    def emit(self, record):
        \"\"\"One log line, printed where the cell's own lines go.\"\"\"
        print("  log:", record.getMessage())
logging.getLogger("documind.chat.approval").addHandler(Show())
logging.getLogger("documind.chat.approval").setLevel(logging.INFO)
def withdraw(**kw):
    \"\"\"The injected executor: it prints what it was asked to do and withdraws nothing.\"\"\"
    print("  withdraw() called with", kw)
    return {"status": "withdrawal_started"}
ASHA, RAVI = "asha@example.com", "ravi@example.com"
cfg = {"configurable": {"thread_id": f"acme:{ASHA}:lesson108"}}     # tenant:user:session, as agent.py builds it
g = approval.build_approval_graph(Scripted(responses=[
    AIMessage("", tool_calls=[{"name": "withdraw_document", "args": {"name": "hr_policy_2026.md"}, "id": "c0"}]),
    AIMessage("The withdrawal was approved and has started.")]), InMemorySaver())
for update in g.stream({"messages": [HumanMessage("Withdraw hr_policy_2026.md")]}, cfg,
                       context={"withdraw": withdraw}, stream_mode="updates"):
    print("  ran:", ", ".join(update))
for w in approval.paused(g, cfg):
    print(f"  waiting: {w['tool']} {w['args']} call {w['call_id']}, takes {w['allowed_decisions']}, asked by {w['requester']}")
try:
    approval.decide(g, cfg, [{"type": "approve"}], by=ASHA, context={"withdraw": withdraw})
except PermissionError as e:
    print("  asha approves:", type(e).__name__, "-", e)
print("  still waiting:", [w["tool"] for w in approval.paused(g, cfg)])
out = approval.decide(g, cfg, [{"type": "approve"}], by=RAVI, context={"withdraw": withdraw})
done = [m for m in out["messages"] if isinstance(m, ToolMessage)][-1]
print(f"  ravi approves: {done.name} {done.status} {done.content}")
print("  path:", " -> ".join(s.next[0] if s.next else "END" for s in reversed(list(g.get_state_history(cfg)))))
print("  waiting now:", approval.paused(g, cfg))
PY

"""

def step_01_a_withdrawal_paused_and_approved(session):
    """Run Do it: a withdrawal, paused and approved at this checkpoint.

    The cell builds the kit's approval graph on a scripted model that asks for withdraw_document, with an in-memory checkpointer and an executor that only prints. It streams the turn to its pause and lists what waits. Then it tries Asha's own approval, and Ravi's.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a withdrawal paused, refused to its requester, approved by a second person; no network, no model).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ran: agent
      ran: __interrupt__
      waiting: withdraw_document {'name': 'hr_policy_2026.md'} call c0, takes ['approve', 'reject'], asked by asha@example.com
      asha approves: PermissionError - the person who asked cannot approve their own request: a second person must
      still waiting: ['withdraw_document']
      log: approval asked: withdraw_document
      withdraw() called with {'tenant': 'acme', 'name': 'hr_policy_2026.md', 'requested_by': 'asha@example.com', 'approved_by': 'ravi@example.com'}
      ravi approves: withdraw_document success {"status": "withdrawal_started", "document": "acme/hr_policy_2026.md", "undo": "make restore SOURCE=acme/hr_policy_2026.md"}
      path: __start__ -> agent -> approve -> t
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_second_process_resumes_it.
COMMANDS_02 = """rm -f ~/lesson108_threads.db
~/graph-venv/bin/python - <<'PY'
import os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
import approval
class Scripted(FakeMessagesListChatModel):
    \"\"\"A model that replies as scripted, in order.\"\"\"
    def bind_tools(self, tools, **kw):
        \"\"\"The graph binds the kit's tools; a scripted model keeps itself.\"\"\"
        return self
cfg = {"configurable": {"thread_id": "acme:asha@example.com:lesson108-sqlite"}}
ask = AIMessage("", tool_calls=[{"name": "withdraw_document", "args": {"name": "hr_policy_2026.md"}, "id": "c0"}])
with SqliteSaver.from_conn_string(os.path.expanduser("~/lesson108_threads.db")) as saver:
    g = approval.build_approval_graph(Scripted(responses=[ask]), saver)
    g.invoke({"messages": [HumanMessage("Withdraw hr_policy_2026.md")]}, cfg, context={})
    print("process 1: paused before", g.get_state(cfg).next, "| waiting:", [w["tool"] for w in approval.paused(g, cfg)])
print("process 1: ends; the paused turn is in the file")
PY
~/graph-venv/bin/python - <<'PY'
import logging, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
import approval
class Scripted(FakeMessagesListChatModel):
    \"\"\"A model that replies as scripted, in order.\"\"\"
    def bind_tools(self, tools, **kw):
        \"\"\"The graph binds the kit's tools; a scripted model keeps itself.\"\"\"
        return self
class Show(logging.Handler):
    \"\"\"Prints each line approval.py logs.\"\"\"
    def emit(self, record):
        \"\"\"One log line, printed where the cell's own lines go.\"\"\"
        print("process 2: log:", record.getMessage())
logging.getLogger("documind.chat.approval").addHandler(Show())
logging.getLogger("documind.chat.approval").setLevel(logging.INFO)
def withdraw(**kw):
    \"\"\"The injected executor: it prints what it was asked to do and withdraws nothing.\"\"\"
    print("process 2: withdraw() called with", kw)
    return {"status": "withdrawal_started"}
cfg = {"configurable": {"thread_id": "acme:asha@example.com:lesson108-sqlite"}}
with SqliteSaver.from_conn_string(os.path.expanduser("~/lesson108_threads.db")) as saver:
    g = approval.build_approval_graph(Scripted(responses=[AIMessage("Withdrawn, from the second process.")]), saver)
    print("process 2: a new graph on the same file finds:", [w["tool"] for w in approval.paused(g, cfg)])
    out = approval.decide(g, cfg, [{"type": "approve"}], by="ravi@example.com", context={"withdraw": withdraw})
    print("process 2: answer:", out["messages"][-1].content, "| waiting now:", approval.paused(g, cfg))
PY

"""

def step_02_a_second_process_resumes_it(session):
    """Run Do it: a second process resumes it at this checkpoint.

    The pause is data in the checkpointer, not a request waiting in memory. The first process pauses the turn into a SQLite file, ~/lesson108_threads.db, through SqliteSaver, the local lane's checkpointer, and ends. The second process is a new interpreter: it builds a new graph on the same file, finds the waiting call, and resumes it with Ravi's approval.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one process pauses the turn into a file, a second process resumes it).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: process 1: paused before ('approve',) | waiting: ['withdraw_document']
    process 1: ends; the paused turn is in the file
    process 2: a new graph on the same file finds: ['withdraw_document']
    process 2: log: approval asked: withdraw_document
    process 2: withdraw() called with {'tenant': 'acme', 'name': 'hr_policy_2026.md', 'requested_by': 'asha@example.com', 'approved_by': 'ravi@example.com'}
    process 2: answer: Withdrawn, from the second process. | waiting now: []
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_a_question_only_the_asker_answers.
COMMANDS_03 = """~/graph-venv/bin/python - <<'PY'
import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
import approval
class Scripted(FakeMessagesListChatModel):
    \"\"\"A model that replies as scripted, in order.\"\"\"
    def bind_tools(self, tools, **kw):
        \"\"\"The graph binds the kit's tools; a scripted model keeps itself.\"\"\"
        return self
ASHA, RAVI = "asha@example.com", "ravi@example.com"
cfg = {"configurable": {"thread_id": f"acme:{ASHA}:lesson108-ask"}}
question = "Are you a confirmed employee at grade E3 or above, or still on probation?"
g = approval.build_approval_graph(Scripted(responses=[
    AIMessage("", tool_calls=[{"name": "ask_user", "args": {"question": question}, "id": "c0"}]),
    AIMessage("The answer, from the person's reply.")]), InMemorySaver())
g.invoke({"messages": [HumanMessage("What is my notice period?")]}, cfg, context={})
for w in approval.paused(g, cfg):
    print(f"  waiting: {w['tool']} takes {w['allowed_decisions']}, for {w['requester']}: {w['description']}")
for who, d in ((RAVI, {"type": "respond", "message": "Confirmed, E3."}), (ASHA, {"type": "approve"})):
    try:
        approval.decide(g, cfg, [d], by=who)
    except (PermissionError, ValueError) as e:
        print(f"  {who.split('@')[0]} sends {d['type']}: {type(e).__name__} - {e}")
out = approval.decide(g, cfg, [{"type": "respond", "message": "I am still on probation."}], by=ASHA)
reply = [m for m in out["messages"] if isinstance(m, ToolMessage)][-1]
print(f"  asha answers: the model reads {reply.name}'s result {reply.content!r} ({reply.status})")
print("  path:", " -> ".join(s.next[0] if s.next else "END" for s in reversed(list(g.get_state_history(cfg)))))
PY

"""

def step_03_a_question_only_the_asker_answers(session):
    """Run Do it: a question only the asker answers at this checkpoint.

    The same graph, now with a scripted model that asks Asha which rule applies to her. The handbook's NP-03 gives a confirmed employee at grade E3 or above 60 days' notice, and its PB-02 gives 15 days during probation. Ravi tries to answer for her, Asha tries to approve, then Asha answers.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a clarifying question, answered only by the person who asked).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: waiting: ask_user takes ['respond'], for asha@example.com: Are you a confirmed employee at grade E3 or above, or still on probation?
      ravi sends respond: PermissionError - only the person who asked may answer their own question
      asha sends approve: ValueError - ask_user takes respond, not 'approve'
      asha answers: the model reads ask_user's result 'I am still on probation.' (success)
      path: __start__ -> agent -> approve -> agent -> END
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_change_it_the_approval_line_above_interrup.
COMMANDS_04 = """twice108() {   # one withdrawal paused, then approved; counts the "approval asked" lines
~/graph-venv/bin/python - <<'PY'
import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
import approval
class Scripted(FakeMessagesListChatModel):
    \"\"\"A model that replies as scripted, in order.\"\"\"
    def bind_tools(self, tools, **kw):
        \"\"\"The graph binds the kit's tools; a scripted model keeps itself.\"\"\"
        return self
import logging
lines = []
class Keep(logging.Handler):
    \"\"\"Keeps every line approval.py logs.\"\"\"
    def emit(self, record):
        \"\"\"One log line, kept for the count.\"\"\"
        lines.append(record.getMessage())
logging.getLogger("documind.chat.approval").addHandler(Keep())
logging.getLogger("documind.chat.approval").setLevel(logging.INFO)
done = []
def withdraw(**kw):
    \"\"\"The injected executor: it counts the withdrawals and withdraws nothing.\"\"\"
    done.append(kw)
    return {"status": "withdrawal_started"}
cfg = {"configurable": {"thread_id": "acme:asha@example.com:lesson108-twice"}}
g = approval.build_approval_graph(Scripted(responses=[
    AIMessage("", tool_calls=[{"name": "withdraw_document", "args": {"name": "hr_policy_2026.md"}, "id": "c0"}]),
    AIMessage("Done.")]), InMemorySaver())
g.invoke({"messages": [HumanMessage("Withdraw hr_policy_2026.md")]}, cfg, context={"withdraw": withdraw})
print("  at the pause:     ", sum("approval asked" in x for x in lines), "approval line(s)")
approval.decide(g, cfg, [{"type": "approve"}], by="ravi@example.com", context={"withdraw": withdraw})
print("  after the resume: ", sum("approval asked" in x for x in lines), "approval line(s),", len(done), "withdrawal(s)")
PY
}
twice108

"""

def step_04_change_it_the_approval_line_above_interrup(session):
    """Run Change it: the approval line above interrupt() at this checkpoint.

    A resumed node runs again from its first line. The kit writes its "approval asked" line below interrupt(), so it is written once, at the resume. The first cell defines twice108, which pauses one withdrawal, approves it, and counts that line at each point. The second cell moves the line above interrupt(), from line 364 to line 361, and runs twice108 again. Then it puts the kit's file back with git, so the setup section's git pull next time is not refused.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (defines twice108, then runs it on the kit as it is).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: at the pause:      0 approval line(s)
      after the resume:  1 approval line(s), 1 withdrawal(s)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_change_it_the_approval_line_above_interrup.
COMMANDS_05 = """python - <<'PY'   # the Change-it: the "approval asked" line moved above interrupt(), nothing else
import warnings
from pathlib import Path
warnings.filterwarnings("ignore", category=UserWarning)
p = Path("services/chat/approval.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
log = next(i for i, x in enumerate(lines) if 'logger.info("approval asked' in x)
stop = next(i for i, x in enumerate(lines) if "answer = interrupt(request)" in x)
lines.insert(stop, lines.pop(log))                  # the same indentation: both lines sit in approve()
p.write_text("".join(lines), encoding="utf-8")
print(f"moved line {log + 1} up to line {stop + 1}, just above: {lines[stop + 1].split('#')[0].strip()}")
PY
twice108
git checkout -- services/chat/approval.py && git diff --quiet -- services/chat/approval.py && echo "approval.py is the kit's again"

"""

def step_05_change_it_the_approval_line_above_interrup(session):
    """Run Change it: the approval line above interrupt() at this checkpoint.

    A resumed node runs again from its first line. The kit writes its "approval asked" line below interrupt(), so it is written once, at the resume. The first cell defines twice108, which pauses one withdrawal, approves it, and counts that line at each point. The second cell moves the line above interrupt(), from line 364 to line 361, and runs twice108 again. Then it puts the kit's file back with git, so the setup section's git pull next time is not refused.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the Change-it: one line moved, twice108 again, then the kit restored).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: moved line 364 up to line 361, just above: answer = interrupt(request)
      at the pause:      1 approval line(s)
      after the resume:  2 approval line(s), 1 withdrawal(s)
    approval.py is the kit's again
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_a_withdrawal_paused_and_approved),
        ('source_27', step_02_a_second_process_resumes_it),
        ('source_29', step_03_a_question_only_the_asker_answers),
        ('source_31', step_04_change_it_the_approval_line_above_interrup),
        ('source_33', step_05_change_it_the_approval_line_above_interrup),
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
