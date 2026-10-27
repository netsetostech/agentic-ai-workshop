"""Offline tests for evals/prompt_bench.py (W2-B, workshop lessons 3.1, 3.2 and 3.3): each row's pool read once and held
fixed, the recorder's thinking level and temperature, SYSTEM edited in memory with generator.py untouched, a report's
failing rows, the gate's own scoring of every answer, the rupees, and the lane's identifiers printed as the pages
print them.

Run with ``python -m unittest discover -s evals/tests -p test_prompt_bench.py`` from deploy/. CI's shared interpreter has
pydantic and none of rag-api's pins, so services/rag-api/generator.py is lifted as tools/check_retrieval.py lifts it: its
functions, classes and constants, from the file as it is, node by node with ast, into a module of their own, with the
library calls replaced at the seam (genai.Client, google.genai's types and errors, fastapi's HTTPException). What
answers here is the kit's own generate() - the packing, the prompt, the schema, the truncation retry, resolve() - over a
scripted model. Nothing reaches a network: /v1/passages and /v1/sources are stand-ins, and the passages are the kit's
handbook cut by the kit's own chunker (shared/documind_corpus.py), with ids minted the way the ingest worker mints them.
One test runs the recorder on google-genai's own types: it skips when the library is missing, and DOCUMIND_REQUIRE_LIBS=1
turns that skip into a failure.
"""
from __future__ import annotations

import ast
import contextlib
import functools
import hashlib
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import types
from types import SimpleNamespace
import unittest
from unittest.mock import patch

EVALS = Path(__file__).resolve().parents[1]
KIT = EVALS.parent
API = KIT / "services" / "rag-api"
GENERATOR = API / "generator.py"
if str(KIT) not in sys.path:
    sys.path.insert(0, str(KIT))              # shared/: the answer contract rag-api's schemas.py imports


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module                # a dataclass under `from __future__ import annotations` looks itself up here
    spec.loader.exec_module(module)
    return module


pb = load(EVALS / "prompt_bench.py", "prompt_bench_under_test")
schemas = load(API / "schemas.py", "schemas_bench_test")
budget = load(API / "context_budget.py", "context_budget_bench_test")
chunker = load(KIT / "shared" / "documind_corpus.py", "documind_corpus_bench_test")

GOLDEN = pb.run_eval.load_golden()
Q = {r["id"]: r["question"] for r in GOLDEN}
BY_ID = {r["id"]: r for r in GOLDEN}
URI = "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md"
RAW = (EVALS / "corpus" / "acme" / "hr_policy_2026.md").read_bytes()
SHA = hashlib.sha256(RAW).hexdigest()
CHUNKS = chunker.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "text": RAW.decode("utf-8"),
                                 "source_uri": URI}, "acme")
SETTINGS = {"project_id": "documind-ai-YOUR-ID", "region": "us-central1", "generator_model": "gemini-3.6-flash",
            "model_backend": "vertex", "max_context_tokens": 8000, "max_answer_tokens": 2048, "generator_location": "",
            "litellm_url": "", "gateway_timeout_s": 90.0}
ASSIGNS = ("SYSTEM", "DATED_RULE", "GATEWAY_JSON_RULE", "GATEWAY_ROUTES", "_gateway_token", "RETRY", "_client", "log")
API_URL = "http://lane.invalid"


def pool(*indexes) -> list[dict]:
    """acme's handbook as /v1/passages returns it: the kit's chunks at these indexes, in the route's shape, each id the
    worker's {tenant}:{sha256}#{i}."""
    return [{"n": n, "chunk_id": f"acme:{SHA}#{i}", "source_uri": URI, "page": CHUNKS[i]["page_start"],
             "doc_type": "policy", "kind": CHUNKS[i]["kind"], "section": CHUNKS[i].get("section"), "text": CHUNKS[i]["text"]}
            for n, i in enumerate(indexes, 1)]


POOLS = {Q["lk-06"]: pool(1, 2, 3, 4, 5, 6),            # NP-03 first: "serves a notice period of 60 days"
         Q["rf-01"]: pool(6, 7, 8, 9, 10, 11)}          # no sabbatical anywhere
LIST_PRICES = patch.object(pb.prices, "PROFILE", "gcp")  # DOCUMIND_PROFILE=local would price every call at 0


def setUpModule():
    LIST_PRICES.start()


def tearDownModule():
    LIST_PRICES.stop()


# --------------------------------------------------------------------- generator.py, lifted
class HTTPException(Exception):
    """fastapi's, as generator.py raises it."""

    def __init__(self, status_code, detail=""):
        super().__init__(detail)
        self.status_code, self.detail = status_code, detail


class APIError(Exception):
    """google.genai.errors.APIError, as generator.py reads it: a code."""

    def __init__(self, code, message=""):
        super().__init__(message)
        self.code = code


FAKE_TYPES = SimpleNamespace(GenerateContentConfig=lambda **kw: kw, ThinkingConfig=lambda **kw: kw,
                             Part=SimpleNamespace(from_uri=lambda **kw: kw))


