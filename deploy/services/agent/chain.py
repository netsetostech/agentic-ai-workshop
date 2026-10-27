"""The peer refuses a delegation loop or a third hop before any model call (workshop lesson 10.7).

Off unless PEER_CHAIN=on on documind-agent. agent.py then hands to_a2a this module's factory (agent_executor_factory,
google-adk 2.8.0 a2a/utils/agent_to_a2a.py), and every task is run by ADK's own executor with one check in front of
it. Off, agent.py never imports this file and every task runs exactly as before.

The caller graph rules out a cycle among the lane's own services by construction: an account may invoke a service
only where its deploy script binds it, and `make check-callers GRAPH=1` shows those bindings acyclic
(commands/check_callers.py). It cannot see an agent the lane does not run. A partner's agent that the peer answers
could hand the question on to an agent that asks the peer again: every hop is a new task, every task may spend the
peer's 12 model calls, and nothing but a timeout ends the loop. So the request carries its own chain, in the A2A
request's metadata (A2A 1.0 has no standard field for it):

    documind_chain       the agents that handed this request on, in order; the chat's ADK brain sends ["documind_adk"]
    documind_handoff_id  the sender's id for the hand-off, which joins its log line to this one

A request whose chain already names this agent is a loop; one whose chain holds MAX_HOPS agents or more would make a
third hop. Both are refused before the runner starts, so they cost no model call. The chain binds only agents that
forward it: one that drops it starts a fresh chain, and what bounds it then are the local limits, the chat's
HANDOFF_MAX_PER_TURN and the peer's cap of 12 model calls a task.

The refusal is a task, ended as ADK ends one. a2a-sdk 1.1.2 wants a new task's first event to be the Task itself (an
update before it raises InvalidAgentResponseError, a2a/server/agent_execution/active_task.py), so the Task goes first,
submitted, as A2aAgentExecutor sends it; then TaskUpdater.reject ends it TASK_STATE_REJECTED ("rejected" on the 0.3
wire), with the reason in its status message. One log line, {"event": "a2a_refused", ...}: the reason, the chain's
length and the hand-off id, never the question's words, never an agent's or a person's name. Like agent.py, this file
imports nothing from the kit: the image copies services/agent alone.
"""
from __future__ import annotations

import json
import logging

from a2a.server.tasks import TaskUpdater
from a2a.types import Part, Task, TaskState, TaskStatus
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor

log = logging.getLogger("documind.agent.chain")

CHAIN_KEY = "documind_chain"
HANDOFF_KEY = "documind_handoff_id"
MAX_HOPS = 3            # a chain of three agents is refused: at most two hops bring a request here


def chain_of(metadata: dict) -> list[str]:
    """The request's chain, as names: a missing chain is empty, and a lone value is a chain of one."""
    chain = metadata.get(CHAIN_KEY) or []
    return [str(agent) for agent in (chain if isinstance(chain, list) else [chain])]


def refusal(chain: list[str], name: str) -> tuple[str, str] | None:
    """Why `name` refuses a request that comes along `chain`, as (reason, words), or None to run it."""
    shown = " -> ".join(agent[:64] for agent in chain[:8]) + (" -> ..." if len(chain) > 8 else "")
    if name in chain:
        return "loop", f"delegation loop: {name} is already in the chain {shown}; refused before any model call"
    if len(chain) >= MAX_HOPS:
        return "hops", (f"too many hops: {len(chain)} (the chain {shown}; {name} refuses {MAX_HOPS} or more); "
                        "refused before any model call")
    return None


class ChainExecutor(A2aAgentExecutor):
    """ADK's executor, with the request's chain read before the runner starts."""

    def __init__(self, *, runner, **kwargs):
        super().__init__(runner=runner, **kwargs)
        self.name = runner.agent.name           # the agent card's name: documind_peer

    async def execute(self, context, event_queue) -> None:
        metadata = context.metadata
        chain = chain_of(metadata)
        why = refusal(chain, self.name)
        if why is None:
            await super().execute(context, event_queue)
            return
        reason, words = why
        if context.current_task is None:        # a new task: the Task first, as A2aAgentExecutor sends it
            await event_queue.enqueue_event(Task(id=context.task_id, context_id=context.context_id,
                                                 status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
                                                 history=[context.message] if context.message else []))
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.reject(updater.new_agent_message([Part(text=words)]))
        log.info(json.dumps({"event": "a2a_refused", "reason": reason, "chain_length": len(chain),
                             "handoff_id": str(metadata.get(HANDOFF_KEY) or "")[:64] or None,
                             "task_id": context.task_id}))


def factory(runner) -> ChainExecutor:
    """to_a2a's agent_executor_factory: ADK's executor around the runner to_a2a made, the chain read first."""
    return ChainExecutor(runner=runner)
