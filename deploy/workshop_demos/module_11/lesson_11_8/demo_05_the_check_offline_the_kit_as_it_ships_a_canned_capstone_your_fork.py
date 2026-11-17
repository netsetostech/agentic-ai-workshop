"""Lesson 11.8: The check, offline: the kit as it ships, a canned capstone, your fork

Run it in your kit checkout. If your checkout holds lesson 11.3's records, components 1, 4 and 8 read them and your output differs from the one below, which was run on a copy of the kit with no records at all. commands/tests/capstone_fork/ is Sahyadri Freight, a made-up logistics company whose corpus is a fleet safety manual and a driver handbook, 32 pages between them, with the four documents and the records lesson 11.3's controlled failure leaves: a mistyped model promoted by force, rolled back and repaired, with a smoke run around each step and the repair's gate report. The kit's tests lay it over a copy of the kit, so you do the same: a local clone of your checkout, the canned files over it, its two golden rows appended, then the check. The clone holds none of your records, so the output is the canned fork's alone. The check's rules are functions you can call. The cell loads the module, points a Fork at the canned fork and prints what the rules see: the smoke runs in order, the rollback they show, each report with its isolation rows, the tenant's pages, and how each FAILURE-MODES command resolves. Your four documents start from the kit's templates in capstone/templates/. Each is the canned fork's document emptied: the same headings, a {{...}} placeholder in every slot, 66 across the four, and a comment at the top saying what the check reads in it and what the defence reads. In your fork you copy them to its root, cp capstone/templates/*.md ., and replace every placeholder, braces included. Here the cell lays them as they ship over the canned fork's four, runs the check, counts the lines that still hold a placeholder, and puts the canned four back. In the fork you will defend, offline. The recording is the author's reference fork, built the way yours will be: a tenant of its own, make ingest-corpus, make roster, golden rows, make gate, lesson 11.3's rollback with a smoke run before and after, and the four documents, written from the templates.

Run order inside this file:
1. Do it: the kit as it ships (source window 18)
2. Do it: a canned capstone that passes (source window 20)
3. Do it: the records, with the kit's own rules (source window 22)
4. Do it: your four documents, from the templates (source window 24)
5. Do it: your fork (source window 26)

Prerequisites: demo_04_the_lines_the_check_rests_on.
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


# Original CLI workflow for step_01_the_kit_as_it_ships.
COMMANDS_01 = """set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to
make capstone-check                 # FORK=. : the checkout you are in, offline
true   # that failure is the cell's answer: compare the output with the page's expected window


"""

def step_01_the_kit_as_it_ships(session):
    """Run Do it: the kit as it ships at this checkpoint.

    Run it in your kit checkout. If your checkout holds lesson 11.3's records, components 1, 4 and 8 read them and your output differs from the one below, which was run on a copy of the kit with no records at all.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads your checkout and runs make eval, a few seconds; no lane, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> capstone-check: the fork at /home/you/deploy_module_rag, offline: its files and records, and make eval. PROJECT=
       adds the lane's reads
       1  FAIL  A live URL behind IAP
                the fork deploys documind-ui behind IAP: --iap and --no-allow-unauthenticated (commands/lesson-12.4.sh)
              - no make smoke-deployed run in evals/reports/smoke-deployed.jsonl: make smoke-deployed PROJECT=<id> (lesson
                11.3) records one
              - no live eval report in evals/reports/ asked the isolation rows: make gate (lesson 11.2) writes one, as
                make eval-live REPORT=<file> does
       2  FAIL  Your own corpus, 30 pages or more, ingested
              - evals/corpus/ holds no tenant o
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_canned_capstone_that_passes.
COMMANDS_02 = """rm -rf /tmp/sahyadri && git clone -q --local . /tmp/sahyadri      # a copy of the kit, with none of your records
cp -r commands/tests/capstone_fork/. /tmp/sahyadri/              # Sahyadri Freight's documents, corpus and records over it
cat /tmp/sahyadri/evals/golden.jsonl.add >> /tmp/sahyadri/evals/golden.jsonl && rm /tmp/sahyadri/evals/golden.jsonl.add
make capstone-check FORK=/tmp/sahyadri

"""