def lifted_generator(model, genai_types=FAKE_TYPES, **settings):
    """services/rag-api/generator.py's functions, classes and constants, lifted from the file with ast into a module of
    their own, the library calls replaced: genai.Client builds `model`, the scripted Gemini; `genai_types` is a stand-in
    that keeps a config as a dict, or google.genai.types itself. Its log lines are kept in `logged`."""
    import pydantic
    mod = types.ModuleType("generator_lifted")
    mod.__file__ = str(GENERATOR)
    mod.__dict__.update({"json": json, "logging": logging, "re": re, "time": time, "SimpleNamespace": SimpleNamespace,
                         "httpx": SimpleNamespace(), "HTTPException": HTTPException, "ValidationError": pydantic.ValidationError,
                         "lru_cache": functools.lru_cache, "genai": SimpleNamespace(Client=lambda **kw: model),
                         "errors": SimpleNamespace(APIError=APIError), "types": genai_types,
                         "DraftCitation": schemas.DraftCitation, "ModelDraft": schemas.ModelDraft,
                         "RAGResponse": schemas.RAGResponse, "resolve": schemas.resolve, "pack_chunks": budget.pack_chunks,
                         "estimate_tokens": budget.estimate_tokens, "TokenBudget": budget.TokenBudget,
                         "TenantCacheManager": None, "settings": SimpleNamespace(**{**SETTINGS, **settings})})
    for node in ast.parse(GENERATOR.read_text(encoding="utf-8")).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) or (
                isinstance(node, ast.Assign) and any(getattr(t, "id", None) in ASSIGNS for t in node.targets)):
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(GENERATOR), "exec"), mod.__dict__)
    mod.logged = []
    mod.log = SimpleNamespace(**{k: (lambda s, k=k: mod.logged.append((k, json.loads(s)))) for k in ("info", "warning", "error")})
    return mod


# --------------------------------------------------------------------- the scripted model and the lane
THOUGHT = {"MINIMAL": 0, "LOW": 120, "MEDIUM": 400, "HIGH": 900}
SOURCE = re.compile(r"\[Source (\d+)\][^\n]*\n(.*?)(?=\n\n\[Source \d+\]|\Z)", re.S)


def sources_in(prompt: str) -> dict[int, str]:
    """{N: the text of [Source N]} in the context generate() packed."""
    context = prompt.split("\nContext:\n", 1)[1].rsplit("\n\nQuestion: ", 1)[0]
    return {int(m.group(1)): m.group(2) for m in SOURCE.finditer(context)}


def context_of(prompt: str) -> str:
    return prompt.split("\nContext:\n", 1)[1]


def level_of(config) -> str:
    tc = config["thinking_config"] if isinstance(config, dict) else config.thinking_config
    level = tc["thinking_level"] if isinstance(tc, dict) else tc.thinking_level
    return getattr(level, "value", level)


def reply(draft, prompt=900, visible=40, thought=None, cached=0, finish="STOP", text=None):
    """A google-genai reply as generator._draft(), _usage() and _finish_reason() read it."""
    return SimpleNamespace(parsed=None if draft is None else schemas.ModelDraft(**draft),
                           text=text if text is not None else (json.dumps(draft) if draft else ""),
                           candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name=finish))], prompt_feedback=None,
                           usage_metadata=SimpleNamespace(prompt_token_count=prompt, candidates_token_count=visible,
                                                          thoughts_token_count=thought, cached_content_token_count=cached))


def notice_draft(n: int, answer: str = "A confirmed E3 serves a notice period of 60 days [{n}].",
                 quote: str = "serves a notice period of 60 days") -> dict:
    return {"answer": answer.format(n=n), "citations": [{"source": n, "quote": quote}], "confidence": "high",
            "answerable": True}


REFUSAL = {"answer": "The handbook does not cover this.", "citations": [], "confidence": "low", "answerable": False}


def grounded(req) -> SimpleNamespace:
    """A model that reads its context: the notice period from the passage that holds NP-03, quoting its clause, and a
    refusal for anything else. The thought tokens rise with the level; the visible ones do not."""
    question = req["prompt"].rsplit("\n\nQuestion: ", 1)[1]
    if "notice period" in question:
        n = next(k for k, t in sources_in(req["prompt"]).items() if "notice period of 60 days" in t)
        draft = notice_draft(n)
    else:
        draft = REFUSAL
    return reply(draft, prompt=len(req["prompt"]) // 4, thought=THOUGHT[level_of(req["config"])])


class Gemini:
    """The scripted model behind generator._client: every request kept, each answered by `answer(request)`."""

    def __init__(self, answer=grounded, order=None):
        self.answer, self.requests, self.order = answer, [], order

    @property
    def models(self):
        return self

    def generate_content(self, *, model, contents, config=None):
        req = {"model": model, "prompt": contents[0], "contents": contents, "config": config}
        self.requests.append(req)
        if self.order is not None:
            self.order.append("generate")
        return self.answer(req)


class Lane:
    """/v1/passages and GET /v1/sources, stood in: each pool by question, every call kept."""

    def __init__(self, pools=None, current=frozenset({SHA}), order=None):
        self.pools, self.current, self.order = POOLS if pools is None else pools, current, order
        self.calls, self.sources_asked = [], []

    def passages(self, api_url, question, tenant, email, token, top_k=6):
        self.calls.append({"api_url": api_url, "question": question, "tenant": tenant, "email": email, "token": token,
                           "top_k": top_k})
        if self.order is not None:
            self.order.append("passages")
        return self.pools.get(question)

    def sources(self, api_url, tenant, token):
        self.sources_asked.append(tenant)
        return None if self.current is None else set(self.current)


def run(argv, model=None, lane=None, report=True, api_url=API_URL, env=None, **settings):
    """prompt_bench.main() over the lifted generator: (exit code, what it printed, the module, the lane, the report)."""
    model = model or Gemini()
    gen = lifted_generator(model, **settings)
    lane = lane or Lane()
    out = io.StringIO()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "bench.json")
        extra = ["--report", path] if report else []
        with patch.dict(os.environ, {"DOCUMIND_ID_TOKEN": "token-abc", "DOCUMIND_USER_EMAIL": "eval@documind.in",
                                     **(env or {})}), contextlib.redirect_stdout(out):
            code = pb.main(list(argv) + ["--api-url", api_url] + extra, generator=gen, passages=lane.passages,
                           sources=lane.sources)
        data = json.loads(Path(path).read_text(encoding="utf-8")) if report and os.path.exists(path) else None
    return code, out.getvalue(), gen, lane, data


