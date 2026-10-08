"""Lesson 7.5: From a segment to a pill, run

Do it

Run order inside this file:
1. Do it (source window 8)

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


def step_01_from_a_segment_to_a_pill_run(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the contract and the UI's pill, run; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 1. resolve(): 2 draft citations in, 1 out ([Source 7] was not in the context):
       {'chunk_id': 'acme:77e0...#1', 'source_uri': 'gs://documind-ai-YOUR-ID-uploads/acme/townhall_2026_q1.mp4', 'page': None, 'score': 0.88, 'kind': 'segment', 'media_url': 'gs://documind-ai-YOUR-ID-uploads/acme/townhall_2026_q1.mp4', 'start': 200.7, 'end': 238.0}
    2. the answer as the UI draws it: Revenue in EMEA fell 5.2 per cent, from 96 crore to 91 crore [Clip 3, 03:20].
       under Sources: the video from second 200, captioned 03:20 – 03:58 of townhall_2026_q1.mp4
    3. the pills for the three sources: [1] [Fig 2] [Clip 3, 03:20] | a segment with no start: [Clip 3, ?]
    4. the usage row's modality: video | the same answ
    """
    import ast, re, sys
    sys.path.insert(0, ".")
    from shared.documind_schemas import ModelDraft, resolve     # the answer contract, resolved the way rag-api resolves it
    
    ns = {}                                                       # the UI's pill and clock, and the usage row's modality, lifted out
    for path, names in (("services/frontend/citations.py", ("_mmss", "_label")), ("services/rag-api/main.py", ("modality_of",))):
        for node in ast.parse(open(path, encoding="utf-8").read()).body:          # (citations.py imports streamlit; main.py the cloud clients)
            if isinstance(node, ast.FunctionDef) and node.name in names:
                exec(compile(ast.Module([node], []), path, "exec"), ns)
    
    URI = "gs://documind-ai-YOUR-ID-uploads/acme/"
    packed = [                                                    # three chunks as the budget packed them: a table row, a figure, a clip
        {"id": "acme:3f2a...#AR-02", "source_uri": URI + "annual_report_2026.md", "kind": "text", "rerank_score": 0.62,
         "text": "| EMEA | 96 | 91 | -5.2% |"},
        {"id": "acme:9c1d...#0", "source_uri": URI + "annual_report_2026_fig3.png", "kind": "figure", "media_url": URI + "annual_report_2026_fig3.png",
         "rerank_score": 0.71, "text": "Figure 3: revenue by region, FY2025 against FY2026. EMEA fell from 96 to 91 (-5.2%)."},
        {"id": "acme:77e0...#1", "source_uri": URI + "townhall_2026_q1.mp4", "kind": "segment", "media_url": URI + "townhall_2026_q1.mp4",
         "start": 200.7, "end": 238.0, "rerank_score": 0.88,
         "text": "Arjun, the CFO: EMEA is the one region that shrank; revenue fell 5.2 per cent, from 96 crore to 91 crore."},
    ]
    draft = ModelDraft(answer="Revenue in EMEA fell 5.2 per cent, from 96 crore to 91 crore [3].", confidence="high", answerable=True,
                       citations=[{"source": 3, "quote": "revenue fell 5.2 per cent, from 96 crore to 91 crore"},
                                  {"source": 7, "quote": "a source the model made up"}])
    answer = resolve(draft, packed)
    c = answer.citations[0]
    print(f"1. resolve(): {len(draft.citations)} draft citations in, {len(answer.citations)} out ([Source 7] was not in the context):")
    print("  ", c.model_dump(exclude={"quote"}))
    pill = lambda m: ns["_label"](int(m.group(1)), packed[int(m.group(1)) - 1])
    print("2. the answer as the UI draws it:", re.sub(r"\[(\d+)\]", pill, draft.answer))
    print(f"   under Sources: the video from second {int(float(c.start or 0))}, captioned {ns['_mmss'](c.start)} – {ns['_mmss'](c.end)} "
          f"of {c.source_uri.rsplit('/', 1)[-1]}")
    print("3. the pills for the three sources:", *[ns["_label"](i, s) for i, s in enumerate(packed, 1)],
          "| a segment with no start:", ns["_label"](3, {"kind": "segment"}))
    print("4. the usage row's modality:", ns["modality_of"]([x.kind for x in answer.citations]),
          "| the same answer from the table and the figure:", ns["modality_of"](["text", "figure"]))
    for cited in (3, 1):                                          # run_eval's rule for a media row: mm-03 asks for a segment
        one = ModelDraft(answer=draft.answer, confidence="high", answerable=True, citations=[{"source": cited, "quote": "5.2 per cent"}])
        kinds = sorted({x.kind for x in resolve(one, packed).citations})
        print(f"5. mm-03, citing [Source {cited}]: kinds {kinds} -> {'counts' if 'segment' in kinds else 'cited no segment'}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_8', step_01_from_a_segment_to_a_pill_run),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
