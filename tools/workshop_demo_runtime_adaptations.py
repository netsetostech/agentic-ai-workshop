"""Explicit source-cell adjustments needed when terminal cells become IDE calls.

Keep changes narrow and record every departure in the lesson map/README. Domain
examples remain visible in the demo; only repeated I/O/lifecycle code is shared.
"""
import re

# What a page's expected window shows when the cell's own command fails on purpose: make's error line, the exit
# status the cell echoes, a kit guard's STOP line (11.4's ledger probe, 22 October 2026), or make capstone-check's
# ">> incomplete:" (11.8, the kit as it ships). A cell whose expected output holds one runs as the page runs it (see
# the end of adapt()).
EXPECTED_FAILURE = re.compile(r"make: \*\*\* \[|exit status: [1-9]|\bexit [1-9]\b|returned non-zero|\bError [12]\b"
                              r"|(?:^|\n)STOP: |(?:^|\n)>> incomplete: ")

# A cell that prints its own exit status after a command (cmd; echo "exit $?") asks for the status a failure leaves,
# which a terminal without set -e prints and the demo shell's errexit never reached. While its expected window still
# awaits the author's run there is no output to read the failure from, so the cell's own echo says it: 0.4's smoke
# without the tenant and make down, and 11.1-11.3's refused gates and promotes stopped their demos (24 October 2026).
STATUS_ECHO = re.compile(r";\s*echo\b[^\n]*\$\?")
UNRECORDED = re.compile(r"^\[awaiting the author's run: ")

# A version check cut to its first line by head. gcloud and terraform go on writing after it, and under the demo shell's
# pipefail the writer's SIGPIPE (exit 141) failed the cell whenever head closed first: a race, which 0.2's setup won in
# the morning and lost after a restart (23 October 2026). sed reads every line and prints the first.
VERSION_HEAD = re.compile(r"(gcloud --version|terraform version)\s*\|\s*head -(?:n ?)?1\b")


AUTHOR_FILES = ("evals/judge_labels.L1.csv", "evals/judge_labels.L2.csv", "evals/judge_set.ratings.jsonl")


def author_files(line):
    """The author's recorded files of lesson 4.5 that one shell line reads: named, or a make judge-agree default."""
    need = {f for f in AUTHOR_FILES if f in line}
    if line.startswith("make judge-agree"):
        if "PEOPLE=1" in line and "AGAINST=" not in line:
            need.add("evals/judge_labels.L1.csv")                 # your sheet against the author's, by default
        if "PEOPLE=1" not in line and "RUN=" not in line:
            need.add("evals/judge_set.ratings.jsonl")             # the judge's ratings: the author's capture, by default
    return sorted(need)


def author_guarded(line):
    """A line that runs once the author's files it reads are in the kit, and says which it waits for until then."""
    need = author_files(line)
    if not need:
        return line
    test = " && ".join(f"[ -f {f} ]" for f in need)
    return (f'if {test}; then {line}\nelse echo "waits for the author\'s {" and ".join(n.split("/")[-1] for n in need)}: '
            f'not in your kit yet"; fi')


def poison_role(code):
    """Lesson 1.5's three poison-drill cells, found by what they run rather than by window number.

    The numbers went stale once (19/34/36 became 20/35/37 when the page gained a window), and the drill then ran the
    page's wildcard delete and first-message --auto-ack instead of the owned helpers, without a word (21 October 2026).
    """
    if "make poison PROJECT" in code:
        return "create_drill"
    if "subscriptions pull ingest-dlq-sub" in code:
        acknowledges = "--auto-ack" in code or "subscriptions ack ingest-dlq-sub" in code
        return "finish_drill" if acknowledges else "inspect_dead_letter"
    return None


