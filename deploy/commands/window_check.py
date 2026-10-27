"""Twenty turns of one conversation, and what each model call is sent of it (workshop lesson 6.9).

    python commands/window_check.py                       # the window in front of the model, offline: Rs 0
    python commands/window_check.py --mode full           # what the brains send today, measured the same way
    python commands/window_check.py --history 500         # the window's budget for earlier turns (2,000 by default)
    python commands/window_check.py --live                # Gemini, full against windowed, on your machine
    make window-check [MODE=windowed|full] [TURNS=] [HISTORY=] [BRAIN=langgraph] [SAVE=] [LIVE=1]   (mk/memory.mk)

The kit's LangChain brain (BRAIN=langgraph: its LangGraph brain) answers TURNS of twenty scripted questions in one
conversation, on an InMemorySaver. Its model is services/chat/context_window.windowed(): the window in front of the
model, or, with MODE=full, nothing changed and every call measured. After each turn, one row: the thread's size, which
is what the checkpoint holds, and for the turn's largest call the context it was sent and its ceiling (the floor - the
system prompt and the turn, whole - plus the history budget), with the earlier turns it kept whole and those it brought
forward in one line. MODE=windowed holds every call under its ceiling while the thread grows; MODE=full sends the whole
thread, and the same ceiling shows where the window would have cut. The questions include a card number (a published
test number), which the window masks, and one of 395 characters, which later calls carry cut to 300.

OFFLINE (the default) needs no credential and opens no connection. The harness is lesson 6.8's (commands/thread_replay.py
offline() and scripted()): a socket guard that refuses anything but loopback, a scripted model that searches for the
question and then answers from the first passage, and every search answered by documind_tools.retrieve() on the local
profile over evals/corpus, held in memory. Rs 0.

LIVE (--live; make window-check LIVE=1 PROJECT=...) is the comparison the author runs on their own machine, never on the
lane: the same questions, each asked in two fresh conversations of the same brain, one sent the whole thread and one the
window, with Gemini (shared/profile.build_llm(): CHAT_MODEL, location global, the project in GOOGLE_CLOUD_PROJECT). The
searches are still the Rs 0 lane's, so both conversations read the same passages and only Gemini is billed, priced at
list price by each turn's limits.Meter. Per turn and per conversation: Gemini's own input, cached and output tokens, the
window's estimate of the same calls, the rupees, the limit that stopped the turn if one did (stopped_by, in the offline
table too), and the answer with the sources it cites. A turn that fails stops the
run there, with the turn, the conversation and the error named; the turns before it are printed.

SAVE=<file> writes every turn as JSON: the question, the answer and its citations, the thread's size, every call's
window report and the turn's usage.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import thread_replay as rp  # noqa: E402 - lesson 6.8's offline harness: the socket guard, the script, the Rs 0 lane

TENANT, SESSION = "acme", "lesson69"
USER = f"documind-ui-sa@{rp.PLACEHOLDER}.iam.gserviceaccount.com"
BRAINS = ("langchain", "langgraph")
MODES = ("full", "windowed")              # context_window.MODES
QUESTIONS = (
    "What is the notice period for an employee at grade E3?",
    "And during probation?",
    "How many days of earned leave can be carried forward into the next year?",
    "Is earned leave encashed when someone leaves the company?",
    "What is the cap on domestic travel reimbursement per trip?",
    "My corporate card 4111 1111 1111 1111 was charged twice for one flight. Who has to approve a travel claim above "
    "the cap?",
    "When is Form 16 issued?",
    "Can files be copied to a USB drive on a company laptop?",
    "I am drafting a note for the finance team about purchase approvals. A vendor has quoted Rs 3,50,000 for a year of "
    "software licences, and someone has suggested raising two purchase orders of Rs 1,75,000 each so that the function "
    "head can approve both without the CFO. Before I send the note, what exactly does the purchase approval policy say "
    "about the thresholds, and about splitting a purchase?",
    "How many days a month may an employee work remotely?",
    "After how many years of continuous service is gratuity payable?",
    "Is gratuity payable to a contract employee?",
    "How many weeks of maternity benefit does a woman get under the Code on Social Security?",
    "What does the Payment of Bonus Act say about the minimum bonus?",
    "How often is production access reviewed?",
    "What happens to an account that has not been used for 45 days?",
    "Who answers questions about the referral bonus, and how quickly?",
    "What does the Digital Personal Data Protection Act say about a data principal's right to erasure?",
    "Summarise what you told me about the notice period and probation.",
    "What was the first question I asked you in this conversation?",
)


class Refused(Exception):
    """A request this check turns down, with the reason to print."""


class TurnFailed(Exception):
    """A live turn that raised: the run stops there, the turns before it printed."""


def _kit_on_path() -> None:
    for p in (str(KIT / "services" / "chat"), str(KIT)):
        if p not in sys.path:
            sys.path.insert(0, p)


# ----------------------------------------------------------------------------- the brain and its turns
def build_brain(name: str, saver, model):
    """One of the kit's own brains, built with the windowed model: only what each call is sent differs."""
    _kit_on_path()
    import brains
    if name not in BRAINS:
        raise Refused(f"BRAIN must be one of {', '.join(BRAINS)}: the window sits in front of an agent brain's model")
    return brains.LangChainBrain(saver, llm=model) if name == "langchain" else brains.LangGraphBrain(saver, llm=model)


