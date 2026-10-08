"""Lesson 1.3: Carry-over: re-issue the handbook, embed only what changed

The worker's planner on the two versions of the handbook, with a stand-in for what held_vectors() would lend: one vector per version-1 hash. The upload must keep the object name, acme/hr_policy_2026.md, or it is a new source and nothing is held. The loop then waits for the worker's ingest_ok line and prints its counts. Cost: two clauses, 453 characters, about a hundredth of a paisa; a Markdown file pays no Document AI. Refresh Documents. The handbook's row in the Versions table now reads reused 281, embedded 2, retired 283, with an effective date of 1 October 2026 that the revision declares in its first lines. The first call below is the same row from the API; the second reads the rows themselves and checks the thing the counts claim: an unchanged clause's new row carries the same numbers as its retired predecessor, and a changed clause's does not. The third asks the question the revision changed the answer to. Upload version 1 again under the same name. Its doc_key is the one the lane retired a minute ago, so the worker does not parse, chunk or embed anything: it flips the retired rows back to current, retires revision 2, and logs ingest_reactivated with embedded 0. This is the undo from lesson 1.1, seen from the embedding side: nothing was ever deleted, so nothing has to be made again.

Run order inside this file:
1. Plan it locally, Rs 0 (source window 33)
2. Do it on the lane: revision 2 over the same name (source window 35)
3. See it in the UI, then read it three more ways (source window 37)
4. Undo it: the same bytes again, and nothing is embedded (source window 39)

Prerequisites: demo_06_validate_the_stamp_and_the_function_that_reads_it.
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


def step_01_plan_it_locally_rs_0(session):
    """Run Plan it locally, Rs 0 at this checkpoint.

    The worker's planner on the two versions of the handbook, with a stand-in for what held_vectors() would lend: one vector per version-1 hash.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: v2: 283 chunks, reused 281, to embed 2: ['preamble', 'NP-03']
      preamble: hash 903e2b39ee92 -> b4736d2f3e52
      NP-03: hash f4512754ae41 -> 876232171dec
    """
    import os, sys
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", os.environ["PROJECT"])
    sys.path[:0] = [".", "services/ingest"]
    from shared import documind_corpus as dc
    from indexer import plan_carry_over
    def cut(path):
        """Parse and chunk the supplied handbook input with the kit parser; retain its real section identities.
        
        Example: cut('evals/corpus/acme/hr_policy_2026.md')
        """
        text = open(path, encoding="utf-8").read()
        return dc.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://x", "text": text}, "acme")
    v1, v2 = cut("evals/corpus/acme/hr_policy_2026.md"), cut("evals/demo/hr_policy_2026_v2.md")
    held = {c["chunk_hash"]: ["the v1 vector"] for c in v1}          # what held_vectors() would lend: one per v1 hash
    vectors, misses = plan_carry_over(v2, held)
    print(f"v2: {len(v2)} chunks, reused {len(v2) - len(misses)}, to embed {len(misses)}: {[v2[i]['locator'] for i in misses]}")
    for i in misses:
        old = next(c for c in v1 if c["locator"] == v2[i]["locator"])
        print(f"  {v2[i]['locator']}: hash {old['chunk_hash'][:12]} -> {v2[i]['chunk_hash'][:12]}")

# Original CLI workflow for step_02_on_the_lane_revision_2_over_the_same_name.
COMMANDS_02 = """SINCE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
gcloud storage cp evals/demo/hr_policy_2026_v2.md "gs://$PROJECT-uploads/acme/hr_policy_2026.md"
for i in $(seq 1 30); do sleep 10
  LINE="$(gcloud logging read "resource.type=\\"cloud_run_revision\\" AND resource.labels.service_name=\\"documind-ingest\\" AND jsonPayload.event=\\"ingest_ok\\" AND jsonPayload.tenant=\\"acme\\" AND timestamp>=\\"$SINCE\\"" \\
    --project "$PROJECT" --limit 1 --format='value(jsonPayload.chunks,jsonPayload.reused,jsonPayload.embedded,jsonPayload.retired,jsonPayload.effective_from)')"
  [ -n "$LINE" ] && { echo ">> chunks reused embedded retired effective_from: $LINE"; break; }
done