def kit_prompt_rules(prompt: str) -> list[str]:
    return [m.group(2) for m in re.finditer(r"^(\d+)\. (.*)$", prompt.split("\n\nContext:\n", 1)[0], re.M)]


# --------------------------------------------------------------------- the tests
class RetrievalTests(unittest.TestCase):
    def test_each_rows_pool_is_read_once_before_anything_is_asked_and_held_fixed(self):
        order = []
        model, lane = Gemini(order=order), Lane(order=order)
        code, out, gen, lane, data = run(["--rows", "rf-01,lk-06", "--levels", "LOW,HIGH", "--runs", "2",
                                          "--add-rule", "Answer in one sentence."], model=model, lane=lane)
        self.assertEqual(code, 0, out)
        # once a row, in golden.jsonl's order (lk-06 before rf-01), with ask()'s top_k, the token and the member
        self.assertEqual([c["question"] for c in lane.calls], [Q["lk-06"], Q["rf-01"]])
        self.assertEqual({(c["top_k"], c["token"], c["email"], c["tenant"], c["api_url"]) for c in lane.calls},
                         {(6, "token-abc", "eval@documind.in", "acme", API_URL)})
        self.assertEqual(order, ["passages"] * 2 + ["generate"] * 16)        # 2 rows x 2 arms x 2 levels x 2 runs
        for q in (Q["lk-06"], Q["rf-01"]):
            seen = {context_of(r["prompt"]) for r in model.requests if r["prompt"].endswith(q)}
            self.assertEqual(len(seen), 1, "every arm, level and run reads the row's one pool")
            self.assertEqual(len([r for r in model.requests if r["prompt"].endswith(q)]), 8)
        self.assertEqual(lane.sources_asked, ["acme"])                        # GET /v1/sources once a tenant
        self.assertIn("pools: POST /v1/passages once a row (top_k 6)", out)

    def test_the_prompt_is_what_generate_builds_from_the_pool(self):
        model = Gemini()
        code, out, gen, lane, data = run(["--rows", "lk-06"], model=model)
        prompt = model.requests[0]["prompt"]
        # the pool, under the names pack_chunks() reads: [Source N] headers name the file, the page and the section
        self.assertTrue(prompt.startswith(gen.SYSTEM + "\n\nContext:\n[Source 1] hr_policy_2026.md, p.1, NP-03"), prompt[:400])
        self.assertTrue(prompt.endswith("\n\nQuestion: " + Q["lk-06"]))
        self.assertNotIn(gen.DATED_RULE.strip(), prompt)                      # /v1/passages returns no effective_from
        self.assertEqual(model.requests[0]["contents"], [prompt])             # and no media_url: no image part
        self.assertEqual(pb.chunks_of(POOLS[Q["lk-06"]])[0]["id"], f"acme:{SHA}#1")

    def test_a_row_with_no_pool_is_not_benched(self):
        lane = Lane(pools={Q["lk-06"]: [], Q["rf-01"]: None})
        model = Gemini()
        code, out, gen, lane, data = run(["--rows", "lk-06,rf-01"], model=model, lane=lane)
        self.assertEqual(code, 1)
        self.assertEqual(model.requests, [])
        self.assertIn("an empty pool, which /v1/query refuses with no model call: not benched", out)
        self.assertIn("no pool read back (an error, a 4xx or the Desk's door): not benched", out)
        self.assertIn("no pool to answer from: nothing benched", out)


