"""Lesson 1.8: Create this chapter's note and the checks

A fresh name, a new fact and an unchanged local copy remove the dependencies on earlier lessons. This chapter does not use ~/lesson34_note.md or the smoke-lantern question. Another smoke note may still answer that question even after one copy is retired. Our primary checks are the exact source name, its object generation and its citation; a bare answerable True is insufficient. The helper block is preparation, not a slide to type live. It stops on failed uploads, polls the exact source and generation, checks citations, and refuses to apply an unexplained tenant-wide plan. The log filter includes both the version key and generation, so another acme upload cannot satisfy the wait. To resume after reopening a shell, first run the shared shell setup, then source this directory's session.env and helpers.sh; do not create a new note midway through a restore.

Run order inside this file:
1. Create this chapter's note and the checks (source window 11)
2. Load the checks once (source window 12)

Prerequisites: demo_03_credentials_backend_and_a_clean_baseline.
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


# Original CLI workflow for step_01_create_this_chapter_s_note_and_the_checks.
COMMANDS_01 = """export NOTE="$DEMO_DIR/note.md"
export SOURCE="acme/lesson44_${RUN_ID}.md"
export OBJECT="gs://${PROJECT}-uploads/$SOURCE"
export QUESTION="Where is the violet compass for drill $RUN_ID stored?"
cat > "$NOTE" <<EOF
# Recovery drill $RUN_ID

The violet compass for drill $RUN_ID is stored in locker Q7
in the Jaipur training room.
EOF
sha256sum "$NOTE" > "$DEMO_DIR/note.sha256"
export DOC_KEY="acme_$(sha256sum "$NOTE" | cut -d ' ' -f1)"
python - <<'PY'
import json, os
from pathlib import Path
Path(os.environ["DEMO_DIR"], "query.json").write_text(json.dumps({
    "query": os.environ["QUESTION"], "tenant_id": "acme", "stream": False
}), encoding="utf-8")
PY
declare -p RUN_ID DEMO_DIR NOTE SOURCE OBJECT QUESTION DOC_KEY > "$DEMO_DIR/session.env"
printf 'Keep this directory for the whole demo: %s\\n' "$DEMO_DIR"

"""

def step_01_create_this_chapter_s_note_and_the_checks(session):
    """Run Create this chapter's note and the checks at this checkpoint.

    A fresh name, a new fact and an unchanged local copy remove the dependencies on earlier lessons. This chapter does not use ~/lesson34_note.md or the smoke-lantern question. Another smoke note may still answer that question even after one copy is retired. Our primary checks are the exact source name, its object generation and its citation; a bare answerable True is insufficient.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run once; keep the note and its checksum unchanged.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_load_the_checks_once.