def thread_of(brain, config: dict) -> list:
    """The conversation as the checkpoint holds it."""
    graph = getattr(brain, "agent", None) or brain.graph
    return list(graph.get_state(config).values.get("messages", []))


def ask(brain, model, question: str, config: dict, name: str) -> dict:
    """One turn: the brain's own answer(), with a Meter of the turn's own, and what each of its calls was sent."""
    import brains
    import context_window as cw
    import limits

    meter = limits.Meter(model=brains.MODEL)
    before = len(model.calls)
    out = brain.answer(question, config=config, context={"tenant_id": TENANT, "user_id": USER, "assertion": "",
                                                          "brain": name, "meter": meter})
    calls = model.calls[before:]
    thread = thread_of(brain, config)
    largest = max(calls, key=lambda r: r["context_tokens"]) if calls else None
    return {"question": question, "answer": out["answer"], "tool_calls": out["tool_calls"],
            "citations": [c.get("chunk_id") for c in out.get("citations") or []],
            "thread_messages": len(thread), "thread_tokens": cw.tokens(thread), "calls": calls, "largest": largest,
            "estimate": sum(r["context_tokens"] for r in calls), "usage": meter.row(), "rupees": meter.spent_inr()}


def config_for(session: str) -> dict:
    return {"configurable": {"thread_id": f"{TENANT}:{USER}:{session}"}}


# ----------------------------------------------------------------------------- offline
def run_offline(mode: str, turns: int, brain_name: str, history: int | None, out=None) -> list[dict]:
    """TURNS scripted questions in one conversation, offline, with the window (windowed) or without it (full)."""
    out = out or sys.stdout
    with rp.offline([]):
        _kit_on_path()
        import context_window as cw
        from langgraph.checkpoint.memory import InMemorySaver

        model = cw.windowed(rp.scripted([]), mode, history_tokens=history)
        brain = build_brain(brain_name, InMemorySaver(), model)
        budget = cw.HISTORY_TOKENS if history is None else history
        _offline_head(out, mode, turns, brain_name, budget)
        rows = []
        for n, question in enumerate(QUESTIONS[:turns], 1):
            row = ask(brain, model, question, config_for(SESSION), brain_name)
            row["turn"] = n
            rows.append(row)
            print(_offline_row(row, mode), file=out)
        _offline_tail(out, mode, rows)
        return rows


