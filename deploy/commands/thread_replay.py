"""Replay one turn of an exported thread, then fork it, on your own machine (workshop lesson 6.8). Never on the lane.

    python commands/thread_replay.py --offline                  # the fixture thread: no network, no credential, Rs 0
    python commands/thread_replay.py --offline --file thread.json --at 3
    python commands/thread_replay.py --file thread.json [--at STEP] [--fork QUESTION] [--db copy.db]   # Gemini, rag-api
    python commands/thread_replay.py --write-fixture evals/threads/cut_off_turn.json              # how it was made
    make replay [FILE=] [AT=] [OFFLINE=1] [FORK=] [DB=]          # the same, in ~/graph-venv (mk/memory.mk)

The file is what `make thread EXPORT=` wrote (commands/thread_read.py): one conversation's checkpoints along its latest
history, each with its step, source, next and messages. Four things happen, and the lane is touched by none of them:

1. COPY. A local saver gets the thread one checkpoint at a time, each through graph.update_state() with the messages
   that checkpoint added and as the node that would have added them: an input checkpoint as "__input__" (its question
   waits, next __start__), the question as "__start__", a tool result as "tools", a model message as "agent". So every
   step of the copy has the file's step number, next and messages, and the copy is checked against the file step by
   step. The copy is replayed through brains.LangGraphBrain, the kit's own graph, whichever brain wrote the turn:
   create_agent's model node is the LangGraph brain's agent node.
2. REPLAY from AT: graph.invoke(None, the config at AT) - LangGraph resumes the graph from that checkpoint's next. A
   step whose next is tools is a turn the model had asked a tool of when it stopped (a stream closed, an instance
   gone); the replay runs the tool and finishes the turn. From a past step the replay is a branch beside the copy's own
   continuation; when that step is one the graph wrote itself (here, an input checkpoint) LangGraph first saves a
   checkpoint marked source=fork, and from update_state's checkpoints it does not (langgraph 1.2.12,
   pregel/_loop.py:958-971). What the replay produced is compared with what was recorded after AT, if anything: the
   steps (each message's kind and the tools asked for), the sources each search returned, and the answer.
3. FORK from the turn's input checkpoint: graph.update_state(that config, a new question with a new uuid4 id, as
   _turn() gives one) and graph.invoke(None, the fork's config). FORK= is the question; by default the turn's own
   question with "Answer in one sentence." after it.
4. HISTORY: graph.get_state_history() on the copy lists every checkpoint - the copied line, the replay's and the
   fork's - each with the step it follows from.

OFFLINE=1 needs no credential and opens no connection: a socket that would leave the machine is refused, and nothing
mints a token. The model is a script, not a model: the thread's own model messages after AT are played back in order,
then a rule - search for the question, then answer from the first passage, labelled "(offline, scripted)". A search
the thread recorded (the same query, doc_type and top_k) is answered with the passages it recorded; any other search is
answered by the kit's Rs 0 lane - documind_tools.retrieve() on the local profile, its BM25 and evidence gate, over
evals/corpus held in memory, as tools/check_local_lane.py stands Chroma in. A replay of a recorded turn therefore runs
the kit's real graph, tool layer and citation numbering, and must match what was recorded.

Without OFFLINE the turn runs as on the lane: Gemini through shared/profile.build_llm() (location global) and the
lane's rag-api through documind_tools.retrieve() as documind-ui-sa (GOOGLE_CLOUD_PROJECT, RAG_API_URL and
DOCUMIND_IMPERSONATE_SA, which make replay sets). That is a few model calls and searches, priced at list price by the
turn's limits.Meter and printed: the replay costs what a turn costs. The words may differ from the recorded turn's.

The saver is an InMemorySaver; DB=<file> uses SqliteSaver instead, requirements-local.txt's pin
(langgraph-checkpoint-sqlite 3.1.1, the laptop lane's), so the copy and its branches stay in a file to read again.
--write-fixture is how evals/threads/cut_off_turn.json was made: two turns of the kit's LangGraph brain, offline, the
second cut off by closing the stream right after the model asked for retrieve, then thread_read's snapshots() and
export(). commands/tests/test_thread_read.py checks the shipped file against what it writes today.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import json
import os
import socket
import sys
import types
import uuid
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import thread_read as tr  # noqa: E402 - commands/thread_read.py: the export's format, the reader's words

FIXTURE = KIT / "evals" / "threads" / "cut_off_turn.json"
PLACEHOLDER = "documind-ai-YOUR-ID"
NODE = {"model": "agent"}                 # create_agent's model node is the LangGraph brain's agent node
LOOPBACK = ("127.0.0.1", "::1", "localhost")
FIRST = "After how many years of continuous service is gratuity payable?"
SECOND = "Is gratuity payable to a contract employee?"


# ----------------------------------------------------------------------------- the file
def load(path) -> dict:
    """An export, its messages rebuilt with LangChain's messages_from_dict and put back in each checkpoint."""
    from langchain_core.messages import messages_from_dict

    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("format") != tr.FORMAT:
        raise tr.Refused(f"{path} is not a thread export ({tr.FORMAT}): make thread SESSION= EXPORT= writes one")
    by_id = {m.id: m for m in messages_from_dict(doc["messages"])}
    chain = doc["checkpoints"]
    if not chain:
        raise tr.Refused(f"{path} holds no checkpoints")
    for prev, cp in zip(chain, chain[1:]):
        if cp["parent_checkpoint_id"] != prev["checkpoint_id"]:
            raise tr.Refused(f"{path}: step {cp['step']} does not follow step {prev['step']}: an export is one line")
    for cp in chain:
        missing = [i for i in cp["messages"] + cp["input"] if i not in by_id]
        if missing:
            raise tr.Refused(f"{path}: step {cp['step']} names a message the file does not hold ({missing[0]})")
        cp["messages"] = [by_id[i] for i in cp["messages"]]
        cp["input"] = [by_id[i] for i in cp["input"]]
    doc["by_id"] = by_id
    return doc


