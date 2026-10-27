"""Read a conversation's checkpoints back from the lane, step by step (workshop lesson 6.8). Reads only.

    python commands/thread_read.py --project P --email E                      # E's threads, one row per session
    python commands/thread_read.py --project P --email E --session S          # one thread, a row per step
    python commands/thread_read.py --project P --email E --session S --at 3   # and the messages saved at step 3
    python commands/thread_read.py --project P --email E --session S --export thread.json   # for thread_replay.py
    make thread [EMAIL=] [SESSION=] [AT=] [EXPORT=] [TENANT=]                 # the same, in ~/graph-venv (mk/memory.mk)

The chat service keeps every conversation in Cloud SQL through langgraph-checkpoint-postgres (agent.py's
build_checkpointer), one thread per tenant:user:session (agent.py's thread_config). Lesson 6.6 counted the rows; this
reads them back the way LangGraph itself would:

    checkpoints        one row per step: the checkpoint as JSONB, with the plain values inline (a string, a number, a
                       boolean, None) and every channel's version; the step, its source (input, loop, update) and the
                       rest of the metadata
    checkpoint_blobs   one row per (channel, version) of every other value - the messages list, again in full at each
                       new version - as (type, blob), written by the pinned serializer's dumps_typed()
    checkpoint_writes  what a step's tasks wrote before the next checkpoint: a task's error, for instance

The schema and the decode are langgraph-checkpoint-postgres 3.1.2's: the tables in base.py's MIGRATIONS (:47-76), a
checkpoint's values rebuilt as `{**inline, **blobs}` with type "empty" skipped (__init__.py:559-599, base.py:375-384),
each blob through JsonPlusSerializer.loads_typed. One difference, on purpose: the serializer here is strict
(allowed_msgpack_modules=None), so a blob may revive only the types langgraph lists as safe - LangChain's messages,
Send, datetimes - and anything else comes back as plain data. Reading a database never imports a module it names.

What a step's `next` is - the node that runs from it - is not stored anywhere. LangGraph works it out from the
checkpoint's versions and the graph's edges, so each checkpoint is read through the graph of the brain that wrote it:
brains.LangChainBrain's create_agent graph for a checkpoint whose metadata says ls_integration=langchain_create_agent
(langchain 1.4.0, agents/factory.py:1832), brains.LangGraphBrain's for the rest. graph.get_state() at that checkpoint
gives what get_state_history() would: its messages, next, metadata and any task's error. No model is called; the
graphs are built over a saver that only reads.

HOW IT CONNECTS: as the operator, the way lesson 6.6's cells do - the DSN from Secret Manager into memory (gcloud
secrets versions access), the instance's connection name, the Cloud SQL Python Connector with pg8000 on your own
credentials - and then `SET default_transaction_read_only = on` before the first query, so not one statement of this
session can write. The password is never printed. The ADK brain keeps its sessions apart (6.6) and the direct brain
keeps nothing, so a thread here holds the langchain and langgraph brains' turns; a Desk thread (desk~ sessions,
desk_graph.py) is listed and not decoded.

A thread is read along its latest history: from its newest checkpoint back through each parent. A checkpoint off that
line means the thread branched on the lane - two turns started from one checkpoint, which nothing in the service
prevents yet - and is counted, not decoded. --export writes that line for commands/thread_replay.py: each checkpoint's
step, source, brain, next, metadata and the ids of its messages, the input an input checkpoint holds, and every
message once, in LangChain's messages_to_dict form.

Needs the chat image's pins (services/chat/requirements.txt) and, for the lane, cloud-sql-python-connector[pg8000]
1.22.0 and pg8000 1.31.5, as lesson 6.6's venv cell installs them; commands/graph-venv.sh does both for make thread.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import json
import re
import shutil
import subprocess
import sys
import warnings
from pathlib import Path
from urllib.parse import unquote, urlparse

KIT = Path(__file__).resolve().parents[1]
FORMAT = "documind-thread/1"
SESSION = re.compile(r"^[A-Za-z0-9_-]{1,64}$")           # agent.ChatRequest.session_id's pattern
DESK = "desk~"                                            # desk_graph.SESSION_PREFIX: the routed Desk's threads
CREATE_AGENT = "langchain_create_agent"                   # the metadata create_agent stamps on its checkpoints
SECRET, INSTANCE = "documind-checkpoint-dsn", "documind-checkpoint"   # terraform/cloudsql.tf

READ_ONLY = "SET default_transaction_read_only = on"
SQL = {
    "threads": "SELECT thread_id, count(*), count(*) FILTER (WHERE metadata->>'source' = 'input'), "
               "max((metadata->>'step')::int), max(checkpoint->>'ts') FROM checkpoints "
               "WHERE checkpoint_ns = '' AND split_part(thread_id, ':', 2) = %s GROUP BY thread_id ORDER BY 5 DESC",
    "find": "SELECT DISTINCT thread_id FROM checkpoints WHERE checkpoint_ns = '' "
            "AND split_part(thread_id, ':', 2) = %s AND split_part(thread_id, ':', 3) = %s",
    "checkpoints": "SELECT checkpoint_id, parent_checkpoint_id, checkpoint::text, metadata::text FROM checkpoints "
                   "WHERE thread_id = %s AND checkpoint_ns = '' ORDER BY checkpoint_id",
    "blobs": "SELECT channel, version, type, blob FROM checkpoint_blobs WHERE thread_id = %s AND checkpoint_ns = ''",
    "writes": "SELECT checkpoint_id, task_id, channel, type, blob FROM checkpoint_writes "
              "WHERE thread_id = %s AND checkpoint_ns = '' ORDER BY checkpoint_id, task_id, idx",
}


class Refused(Exception):
    """A request this reader turns down, with the reason to print."""


# ----------------------------------------------------------------------------- the lane, read only
def _gcloud(project: str, *args: str) -> str:
    exe = shutil.which("gcloud") or "gcloud"
    try:
        return subprocess.run([exe, *args, "--project", project], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        said = (getattr(exc, "stderr", "") or str(exc)).strip().splitlines()
        raise Refused(f"gcloud {' '.join(args[:3])} failed: {said[-1] if said else exc}") from None


@contextlib.contextmanager
def lane(project: str, gcloud=_gcloud, connector=None):
    """A query function on the lane's checkpoint database, as the operator, in a session that cannot write: q(sql, *args)
    returns the rows. Lesson 6.6's cell, as a function: the DSN read into memory, the connector on your credentials."""
    dsn = urlparse(gcloud(project, "secrets", "versions", "access", "latest", "--secret", SECRET))
    instance = gcloud(project, "sql", "instances", "describe", INSTANCE, "--format", "value(connectionName)")
    if connector is None:
        from google.cloud.sql.connector import Connector as connector
    with connector() as conn:
        db = conn.connect(instance, "pg8000", user=dsn.username, password=unquote(dsn.password or ""),
                          db=dsn.path.lstrip("/"))
        try:
            db.autocommit = True                   # each statement its own transaction, each one read only
            cur = db.cursor()
            cur.execute(READ_ONLY, ())             # a tuple, empty or not: pg8000 takes len() of it (6.6's note)

            def q(sql: str, *args):
                if not sql.lstrip().upper().startswith("SELECT"):
                    raise Refused(f"thread_read runs SELECT statements only: {sql[:40]}")
                cur.execute(sql, args)
                return cur.fetchall()

            q.label = f"{instance}, database {dsn.path.lstrip('/')}, as {dsn.username} (read only)"
            yield q
        finally:
            db.close()