class RecorderTests(unittest.TestCase):
    def test_the_level_and_the_temperature_are_sent_and_nothing_else_changes(self):
        model = Gemini()
        code, out, gen, lane, data = run(["--rows", "lk-06", "--levels", "low,MEDIUM,high", "--temperature", "2.0"],
                                         model=model)
        self.assertEqual(code, 0, out)
        sent = [(level_of(r["config"]), r["config"].get("temperature")) for r in model.requests]
        self.assertEqual(sent, [("LOW", None), ("MEDIUM", None), ("HIGH", None), ("LOW", 2.0), ("MEDIUM", 2.0), ("HIGH", 2.0)])
        self.assertTrue(all("temperature" not in r["config"] for r in model.requests[:3]), "the kit arm sends none")
        # the API's own request: generate() with no recorder, and the kit arm at LOW, send the same config
        plain = Gemini()
        own = lifted_generator(plain)
        own.generate(Q["lk-06"], pb.chunks_of(POOLS[Q["lk-06"]]), tenant_id=None, model="gemini-3.6-flash", backend="vertex")
        self.assertEqual(model.requests[0]["config"], plain.requests[0]["config"])
        self.assertEqual(plain.requests[0]["config"]["thinking_config"], {"thinking_level": "LOW"})
        for r in model.requests:
            self.assertEqual({k: v for k, v in r["config"].items() if k not in ("thinking_config", "temperature")},
                             {k: v for k, v in plain.requests[0]["config"].items() if k != "thinking_config"})
        self.assertIs(model.requests[0]["config"]["response_schema"], schemas.ModelDraft)
        calls = [c for a in data["answers"] for c in a["calls"]]
        self.assertEqual([(c["thinking_level"], c["temperature"], c["max_output_tokens"]) for c in calls],
                         [(lv, t, 2048) for t in (None, 2.0) for lv in ("LOW", "MEDIUM", "HIGH")])
        self.assertEqual([c["thought"] for c in calls], [120, 400, 900] * 2)    # thought apart from visible
        self.assertEqual({c["visible"] for c in calls}, {40})
        self.assertIn("(the kit arm at LOW is the API's own request", out)

    def test_the_recorder_on_google_genais_own_types(self):
        try:
            from google.genai import types as gt
        except ImportError:
            if os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1":
                raise
            self.skipTest("google-genai is not installed in this interpreter")
        model = Gemini()
        code, out, gen, lane, data = run(["--rows", "lk-06", "--levels", "LOW,HIGH", "--temperature", "2.0"], model=model,
                                         genai_types=gt)
        self.assertEqual(code, 0, out)
        configs = [r["config"] for r in model.requests]
        self.assertTrue(all(isinstance(c, gt.GenerateContentConfig) for c in configs))
        self.assertEqual([(c.thinking_config.thinking_level, c.temperature) for c in configs],
                         [(gt.ThinkingLevel.LOW, None), (gt.ThinkingLevel.HIGH, None),
                          (gt.ThinkingLevel.LOW, 2.0), (gt.ThinkingLevel.HIGH, 2.0)])
        for c in configs:
            self.assertEqual((c.max_output_tokens, c.response_mime_type), (2048, "application/json"))
            gt.GenerateContentConfig.model_validate(c.model_dump(exclude_none=True))
        built = gt.GenerateContentConfig(max_output_tokens=2048, thinking_config=gt.ThinkingConfig(thinking_level="LOW"))
        rec = pb.Recorder(None, gt)
        rec.level, rec.temperature = "HIGH", 2.0
        self.assertEqual(pb.sent(rec.configure(built)), {"thinking_level": "HIGH", "temperature": 2.0, "max_output_tokens": 2048})
        self.assertEqual(pb.sent(built), {"thinking_level": "LOW", "temperature": None, "max_output_tokens": 2048})


class SystemTests(unittest.TestCase):
    def test_rules_edited_in_memory_and_generator_py_untouched(self):
        before = GENERATOR.read_bytes()
        model = Gemini()
        code, out, gen, lane, data = run(["--rows", "lk-06", "--drop-rule", "4", "--add-rule", "Name the clause code."],
                                         model=model)
        self.assertEqual(code, 0, out)
        kit_rules = pb.rules_of(gen.SYSTEM)[1]
        self.assertEqual(len(kit_rules), 5)
        kit, edit = model.requests
        self.assertTrue(kit["prompt"].startswith(gen.SYSTEM + "\n\nContext:\n"))
        self.assertEqual(kit_prompt_rules(kit["prompt"]), kit_rules)
        self.assertEqual(kit_prompt_rules(edit["prompt"]), kit_rules[:3] + [kit_rules[4], "Name the clause code."])
        self.assertNotIn(kit_rules[3], edit["prompt"])
        self.assertEqual(context_of(kit["prompt"]), context_of(edit["prompt"]))
        self.assertEqual(GENERATOR.read_bytes(), before)
        self.assertEqual(gen.SYSTEM, pb.edit_system(gen.SYSTEM))             # the kit's again, and no edit is no change
        self.assertIsInstance(gen._client, Gemini)
        self.assertIn("generator.py unchanged on disk; SYSTEM is the kit's again", out)
        self.assertIn("edit  rule 4 dropped; rule added: Name the clause code. - 5 rules; no temperature", out)
        self.assertEqual(pb.rules_of(data["arms"][1]["system"])[1], kit_rules[:3] + [kit_rules[4], "Name the clause code."])
        # each arm's prompt text hashed as a prompt version's is (lesson 3.6): SYSTEM, then DATED_RULE, in UTF-8
        kit_sha = hashlib.sha256((gen.SYSTEM + gen.DATED_RULE).encode("utf-8")).hexdigest()
        edit_sha = hashlib.sha256((data["arms"][1]["system"] + gen.DATED_RULE).encode("utf-8")).hexdigest()
        self.assertEqual([a["prompt_sha256"] for a in data["arms"]], [kit_sha, edit_sha])
        self.assertNotEqual(kit_sha, edit_sha)
        self.assertIn(f"\n          prompt sha256 {kit_sha}\n", out)
        self.assertIn(f"\n          prompt sha256 {edit_sha}\n", out)

    def test_edit_system(self):
        system = "Head.\nRules:\n1. One.\n2. Two.\n3. Three.\n"
        self.assertEqual(pb.edit_system(system), system)
        self.assertEqual(pb.edit_system(system, add=["Four."], drop=[1, 3]), "Head.\nRules:\n1. Two.\n2. Four.\n")
        for add, drop, why in (([], [4], "--drop-rule 4: SYSTEM's rules are 1 to 3"), (["two\nlines"], [], "one line"),
                               ([" "], [], "one line")):
            with self.assertRaises(ValueError) as e:
                pb.edit_system(system, add, drop)
            self.assertIn(why, str(e.exception))
        with self.assertRaises(ValueError):
            pb.rules_of("Head.\n1. One.\nA tail.\n")
        self.assertEqual([a["name"] for a in pb.arms(system)], ["kit"])
        self.assertEqual([a["name"] for a in pb.arms(system, temperature=0.0)], ["kit", "edit"])
        self.assertEqual([a["name"] for a in pb.arms(system, add=["x"], baseline=False)], ["edit"])

    def test_the_kit_system_and_client_come_back_whatever_happens(self):
        model = Gemini()
        gen = lifted_generator(model)
        kit = gen.SYSTEM
        arm_list = pb.arms(kit, add=["Never answer."])

        def judge(row, status, body):
            raise RuntimeError("the judge failed")

        with self.assertRaises(RuntimeError), contextlib.redirect_stdout(io.StringIO()):
            pb.bench(gen, [BY_ID["lk-06"]], {"lk-06": POOLS[Q["lk-06"]]}, arm_list[1:], ["LOW"], 1, "gemini-3.6-flash", judge)
        self.assertEqual(gen.SYSTEM, kit)
        self.assertIs(gen._client, model)
        self.assertIn("Never answer.", model.requests[0]["prompt"])