def _offline_head(out, mode: str, turns: int, brain_name: str, budget: int) -> None:
    brain = "LangChain" if brain_name == "langchain" else "LangGraph"
    print(f"make window-check MODE={mode}: {turns} turn{'s' if turns != 1 else ''} of one conversation, offline, Rs 0",
          file=out)
    print(f"  the kit's {brain} brain on an InMemorySaver; a scripted model (it searches for the question, then answers "
          f"from\n  the first passage) and the Rs 0 lane over evals/corpus; no network, no credential", file=out)
    if mode == "windowed":
        print(f"  every call is sent the window: the system prompt and the turn it answers, whole, and at most "
              f"{budget:,} tokens\n  of earlier turns (CHAT_HISTORY_TOKENS)", file=out)
    else:
        print(f"  every call is sent the whole thread, as the brains do today; the ceiling is the window's (the floor "
              f"plus {budget:,}\n  tokens of earlier turns), shown for comparison", file=out)
    print("  tokens are langchain-core's estimate (count_tokens_approximately), not Gemini's count\n", file=out)
    if mode == "windowed":
        print("          thread           the turn's largest call     earlier turns              write rules", file=out)
        print("  turn    msgs   tokens     context   ceiling     kept whole  brought forward  cleared  masked  cut",
              file=out)
    else:
        print("          thread           the turn's largest call", file=out)
        print("  turn    msgs   tokens     context   ceiling     over the ceiling", file=out)


def _offline_row(row: dict, mode: str) -> str:
    r = row["largest"]
    head = (f"  {row['turn']:>4}  {row['thread_messages']:>6}  {row['thread_tokens']:>7,}   {r['context_tokens']:>9,}"
            f"  {r['ceiling']:>8,}")
    stopped = f"  (stopped by {row['usage']['stopped_by']})" if row["usage"].get("stopped_by") else ""
    if mode == "full":
        over = r["context_tokens"] - r["ceiling"]
        return head + (f"     {over:>+8,}" if over > 0 else "            -") + stopped
    open_calls = f"  ({r['unanswered']} call{'s' if r['unanswered'] != 1 else ''} left open)" if r["unanswered"] else ""
    return (head + f"     {r['kept']:>10}  {r['brought_forward']:>15}  {r['cleared']:>7}  {r['masked']:>6}  {r['cut']:>3}"
            + open_calls + stopped)


def _offline_tail(out, mode: str, rows: list[dict]) -> None:
    if not rows:
        return
    calls = [r for row in rows for r in row["calls"]]
    last = rows[-1]["calls"][-1]
    whole = last["system_tokens"] + last["thread_tokens"]
    print(f"\n{len(rows)} turns, {len(calls)} model calls, Rs 0 (a script, not a model). The thread holds "
          f"{rows[-1]['thread_messages']} messages, {rows[-1]['thread_tokens']:,} tokens: the checkpoint keeps every "
          f"one.", file=out)
    if mode == "windowed":
        over = [r for r in calls if r["context_tokens"] > r["ceiling"]]
        print(f"Every call's context was within its ceiling: {'yes' if not over else f'no, {len(over)} over'}. The last "
              f"call sent {last['context_tokens']:,} tokens, its ceiling {last['ceiling']:,}:", file=out)
        print(f"  the system prompt ({last['system_tokens']:,}) and turn {rows[-1]['turn']} whole "
              f"({last['floor_tokens'] - last['system_tokens']:,}); {last['kept']} earlier turn"
              f"{'s' if last['kept'] != 1 else ''} kept whole, {last['cleared']} result"
              f"{'s' if last['cleared'] != 1 else ''} cleared; {last['brought_forward']} brought forward in one line, "
              f"{last['listed']} of their questions listed", file=out)
        print(f"  the whole thread would have been {whole:,} tokens", file=out)
        if last["line"]:
            print(f"  the line: {rp.tr.short(last['line'], 230)}", file=out)
    else:
        first = next((row["turn"] for row in rows if row["largest"]["context_tokens"] > row["largest"]["ceiling"]), None)
        print("Every call sent the whole thread. " + (
            f"From turn {first} on, the largest call was over the ceiling the window would hold it to; the last call "
            f"sent {last['context_tokens']:,} tokens, {last['context_tokens'] / last['ceiling']:.1f} times its ceiling of "
            f"{last['ceiling']:,}." if first else "No call went over the ceiling the window would hold it to."), file=out)


