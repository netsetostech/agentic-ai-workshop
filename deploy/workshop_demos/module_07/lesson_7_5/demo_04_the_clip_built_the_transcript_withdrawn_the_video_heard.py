"""Lesson 7.5: The clip built, the transcript withdrawn, the video heard

make media MEDIA_ARGS=--video runs evals/build_media.py: Next, the transcript goes. upload.sh keeps a transcript home once its video exists, as it keeps a PDF's text mirror home, but it removes nothing already sent: make retire withdraws it as lesson 7.4 showed. The rows are retired, acme's two managed stores delete their copies, and the ledger row becomes a tombstone. The object stays in the bucket, and make restore would bring it back. make retire withdraws it as lesson 7.4 showed. The rows are retired, acme's two managed stores delete their copies, and the ledger row becomes a tombstone. The object stays in the bucket, and make restore would bring it back. Then the video goes up as a new document. make reindex copies it into acme's uploads and waits for the worker's line. The worker's media branch describes it in one Gemini call: Then the video goes up as a new document. make reindex copies it into acme's uploads and waits for the worker's line. The worker's media branch describes it in one Gemini call: Last, read the video's rows from acme's index, and hold them against the ground truth:

Run order inside this file:
1. Definition (source window 10)
2. Definition (source window 13)
3. Definition (source window 16)
4. Definition (source window 18)

Prerequisites: demo_03_from_a_segment_to_a_pill_run.
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


# Original CLI workflow for step_01_definition.
COMMANDS_01 = """python -m pip install -q Pillow==12.3.0 google-cloud-texttospeech==2.37.0 imageio-ffmpeg==0.6.0   # slides, voices, a static ffmpeg
make media MEDIA_ARGS=--video

"""

def step_01_definition(session):
    """Run Definition at this checkpoint.

    make media MEDIA_ARGS=--video runs evals/build_media.py:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the town hall synthesised: a minute or two).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/build_media.py --video
      keep annual_report_2026_fig3.png (43 KB) - exists; --force re-renders
      keep inv_2026_0412.png (123 KB) - exists; --force re-renders
      keep payment_of_bonus_act_1965_p30.png (151 KB) - exists; --force re-renders
      voices: {'Meera': 'en-IN-Chirp3-HD-Aoede', 'Arjun': 'en-IN-Chirp3-HD-Charon'}
      Meera    0.0-  21.5s  Good morning, everyone, and welcome to the FY2026 town hall....
      Arjun   22.2-  57.7s  Thanks, Meera. Let me start with the table you all have on s...
      Meera   58.4-  69.6s  On people, headcount closed at 4,180, up from 3,742, and att...
      Arjun   70.3-  93.1s  On capital expenditure we invested 78 crore during the year....
      Meera   93.8- 10
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_definition.
COMMANDS_02 = """make retire PROJECT="$PROJECT" SOURCE=acme/townhall_2026_q1.md

"""

def step_02_definition(session):
    """Run Definition at this checkpoint.

    Next, the transcript goes. upload.sh keeps a transcript home once its video exists, as it keeps a PDF's text mirror home, but it removes nothing already sent: make retire withdraws it as lesson 7.4 showed. The rows are retired, acme's two managed stores delete their copies, and the ledger row becomes a tombstone. The object stays in the bucket, and make restore would bring it back.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the transcript withdrawn from acme).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"event": "reconcile_withdrawn", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/acme/townhall_2026_q1.md", "fingerprint": "1a19e8a7d490616d", "retired_doc_keys": ["acme_b0d7702de2bf5a7d0770de433916af821b4a83f13ca321e074293ef99f4d75c1"], "retired_ids": ["acme:b0d7702de2bf5a7d0770de433916af821b4a83f13ca321e074293ef99f4d75c1#0"], "retired_chunks": 1, "note": "a tombstone: the object is kept and nothing automatic re-ingests it; make restore SOURCE= does"}
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_definition.
COMMANDS_03 = """make reindex PROJECT="$PROJECT" TENANT=acme FILE=evals/corpus/acme/townhall_2026_q1.mp4