class RowTests(unittest.TestCase):
    def report(self, d: str, records: list[dict]) -> str:
        path = os.path.join(d, "live.json")
        Path(path).write_text(json.dumps({"api_url": "https://api", "records": records}), encoding="utf-8")
        return path

    def test_failing_picks_a_reports_failing_rows(self):
        records = [{"id": "lk-06", "pass": False, "why": "answered without ['60']", "answer": "Ninety days."},
                   {"id": "lk-01", "pass": True, "why": ""},
                   {"id": "rf-01", "pass": False, "why": "answered, should refuse"},
                   {"id": "jn-03", "outcome": "error", "pass": False, "why": "HTTP 502"}]
        with tempfile.TemporaryDirectory() as d:
            path = self.report(d, records)
            self.assertEqual(sorted(pb.report_rows(path, True)), ["jn-03", "lk-06", "rf-01"])
            self.assertEqual(sorted(pb.report_rows(path, False)), ["jn-03", "lk-01", "lk-06", "rf-01"])
            rows = pb.select_rows(GOLDEN, [], ["refusal"], pb.report_rows(path, True))
            refusals = [r["id"] for r in GOLDEN if r["shape"] == "refusal"]
            self.assertEqual(len(refusals), 8)
            self.assertEqual([r["id"] for r in rows], [r["id"] for r in GOLDEN if r["id"] in {"lk-06", "jn-03", *refusals}])
            code, out, gen, lane, data = run(["--from-report", path, "--failing", "--shape", "refusal"])
        self.assertEqual(code, 0, out)
        self.assertEqual([c["question"] for c in lane.calls], [Q[r["id"]] for r in rows])
        self.assertIn("eval-live: did not pass - answered without ['60']", out)
        self.assertEqual({a["id"] for a in data["answers"]}, {"lk-06", "rf-01"})     # the rows with a pool here
        self.assertEqual(data["rows"][0]["report"], {"pass": False, "why": "answered without ['60']", "answer": "Ninety days."})

    def test_rows_are_refused_when_they_cannot_be_read(self):
        with tempfile.TemporaryDirectory() as d:
            for argv, why in ((["--rows", "zz-99"], "not golden rows: zz-99"),
                              (["--shape", "joins"], "--shape joins: one of"),
                              (["--from-report", self.report(d, [{"id": "zz-01", "pass": False}])], "not golden rows: zz-01"),
                              (["--from-report", os.path.join(d, "missing.json")], "not readable as JSON"),
                              (["--rows", "lk-06", "--levels", "LOWEST"], "--levels LOWEST: one of MINIMAL, LOW, MEDIUM, HIGH"),
                              (["--rows", "lk-06", "--drop-rule", "9"], "--drop-rule 9: SYSTEM's rules are 1 to 5"),
                              (["--rows", "lk-06", "--model", "projects/documind-ai-YOUR-ID/locations/us-central1/endpoints/7"],
                               "a tuned endpoint is served on a regional client")):
                with self.assertRaises(SystemExit) as e:
                    run(argv)
                self.assertIn(why, str(e.exception), argv)
            Path(d, "bad.json").write_text(json.dumps({"rows": 3}), encoding="utf-8")
            with self.assertRaises(SystemExit) as e:
                run(["--from-report", os.path.join(d, "bad.json")])
            self.assertIn("not a run_eval.py --report file", str(e.exception))
        for argv in (["--failing", "--rows", "lk-06"], ["--levels", "LOW"], ["--rows", "lk-06", "--runs", "0"],
                     ["--rows", "lk-06", "--no-baseline"]):
            with self.assertRaises(SystemExit) as e, contextlib.redirect_stderr(io.StringIO()):
                run(argv)
            self.assertEqual(e.exception.code, 2, argv)                      # argparse's own refusal

    def test_the_generator_needs_the_lanes_project(self):
        with patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": ""}), self.assertRaises(SystemExit) as e:
            pb.load_generator()
        self.assertIn("GOOGLE_CLOUD_PROJECT is not set", str(e.exception))


