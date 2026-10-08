# CLAUDE.md

Guidance for Claude working in this repository.

## What this repo is

The private authoring repository of the Agents Workshop, the v5 edition of Netsetos' GenAI on GCP course: Basics and
Modules 0-12, 95 lessons (the Cohort 2 structure), one main page per lesson, every lesson verified against the DocuMind
kit in `deploy/`. Audience: Indian production engineers shipping AI on Google Cloud. The pages go to Wix (netsetos.com).
The kit is published to the public `netsetos/agents_workshop_learner`, and learners clone it to `~/deploy_module_rag`.

## Sources of truth

- `course-manifest.json`: module and lesson numbers, titles, slugs, page file names, status. A page's title, hero crumb
  and footer must match it; `pagekit/check_lesson.py` enforces that.
- `plan/cohort-2-build-plan-2026-10-07.md`, with `plan/cohort-2-structure-2026-10-07.json`: the Cohort 2 structure,
  today's lesson numbers mapped to it, and the order of work, dated to the 7 Nov - 6 Dec 2026 cohort.
- `plan/course-plan-v5-story-2026-09-22.md`: the files, make targets and proof per lesson, in the numbers before the
  renumbering. `plan/course-roadmap-v5-2026-09-22.md`: the order of work and each lesson's status before Cohort 2.
- `deploy/`: the only place kit code is edited. Never edit the learner repository; the next publish overwrites it.

## Writing a lesson page (the author's rules)

- One file per lesson: `lessons/NN-module/N.M-slug/Netsetos_GCP_Capstone_N.M_<Topic>_WIX.html`. No practice lab, live
  session, interview Q&A or notebook unless the author asks.
- Write for the lesson's own manifest title. Do not re-cut other lessons' content.
- Shape: hero with chips; table of contents; an "In this lesson" box of one or two lines; Level 0 theory with an analogy
  and a diagram or interactive built on the kit's real rules and data; a definitions table; the shared shell-setup
  section from 1.1 (a Basics page: the laptop setup in `pagekit/basics_setup.html`); then levels rising from the deployed UI, to the kit function (verbatim excerpts), to REST calls, to
  direct Firestore and API reads; a "Verify it yourself" checklist; a "What changed on your lane" box; a footer that
  names the next lesson.
- No "Check yourself" quizzes and no exercise grid.
- Verify every number against the kit code or a run on a live lane before stating it. Lane-dependent values are
  placeholders (`NUMBER`, `documind-ai-YOUR-ID`, `COMMIT`, "yours"), never invented digits and never the author's real
  project id, project number or email.
- Python cells are wrapped as `python - <<'PY' ... PY`, with their own client and
  `warnings.filterwarnings("ignore", category=UserWarning)`, so they paste into bash.
- Copy buttons go on bash windows only. Excerpts and expected output carry a "read only" badge.
- The page hides its own vertical scrollbar (the Wix embed showed one) and keeps the template's auto-height handshake.
- Theme: teal `#0d9488`, secondary `#0891b2`, navy `#0f1729`; DM Sans body, Playfair Display h1/h2, JetBrains Mono code;
  760px content width; inline CSS in a single file.
- Build from parts with the lesson's `build.py`: excerpts come from `pagekit.pagebuild.block()` verbatim, numbers are
  computed from the kit at build time. Then `python pagekit/check_lesson.py N.M` and `python pagekit/audit_pages.py N.M`
  must pass. R39 (the em dash in code-window labels) is the one known audit exception.

## The kit (`deploy/`)

- The Makefile keeps the variables, `guard-project`, `.PHONY` and the core targets; each course module's targets live in
  `mk/<lane>.mk` (ingestion, lifecycle so far), pulled in by `include mk/*.mk`. A recipe longer than a few lines is a
  script in `commands/` or a subcommand of `commands/lane.py`, so every target also runs without make. A new module is
  one `.mk` file plus its targets in `.PHONY`.
- The code's comments carry lesson numbers from the earlier notebook course ("4.5's hybrid", "12.6's cache"). The
  workshop's numbers are the manifest's; `deploy/INDEX.md` maps every kit file to the lessons that show it.
- After a kit change: rebuild the pages that quote the changed lines (`check_lesson.py` names them), then
  `python tools/kit_index.py`.
- SDK and models: `google-genai` (`from google import genai`); `gemini-3.6-flash` by default, `gemini-3.1-pro-preview`
  for high reasoning, `gemini-3.1-flash-lite` for cheap bulk. Standard prices per 1M tokens (USD): flash 1.50/7.50,
  flash-lite 0.25/1.50, pro 2.00/12.00. Costs in rupees at `USD_INR = 85`.
- Endpoints: Gemini 3.x generation is served only from `location="global"`; embeddings (`text-embedding-005`,
  `gemini-embedding-001`), tuning and evaluation are regional (`us-central1`); context caching goes on `global`
  (minimum 4,096 tokens for 3.x). A tuned endpoint is served from the location its path names.
- Placeholder project id: `documind-ai-YOUR-ID`. Never paste real keys, project ids or service-account JSON.

## Publishing and git

- A kit publish goes to a public repository: run `python tools/publish_learner.py --dest <learner checkout> --commit`
  and push only with the author's explicit go-ahead, each time, until the automatic publish is switched on.
- Work on a branch and open a pull request; do not push to main. One lesson per pull request by default.
- Never commit `.env`, `.claude/`, `.publish-deny`, Terraform state or notebook outputs.