"""

def step_03_definition(session):
    """Run Definition at this checkpoint.

    make retire withdraws it as lesson 7.4 showed. The rows are retired, acme's two managed stores delete their copies, and the ledger row becomes a tombstone. The object stays in the bucket, and make restore would bring it back. Then the video goes up as a new document. make reindex copies it into acme's uploads and waits for the worker's line. The worker's media branch describes it in one Gemini call:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the video uploaded; waits for the worker).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ...
    >> gs://documind-ai-YOUR-ID-uploads/acme/townhall_2026_q1.mp4 - waiting for the worker (up to 5 min)
    >> event doc_key chunks reused embedded retired effective_from
    >> ingest_ok	acme_a85a89590f9a2b8b7ffc8588e11578297c5bc1fe5181482b0ef75d22d00881d3	5	0	5	0	
    >> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=townhall_2026_q1.mp4 API=<candidate url>
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def step_04_definition(session):
    """Run Definition at this checkpoint.

    Then the video goes up as a new document. make reindex copies it into acme's uploads and waits for the worker's line. The worker's media branch describes it in one Gemini call: Last, read the video's rows from acme's index, and hold them against the ground truth:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 5 segments of townhall_2026_q1.mp4 in acme's index, against the ground truth's 5 turns:
      segment t0-22     00:00-00:22   22 s  over Meera 00:00
          Meera, the CEO, opens the FY2026 town hall over a first slide saying the video is synthetic, welcoming s...
      segment t22-58    00:22-00:58   36 s  over Arjun 00:22
          Arjun, the CFO, walks through the revenue table on slide two: India grew from 412 to 508 crore, up 23.3 ...
      segment t58-70    00:58-01:10   12 s  over Meera 00:58
          Meera says headcount closed at 4,180, up from 3,742, and attrition came down to 11.4 per cent from 14.9 ...
      segment t70-93    01:10-01:33   23 s  over Arjun 01:10
          Arjun says capital expenditure was 7
    """
    import json, os
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
    P = os.environ["PROJECT"]
    URI = f"gs://{P}-uploads/acme/townhall_2026_q1.mp4"
    db = firestore.Client(project=P)
    rows = [d.to_dict() for d in db.collection("chunks").where(filter=FieldFilter("tenant_id", "==", "acme"))
            .where(filter=FieldFilter("source_uri", "==", URI)).where(filter=FieldFilter("current", "==", True)).stream()]
    truth = json.load(open("evals/corpus/acme/townhall_2026_q1.segments.json", encoding="utf-8"))["segments"]
    mmss = lambda s: f"{int(s) // 60:02d}:{int(s) % 60:02d}"
    print(f"{len(rows)} segments of townhall_2026_q1.mp4 in acme's index, against the ground truth's {len(truth)} turns:")
    for r in sorted(rows, key=lambda r: r["start"]):
        heard = [f"{t['speaker']} {mmss(t['start'])}" for t in truth if min(t["end"], r["end"]) - max(t["start"], r["start"]) > 1]   # a second of the turn or more
        print(f"  {r['kind']} {r['locator']:9} {mmss(r['start'])}-{mmss(r['end'])} {r['end'] - r['start']:4.0f} s  over {', '.join(heard) or 'nobody'}")
        print(f"      {r['text'][:104]}...")
    longest = max(r["end"] - r["start"] for r in rows)
    bad = [r["locator"] for r in rows if not 0 <= r["start"] < r["end"]]
    video_end = truth[-1]["end"]
    print(f"checks: longest {longest:.0f} s (the prompt asks for at most 60) -> {'PASS' if longest <= 60 else 'FAIL'}; "
          f"start before end in every row -> {'PASS' if not bad else 'FAIL ' + ', '.join(bad)}; "
          f"last end {mmss(max(r['end'] for r in rows))} against the speech's end {mmss(video_end)}")
    said = next(t for t in truth if "5.2 per cent" in t["text"])
    hit = [r["locator"] for r in rows if r["start"] <= said["end"] and r["end"] >= said["start"] and "5.2 per cent" in r["text"]]
    print(f"the EMEA line: {said['speaker']} says '5.2 per cent' in the turn at {mmss(said['start'])}-{mmss(said['end'])}; "
          f"the segment that quotes it: {', '.join(hit) or 'none'}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_10', step_01_definition),
        ('source_13', step_02_definition),
        ('source_16', step_03_definition),
        ('source_18', step_04_definition),
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