"""

def step_02_on_the_lane_revision_2_over_the_same_name(session):
    """Run Do it on the lane: revision 2 over the same name at this checkpoint.

    The upload must keep the object name, acme/hr_policy_2026.md, or it is a new source and nothing is held. The loop then waits for the worker's ingest_ok line and prints its counts. Cost: two clauses, 453 characters, about a hundredth of a paisa; a Markdown file pays no Document AI.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (one re-issue; the worker takes under a minute).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> chunks reused embedded retired effective_from: 283	281	2	283	2026-10-01
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_see_it_in_the_ui_then_read_it_three_more_w.
COMMANDS_03 = """curl -s "$API/v1/sources?tenant_id=acme" -H "Authorization: Bearer $(tok "$API")" \\
  | python -c "import json,sys; [print(r['name'], 'chunks', r['chunks'], 'reused', r['reused'], 'embedded', r['embedded'], 'retired', r['retired'], 'effective', r['effective_from'], r['embedding']) for r in json.load(sys.stdin)['sources'] if r['name'].endswith('hr_policy_2026.md')]"

python - <<'PY'
import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
PROJECT = os.environ["PROJECT"]
db = firestore.Client(project=PROJECT)
rows = [s.to_dict() for s in db.collection("chunks").where("tenant_id", "==", "acme")
        .where("source_uri", "==", f"gs://{PROJECT}-uploads/acme/hr_policy_2026.md").stream()]
print("rows for the source:", len(rows), "| current:", sum(r["current"] for r in rows), "| retired:", sum(not r["current"] for r in rows))
for loc in ("LV-01", "NP-03", "preamble"):
    cur = next(r for r in rows if r["locator"] == loc and r["current"])
    old = max((r for r in rows if r["locator"] == loc and not r["current"]), key=lambda r: r["indexed_at"])
    print(f"  {loc:9} hash {old['chunk_hash'][:12]} -> {cur['chunk_hash'][:12]}   same vector: {list(old['embedding']) == list(cur['embedding'])}")
PY

curl -s -X POST $API/v1/query -H "Authorization: Bearer $(tok $API)" -H "Content-Type: application/json" \\
  -d '{"query":"How many days of notice does a confirmed employee at grade E3 serve?","tenant_id":"acme","stream":false}' \\
  | python -c "import json,sys; j=json.load(sys.stdin); print(j['answer'][:140]); print([(c['chunk_id'].split('#')[1], c['source_uri'].split('/')[-1]) for c in j['citations'][:2]], j['stages']['retrieval_backend'])"

"""

def step_03_see_it_in_the_ui_then_read_it_three_more_w(session):
    """Run See it in the UI, then read it three more ways at this checkpoint.

    Refresh Documents. The handbook's row in the Versions table now reads reused 281, embedded 2, retired 283, with an effective date of 1 October 2026 that the revision declares in its first lines. The first call below is the same row from the API; the second reads the rows themselves and checks the thing the counts claim: an unchanged clause's new row carries the same numbers as its retired predecessor, and a changed clause's does not. The third asks the question the revision changed the answer to.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme/hr_policy_2026.md chunks 283 reused 281 embedded 2 retired 283 effective 2026-10-01 text-embedding-005@1
    rows for the source: 566 | current: 283 | retired: 283
      LV-01     hash ff463cede286 -> ff463cede286   same vector: True
      NP-03     hash f4512754ae41 -> 876232171dec   same vector: False
      preamble  hash 903e2b39ee92 -> b4736d2f3e52   same vector: False
    A confirmed employee at grade E3 or above serves a notice period of 90 days ... [Source 1]
    [('1', 'hr_policy_2026.md'), ('2', 'hr_policy_2026.md')] vector
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_undo_it_the_same_bytes_again_and_nothing_i.
COMMANDS_04 = """SINCE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
gcloud storage cp evals/corpus/acme/hr_policy_2026.md "gs://$PROJECT-uploads/acme/hr_policy_2026.md"
for i in $(seq 1 30); do sleep 10
  LINE="$(gcloud logging read "resource.type=\\"cloud_run_revision\\" AND resource.labels.service_name=\\"documind-ingest\\" AND jsonPayload.event=\\"ingest_reactivated\\" AND jsonPayload.tenant=\\"acme\\" AND timestamp>=\\"$SINCE\\"" \\
    --project "$PROJECT" --limit 1 --format='value(jsonPayload.chunks,jsonPayload.reused,jsonPayload.embedded,jsonPayload.retired)')"
  [ -n "$LINE" ] && { echo ">> reactivated: chunks reused embedded retired: $LINE"; break; }
done

curl -s -X POST $API/v1/query -H "Authorization: Bearer $(tok $API)" -H "Content-Type: application/json" \\
  -d '{"query":"How many days of notice does a confirmed employee at grade E3 serve?","tenant_id":"acme","stream":false}' \\
  | python -c "import json,sys; print(json.load(sys.stdin)['answer'][:120])"

"""

def step_04_undo_it_the_same_bytes_again_and_nothing_i(session):
    """Run Undo it: the same bytes again, and nothing is embedded at this checkpoint.

    Upload version 1 again under the same name. Its doc_key is the one the lane retired a minute ago, so the worker does not parse, chunk or embed anything: it flips the retired rows back to current, retires revision 2, and logs ingest_reactivated with embedded 0. This is the undo from lesson 1.1, seen from the embedding side: nothing was ever deleted, so nothing has to be made again.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the undo; no model call).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> reactivated: chunks reused embedded retired: 283	283	0	283
    A confirmed employee at grade E3 or above serves a notice period of 60 days ... [Source 1]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_33', step_01_plan_it_locally_rs_0),
        ('source_35', step_02_on_the_lane_revision_2_over_the_same_name),
        ('source_37', step_03_see_it_in_the_ui_then_read_it_three_more_w),
        ('source_39', step_04_undo_it_the_same_bytes_again_and_nothing_i),
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
