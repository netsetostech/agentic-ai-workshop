"""Lesson 3.6: Ship it: v4 on a branch, checked, built, and answering on a candidate

Do it: the branch, and rule 5 in both copies Do it: the check refuses the old label The cell sets the version and adds the line, taking the sha256 from prompt_pin's own reader of the two strings, so the registry gets exactly what the check will compute. Then the check, and the unit test the dry run runs on every push of the learner repository. Do it: commit Do it: build the image, and stage the candidate The workflow's own check, by hand: each URL's /version, with a token minted for the live URL, beside this checkout's short sha. Do it: the candidate's quotes Do it: v3 against v4, quote by quote

Run order inside this file:
1. Do it: the branch, and rule 5 in both copies (source window 39)
2. Do it: the check refuses the old label (source window 41)
3. Do it: name it v4, register it, and check again (source window 43)
4. Do it: commit (source window 45)
5. Do it: build the image, and stage the candidate (source window 47)
6. Do it: the label on both URLs (source window 49)
7. Do it: the candidate's quotes (source window 51)
8. Do it: v3 against v4, quote by quote (source window 53)

Prerequisites: demo_06_the_change_in_memory_rule_5_weakened_on_the_bench_and_the_sha256_it_would_regist.
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


# Original CLI workflow for step_01_the_branch_and_rule_5_in_both_copies.
COMMANDS_01 = """git status --short; git switch -c prompt-v4
python - <<'PY'
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
OLD = "5. A quote is the clause that answers - at most twenty-five words, never a whole section."
NEW = "5. A quote sums up the clause that answers - at most fifteen words, in plain language."
for path in ("services/rag-api/generator.py", "evals/make_trainset.py"):  # the served SYSTEM, and the tuning set's copy of it
    text = open(path, encoding="utf-8").read()
    assert text.count(OLD) == 1, f"{path}: rule 5 is not the kit's: git checkout {path}, then run this again"
    open(path, "w", encoding="utf-8", newline="\\n").write(text.replace(OLD, NEW))
    print(f"{path}: rule 5 now reads {NEW[3:]!r}")
PY
git diff --stat

"""

def step_01_the_branch_and_rule_5_in_both_copies(session):
    """Run Do it: the branch, and rule 5 in both copies at this checkpoint.

    Do it: the branch, and rule 5 in both copies

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a branch of your clone; two files edited).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Switched to a new branch 'prompt-v4'
    services/rag-api/generator.py: rule 5 now reads 'A quote sums up the clause that answers - at most fifteen words, in plain language.'
    evals/make_trainset.py: rule 5 now reads 'A quote sums up the clause that answers - at most fifteen words, in plain language.'
     evals/make_trainset.py        | 2 +-
     services/rag-api/generator.py | 2 +-
     2 files changed, 2 insertions(+), 2 deletions(-)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_the_check_refuses_the_old_label(session):
    """Run Do it: the check refuses the old label at this checkpoint.

    Do it: the check refuses the old label

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the check, which should fail).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python commands/prompt_pin.py
    prompt:   documind-rag@v3 (services/rag-api/config.py: prompt_id@prompt_version, as /version reports it)
    text:     SYSTEM + DATED_RULE, 601 characters, as generate() joins them (services/rag-api/generator.py)
    sha256:   269dec90134e07beb3449813e1eb156c803568aa370bb52baa3a87aab8b2f6e8
    registry: documind-rag@v3 has another sha256, 543ed8060f1b177cc26159b1af609d16dabeeafa88097945f5a74e884aca4e1e: SYSTEM or DATED_RULE changed and prompt_version did not
    A changed prompt needs a new version. Set prompt_version to "v4" in services/rag-api/config.py, then add
        "documind-rag@v4": "269dec90134e07beb3449813e1eb156c803568aa370bb52baa3a87aab8b2f6e8"
    to "versions" in servic
    """
    from workshop_helpers.gates import expect_failure
    expect_failure(session, ["make", "prompt-version"], status=2, messages=["has another sha256", "A changed prompt needs a new version"])
    print("exit 2")

