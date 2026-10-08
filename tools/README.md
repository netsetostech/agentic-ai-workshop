# tools

| File | What it does |
|---|---|
| `publish_learner.py` | `deploy/` at HEAD becomes the whole learner repository (`--check` scans only) |
| `leakscan.py` | the one list of what never leaves this repository, used by the publish and by the page checker |
| `kit_index.py` | writes `deploy/INDEX.md`: every kit file and the lessons that quote or name it (`--check` in CI) |
| `check_authz.py` | each service binds exactly its callers |
| `check_lifecycle.py` | the document lifecycle: the tombstone, the verified undo, the released claim |
| `check_retrieval.py` | the same predicates on every retrieval path, the bounded reranker, the packed set |
| `check_one_retrieval.py` | one retrieval implementation under `deploy/` |
| `check_real_corpus.py` | every golden figure survives chunking; a plain lexical retriever finds every anchor |
| `check_local_lane.py` | the Rs 0 lane answers what the corpus answers, refuses what it does not, leaks nothing |
| `build_workshop_demos.py` | extracts main-HTML examples and builds the reviewed lesson demos (`--check` detects drift) |
| `group_workshop_demos.py` | groups actual HTML sections into numbered files, with setup, conditional paths and end-of-lesson restoration |
| `workshop_demo_groups.py` | reviewed optional/recovery/cleanup roles, manual checkpoints and upstream prerequisites |
| `workshop_demo_reviewed.json` | source digests that require a grouping review when an HTML page changes |
| `workshop_demo_runtime_adaptations.py` | documented adjustments for IDE state, expected red gates and owned cleanup |
| `check_workshop_demos.py` | verifies every lesson map, window coverage, imports, functions and Bash syntax without cloud calls |
| `workshop_docstrings.py` | retains executable AST while documenting nested lesson functions/classes and actual usage examples |
| `../pagekit/demo_links.py` | inserts public learner-file links at actual HTML headings; strips only those generated blocks before source hashing |

The number after `demo_` is the visible HTML section badge, never the position in a
handwritten group list. Read the page first; conditional and manual-action
overrides still require review. The nine course-plan lessons explicitly lack HTML.
Run the generator, its `--check`, the workshop checker and offline tests after
changes. The checker compiles raw HTML heredocs as well as generated Python,
checks Bash syntax, and requires summaries/examples on every definition.

Page builders use `pagekit.pagebuild.kit_runtime_files()` when counting deployed
implementations. Teaching copies under `workshop_demos/` must not inflate counts
of event writers, backend readers or service calls. Teaching content must be at
least 60 KB and has no upper limit; exact generated IDE navigation has a separate
10 KB bound checked against the lesson map.

The six `check_*.py` gates came from the earlier course's repository unchanged; they read only the kit. That repository's
other nine gates (auth wiring, contract, lanes, media contract, graph backends, eval gate, release, Colab links, notebook
sync) check its notebooks and stayed there.
