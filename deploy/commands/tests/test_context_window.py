"""Offline checks for the window over a conversation: what each model call is sent of it (workshop lesson 6.9).

    python -m unittest commands/tests/test_context_window.py -v          # from deploy/

No network, no credential, no model. The first class needs only the standard library: mk/memory.mk's window-check
target, the Makefile's 888 lines and the target's name in .PHONY, both CI lines and the new files' UNOWNED.md rows;
nothing under services/ imports the module; the rule's arithmetic, plan(), on token counts, at its edges and on random
sizes; turns() on stand-in messages, a result whose call sits in an earlier turn joining the turns between; the write
rules on an earlier question - masked, then cut to the Desk's own 300 characters; the Rs 0 lane's ranking, its counts
cached, equal to the textbook one (shared/documind_tools.py, which imports requests); a row that names the limit that
stopped its turn.

The second runs on LangChain's messages and the kit's brains, and needs the chat image's pins (pip install -r
services/chat/requirements.txt). window() on generated threads of every shape - tool rounds of parallel calls,
refusals, a turn cut off with its call open, a result whose call sits in an earlier turn, answers in content blocks,
card and Aadhaar numbers, questions of 4,000 characters, budgets from 0 up - holds every call under its ceiling, keeps
the system prompt and the newest turn whole, keeps the thread's order, splits no tool pair and leaves no call open that
was answered, masks every number it carries from the person and the earlier answers, cuts every earlier question to
300 characters, and changes nothing it was given; an oversized newest turn goes whole. full() returns the very list the
brain built. The kit's LangChain and LangGraph brains built with windowed() send their model exactly window() of what
they hold, and keep every message in the checkpoint, unmasked; with mode full they send what they send without it. The
middleware form sends the same window and leaves create_agent's checkpoints as they were (lesson 6.6's +3 and +5).
make window-check's offline run, both modes, on part of the Rs 0 lane's corpus, and its live path on a scripted model
inside lesson 6.8's socket guard. Without the pins that class is skipped and says so; with DOCUMIND_REQUIRE_LIBS=1, as
CI's chat-pins step sets it, a missing pin is an error instead.
"""
import importlib.util
import io
import json
import logging
import math
import os
from pathlib import Path
import random
import re
import sys
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
import context_window as cw                    # noqa: E402 - the standard library and the Desk's rules at import
import desk_router                             # noqa: E402
from shared import desk_rules, identifiers     # noqa: E402

FRAMEWORKS = all(importlib.util.find_spec(m) for m in ("langchain", "langgraph", "langchain_core"))
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
CARD = "4111 1111 1111 1111"                                      # a published test number, Luhn-valid
AADHAAR = "2345 6789 012" + identifiers.verhoeff_digit("23456789012")   # made for the test, Verhoeff-valid
NEW_FILES = ("services/chat/context_window.py", "commands/window_check.py", "commands/tests/test_context_window.py")


def read(*parts) -> str:
    return (KIT.joinpath(*parts)).read_text(encoding="utf-8")


def M(kind, cid=None, calls=(), ref=None):
    """A stand-in message: only what turns() reads."""
    return types.SimpleNamespace(type=kind, id=cid, tool_calls=[{"id": c} for c in calls], tool_call_id=ref)