# Original CLI workflow for step_03_name_it_v4_register_it_and_check_again.
COMMANDS_03 = """python - <<'PY'
import hashlib, json, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "commands")
import prompt_pin                                                     # the check's own reader of SYSTEM + DATED_RULE
CFG, REG = prompt_pin.CONFIG, prompt_pin.REGISTRY
cfg = open(CFG, encoding="utf-8").read()
assert cfg.count('    prompt_version: str = "v3"\\n') == 1, f"{CFG}: prompt_version is not v3"
open(CFG, "w", encoding="utf-8", newline="\\n").write(cfg.replace('    prompt_version: str = "v3"\\n', '    prompt_version: str = "v4"\\n'))
digest = hashlib.sha256(prompt_pin.prompt_text(open(prompt_pin.GENERATOR, encoding="utf-8").read()).encode("utf-8")).hexdigest()
reg = json.load(open(REG, encoding="utf-8"))
reg["versions"]["documind-rag@v4"] = digest                           # beside v3's line, which stays as it is
open(REG, "w", encoding="utf-8", newline="\\n").write(json.dumps(reg, indent=2, ensure_ascii=False) + "\\n")
print(f"{CFG}: prompt_version v4")
print(f'{REG}: "documind-rag@v4": "{digest}"')
PY
make prompt-version; echo "exit $?"
python -m unittest discover -s commands/tests -p test_prompt_versions.py

"""

def step_03_name_it_v4_register_it_and_check_again(session):
    """Run Do it: name it v4, register it, and check again at this checkpoint.

    The cell sets the version and adds the line, taking the sha256 from prompt_pin's own reader of the two strings, so the registry gets exactly what the check will compute. Then the check, and the unit test the dry run runs on every push of the learner repository.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two more files edited; then the check and the unit test the dry run runs).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: services/rag-api/config.py: prompt_version v4
    services/rag-api/prompt_versions.json: "documind-rag@v4": "269dec90134e07beb3449813e1eb156c803568aa370bb52baa3a87aab8b2f6e8"
    python commands/prompt_pin.py
    prompt:   documind-rag@v4 (services/rag-api/config.py: prompt_id@prompt_version, as /version reports it)
    text:     SYSTEM + DATED_RULE, 601 characters, as generate() joins them (services/rag-api/generator.py)
    sha256:   269dec90134e07beb3449813e1eb156c803568aa370bb52baa3a87aab8b2f6e8
    registry: documind-rag@v4 has this sha256 (services/rag-api/prompt_versions.json): the text is the one its version names
    exit 0
    .......
    ----------------------------------------------------------------------
    Ran 7 te
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_commit.
COMMANDS_04 = """git -c user.name="$ME" -c user.email="$ME" commit -qam "Prompt v4: rule 5 asks for a summary of the clause"
git show --stat --format='%h %s' HEAD

"""

def step_04_commit(session):
    """Run Do it: commit at this checkpoint.

    Do it: commit

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one commit on the branch; nothing is pushed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: COMMIT Prompt v4: rule 5 asks for a summary of the clause

     evals/make_trainset.py                | 2 +-
     services/rag-api/config.py            | 2 +-
     services/rag-api/generator.py         | 2 +-
     services/rag-api/prompt_versions.json | 3 ++-
     4 files changed, 5 insertions(+), 4 deletions(-)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_build_the_image_and_stage_the_candidate.
COMMANDS_05 = """gcloud run services describe documind-api --region "$REGION" --project "$PROJECT" --format=json \\
  | python -c 'import json, sys; env = json.load(sys.stdin)["spec"]["template"]["spec"]["containers"][0].get("env", []); print("PROMPT_VERSION on the service:", next((e.get("value") for e in env if e["name"] == "PROMPT_VERSION"), "not set, so config.py names the version"))'
make build PROJECT="$PROJECT" SERVICES=api
make release-candidate PROJECT="$PROJECT"
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"

"""