def turn_of(chain: list, i: int) -> tuple[int, int]:
    """(the index of the turn's input checkpoint, the index of its last checkpoint) for the checkpoint at i."""
    starts = [j for j, cp in enumerate(chain) if cp["source"] == "input"]
    s = max([j for j in starts if j <= i], default=0)
    e = min([j for j in starts if j > i], default=len(chain)) - 1
    return s, e


def default_at(chain: list) -> int:
    """A thread that stopped mid-turn resumes where it stopped; a finished one replays its last turn from its question."""
    if chain[-1]["next"]:
        return len(chain) - 1
    s, _ = turn_of(chain, len(chain) - 1)
    return s + 1 if s + 1 < len(chain) else s


def question_of(chain: list, s: int, e: int):
    """The question of the turn between s and e: the input its input checkpoint holds, or the first person's message."""
    if chain[s]["input"]:
        return chain[s]["input"][-1]
    known = {m.id for m in chain[s]["messages"]}
    return next((m for m in chain[e]["messages"] if m.id not in known and m.type == "human"), None)


# ----------------------------------------------------------------------------- 1. the copy
def as_node(new: list, lane_next: list) -> str:
    """The node a checkpoint's new messages are applied as, so the copy's next is the lane's."""
    if [NODE.get(n, n) for n in dict.fromkeys(lane_next)] == ["agent"]:
        return "tools" if new and new[-1].type == "tool" else "__start__"
    return "agent"                       # next tools, refuse or nothing: the brain's route() reads the model's message


