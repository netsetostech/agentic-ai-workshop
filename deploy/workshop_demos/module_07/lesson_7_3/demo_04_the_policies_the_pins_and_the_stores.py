"""Lesson 7.3: The policies, the pins and the stores

Do it

Run order inside this file:
1. Do it (source window 13)

Prerequisites: demo_03_the_mirror_s_rules_run.
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


# Original CLI workflow for step_01_the_policies_the_pins_and_the_stores.
COMMANDS_01 = """for t in acme zeta globex; do
  make tenant-policy PROJECT="$PROJECT" TENANT=$t        # where its text may be held
  make tenant-backend PROJECT="$PROJECT" TENANT=$t       # which store answers it
done
make managed-status PROJECT="$PROJECT"                     # every store, held against the ledger

"""

def step_01_the_policies_the_pins_and_the_stores(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme: data_region=any
    acme: retrieval_backend=vector
    zeta: data_region=any
    zeta: retrieval_backend=vertex_search
    globex: data_region=in
    globex: retrieval_backend=default (the deployment RETRIEVAL_BACKEND)
    cd services/ingest && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID RAG_LOCATION=us-central1 AUDIT_BUCKET=documind-ai-YOUR-ID-audit \\
      python managed.py --project documind-ai-YOUR-ID --status --mode both
    {"tenant": "acme", "store": "rag_engine", "ledger_current": 21, "held": 18, "missing": 3, "orphans": 0, "status": "drift", "missing_doc_keys": ["acme_0994e77d201672aa703e6d5a9a00590d117ad98239b319e900a0d6a787ede170", "acme_80403acbbf9b2ada3bb37bfa6983bd864696ed45ca459a5ad7cf0296596ca987", "acme
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_the_policies_the_pins_and_the_stores),
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
