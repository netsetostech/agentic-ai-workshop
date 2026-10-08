"""Lesson 1.5: The batch lane: the 250-page decision, the queued claim, the job

Optional, and it costs money (the page's own box): join the CGST and IT Acts into a 270-page PDF and upload it to acme. The worker queues it for the batch lane. Where the batch job is declared it parses all 270 pages at once: about Rs 34 on the OCR processor or Rs 230 on the Layout Parser, plus embeddings. The page leaves the PDF in acme's uploads. Decide before you run it.

Run order inside this file:
1. Read the lane, Rs 0 (source window 30)

Prerequisites: demo_06_the_batch_lane_the_250_page_decision_the_queued_claim_the_job.
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


# Original CLI workflow for step_01_read_the_lane_rs_0.
COMMANDS_01 = """python - <<'PY'
from pypdf import PdfReader, PdfWriter
w = PdfWriter()
for path in ("evals/corpus/acme/cgst_act_2017.pdf", "evals/corpus/acme/it_act_2000.pdf"):
    for page in PdfReader(path).pages:
        w.add_page(page)
with open("/tmp/cgst_it_bundle.pdf", "wb") as f:
    w.write(f)
print("bundle pages:", len(PdfReader("/tmp/cgst_it_bundle.pdf").pages))
PY

SINCE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
gcloud storage cp /tmp/cgst_it_bundle.pdf "gs://$PROJECT-uploads/acme/cgst_it_bundle.pdf"
for i in $(seq 1 30); do sleep 10
  LINE="$(gcloud logging read "resource.type=\\"cloud_run_revision\\" AND resource.labels.service_name=\\"documind-ingest\\" AND jsonPayload.event=\\"ingest_queued_batch\\" AND timestamp>=\\"$SINCE\\"" \\
    --project "$PROJECT" --limit 1 --format='value(jsonPayload.pages,jsonPayload.consumer)')"
  [ -n "$LINE" ] && { echo ">> queued: pages, consumer: $LINE"; break; }
done
make queued PROJECT=$PROJECT

"""

def step_01_read_the_lane_rs_0(session):
    """Run Read the lane, Rs 0 at this checkpoint.

    The queue is a Firestore query the kit prints for you. The job and its schedule exist only if BATCH_JOB was set when the lane was deployed; the box above the setup read it off the worker. The corpus has no PDF over 250 pages, so the drill makes one: the CGST Act (236 pages) and the IT Act (34) joined with pypdf on your machine, at no cost. Uploading it costs nothing either, and that is the point of the first half: the worker counts 270 pages, writes the queued claim, answers 200, and no page has been sent to Document AI. The second half is where the money goes. When the job is declared, the worker starts it at once and it parses all 270 pages: about Rs 34 on the OCR processor, about Rs 230 on the Layout Parser (at the list prices lesson 1.2 quoted and Rs 85 to the dollar), plus a few rupees of embeddings for roughly six hundred windows. When the job is not declared, the claim simply waits, and make queued shows it. Decide before you upload.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the join is free; the upload starts the paid parse if the job is declared).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: bundle pages: 270
    >> queued: pages, consumer: 270	documind-ingest-batch started (run requested); the hourly schedule backstops it
    1 queued document(s)
      acme_3ff3f2ac3237...  gs://documind-ai-YOUR-ID-uploads/acme/cgst_it_bundle.pdf  pages=270  generation=1758543112345678
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_30', step_01_read_the_lane_rs_0),
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