def copy_thread(graph, thread_id: str, chain: list) -> tuple[list, list]:
    """Each checkpoint of the file as one checkpoint of the local saver. Returns (the local configs, the differences)."""
    cfg, configs, problems, prev = {"configurable": {"thread_id": thread_id}}, [], [], []
    for cp in chain:
        if list(dict.fromkeys(cp["next"])) == ["__start__"]:
            cfg = graph.update_state(cfg, {"messages": copy.deepcopy(cp["input"])}, as_node="__input__")
        else:
            known = {m.id for m in prev}
            if not known <= {m.id for m in cp["messages"]}:
                problems.append(f"step {cp['step']}: messages were removed, which a copy made by appending cannot show")
            new = [m for m in cp["messages"] if m.id not in known]
            cfg = graph.update_state(cfg, {"messages": copy.deepcopy(new)}, as_node=as_node(new, cp["next"]))
        snap = graph.get_state(cfg)
        want, got = sorted({NODE.get(n, n) for n in cp["next"]}), sorted(set(snap.next))
        got_ids = [m.id for m in snap.values.get("messages", [])]
        if snap.metadata.get("step") != cp["step"] or got != want or got_ids != [m.id for m in cp["messages"]]:
            problems.append(f"step {cp['step']}: the copy has step {snap.metadata.get('step')}, next {tr._next(got)} and "
                            f"{len(got_ids)} messages; the file has next {tr._next(want)} and {len(cp['messages'])}")
        configs.append(cfg)
        prev = cp["messages"]
    return configs, problems


# ----------------------------------------------------------------------------- offline: a script and the Rs 0 lane
def scripted(play: list):
    """OFFLINE=1's model: the AI messages in `play`, in order, then the rule. A new message each time, with no id and
    no usage, so nothing is billed."""
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import AIMessage
    from langchain_core.outputs import ChatGeneration, ChatResult
    from pydantic import Field

    def rule(messages):
        last = next((m for m in reversed(messages) if m.type != "system"), None)
        if last is None or last.type == "human":
            ask = tr.text_of(last.content) if last is not None else ""
            return AIMessage("", tool_calls=[{"name": "retrieve", "args": {"query": ask},
                                              "id": f"call_{uuid.uuid4().hex[:12]}", "type": "tool_call"}])
        if last.type == "tool":
            cites = tr.citations_of(last) or []
            if cites:
                c = cites[0]
                return AIMessage(f'(offline, scripted) The first passage says: "{tr.short(c.get("quote", ""), 150)}" '
                                 f'[{c.get("n", 1)}]')
            return AIMessage("(offline, scripted) The search found nothing to cite, so the documents give no answer.")
        return AIMessage("(offline, scripted) Nothing further.")

    class Scripted(BaseChatModel):
        play: list = Field(default_factory=list)
        asked: list = Field(default_factory=list)

        @property
        def _llm_type(self) -> str:
            return "documind-replay-script"

        def bind_tools(self, tools, **kwargs):
            return self

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            self.asked.append(len(messages))
            if self.play:
                r = self.play.pop(0)
                msg = AIMessage(content=copy.deepcopy(r.content), tool_calls=copy.deepcopy(r.tool_calls))
            else:
                msg = rule(messages)
            return ChatResult(generations=[ChatGeneration(message=msg)])

    return Scripted(play=list(play))


def recorded_searches(messages: list) -> list:
    """((query, doc_type, top_k), the result as documind_tools.retrieve returned it) for every search the thread holds."""
    asked = {c["id"]: c.get("args") or {} for m in messages if m.type == "ai"
             for c in (getattr(m, "tool_calls", None) or []) if c["name"] == "retrieve"}
    out = []
    for m in messages:
        if m.type != "tool" or m.tool_call_id not in asked:
            continue
        try:
            body = json.loads(tr.text_of(m.content))
        except ValueError:
            continue
        args = asked[m.tool_call_id]
        doc_type = args.get("doc_type")
        key = (args.get("query", ""), None if doc_type in (None, "", "all") else doc_type, int(args.get("top_k") or 5))
        if not isinstance(body, dict):
            continue
        if body.get("error"):        # tools.search() turns this back into the error result the model read
            result = {"error": "document retrieval is unavailable", "citations": [], "answerable": False,
                      "confidence": "low"}
        else:
            result = {"citations": [{k: v for k, v in c.items() if k != "n"} for c in body.get("citations", [])],
                      "answerable": body.get("answerable", False), "confidence": body.get("confidence", "low")}
        out.append((key, result))
    return out