def threads(q, email: str) -> list[dict]:
    """The person's threads, one per session, the latest written first."""
    out = []
    for thread_id, n, turns, step, ts in q(SQL["threads"], email):
        tenant, _, session = thread_id.split(":", 2)
        out.append({"thread_id": thread_id, "tenant": tenant, "session": session, "checkpoints": int(n),
                    "turns": int(turns), "last_step": step, "last_write": ts or "",
                    "kind": "desk" if session.startswith(DESK) else "chat"})
    return out


def find(q, email: str, session: str, tenant: str | None = None) -> str:
    """The thread id of the person's session: tenant:email:session, the tenant looked up unless given."""
    if ":" in email or not email:
        raise Refused("EMAIL must be one address, with no ':' (agent.py's thread_config refuses one)")
    if session.startswith(DESK):
        raise Refused(f"{session} is a Desk thread (services/chat/desk_graph.py): this reader decodes the chat "
                      "brains' threads")
    if not SESSION.match(session):
        raise Refused(f"SESSION must match the chat's session_id pattern {SESSION.pattern}")
    if tenant:
        return f"{tenant}:{email}:{session}"
    found = sorted(t for (t,) in q(SQL["find"], email, session))
    if not found:
        raise Refused(f"no thread for {email} with session {session}: run without SESSION to list the sessions")
    if len(found) > 1:
        tenants = ", ".join(t.split(":", 1)[0] for t in found)
        raise Refused(f"session {session} is in {len(found)} tenants' threads ({tenants}): name one with TENANT=")
    return found[0]