class ScoringTests(unittest.TestCase):
    def test_every_answer_is_judged_by_the_gates_rule(self):
        model = Gemini()
        code, out, gen, lane, data = run(["--rows", "lk-06,rf-01", "--levels", "LOW,HIGH"], model=model)
        self.assertEqual(code, 0, out)
        verdicts = {(a["id"], a["level"]): (a["outcome"], a["pass"], a["why"]) for a in data["answers"]}
        self.assertEqual(set(verdicts.values()), {("ok", True, "")})
        # the same reply through run_eval.row_verdict() directly: the bench adds nothing and leaves nothing out
        status, body = pb.answer_one(lifted_generator(Gemini()), Q["lk-06"], pb.chunks_of(POOLS[Q["lk-06"]]), "gemini-3.6-flash")
        corpus = pb.run_eval.load_corpus()
        v = pb.run_eval.row_verdict(BY_ID["lk-06"], status, body, {SHA}, pb.run_eval.load_manifest_objects(),
                                    re.sub(r"\s+", " ", pb.run_eval.haystack(corpus, "acme")))
        self.assertEqual((status, v["outcome"], v["pass"], v["valid"], v["supported"], v["contained"]),
                         (200, "ok", True, True, True, True))
        lk06 = next(a for a in data["answers"] if a["id"] == "lk-06")
        self.assertEqual(lk06["cites"], [{"chunk_id": f"acme:{SHA}#1", "source_uri": URI,
                                          "quote": "serves a notice period of 60 days", "check": "own"}])
        self.assertIn("quotes kit LOW: 1 of 1 in the passage they cite", out)

    def test_a_wrong_answer_a_breach_and_a_stale_version_fail_as_the_gate_fails_them(self):
        def wrong(req):
            question = req["prompt"].rsplit("\n\nQuestion: ", 1)[1]
            if "notice period" in question:      # a figure the passage does not hold, quoted from the wrong source
                return reply(notice_draft(2, answer="Ninety days [{n}].", quote="serves a notice period of 60 days"))
            return reply(notice_draft(1, answer="Ten days of sabbatical [{n}].", quote="invented words"))

        code, out, gen, lane, data = run(["--rows", "lk-06,rf-01"], model=Gemini(wrong))
        by = {a["id"]: a for a in data["answers"]}
        self.assertEqual((by["lk-06"]["pass"], by["lk-06"]["why"]), (False, "answered without ['60']"))
        self.assertEqual(by["lk-06"]["cites"][0]["check"], "elsewhere")
        self.assertEqual((by["rf-01"]["pass"], by["rf-01"]["why"]), (False, "answered, should refuse"))
        self.assertEqual(by["rf-01"]["cites"][0]["check"], "absent")
        self.assertIn("quotes kit LOW: 0 of 2 in the passage they cite (elsewhere 1, absent 1)", out)
        self.assertEqual(code, 0)
        # the ledger lists another version as current: the citation names a retired one
        code, out, gen, lane, data = run(["--rows", "lk-06"], lane=Lane(current={"d" * 64}))
        self.assertEqual((data["answers"][0]["pass"], data["answers"][0]["why"]),
                         (False, f"chunk acme:{SHA[:35]} is a version the ledger does not list as current"))
        code, out, gen, lane, data = run(["--rows", "lk-06"], lane=Lane(current=None))
        self.assertTrue(data["answers"][0]["pass"])
        self.assertIn("[info] version check skipped for acme: GET /v1/sources was unavailable", out)

    def test_an_answer_cut_off_twice_is_an_error_with_both_calls_billed(self):
        cut = reply(None, prompt=1000, visible=50, thought=1998, finish="MAX_TOKENS", text='{"answer": "Sixty')
        code, out, gen, lane, data = run(["--rows", "lk-06", "--levels", "HIGH"], model=Gemini(lambda req: cut))
        a = data["answers"][0]
        self.assertEqual((a["status"], a["outcome"], a["pass"]), (502, "error", False))
        self.assertEqual(a["why"], "HTTP 502 HTTPException: generation produced no parseable answer (MAX_TOKENS)")
        self.assertEqual([c["max_output_tokens"] for c in a["calls"]], [2048, 6144])   # generate()'s own retry, recorded
        self.assertEqual([c["finish"] for c in a["calls"]], ["MAX_TOKENS", "MAX_TOKENS"])
        self.assertAlmostEqual(a["cost_inr"], 2 * pb.call_inr(a["calls"][0]))
        self.assertEqual(code, 1, "no answer came back")
        self.assertIn("errors kit HIGH: 1 of 1 came back as an error, not an answer", out)
        self.assertIn("retried kit HIGH: 1 of 1 were cut off at max_output_tokens", out)
        self.assertIn("ERROR thought  3,996", out)

    def test_a_429_on_the_model_asked_falls_back_to_the_default_and_says_so(self):
        def quota(req):
            if req["model"] == "gemini-3.1-flash-lite":
                raise APIError(429, "RESOURCE_EXHAUSTED")
            return grounded(req)

        code, out, gen, lane, data = run(["--rows", "lk-06", "--model", "gemini-3.1-flash-lite"], model=Gemini(quota))
        self.assertEqual(code, 0, out)
        a = data["answers"][0]
        self.assertEqual((a["pass"], a["model"]), (True, "gemini-3.6-flash"))
        self.assertEqual([c["model"] for c in a["calls"]], ["gemini-3.1-flash-lite", "gemini-3.6-flash"])
        self.assertEqual(a["calls"][0]["error"], "APIError: RESOURCE_EXHAUSTED")
        self.assertEqual(a["cost_inr"], pb.call_inr(a["calls"][1]))          # the refused call billed nothing
        self.assertEqual(gen.logged[-1][1]["event"], "tier_exhausted")
        self.assertIn("fell back kit LOW: 1 of 1 were answered by the default model after a 429", out)


