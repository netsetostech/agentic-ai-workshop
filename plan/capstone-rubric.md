# DocuMind Capstone — the eight components and the published rubric

**Status:** authored 2026-09-05 for the notebook course's Module 13; renumbered 2026-10-13 to the
Agents Workshop's lessons (`course-manifest.json`), where the capstone is lesson 11.8, and on the same
day every lesson number in it checked against the manifest and every file it cites found, in the kit
or the course.
**Published means published**: lesson 11.8's page shows this document to learners, weeks before the
defence, and the assessor scores against this file and nothing else. A rubric a learner has not seen
is an exam, and this is not one.

What this credential is, and how it differs from the course certificate, is the course owner's to
state, with the decisions under *Open, and owned by the course owner* at the end of this file.

---

## The eight mandatory components

Every one is a thing that **exists in the learner's fork** and can be checked by a stranger in
under ten minutes. That constraint is deliberate: a component nobody can verify is a claim.

| # | Component | Where it comes from | How a reviewer checks it |
|---|---|---|---|
| 1 | **A live URL behind IAP** | 0.3, 3.8, 4.7 | Open it. Sign in. Ask a question. A non-member gets 403. |
| 2 | **Your own corpus, ≥ 30 pages, ingested** — a tenant other than acme, globex and zeta | 1.5, 3.8, 11.8 | The UI's Documents page lists them; a query cites one. |
| 3 | **An eval suite, ≥ 30 golden rows, including tenant isolation** | 4.1, 4.2, 4.7 | `make eval` exits 0; `evals/golden.jsonl` has ≥ 5 isolation rows. |
| 4 | **One lane on top of the core** — chat, media, SLM or graph | chosen in 11.8; built in 5.4 (chat), 7.5 (media), 9.2 (SLM) or 7.1–7.2 (graph) | The lane's feature works from the live URL. |
| 5 | **`ARCHITECTURE.md`, with the alternatives you rejected** | 11.8 | It names at least three rejected options and why. |
| 6 | **`COST-MODEL.md`** at 1k / 10k / 100k queries a month | 8.3, 11.5, 11.6 | Dual-priced INR, dated, at `USD_INR = 85`. |
| 7 | **`FAILURE-MODES.md`**, four entries, each proved by a script | 11.7 | Run the entry's command, a `make gotcha-drill` from `ops/gotchas.json` or a script in the fork; the documented symptom appears. |
| 8 | **`RUNBOOK.md` + one recorded rollback** | 11.3 | The rollback log shows `/version` before and after. |

The four documents start from the kit's templates, `capstone/templates/ARCHITECTURE.md`, `COST-MODEL.md`,
`FAILURE-MODES.md` and `RUNBOOK.md`, copied to the fork's root. Each holds `{{...}}` placeholders, and
`make capstone-check` fails its component until the ones it reads are replaced.
`commands/tests/capstone_fork/` holds the four filled in, for a made-up company.

**Component 5 is the one people under-build and the one the defence leans on hardest.** An
architecture document that lists what you built is a description. One that lists what you did not
build, and why, is a decision record — and the interview is sixty minutes of asking why.

### What is deliberately NOT on the list

- **A novel feature.** The lane is one of four, chosen not invented. This credential is about
  shipping and defending, not about ideas.
- **Test coverage percentage.** Component 3 asks for evals of the thing the product does. A
  coverage number for a RAG service measures the wrong layer.
- **Uptime.** You will have run it for days, not months. Claiming an SLO you have not observed
  is exactly the kind of answer the rubric penalises under *Evals*.

---

## The rubric

**Five dimensions, scored 0–3 each. 15 points available. 9 to pass, with no dimension at 0.**

The "no zero" rule matters more than the total: a learner who cannot speak to failure modes at
all has not built a production system, however good the architecture is. Two assessors score
independently; a split of more than 3 points goes to a third.

### 1. Architecture (0–3)