def rows(q, thread_id: str) -> tuple[list, list, list]:
    """The thread's rows as stored: checkpoints (oldest first), blobs and pending writes."""
    return q(SQL["checkpoints"], thread_id), q(SQL["blobs"], thread_id), q(SQL["writes"], thread_id)


# ----------------------------------------------------------------------------- decoding, as the pinned library does
def serializer():
    """The pinned JsonPlusSerializer, strict: only the types langgraph lists as safe are revived."""
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
    return JsonPlusSerializer(allowed_msgpack_modules=None)


def _bytes(value) -> bytes:
    return bytes(value) if isinstance(value, (bytes, bytearray, memoryview)) else value


def decode(thread_id: str, checkpoint_rows: list, blob_rows: list, write_rows: list, serde=None) -> list:
    """CheckpointTuples, oldest first, from the three tables' rows: a checkpoint's values are its inline values plus the
    blob of each channel at the version the checkpoint names (PostgresSaver._load_checkpoint_tuple), and its pending
    writes are the writes stored against its id, in task and index order."""
    from langgraph.checkpoint.base import CheckpointTuple

    serde = serde or serializer()
    blobs = {(ch, ver): (typ, _bytes(blob)) for ch, ver, typ, blob in blob_rows}
    decoded: dict = {}

    def value(channel, version):
        if (channel, version) not in decoded:
            typ, blob = blobs[(channel, version)]
            decoded[(channel, version)] = serde.loads_typed((typ, blob))
        return copy.deepcopy(decoded[(channel, version)])

    writes: dict = {}
    for cid, task_id, channel, typ, blob in write_rows:
        writes.setdefault(cid, []).append((task_id, channel, serde.loads_typed((typ, _bytes(blob)))))
    out = []
    for cid, parent, checkpoint, metadata in checkpoint_rows:
        checkpoint = json.loads(checkpoint) if isinstance(checkpoint, str) else checkpoint
        metadata = json.loads(metadata) if isinstance(metadata, str) else (metadata or {})
        if checkpoint.get("v", 4) < 4:
            raise Refused(f"checkpoint {cid} is format v{checkpoint.get('v')}, older than this kit's langgraph writes")
        values = dict(checkpoint.get("channel_values") or {})
        for channel, version in (checkpoint.get("channel_versions") or {}).items():
            if (channel, version) in blobs and blobs[(channel, version)][0] != "empty":
                values[channel] = value(channel, version)
        out.append(CheckpointTuple(_config(thread_id, cid), {**checkpoint, "channel_values": values}, metadata,
                                   _config(thread_id, parent) if parent else None, writes.get(cid, [])))
    return out


def _config(thread_id: str, checkpoint_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id, "checkpoint_ns": "", "checkpoint_id": checkpoint_id}}


