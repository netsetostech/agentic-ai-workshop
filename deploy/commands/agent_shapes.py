"""Agent shapes, offline: two ADK desks hand one question back and forth, and a cap ends it (workshop lesson 10.7).

    python commands/agent_shapes.py --offline          # from deploy/, in ~/graph-venv: make agent-shapes OFFLINE=1

swarm_adk, the one shape so far: a root and two desks under it, handbook_desk and statute_desk, each an ADK LlmAgent
in chat mode (google-adk 2.8.0). ADK offers each agent its transfer_to_agent tool, whose agent_name is an enum of the
agents it may hand the turn to: its sub-agents, its parent, and its peers unless disallow_transfer_to_peers is set
(flows/llm_flows/agent_transfer.py). Nobody in the shape owns the answer, so two desks that each think the other should
answer hand the question back and forth, a ping-pong, until something outside them stops it.

TransferCap stops it: an ADK plugin on the Runner's App that counts the agents a turn starts in a temp: key of the
session state, which ADK keeps for one invocation and never stores (sessions/base_session_service.py), and refuses the
start after MAX_TRANSFERS transfers by answering in that agent's place. A before_agent_callback that returns content
ends the invocation (agents/base_agent.py), so the refused agent's model is never called.

Offline (--offline, the only mode so far): scripted models, no credential, no network, Rs 0. Each desk's script reads
the enum it was offered and asks for the other desk when it may, for the root otherwise; the root's sends the question
to each desk in turn. The turn runs twice: with transfers between the desks allowed, then with
disallow_transfer_to_peers on both, where the loop runs through the root and the same cap ends it. Taking an edge away
does not give a loop its stop; a cap does. Verified by commands/tests/test_agent_shapes.py.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import warnings
from typing import Any

MAX_TRANSFERS = 3                     # a turn's transfers between agents; the start after the last is refused
STOP = "Stopped after {n} transfers in one turn."
STARTS = "temp:agent_starts"          # the cap's count: a temp: key, kept for one invocation and never stored
QUESTION = "What notice period does a confirmed E3 employee at ACME serve?"
ROOT = "desk_root"
DESKS = {"handbook_desk": "Answers from ACME's employee handbook: notice, leave and conduct.",
         "statute_desk": "Answers from the labour statutes: gratuity, notice pay and leave encashment."}


def transfer_cap(max_transfers: int = MAX_TRANSFERS):
    """The cap, as an ADK plugin. Built here so google-adk is imported lazily, as services/chat/brains.py does."""
    from google.adk.plugins.base_plugin import BasePlugin
    from google.genai import types as gt

    class TransferCap(BasePlugin):
        """Counts the agents a turn starts: the first is the turn's own, every later one a transfer."""

        def __init__(self):
            super().__init__(name="transfer_cap")

        async def before_agent_callback(self, *, agent, callback_context):
            """None lets the agent run; content answers in its place."""
            starts = callback_context.state.get(STARTS, 0) + 1
            callback_context.state[STARTS] = starts
            if starts - 1 > max_transfers:      # content here ends the invocation: this agent's model is never called
                return gt.Content(role="model", parts=[gt.Part(text=STOP.format(n=max_transfers))])
            return None

    return TransferCap()


def offered(llm_request) -> list:
    """The agent_name enum of the transfer tool a model was offered: the agents it may hand the turn to."""
    for tool in llm_request.config.tools or []:
        for fd in tool.function_declarations or []:
            if fd.name == "transfer_to_agent":
                if fd.parameters is not None:
                    return list(fd.parameters.properties["agent_name"].enum or [])
                return list((fd.parameters_json_schema or {})["properties"]["agent_name"].get("enum") or [])
    return []


def scripted(name: str, log: dict):
    """A scripted model for one agent. It never answers: a desk asks for the other desk if it may, else for the root,
    and the root sends the question to each desk in turn. Every call is logged with the enum it was offered."""
    from google.adk.models.base_llm import BaseLlm
    from google.adk.models.llm_response import LlmResponse
    from google.genai import types as gt

    class Script(BaseLlm):
        """One agent's scripted model: a transfer_to_agent call, chosen from the enum the request offers."""
        model: str = "scripted"
        trace: Any = None                    # the run's log, shared by reference

        async def generate_content_async(self, llm_request, stream=False):
            enum = offered(llm_request)
            if name == ROOT:
                mine = sum(1 for call in self.trace["calls"] if call[0] == ROOT)
                target = list(DESKS)[mine % len(DESKS)]
            else:
                other = next(d for d in DESKS if d != name)
                target = other if other in enum else ROOT
            self.trace["calls"].append((name, enum, target))
            yield LlmResponse(content=gt.Content(role="model", parts=[gt.Part(function_call=gt.FunctionCall(
                name="transfer_to_agent", args={"agent_name": target}))]))

    return Script(trace=log)