class _Corpus:
    """The Rs 0 lane's store, held in memory: Chroma's get(where=...) over the rows shared/local_corpus.py would write
    (the same stand-in tools/check_local_lane.py uses)."""

    def __init__(self, tenant: str):
        from shared import local_corpus as lc
        self.rows = lc.chunks_for(tenant)
        self._collection = types.SimpleNamespace(count=lambda: len(self.rows))

    def get(self, where=None, include=None):
        conds = [where] if "$and" not in (where or {}) else where["$and"]

        def ok(c, k, v):
            return c.get(k) in v["$in"] if isinstance(v, dict) and "$in" in v else c.get(k) == v
        keep = [c for c in self.rows if all(ok(c, k, v) for cond in conds for k, v in cond.items())]
        return {"ids": [c["chunk_id"] for c in keep], "documents": [c["text"] for c in keep],
                "metadatas": [{"tenant_id": c["tenant_id"], "doc_type": c["doc_type"], "page": c["page_start"],
                               "source_uri": c["source_uri"], "chunk_id": c["chunk_id"]} for c in keep]}


@contextlib.contextmanager
def offline(messages: list):
    """No network, no token, the script's searches: documind_tools.retrieve answers a recorded search as recorded and
    any other from the kit's Rs 0 lane. Everything it patches is put back on the way out."""
    _kit_on_path()
    import shared.profile as profile
    from shared import documind_tools as dt
    from shared import local_corpus as lc

    recorded, stores, real = recorded_searches(messages), {}, dt.retrieve

    def retrieve(query, tenant_id="", top_k=5, doc_type=None, assertion=None, brain=None, passages=False):
        key = (query, None if doc_type in (None, "", "all") else doc_type, int(top_k or 5))
        hit = next((r for k, r in recorded if k == key), None)
        if hit is not None:
            return copy.deepcopy(hit)
        if tenant_id not in stores:
            stores[tenant_id] = _Corpus(tenant_id)
        profile.build_store = lambda embeddings=None: stores[tenant_id]
        return real(query, tenant_id=tenant_id, top_k=top_k, doc_type=doc_type, assertion=assertion, brain=brain,
                    passages=passages)

    def no_token(audience):
        raise OSError("offline: no identity token is minted")

    saved = {"retrieve": dt.retrieve, "PROFILE": dt.PROFILE, "_id_token": dt._id_token}
    saved_store, saved_project = profile.build_store, lc.PROJECT_ID
    dt.retrieve, dt.PROFILE, dt._id_token, lc.PROJECT_ID = retrieve, "local", no_token, PLACEHOLDER
    try:
        with no_network():
            yield
    finally:
        for k, v in saved.items():
            setattr(dt, k, v)
        profile.build_store, lc.PROJECT_ID = saved_store, saved_project


@contextlib.contextmanager
def no_network():
    """Every socket that would leave the machine is refused, and every name but loopback's goes unresolved."""
    real = (socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo)

    def far(address) -> bool:
        return not (isinstance(address, tuple) and str(address[0]) in LOOPBACK)

    def connect(sock, address):
        if far(address):
            raise OSError(f"offline: refused a connection to {address!r}")
        return real[0](sock, address)

    def connect_ex(sock, address):
        if far(address):
            raise OSError(f"offline: refused a connection to {address!r}")
        return real[1](sock, address)

    def getaddrinfo(host, *args, **kwargs):
        if str(host) not in LOOPBACK:
            raise OSError(f"offline: refused to resolve {host!r}")
        return real[2](host, *args, **kwargs)

    socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo = connect, connect_ex, getaddrinfo
    try:
        yield
    finally:
        socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo = real


def _kit_on_path() -> None:
    tr._kit_on_path()


