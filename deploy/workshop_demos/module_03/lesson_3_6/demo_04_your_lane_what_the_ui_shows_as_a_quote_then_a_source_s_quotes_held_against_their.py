"""Lesson 3.6: Your lane: what the UI shows as a quote, then a source's quotes held against their passages

Do it: the scoped gate, the switch on The cell reads the report the gate wrote and prints each citation's verdict, the position of the passage it names, and the quote's first words; then any row whose pool could not be read or came back without one of its anchors.

Run order inside this file:
1. Do it: the scoped gate, the switch on (source window 18)
2. Do it: every citation's verdict (source window 20)

Prerequisites: demo_03_offline_nine_quotes_through_both_measures_and_the_gate_s_own_lines_over_a_stand.
Use the existing rag-shell-venv interpreter; Run or Debug this file.
The functions below contain the lesson examples in source order. Helpers
supply configuration, authentication, state and CLI execution. See README.md
for expected observations, effects and the next file; GUIDE.md retains prose.
Example: open this file at the matching HTML heading, Run once, then inspect
the observations below before continuing to the next numbered section.
A successful process is not proof that a live result matched the sample.

"""
from workshop_helpers.session import DemoSession
from workshop_helpers.steps import manual_checkpoint, run_steps

# REPEAT replays the whole file; use only after reviewing its effects.
REPEAT = False
# A failed function may have partial effects. Inspect its saved attempt first.
RETRY_FAILED_STEP = False


# Original CLI workflow for step_01_the_scoped_gate_the_switch_on.
COMMANDS_01 = """DOCUMIND_EVAL_PASSAGES=1 make eval-live PROJECT="$PROJECT" SOURCE=hr_policy_2026.md REPORT=evals/reports/quotes36.json

"""

def step_01_the_scoped_gate_the_switch_on(session):
    """Run Do it: the scoped gate, the switch on at this checkpoint.

    Do it: the scoped gate, the switch on

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (ten answers, then ten pool reads: a few rupees).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/quotes_live.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_every_citation_s_verdict(session):
    """Run Do it: every citation's verdict at this checkpoint.

    The cell reads the report the gate wrote and prints each citation's verdict, the position of the passage it names, and the quote's first words; then any row whose pool could not be read or came back without one of its anchors.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the report; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/quotes_live_cites.txt]
    """
    import json, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    path = "evals/reports/quotes36.json"                                  # the report the scoped gate just wrote
    r = json.load(open(path, encoding="utf-8"))
    pq = r.get("passage_checks")
    if not pq:
        raise SystemExit(f"{path} has no passage_checks: run make eval-live with DOCUMIND_EVAL_PASSAGES=1")
    
    
    def pct(v):
        """A rate as the gate prints it, or n/a when nothing was counted.
        
        Example: pct(r.get('quote_support_rate'))
        """
        return "n/a" if v is None else f"{v:.1%}"
    
    
    print(f"{r['api_url']}  {r['rows']} rows | quote_support_rate {pct(r.get('quote_support_rate'))} | quote_passage_rate {pct(pq['quote_passage_rate'])}")
    for rec in r["records"]:
        for c in rec.get("cites") or []:
            words = " ".join((c.get("quote") or "").split())
            print(f"  {rec['id']:6} {c.get('check', 'not read'):11} #{(c.get('chunk_id') or '').rsplit('#', 1)[-1]:<4} {words[:60]!r}{' ...' if len(words) > 60 else ''}")
        lost = sorted(a for a, hit in (rec.get("anchors") or {}).items() if not hit)
        if "pool" in rec and (rec["pool"] is None or lost):
            print(f"  {rec['id']:6} pool {rec['pool']}{'; anchors not in it: ' + ', '.join(lost) if lost else ''}")
    print("verdicts: " + ", ".join(f"{k} {n}" for k, n in pq["quotes"].items()))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_the_scoped_gate_the_switch_on),
        ('source_20', step_02_every_citation_s_verdict),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