def latest_line(tuples: list) -> tuple[list, list]:
    """(the line from the root to the newest checkpoint, the checkpoints off it). Checkpoint ids sort by time."""
    if not tuples:
        return [], []
    by_id = {t.config["configurable"]["checkpoint_id"]: t for t in tuples}
    line, cid = [], max(by_id)
    while cid is not None and cid in by_id:
        line.append(by_id[cid])
        parent = by_id[cid].parent_config
        cid = parent["configurable"]["checkpoint_id"] if parent else None
    line.reverse()
    on = {t.config["configurable"]["checkpoint_id"] for t in line}
    return line, [t for t in tuples if t.config["configurable"]["checkpoint_id"] not in on]


def brain_of(metadata: dict) -> str:
    return "langchain" if (metadata or {}).get("ls_integration") == CREATE_AGENT else "langgraph"


def _kit_on_path() -> None:
    for p in (str(KIT / "services" / "chat"), str(KIT)):
        if p not in sys.path:
            sys.path.insert(0, p)


def _read_only_saver(tuples: list):
    """A checkpointer over decoded tuples that serves reads and refuses every write."""
    from langgraph.checkpoint.base import BaseCheckpointSaver

    class ReadOnly(BaseCheckpointSaver):
        def __init__(self):
            super().__init__(serde=serializer())
            self.by_id = {t.config["configurable"]["checkpoint_id"]: t for t in tuples}

        def get_tuple(self, config):
            cid = config["configurable"].get("checkpoint_id") or (max(self.by_id) if self.by_id else None)
            return copy.deepcopy(self.by_id[cid]) if cid in self.by_id else None

        def list(self, config, *, filter=None, before=None, limit=None):
            for cid in sorted(self.by_id, reverse=True)[:limit]:
                yield copy.deepcopy(self.by_id[cid])

        def put(self, *args, **kwargs):
            raise Refused("a thread read back from the lane is read only")

        put_writes = put

    return ReadOnly()


def kit_graphs(saver) -> dict:
    """The kit's two LangGraph brains' graphs on `saver`. Built to be read, so the model is a stand-in never called."""
    _kit_on_path()
    import brains
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel

    class NeverCalled(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs):
            return self

    llm = NeverCalled(responses=[])
    return {"langgraph": brains.LangGraphBrain(saver, llm=llm).graph,
            "langchain": brains.LangChainBrain(saver, llm=llm).agent}


def snapshots(tuples: list) -> list[dict]:
    """Each checkpoint as graph.get_state() reads it at its id, through the graph of the brain that wrote it."""
    graphs = kit_graphs(_read_only_saver(tuples))
    out = []
    for t in tuples:
        brain = brain_of(t.metadata)
        snap = graphs[brain].get_state(t.config)
        start = t.checkpoint["channel_values"].get("__start__")
        waiting = tuple(snap.next) == ("__start__",) and isinstance(start, dict)
        out.append({"checkpoint_id": t.config["configurable"]["checkpoint_id"],
                    "parent_checkpoint_id": t.parent_config["configurable"]["checkpoint_id"] if t.parent_config else None,
                    "step": t.metadata.get("step"), "source": t.metadata.get("source"), "brain": brain,
                    "next": list(snap.next), "created_at": snap.created_at, "metadata": dict(t.metadata),
                    "messages": list(snap.values.get("messages", [])),
                    "input": list(start.get("messages") or []) if waiting else [],
                    "errors": [f"{task.name}: {task.error}" for task in snap.tasks if task.error]})
    return out


def export(thread_id: str, steps: list[dict], left_out: int = 0) -> dict:
    """The thread as one JSON document: each checkpoint with its messages by id, and every message once."""
    from langchain_core.messages import messages_to_dict

    seen, messages, cps = set(), [], []
    for s in steps:
        for m in s["input"] + s["messages"]:
            if m.id is None:
                raise Refused(f"step {s['step']}: a message with no id cannot be referenced")
            if m.id not in seen:
                seen.add(m.id)
                messages.append(m)
        cps.append({**{k: s[k] for k in ("checkpoint_id", "parent_checkpoint_id", "step", "source", "brain", "next",
                                         "created_at", "metadata")},
                    "messages": [m.id for m in s["messages"]], "input": [m.id for m in s["input"]]})
    tenant, user, session = thread_id.split(":", 2)
    return {"format": FORMAT, "thread_id": thread_id, "tenant": tenant, "user": user, "session": session,
            "written_by": "commands/thread_read.py", "left_out": left_out, "checkpoints": cps,
            "messages": json.loads(json.dumps(messages_to_dict(messages), default=str))}


