# agents_workshop

The authoring repository of the Agents Workshop: the v5 edition of Netsetos' GenAI on GCP course, Basics and Modules
0-12, 95 lessons that build, break and run one production system, DocuMind. Private. Two things leave it:

- **the lesson pages**, pasted into Wix (netsetos.com) by the author;
- **the kit**, `deploy/`, published byte for byte as the public
  [netsetos/agents_workshop_learner](https://github.com/netsetos/agents_workshop_learner), which every learner clones.

## What is where

For sequential IDE examples for every module and lesson, start at
[deploy/workshop_demos/README.md](deploy/workshop_demos/README.md).
The main lesson HTML supplies the examples and their ordering; setup/helpers live
in one directory and each lesson has its own runnable files and heading map.

| Path | What it holds |
|---|---|
| `course-manifest.json` | Basics, Modules 0-12 and their 95 lessons: numbers, titles, slugs, file names, status, each lesson's proof. The source of truth for names |
| `lessons/NN-module/N.M-slug/` | one lesson: its page (`Netsetos_GCP_Capstone_N.M_Topic_WIX.html`, the file you paste), `build.py`, `parts/`, `data/` |
| `pagekit/` | what every build shares: the template, `pagebuild.py`, the build runner, the page checker, the responsive audit |
| `deploy/` | the DocuMind kit: services, Terraform, evals, smoke tests, the Makefile and `mk/`. Edited here only |
| `tools/` | the publish and its leak scan, the kit index, the kit's offline gates |
| `plan/` | the v5 story and roadmap, the capstone rubric; `plan/archive/` keeps v3, v4 and the retired v4 lesson packages |

## Build and check a page

```bash
python pagekit/build.py 5.1          # parts + kit excerpts + template -> the page, written next to build.py
python pagekit/check_lesson.py 5.1   # the manifest, the page rules, every excerpt verbatim, nothing private
python pagekit/audit_pages.py 5.1    # the phone widths, the embed, touch sizes
```

Lesson 1.1's page is its own source: edit it directly. Every other page copies its shell-setup section, so after
editing 1.1's setup run `python pagekit/build.py --all`. The builds for 1.6 and 1.8 run kit scripts
(`evals/run_eval.py --source`, `services/ingest/reconcile.py --selftest`) to capture their numbers, so they need the
kit's Python dependencies. A page that quotes a kit line the kit no longer has fails `check_lesson.py` until it is
rebuilt.

## Publish the kit

```bash
git clone https://github.com/netsetos/agents_workshop_learner.git ../agents_workshop_learner   # once
python tools/publish_learner.py --dest ../agents_workshop_learner --commit
git -C ../agents_workshop_learner push origin main
```

The publish copies what is committed under `deploy/` at HEAD, including the executable bits, and deletes anything else
in the learner repo. It copies nothing if `tools/leakscan.py` finds key material, a real project id or number, a
personal mailbox, a page or a notebook. Put your lane's project id and number in `.publish-deny` (gitignored, one per
line) and it refuses those too. `.github/workflows/publish-learner.yml` automates this after the checks pass on main;
it stays off until a deploy key and `LEARNER_PUBLISH=on` are set (the file says how).

## On every pull request

`.github/workflows/checks.yml` runs the page checker and the responsive audit on every page, then the kit: every Python
file compiles, the offline regression suites, the offline eval gate, six offline gates, `deploy/INDEX.md` is current,
and the publish scan. The kit's heavy validation (terraform validate, the image builds) runs in the learner repo on
every publish, in its `documind-dryrun` workflow.

## Where this came from

Seeded on 22 September 2026 from `netsetos/agentic-ai-weekend-gcp`, branch `claude/rag-production-hardening` at
`951844b`, plus the work that followed it: the v5 manifest, the pages for lessons 3.1 to 5.1, the kit's `mk/` split
and `commands/lane.py`. The earlier 13-module notebook course, its pages, notebooks and Colab tooling stay in that
repository and in `netsetos/agentic-ai-weekend-gcp-learners`.