# ----------------------------------------------------------------------------- live
@contextlib.contextmanager
def rs0_lane():
    """documind_tools.retrieve() on the kit's Rs 0 lane for a live run: the local profile's search over evals/corpus,
    held in memory (thread_replay's stand-in for Chroma), no rag-api and no token minted; the corpus's URIs name the
    placeholder project, never yours. The model keeps its network. Everything patched is put back on the way out."""
    _kit_on_path()
    import shared.profile as profile
    from shared import documind_tools as dt
    from shared import local_corpus as lc

    stores, real = {}, dt.retrieve

    def retrieve(query, tenant_id="", top_k=5, doc_type=None, assertion=None, brain=None, passages=False):
        if tenant_id not in stores:
            stores[tenant_id] = rp._Corpus(tenant_id)
        profile.build_store = lambda embeddings=None: stores[tenant_id]
        return real(query, tenant_id=tenant_id, top_k=top_k, doc_type=doc_type, assertion=assertion, brain=brain,
                    passages=passages)

    def no_token(audience):
        raise OSError("the Rs 0 lane mints no identity token")

    saved = {"retrieve": dt.retrieve, "PROFILE": dt.PROFILE, "_id_token": dt._id_token}
    saved_store, saved_project = profile.build_store, lc.PROJECT_ID
    dt.retrieve, dt.PROFILE, dt._id_token, lc.PROJECT_ID = retrieve, "local", no_token, rp.PLACEHOLDER
    try:
        yield
    finally:
        for k, v in saved.items():
            setattr(dt, k, v)
        profile.build_store, lc.PROJECT_ID = saved_store, saved_project


def run_live(turns: int, brain_name: str, history: int | None, llm_factory=None, out=None) -> dict:
    """Each question in two fresh conversations of the same brain, full then windowed, with Gemini unless llm_factory
    makes the model (the tests' scripted one). Returns {mode: [rows]}."""
    out = out or sys.stdout
    if llm_factory is None and not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        raise Refused("a live run needs GOOGLE_CLOUD_PROJECT, your project, for Gemini: make window-check LIVE=1 "
                      "PROJECT=<your project> sets it")
    with rs0_lane():
        import brains
        import context_window as cw
        from langgraph.checkpoint.memory import InMemorySaver
        from shared.profile import build_llm

        make = llm_factory or build_llm
        budget = cw.HISTORY_TOKENS if history is None else history
        runs = {}
        for mode in MODES:
            model = cw.windowed(make(), mode, history_tokens=history)
            runs[mode] = (build_brain(brain_name, InMemorySaver(), model), model, config_for(f"{SESSION}-{mode}"))
        model_name = os.environ.get("CHAT_MODEL", "gemini-3.6-flash") if llm_factory is None else "a scripted model"
        brain = "LangChain" if brain_name == "langchain" else "LangGraph"
        print(f"make window-check LIVE=1: full against windowed with {model_name}"
              f"{' (location global)' if llm_factory is None else ''}, on your machine", file=out)
        print(f"  {turns} question{'s' if turns != 1 else ''}, each asked in two fresh conversations of the kit's {brain} "
              f"brain: one sent the whole\n  thread, one the window ({budget:,} tokens of earlier turns); searches from "
              f"the Rs 0 lane over evals/corpus, so\n  only the model is billed, at list price (limits.Meter). \"in\" is "
              f"the model's own count, the declarations included;\n  \"estimate\" is the window's, for the same calls",
              file=out)
        rows: dict = {mode: [] for mode in MODES}
        for n, question in enumerate(QUESTIONS[:turns], 1):
            print(f"\nturn {n}: {rp.tr.short(question, 104)}", file=out)
            for mode in MODES:
                b, model, cfg = runs[mode]
                try:
                    row = ask(b, model, question, cfg, brain_name)
                except Exception as exc:                      # noqa: BLE001 - named, then the run stops
                    raise TurnFailed(f"turn {n}, the {mode} conversation: {type(exc).__name__}: "
                                     f"{rp.tr.short(str(exc), 300)}") from exc
                row["turn"] = n
                rows[mode].append(row)
            same = set(rows["full"][-1]["citations"]) == set(rows["windowed"][-1]["citations"])
            for mode in MODES:
                print(_live_row(rows[mode][-1], mode, same), file=out)
        _live_tail(out, rows)
        return rows


def _short_sources(ids: list) -> str:
    names = [str(i).split(":", 1)[-1] for i in dict.fromkeys(ids) if i]
    if not names:
        return "none"
    return ", ".join(names[:3]) + (f" and {len(names) - 3} more" if len(names) > 3 else "")