def adapt(lesson, window, code, body):
    """Return executable code plus human-readable reasons for reviewed changes."""
    number = window["window"]
    changes = []
    if ((lesson == "1.5" and poison_role(code))
            or (lesson == "1.6" and number == 21)
            or (lesson == "4.2" and number == 18)
            or (lesson == "5.2" and number in {17, 19, 21})
            or (lesson == "3.8" and number == 17)):
        window["offline_override"] = False
    if lesson == "1.5" and poison_role(code):
        function = poison_role(code)
        body = f"from workshop_helpers.poison import {function}\n{function}(session)"
        changes.append("Use a unique saved empty-object name and generation; inspect/acknowledge only its exact dead letter and delete only its owned object. Time-window retry logs alone cannot identify that object.")
    if lesson == "1.6" and number == 21:
        body = ('from workshop_helpers.gates import live_gate\n'
                'live_gate(session, report=session.directory / "lesson42-red-gate.json", source="hr_policy_2026.md", expect_red=True)')
        changes.append("Require a fresh report with evaluated answers that fail assertions; preserve the expected nonzero exit without treating authentication or command failure as the lesson's proof.")
    if lesson == "4.1" and number == 10:
        body = ('from workshop_helpers.steps import backup_files\n'
                'backup_files(session, ["evals/build_golden.py", "evals/golden.jsonl", "evals/required.json", "evals/paraphrases.jsonl"])\n'
                'session.shell(' + repr(code) + ')')
        changes.append("Back up the exact four original evaluation files before any build/edit; cleanup preserves pre-existing learner edits.")
    if lesson == "4.1" and number in {23, 25}:
        match = re.search(r"python - <<'PY'\n(.*?)\nPY\n", code, re.S)
        assert match
        body = match[1] + '\nimport sys\nfrom workshop_helpers.gates import expect_failure\n'
        if number == 23:
            body += ('expect_failure(session, [sys.executable, "evals/build_golden.py"], status=1, '
                     'messages=["iso-11:", "OWN corpus"])\n'
                     'print("Unchanged golden row count:", len(Path("evals/golden.jsonl").read_text().splitlines()))')
        else:
            body += ('session.command([sys.executable, "evals/build_golden.py"])\n'
                     'expect_failure(session, [sys.executable, "evals/run_eval.py"], status=1, '
                     'messages=["iso-11:", "required.json does not list"])')
        changes.append("Capture the deliberately red gate and assert its exact exit/diagnostic. Bash errexit must not stop before the intended observation, and an arbitrary error must not count as success.")
    if lesson == "4.1" and number == 44:
        body = 'from workshop_helpers.steps import restore_files\nrestore_files(session)'
        changes.append("Restore exact saved originals and retain a copy of lesson edits; never discard pre-existing changes with git checkout.")
    if lesson == "4.2" and number == 18:
        body = 'from workshop_helpers.gates import live_gate\nlive_gate(session, report="evals/reports/lesson72.json")'
        changes.append("Retain the live gate's actual status and fresh structured report so the next functions can inspect a red result; missing reports remain errors.")
    if lesson == "5.2" and number == 17:
        body = '''import os, sys
session.set_environment(SELF_URL="http://localhost:8121", RAG_API_URL=os.environ["API"],
                        GOOGLE_CLOUD_PROJECT=session.config.project,
                        DOCUMIND_IMPERSONATE_SA=session.config.ui_service_account)
session.start_local_service([sys.executable, "-m", "uvicorn", "services.mcp.server:app", "--port", "8121"],
                            "http://localhost:8121/health", expected_health={"status": "ok", "self_url": "http://localhost:8121"})
print("Owned MCP server log:", session.state["local_service"]["log"])
'''
        changes.append("Start an owned server with a bounded health check and saved PID/log, instead of an unbounded shell loop. Tokens are minted in each calling demo, never stored between runs.")
    # B.1's server keeps a counter at the cell's top level and its handler says `global busy`. Wrapped in a step
    # function the counter is that function's local, so the handler needs nonlocal (NameError otherwise).
    if (lesson, number) == ("B.1", 24):
        assert body is not None and body.count("global busy") == 1
        body = body.replace("global busy", "nonlocal busy")
        changes.append("The counter `busy` is a local of this step function, not a module global, so the request handler declares it nonlocal. The page's cell runs at top level, where global is right.")
    # 0.1 creates the project with two placeholders the learner edits. Take the project from settings.local.json and
    # the billing account from the one open account, and do not fail when the project was already made (console, or
    # an earlier run): every later file needs this one to have completed.
    if (lesson, number) == ("0.1", 6):
        assert code.startswith("export BILLING=XXXXXX-XXXXXX-XXXXXX") and "export PROJECT=documind-ai-YOUR-ID" in code
        code = (': "${PROJECT:?set project in setup/config/settings.local.json first}"\n'
                'export BILLING="${BILLING:-$(gcloud billing accounts list --filter=open=true --format="value(name.basename())" | head -n 1)}"\n'
                ': "${BILLING:?no open billing account: export BILLING=XXXXXX-XXXXXX-XXXXXX, the ACCOUNT_ID of yours}"\n'
                'if gcloud projects describe "$PROJECT" >/dev/null 2>&1; then\n'
                '  echo "$PROJECT already exists: making it the default and linking billing"\n'
                '  gcloud config set project "$PROJECT"\n'
                'else\n'
                '  gcloud projects create "$PROJECT" --name="DocuMind lane" --set-as-default\n'
                'fi\n'
                'gcloud billing projects link "$PROJECT" --billing-account="$BILLING"\n')
        changes.append("The project id comes from settings.local.json and the billing account from your one open account (export BILLING first if you have several), instead of the page's two placeholders. A project that already exists is made the default and linked rather than created again, so the files after this one can run.")
    # 0.2's lane runs until Ctrl+C in a second terminal. In the IDE it is an owned process with a health check, run
    # with the lane's own venv: the helpers export PY as the IDE interpreter, which make would otherwise use.
    if (lesson, number) == ("0.2", 12):
        assert "make chat-local" in code and "rag-local-venv/bin/activate" in code
        window["offline_override"] = False
        body = ('from pathlib import Path\n'
                'lane_python = Path.home() / "rag-local-venv" / "bin" / "python"   # the venv step 1 made, not the IDE\'s\n'
                'session.start_local_service(["make", "chat-local", f"PY={lane_python}"], "http://localhost:8081/health",\n'
                '                            timeout=600)   # a first run seeds the corpus before the server answers\n'
                'print("Owned lane log:", session.state["local_service"]["log"])')
        changes.append("Start the lane as an owned background process with a health check (up to ten minutes: the first run seeds acme's corpus first), instead of a shell that never returns. PY names the lane's venv: the helpers export PY as the IDE interpreter, which lacks the lane's packages.")
    if (lesson, number) == ("0.2", 21):
        assert "rag-local-venv/bin/python" in code
        body = 'session.stop_local_service()   # the page: Ctrl+C in the second terminal\nsession.shell(COMMANDS)'
        changes.append("Stop this session's own lane process (the page's Ctrl+C) before reading the store directly.")
    if lesson == "5.2" and number in {19, 21}:
        prefix = ('import os\nos.environ["MCP_TOKEN"] = session.identity_token("http://localhost:8121")\n')
        if number == 21:
            prefix += 'os.environ["NO_EMAIL_TOKEN"] = session.identity_token("http://localhost:8121", include_email=False)\n'
        body = prefix + body
        changes.append("Mint fresh local-server audience tokens in this process; secret tokens are intentionally excluded from persisted session state.")
    if lesson == "5.2" and number == 23:
        inner = re.search(r"python - <<'PY'\n(.*?)\nPY", code, re.S)[1]
        inner = inner.replace('open("/tmp/mcp121.log")', 'open(owned["log"], encoding="utf-8")')
        body = 'owned = session.state.get("local_service")\nsession.stop_local_service()\nif owned:\n' + '\n'.join('    '+line for line in inner.splitlines())
        changes.append("Stop only this session's verified process group and inspect its saved log; never kill an unverified saved shell PID.")
    if lesson == "3.8" and number == 17:
        body = '''from pathlib import Path
from workshop_helpers.lesson31 import LessonCloud
cloud = LessonCloud(session)
data = (Path.home() / "pune_visitor_rules.md").read_bytes()
expected = cloud.fixture("acme", "pune_visitor_rules.md", data, upload=False, follow_upload=True)
observed = cloud.wait_indexed(expected)
print("your file's hash begins:", expected["sha256"][:12])
print("Your UI upload:", expected, "|", observed["summary"])
cloud.worker_logs(expected)
'''
        changes.append("Follow the version the UI upload wrote: its source generation, claim and current chunks; an unrelated latest ingest_ok event cannot satisfy this checkpoint. A copy whose line endings differ from the file in your home directory is its own version with its own hash, as the page says, so the demo follows it and says so instead of refusing it.")
    if lesson == "2.3" and number == 10:
        body = 'from workshop_helpers.lesson31 import require_fresh_vector\n' + body
        body = body.replace('j = ask(k); s = j["stages"]', 'j = ask(k); s = j["stages"]\n    require_fresh_vector(j)')
        changes.append("Reject semantic-cache hits or a fallback-only pool before comparing top_k/reranker behavior.")
    if lesson in {"2.2", "2.3", "2.4", "3.4", "3.5", "3.7"}:
        if body == "session.pin_vector()":
            window["offline_override"] = False
            body += '\nfrom workshop_helpers.lesson31 import prepare_cache\nprepare_cache(session)'
            changes.append("Temporarily disable an enabled answer cache for this retrieval/generation experiment and save its prior value. This changes the shared API; finish restores it. Cache lessons in Module 6 are unaffected.")
        elif body == "session.restore_backend()":
            window["offline_override"] = False
            # Separate checkpointing still attempts backend restoration if cache recovery fails.
            body = ('from workshop_helpers.lesson31 import restore_cache\n'
                    'try:\n    restore_cache(session)\nfinally:\n    session.restore_backend()')
            changes.append("Restore the saved answer-cache value and tenant backend, including after a failed experiment.")
    # The page runs every cell in an interactive shell: a pipeline's status is its last command's, and a command that
    # finds nothing does not stop the lines after it. The demos run cells under `set -eE -o pipefail`. These cells read
    # the smoke through a filter, or read the UI's IAP state line by line, and their page shows the outcome either way.
    if (lesson, number) in {("2.3", 39), ("2.4", 20), ("4.7", 23)}:
        assert "make smoke" in code and "| grep" in code
        code = "set +o pipefail   # as the page runs it: make smoke's own status does not stop this filtered read\n" + code
        changes.append("Run with the page's pipeline status (no pipefail). The cell filters make smoke for the lines this lesson reads; a check failing elsewhere in the smoke shows in those lines instead of stopping the cell before its later lines.")
    if (lesson, number) == ("4.3", 22):
        assert code.startswith('make eval-live PROJECT="$PROJECT" API="$CAND" REPORT=evals/reports/cand43.json')
        body = ('import os\nfrom workshop_helpers.gates import live_gate\n'
                'live_gate(session, report="evals/reports/cand43.json", api=os.environ["CAND"])')
        changes.append("Run the candidate's gate through live_gate: its exit is the release decision the page reads, 0 or a red 2, and the demo must go on to the next step and the cleanup that removes the candidate's tag. Before lesson 7.5's video, mm-03 keeps a full gate red (21 October 2026 the tag was left behind). A missing report or an HTTP/auth failure still fails.")
    if (lesson, number) in {("4.9", 8), ("4.9", 12)}:
        cand = number == 12
        report = "evals/reports/cand49.json" if cand else "evals/reports/live49.json"
        assert code.startswith("DOCUMIND_EVAL_PASSAGES=1 make eval-live") and report in code and (('API="$CAND"' in code) == cand)
        body = ('import os\nfrom workshop_helpers.gates import live_gate\n'
                'os.environ["DOCUMIND_EVAL_PASSAGES"] = "1"\n'
                f'try:\n    live_gate(session, report="{report}"' + (', api=os.environ["CAND"]' if cand else '') + ')\n'
                'finally:\n    os.environ.pop("DOCUMIND_EVAL_PASSAGES", None)')
        changes.append("Run the eval through live_gate with the page's switch on: this lesson reads the failing rows of a live and a candidate report, so a red exit with a fresh report is its input, not an error (before lesson 7.5's video, mm-03 alone keeps the gate red). A missing report or an HTTP/auth failure still fails.")
    if (lesson, number) == ("4.3", 11):
        last = 'python evals/run_eval.py; echo "exit $?"'
        assert code.rstrip().endswith(last)
        code = (code.rstrip()[: -len(last)]
                + 'python evals/run_eval.py > /tmp/gate43.txt 2>&1 && s=0 || s=$?; cat /tmp/gate43.txt; echo "exit $s"\n'
                + "[ \"$s\" -eq 1 ] && grep -q \"lk-06: must_contain '120 days' is not in acme's corpus\" /tmp/gate43.txt\n")
        changes.append("The refusal is the observation: the offline gate must exit 1 with its own words for the broken lk-06. Under the demo's set -e the exit stopped the step before the page's echo, step 3's git checkout never ran, and the lane's golden set stayed broken for the next lesson (21 October 2026). Any other exit, or a 1 without those words, fails.")
    if (lesson, number) == ("3.6", 41):
        assert code.startswith('make prompt-version; echo "exit $?"')
        body = ('from workshop_helpers.gates import expect_failure\n'
                'expect_failure(session, ["make", "prompt-version"], status=2, '
                'messages=["has another sha256", "A changed prompt needs a new version"])\n'
                'print("exit 2")')
        changes.append("The refusal is the observation: make prompt-version must exit 2 with the registry's own words for the edited text under the old label. Under the demo's set -e it stopped the step before the page's echo, and the kit was left on prompt-v4 with rule 5 edited (21 October 2026). Any other exit, or a 2 without those words, fails.")
    if (lesson, number) == ("3.9", 43):
        assert code.rstrip().endswith("terraform -chdir=terraform state list | grep -c gemini_rpm")
        code = ("set +e +o pipefail   # as the page runs it: grep -c prints 0 and exits 1 when the override is not in the state\n"
                + code.rstrip() + "\ntrue                 # the cell's status is not grep's: its 0 is the answer\n")
        changes.append("Run with the page's shell semantics: every line is a read. grep -c prints 0 and exits 1 on a lane without quota.tf's override, and that 0 is the answer the page reads, not a failure; the cell ends on true so its last line's status is not taken for one.")
    if (lesson, number) == ("8.2", 15):
        test = 'python -m unittest commands/tests/test_twin_chunker.py 2>&1 | grep -E "^(FAIL:|AssertionError|Ran |OK|FAILED)"'
        assert code.startswith("sed -i 's/^CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200/") and "services/ingest/main.py\n" in code and test in code
        code = code.replace(test, '{ python -m unittest commands/tests/test_twin_chunker.py 2>&1 || true; } '
                            '| grep -E "^(FAIL:|AssertionError|Ran |OK|FAILED)" | tee /tmp/twin82.txt\n'
                            'grep -q "^FAILED" /tmp/twin82.txt   # one twin edited: the test must fail, naming both lines', 1)
        changes.append("Read the twin test's red as the cell's answer: with the worker alone edited it must fail, and its exit 1 under pipefail stopped the demo with services/ingest/main.py edited and the put-back step never run (22 October 2026). The step now fails only if the test passes.")
    if (lesson, number) == ("10.11", 13):
        placeholder = "PREV=REVISION   # the revision your plan's step 1 names, as it printed it"
        assert code.startswith(placeholder) and '--to-revisions "$PREV=100"' in code
        code = code.replace(placeholder,
                            "PREV=\"$(make -s remediate OFFLINE=1 FIXTURE=evals/reports/remediate_held.json | grep -o -- '--to-revisions [a-z0-9-]*=100' "
                            "| head -n 1 | sed 's/^--to-revisions //; s/=100$//')\"   # the revision your plan's step 1 names, as it printed it\n"
                            'echo "rolling back to: $PREV"', 1)
        changes.append("Fill in the page's placeholder from the plan itself: the saved plan replays offline at Rs 0, and its step 1 names the revision to roll back to. The literal REVISION was sent to gcloud, which refused it, and the fault stayed on the lane (22 October 2026).")
    if (lesson, number) == ("10.11", 19):
        assert code.strip() == "make incident-drill PROJECT=$PROJECT RESTORE=1"
        code = ('if [ -s .fault-hold ]; then make incident-drill PROJECT=$PROJECT RESTORE=1\n'
                'else echo "no fault is held in this checkout (.fault-hold): nothing to restore"; fi\n')
        changes.append("Restore only a fault this checkout holds: the restore is the lesson's cleanup, run after a failure too, and a run that stopped before the hold has nothing to put back.")
    if (lesson, number) == ("10.8", 7):
        upload = 'make ingest-one PROJECT="$PROJECT" TENANT=acme FILE=evals/adversarial/vendor_note_acme.md'
        assert code.startswith(upload + "\n")
        code = code.replace(upload, (
            'if make -s sources PROJECT="$PROJECT" TENANT_ONLY=acme 2>/dev/null | grep -Eq "^acme/vendor_note_acme.md +withdrawn"; then\n'
            '  # a second run: the lesson\'s own cleanup withdrew the note, and the same bytes uploaded again stay withdrawn\n'
            '  make restore PROJECT="$PROJECT" SOURCE=acme/vendor_note_acme.md\n'
            '  for i in $(seq 1 30); do\n'
            '    make -s sources PROJECT="$PROJECT" TENANT_ONLY=acme 2>/dev/null | grep -Eq "^acme/vendor_note_acme.md +indexed" && break; sleep 10\n'
            '  done\n'
            'else\n'
            '  ' + upload + '\n'
            'fi'), 1)
        changes.append("Bring the note back the way a withdrawn version comes back: on a second run of the lesson its cleanup has withdrawn the note, and the worker keeps the same bytes uploaded again withdrawn (ingest_duplicate, then ingest_withdrawn), so make ingest-one waited five minutes for an ingest_ok that never came (22 October 2026). A first run uploads it as the page does.")
    # 11.4's put-back is the lesson's cleanup (run after a failure too): on 22 October 2026 a stopped run left acme's
    # handbook on the broken revision 2. It re-issues version 1 only when the ledger's current version is another one:
    # the same bytes again are a duplicate the worker acks without the line make reindex waits five minutes for.
    if (lesson, number) == ("11.4", 20):
        put_back = 'make reindex PROJECT="$PROJECT" TENANT=acme FILE=evals/corpus/acme/hr_policy_2026.md'
        assert code.startswith(put_back + "\n") and "ask131 restored" in code
        code = code.replace(put_back, (
            'CUR="$(python - <<\'PY\'\n'
            'import os, warnings\n'
            'warnings.filterwarnings("ignore")\n'
            'from google.cloud import firestore\n'
            'rows = firestore.Client(project=os.environ["PROJECT"]).collection("sources").where("tenant_id", "==", "acme").stream()\n'
            'print(next((r.to_dict().get("doc_key") or "" for r in rows if (r.to_dict().get("name") or "").endswith("hr_policy_2026.md")), ""))\n'
            'PY\n'
            ')"\n'
            'if [ "$CUR" != "acme_$(sha256sum evals/corpus/acme/hr_policy_2026.md | cut -c1-64)" ]; then\n'
            '  ' + put_back + '\n'
            'else echo "acme\'s handbook is already version 1: nothing to put back"; fi'), 1)
        code = code.replace("ask131 restored", "type ask131 >/dev/null 2>&1 && ask131 restored   # the lesson's question, when its helper is defined", 1)
        changes.append("Put version 1 back only when it is not already current: this is the lesson's cleanup now, run after a failure too, and re-uploading the current bytes is a duplicate that make reindex would wait five minutes for.")
    # 10.8's poisoned server runs "in a second shell tab" until Ctrl-C: in one script it never returned (22 October 2026).
    # Here it runs in the background, the cell waits for its port, and the rug pull's cell stops it when it is done.
    if (lesson, number) == ("10.8", 66):
        assert code.startswith('make evil-mcp PY="$PY"')
        code = ('(make evil-mcp PY="$PY" > /tmp/evil-mcp.log 2>&1 &)   # the second tab: the poisoned server, in the background here\n'
                'for i in $(seq 1 30); do curl -s -o /dev/null http://127.0.0.1:8900/mcp && break; sleep 1; done\n'
                'head -n 1 /tmp/evil-mcp.log\n')
        changes.append("Run the second tab's server in the background: make evil-mcp serves until Ctrl-C, so in one script the demo waited on it for ever. The cell waits for port 8900 and prints the server's first line, as the tab would show it.")
    if (lesson, number) == ("10.8", 72):
        assert code.startswith('make evil-mcp PY="$PY" RUG=1') and 'make pin-tools PY="$PY" CHECK=1 URL=http://127.0.0.1:8900/mcp' in code
        code = ('set +e +o pipefail   # as the page runs it: the check is meant to fail on the rug pull\n'
                'pkill -f "evals/adversarial/evil_mcp.py"; sleep 1                # Ctrl-C on the first shape\n'
                '(make evil-mcp PY="$PY" RUG=1 > /tmp/evil-mcp.log 2>&1 &)        # the second tab again, the rug pull\n'
                'for i in $(seq 1 30); do curl -s -o /dev/null http://127.0.0.1:8900/mcp && break; sleep 1; done\n'
                'head -n 1 /tmp/evil-mcp.log\n'
                'make pin-tools PY="$PY" CHECK=1 URL=http://127.0.0.1:8900/mcp; echo "exit status: $?"\n'
                'pkill -f "evals/adversarial/evil_mcp.py"   # the server stopped: nothing after this cell needs it\n'
                'true\n')
        changes.append("Swap the background server for its rug-pull shape, run the page's check against it (meant to fail), then stop the server, so no process is left serving on port 8900 after the demo.")
    if (lesson, number) == ("10.8", 37):
        refused = 'make attack-offline SURFACES=chat,desk,peer; echo "exit status: $?"'
        assert code.strip() == refused
        code = ('make attack-offline SURFACES=chat,desk,peer && status=0 || status=$?; echo "exit status: $status"\n'
                '[ "$status" -eq 2 ]   # the live surfaces are refused offline: run_attacks.py exits 2, and make with it\n')
        changes.append("Read the refusal as the cell's answer: --offline runs the api surface only, so run_attacks.py refuses chat, desk and peer and make exits 2, which stopped the demo before the page's exit-status line (22 October 2026). The step now fails only if the live surfaces are not refused.")
    # 11.7's detectors exit 1 when one finds something, as the page says, and every lane finds at least the admin address
    # deploy-drops-hotfix reads: the demo stopped there (22 October 2026). Through make both 1 and the script's 2 (a read
    # that failed, nothing found) are make's exit 2, told apart by make's "Error 1" and "Error 2".
    if (lesson, number) == ("11.7", 37):
        detect = 'make gotcha-detect PROJECT="$PROJECT" REGION="$REGION"'
        assert code.strip() == detect
        code = (detect + " 2>&1 | tee /tmp/gotcha-detect.out && status=0 || status=$?\n"
                "grep -qE '^[0-9]+ detectors: [0-9]+ found, [0-9]+ could not read$' /tmp/gotcha-detect.out   # every detector ran\n"
                "[ \"$status\" -eq 0 ] || grep -q 'gotcha-detect\\] Error 1$' /tmp/gotcha-detect.out   # Error 1: something found, as the page expects\n")
        changes.append("Read the detectors' exit as the page does: 1 when anything is found, which every lane shows (the admin address deploy-drops-hotfix reads), stopped the demo at its first cell (22 October 2026). The step fails if a detector's read failed with nothing found (make's Error 2) or the summary line never printed.")
    # 11.8's check on your own fork, and with your lane, gives a verdict either way: complete (exit 0) once the capstone
    # is done, incomplete (exit 1) before it, which the run list calls work on the fork, not a recording. On a checkout
    # that is still the kit it is incomplete, and the demo stopped there, before the lane's reads and the handover
    # (22 October 2026). Through make, 1 is make's "Error 1"; the check's 2, a stop, is "Error 2".
    if (lesson, number) in {("11.8", 26), ("11.8", 32)}:
        check, _, note = code.strip().partition("#")
        check = check.strip()
        assert check.startswith("make capstone-check") and "\n" not in check
        code = ((f"# {note.strip()}\n" if note else "")
                + check + " 2>&1 | tee /tmp/capstone-check.out && status=0 || status=$?\n"
                "grep -qE '^>> (complete|incomplete): ' /tmp/capstone-check.out   # the check gave its verdict\n"
                "[ \"$status\" -eq 0 ] || grep -q 'capstone-check\\] Error 1$' /tmp/capstone-check.out   # Error 1: incomplete, work on the fork\n")
        changes.append("Read the check's verdict as the cell's answer: incomplete (exit 1) is work on your fork, and on a checkout that is still the kit it is what the check says, which stopped the demo before the lane's reads and the handover (22 October 2026). The step fails if the check stopped (make's Error 2) or printed no verdict.")
    # 0.2's loosened row: the page runs make dryrun to watch the eval gate refuse lk-06, and its expected window ends on
    # run_eval.py's closing sentence (make's own error line is in the prose), so the rule at the end never matched. The
    # demo stopped there, before "Repair it", and left evals/golden.jsonl loosened (23 October 2026).
    if (lesson, number) == ("0.2", 33):
        assert code.strip() == 'cd "$DEMO_ROOT" && make dryrun'
        code = ('cd "$DEMO_ROOT" && make dryrun 2>&1 | tee /tmp/dryrun-loosened.out && status=0 || status=$?\n'
                "[ \"$status\" -ne 0 ] && grep -q 'lk-06: an answerable row with no must_contain' /tmp/dryrun-loosened.out   # the gate refused the loosened row\n")
        changes.append("Read the gate's refusal as the cell's answer: with lk-06 loosened, make dryrun fails falsifiable and exits non-zero, which stopped the demo before Repair it and left evals/golden.jsonl loosened (23 October 2026). The step fails if the dryrun passes or fails for any other reason.")
    if (lesson, number) == ("10.7", 41):
        check = 'python commands/check_callers.py --graph; echo "exit $?"'
        assert code.startswith("sed -i 's/^for who in documind-ui-sa documind-outsider-sa/") and check in code \
            and "git checkout -q commands/lesson-12.8.sh" in code
        code = code.replace(check, 'python commands/check_callers.py --graph && graph=0 || graph=$?; echo "exit $graph"', 1)
        code = code.rstrip("\n") + '\n[ "$graph" -ne 0 ]   # the edge back must be refused: the check names the cycle and exits 1\n'
        changes.append("Read the check's refusal as the cell's answer: with the peer's account added to lesson-12.8.sh the check names the cycle and exits 1, which stopped the demo before the put-back line and left lesson-12.8.sh edited (22 October 2026). The file is put back first; the step fails only if the check let the edge through.")
    if (lesson, number) == ("6.8", 37):
        grep = 'grep -c "a follow-up too" services/chat/brains.py'
        assert code.startswith("sed -i 's/document question, a follow-up too, and cite/") and grep in code
        code = code.replace(grep, grep + " || true", 1)
        changes.append("Read grep's count, not its status: once the sed has taken the clause out, grep -c prints the 0 the page reads and exits 1, which stopped the demo with brains.py still edited and its restore not run (22 October 2026). The sed still fails the step if it fails.")
    if (lesson, number) == ("3.8", 11):
        assert '--format=yaml | grep -i "iap-enabled"' in code
        code = "set +e +o pipefail   # as the page runs it: every line is a read, and grep finding nothing is an answer\n" + code
        changes.append("Run with the page's shell semantics: every line is a read. If the UI is not behind IAP, grep prints nothing and the IAP policy and the unsigned request after it show why, instead of the cell stopping at grep.")
    # A red gate on either revision is what these lessons compare; an auth, token or command failure still fails.
    if (lesson, number) == ("3.3", 21):
        assert 'print("to bench, one rule each: " + ("export " + " ".join(pairs)' in code
        body = ('session.shell(COMMANDS)\nimport os, re\n'
                 'log = sorted(session.attempt.glob("command_*.log"))[-1].read_text(encoding="utf-8")\n'
                 'found = re.search(r"to bench, one rule each: export ((?:FIX[123]=\\S+ ?)+)", log)\n'
                 'for pair in (found[1].split() if found else []):\n'
                 '    key, _, value = pair.partition("=")\n'
                 '    os.environ[key] = value\n'
                 'print("For step 7:", found[1] if found else "no row the prompt can fix")')
        changes.append("Export the cell's FIX1-FIX3 as the page asks you to paste them: the cell prints the export line, which a Python cell cannot run in your shell, so step 7's bench stopped at ${FIX1:?} (21 October 2026). The session keeps them for the next file.")
    if (lesson, number) == ("3.3", 19):
        assert code.startswith('DOCUMIND_EVAL_PASSAGES=1 make eval-live PROJECT="$PROJECT" REPORT=evals/reports/lesson33.json')
        body = ('import os\nfrom workshop_helpers.gates import live_gate\n'
                'os.environ["DOCUMIND_EVAL_PASSAGES"] = "1"\n'
                'try:\n    live_gate(session, report="evals/reports/lesson33.json")\n'
                'finally:\n    os.environ.pop("DOCUMIND_EVAL_PASSAGES", None)')
        changes.append("Run the eval through live_gate with the page's switch on: the rates and the required rows decide its exit, and a red exit with a fresh report is the reading step 6 starts from, as the page says. Before lesson 7.5 builds the town hall video, mm-03 cannot cite a segment and blocks the gate on its own. A missing report or an HTTP/auth failure still fails.")
    if (lesson, number) in {("3.2", 46), ("3.2", 48)}:
        arm = "kit" if number == 46 else "none"
        assert f'python evals/route_eval.py --live-l1 --project "$PROJECT" --exemplars {arm} --report "$HOME/exemplars_{arm}.json"' in code
        body = ('from pathlib import Path\nfrom workshop_helpers.gates import route_gate\n'
                f'route_gate(session, exemplars="{arm}", report=Path.home() / "exemplars_{arm}.json")')
        changes.append("Run the arm through route_gate: the dev gates' FAIL lines and exit 1 are a reading this lesson compares, as the page says, so the next arm still runs; a run that writes no fresh report with its decisions still fails.")
    if (lesson, number) == ("4.4", 14):
        assert code.startswith('make eval-live PROJECT="$PROJECT" SOURCE=hr_policy_2026.md REPORT=evals/reports/base73.json | tail -3\n') and 'REPORT=evals/reports/cand73.json API="$CAND"' in code
        body = ('import os\nfrom workshop_helpers.gates import live_gate\n'
                'live_gate(session, report="evals/reports/base73.json", source="hr_policy_2026.md")\n'
                'live_gate(session, report="evals/reports/cand73.json", source="hr_policy_2026.md", api=os.environ["CAND"])')
        changes.append("Run both gates through live_gate: a red gate on the live revision or the candidate is an observation this lesson compares, and each keeps its fresh report. The page's `| tail -3` stopped the cell under pipefail on a red baseline; here the whole gate output shows. A missing report or an HTTP/auth failure still fails.")
    if (lesson, number) == ("12.3", 16):
        assert code.startswith('make eval-live PROJECT="$PROJECT" REPORT="$HOME/base173.json" | tail -3\n') and 'API="$CAND" REPORT="$HOME/cand173.json"' in code
        body = ('import os\nfrom pathlib import Path\nfrom workshop_helpers.gates import live_gate\n'
                'live_gate(session, report=Path.home() / "base173.json")\n'
                'live_gate(session, report=Path.home() / "cand173.json", api=os.environ["CAND"])')
        changes.append("Run both gates through live_gate: a red gate on the live revision or the tuned candidate is an observation this lesson compares, and each keeps its fresh report. The page's `| tail -3` stopped the cell under pipefail on a red baseline; here the whole gate output shows. A missing report or an HTTP/auth failure still fails.")
    if (lesson, number) == ("12.3", 27):
        assert code.startswith('make eval-live PROJECT="$PROJECT" API="$UNTUNED" REPORT="$HOME/untuned173.json"')
        body = ('import os\nfrom pathlib import Path\nfrom workshop_helpers.gates import live_gate\n'
                'live_gate(session, report=Path.home() / "untuned173.json", api=os.environ["UNTUNED"])')
        changes.append("Run the untuned gate through live_gate: a red gate on the untuned base is an observation this lesson compares, and it keeps its fresh report.")
    if (lesson, number) == ("9.3", 19):
        assert code.startswith('make gke-up PROJECT="$PROJECT"')
        body = ('from workshop_helpers.gates import expect_guard\n'
                'expect_guard(session, ["make", "gke-up", "PROJECT=" + session.config.project],\n'
                '             stop="STOP: the Standard CPU lab cannot run the L4 GPU lesson")')
        changes.append("The page runs make gke-up to watch its guard stop on the Standard CPU lab (exit 2 with STOP). Accept that stop as the observation, and exit 0 where the lab is Autopilot; any other exit is still an error.")
    # The page sleeps after make off before reading Cloud Monitoring; the IDE pauses there too (MANUAL). Wait only for
    # what is left of the page's interval, counted from make off's recorded completion, so the two never add up.
    if (lesson, number) == ("11.6", 22):
        assert code.startswith("sleep 900 ")
        code = code.split("\n", 1)[1]
        body = ('from workshop_helpers.steps import wait_after\n'
                'wait_after(session, "source_20", 900)   # the page\'s sleep 900, less the time since make off completed\n'
                'session.shell(COMMANDS)')
        changes.append("Replace the page's sleep 900 with a wait for whatever is left of those fifteen minutes since make off completed. The manual pause before it lets you stop and come back; the pause and the sleep no longer add up to thirty minutes.")
    if (lesson, number) == ("9.4", 20):
        assert body is not None and "instance_count" in body
        body = ('from workshop_helpers.steps import wait_after\n'
                'wait_after(session, "source_17", 600)   # the page: at least ten minutes after make off\n' + body)
        changes.append("The page reads Cloud Monitoring at least ten minutes after make off. Wait for whatever is left of those ten minutes after the manual pause, so an early 'done' cannot read the instance count too soon.")
    # A shell cell whose expected output shows a command failing (a refusal, a red check, an oracle's FAIL) is answered
    # by that failure, in a shell that goes on to the next line. The demo shell's set -e stopped there instead, often
    # before a put-back line (22 October 2026: Module 10 stopped at five such cells). Windows adapted above keep theirs.
    # Lesson 5.5's filter step expects acme's text rows unknown, as the worker wrote them: a doc_type filter then finds
    # nothing. Lesson 5.2 classes them and its finish cell puts them back; when that did not run, the filter found two
    # invoice rows and the step still passed (22 October 2026). The reset's plan, never applied here, counts what is left.
    if (lesson, number) == ("5.5", 28):
        assert code.startswith('export SINCE103="$(date -u +%FT%TZ)"') and 'for doc_type in (None, "invoice"):' in code
        code = ('# acme\'s rows must be unknown, as the worker wrote them: count what lesson 5.2\'s reset would still change\n'
                'PYTHONPATH=.:services/ingest GOOGLE_CLOUD_PROJECT="$PROJECT" python services/ingest/relabel.py --project "$PROJECT" --tenant acme --reset |\n'
                '  python -c \'import json,sys; s=[json.loads(x) for x in sys.stdin if "relabel_plan" in x][-1]; n=s["rows"]+s["history_rows"]; print(f"acme rows still classed: {n}"); sys.exit(1 if n else 0)\' ||\n'
                '  { echo "STOP: acme\'s rows still carry classes, so the filter would find them. Run lesson 5.2\'s finish cell first: make doc-types PROJECT=\\"$PROJECT\\" TENANT=acme RESET=1 APPLY=1 (with VECTOR_INDEX_NAME exported)." >&2; exit 1; }\n'
                + code)
        changes.append("Before the filter, count the rows lesson 5.2's reset would still change (its plan only, nothing written): the step expects every acme text row unknown, and stops with the fix when 5.2's finish cell has not put them back, instead of passing on a filter that found classed rows.")
    # Lesson 4.5's author files - two people's labels and the judge's ratings of the frozen rows - are recorded from the
    # author's run and are not in the kit yet. A line that reads one runs once it is there and says so while it is not;
    # the learner's own path (a set of their own, a colleague's sheet, their lane's ratings) has its own cells.
    if lesson == "4.5" and body is None and not changes and any(author_files(line) for line in (code or "").splitlines()):
        code = "\n".join(author_guarded(line) for line in code.splitlines()) + "\n"
        changes.append("Run each line that reads the author's recorded files (judge_labels.L1.csv, judge_labels.L2.csv, judge_set.ratings.jsonl) only once they are in your kit; until then it prints which file it waits for. Your own path's cells run instead: your frozen set, your colleague's sheet, your lane's ratings (24 October 2026).")
    expected = window.get("expected") or ""
    if not changes and body is None and EXPECTED_FAILURE.search(expected):
        code = ("set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to\n"
                + code.rstrip("\n") + "\ntrue   # that failure is the cell's answer: compare the output with the page's expected window\n")
        changes.append("Run with the page's shell semantics: the page's expected output shows a command in this cell failing (a refusal, a red check, an oracle's FAIL), which is the cell's answer. Every line runs, a put-back line included, and the step ends green; compare the output with the expected window.")
    elif not changes and body is None and UNRECORDED.match(expected) and STATUS_ECHO.search(code or ""):
        code = ("set +e +o pipefail   # as the page runs it: the cell prints its own exit status, which a failure must reach\n"
                + code.rstrip("\n") + "\ntrue   # the status it printed is the cell's answer: compare it with the page's prose\n")
        changes.append("Run with the page's shell semantics: the cell prints its own exit status after a command (cmd; echo \"exit $?\"), and the page's prose says which commands here fail on purpose. Its expected output is not recorded yet, so the demo cannot read the failure from it. Every line runs, a put-back line included, and the step ends green; compare the printed status with the page.")
    if code and VERSION_HEAD.search(code):
        code = VERSION_HEAD.sub(r"\1 | sed -n 1p", code)
        changes.append("Print the version's first line with sed instead of head: gcloud and terraform go on writing after it, and under the demo shell's pipefail their SIGPIPE when head closed first failed the cell with exit 141, by chance (23 October 2026). The line printed is the same.")
    return code, body, changes