class TheRuleAlone(unittest.TestCase):
    """What needs no LangChain: the target, the files, the arithmetic, the turns, the write rules on a question."""

    def test_memory_mk_holds_window_check_and_the_makefile_keeps_its_lines(self):
        mk, memory, readme = read("Makefile"), read("mk", "memory.mk"), read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                     # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")]
        self.assertIn("window-check", phony.split())                    # present; later kits append after it
        self.assertRegex(memory, r"(?m)^window-check: \$\(if \$\(LIVE\),guard-project,\)$")   # offline needs no project
        recipe = memory[memory.index("window-check: "):]
        self.assertIn("bash commands/graph-venv.sh commands/window_check.py", recipe)
        self.assertIn("$(if $(LIVE),GOOGLE_CLOUD_PROJECT=$(PROJECT))", recipe)
        for var, flag in (("MODE", "--mode"), ("TURNS", "--turns"), ("HISTORY", "--history"), ("BRAIN", "--brain"),
                          ("SAVE", "--save"), ("LIVE", "--live")):
            self.assertIn(f"$(if $({var}),{flag}", recipe, var)
        for target in ("thread", "replay"):                             # lesson 6.8's targets stay as they were
            self.assertRegex(memory, rf"(?m)^{target}:")
        self.assertIn("`window-check`", readme)
        self.assertIn("`window_check.py`", readme)

    def test_both_chat_pin_steps_run_this_file(self):
        line = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_context_window.py -v"
        self.assertIn(line, read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = ROOT / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                            # the authoring repository's own CI
            self.assertIn(line, repo_ci.read_text(encoding="utf-8"))

    def test_the_new_files_have_their_unowned_rows(self):
        # An UNOWNED.md row until lesson 6.9's page quotes the file; from then on INDEX.md names the lesson.
        unowned, index = read("UNOWNED.md"), read("INDEX.md")
        quoted = set(re.findall(r"^\| `([^`]+)` \| \w+ \| (?!- \|)[^|]+ \|", index, re.M))
        self.assertIn("## Working memory (lesson 6.9)", unowned)
        for f in NEW_FILES:
            self.assertTrue(f"| `{f}` | **6.9**" in unowned or f in quoted, f)
            self.assertTrue((KIT / f).exists(), f)

    def test_nothing_in_the_service_imports_the_window(self):
        imports = re.compile(r"(?m)^\s*(?:import\s+context_window\b|from\s+context_window\s+import\b)|"
                             r"import_module\(\s*['\"]context_window['\"]")
        for root in ("services", "shared", "smoke"):
            for path in (KIT / root).rglob("*.py"):
                if path.name != "context_window.py":
                    self.assertNotRegex(path.read_text(encoding="utf-8", errors="replace"), imports, path)

    def test_the_rules_constants(self):
        self.assertEqual(cw.PREV_CHARS, desk_router.PREV_CHARS)        # the Desk's own number, not a copy
        self.assertEqual(cw.PREV_CHARS, 300)
        self.assertEqual(cw.MODES, ("full", "windowed"))
        self.assertEqual(json.loads(cw.CLEARED), {"cleared": True,
                                                  "reason": "evidence from an earlier turn: search again if you need it"})
        self.assertIn('prev = desk_rules.mask(body.prev_question)[0][:desk_router.PREV_CHARS]',
                      read("services", "chat", "desk.py"))              # the Desk's order: mask, then cut

    def test_plan_at_its_edges(self):
        self.assertEqual(cw.plan([], [], 2000, 40), (0, 0, False))                   # nothing earlier
        self.assertEqual(cw.plan([100, 100], [[5], [5]], 200, 40), (2, 0, False))    # all fit: no line
        self.assertEqual(cw.plan([100, 100, 100], [[10], [10], [10]], 250, 30), (2, 1, True))
        self.assertEqual(cw.plan([100, 100, 100], [[10], [10], [10]], 0, 30), (0, 0, False))   # no room for the line
        self.assertEqual(cw.plan([100, 100], [[5], [5]], 50, 40), (0, 2, True))     # the line, two questions, no turn
        self.assertEqual(cw.plan([100, 10], [[5], [5]], 60, 40), (1, 1, True))       # newest first, then the line
        self.assertEqual(cw.plan([10, 300, 10], [[5], [5], [5]], 100, 40), (1, 2, True))   # a big turn stops the window
        self.assertEqual(cw.plan([30, 30], [[5], [5]], 40, 50), (1, 0, False))       # turns without their line

    def test_plan_on_random_sizes(self):
        rng = random.Random(69)
        for _ in range(3000):
            n = rng.randint(0, 12)
            sizes = [rng.randint(1, 400) for _ in range(n)]
            qs = [[rng.randint(1, 80) for _ in range(rng.randint(0, 2))] for _ in range(n)]
            budget, head = rng.choice([0, 30, 200, 600, 2000, 10**6]), rng.randint(10, 60)
            kept, listed, line = cw.plan(sizes, qs, budget, head)
            dropped = [q for x in qs[:n - kept] for q in x]
            used = sum(sizes[n - kept:]) + (head if line else 0) + sum(dropped[len(dropped) - listed:] if listed else [])
            self.assertLessEqual(used, budget, (sizes, qs, budget, head))
            self.assertTrue(0 <= kept <= n and 0 <= listed <= len(dropped))
            if sum(sizes) <= budget:
                self.assertEqual((kept, listed, line), (n, 0, False))
                continue
            self.assertEqual(line, head <= budget)
            self.assertLess(kept, n)
            room = budget - (head if line else 0) - sum(sizes[n - kept:])
            self.assertGreater(sizes[n - kept - 1], room)              # the next older turn did not fit
            if line and listed < len(dropped):
                left = room - sum(dropped[len(dropped) - listed:] if listed else [])
                self.assertGreater(dropped[len(dropped) - listed - 1], left)
            if not line:
                self.assertEqual(listed, 0)

    def test_turns_start_at_each_persons_message_and_join_a_split_pair(self):
        self.assertEqual(cw.turns([]), [])
        t = [M("human", "h1"), M("ai", "a1", ["c1"]), M("tool", "t1", ref="c1"), M("ai", "z1"),
             M("human", "h2"), M("ai", "z2")]
        self.assertEqual([[m.id for m in u] for u in cw.turns(t)], [["h1", "a1", "t1", "z1"], ["h2", "z2"]])
        lead = [M("ai", "x"), M("human", "h1"), M("ai", "z1")]          # before the first question: a turn of its own
        self.assertEqual([[m.id for m in u] for u in cw.turns(lead)], [["x"], ["h1", "z1"]])
        # a call left open, a new question, then a repair answering the old call: three turns become one
        split = [M("human", "h1"), M("ai", "z1"), M("human", "h2"), M("ai", "a2", ["c2"]), M("human", "h3"),
                 M("ai", "a3", ["c3"]), M("tool", "t3", ref="c3"), M("tool", "t2", ref="c2"), M("ai", "z3"),
                 M("human", "h4")]
        self.assertEqual([[m.id for m in u] for u in cw.turns(split)],
                         [["h1", "z1"], ["h2", "a2", "h3", "a3", "t3", "t2", "z3"], ["h4"]])
        orphan = [M("human", "h1"), M("tool", "t0", ref="nowhere"), M("human", "h2")]   # no call anywhere: as it is
        self.assertEqual([[m.id for m in u] for u in cw.turns(orphan)], [["h1", "t0"], ["h2"]])

    def test_an_earlier_question_is_masked_then_cut_to_the_desks_300(self):
        self.assertEqual(cw.carried("short"), ("short", 0, False))
        self.assertEqual(cw.carried("x" * 500), ("x" * 300, 0, True))
        q, n, cut = cw.carried(f"My card {CARD} and Aadhaar {AADHAAR}, please")
        self.assertEqual((q, n, cut), ("My card [card no.] and Aadhaar [Aadhaar], please", 2, False))
        # masked first, then cut: a number across the 300th character leaves no digit of it behind
        q, n, cut = cw.carried("a" * 290 + " " + CARD + " " + "b" * 50)
        self.assertEqual((n, cut, len(q)), (1, True, 300))
        self.assertNotRegex(q, r"\d")
        self.assertEqual(q, ("a" * 290 + " [card no.] " + "b" * 50)[:300])

    def test_the_command_refuses_before_it_runs_anything(self):
        import window_check as wc
        for argv, said in ((["--turns", "0"], "TURNS must be 1 to 20"), (["--turns", "21"], "TURNS must be 1 to 20"),
                           (["--history", "-1"], "HISTORY is a number of tokens")):
            err = io.StringIO()
            with patch("sys.stderr", err):
                self.assertEqual(wc.main(argv), 2, argv)
            self.assertIn(said, err.getvalue())
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GOOGLE_CLOUD_PROJECT", None)
            err = io.StringIO()
            with patch("sys.stderr", err):
                self.assertEqual(wc.main(["--live", "--turns", "1"]), 2)
            self.assertIn("a live run needs GOOGLE_CLOUD_PROJECT", err.getvalue())
        self.assertEqual(len(wc.QUESTIONS), 20)
        self.assertEqual([i for i, q in enumerate(wc.QUESTIONS, 1) if desk_rules.mask(q)[1]], [6])     # one card
        self.assertEqual([i for i, q in enumerate(wc.QUESTIONS, 1) if len(q) > 300], [9])
        self.assertEqual([q for q in wc.QUESTIONS if desk_rules.gate(q)], [])  # none the Desk's door would take

    def test_the_rs0_lanes_ranking_tokenises_each_chunk_once_and_ranks_as_before(self):
        """13 October 2026: documind_tools._lexical_rank tokenised every chunk on every search and matched each word
        against every token - 1.5 s a search over acme's chunks, so window-check's searches took minutes and, on a busy
        machine, could pass retrieve's budget. Each chunk's counts are now cached and each word matched over the
        vocabulary: the ranking must be the textbook one, to the last float, for every question the check asks."""
        import window_check as wc
        from shared import documind_tools as dt
        from shared import local_corpus as lc

        keep = ("hr_policy_2026.md", "payment_of_gratuity_act_1972.md", "dpdp_act_2023.md")
        rows = [(c["text"], {"chunk_id": c["chunk_id"]}) for c in lc.chunks_for("acme") if c["source_uri"].endswith(keep)]

        def textbook(query):                # _lexical_rank's body as it was until 13 October 2026: the reference
            words = dt._words(query)
            if not rows or not words:
                return [], {}
            toks = [re.findall(r"[a-z0-9]+", text.lower()) for text, _ in rows]
            n, avgdl = len(toks), sum(map(len, toks)) / max(1, len(toks))
            tf = [{w: sum(1 for t in doc if dt._match(w, t)) for w in words} for doc in toks]
            df = {w: sum(1 for d in tf if d[w]) for w in words}
            if n >= 8:
                words = [w for w in words if df[w] / n <= 0.5]
            if not words:
                return [], {}
            idf = {w: math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5)) for w in words}
            k1, b = 1.5, 0.75
            ranked = []
            for (text, meta), doc, f in zip(rows, toks, tf):
                hit = [w for w in words if f[w]]
                if not hit:
                    continue
                s = sum(idf[w] * f[w] * (k1 + 1) / (f[w] + k1 * (1 - b + b * len(doc) / avgdl)) for w in hit)
                ranked.append((s, hit, text, meta))
            ranked.sort(key=lambda r: (-r[0], -len(r[1]), len(r[2])))
            return ranked, idf

        dt._counted.cache_clear()
        for q in wc.QUESTIONS + ("What is the notice period?", "sabbatical"):
            self.assertEqual(dt._lexical_rank(q, rows), textbook(q), q)
        self.assertEqual(dt._counted.cache_info().misses, len({text for text, _ in rows}))   # once each, 22 searches

    def test_a_row_says_when_a_limit_stopped_its_turn(self):
        """13 October 2026: a LIVE=1 row printed no stopped_by, so a turn a limit ended read like any other."""
        import window_check as wc
        usage = {"tokens_in": 900, "cached_tokens": 0, "tokens_out": 40, "model_calls": 12, "stopped_by": "model_calls"}
        row = {"usage": usage, "largest": None, "estimate": 880, "rupees": 0.25, "citations": [],
               "answer": "I stopped this turn at one of its limits before I could finish."}
        self.assertIn("  calls 12  Rs 0.25; stopped by model_calls\n", wc._live_row(row, "full", False))
        self.assertNotIn("stopped by", wc._live_row({**row, "usage": {**usage, "stopped_by": None}}, "full", False))
        largest = {"context_tokens": 900, "ceiling": 2500, "kept": 1, "brought_forward": 0, "cleared": 0, "masked": 0,
                   "cut": 0, "unanswered": 0}
        table = {**row, "turn": 3, "thread_messages": 12, "thread_tokens": 1500, "largest": largest}
        for mode in ("full", "windowed"):
            self.assertTrue(wc._offline_row(table, mode).endswith("  (stopped by model_calls)"), mode)
            self.assertNotIn("stopped", wc._offline_row({**table, "usage": {**usage, "stopped_by": None}}, mode))