| Score | What it looks like |
|---|---|
| 0 | Cannot draw the request path from browser to answer. |
| 1 | Draws it. Cannot say why any component is there rather than an alternative. |
| 2 | Draws it and defends the main choices with reasons that are specific to this workload. |
| 3 | Also names what they rejected and what would change their mind — a threshold, not a feeling. |

> The 3 is not eloquence. It is a **falsifiable** statement: "we chose Cloud Run because our duty
> cycle is 4%; above roughly 74% GKE is cheaper and we would move."

### 2. Failure modes (0–3)

| Score | What it looks like |
|---|---|
| 0 | "It hasn't failed." |
| 1 | Can name failures in the abstract — the model, the network. |
| 2 | Four documented failure modes with real symptoms, each reproduced by a script. |
| 3 | Also: which of them the monitoring would catch, which it would not, and what they did about the second group. |

### 3. Cost at 10× (0–3)

| Score | What it looks like |
|---|---|
| 0 | Does not know what it costs today. |
| 1 | Knows the monthly bill. Cannot decompose it. |
| 2 | Cost per answer, in rupees, split by model / retrieval / hosting, dual-priced with dates. |
| 3 | Also: what breaks first at 10× — and it is a specific limit, not "we'd scale it". |

> The commonest 2-instead-of-3: the learner scales the bill by ten and stops. At 10× something
> stops being linear — a quota, a Vector Search replica, a cold-start rate, a per-tenant cache
> that no longer fits. Naming it is the difference.

### 4. Evals (0–3)

| Score | What it looks like |
|---|---|
| 0 | No eval suite, or one that has never gone red. |
| 1 | A suite that runs. Cannot say what would make it fail. |
| 2 | Thresholds with reasons, and a red run they can point at in CI history. |
| 3 | Also: which assertions are **vacuous** — enforced upstream so they cannot fail — and what they replaced them with. |

> Dimension 4's 3 is the hardest point in the rubric and it is deliberately the lesson of 4.1 and 4.7:
> DocuMind's own `must_not_contain` isolation rows pass by construction, because the retriever
> filters by tenant before generation. A learner who finds that in their own suite has understood
> something most teams never do.

### 5. What you would do next month (0–3)

| Score | What it looks like |
|---|---|
| 0 | "More features." |
| 1 | A list of features. |
| 2 | A prioritised list with a reason for the order. |
| 3 | The top item is something they learned from operating it — a real observation, not a plan they had before they started. |

---

## The defence: 90 minutes

| Minutes | What happens |
|---|---|
| 0–15 | **Present.** The learner drives: architecture, the lane, one thing that went wrong. |
| 15–75 | **Interview.** Two assessors, the five dimensions, in any order. Live system on screen. |
| 75–90 | **Feedback**, scored there and then, against this file. |

**A defence is not the peer mock.** The **60-minute peer mock interview** runs the week before —
practice, unscored, with a peer. The **90-minute defence** is assessed, by two assessors, and the
credential depends on it. The two are different events with different purposes and the words are
not interchangeable.

**One retry within 30 days.** A retry is scored the same way by at least one assessor who was not
in the first defence.

---

## For the assessor

- **Score the system in front of you, not the story.** Every dimension can be checked live.
- **A missing component is not a zero on a dimension** — it is an incomplete submission, and the
  defence does not run. Check the eight before the day: `make capstone-check FORK=<the fork>`
  (lesson 11.8) says PASS or FAIL for each, with `PROJECT=` it also reads the lane, and it scores
  nothing.
- **"I don't know" scores better than a confident wrong answer**, and say so at the start. The
  dimensions reward calibration; a learner who inflates one answer makes you doubt the other four.
- **Write the reason next to the score.** The feedback slot is fifteen minutes and it is the part
  the learner keeps.

---

## Open, and owned by the course owner

Four commercial decisions this document deliberately does not make: the capstone tier's price, the
v2.0 track ID, the length of the 50% upgrade window, and whether the capstone is purchasable without
the course. None of them changes the rubric; all of them change lesson 11.8's copy. They are Sart's,
the course owner's.
