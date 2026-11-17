"""Offline checks for reading a conversation's checkpoints back, and for replaying and forking it (workshop lesson 6.8).

    python -m unittest commands/tests/test_thread_read.py -v          # from deploy/

No database, no network, no credential. The first class needs only the standard library: mk/memory.mk's two targets,
the CI lines that run this file and the new files' UNOWNED.md rows; thread_read.py's statements (SELECTs, after a
session made read only) and a person's threads listed through a fake gcloud and a fake connector whose cursor answers
each statement, the password used and never printed; the rules for EMAIL, SESSION, AT and a tenant named twice; a
thread's latest line.

The second runs the kit's own brains, needs the chat image's pins (pip install -r services/chat/requirements.txt) and
makes the rows a lane would hold. The kit's LangChain and LangGraph brains write threads into an InMemorySaver with
scripted models; each checkpoint becomes the rows PostgresSaver stores - its put()'s split of inline values from blobs,
and the pinned library's own _dump_blobs() and _dump_writes() through the pinned serializer - and a fake pg8000 cursor
serves them to thread_read. Decoding gives back every step's messages, metadata and next, for a langgraph thread, a
thread both brains wrote, a recursion-limit repair and a turn cut off mid-flight; the strict serializer revives no type
outside langgraph's safe list; the export round-trips. The offline replay opens no connection and needs no project; it
copies the thread step for step, matches a recorded turn, and finishes a cut-off one, matched as far as its recording
goes; the fork is a new branch from the turn's input with a new question, and get_state_history lists the copy, the
replay and the fork. The shipped fixture,
evals/threads/cut_off_turn.json, is what thread_replay.py --write-fixture writes today. Without the pins that class is
skipped and says so; with DOCUMIND_REQUIRE_LIBS=1, as CI's chat-pins step sets it, a missing pin is an error instead.
"""
import contextlib
import dataclasses
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import re
import socket
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import uuid
import warnings

KIT = Path(__file__).resolve().parents[2]
ROOT = KIT.parent
for p in (str(KIT / "commands"), str(KIT / "services/chat"), str(KIT)):
    if p not in sys.path:
        sys.path.insert(0, p)
import thread_read as tr                       # noqa: E402 - the standard library at import; LangGraph where it is used

FRAMEWORKS = all(importlib.util.find_spec(m) for m in ("langchain", "langgraph", "langgraph.checkpoint.postgres"))
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
PROJECT = "documind-ai-YOUR-ID"
UI = f"documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"
INSTANCE = f"{PROJECT}:asia-south1:documind-checkpoint"
DSN = f"postgresql://chat:pa%40ss-word@/documind?host=/cloudsql/{INSTANCE}"


def read(*parts) -> str:
    return (KIT.joinpath(*parts)).read_text(encoding="utf-8")


@dataclasses.dataclass
class Note:                                    # a type no langgraph allowlist names, for the strict serializer
    text: str


# ----------------------------------------------------------------------------- a lane that is only a fake
class Cursor:
    def __init__(self, db):
        self.db, self.rows = db, None

    def execute(self, sql, args=()):
        len(args)                              # as pg8000 does: None has no len(), and the reader must not send it
        self.db.statements.append((sql, tuple(args), self.db.autocommit))
        if sql == tr.READ_ONLY:
            self.rows = None
            return
        if not sql.lstrip().upper().startswith("SELECT"):
            raise AssertionError(f"a statement that is not a SELECT reached the database: {sql}")
        name = next(k for k, v in tr.SQL.items() if v == sql)
        self.rows = self.db.answer(name, args)

    def fetchall(self):
        if self.rows is None:
            raise AssertionError("fetchall() after a statement with no result set")
        return list(self.rows)


class Database:
    """pg8000's connection, over tables kept as the lane keeps them: {thread_id: (checkpoints, blobs, writes)}."""

    def __init__(self, tables):
        self.tables, self.statements, self.autocommit, self.closed, self.login = tables, [], False, False, None

    def cursor(self):
        return Cursor(self)

    def close(self):
        self.closed = True

    def answer(self, name, args):
        if name == "threads":
            out = []
            for tid, (cps, _, _) in self.tables.items():
                if tid.split(":")[1] != args[0]:
                    continue
                metas = [json.loads(m) for _, _, _, m in cps]
                out.append((tid, len(cps), sum(m.get("source") == "input" for m in metas),
                            max(m.get("step", -1) for m in metas), max(json.loads(c)["ts"] for _, _, c, _ in cps)))
            return sorted(out, key=lambda r: r[4], reverse=True)
        if name == "find":
            return [(t,) for t in self.tables if t.split(":")[1:] == list(args)]
        return self.tables.get(args[0], ([], [], []))[("checkpoints", "blobs", "writes").index(name)]


def connector(db):
    class Connector:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def connect(self, instance, driver, **login):
            db.login = (instance, driver, login)
            return db
    return Connector