# ----------------------------------------------------------------------------- 2-4. replay, fork, history
def run(graph, cfg: dict, ctx: dict):
    """graph.invoke(None, cfg): resume from cfg's checkpoint. Returns (the final values, what stopped it, if anything)."""
    import limits
    from langgraph.errors import GraphRecursionError

    try:
        return graph.invoke(None, config={**cfg, "recursion_limit": limits.recursion_limit()}, context=ctx), None
    except GraphRecursionError:              # the framework's backstop, as the brains catch it
        return graph.get_state({"configurable": {"thread_id": cfg["configurable"]["thread_id"]}}).values, "recursion_limit"


def ledger_of(chain: list, s: int, i: int) -> list:
    """The citations the turn had numbered by step i, so a search after it numbers on from them (tools._number)."""
    before = {m.id for m in chain[s]["messages"]}
    got: dict = {}
    for m in chain[i]["messages"]:
        if m.id not in before and m.type == "tool":
            for c in tr.citations_of(m) or []:
                if c.get("n") is not None:
                    got.setdefault(c["n"], dict(c))
    return [got[n] for n in sorted(got)]


def shape(messages: list) -> dict:
    """What a replay is compared on: each message's kind and the tools it asked for, the sources each search returned,
    and the answer."""
    steps, sources = [], []
    for m in messages:
        if m.type == "ai" and getattr(m, "tool_calls", None):
            steps.append("ai asks " + "+".join(c["name"] for c in m.tool_calls))
        else:
            steps.append(m.type)
        if m.type == "tool":
            sources.append([c.get("chunk_id") for c in tr.citations_of(m) or []])
    answer = next((tr.text_of(m.content) for m in reversed(messages)
                   if m.type == "ai" and not getattr(m, "tool_calls", None)), None)
    return {"steps": steps, "sources": sources, "answer": answer}


def compare(recorded: list, replayed: list) -> str:
    a, b = shape(recorded), shape(replayed)
    n = len(a["steps"])
    if a["answer"] is None and b["answer"] is not None and b["steps"][:n] == a["steps"] and n < len(b["steps"]) \
            and b["sources"][:len(a["sources"])] == a["sources"]:
        # A recording cut off mid-turn, matched step for step and then finished: nothing the recording holds differs
        # (13 October 2026: this printed "differs", for the steps, sources and answer it never reached).
        found = sum(map(len, b["sources"]))
        return (f"the replay matches the recorded turn as far as the recording goes: the same steps "
                f"({', '.join(a['steps'])}), then it finished the turn ({', '.join(b['steps'][n:])}), with {found} "
                f"citation{'s' if found != 1 else ''} and an answer")
    same = {k: a[k] == b[k] for k in a}
    found = sum(map(len, b["sources"]))
    parts = [f"{'the same' if same['steps'] else 'different'} steps ({', '.join(b['steps'])})",
             "no search" if same["sources"] and not b["sources"] else
             f"{'the same' if same['sources'] else 'different'} sources ({found} citation{'s' if found != 1 else ''})",
             f"{'the same' if same['answer'] else 'a different'} answer"]
    head = "the replay matches the recorded turn" if all(same.values()) else "the replay differs from the recorded turn"
    return f"{head}: " + ", ".join(parts)


def _ids(saver, thread_id: str) -> list:
    return [t.config["configurable"]["checkpoint_id"] for t in saver.list({"configurable": {"thread_id": thread_id}})]