def step_05_build_the_image_and_stage_the_candidate(session):
    """Run Do it: build the image, and stage the candidate at this checkpoint.

    Do it: build the image, and stage the candidate

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one Cloud Build of the API's image, then a revision with no traffic: minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ship_v4.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

# Original CLI workflow for step_06_the_label_on_both_urls.
COMMANDS_06 = """for u in "$API" "$CAND"; do
  curl -s "$u/version" -H "Authorization: Bearer $(tok "$API")" \\
    | python -c 'import json, sys; v = json.load(sys.stdin); print(sys.argv[1], "| prompt", v["prompt"], "| git_sha", v["git_sha"], "| this commit:", v["git_sha"] == sys.argv[2])' "$u" "$(git rev-parse --short HEAD)"
done

"""

def step_06_the_label_on_both_urls(session):
    """Run Do it: the label on both URLs at this checkpoint.

    The workflow's own check, by hand: each URL's /version, with a token minted for the live URL, beside this checkout's short sha.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two GETs: the live revision and the candidate).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/version_v4.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_06)

# Original CLI workflow for step_07_the_candidate_s_quotes.
COMMANDS_07 = """DOCUMIND_EVAL_PASSAGES=1 make eval-live PROJECT="$PROJECT" API="$CAND" SOURCE=hr_policy_2026.md REPORT=evals/reports/quotes36_v4.json

"""

def step_07_the_candidate_s_quotes(session):
    """Run Do it: the candidate's quotes at this checkpoint.

    Do it: the candidate's quotes

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same ten questions to the candidate: a few rupees).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/quotes_candidate.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_07)

def step_08_v3_against_v4_quote_by_quote(session):
    """Run Do it: v3 against v4, quote by quote at this checkpoint.

    Do it: v3 against v4, quote by quote

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the two reports; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/quotes_compare.txt]
    """
    import json, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    V3, V4 = "evals/reports/quotes36.json", "evals/reports/quotes36_v4.json"    # step 4's report, and the candidate's
    
    
    def load(path):
        """One run_eval.py report, its passage checks, and the gate's exit as the gate decides it.
        
        Example: json.load(open(path, encoding='utf-8'))
        """
        r = json.load(open(path, encoding="utf-8"))
        code = 2 if r["leaks"] else 1 if (r["failed"] or r["stale"] or r["required_failed"]) else 0
        return r, r.get("passage_checks") or {}, code
    
    
    def pct(v):
        """A rate as the gate prints it, or n/a when nothing was counted.
        
        Example: pct(r.get('quote_support_rate'))
        """
        return "n/a" if v is None else f"{v:.1%}"
    
    
    def verdicts(rec):
        """A row's quote checks in citation order, or why it has none.
        
        Example: verdicts(x)
        """
        return " ".join(c.get("check", "-") for c in rec.get("cites") or []) or rec.get("why") or "-"
    
    
    (a, qa, ea), (b, qb, eb) = load(V3), load(V4)
    for name, r, q, e in (("v3", a, qa, ea), ("v4", b, qb, eb)):
        print(f"{name}: gate exit {e} | quote_support_rate {pct(r.get('quote_support_rate'))} | quote_passage_rate "
              f"{pct(q.get('quote_passage_rate'))} | " + ", ".join(f"{k} {n}" for k, n in (q.get("quotes") or {}).items()))
    by_id = {x["id"]: x for x in b["records"]}
    print(f"\n  {'row':6} {'v3':22} {'v4':22} v4's first quote")
    for x in a["records"]:
        y = by_id.get(x["id"], {})
        first = " ".join(((y.get("cites") or [{}])[0].get("quote") or "").split())
        print(f"  {x['id']:6} {verdicts(x)[:22]:22} {verdicts(y)[:22]:22} {first[:50]!r}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_39', step_01_the_branch_and_rule_5_in_both_copies),
        ('source_41', step_02_the_check_refuses_the_old_label),
        ('source_43', step_03_name_it_v4_register_it_and_check_again),
        ('source_45', step_04_commit),
        ('source_47', step_05_build_the_image_and_stage_the_candidate),
        ('source_49', step_06_the_label_on_both_urls),
        ('source_51', step_07_the_candidate_s_quotes),
        ('source_53', step_08_v3_against_v4_quote_by_quote),
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
