"""Build lesson 5.8 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

A person in the loop. services/chat/approval.py pauses a LangGraph turn for a person: withdraw_document waits for a
second person in the company (the person who asked cannot approve their own request), ask_user waits for the person
who asked, and offer_case offers a case and writes nothing. Nothing in the chat service imports the module, so it runs
offline (make approval-check, the page's cells), and tools.BLOCKED and the refuse node stay as lessons 5.4, 5.5 and
5.7 show them. On the lane: escalation by rule at the chat door (lesson 5.6's case_offer, a case raised into the People
team's queue and read in its inbox), and a clarifying question in words, answered on the same thread.

Build-time proof, all on the kit's own code:
  - the widget's every transition is build_approval_graph() and decide() (or a resume sent straight to the graph) run
    here on a scripted model: each scenario to its pause, then each person's decision on a fresh copy of that pause,
    with paused() checked unchanged after every refusal. The people, the document and the fakes (a roster, acme's
    queues) are commands/tests/test_approvals.py's own;
  - the offline cells (the pause, a second process resuming from one SQLite file, ask_user, the Change-it) are run
    here as the learner runs them, and make approval-check's output is the kit's test file run on the chat pins;
  - the lane cells are run against the kit's own chat service on stand-ins: agent.py's chat() with the real
    LangGraph brain on a scripted model, desk.py's chat door and case routes, shared/cases.py, commands/desk_ops.py,
    over a fake Firestore and audit bucket (commands/tests/test_cases.py's), a fake gcloud for the log read. Their
    outputs are not shown: the page shows the author's recordings, pb.recorded("5.8", ...), listed in RUN_LIST.md.
"""
import ast
import contextlib
import html
import importlib.util
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import types
import warnings
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "5.8"
title = ("<title>Lesson 5.8 Pause, approve, clarify and escalate: human in the loop - a turn that waits for a second "
         "person, a question only the asker answers, and a case in the People team's inbox | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
warnings.filterwarnings("ignore")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:8px 0 4px;}
.hl-nodes{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0;}
.hl-node{font-family:var(--mono);font-size:12.5px;padding:8px 12px;border-radius:8px;border:1px solid var(--border);background:var(--card);color:var(--slate);min-height:20px;}
.hl-node.on{background:var(--navy);color:#fff;border-color:var(--navy);}
.hl-node.wait{background:#fef3c7;color:#78350f;border-color:#f59e0b;}
.hl-btn{font:inherit;font-size:13px;min-height:44px;padding:6px 12px;border-radius:8px;border:1px solid var(--border);background:var(--card);cursor:pointer;color:var(--navy);margin:4px 6px 4px 0;}
.hl-btn:disabled{opacity:.5;cursor:default;}
.hl-wait{border-left:3px solid #f59e0b;background:#fffbeb;padding:6px 10px;margin:6px 0;color:#78350f;font-size:12.5px;}
.hl-steps{margin:6px 0 0;padding-left:20px;font-size:13px;line-height:1.5;}
.hl-steps li{margin:3px 0;overflow-wrap:anywhere;}
.hl-steps li.user{color:var(--navy);}.hl-steps li.ai{color:#1e3a8a;}.hl-steps li.tool{color:#065f46;}.hl-steps li.err{color:#991b1b;}.hl-steps li.pause{color:#92400e;}.hl-steps li.skip{color:#64748b;}
.hl-out{font-family:var(--mono);font-size:12.5px;padding:5px 10px;border-radius:8px;display:inline-block;margin-top:6px;background:#f1f5f9;color:var(--navy);overflow-wrap:anywhere;}
"""

setup = setup_section()


def load(name: str, rel: str):
    """A kit file loaded as a module of its own name, so the page's copy never collides with another import."""
    spec = importlib.util.spec_from_file_location(name, KIT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod                        # pydantic resolves the routes' models by their module
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ verbatim excerpts
AP, BR, CD, DL = "services/chat/approval.py", "services/chat/brains.py", "services/chat/desk.py", "shared/desk_law.py"
AR, SA, REC, MK = "services/chat/approval_routes.py", "shared/approvals.py", "services/ingest/reconcile.py", "mk/agents.mk"
EXCERPTS = {
    "header": ("services/chat/approval.py - the module's docstring: what it is, and the three tools",
               block(AP, "THE SERVICE REACHES THIS MODULE THROUGH ONE SWITCH, OFF UNTIL AN OPERATOR SETS IT.", end="The pause, in two forms")),
    "consts": ("services/chat/approval.py - who decides which tool, and the limits on a decision's words",
               block(AP, 'NEEDS_APPROVAL = frozenset({"withdraw_document"})', n=5)),
    "owner": ("services/chat/approval.py - owner(): the tenant and the person who asked, from the thread id",
              block(AP, "def owner(config) -> tuple[str, str]:")),
    "withdraw": ("services/chat/approval.py - withdraw_document: the side effect, and the last lock",
                 block(AP, "@tool", end="@tool")),
    "ask": ("services/chat/approval.py - ask_user: a question the person who asked answers",
            block(AP, "@tool", end="@tool", nth=2)),
    "offer": ("services/chat/approval.py - offer_case: the hand-off a model may offer, which writes nothing",
              block(AP, "@tool", end="for _t in (withdraw_document, ask_user, offer_case):", nth=3)),
    "check": ("services/chat/approval.py - _check(): who may make which decision",
              block(AP, "def _check(ask: dict, decision, by, may_approve=None)")),
    "approve": ("services/chat/approval.py - build_approval_graph(): route, the approve node and onward",
                block(AP, "    def route(state):", end="    g = StateGraph(MessagesState, context_schema=dict)")),
    "wiring": ("services/chat/approval.py - the graph: the brain's, with approve where refuse is",
               block(AP, "    g = StateGraph(MessagesState, context_schema=dict)", n=9)),
    "brain_route": ("services/chat/brains.py - the LangGraph brain's route and refuse node, as lesson 5.4 reads them",
                    block(BR, "        def route(state):", end="        g = StateGraph(MessagesState, context_schema=dict)")),
    "paused": ("services/chat/approval.py - paused(): what a paused turn waits for",
               block(AP, "def paused(agent, config: dict) -> list[dict]:")),
    "decide": ("services/chat/approval.py - decide(): refuse before anything runs, then resume for the person who asked",
               block(AP, "def decide(agent, config: dict, decisions: list[dict], *, by: str, context: dict | None = None,",
                     end="# ------------------------------")),
    "hitl": ("services/chat/approval.py - hitl_middleware(): the same pause for create_agent",
             block(AP, "def hitl_middleware():")),
    "mk": ("mk/agents.mk - make approval-check", block("mk/agents.mk", "# A person in the loop (workshop lesson 5.8)", n=7)),
    "sh": ("commands/approval-check.sh - the venv, the pins and the test file", block("commands/approval-check.sh", "set -euo pipefail", n=7)),
    "door": ("services/chat/desk.py - the chat door's answer to a hit: the fixed reply and case_offer, before any brain",
             block(CD, "        sensitive = cls in desk_rules.SENSITIVE", n=11)),
    "template": ("shared/desk_law.py - the fixed reply to a request for a person, and the case it opens",
                 block(DL, '    "human_requested": (', n=5) + "\n...\n" + block(DL, '    "people_query": {"queue": "people"', n=2)),
    # the approval wired in (13 October 2026): the switch, the records, the routes, the operator's run
    "wired": ("services/chat/approval_routes.py - wired(): chat()'s one call, the switch, and the hold",
              block(AR, "def wired(app, name: str, brain, tenant: str, email: str, session_id: str):",
                    end="# ---------------------------------------------------------------- the routes")),
    "agent_lines": ("services/chat/agent.py - the call in chat(), and the install line after the Desk's",
                    block("services/chat/agent.py", "    # A company whose agent_actions is approval (workshop lesson 5.8)", n=3) + "\n...\n"
                    + block("services/chat/agent.py", "import approval_routes  # noqa: E402", n=2)),
    "records": ("shared/approvals.py - the records, as the module's docstring lists them",
                block(SA, "    open_request()  the pause as a record", end="A record's fields:")),
    "decide_route": ("services/chat/approval_routes.py - the decision route: the record's checks, then decide()",
                     block(AR, '@router.post("/v1/approvals/{approval_id:approval_id}/decide")', end="    summary = _summary(out, ctx)")),
    "approved": ("services/ingest/reconcile.py - --approved: the re-check, then --retire's own branch through main()",
                 block(REC, "    if a.approved:", end="    if a.retire:")),
    "mk_wired": ("mk/agents.mk - agent-actions, withdraw-run and smoke-approval",
                 block(MK, "agent-actions: guard-project", n=2) + "\n\n" + block(MK, "withdraw-run: guard-project", n=5) + "\n\n"
                 + block(MK, "smoke-approval: guard-project", n=5)),
    "roles_line": ("shared/roles.py - ROLES, with doc_approver", block("shared/roles.py", "ROLES = (EMPLOYEE, LEAVER,", n=1)),
    "actions": ("shared/audit_log.py - the approval actions, on the line after the Desk's",
                block("shared/audit_log.py", "    # A person in the loop (workshop lesson 5.8): a withdrawal a model asked for", n=4)),
}
assert EXCERPTS["header"][1].startswith("THE SERVICE REACHES THIS MODULE THROUGH ONE SWITCH, OFF UNTIL AN OPERATOR SETS IT.")
assert "offer_case" in EXCERPTS["header"][1] and "approval_routes.py imports it" in EXCERPTS["header"][1]
assert EXCERPTS["wired"][1].rstrip().endswith("return Wired(ab, db, tenant, email, session_id)") and "raise HTTPException(409," in EXCERPTS["wired"][1]
assert EXCERPTS["agent_lines"][1].count("\n") == 5 and 'brain = approval_routes.wired(request.app, name, brain, tenant_id, user["email"], req.session_id)' in EXCERPTS["agent_lines"][1]
assert EXCERPTS["records"][1].lstrip().startswith("open_request()") and EXCERPTS["records"][1].rstrip().endswith("with every time as ISO text.")
assert EXCERPTS["decide_route"][1].rstrip().endswith("out = ab.graph.get_state(config).values") and "approval.roster_rule(db, approvals.APPROVER)" in EXCERPTS["decide_route"][1]
assert EXCERPTS["approved"][1].rstrip().endswith("return 0") and '"--retire", source, "--apply"' in EXCERPTS["approved"][1]
assert EXCERPTS["mk_wired"][1].rstrip().endswith("$(if $(DOC),DOCUMIND_DOC=$(DOC),) $(PY) smoke/smoke_approval.py")
assert EXCERPTS["roles_line"][1].rstrip().endswith('"desk_eval", "doc_approver")')
assert EXCERPTS["actions"][1].rstrip().endswith('"approval.request", "approval.approve", "approval.reject", "doc.withdraw",')
assert EXCERPTS["withdraw"][1].startswith("@tool\ndef withdraw_document(") and EXCERPTS["withdraw"][1].rstrip().endswith(
    'return {**(done or {}), "document": f"{tenant}/{doc}", "undo": f"make restore SOURCE={tenant}/{doc}"}')
assert EXCERPTS["ask"][1].startswith("@tool\ndef ask_user(") and EXCERPTS["ask"][1].rstrip().endswith(
    'raise ToolException("nobody was asked: put the question in your answer instead")')
assert EXCERPTS["offer"][1].startswith("@tool\ndef offer_case(") and EXCERPTS["offer"][1].rstrip().endswith(
    '"note": "Nothing is raised until the person presses Raise a case and confirms."}')
assert EXCERPTS["check"][1].rstrip().endswith("return None") and "cannot approve their own request" in EXCERPTS["check"][1]
assert EXCERPTS["approve"][1].rstrip().endswith('return [Send("tools", [c]) for c in calls] if calls else "agent"')
assert "answer = interrupt(request)" in EXCERPTS["approve"][1] and 'logger.info("approval asked' in EXCERPTS["approve"][1]
assert EXCERPTS["wiring"][1].rstrip().endswith("return g.compile(checkpointer=checkpointer)")
assert 'return "refuse" if any(c["name"] in BLOCKED for c in calls) else "tools"' in EXCERPTS["brain_route"][1]
assert EXCERPTS["paused"][1].rstrip().endswith("return _asks(calls, request, config)")
assert EXCERPTS["decide"][1].rstrip().endswith('config={**config, "recursion_limit": limits.recursion_limit()}, context=ctx)')
assert EXCERPTS["hitl"][1].rstrip().endswith("for name, allowed in DECISIONS.items()})")
assert EXCERPTS["mk"][1].rstrip().endswith("@PY=$(PY) bash commands/approval-check.sh")
assert EXCERPTS["sh"][1].rstrip().endswith('DOCUMIND_REQUIRE_LIBS=1 "$VENV/bin/python" -m unittest commands/tests/test_approvals.py -v')
assert EXCERPTS["door"][1].rstrip().endswith('"case_offer": {"case_type": cls}})')
assert '"human_requested": {"queue": "people", "draft": True' in EXCERPTS["template"][1]


def kit_window(label: str, code: str) -> str:
    """pagebuild.window(); a module's docstring is prose inside a string, so it is coloured as one string."""
    if label not in (EXCERPTS["header"][0], EXCERPTS["records"][0]):
        return window(label, code)
    empty = window(label, "")
    assert empty.count('<pre tabindex="0"></pre>') == 1
    return empty.replace('<pre tabindex="0"></pre>', '<pre tabindex="0"><span class="st">' + html.escape(code, quote=False) + "</span></pre>")


fill = filler(EXCERPTS, kit_window)

# ------------------------------------------------------------------ the kit's facts the page states
for p in (str(KIT / "services/chat"), str(KIT)):
    if p not in sys.path:
        sys.path.insert(0, p)
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage  # noqa: E402
from langgraph.checkpoint.memory import InMemorySaver  # noqa: E402
from langgraph.types import Command  # noqa: E402
import shared.documind_tools as dt  # noqa: E402
from shared import cases, desk_law, desk_rules, prices, roles  # noqa: E402

SEARCHED = []


def stand_in_retrieve(query, tenant_id="", top_k=5, doc_type=None, assertion=None, brain=None, **kw):
    """rag-api, standing in: one passage of the handbook for any question, and the call noted."""
    SEARCHED.append((tenant_id, query))
    return {"answer": "rag-api's own answer", "answerable": True, "confidence": "high",
            "citations": [{"chunk_id": "acme:np#0", "source_uri": "gs://YOUR-BUCKET/acme/hr_policy_2026.md", "page": 1,
                           "quote": "During probation the notice period is 15 days for either side.", "score": 0.9}]}


dt.retrieve = stand_in_retrieve
import approval  # noqa: E402
import approval_routes  # noqa: E402
from shared import approvals  # noqa: E402
import brains  # noqa: E402
import limits  # noqa: E402
import tools  # noqa: E402

kt = load("kit_test_approvals_108", "commands/tests/test_approvals.py")
kd = load("kit_test_desk_rules_108", "commands/tests/test_desk_rules.py")
ASKER, SECOND, OTHER, DOC, TENANT = kt.ASKER, kt.SECOND, kt.OTHER, kt.DOC, kt.TENANT
assert (TENANT, ASKER, SECOND, OTHER, DOC) == ("acme", "asha@example.com", "ravi@example.com", "meena@example.com", "hr_policy_2026.md")

AP_SRC = (KIT / AP).read_text(encoding="utf-8")
N_AP_LINES = len(AP_SRC.splitlines())
IMPORTERS = [p.relative_to(KIT).as_posix() for p in (KIT / "services").rglob("*.py")
             if p.name != "approval.py" and "__pycache__" not in p.parts
             and re.search(r"^\s*(?:from approval import|import approval\b)", p.read_text(encoding="utf-8"), re.M)]
assert IMPORTERS == ["services/chat/approval_routes.py"], IMPORTERS           # one module imports it, behind the switch
AGENT_SRC = (KIT / "services/chat/agent.py").read_text(encoding="utf-8")
assert AGENT_SRC.count('brain = approval_routes.wired(request.app, name, brain, tenant_id, user["email"], req.session_id)') == 1
assert AGENT_SRC.count("approval_routes.install(app, caller=caller, tenant_for=tenant_for, thread_config=thread_config)") == 1
assert (approval_routes.SWITCH, approval_routes.ON, approval_routes.WIRED_BRAIN) == ("agent_actions", "approval", "langgraph")
assert "if name != WIRED_BRAIN or not switched_on(tenant):\n        return brain" in (KIT / AR).read_text(encoding="utf-8")
assert tools.BLOCKED == {"delete_document", "send_email", "modify_access"}     # BLOCKED stays, as 5.4, 5.5 and 5.7 quote it
LG = brains.LangGraphBrain(InMemorySaver(), llm=kt.scripted([AIMessage("")])).graph.get_graph()
assert list(LG.nodes) == ["__start__", "agent", "tools", "refuse", "__end__"]   # the refuse node stays
assert approval.NEEDS_APPROVAL == frozenset({"withdraw_document"}) and approval.NEEDS_ANSWER == frozenset({"ask_user"})
assert approval.DECISIONS == {"withdraw_document": ("approve", "reject"), "ask_user": ("respond",)}
assert (approval.NAME_MAX, approval.REASON_MAX, approval.ANSWER_MAX) == (200, 200, 4000)
assert [t.name for t in approval.PERSON_TOOLS] == ["withdraw_document", "ask_user", "offer_case"]
assert roles.ROLES[-1] == "doc_approver" == approvals.APPROVER and "people_ops" in roles.ROLES   # the approver's role (5.8-B); people_ops reads people
assert roles.desks(["doc_approver"]) == set()                              # it opens no desk
assert tuple(desk_law.QUEUES["people"]["read"]) == ("people_ops",)        # the People team's queue: people_ops reads it
AG_GRAPH = approval.build_approval_graph(kt.scripted([AIMessage("")]), InMemorySaver()).get_graph()
assert list(AG_GRAPH.nodes) == ["__start__", "agent", "approve", "tools", "__end__"]
N_AG_EDGES, N_LG_EDGES = len(AG_GRAPH.edges), len(LG.edges)
assert (N_AG_EDGES, N_LG_EDGES) == (7, 6), (N_AG_EDGES, N_LG_EDGES)
reqs = (KIT / "services/chat/requirements.txt").read_text(encoding="utf-8") + (KIT / "services/chat/requirements-local.txt").read_text(encoding="utf-8")
PINS = {k: re.search(rf"(?m)^{re.escape(k)}==([\d.]+)$", reqs).group(1) for k in ("langchain", "langgraph", "langgraph-checkpoint-sqlite")}
assert PINS == {"langchain": "1.4.0", "langgraph": "1.2.12", "langgraph-checkpoint-sqlite": "3.1.1"}
assert "a second process sharing a SqliteSaver file resumes a" in AP_SRC
# what step 8 says the kit does not do yet, checked here so the page changes when the kit does
TOP_DEFS = {n.name for n in ast.parse(AP_SRC).body if isinstance(n, ast.FunctionDef)}
assert TOP_DEFS == {"_key", "owner", "normalize_name", "withdraw_document", "ask_user", "offer_case", "_describe", "_pending",
                    "_request", "_asks", "_check", "_refusals", "roster_rule", "paused", "decide", "build_approval_graph",
                    "hitl_middleware"}, TOP_DEFS
assert "expire" not in AP_SRC.lower() and "adk" not in AP_SRC.lower()          # the pause has no clock of its own; no form for the ADK brain
assert approvals.TTL_H == 24.0 and 'TTL_H = float(os.environ.get("APPROVAL_TTL_H", "24"))' in (KIT / SA).read_text(encoding="utf-8")   # the record has one
assert approvals.STATUSES == ("pending", "approved", "rejected", "cancelled", "answered", "failed", "expired", "lost", "withdrawn")
assert [t.name for t in tools.TOOLS] == ["retrieve", "calculate_processing_cost"]   # the lane's brains have no ask_user with the switch off
SWITCHED = sorted(p.relative_to(KIT).as_posix() for p in pb.kit_runtime_files("*.py") if p.name != "approval.py"
                  and p.relative_to(KIT).parts[0] in ("services", "shared") and "agent_actions" in p.read_text(encoding="utf-8", errors="replace"))
assert SWITCHED == ["services/chat/agent.py", "services/chat/approval_routes.py"], SWITCHED   # the switch: one call, one module
OPS_SRC = (KIT / "commands/desk_ops.py").read_text(encoding="utf-8")
assert '"agent_actions": ("off", "approval")' in OPS_SRC and 'desk --tenant $(TENANT) $(if $(AGENT_ACTIONS),--actions $(AGENT_ACTIONS),)' in (KIT / MK).read_text(encoding="utf-8")
assert "may_approve is not None and not may_approve(" in AP_SRC                 # anyone else, unless the caller says otherwise
assert "may_approve=approval.roster_rule(db, approvals.APPROVER)" in (KIT / AR).read_text(encoding="utf-8")   # the routes say: doc_approver
AUD_SRC = (KIT / "shared/audit_log.py").read_text(encoding="utf-8")
ACTIONS = set(ast.literal_eval(re.search(r"AUDIT_ACTIONS = (\{.*?\})\n", AUD_SRC, re.S).group(1)))
assert {"approval.request", "approval.approve", "approval.reject", "doc.withdraw"} <= ACTIONS
EMITTED = sorted(set(re.findall(r'audit_log\.emit\("([a-z_.]+)"', (KIT / SA).read_text(encoding="utf-8"))))
assert EMITTED == ["approval.approve", "approval.reject", "approval.request", "doc.withdraw"], EMITTED   # what lesson 4.8 lists
assert re.findall(r"mirror\.(\w+)\(", (KIT / REC).read_text(encoding="utf-8")) == ["retired", "retired"]   # lesson 7.3's fact holds
# the kit's own may_approve (13 October 2026): roster_rule(db, role), on the kit test's fake roster. Ravi holds
# people_ops in acme, Meena is an acme employee without it, Zoe is on no roster of acme's: each refusal says why.
ROSTER_RULE = approval.roster_rule(kt.roster({ASKER: None, SECOND: ["employee", "people_ops"], OTHER: None}), "people_ops")
assert ROSTER_RULE(TENANT, SECOND) is True
for _who, _why in ((OTHER, f"{OTHER} does not hold people_ops in acme"),
                   ("zoe@example.com", "zoe@example.com is not on acme's roster")):
    try:
        ROSTER_RULE(TENANT, _who)
        raise AssertionError(f"roster_rule let {_who} decide")
    except PermissionError as e:
        assert _why in str(e), e
assert limits.TURN_BUDGET_INR == 5 and "elif self.spent_inr() >= self.budget_inr:" in (KIT / "services/chat/limits.py").read_text(encoding="utf-8")
CHAT_PY = (KIT / "services/frontend/chat.py").read_text(encoding="utf-8")
assert "case_offer" not in CHAT_PY and 'st.caption(f"brain: {body.get(\'brain\')} · tools:' in CHAT_PY   # the Chat page offers no case

# the escalation: the gate's own human_requested example, and one of its near misses
ESCALATE = "Escalate this to a human please"
NEAR = "How do I contact HR about payroll?"
assert ("en", ESCALATE) in kd.EXAMPLES["human_requested"] and NEAR in kd.NEAR_MISSES
assert desk_rules.gate(ESCALATE) == "human_requested" and desk_rules.gate(NEAR) is None
assert "human_requested" not in desk_rules.SENSITIVE                         # its row names the person
TEMPLATE = desk_law.template("human_requested")
assert desk_law.CASE_TYPES["human_requested"] == {"queue": "people", "draft": True, "fallback": None, "clock": None, "basis": ()}
QUEUES_ACME = json.loads((KIT / "evals/desk/queues.acme.json").read_text(encoding="utf-8"))
SLA_PEOPLE, PEOPLE_NAME = QUEUES_ACME["people"]["sla_days"], QUEUES_ACME["people"]["name"]
assert (SLA_PEOPLE, PEOPLE_NAME) == (5, "People team")
DRAFT_MIN = int(cases.DRAFT_TTL.total_seconds() // 60)
assert DRAFT_MIN == 30

# the clarification: a question the handbook answers two ways, and the reply that picks one
Q_NOTICE, Q_REPLY = "What is my notice period?", "I am still on probation."
assert desk_rules.gate(Q_NOTICE) is None and desk_rules.gate(Q_REPLY) is None
HANDBOOK = (KIT / "evals/corpus/acme/hr_policy_2026.md").read_text(encoding="utf-8")
assert "## NP-03 — Notice period\n\nA confirmed employee at grade E3 or above serves a notice period of 60 days." in HANDBOOK
assert "## PB-02 — Probation\n\nNew joiners serve six months on probation at grade E2. During probation the notice\nperiod is 15 days for either side." in HANDBOOK

# the Desk page's labels the walk quotes, as services/frontend/desk.py draws them
FD_SRC = (KIT / "services/frontend/desk.py").read_text(encoding="utf-8")
UI_LABELS = ['st.subheader("Tell the Desk")', 'st.text_area("What do you need help with?"', 'st.form_submit_button("Send")',
             '"human_requested": "Ask for a person"}', '"human_requested": "I want to talk to a person",',
             'st.selectbox("What is it about?"', 'st.text_area("In your own words (you can change this before sending)"',
             'st.form_submit_button("Next: check it before sending")', 'st.form_submit_button("Send", type="primary")',
             '"Nothing is sent until you press Send. This draft is kept for 30 minutes"',
             'f"Sent. Your case reference is {_ref(out)}. You can follow it under Your cases."',
             'st.subheader("Your inbox")', '"human_requested": "Asked for a person"}', '"open": "Sent"',
             'f"**Raised by:** {_md(c.get(\'requester\'))}"', '"**In their words:**  \\n"',
             'st.selectbox("Change the status to"', '"acknowledged": "Acknowledged (we have seen it)"',
             'st.form_submit_button("Update")', '"acknowledged": "Seen by the team"', 'st.subheader("Your cases")',
             'st.caption(f"This is a fixed reply. {used} To reach a person, raise the case below. "',
             '"A case does not include what you typed here."', 'else "No AI model was used.")',
             '"brain": "direct"}', 'with st.expander(f"{name}. Status: {state}"):', '"people": {"read": ("people_ops",)',
             "**: not sent yet\")", "return [f\"**Goes to:** {_md(owner.get('queue_name') or 'the team your company names')}{contact}\"]"]
assert all(label in FD_SRC for label in UI_LABELS), [label for label in UI_LABELS if label not in FD_SRC]

# the middleware form: one node more, so one checkpoint more for each model call (as the kit's test counts them)
from langchain.agents import create_agent  # noqa: E402


def mw_agent(script, middleware):
    """create_agent on a scripted model with the kit's tools and PERSON_TOOLS, with or without the HITL middleware."""
    return create_agent(model=kt.scripted(script), tools=tools.TOOLS + approval.PERSON_TOOLS, middleware=middleware,
                        checkpointer=InMemorySaver())


assert "HumanInTheLoopMiddleware.after_model" in mw_agent([], [approval.hitl_middleware()]).get_graph().nodes
CHECKPOINTS = {}
for label, script, calls in (("one", [AIMessage("Hello.")], 1),
                             ("two", kt.turn([("calculate_processing_cost", {"total_pages": 10})], "About Rs 42."), 2)):
    counts = []
    for middleware in ([], [approval.hitl_middleware()]):
        ag = mw_agent(script, middleware)
        ag.invoke({"messages": [HumanMessage("Hi")]}, kt.cfg("count-" + label))
        counts.append(len(list(ag.checkpointer.list(kt.cfg("count-" + label)))))
    assert counts[1] - counts[0] == calls, (label, counts)
    CHECKPOINTS[label] = counts
assert CHECKPOINTS["one"][1] - CHECKPOINTS["one"][0] == 1 and CHECKPOINTS["two"][1] - CHECKPOINTS["two"][0] == 2

# ------------------------------------------------------------------ Level 0: every transition the widget shows, run on the kit
REASON, ANSWER = "That handbook is still in force.", Q_REPLY
CLARIFY_Q = "Are you a confirmed employee at grade E3 or above, or still on probation?"
PEOPLE = {"asha": ASKER, "ravi": SECOND, "meena": OTHER}
STATUS = {"LookupError": 409, "ValueError": 422, "PermissionError": 403}       # decide()'s docstring: a route's answer
SCEN = {
    "withdraw": {"label": "withdraw_document: withdraw hr_policy_2026.md", "question": f"Withdraw {DOC}",
                 "calls": [("withdraw_document", {"name": DOC})]},
    "mixed": {"label": "retrieve and withdraw_document, in one message", "question": f"Withdraw {DOC}, and tell me the notice period",
              "calls": [("retrieve", {"query": "notice period"}), ("withdraw_document", {"name": DOC})]},
    "ask": {"label": "ask_user: a clarifying question", "question": Q_NOTICE,
            "calls": [("ask_user", {"question": CLARIFY_Q})]},
    "offer": {"label": "offer_case: a request the rules miss", "question": "Could someone from HR look at my notice period?",
              "calls": [("offer_case", {"case_type": "human_requested"})]},
    "plain": {"label": "retrieve alone: nothing to wait for", "question": Q_NOTICE,
              "calls": [("retrieve", {"query": "notice period"})]},
}
# offer_case is the model's offer when the rules miss (the page says so): the door would answer a request it knows first
assert desk_rules.gate(SCEN["offer"]["question"]) is None and desk_rules.mask(SCEN["offer"]["question"])[1] == []
HOWS = ("decide", "role", "straight")
RAVI_ONLY = (lambda tenant, email: (tenant, email) == (TENANT, SECOND))      # the test's may_approve: who else may
_session = iter(range(10_000))


def call_text(name: str, args: dict) -> str:
    """A tool call as the panel names it."""
    return f"{name}({', '.join(f'{k}={v!r}' for k, v in args.items())})"


def to_pause(key: str):
    """A fresh graph on a scripted model, run from the question until it pauses or ends."""
    calls, withdraw = kt.withdrawer()
    g = approval.build_approval_graph(kt.scripted(kt.turn(SCEN[key]["calls"], "The answer.")), InMemorySaver())
    c = kt.cfg(f"page-{key}-{next(_session)}")
    ctx = {"withdraw": withdraw}
    if key == "offer":
        ctx.update(db=kt.roster({ASKER: None}), case_queues=kt.acme_queues(), offers=[])
    before = len(SEARCHED)
    updates = [list(u) for u in g.stream({"messages": [HumanMessage(SCEN[key]["question"])]}, c, context=ctx,
                                         stream_mode="updates")]
    return g, c, ctx, calls, updates, len(SEARCHED) - before


def history(g, c) -> list:
    """The node each checkpoint says runs next, oldest first: the turn's path, as the kit's test reads it."""
    return [list(s.next) for s in reversed(list(g.get_state_history(c)))]


def results(out, after: int) -> list:
    """The tool results the resumed turn added, in order: [name, status, content]."""
    return [[m.name, m.status, m.content] for m in out["messages"][after:] if isinstance(m, ToolMessage)]


def decision(kind: str) -> dict:
    """One decision of each kind, with the words the kit's tests use."""
    return {"approve": {"type": "approve"}, "reject": {"type": "reject", "message": REASON},
            "respond": {"type": "respond", "message": ANSWER}}[kind]


SCEN_DATA = {}
for key, sc in SCEN.items():
    g, c, ctx, calls, updates, searched = to_pause(key)
    waiting = approval.paused(g, c)
    entry = {"label": sc["label"], "question": sc["question"], "calls": [call_text(n, a) for n, a in sc["calls"]],
             "updates": [u[0] for u in updates], "searched_before": searched}
    if not waiting:                                                    # a turn with nothing to wait for runs through
        state = g.get_state(c).values
        entry.update(pauses=False, path=history(g, c), results=results(state, 1))
        if key == "offer":
            assert ctx["db"].writes == [] and ctx["offers"] == [{"case_type": "human_requested"}]
            assert json.loads(entry["results"][0][2])["handled_by"] == PEOPLE_NAME
        SCEN_DATA[key] = entry
        continue
    assert entry["updates"] == ["agent", "__interrupt__"] and searched == 0     # the turn stopped before any tool ran
    entry.update(pauses=True, waiting=[{k: w[k] for k in ("tool", "args", "call_id", "allowed_decisions", "description",
                                                           "tenant", "requester")} for w in waiting], outcomes={})
    for who, email in PEOPLE.items():
        for kind in ("approve", "reject", "respond"):
            for how in HOWS:
                g, c, ctx, calls, _, _ = to_pause(key)
                before, n_msgs, n_search = approval.paused(g, c), len(g.get_state(c).values["messages"]), len(SEARCHED)
                try:
                    if how == "straight":
                        out = g.invoke(Command(resume={"decisions": [decision(kind)], "by": email}), c, context=ctx)
                    else:
                        out = approval.decide(g, c, [decision(kind)], by=email, context=ctx,
                                              may_approve=RAVI_ONLY if how == "role" else None)
                except (LookupError, ValueError, PermissionError) as e:
                    assert approval.paused(g, c) == before and calls == [] and len(SEARCHED) == n_search
                    res = {"kind": "refused", "error": type(e).__name__, "status": STATUS[type(e).__name__], "message": str(e)}
                else:
                    if "__interrupt__" in out:                         # the approve node's own lock asked again
                        assert approval.paused(g, c) == before and calls == []
                        res = {"kind": "asked_again", "refused": out["__interrupt__"][0].value["refused"]}
                    else:
                        assert approval.paused(g, c) == []
                        res = {"kind": "resumed", "path": history(g, c), "results": results(out, n_msgs),
                               "withdrawn": list(calls), "searched": len(SEARCHED) - n_search}
                        try:
                            approval.decide(g, c, [decision(kind)], by=email, context=ctx)
                        except LookupError as e:                       # nothing waits now: a route's 409
                            AFTER = str(e)
                entry["outcomes"][f"{who}|{kind}|{how}"] = res
    SCEN_DATA[key] = entry
assert AFTER == "this conversation is not waiting for anyone"
W = SCEN_DATA
# the kit's rules, read back from the runs (the prose states them)
assert W["withdraw"]["outcomes"]["asha|approve|decide"] == {"kind": "refused", "error": "PermissionError", "status": 403,
                                                          "message": "the person who asked cannot approve their own request: a second person must"}
assert W["withdraw"]["outcomes"]["asha|approve|straight"] == {"kind": "asked_again", "refused": [
    "the person who asked cannot approve their own request: a second person must"]}
OWN = W["withdraw"]["outcomes"]["asha|approve|decide"]["message"]
ok = W["withdraw"]["outcomes"]["ravi|approve|decide"]
assert ok["kind"] == "resumed" and ok["path"] == [["__start__"], ["agent"], ["approve"], ["tools"], ["agent"], []]
assert ok["withdrawn"] == [{"tenant": TENANT, "name": DOC, "requested_by": ASKER, "approved_by": SECOND}]
assert W["withdraw"]["outcomes"]["meena|approve|decide"]["kind"] == "resumed"            # with no may_approve, anyone else
assert W["withdraw"]["outcomes"]["meena|approve|role"] == {"kind": "refused", "error": "PermissionError", "status": 403,
                                                         "message": f"{OTHER} may not decide withdraw_document requests in this company"}
LAST_LOCK = W["withdraw"]["outcomes"]["ravi|approve|straight"]
assert LAST_LOCK["kind"] == "resumed" and LAST_LOCK["withdrawn"] == [] and LAST_LOCK["results"][0][1] == "error"
assert "withdraw_document runs only after a second person in the company approves this call" in LAST_LOCK["results"][0][2]
CANCEL = W["withdraw"]["outcomes"]["asha|reject|decide"]
assert json.loads(CANCEL["results"][0][2])["error"] == "withdraw_document was cancelled by the person who asked for it, so nothing was done"
REJECT = W["mixed"]["outcomes"]["ravi|reject|decide"]
assert [r[:2] for r in REJECT["results"]] == [["withdraw_document", "error"], ["retrieve", "success"]] and REJECT["searched"] == 1
assert json.loads(REJECT["results"][0][2]) == {"error": "withdraw_document was rejected by a second person, so nothing was done",
                                               "their_reason": REASON}
BOTH = W["mixed"]["outcomes"]["ravi|approve|decide"]
assert BOTH["kind"] == "resumed" and BOTH["searched"] == 1 and len(BOTH["withdrawn"]) == 1
WRONG_KIND = W["withdraw"]["outcomes"]["ravi|respond|decide"]
assert WRONG_KIND == {"kind": "refused", "error": "ValueError", "status": 422,
                      "message": "withdraw_document takes approve or reject, not 'respond'"}
ASKED = W["ask"]["outcomes"]
assert ASKED["asha|respond|decide"]["results"] == [["ask_user", "success", ANSWER]]
assert ASKED["asha|respond|decide"]["path"][-3:] == [["approve"], ["agent"], []]
assert ASKED["ravi|respond|decide"]["message"] == "only the person who asked may answer their own question"
assert ASKED["asha|approve|decide"]["message"] == "ask_user takes respond, not 'approve'"
assert W["plain"]["path"] == [["__start__"], ["agent"], ["tools"], ["agent"], []] and not W["plain"]["pauses"]
assert W["offer"]["path"] == [["__start__"], ["agent"], ["tools"], ["agent"], []] and not W["offer"]["pauses"]
N_TRANSITIONS = sum(len(e.get("outcomes", {})) for e in W.values())
assert N_TRANSITIONS == 3 * 3 * 3 * len(HOWS)

# ------------------------------------------------------------------ the offline cells, run here as the learner runs them
SCRIPTED_CLASS = '''class Scripted(FakeMessagesListChatModel):
    """A model that replies as scripted, in order."""
    def bind_tools(self, tools, **kw):
        """The graph binds the kit's tools; a scripted model keeps itself."""
        return self'''
HEAD = '''import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
import approval
''' + SCRIPTED_CLASS

PAUSE_PY = HEAD + '''
import logging
class Show(logging.Handler):
    """Prints each line approval.py logs."""
    def emit(self, record):
        """One log line, printed where the cell's own lines go."""
        print("  log:", record.getMessage())
logging.getLogger("documind.chat.approval").addHandler(Show())
logging.getLogger("documind.chat.approval").setLevel(logging.INFO)
def withdraw(**kw):
    """The injected executor: it prints what it was asked to do and withdraws nothing."""
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
print("  waiting now:", approval.paused(g, cfg))'''

SQLITE_A = '''import os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
import approval
''' + SCRIPTED_CLASS + '''
cfg = {"configurable": {"thread_id": "acme:asha@example.com:lesson108-sqlite"}}
ask = AIMessage("", tool_calls=[{"name": "withdraw_document", "args": {"name": "hr_policy_2026.md"}, "id": "c0"}])
with SqliteSaver.from_conn_string(os.path.expanduser("~/lesson108_threads.db")) as saver:
    g = approval.build_approval_graph(Scripted(responses=[ask]), saver)
    g.invoke({"messages": [HumanMessage("Withdraw hr_policy_2026.md")]}, cfg, context={})
    print("process 1: paused before", g.get_state(cfg).next, "| waiting:", [w["tool"] for w in approval.paused(g, cfg)])
print("process 1: ends; the paused turn is in the file")'''

SQLITE_B = '''import logging, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
import approval
''' + SCRIPTED_CLASS + '''
class Show(logging.Handler):
    """Prints each line approval.py logs."""
    def emit(self, record):
        """One log line, printed where the cell's own lines go."""
        print("process 2: log:", record.getMessage())
logging.getLogger("documind.chat.approval").addHandler(Show())
logging.getLogger("documind.chat.approval").setLevel(logging.INFO)
def withdraw(**kw):
    """The injected executor: it prints what it was asked to do and withdraws nothing."""
    print("process 2: withdraw() called with", kw)
    return {"status": "withdrawal_started"}
cfg = {"configurable": {"thread_id": "acme:asha@example.com:lesson108-sqlite"}}
with SqliteSaver.from_conn_string(os.path.expanduser("~/lesson108_threads.db")) as saver:
    g = approval.build_approval_graph(Scripted(responses=[AIMessage("Withdrawn, from the second process.")]), saver)
    print("process 2: a new graph on the same file finds:", [w["tool"] for w in approval.paused(g, cfg)])
    out = approval.decide(g, cfg, [{"type": "approve"}], by="ravi@example.com", context={"withdraw": withdraw})
    print("process 2: answer:", out["messages"][-1].content, "| waiting now:", approval.paused(g, cfg))'''

ASK_PY = HEAD + f'''
ASHA, RAVI = "asha@example.com", "ravi@example.com"
cfg = {{"configurable": {{"thread_id": f"acme:{{ASHA}}:lesson108-ask"}}}}
question = "{CLARIFY_Q}"
g = approval.build_approval_graph(Scripted(responses=[
    AIMessage("", tool_calls=[{{"name": "ask_user", "args": {{"question": question}}, "id": "c0"}}]),
    AIMessage("The answer, from the person's reply.")]), InMemorySaver())
g.invoke({{"messages": [HumanMessage("{Q_NOTICE}")]}}, cfg, context={{}})
for w in approval.paused(g, cfg):
    print(f"  waiting: {{w['tool']}} takes {{w['allowed_decisions']}}, for {{w['requester']}}: {{w['description']}}")
for who, d in ((RAVI, {{"type": "respond", "message": "Confirmed, E3."}}), (ASHA, {{"type": "approve"}})):
    try:
        approval.decide(g, cfg, [d], by=who)
    except (PermissionError, ValueError) as e:
        print(f"  {{who.split('@')[0]}} sends {{d['type']}}: {{type(e).__name__}} - {{e}}")
out = approval.decide(g, cfg, [{{"type": "respond", "message": "{Q_REPLY}"}}], by=ASHA)
reply = [m for m in out["messages"] if isinstance(m, ToolMessage)][-1]
print(f"  asha answers: the model reads {{reply.name}}'s result {{reply.content!r}} ({{reply.status}})")
print("  path:", " -> ".join(s.next[0] if s.next else "END" for s in reversed(list(g.get_state_history(cfg)))))'''

TWICE_PY = HEAD + '''
import logging
lines = []
class Keep(logging.Handler):
    """Keeps every line approval.py logs."""
    def emit(self, record):
        """One log line, kept for the count."""
        lines.append(record.getMessage())
logging.getLogger("documind.chat.approval").addHandler(Keep())
logging.getLogger("documind.chat.approval").setLevel(logging.INFO)
done = []
def withdraw(**kw):
    """The injected executor: it counts the withdrawals and withdraws nothing."""
    done.append(kw)
    return {"status": "withdrawal_started"}
cfg = {"configurable": {"thread_id": "acme:asha@example.com:lesson108-twice"}}
g = approval.build_approval_graph(Scripted(responses=[
    AIMessage("", tool_calls=[{"name": "withdraw_document", "args": {"name": "hr_policy_2026.md"}, "id": "c0"}]),
    AIMessage("Done.")]), InMemorySaver())
g.invoke({"messages": [HumanMessage("Withdraw hr_policy_2026.md")]}, cfg, context={"withdraw": withdraw})
print("  at the pause:     ", sum("approval asked" in x for x in lines), "approval line(s)")
approval.decide(g, cfg, [{"type": "approve"}], by="ravi@example.com", context={"withdraw": withdraw})
print("  after the resume: ", sum("approval asked" in x for x in lines), "approval line(s),", len(done), "withdrawal(s)")'''

MOVE_PY = '''import warnings
from pathlib import Path
warnings.filterwarnings("ignore", category=UserWarning)
p = Path("services/chat/approval.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
log = next(i for i, x in enumerate(lines) if 'logger.info("approval asked' in x)
stop = next(i for i, x in enumerate(lines) if "answer = interrupt(request)" in x)
lines.insert(stop, lines.pop(log))                  # the same indentation: both lines sit in approve()
p.write_text("".join(lines), encoding="utf-8")
print(f"moved line {log + 1} up to line {stop + 1}, just above: {lines[stop + 1].split('#')[0].strip()}")'''
RESTORED = "approval.py is the kit's again"


def heredoc(body: str, python: str = "python", prefix: str = "") -> str:
    """A cell: the body as a quoted heredoc, so it pastes into bash as it is."""
    return f"{prefix}{python} - <<'PY'\n{body}\nPY"


GV = "~/graph-venv/bin/python"
T = Path(tempfile.mkdtemp(prefix="lesson108-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1",
       "HOME": str(T), "USERPROFILE": str(T)}
for k in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT", "DOCUMIND_PROFILE"):
    ENV.pop(k, None)


def run_cell(body: str, cwd: Path = KIT, env: dict | None = None) -> str:
    """One Python cell, run as the learner runs it: a fresh interpreter, the kit as the working directory."""
    r = subprocess.run([sys.executable, "-"], input=body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                       env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-2000:]
    return r.stdout


OUT = {}
OUT["pause"] = run_cell(PAUSE_PY)
assert "  ran: agent\n  ran: __interrupt__\n" in OUT["pause"] and f"  asha approves: PermissionError - {OWN}\n" in OUT["pause"]
assert "  path: __start__ -> agent -> approve -> tools -> agent -> END\n" in OUT["pause"]
assert OUT["pause"].count("  log: approval asked: withdraw_document") == 1
assert OUT["pause"].index("  log: approval asked") > OUT["pause"].index("  still waiting:")    # written at the resume only
OUT["sqlite"] = run_cell(SQLITE_A) + run_cell(SQLITE_B)                                          # two processes, one file
assert "process 1: paused before ('approve',) | waiting: ['withdraw_document']" in OUT["sqlite"]
assert "process 2: a new graph on the same file finds: ['withdraw_document']" in OUT["sqlite"]
assert "process 2: answer: Withdrawn, from the second process. | waiting now: []" in OUT["sqlite"]
assert OUT["sqlite"].count("process 2: log: approval asked: withdraw_document") == 1
assert "'requested_by': 'asha@example.com', 'approved_by': 'ravi@example.com'" in OUT["sqlite"]
OUT["ask"] = run_cell(ASK_PY)
assert "  ravi sends respond: PermissionError - only the person who asked may answer their own question" in OUT["ask"]
assert "  asha sends approve: ValueError - ask_user takes respond, not 'approve'" in OUT["ask"]
assert f"the model reads ask_user's result {Q_REPLY!r} (success)" in OUT["ask"]
assert "  path: __start__ -> agent -> approve -> agent -> END" in OUT["ask"]
OUT["twice"] = run_cell(TWICE_PY)
assert OUT["twice"] == "  at the pause:      0 approval line(s)\n  after the resume:  1 approval line(s), 1 withdrawal(s)\n", OUT["twice"]
# the Change-it, on a copy of the kit's chat service and shared code: the line moved above interrupt(), then the count
COPY = T / "kit"
for rel in ("services/chat", "shared"):
    shutil.copytree(KIT / rel, COPY / rel, ignore=shutil.ignore_patterns("__pycache__"))
moved = run_cell(MOVE_PY, cwd=COPY)
assert re.fullmatch(r"moved line \d+ up to line \d+, just above: answer = interrupt\(request\)\n", moved), moved
CHANGED = (COPY / AP).read_text(encoding="utf-8")
assert len(CHANGED.splitlines()) == N_AP_LINES and sorted(CHANGED.splitlines()) == sorted(AP_SRC.splitlines())   # one line moved
twice_changed = run_cell(TWICE_PY, cwd=COPY)
assert twice_changed == "  at the pause:      1 approval line(s)\n  after the resume:  2 approval line(s), 1 withdrawal(s)\n", twice_changed
OUT["move"] = moved + twice_changed + RESTORED + "\n"
MOVE_FROM, MOVE_TO = (int(x) for x in re.match(r"moved line (\d+) up to line (\d+)", moved).groups())
assert AP_SRC.splitlines()[MOVE_FROM - 1].strip().startswith('logger.info("approval asked')
assert AP_SRC.splitlines()[MOVE_TO - 1].strip().startswith("answer = interrupt(request)")

# make approval-check: the kit's own test file, as commands/approval-check.sh runs it, on the chat pins
t = subprocess.run([sys.executable, "-m", "unittest", "commands/tests/test_approvals.py", "-v"], cwd=str(KIT),
                   capture_output=True, text=True, encoding="utf-8", env={**ENV, "DOCUMIND_REQUIRE_LIBS": "1"})
assert t.returncode == 0, (t.stdout + t.stderr)[-3000:]
CHECK_LINES = (t.stdout + t.stderr).rstrip("\n").splitlines()
assert CHECK_LINES[-1] == "OK" and not any("skipped" in x for x in CHECK_LINES), CHECK_LINES
N_TESTS = int(re.search(r"^Ran (\d+) tests? in", "\n".join(CHECK_LINES), re.M).group(1))
TEST_NAMES = re.findall(r"^(test_\w+) \(commands\.tests\.test_approvals\.(\w+)\.", "\n".join(CHECK_LINES), re.M)
N_WIRING, N_APPROVALS = (sum(c == k for _, c in TEST_NAMES) for k in ("Wiring", "Approvals"))
assert N_TESTS == len(TEST_NAMES) == N_WIRING + N_APPROVALS and N_WIRING == 4 and N_APPROVALS == 11, (N_TESTS, TEST_NAMES)
OUT["check"] = "\n".join(re.sub(r"^Ran (\d+) tests in [\d.]+s$", r"Ran \1 tests in N.NNNs", x) for x in CHECK_LINES) + "\n"

# the wired approval's own test file (step 8), as its cell runs it: the switch off and on, on the kit's chat service
t = subprocess.run([sys.executable, "-m", "unittest", "commands/tests/test_approval_wired.py", "-v"], cwd=str(KIT),
                   capture_output=True, text=True, encoding="utf-8", env={**ENV, "DOCUMIND_REQUIRE_LIBS": "1"})
assert t.returncode == 0, (t.stdout + t.stderr)[-3000:]
WIRED_LINES = (t.stdout + t.stderr).rstrip("\n").splitlines()
assert WIRED_LINES[-1] == "OK" and not any("skipped" in x for x in WIRED_LINES), WIRED_LINES
N_WIRED_TESTS = int(re.search(r"^Ran (\d+) tests? in", "\n".join(WIRED_LINES), re.M).group(1))
WIRED_CLASSES = re.findall(r"^test_\w+ \(commands\.tests\.test_approval_wired\.(\w+)\.", "\n".join(WIRED_LINES), re.M)
assert N_WIRED_TESTS == len(WIRED_CLASSES) == 18 and set(WIRED_CLASSES) == {"Records", "Wiring", "WiredService"}, WIRED_CLASSES
OUT["wired_check"] = "\n".join(re.sub(r"^Ran (\d+) tests in [\d.]+s$", r"Ran \1 tests in N.NNNs", x) for x in WIRED_LINES) + "\n"

# ------------------------------------------------------------------ the lane cells (the author's runs: pb.recorded)
SA_FN = 'sa() { echo "documind-$1-sa@$PROJECT.iam.gserviceaccount.com"; }'
ETOK_FN = ('etok() { gcloud auth print-identity-token --include-email --audiences="$CHAT" \\\n'
           '         --impersonate-service-account="$(sa "$1")"; }')
ROLES_SET = "employee,grc_member,ic_member:hyderabad,ic_member:pune,people_ops"
CALL_FN = '''def call(path, body=None):
    """One call to the chat service as documind-evalacme-sa: the status and the JSON it answers."""
    req = urllib.request.Request(os.environ["CHAT"] + path, method="GET" if body is None else "POST",
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
def show(text):
    """An answer on indented lines of at most 100 characters."""
    print(textwrap.fill(" ".join(str(text).split()), 100, initial_indent="    ", subsequent_indent="    "))'''

ESCALATE_PY = f'''import json, os, textwrap, urllib.error, urllib.request, uuid, warnings
from datetime import datetime
warnings.filterwarnings("ignore", category=UserWarning)
{CALL_FN}
def span(a, b):
    """The time from one ISO timestamp to another."""
    return str(datetime.fromisoformat(b) - datetime.fromisoformat(a))
offer = None
for q in ("{ESCALATE}", "{NEAR}"):
    s, a = call("/v1/chat", {{"question": q, "session_id": "lesson108-esc", "brain": "langgraph"}})
    print(f"  {{q}}")
    print(f"    {{s}}  brain {{a['brain']}}  tool_calls {{a['tool_calls']}}  model_calls {{a['limits']['model_calls']}}"
          f"  Rs {{a['limits']['cost_inr']}}  case_offer {{a.get('case_offer')}}")
    show(a["answer"])
    offer = offer or a.get("case_offer")
s, d = call("/v1/cases", {{"case_type": offer["case_type"], "summary": "Lesson 5.8 test: please call me about my notice period."}})
print(f"  draft    {{s}}  {{d['status']}} in {{d['queue']}} ({{d['owner']['queue_name']}}),"
      f" expires {{span(d['created_at'], d['expire_at'])}} after it was made")
s, c = call(f"/v1/cases/{{d['case_id']}}/confirm", {{"token": "lesson108-" + uuid.uuid4().hex[:12]}})
print(f"  confirm  {{s}}  {{c['status']}}, due {{span(c['opened_at'], c['due_at'])}} after it opened: {{c['sla_basis']}}")
s, w = call(f"/v1/cases/{{d['case_id']}}/cancel", {{}})
print(f"  cancel   {{s}}  {{w['status']}}, by the person who raised it")
open(os.path.expanduser("~/lesson108_case.txt"), "w").write(d["case_id"])'''

CLARIFY_PY = f'''import json, os, textwrap, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
{CALL_FN}
for session, q in (("lesson108", "{Q_NOTICE}"), ("lesson108", "{Q_REPLY}"), ("lesson108-new", "{Q_REPLY}")):
    s, a = call("/v1/chat", {{"question": q, "session_id": session, "brain": "langgraph"}})
    print(f"  [{{session}}] {{q}}")
    print(f"    {{s}}  tool_calls {{a['tool_calls']}}  model_calls {{a['limits']['model_calls']}}  Rs {{a['limits']['cost_inr']}}"
          f"  citations {{[c['n'] for c in a['citations']]}}")
    show(a["answer"])'''

ROWS_PY = '''import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" AND '
     f'(jsonPayload.event="chat" OR jsonPayload.event="desk_gate") AND timestamp>="{os.environ["SINCE108"]}"')
out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "20",
                      "--format", "json"], capture_output=True, text=True, check=True).stdout
for e in json.loads(out or "[]"):
    j = e["jsonPayload"]
    who = str(j.get("user")).split("@")[0]
    if j["event"] == "desk_gate":
        print(f"  desk_gate  user {who:22} class {j['class']}  method {j['method']}  rules {j['rules_version']}")
    else:
        print(f"  chat       user {who:22} brain {j['brain']}  session {j['session_id']}  tool_calls {j['tool_calls']}"
              f"  model_calls {j['model_calls']}  tokens {j['tokens_in']}/{j['tokens_out']}  cost_usd {j['cost_usd']}")'''

RECORDS_PY = '''import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
db = firestore.Client(project=os.environ["PROJECT"])
cid = open(os.path.expanduser("~/lesson108_case.txt")).read().strip()
c = db.collection("cases").document(cid).get().to_dict()
print(f"  cases/{cid}")
print(f"    {c['case_type']} {c['status']} in {c['queue']}, source {c['source']}, via {c['via']}, opened {c['opened_at'] is not None}")
print(f"    summary {c['summary']!r}  audit_pending {c['audit_pending']}  token_sha256 {len(c['token_sha256'])} hex digits")
me = os.environ["ME"].lower()
r = db.collection("tenants").document("acme").collection("roles").document(me).get().to_dict()
print(f"  tenants/acme/roles/{me.split('@')[0]}@...: {r['roles']}, set by {r['set_by'].split('@')[0]}@...")'''

# ------------------------------------------------------------------ step 8's cells: the switch, the smoke, the run, the reads, the restore
DOC_W = "townhall_2026_q1.md"                 # smoke_approval.py's default document: small, acme's, and make restore brings it back
assert 'DOC = os.environ.get("DOCUMIND_DOC", "townhall_2026_q1.md")' in (KIT / "smoke/smoke_approval.py").read_text(encoding="utf-8")
assert (KIT / "evals/corpus/acme" / DOC_W).is_file()
SWITCH_SH = (SA_FN + "\n"
             'make agent-actions PROJECT="$PROJECT" TENANT=acme AGENT_ACTIONS=approval\n'
             'make roles PROJECT="$PROJECT" TENANT=acme EMAIL="$(sa evalacme)" ROLES=employee,doc_approver')
SMOKE_SH = 'make smoke-approval PROJECT="$PROJECT" TENANT=acme'
APPROVED_ID_PY = '''import json, os, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
req = urllib.request.Request(os.environ["CHAT"] + "/v1/approvals", headers={"Authorization": "Bearer " + os.environ["TOKEN"]})
mine = json.load(urllib.request.urlopen(req, timeout=60))["mine"]
print(next(r["approval_id"] for r in mine if r["status"] == "approved"))'''
WITHDRAW_SH = ('APPROVAL="$(TOKEN="$(etok ui)" ' + heredoc(APPROVED_ID_PY) + '\n)"\necho "approval $APPROVAL"\n'
               'make withdraw-run PROJECT="$PROJECT" APPROVAL="$APPROVAL"\n'
               f'make sources PROJECT="$PROJECT" TENANT_ONLY=acme | grep -E "^source|{DOC_W.rsplit(".", 1)[0]}"')
APPROVALS_PY = '''import datetime as dt, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore, storage
db = firestore.Client(project=os.environ["PROJECT"])
rows = sorted((s.to_dict() for s in db.collection("approvals").where("tenant", "==", "acme").stream()), key=lambda r: r["created_at"])
def who(email):
    """An email's local part, the domain elided; - for nobody."""
    return email.split("@")[0] + "@..." if email else "-"
for r in rows:
    print(f"  approvals/{r['approval_id']}")
    print(f"    {r['status']:10} kind {r['kind']}  waiting {[w['tool'] for w in r['waiting']]}  session {r['session_id']}")
    print(f"    asked by {who(r['requester'])}, decided by {who(r.get('decided_by'))}, audit_pending {r.get('audit_pending')}")
    if r.get("withdrawal"):
        w = r["withdrawal"]
        print(f"    withdrawal {w['tenant']}/{w['name']}, approved by {who(w['approved_by'])}, run by {who(r.get('run_by'))}, {r['status']}")
today = dt.datetime.now(dt.timezone.utc).strftime("%Y/%m/%d")
blobs = storage.Client(project=os.environ["PROJECT"]).list_blobs(os.environ["PROJECT"] + "-audit", prefix=f"{today}/acme/")
events = sorted(b.name.rsplit("/", 1)[1].split("-", 1)[0] for b in blobs)
print("  today's acme events in the audit bucket:", [e for e in events if e.startswith("approval.") or e == "doc.withdraw"])'''
RESTORE_SH = (f'make restore PROJECT="$PROJECT" SOURCE=acme/{DOC_W}\n'
              'make agent-actions PROJECT="$PROJECT" TENANT=acme AGENT_ACTIONS=off')

CELLS = {
    "check": "make approval-check",
    "wired_check": f"{GV} -m unittest commands/tests/test_approval_wired.py -v",
    "switch": SWITCH_SH, "smoke_approval": SMOKE_SH, "withdraw": WITHDRAW_SH, "approvals": heredoc(APPROVALS_PY), "restore": RESTORE_SH,
    "pause": heredoc(PAUSE_PY, GV),
    "sqlite": "rm -f ~/lesson108_threads.db\n" + heredoc(SQLITE_A, GV) + "\n" + heredoc(SQLITE_B, GV),
    "ask": heredoc(ASK_PY, GV),
    "twice": "twice108() {   # one withdrawal paused, then approved; counts the \"approval asked\" lines\n"
             + heredoc(TWICE_PY, GV) + "\n}\ntwice108",
    "move": ("python - <<'PY'   # the Change-it: the \"approval asked\" line moved above interrupt(), nothing else\n"
             + MOVE_PY + "\nPY\ntwice108\n"
             f'git checkout -- services/chat/approval.py && git diff --quiet -- services/chat/approval.py && echo "{RESTORED}"'),
    "roles": ('export CHAT="https://documind-chat-$NUMBER.$REGION.run.app" SINCE108="$(date -u +%FT%TZ)"\n'
              + SA_FN + "\n" + ETOK_FN + "\n"
              f'make roles PROJECT="$PROJECT" TENANT=acme EMAIL="$ME" ROLES={ROLES_SET}'),
    "escalate": heredoc(ESCALATE_PY, prefix='TOKEN="$(etok evalacme)" '),
    "clarify": heredoc(CLARIFY_PY, prefix='TOKEN="$(etok evalacme)" '),
    "rows": heredoc(ROWS_PY),
    "records": 'make cases PROJECT="$PROJECT" TENANT=acme\n' + heredoc(RECORDS_PY),
}
BODIES = (PAUSE_PY, SQLITE_A, SQLITE_B, ASK_PY, TWICE_PY, MOVE_PY, ESCALATE_PY, CLARIFY_PY, ROWS_PY, RECORDS_PY, APPROVED_ID_PY, APPROVALS_PY)
assert all(b in "\n".join(CELLS.values()) for b in BODIES)
for k, body in enumerate(BODIES):
    tree = ast.parse(body)
    assert 'warnings.filterwarnings("ignore", category=UserWarning)' in body, k
    undocumented = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and not ast.get_docstring(n)]
    assert not undocumented, (k, undocumented)          # the IDE demos are made from the cells: every definition says what it does
assert all(make in (KIT / "mk/agents.mk").read_text(encoding="utf-8") for make in ("\nroles: guard-project\n", "\ncases: guard-project\n",
                                                                                  "\napproval-check:\n", "\nagent-actions: guard-project\n",
                                                                                  "\nwithdraw-run: guard-project\n", "\nsmoke-approval: guard-project\n"))
assert "\nrestore: guard-project\n" in (KIT / "mk/lifecycle.mk").read_text(encoding="utf-8") and "\nsources: guard-project\n" in (KIT / "mk/lifecycle.mk").read_text(encoding="utf-8")

# ------------------------------------------------------------------ the lane cells, checked on the kit's own chat service
# Their outputs are the author's recordings (RUN_LIST.md). Here each cell runs against agent.py's chat() with the real
# LangGraph brain on a scripted model, desk.py's chat door and case routes, shared/cases.py and commands/desk_ops.py,
# over commands/tests/test_cases.py's fake Firestore and audit bucket, so a cell that would fail on a lane fails the build.
tc = load("kit_test_cases_108", "commands/tests/test_cases.py")
logging.getLogger().handlers.clear()
import agent  # noqa: E402  (the chat service; its lifespan never runs here, so no checkpointer database is opened)
import desk  # noqa: E402
logging.getLogger().handlers.clear()                          # agent.py's basicConfig would print every row here
logging.getLogger().setLevel(logging.WARNING)
LANE_ID, ME = "documind-ai-stand-in", "you@example.com"
db = tc.FakeDB()
EVALACME = f"documind-evalacme-sa@{LANE_ID}.iam.gserviceaccount.com"
UI_SA, EVALZETA = f"documind-ui-sa@{LANE_ID}.iam.gserviceaccount.com", f"documind-evalzeta-sa@{LANE_ID}.iam.gserviceaccount.com"
ROSTER = {ME: "acme", EVALACME: "acme", UI_SA: "acme", EVALZETA: "zeta"}      # 5.6's eval accounts, and 5.1's ui-sa on acme
for email, tenant in ROSTER.items():
    db.collection("tenants").document(tenant).collection("members").document(email).set({"email": email})
db.collection("tenant_settings").document("acme").set({"case_queues": tc.queues_file("acme")})
roles.set_roles(db, "acme", ME, ["employee", "grc_member", "ic_member:hyderabad", "ic_member:pune"], ME, audit=False)   # 5.6's
EVENTS, ROWS = [], []


class Rows(logging.Handler):
    """The chat service's log rows, as Cloud Logging would keep them."""

    def emit(self, record):
        """Keep a JSON row; any other line is not a row."""
        try:
            ROWS.append({"jsonPayload": json.loads(record.getMessage()), "resource": {"labels": {"service_name": "documind-chat"}}})
        except ValueError:
            pass


for name in ("documind.chat.agent", "documind.chat.desk", "documind.chat.approval_routes"):
    lg = logging.getLogger(name)
    lg.addHandler(Rows())
    lg.setLevel(logging.INFO)
    lg.propagate = False


from fastapi import Request  # noqa: E402


def stand_in_caller(request: Request):
    """agent.caller() for the stand-in: the bearer token names the account."""
    auth = request.headers.get("authorization") or ""
    return {"email": {"evalacme": EVALACME, "ui": UI_SA, "evalzeta": EVALZETA}.get(auth[7:], ""), "assertion": None}


SCRIPT = (kt.turn([("retrieve", {"query": "contact HR payroll"})], "Payroll questions go to the People team [1].")
          + kt.turn([("retrieve", {"query": "notice period"})], "It depends on your grade and status: which applies to you? [1]")
          + kt.turn([("retrieve", {"query": "probation notice period"})], "During probation it is 15 days [1].")
          + kt.turn([("retrieve", {"query": "probation"})], "Probation lasts six months [1]."))
STACK = contextlib.ExitStack()
for p in (patch.object(cases, "_fs", lambda: tc.FS), patch.object(tc.audit_log, "storage", tc._storage(EVENTS)),
          patch.object(tc.audit_log, "_bucket", None), patch.dict(os.environ, {"AUDIT_BUCKET": f"{LANE_ID}-audit"}),
          patch.object(desk, "PROFILE", "gcp"), patch.object(desk, "_client", lambda: db),
          patch.object(desk, "settings", lambda t: dict(db.docs.get(f"tenant_settings/{t}") or {})),
          patch.object(desk, "CHECKED", types.SimpleNamespace(tenants=lambda: _no_tenants())),
          patch.object(agent, "tenant_for", lambda e: ROSTER.get((e or "").lower())),
          patch.dict(desk._hooks, {"caller": stand_in_caller, "tenant_for": lambda e: ROSTER.get((e or "").lower())}),
          patch.object(approval_routes, "PROFILE", "gcp"),
          patch.dict(approval_routes._hooks, {"caller": stand_in_caller, "tenant_for": lambda e: ROSTER.get((e or "").lower())})):
    STACK.enter_context(p)


async def _no_tenants():
    """No company on the stand-in lane has the model check on."""
    return frozenset()


agent.app.dependency_overrides[agent.caller] = stand_in_caller
agent.app.state.checkpointer = InMemorySaver()
agent.app.state.brains = {"langgraph": brains.LangGraphBrain(agent.app.state.checkpointer, llm=kt.scripted(SCRIPT))}
from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(agent.app)
LOCK = threading.Lock()
BRIDGE_ERRORS = []


class Bridge(BaseHTTPRequestHandler):
    """HTTP in front of the in-process chat service, so the cells' urllib calls reach it."""

    def log_message(self, *a):
        """No access log in the build's output."""

    def _go(self):
        """Hand the request to the in-process service and send its answer back."""
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n) if n else None
        try:
            with LOCK:
                r = client.request(self.command, self.path, content=body,
                                   headers={k: v for k, v in self.headers.items() if k.lower() not in ("host", "content-length")})
            status, data, kind = r.status_code, r.content, r.headers.get("content-type", "application/json")
        except Exception as e:  # noqa: BLE001 - the cell then fails on a 500, and the build says why, instead of hanging
            BRIDGE_ERRORS.append(repr(e))
            status, data, kind = 500, json.dumps({"detail": repr(e)}).encode(), "application/json"
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    do_GET = do_POST = _go


srv = ThreadingHTTPServer(("127.0.0.1", 0), Bridge)
threading.Thread(target=srv.serve_forever, daemon=True).start()
LANE_ENV = {"CHAT": f"http://127.0.0.1:{srv.server_address[1]}", "TOKEN": "evalacme", "PROJECT": LANE_ID, "ME": ME,
            "SINCE108": "YYYY-MM-DDTHH:MM:SSZ"}
STANDIN = {}


def ops(*args) -> str:
    """commands/desk_ops.py, as make runs it, against the stand-in's Firestore."""
    fs = types.SimpleNamespace(Client=lambda project=None: db, SERVER_TIMESTAMP="SERVER_TIMESTAMP")
    with tc.cloud_modules(firestore=fs), patch.dict(os.environ, {"DOCUMIND_OPERATOR": ME}), redirect_stdout(io.StringIO()) as out:
        assert tc.desk_ops.main(["--project", LANE_ID, *args]) == 0
    return out.getvalue()


def run_lane(body: str) -> str:
    """A lane cell against the stand-in chat service; the bridge's own failures are named if the cell fails."""
    try:
        return run_cell(body, env=LANE_ENV)
    except AssertionError:
        raise AssertionError(f"the chat service raised: {BRIDGE_ERRORS}") from None


STANDIN["roles"] = ops("roles", "--tenant", "acme", "--email", ME, "--set", ROLES_SET)
assert json.loads(STANDIN["roles"])["granted"] == ["people_ops"] and json.loads(STANDIN["roles"])["revoked"] == []
STANDIN["escalate"] = run_lane(ESCALATE_PY)
esc = STANDIN["escalate"]
assert f"  {ESCALATE}\n    200  brain desk_gate  tool_calls []  model_calls 0  Rs 0.0  case_offer {{'case_type': 'human_requested'}}\n" in esc, esc
assert f"  {NEAR}\n    200  brain langgraph  tool_calls ['retrieve']  model_calls 2" in esc and "case_offer None" in esc, esc
assert f"  draft    200  draft in people ({PEOPLE_NAME}), expires 0:{DRAFT_MIN}:00 after it was made" in esc, esc
assert (f"  confirm  200  open, due {SLA_PEOPLE} days, 0:00:00 after it opened: the company's own target: {SLA_PEOPLE} days "
        "(case_queues.people.sla_days)") in esc, esc
assert "  cancel   200  withdrawn, by the person who raised it" in esc, esc
assert " ".join(TEMPLATE.split())[:60] in " ".join(esc.split()), esc
STANDIN["clarify"] = run_lane(CLARIFY_PY)
assert STANDIN["clarify"].count("    200  tool_calls ['retrieve']  model_calls 2") == 3 and "citations [1]" in STANDIN["clarify"]
KEPT = [r for r in ROWS if r["jsonPayload"].get("event") in ("chat", "desk_gate")]     # the cell's filter, as Logging applies it
assert 'jsonPayload.event="chat" OR jsonPayload.event="desk_gate"' in ROWS_PY
fake_sub = types.ModuleType("subprocess")
fake_sub.run = lambda cmd, **kw: types.SimpleNamespace(stdout=json.dumps(KEPT), stderr="", returncode=0)
with patch.dict(sys.modules, {"subprocess": fake_sub}), redirect_stdout(io.StringIO()) as so, patch.dict(os.environ, LANE_ENV):
    exec(compile(ROWS_PY, "<rows>", "exec"), {"__name__": "__cell__"})
STANDIN["rows"] = so.getvalue()
assert STANDIN["rows"].count("  desk_gate  user documind-evalacme-sa") == 1 and "class human_requested  method rule" in STANDIN["rows"]
assert STANDIN["rows"].count("  chat       user documind-evalacme-sa") == 4 and "session lesson108-new" in STANDIN["rows"]
STANDIN["cases"] = ops("cases", "--tenant", "acme")
fake_fs = types.SimpleNamespace(Client=lambda project=None: db)
with tc.cloud_modules(firestore=fake_fs), patch.dict(os.environ, {**LANE_ENV, "HOME": str(T), "USERPROFILE": str(T)}), \
        redirect_stdout(io.StringIO()) as so:
    exec(compile(RECORDS_PY, "<records>", "exec"), {"__name__": "__cell__"})
STANDIN["records"] = so.getvalue()
assert "    human_requested withdrawn in people, source button, via direct, opened True" in STANDIN["records"], STANDIN["records"]
assert f"'{ROLES_SET.replace(',', chr(39) + ', ' + chr(39))}'" in STANDIN["records"] and "set by you@..." in STANDIN["records"]
assert [e["action"] for e in EVENTS] == ["role.grant", "case.open", "case.close"], [e["action"] for e in EVENTS]
assert EVENTS[-1]["meta"] == {"status": "withdrawn", "from": "open", "by": "requester"}, EVENTS[-1]   # the requester withdrew it
assert EVENTS[0]["target"]["roles"] == ["people_ops"]                           # one grant event, naming people_ops

# ------------------------------------------------------------------ step 8 on the stand-in: the switch, the smoke in process, the run's checks, the reads
# The switch and the role, as make agent-actions and make roles write them (desk_ops.py on the fake Firestore).
STANDIN["switch"] = ops("desk", "--tenant", "acme", "--actions", "approval") + ops("roles", "--tenant", "acme", "--email", EVALACME,
                                                                                    "--set", "employee,doc_approver")
_sw, _gr = (json.loads(x) for x in STANDIN["switch"].splitlines()[:2])
assert (_sw["tenant"], _sw["agent_actions"], _sw["desk_gate"]) == ("acme", "approval", "rules") and "note" in _sw, _sw
assert (_gr["granted"], _gr["after"]) == (["doc_approver"], ["doc_approver", "employee"]), _gr
assert db.docs["tenant_settings/acme"]["agent_actions"] == "approval" and EVENTS[-1]["action"] == "role.grant"
# The approval brain on the service's checkpointer, replying as scripted: two withdrawals, each paused, then each resume.
WIRED_SCRIPT = (kt.turn([("withdraw_document", {"name": DOC_W})],
                        "Approved and queued: the operator runs make withdraw-run; until then the document stays in search.")
                + kt.turn([("withdraw_document", {"name": DOC_W})],
                          "Nothing was withdrawn: the second person rejected it, as the document is still in force."))
agent.app.state.approval_brain = approval_routes.ApprovalBrain(agent.app.state.checkpointer, llm=kt.scripted(WIRED_SCRIPT))
# make smoke-approval, in process: the smoke module on the bridge, its tokens the stand-in's names for the three accounts.
with patch.dict(os.environ, {"DOCUMIND_CHAT_URL": LANE_ENV["CHAT"], "DOCUMIND_PROJECT": LANE_ID, "DOCUMIND_TENANT": "acme",
                             "DOCUMIND_DOC": DOC_W}):
    sm = load("kit_smoke_approval_108", "smoke/smoke_approval.py")
sm.token_as = lambda sa, audience: {EVALACME: "evalacme", UI_SA: "ui", EVALZETA: "evalzeta"}.get(sa)
n_rows = len(ROWS)
with redirect_stdout(io.StringIO()) as so:
    _rc = sm.main()
STANDIN["smoke_approval"] = so.getvalue()
assert _rc == 0 and "[FAIL]" not in STANDIN["smoke_approval"], STANDIN["smoke_approval"]
SMOKE_PASSES = re.findall(r"\[PASS\] ([a-z0-9 -]+?)  ", STANDIN["smoke_approval"])
assert SMOKE_PASSES == ["paused", "held", "self-approval refused", "stranger 404", "approver inbox", "approved", "decided once",
                        "rejected", "my records"], SMOKE_PASSES
assert "  9 passed, 0 failed" in STANDIN["smoke_approval"] and f"make restore PROJECT={LANE_ID} SOURCE=acme/{DOC_W}" in STANDIN["smoke_approval"]
APPROVED = re.search(r"\[PASS\] paused  approval ([0-9a-f]{32}) ", STANDIN["smoke_approval"]).group(1)
assert f"make withdraw-run PROJECT={LANE_ID} APPROVAL={APPROVED}" in STANDIN["smoke_approval"]
WIRED_ROWS = [r["jsonPayload"] for r in ROWS[n_rows:]]
assert [(r["event"], r.get("surface")) for r in WIRED_ROWS].count(("chat", "approval")) == 2        # the two resumed turns
assert [r["status"] for r in WIRED_ROWS if r.get("surface") == "approval"] == ["approved", "rejected"]
assert [r["decided_by"] for r in WIRED_ROWS if r.get("surface") == "approval"] == [EVALACME, EVALACME]
assert [(r["event"], r.get("surface"), r.get("brain")) for r in WIRED_ROWS].count(("chat", "chat", "langgraph")) == 2   # the two pauses
WIRED_EVENTS = [e["action"] for e in EVENTS if e["action"].startswith("approval.")]
assert WIRED_EVENTS == ["approval.request", "approval.approve", "approval.request", "approval.reject"], WIRED_EVENTS
assert all(e["actor"]["email"] in (UI_SA, EVALACME) and e["target"]["document"] == f"acme/{DOC_W}" for e in EVENTS if e["action"].startswith("approval."))
recs = sorted((d for p, d in db.docs.items() if p.startswith("approvals/")), key=lambda d: d["created_at"])
assert [r["status"] for r in recs] == ["approved", "rejected"] and recs[0]["approval_id"] == APPROVED
assert recs[0]["withdrawal"]["approved_by"] == EVALACME and recs[0]["withdrawal"]["requested_by"] == UI_SA and recs[0]["audit_pending"] == []
# the run's first line (the approved record's id, read as the requester), then reconcile.py --approved's checks, dry
STANDIN["approved_id"] = run_cell(APPROVED_ID_PY, env={**LANE_ENV, "TOKEN": "ui"})
assert STANDIN["approved_id"].strip() == APPROVED, STANDIN["approved_id"]
for p in (str(KIT / "services/ingest"),):
    if p not in sys.path:
        sys.path.insert(0, p)
rc_mod = load("kit_reconcile_108", "services/ingest/reconcile.py")
fake_fs = types.SimpleNamespace(Client=lambda project=None: db, SERVER_TIMESTAMP="SERVER_TIMESTAMP", DELETE_FIELD=tc.DELETE)
TODAY = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y/%m/%d")


class _Blob:
    """One object of the stand-in audit bucket, by name alone."""

    def __init__(self, name):
        self.name = name


def _list_blobs(bucket, prefix=""):
    """The stand-in bucket's objects under a prefix: the events the fake bucket collected, at audit_log.emit()'s paths."""
    return [_Blob(f"{TODAY}/{e['actor'].get('tenant_id', '_')}/{e['action']}-{e['id']}.json") for e in EVENTS
            if f"{TODAY}/{e['actor'].get('tenant_id', '_')}/".startswith(prefix)]


fake_gcs = types.SimpleNamespace(Client=lambda project=None: types.SimpleNamespace(list_blobs=_list_blobs, bucket=lambda name: None))
with tc.cloud_modules(firestore=fake_fs, storage=fake_gcs), patch.object(sys, "argv", ["reconcile.py", "--project", LANE_ID, "--approved", APPROVED]), \
        redirect_stdout(io.StringIO()) as so:
    _rc = rc_mod.main()
STANDIN["withdraw_dry"] = so.getvalue()
assert _rc == 0 and STANDIN["withdraw_dry"].startswith(f"would run approval {APPROVED}: withdraw acme/{DOC_W}, asked for by {UI_SA}, approved by {EVALACME}; the checks pass"), STANDIN["withdraw_dry"]
with tc.cloud_modules(firestore=fake_fs, storage=fake_gcs), patch.object(sys, "argv", ["reconcile.py", "--project", LANE_ID, "--approved", recs[1]["approval_id"]]), \
        redirect_stdout(io.StringIO()) as so:
    _rc = rc_mod.main()
assert _rc == 1 and json.loads(so.getvalue()) == {"event": "reconcile_approved_refused", "approval": recs[1]["approval_id"], "status": 409,
                                                   "why": f"approval {recs[1]['approval_id']} is rejected, not approved: nothing to run"}, so.getvalue()
# the direct reads: the records from Firestore and today's events in the bucket (on the stand-in the first record is still approved)
with tc.cloud_modules(firestore=fake_fs, storage=fake_gcs), patch.dict(os.environ, {**LANE_ENV, "HOME": str(T), "USERPROFILE": str(T)}), \
        redirect_stdout(io.StringIO()) as so:
    exec(compile(APPROVALS_PY, "<approvals>", "exec"), {"__name__": "__cell__"})
STANDIN["approvals"] = so.getvalue()
assert STANDIN["approvals"].count("  approvals/") == 2 and "    approved   kind approval  waiting ['withdraw_document']" in STANDIN["approvals"]
assert "    rejected   kind approval" in STANDIN["approvals"] and f"    withdrawal acme/{DOC_W}, approved by documind-evalacme-sa@..., run by -, approved" in STANDIN["approvals"]
assert "asked by documind-ui-sa@..., decided by documind-evalacme-sa@..., audit_pending []" in STANDIN["approvals"]
assert STANDIN["approvals"].rstrip().endswith("['approval.approve', 'approval.reject', 'approval.request', 'approval.request']"), STANDIN["approvals"]
# the switch back off, as the last cell writes it
STANDIN["off"] = ops("desk", "--tenant", "acme", "--actions", "off")
assert json.loads(STANDIN["off"])["agent_actions"] == "off" and not approval_routes.switched_on("acme")
STACK.close()
srv.shutdown()
shutil.rmtree(T, ignore_errors=True)
if os.environ.get("STANDIN"):
    for k, v in STANDIN.items():
        print(f"===== stand-in {k}\n{v}")

REC = {k: pb.recorded(LESSON, f"{k}.txt") for k in ("roles", "escalate", "clarify", "rows", "records",
                                                    "switch", "smoke_approval", "withdraw", "approvals", "restore")}
OUT.update(REC)

# ------------------------------------------------------------------ what the lane's runs cost: shared/prices.py and limits.py
assert prices.DEFAULT_MODEL == "gemini-3.6-flash" and brains.MODEL == "gemini-3.6-flash"
prices.PROFILE = "gcp"                     # list prices, whatever DOCUMIND_PROFILE the build's own shell carries
RAG_ANSWER_INR = prices.inr(prices.usd(prices.DEFAULT_MODEL, 2000, 300))     # the course's typical answer, as 4.3 prices it
assert f"{RAG_ANSWER_INR:.2f}" == "0.45"
N_AGENT_TURNS = 1 + 3                      # the near miss, and the three clarifying turns; the door's turn calls no model

# ------------------------------------------------------------------ the windows
def bash_window(label: str, code: str) -> str:
    """A command window with a copy button."""
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    """An expected-output window, read only."""
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "check": "run in the operator shell, in the kit (the kit's own tests, offline; the first run makes or completes ~/graph-venv)",
    "pause": "run in the operator shell, in the kit (a withdrawal paused, refused to its requester, approved by a second person; no network, no model)",
    "sqlite": "run in the operator shell, in the kit (one process pauses the turn into a file, a second process resumes it)",
    "ask": "run in the operator shell, in the kit (a clarifying question, answered only by the person who asked)",
    "twice": "run in the operator shell, in the kit (defines twice108, then runs it on the kit as it is)",
    "move": "run in the operator shell, in the kit (the Change-it: one line moved, twice108 again, then the kit restored)",
    "roles": "run in the operator shell, in the kit (the names the lane steps use, then people_ops beside your four roles)",
    "escalate": "run in the operator shell, in the kit (a request for a person and a near miss, as documind-evalacme-sa; then the case)",
    "clarify": "run in the operator shell, in the kit (a question, the reply on the same session, the reply in a new session)",
    "rows": "run in the operator shell, in the kit (the chat service's chat and desk_gate rows since step 3; reads only)",
    "records": "run in the operator shell, in the kit (acme's open cases, then step 6's case and your role document, from Firestore)",
    "wired_check": "run in the operator shell, in the kit (the wired approval's own tests, offline, in ~/graph-venv from step 4)",
    "switch": "run in the operator shell, in the kit (acme's agent_actions to approval; doc_approver for documind-evalacme-sa)",
    "smoke_approval": "run in the operator shell, in the kit (the whole flow once, against your chat service; about Rs 10-15)",
    "withdraw": "run in the operator shell, in the kit (the approved record's id, your run of it, and acme's sources)",
    "approvals": "run in the operator shell, in the kit (acme's approval records and today's approval events, from Firestore and the bucket)",
    "restore": "run in the operator shell, in the kit (the document back, and acme's switch off)",
}
LANE = "(the author's lane, recorded: your ids, words, tokens and rupees differ)"
OUT_LABELS = {
    "check": "(the kit's test file run here on the chat image's pins; a first run prints pip's lines above these)",
    "pause": "(this cell run on the kit)",
    "sqlite": "(this cell run on the kit: two processes, one file)",
    "ask": "(this cell run on the kit)",
    "twice": "(this cell run on the kit)",
    "move": "(this cell run on a copy of the kit, as your kit would print it)",
    "wired_check": "(the kit's test file run here on the chat image's pins)",
    "roles": LANE, "escalate": LANE, "clarify": LANE, "rows": LANE, "records": LANE,
    "switch": LANE, "smoke_approval": LANE, "withdraw": LANE, "approvals": LANE, "restore": LANE,
}
assert set(CELLS) == set(OUT) == set(CELL_LABELS) == set(OUT_LABELS), set(CELLS) ^ set(OUT)
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: the kit's own transitions, replayed
WDATA = {"people": {"asha": "Asha, who asked", "ravi": "Ravi, a second person", "meena": "Meena, another person"},
         "kinds": {"approve": "approve", "reject": f"reject: “{REASON}”", "respond": f"respond: “{ANSWER}”"},
         "hows": {"decide": "through decide()", "role": "decide(), may_approve: Ravi only",
                  "straight": "straight to the graph"},
         "after": AFTER, "scen": W}
UI_JS = r"""var root = document.getElementById('hl'); if (!root) return;
  var D = %s, $ = function(id){ return document.getElementById(id); }, state = null;
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }
  function fill(id, obj){ var sel = $(id); Object.keys(obj).forEach(function(k){ var o = document.createElement('option'); o.value = k; o.textContent = obj[k]; sel.appendChild(o); }); }
  Object.keys(D.scen).forEach(function(k){ var o = document.createElement('option'); o.value = k; o.textContent = D.scen[k].label; $('hl-s').appendChild(o); });
  fill('hl-who', D.people); fill('hl-kind', D.kinds); fill('hl-how', D.hows);
  function lights(on, wait){ ['__start__', 'agent', 'approve', 'tools', '__end__'].forEach(function(n){ $('hl-' + n).className = 'hl-node' + (n === wait ? ' wait' : n === on ? ' on' : ''); }); }
  function line(kind, text){ $('hl-log').insertAdjacentHTML('beforeend', '<li class="' + kind + '">' + esc(text) + '</li>'); }
  function shown(r){ return r[0] + ' ' + r[1] + ': ' + r[2]; }
  function path(p){ return 'path ' + p.map(function(n){ return !n.length ? 'END' : n.length > 1 ? n[0] + ' ×' + n.length : n[0]; }).join(' -> '); }
  function start(){
    var s = D.scen[$('hl-s').value]; state = {s: s, done: !s.pauses}; $('hl-log').innerHTML = '';
    line('user', '__start__: the question arrives: "' + s.question + '"');
    line('ai', 'agent: the model asks for ' + s.calls.join(' and '));
    if (s.pauses) {
      line('pause', 'approve: route sent the turn here. interrupt() stops it, and the checkpointer keeps it' + (s.calls.length > 1 ? '; the call beside it waits too, and has not run' : ''));
      $('hl-wait').innerHTML = '<b class="h">paused() lists</b>' + s.waiting.map(function(w){ return esc(w.tool + ' ' + JSON.stringify(w.args) + ', call ' + w.call_id + ', takes ' + w.allowed_decisions.join(' or ') + ', asked by ' + w.requester) + '<br>' + esc('"' + w.description + '"'); }).join('<br>');
      $('hl-wait').hidden = false; lights('', 'approve'); $('hl-out').textContent = 'paused: waiting for a decision';
    } else {
      s.results.forEach(function(r){ line('tool', 'tools: ' + shown(r)); });
      line('ai', 'agent: the model reads the results and answers'); line('skip', '__end__: nothing waited');
      $('hl-wait').hidden = true; lights('__end__', ''); $('hl-out').textContent = path(s.path);
    }
    $('hl-go').disabled = false;
  }
  function send(){
    var s = state.s, who = $('hl-who').value, kind = $('hl-kind').value, how = $('hl-how').value;
    var by = D.people[who].split(',')[0];
    if (state.done) { line('err', by + ' sends ' + kind + ': LookupError, 409 - ' + D.after); $('hl-out').textContent = 'nothing waits: the turn has ended'; return; }
    var r = s.outcomes[who + '|' + kind + '|' + how];
    if (r.kind === 'refused') {
      line('err', by + ' sends ' + kind + ' through decide(): ' + r.error + ', a route\'s ' + r.status + ' - ' + r.message + '. Nothing ran; the same call still waits');
      $('hl-out').textContent = 'still paused';
    } else if (r.kind === 'asked_again') {
      line('err', by + ' sends ' + kind + ' straight to the graph: the approve node runs again, finds "' + r.refused.join('; ') + '", and calls interrupt() again');
      $('hl-out').textContent = 'still paused: the node asked again, saying why';
    } else {
      line('pause', 'approve: ' + by + ' sends ' + kind + (how === 'straight' ? ' straight to the graph' : ' through decide()') + '; the node runs again from its first line, and interrupt() returns the decision');
      r.results.forEach(function(x){ line(x[1] === 'error' ? 'err' : 'tool', (x[0] === s.waiting[0].tool && kind !== 'approve' ? 'approve: ' : 'tools: ') + shown(x)); });
      if (r.withdrawn.length) line('tool', 'withdraw() was called with ' + JSON.stringify(r.withdrawn[0]));
      else if (s.waiting[0].tool === 'withdraw_document') line('skip', 'withdraw() was never called: nothing was withdrawn');
      line('ai', 'agent: the model reads the results and answers'); line('skip', '__end__: nothing waits now');
      $('hl-wait').hidden = true; lights('__end__', ''); state.done = true;
      $('hl-out').textContent = path(r.path);
    }
  }
  $('hl-s').addEventListener('change', start); $('hl-again').addEventListener('click', start); $('hl-go').addEventListener('click', send);
  $('hl-s').value = 'withdraw'; start();""" % json.dumps(WDATA, ensure_ascii=False)

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

# a JS check: the widget's lookup keys are exactly the transitions computed above
node = shutil.which("node")
if node:
    probe = Path(tempfile.mkdtemp(prefix="lesson108-js-")) / "keys.js"
    probe.write_text("var D = " + json.dumps(WDATA) + ";\nvar n = 0; Object.keys(D.scen).forEach(function(k){ var s = D.scen[k];"
                     " if (s.pauses) ['asha','ravi','meena'].forEach(function(w){ ['approve','reject','respond'].forEach(function(d){"
                     " ['decide','role','straight'].forEach(function(h){ if (!s.outcomes[w + '|' + d + '|' + h]) throw new Error(k + w + d + h); n++; }); }); }); });"
                     "\nconsole.log(n);\n", encoding="utf-8")
    r = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8")
    shutil.rmtree(probe.parent, ignore_errors=True)
    assert r.returncode == 0 and int(r.stdout.strip()) == N_TRANSITIONS, (r.stdout, r.stderr)

# ------------------------------------------------------------------ the numbers the prose states
WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven",
         12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen",
         19: "nineteen", 20: "twenty", 21: "twenty-one", 22: "twenty-two", 23: "twenty-three", 24: "twenty-four"}
PART_A, PART_C = pb.part(LESSON, "a"), pb.part(LESSON, "c")
N_DEFS = PART_A.split('id="s2"', 1)[1].count("<tr><td><strong>")             # the definitions table's rows
N_CHECKS = len(re.findall(r"<tr><td>\d+</td>", PART_C.split('id="s10"', 1)[1]))  # the checklist's rows
assert N_DEFS in WORDS and N_CHECKS in WORDS, (N_DEFS, N_CHECKS)
STATS = {
    "N_DEFS": WORDS[N_DEFS].capitalize(), "N_CHECKS": WORDS[N_CHECKS].capitalize(),
    "N_AP_LINES": str(N_AP_LINES), "N_TESTS": str(N_TESTS), "N_WIRING": WORDS[N_WIRING], "N_APPROVALS": WORDS[N_APPROVALS],
    "N_TRANSITIONS": str(N_TRANSITIONS), "N_AG_EDGES": WORDS[N_AG_EDGES], "N_LG_EDGES": WORDS[N_LG_EDGES],
    "NAME_MAX": str(approval.NAME_MAX), "REASON_MAX": str(approval.REASON_MAX), "ANSWER_MAX": f"{approval.ANSWER_MAX:,}",
    "PIN_LC": PINS["langchain"], "PIN_LG": PINS["langgraph"], "PIN_SQLITE": PINS["langgraph-checkpoint-sqlite"],
    "CP_ONE_A": str(CHECKPOINTS["one"][0]), "CP_ONE_B": str(CHECKPOINTS["one"][1]),
    "CP_TWO_A": str(CHECKPOINTS["two"][0]), "CP_TWO_B": str(CHECKPOINTS["two"][1]),
    "SLA_PEOPLE": str(SLA_PEOPLE), "PEOPLE_NAME": PEOPLE_NAME, "DRAFT_MIN": str(DRAFT_MIN),
    "ESCALATE": html.escape(ESCALATE), "NEAR": html.escape(NEAR), "Q_NOTICE": html.escape(Q_NOTICE), "Q_REPLY": html.escape(Q_REPLY),
    "CLARIFY_Q": html.escape(CLARIFY_Q), "REASON": html.escape(REASON),
    "TEMPLATE": html.escape(TEMPLATE).replace("\n\n", " "), "OWN": html.escape(OWN),
    "RAG_INR": f"{RAG_ANSWER_INR:.2f}", "TURN_BUDGET": f"{limits.TURN_BUDGET_INR:g}", "MAX_CALLS": str(limits.MAX_MODEL_CALLS),
    "N_AGENT_TURNS": WORDS[N_AGENT_TURNS], "MOVE_FROM": str(MOVE_FROM), "MOVE_TO": str(MOVE_TO),
    "N_BLOCKED": WORDS[len(tools.BLOCKED)],
    "N_WIRED_TESTS": str(N_WIRED_TESTS), "TTL_H": f"{approvals.TTL_H:g}", "DOC": DOC_W,
    "STATUSES": ", ".join(f"<code>{s}</code>" for s in approvals.STATUSES),
}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(json.dumps(WDATA, indent=1, ensure_ascii=False))
    print(STATS)
    sys.exit(0)


def subst(text: str) -> str:
    """Every %%NAME%% in a part: a window, or a number the build computed."""
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {N_TRANSITIONS} transitions through approval.py on a scripted model, every refusal checked with paused() | "
      f"{N_TESTS} + {N_WIRED_TESTS} kit tests OK | the offline cells run on the kit | the {len(REC)} lane cells run on the kit's chat "
      f"service, door, case and approval routes over stand-ins (the smoke in process: {len(SMOKE_PASSES)} passes); their outputs are the "
      "author's recordings")