COMMANDS_02 = """cat > "$DEMO_DIR/helpers.sh" <<'SH'
set -o pipefail

ch44_source() {
  local token
  token="$(tok "$API")" || return
  curl -fsS "$API/v1/sources?tenant_id=acme" \\
    -H "Authorization: Bearer $token" |
    python -c 'import json,sys
j=json.load(sys.stdin)
r=next((r for r in j["sources"] if r["name"]==sys.argv[1]),None)
print(json.dumps(r,indent=2))' "$SOURCE" > "$DEMO_DIR/source.json" || return
  cat "$DEMO_DIR/source.json"
}

ch44_ask() {
  local token
  token="$(tok "$API")" || return
  curl -fsS "$API/v1/query" -H "Authorization: Bearer $token" \\
    -H "Content-Type: application/json" \\
    --data-binary @"$DEMO_DIR/query.json" > "$DEMO_DIR/answer.json" || return
  python - "$1" <<'PY'
import json, os, sys
from pathlib import Path
j=json.loads(Path(os.environ["DEMO_DIR"], "answer.json").read_text())
backend=j.get("stages", {}).get("retrieval_backend")
cited=any(c.get("source_uri")==os.environ["OBJECT"] for c in j.get("citations", []))
print("retrieval:", backend, "| answerable:", j["answerable"], "| fixture cited:", cited)
print(j["answer"])
for c in j.get("citations", []):
    print("citation:", c.get("source_uri"), "|", c.get("quote", ""))
assert backend=="vector", "Wait for the backend pin to refresh; inspect the returned stages."
if sys.argv[1]=="present":
    assert j["answerable"] and cited, "The answer must cite this exact fixture."
    assert "Q7" in j["answer"] and "Jaipur" in j["answer"], "Check the fixture's stated location."
else:
    assert not cited, "The retired fixture is still cited; inspect retrieval and propagation."
    if j["answerable"]:
        print("Another source answered. This is not proof that the fixture is still indexed.")
PY
}

ch44_logs() {
  gcloud logging read "resource.type=\\"cloud_run_revision\\" AND resource.labels.service_name=\\"documind-ingest\\" AND jsonPayload.doc_key=\\"$DOC_KEY\\" AND jsonPayload.generation=\\"$CH44_GENERATION\\" AND timestamp>=\\"$CH44_SINCE\\"" \\
    --project "$PROJECT" --limit 10 \\
    --format='table(timestamp,jsonPayload.event,jsonPayload.chunks,jsonPayload.reused,jsonPayload.embedded,jsonPayload.error)'
}

ch44_upload() {
  sha256sum -c "$DEMO_DIR/note.sha256" || return
  export CH44_SINCE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  gcloud storage cp "$NOTE" "$OBJECT" || return
  CH44_GENERATION="$(gcloud storage objects describe "$OBJECT" --format='value(generation)')" || return
  export CH44_GENERATION
  [ -n "$CH44_GENERATION" ] || return 1
  for attempt in $(seq 1 30); do
    ch44_source > /dev/null || return
    if python - <<'PY'
import json, os, sys
from pathlib import Path
r=json.loads(Path(os.environ["DEMO_DIR"], "source.json").read_text()) or {}
ready=(r.get("status")=="indexed"
       and str(r.get("generation"))==os.environ["CH44_GENERATION"]
       and r.get("doc_key")==os.environ["DOC_KEY"])
sys.exit(0 if ready else 1)
PY
    then cat "$DEMO_DIR/source.json"; return 0; fi
    sleep 10
  done
  echo "STOP: this upload did not reach indexed state within five minutes."
  ch44_logs
  return 1
}

ch44_plan() {
  make --no-print-directory reconcile PROJECT="$PROJECT" TENANT_ONLY=acme \\
    > "$DEMO_DIR/plan.txt" || { cat "$DEMO_DIR/plan.txt"; return 1; }
  cat "$DEMO_DIR/plan.txt"
  python - "$1" <<'PY'
import json, os, sys
from pathlib import Path
rows=[json.loads(s) for s in Path(os.environ["DEMO_DIR"], "plan.txt").read_text().splitlines()
      if s.startswith("{")]
summary=next(r for r in reversed(rows) if r.get("event")=="reconcile_done")
repairs=[r for r in rows if r.get("reconcile") in ("retire","reingest","backfill","touch")]
assert summary.get("applied") is False, "Expected a read-only plan."
if sys.argv[1]=="clean":
    assert summary["drift"]==0 and not repairs, "Resolve unrelated repairs before the live demo."
else:
    assert len(repairs)==1 and repairs[0]["reconcile"]=="retire" \\
        and repairs[0]["name"]==os.environ["SOURCE"], "STOP: plan includes unexpected work."
    assert summary["drift"]==1
print("Checkpoint passed:", sys.argv[1])
PY
}
SH
source "$DEMO_DIR/helpers.sh"
ch44_plan clean

"""

def step_02_load_the_checks_once(session):
    """Run Load the checks once at this checkpoint.

    The helper block is preparation, not a slide to type live. It stops on failed uploads, polls the exact source and generation, checks citations, and refuses to apply an unexplained tenant-wide plan. The log filter includes both the version key and generation, so another acme upload cannot satisfy the wait. To resume after reopening a shell, first run the shared shell setup, then source this directory's session.env and helpers.sh; do not create a new note midway through a restore.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — save and load the chapter checks; no cloud writes in this block.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_11', step_01_create_this_chapter_s_note_and_the_checks),
        ('source_12', step_02_load_the_checks_once),
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
