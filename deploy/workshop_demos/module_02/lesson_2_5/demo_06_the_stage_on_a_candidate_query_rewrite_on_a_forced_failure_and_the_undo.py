"""Lesson 2.5: The stage on a candidate: QUERY_REWRITE=on, a forced failure, and the undo

The cell creates the revision and asks it the paraphrase from step 3. ask() prints the stage's three keys, the clocks, the answer's cost and the citations. If the first line says same, the model judged the question a good search query already; ask another of step 5's questions, such as pp-10's, the same way. QUERY_REWRITE_MODEL is a setting, so a revision whose model name is wrong is one variable away. The call fails, rewrite() catches it, and the stage searches the question: the answer still comes, with HTTP 200. Do it: the two lines the two questions wrote The variables exist only on the candidate's template, so they are removed rather than set back, and the tag is dropped. Both template lines must print empty.

Run order inside this file:
1. Do it: the stage on, one question (source window 31)
2. Do it: a model that does not exist, the same question (source window 33)
3. Do it: the two lines the two questions wrote (source window 35)
4. Do it: the undo (source window 37)

Prerequisites: demo_05_rewrite_called_directly_one_question_one_call_one_outcome.
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


# Original CLI workflow for step_01_the_stage_on_one_question.
COMMANDS_01 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --update-env-vars QUERY_REWRITE=on --quiet
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"
ask() { curl -s -X POST "$1/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d "{\\"query\\":\\"$2\\",\\"tenant_id\\":\\"acme\\",\\"stream\\":false,\\"top_k\\":3}" | python -c "
import sys, json
sys.path.insert(0, '.'); from shared import prices
j = json.load(sys.stdin); s = j['stages']
usd = j.get('cost_usd') or prices.usd(j.get('model'), j.get('tokens_in') or 0, j.get('tokens_out') or 0, j.get('cached_tokens') or 0)   # cost_usd is empty on the vertex backend
print('rewrite', s.get('rewrite', '-'), '| rewrite_ms', s.get('rewrite_ms', '-'), '| retrieve_ms', s['retrieve_ms'], '| pool', s['pool'],
      '| answerable', j['answerable'], '| Rs %.2f' % prices.inr(usd))
print('   searched:', s.get('search_query', '(no stage: the question)'))
for c in j['citations']:
    print('   cited:', c['source_uri'].split('/')[-1], '#' + c['chunk_id'].rsplit('#', 1)[1], c['quote'][:60])"; }
ask "$CAND" "How much can I claim per trip for domestic travel?"

"""

def step_01_the_stage_on_one_question(session):
    """Run Do it: the stage on, one question at this checkpoint.

    The cell creates the revision and asks it the paraphrase from step 3. ask() prints the stage's three keys, the clocks, the answer's cost and the citations. If the first line says same, the model judged the question a good search query already; ask another of step 5's questions, such as pp-10's, the same way.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one new revision, no traffic; one question to it).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/candidate.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_model_that_does_not_exist_the_same_quest.
COMMANDS_02 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --update-env-vars QUERY_REWRITE_MODEL=no-such-model --quiet
ask "$CAND" "How much can I claim per trip for domestic travel?"

"""

def step_02_a_model_that_does_not_exist_the_same_quest(session):
    """Run Do it: a model that does not exist, the same question at this checkpoint.

    QUERY_REWRITE_MODEL is a setting, so a revision whose model name is wrong is one variable away. The call fails, rewrite() catches it, and the stage searches the question: the answer still comes, with HTTP 200.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one more revision, no traffic, a model that does not exist; the same question).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/candidate.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_two_lines_the_two_questions_wrote.
COMMANDS_03 = """gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query_rewrite"' \\
  --project "$PROJECT" --freshness 15m --limit 2 --format=json | python -c "import sys, json; [print(json.dumps(e['jsonPayload'])) for e in json.load(sys.stdin)]"

"""

def step_03_the_two_lines_the_two_questions_wrote(session):
    """Run Do it: the two lines the two questions wrote at this checkpoint.

    Do it: the two lines the two questions wrote

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (reads the API's log; the two lines the two questions wrote).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/rewrite_rows.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_the_undo.
COMMANDS_04 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --remove-env-vars QUERY_REWRITE,QUERY_REWRITE_MODEL --quiet
gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate --quiet
echo "template now: QUERY_REWRITE=$(svc_env documind-api QUERY_REWRITE) QUERY_REWRITE_MODEL=$(svc_env documind-api QUERY_REWRITE_MODEL)"
gcloud run services describe documind-api --region "$REGION" --project "$PROJECT" --format='value(status.traffic[].percent,status.traffic[].revisionName)'

"""

def step_04_the_undo(session):
    """Run Do it: the undo at this checkpoint.

    The variables exist only on the candidate's template, so they are removed rather than set back, and the tag is dropped. Both template lines must print empty.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (the undo: the two variables removed, the tag dropped, the template read back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/candidate.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_31', step_01_the_stage_on_one_question),
        ('source_33', step_02_a_model_that_does_not_exist_the_same_quest),
        ('source_35', step_03_the_two_lines_the_two_questions_wrote),
        ('source_37', step_04_the_undo),
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
