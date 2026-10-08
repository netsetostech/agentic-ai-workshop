# Lesson 0.2: the runs the page still needs

The build computes everything it can: `make dryrun`'s three commands green, red on the loosened `lk-06` and green
again, the `git diff`, the seed line of `make chat-local`, and the Rs 0 lane's retrieval for the notice-period
question. Six outputs only a laptop can print are read from `data/` with `pb.recorded()`. Until a file exists the page
shows a marked stand-in, and `python pagekit/build.py 0.2` names every one still awaited.

- **Where:** one session on a laptop: Linux, macOS, or WSL 2 with Ubuntu on Windows. Use bash (on macOS, type `bash`
  first). Run the steps in the page's order, in two terminals as the page says.
- **Cost:** Rs 0. Nothing here signs in to Google Cloud, calls gcloud or touches a project. The only network use is
  `git clone`, pip, `ollama pull`, and in run 6 Terraform's provider download and Docker's image builds.
- **Before:** install git, curl, Python 3.12, Terraform 1.9.0 or newer, gcloud, Docker, Ollama and make, as the
  page's tool table says.
- **Recording:** paste each output as plain text, LF line endings, into the file named below, under
  `lessons/00-setup/0.2-local-environment/data/`. Replace your home directory with `/home/you` and your user name
  wherever else it appears, a process id with `NUMBER`, and a kit commit hash with `COMMIT` (its date with
  `YYYY-MM-DD`). Leave versions, timings and everything else as printed. No real project id or email can appear in
  these runs; if one does, replace it with `documind-ai-YOUR-ID` or `you@your-company.com`.

| # | Data file | Terminal | Command (the page's own block) | What to paste | The build checks (today's values, computed from the kit) |
|---|---|---|---|---|---|
| 1 | `data/tool_checks.txt` | 1 | the tool check (setup section) | everything it prints | - |
| 2 | `data/install_check.txt` | 1 | the clone, venv and install block (setup section), on a machine without `~/rag-shell-venv` | the `kit ...` and `Python 3.12...` lines, then a line `...`, then from the second `Python: /home/you/rag-shell-venv/bin/python` line to the `PASS: Terraform ...` line | contains `PASS: 31 source-pinned packages and 28 operator imports are available.` |
| 3 | `data/chat_local.txt` | 2 | the lane's venv block, then the start block (step 4) | everything `make chat-local` prints, its echoed commands included, to uvicorn's `Uvicorn running on http://127.0.0.1:8081` line | contains `seeded 1628 chunks for tenant 'acme' into the local store` |
| 4 | `data/chat_health.txt` | 1 | `curl -s localhost:8081/health \| python -m json.tool` (step 4) | the JSON | contains `"profile": "local"` |
| 5 | `data/chat_answer.txt` | 1 | the question through the direct brain (step 4), while the lane serves | everything the block prints: the answer, the five citation lines, the brain and cost line | contains `acme:hr_policy_2026#NP-03`, `60` and `cost Rs 0.0` |
| 6 | `data/dryrun_tools.txt` | 1 | `cd "$DEMO_ROOT" && make dryrun`, with Terraform installed and Docker running (tflint too if you have it) | the complete output, make's echoed commands and its per-check seconds included | contains `Tier-A offline dry run` and `The golden set is sound.` |

The commands, in order:

```bash
# terminal 1, run 1: the tool check
for t in git curl python3.12 terraform gcloud docker ollama make; do
  printf '%-10s %s\n' "$t" "$(command -v "$t" || echo MISSING)"
done
python3.12 --version; terraform version | head -1; gcloud --version | head -1
docker --version; ollama --version

# terminal 1, run 2: move an existing operator venv aside first, so the run is a first install
[ -d "$HOME/rag-shell-venv" ] && mv "$HOME/rag-shell-venv" "$HOME/rag-shell-venv.before-0.2"
export DEMO_ROOT="${DEMO_ROOT:-$HOME/deploy_module_rag}" KIT_REPO=https://github.com/netsetos/agents_workshop_learner.git
if [ ! -d "$DEMO_ROOT" ]; then git clone -q "$KIT_REPO" "$DEMO_ROOT"
else git -C "$DEMO_ROOT" pull -q --ff-only; fi
cd "$DEMO_ROOT" && git log -1 --format='kit %h, %cd' --date=short
[ -d "$HOME/rag-shell-venv" ] || python3.12 -m venv "$HOME/rag-shell-venv"
source "$HOME/rag-shell-venv/bin/activate" && python --version
source commands/session-restart.sh
rag_install_python_dependencies
rag_require_terraform

# terminal 2, run 3: the lane's venv and model, then the lane (leave it running)
cd "${DEMO_ROOT:-$HOME/deploy_module_rag}"
[ -d "$HOME/rag-local-venv" ] || python3.12 -m venv "$HOME/rag-local-venv"
"$HOME/rag-local-venv/bin/python" -m pip install -q -r services/chat/requirements.txt -r services/chat/requirements-local.txt
ollama pull gemma3:4b
source "$HOME/rag-local-venv/bin/activate"
export DOCUMIND_CHROMA_DIR="$PWD/documind_chroma"    # without it the service opens services/chat/documind_chroma, empty
make chat-local

# terminal 1, run 4: the health check
curl -s localhost:8081/health | python -m json.tool

# terminal 1, run 5: the notice-period question through the direct brain
curl -s localhost:8081/v1/chat -H 'content-type: application/json' -o /tmp/answer02.json \
  -d '{"question": "What is the notice period for a confirmed E3?", "brain": "direct", "session_id": "lesson-0-2"}'
python - <<'PY'
import json, warnings; warnings.filterwarnings("ignore", category=UserWarning)
r = json.load(open("/tmp/answer02.json", encoding="utf-8"))
print(r["answer"])
for c in r["citations"]:
    print(f'  {c["score"]:5.3f}  {c["chunk_id"]}  page {c["page"]}')
print("brain", r["brain"], "| tool calls", r["tool_calls"], "| model calls", r["limits"]["model_calls"],
      "| cost Rs", r["limits"]["cost_inr"])
PY

# terminal 2: Ctrl+C stops the lane. Terminal 1, run 6: the dry run with Terraform and Docker
cd "$DEMO_ROOT" && make dryrun
```

Then rebuild and check: `python pagekit/build.py 0.2`, `python pagekit/check_lesson.py 0.2`,
`python pagekit/audit_pages.py 0.2`. The build fails with the file's name if a recording does not match what it
computed from the kit (the last column above).

What to look for while running, because the page leans on it:

- Run 3: if `DOCUMIND_CHROMA_DIR` is not exported, the seed fills `$DEMO_ROOT/documind_chroma` and the service opens
  `services/chat/documind_chroma`, which is empty; run 5 then answers `local corpus is empty - run: python -m
  shared.local_corpus` with no citations. The page tells learners to export it; see the coordinator note in the
  lesson's pull request about fixing the kit's recipe instead.
- Run 5: the five citations should match the build's own read of the store (the `expected` window under the direct
  read in step 4): `acme:hr_policy_2026#NP-03` at 1.000, then four statute windows. The answer's wording is
  gemma3:4b's; it should say 60 days.
- Run 6: the docker check builds every Python image, which takes a while; a `WARN` on `copy-paths` (the slm image's
  `build/` folder) is expected, and the run must end with `The golden set is sound.`
- The lane leaves `documind_chroma/` and `services/chat/documind_threads.db` untracked in the clone; harmless, and the
  page says so.