# ----------------------------------------------------------------------------- printing
def text_of(content) -> str:
    """A message's text: Gemini 3 can send a list of blocks where older models sent a string (as brains._summary)."""
    if isinstance(content, str):
        return content
    return "".join(b if isinstance(b, str) else b.get("text", "") for b in content or []
                   if isinstance(b, str) or b.get("type") == "text")


def short(text: str, width: int = 80) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= width else text[:width - 3].rstrip() + "..."


def citations_of(message) -> list | None:
    """The citations a retrieve result carries, or None when its content is not a search result."""
    try:
        body = json.loads(text_of(message.content))
    except (TypeError, ValueError):
        return None
    return body.get("citations") if isinstance(body, dict) and isinstance(body.get("citations"), list) else None


def asks(m) -> str:
    """The tool calls a model message makes, as name(arg=value, ...)."""
    return ", ".join(f"{c['name']}({', '.join(f'{k}={v!r}' for k, v in (c.get('args') or {}).items())})"
                     for c in getattr(m, "tool_calls", None) or [])


def describe(m, width: int = 80) -> str:
    """One line for one message: who wrote it, and what it says or asks."""
    if m.type == "ai" and getattr(m, "tool_calls", None):
        return "ai     asks " + short(asks(m), width - 12)
    if m.type == "tool":
        if getattr(m, "status", "success") == "error":
            return f"tool   {m.name} refused: " + short(text_of(m.content), width - 20)
        cites = citations_of(m)
        if cites is not None:
            try:
                body = json.loads(text_of(m.content))
            except ValueError:
                body = {}
            if body.get("error"):
                return f"tool   {m.name}: " + short(body["error"], width - 10)
            ns = [c.get("n") for c in cites if c.get("n") is not None]
            span = f" [{min(ns)}]-[{max(ns)}]" if len(ns) > 1 else f" [{ns[0]}]" if ns else ""
            return f"tool   {m.name}: {len(cites)} citation{'s' if len(cites) != 1 else ''}{span}"
        return f"tool   {m.name}: " + short(text_of(m.content), width - 10)
    return f"{m.type:6} " + short(text_of(m.content), width)


def _next(nodes: list) -> str:
    return ", ".join(nodes) if nodes else "-"


def print_threads(email: str, found: list[dict], label: str) -> None:
    print(label)
    if not found:
        print(f"no threads for {email}")
        return
    print(f"threads of {email}, the latest written first:")
    print(f"  {'tenant':8} {'session':24} {'checkpoints':>11} {'turns':>5} {'last step':>9}  last write")
    for t in found:
        desk = t["kind"] == "desk"
        turns, step = ("-", "-") if desk else (t["turns"], "-" if t["last_step"] is None else t["last_step"])
        print(f"  {t['tenant']:8} {t['session'][:24]:24} {t['checkpoints']:>11} {turns:>5} {step:>9}  {t['last_write'][:16]}"
              + ("  (a Desk thread, desk_graph.py: not decoded here)" if desk else ""))