class SummaryTests(unittest.TestCase):
    def test_distinct_answers_and_citation_sets_per_row_across_runs(self):
        said = {}

        def wordings(req):
            # LOW says it two ways in turn; HIGH says it one way every time
            level = level_of(req["config"])
            said[level] = said.get(level, 0) + 1
            n = next(k for k, t in sources_in(req["prompt"]).items() if "notice period of 60 days" in t)
            words = ("A confirmed E3 serves 60 days [{n}]." if level == "HIGH" or said[level] % 2
                     else "Sixty days, that is 60 days [{n}].")
            return reply(notice_draft(n, answer=words), thought=THOUGHT[level])

        code, out, gen, lane, data = run(["--rows", "lk-06", "--runs", "5", "--levels", "LOW,HIGH"], model=Gemini(wordings))
        low, high = (next(s for s in data["summary"] if s["level"] == lv) for lv in ("LOW", "HIGH"))
        self.assertEqual((low["answers"], low["passed"], low["distinct_answers"], low["distinct_citations"]), (5, 5, 2, 1))
        self.assertEqual((high["answers"], high["passed"], high["distinct_answers"], high["distinct_citations"]), (5, 5, 1, 1))
        self.assertEqual((low["thought"], low["visible"], low["calls"], low["retried"]), (5 * 120, 5 * 40, 5, 0))
        self.assertRegex(out, r"\n  kit   LOW     5/5 = 100\.0% \[56\.6%, 100\.0%\] +2 of 5 +1 of 5 +120 +40 ")
        self.assertRegex(out, r"\n  kit   HIGH    5/5 = 100\.0% \[56\.6%, 100\.0%\] +1 of 5 +1 of 5 +900 +40 ")

    def test_the_rupees_are_list_price(self):
        flash = {"model": "gemini-3.6-flash", "tokens_in": 1000, "cached": 200, "visible": 100, "thought": 300}
        # 800 fresh input tokens at 1.50, 200 cached at a tenth of it, 400 output (visible and thought) at 7.50, x 85
        self.assertAlmostEqual(pb.call_inr(flash), 85 * (800 * 1.50 + 200 * 0.15 + 400 * 7.50) / 1e6)
        self.assertAlmostEqual(pb.call_inr(flash), 0.35955)
        self.assertAlmostEqual(pb.call_inr({**flash, "model": "gemini-3.1-flash-lite"}),
                               85 * (800 * 0.25 + 200 * 0.025 + 400 * 1.50) / 1e6)
        self.assertAlmostEqual(pb.call_inr({**flash, "model": "an-unknown-model"}), 0.35955)   # priced as flash
        self.assertAlmostEqual(pb.call_inr({**flash, "thought": 0}), 85 * (800 * 1.50 + 200 * 0.15 + 100 * 7.50) / 1e6)
        code, out, gen, lane, data = run(["--rows", "lk-06,rf-01", "--levels", "LOW,HIGH", "--model", "gemini-3.1-flash-lite"])
        calls = [c for a in data["answers"] for c in a["calls"]]
        self.assertEqual({c["model"] for c in calls}, {"gemini-3.1-flash-lite"})
        total = sum(pb.call_inr(c) for c in calls)
        self.assertAlmostEqual(data["cost_inr"], total)
        self.assertIn(f"Rs {total:.4f} in all: 4 answers, 4 model calls on gemini-3.1-flash-lite", out)
        for s in data["summary"]:
            mine = [a for a in data["answers"] if a["level"] == s["level"]]
            self.assertAlmostEqual(s["cost_inr"], sum(a["cost_inr"] for a in mine))
            self.assertIn(f"{s['cost_inr'] / s['answers']:10.4f}", out)


