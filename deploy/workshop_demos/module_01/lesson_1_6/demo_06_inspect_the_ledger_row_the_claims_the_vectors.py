"""Lesson 1.6: Inspect: the ledger row, the claims, the vectors

Read the three

Run order inside this file:
1. Read the three (source window 17)

Prerequisites: demo_05_do_it_revision_3_of_the_handbook_on_the_lane.
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


# Original CLI workflow for step_01_read_the_three.
COMMANDS_01 = """curl -s "$API/v1/sources?tenant_id=acme" -H "Authorization: Bearer $(tok "$API")" \\
  | python -c "import json,sys; [print(r['name'], 'chunks', r['chunks'], 'reused', r['reused'], 'embedded', r['embedded'], 'retired', r['retired'], 'effective', r['effective_from'], r['embedding']) for r in json.load(sys.stdin)['sources'] if r['name'].endswith('hr_policy_2026.md')]"

python - <<'PY'
import os, hashlib, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
PROJECT = os.environ["PROJECT"]
db = firestore.Client(project=PROJECT)
uri = f"gs://{PROJECT}-uploads/acme/hr_policy_2026.md"
v1key = "acme_" + hashlib.sha256(open("evals/corpus/acme/hr_policy_2026.md", "rb").read()).hexdigest()
claims = sorted(((s.id, s.to_dict()) for s in db.collection("documents").where("gcs_uri", "==", uri).stream()),
                key=lambda kv: str(kv[1].get("claimed_at") or ""))
print(len(claims), "claims (versions) for hr_policy_2026.md, oldest first")
for key, d in claims:
    tail = (f"  superseded_by {str(d.get('superseded_by'))[:13]}..." if d.get("superseded_by") else "") + ("  reactivated once" if d.get("reactivated_at") else "")
    print(f"  {key[:13]}...  {d.get('status'):10} chunks {d.get('chunks')}  reused {d.get('reused')}  embedded {d.get('embedded')}{tail}")
rows = [r.to_dict() for r in db.collection("chunks").where("tenant_id", "==", "acme").where("source_uri", "==", uri).stream()]
cur = {r["locator"]: r for r in rows if r.get("current")}
v1 = {r["locator"]: r for r in rows if r.get("doc_key") == v1key}
print("rows:", len(rows), "| current:", len(cur), "| retired:", len(rows) - len(cur))
for loc in ("LV-01", "NP-03"):
    print(f"  {loc:6} current hash {cur[loc]['chunk_hash'][:12]}  version 1's hash {v1[loc]['chunk_hash'][:12]}  same vector: {list(cur[loc]['embedding']) == list(v1[loc]['embedding'])}")
PY

"""

def step_01_read_the_three(session):
    """Run Read the three at this checkpoint.

    Read the three

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (the ledger row from the API, then the claims and the vectors from Firestore).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme/hr_policy_2026.md chunks 283 reused 281 embedded 2 retired 283 effective 2026-11-01 text-embedding-005@1
    3 claims (versions) for hr_policy_2026.md, oldest first
      acme_497809ff...  superseded chunks 283  reused 0  embedded 283  superseded_by acme_54337b4b...  reactivated once
      acme_55603088...  superseded chunks 283  reused 281  embedded 2  superseded_by acme_497809ff...
      acme_54337b4b...  indexed    chunks 283  reused 281  embedded 2
    rows: 849 | current: 283 | retired: 566
      LV-01  current hash ff463cede286  version 1's hash ff463cede286  same vector: True
      NP-03  current hash 876232171dec  version 1's hash f4512754ae41  same vector: False
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_17', step_01_read_the_three),
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