def print_thread(thread_id: str, steps: list[dict], off: list, label: str) -> None:
    turns = sum(1 for s in steps if s["source"] == "input")
    print(label)
    print(f"thread {thread_id}: {len(steps)} checkpoints, {turns} turn{'s' if turns != 1 else ''}")
    if off:
        at = ", ".join(str(t.metadata.get("step")) for t in off)
        print(f"  {len(off)} more checkpoint{'s sit' if len(off) != 1 else ' sits'} off this thread's latest history, "
              f"at step {at}: the thread branched on the lane (two turns from one checkpoint), and only the latest line "
              "is read")
    print(f"  {'step':>4}  {'written':8}  {'source':6}  {'brain':9}  {'next':10}  {'msgs':>4}  the newest message")
    for s in steps:
        if s["input"]:
            newest = "input, not in the messages yet: " + describe(s["input"][-1], 46)
        else:
            newest = describe(s["messages"][-1]) if s["messages"] else "-"
        written = (s["created_at"] or "")[11:19] or "-"           # the checkpoint's ts, UTC: when that step was saved
        print(f"  {s['step']:>4}  {written:8}  {s['source']:6}  {s['brain']:9}  {_next(s['next']):10}  "
              f"{len(s['messages']):>4}  {newest}")


def print_step(s: dict) -> None:
    print(f"\nstep {s['step']}: checkpoint {s['checkpoint_id']}, parent {s['parent_checkpoint_id'] or '-'}, "
          f"written {s['created_at']}")
    print(f"  source {s['source']}, brain {s['brain']}, next {_next(s['next'])}")
    print(f"  metadata {json.dumps(s['metadata'], sort_keys=True)}")
    for e in s["errors"]:
        print(f"  a task failed here: {short(e, 120)}")
    if s["input"]:
        print("  the input this checkpoint holds, applied at the next step:")
        for m in s["input"]:
            print(f"     {describe(m, 110)}")
    print(f"  the messages saved at step {s['step']} ({len(s['messages'])}):")
    for i, m in enumerate(s["messages"], 1):
        print(f"  {i:>3}. {describe(m, 110)}")


# ----------------------------------------------------------------------------- the command
def pick(steps: list[dict], at: str) -> dict:
    """The step AT names: a step number, or a checkpoint id."""
    if re.fullmatch(r"-?\d+", at):
        hits = [s for s in steps if s["step"] == int(at)]
    else:
        hits = [s for s in steps if s["checkpoint_id"] == at]
    if not hits:
        raise Refused(f"no checkpoint at {at} on this thread: steps {steps[0]['step']} to {steps[-1]['step']}")
    return hits[0]


def main(argv: list[str] | None = None, *, gcloud=_gcloud, connector=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--project", required=True)
    ap.add_argument("--email", required=True, help="whose threads: the address in tenant:EMAIL:session")
    ap.add_argument("--tenant", help="the tenant, when a session is in more than one (looked up otherwise)")
    ap.add_argument("--session", help="one thread: decode its checkpoints")
    ap.add_argument("--at", help="a step (or a checkpoint id): print the messages saved there")
    ap.add_argument("--export", help="write the thread to this JSON file, for commands/thread_replay.py")
    a = ap.parse_args(argv)
    if (a.at or a.export) and not a.session:
        print("AT and EXPORT need SESSION: run without them to list the sessions", file=sys.stderr)
        return 2
    if not a.email or ":" in a.email:
        print("EMAIL must be one address, with no ':' (agent.py's thread_config refuses one)", file=sys.stderr)
        return 2
    warnings.filterwarnings("ignore", category=UserWarning)     # as every lesson cell: a library's notices are not output
    try:
        with lane(a.project, gcloud=gcloud, connector=connector) as q:
            if not a.session:
                print_threads(a.email, threads(q, a.email), q.label)
                return 0
            thread_id = find(q, a.email, a.session, a.tenant)
            stored = rows(q, thread_id)
            label = q.label
        if not stored[0]:
            raise Refused(f"no checkpoints for {thread_id}")
        line, off = latest_line(decode(thread_id, *stored))
        steps = snapshots(line)
        print_thread(thread_id, steps, off, label)
        if a.at:
            print_step(pick(steps, a.at))
        if a.export:
            doc = export(thread_id, steps, left_out=len(off))
            Path(a.export).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"\nwrote {a.export}: {len(doc['checkpoints'])} checkpoints and {len(doc['messages'])} messages. "
                  f"Replay a turn of it locally: make replay FILE={a.export} AT=<step>")
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