class IdentifierTests(unittest.TestCase):
    """13 October 2026: the bench printed the lane's project id and number, and its output is pasted into the pages.
    It now prints them as the pages do, unless BENCH_REDACT=0; every request still goes to the lane's own address."""

    PROJECT, NUMBER = "documind-ai-" + "abc123", "1234" + "56789012"   # split: the file must not look like a real id or number to tools/leakscan.py
    LANE_URL = f"https://documind-api-{NUMBER}.asia-south1.run.app"
    BUCKET_URI = f"gs://{PROJECT}-uploads/acme/hr_policy_2026.md"
    DENIED = f"on {PROJECT}, projects/{NUMBER}/x"                 # short enough to stay in the answer line's 70 characters

    def bench(self, redact: str | None):
        def denied(req):
            raise APIError(403, self.DENIED)

        lane = Lane(pools={Q["lk-06"]: [dict(p, source_uri=self.BUCKET_URI) for p in pool(1, 2, 3, 4, 5, 6)]})
        env = {"GOOGLE_CLOUD_PROJECT": self.PROJECT, **({"BENCH_REDACT": redact} if redact is not None else {})}
        with patch.dict(os.environ, {}):
            os.environ.pop("BENCH_REDACT", None)
            return run(["--rows", "lk-06", "--show"], model=Gemini(denied), lane=lane, api_url=self.LANE_URL, env=env)

    def test_the_lanes_project_id_and_number_are_printed_and_reported_as_the_pages_print_them(self):
        code, out, gen, lane, data = self.bench(None)
        self.assertIn("== prompt bench: gemini-3.6-flash, against https://documind-api-NUMBER.asia-south1.run.app ==", out)
        self.assertIn("HTTP 403 APIError: on documind-ai-YOUR-ID, projects/NUMBER/x", out)
        report = json.dumps(data)
        for text in (out, report):
            self.assertNotIn(self.PROJECT, text)
            self.assertNotIn(self.NUMBER, text)
        self.assertEqual(data["api_url"], "https://documind-api-NUMBER.asia-south1.run.app")
        self.assertEqual({p["source_uri"] for p in data["rows"][0]["pool"]},
                         {"gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md"})
        self.assertEqual(data["answers"][0]["error"], "APIError: on documind-ai-YOUR-ID, projects/NUMBER/x")
        self.assertEqual(data["answers"][0]["status"], 403)                       # a number stays a number
        self.assertEqual({c["api_url"] for c in lane.calls}, {self.LANE_URL})    # the requests went to the lane itself
        self.assertEqual(code, 1, "no answer came back")

    def test_bench_redact_0_prints_them_as_they_are(self):
        _, out, _, lane, data = self.bench("0")
        self.assertIn(f"== prompt bench: gemini-3.6-flash, against {self.LANE_URL} ==", out)
        self.assertIn(f"HTTP 403 APIError: {self.DENIED}", out)
        self.assertEqual(data["api_url"], self.LANE_URL)
        self.assertEqual({p["source_uri"] for p in data["rows"][0]["pool"]}, {self.BUCKET_URI})

    def test_what_the_redactor_replaces(self):
        hide = pb.redactor(self.PROJECT, self.LANE_URL)
        for text, want in ((f"gs://{self.PROJECT}-uploads/a.md", "gs://documind-ai-YOUR-ID-uploads/a.md"),
                           (f"documind-ui-sa@{self.PROJECT}.iam.gserviceaccount.com",
                            "documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com"),
                           (f"{self.PROJECT}4 and x{self.PROJECT}", f"{self.PROJECT}4 and x{self.PROJECT}"),  # other names
                           (f"project {self.NUMBER} is", "project NUMBER is"),
                           (f"{self.NUMBER}3", f"{self.NUMBER}3"),                                    # another number
                           ("https://documind-chat-" + "9876" + "54321098" + ".us-central1.run.app",
                            "https://documind-chat-NUMBER.us-central1.run.app"),                     # any Cloud Run address
                           ("projects/" + "9876" + "54321098" + "/locations/global", "projects/NUMBER/locations/global")):
            self.assertEqual(hide(text), want, text)
        self.assertEqual(pb.redactor(self.PROJECT, self.LANE_URL, on=False)(self.BUCKET_URI), self.BUCKET_URI)
        self.assertEqual(pb.redactor("x", None)("x marks it"), "x marks it")     # not a project id's shape: left alone
        stand_in = pb.redactor("documind-ai-YOUR-ID", "http://stand-in.invalid")   # the pages' own scripted run
        page = "== prompt bench: gemini-3.6-flash, against http://stand-in.invalid ==\n  gs://documind-ai-YOUR-ID-uploads"
        self.assertEqual(stand_in(page), page)


class WiringTests(unittest.TestCase):
    def read(self, *parts) -> str:
        return KIT.joinpath(*parts).read_text(encoding="utf-8")

    def test_the_make_target_and_its_listings(self):
        mk, gen_mk, readme, unowned = self.read("Makefile"), self.read("mk", "generation.mk"), self.read("mk", "README.md"), \
            self.read("UNOWNED.md")
        self.assertEqual(len(mk.splitlines()), 888)
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        self.assertIn("bench", phony)
        self.assertIn("\nbench: guard-project\n", gen_mk)
        recipe = gen_mk.split("\nbench: guard-project\n", 1)[1]
        for needle in ("--impersonate-service-account=documind-ui-sa@$(PROJECT).iam.gserviceaccount.com",
                       "GOOGLE_CLOUD_PROJECT=$(PROJECT)", "$(PY) evals/prompt_bench.py --api-url $$API $(BENCH_ARGS)"):
            self.assertIn(needle, recipe)
        self.assertEqual(gen_mk.count("\n# ----------"), 0, "one header block, at the top")
        self.assertTrue(gen_mk.startswith("# ---------- Generation"))
        row = next(l for l in readme.splitlines() if l.startswith("| `generation.mk` |"))    # bench shares the file
        self.assertIn("`bench`", row.split("|")[2])                                         # with prompt-version
        for f in ("evals/prompt_bench.py", "evals/tests/test_prompt_bench.py", "mk/generation.mk"):
            self.assertIn(f"`{f}`", unowned)


if __name__ == "__main__":
    unittest.main()
