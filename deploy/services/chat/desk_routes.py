"""The DocuMind Desk's routes (workshop lesson 10.4): one row per route, in code, which the router and the desk graph
both read.

    handbook       the company's own HR handbook                  direct: one rag-api answer over [policy]
    statute        what Indian law says, as text in the corpus    direct: one rag-api answer over [statute, guidance]
    case           something a person must handle                 code: the case queue (shared/cases.py)
    clarify        too short or too vague to place                code: one question, two buttons
    out_of_scope   anything else                                  code: a fixed reply and a case offer

Code fixes each desk's retrieval filter from its row; the model never chooses or widens it. A direct desk returns
rag-api's own cited answer, as the direct brain does (services/chat/brains.py), so the chat service calls no model of
its own there: its model column is None. When the router says a figure is asked (needs_calculation), an answer desk
runs in agent mode instead (services/chat/desk_agent.py): agent_model reads this turn's passages through a retrieve
held to the same filter and works the figure out with the desk's calculators (shared/desk_calc.py), its tools. No
tool names a desk, and none can hand a turn to another desk: the parts of a turn are a list the router fixes and the
graph's next_part node pops (services/chat/desk_graph.py).

A desk's roles are the roles that open it. They repeat shared/roles.py's DESKS read the other way round, and
commands/tests/test_desk.py holds the two equal: a leaver, and a person whose roles could not be read, reach the case
desk only.

The Desk is not a fifth brain: it adds nothing to brains.BRAINS or to ChatRequest's brain values, so /v1/chat is
unchanged. rag-api's usage rows name it by the brain label "desk" (services/rag-api/schemas.py).

PROMPT_EXEMPLARS are the classifier's examples: tenant-neutral questions from evals/routes.jsonl's dev rows (the test
holds each one equal to its row), with no company name and no figure, at most twelve. Every row there is still a model
draft, so these are starting examples until people write and review the rows; case and clarify have none until such
rows exist. The router's eval leaves the groups of these rows out of a live score, because the prompt has seen them.
"""
from __future__ import annotations

from shared.desk_calc import for_desk

AGENT_MODEL = "gemini-3.6-flash"        # agent mode, on location global (Gemini 3.x generation is not regional)

ROUTES = ("handbook", "statute", "case", "clarify", "out_of_scope")     # what the classifier may answer
ANSWER_DESKS = ("handbook", "statute")                                  # the desks that retrieve
# What a decision's route may also be: the checks' outcomes, and the router's own failure.
OUTCOMES = ("not_covered", "denied", "fallback")

DESKS: dict[str, dict] = {
    "handbook": {
        "label": "the company handbook",
        "description": ("the company's own HR handbook and policies: leave, notice periods, travel and expenses, "
                        "payroll dates, IT and security rules, approvals, remote work"),
        "doc_types": ("policy",),
        "mode": "direct",                   # agent mode when a figure is asked: agent_model, with tools
        "model": None,
        "agent_model": AGENT_MODEL,
        "tools": ("retrieve",) + for_desk("handbook"),
        "roles": ("employee",),
        "queue_key": "clause_prefixes",     # a case it hands over goes to the queue its clause's prefix names
        "chip": "Ask what the company handbook says",
    },
    "statute": {
        "label": "the law",
        "description": ("what Indian law says: the Labour Codes, the Acts they repeal, the ministry's compliance "
                        "handbook, the DPDP Act, the IT Act, the CGST Act; how a legal process works"),
        "doc_types": ("statute", "guidance"),
        "mode": "direct",
        "model": None,
        "agent_model": AGENT_MODEL,
        "tools": ("retrieve",) + for_desk("statute"),
        "roles": ("employee",),
        "queue_key": None,
        "chip": "Ask what the law says",
    },
    "case": {
        "label": "a person",
        "description": ("something a person must handle: harassment or unfair treatment that happened to the asker, "
                        "the asker's own personal data, unpaid dues after leaving, a request to talk to a person"),
        "doc_types": (),
        "mode": "code",
        "model": None,
        "agent_model": None,
        "tools": (),
        "roles": ("employee", "leaver", "unread"),
        "queue_key": None,
        "chip": "Raise a case",
    },
    "clarify": {
        "label": "a question back",
        "description": "too short or too vague to place on one desk",
        "doc_types": (),
        "mode": "code",
        "model": None,
        "agent_model": None,
        "tools": (),
        "roles": ("employee",),
        "queue_key": None,
        "chip": None,
    },
    "out_of_scope": {
        "label": "another system",
        "description": ("anything else: an action in another system, the asker's own HR record, contracts, invoices, "
                        "the company's finances or results, general chat"),
        "doc_types": (),
        "mode": "code",
        "model": None,
        "agent_model": None,
        "tools": (),
        "roles": ("employee",),
        "queue_key": None,
        "chip": None,
    },
}

# (row id in evals/routes.jsonl, route, question): the classifier's examples. At most twelve.
PROMPT_EXEMPLARS: tuple[tuple[str, str, str], ...] = (
    ("lk-03", "handbook", "How many days of earned leave can I carry forward?"),
    ("lk-05", "handbook", "Are USB drives allowed on a company laptop?"),
    ("lk-09", "handbook", "How many days a month can I work remotely?"),
    ("lk-16", "statute", "After how many years of continuous service does gratuity become payable?"),
    ("lk-26", "statute", "What is a Consent Manager under the DPDP Act?"),
    ("lk-15", "statute", "From how many employees must an establishment provide a creche?"),
    ("pp-11", "out_of_scope", "How much notice does the MSA need for termination for convenience?"),
    ("iso-05", "out_of_scope", "What is the PAN on the invoice?"),
)


def doc_types(desk: str) -> list[str]:
    """The retrieval filter of an answer desk, fixed here."""
    return list(DESKS[desk]["doc_types"])


def fallback_doc_types(desks) -> list[str]:
    """The fallback's filter: every doc type of the answer desks given, in table order."""
    return [t for d in ANSWER_DESKS if d in set(desks) for t in DESKS[d]["doc_types"]]


def coverage(classes) -> dict[str, bool]:
    """Which answer desks a tenant can answer from, given the doc_type classes its registry holds
    (shared/doc_types.py): a desk is covered when the tenant holds any class the desk reads."""
    held = set(classes or ())
    return {d: bool(held & set(DESKS[d]["doc_types"])) for d in ANSWER_DESKS}


def enabled_routes(classes) -> list[str]:
    """The routes a tenant's exemplar index holds: the answer desks it is covered for, and the three code desks."""
    cov = coverage(classes)
    return [r for r in ROUTES if r not in ANSWER_DESKS or cov[r]]