async def swarm_adk(peers: bool = True, turns: int = 1) -> dict:
    """The shape, offline: one question through the root and its two desks under TransferCap, `turns` times in one
    session. Returns each turn's calls (agent, enum offered, target), transfers, answer and last speaker, and the
    session state ADK stored after the last turn."""
    from google.adk.agents import LlmAgent
    from google.adk.apps import App
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types as gt

    log = {"calls": []}
    desks = [LlmAgent(name=name, description=about, instruction=about, model=scripted(name, log),
                      disallow_transfer_to_peers=not peers) for name, about in DESKS.items()]
    root = LlmAgent(name=ROOT, description="Sends each question to the desk that should answer it.",
                    instruction="Transfer each question to the desk that should answer it.",
                    model=scripted(ROOT, log), sub_agents=desks)
    svc = InMemorySessionService()
    runner = Runner(app=App(name="shapes", root_agent=root, plugins=[transfer_cap()]), session_service=svc)
    sess = await svc.create_session(app_name="shapes", user_id="you", session_id="swarm")
    out = []
    for _ in range(turns):
        log["calls"] = []
        transfers, answer, last = [], "", ""
        async for ev in runner.run_async(user_id="you", session_id=sess.id,
                                         new_message=gt.Content(role="user", parts=[gt.Part(text=QUESTION)])):
            if ev.actions.transfer_to_agent:
                transfers.append((ev.author, ev.actions.transfer_to_agent))
            text = "".join(p.text or "" for p in (ev.content.parts or [])) if ev.content else ""
            if ev.is_final_response() and text:
                answer, last = text, ev.author
        out.append({"calls": list(log["calls"]), "transfers": transfers, "answer": answer, "last": last})
    stored = await svc.get_session(app_name="shapes", user_id="you", session_id=sess.id)
    return {"peers": peers, "turns": out, "stored": dict(stored.state)}


def report(run: dict) -> list:
    """The printed lines of one run's first turn."""
    turn = run["turns"][0]
    enums = {}
    for agent, enum, _ in turn["calls"]:
        enums.setdefault(agent, enum)
    width = max(len(a) for a in enums)
    lines = ["who each agent may transfer to (transfer_to_agent's enum, as its model was offered it):"]
    lines += [f"  {a:<{width}}  {', '.join(e)}" for a, e in enums.items()]
    capped = turn["answer"] == STOP.format(n=MAX_TRANSFERS)     # the cap answered: the last transfer asked was refused
    for i, (frm, to) in enumerate(turn["transfers"], 1):
        refused = capped and i == len(turn["transfers"])
        lines.append(f"transfer {i}: {frm} -> {to}" + (f"   refused: TransferCap answered before {to} ran"
                                                        if refused else ""))
    writer = f"TransferCap, in {turn['last']}'s place" if capped else turn["last"]
    lines.append(f"answer, written by {writer}: {turn['answer']}")
    lines.append(f"model calls: {len(turn['calls'])} | transfers made: {len(turn['transfers']) - capped} | "
                 f"session state stored after the turn: {run['stored']}")
    return lines


def main(argv=None) -> int:
    """--offline: the shape run twice, with the peer edges and without them. Anything else: exit 2."""
    ap = argparse.ArgumentParser(description="Agent shapes offline: a ping-pong between two ADK desks, and its cap.")
    ap.add_argument("--offline", action="store_true",
                    help="scripted models, no credential, Rs 0 (the only mode so far)")
    args = ap.parse_args(argv)
    if not args.offline:
        print("agent_shapes.py runs offline only so far: python commands/agent_shapes.py --offline "
              "(make agent-shapes OFFLINE=1)", file=sys.stderr)
        return 2
    warnings.filterwarnings("ignore")
    logging.getLogger("google_adk").setLevel(logging.ERROR)    # ADK's notes on a scripted model's missing usage
    print(f"swarm_adk, offline: scripted models, no credential, Rs 0. TransferCap ends a turn after {MAX_TRANSFERS} "
          "transfers.")
    print(f"Q: {QUESTION}")
    for peers, title in ((True, "transfers between the desks allowed (ADK's default)"),
                         (False, "disallow_transfer_to_peers=True on both desks")):
        print(f"\n== {title}")
        for line in report(asyncio.run(swarm_adk(peers))):
            print(line)
    print("\nWith the peer edges gone the loop ran through the root; the cap ended it both times.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