def _live_row(row: dict, mode: str, same: bool) -> str:
    u = row["usage"]
    r = row["largest"] or {}
    window = (f"; the largest call {r['context_tokens']:,} of a {r['ceiling']:,} ceiling, {r['kept']} earlier turn"
              f"{'s' if r['kept'] != 1 else ''} whole, {r['brought_forward']} brought forward"
              if mode == "windowed" and r else "")
    # A turn a limit ended says so (13 October 2026: the row printed no stopped_by, so it read like any other).
    stopped = f"; stopped by {u['stopped_by']}" if u.get("stopped_by") else ""
    text = rp.tr.short(rp.tr.text_of(row["answer"]), 100)
    sources = "the same as full" if mode == "windowed" and same else _short_sources(row["citations"])
    return (f"  {mode:9} in {u['tokens_in']:>7,} (estimate {row['estimate']:>7,})  cached {u['cached_tokens']:>6,}  out "
            f"{u['tokens_out']:>5,}  calls {u['model_calls']}  Rs {row['rupees']:.2f}{window}{stopped}\n"
            f"            {text!r}\n            sources: {sources}")


def _live_tail(out, rows: dict) -> None:
    if not rows["full"]:
        return
    tot = {}
    for mode in MODES:
        us = [r["usage"] for r in rows[mode]]
        tot[mode] = {"in": sum(u["tokens_in"] for u in us), "cached": sum(u["cached_tokens"] for u in us),
                     "out": sum(u["tokens_out"] for u in us), "rs": sum(r["rupees"] for r in rows[mode])}
    print("\ntotals:", file=out)
    for mode in MODES:
        t = tot[mode]
        print(f"  {mode:9} {t['in']:>9,} tokens in ({t['cached']:,} cached), {t['out']:,} out, Rs {t['rs']:.2f}",
              file=out)
    f, w = tot["full"], tot["windowed"]
    same = sum(set(a["citations"]) == set(b["citations"]) for a, b in zip(rows["full"], rows["windowed"]))

    def change(full_, windowed_, what):
        pct = round(100 * (full_ - windowed_) / full_)
        return f"{abs(pct)}% {'fewer' if pct >= 0 else 'more'} {what}"

    if f["in"] and f["rs"]:
        print(f"  the window sent {change(f['in'], w['in'], 'input tokens')} and cost "
              f"{change(f['rs'], w['rs'], 'rupees')} than the whole thread", file=out)
    print(f"  the two answers cited the same sources on {same} of {len(rows['full'])} turns; read the answers above for "
          "the rest", file=out)


# ----------------------------------------------------------------------------- the command
def _jsonable(rows) -> object:
    return json.loads(json.dumps(rows, default=str))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--mode", choices=MODES, default="windowed", help="windowed (the default) or full (offline)")
    ap.add_argument("--turns", type=int, help=f"how many of the {len(QUESTIONS)} questions, from the first (default all)")
    ap.add_argument("--history", type=int, help="the window's budget for earlier turns, in tokens "
                                                "(CHAT_HISTORY_TOKENS, 2,000 by default)")
    ap.add_argument("--brain", choices=BRAINS, default="langchain", help="the kit's brain to drive")
    ap.add_argument("--live", action="store_true", help="Gemini, full against windowed, on your machine")
    ap.add_argument("--save", help="write every turn as JSON to this file")
    a = ap.parse_args(argv)
    # pydantic warns that the runtime context the tools are handed (a dict holding the turn's Meter) is not its schema's
    # None when it serializes the tool call: noise here, as in every lesson cell that runs the brains.
    warnings.filterwarnings("ignore", category=UserWarning)
    try:
        turns = a.turns if a.turns is not None else len(QUESTIONS)
        if not 1 <= turns <= len(QUESTIONS):
            raise Refused(f"TURNS must be 1 to {len(QUESTIONS)}: the check has {len(QUESTIONS)} scripted questions")
        if a.history is not None and a.history < 0:
            raise Refused("HISTORY is a number of tokens, 0 or more")
        if a.live:
            rows = run_live(turns, a.brain, a.history)
        else:
            rows = run_offline(a.mode, turns, a.brain, a.history)
        if a.save:
            Path(a.save).write_text(json.dumps(_jsonable(rows), indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                                    newline="\n")
            print(f"\nwrote {a.save}")
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except TurnFailed as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