# ----------------------------------------------------------------------------- the library half
def norm(messages) -> list:
    """Messages compared by what a model reads of them: kind, text, the calls asked and the call a result answers."""
    return [(m.type, cw.text_of(m.content), [(c["name"], c.get("args")) for c in getattr(m, "tool_calls", None) or []],
             getattr(m, "tool_call_id", None), getattr(m, "status", None)) for m in messages]


@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins: pip install -r services/chat/requirements.txt")
class TheWindowOnTheKitsBrains(unittest.TestCase):
    """window(), full(), windowed() and middleware() on LangChain's messages and the kit's own brains."""

    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        logging.disable(logging.CRITICAL)
        import brains
        import limits
        from langchain_core.language_models.chat_models import BaseChatModel
        from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
        from langchain_core.outputs import ChatGeneration, ChatResult
        from pydantic import Field

        cls.brains, cls.limits = brains, limits
        cls.AI, cls.Human, cls.System, cls.Tool = AIMessage, HumanMessage, SystemMessage, ToolMessage

        class Recorder(BaseChatModel):
            """The model a brain calls, recording what each call was sent: it searches for the newest question, then
            answers from the first passage, as lesson 6.8's script does."""
            seen: list = Field(default_factory=list)

            @property
            def _llm_type(self) -> str:
                return "recorder"

            def bind_tools(self, tools, **kw):
                return self

            def _generate(self, messages, stop=None, run_manager=None, **kw):
                self.seen.append(list(messages))
                last = messages[-1]
                if last.type == "human":                       # the call's id is the call's number: two runs agree
                    text = cw.text_of(last.content).rsplit("\n\n", 1)[-1]
                    msg = AIMessage("", tool_calls=[{"name": "retrieve", "args": {"query": text[:80]},
                                                     "id": f"call_{len(self.seen)}", "type": "tool_call"}])
                elif last.type == "tool":
                    body = json.loads(cw.text_of(last.content))
                    quote = (body.get("citations") or [{}])[0].get("quote", "nothing")
                    msg = AIMessage(f"The first passage says {quote[:60]!r} [1].")
                else:
                    msg = AIMessage("Nothing further.")
                return ChatResult(generations=[ChatGeneration(message=msg)])

        class Script(FakeMessagesListChatModel):
            seen: list = Field(default_factory=list)

            def bind_tools(self, tools, **kw):
                return self

            def _generate(self, messages, stop=None, run_manager=None, **kw):
                self.seen.append(list(messages))
                return super()._generate(messages, stop=stop, run_manager=run_manager, **kw)

        cls.Recorder, cls.Script = Recorder, Script

        def passages(query, **kw):                 # the one retrieve(), answered here: two passages, each long
            return {"answerable": True, "confidence": "high", "citations": [
                {"chunk_id": f"acme:hr_policy_2026#S-{i}", "source_uri": "gs://b/acme/hr_policy_2026.md", "page": 1,
                 "quote": f"Section {i} for {query[:20]}: " + "policy text " * 60, "score": 0.9 - i / 10}
                for i in range(2)]}

        cls.passages = staticmethod(passages)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    # ---- helpers
    def thread(self, rng, turns, *, numbers=True, long_every=0, open_at=None, late=False, blocks=False):
        """A thread as a checkpoint would hold it: turns of a question, rounds of parallel calls and results
        (refusals among them), an answer. open_at leaves that turn's call unanswered and asks the next question; with
        late, the next turn's first message is that call's result (a repair after a new question), so the pair spans
        two turns, which turns() joins."""
        out = []
        for t in range(turns):
            q = rng.choice(["What is the notice period?", "And during probation?", "How is gratuity computed?"])
            if numbers and rng.random() < 0.3:
                q += f" My card is {CARD}." if rng.random() < 0.5 else f" Aadhaar {AADHAAR}."
            if long_every and t % long_every == 0:
                q += " " + "context " * rng.randint(40, 499)
            out.append(self.Human(q[:4000], id=str(uuid.uuid4())))
            if late and open_at is not None and t == open_at + 1:
                out.append(self.Tool(json.dumps({"error": "the turn stopped before this call ran"}), name="retrieve",
                                     tool_call_id=f"open{open_at}", id=str(uuid.uuid4())))
            if open_at == t:
                out.append(self.AI("", tool_calls=[{"name": "retrieve", "args": {"query": q[:40]}, "id": f"open{t}",
                                                     "type": "tool_call"}], id=str(uuid.uuid4())))
                continue
            for r in range(rng.randint(0, 3)):
                calls = [{"name": rng.choice(["retrieve", "calculate_processing_cost"]), "args": {"query": f"q{t}{r}{k}"},
                          "id": f"c{t}_{r}_{k}", "type": "tool_call"} for k in range(rng.randint(1, 3))]
                out.append(self.AI(rng.choice(["", "Let me check."]), tool_calls=calls, id=str(uuid.uuid4())))
                for c in calls:
                    if rng.random() < 0.15:
                        out.append(self.Tool(json.dumps({"error": f"{c['name']} requires manual approval"}),
                                             tool_call_id=c["id"], name=c["name"], status="error", id=str(uuid.uuid4())))
                    else:
                        body = {"citations": [{"quote": "w " * rng.randint(10, 900)}]}
                        if numbers and rng.random() < 0.1:
                            body["citations"][0]["quote"] += f" card {CARD}"
                        out.append(self.Tool(json.dumps(body), tool_call_id=c["id"], name=c["name"],
                                             id=str(uuid.uuid4())))
            answer = "The answer is " + "x " * rng.randint(5, 300) + (f" (your card {CARD})" if numbers and
                                                                    rng.random() < 0.2 else "")
            content = [{"type": "text", "text": answer}, {"type": "thinking", "thinking": "..."}] if blocks and \
                rng.random() < 0.5 else answer
            out.append(self.AI(content, id=str(uuid.uuid4())))
        return out

    def check(self, given, sent, rep, budget):
        """Every promise the window makes, on one call."""
        system, thread = cw._split(given)
        units = cw.turns(thread)
        newest = units[-1] if units else []
        # the ceiling, as the report states it and as the messages sent add up
        self.assertEqual(rep["context_tokens"], cw.tokens(sent))
        self.assertEqual(rep["ceiling"], rep["floor_tokens"] + budget)
        self.assertLessEqual(rep["context_tokens"], rep["ceiling"])
        self.assertLessEqual(rep["earlier_tokens"], budget)
        self.assertEqual(rep["thread_tokens"], cw.tokens(thread))
        # the system prompt: the same messages, first
        self.assertGreaterEqual(len(sent), len(system))
        self.assertTrue(all(a is b for a, b in zip(sent, system)))
        # the newest turn whole, last, every message but its question the very one stored
        tail = sent[len(sent) - len(newest):] if newest else []
        self.assertEqual([m.id for m in tail], [m.id for m in newest])
        last_q = max((i for i, m in enumerate(newest) if m.type == "human"), default=None)
        for i, (a, b) in enumerate(zip(tail, newest)):
            if b.type != "human":
                self.assertIs(a, b)
            elif i == last_q:
                masked = desk_rules.mask(cw.text_of(b.content))[0]
                text = cw.text_of(a.content)
                self.assertTrue(text == masked or (rep["line"] and text == rep["line"] + "\n\n" + masked), text[:200])
        # the thread's order: what is sent is a part of what is stored, in the same order
        ids = [m.id for m in thread]
        pos = [ids.index(m.id) for m in sent[len(system):] if m.id in ids]
        self.assertEqual(pos, sorted(pos))
        self.assertEqual(len(pos), len(sent) - len(system))            # nothing added: the line rides in a message
        # no pair split, and no answered call left open
        body = sent[len(system):]
        asked = {c["id"] for m in body for c in getattr(m, "tool_calls", None) or []}
        answered_in_thread = {m.tool_call_id for m in thread if m.type == "tool"}
        answered = {m.tool_call_id for m in body if m.type == "tool"}
        for m in body:
            if m.type == "tool":
                self.assertIn(m.tool_call_id, asked)                       # a result's call is there
        self.assertEqual(asked & answered_in_thread, answered & asked)     # a call's result is there, if it had one
        self.assertEqual(rep["unanswered"], len(asked - answered))
        self.assertLessEqual(rep["unanswered"], cw._open_calls(thread))
        # the write rules: no number in what the person wrote, in the line or in an earlier answer; earlier questions,
        # kept or brought forward, at most 300 characters
        newest_ids = {m.id for m in newest}
        newest_q = newest[last_q].id if last_q is not None else None
        line = rep["line"]
        if line:
            self.assertEqual(identifiers.find_numbers(line), [])
            for item in re.findall(r'\(\d+\) ("(?:[^"\\]|\\.)*")', line):
                self.assertLessEqual(len(json.loads(item)), 300)
        for m in body:
            text = cw.text_of(m.content)
            if line and text.startswith(line + "\n\n"):
                text = text[len(line) + 2:]
            if m.type == "human":
                self.assertEqual(identifiers.find_numbers(text), [], text[:120])
                if m.id != newest_q:
                    self.assertLessEqual(len(text), 300)
            elif m.id not in newest_ids:
                self.assertEqual(identifiers.find_numbers(text), [], text[:120])
                if m.type == "tool" and getattr(m, "status", "success") != "error":
                    self.assertEqual(m.content, cw.CLEARED)
                elif m.type == "tool":                                   # a refusal stays, masked, never cleared
                    stored = next(x for x in thread if x.id == m.id)
                    self.assertEqual(text, desk_rules.mask(cw.text_of(stored.content))[0])

    def calls_of(self, thread):
        """The message lists a brain would send at each model call of this thread: before each model message."""
        sys_msg = self.System(content=self.brains.SYSTEM)
        return [[sys_msg] + thread[:i] for i, m in enumerate(thread) if m.type == "ai"] + [[sys_msg] + thread]

    # ---- window(), on its own
    def test_every_promise_on_generated_threads(self):
        rng = random.Random(6.9)
        checked, joined = 0, 0
        for seed in range(40):
            t = self.thread(rng, rng.randint(1, 14), long_every=rng.choice([0, 3]), blocks=seed % 2 == 0,
                            open_at=rng.choice([None, None, 0, 1]), late=seed % 3 == 0)
            joined += len(cw.turns(t)) < sum(m.type == "human" for m in t)       # a pair across two turns
            given_all = self.calls_of(t)
            for given in given_all[-4:] + given_all[:2]:
                before = [m.model_dump() for m in given]
                for budget in (0, 40, 300, 1200, 2000, 10**6):
                    sent, rep = cw.window(given, history_tokens=budget)
                    self.check(given, sent, rep, budget)
                    checked += 1
                self.assertEqual([m.model_dump() for m in given], before)    # nothing given was changed
        self.assertGreater(checked, 1000)
        self.assertGreater(joined, 0)

    def test_an_oversized_newest_turn_goes_whole_and_alone(self):
        rng = random.Random(1)
        t = self.thread(rng, 6, numbers=False)
        big = [self.Human("How is gratuity computed? " + "detail " * 3000, id="big"),
               self.AI("", tool_calls=[{"name": "retrieve", "args": {"query": "g"}, "id": "cb", "type": "tool_call"}],
                       id="ab"),
               self.Tool(json.dumps({"citations": [{"quote": "q " * 20000}]}), tool_call_id="cb", name="retrieve",
                         id="tb")]
        given = [self.System(content="sys")] + t + big
        sent, rep = cw.window(given, history_tokens=500)
        self.check(given, sent, rep, 500)
        self.assertGreater(rep["floor_tokens"], 10000)                  # the floor alone is far over 500
        self.assertEqual([m.id for m in sent[-3:]], ["big", "ab", "tb"])
        self.assertIs(sent[-1], big[-1])
        self.assertEqual(cw.text_of(sent[-3].content).rsplit("\n\n", 1)[-1], big[0].content)   # whole, not cut

    def test_an_earlier_calls_arguments_are_masked_with_the_rest(self):
        """13 October 2026: the window masked a person's words and the model's answers, not the arguments of an earlier
        tool call, so a card number the model repeated in its search query went to the model again, whole."""
        probe = [self.Human(f"My card {CARD} was charged twice", id="h1"),
                 self.AI("", tool_calls=[{"name": "retrieve", "args": {"query": f"card {CARD} charged", "k": 3},
                                          "id": "c1", "type": "tool_call"}], id="a1"),
                 self.Tool(json.dumps({"citations": [{"quote": "x " * 50}]}), tool_call_id="c1", name="retrieve", id="t1"),
                 self.AI(f"Your card {CARD} shows two charges [1].", id="z1"), self.Human("And then?", id="hN")]
        given = [self.System(content="sys")] + probe
        sent, rep = cw.window(given, history_tokens=10**6)
        self.check(given, sent, rep, 10**6)
        calls = [c for m in sent for c in (getattr(m, "tool_calls", None) or [])]
        self.assertEqual(calls, [{"name": "retrieve", "args": {"query": "card [card no.] charged", "k": 3}, "id": "c1",
                                  "type": "tool_call"}])
        self.assertNotIn(CARD, json.dumps([m.model_dump() for m in sent]))
        self.assertEqual(rep["masked"], 3)                               # the question, the query and the answer
        self.assertEqual(probe[1].tool_calls[0]["args"]["query"], f"card {CARD} charged")   # nothing given was changed

    def test_the_line_and_the_kept_turns(self):
        turns = [[self.Human(f"Question {i}?" + (f" card {CARD}" if i == 2 else "") + (" long" * 100 if i == 3 else ""),
                             id=f"h{i}"),
                  self.AI("", tool_calls=[{"name": "retrieve", "args": {"query": f"q{i}"}, "id": f"c{i}",
                                           "type": "tool_call"}], id=f"a{i}"),
                  self.Tool(json.dumps({"citations": [{"quote": "p " * 400}]}), tool_call_id=f"c{i}", name="retrieve",
                            id=f"t{i}"),
                  self.AI(f"Answer {i} [1]." + (f" Your card {CARD} is noted." if i == 2 else ""), id=f"z{i}")]
                 for i in range(1, 11)]
        thread = [m for u in turns for m in u] + [self.Human("And the newest?", id="hN")]
        given = [self.System(content="sys")] + thread
        sent, rep = cw.window(given, history_tokens=400)
        self.check(given, sent, rep, 400)
        self.assertEqual((rep["turns"], rep["kept"] + rep["brought_forward"]), (11, 10))
        kept = [m.id for m in sent if m.type == "human"][:-1]
        self.assertEqual(kept, [f"h{i}" for i in range(11 - rep["kept"], 11)])      # the newest earlier turns
        first = next(m for m in sent if m.type == "human")
        self.assertTrue(cw.text_of(first.content).startswith(rep["line"] + "\n\n"))
        d = rep["brought_forward"]
        self.assertTrue(rep["line"].startswith(f"[Earlier in this conversation, not shown here: turns 1 to {d}."))
        self.assertTrue(rep["line"].endswith("Search again for anything you need from them.]"))
        listed = re.findall(r'\((\d+)\) ("(?:[^"\\]|\\.)*")', rep["line"])
        self.assertEqual(len(listed), rep["listed"])
        self.assertEqual([int(n) for n, _ in listed], list(range(d - rep["listed"] + 1, d + 1)))   # the newest, in order
        for n, q in listed:
            self.assertEqual(json.loads(q), desk_rules.mask(turns[int(n) - 1][0].content)[0][:300])
        # each kept turn: its question and answer as stored but masked, its call as it was, its result cleared
        for i in range(11 - rep["kept"], 11):
            got = {m.id: m for m in sent}
            self.assertIs(got[f"a{i}"], turns[i - 1][1])
            self.assertEqual(got[f"t{i}"].content, cw.CLEARED)
            self.assertEqual(got[f"t{i}"].tool_call_id, f"c{i}")
        self.assertEqual(rep["cleared"], rep["kept"])
        # with everything earlier inside the budget there is no line, and every earlier turn is kept
        sent, rep = cw.window(given, history_tokens=10**6)
        self.assertEqual((rep["kept"], rep["brought_forward"], rep["line"]), (10, 0, None))
        self.assertEqual(rep["masked"], 2)                               # turn 2's question and its answer
        self.assertEqual(rep["cut"], 1)                                  # turn 3's question
        # a budget too small for the line: earlier turns leave without one
        sent, rep = cw.window(given, history_tokens=5)
        self.check(given, sent, rep, 5)
        self.assertEqual((rep["kept"], rep["line"], [m.id for m in sent]), (0, None, [None, "hN"]))

    def test_in_an_earlier_turn_a_refusal_stays_and_a_result_is_cleared(self):
        calls = [{"name": "retrieve", "args": {"query": "q"}, "id": "c1", "type": "tool_call"},
                 {"name": "delete_document", "args": {"name": "x"}, "id": "c2", "type": "tool_call"}]
        refusal = self.Tool(json.dumps({"error": "delete_document requires manual approval"}), name="delete_document",
                            tool_call_id="c2", status="error", id="t2")
        found = self.Tool(json.dumps({"citations": [{"quote": "p " * 200}]}), name="retrieve", tool_call_id="c1",
                          id="t1")
        given = [self.System(content="sys"), self.Human("Search, then delete it.", id="h1"),
                 self.AI("", tool_calls=calls, id="a1"), found, refusal,
                 self.AI("I cannot delete it without approval.", id="z1"), self.Human("Why not?", id="h2")]
        sent, rep = cw.window(given, history_tokens=10**6)
        self.check(given, sent, rep, 10**6)
        got = {m.id: m for m in sent}
        self.assertIs(got["t2"], refusal)                                # as it was: the model reads why
        self.assertEqual(got["t1"].content, cw.CLEARED)
        self.assertEqual((got["t1"].tool_call_id, got["t1"].name), ("c1", "retrieve"))
        self.assertEqual(rep["cleared"], 1)

    def test_a_cut_off_turn_is_passed_as_it_is(self):
        rng = random.Random(3)
        t = self.thread(rng, 5, numbers=False, open_at=1)
        given = [self.System(content="sys")] + t
        sent, rep = cw.window(given, history_tokens=10**6)
        self.check(given, sent, rep, 10**6)
        self.assertEqual(rep["unanswered"], 1)                          # the thread's open call, sent as it was
        self.assertEqual(cw.full(given)[1]["unanswered"], 1)
        sent, rep = cw.window(given, history_tokens=0)
        self.assertEqual(rep["unanswered"], 0)                          # dropped with its turn: never split

    def test_full_returns_the_very_list(self):
        rng = random.Random(4)
        given = [self.System(content="sys")] + self.thread(rng, 8)
        sent, rep = cw.full(given, history_tokens=300)
        self.assertIs(sent, given)
        self.assertEqual((rep["mode"], rep["context_tokens"], rep["cleared"], rep["masked"], rep["cut"]),
                         ("full", cw.tokens(given), 0, 0, 0))
        self.assertEqual(rep["kept"], rep["turns"] - 1)
        self.assertEqual(rep["floor_tokens"], cw.tokens(given[:1] + cw.turns(given[1:])[-1]))   # as stored, unmasked
        self.assertEqual(rep["ceiling"], rep["floor_tokens"] + 300)
        self.assertGreater(rep["context_tokens"], rep["ceiling"])                 # eight turns: over what the window
        for bad in (lambda: cw.windowed(self.Recorder(), "trimmed"), lambda: cw.middleware("window")):   # would send
            with self.assertRaises(ValueError):
                bad()

    # ---- the kit's brains, built with windowed()
    def run_brain(self, name, model, questions, session="s"):
        from langgraph.checkpoint.memory import InMemorySaver
        import shared.documind_tools as dt

        brain = self.brains.LangChainBrain(InMemorySaver(), llm=model) if name == "langchain" else \
            self.brains.LangGraphBrain(InMemorySaver(), llm=model)
        cfg = {"configurable": {"thread_id": f"acme:you:{session}"}}
        outs = []
        with patch.object(dt, "retrieve", self.passages):
            for q in questions:
                outs.append(brain.answer(q, config=cfg, context={"tenant_id": "acme", "user_id": "you",
                                                                  "assertion": "", "brain": name}))
        graph = getattr(brain, "agent", None) or brain.graph
        return brain, outs, graph.get_state(cfg).values["messages"], cfg

    QUESTIONS = ("What is the notice period?", "And during probation?", f"My card {CARD} was charged twice: who approves?",
                 "Explain the purchase policy. " + "Some context. " * 40, "How many days of earned leave carry over?",
                 "When is Form 16 issued?", "How often is access reviewed?", "What was my first question?")

    def test_a_windowed_brain_sends_the_window_of_what_it_holds_and_keeps_everything(self):
        for name in ("langgraph", "langchain"):
            with self.subTest(brain=name):
                rec = self.Recorder()
                model = cw.windowed(rec, history_tokens=300)
                _, outs, thread, _ = self.run_brain(name, model, self.QUESTIONS)
                self.assertEqual(len(thread), 4 * len(self.QUESTIONS))        # every message kept in the checkpoint
                self.assertEqual([cw.text_of(m.content) for m in thread if m.type == "human"], list(self.QUESTIONS))
                self.assertIn(CARD, thread[8].content)                         # stored as typed: the window writes
                ais = [i for i, m in enumerate(thread) if m.type == "ai"]      # nothing back
                self.assertEqual(len(rec.seen), len(ais))
                self.assertEqual(len(model.calls), len(ais))
                for k, i in enumerate(ais):
                    given = [self.System(content=self.brains.SYSTEM)] + thread[:i]
                    sent, rep = cw.window(given, history_tokens=300)
                    self.assertEqual(norm(rec.seen[k]), norm(sent), (name, k))
                    self.assertEqual({x: y for x, y in model.calls[k].items()}, rep)
                    self.check(given, sent, rep, 300)
                self.assertTrue(any(r["brought_forward"] for r in model.calls))
                self.assertNotIn(CARD, json.dumps(norm([m for s in rec.seen for m in s])))   # the model never saw it

    def test_full_mode_is_todays_behaviour(self):
        for name in ("langgraph", "langchain"):
            with self.subTest(brain=name):
                bare, wrapped = self.Recorder(), self.Recorder()
                model = cw.windowed(wrapped, "full", history_tokens=300)
                _, outs_a, thread_a, _ = self.run_brain(name, bare, self.QUESTIONS, "a")
                _, outs_b, thread_b, _ = self.run_brain(name, model, self.QUESTIONS, "b")
                self.assertEqual(len(bare.seen), len(wrapped.seen))
                for a, b in zip(bare.seen, wrapped.seen):
                    self.assertEqual(norm(a), norm(b))                         # the same calls, message for message
                self.assertEqual(norm(thread_a), norm(thread_b))
                self.assertEqual([o["answer"] for o in outs_a], [o["answer"] for o in outs_b])
                self.assertTrue(all(r["mode"] == "full" and r["context_tokens"] == r["system_tokens"] + r["thread_tokens"]
                                    for r in model.calls))
                self.assertIn(CARD, json.dumps(norm([m for s in wrapped.seen for m in s])))   # nothing masked

    def test_the_middleware_sends_the_window_and_keeps_the_checkpoints(self):
        """create_agent with the window last in its middleware: the same checkpoints a turn wrote before (+3 for a turn
        with no tool, +5 with one search, lesson 6.6), and the model sent window() of the state."""
        from langchain.agents import create_agent
        from langgraph.checkpoint.memory import InMemorySaver
        import shared.documind_tools as dt
        import tools

        def script():
            call = self.AI("", tool_calls=[{"name": "retrieve", "args": {"query": "notice"}, "id": "c1",
                                            "type": "tool_call"}])
            return [self.AI("Hello."), call, self.AI("Sixty days [1]."), self.AI("Hello again.")]

        counts, seen = {}, {}
        for form in ("kit", "window"):
            saver, model = InMemorySaver(), self.Script(responses=script())
            brain = self.brains.LangChainBrain.__new__(self.brains.LangChainBrain)
            mw = [self.limits.TurnLimitsMiddleware(), self.brains._guard_middleware()]
            reports = []
            if form == "window":
                mw.append(cw.middleware(history_tokens=0, calls=reports))
            brain.agent = create_agent(model=model, tools=tools.TOOLS, system_prompt=self.brains.SYSTEM,
                                       middleware=mw, checkpointer=saver)
            cfg = {"configurable": {"thread_id": "acme:you:mw"}}
            got = []
            with patch.object(dt, "retrieve", self.passages):
                for q in ("Hi", "What is the notice period?", "Thanks"):
                    before = len(list(saver.list(cfg)))
                    brain.answer(q, config=cfg, context={"tenant_id": "acme", "user_id": "you", "assertion": ""})
                    got.append(len(list(saver.list(cfg))) - before)
            counts[form], seen[form] = got, model.seen
            if form == "window":
                thread = brain.agent.get_state(cfg).values["messages"]
                ais = [i for i, m in enumerate(thread) if m.type == "ai"]
                self.assertEqual(len(reports), len(ais))
                for k, i in enumerate(ais):
                    sent, rep = cw.window([self.System(content=self.brains.SYSTEM)] + thread[:i], history_tokens=0)
                    self.assertEqual(norm(model.seen[k]), norm(sent))
                    self.assertEqual(reports[k], rep)
                self.assertEqual(len(thread), 2 + 4 + 2)                       # every message kept
        self.assertEqual(counts["kit"], [3, 5, 3])                             # lesson 6.6's counts, without the window
        self.assertEqual(counts["window"], counts["kit"])                      # and with it
        self.assertEqual(len(seen["window"][-1]), 2)                           # budget 0: the system prompt and "Thanks"
        self.assertGreater(len(seen["kit"][-1]), 2)

    # ---- make window-check
    def small_corpus(self):
        """The Rs 0 lane's acme corpus cut to five documents, so the twenty turns' searches are quick."""
        from shared import local_corpus as lc
        real = lc.chunks_for
        keep = ("hr_policy_2026.md", "payment_of_gratuity_act_1972.md", "payment_of_bonus_act_1965.md",
                "dpdp_act_2023.md", "maternity_benefit_act_1961.md")
        rows = [r for r in real("acme") if r["source_uri"].endswith(keep)]
        return patch.object(lc, "chunks_for", lambda tenant: list(rows))

    def test_window_check_offline_in_both_modes(self):
        import window_check as wc

        runs, printed = {}, {}
        with self.small_corpus():                    # its searches find less, so a smaller budget shows the line
            for mode in ("windowed", "full"):
                out = io.StringIO()
                runs[mode] = wc.run_offline(mode, 20, "langchain", 600, out=out)
                printed[mode] = out.getvalue()
        win, full = runs["windowed"], runs["full"]
        self.assertEqual(len(win), 20)
        calls = [r for row in win for r in row["calls"]]
        self.assertEqual(len(calls), 40)
        self.assertTrue(all(r["context_tokens"] <= r["ceiling"] and r["budget"] == 600 for r in calls))
        sizes = [row["thread_tokens"] for row in win]
        self.assertEqual(sizes, sorted(sizes))                                 # the thread grows
        self.assertEqual([row["thread_messages"] for row in win], list(range(4, 84, 4)))
        self.assertGreater(win[-1]["largest"]["brought_forward"], 0)           # the line by turn 20
        self.assertLess(win[-1]["largest"]["context_tokens"], full[-1]["largest"]["context_tokens"])
        self.assertEqual(win[5]["largest"]["masked"], 1)                       # turn 6's card, masked before it is read
        self.assertEqual(win[9]["largest"]["cut"], 1)                          # turn 9's question, carried into turn 10
        last = [r for r in full[-1]["calls"]][-1]
        self.assertEqual(last["context_tokens"], last["system_tokens"] + last["thread_tokens"])
        self.assertEqual(sum(r["masked"] + r["cut"] + r["cleared"] for row in full for r in row["calls"]), 0)
        over = [row["turn"] for row in full if row["largest"]["context_tokens"] > row["largest"]["ceiling"]]
        self.assertTrue(over and over == list(range(over[0], 21)))            # over the ceiling, and staying over
        for a, b in zip(full, win):
            if not desk_rules.mask(a["question"])[1]:
                self.assertEqual(a["answer"], b["answer"], a["turn"])          # the script reads only the newest turn
        p = printed["windowed"]
        self.assertIn("make window-check MODE=windowed: 20 turns of one conversation, offline, Rs 0", p)
        self.assertIn("at most 600 tokens", p)
        self.assertIn("Every call's context was within its ceiling: yes.", p)
        self.assertEqual(len(re.findall(r"(?m)^ +\d+ +\d+ +[\d,]+ ", p)), 20)
        self.assertIn("make window-check MODE=full", printed["full"])
        self.assertIn(f"From turn {over[0]} on, the largest call was over the ceiling", printed["full"])
        self.assertNotIn("4111", p + printed["full"])                          # the table names no number

    def test_the_live_path_on_a_scripted_model(self):
        import thread_replay as rp
        import window_check as wc
        from shared import documind_tools as dt

        out = io.StringIO()
        saved = (dt.retrieve, dt.PROFILE, dt._id_token)
        with self.small_corpus(), rp.no_network():
            rows = wc.run_live(3, "langgraph", 300, llm_factory=lambda: rp.scripted([]), out=out)
        self.assertEqual((dt.retrieve, dt.PROFILE, dt._id_token), saved)     # the Rs 0 lane put back
        self.assertEqual({m: len(r) for m, r in rows.items()}, {"full": 3, "windowed": 3})
        self.assertNotEqual(rows["full"][0]["calls"][0]["mode"], rows["windowed"][0]["calls"][0]["mode"])
        p = out.getvalue()
        self.assertIn("full against windowed with a scripted model", p)
        self.assertIn("the two answers cited the same sources on 3 of 3 turns", p)
        self.assertEqual(p.count("\nturn "), 3)
        self.assertEqual(rows["full"][2]["answer"], rows["windowed"][2]["answer"])

        class Boom(Exception):
            pass

        def explode(*a, **k):
            raise Boom("the model refused the request")

        with self.small_corpus(), rp.no_network(), patch.object(wc, "ask", explode):
            with self.assertRaises(wc.TurnFailed) as caught:
                wc.run_live(2, "langgraph", None, llm_factory=lambda: rp.scripted([]), out=io.StringIO())
        self.assertIn("turn 1, the full conversation: Boom: the model refused the request", str(caught.exception))
        self.assertEqual((dt.retrieve, dt.PROFILE, dt._id_token), saved)


if __name__ == "__main__":
    unittest.main()
