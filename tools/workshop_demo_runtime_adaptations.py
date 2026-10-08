"""Explicit source-cell adjustments needed when terminal cells become IDE calls.

Keep changes narrow and record every departure in the lesson map/README. Domain
examples remain visible in the demo; only repeated I/O/lifecycle code is shared.
"""
import re


def adapt(lesson, window, code, body):
    """Return executable code plus human-readable reasons for reviewed changes."""
    number = window["window"]
    changes = []
    if ((lesson == "1.5" and number in {19, 34, 36})
            or (lesson == "1.6" and number == 21)
            or (lesson == "4.2" and number == 18)
            or (lesson == "5.2" and number in {13, 15, 17})
            or (lesson == "3.8" and number == 17)):
        window["offline_override"] = False
    if lesson == "1.5" and number in {19, 34, 36}:
        function = {19: "create_drill", 34: "inspect_dead_letter", 36: "finish_drill"}[number]
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
    if lesson == "5.2" and number == 13:
        body = '''import os, sys
session.set_environment(SELF_URL="http://localhost:8121", RAG_API_URL=os.environ["API"],
                        GOOGLE_CLOUD_PROJECT=session.config.project,
                        DOCUMIND_IMPERSONATE_SA=session.config.ui_service_account)
session.start_local_service([sys.executable, "-m", "uvicorn", "services.mcp.server:app", "--port", "8121"],
                            "http://localhost:8121/health", expected_health={"status": "ok", "self_url": "http://localhost:8121"})
print("Owned MCP server log:", session.state["local_service"]["log"])
'''
        changes.append("Start an owned server with a bounded health check and saved PID/log, instead of an unbounded shell loop. Tokens are minted in each calling demo, never stored between runs.")
    if lesson == "5.2" and number in {15, 17}:
        prefix = ('import os\nos.environ["MCP_TOKEN"] = session.identity_token("http://localhost:8121")\n')
        if number == 17:
            prefix += 'os.environ["NO_EMAIL_TOKEN"] = session.identity_token("http://localhost:8121", include_email=False)\n'
        body = prefix + body
        changes.append("Mint fresh local-server audience tokens in this process; secret tokens are intentionally excluded from persisted session state.")
    if lesson == "5.2" and number == 19:
        inner = re.search(r"python - <<'PY'\n(.*?)\nPY", code, re.S)[1]
        inner = inner.replace('open("/tmp/mcp121.log")', 'open(owned["log"], encoding="utf-8")')
        body = 'owned = session.state.get("local_service")\nsession.stop_local_service()\nif owned:\n' + '\n'.join('    '+line for line in inner.splitlines())
        changes.append("Stop only this session's verified process group and inspect its saved log; never kill an unverified saved shell PID.")
    if lesson == "3.8" and number == 17:
        body = '''from pathlib import Path
from workshop_helpers.lesson31 import LessonCloud
cloud = LessonCloud(session)
data = (Path.home() / "pune_visitor_rules.md").read_bytes()
expected = cloud.fixture("acme", "pune_visitor_rules.md", data, upload=False)
observed = cloud.wait_indexed(expected)
print("Exact UI upload:", expected, "|", observed["summary"])
cloud.worker_logs(expected)
'''
        changes.append("Verify the exact UI-uploaded bytes, source generation, claim and current chunks; an unrelated latest ingest_ok event cannot satisfy this checkpoint.")
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
    if (lesson, number) == ("3.8", 11):
        assert '--format=yaml | grep -i "iap-enabled"' in code
        code = "set +e +o pipefail   # as the page runs it: every line is a read, and grep finding nothing is an answer\n" + code
        changes.append("Run with the page's shell semantics: every line is a read. If the UI is not behind IAP, grep prints nothing and the IAP policy and the unsigned request after it show why, instead of the cell stopping at grep.")
    # A red gate on either revision is what these lessons compare; an auth, token or command failure still fails.
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
    return code, body, changes