def step_02_a_canned_capstone_that_passes(session):
    """Run Do it: a canned capstone that passes at this checkpoint.

    commands/tests/capstone_fork/ is Sahyadri Freight, a made-up logistics company whose corpus is a fleet safety manual and a driver handbook, 32 pages between them, with the four documents and the records lesson 11.3's controlled failure leaves: a mistyped model promoted by force, rolled back and repaired, with a smoke run around each step and the repair's gate report. The kit's tests lay it over a copy of the kit, so you do the same: a local clone of your checkout, the canned files over it, its two golden rows appended, then the check. The clone holds none of your records, so the output is the canned fork's alone.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a copy of the kit with the canned fork over it, then the check; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> capstone-check: the fork at /tmp/sahyadri, offline: its files and records, and make eval. PROJECT= adds the lane's
       reads
       1  PASS  A live URL behind IAP
                the fork deploys documind-ui behind IAP: --iap and --no-allow-unauthenticated (commands/lesson-12.4.sh)
                a member was answered: GET /version said git_sha abc1234, gemini-3.6-flash, documind-rag@v3 (make
                smoke-deployed, 2026-11-17T10:30:00Z)
                a non-member was refused: every isolation row (11) answered 403 to the outsider
                (evals/reports/gate-documind-api-00043-fix.json)
       2  PASS  Your own corpus, 30 pages or more, ingested
                sahyadri's corpus: 2 documents, 32 pages a
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def step_03_the_records_with_the_kit_s_own_rules(session):
    """Run Do it: the records, with the kit's own rules at this checkpoint.

    The check's rules are functions you can call. The cell loads the module, points a Fork at the canned fork and prints what the rules see: the smoke runs in order, the rollback they show, each report with its isolation rows, the tenant's pages, and how each FAILURE-MODES command resolves.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's own rules on the canned fork's records; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 4 make smoke-deployed runs in evals/reports/smoke-deployed.jsonl, oldest first:
      2026-11-17T08:10:00Z  serving documind-api-00041-kel  candidate documind-api-00041-kel  PASS  /version: git_sha abc1234, gemini-3.6-flash, documind-rag@v3
      2026-11-17T09:20:00Z  serving documind-api-00042-typ  candidate documind-api-00042-typ  FAIL  /version: git_sha abc1234, gemini-3.6-flsh, documind-rag@v3
      2026-11-17T09:35:00Z  serving documind-api-00041-kel  candidate documind-api-00042-typ  PASS  /version: git_sha abc1234, gemini-3.6-flash, documind-rag@v3
      2026-11-17T10:30:00Z  serving documind-api-00043-fix  candidate documind-api-00043-fix  PASS  /version: git_sha abc1234, gemini-3.6-flash, documind-
    """
    import importlib.util, warnings
    from pathlib import Path
    warnings.filterwarnings("ignore", category=UserWarning)
    spec = importlib.util.spec_from_file_location("capstone_check", "commands/capstone_check.py")
    cc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cc)                           # the kit's own rules: no lane, no network, nothing changed
    fork = cc.Fork(Path("/tmp/sahyadri"))
    print(f"{len(fork.runs)} make smoke-deployed runs in {cc.SMOKE_LOG}, oldest first:")
    for run in fork.runs:
        print(f"  {run['finished']}  serving {run['serving']}  candidate {run['candidate']}  {run['verdict'].upper():4}  "
              f"/version: {cc.release.answered(run['version'])}")
    before, after = cc.rollback(fork.runs)
    print(f"the rollback the check finds: {before['serving']} -> {after['serving']}, "
          f"{'the traffic left the revision the candidate tag names' if after['candidate'] == before['serving'] else 'back to an older revision'}")
    for rel, report in fork.reports:
        print(f"{rel}: {report['rows']} rows, {cc.isolation_asked(report)} isolation rows asked, every one refused: {cc.outsider_refused(report)}")
    print(f"your own tenant: {fork.own_tenant}; " + ", ".join(f"{name} {n} pages" for name, n in fork.corpus[fork.own_tenant])
          + f"; {sum(n or 0 for _, n in fork.corpus[fork.own_tenant])} in all")
    for title, symptom, commands in cc.failure_modes((fork.root / "FAILURE-MODES.md").read_text(encoding="utf-8")):
        why = [cc.unresolved(c, fork.targets, fork.has_file, fork.registry) for c in commands]
        print(f"FAILURE-MODES.md: {title!r}: Symptom {'yes' if symptom else 'no'}; " + "; ".join(f"`{c}` {w or 'runs in the fork'}" for c, w in zip(commands, why)))

# Original CLI workflow for step_04_your_four_documents_from_the_templates.
COMMANDS_04 = """set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to
cp capstone/templates/*.md /tmp/sahyadri/                 # the four templates over the canned four, as they ship
make capstone-check FORK=/tmp/sahyadri; echo "exit $?"
grep -c '{{' /tmp/sahyadri/{ARCHITECTURE,COST-MODEL,FAILURE-MODES,RUNBOOK}.md   # lines with a placeholder left
cp commands/tests/capstone_fork/*.md /tmp/sahyadri/      # the canned four back
make capstone-check FORK=/tmp/sahyadri >/dev/null; echo "exit $?"
true   # that failure is the cell's answer: compare the output with the page's expected window


"""

def step_04_your_four_documents_from_the_templates(session):
    """Run Do it: your four documents, from the templates at this checkpoint.

    Your four documents start from the kit's templates in capstone/templates/. Each is the canned fork's document emptied: the same headings, a {{...}} placeholder in every slot, 66 across the four, and a comment at the top saying what the check reads in it and what the defence reads. In your fork you copy them to its root, cp capstone/templates/*.md ., and replace every placeholder, braces included. Here the cell lays them as they ship over the canned fork's four, runs the check, counts the lines that still hold a placeholder, and puts the canned four back.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the templates over the canned fork's copy, then its four back; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> capstone-check: the fork at /tmp/sahyadri, offline: its files and records, and make eval. PROJECT= adds the lane's
       reads
       1  PASS  A live URL behind IAP
                the fork deploys documind-ui behind IAP: --iap and --no-allow-unauthenticated (commands/lesson-12.4.sh)
                a member was answered: GET /version said git_sha abc1234, gemini-3.6-flash, documind-rag@v3 (make
                smoke-deployed, 2026-11-17T10:30:00Z)
                a non-member was refused: every isolation row (11) answered 403 to the outsider
                (evals/reports/gate-documind-api-00043-fix.json)
       2  PASS  Your own corpus, 30 pages or more, ingested
                sahyadri's corpus: 2 documents, 32 pages a
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_your_fork.
COMMANDS_05 = """# in the fork, offline: its files, its records, and make eval
make capstone-check 2>&1 | tee /tmp/capstone-check.out && status=0 || status=$?
grep -qE '^>> (complete|incomplete): ' /tmp/capstone-check.out   # the check gave its verdict
[ "$status" -eq 0 ] || grep -q 'capstone-check\\] Error 1$' /tmp/capstone-check.out   # Error 1: incomplete, work on the fork


"""

def step_05_your_fork(session):
    """Run Do it: your fork at this checkpoint.

    In the fork you will defend, offline. The recording is the author's reference fork, built the way yours will be: a tenant of its own, make ingest-corpus, make roster, golden rows, make gate, lesson 11.3's rollback with a smoke run before and after, and the four documents, written from the templates.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in your fork (offline; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/capstone_check.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_the_kit_as_it_ships),
        ('source_20', step_02_a_canned_capstone_that_passes),
        ('source_22', step_03_the_records_with_the_kit_s_own_rules),
        ('source_24', step_04_your_four_documents_from_the_templates),
        ('source_26', step_05_your_fork),
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
