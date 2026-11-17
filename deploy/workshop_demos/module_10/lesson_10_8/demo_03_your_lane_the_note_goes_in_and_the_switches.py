"""Lesson 10.8: Your lane: the note goes in, and the switches

make ingest-one puts one object under acme's prefix in the uploads bucket and waits for the worker's ingest_ok line. The note has no entry in acme's registry, so it ingests as doc_type unknown, as the next step's code says. make sources lists the ledger's current versions; the grep keeps the note's row. Then export the two agent addresses the rest of the page uses, and read the peer's switches: /health says tool_pins off and agent_fence false as lesson 10.6's deploy script leaves them. There is no make target for the switches: they are service environment variables, set the way make limits-drill sets others. The update makes a new documind-chat revision that serves at once, as long as the service's traffic follows its latest revision, which make limits-drill and make handoff check the same way before they change a variable; gcloud run services update-traffic documind-chat --to-latest puts it back if it does not. Step 9 turns them off again around the same cell, and step 12 leaves them off.

Run order inside this file:
1. Do it: the note into acme's corpus (source window 7)
2. Do it: both chat switches on (source window 9)

Prerequisites: setup_prepare.
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


# Original CLI workflow for step_01_the_note_into_acme_s_corpus.
COMMANDS_01 = """if make -s sources PROJECT="$PROJECT" TENANT_ONLY=acme 2>/dev/null | grep -Eq "^acme/vendor_note_acme.md +withdrawn"; then
  # a second run: the lesson's own cleanup withdrew the note, and the same bytes uploaded again stay withdrawn
  make restore PROJECT="$PROJECT" SOURCE=acme/vendor_note_acme.md
  for i in $(seq 1 30); do
    make -s sources PROJECT="$PROJECT" TENANT_ONLY=acme 2>/dev/null | grep -Eq "^acme/vendor_note_acme.md +indexed" && break; sleep 10
  done
else
  make ingest-one PROJECT="$PROJECT" TENANT=acme FILE=evals/adversarial/vendor_note_acme.md
fi
make sources PROJECT="$PROJECT" TENANT_ONLY=acme | grep -i vendor_note
export CHAT="https://documind-chat-$NUMBER.$REGION.run.app" AGENT="https://documind-agent-$NUMBER.$REGION.run.app"
curl -s -H "Authorization: Bearer $(tok "$AGENT")" "$AGENT/health"; echo

"""

def step_01_the_note_into_acme_s_corpus(session):
    """Run Do it: the note into acme's corpus at this checkpoint.

    make ingest-one puts one object under acme's prefix in the uploads bucket and waits for the worker's ingest_ok line. The note has no entry in acme's registry, so it ingests as doc_type unknown, as the next step's code says. make sources lists the ledger's current versions; the grep keeps the note's row. Then export the two agent addresses the rest of the page uses, and read the peer's switches: /health says tool_pins off and agent_fence false as lesson 10.6's deploy script leaves them.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the note into acme's bucket, the worker's line, the ledger row, the peer's switches).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ingest.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_both_chat_switches_on.
COMMANDS_02 = """gcloud run services update documind-chat --region "$REGION" --project "$PROJECT" --quiet \\
  --update-env-vars AGENT_FENCE=on,AGENT_SCRUB=on

"""

def step_02_both_chat_switches_on(session):
    """Run Do it: both chat switches on at this checkpoint.

    There is no make target for the switches: they are service environment variables, set the way make limits-drill sets others. The update makes a new documind-chat revision that serves at once, as long as the service's traffic follows its latest revision, which make limits-drill and make handoff check the same way before they change a variable; gcloud run services update-traffic documind-chat --to-latest puts it back if it does not. Step 9 turns them off again around the same cell, and step 12 leaves them off.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a new documind-chat revision with both switches on).
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
        ('source_7', step_01_the_note_into_acme_s_corpus),
        ('source_9', step_02_both_chat_switches_on),
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
