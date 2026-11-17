"""Lesson 3.6: Offline: nine quotes through both measures, and the gate's own lines over a stand-in API

Do it: nine quotes, two measures The cell plays the API. Each row's /v1/query reply carries the row's figure and one citation, made by resolve() from a draft, so its quote reaches the gate exactly as rag-api would hand it on. Each row's /v1/passages reply is six handbook passages, the row's own clause first. Four rows are planted: lk-04 quotes its probation sentence under NP-03's number, lk-06 paraphrases, lk-08 leaves the quote empty, and lk-09's pool comes back without the passage it cites. The other six quote the first sentence of their clause.

Run order inside this file:
1. Do it: nine quotes, two measures (source window 10)
2. Do it: the gate's own lines, over a stand-in API (source window 12)

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


def step_01_nine_quotes_two_measures(session):
    """Run Do it: nine quotes, two measures at this checkpoint.

    Do it: nine quotes, two measures

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a Python cell; Rs 0: nothing leaves the machine).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: case                                    chars  quote_check  judge_citations
    the sentence, under its own passage        76  own          supported
    a line break, in capitals                  69  own          supported
    the same sentence, under [2]               76  elsewhere    supported
    a paraphrase                               40  absent       not supported
    revision 2's figure                        76  absent       not supported
    an empty quote, filled in by resolve()    234  substituted  supported
    _draft()'s cut of a whole section         200  own          not supported
    an elision, mid-sentence                   59  absent       not supported
    a passage the pool did not hold            76  u
    """
    import hashlib, re, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = [".", "evals"]
    import run_eval as rv                                                  # the gate: judge_citations() and quote_check()
    from shared import documind_corpus as dc
    from shared.documind_schemas import DraftCitation, ModelDraft, resolve
    raw = open("evals/corpus/acme/hr_policy_2026.md", "rb").read()
    sha, uri = hashlib.sha256(raw).hexdigest(), "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md"
    cut = dc.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": uri, "text": raw.decode("utf-8")}, "acme")
    P = {c["locator"]: {"chunk_id": f"acme:{sha}#{i}", "source_uri": uri, "text": c["text"]} for i, c in enumerate(cut)}
    pool = [P[k] for k in ("NP-03", "PB-02", "LV-07", "LV-01", "GEN-000", "GEN-001")]   # six passages, ids as the worker mints them
    corpus = re.sub(r"\s+", " ", rv.haystack(rv.load_corpus(), "acme"))  # what judge_citations() searches: every acme mirror
    row = next(r for r in rv.load_golden() if r["id"] == "lk-06")
    said = "A confirmed employee at grade E3 or above serves a notice period of 60 days."
    whole = " ".join(P["GEN-000"]["text"].split("\n", 1)[1].split())     # a whole section, longer than a draft's 200 characters
    empty = resolve(ModelDraft(answer="60 days [1].", confidence="high", answerable=True,
                               citations=[DraftCitation(source=1, quote="")]), pool).citations[0].quote
    cases = [("NP-03", said, "the sentence, under its own passage"),
             ("NP-03", "NOTICE RUNS from the date the resignation is acknowledged in writing.", "a line break, in capitals"),
             ("PB-02", said, "the same sentence, under [2]"),
             ("NP-03", "Confirmed E3 staff give 60 days' notice.", "a paraphrase"),
             ("NP-03", said.replace("60 days", "90 days"), "revision 2's figure"),
             ("NP-03", empty, "an empty quote, filled in by resolve()"),
             ("GEN-000", whole[:200 - 3].rstrip() + "...", "_draft()'s cut of a whole section"),
             ("NP-03", "A confirmed employee ... serves a notice period of 60 days.", "an elision, mid-sentence"),
             ("EXP-12", said, "a passage the pool did not hold")]
    got = []
    print(f"{'case':39} {'chars':>5}  {'quote_check':12} judge_citations")
    for code, quote, label in cases:
        c = {"chunk_id": P[code]["chunk_id"], "source_uri": uri, "quote": quote}
        verdict, supported = rv.quote_check(c, pool), rv.judge_citations(row, [c], None, {}, corpus)[1]
        got.append((verdict, supported))
        print(f"{label:39} {len(quote):5}  {verdict:12} {'supported' if supported else 'not supported'}")
    print("quote_check: " + ", ".join(f"{v} {sum(g == v for g, _ in got)}" for v in rv.QUOTE_VERDICTS)
          + f" | judge_citations: supported {sum(s for _, s in got)} of {len(got)}")

def step_02_the_gate_s_own_lines_over_a_stand_in_api(session):
    """Run Do it: the gate's own lines, over a stand-in API at this checkpoint.

    The cell plays the API. Each row's /v1/query reply carries the row's figure and one citation, made by resolve() from a draft, so its quote reaches the gate exactly as rag-api would hand it on. Each row's /v1/passages reply is six handbook passages, the row's own clause first. Four rows are planted: lk-04 quotes its probation sentence under NP-03's number, lk-06 paraphrases, lk-08 leaves the quote empty, and lk-09's pool comes back without the passage it cites. The other six quote the first sentence of their clause.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the gate against a stand-in API this cell plays; Rs 0; writes evals/reports/standin36.json).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: scoped to hr_policy_2026.md: 10 row(s) cite it
      10 rows (10 answerable, 0 not) against https://stand-in.invalid

      [PASS] request_success_rate  100.0%  (threshold 100%; 10 rows)
      [PASS] answerable_rate       100.0%  (threshold 80%; 10 rows)
      [PASS] citation_rate         100.0%  (threshold 95%; 10 rows)
      [PASS] citation_valid_rate   100.0%  (threshold 100%; 10 rows)
      [PASS] must_contain_rate     100.0%  (threshold 85%; 10 rows)
      [PASS] correct_rate          100.0%  (threshold 68%; 10 rows)
      [ -- ] refusal_rate            0.0%  (threshold 90%; no rows in scope; 0 rows)
      [ -- ] media_kind_rate         0.0%  (threshold 80%; no rows in scope; 0 rows)
      [ -- ] isolation_403_rate      0.0% 
    """
    import hashlib, os, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = [".", "evals"]
    import run_eval as rv
    from shared import documind_corpus as dc
    from shared.documind_schemas import DraftCitation, ModelDraft, resolve
    for k in ("DOCUMIND_ID_TOKEN", "DOCUMIND_OUTSIDER_TOKEN"):
        os.environ.pop(k, None)
    os.environ["DOCUMIND_EVAL_PASSAGES"] = "1"                            # the switch: each answered row's pool read again
    SOURCE, API = "hr_policy_2026.md", "https://stand-in.invalid"
    raw = open("evals/corpus/acme/" + SOURCE, "rb").read()
    sha, uri = hashlib.sha256(raw).hexdigest(), "gs://documind-ai-YOUR-ID-uploads/acme/" + SOURCE
    cut = dc.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": uri, "text": raw.decode("utf-8")}, "acme")
    P = {c["locator"]: {"n": i, "chunk_id": f"acme:{sha}#{i}", "source_uri": uri, "page": 1, "kind": "text", "text": c["text"]}
         for i, c in enumerate(cut)}                                        # ids as the ingest worker mints them
    CLAUSES = [k for k in P if k != "preamble" and not k.startswith("GEN")]
    rows = [r for r in rv.load_golden() if rv.in_scope(r, SOURCE, rv.load_corpus())]
    
    
    def sentence(code):
        """The first sentence of a clause's body: what a model that keeps rule 5 would quote.
        
        Example: sentence('PB-02')
        """
        return " ".join(P[code]["text"].split("\n", 1)[1].split()).split(". ")[0].rstrip(".") + "."
    
    
    PLANT = {"lk-04": ("NP-03", sentence("PB-02")),                        # the clause's words, under another passage
             "lk-06": ("NP-03", "Confirmed E3 staff give 60 days' notice."),       # words the model wrote
             "lk-08": ("FIN-02", "")}                                        # no quote: resolve() puts the passage's opening in
    GONE = {"lk-09": "WFH-01"}                                               # cited, and missing from the pool read back
    asked, read = iter(rows), iter(rows)
    
    
    def ask(api_url, question, tenant, email, token, retries=1):
        """The stand-in /v1/query: the row's figure, and one citation resolved the way rag-api resolves one.
        
        Example: ask(api_url, question, tenant, email, token, retries) in the owning lesson/helper context
        """
        row = next(asked)
        code, quote = PLANT.get(row["id"], (row["must_retrieve"][0], sentence(row["must_retrieve"][0])))
        draft = ModelDraft(answer=f"The handbook says {' and '.join(row['must_contain'])} [1].", confidence="high",
                           answerable=True, citations=[DraftCitation(source=1, quote=quote)])
        return 200, {**resolve(draft, [P[code]]).model_dump(), "model": "stand-in", "backend": "vertex", "cache_hit": "none"}, 1500
    
    
    def passages(api_url, question, tenant, email, token, top_k=6, retries=1):
        """The stand-in /v1/passages: six of the handbook's clauses, the row's own first.
        
        Example: passages(api_url, question, tenant, email, token, top_k, retries) in the owning lesson/helper context
        """
        row = next(read)
        first = row["must_retrieve"][0]
        return [P[c] for c in [first] + [c for c in CLAUSES if c != first] if c != GONE.get(row["id"])][:top_k]
    
    
    rv.ask, rv.passages, rv.fetch_current_shas = ask, passages, lambda *a, **k: {sha}
    print("exit", rv.live(API, source=SOURCE, report="evals/reports/standin36.json"))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_10', step_01_nine_quotes_two_measures),
        ('source_12', step_02_the_gate_s_own_lines_over_a_stand_in_api),
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