def replay(doc: dict, *, at: str | None = None, fork: str | None = None, offline_mode: bool = False, saver=None,
           source: str = "") -> dict:
    """Copy, replay from AT, fork from its turn's input, and list the history. Returns what each step produced."""
    chain, thread_id = doc["checkpoints"], doc["thread_id"]
    if at is None:
        i = default_at(chain)
    else:
        picked = tr.pick(chain, at)
        i = next(k for k, cp in enumerate(chain) if cp is picked)
    if not chain[i]["next"]:
        can = ", ".join(str(cp["step"]) for cp in chain if cp["next"])
        raise tr.Refused(f"step {chain[i]['step']} ends its turn (next is empty): nothing runs from it. Steps that "
                         f"can be replayed: {can}")
    s, e = turn_of(chain, i)
    question = question_of(chain, s, e)
    asked = tr.text_of(question.content) if question is not None else ""
    fork_q = fork or (f"{asked} Answer in one sentence." if asked else "Answer in one sentence.")
    known = {m.id for m in chain[i]["messages"]}
    recorded = [m for m in chain[e]["messages"] if m.id not in known] if e > i else []
    turns = sum(1 for cp in chain if cp["source"] == "input")
    tenant, user = doc["tenant"], doc["user"]

    print(f"thread {thread_id}")
    print(f"  from {source or 'the file'}: {len(chain)} checkpoints, steps {chain[0]['step']} to {chain[-1]['step']}, "
          f"{turns} turn{'s' if turns != 1 else ''}")
    if offline_mode:
        print("offline: the model is a script (the thread's own model messages played back, then a rule), a search the "
              "thread\n  recorded is answered as recorded and any other by the kit's Rs 0 lane over evals/corpus; "
              "no network, Rs 0")
    else:
        print(f"on your machine: Gemini ({os.environ.get('CHAT_MODEL', 'gemini-3.6-flash')}, location global) and your "
              f"lane's rag-api as {os.environ.get('DOCUMIND_IMPERSONATE_SA', '')}")

    stack = contextlib.ExitStack()
    with stack:
        if offline_mode:
            stack.enter_context(offline(list(doc["by_id"].values())))
        _kit_on_path()
        import brains
        import limits
        from langchain_core.messages import HumanMessage

        if saver is None:
            from langgraph.checkpoint.memory import InMemorySaver
            saver = InMemorySaver()
        play = [m for m in recorded if m.type == "ai"]
        brain = brains.LangGraphBrain(saver, llm=scripted(play) if offline_mode else None)
        fork_brain = brains.LangGraphBrain(saver, llm=scripted([])) if offline_mode else brain

        # 1. the copy
        configs, problems = copy_thread(brain.graph, thread_id, chain)
        copied = set(_ids(saver, thread_id))
        print(f"\n1. the copy: {len(copied)} checkpoints in a local {type(saver).__name__}, one update_state() each; "
              + ("every step's number, next and messages are the file's" if not problems else
                 f"{len(problems)} step{'s' if len(problems) != 1 else ''} differ:"))
        for p in problems:
            print(f"     {p}")

        # 2. the replay
        nxt = tr._next([NODE.get(n, n) for n in dict.fromkeys(chain[i]["next"])])
        print(f"\n2. replay from step {chain[i]['step']} (next {nxt}): graph.invoke(None, the config at step "
              f"{chain[i]['step']}), through the kit's LangGraph brain")
        print(f"   the turn's question: {tr.short(asked, 100)!r}")
        if i == e:                           # the recorded turn has nothing after AT: it stopped there, unfinished
            last = chain[i]["messages"][-1] if chain[i]["messages"] else None
            if nxt == "tools" and last is not None and last.type == "ai":
                why = f"the model had asked {tr.asks(last)} and the tool never ran"
            elif nxt == "agent":
                why = ("a tool's result was saved and the model never read it" if last is not None and last.type == "tool"
                       else "the question was saved and the model was never called")
            else:
                why = "its input was saved and the turn never began" if nxt == "__start__" else f"next was {nxt}"
            print(f"   step {chain[i]['step']} is where the recorded turn stopped: {why}")
        meter = limits.Meter(model=brains.MODEL)
        ctx = {"tenant_id": tenant, "user_id": user, "assertion": "", "brain": "langgraph",
               "cited": ledger_of(chain, s, i), "meter": meter}
        values, stopped = run(brain.graph, configs[i], ctx)
        replay_ids = set(_ids(saver, thread_id)) - copied
        replayed = [m for m in values.get("messages", []) if m.id not in known]
        for m in replayed:
            print(f"     + {tr.describe(m, 96)}")
        if stopped:
            print(f"   stopped by the framework's {stopped}")
        if recorded:
            print(f"   {compare(recorded, replayed)}")
        else:
            print(f"   nothing was recorded after step {chain[i]['step']}: the replay finished the turn: "
                  f"{len(replayed)} message{'s' if len(replayed) != 1 else ''}, "
                  f"{meter.model_calls} model call{'s' if meter.model_calls != 1 else ''}")

        # 3. the fork
        print(f"\n3. fork from step {chain[s]['step']}, the turn's input: graph.update_state(the config at step "
              f"{chain[s]['step']}, a new question), then graph.invoke(None, the fork)")
        print(f"   the fork's question: {tr.short(fork_q, 100)!r}")
        before = set(_ids(saver, thread_id))
        fcfg = brain.graph.update_state(configs[s], {"messages": [HumanMessage(fork_q, id=str(uuid.uuid4()))]},
                                        as_node="__start__")
        fork_meter = limits.Meter(model=brains.MODEL)
        fvalues, fstopped = run(fork_brain.graph, fcfg, {"tenant_id": tenant, "user_id": user, "assertion": "",
                                                         "brain": "langgraph", "cited": [], "meter": fork_meter})
        fork_ids = set(_ids(saver, thread_id)) - before
        base = {m.id for m in chain[s]["messages"]}
        for m in [m for m in fvalues.get("messages", []) if m.id not in base]:
            print(f"     + {tr.describe(m, 96)}")
        if fstopped:
            print(f"   stopped by the framework's {fstopped}")

        # 4. the history
        hist = list(brain.graph.get_state_history({"configurable": {"thread_id": thread_id}}))[::-1]
        step_of = {h.config["configurable"]["checkpoint_id"]: h.metadata.get("step") for h in hist}
        parents = {(h.parent_config or {}).get("configurable", {}).get("checkpoint_id") for h in hist}
        ends = len(set(step_of) - parents)              # a branch ends at a checkpoint no other one follows
        print(f"\n4. graph.get_state_history(thread): {len(hist)} checkpoints, in {ends} branches")
        print(f"     {'branch':9}  {'step':>4}  {'source':6}  {'next':10}  {'msgs':>4}  {'from':>4}  the newest message")
        for h in hist:
            cid = h.config["configurable"]["checkpoint_id"]
            parent = (h.parent_config or {}).get("configurable", {}).get("checkpoint_id")
            branch = "copy" if cid in copied else "replay" if cid in replay_ids else "fork" if cid in fork_ids else "?"
            msgs = h.values.get("messages", [])
            print(f"     {branch:9}  {str(h.metadata.get('step')):>4}  {str(h.metadata.get('source')):6}  "
                  f"{tr._next(list(h.next)):10}  {len(msgs):>4}  {str(step_of.get(parent, '-')) if parent else '-':>4}  "
                  f"{tr.describe(msgs[-1], 56) if msgs else '-'}")
        spent = meter.spent_inr() + fork_meter.spent_inr()
        calls = meter.model_calls + fork_meter.model_calls
        print(f"\nonly the local copy was written; the lane never is. Model calls: the replay {meter.model_calls}, the "
              f"fork {fork_meter.model_calls}; " + ("Rs 0 (a script, not a model)" if offline_mode else
                                                     f"Rs {spent:.2f} at list price with the searches (limits.Meter)"))
        return {"copied": len(copied), "problems": problems, "replayed": replayed, "recorded": recorded,
                "replay_ids": replay_ids, "fork_ids": fork_ids, "history": hist, "model_calls": calls,
                "fork_messages": fvalues.get("messages", []), "stopped": stopped or fstopped}