def gcloud(project, *args):
    assert project == PROJECT, project
    if args[:3] == ("secrets", "versions", "access"):
        return DSN
    if args[:3] == ("sql", "instances", "describe"):
        return INSTANCE
    raise AssertionError(args)


def run_read(db, *argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = tr.main(["--project", PROJECT, *argv], gcloud=gcloud, connector=connector(db))
    return code, out.getvalue(), err.getvalue()


def stored(n_cps, tid, source="loop"):
    """Checkpoint rows that only the listing reads: ids, steps, sources and times."""
    rows = []
    for k in range(n_cps):
        meta = {"source": "input" if k in (0, 5) else source, "step": k - 1, "parents": {}}
        rows.append((f"cp{k:03d}", f"cp{k - 1:03d}" if k else None, json.dumps({"ts": f"2026-10-08T10:{k:02d}:00+00:00"}),
                     json.dumps(meta)))
    return rows, [], []


class TheReaderAlone(unittest.TestCase):
    """What needs no LangGraph: the targets, the statements, the listing, the rules."""

    def test_memory_mk_holds_the_two_targets_and_the_makefile_keeps_its_lines(self):
        mk, memory, readme = read("Makefile"), read("mk", "memory.mk"), read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                     # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")]
        self.assertTrue({"thread", "replay"} <= set(phony.split()), phony[-80:])     # later kits append after them
        for target in ("thread", "replay"):
            self.assertRegex(memory, rf"(?m)^{target}:")
            self.assertIn(f"`{target}`", readme)
        self.assertIn("| `memory.mk` |", readme)
        self.assertRegex(memory, r"(?m)^thread: guard-project$")
        self.assertRegex(memory, r"(?m)^replay: \$\(if \$\(OFFLINE\),,guard-project\)$")     # OFFLINE=1 needs no project
        self.assertIn("commands/thread_read.py", memory)
        self.assertIn("commands/thread_replay.py", memory)
        self.assertIn("DOCUMIND_IMPERSONATE_SA=documind-ui-sa@$(PROJECT).iam.gserviceaccount.com", memory)
        self.assertIn("--connector", memory)                            # make thread installs the Cloud SQL connector
        venv = read("commands", "graph-venv.sh")
        self.assertIn('"$VENV/bin/pip" install -q -r services/chat/requirements.txt ${extra[@]+"${extra[@]}"}', venv)
        self.assertIn('extra=("cloud-sql-python-connector[pg8000]==1.22.0" "pg8000==1.31.5")', venv)   # lesson 6.6's pins

    def test_both_chat_pin_steps_run_this_file(self):
        line = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_thread_read.py -v"
        self.assertIn(line, read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = ROOT / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                            # the authoring repository's own CI
            self.assertIn(line, repo_ci.read_text(encoding="utf-8"))

    def test_the_new_files_have_their_unowned_rows(self):
        # An UNOWNED.md row until lesson 6.8's page quotes the file; from then on INDEX.md names the lesson.
        unowned, index = read("UNOWNED.md"), read("INDEX.md")
        quoted = set(re.findall(r"^\| `([^`]+)` \| \w+ \| (?!- \|)[^|]+ \|", index, re.M))
        for f in ("commands/thread_read.py", "commands/thread_replay.py", "commands/graph-venv.sh", "mk/memory.mk",
                  "evals/threads/cut_off_turn.json", "commands/tests/test_thread_read.py"):
            self.assertTrue(f"| `{f}` | **6.8**" in unowned or f in quoted, f)
            self.assertTrue((KIT / f).exists(), f)

    def test_compare_reads_a_cut_off_recording_as_far_as_it_goes(self):
        """13 October 2026: a recording that stops mid-turn, replayed and finished, read "differs" - for the steps, the
        sources and the answer it never reached. Only what the recording holds is compared."""
        import thread_replay as rp
        m = types.SimpleNamespace
        human, answer = m(type="human", tool_calls=None, content="q"), m(type="ai", tool_calls=[], content="Yes [1].")
        ask = m(type="ai", tool_calls=[{"name": "retrieve", "args": {"query": "q"}, "id": "c1"}], content="")
        found = m(type="tool", tool_calls=None, content=json.dumps({"citations": [{"chunk_id": "a"}, {"chunk_id": "b"}]}))
        self.assertEqual(rp.compare([human, ask], [human, ask, found, answer]),
                         "the replay matches the recorded turn as far as the recording goes: the same steps (human, ai "
                         "asks retrieve), then it finished the turn (tool, ai), with 2 citations and an answer")
        self.assertIn("as far as the recording goes: the same steps (human, ai asks retrieve, tool), then it finished the "
                      "turn (ai)", rp.compare([human, ask, found], [human, ask, found, answer]))
        self.assertEqual(rp.compare([human, ask, found, answer], [human, ask, found, answer]),      # a finished turn,
                         "the replay matches the recorded turn: the same steps (human, ai asks retrieve, tool, ai), the "
                         "same sources (2 citations), the same answer")                                # compared whole
        other = m(type="ai", tool_calls=[{"name": "calculate_processing_cost", "args": {}, "id": "c2"}], content="")
        moved = m(type="tool", tool_calls=None, content=json.dumps({"citations": [{"chunk_id": "z"}]}))
        for recorded, replayed in (([human, ask], [human, other, found, answer]),           # another step
                                   ([human, ask, found], [human, ask, moved, answer]),       # other sources
                                   ([human, ask], [human, ask, found])):                     # no answer either
            self.assertTrue(rp.compare(recorded, replayed).startswith("the replay differs"), (recorded, replayed))

    def test_every_statement_is_a_select(self):
        self.assertEqual(tr.READ_ONLY, "SET default_transaction_read_only = on")
        for name, sql in tr.SQL.items():
            self.assertTrue(sql.startswith("SELECT "), name)
            self.assertNotRegex(sql.upper(), r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT)\b", name)
            self.assertNotIn("%%", sql)

    def test_a_persons_threads_listed_read_only_and_the_password_never_printed(self):
        db = Database({f"acme:{UI}:lesson68": stored(9, f"acme:{UI}:lesson68"),
                       f"acme:{UI}:smoke-langgraph": stored(5, ""),
                       f"acme:{UI}:desk~gc-0a1b": stored(3, ""),
                       f"zeta:someone@example.com:lesson68": stored(4, "")})
        code, out, err = run_read(db, "--email", UI)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(db.login, (INSTANCE, "pg8000", {"user": "chat", "password": "pa@ss-word", "db": "documind"}))
        self.assertEqual(db.statements[0], (tr.READ_ONLY, (), True))   # autocommit on, then read only, before any read
        self.assertTrue(all(auto for _, _, auto in db.statements))
        self.assertEqual([s for s, _, _ in db.statements[1:]], [tr.SQL["threads"]])
        self.assertTrue(db.closed)
        self.assertNotIn("pa@ss", out + err)
        self.assertNotIn("pa%40ss", out + err)
        self.assertIn(f"{INSTANCE}, database documind, as chat (read only)", out)
        sessions = re.findall(r"^  acme\s+(\S+)\s+(\d+)\s+(\S+)", out, re.M)
        self.assertEqual([(s, int(n)) for s, n, _ in sessions], [("lesson68", 9), ("smoke-langgraph", 5), ("desk~gc-0a1b", 3)])
        self.assertIn("(a Desk thread, desk_graph.py: not decoded here)", out)
        self.assertNotIn("someone@example.com", out)
        lesson = re.search(r"^  acme\s+lesson68\s+9\s+2\s+7\s+2026-10-08T10:08$", out, re.M)
        self.assertIsNotNone(lesson, out)                              # 9 checkpoints, 2 turns, last step 7, last write

    def test_the_rules_refuse_before_any_decoding(self):
        db = Database({f"acme:{UI}:lesson68": stored(4, ""), f"zeta:{UI}:lesson68": stored(4, "")})
        cases = [(["--email", UI, "--at", "3"], "AT and EXPORT need SESSION"),
                 (["--email", "a:b@example.com"], "no ':'"),
                 (["--email", UI, "--session", "desk~gc-0a1b"], "a Desk thread"),
                 (["--email", UI, "--session", "bad session!"], "session_id pattern"),
                 (["--email", UI, "--session", "lesson68"], "in 2 tenants' threads (acme, zeta): name one with TENANT="),
                 (["--email", UI, "--session", "nothing-here"], "no thread for")]
        for argv, said in cases:
            code, out, err = run_read(db, *argv)
            self.assertEqual(code, 2, argv)
            self.assertIn(said, err, argv)
        self.assertTrue(all(s == tr.READ_ONLY or s in (tr.SQL["find"],) for s, _, _ in db.statements))

    def test_a_thread_is_read_along_its_latest_line(self):
        def cp(cid, parent, step):
            return types.SimpleNamespace(config={"configurable": {"checkpoint_id": cid}}, metadata={"step": step},
                                         parent_config={"configurable": {"checkpoint_id": parent}} if parent else None)
        # two turns started from c3 at once: c4a is the older child, c4b's line is the latest
        tuples = [cp("c1", None, -1), cp("c2", "c1", 0), cp("c3", "c2", 1), cp("c4a", "c3", 2), cp("c4b", "c3", 2),
                  cp("c5b", "c4b", 3)]
        line, off = tr.latest_line(tuples)
        self.assertEqual([t.config["configurable"]["checkpoint_id"] for t in line], ["c1", "c2", "c3", "c4b", "c5b"])
        self.assertEqual([t.config["configurable"]["checkpoint_id"] for t in off], ["c4a"])
        self.assertEqual(tr.latest_line([]), ([], []))


# ----------------------------------------------------------------------------- the library half
def pg_rows(saver, thread_id):
    """The rows PostgresSaver would store for the thread `saver` holds: put()'s split of plain values, kept inline,
    from the others, kept as blobs (langgraph-checkpoint-postgres 3.1.2 __init__.py:309-319), each new version's blob and
    each task's writes made by the pinned library's own _dump_blobs() and _dump_writes() with its default serializer."""
    from langgraph.checkpoint.base import get_serializable_checkpoint_metadata
    from langgraph.checkpoint.postgres.base import BasePostgresSaver
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

    pg = BasePostgresSaver(serde=JsonPlusSerializer())
    versions, checkpoints, blobs, writes = {}, [], {}, []
    for t in list(saver.list({"configurable": {"thread_id": thread_id}}))[::-1]:
        c, cid = t.checkpoint, t.config["configurable"]["checkpoint_id"]
        parent = t.parent_config["configurable"]["checkpoint_id"] if t.parent_config else None
        kept = {**c, "channel_values": dict(c["channel_values"])}
        blob_values = {k: kept["channel_values"].pop(k) for k, v in c["channel_values"].items()
                       if not (v is None or isinstance(v, (str, int, float, bool)))}
        seen = versions.get(parent, {})
        new = {k: v for k, v in c["channel_versions"].items() if seen.get(k) != v and k in blob_values}
        for row in pg._dump_blobs(thread_id, "", blob_values, new):
            blobs.setdefault((row[2], row[3]), (row[2], row[3], row[4], row[5]))      # ON CONFLICT DO NOTHING
        checkpoints.append((cid, parent, json.dumps(kept), json.dumps(get_serializable_checkpoint_metadata(t.config, t.metadata))))
        by_task = {}
        for task_id, channel, value in t.pending_writes or []:
            by_task.setdefault(task_id, []).append((channel, value))
        for task_id, ws in by_task.items():
            writes += [(r[2], r[3], r[5], r[6], r[7], r[8]) for r in pg._dump_writes(thread_id, "", cid, task_id, "", ws)]
        versions[cid] = c["channel_versions"]
    writes.sort(key=lambda w: (w[0], w[1], w[2]))
    return checkpoints, list(blobs.values()), [(w[0], w[1], w[3], w[4], bytes(w[5])) for w in writes]


@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins: pip install -r services/chat/requirements.txt")
class ThreadsOfTheKitsBrains(unittest.TestCase):
    """Threads the kit's own brains wrote, read back from lane-shaped rows, replayed and forked offline."""

    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        logging.disable(logging.CRITICAL)
        import brains
        import limits
        import thread_replay
        from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
        from langchain_core.messages import AIMessage
        from langgraph.checkpoint.memory import InMemorySaver
        import shared.documind_tools as dt

        cls.brains, cls.limits, cls.rp, cls.AIMessage = brains, limits, thread_replay, AIMessage

        class Script(FakeMessagesListChatModel):
            def bind_tools(self, tools, **kw):
                return self

        def passages(query, **kw):
            n = 2 if "contract" in query else 3
            return {"answerable": True, "confidence": "high", "citations": [
                {"chunk_id": f"acme:payment_of_gratuity_act_1972#p4-{i}", "source_uri": "gs://b/acme/gratuity.pdf",
                 "page": 4, "quote": f"Gratuity shall be payable ... ({query[:12]} {i})", "score": 0.9 - i / 10} for i in range(n)]}

        def call(q, i):
            return AIMessage("", tool_calls=[{"name": "retrieve", "args": {"query": q}, "id": f"call_{i}"}])

        saver, saved = InMemorySaver(), dt.retrieve
        dt.retrieve = passages
        try:
            ctx = lambda brain: {"tenant_id": "acme", "user_id": UI, "assertion": "", "brain": brain}  # noqa: E731
            cls.ids = {k: f"acme:{UI}:{k}" for k in ("graph", "mixed", "repair")}
            cfg = {k: {"configurable": {"thread_id": v}} for k, v in cls.ids.items()}
            lg = brains.LangGraphBrain(saver, llm=Script(responses=[call("gratuity years", 1), AIMessage("Five years [1]."),
                                                                     call("contract employee", 2), AIMessage("Yes [1].")]))
            lg.answer("After how many years is gratuity payable?", config=cfg["graph"], context=ctx("langgraph"))
            lg.answer("And for a contract employee?", config=cfg["graph"], context=ctx("langgraph"))
            lc = brains.LangChainBrain(saver, llm=Script(responses=[call("gratuity years", 3), AIMessage("Five years [1].")]))
            lc.answer("After how many years is gratuity payable?", config=cfg["mixed"], context=ctx("langchain"))
            brains.LangGraphBrain(saver, llm=Script(responses=[AIMessage("You asked about gratuity.")])).answer(
                "What did I ask?", config=cfg["mixed"], context=ctx("langgraph"))
            looping = brains.LangChainBrain(saver, llm=Script(responses=[call("again", k) for k in range(10, 20)]))
            with patch.object(limits, "recursion_limit", return_value=3):
                looping.answer("Loop?", config=cfg["repair"], context=ctx("langchain"))
        finally:
            dt.retrieve = saved
        cls.saver = saver
        cls.cut = tempfile.mkdtemp(prefix="tr68-")
        cls.fixture_doc = thread_replay.write_fixture(Path(cls.cut) / "cut_off_turn.json")
        cls.cut_id = cls.fixture_doc["thread_id"]
        cls.cut_saver = None

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def tables(self):
        return {tid: pg_rows(self.saver, tid) for tid in self.ids.values()}

    def read_back(self, key):
        tid = self.ids[key]
        line, off = tr.latest_line(tr.decode(tid, *pg_rows(self.saver, tid)))
        return tr.snapshots(line), off

    def own(self, key):
        """The same thread through the saver that wrote it: (step, source, next, messages, metadata) per checkpoint."""
        graphs = tr.kit_graphs(self.saver)
        out = []
        for t in list(self.saver.list({"configurable": {"thread_id": self.ids[key]}}))[::-1]:
            snap = graphs[tr.brain_of(t.metadata)].get_state(t.config)
            out.append((t.metadata["step"], t.metadata["source"], list(snap.next), snap.values.get("messages", []),
                        {k: v for k, v in t.metadata.items() if k != "writes"}))
        return out

    # ---- decoding
    def test_decoding_gives_back_every_step_of_a_langgraph_thread(self):
        steps, off = self.read_back("graph")
        self.assertEqual(off, [])
        got = [(s["step"], s["source"], s["next"], s["messages"], s["metadata"]) for s in steps]
        self.assertEqual(got, self.own("graph"))
        self.assertEqual([s["next"] for s in steps], [["__start__"], ["agent"], ["tools"], ["agent"], [],
                                                       ["__start__"], ["agent"], ["tools"], ["agent"], []])
        self.assertEqual({s["brain"] for s in steps}, {"langgraph"})
        self.assertEqual([len(s["messages"]) for s in steps], [0, 1, 2, 3, 4, 4, 5, 6, 7, 8])
        self.assertEqual([m.content for m in steps[5]["input"]], ["And for a contract employee?"])
        self.assertEqual(steps[2]["messages"][-1].tool_calls[0]["args"], {"query": "gratuity years"})
        cites = json.loads(steps[3]["messages"][-1].content)["citations"]
        self.assertEqual([c["n"] for c in cites], [1, 2, 3])

    def test_each_checkpoint_is_read_through_the_graph_of_the_brain_that_wrote_it(self):
        steps, _ = self.read_back("mixed")
        self.assertEqual([(s["step"], s["source"], s["next"], s["messages"], s["metadata"]) for s in steps], self.own("mixed"))
        self.assertEqual([s["brain"] for s in steps], ["langchain"] * 5 + ["langgraph"] * 3)
        self.assertEqual([s["next"] for s in steps], [["__start__"], ["model"], ["tools"], ["model"], [],
                                                       ["__start__"], ["agent"], []])
        self.assertTrue(all(s["metadata"].get("ls_integration") == tr.CREATE_AGENT for s in steps[:5]))

    def test_a_recursion_limit_repair_reads_as_the_update_it_was(self):
        steps, _ = self.read_back("repair")
        self.assertEqual([(s["step"], s["source"], s["next"], s["messages"], s["metadata"]) for s in steps], self.own("repair"))
        last = steps[-1]
        self.assertEqual((last["source"], last["brain"], last["next"]), ("update", "langchain", []))
        self.assertEqual(last["messages"][-1].content, self.limits.STOP_ANSWER)
        asked = {c["id"] for m in last["messages"] for c in (getattr(m, "tool_calls", None) or [])}
        self.assertEqual(asked, {m.tool_call_id for m in last["messages"] if m.type == "tool"})

    def test_a_cut_off_turn_waits_at_tools_with_its_call_open(self):
        doc = self.fixture_doc
        last = doc["checkpoints"][-1]
        self.assertEqual((last["source"], last["next"]), ("loop", ["tools"]))
        by_id = {m["data"]["id"]: m for m in doc["messages"]}
        final = by_id[last["messages"][-1]]
        self.assertEqual(final["type"], "ai")
        self.assertEqual([c["name"] for c in final["data"]["tool_calls"]], ["retrieve"])
        self.assertFalse(any(by_id[i]["type"] == "tool" and by_id[i]["data"]["tool_call_id"] == final["data"]["tool_calls"][0]["id"]
                             for i in last["messages"]))

    def test_the_serializer_revives_only_langgraphs_safe_types(self):
        from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
        typ, blob = JsonPlusSerializer().dumps_typed({"id": uuid.UUID(int=7), "note": Note("from the database")})
        loose, strict = JsonPlusSerializer().loads_typed((typ, blob)), tr.serializer().loads_typed((typ, blob))
        self.assertIsInstance(loose["note"], Note)                       # the library's default imports and builds it
        self.assertEqual(strict["id"], uuid.UUID(int=7))                 # on langgraph's safe list
        self.assertNotIsInstance(strict["note"], Note)                   # not on it: plain data, nothing imported
        self.assertEqual(strict["note"], {"text": "from the database"})

    def test_the_decode_reads_each_version_of_messages_once_and_skips_empty_blobs(self):
        cps, blobs, writes = pg_rows(self.saver, self.ids["graph"])
        blobs = blobs + [("phantom", "00000000000000000000000000000099.0.1", "empty", None)]
        cps = [(cid, parent, json.dumps({**json.loads(c), "channel_versions": {**json.loads(c)["channel_versions"],
                                                                                "phantom": "00000000000000000000000000000099.0.1"}}), m)
               for cid, parent, c, m in cps]
        calls = []
        serde = tr.serializer()
        real = serde.loads_typed
        serde.loads_typed = lambda data: calls.append(data[0]) or real(data)
        tuples = tr.decode(self.ids["graph"], cps, blobs, writes, serde=serde)
        self.assertNotIn("phantom", tuples[-1].checkpoint["channel_values"])
        self.assertEqual(len(calls), len([b for b in blobs if b[2] != "empty"]) + len(writes))

    # ---- the command, end to end against the fake lane
    def test_make_thread_prints_each_step_and_the_messages_at_one(self):
        db = Database(self.tables())
        code, out, err = run_read(db, "--email", UI, "--session", "graph", "--at", "2")
        self.assertEqual((code, err), (0, ""))
        self.assertIn(f"thread {self.ids['graph']}: 10 checkpoints, 2 turns", out)
        rows = re.findall(r"^\s+(-?\d+)  \d\d:\d\d:\d\d  (\w+)\s+(\w+)\s+(\S+)\s+(\d+)  ", out, re.M)
        self.assertEqual(len(rows), 10)                                  # each step with the time it was written
        self.assertEqual([(int(s), src, nx, int(n)) for s, src, _, nx, n in rows][:5],
                         [(-1, "input", "__start__", 0), (0, "loop", "agent", 1), (1, "loop", "tools", 2), (2, "loop", "agent", 3),
                          (3, "loop", "-", 4)])
        self.assertIn("input, not in the messages yet: human  After how many years", out)
        self.assertIn("step 2: checkpoint ", out)
        self.assertIn("source loop, brain langgraph, next agent", out)
        self.assertIn("the messages saved at step 2 (3):", out)
        self.assertIn("ai     asks retrieve(query='gratuity years')", out)
        self.assertIn("tool   retrieve: 3 citations [1]-[3]", out)
        self.assertEqual({s for s, _, _ in db.statements[1:]}, {tr.SQL["find"], tr.SQL["checkpoints"], tr.SQL["blobs"], tr.SQL["writes"]})

    def test_the_export_round_trips_and_says_what_it_left_out(self):
        tables = self.tables()
        tid = self.ids["graph"]
        cps, blobs, writes = tables[tid]
        # a second turn started from the same checkpoint as the first's last: the thread branched on the lane
        branch = [(cid + "x", parent, c, m) for cid, parent, c, m in cps[-2:-1]]
        tables[tid] = (sorted(cps + branch, key=lambda r: r[0]), blobs, writes)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "thread.json"
            code, out, err = run_read(Database(tables), "--email", UI, "--session", "graph", "--export", str(path))
            self.assertEqual((code, err), (0, ""))
            self.assertIn("1 more checkpoint sits off this thread's latest history, at step 7", out)
            self.assertIn(f"wrote {path}: 10 checkpoints", out)
            doc = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual((doc["format"], doc["thread_id"], doc["left_out"], doc["session"]), (tr.FORMAT, tid, 1, "graph"))
            loaded = self.rp.load(path)
        own = self.own("graph")
        self.assertEqual([cp["messages"] for cp in loaded["checkpoints"]], [o[3] for o in own])
        self.assertEqual([cp["next"] for cp in loaded["checkpoints"]], [o[2] for o in own])
        self.assertEqual(len(doc["messages"]), 8)                        # every message once
        self.assertEqual(json.loads(json.dumps(doc)), doc)

    # ---- the offline replay
    def replay(self, doc, **kw):
        """An offline replay with no project or credential in the environment, every name resolved and every socket
        connected inside the replay's own guard recorded: none may leave the machine."""
        out, tried, real_guard = io.StringIO(), [], self.rp.no_network

        @contextlib.contextmanager
        def recorded_guard():
            with real_guard():
                inner = (socket.socket.connect, socket.getaddrinfo)
                socket.socket.connect = lambda sock, address: tried.append(address) or inner[0](sock, address)
                socket.getaddrinfo = lambda host, *a, **k: tried.append(host) or inner[1](host, *a, **k)
                try:
                    yield
                finally:
                    socket.socket.connect, socket.getaddrinfo = inner
                    tried.append("guarded")
        env = {k: v for k, v in os.environ.items() if k not in ("GOOGLE_CLOUD_PROJECT", "RAG_API_URL", "DOCUMIND_IMPERSONATE_SA",
                                                                  "GOOGLE_APPLICATION_CREDENTIALS")}
        with patch.dict(os.environ, env, clear=True), patch.object(self.rp, "no_network", recorded_guard), \
                contextlib.redirect_stdout(out):
            got = self.rp.replay(doc, offline_mode=True, **kw)
        self.assertEqual(tried[-1:], ["guarded"])                         # the whole replay ran inside the guard
        self.assertEqual([a for a in tried[:-1] if (a[0] if isinstance(a, tuple) else a) not in self.rp.LOOPBACK], [])
        return got, out.getvalue()

    def export_of(self, key):
        steps, _ = self.read_back(key)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "t.json"
            path.write_text(json.dumps(tr.export(self.ids[key], steps)), encoding="utf-8")
            return self.rp.load(path)

    def test_the_offline_replay_refuses_the_network_and_mints_nothing(self):
        import shared.documind_tools as dt
        with self.rp.no_network():
            with self.assertRaises(OSError):
                socket.create_connection(("192.0.2.1", 443), timeout=1)
            with self.assertRaises(OSError):
                socket.getaddrinfo("oauth2.googleapis.com", 443)
            a, b = socket.socketpair()                                    # loopback still works
            a.close(), b.close()
        before = (dt.retrieve, dt._id_token, dt.PROFILE)
        with self.rp.offline([]):
            with self.assertRaises(OSError):
                dt._id_token("https://documind-api.invalid")
            self.assertEqual(dt.PROFILE, "local")                         # an unrecorded search: the Rs 0 lane
        self.assertEqual((dt.retrieve, dt._id_token, dt.PROFILE), before)  # everything put back

    def test_a_replay_of_a_recorded_turn_matches_it(self):
        doc = self.export_of("graph")
        got, out = self.replay(doc, at="4")                              # the second turn, from its input
        self.assertEqual(got["problems"], [])
        self.assertEqual(got["copied"], 10)
        self.assertIn("the replay matches the recorded turn: the same steps (human, ai asks retrieve, tool, ai), "
                      "the same sources (2 citations), the same answer", out)
        self.assertEqual([m.type for m in got["replayed"]], ["human", "ai", "tool", "ai"])
        self.assertEqual(got["replayed"][-1].content, "Yes [1].")
        self.assertNotEqual(got["replayed"][1].id, got["recorded"][1].id)  # a new message, the same words
        first = next(h for h in got["history"] if h.config["configurable"]["checkpoint_id"] == min(got["replay_ids"]))
        self.assertEqual((first.metadata["source"], first.metadata["step"]), ("fork", 5))   # from an input: LangGraph's fork mark

    def test_a_replay_from_mid_turn_numbers_on_from_the_turns_citations(self):
        doc = self.export_of("graph")
        got, out = self.replay(doc, at="2")                              # after the search: the model's answer only
        self.assertIn("the replay matches the recorded turn: the same steps (ai), no search, the same answer", out)
        self.assertEqual([m.content for m in got["replayed"]], ["Five years [1]."])

    def test_a_turn_cut_off_mid_flight_is_finished_from_its_checkpoint(self):
        doc = self.rp.load(Path(self.cut) / "cut_off_turn.json")
        got, out = self.replay(doc)                                      # by default: where it stopped
        self.assertIn("2. replay from step 6 (next tools)", out)
        self.assertIn("step 6 is where the recorded turn stopped: the model had asked retrieve(query="
                      "'Is gratuity payable to a contract employee?') and the tool never ran", out)
        self.assertEqual([m.type for m in got["replayed"]], ["tool", "ai"])
        self.assertTrue(got["replayed"][-1].content.startswith("(offline, scripted) The first passage says: "))
        cites = tr.citations_of(got["replayed"][0])
        self.assertTrue(cites and all(c["chunk_id"].startswith("acme:") and PROJECT in c["source_uri"] for c in cites), cites)
        self.assertEqual(got["recorded"], [])
        self.assertIn("nothing was recorded after step 6: the replay finished the turn: 2 messages, 1 model call", out)
        self.assertEqual(got["model_calls"], 3)                          # the replay's one, the fork's two

    def test_a_cut_off_turn_replayed_from_its_input_matches_as_far_as_it_was_recorded(self):
        doc = self.rp.load(Path(self.cut) / "cut_off_turn.json")
        got, out = self.replay(doc, at="4")                              # the cut-off turn, from its input
        self.assertEqual([m.type for m in got["recorded"]], ["human", "ai"])
        self.assertEqual([m.type for m in got["replayed"]], ["human", "ai", "tool", "ai"])
        self.assertRegex(out, r"the replay matches the recorded turn as far as the recording goes: the same steps \(human, "
                              r"ai asks retrieve\), then it finished the turn \(tool, ai\), with [1-9]\d* citations? and an "
                              r"answer\n")
        self.assertNotIn("differs", out)

    def test_the_fork_is_a_new_branch_and_the_history_lists_every_branch(self):
        doc = self.export_of("graph")
        got, out = self.replay(doc, at="6", fork="Is gratuity payable to an apprentice?")
        hist = got["history"]
        by_id = {h.config["configurable"]["checkpoint_id"]: h for h in hist}
        parent = lambda h: (h.parent_config or {}).get("configurable", {}).get("checkpoint_id")  # noqa: E731
        fork_first = min(got["fork_ids"])
        self.assertEqual(by_id[parent(by_id[fork_first])].metadata["step"], 4)        # the turn's input, step 4
        self.assertEqual(by_id[fork_first].metadata["source"], "update")
        replay_first = min(got["replay_ids"])
        self.assertEqual(by_id[parent(by_id[replay_first])].metadata["step"], 6)      # the replay starts from step 6's copy,
        self.assertEqual(by_id[replay_first].metadata["source"], "loop")              # an update: no fork mark (_loop.py:960)
        leaves = set(by_id) - {parent(h) for h in hist}
        self.assertEqual(len(leaves), 3)                                               # the copy, the replay, the fork
        self.assertIn(f"4. graph.get_state_history(thread): {len(hist)} checkpoints, in 3 branches", out)
        asked = [m for m in got["fork_messages"] if m.type == "human"][-1]
        self.assertEqual(asked.content, "Is gratuity payable to an apprentice?")
        self.assertEqual(uuid.UUID(asked.id).version, 4)
        self.assertEqual([m.content for m in got["fork_messages"] if m.type == "human"],
                         ["After how many years is gratuity payable?", "Is gratuity payable to an apprentice?"])
        rows = re.findall(r"^     (copy|replay|fork)\s+(-?\d+)", out, re.M)
        self.assertEqual([b for b, _ in rows].count("copy"), 10)
        self.assertEqual(len(rows), len(hist))

    def test_a_step_that_ends_its_turn_cannot_be_replayed(self):
        doc = self.export_of("graph")
        with self.assertRaises(tr.Refused) as cm, contextlib.redirect_stdout(io.StringIO()):
            self.rp.replay(doc, at="3", offline_mode=True)
        self.assertIn("step 3 ends its turn", str(cm.exception))

    def test_the_command_runs_the_fixture_offline_and_refuses_a_lane_replay_without_its_settings(self):
        env = {k: v for k, v in os.environ.items() if k not in ("GOOGLE_CLOUD_PROJECT", "RAG_API_URL", "DOCUMIND_IMPERSONATE_SA")}
        out, err = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, env, clear=True), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(self.rp.main(["--offline"]), 0)
            self.assertEqual(self.rp.main(["--file", str(self.rp.FIXTURE)]), 2)
            self.assertEqual(self.rp.main([]), 2)
        self.assertIn("  from evals/threads/cut_off_turn.json: 8 checkpoints, steps -1 to 6, 2 turns\n", out.getvalue())
        self.assertIn("only the local copy was written; the lane never is.", out.getvalue())
        self.assertIn("Rs 0 (a script, not a model)", out.getvalue())
        self.assertIn("needs GOOGLE_CLOUD_PROJECT, RAG_API_URL, DOCUMIND_IMPERSONATE_SA", err.getvalue())
        self.assertIn("a lane replay needs FILE=", err.getvalue())

    def test_db_keeps_the_copy_in_a_new_sqlite_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "copy.db"
            path.write_text("taken", encoding="utf-8")
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(self.rp.main(["--offline", "--db", str(path)]), 2)
            self.assertIn("exists", err.getvalue())
            if importlib.util.find_spec("langgraph.checkpoint.sqlite") is None:
                return                      # requirements-local.txt's pin, not the chat image's: the refusal is the check
            path.unlink()
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(self.rp.main(["--offline", "--db", str(path)]), 0)
            self.assertIn("in a local SqliteSaver", out.getvalue())
            import sqlite3
            with contextlib.closing(sqlite3.connect(path)) as con:
                n = con.execute("SELECT count(*) FROM checkpoints").fetchone()[0]
            self.assertEqual(n, len(re.findall(r"^     (?:copy|replay|fork) ", out.getvalue(), re.M)))

    # ---- the fixture
    def test_the_shipped_fixture_is_what_write_fixture_writes_today(self):
        def skeleton(doc):
            msgs = {m["data"]["id"]: m for m in doc["messages"]}

            def norm(i):
                d = msgs[i]["data"]
                return (msgs[i]["type"], d.get("content"), [(c["name"], c["args"]) for c in d.get("tool_calls") or []],
                        d.get("name"), d.get("status"))
            return [(c["step"], c["source"], c["brain"], c["next"], [norm(i) for i in c["messages"]],
                     [norm(i) for i in c["input"]]) for c in doc["checkpoints"]]
        shipped = json.loads(self.rp.FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(skeleton(shipped), skeleton(self.fixture_doc))
        self.assertEqual({k: shipped[k] for k in ("format", "thread_id", "tenant", "user", "session", "written_by", "left_out")},
                         {"format": tr.FORMAT, "thread_id": f"acme:{UI}:lesson68", "tenant": "acme", "user": UI,
                          "session": "lesson68", "written_by": "commands/thread_replay.py --write-fixture", "left_out": 0})
        self.assertEqual(len(shipped["checkpoints"]), 8)
        self.assertNotRegex(self.rp.FIXTURE.read_text(encoding="utf-8"), r"documind-ai-(?!YOUR-ID)")


if __name__ == "__main__":
    unittest.main()
