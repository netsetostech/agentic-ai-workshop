"""Build lesson 10.4 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The routed DocuMind Desk: one front door, POST /v1/desk, and one desk for each question. The router
(services/chat/desk_router.py) decides by code first - who is asking, the hard gate, the masking, the identifiers a
question names - and only then asks two signals, a flash-lite classifier with an enum-only schema and a k=7 vote over
the tenant's own exemplars, with one arbiter call when they disagree. The desk graph (services/chat/desk_graph.py)
runs the desk it chose: the handbook over [policy], the law over [statute, guidance] with its in-force lines, a
clarify, out_of_scope or the case desk by code. Before any of it, every chunk gets its class from the operator's
registry (shared/doc_types.py, services/ingest/relabel.py), because a desk's filter is a class. The lane walk: the
three services, the eval accounts, the registry and the relabel, the exemplar index, the switches; the Desk page; the
code; /v1/route and /v1/desk; make smoke-desk; the shadow on zeta; the rows; make route-eval; make smoke-chat.

Build-time proof. The thresholds the widget shows are the kit's constants, read here and asserted equal. Every
"rules first" verdict in the widget is decide() run here with a recording stand-in for the models, and the acceptance
sandbox's script is checked in node against desk_router.accept() and candidates() over a grid. The expected outputs
are the kit's own code run against stand-ins: commands/desk_ops.py and services/ingest/relabel.py against a fake
Firestore holding the eval corpus's objects; agent.py's app, with the Desk installed, behind a local HTTP bridge, with
a stand-in identity, roster, rag-api and models (a scripted classifier and arbiter, offline embeddings); the lane's
cells, smoke/smoke_desk.py and evals/route_eval.py run against that bridge. Wherever a model decides on a lane, the
page says so and shows the value as yours to read. Ids, times and tokens are made deterministic, and every timestamp
is shown as a placeholder.
"""
import ast
import base64
import contextlib
import copy
import hashlib
import html
import importlib.util
import io
import itertools
import json
import math
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import types
import uuid
import warnings
from collections import Counter
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "10.4"
title = ("<title>Lesson 10.4 Route each question to one specialist agent - the rules first, two signals, one arbiter, "
         "and a desk for each question | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
LANE_ID = PROJ.lower()                 # the stand-ins run on a real-looking (lower-case) id; every output shows PROJ
ME = "you@example.com"
warnings.filterwarnings("ignore")
logging.getLogger().addHandler(logging.NullHandler())   # agent.py's basicConfig must not print the build's rows

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:1fr;gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;width:100%;}
.pc-in select:disabled{color:#94a3b8;background:#f1f5f9;}
@media (min-width:640px){.pc-in.two{grid-template-columns:1fr 1fr;}}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:8px 0 4px;}
.pc-box p{margin:4px 0;}
.rt-words{font-size:14px;color:var(--navy);background:#f1f5f9;border-radius:8px;padding:8px 10px;margin:6px 0;}
.rt-src{font-size:12px;color:var(--slate);margin:0 0 6px;}
.rt-verdict{font-family:var(--mono);font-size:13px;padding:5px 10px;border-radius:8px;display:inline-block;margin:4px 0;}
.rt-verdict.rule{background:#ccfbf1;color:#134e4a;}.rt-verdict.model{background:#e0f2fe;color:#0c4a6e;}.rt-verdict.no{background:#fee2e2;color:#7f1d1d;}
.rt-stages{margin:6px 0 0;padding-left:0;list-style:none;font-size:13.5px;}
.rt-stages li{margin:4px 0;padding-left:22px;position:relative;}
.rt-stages li::before{position:absolute;left:0;top:0;font-family:var(--mono);}
.rt-stages li.yes{color:#134e4a;}.rt-stages li.yes::before{content:"\\2713";}
.rt-stages li.no{color:#475569;}.rt-stages li.no::before{content:"\\2013";}
.rt-stages li.stop{color:#7c2d12;font-weight:600;}.rt-stages li.stop::before{content:"\\25A0";}
.rt-stages li.next{color:#0c4a6e;}.rt-stages li.next::before{content:"\\2192";}
.rt-masked{white-space:pre-wrap;border-left:3px solid var(--teal);padding:4px 10px;margin:4px 0;color:var(--navy);}
.rt-th{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0;}
.rt-th span{font-family:var(--mono);font-size:12px;background:#f1f5f9;border:1px solid var(--border);border-radius:6px;padding:2px 8px;}
.rt-rules{margin:6px 0 0;padding-left:0;list-style:none;font-size:13px;}
.rt-rules li{margin:3px 0;}
.rt-rules li.fired{color:#134e4a;font-weight:600;}
.rt-rules li.skip{color:#475569;}
"""

setup = setup_section()


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, KIT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod                        # pydantic resolves the routes' models by their module
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ verbatim excerpts
RT, RS, GR, DT, RL = ("services/chat/desk_router.py", "services/chat/desk_routes.py", "services/chat/desk_graph.py",
                      "shared/doc_types.py", "services/ingest/relabel.py")
CD, FD, LW = "services/chat/desk.py", "services/frontend/desk.py", "shared/desk_law.py"
EXCERPTS = {
    "assign": ("shared/doc_types.py - assign(): a version gets its class only when it is the version a person pinned",
               block(DT, "def assign(db, doc, name: str):")),
    "plan": ("services/ingest/relabel.py - plan(): one action per current version, from the rows and the registry",
             block(RL, "def plan(rows: list[dict], registry: dict[str, dict], reset: bool = False) -> list[dict]:")),
    "desks": ("services/chat/desk_routes.py - one desk's row, and the filter code fixes from it",
              block(RS, '    "handbook": {', n=13) + "\n    ...\n\n\n" + block(RS, "def doc_types(desk: str) -> list[str]:", n=3)),
    "cascade": ("services/chat/desk_router.py - the cascade, as the module's docstring gives it",
                block(RT, "    0  who        no role at all is denied", end="L1 failing (a timeout, an error")),
    "consts": ("services/chat/desk_router.py - the router's numbers, every one a starting value",
               block(RT, "# Starting values, every one", end="STICKY_ROUTES = ")),
    "schema": ("services/chat/desk_router.py - L1's schema has no free-text field, and its request",
               block(RT, "SCHEMA = {", n=9) + "\n\n\n" + block(RT, "def l1_config(", n=6)),
    "decide": ("services/chat/desk_router.py - decide(): who, the gate and the masking, before anything reads the words",
               block(RT, "    rec = _new(None, [])                    # no text", end="def _done(")),
    "anchors": ("services/chat/desk_router.py - anchors(): identifiers only, never topic words",
                block(RT, "def anchors(question: str, clause_prefixes=()) -> list[str]:")),
    "signals": ("services/chat/desk_router.py - stage 5 and 6 inside _route(): two signals in parallel, then accept()",
                block(RT, "        deadline = min(time.monotonic() + L1_TIMEOUT_S", n=29)),
    "accept": ("services/chat/desk_router.py - rules D, A, B and C in accept(), and rule F's enum in candidates()",
               block(RT, "def case_signal(", n=5) + "\n\n\n" + block(RT, "def accept(l1: dict | None") + "\n\n\n"
               + block(RT, "def candidates(l1: dict, knn: dict | None) -> list[str]:", n=7)),
    "arbiter": ("services/chat/desk_router.py - _arbiter(): one L2 call; on any failure L1's route stands",
                block(RT, "def _arbiter(")),
    "dispatch": ("services/chat/desk_graph.py - dispatch() and next_part(): the parts are a list the router fixed",
                 block(GR, "def dispatch(state: DeskState, runtime: Runtime)") + "\n\n\n" + block(GR, "def next_part(")),
    "inforce": ("shared/desk_law.py - in_force_line(): what the corpus's own text says, and no date until a person checks it",
                block(LW, "def in_force_line(key: str) -> str:") + "\n\n\n" + block(LW, "def in_force_lines(names) -> list[str]:")),
    "routes": ("services/chat/desk.py - the routed Desk's routes, as the module's docstring lists them",
               block(CD, "    POST /v1/desk     one turn for a person.", end="Each Desk row names every field")),
    "page": ("services/frontend/desk.py - what Ask the Desk does, from the page's docstring",
             block(FD, "routed_half(): while desk_route is on or single,", end='"""')),
}
# The Google Chat door: the Desk's side (delegation.py), the bridge (services/gchat/) and its deploy block
DG, GM, CA, CL, GS = ("services/chat/delegation.py", "services/gchat/main.py", "services/gchat/cards.py",
                      "services/gchat/claims.py", "commands/gchat.sh")
EXCERPTS.update({
    "gchatsh": ("commands/gchat.sh - the bridge's deploy: no IAP, and why",
                block(GS, "# 1. The service. No IAP", end="# 2. Who may call it")),
    "verify": ("services/gchat/main.py - expected_caller() and verify(): one caller for each path, checked in code",
               block(GM, "def expected_caller(path: str) -> str | None:") + "\n\n\n"
               + block(GM, "def verify(headers, path: str) -> JSONResponse | None:", end="# ------------------------------")),
    "deleg": ("services/chat/delegation.py - the delegate, the delegable routes, and principal()",
              block(DG, 'HEADER = "x-documind-principal"', n=9) + "\n\n\n"
              + block(DG, "def principal(request, caller, tenant_for, settings) -> dict:")),
    "render": ("services/gchat/cards.py - render(): one Google Chat message for one Desk reply",
               block(CA, "def render(desk: dict, self_url: str, session_id: str) -> dict:")),
    "claims": ("services/gchat/claims.py - the claims' database and lifetime, and take()",
               block(CL, 'DATABASE = "documind-gchat"', n=6) + "\n\n\n" + block(CL, "def take(key: str, kind: str, db=None) -> bool:")),
})
assert EXCERPTS["gchatsh"][1].startswith("# 1. The service. No IAP") and "--no-allow-unauthenticated --ingress=all" in EXCERPTS["gchatsh"][1]
assert "--iap" not in EXCERPTS["gchatsh"][1] and EXCERPTS["gchatsh"][1].rstrip().endswith('GCHAT_CALLER=service-$PROJECT_NUMBER@gcp-sa-gsuiteaddons.iam.gserviceaccount.com"')
assert EXCERPTS["verify"][1].rstrip().endswith("return None") and 'return _refuse(headers, path, "wrong_caller")' in EXCERPTS["verify"][1]
assert EXCERPTS["deleg"][1].startswith('HEADER = "x-documind-principal"') and EXCERPTS["deleg"][1].split("\n\n\n")[0].rstrip().endswith('SWITCH = "desk_gchat"')
assert EXCERPTS["deleg"][1].rstrip().endswith('return {"email": person, "assertion": None, "via": name, "delegate": name}')
assert EXCERPTS["render"][1].rstrip().endswith("return fit(text_card(desk, self_url, session_id), desk, self_url, session_id)")
assert EXCERPTS["claims"][1].startswith('DATABASE = "documind-gchat"') and EXCERPTS["claims"][1].rstrip().endswith("return _tx(db.transaction())")
assert '"expire_at": now + TTL})' in EXCERPTS["claims"][1]
assert EXCERPTS["assign"][1].rstrip().endswith('return doc.model_copy(update={"doc_type": cls})')
assert "if entry.get(\"pin\") and entry.get(\"pin\") == doc.doc_key:" in EXCERPTS["assign"][1]
assert EXCERPTS["plan"][1].rstrip().endswith("return out") and '"targets": targets, "change": change})' in EXCERPTS["plan"][1]
assert '"doc_types": ("policy",),' in EXCERPTS["desks"][1] and EXCERPTS["desks"][1].rstrip().endswith('return list(DESKS[desk]["doc_types"])')
assert EXCERPTS["cascade"][1].startswith("    0  who") and "desk_max_parts allows (1 when unset), else it is a chip." in EXCERPTS["cascade"][1]
assert EXCERPTS["consts"][1].startswith("# Starting values, every one") and EXCERPTS["consts"][1].rstrip().endswith(
    "MAX_PARTS = 2                   # tenant_settings desk_max_parts may lower it; the code default is 1")
assert EXCERPTS["schema"][1].rstrip().endswith('"http_options": {"timeout": int(timeout_s * 1000), "retry_options": {"attempts": 1}}}')
assert EXCERPTS["decide"][1].rstrip().endswith('return _fallback(rec, ctx, roles.desks(ctx.get("roles") or ()), t0, f"error:{type(e).__name__}")')
assert "gate = desk_rules.gate(question)                                     # stage 1: before anything else" in EXCERPTS["decide"][1]
assert EXCERPTS["anchors"][1].rstrip().endswith("return [r for r in ROUTES if r in found]")
assert EXCERPTS["signals"][1].rstrip().endswith('route, method, confidence = _arbiter(rec, masked, l1, knn, models, meter, left, pool)'), EXCERPTS["signals"][1][-200:]
assert EXCERPTS["accept"][1].rstrip().endswith("return out") and 'return "case", "D"' in EXCERPTS["accept"][1]
assert EXCERPTS["arbiter"][1].rstrip().endswith('return choice, "arbiter", "medium"')
assert EXCERPTS["dispatch"][1].rstrip().endswith('"last_at": time.time(), "clarified": False})')
assert "if parts and limits.meter_of(runtime.context).left() >= PART_MIN_S:" in EXCERPTS["dispatch"][1]
assert EXCERPTS["inforce"][1].rstrip().endswith("return [in_force_line(k) for k in keys] + [NOT_ADVICE]")
assert EXCERPTS["routes"][1].startswith("    POST /v1/desk") and "shadow            while desk_route is shadow and desk_gate is not off" in EXCERPTS["routes"][1]
assert EXCERPTS["page"][1].startswith("routed_half(): while desk_route is on or single") and EXCERPTS["page"][1].rstrip().endswith(
    "is never shown back or kept, and a 409 (a chip no longer on offer) has its own plain sentence.")
DOCSTRING_WINDOWS = ("cascade", "routes", "page")


def kit_window(label: str, code: str) -> str:
    """pagebuild.window(); a docstring excerpt is prose inside a string, so it is coloured as one string."""
    if label not in [EXCERPTS[k][0] for k in DOCSTRING_WINDOWS]:
        return window(label, code)
    empty = window(label, "")
    assert empty.count('<pre tabindex="0"></pre>') == 1
    return empty.replace('<pre tabindex="0"></pre>', '<pre tabindex="0"><span class="st">' + html.escape(code, quote=False) + "</span></pre>")


fill = filler(EXCERPTS, kit_window)


def fd_const(name: str):
    """A constant of the Desk page's own code (services/frontend/desk.py), read without importing Streamlit."""
    for node in ast.parse((KIT / FD).read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(isinstance(x, ast.Name) and x.id == name for x in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)


# ------------------------------------------------------------------ the kit's modules and its facts
for p in (str(KIT / "services/ingest"), str(KIT / "services/chat"), str(KIT)):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ["CHECKPOINT_DSN"] = "memory"           # agent.py's InMemorySaver, said out loud (its rule 4)
os.environ["RAG_TIMEOUT_S"] = "90"                # the lane's 90 (lesson-12.8.sh), so the limits are the lane's
import desk_router  # noqa: E402
import desk_routes  # noqa: E402
import limits  # noqa: E402
from shared import desk_law, desk_recall, desk_rules, doc_types, identifiers, prices, roles  # noqa: E402

tc = load("kit_test_cases_106", "commands/tests/test_cases.py")
td = load("kit_test_desk_106", "commands/tests/test_desk.py")
kt = load("kit_desk_rules_106", "commands/tests/test_desk_rules.py")
route_eval = load("route_eval_106", "evals/route_eval.py")
lane = load("lane_106", "commands/lane.py")
smoke_cases0 = load("smoke_cases_106", "smoke/smoke_cases.py")
POSH = smoke_cases0.POSH
WORDS = {0: "no", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
         10: "ten", 11: "eleven", 12: "twelve"}

# the router's numbers: the kit's constants, read here; the page and the widget show these and nothing else
TH = {"K": desk_router.K, "ACCEPT_VOTES": desk_router.ACCEPT_VOTES, "CASE_VOTES": desk_router.CASE_VOTES,
      "TAU_OOS": desk_router.TAU_OOS, "L1_TIMEOUT_S": desk_router.L1_TIMEOUT_S, "L2_TIMEOUT_S": desk_router.L2_TIMEOUT_S,
      "ROUTER_BUDGET_S": desk_router.ROUTER_BUDGET_S, "STICKY_S": desk_router.STICKY_S}
src_router = (KIT / RT).read_text(encoding="utf-8")
for k, v in TH.items():                       # the widget's numbers are the kit's constants, as the source spells them
    assert re.search(rf"^{k} = ", src_router, re.M), k
assert (TH["K"], TH["ACCEPT_VOTES"], TH["CASE_VOTES"], TH["TAU_OOS"]) == (7, 5, 3, 0.70)
assert "# Starting values, every one, until people write and review the dev rows" in src_router
src_graph = (KIT / GR).read_text(encoding="utf-8")
assert re.search(r"^PART_MIN_S = 30\.0 +# starting value", src_graph, re.M)
import desk_graph  # noqa: E402  - LangGraph, from the chat image's pins
assert desk_graph.PART_MIN_S == 30.0
assert desk_router.RULE_E_LOGPROBS is False and desk_router.L2_THINKING == "LOW"
assert (desk_router.L1_MODEL, desk_router.L2_MODEL, desk_router.EMBED_MODEL) == ("gemini-3.1-flash-lite", "gemini-3.6-flash", "text-embedding-005")
assert (desk_router.GEN_LOCATION, desk_router.EMBED_LOCATION, desk_router.EMBED_DIM) == ("global", "us-central1", 768)
assert desk_router.ROUTES == desk_routes.ROUTES == ("handbook", "statute", "case", "clarify", "out_of_scope")
assert desk_routes.ANSWER_DESKS == ("handbook", "statute")
assert desk_routes.doc_types("handbook") == ["policy"] and desk_routes.doc_types("statute") == ["statute", "guidance"]
assert len(desk_routes.PROMPT_EXEMPLARS) == 8 and {r for _, r, _ in desk_routes.PROMPT_EXEMPLARS} == {"handbook", "statute", "out_of_scope"}
assert "case and clarify have none until such\nrows exist" in desk_routes.__doc__
assert not any(f in desk_router.SCHEMA["properties"] and desk_router.SCHEMA["properties"][f]["type"] == "string"
               and "enum" not in desk_router.SCHEMA["properties"][f] for f in desk_router.SCHEMA["properties"])
ROUTE_ROWS = route_eval.load_rows()
ROUTE_COUNT = Counter((r["expected_route"], r["split"]) for r in ROUTE_ROWS)
N_ROUTE_ROWS = len(ROUTE_ROWS)
assert {r["author"] for r in ROUTE_ROWS} == {"model-draft"}                       # no people-written row yet
assert not [r for r in ROUTE_ROWS if r["split"] == "test"]                         # the test split is empty
assert not [r for r in ROUTE_ROWS if r["must_escalate"] or r["expected_route"] in ("case", "clarify")]
assert set(desk_law.IN_FORCE.values()) == {None}                                   # no in-force date entered
assert {r["language"] for r in ROUTE_ROWS} == {"en"}
ALERTS_TF = (KIT / "terraform/desk_alerts.tf").read_text(encoding="utf-8")
assert re.search(r'variable "desk_router_alerts" \{[^}]*default\s*=\s*false', ALERTS_TF, re.S)
mk_src = (KIT / "mk/agents.mk").read_text(encoding="utf-8")
assert "DESK_ROUTER_ALERTS ?= false" in mk_src
EVAL_SAS = re.search(r"^DESK_EVAL_SAS = (.+)$", mk_src, re.M).group(1).split()
assert EVAL_SAS == ["documind-evalacme-sa", "documind-evalzeta-sa", "documind-evalglobex-sa", "documind-evalleaver-sa",
                    "documind-evalgrc-sa"]
QA = json.loads((KIT / "evals/desk/queues.acme.json").read_text(encoding="utf-8"))
ACME_PREFIXES = sorted(QA["clause_prefixes"])
NOW = 1_790_000_000.0


# ------------------------------------------------------------------ Level 0: the router's rules, run here
class Recording:
    """The models, as decide() calls them: every call is recorded; L1 answers the route it is told to."""

    def __init__(self, l1_route="handbook"):
        self.calls, self.l1_route = [], l1_route

    def l1(self, text):
        self.calls.append("l1")
        return ({"route": self.l1_route, "second_route": "none", "case_type": "none", "needs_calculation": False,
                 "followup": False}, {})

    def l2(self, text, cands):
        self.calls.append("l2")
        return cands[0], {}

    def embed(self, text):
        self.calls.append("embed")
        return route_eval.offline_embed(text, 768)


ONE_ROW_INDEX = [{"route": "handbook", "vector": route_eval.offline_embed("notice period", 768), "row_id": "x"}]
WHO = {"employee": ["employee"], "leaver": ["leaver"], "grc_member alone": ["grc_member"]}
assert roles.desks(["grc_member"]) == set() and roles.desks(["leaver"]) == {"case"}
assert roles.desks(["employee"]) == {"handbook", "statute", "clarify", "out_of_scope", "case"}
RR = {r["id"]: r for r in ROUTE_ROWS}
WAGES_CUT = td.WAGES_CUT
# The gate's own example, read from the kit's test so that tools/tests/test_desk_gate_lessons.py, which holds every
# lesson question to "never fires on acme", does not see it as one of this page's questions.
HUMAN_HINGLISH = next(q for lang, q in kt.EXAMPLES["human_requested"] if lang == "hinglish" and q.startswith("Mujhe"))
assert desk_rules.gate(HUMAN_HINGLISH) == "human_requested"
QUESTIONS = [   # (text, where it comes from)
    (POSH, "smoke/smoke_cases.py, the POSH question its smoke asks"),
    (HUMAN_HINGLISH, "commands/tests/test_desk_rules.py, a human_requested example (Hinglish)"),
    (RR["lk-10"]["question"], "evals/desk/routes.jsonl, row lk-10"),
    (f"Whose GSTIN is {td.GSTIN}?", "commands/tests/test_desk.py's GSTIN, with a valid check character"),
    ("What does NP-03 say about notice?", "a handbook clause code: NP is in acme's clause-prefix map"),
    (RR["lk-18"]["question"], "evals/desk/routes.jsonl, row lk-18"),
    ("Under the Payment of Bonus Act, what bonus do I get?", "a named Act, and \"I\" in the question"),
    (WAGES_CUT, "commands/tests/test_desk.py, WAGES_CUT"),
    ("Who approves under FIN-02 and the Code on Wages?", "two anchors: a clause code and a named Code"),
    (RR["lk-06"]["question"], "evals/desk/routes.jsonl, row lk-06"),
    ("What is the notice period?", "no identifier at all"),
    (f"My Aadhaar {td.AADHAAR} is on the joining form. Which form changes the address on it?",
     "commands/tests/test_desk.py's AADHAAR, a number with a valid check digit"),
]


def ctx_for(who, **kw):
    base = {"tenant": "acme", "roles": WHO[who], "single": None, "coverage": {}, "clause_prefixes": ACME_PREFIXES,
            "index": ONE_ROW_INDEX, "max_parts": 1, "now": NOW}
    base.update(kw)
    return base


def trace(q, who):
    """The stages a question passes, as the widget shows them, from decide() and the rules it calls."""
    m = Recording()
    d = desk_router.decide(q, ctx_for(who), m)
    permitted = sorted(roles.desks(WHO[who]))
    gate = desk_rules.gate(q)
    masked, kinds = desk_rules.mask(q)
    hints = desk_router.anchors(masked, ACME_PREFIXES)
    nearhit = desk_rules.near(masked)
    st = [["yes", f"Who: {', '.join(WHO[who])} opens {', '.join(permitted) if permitted else 'no desk'}."]]
    if gate:
        st.append(["stop", f"Gate: the words match the {gate} class. A person takes it, the question text is not kept, and no model reads it."])
        assert (d["route"], d["method"], d["case_type"], m.calls) == ("case", "rule", gate, [])
        return {"stages": st, "route": "case", "method": "rule", "masked": None, "case_type": gate}
    st.append(["no", "Gate: no class matches."])
    if not permitted:
        st.append(["stop", "Roles: none of these roles opens a desk, so the turn is denied here, with no model call."])
        assert (d["route"], d["method"], m.calls) == ("denied", "rule", [])
        return {"stages": st, "route": "denied", "method": "rule", "masked": None, "case_type": None}
    st.append(["yes" if kinds else "no", f"Masking: {', '.join(kinds)} replaced before anything else reads the question." if kinds
               else "Masking: no Aadhaar or card number to replace."])
    assert d["question"] == masked and d["masked"] == kinds
    if not hints:
        st.append(["no", "Anchors: no identifier names a desk."])
    elif len(hints) == 1 and not nearhit:
        st.append(["stop", f"Anchors: one identifier points to {hints[0]}, and nothing in the words is near a case. The anchor decides."])
    elif len(hints) == 1:
        st.append(["next", f"Anchors: {hints[0]}, but the words are near a case (\"I\", \"my\" or a case topic), so the anchor is only a hint to the models."])
    else:
        st.append(["next", f"Anchors: {' and '.join(hints)}, more than one, so they are hints to the models."])
    if len(hints) == 1 and not nearhit:
        assert d["method"] == "anchor" and m.calls == []
        if d["route"] == "denied":
            st.append(["stop", f"Roles: {', '.join(WHO[who])} does not open the {hints[0]} desk. Denied, with no model call."])
        else:
            st.append(["yes", f"Roles: {', '.join(WHO[who])} opens {hints[0]}."])
        return {"stages": st, "route": d["route"], "method": "anchor", "masked": masked if kinds else None,
                "case_type": None, "desk": hints[0]}
    assert Counter(m.calls)["l1"] == 1 and Counter(m.calls)["embed"] == 1, m.calls    # L1 and the vote, in parallel
    st.append(["next", "Models: L1 (flash-lite) and the vote over the tenant's exemplars run in parallel, then the acceptance rules (panel B)."])
    outcome = {}
    for r in desk_router.ROUTES:                             # what the roles allow, whatever L1 says
        mm = Recording(r)
        outcome[r] = desk_router.decide(q, ctx_for(who), mm)["route"]
    if who == "leaver":
        assert outcome == {r: ("case" if r == "case" else "denied") for r in desk_router.ROUTES}, outcome
        st.append(["stop", "Roles: a leaver opens only the case desk. Whatever the models choose, any other route ends denied."])
    else:
        assert outcome == {r: r for r in desk_router.ROUTES}, outcome
    return {"stages": st, "route": None, "method": "models", "after": "denied" if who == "leaver" else None,
            "masked": masked if kinds else None, "case_type": None}


PANEL_A = []
for q, src in QUESTIONS:
    PANEL_A.append({"q": q, "src": src, "by": {w: trace(q, w) for w in WHO}})
by_emp = {p["q"]: p["by"]["employee"] for p in PANEL_A}
assert [by_emp[q]["method"] for q, _ in QUESTIONS] == ["rule", "rule", "anchor", "anchor", "anchor", "anchor", "models",
                                                       "models", "models", "models", "models", "models"], [by_emp[q]["method"] for q, _ in QUESTIONS]
assert [by_emp[q]["route"] for q, _ in QUESTIONS[:6]] == ["case", "case", "out_of_scope", "out_of_scope", "handbook", "statute"]
assert by_emp[POSH]["case_type"] == "posh" and by_emp[QUESTIONS[1][0]]["case_type"] == "human_requested"
assert by_emp[QUESTIONS[-1][0]]["masked"] == "My Aadhaar [Aadhaar] is on the joining form. Which form changes the address on it?"
assert desk_rules.near(WAGES_CUT) and desk_router.anchors(WAGES_CUT, ACME_PREFIXES) == ["statute"]
N_RULE = sum(1 for p in PANEL_A if p["by"]["employee"]["method"] in ("rule", "anchor"))


# panel B: the acceptance rules. The script below mirrors accept() and candidates(); node runs it over a grid of every
# input the panel offers, and the build compares each answer with the kit's own functions.
PB = {"l1": list(desk_router.ROUTES) + ["none"], "second": desk_router.SCHEMA["properties"]["second_route"]["enum"],
      "ctype": desk_router.SCHEMA["properties"]["case_type"]["enum"], "kroute": list(desk_router.ROUTES) + ["none"],
      "kvotes": list(range(1, TH["K"] + 1)), "kcase": list(range(0, TH["K"] + 1)),
      "ksim": [0.95, 0.85, 0.75, 0.71, 0.70, 0.69, 0.60, 0.45],
      "anch": [[], ["handbook"], ["statute"], ["out_of_scope"], ["handbook", "statute"], ["statute", "out_of_scope"],
               ["handbook", "out_of_scope"]]}
assert TH["TAU_OOS"] in PB["ksim"]
ACCEPT_JS = r"""function mkL1(route, second, ctype){ return route === 'none' ? null : {route: route, second_route: second, case_type: ctype}; }
function mkKnn(route, votes, kcase, sim, K){ if (route === 'none') return null; var v = {}; v[route] = votes; if (route !== 'case' && kcase > 0) v.case = kcase; return {route: route, share: votes / K, sim: sim, votes: v}; }
function caseSignal(l1, knn, th){ if (l1 && (l1.route === 'case' || l1.second_route === 'case' || l1.case_type === 'posh')) return true; return !!(knn && (knn.votes.case || 0) >= th.CASE_VOTES); }
function accept(l1, knn, anch, th){
  if (caseSignal(l1, knn, th)) return ['case', 'D'];
  if (!l1) return null;
  if (knn && knn.route === l1.route && knn.share * th.K >= th.ACCEPT_VOTES - 1e-9) return [l1.route, 'A'];
  if (anch.indexOf(l1.route) >= 0) return [l1.route, 'B'];
  if (l1.route === 'out_of_scope' && knn !== null && knn.sim < th.TAU_OOS) return ['out_of_scope', 'C'];
  return null; }
function candidates(l1, knn, routes){ var out = []; [l1.route, knn ? knn.route : null, 'clarify'].forEach(function(r){ if (routes.indexOf(r) >= 0 && out.indexOf(r) < 0) out.push(r); }); return out; }
"""


def py_mk(route, second, ctype, kroute, votes, kcase, sim):
    l1 = None if route == "none" else {"route": route, "second_route": second, "case_type": ctype}
    if kroute == "none":
        return l1, None
    v = {kroute: votes}
    if kroute != "case" and kcase > 0:
        v["case"] = kcase
    return l1, {"route": kroute, "share": votes / TH["K"], "sim": sim, "votes": v}


def grid_py():
    out = []
    for r, s2, ct, kr, kv, kc, ks, an in itertools.product(*(PB[k] for k in ("l1", "second", "ctype", "kroute", "kvotes", "kcase", "ksim", "anch"))):
        l1, knn = py_mk(r, s2, ct, kr, kv, kc, ks)
        v = desk_router.accept(l1, knn, an)
        out.append(f"{v[1]}{v[0]}" if v else ("F" + ",".join(desk_router.candidates(l1, knn)) if l1 else "N"))
    return ";".join(out)


NODE = shutil.which("node") or "/opt/node22/bin/node"
GRID_JS = ACCEPT_JS + r"""
var P = %s, TH = %s, ROUTES = %s, out = [];
P.l1.forEach(function(r){ P.second.forEach(function(s2){ P.ctype.forEach(function(ct){ P.kroute.forEach(function(kr){
P.kvotes.forEach(function(kv){ P.kcase.forEach(function(kc){ P.ksim.forEach(function(ks){ P.anch.forEach(function(an){
  var l1 = mkL1(r, s2, ct), knn = mkKnn(kr, kv, kc, ks, TH.K), v = accept(l1, knn, an, TH);
  out.push(v ? v[1] + v[0] : (l1 ? 'F' + candidates(l1, knn, ROUTES).join(',') : 'N'));
}); }); }); }); }); }); }); });
process.stdout.write(require('crypto').createHash('sha256').update(out.join(';')).digest('hex') + ' ' + out.length);
""" % (json.dumps(PB), json.dumps(TH), json.dumps(list(desk_router.ROUTES)))
with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
    f.write(GRID_JS)
got = subprocess.run([NODE, f.name], capture_output=True, text=True, check=True).stdout.split()
os.unlink(f.name)
_g = grid_py()
N_GRID = _g.count(";") + 1
assert got == [hashlib.sha256(_g.encode()).hexdigest(), str(N_GRID)], (got, N_GRID)
del _g


# ------------------------------------------------------------------ the stand-ins: one fake Firestore for every cell
DELETE = tc.FS.DELETE_FIELD


class Snap:
    def __init__(self, ref, data):
        self.reference, self.id, self._d, self.exists, self.update_time = ref, ref.id, data, data is not None, None

    def to_dict(self):
        return copy.deepcopy(self._d)


class Ref:
    def __init__(self, db, path):
        self.db, self.path, self.id = db, path, path.rsplit("/", 1)[-1]

    def get(self, transaction=None, field_paths=None):
        return Snap(self, copy.deepcopy(self.db.docs.get(self.path)))

    def set(self, data, merge=False):
        data = copy.deepcopy(data)
        if merge is True and self.path in self.db.docs:
            self.db.docs[self.path].update(data)
        elif isinstance(merge, list) and self.path in self.db.docs:
            self.db.docs[self.path].update({k: data[k] for k in merge})
        else:
            self.db.put(self.path, data)

    def update(self, data):
        doc = self.db.docs[self.path]
        for k, v in data.items():
            if v is DELETE:
                doc.pop(k, None)
            else:
                doc[k] = copy.deepcopy(v)

    def delete(self):
        self.db.drop(self.path)

    def collection(self, name):
        return Query(self.db, f"{self.path}/{name}")


class Query:
    def __init__(self, db, path, filters=(), order=(), lim=None):
        self.db, self.path, self.filters, self.order, self.lim = db, path, filters, order, lim

    def document(self, id_):
        return Ref(self.db, f"{self.path}/{id_}")

    def where(self, field=None, op=None, value=None, *, filter=None):
        if filter is not None:
            field, op, value = filter.field_path, filter.op_string, filter.value
        return Query(self.db, self.path, self.filters + ((field, op, value),), self.order, self.lim)

    def select(self, fields):
        return self

    def order_by(self, field, direction="ASCENDING"):
        return Query(self.db, self.path, self.filters, self.order + ((field, direction),), self.lim)

    def limit(self, n):
        return Query(self.db, self.path, self.filters, self.order, n)

    def stream(self, retry=None, timeout=None):              # both reads pass them: the shadow's and desk_recall's
        rows = []
        for id_, path in sorted(self.db.kids.get(self.path, {}).items()):
            doc = self.db.docs[path]
            ok = True
            for field, op, value in self.filters:
                v = doc.get(field)
                ok = ok and ((op == "==" and v == value) or (op == "in" and v in value)
                             or (op == "<=" and v is not None and v <= value)
                             or (op == "array_contains" and isinstance(v, list) and value in v))
            if ok:
                rows.append(Snap(Ref(self.db, path), copy.deepcopy(doc)))
        for field, direction in reversed(self.order):
            rows.sort(key=lambda s: (s._d.get(field) is not None, s._d.get(field) or 0), reverse=direction == "DESCENDING")
        return iter(rows[: self.lim] if self.lim else rows)

    def get(self):
        return list(self.stream())


class Batch:
    def __init__(self):
        self.ops = []

    def update(self, ref, data):
        self.ops.append(lambda: ref.update(data))

    def set(self, ref, data, merge=False):
        self.ops.append(lambda: ref.set(data, merge=merge))

    def delete(self, ref):
        self.ops.append(ref.delete)

    def commit(self):
        for op in self.ops:
            op()
        self.ops = []


class FakeDB:
    def __init__(self):
        self.docs, self.kids = {}, {}

    def put(self, path, data):
        self.docs[path] = data
        head, _, id_ = path.rpartition("/")
        self.kids.setdefault(head, {})[id_] = path

    def drop(self, path):
        self.docs.pop(path, None)
        head, _, id_ = path.rpartition("/")
        self.kids.get(head, {}).pop(id_, None)

    def collection(self, name):
        return Query(self, name)

    def batch(self):
        return Batch()

    def transaction(self):
        return tc.Tx(self)

    def get_all(self, refs, field_paths=None, transaction=None):
        return [r.get() for r in refs]


db = FakeDB()
TODAY = datetime(2026, 10, 1, 5, 30, tzinfo=timezone.utc)
_hex = (hashlib.sha256(f"lesson 10.6, stand-in {i}".encode()).hexdigest() for i in itertools.count())
_tick = itertools.count()


def tick() -> datetime:
    return TODAY + timedelta(seconds=next(_tick))


class FakeDT(datetime):
    @classmethod
    def now(cls, tz=None):
        return tick()


class Blob:
    def __init__(self, bucket, name):
        self.bucket, self.name, self.data = bucket, name, ""

    def upload_from_string(self, data, content_type=None):
        self.data = data
        self.bucket.blobs.append(self)


class Bucket:
    def __init__(self, name):
        self.name, self.blobs = name, []

    def blob(self, name):
        return Blob(self, name)


AUDIT = Bucket(f"{LANE_ID}-audit")
fake_storage = types.ModuleType("google.cloud.storage")
fake_storage.Client = lambda *a, **k: types.SimpleNamespace(bucket=lambda name: AUDIT, get_bucket=lambda name: AUDIT)
cases = sys.modules.get("shared.cases") or __import__("shared.cases", fromlist=["cases"])
audit_log = tc.audit_log
STACK = contextlib.ExitStack()
for p in (patch.object(cases, "_fs", lambda: tc.FS), patch.object(cases, "_now", tick),
          patch.object(cases, "secrets", types.SimpleNamespace(token_hex=lambda n=16: next(_hex)[:2 * n])),
          patch.object(audit_log, "storage", fake_storage), patch.object(audit_log, "_bucket", None),
          patch.object(audit_log, "datetime", FakeDT),
          patch.object(audit_log, "uuid", types.SimpleNamespace(uuid4=lambda: uuid.UUID(hex=next(_hex)[:32], version=4))),
          patch.dict(os.environ, {"AUDIT_BUCKET": f"{LANE_ID}-audit"})):
    STACK.enter_context(p)


def sa(name: str) -> str:
    return f"documind-{name}-sa@{LANE_ID}.iam.gserviceaccount.com"


# the lane as lesson 5.6 left it: the rosters, acme's queues with you on both committees, your roles; desk_gate unset,
# so acme has the gate's rules
TENANT_OF: dict[str, str] = {}


def roster(tenant, members):
    plan, policies = lane.roster_plan(LANE_ID, tenant, members)
    for t, e in plan:
        TENANT_OF.setdefault(e.lower(), t)
        db.put(f"tenants/{t}/members/{e.lower()}", {"email": e.lower()})
    for t, r in policies:
        db.collection("tenant_settings").document(t).set({"data_region": r}, merge=True)
    return plan, policies


roster("acme", [ME])
roster("acme", [sa("evalacme"), sa("evalgrc")])
roster("zeta", [sa("evalzeta")])
QFILE = {t: json.loads((KIT / f"evals/desk/queues.{t}.json").read_text(encoding="utf-8")) for t in ("acme", "zeta", "globex")}
db.collection("tenant_settings").document("acme").set(
    {"case_queues": tc.desk_ops._notes_off(QFILE["acme"]), "case_queues_set_by": ME}, merge=True)
cases_roles = {ME: ["employee", "grc_member", "ic_member:hyderabad", "ic_member:pune"], sa("evalgrc"): ["grc_member"]}
for e, rs in cases_roles.items():
    db.put(f"tenants/acme/roles/{e.lower()}", {"roles": rs, "set_by": ME})


# the corpus as evals/upload.sh and make media leave it on a default lane: every manifest object whose file the kit
# holds, a PDF's text mirror skipped for its PDF; no town hall video (make media --video is optional), no whiteboard
# photograph (the owner supplies it). The chunks are the worker's for the same bytes (shared/documind_corpus.py mints
# the same texts and locators), with the lane's ids, tenant:sha256#i, every text row "unknown" and every figure
# "figure", as the worker writes them before any registry exists.
from shared import documind_corpus  # noqa: E402

MANIFEST = json.loads((KIT / "evals/manifest.json").read_text(encoding="utf-8"))
ON_LANE, CHUNKS_OF = [], {}
for m in MANIFEST:
    f = KIT / "evals" / m["file"]
    if not f.exists() or f.suffix == ".mp4":
        continue
    ON_LANE.append(m)
assert len(MANIFEST) == 33 and len(ON_LANE) == 31
assert {m["file"].rsplit("/", 1)[1] for m in MANIFEST} - {m["file"].rsplit("/", 1)[1] for m in ON_LANE} == {
    "townhall_2026_q1.mp4", "whiteboard_arch.png"}
for m in ON_LANE:
    t, f = m["tenant_id"], KIT / "evals" / m["file"]
    sha = hashlib.sha256(f.read_bytes()).hexdigest()
    if m.get("sha256"):
        assert sha == m["sha256"], m["file"]
    name, uri = f"{t}/{f.name}", f"gs://{LANE_ID}-uploads/{t}/{f.name}"
    doc_key = f"{t}_{sha}"
    if f.suffix == ".png":
        pieces = [{"text": f"(the figure's caption) {f.stem}", "locator": "figure", "kind": "figure"}]
    else:
        mirror = f.with_suffix(".md")
        if mirror.exists():
            pieces = [{"text": c["text"], "locator": c["locator"], "kind": "text"} for c in documind_corpus.chunk_document(
                {"text": mirror.read_text(encoding="utf-8"), "source_uri": uri, "doc_type": "unknown", "slug": f.stem}, t)]
        else:                                            # posh_act_2013.pdf: a scan, read by Document AI's OCR
            pieces = [{"text": "(the scan's OCR text)", "locator": "p1-0", "kind": "text"}]
    CHUNKS_OF[name] = []
    for i, c in enumerate(pieces):
        cid = f"{t}:{sha}#{i}"
        db.put(f"chunks/{cid}", {"tenant_id": t, "source_uri": uri, "doc_key": doc_key, "doc_type": c["kind"] if c["kind"] != "text" else "unknown",
                                  "kind": c["kind"], "current": True, "staged": False, "text": c["text"], "locator": c["locator"]})
        CHUNKS_OF[name].append(cid)
    db.put(f"sources/{t}~{f.name}", {"tenant_id": t, "name": name, "gcs_uri": uri, "doc_key": doc_key, "sha256": sha,
                                     "status": "indexed", "chunks": len(pieces)})

# What earlier lessons leave on a lane that the manifest does not name, so the registry never classes them: 1.4's
# personalised acme/smoke_note_v1.md, 3.4's acme/smoke_note.md (the demo note's v1 bytes, restored at that lesson's
# end), 3.8's acme/pune_visitor_rules.md (which "can stay") and 1.2's copy of the maternity amendment under globex.
# 4.8's vendor note is retired by its lesson, so it has no current rows. The worker wrote them "unknown", and the
# relabel leaves an unregistered object as it is.
ROOT = pb.ROOT
P64 = html.unescape((ROOT / "lessons/03-generation/3.8-ui-journey/parts/b.html").read_text(encoding="utf-8")
                    .split('cat &gt; "$HOME/pune_visitor_rules.md" &lt;&lt;EOF\n', 1)[1].split("\nEOF\n", 1)[0])
NOTE_V1 = (KIT / "evals/demo/smoke_note_v1.md").read_text(encoding="utf-8")
LEFT_BY_LESSONS = {
    "acme/smoke_note_v1.md": NOTE_V1 + "\nPersonalised for you@example.com in lesson 1.4.\n",
    "acme/smoke_note.md": NOTE_V1,
    "acme/pune_visitor_rules.md": P64.replace("$ME", "you@example.com").replace("$(date -u +%F)", "2026-09-23") + "\n",
    "globex/maternity_benefit_amendment_act_2017.pdf":
        (KIT / "evals/corpus/acme/maternity_benefit_amendment_act_2017.md").read_text(encoding="utf-8"),
}
assert "smoke_note_v1.md" in (ROOT / "lessons/01-rag-foundation/1.4-indexed-records/parts/c.html").read_text(encoding="utf-8")
assert 'evals/demo/smoke_note_v1.md "gs://$PROJECT-uploads/acme/smoke_note.md"' in html.unescape(
    (ROOT / "lessons/03-generation/3.4-context-budget/Netsetos_GCP_Capstone_3.4_Context_Budget_WIX.html").read_text(encoding="utf-8"))
assert "TENANT=globex FILE=evals/corpus/acme/maternity_benefit_amendment_act_2017.pdf" in (
    ROOT / "lessons/01-rag-foundation/1.2-parse-and-chunk/parts/b.html").read_text(encoding="utf-8")
assert not set(LEFT_BY_LESSONS) & {f"{m['tenant_id']}/{m['file'].rsplit('/', 1)[1]}" for m in MANIFEST}
for name, text in LEFT_BY_LESSONS.items():
    t, fname = name.split("/", 1)
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    uri = f"gs://{LANE_ID}-uploads/{name}"
    pieces = documind_corpus.chunk_document({"text": text, "source_uri": uri, "doc_type": "unknown",
                                             "slug": fname.rsplit(".", 1)[0]}, t)
    CHUNKS_OF[name] = []
    for i, c in enumerate(pieces):
        cid = f"{t}:{sha}#{i}"
        db.put(f"chunks/{cid}", {"tenant_id": t, "source_uri": uri, "doc_key": f"{t}_{sha}", "doc_type": "unknown",
                                  "kind": "text", "current": True, "staged": False, "text": c["text"], "locator": c["locator"]})
        CHUNKS_OF[name].append(cid)
    db.put(f"sources/{t}~{fname}", {"tenant_id": t, "name": name, "gcs_uri": uri, "doc_key": f"{t}_{sha}", "sha256": sha,
                                    "status": "indexed", "chunks": len(pieces)})
UNREGISTERED = {t: sorted(n for n in LEFT_BY_LESSONS if n.startswith(t + "/")) for t in ("acme", "zeta", "globex")}

NP03 = next(cid for cid in CHUNKS_OF["acme/hr_policy_2026.md"] if db.docs[f"chunks/{cid}"]["locator"] == "NP-03")
assert NP03.endswith("#1") and db.docs[f"chunks/{NP03}"]["text"].startswith("NP-03 — Notice period")
PNG_SHA = {hashlib.sha256((KIT / "evals" / m["file"]).read_bytes()).hexdigest(): m["file"].rsplit("/", 1)[1]
           for m in ON_LANE if m["file"].endswith(".png")}
assert len(PNG_SHA) == 3


def ops(*args) -> tuple[str, int]:
    """commands/desk_ops.py, as make runs it, against the fake Firestore."""
    fs = types.SimpleNamespace(Client=lambda project=None: db, SERVER_TIMESTAMP="SERVER_TIMESTAMP")
    with tc.cloud_modules(firestore=fs), patch.dict(os.environ, {"DOCUMIND_OPERATOR": ME}), redirect_stdout(io.StringIO()) as out:
        code = tc.desk_ops.main(["--project", LANE_ID, *args])
    return out.getvalue(), code


import relabel  # noqa: E402  - services/ingest/relabel.py, the module desk_ops imports
SEARCHED: dict = {}


class SearchStandIn:
    """Step 3 of the relabel on a stand-in: each version's Vertex AI Search document, updated once."""

    def __init__(self, store):
        self.store = store

    def __call__(self, tenant_id, doc_key, doc_type):
        was = SEARCHED.get(doc_key)
        SEARCHED[doc_key] = doc_type
        return "unchanged" if was == doc_type else "updated"


class Job:
    num_dml_affected_rows = 0

    def result(self):
        return None


bq_mod = types.SimpleNamespace(Client=lambda project=None: types.SimpleNamespace(query=lambda sql, job_config=None: Job()),
                               ScalarQueryParameter=lambda *a: a, ArrayQueryParameter=lambda *a: a,
                               QueryJobConfig=lambda **k: k)
indexer_mod = types.ModuleType("indexer")
indexer_mod._repair_snapshots = lambda index_name, db_, snaps, batch_size=100: len(list(snaps))
indexer_mod.remove_datapoints = lambda index_name, ids: None
managed_mod = types.ModuleType("managed")


class _Store:
    def __init__(self, project, location="global", bucket="", clients=None):
        self.location = location

    @property
    def region(self):
        return self.location


managed_mod.VertexSearchStore = _Store
INDEX_NAME = "projects/NUMBER/locations/REGION/indexes/INDEX_ID"


def relabel_run(tenant, *extra) -> tuple[str, int]:
    """services/ingest/relabel.py, as make doc-types runs it after desk_ops, against the same stand-ins."""
    fs = types.SimpleNamespace(Client=lambda project=None: db, SERVER_TIMESTAMP="SERVER_TIMESTAMP")
    env = {"GOOGLE_CLOUD_PROJECT": LANE_ID, "MANAGED_MIRROR": "both", "BQ_CHUNK_TABLE": f"{LANE_ID}.rag_data.chunk_source",
           "VECTOR_INDEX_NAME": INDEX_NAME}
    with tc.cloud_modules(firestore=fs, bigquery=bq_mod), patch.dict(sys.modules, {"indexer": indexer_mod, "managed": managed_mod}), \
            patch.object(relabel, "SearchLabels", SearchStandIn), patch.dict(os.environ, env), redirect_stdout(io.StringIO()) as out:
        code = relabel.main(["--project", LANE_ID, "--tenant", tenant, *extra])
    return out.getvalue(), code


def doc_types_make(tenant, *flags, apply=False) -> str:
    """make doc-types: desk_ops doc-types, then relabel.py (the plan, or --apply)."""
    o1, c1 = ops("doc-types", "--tenant", tenant, *flags)
    o2, c2 = relabel_run(tenant, *(["--apply"] if apply else []))
    assert (c1, c2) == (0, 0), (o1, o2)
    return o1 + o2


# ------------------------------------------------------------------ step 3 on the stand-ins
OUT: dict[str, str] = {}
RAW: dict[str, str] = {}
ROSTER_G, POLICIES = roster("globex", [sa("evalglobex")])
ROSTER_L, _ = roster("acme", [sa("evalleaver")])
assert POLICIES == [("acme", "any"), ("zeta", "any"), ("globex", "in")]
o_r = []
for who, rs in ((sa("evalacme"), "employee,desk_eval"), (sa("evalleaver"), "leaver,desk_eval")):
    o, c = ops("roles", "--tenant", "acme", "--email", who, "--set", rs)
    assert c == 0, o
    o_r.append(o)
o, c = ops("roles", "--tenant", "globex", "--email", sa("evalglobex"), "--set", "employee,desk_eval,ic_member:head_office")
assert c == 0, o
o_r.append(o)
RAW["ids_roles"] = "".join(o_r)
assert roles.desks(roles.roles_for(db, "acme", sa("evalleaver"))) == {"case"}

# make doc-types TENANT=acme SEED=manifest: the registry written, the view, the relabel's plan
RAW["labels"] = doc_types_make("acme", "--seed", "manifest")
# APPLY=1 for acme, then zeta and globex seeded and applied in one run each
RAW["apply_acme"] = doc_types_make("acme", apply=True)
RAW["apply_zeta"] = doc_types_make("zeta", "--seed", "manifest", apply=True)
RAW["apply_globex"] = doc_types_make("globex", "--seed", "manifest", apply=True)
RAW["again"] = doc_types_make("acme")
for t in ("acme", "zeta", "globex"):      # every current row now carries its class
    assert not relabel.plan_lines(relabel.plan(relabel.read_rows(db, t), doc_types.read_registry(db, t))), t
assert db.docs[f"chunks/{NP03}"]["doc_type"] == "policy"

# make route-index for acme and zeta: the real rows and version; the embeddings offline (no lane)
OFFLINE_768 = types.SimpleNamespace(embed_many=lambda texts: [route_eval.offline_embed(x, 768) for x in texts])
with patch.object(desk_router.GeminiModels, "for_project", classmethod(lambda cls, project: OFFLINE_768)):
    RAW["index"] = "".join(ops("route-index", "--tenant", t)[0] for t in ("acme", "zeta"))

# make desk TENANT=acme DESK_ROUTE=on; globex's queues with its eval account as the committee; globex in single mode
T = Path(tempfile.mkdtemp(prefix="lesson106-"))
QG = T / "queues.globex.json"
QG.write_text((KIT / "evals/desk/queues.globex.json").read_text(encoding="utf-8").replace("you@example.com", sa("evalglobex")), encoding="utf-8")
ALERTS_ECHO = re.search(r'\$\(if \$\(filter shadow on,\$\(DESK_ROUTE\)\),@echo ">> (.+?)"\)', mk_src).group(1)
o1, c1 = ops("desk", "--tenant", "acme", "--route", "on")
o2, c2 = ops("queues", "--tenant", "globex", "--file", str(QG))
o3, c3 = ops("desk", "--tenant", "globex", "--route", "single", "--single", "statute")
assert (c1, c2, c3) == (0, 0, 0), (o1, o2, o3)
assert json.loads(o1)["desk_route"] == "on" and json.loads(o3)["desk_route"] == "single" and json.loads(o3)["desk_single"] == "statute"
assert json.loads(o2)["posh_missing"] == [] and all(x.startswith("queue ") for x in json.loads(o2)["not_readers"])
RAW["switch"] = o1 + ">> " + ALERTS_ECHO + "\n" + o2.replace(str(QG), "/home/you/queues.globex.json") + o3

# ------------------------------------------------------------------ the chat service: agent.py's app with the Desk
from fastapi.testclient import TestClient  # noqa: E402
import agent  # noqa: E402  - services/chat/agent.py: its lifespan opens an InMemorySaver (CHECKPOINT_DSN=memory)
import desk as chat_desk  # noqa: E402
from shared import documind_tools, iap  # noqa: E402

door_mod = load("desk_door_106", "services/rag-api/desk_door.py")
BEARER = {"ui": sa("ui"), "evalacme": sa("evalacme"), "evalgrc": sa("evalgrc"), "evalzeta": sa("evalzeta"),
          "evalleaver": sa("evalleaver"), "evalglobex": sa("evalglobex"), "outsider": sa("outsider"), "me": ME}
TOKEN_FOR = {v: k for k, v in BEARER.items()}


def bearer_email(headers) -> str:
    auth = headers.get("authorization") or ""
    who = BEARER.get(auth[7:]) if auth.startswith("Bearer ") else None
    if not who:
        raise iap.IapError("no identity: neither an IAP assertion nor a bearer token")
    return who


def tenant_for(email):
    return TENANT_OF.get(str(email or "").lower())


def settings(tenant):
    return copy.deepcopy(db.docs.get(f"tenant_settings/{tenant}") or {})


ROUTE_ROWS_BY_Q = {}
for r in ROUTE_ROWS:
    ROUTE_ROWS_BY_Q.setdefault(route_eval.normalise(r["question"]), r)
EXTRA_L1 = {"What is the notice period?": ("clarify", "none"), td.FIGURE: ("handbook", "none")}
FIGURES = [r["id"] for r in ROUTE_ROWS if r["note"].startswith("a figure:")]      # the route set's figure rows
assert FIGURES == ["jn-03"] and RR["jn-03"]["must_contain"] == ["45", "60"] and RR["jn-03"]["expected_route"] == "handbook"


class TableModels:
    """The stand-in classifier and arbiter: L1 answers a route-set row's own label (the table is the route set, so it
    is never wrong here; on your lane flash-lite decides), L2 picks the label when it is a candidate; the query
    embedding is the same offline embedding the index was built with. needs_calculation is true for the route set's
    one figure row, jn-03, so its turn runs the handbook desk's agent mode. Token counts as route_eval.py's
    ScriptedModels count them: the prompt's characters / 4 in, 30 out."""

    def l1(self, text):
        q = desk_router.prompt_parts(text)["question"]
        row = ROUTE_ROWS_BY_Q.get(route_eval.normalise(q))
        route, ct = (row["expected_route"], row["case_type"]) if row else EXTRA_L1[q]
        return ({"route": route, "second_route": "none", "case_type": (ct or "people_query") if route == "case" else "none",
                 "needs_calculation": bool(row) and row["id"] in FIGURES, "followup": False},
                {"tokens_in": len(text) // 4, "tokens_out": 30, "cached": 0})

    def l2(self, text, cands):
        q = text.rsplit("Question: <<<", 1)[1].rsplit(">>>", 1)[0]
        row = ROUTE_ROWS_BY_Q.get(route_eval.normalise(q))
        want = row["expected_route"] if row else EXTRA_L1[q][0]
        return (want if want in cands else "clarify"), {"tokens_in": len(text) // 4, "tokens_out": 30, "cached": 0}

    def embed(self, text):
        return route_eval.offline_embed(text, 768)


_WORDS = re.compile(r"[a-z0-9.,]+")


def _sentence(text: str, phrase: str | None) -> str:
    parts = re.split(r"(?<=[.;])\s+", " ".join(text.split()))
    hit = next((x for x in parts if phrase and phrase.lower() in x.lower()), None)
    return hit or parts[0]


RETRIEVED: list[dict] = []


def retrieve(query, tenant_id, top_k=5, doc_type=None, assertion=None, brain=None, passages=False):
    """rag-api's /v1/query on a stand-in: the tenant's current rows of the filter's classes, ranked by the question's
    words (and the row's must_contain phrase, when the question is a route-set row); the answer is the top passage's
    own sentence. With passages=True it is /v1/passages, as an agent desk searches: the same ranking, each chunk's
    full text and no answer. On your lane rag-api's retriever ranks and its model writes the answer."""
    RETRIEVED.append({"tenant": tenant_id, "doc_type": doc_type, "brain": brain})
    words = {w for w in _WORDS.findall(query.lower()) if len(w) > 3 and w not in route_eval._STOP}
    row = ROUTE_ROWS_BY_Q.get(route_eval.normalise(query.split("\n\n(This part:")[0]))
    phrase = (row or {}).get("must_contain", [None])[0] if (row or {}).get("must_contain") else None
    pool = [(path.split("/", 1)[1], db.docs[path]) for path in db.kids.get("chunks", {}).values()]
    pool = [(cid, c) for cid, c in pool if c["tenant_id"] == tenant_id and c["current"]
            and (not doc_type or c["doc_type"] in doc_type)]
    df = Counter(w for _, c in pool for w in words if w in c["text"].lower())
    idf = {w: math.log((len(pool) + 1) / (df[w] + 1)) for w in words}
    scored = []
    for cid, c in pool:
        text = c["text"].lower()
        hits = [w for w in words if w in text]
        score = sum(idf[w] for w in hits) + (10.0 if phrase and phrase.lower() in text and len(hits) >= 2 else 0.0)
        if score > 0:
            scored.append((score, cid, c))
    scored.sort(key=lambda t: (-t[0], t[1]))
    top = scored[:top_k]
    if passages:                                         # main.py's /v1/passages: no model, no cost
        return {"passages": [{"n": i, "chunk_id": cid, "source_uri": c["source_uri"], "page": None, "doc_type": c["doc_type"],
                              "kind": c["kind"], "section": c.get("section"), "text": c["text"]} for i, (_, cid, c) in enumerate(top, 1)],
                "answerable": bool(top), "usage": {"model": "none", "tokens_in": 0, "tokens_out": 0, "cached_tokens": 0, "cost_usd": 0.0}}
    cites = [{"chunk_id": cid, "source_uri": c["source_uri"], "page": None, "quote": " ".join(c["text"].split())[:160],
              "score": round(sc / (top[0][0] or 1), 3)} for sc, cid, c in top]
    out = {"citations": cites, "answerable": bool(cites), "confidence": "high" if cites else "low",
           "usage": {"model": "gemini-3.6-flash", "tokens_in": 2000, "tokens_out": 200, "cached_tokens": 0, "cost_usd": None}}
    if cites:
        out["answer"] = _sentence(top[0][2]["text"], phrase) + " [1]"
    return out


import desk_agent  # noqa: E402  - services/chat/desk_agent.py, the agent mode desk_graph runs on a figure
from langchain_core.language_models.chat_models import BaseChatModel  # noqa: E402
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage  # noqa: E402
from langchain_core.outputs import ChatGeneration, ChatResult  # noqa: E402

AGENT_USAGE = {"input_tokens": 1000, "output_tokens": 50, "total_tokens": 1050}


class FigureAgent(BaseChatModel):
    """The agent mode's chat model on the stand-in, scripted for jn-03, the route set's one figure row: it searches
    with the person's words, calls encashable_days with the balance from the message and the cap from LV-07, then
    answers citing each passage by the n the search gave it. On your lane gemini-3.6-flash chooses the calls and writes
    the answer; the argument check, the arithmetic and the "Worked out in code" block are the kit's either way."""

    def _generate(self, messages, stop=None, run_manager=None, **kw):
        asked = next(m.content for m in messages if isinstance(m, HumanMessage))
        assert asked == RR["jn-03"]["question"], asked
        done = [m for m in messages if isinstance(m, ToolMessage)]
        if not done:
            msg = AIMessage(content="", usage_metadata=dict(AGENT_USAGE), tool_calls=[
                {"name": "retrieve", "args": {"query": asked}, "id": "call-1", "type": "tool_call"}])
        elif len(done) == 1:
            msg = AIMessage(content="", usage_metadata=dict(AGENT_USAGE), tool_calls=[
                {"name": "encashable_days", "args": {"balance": 50, "cap": 45}, "id": "call-2", "type": "tool_call"}])
        else:
            found = json.loads(done[0].content)["passages"]
            n = {code: next(x["n"] for x in found if x["text"].startswith(code + " ")) for code in ("LV-07", "NP-03")}
            msg = AIMessage(content=f"Of your 50 days of earned leave, 45 are encashed on exit, at basic pay [{n['LV-07']}]. A "
                                    f"confirmed employee at grade E3 or above serves a notice period of 60 days [{n['NP-03']}].",
                            usage_metadata=dict(AGENT_USAGE))
        return ChatResult(generations=[ChatGeneration(message=msg)])

    def bind_tools(self, tools, **kw):
        return self

    @property
    def _llm_type(self) -> str:
        return "scripted"


ROWS_LOGGED: list[tuple[str, dict]] = []


class Rows(logging.Handler):
    def __init__(self, service):
        super().__init__(logging.INFO)
        self.service = service

    def emit(self, record):
        try:
            ROWS_LOGGED.append((self.service, json.loads(record.getMessage())))
        except ValueError:
            pass


for name, svc in (("documind-api", "documind-api"), ("documind.chat.desk", "documind-chat"),
                  ("documind.chat.agent", "documind-chat"), ("documind.chat.desk_graph", "documind-chat"),
                  ("documind.chat.desk_router", "documind-chat"), ("documind.chat.delegation", "documind-chat"),
                  ("documind.gchat", "documind-gchat")):
    lg = logging.getLogger(name)
    lg.addHandler(Rows(svc))
    lg.setLevel(logging.INFO)
    lg.propagate = False

assert desk_recall.read_on_tenants(db) == frozenset()          # no company on this lane switches the model check on
for p in (patch.object(iap, "identity", lambda headers, bearer_audience=None: {"email": bearer_email(headers), "via": "iam"}),
          patch.object(agent, "PROFILE", "gcp"), patch.object(chat_desk, "PROFILE", "gcp"),
          patch.object(agent, "tenant_for", tenant_for), patch.dict(chat_desk._hooks, {"tenant_for": tenant_for}),
          patch.object(chat_desk, "settings", settings), patch.object(chat_desk, "_client", lambda: db),
          # the door's own tenants read, over the stand-in: no company on this lane is on, so the list is empty
          patch.object(chat_desk, "CHECKED",
                       desk_recall.OnTenants(lambda: desk_recall.read_on_tenants(db), chat_desk.log, "chat")),
          patch.object(chat_desk, "_models", lambda: TableModels()),
          patch.object(documind_tools, "retrieve", retrieve),
          patch.dict(desk_agent._AGENTS, clear=True), patch.dict(desk_agent._MODEL, {"llm": FigureAgent()})):
    STACK.enter_context(p)
chat_desk._RATE.clear()
chat_desk._COVERAGE.clear()
desk_router._INDEX.clear()


async def handler_app(scope, receive, send):           # rag-api's handlers: a question the gate does not take
    await receive()
    await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": b'{"handler":true}'})


def member(email, tenant):
    from fastapi import HTTPException
    if TENANT_OF.get(email.lower()) != tenant:
        raise HTTPException(403, f"{email} is not a member of {tenant}")


def api_verify(c):
    try:
        return {"email": bearer_email(c.headers)}
    except iap.IapError as e:
        from fastapi import HTTPException
        raise HTTPException(401, str(e))


api_app = door_mod.DeskDoor(handler_app, settings=settings, verify=api_verify, member=member)
LOCK = threading.Lock()


def bridge(app, lifespan=False, lock=None):
    client = TestClient(app, raise_server_exceptions=True)
    lock = lock or LOCK                     # a bridge whose handler calls another bridge needs a lock of its own
    if lifespan:
        client.__enter__()

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _go(self):
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n) if n else None
            with lock:
                r = client.request(self.command, self.path, content=body,
                                   headers={k: v for k, v in self.headers.items() if k.lower() not in ("host", "content-length")})
            data = r.content
            self.send_response(r.status_code)
            for k, v in r.headers.items():
                if k.lower() not in ("content-length", "transfer-encoding", "connection", "date", "server"):
                    self.send_header(k, v)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = _go

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}", client


api_srv, API_LOCAL, _ = bridge(api_app)
chat_srv, CHAT_LOCAL, chat_client = bridge(agent.app, lifespan=True)


def as_me(body):
    r = chat_client.post("/v1/desk", json={**body, "session_id": "deskpage106"}, headers={"Authorization": "Bearer me"})
    assert r.status_code == 200, r.text
    return r.json()


# step 4, the Desk page, as you: the four questions the page walk asks, and one chip. The question with no desk in it
# comes first, in a fresh conversation: after a handbook answer, a follow-up L1 marks as one keeps the handbook (sticky).
# lk-17 is not one of the prompt's examples (desk_routes.PROMPT_EXEMPLARS), so the classifier has not seen it.
PAGE_QS = ["What is the notice period?", RR["lk-06"]["question"], RR["lk-17"]["question"], RR["lk-10"]["question"]]
assert not {"lk-06", "lk-17", "lk-10"} & {rid for rid, _, _ in desk_routes.PROMPT_EXEMPLARS}
assert "lk-17" not in route_eval.prompt_groups(ROUTE_ROWS) and RR["lk-17"]["expected_route"] == "statute"
assert not desk_router.anchors(PAGE_QS[2], ()) and not desk_router.anchors(PAGE_QS[0], ())
PAGE = {}
PAGE["clarify"] = as_me({"question": PAGE_QS[0]})
PAGE["chip"] = as_me({"chip": "handbook"})
PAGE["hb"] = as_me({"question": PAGE_QS[1]})
PAGE["law"] = as_me({"question": PAGE_QS[2]})
PAGE["oos"] = as_me({"question": PAGE_QS[3]})
assert (PAGE["hb"]["route"], PAGE["hb"]["outcome"], PAGE["hb"]["email"]) == ("handbook", "answer", ME)
assert PAGE["clarify"]["route"] == "clarify" and [c["desk"] for c in PAGE["clarify"]["chips"]] == ["handbook", "statute"]
CLARIFY_TEXT = PAGE["clarify"]["answer"]
assert CLARIFY_TEXT == "Should I answer this from the company handbook or from the law?", CLARIFY_TEXT
assert (PAGE["chip"]["route"], PAGE["chip"]["method"]) == ("handbook", "user")
assert PAGE["law"]["route"] == "statute" and PAGE["law"]["sections"][0]["in_force"][-1] == desk_law.NOT_ADVICE
assert len(PAGE["law"]["sections"][0]["in_force"]) >= 2 and all(w in PAGE["law"]["answer"] for w in RR["lk-17"]["must_contain"])
assert (PAGE["oos"]["route"], PAGE["oos"]["method"], PAGE["oos"]["retrieve_calls"]) == ("out_of_scope", "anchor", 0)
OOS_TEXT = PAGE["oos"]["answer"]
assert OOS_TEXT == desk_graph.OOS[None], OOS_TEXT
CHIP_LABELS = fd_const("ROUTED_CHIPS")
assert CHIP_LABELS == {d: desk_routes.DESKS[d]["chip"] for d in ("handbook", "statute", "case")}
assert [c["label"] for c in PAGE["clarify"]["chips"]] == [CHIP_LABELS["handbook"], CHIP_LABELS["statute"]]
FD_SRC = (KIT / FD).read_text(encoding="utf-8")
UI_LABELS = ['st.subheader("Ask the Desk")', '"DocuMind sends your question to the desk that answers it: your company\'s handbook, the law, or a "',
             'st.text_area("Your question"', 'placeholder="For example: How many days of notice do I give when I resign?"',
             'st.form_submit_button("Ask")', 'st.caption("DocuMind\'s answer from your company\'s documents and the law it holds. If you need a person, "',
             '"raise a case.")', 'ROUTED_MODES = ("on", "single")']
assert all(x in FD_SRC for x in UI_LABELS), [x for x in UI_LABELS if x not in FD_SRC]
assert fd_const("ASK_PROBLEM") == {409: "That choice is no longer on offer. Please ask your question again."}

# ------------------------------------------------------------------ the cells, run against the bridges
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": LANE_ID, "ME": ME,
       "HOME": str(T), "USERPROFILE": str(T), "API": API_LOCAL, "CHAT": CHAT_LOCAL, "TOKEN": "evalacme", "T_ACME": "evalacme", "T_LEAVER": "evalleaver",
       "T_GLOBEX": "evalglobex", "T_ZETA": "evalzeta", "SINCE106": "YYYY-MM-DDTHH:MM:SSZ"}
ISO = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?\+00:00")


def run_cell(body: str, env: dict | None = None, argv: list | None = None) -> str:
    r = subprocess.run([sys.executable] + (argv or ["-"]), input=body if not argv else None, cwd=str(KIT), capture_output=True,
                       text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-2500:]
    return r.stdout


def norm(text: str) -> str:
    return (ISO.sub("YYYY-MM-DDTHH:MM:SS+00:00", text).replace(CHAT_LOCAL, "https://documind-chat-NUMBER.asia-south1.run.app")
            .replace(API_LOCAL, "https://documind-api-NUMBER.asia-south1.run.app"))


POST_FN = """def post(path, body, token):
    req = urllib.request.Request(os.environ["CHAT"] + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ[token]})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
rows = {r["id"]: r for r in (json.loads(x) for x in open("evals/routes.jsonl", encoding="utf-8") if x.strip())}"""

OFFLINE_PY = """import logging, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["services/chat", "."]
import desk_router
logging.getLogger("documind.chat.desk_router").setLevel(logging.ERROR)   # its warning is the reason printed below
from shared import desk_rules
from smoke.smoke_cases import POSH
PREFIXES = ["EXP", "FIN", "GEN", "IT", "LV", "NP", "PB", "PR", "SEC", "WFH"]   # acme's clause-prefix map
for q in (POSH, "What is the total payable on invoice INV-2026-0412?", "What does NP-03 say about notice?",
          "What is the minimum bonus under the Payment of Bonus Act?", "Under the Payment of Bonus Act, what bonus do I get?",
          "What is the notice period for a confirmed E3?"):
    d = desk_router.decide(q, {"tenant": "acme", "roles": ["employee"], "clause_prefixes": PREFIXES}, models=None)
    print(f"  gate {str(d['gate']):5} anchors {str(d['anchors']):14} near {str(desk_rules.near(q)):5} -> "
          f"{d['route']:12} {d['method']:8} {d['fallback_reason'] or ''}")
print("  K", desk_router.K, "ACCEPT_VOTES", desk_router.ACCEPT_VOTES, "CASE_VOTES", desk_router.CASE_VOTES,
      "TAU_OOS", desk_router.TAU_OOS, "prompt", desk_router.PROMPT_VERSION)"""

ROUTE_PY = """import json, os, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from smoke.smoke_cases import POSH
""" + POST_FN + """
for label, q in (("POSH", POSH), ("lk-10", rows["lk-10"]["question"]), ("NP-03", "What does NP-03 say about notice?"),
                 ("lk-18", rows["lk-18"]["question"]), ("lk-06", rows["lk-06"]["question"])):
    status, b = post("/v1/route", {"question": q}, "TOKEN")
    d = b["decision"]
    print(f"  {label:6} {status} route {b['route']:13} method {b['method']:7} anchors {str(d['anchors']):18}"
          f" model_calls {b['model_calls']}  Rs {b['cost_inr']}")
    if d["l1"]:
        print(f"         L1 {d['l1']['route']}; the vote {d['knn_route']}, {round(d['knn_share'] * 7)} of 7, nearest cosine"
              f" {d['knn_sim']}; accepted by rule {d['accepted_by']}")
status, b = post("/v1/route", {"question": rows["lk-06"]["question"]}, "T_UI")
print(f"  as ui-sa {status} {b['detail']}")"""

DESK_PY = """import json, os, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
""" + POST_FN + """
for n, rid in enumerate(("lk-06", "lk-17")):
    status, b = post("/v1/desk", {"question": rows[rid]["question"], "session_id": f"lesson106-{n}"}, "T_ACME")
    print(f"  {rid} {status} route {b['route']} method {b['method']} outcome {b['outcome']}  model_calls {b['model_calls']}"
          f"  retrieve_calls {b['retrieve_calls']}  Rs {b['limits']['cost_inr']}")
    for s in b["sections"]:
        objs = sorted({c["source_uri"].split("/", 3)[3] for c in s["citations"]})
        print(f"    {s['title']}: {len(s['citations'])} citations from {', '.join(objs)}")
        print(f"    the answer says {rows[rid]['must_contain']}: {all(w in s['answer'] for w in rows[rid]['must_contain'])}")
        for line in s["in_force"]:
            print(f"    | {line}")
    print(f"    chips {[c['desk'] for c in b['chips']]}")"""

MORE_PY = """import json, os, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
""" + POST_FN + """
status, b = post("/v1/desk", {"question": rows["lk-06"]["question"], "session_id": "lesson106-leaver"}, "T_LEAVER")
print(f"  leaver  {status} route {b['route']} outcome {b['outcome']}  retrieve_calls {b['retrieve_calls']}"
      f"  model_calls {b['model_calls']}  chips {[c['desk'] for c in b['chips']]}")
print(f"          {b['answer']}")
status, b = post("/v1/desk", {"question": rows["lk-28"]["question"], "session_id": "lesson106-globex"}, "T_GLOBEX")
print(f"  globex  {status} tenant {b['tenant']} mode {b['mode']} route {b['route']} method {b['method']}"
      f"  model_calls {b['model_calls']}  outcome {b['outcome']}")
print(f"          cites {sorted({c['source_uri'].split('/', 3)[3] for c in b['citations']})}")
status, b = post("/v1/desk", {"question": "What is the notice period?", "session_id": "lesson106-clarify"}, "T_ACME")
print(f"  clarify {status} route {b['route']} method {b['method']}: {b['answer']}")
print(f"          chips {[c['label'] for c in b['chips']]}")"""

CALC_PY = """import json, os, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
""" + POST_FN + """
row = rows["jn-03"]
status, b = post("/v1/desk", {"question": row["question"], "session_id": "lesson106-figure"}, "T_ACME")
s = b["sections"][0]
print(f"  jn-03 {status} route {b['route']} method {b['method']} mode {s['mode']}  tool_calls {b['tool_calls']}")
print(f"        retrieve_calls {b['retrieve_calls']}  model_calls {b['model_calls']}  Rs {b['limits']['cost_inr']}")
print(f"        the answer says {row['must_contain']}: {all(w in s['answer'] for w in row['must_contain'])}")
print()
print(s["answer"])"""

CHATS_PY = """import json, os, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
""" + POST_FN + """
for rid in ("iso-01", "lk-21", "lk-13"):
    status, b = post("/v1/chat", {"question": rows[rid]["question"], "session_id": "lesson106-shadow", "brain": "direct"}, "T_ZETA")
    says = rows[rid]["must_contain"]
    print(f"  {rid:6} {status} brain {b['brain']}  citations {len(b['citations'])}  model_calls {b['limits']['model_calls']}"
          + (f"  the answer says {says}: {all(w in b['answer'] for w in says)}" if says else ""))"""

OUT_PY = {}
OUT_PY["offline"] = run_cell(OFFLINE_PY)
OUT_PY["route"] = run_cell(ROUTE_PY, env={"T_UI": "ui"})
OUT_PY["desk"] = run_cell(DESK_PY)
OUT_PY["more"] = run_cell(MORE_PY)
OUT_PY["calc"] = run_cell(CALC_PY)
assert "mode agent  tool_calls ['retrieve', 'encashable_days']" in OUT_PY["calc"] and ": True" in OUT_PY["calc"], OUT_PY["calc"]
assert "\n\nWorked out in code:\n- Earned leave encashed on exit (LV-07): min(50, 45) = 45 days. The balance from your message; the cap from LV-07 [" in OUT_PY["calc"], OUT_PY["calc"]
assert "Condition: LV-07 bars encashment during probation" in OUT_PY["calc"]

# make smoke-desk: smoke/smoke_desk.py, then smoke_cases.py, against the bridges (tokens are the stand-in's names)
SMOKE_ENV = {"DOCUMIND_CHAT_URL": CHAT_LOCAL, "DOCUMIND_API_URL": API_LOCAL, "DOCUMIND_PROJECT": LANE_ID,
             "DOCUMIND_OUTSIDER_SA": sa("outsider"), "DOCUMIND_IC_EMAIL": ME, "DOCUMIND_TENANT": "acme"}
n_rows = len(ROWS_LOGGED)
with patch.dict(os.environ, SMOKE_ENV), patch.dict(sys.modules):
    sys.path.insert(0, str(KIT / "smoke"))
    sc = load("smoke_cases", "smoke/smoke_cases.py")
    sd = load("smoke_desk_106", "smoke/smoke_desk.py")
    fake_token = lambda acct, audience: TOKEN_FOR.get(acct)  # noqa: E731
    with patch.object(sc, "token_as", fake_token), patch.object(sd, "token_as", fake_token), redirect_stdout(io.StringIO()) as so:
        rc = sd.main()
    sys.path.remove(str(KIT / "smoke"))
SMOKE = so.getvalue()
assert rc == 0 and SMOKE.count("0 failed") == 2, SMOKE
N_SMOKE_DESK = SMOKE.split("passed,")[0].rsplit("\n", 1)[-1].strip()
OUT_PY["smoke"] = norm(SMOKE)

# the shadow on zeta: its queues with its eval account as the committee, the account's roles, then the shadow (zeta
# has the gate's rules already: nothing has switched them off)
QZ = T / "queues.zeta.json"
QZ.write_text((KIT / "evals/desk/queues.zeta.json").read_text(encoding="utf-8").replace("you@example.com", sa("evalzeta")), encoding="utf-8")
o1, c1 = ops("queues", "--tenant", "zeta", "--file", str(QZ))
o2, c2 = ops("roles", "--tenant", "zeta", "--email", sa("evalzeta"), "--set", "employee,desk_eval,ic_member:head_office")
o3, c3 = ops("desk", "--tenant", "zeta", "--route", "shadow")
assert (c1, c2, c3) == (0, 0, 0), (o1, o2, o3)
RAW["shadow"] = o1.replace(str(QZ), "/home/you/queues.zeta.json") + o2 + o3 + ">> " + ALERTS_ECHO + "\n"
chat_desk.SHADOWING._at = None
n_shadow = len(ROWS_LOGGED)
OUT_PY["chats"] = run_cell(CHATS_PY)
SHADOW_ROWS = [j for _, j in ROWS_LOGGED[n_shadow:] if j.get("event") == "desk_shadow"]
CHAT_ROWS = [j for _, j in ROWS_LOGGED[n_shadow:] if j.get("event") == "chat"]
assert [r["route"] for r in SHADOW_ROWS] == ["handbook", "statute", "out_of_scope"], SHADOW_ROWS
assert [r["method"] for r in SHADOW_ROWS] == ["model", "anchor", "model"], [r["method"] for r in SHADOW_ROWS]
assert len(CHAT_ROWS) == 3 and all(r["brain"] == "direct" for r in CHAT_ROWS)

# step 7: the rows themselves, read from Firestore
ROWS_PY = """import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
db = firestore.Client(project=os.environ["PROJECT"])
hits = [s for s in db.collection("chunks").where("tenant_id", "==", "acme").where("locator", "==", "NP-03").stream()
        if s.to_dict().get("current")]
c = hits[0].to_dict()
print(f"  chunks/{hits[0].id}")
print(f"    doc_type {c['doc_type']}  kind {c['kind']}  current {c['current']}  {c['source_uri'].split('/', 3)[3]}")
e = db.document("tenants/acme/doc_types/acme~hr_policy_2026.md").get().to_dict()
print(f"  tenants/acme/doc_types/acme~hr_policy_2026.md: {e['doc_type']}, pin {e['pin'][:17]}..., set by {e['set_by']}, source {e['source']}")
print(f"    the pin is the chunk's doc_key: {e['pin'] == c['doc_key']}")
x = db.document("tenants/acme/desk_exemplars/lk-06").get().to_dict()
print(f"  tenants/acme/desk_exemplars/lk-06: route {x['route']}, group {x['group']}, {len(list(x['vector']))} dimensions,"
      f" {x['embedding_model']}, index {x['index_version']}")
for t in ("acme", "zeta", "globex"):
    s = db.document(f"tenant_settings/{t}").get().to_dict()
    print(f"  tenant_settings/{t}: desk_gate {s.get('desk_gate', 'rules')}, desk_route {s.get('desk_route', 'off')},"
          f" desk_single {s.get('desk_single')}, data_region {s.get('data_region')}")"""


class DocRef(Ref):
    pass


def _document(path):
    return Ref(db, path)


fake_fs = types.SimpleNamespace(Client=lambda project=None: types.SimpleNamespace(collection=db.collection, document=_document),
                                Query=types.SimpleNamespace(DESCENDING="DESCENDING"))


def run_here(code: str, mods: dict) -> str:
    """A cell that reads Google Cloud, run in this process with stand-ins for the clients it imports."""
    with tc.cloud_modules(**mods), patch.dict(os.environ, {"HOME": str(T), "USERPROFILE": str(T), "PROJECT": LANE_ID, "ME": ME, "SINCE106": "-"}), \
            redirect_stdout(io.StringIO()) as out:
        exec(compile(code, "<cell>", "exec"), {"__name__": "__cell__"})
    return out.getvalue()


OUT_PY["rows"] = run_here(ROWS_PY, {"firestore": fake_fs})
assert f"chunks/{NP03}" in OUT_PY["rows"] and "doc_type policy" in OUT_PY["rows"] and "the pin is the chunk's doc_key: True" in OUT_PY["rows"]
assert "768 dimensions, text-embedding-005" in OUT_PY["rows"]

LOGS_PY = """import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
f = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" AND '
     f'(jsonPayload.event="desk" OR jsonPayload.event="desk_shadow") AND timestamp>="{os.environ["SINCE106"]}"')
out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "60",
                      "--format", "json"], capture_output=True, text=True, check=True).stdout
for e in json.loads(out or "[]"):
    j = e["jsonPayload"]
    who = (j["user"] or "None").split("@")[0]
    print(f"  {j['event']:11} {j['surface']:5} {j['tenant']:6} {who:25} {j['route']:12} {j['method']:7}"
          f" {str(j['accepted_by']):4} calls {j['model_calls']}  {j.get('outcome') or ''}")"""
LOG_ROWS = [{"jsonPayload": j, "resource": {"labels": {"service_name": svc}}} for svc, j in ROWS_LOGGED
            if svc == "documind-chat" and j.get("event") in ("desk", "desk_shadow")]
fake_sub = types.ModuleType("subprocess")
fake_sub.run = lambda cmd, **kw: types.SimpleNamespace(stdout=json.dumps(LOG_ROWS), stderr="", returncode=0)
with patch.dict(sys.modules, {"subprocess": fake_sub}):
    OUT_PY["logs"] = run_here(LOGS_PY, {})
assert "desk_shadow chat  zeta" in OUT_PY["logs"] and "None" in OUT_PY["logs"]

o, c = ops("desk", "--tenant", "zeta", "--route", "on")
assert c == 0 and json.loads(o)["desk_route"] == "on", o
RAW["zetaon"] = o + ">> " + ALERTS_ECHO + "\n"
# step 9: make route-eval SPLIT=dev and SPLIT=test - evals/route_eval.py --live, against the bridge
CHAT_NAMED = "https://documind-chat-NUMBER.asia-south1.run.app"


RATE_WAITS = []


def eval_poster(base, path, token, body, timeout=150, sleep=None):
    """The kit's own post(), sent to the bridge; its wait on a 429 (Retry-After, 60 s) is a minute passing for the
    service's rate window, as on your lane."""
    assert base == CHAT_NAMED
    return route_eval.post(CHAT_LOCAL, path, token, body, timeout,
                           sleep=lambda s: (RATE_WAITS.append(s), chat_desk._RATE.clear()))


def live_eval(split):
    a = types.SimpleNamespace(arm=None, chat_url=CHAT_NAMED, project=LANE_ID, routes=route_eval.ROUTES_FILE, split=split,
                              registry=None, save=None, report=None)
    with redirect_stdout(io.StringIO()) as out:
        rc = route_eval.run_live(a, minter=lambda account, audience: TOKEN_FOR.get(account), poster=eval_poster)
    return rc, out.getvalue()


t_eval = time.monotonic()
RC_DEV, EVAL_DEV = live_eval("dev")
RC_TEST, EVAL_TEST = live_eval("test")
print(f"route-eval dev took {time.monotonic() - t_eval:.0f} s", file=sys.stderr)
RAW["eval_dev"], RAW["eval_test"] = EVAL_DEV, EVAL_TEST
assert RC_TEST == 1 and "FAIL  route accuracy 0/0 (no rows)" in EVAL_TEST, EVAL_TEST
assert RC_DEV == 0 and "not scored" not in EVAL_DEV and RATE_WAITS == [60], (RATE_WAITS, EVAL_DEV[-3000:])

# the page's last cell: make smoke-chat, the kit's smoke_chat.py against the same app. The direct brain is the kit's
# over the stand-in retrieval; the three agent brains are stand-ins that call retrieve() and are charged two model
# calls each (on your lane, Gemini answers).
class CannedBrain:
    def __init__(self, name):
        self.name = name

    def answer(self, question, *, config, context):
        r = documind_tools.retrieve(question, tenant_id=context["tenant_id"], top_k=5, brain=self.name)
        meter = limits.meter_of(context)
        meter.charge_rag(r.get("usage"))
        for t_in, t_out in ((1180, 28), (2410, 61)):
            assert meter.allow_model_call()
            meter.charge_model(t_in, t_out)
        return {"answer": "(the brain's answer, citing [1])", "tool_calls": ["retrieve"], "refusals": [],
                "citations": [{**c, "n": k} for k, c in enumerate(r["citations"], 1)]}


chat_client.app.state.brains.update({b: CannedBrain(b) for b in ("langchain", "langgraph", "adk")})
SMOKE_CHAT_ENV = {"DOCUMIND_CHAT_URL": CHAT_LOCAL, "DOCUMIND_IMPERSONATE_SA": sa("ui"), "DOCUMIND_OUTSIDER_SA": sa("outsider")}
with patch.dict(os.environ, SMOKE_CHAT_ENV):
    smc = load("smoke_chat_106", "smoke/smoke_chat.py")
    with patch.object(smc, "token_as", lambda acct: TOKEN_FOR.get(acct)), redirect_stdout(io.StringIO()) as so:
        rc = smc.main()
SMOKE_CHAT = so.getvalue()
assert rc == 0 and "6 passed, 0 failed" in SMOKE_CHAT, SMOKE_CHAT
assert "[PASS] health  profile=gcp default=langchain limits=12 calls, Rs 5.0, 100.0 s" in SMOKE_CHAT, SMOKE_CHAT
RAW["smokechat"] = norm(SMOKE_CHAT)

# ------------------------------------------------------------------ the Google Chat door, on the same stand-ins
# The bridge (services/gchat/main.py) is the kit's, unchanged. What stands in: Google's token check (the stand-in's
# token names, as for every service here), the bridge's own ID token for the chat service, Pub/Sub's publish and push,
# the Chat API's spaces.messages.create, and the bridge's claims database (claims._transactional, the one seam the
# kit's own tests use). The events are the kit's placeholder fixtures (commands/tests/test_gchat.py), which stand in
# for what Google sends until the lane probe records a real one. It runs after every other cell, so the outputs above
# are a lane where nobody has messaged the app.
sys.path.insert(0, str(KIT / "services/gchat"))
GCHAT_SELF = "https://documind-gchat-NUMBER.asia-south1.run.app"
ADDON = "service-NUMBER@gcp-sa-gsuiteaddons.iam.gserviceaccount.com"
with patch.dict(os.environ, {"SELF_URL": GCHAT_SELF, "CHAT_URL": CHAT_LOCAL, "GCHAT_CALLER": ADDON,
                             "GOOGLE_CLOUD_PROJECT": LANE_ID}):
    gmain = load("gchat_main_106", "services/gchat/main.py")
import cards as gcards  # noqa: E402  - services/gchat/, the modules gmain imported
import claims as gclaims  # noqa: E402
import events as gevents  # noqa: E402
import post as gpost  # noqa: E402
import replies as greplies  # noqa: E402
import delegation  # noqa: E402  - services/chat/delegation.py, which desk.py's _principal() calls
from google.oauth2 import id_token as g_id_token  # noqa: E402
assert gmain.cards is gcards and gmain.claims is gclaims and gmain.post is gpost and gmain.events is gevents
tg = load("kit_test_gchat_106", "commands/tests/test_gchat.py")
WS = tg.EMPLOYEE                                         # your Google Workspace address, as the kit's fixtures name it
assert WS == "employee@example.com" and tg.CALLER == ADDON
BEARER.update({"gchat": sa("gchat"), "gchatpush": sa("gchatpush"), "addon": ADDON})
TOKEN_FOR.update({v: k for k, v in BEARER.items()})

# the kit's facts the page states, read here
assert (gclaims.DATABASE, gclaims.COLLECTION, gclaims.TTL) == ("documind-gchat", "gchat_events", timedelta(hours=24))
assert gpost.TOPIC == "documind-gchat-work" and gmain.SUBSCRIPTION == "documind-gchat-push"
assert (gmain.PUSH_ACCOUNT, gmain.BRIDGE_ACCOUNT) == ("documind-gchatpush-sa", "documind-gchat-sa")
assert delegation.DELEGATES == {"documind-gchat-sa": "gchat"} and delegation.SWITCH == "desk_gchat"
assert delegation.HEADER == "x-documind-principal" and gmain.PRINCIPAL_HEADER.lower() == delegation.HEADER
DELEG_RULES = re.findall(r"# (\d)\b", EXCERPTS["deleg"][1].split("def principal(")[1])
assert DELEG_RULES == [str(i) for i in range(1, 8)], DELEG_RULES            # seven rules, each marked in the code
DELEGABLE = [f"{m} {p}" for m, p in delegation.DELEGABLE]
assert "POST /v1/desk" in DELEGABLE and not [d for d in DELEGABLE if "/v1/route" in d or "/v1/chat" in d]
assert gmain.GCHAT_ASYNC is True and gpost.DUPLICATE_STATUS == 409 and "UNCONFIRMED" in gpost.__doc__
assert "UNCONFIRMED" in gcards.action.__doc__ or "UNCONFIRMED" in gcards.__doc__
assert "UNCONFIRMED" in gevents.direct_message.__doc__ and "UNCONFIRMED" in gpost.auth_order.__doc__
GS_SRC = (KIT / GS).read_text(encoding="utf-8")
assert "--min-instances=0" in GS_SRC and "--iap" not in GS_SRC
ADDON_ECHO = re.search(r'\|\| echo "(>> the Chat app\'s add-on agent does not exist yet[^"]*)"', GS_SRC).group(1)
GCHAT_TF_SRC = (KIT / "terraform/gchat.tf").read_text(encoding="utf-8")
assert "# Nothing here bills while idle except what the claims database stores, and its claims expire within a day." in GCHAT_TF_SRC
assert 'deletion_policy         = "DELETE"' in GCHAT_TF_SRC and 'collection = "gchat_events"' in GCHAT_TF_SRC
assert 'name  = "documind-gchat-push"' in GCHAT_TF_SRC and 'account_id   = "documind-gchatpush-sa"' in GCHAT_TF_SRC
MAKEFILE_SRC = (KIT / "Makefile").read_text(encoding="utf-8")
assert "documind-gchat" in MAKEFILE_SRC.split("DOWN_SERVICES     =")[1].split("\n")[0]
assert 'resource "google_monitoring_alert_policy" "desk_delegation_refused"' in ALERTS_TF
ALERT_NAME = re.search(r'resource "google_monitoring_alert_policy" "desk_delegation_refused" \{\n  display_name = "([^"]+)"', ALERTS_TF).group(1)
assert not re.search(r"^\s*count\s*=", ALERTS_TF.split('resource "google_monitoring_alert_policy" "desk_delegation_refused"')[1].split("\n}\n")[0], re.M)   # on every lane
# both refuse unless the last apply had GCHAT_DOOR=true (terraform output gchat_door)
assert "deploy-gchat: guard-project tf-backend\n\t@$(GCHAT_DOOR_ON)\n\t$(MAKE) build deploy-services SERVICES=gchat SCRIPTS=commands/gchat.sh" in mk_src
assert "\nsmoke-gchat: guard-project tf-backend\n\t@$(GCHAT_DOOR_ON)\n" in mk_src and "$(PY) smoke/smoke_gchat.py" in mk_src
assert "GCHAT_DOOR ?= false\nTF_EXTRA_VARS += -var gchat_door=$(GCHAT_DOOR)\n" in mk_src and "terraform output -raw gchat_door" in mk_src
assert "smoke-gchat" not in MAKEFILE_SRC.split("smoke-all:")[1].split("\n\n")[0]
assert "commands/tests/test_gchat.py" in (KIT / "commands/desk-check.sh").read_text(encoding="utf-8")
assert "documind-gchat-sa; do" in (KIT / "commands/lesson-12.8.sh").read_text(encoding="utf-8")   # step 3's chat deploy binds it
assert "make plan up GCHAT_DOOR=true" in (KIT / "smoke/smoke_gchat.py").read_text(encoding="utf-8")


class GTx:
    """claims.py's transaction, as the kit's own tests run it: one attempt, no contention."""

    def set(self, ref, data):
        ref.set(data)


class GchatDB(FakeDB):
    def transaction(self):
        return GTx()


GDB = GchatDB()                                          # the documind-gchat database, on its own


class GResp:
    def __init__(self, status, body):
        self.status_code, self._b = status, body

    def json(self):
        return self._b


PUBLISHED, POSTED = [], []


class GoogleStandIn:
    """The session post.py gets from Application Default Credentials: Pub/Sub's publish and the Chat API's
    spaces.messages.create, recorded. On your lane these are Google's, as the bridge's own account."""

    def post(self, url, **kw):
        if url.endswith(f"/topics/{gpost.TOPIC}:publish"):
            PUBLISHED.append(kw["json"]["messages"][0]["data"])
            return GResp(200, {"messageIds": [str(len(PUBLISHED))]})
        assert re.match(r"^https://chat\.googleapis\.com/v1/spaces/\w+/messages$", url), url
        POSTED.append({"url": url, "params": kw.get("params"), "body": kw["json"]})
        return GResp(200, {})


def g_now():
    return tick()


n_g = len(ROWS_LOGGED)
GSTACK = contextlib.ExitStack()
for p in (patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": LANE_ID}), patch.object(delegation, "PROFILE", "gcp"),
          patch.object(iap, "bearer_email", lambda headers, audience: bearer_email(headers).lower()),   # as iap.py returns it
          patch.object(g_id_token, "fetch_id_token", lambda request, audience: "gchat"),
          patch.object(gpost, "_adc", lambda scopes: GoogleStandIn()),
          patch.object(gclaims, "_client", GDB), patch.object(gclaims, "_transactional", lambda fn: (lambda tx: fn(tx))),
          patch.object(gclaims, "_now", g_now), patch.object(gevents, "today_ist", lambda now=None: "20261001")):
    GSTACK.enter_context(p)

# step 4, with a Workspace account: your address on acme's roster, then the door on for acme
ROSTER_WS, POL_WS = roster("acme", [WS])
assert ROSTER_WS[0] == ("acme", WS) and POL_WS == POLICIES, (ROSTER_WS, POL_WS)
o_g, c_g = ops("desk", "--tenant", "acme", "--gchat", "on")
assert c_g == 0 and json.loads(o_g)["desk_gchat"] == "on", o_g
RAW["gchaton"] = o_g
gclient = TestClient(gmain.app)
CHAT_EVENT = {"authorization": "Bearer addon"}


def chat_event(text, name):
    """One person's message to the app, as the kit's add-on fixture shapes it, sent to POST /."""
    r = gclient.post("/", json=tg.addon_message(text=text, name=name), headers=CHAT_EVENT)
    assert r.status_code == 200, (r.status_code, r.text)
    return r.json()["hostAppDataAction"]["chatDataAction"]["createMessageAction"]["message"]


Q06_TEXT = RR["lk-06"]["question"]
GCHATQS_PY = """import json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from smoke.smoke_cases import POSH
rows = {r["id"]: r for r in (json.loads(x) for x in open("evals/routes.jsonl", encoding="utf-8") if x.strip())}
print(f"lk-06: {rows['lk-06']['question']}")
print(f"POSH:  {POSH}")"""
GCHATQS_OUT = run_cell(GCHATQS_PY)
assert GCHATQS_OUT == f"lk-06: {Q06_TEXT}\nPOSH:  {POSH}\n", GCHATQS_OUT
CONV = {"q06_ack": chat_event(Q06_TEXT, "spaces/DMSPACE/messages/MESSAGEA")}
assert CONV["q06_ack"] == {"text": greplies.ACK} and len(PUBLISHED) == 1 and not POSTED
pushed = json.loads(base64.b64decode(PUBLISHED[0]))
assert set(pushed) == {"key", "kind", "email", "space", "thread", "session_id", "question"} and pushed["email"] == WS
assert pushed["question"] == Q06_TEXT and pushed["session_id"] == "gc-" + hashlib.sha256(b"spaces/DMSPACE").hexdigest()[:24] + "-20261001"
r = gclient.post("/work", headers={"authorization": "Bearer gchatpush"},
                 json={"message": {"data": PUBLISHED[0], "messageId": "1"}, "subscription": f"projects/{LANE_ID}/subscriptions/{gmain.SUBSCRIPTION}"})
assert r.status_code == 204 and len(POSTED) == 1, (r.status_code, r.text)
CONV["q06_card"] = {k: v for k, v in POSTED[0]["body"].items() if k != "thread"}
assert POSTED[0]["params"]["messageId"] == gevents.client_id(pushed["key"]) and len(POSTED[0]["params"]["messageId"]) == 63
CONV["posh"] = chat_event(POSH, "spaces/DMSPACE/messages/MESSAGEB")
assert len(PUBLISHED) == 1 and len(POSTED) == 1                       # a gate hit is answered at once, never queued
G_ROWS = [(svc, j) for svc, j in ROWS_LOGGED[n_g:]]
G_DESK = [j for svc, j in G_ROWS if j.get("event") == "desk" and j.get("via") == "gchat"]
assert [(d["route"], d["user"], d["delegate"], d["case_type"]) for d in G_DESK] == [
    ("handbook", WS, "gchat", None), ("case", None, None, "sensitive")], G_DESK
G_ROW = [j for svc, j in G_ROWS if j.get("event") == "gchat"]
assert [(j["kind"], j["outcome"], j["queued"], j["user"], j["class"]) for j in G_ROW] == [
    ("message", "queued", True, None, None), ("message", "gate", False, None, "sensitive")], G_ROW   # before the class: nobody
assert [j["outcome"] for svc, j in G_ROWS if j.get("event") == "gchat_answer"] == ["answer"]
assert not [j for svc, j in G_ROWS if j.get("event") in ("desk_delegation_refused", "desk_delegation_denied", "gchat_verify_failed")]
CLAIMS = {p: d for p, d in GDB.docs.items() if p.startswith(gclaims.COLLECTION + "/")}
assert len(CLAIMS) == 1 and next(iter(CLAIMS.values()))["state"] == "answered", CLAIMS   # the disclosure was never claimed
for d in CLAIMS.values():
    assert set(d) == {"kind", "state", "attempts", "created_at", "leased_at", "expire_at"}
    assert not any("@" in str(v) or Q06_TEXT in str(v) or POSH in str(v) for v in d.values())
    assert d["expire_at"] - d["created_at"] == gclaims.TTL
assert not any(Q06_TEXT in json.dumps(j) or POSH in json.dumps(j) for _, j in G_ROWS)    # no row holds the words


def card_text(message: dict, indent: str = "         ") -> list[str]:
    """What one message holds, in order, as text: Google Chat draws a card in its own layout."""
    import textwrap

    def para(s, pre=""):
        s = html.unescape(str(s))
        out = []
        for chunk in s.split("\n"):
            out += textwrap.wrap(chunk, 84, initial_indent=indent + pre, subsequent_indent=indent + pre) or [indent + pre]
        return out
    if "text" in message and "cardsV2" not in message:
        return para(message["text"])
    card = message["cardsV2"][0]["card"]
    h = card["header"]
    lines = [indent + "[card] " + h["title"] + (" - " + h["subtitle"] if h.get("subtitle") else "")]
    for s in card["sections"]:
        if s.get("header"):
            lines.append(indent + "-- " + html.unescape(s["header"]))
        for w in s["widgets"]:
            if "textParagraph" in w:
                lines += para(w["textParagraph"]["text"])
            elif "decoratedText" in w:
                lines += para(w["decoratedText"]["topLabel"] + ":")
                lines += para(w["decoratedText"]["text"], "  ")
            elif "buttonList" in w:
                lines.append(indent + "  ".join(f"[{b['text']}]" for b in w["buttonList"]["buttons"]))
    return lines


WHO_W = len(gcards.TITLE) + 2                         # "HR Desk: " and "you:" padded to one width
assert WHO_W == 9


def said(who: str, words: str) -> str:
    """One line of the conversation, its speaker first."""
    import textwrap
    return "\n".join(textwrap.wrap(words, 84, initial_indent=(who + ":").ljust(WHO_W), subsequent_indent=" " * WHO_W))


CONV_TEXT = [f"In a direct message with {gcards.TITLE}, as {WS}:", "",
             said("you", Q06_TEXT), said(gcards.TITLE, CONV["q06_ack"]["text"]),
             said(gcards.TITLE, "(then, posted by the bridge's worker)"), *card_text(CONV["q06_card"]), "",
             said("you", POSH), said(gcards.TITLE, "(at once, with no acknowledgement)"), *card_text(CONV["posh"])]
assert CONV["q06_ack"]["text"] == greplies.ACK
OUT["gchatconv"] = "\n".join(CONV_TEXT) + "\n"
card06 = CONV["q06_card"]["cardsV2"][0]["card"]
assert card06["header"] == {"title": gcards.TITLE, "subtitle": gcards.SUBTITLES["handbook"]}
assert [s.get("header") for s in card06["sections"]] == [None, "Sources"], card06["sections"]
assert all("hr_policy_2026.md" in w["decoratedText"]["topLabel"] for w in card06["sections"][1]["widgets"])
cardp = CONV["posh"]["cardsV2"][0]["card"]
POSH_UNITS = [s["header"] for s in cardp["sections"] if s.get("header")]
CONV_FLAT = " ".join(OUT["gchatconv"].split())                     # the card's lines, unwrapped
assert POSH_UNITS == ["Hyderabad", "Pune"] and gcards.POSH_BUTTON in OUT["gchatconv"] and gcards.POSH_PRIVACY in CONV_FLAT
assert CONV_FLAT.count(gcards.POSH_MEMBERS + " [" + gcards.POSH_BUTTON + "]") == len(POSH_UNITS)   # above each button
assert Q06_TEXT in OUT["gchatconv"] and POSH in OUT["gchatconv"]
assert "gs://" not in OUT["gchatconv"]

# step 7: make smoke-gchat, smoke/smoke_gchat.py against the bridge and the chat service on their stand-ins; its rows
# are read from what the smoke itself logged, as on a lane where nobody has messaged the app in the last hour
gsrv, GCHAT_LOCAL, _ = bridge(gmain.app, lock=threading.Lock())
n_s = len(ROWS_LOGGED)


def fake_gcloud(cmd, **kw):
    if cmd[:3] == ["gcloud", "config", "get-value"]:
        return types.SimpleNamespace(stdout=ME + "\n", stderr="", returncode=0)
    assert cmd[:3] == ["gcloud", "logging", "read"], cmd
    want = dict(re.findall(r'jsonPayload\.(\w+)="([^"]*)"', cmd[3]))
    got = [j for _, j in ROWS_LOGGED[n_s:] if all(j.get(k) == v for k, v in want.items())][::-1][:3]   # newest first
    return types.SimpleNamespace(stdout=json.dumps([{"jsonPayload": j} for j in got]), stderr="", returncode=0)


SMOKE_G_ENV = {"DOCUMIND_GCHAT_URL": GCHAT_LOCAL, "DOCUMIND_CHAT_URL": CHAT_LOCAL, "DOCUMIND_PROJECT": LANE_ID,
               "DOCUMIND_OUTSIDER_SA": sa("outsider"), "DOCUMIND_TENANT": ""}
with patch.dict(os.environ, SMOKE_G_ENV):
    smg = load("smoke_gchat_106", "smoke/smoke_gchat.py")
    with patch.object(smg, "token_as", lambda acct, audience: TOKEN_FOR.get(acct)), \
            patch.object(smg, "subprocess", types.SimpleNamespace(run=fake_gcloud)), redirect_stdout(io.StringIO()) as so:
        rc = smg.main()
SMOKE_G = so.getvalue()
assert rc == 0 and "4 passed, 0 failed" in SMOKE_G and SMOKE_G.count("[PASS]") == 4, SMOKE_G
assert f"-> 403 '{delegation.NOT_A_DELEGATE}'" in SMOKE_G and f"-> 401 '{smg.CODE_401}'" in SMOKE_G
S_ROWS = [j for _, j in ROWS_LOGGED[n_s:]]
assert [(j["event"], j.get("reason")) for j in S_ROWS] == [("gchat_verify_failed", "wrong_caller")] * 2 + [
    ("desk_delegation_refused", delegation.NOT_A_DELEGATE)] * 2, S_ROWS
gsrv.shutdown()


def smoke_g_text(raw: str) -> str:
    out = raw.replace(GCHAT_LOCAL, GCHAT_SELF)
    out = out.replace(CHAT_LOCAL, "https://documind-chat-NUMBER.asia-south1.run.app")
    # a refused token's booleans come from your token's own claims: the stand-in's tokens carry none, so they are cut
    out = re.sub(r'(\{"event": "gchat_verify_failed", "path": "[^"]*", "reason": "[^"]*"), [^\n]*\}', r"\1, ...}", out)
    return out.strip("\n") + "\n"


OUT["smokegchat"] = smoke_g_text(SMOKE_G)
assert OUT["smokegchat"].count('"reason": "wrong_caller", ...}') == 2 and "(none)" in OUT["smokegchat"]

# step 8: the door's rows and claims, read as the cell reads them: the desk rows through the door, then the claims
GCHATROWS_PY = """import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
f = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" AND '
     f'jsonPayload.event="desk" AND jsonPayload.via="gchat" AND timestamp>="{os.environ["SINCE106"]}"')
out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "20",
                      "--format", "json"], capture_output=True, text=True, check=True).stdout
rows = [e["jsonPayload"] for e in json.loads(out or "[]")]
print(f"  desk rows through the Google Chat door: {len(rows)}")
for j in rows:
    print(f"    via {j['via']}  delegate {j['delegate']}  user {j['user']}  route {j['route']}  case_type {j['case_type']}"
          f"  outcome {j['outcome']}")
db = firestore.Client(project=os.environ["PROJECT"], database="documind-gchat")
claims = list(db.collection("gchat_events").stream())
print(f"  claims in documind-gchat's gchat_events: {len(claims)}")
for s in claims:
    d = s.to_dict()
    print(f"    {s.id[:16]}...  fields {sorted(d)}")
    print(f"      kind {d['kind']}  state {d['state']}  attempts {d['attempts']}  an email in it: {any('@' in str(v) for v in d.values())}"
          f"  expire_at - created_at: {d['expire_at'] - d['created_at']}")"""
G_LOG_ROWS = [{"jsonPayload": j} for j in G_DESK]
fake_gsub = types.ModuleType("subprocess")
fake_gsub.run = lambda cmd, **kw: types.SimpleNamespace(stdout=json.dumps(G_LOG_ROWS), stderr="", returncode=0)
fake_gfs = types.SimpleNamespace(Client=lambda project=None, database=None: (
    types.SimpleNamespace(collection=GDB.collection) if database == gclaims.DATABASE else None))
with patch.dict(sys.modules, {"subprocess": fake_gsub}):
    OUT["gchatrows"] = run_here(GCHATROWS_PY, {"firestore": fake_gfs})
assert "desk rows through the Google Chat door: 2" in OUT["gchatrows"] and "an email in it: False" in OUT["gchatrows"]
assert "expire_at - created_at: 1 day, 0:00:00" in OUT["gchatrows"] and "state answered  attempts 1" in OUT["gchatrows"]
assert "via gchat  delegate None  user None  route case  case_type sensitive" in OUT["gchatrows"], OUT["gchatrows"]
GSTACK.close()

PAGE_PY = """import json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
rows = {r["id"]: r for r in (json.loads(x) for x in open("evals/routes.jsonl", encoding="utf-8") if x.strip())}
for rid in ("lk-06", "lk-17", "lk-10"):
    print(f"{rid}: {rows[rid]['question']}")"""
# the Desk page walk's chips, as the page draws them
assert [c["desk"] for c in PAGE["hb"]["chips"]] == [] and [c["desk"] for c in PAGE["oos"]["chips"]] == ["case"], (PAGE["hb"]["chips"], PAGE["oos"]["chips"])
assert PAGE["oos"]["citations"] == [] and PAGE["law"]["sections"][0]["title"] == desk_graph.TITLES["statute"]
assert [s["title"] for s in PAGE["hb"]["sections"]] == [desk_graph.TITLES["handbook"]]

# route_eval --local: the router in process on a scripted classifier, each row's own group held out of the vote
OUT_LOCAL = run_cell("", argv=["evals/route_eval.py", "--local"])
assert OUT_LOCAL.startswith("local: the classifier is scripted, so this measures the cascade, not a model") and "the dev gates hold" in OUT_LOCAL
RE_SRC = (KIT / "evals/route_eval.py").read_text(encoding="utf-8")
assert '"index": held_out(r, index_by_tenant.get(r["tenant"], [])),' in RE_SRC        # --local holds each row's group out
assert route_eval.DEV_GATES == {"route": 0.95, "per_desk": 0.90, "escalation": 1.0}
SCORED_DEV = [r for r in ROUTE_ROWS if r["split"] == "dev" and r["group"] not in route_eval.prompt_groups(ROUTE_ROWS)]
INDEXED = route_eval.index_rows(ROUTE_ROWS)
assert len(SCORED_DEV) == 187 and len(INDEXED) == 198 and N_ROUTE_ROWS == 207
# the deployed index holds the dev rows themselves: every scored row of a routed tenant is its own exemplar
assert {r["id"] for r in SCORED_DEV if r["tenant"] not in route_eval.SINGLE} <= {r["id"] for r in INDEXED}
N_SINGLE = sum(1 for r in SCORED_DEV if r["tenant"] in route_eval.SINGLE)
N_DESK_ROWS = sum(1 for r in SCORED_DEV if r["expected_route"] in route_eval.DESK_ROWS or r["expected_outcome"] == "denied")
assert f"over {N_DESK_ROWS} turns" in EVAL_DEV and f"over {len(SCORED_DEV)} turns" in EVAL_DEV
assert 'if status == 429 and attempt < 3:' in RE_SRC and 'headers={"Retry-After": "60"}' in (KIT / CD).read_text(encoding="utf-8")

# ------------------------------------------------------------------ the shapes of what Terraform, the builds and gcloud print
mkfile = (KIT / "Makefile").read_text(encoding="utf-8")
assert 'echo ">> $$f (DEPLOY block)"' in mkfile and 'echo ">> building $(IMAGE_REPO)/$$svc:$(GIT_SHA) from services/$$dir"' in mkfile
infra_src = (KIT / "commands/infrastructure.py").read_text(encoding="utf-8")
PASS_LINES = [re.search(r'print\(f?"(PASS: no deletes[^"]*)', infra_src).group(1).replace("{path}", ".../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan"),
              re.search(r'print\(f?"(Review the displayed changes[^"]*)', infra_src).group(1),
              re.search(r'print\(f?"(PASS: selected plan[^"]*)', infra_src).group(1).replace("{path}", ".../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan")]
REPO = f"asia-south1-docker.pkg.dev/{PROJ}/documind"
OUT["deploy"] = (f"...\n>> building {REPO}/api:COMMIT from services/rag-api\n...\n>> building {REPO}/ui:COMMIT from services/frontend\n...\n"
                 + "".join(f">> commands/lesson-12.{n}.sh (DEPLOY block)\n...\n" for n in (2, 4, 8))
                 + "Plan: N to add, N to change, 0 to destroy.\n" + "\n".join(PASS_LINES) + "\n...\n"
                 "Apply complete! Resources: N added, N changed, 0 destroyed.\n")
# DESK_JOB=true points the hourly job at chat:$(GIT_SHA), the image commands/lesson-12.8.sh builds for this commit
assert "CHAT_IMAGE ?= $(IMAGE_REPO)/chat:$(GIT_SHA)" in mk_src and "documind/chat:$GIT_SHA" in (KIT / "commands/lesson-12.8.sh").read_text(encoding="utf-8")
GCHAT_TF = (KIT / "terraform/gchat.tf").read_text(encoding="utf-8")
assert 'name                    = "documind-gchat"' in GCHAT_TF and '"documind-gchatpush-sa"' in GCHAT_TF
assert 'name  = "documind-gchat-work"' in GCHAT_TF and 'name  = "documind-gchat-push"' in GCHAT_TF and '"chat.googleapis.com"' in GCHAT_TF
# GCHAT_DOOR=true declares the door: every gchat.tf resource and desk.tf's documind-gchat-sa count on it, nothing else
DOOR_COUNT = re.compile(r'^resource "[^"]+" "[^"]+" \{\n  count += var\.gchat_door \? 1 : 0\n', re.M)
DESK_TF = (KIT / "terraform/desk.tf").read_text(encoding="utf-8")
assert len(DOOR_COUNT.findall(GCHAT_TF)) == GCHAT_TF.count('\nresource "')
assert DOOR_COUNT.findall(DESK_TF) == ['resource "google_service_account" "gchat" {\n  count        = var.gchat_door ? 1 : 0\n']
assert not [f.name for f in (KIT / "terraform").glob("*.tf") if f.name not in ("gchat.tf", "desk.tf")
            and re.search(r"google_\w+\.gchat|var\.gchat_door", f.read_text(encoding="utf-8"))]   # so turning it on changes nothing
N_DOOR = len(DOOR_COUNT.findall(GCHAT_TF + DESK_TF))
assert (KIT / "commands/lesson-12.8.sh").exists()
# the door's plan on a lane step 3 applied adds only what counts on gchat_door; then chat again (commands/lesson-12.8.sh
# binds documind-gchat-sa, which exists now), then make deploy-gchat: make build, then make deploy-services with
# commands/gchat.sh; its last line is the add-on agent's binding, which echoes ADDON_ECHO while that agent does not
# exist (the kit's assumption: until an app is configured)
GCHAT_DEPLOYED = f">> building {REPO}/gchat:COMMIT from services/gchat\n...\n>> commands/gchat.sh (DEPLOY block)\n...\n"
OUT["deploygchat"] = (f"Plan: {N_DOOR} to add, 0 to change, 0 to destroy.\n" + "\n".join(PASS_LINES) + "\n...\n"
                      f"Apply complete! Resources: {N_DOOR} added, 0 changed, 0 destroyed.\n"
                      ">> commands/lesson-12.8.sh (DEPLOY block)\n...\n" + GCHAT_DEPLOYED + ADDON_ECHO + "\n")

# ------------------------------------------------------------------ what each output shows of your lane
NUM = "\x00N\x00"                         # a lane-dependent number, shown as N


def masked(obj, keys):
    """obj with every number under one of keys, at any depth below it, shown as N."""
    def num(v):
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return NUM
        if isinstance(v, dict):
            return {k: num(x) for k, x in v.items()}
        return v
    if isinstance(obj, dict):
        return {k: (num(v) if k in keys else masked(v, keys)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [masked(v, keys) for v in obj]
    return obj


def dumps(v) -> str:
    return json.dumps(v, ensure_ascii=False).replace(json.dumps(NUM), "N")


def pretty(obj) -> str:
    """One JSON line, shown with a break after each top-level key, as it would wrap anyway."""
    return "{" + ",\n ".join(json.dumps(k) + ": " + dumps(v) for k, v in obj.items()) + "}"


def json_lines(text: str, keys=(), short=False) -> str:
    out = []
    for line in text.splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            out.append(line)
            continue
        obj = masked(obj, set(keys))
        if str(obj.get("seed") or obj.get("relabel") or "").endswith(".png"):
            obj = {k: ("yours" if k in ("pin", "doc_key") else v) for k, v in obj.items()}   # make media draws them on your lane
        one = dumps(obj)
        out.append(one if short or len(one) <= 110 else pretty(obj))     # a long line is broken after each key
    return "\n".join(out) + "\n"


VIEW_ROW = re.compile(r"^(\S+ +\S+ +\S+ +)(\S+)( +)(\d+)(  )(.*)$")


def view_line(line: str) -> str:
    """A row of make doc-types' view: the chunk count is your worker's, and a figure's pin is yours."""
    m = VIEW_ROW.match(line)
    if not m:
        return line
    head, pin, gap, count, two, state = m.groups()
    if head.split()[0].endswith(".png"):
        gap, pin = gap + " " * (len(pin) - len("yours")), "yours"
    field = gap + count
    return head + pin + " " * (len(field) - 1) + "N" + two + re.sub(r"relabel \d+ rows", "relabel N rows", state)


def pick(text: str, keep) -> str:
    """The lines keep() wants, a "..." for each run of the others."""
    out, gap = [], False
    for line in text.rstrip("\n").splitlines():
        if keep(line):
            out.append(line)
            gap = False
        elif not gap:
            out.append("...")
            gap = True
    return "\n".join(out) + "\n"


def names(*objs):
    pat = re.compile("|".join(rf"\b(?:acme|zeta|globex)/{re.escape(o)}[\" ]" for o in objs))
    return lambda line: bool(pat.search(line))


ROW_KEYS = ("rows", "of", "from", "history_rows", "firestore_rows", "vector_datapoints", "vector_skipped", "vector_restored",
            "vector_removed", "left_current", "answer_cache_expired", "search", "bigquery")
SHOW = ("annual_report_2026_fig3.png", "hr_policy_2026.md", "labour_codes_compliance_handbook.pdf", "msa_acme_2026.md",
        "payment_of_gratuity_act_1972.pdf", "townhall_2026_q1.mp4")
EVENT = lambda line: line.startswith('{"event"')      # noqa: E731
HEADER = lambda line: line.startswith("object ")       # noqa: E731


def view_text(raw: str, keep, keys=ROW_KEYS) -> str:
    shown = pick(raw, lambda line: keep(line) or EVENT(line) or HEADER(line))
    return "".join(json_lines(line, keys) if line.startswith("{") else view_line(line) + "\n"
                   for line in shown.splitlines(keepends=False))


LEFT = [n.split("/", 1)[1] for n in UNREGISTERED["acme"]]
VERSION_KEYS = ("versions", "to_change")          # how many versions your lane holds is yours: the earlier lessons' notes
OUT["labels"] = view_text(RAW["labels"], lambda line: names(*SHOW, *LEFT)(line) and not line.startswith('{"relabel"')
                          or names("hr_policy_2026.md")(line), keys=ROW_KEYS + VERSION_KEYS)
assert '"to_change": N' in OUT["labels"] and '"rows": N' in OUT["labels"] and '"pin": "yours"' in OUT["labels"]
assert re.search(r"^acme/smoke_note\.md +unknown +- +- +N  unregistered$", OUT["labels"], re.M), OUT["labels"]
assert re.search(r"^acme/hr_policy_2026\.md +unknown +policy +acme_497809ffbaa6 +N  relabel N rows$", OUT["labels"], re.M), OUT["labels"]


def event_short(raw: str, keep=("event", "tenant", "versions", "to_change", "rows", "unregistered", "pin_miss", "failed")) -> str:
    e = json.loads(next(line for line in raw.splitlines() if EVENT(line)))
    e = masked({k: e[k] for k in keep}, set(ROW_KEYS + VERSION_KEYS))
    return dumps(e)[:-1] + ", ...}\n"


OUT["apply"] = (view_text(RAW["apply_acme"], lambda line: names("hr_policy_2026.md", "annual_report_2026_fig3.png")(line),
                          keys=ROW_KEYS + VERSION_KEYS)
                + "...\n" + event_short(RAW["apply_zeta"]) + "...\n" + event_short(RAW["apply_globex"]))
OUT["again"] = view_text(RAW["again"], names("hr_policy_2026.md", "annual_report_2026_fig3.png", "msa_acme_2026.md", *LEFT),
                         keys=[k for k in ROW_KEYS if k != "rows"] + ["versions"])   # nothing left to change: 0 on every lane
assert '"to_change": 0' in OUT["again"] and '"rows": 0' in OUT["again"] and "pinned" in OUT["again"]
assert re.search(r"^acme/pune_visitor_rules\.md +unknown +- +- +N  unregistered$", OUT["again"], re.M), OUT["again"]
for t in ("acme", "zeta", "globex"):
    e = json.loads(next(line for line in RAW[f"apply_{t}"].splitlines() if EVENT(line)))
    assert e["failed"] == [] and e["pin_miss"] == [] and e["unregistered"] == UNREGISTERED[t], e
    assert e["to_change"] == e["versions"] - len(UNREGISTERED[t]), e
OUT["index"] = json_lines(RAW["index"])
OUT["switch"] = json_lines(RAW["switch"])
OUT["gchatws"] = (GCHAT_DEPLOYED + f"{WS} is on acme\n...\n" + "".join(f"{t}: data_region={r}\n" for t, r in POL_WS)
                  + json_lines(RAW["gchaton"]) + GCHATQS_OUT)
assert 'desk_gchat": "on"' in OUT["gchatws"] and "acme: data_region=any" in OUT["gchatws"]
ROSTER_LINES = ("".join(f"{e.lower()} is on {t}\n" for t, e in ROSTER_G[:1]) + "...\n" + "".join(f"{t}: data_region={r}\n" for t, r in POLICIES)
                + "".join(f"{e.lower()} is on {t}\n" for t, e in ROSTER_L[:1]) + "...\n" + "".join(f"{t}: data_region={r}\n" for t, r in POLICIES))
OUT["ids"] = ROSTER_LINES + json_lines(RAW["ids_roles"])
OUT["page"] = (run_cell(PAGE_PY) + "https://documind-ui-NUMBER.asia-south1.run.app   <- open it signed in as you@example.com, then choose Desk\n")
OUT["offline"] = OUT_PY["offline"]
OUT["local"] = pick(OUT_LOCAL, lambda line: not re.match(r"^    \w+ -> \w+: ", line))

RS = re.compile(r"Rs (?!0(?:\.0+)?(?![\d.]))\d+(?:\.\d+)?")      # every amount but Rs 0
VOTE = re.compile(r"\d of 7, nearest cosine [\d.]+")
OUT["route"] = VOTE.sub("N of 7, nearest cosine N.NNNN", RS.sub("Rs N.NNNN", OUT_PY["route"]))
assert OUT["route"].count("model_calls 0  Rs 0.0") == 4 and "Rs N.NNNN" in OUT["route"]
OUT["desk"] = re.sub(r": \d+ citations from", ": N citations from", RS.sub("Rs N.NNNN", OUT_PY["desk"]))
assert OUT["desk"].count("the answer says") == 2 and "False" not in OUT["desk"] and desk_law.NOT_ADVICE in OUT["desk"]
OUT["more"] = OUT_PY["more"]
OUT["calc"] = re.sub(r"model_calls \d+", "model_calls N", RS.sub("Rs N.NNNN", OUT_PY["calc"]))
OUT["smoke"] = re.sub(r"\[PASS\] handbook  \d+ citations", "[PASS] handbook  N citations", RS.sub("Rs N.NNNN", OUT_PY["smoke"])).strip("\n") + "\n"
OUT["shadow"] = json_lines(RAW["shadow"])
OUT["chats"] = re.sub(r"citations \d+", "citations N", OUT_PY["chats"])
assert "False" not in OUT["chats"] and OUT["chats"].count("model_calls 0") == 3
OUT["rows"] = OUT_PY["rows"]
OUT["logs"] = OUT_PY["logs"]
OUT["zetaon"] = json_lines(RAW["zetaon"])


def eval_text(raw: str) -> str:
    """make route-eval's report: the denominators are the route set's; every rate, count and time is your lane's."""
    out = []
    for line in raw.rstrip("\n").splitlines():
        if re.match(r"^    \w+ -> \w+: ", line):
            if out[-1] != "    ...":
                out.append("    ...")
            continue
        line = re.sub(r"\b\d+/(\d+) = [\d.]+% \[[\d.]+%, [\d.]+%\]", r"N/\1 = NN.N% [NN.N%, NN.N%]", line)
        if re.match(r"^    (handbook|statute|out_of_scope) +\d", line):          # case and clarify have no rows yet: 0 on every lane
            line = re.sub(r"(?<= )(\d+)(?= |$)", lambda m: " " * (len(m.group(1)) - 1) + "N", line)
        line = re.sub(r"Rs [\d.]+ in all, Rs [\d.]+ a turn", "Rs N.NNNN in all, Rs N.NNNNN a turn", line)
        line = re.sub(r"p50 \d+  p95 \d+", "p50 N  p95 N", line)
        out.append(line)
    return "\n".join(out) + "\n"


OUT["evaldev"] = eval_text(EVAL_DEV)
# make names the recipe's first line when route_eval.py returns 1 (run_live's gate failed)
RE_LINE = mk_src.splitlines().index("route-eval: guard-project") + 2
assert "evals/route_eval.py --live" in mk_src.splitlines()[RE_LINE + 1] and "return 1" in RE_SRC
OUT["evaltest"] = EVAL_TEST + f"make: *** [mk/agents.mk:{RE_LINE}: route-eval] Error 1\n"
assert f"split dev: {len(SCORED_DEV)} rows scored, 20 left out" in OUT["evaldev"] and "N/187 = NN.N%" in OUT["evaldev"]
assert not re.search(r"\b\d+/\d+ = [\d.]+%", OUT["evaldev"].replace("0/0 (no rows)", ""))
OUT["smokechat"] = re.sub(r"'[^']*'$|\"[^\"]*\"$", "'...'", "\n".join(
    re.sub(r"Rs [\d.]+ ", "Rs N.NNNN ", re.sub(r"\d+ ms", "NNNN ms", re.sub(r"citations=\d+", "citations=N", line)))
    if "[PASS] brain" in line else line for line in RAW["smokechat"].splitlines()), flags=re.M).strip("\n") + "\n"
OUT["smokechat"] = re.sub(r"calls=[1-9]\d*", "calls=N", OUT["smokechat"])
assert "[PASS] brain direct  NNNN ms  tools=['retrieve']  citations=N  calls=0 Rs N.NNNN  '...'" in OUT["smokechat"], OUT["smokechat"]

# make desk-check: the offline half run here, on the kit; ~/graph-venv's tests as a shape
def merged(*argv) -> str:
    r = subprocess.run([sys.executable, *argv], cwd=str(KIT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                       encoding="utf-8", env={**ENV, "HOME": str(Path(tempfile.gettempdir())),
                                              "PYTHONWARNINGS": "ignore::DeprecationWarning"})   # the builder's Python's, not the lane's
    assert r.returncode == 0, r.stdout[-2000:]
    return r.stdout.replace(os.sep, "/") if os.sep != "/" else r.stdout   # a path as the learner's Linux shell prints it


DC_SRC = (KIT / "commands/desk-check.sh").read_text(encoding="utf-8")
DC_STEPS = re.findall(r'^"\$PY" (.+)$', DC_SRC, re.M)
assert DC_STEPS == ["evals/build_routes.py --check", "evals/route_eval.py --selftest", "evals/route_probe.py --selftest",
                    "-m unittest discover -s evals/tests -p test_route_eval.py", "evals/route_eval.py --local",
                    "evals/route_threshold.py --selftest", "shared/desk_calc.py --selftest"], DC_STEPS
assert '"$VENV/bin/pip" install -q -r services/chat/requirements.txt' in DC_SRC and 'VENV="${GRAPH_VENV:-$HOME/graph-venv}"' in DC_SRC
assert "desk-check:\n\t@PY=$(PY) bash commands/desk-check.sh" in mk_src


def unittest_shape(text: str) -> str:
    text = re.sub(r"^[.sxEF]+\n", "", text, flags=re.M)
    text = re.sub(r"Ran \d+ tests? in [\d.]+s", "Ran N tests in N.NNNs", text)
    return re.sub(r"OK \(skipped=\d+\)", "OK (skipped=N)", text)


DC = []
for step in DC_STEPS:
    if step == "evals/route_eval.py --local":
        lines = OUT_LOCAL.rstrip("\n").splitlines()
        DC.append(lines[0] + "\n...\n" + lines[-1] + "\n")
        continue
    out = merged(*step.split())
    if step == "shared/desk_calc.py --selftest":                 # one "ok" line a check: the first two and the last line
        lines_dc = out.rstrip("\n").splitlines()
        assert lines_dc[-1] == "every rule says what its corpus line says, and the figures hold", lines_dc[-1]
        out = "\n".join(lines_dc[:2] + ["..."] + lines_dc[-1:]) + "\n"
    DC.append(unittest_shape(out) if step.startswith("-m unittest") else out)
assert "Ran N tests in N.NNNs" in DC[3] and lines[-1].endswith("the dev gates hold"), (DC[3], lines[-1])
OUT["deskcheck"] = "".join(DC) + "Ran N tests in N.NNNs\n\nOK\n"

# make desk-views, then desk_daily read with bq: the view's groups, from the stand-in's desk rows as its SQL groups them
DAILY_SQL = (KIT / "terraform/sql/desk_daily.sql").read_text(encoding="utf-8")
DAILY_COLS = ("tenant", "desk", "callers", "turns", "answered", "clarified", "escalations", "to_l2", "cost_inr")
assert all(f" AS {c}" in DAILY_SQL for c in DAILY_COLS) and "GROUP BY day, tenant, desk, callers;" in DAILY_SQL
assert 'WHERE jsonPayload.event = "desk" AND jsonPayload.surface = "desk"' in DAILY_SQL and 'DATE(timestamp, "Asia/Kolkata") AS day' in DAILY_SQL
assert 'COALESCE(JSON_VALUE(TO_JSON_STRING(jsonPayload), "$.desk"), jsonPayload.route) AS desk' in DAILY_SQL
assert 'ENDS_WITH(IFNULL(jsonPayload.user, ""), ".iam.gserviceaccount.com") OR IFNULL(jsonPayload.arm, "B") != "B"' in DAILY_SQL
DV = mk_src.split("desk-views: guard-project\n", 1)[1].split("\n\n", 1)[0].splitlines()
assert len(DV) == 3 and DV[2].startswith('\t@echo ">> ') and not DV[0].startswith("\t@") and not DV[1].startswith("\t@")
GROUPS = Counter()
for j in (r["jsonPayload"] for r in LOG_ROWS):
    if j["event"] == "desk" and j["surface"] == "desk":
        caller = "service_accounts" if str(j["user"] or "").endswith(".iam.gserviceaccount.com") or (j["arm"] or "B") != "B" else "people"
        GROUPS[(j["tenant"], j["desk"] or j["route"], caller)] += 1
assert ("acme", "handbook", "people") in GROUPS and ("acme", "case", "people") in GROUPS and ("globex", "statute", "service_accounts") in GROUPS, GROUPS


def bq_pretty(cols, rows) -> str:
    """bq query --format=pretty's table: headers centred, strings to the left, numbers to the right."""
    w = [max([len(c)] + [len(str(r[i])) for r in rows]) for i, c in enumerate(cols)]
    rule = "+" + "+".join("-" * (x + 2) for x in w) + "+"
    head = "|" + "|".join(" " + c.center(x) + " " for c, x in zip(cols, w)) + "|"
    body = ["|" + "|".join(" " + (str(v).rjust(x) if i >= 3 else str(v).ljust(x)) + " " for i, (v, x) in enumerate(zip(r, w))) + "|"
            for r in rows]
    return "\n".join([rule, head, rule, *body, rule]) + "\n"


OUT["views"] = ("".join(line[1:].replace("$(PROJECT)", LANE_ID) + "\n...\n" for line in DV[:2]) + DV[2].split('@echo "', 1)[1][:-1] + "\n"
                + bq_pretty(DAILY_COLS, [(*k, *["N"] * 5, "N.NN") for k in sorted(GROUPS)]))

OUT = {k: v.replace(LANE_ID, PROJ) for k, v in OUT.items()}
assert not any(LANE_ID in v for v in OUT.values())
assert not any(re.search(r"127\.0\.0\.1|tmp|lesson106-[a-z0-9_]{8}", v) for v in OUT.values())
# nothing of the machine the page was built on: its paths, its Python's warnings, its site-packages
LEAK = re.compile(r"AppData|site-packages|[A-Za-z]:[\\/](?:Users|Program)|DeprecationWarning|UserWarning|\b[a-z_]+\\[a-z_]+\.(?:jsonl|py|json|md)\b")
assert not any(LEAK.search(v) for v in [*OUT.values(), *OUT_PY.values()]), [k for k, v in {**OUT, **OUT_PY}.items() if LEAK.search(v)]
assert not [j for _, j in ROWS_LOGGED if j.get("event") == "desk_check_tenants_unread"], "a tenants read failed while the build ran the chat door"
assert chat_desk.CHECKED._at is not None, "no chat turn of the build read the tenants list"
CONV_OUT = OUT.pop("gchatconv")                      # an expected conversation, with no cell of its own

# ------------------------------------------------------------------ the cells
SA_FN = 'sa() { echo "documind-$1-sa@$PROJECT.iam.gserviceaccount.com"; }'
ETOK_FN = ('etok() { gcloud auth print-identity-token --include-email --audiences="$CHAT" \\\n'
           '         --impersonate-service-account="$(sa "$1")"; }')


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


CELLS = {
    "deploy": ('git pull   # the kit you deploy is the kit this page quotes\n'
               'make build PROJECT="$PROJECT" REGION="$REGION" SERVICES="api ui"\n'
               'make deploy-services PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME" \\\n'
               '  SCRIPTS="commands/lesson-12.2.sh commands/lesson-12.4.sh commands/lesson-12.8.sh"\n'
               '# then Terraform, now that the chat image this commit names exists: the flags you gave make up\n'
               'make plan PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME" DESK_JOB=true\n'
               'python commands/infrastructure.py apply --project "$PROJECT" --region "$REGION" --terraform-dir terraform'),
    "ids": ('export CHAT="https://documind-chat-$NUMBER.$REGION.run.app" UI="https://documind-ui-$NUMBER.$REGION.run.app"\n'
            'export SINCE106="$(date -u +%FT%TZ)"\n'
            + SA_FN + "\n" + ETOK_FN + "\n"
            'make roster PROJECT="$PROJECT" TENANT=globex MEMBERS="$(sa evalglobex)"\n'
            'make roster PROJECT="$PROJECT" TENANT=acme MEMBERS="$(sa evalleaver)"\n'
            'make roles PROJECT="$PROJECT" TENANT=acme EMAIL="$(sa evalacme)" ROLES=employee,desk_eval\n'
            'make roles PROJECT="$PROJECT" TENANT=acme EMAIL="$(sa evalleaver)" ROLES=leaver,desk_eval\n'
            'make roles PROJECT="$PROJECT" TENANT=globex EMAIL="$(sa evalglobex)" ROLES=employee,desk_eval,ic_member:head_office'),
    "labels": 'make doc-types PROJECT="$PROJECT" TENANT=acme SEED=manifest',
    "apply": ('make doc-types PROJECT="$PROJECT" TENANT=acme APPLY=1\n'
              'make doc-types PROJECT="$PROJECT" TENANT=zeta SEED=manifest APPLY=1\n'
              'make doc-types PROJECT="$PROJECT" TENANT=globex SEED=manifest APPLY=1'),
    "again": 'make doc-types PROJECT="$PROJECT" TENANT=acme',
    "index": 'make route-index PROJECT="$PROJECT" TENANT=acme\nmake route-index PROJECT="$PROJECT" TENANT=zeta',
    "switch": ('make desk PROJECT="$PROJECT" TENANT=acme DESK_ROUTE=on\n'
               'sed "s/you@example.com/$(sa evalglobex)/g" evals/desk/queues.globex.json > "$HOME/queues.globex.json"\n'
               'make desk-queues PROJECT="$PROJECT" TENANT=globex FILE="$HOME/queues.globex.json"\n'
               'make desk PROJECT="$PROJECT" TENANT=globex DESK_ROUTE=single DESK_SINGLE=statute'),
    "page": heredoc(PAGE_PY) + '\necho "$UI   <- open it signed in as $ME, then choose Desk"',
    "offline": heredoc(OFFLINE_PY),
    "local": "python evals/route_eval.py --local",
    "route": heredoc(ROUTE_PY, 'TOKEN="$(etok evalacme)" T_UI="$(etok ui)" '),
    "desk": heredoc(DESK_PY, 'T_ACME="$(etok evalacme)" '),
    "more": heredoc(MORE_PY, 'T_ACME="$(etok evalacme)" T_LEAVER="$(etok evalleaver)" T_GLOBEX="$(etok evalglobex)" '),
    "calc": heredoc(CALC_PY, 'T_ACME="$(etok evalacme)" '),
    "deskcheck": "make desk-check   # the first run makes ~/graph-venv and installs the chat image's pins into it",
    "views": ('make desk-views PROJECT="$PROJECT"\n'
              'bq --project_id="$PROJECT" query --use_legacy_sql=false --format=pretty \\\n'
              "  'SELECT tenant, desk, callers, turns, answered, clarified, escalations, to_l2, cost_inr\n"
              "   FROM `documind_observability.desk_daily`\n"
              """   WHERE day = CURRENT_DATE("Asia/Kolkata") ORDER BY tenant, desk, callers'"""),
    "smoke": 'make smoke-desk PROJECT="$PROJECT" REGION="$REGION" TENANT=acme IC_EMAIL="$ME"',
    "shadow": ('sed "s/you@example.com/$(sa evalzeta)/g" evals/desk/queues.zeta.json > "$HOME/queues.zeta.json"\n'
               'make desk-queues PROJECT="$PROJECT" TENANT=zeta FILE="$HOME/queues.zeta.json"\n'
               'make roles PROJECT="$PROJECT" TENANT=zeta EMAIL="$(sa evalzeta)" ROLES=employee,desk_eval,ic_member:head_office\n'
               'make desk PROJECT="$PROJECT" TENANT=zeta DESK_ROUTE=shadow   # the gate already runs as rules for zeta'),
    "chats": heredoc(CHATS_PY, 'T_ZETA="$(etok evalzeta)" '),
    "rows": heredoc(ROWS_PY),
    "logs": heredoc(LOGS_PY),
    "zetaon": 'make desk PROJECT="$PROJECT" TENANT=zeta DESK_ROUTE=on',
    "evaldev": 'make route-eval PROJECT="$PROJECT" REGION="$REGION" SPLIT=dev',
    "evaltest": 'make route-eval PROJECT="$PROJECT" REGION="$REGION" SPLIT=test',
    "smokechat": 'make smoke-chat PROJECT="$PROJECT" REGION="$REGION"   # Module 5\'s gate, as in lesson 5.7',
    "deploygchat": ('# the Terraform part of make plan up, with the door: keep GCHAT_DOOR=true on every later make plan and make up\n'
                    'make plan PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME" DESK_JOB=true GCHAT_DOOR=true\n'
                    'python commands/infrastructure.py apply --project "$PROJECT" --region "$REGION" --terraform-dir terraform\n'
                    '# chat again, as make up would: its deploy lets documind-gchat-sa, which exists now, call documind-chat\n'
                    'make deploy-services PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME" SCRIPTS=commands/lesson-12.8.sh\n'
                    'make deploy-gchat PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"'),
    "gchatws": ('WS="employee@example.com"   # yours: the Google Workspace address you will message the app from\n'
                'make deploy-gchat PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"   # again, now that the app exists\n'
                'make roster PROJECT="$PROJECT" TENANT=acme MEMBERS="$WS"\n'
                'make desk PROJECT="$PROJECT" TENANT=acme DESK_GCHAT=on\n' + heredoc(GCHATQS_PY)),
    "smokegchat": 'make smoke-gchat PROJECT="$PROJECT" REGION="$REGION"',
    "gchatrows": heredoc(GCHATROWS_PY),
}
assert set(CELLS) == set(OUT), set(CELLS) ^ set(OUT)
assert "DESK_ROUTE=single DESK_SINGLE=statute" in CELLS["switch"] and "smoke-desk: guard-project" in mk_src
assert "route-eval: guard-project" in mk_src and "--split $(or $(SPLIT),dev)" in mk_src
assert "TENANT=$(TENANT)" in mk_src.split("smoke-desk: guard-project")[1].split("\n\n")[0]
for c in CELLS.values():                              # every Python cell pastes into bash and keeps its warnings quiet
    if "python - <<'PY'" in c:
        assert 'warnings.filterwarnings("ignore", category=UserWarning)' in c and "\nPY" in c

CELL_LABELS = {
    "deploy": "run in the operator shell, in the kit (the kit you have now, on your lane; many minutes)",
    "ids": "run in the operator shell, in the kit (two URLs, the time, two helpers, two more eval accounts and the roles of three)",
    "labels": "run in the operator shell, in the kit (acme's registry from the manifest, the view, and the relabel's plan)",
    "apply": "run in the operator shell, in the kit (the relabel applied for acme, then zeta and globex seeded and applied)",
    "again": "run in the operator shell, in the kit (the view again: nothing left to change)",
    "index": "run in the operator shell, in the kit (the exemplar index for the two routed tenants: about 200 embeddings each)",
    "switch": "run in the operator shell, in the kit (acme on; globex's queues, then globex in single mode)",
    "page": "run in the operator shell, in the kit (the three route-set questions to paste, and the page's address)",
    "offline": "run in the operator shell, in the kit (decide() with no models: the rules alone; no lane, no cost)",
    "local": "run in the operator shell, in the kit (the router on every dev row with a scripted classifier; no lane, no cost)",
    "route": "run in the operator shell, in the kit (five decisions from POST /v1/route as evalacme, then the same call as ui-sa)",
    "desk": "run in the operator shell, in the kit (two answers from POST /v1/desk as evalacme)",
    "more": "run in the operator shell, in the kit (the leaver, globex in single mode, and a question with no desk in it)",
    "calc": "run in the operator shell, in the kit (jn-03, a figure, to POST /v1/desk as evalacme: the handbook desk in agent mode)",
    "deskcheck": "run in the operator shell, in the kit (the Desk's offline check: no lane, no cost; the first run installs ~/graph-venv)",
    "views": "run in the operator shell, in the kit (the desk_daily view applied, then today's rows read with bq)",
    "smoke": "run in the operator shell, in the kit (the routed Desk's live smoke, then the case queue's)",
    "shadow": "run in the operator shell, in the kit (zeta's queues with its eval account as the committee, then the router in shadow)",
    "chats": "run in the operator shell, in the kit (three ordinary chat turns on zeta, which the router decides beside)",
    "rows": "run in the operator shell, in the kit (a chunk, its registry entry, an exemplar and the three tenants' switches, from Firestore)",
    "logs": "run in the operator shell, in the kit (every desk and desk_shadow row since step 3; reads only)",
    "zetaon": "run in the operator shell, in the kit (zeta from shadow to on)",
    "evaldev": f"run in the operator shell, in the kit (every dev row through the deployed Desk, one call after another: {len(SCORED_DEV)} decisions and {N_DESK_ROWS} paid answers; the report prints what the router cost)",
    "evaltest": "run in the operator shell, in the kit (the test split: it has no rows yet)",
    "smokechat": "run in the operator shell, in the kit (Module 5's gate: four brains, one question, the outsider refused)",
    "deploygchat": "run in the operator shell, in the kit, only to turn the Google Chat door on (its Terraform with GCHAT_DOOR=true, chat again, then the bridge: its image, its service and who may call it; many minutes)",
    "gchatws": "run in the operator shell, in the kit, only with Google Workspace and once the app is configured (the bridge again, your address on acme's roster, the door on for acme, two questions to paste)",
    "smokegchat": "run in the operator shell, in the kit, only with the Google Chat door on (its refusals; no Google Workspace needed)",
    "gchatrows": "run in the operator shell, in the kit, only with the Google Chat door on (the desk rows that came through the Google Chat door since step 3, then the bridge's claims; reads only)",
}
OUT_LABELS = {
    "deploy": "shape (Cloud Build's, gcloud's and Terraform's own lines are cut down; the plan adds the resources this commit's Terraform declares that your lane lacks)",
    "ids": "shape (make roster also puts the services' own accounts on their rosters; the roles are commands/desk_ops.py on a stand-in Firestore)",
    "labels": "(commands/desk_ops.py and services/ingest/relabel.py on a stand-in Firestore holding the manifest's objects and the notes earlier lessons uploaded; the chunk and version counts, the figures' pins and which unregistered objects you have are yours)",
    "apply": "(the same stand-ins; the version counts, the Firestore, Vector Search, Vertex AI Search and BigQuery counts, and the unregistered names are yours)",
    "again": "(the same stand-ins; an unregistered row is an earlier lesson's object, where your lane has one)",
    "index": "(commands/desk_ops.py on the kit's own route set; the embeddings were offline here, the counts and the version are the route set's)",
    "switch": "(commands/desk_ops.py on the stand-in, with the kit's queues files)",
    "page": "(the first three lines are the route set's own questions)",
    "offline": "(this cell run on the kit)",
    "local": "(run on the kit; the confusion pairs are cut down)",
    "route": "(the cell against agent.py's app behind a local stand-in; the vote and the rupees on the model row are your lane's, and the route and rule are your models' choice)",
    "desk": "(the same stand-in; which Acts the statute answer cites, and so which in-force lines follow, is your retriever's ranking)",
    "more": "(the same stand-in; the leaver's route, and the clarify, are the models' choice on your lane)",
    "calc": "(the same stand-in, with a scripted model in the agent's place: its calls and its words are an example, and the calls and rupees are yours; the Worked out in code block is the kit's)",
    "deskcheck": "shape (the offline half run on the kit; the test counts and times, and ~/graph-venv's tests at the end, are yours)",
    "views": "shape (bq's own lines are cut down; the groups are the stand-in's desk rows grouped as the view groups them, so yours follow what you asked, and every count is yours)",
    "smoke": "(smoke/smoke_desk.py and smoke/smoke_cases.py run against the same stand-in; your ids and dates differ)",
    "shadow": "(commands/desk_ops.py on the stand-in)",
    "chats": "(the cell against the same stand-in, the direct brain answering)",
    "rows": "(the cell against the stand-in's records; the chunk id is the hash of the handbook's bytes, the same on every lane)",
    "logs": "(the stand-in's rows: what the chat service logged while this page was built, before step 4's Google Chat part, whose two turns are here too if you had it; the routes on model rows are your models')",
    "zetaon": "(commands/desk_ops.py on the stand-in)",
    "evaldev": "shape (evals/route_eval.py --live against the stand-in; the denominators are the route set's, every rate, count and time is yours)",
    "evaltest": "(evals/route_eval.py --live against the stand-in, then make's own line: the same on every lane until the test split has rows)",
    "smokechat": "shape (smoke/smoke_chat.py against agent.py's app on the stand-in; the times, rupees and answers are your lane's)",
    "deploygchat": ("shape (Terraform's, Cloud Build's and gcloud's own lines are cut down; the counts are a lane's that step 3 left "
                    "with the door off. The last line appears while the Chat app's add-on agent does not exist; the kit assumes "
                    "that lasts until you configure an app, which is unconfirmed)"),
    "gchatws": ("shape (the bridge's deploy cut down as above, without the last line once the app exists; make roster's and make "
                "desk's lines from commands/lane.py and commands/desk_ops.py on the stand-in; then the two questions)"),
    "smokegchat": ("(smoke/smoke_gchat.py against the bridge and agent.py's app on the stand-in, its log reads answered from what "
                   "the smoke itself logged, as on a lane where nobody messaged the app in the last hour. A refused token's "
                   "five booleans come from your token's own claims, so they are cut)"),
    "gchatrows": ("(the cell against the stand-in's rows and claims database after step 4's conversation; if you did not "
                  "configure the app, both counts are 0. A claim's id is a hash of the message's name, so yours differs)"),
}
assert set(CELL_LABELS) == set(CELLS) == set(OUT_LABELS)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
WIN["OUT_GCHATCONV"] = out_window(
    "conversation (a stand-in run of the kit's own code, not a recorded Google Chat session: the bridge and the Desk are "
    "the kit's, the two messages are the kit's placeholder events, and Google's side is stood in. Google Chat draws each "
    "card in its own layout, and the answer's words and quotes are your models' and your retriever's)", CONV_OUT)

STACK.close()
api_srv.shutdown()
chat_srv.shutdown()
chat_client.__exit__(None, None, None)
shutil.rmtree(T, ignore_errors=True)

# ------------------------------------------------------------------ what the kit does not do yet, asserted
from shared import desk_calc  # noqa: E402
assert desk_calc.gratuity_estimate(52000, 7, 8)["estimate"] is True              # a gratuity figure is always an estimate
assert "always an estimate" in (KIT / "shared/desk_calc.py").read_text(encoding="utf-8")
assert "MINIMAL once the probe shows gemini-3.6-flash takes it" in src_router
assert not [r for r in ROUTE_ROWS if r["language"] != "en"]
assert "recall case                 0/0 (no rows)" in EVAL_DEV and "escalation recall, pooled     0/0 (no rows)" in EVAL_DEV
assert desk_routes.enabled_routes is not None and "case and clarify have none until such" in desk_routes.__doc__

# ------------------------------------------------------------------ what the page's prose says about the kit, asserted
assert doc_types.CLASSES == ("policy", "statute", "guidance", "report", "transcript", "contract", "invoice")
REG = {t: doc_types.read_registry(db, t) for t in ("acme", "zeta", "globex")}
assert [n for n, e in REG["acme"].items() if e.get("doc_type") == "policy"] == ["acme/hr_policy_2026.md"], REG["acme"]
COV = {t: desk_routes.coverage({e.get("doc_type") for e in r.values()}) for t, r in REG.items()}
assert COV == {"acme": {"handbook": True, "statute": True}, "zeta": {"handbook": True, "statute": True},
               "globex": {"handbook": False, "statute": True}}, COV
assert "wrong on about one row in eight; an arbiter that picks the label\n    when it is a candidate, else clarify" in RE_SRC
assert '"""One "desk" row: every field named here, no question,' in (KIT / CD).read_text(encoding="utf-8")
assert "It never answers, drafts or checkpoints." in EXCERPTS["routes"][1]
assert "The router's two thresholds (TAU_OOS, ACCEPT_VOTES) swept on the dev split" in mk_src
assert "The router's three alert policies (terraform/desk_alerts.tf: the fallback share, the L2 share, clarify and\n# out_of_scope week on week)" in mk_src
assert "the enum schema's output tokens" in mk_src and "route-probe: guard-project" in mk_src
assert "holds at most twelve tenant-neutral examples" in desk_router.__doc__
assert {r["expected_route"] for r in INDEXED} == {"handbook", "statute", "out_of_scope"}   # no case example: rule D's vote half cannot fire
assert "make doc-types FOLLOW=<name> APPLY=1" in (KIT / DT).read_text(encoding="utf-8")
assert desk_graph.GRAPH_ROUTES == ("handbook", "statute", "clarify", "fallback")
src_rules = (KIT / "shared/desk_rules.py").read_text(encoding="utf-8")
assert "if _first_person(t) or _HUMAN_IMPERATIVE.search(t) or _exit_dues(t):" in src_rules            # near(): anywhere in the question
assert "every checked Aadhaar and card number replaced" in desk_rules.mask.__doc__                     # mask(): checked numbers only
assert 'if stage in ("gate", "mask"):' in src_router and 'stage = "gate"' in src_router               # a person on an early exception
for s in ('if ctx.get("draft_open"):', 'if ctx.get("chip") == "case":', "elif single:", 'elif ctx.get("chip") in ANSWER_DESKS:'):
    assert s in src_router, s                                                                          # stages 2 and 3, before the anchors
assert src_router.index("elif single:") < src_router.index("hints = anchors(masked")
assert "is not registered and evals/manifest.json gives it no class" in (KIT / "commands/desk_ops.py").read_text(encoding="utf-8")
assert 'GCHAT_VALUES = ("off", "on")' in (KIT / "commands/desk_ops.py").read_text(encoding="utf-8")
CD_SRC = (KIT / CD).read_text(encoding="utf-8")
assert "prev_question: Optional[str]" in CD_SRC.split("class RouteRequest(BaseModel):")[1].split("\n\n\n")[0]
assert "prev_question" not in CD_SRC.split("class DeskRequest(BaseModel):")[1].split("\n\n\n")[0]
assert re.findall(r"^    (POST|GET) (/v1/[\w/]+)", EXCERPTS["routes"][1], re.M) == [("POST", "/v1/desk"), ("POST", "/v1/route"), ("GET", "/v1/desk/check")]
assert desk_graph.STARTS_WITH_QUESTION == ("exit_dues", "people_query", "human_requested")
assert "nothing is checkpointed; only answer, clarify and fallback turns invoke it" in EXCERPTS["routes"][1].replace("\n" + " " * 22, " ")
CSS_LINE = desk_law.in_force_line("code_on_social_security_2020")
assert "comes into force on such date as the Central Government may, by notification, appoint" in CSS_LINE and desk_law.UNCHECKED in CSS_LINE
assert desk_law.IN_FORCE == {"labour_codes": None, "dpdp_rights": None}
N_AUTH = re.search(r"authority_rate +N/(\d+) = ", OUT["evaldev"]).group(1)
assert "--registry" not in mk_src.splitlines()[RE_LINE + 1] and "classes_from_registry(a.registry) if a.registry else classes_from_manifest()" in RE_SRC
assert "every answer row cites, and every citation is the row's own tenant's object with a class in the\n                     row's expected_doc_types" in RE_SRC
assert [c["label"] for c in PAGE["oos"]["chips"]] == [CHIP_LABELS["case"]]

# ------------------------------------------------------------------ the cost of a turn, from the kit's prompts and prices
Q06 = RR["lk-06"]["question"]
L1_IN = len(desk_router.prompt(Q06)) // 4
L2_IN = len(desk_router.arbiter_prompt(Q06, ["handbook", "statute", "clarify"])) // 4
L1_CAP = prices.inr(prices.usd(desk_router.L1_MODEL, L1_IN, desk_router.L1_MAX_OUTPUT_TOKENS))
L1_30 = prices.inr(prices.usd(desk_router.L1_MODEL, L1_IN, 30))
L2_CAP = prices.inr(prices.usd(desk_router.L2_MODEL, L2_IN, desk_router.L2_MAX_OUTPUT_TOKENS))
assert prices.USD_INR == 85 and prices.PRICES[desk_router.L1_MODEL] == (0.25, 1.50) and prices.PRICES[desk_router.L2_MODEL] == (1.50, 7.50)
assert 0.01 < L1_CAP < 0.1 and 0.1 < L2_CAP < 1.0

# ------------------------------------------------------------------ the widget
DATA = {"a": PANEL_A, "who": list(WHO), "th": TH, "pb": PB, "routes": list(desk_router.ROUTES),
        "models": {"l1": desk_router.L1_MODEL, "l2": desk_router.L2_MODEL, "embed": desk_router.EMBED_MODEL,
                   "thinking": desk_router.L2_THINKING}}
UI_JS = ACCEPT_JS + r"""var D = %s, $ = function(id){ return document.getElementById(id); };
function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }
function fill(sel, vals, label){ sel.innerHTML = ''; vals.forEach(function(v, i){ var o = document.createElement('option'); o.value = i; o.textContent = label ? label(v) : String(v); sel.appendChild(o); }); }
var TH = D.th;
if ($('rt')) {
  var qs = $('rt-q'), ws = $('rt-who');
  fill(qs, D.a, function(p){ return p.q.length > 64 ? p.q.slice(0, 62) + '...' : p.q; });
  fill(ws, D.who);
  var renderA = function(){
    var p = D.a[+qs.value], t = p.by[D.who[+ws.value]], v = $('rt-verdict');
    $('rt-words').textContent = p.q;
    $('rt-src').textContent = p.src;
    $('rt-masked').hidden = !t.masked;
    $('rt-masked').textContent = t.masked ? 'What the router reads from here on: ' + t.masked : '';
    $('rt-stages').innerHTML = t.stages.map(function(s){ return '<li class="' + s[0] + '">' + esc(s[1]) + '</li>'; }).join('');
    if (t.method === 'rule') { v.className = 'rt-verdict ' + (t.route === 'denied' ? 'no' : 'rule'); v.textContent = t.route === 'denied' ? 'denied by rule: no model call, Rs 0' : 'case by rule (' + t.case_type + '): no model call, Rs 0'; }
    else if (t.method === 'anchor') { v.className = 'rt-verdict ' + (t.route === 'denied' ? 'no' : 'rule'); v.textContent = t.route === 'denied' ? 'denied: the anchor names a desk these roles do not open, Rs 0' : t.route + ' by its anchor: no model call, Rs 0'; }
    else { v.className = 'rt-verdict model'; v.textContent = t.after === 'denied' ? 'to the two signals, then denied unless they choose case' : 'to the two signals: try panel B'; }
  };
  qs.addEventListener('change', renderA); ws.addEventListener('change', renderA);
  qs.value = 0; ws.value = 0; renderA();
}
if ($('ac')) {
  var S = {l1: $('ac-l1'), second: $('ac-second'), ctype: $('ac-ctype'), kroute: $('ac-kroute'), kvotes: $('ac-kvotes'), kcase: $('ac-kcase'), ksim: $('ac-ksim'), anch: $('ac-anch')};
  fill(S.l1, D.pb.l1, function(v){ return v === 'none' ? 'no answer (failed or timed out)' : v; });
  fill(S.second, D.pb.second); fill(S.ctype, D.pb.ctype);
  fill(S.kroute, D.pb.kroute, function(v){ return v === 'none' ? 'no vote (no index)' : v; });
  fill(S.kvotes, D.pb.kvotes, function(v){ return v + ' of ' + TH.K; });
  fill(S.ksim, D.pb.ksim, function(v){ return v.toFixed(2); });
  fill(S.anch, D.pb.anch, function(v){ return v.length ? v.join(' and ') : 'none'; });
  $('ac-th').innerHTML = ['K ' + TH.K, 'ACCEPT_VOTES ' + TH.ACCEPT_VOTES, 'CASE_VOTES ' + TH.CASE_VOTES, 'TAU_OOS ' + TH.TAU_OOS.toFixed(2), 'L1 ' + TH.L1_TIMEOUT_S + ' s', 'L2 ' + TH.L2_TIMEOUT_S + ' s', 'budget ' + TH.ROUTER_BUDGET_S + ' s'].map(function(x){ return '<span>' + esc(x) + '</span>'; }).join('');
  var caseOptions = function(){
    var kr = D.pb.kroute[+S.kroute.value], kv = D.pb.kvotes[+S.kvotes.value], keep = +S.kcase.value || 0;
    var top = (kr === 'none' || kr === 'case') ? 0 : Math.min(kv, TH.K - kv);
    fill(S.kcase, D.pb.kcase.slice(0, top + 1), function(v){ return v + ' of ' + TH.K; });
    S.kcase.value = Math.min(keep, top); S.kcase.disabled = top === 0;
  };
  var renderB = function(){
    var r = D.pb.l1[+S.l1.value], kr = D.pb.kroute[+S.kroute.value];
    S.second.disabled = S.ctype.disabled = r === 'none';
    S.kvotes.disabled = S.ksim.disabled = kr === 'none';
    var l1 = mkL1(r, D.pb.second[+S.second.value], D.pb.ctype[+S.ctype.value]);
    var knn = mkKnn(kr, D.pb.kvotes[+S.kvotes.value], D.pb.kcase[+S.kcase.value] || 0, D.pb.ksim[+S.ksim.value], TH.K);
    var an = D.pb.anch[+S.anch.value], v = accept(l1, knn, an, TH), out = $('ac-out'), h = '';
    var fired = v ? v[1] : (l1 ? 'F' : null);
    var rules = [['D', 'L1 says case (route, second route, or a posh case type), or ' + TH.CASE_VOTES + ' of ' + TH.K + ' neighbours are case: case. Checked first.'],
                 ['A', 'L1 equals the vote, and the vote is ' + TH.ACCEPT_VOTES + ' of ' + TH.K + ' or more.'],
                 ['B', 'L1 equals a desk an anchor pointed to.'],
                 ['C', 'L1 says out_of_scope and the nearest exemplar is under cosine ' + TH.TAU_OOS.toFixed(2) + '.'],
                 ['E', 'Logprob acceptance: not built.'],
                 ['F', 'Anything else: one L2 call, the arbiter.']];
    h += '<ul class="rt-rules">' + rules.map(function(x){ var cls = x[0] === fired ? 'fired' : 'skip'; return '<li class="' + cls + '"><strong>' + x[0] + '</strong> ' + esc(x[1]) + '</li>'; }).join('') + '</ul>';
    if (v) h += '<p class="rt-verdict model">rule ' + v[1] + ' accepts: ' + esc(v[0]) + ', method model, one model call</p>';
    else if (l1) { var c = candidates(l1, knn, D.routes); h += '<p class="rt-verdict model">rule F: ' + esc(D.models.l2) + ' (thinking ' + esc(D.models.thinking) + ', ' + TH.L2_TIMEOUT_S + ' s) chooses one of ' + esc(c.join(', ')) + '</p><p>Its schema allows those ' + c.length + ' and nothing else. If it fails or times out, L1’s ' + esc(l1.route) + ' stands, with confidence low and the desk chips.</p>'; }
    else h += '<p class="rt-verdict no">no L1 answer and no case signal: the fallback, a direct answer over the doc types the person may read, with the desk chips</p>';
    if (knn) h += '<p class="rt-src">The vote: ' + esc(knn.route) + ' ' + D.pb.kvotes[+S.kvotes.value] + ' of ' + TH.K + ' (share ' + knn.share.toFixed(3) + ')' + (knn.votes.case && knn.route !== 'case' ? ', case ' + knn.votes.case + ' of ' + TH.K : '') + ', nearest cosine ' + knn.sim.toFixed(2) + '.</p>';
    out.innerHTML = h;
  };
  Object.keys(S).forEach(function(k){ S[k].addEventListener('change', function(){ if (k === 'kroute' || k === 'kvotes') caseOptions(); renderB(); }); });
  S.l1.value = 0; S.kroute.value = 0; S.kvotes.value = TH.ACCEPT_VOTES - 1; S.ksim.value = 1; caseOptions(); renderB();
}""" % json.dumps(DATA, ensure_ascii=False)
assert desk_router.accept({"route": "handbook", "second_route": "none", "case_type": "none"},       # the panel's opening state
                          {"route": "handbook", "share": TH["ACCEPT_VOTES"] / TH["K"], "sim": PB["ksim"][1],
                           "votes": {"handbook": TH["ACCEPT_VOTES"]}}, []) == ("handbook", "A")
assert PB["l1"][0] == "handbook" and PB["kroute"][0] == "handbook" and PB["kvotes"][TH["ACCEPT_VOTES"] - 1] == TH["ACCEPT_VOTES"]

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

STATS = {
    "K": str(TH["K"]), "ACCEPT_VOTES": str(TH["ACCEPT_VOTES"]), "CASE_VOTES": str(TH["CASE_VOTES"]),
    "TAU_OOS": f"{TH['TAU_OOS']:.2f}", "L1_S": f"{TH['L1_TIMEOUT_S']:g}", "L2_S": f"{TH['L2_TIMEOUT_S']:g}",
    "BUDGET_S": f"{TH['ROUTER_BUDGET_S']:g}", "STICKY_MIN": str(TH["STICKY_S"] // 60), "PART_MIN_S": f"{desk_graph.PART_MIN_S:g}",
    "PROMPT_VERSION": desk_router.PROMPT_VERSION, "N_EXEMPLARS": WORDS[len(desk_routes.PROMPT_EXEMPLARS)],
    "N_ROUTE_ROWS": str(N_ROUTE_ROWS), "N_SCORED": str(len(SCORED_DEV)), "N_HELD": str(N_ROUTE_ROWS - len(SCORED_DEV)),
    "N_INDEX": str(len(INDEXED)), "N_SINGLE": WORDS[N_SINGLE], "N_DESK_ROWS": str(N_DESK_ROWS),
    "N_GRID": f"{N_GRID:,}", "N_QUESTIONS": WORDS[len(QUESTIONS)], "N_RULE": WORDS[N_RULE], "N_MODEL_Q": WORDS[len(QUESTIONS) - N_RULE],
    "ROUTE_RATE": str(chat_desk.ROUTE_RATE), "SHADOW_S": f"{chat_desk.SHADOW_TIMEOUT_S:g}", "SETTINGS_S": str(chat_desk.SETTINGS_TTL_S),
    "INDEX_MIN": str(desk_router.INDEX_TTL_S // 60), "QUESTION_CHARS": f"{desk_router.QUESTION_CHARS:,}", "PREV_CHARS": str(desk_router.PREV_CHARS),
    "L1_IN": str(L1_IN), "L2_IN": str(L2_IN), "L1_OUT": str(desk_router.L1_MAX_OUTPUT_TOKENS), "L2_OUT": f"{desk_router.L2_MAX_OUTPUT_TOKENS:,}",
    "L1_CAP": f"{L1_CAP:.4f}", "L1_30": f"{L1_30:.4f}", "L2_CAP": f"{L2_CAP:.3f}",
    "N_SMOKE_DESK": str(SMOKE.split("passed,")[0].rsplit("\n", 1)[-1].strip()), "N_SMOKE_CASES": str(SMOKE.split("passed,")[1].rsplit("\n", 1)[-1].strip()),
    "N_EVAL": WORDS[len(EVAL_SAS)], "DEV_GATE": f"{route_eval.DEV_GATES['route']:.0%}", "DESK_GATE": f"{route_eval.DEV_GATES['per_desk']:.0%}",
    "CLARIFY_TEXT": html.escape(CLARIFY_TEXT, quote=False), "OOS_TEXT": html.escape(OOS_TEXT, quote=False),
    "CHIP_HB": html.escape(CHIP_LABELS["handbook"], quote=False), "CHIP_LAW": html.escape(CHIP_LABELS["statute"], quote=False), "CHIP_CASE": html.escape(CHIP_LABELS["case"], quote=False),
    "ASK_409": html.escape(fd_const("ASK_PROBLEM")[409], quote=False), "NOT_ADVICE": html.escape(desk_law.NOT_ADVICE, quote=False),
    "Q06": html.escape(RR["lk-06"]["question"], quote=False), "Q17": html.escape(RR["lk-17"]["question"], quote=False), "Q10": html.escape(RR["lk-10"]["question"], quote=False),
    "TITLE_HB": html.escape(desk_graph.TITLES["handbook"], quote=False), "TITLE_LAW": html.escape(desk_graph.TITLES["statute"], quote=False),
    "INDEX_VERSION": json.loads(RAW["index"].splitlines()[0])["index_version"],
    "IDX_HB": str(json.loads(RAW["index"].splitlines()[0])["routes"]["handbook"]), "IDX_LAW": str(json.loads(RAW["index"].splitlines()[0])["routes"]["statute"]),
    "IDX_OOS": str(json.loads(RAW["index"].splitlines()[0])["routes"]["out_of_scope"]),
    "N_LOCAL_ARB": re.search(r"methods: .*arbiter (\d+)", OUT_LOCAL).group(1),
    "QJN03": html.escape(RR["jn-03"]["question"], quote=False), "N_AUTH": N_AUTH,
}
assert STATS["N_SMOKE_DESK"] == "8" and STATS["N_SMOKE_CASES"] == "11", (STATS["N_SMOKE_DESK"], STATS["N_SMOKE_CASES"])
E = lambda v: html.escape(str(v), quote=False)  # noqa: E731
STATS.update({                                  # the Google Chat door's numbers and words, from the kit
    "GCHAT_ACK": E(greplies.ACK), "HR_TITLE": E(gcards.TITLE), "SUB_HB": E(gcards.SUBTITLES["handbook"]),
    "SUB_LAW": E(gcards.SUBTITLES["statute"]), "POSH_BUTTON": E(gcards.POSH_BUTTON), "POSH_MEMBERS": E(gcards.POSH_MEMBERS),
    "RATE_PER_MIN": WORDS[gmain.RATE_PER_MIN], "QUESTION_MAX": f"{gevents.QUESTION_MAX:,}", "GATE_S": str(gmain.GATE_BUDGET_S),
    "CHECK_S": str(gmain.CHECK_BUDGET_S), "WORK_S": str(gmain.WORK_TIMEOUT_S), "MAX_ATTEMPTS": WORDS[gmain.MAX_ATTEMPTS],
    "LIMIT_BYTES": f"{gcards.LIMIT_BYTES:,}", "CLAIM_TTL_H": str(int(gclaims.TTL.total_seconds() // 3600)),
    "NOT_A_DELEGATE": E(delegation.NOT_A_DELEGATE), "CODE_401": E(smg.CODE_401), "DOOR_OFF": E(delegation.DOOR_OFF),
    "N_DELEG_RULES": WORDS[len(DELEG_RULES)], "N_DELEGABLE": WORDS[len(delegation.DELEGABLE)], "ALERT_NAME": E(ALERT_NAME),
    "N_DOOR": str(N_DOOR), "N_SMOKE_GCHAT": str(SMOKE_G.count("[PASS]")), "N_SMOKE_GCHAT_W": WORDS[SMOKE_G.count("[PASS]")], "NOT_ON_ROSTER": E(greplies.NOT_ON_ROSTER.split(".")[0] + "."),
})
assert STATS["N_DELEG_RULES"] == "seven" and STATS["N_DELEGABLE"] == "six" and STATS["N_SMOKE_GCHAT_W"] == "four" and N_DOOR == 11
assert gmain.RATE_PER_MIN == 6 and gevents.QUESTION_MAX == 4000 and STATS["CLAIM_TTL_H"] == "24"
assert int(STATS["IDX_HB"]) + int(STATS["IDX_LAW"]) + int(STATS["IDX_OOS"]) == len(INDEXED)

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(STATS)
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    assert "%%" not in text, re.findall(r"%%\w+%%", text)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: decide() on {len(QUESTIONS)} questions x {len(WHO)} callers, accept() in node over {N_GRID:,} inputs | desk_ops, relabel, "
      f"the Desk's routes, the smokes ({STATS['N_SMOKE_DESK']} and {STATS['N_SMOKE_CASES']} PASS) and route_eval --live on stand-ins")