# ----------------------------------------------------------------------------- the fixture
def write_fixture(path) -> dict:
    """Two turns of the kit's LangGraph brain on an InMemorySaver, offline; the second stops where its stream was closed
    right after the model asked for retrieve, so its last checkpoint waits at next tools with the call open. Exported
    the way thread_read exports a lane thread."""
    thread_id = f"acme:documind-ui-sa@{PLACEHOLDER}.iam.gserviceaccount.com:lesson68"
    with offline([]):
        _kit_on_path()
        import brains
        import limits
        from langgraph.checkpoint.memory import InMemorySaver

        saver = InMemorySaver()
        brain = brains.LangGraphBrain(saver, llm=scripted([]))
        cfg = {"configurable": {"thread_id": thread_id}}
        who = {"tenant_id": "acme", "user_id": thread_id.split(":")[1], "assertion": "", "brain": "langgraph"}
        brain.answer(FIRST, config=cfg, context=dict(who))
        _, state, ctx = brains._turn(SECOND, dict(who))      # what LangGraphBrain.answer() starts a turn with
        stream = brain.graph.stream(state, config={**cfg, "recursion_limit": limits.recursion_limit()}, context=ctx,
                                    stream_mode="updates")
        for update in stream:
            if any(getattr(m, "tool_calls", None) for m in (update.get("agent") or {}).get("messages", [])):
                break                        # the client goes: the tool call is saved, the tool never runs
        stream.close()
        tuples = list(saver.list(cfg))[::-1]
    doc = tr.export(thread_id, tr.snapshots(tuples))
    doc["written_by"] = "commands/thread_replay.py --write-fixture"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return doc


# ----------------------------------------------------------------------------- the command
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--file", help="a thread export (make thread EXPORT=); with --offline, "
                                   f"{FIXTURE.relative_to(KIT).as_posix()} by default")
    ap.add_argument("--at", help="the step to replay from (a step number or a checkpoint id)")
    ap.add_argument("--fork", help="the fork's question (default: the turn's own, asked for one sentence)")
    ap.add_argument("--offline", action="store_true", help="a script and the Rs 0 lane: no network, no credential")
    ap.add_argument("--db", help="keep the copy in this new SQLite file (SqliteSaver) instead of in memory")
    ap.add_argument("--write-fixture", metavar="PATH", help="write the offline cut-off thread, as the fixture was made")
    a = ap.parse_args(argv)
    # pydantic warns that the runtime context the tools are handed (a dict holding the turn's Meter) is not its schema's
    # None when it serializes the tool call: noise here, as in every lesson cell that runs the brains.
    warnings.filterwarnings("ignore", category=UserWarning)
    try:
        if a.write_fixture:
            doc = write_fixture(a.write_fixture)
            print(f"wrote {a.write_fixture}: {len(doc['checkpoints'])} checkpoints, the last at next "
                  f"{tr._next(doc['checkpoints'][-1]['next'])}")
            return 0
        if not a.file and not a.offline:
            raise tr.Refused("a lane replay needs FILE=, the file make thread SESSION= EXPORT= wrote (or OFFLINE=1 for "
                             "the fixture thread)")
        if not a.offline:
            need = [k for k in ("GOOGLE_CLOUD_PROJECT", "RAG_API_URL", "DOCUMIND_IMPERSONATE_SA") if not os.environ.get(k)]
            if need:
                raise tr.Refused(f"a replay with Gemini and your rag-api needs {', '.join(need)}: make replay sets them "
                                 "from PROJECT, or use OFFLINE=1")
        path = Path(a.file) if a.file else FIXTURE
        shown = a.file or FIXTURE.relative_to(KIT).as_posix()       # the fixture by its kit path, not this machine's
        doc = load(path)
        with contextlib.ExitStack() as stack:
            saver = None
            if a.db:
                if Path(a.db).exists():
                    raise tr.Refused(f"{a.db} exists: DB= names a new file, so a copy never lands on another")
                try:
                    from langgraph.checkpoint.sqlite import SqliteSaver
                except ImportError:
                    raise tr.Refused("DB= needs SqliteSaver, requirements-local.txt's langgraph-checkpoint-sqlite==3.1.1: "
                                     "pip install -r services/chat/requirements-local.txt, or leave DB= empty") from None
                saver = stack.enter_context(SqliteSaver.from_conn_string(a.db))
            replay(doc, at=a.at, fork=a.fork, offline_mode=a.offline, saver=saver, source=shown)
            if a.db:
                print(f"the copy and both branches are in {a.db} (SqliteSaver's checkpoints table)")
    except tr.Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
