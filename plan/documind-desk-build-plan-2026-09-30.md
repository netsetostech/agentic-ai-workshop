# DocuMind Desk: build plan (30 September 2026)

For the course author. This plan turns the DocuMind Desk design in
`/mnt/project-files/research/documind-query-router-2026-09-30.md` ("the research report") into ordered pull requests
and lessons, and slots them into `plan/agents-mcp-gaps-plan-2026-09-29.md` ("the gap plan", draft PR #72, branch
`claude/project-thread-ty0x54`).

How to read the references:

- Kit paths are relative to `deploy/` unless they start with `lessons/`, `tools/`, `plan/`, `pagekit/` or
  `.github/`. Corpus paths are relative to `deploy/evals/corpus/`.
- Every kit anchor was checked in the working tree at `305c9d3`. That commit adds only the gap plan, so the kit is
  byte-identical to `ee81900`. Line numbers move as pull requests land, so each pull request re-derives the page lines
  it touches with `pagekit/check_lesson.py`.
- Lane values are placeholders: `documind-ai-YOUR-ID`, `NUMBER`, `REGION`, `COMMIT`, `you@example.com`, "yours".
- A figure that comes from the research report and not from the kit is labelled an estimate.
- WebSearch was not run for this plan, except for the Google Chat door (sections 4.11a and 4.11b). Its Google facts
  come from Google's developer pages and two third-party posts read on 30 September 2026, each cited by a label that
  table W in section 4.11a resolves to its URL, with whether the page was read or only seen as a search result. The
  two legal dates below that come from the research report are marked "verify against the Gazette".
- Nothing in the repository was edited. This file is the only file written. It was revised the same day after two
  reviews, and every fix was checked against the tree before it was applied.
- 30 September 2026, revision: the Google Chat door (PR 13, G10-j). It adds sections 4.11a and 4.11b and Desk
  decisions 29 to 38, and updates the counts, flags, tests and milestones in sections 1 to 4, 6 and 7 to match. Its kit
  anchors were checked in the working tree at `38898c9`, whose kit is byte-identical to `ee81900`. The addition was
  reviewed twice before it was inserted.
- "Desk decision N" is a row of section 8. "Gap decision N" is a decision of the gap plan.

---

## 1. The objective and the scope

### 1.1 What launches

DocuMind Desk is one front door per tenant for employees' questions about their own company's handbook and about
Indian labour and data-protection law. A code-first router sends each question to exactly one desk.

| Route | Handles | How it resolves | Model calls |
|---|---|---|---|
| `handbook` | The tenant's handbook clauses: notice, probation, leave, travel, payroll dates, IT rules, approvals | A specialist agent. Direct mode by default: one retrieve that code scopes to `policy`, returning rag-api's cited answer. Agent mode when a figure is asked, with code calculators | router, then about one rag-api answer |
| `statute` | What the law in the tenant's corpus says: the four Labour Codes, the repealed Acts, the DPDP Act, the IT Act, public-law GST | A specialist agent scoped to `statute` and `guidance`. Code appends an in-force line to every cited instrument | router, then about one rag-api answer |
| `case` | POSH disclosure, grievance, privacy request, late exit dues, a question the handbook cannot answer, "talk to a person" | Code only: a case in the queue of the person the law names, with the statutory reference and the clock | none once a rule fires |
| `clarify` | A first turn too elliptical to place | Code: one question and two buttons, capped at one in a row | router only |
| `out_of_scope`, `not_covered`, `denied` | Actions in other systems, own HRMS records, another person's data, legal advice, questions for a desk the tenant lacks, a person without the role | Fixed replies that name the right channel, with a case offer | router only, or none |

The router has four parts, all in code except its model calls (L1, L2 and the kNN's query embedding):

- **Stage 0, who.** Identity comes from the verified IAP assertion or bearer token. The tenant comes from the roster.
  Roles come from an operator-written store. A member with no role document is `employee`; a failed read allows only
  the case desk.
  On the Google Chat door the verified caller is the bridge service, and the person is the one the bridge names in
  its delegation header, accepted only under the rules of section 4.11a.
- **Stages 1 and 2, the hard gate and the draft check.** A case lexicon in English, Hindi and Hinglish, and a PII tier
  that masks Aadhaar and card numbers. The gate runs on the Desk (`/v1/desk`), on `/v1/chat`, and inside rag-api on
  `/v1/query`, `/v1/stream` and `/v1/passages`.
- **Stages 3 to 6, the chip, the anchors and the signals.** A tapped chip, or a unique identifier such as a clause code
  or an Act title with no first-person marker near it, decides at Rs 0. Otherwise a `gemini-3.1-flash-lite`
  classifier (L1) with enum-only JSON runs beside a per-tenant kNN vote over labelled exemplars. When they disagree,
  one `gemini-3.6-flash` arbiter call (L2) decides.
- **Stages 7 and 8, the checks and the dispatch.** Sticky follow-up, the clarify cap, coverage, roles, then exactly one
  desk.

**Tenants and modes at launch.** Document counts come from `evals/manifest.json`.

| Tenant | Documents | Mode | What runs |
|---|---|---|---|
| acme | 23 objects: policy 1, statute 12, guidance 1, report 1, transcript 1, contract 1, invoice 1, media 5 | `desk_route` on | handbook, statute, case, clarify, out_of_scope |
| zeta | 7 objects: policy 1, statute 4 (the four Codes), guidance 1, contract 1 | `desk_route` shadow, then on | the same five routes |
| globex | 3 objects: statute 2 (DPDP Act, IT Act), contract 1 | `desk_route` single, desk `statute` | the gate, the case path and the statute desk. The classifier is never called, so this `data_region` "in" tenant (`commands/lane.py:148`) makes no router model call |

Three per-tenant flags live in `tenant_settings/{t}`:

- `desk_gate`: off | on.
- `desk_route`: off | shadow | on | single.
- `desk_gchat`: off | on (the Google Chat door, Desk decision 29).

All three default to off and are read through the same 60-second cache pattern as rag-api's `tenant_settings()`
(`services/rag-api/main.py:103-119`). A failed read is "off". The same document holds `desk_single` (single mode's one
desk), `desk_max_parts` (code default 1), `case_queues` and `clause_notes`. The service's own defaults are set in code,
not in the environment, because `deploy-services` empties `CHAT_EXTRA_ENV` (`Makefile:353`).

**The Google Chat door (Desk decision 29).** Employees can also reach the Desk from Google Chat. A direct message to
an "HR Desk" Chat app goes to a small bridge service, `documind-gchat`, which checks that the request came from
Google and then asks the Desk on the sender's behalf as an allow-listed delegate (section 4.11a). The Desk applies the
same gate, roles, coverage and routes as on the Desk page, and the answer comes back as a card with its citations. The
bridge makes no model call and reads no document.

It is a post-launch addition inside this plan: G10-j, then a content pull request that teaches it in 10.6 (section
4.13), with its own milestone, M6a (section 7). It is off for every tenant until `desk_gchat` is switched on. No
earlier milestone waits for it, and a lane without a Business or Enterprise Google Workspace account (Desk decision
30) runs the whole Desk without it.

### 1.2 What does not launch

| Left out | Reason | Consequence |
|---|---|---|
| `compliance_review`, `vendor_finance` (Phase E) | The user's scope | Their roles (finance_ap, legal, hr_compliance, case_integration), the document ACL (`DOC_ACL`), rag-api's delegation header (the Chat door's narrower delegation to the chat service is built, section 4.11a), Pub/Sub case delivery and the invoice fixture relabel are not built. Contract, invoice and report questions are `out_of_scope` with `oos_reason` "no_desk". The Chat page still answers them |
| `company_info` | The user's scope | Annual report and town hall questions are `out_of_scope` "no_desk". The classifier has five labels, not eight |
| Optional documents | The user's decision | The DPDP Rules 2025 are not ingested, and globex gets no handbook. Globex runs single mode on `statute`. Privacy cases cite the Act only: s.8(9) (`acme/dpdp_act_2023.md:379-382`) and s.13(2), "within such period as may be prescribed" (`:490-492`). The Rules' 90-day figure is never shown. A breach-notice question gets a partial refusal |
| The `doc_admin` upload gate | It would rebuild 6.4 and 16.2 | A version pin in the operator registry replaces it (section 5.1) |
| HRMS connector, `roster-sync`, signed links for leavers | No HRMS in the kit | A `leaver` role, written by hand, allows cases only |
| Multi-part answers on by default | Unproven | Built with `desk_max_parts`, a `tenant_settings` field whose code default is 1, until the multi-intent rows pass |
| Other chat surfaces: Slack, Microsoft Teams, WhatsApp | The user's scope: Google Chat is the one chat door. Slack is the fallback for a company with no Business or Enterprise Google Workspace (Desk decision 30) | Not built. The bridge's shape (verify the platform's request, map the sender's email to the roster, call the Desk as the allow-listed delegate, reply later) would carry over |

### 1.3 Definition of done

1. **Kit.** Every pull request in section 4 is merged, except G10-j and the 10.6 Google Chat content pull request,
   which item 7 covers. The following are green: `.github/workflows/checks.yml`, G8-a's chat-pins job with
   `test_cases.py` and `test_desk.py` added to its step (section 4.0), `make desk-check`,
   `python tools/check_one_retrieval.py deploy/`, `python tools/check_authz.py`, `python tools/check_retrieval.py` and
   `python deploy/validate.py`. Every flag defaults to off, and a tenant with every flag off behaves byte for byte as
   today.
2. **Lane (the author's).** The following hold:
   - acme runs `desk_gate=on` and `desk_route=on`; zeta ran shadow, then on; globex runs `single` on `statute`.
   - `make smoke-desk` and `make smoke-cases` pass.
   - `make eval-live` gives the same per-row verdicts as before the relabel.
   - A POSH disclosure through `/v1/stream` returns model `none` and cost 0.
3. **Route test gates (Phase A, 392 test rows)** hold on `make route-eval SPLIT=test`. The decision metrics come from
   `/v1/route`; `authority_rate`, `tool_calls` and the answer checks come from `/v1/desk` (section 4.9):
   - every escalation row passes (20 a class, 100 in all);
   - top-1 route accuracy is 95% or more;
   - per-desk recall is 90% or more with no regression;
   - `authority_rate` is 1.00 per desk;
   - denial is 100% with zero retrieve calls;
   - POSH by rule makes 0 model calls.

   Two design budgets from the research report are also checked: mean router cost of Rs 0.03 or less, and a p95 of
   1.5 s or less on the L1-only path.

   **The ship decision.** B (the routed Desk) ships only if it is non-inferior to C (code only: the gate, coverage,
   then a direct answer over the person's doc types) and to A* (one agent with the real `doc_type` vocabulary and the
   calculators) on `correct_rate` and `authority_rate` on the test split, by the research report's section 7.4 test
   (exact McNemar, a pre-registered margin, proposed 3 points). Otherwise the tenant runs `single`, or the desk folds
   back to the direct scoped answer.
4. **GA gate.** The test split grows to 667 rows, with 75 escalation rows a class, and every escalation row passes.
5. **Course.**
   - Lessons 10.5 and 10.6 (Desk decision 0) are drafted and pass `check_lesson.py` and `audit_pages.py`.
   - Every forced rebuild is merged, and every stated lesson count has moved.
   - `python tools/kit_index.py` has been rerun, and no Desk file is left in `deploy/UNOWNED.md` (G10-j's files leave
     it with item 7).
   - The learner kit is published only with the author's explicit go-ahead, each time.
6. **Outside this repository.** A real pilot tenant's demand data, ticket counts and the product go or no-go on
   personal-record questions (research report, section 11.1, Phases B to D). The kit ships what a pilot needs to
   start measuring: shadow mode and `desk_daily`. The reviewed sample of routed turns (research report, section 7.7)
   is a pilot follow-up, not part of this plan.
7. **The Google Chat door (Desk decision 29).**
   - G10-j is merged, and `test_gchat.py` runs in G8-a's chat-pins step (section 4.0). `python tools/check_authz.py`
     is green with `documind-gchat` in the caller graph and the delegate checks of section 4.11a.
   - On the author's lane and Workspace, `make smoke-gchat` passes, and the probe's facts are recorded in G10-j's
     pull request (section 4.11a, lane proof).
   - Section 4.11b's demo runs end to end. A handbook answer and a statute answer arrive as cited cards, and a POSH
     disclosure opens a confidential case with model `none`, cost 0 and nothing published to the bridge's queue.
   - `make desk TENANT=acme DESK_GCHAT=off` closes the door for acme within 60 s.
   - The 10.6 Google Chat content pull request is merged (section 4.13). It teaches the door inside 10.6's levels
     (Desk decision 34) and removes G10-j's rows from `deploy/UNOWNED.md`.

---

## 2. Code or new lessons: both

### 2.1 The answer

Both are needed.

**Why code.** The kit has none of the pieces:

- There is no roles store: a member document is `{email, added_at}`, written without merge (`shared/tenancy.py:77-82`).
- There is no case record, no router and no gate.
- Every text chunk the worker ingests from GCS carries `doc_type` "unknown" (`services/ingest/contracts.py:70`), so on a
  lane ingested with `make ingest-corpus` a scoped desk would hit the empty-pool refusal
  (`services/rag-api/main.py:208-222`). Rows seeded by `shared/documind_corpus.py` already carry the manifest's class
  (`:121`), and the worker keeps a seeded version's rows (`services/ingest/main.py:394-405`); the relabel plans no
  change for them.

**Why lessons.** The course verifies every lesson against the kit (`CLAUDE.md`), and kit code that no lesson teaches
goes into `deploy/UNOWNED.md`. That file records that such code had drifted silently three times. Such code also maps
to no lesson in `deploy/INDEX.md`, the map `tools/kit_index.py` writes.

In total: thirteen kit pull requests (G10-a to G10-j, with G10-a2, G10-e2 and G10-p), two new Core lessons, forced
rebuilds of nine existing lessons (3.4, 5.1, 5.4, 8.2, 8.3, 10.1, 10.4, 13.2, 16.2; eleven if the passages branch
cannot keep 10.3's and 18.4's lines, section 4.6), and content changes in 10.4, 12.1 and 13.1, plus the Google Chat
door added to 10.6 after G10-j. Eighteen pull requests in all, with the two page pull requests and the three content
pull requests. G10-j adds no lesson to the rebuild list: the lessons it can force (10.1, and 13.2 for its alert) are
already on it, and with Desk decision 36's hooks it forces none.

### 2.2 Recommended: Option B, two new Core lessons in Module 10 (Desk decision 0)

Module 10 is "Agents - Build a tool-using agent" (Core, gate `make smoke-chat`). Its targets live in `mk/agents.mk`,
which the first Desk or G6-a pull request creates (section 4.0).

| Lesson | Title | Working piece | Proof (the manifest's `proof`) |
|---|---|---|---|
| 10.5 | Hand a question to the person the law names | The hard gate on every door, roles, cases and the case inbox | a POSH disclosure through `/v1/stream` returns the fixed template with model `none` and cost 0; a confirmed grievance case in the committee's inbox |
| 10.6 | Route each question to one specialist agent | The relabel, the router, the desk graph, the Desk page and the route eval | `make route-eval SPLIT=test` passes every escalation row; a cited handbook answer and a statute answer with its in-force line on the Desk page |

Why two lessons:

- Each has its own working piece, target and proof. That is the criterion decision 1 of the gap plan applies.
- They land at different times. 10.5 needs G2-a, the gate and the case path. 10.6 needs the router, which needs
  G6-a's Meter and the dev set.
- One lesson would carry the relabel, the gate, cases, roles, the router, the graph and the evals. That does not fit
  90 minutes.

If gap decision 1's reserved 10.5 split of G2 is taken, these lessons become 10.6 and 10.7 (Desk decision 19).

### 2.3 The alternatives

| Option | Lessons (without / with gap decision 1) | For | Against |
|---|---|---|---|
| **B (recommended)**: 10.5 and 10.6 | 62 / 65 | Two proofs; the legal handoff is taught before routing | Two pages to write |
| A: one lesson, 10.5 | 61 / 64 | One page | Over 90 minutes; mixes the legal handoff with classification |
| C: no new lesson; the Desk becomes the brief for 14.4 "Complete the independent capstone and operational handover", or is spread over 7.1, 8.1, 8.3 and 13.3 | 60 / 63 | No count change | The code sits in `deploy/UNOWNED.md` until 14.4 exists (Module 14 has no folder yet). Spreading it re-cuts other lessons' content, which `CLAUDE.md` rules out |
| B': a new Advanced Module 19 | 62 / 65 | Module 10 stays lean | Every "18 modules" statement moves too (`course-manifest.json` `total_modules`, `README.md:19`, `CLAUDE.md`, the roadmap title "18 chapters", `deploy/workshop_demos/README.md:3`). A legally consequential gate would be taught as optional |

### 2.4 Counts

Each new Core lesson adds one lesson and 1.5 hours (gap plan, section 3). The 13 Advanced scenes and their 19.5 hours
are unchanged in every row.

| Scenario | Lessons | Core | Core hours |
|---|---|---|---|
| Today (`course-manifest.json`, `plan/course-plan-v5-story-2026-09-22.md:84`) | 60 | 47 | 70.5 |
| Desk, option B only | 62 | 49 | 73.5 |
| Gap plan decision 1 only (11.4, 12.4, 12.5) | 63 | 50 | 75 |
| Decision 1 and Desk option B | 65 | 52 | 78 |
| Decision 1 and Desk option A | 64 | 51 | 76.5 |
| Desk option B with the 10.6 split (Desk decision 18) | 63 | 50 | 75 |
| Decision 1 and the split | 66 | 53 | 79.5 |

The Google Chat door adds no lesson in any row. It is taught inside 10.6's levels (Desk decision 34), so every figure
above stands. Only the alternative of a Core lesson of its own would add one lesson and 1.5 hours to each row.

---

## 3. Before the Desk: the gap-plan items it needs

### 3.1 Dependency table

| Gap item (gap plan step) | What the Desk takes from it | Needed by | Kind |
|---|---|---|---|
| G8-a (1.2) | `status: "error"` as the one refusal marker, one tool list, and the chat-pins CI job, whose step G10-e, G10-f and G10-j extend with `test_cases.py`, `test_desk.py` and `test_gchat.py` | G10-e, G10-f, G10-h, G10-j | Hard |
| G6-a (2.1) | `Meter` and `charge_model`, `shared/prices.py`, `TurnLimitsMiddleware`, `stopped_by`. `mk/agents.mk` is created by the first Desk pull request; G6-a adds its targets and edits the `mk/README.md` row | G10-f (the router charges the Meter), G10-h, G10-p | Hard |
| A retrieve-only path. Gap decision 14 proposed a flag on `/v1/query` as its own gap; this plan proposes a `/v1/passages` route, its own pull request G10-p right after G6-a (section 4.6, Desk decision 27) | `/v1/passages` with each chunk's full text | G10-h only (agent mode) | Hard for agent mode |
| G2-a (2.4) | See the list below | G10-e | Shared slice. G10-e lands after the end of gap phase 2 (section 3.2) |
| G3 (4.1) | Spans `desk.gate`, `desk.route`, `desk.<route>`, `desk.case` | G10-i | Soft; amended in section 3.4 |
| G5-b (5.3) | The fence and taint on agent-mode desks | G10-h | Soft; amended in section 3.4 |
| G9-A (1.5) | Stdlib identifier checks | G10-c | Soft. G9-A keeps its checks inside `documind_classifier.py`, because 18.1 asserts the Dockerfile's COPY line (`lessons/18-serving/18.1-gateway-routes/build.py:145`, `services/litellm/Dockerfile:15`) and the litellm image builds from `services/litellm/` with no `shared/`. `shared/identifiers.py` mirrors them, and a test, with Presidio stubbed as G9's stdlib tier does, runs the same Verhoeff and Luhn vectors through both |
| G9-B (5.6) | A sensitive door | none at launch | Soft; amended in section 3.4 |

G2-a's shared slice is:

- `AUDIT_BUCKET` on the chat service (`commands/lesson-12.8.sh:32`);
- the pins `google-cloud-storage==3.13.1` and `langgraph==1.2.12` in `services/chat/requirements.txt`;
- `objectCreator` on the audit bucket for chat-sa, beside `ingest_audit` and `api_audit`
  (`terraform/storage.tf:96-105`);
- the approvals line in `AUDIT_ACTIONS`, after `"doc.mirror"` (`shared/audit_log.py:27`);
- the Firestore record-with-TTL pattern and the operator-written role pattern.

**Not needed:**

- G1, G6-b and the G1 peer: the Desk never calls the A2A peer.
- G4, G5-a, G5-c: MCP hardening and the injection lesson do not touch the Desk path.
- G6-c: the per-turn rupee cap of Rs 5 covers every launch desk. A direct turn is an estimated Rs 0.37 plus the
  router, and an agent turn about Rs 0.58 (the "expected shape" in
  `deploy/workshop_demos/module_10/lesson_10_4/README.md:155-181`). So no per-route `budget_inr` extension is needed
  until Phase E.
- G7: the router reads only the last masked question and route, and desk threads are short. Desk threads are not
  windowed; section 3.4 asks G7 to say so.
- G8-b: `route_eval.py` opens its own session per row and does not use `judge.py`'s shared session
  (`evals/judge.py:126`).
- G8-c.
- G2-b to G2-e.

### 3.2 Where the Desk lands in the gap plan's phase order

| Gap plan phase | Gap pull requests | Desk pull requests beside them |
|---|---|---|
| 1. Fixes | 1.1 G5-a, 1.2 G8-a, 1.3 G8-b, 1.4 G8-c, 1.5 G9-A | G10-a, G10-b and G10-d. They have no gap dependency and land with every flag off. G10-a2 lands when the writers finish, and G10-c after it (it is tuned on G10-a2's escalation rows), during phase 1 or 2 |
| 2. Limits and approval | 2.1 G6-a, 2.2 G6-b, 2.3 G6-c, 2.4 G2-a to 2.8 G2-e | G10-p right after G6-a. G10-e waits for the end of the phase, so G2-d's 8.3 scene does not rebase over the Desk's 8.3 rebuild |
| 3. Multi-agent | 3.1 G1 | G10-e, G10-e2, the 10.5 page, G10-f, G10-g, G10-h, G10-i, G10-j, the 10.6 page, the 12.1 and 13.1 content, and the 10.6 Google Chat content. None of them is blocked by G1 |
| 4. Tracing | 4.1 G3 | See Desk decision 26 below |
| 5. Hardening, injection, context, gateway | 5.1 to 5.6 | The GA gate: the test split grows to 667 |

**Placing the Desk in phase 3 holds phases 4 and 5.** The gap plan starts a phase only when the earlier phase's kit
changes are merged (gap plan, section 3). Read that way, G3, G4-A, G4-B, G5-b, G5-c, G7 and G9-B would wait until
the 10.6 page merges, behind eight Desk items of effort L or M. Desk decision 26:

- **(a), recommended.** The Desk is its own track, not bound by the gap plan's phase rule. A Desk pull request waits
  only for the items in its "Depends on". G3 starts after G1, as the gap plan says. G3 instruments the Desk seams that
  exist when it lands, and each Desk pull request that lands after G3 adds its own spans (section 3.4).
- **(b).** The Desk holds phase 4, as the table above reads.

### 3.3 A row for the gap plan

This plan proposes one row for the gap plan's section 2 table. The edit belongs to PR #72 and is not made here:

| Gap | What the kit does today | What it will do | Lessons | Effort | Depends on |
|---|---|---|---|---|---|
| G10 DocuMind Desk | One agent layer that answers every question; no gate, roles, cases or router; `doc_type` "unknown" on every GCS-ingested text chunk | A code-first router to one of five routes; a hard gate on every door; cases in the queue the law names; a registry-driven `doc_type`; the same Desk in Google Chat through an allow-listed delegate | New 10.5 and 10.6 (Desk decision 0), with the Google Chat door taught in 10.6; rebuilds 3.4, 5.1, 5.4, 8.2, 8.3, 10.1, 10.4, 13.2, 16.2 (and 10.3, 18.4 only if G10-p cannot keep their lines); content in 10.4, 10.6 (the Google Chat door), 12.1 and 13.1 | L (13 kit PRs, 2 page PRs, 3 content PRs) | G8-a, G6-a, G2-a (hard); G3, G5-b, G9-A, G9-B (soft); a Business or Enterprise Google Workspace account for G10-j's lane proof |

PR #72's text of gap decision 14 changes with this row: "a retry-free retrieve-only route `/v1/passages`, its own pull
request (G10-p) right after G6-a" (Desk decision 27).

### 3.4 Amendments to later gap items (for PR #72)

These edits belong to PR #72 and are not made here. Each keeps a later gap item correct once the Desk exists.

- **G3 (gap 4.1).** It instruments `services/rag-api/desk_door.py`, `services/chat/desk.py` (install, the chat door,
  `/v1/desk`, `/v1/route`), `desk_router.decide` and the `desk_graph` nodes, with the spans `desk.gate`, `desk.route`,
  `desk.<route>` and `desk.case`, for the Desk files that exist when it lands. Its `FlushMiddleware` line is added
  after `install_desk_door` in rag-api and after `desk.install` in chat, so the flush is outermost (Starlette makes the
  last-added middleware the outermost). Its rebuild list adds 10.5 and 10.6 where they quote a changed line.
  If G10-j has landed, G3 also instruments the bridge's two handlers in `services/gchat/main.py` (`/` and `/work`)
  with a `gchat.event` and a `gchat.answer` span, adds its `FlushMiddleware` line as the bridge's only middleware, and
  grants `documind-gchat-sa` `roles/cloudtrace.agent`. If G3 lands first, G10-j does all three itself.
- **G5-b (gap 5.3).** `TAINT_SOURCES` and the fence cover `desk_graph`'s passages-backed tool, not only `retrieve` and
  `documind_peer`. Its rebuild list adds 10.6 where it quotes a changed line.
- **G9-B (gap 5.6).** The router's L1 and L2 and the agent-mode desks follow the tenant's gateway pin, or 18.1 names
  them as a further door that stays on Vertex AI.
- **G7 (gap 5.5).** It states that desk threads are not windowed.
- **G6-a (gap 2.1).** `mk/agents.mk` may already exist; G6-a adds its targets and edits the `mk/README.md` row.
- **G2-a (gap 2.4).** Its operators-loop change ("the operators loop (386) adds approver-sa") breaks 12.2's verbatim
  assert of that loop line (`lessons/12-protocols/12.2-mcp-deploy/build.py:93`) and makes 12.2's printed mint lines
  (`:256`) incomplete; the gap plan's list says `check_lesson` confirms 12.2. Either 12.2 joins G2-a's rebuilds, or
  approver-sa gets its own token-creator loop, as the Desk's `desk-operators` does (section 4.5).
- **The lesson-count rule (gap plan, section 3).** Add the roadmap's batch table, the code-window count on
  `REVIEW.md:7`, and the course plan's chapter 10 end state (section 6.4), so that 12.4, 12.5 and 11.4 move them too.

---

## 4. The steps

### 4.0 Rules for every Desk pull request, and anchors that differ from the research report

Every Desk pull request follows these rules:

- It is a branch and a pull request, never a push to main.
- A kit pull request carries every rebuild its quoted lines or build asserts force (gap decision 16). New scene
  content follows one lesson per pull request.
- After each kit pull request, run:
  - `python pagekit/check_lesson.py N.M` and `python pagekit/audit_pages.py N.M` for each rebuilt lesson (R39 is the
    one known exception);
  - `python tools/kit_index.py`, then `--check`;
  - `python tools/build_workshop_demos.py`, then `--check`;
  - `python tools/check_workshop_demos.py` and `python deploy/workshop_demos/tests/run_tests.py`, with each changed
    digest reviewed in `tools/workshop_demo_reviewed.json`;
  - `python tools/publish_learner.py --check`.
- New targets go in `mk/agents.mk`, in the `.PHONY` list at `Makefile:188`, and in `mk/README.md`. A recipe longer than
  a few lines becomes a subcommand of a new `commands/desk_ops.py`. That leaves `commands/lane.py` and the subcommand
  set pinned in `commands/tests/test_lane.py:25-26` alone. The first Desk pull request that needs `mk/agents.mk` or
  `commands/desk_ops.py` creates it, with the `mk/README.md` row; G10-a and G10-b may land in either order, so each
  checks.
- Tests with FastAPI or LangGraph run in G8-a's chat-pins job. That step runs named files only (gap plan, G8-a:
  "install `services/chat/requirements.txt`, run `test_chat_brains.py`"), so G10-e adds
  `DOCUMIND_REQUIRE_LIBS=1 python -m unittest commands/tests/test_cases.py` to it, G10-f adds `test_desk.py` and G10-j
  adds `test_gchat.py`, in both `.github/workflows/checks.yml` and `deploy/.github/workflows/documind-dryrun.yml`. The
  shared step (`python -m unittest discover -s deploy/commands/tests`, `checks.yml:55`) would only skip their library
  halves. `make desk-check` runs these files in `~/graph-venv`, which G6-a's `limits-check` builds from the chat pins,
  and builds it when it is missing. Stdlib tests run in the shared interpreter, which `checks.yml` discovers in
  `deploy/commands/tests` and `deploy/evals/tests`. Tests that need a library use G6-a's pattern:
  `DOCUMIND_REQUIRE_LIBS=1` turns skips into failures.
- One ASGI order per service. In rag-api: G3's flush outermost, then the desk door, then CORS. In chat: G3's flush
  outermost, then the chat door. In the bridge (section 4.11a): G3's flush, and nothing else. Starlette makes the
  last-added middleware the outermost, so G3's lines go after the Desk's install lines (section 3.4).
- Each kit pull request whose new files no page quotes yet adds them to `deploy/UNOWNED.md` under a "DocuMind Desk
  (lessons 10.5, 10.6)" heading. `tools/kit_index.py` writes only `deploy/INDEX.md`, so this is by hand. The 10.5 and
  10.6 page pull requests remove the rows they adopt.
- Kit comments name "workshop lesson 10.5" or "10.6", never the notebook numbering (the gap plan's rule).
- Any shared module holding a function that takes `query`, `q` or `question` keeps the words "chunk", "corpus",
  "embed", "vector" and "/v1/query" out of that function's body. `tools/check_one_retrieval.py` scans `shared/` and
  flags such a function as a second retrieval.
- New code goes in new modules, with one install line per endpoint, so quoted spans stay byte-identical.

Where the research report and the working tree disagree, the tree holds:

| The research report says | The working tree shows | This plan uses |
|---|---|---|
| The undo's reupsert pattern is at `services/rag-api/main.py:357-358` | It is in the ingest worker, `services/ingest/main.py:359-360` | the ingest worker's lines |
| The relabel should "refresh the fingerprint" | `corpus_fingerprint` hashes only the sorted current doc_keys (`services/ingest/idempotency.py:357-363`), so a relabel does not move it | an explicit purge of the tenant's `answer_cache` |
| The duplicate ack is at `services/ingest/main.py:342` and `:388-392` | `claim` is at 343; the duplicate returns are at 383 and 392 | 383, 392 |
| Take `doc_type` from the registry at `main.py:340` | 340-341 builds the contract in `push()` only; `services/ingest/batch.py:71` and `:78` also call `index_document` | a hook in `index_document`, before its `try:` at 432, covering both lanes |
| Add per-file metadata at `evals/upload.sh:48` | The registry is keyed by object name | `upload.sh` unchanged (16.1 quotes it) |
| `Citation` gains `doc_type` (D2) | `Citation` is quoted by 5.3, 6.2 and 16.1 | `authority_rate` looks up each citation's `source` in the registry; no schema change |
| The gate goes before `screen_prompt` at `main.py:375` and `:429` | A call there changes 5.1's `handler_head` excerpt (from `@app.post("/v1/query"` to `    if hit:`) and 6.3's stream excerpts | a pure ASGI door installed after `main.py:66`; the handlers stay byte-identical |
| Add a `lane.py roles` subcommand | A new subcommand changes `commands/tests/test_lane.py:25-26` | `commands/desk_ops.py` |
| Identity at `services/chat/agent.py:152-171`, tenant at `:183-188` | `caller()` is 150-169; `tenant_for` is at 186 and the 403 at 187-188 | the tree's lines |
| The audit bucket's retention at `terraform/storage.tf:94` | The retention policy is 81-89; line 94 is the comment that says it refuses every delete | 81-89 |
| A signed chip (HMAC over thread, turn, desk and question hash) | Needs a key in Secret Manager | chip ids stored server side in `DeskState`; a press counts only when it matches the thread's last offer |
| Sensitive audit actor `HMAC(tenant_key, email)` | Needs a key | a case reference, with no email (Desk decision 6) |
| A new log sink costs nothing | 13.2 parses `terraform/sink.tf`'s filter and prints which events BigQuery sees (`lessons/13-operations/13.2-usage-reconcile/build.py:163-169`), and 16.2 quotes the sink and asserts its event line (`lessons/16-multimodal/16.2-studio-voice/build.py:93`, `:102`) | widen the one sink and rebuild 13.2 and 16.2 (G10-i) |
| The worker hook rebuilds the ingest quoters (3.2, 3.3, 3.4, 4.1, 4.3, 4.4, 8.3, 15.4, 16.1) | No excerpt covers `services/ingest/main.py:422-446`. The `MEDIA_TYPES` literal at 118-119, which 3.2, 15.3 and 16.1 assert, stays | no rebuild |

Effort scale: S is a day or less, M is two to four days, and L is about a week of author time. These are estimates,
not measurements.

### 4.1 PR 1, G10-a, and PR 2, G10-a2: the route eval scaffold, the dev set and the probe

**Goal.** Measure before building. Every existing question gets a route label (G10-a), the new dev rows are written by
people (G10-a2), the metrics run offline, and four platform facts are measured on a lane.

**PR 1, G10-a: files and change.**

- `evals/routes.jsonl` (new): the 207 relabelled dev rows; G10-a2 adds the rest of section 5.2's dev column. Each row
  has these fields: `{id, of, group, tenant, identity, question, prev_question, prev_route, expected_route,
  acceptable_routes, expected_doc_types, expected_outcome, case_type, must_escalate, language, expect_model_calls_max,
  must_contain, must_not_contain, source, split, author, note}`.
  - `identity` is a symbolic name (`acme_employee`, `acme_leaver`), resolved from `PROJECT` at run time, so no row
    carries an email.
  - Routes are handbook, statute, case, clarify and out_of_scope.
  - Outcomes are answer, grounded_refusal, not_covered, denied, clarify, case and oos.
- `evals/build_routes.py` (new): builds the 207 relabelled dev rows. They come from 65 golden rows
  (`evals/golden.jsonl`), 42 paraphrases (`evals/paraphrases.jsonl`) and about 100 first-person rewrites of the 317 SFT
  user turns (`evals/sft/documind_sft_v1.chat.jsonl`). The script also validates the hand-written rows. `--check`
  fails when a golden row has no route label. The labelling rule of the research report's section 4.4 applies: a
  first-person question with no authority marker goes to `handbook`, and "under the Act / Code / law" goes to
  `statute`.
- `evals/route_eval.py` (new, stdlib). It provides:
  - `--selftest`: the schema, the group split, cross-split contamination by normalised text, and the Wilson helper;
  - scoring of a predictions file;
  - the 5x5 confusion matrix, with each rate printed with its denominator and a Wilson 95% interval;
  - per-class escalation recall and per-language recall;
  - `authority_rate`: each citation's `source` is mapped to its class through the registry (section 5.1), or through
    `evals/manifest.json` offline, and must fall in the row's `expected_doc_types`;
  - `--arm B|C|Astar`, which labels and scores a run by arm. B is the routed Desk. C is code only: the gate, coverage,
    then a direct answer over the person's doc types with no classifier. A* is one agent with the real `doc_type`
    vocabulary and the calculators. The live arms arrive with G10-g (B, C) and G10-h (A*); section 1.3 states the
    ship decision they feed.
- `evals/route_probe.py` (new): the Phase 0 probe. It records:
  - whether `gemini-3.1-flash-lite` on `location="global"` returns `response_logprobs`;
  - whether `thinking_budget=0` gives zero thinking tokens, as rag-api's router sets it
    (`services/rag-api/router.py:16-17`);
  - how many output tokens the enum schema takes;
  - whether `gemini-3.6-flash` accepts the minimal thinking level.
- `evals/tests/test_route_eval.py` (new).
- `mk/agents.mk` (created here unless an earlier pull request created it, section 4.0), `Makefile:188` `.PHONY`,
  `mk/README.md`: the targets `desk-check` and `route-probe`.

**Tests.** The Wilson lower bound when every row passes is n / (n + 3.84): 20 gives 83.9%, 73 gives 95.0%, 75 gives
95.1% and 100 gives 96.3%. The other tests cover a group split leak, an identical cross-split question, and a golden id
with no label.

**Make targets.** `make desk-check` (offline) and `make route-probe PROJECT=documind-ai-YOUR-ID` (lane, a few calls,
well under Rs 1).

**Offline proof.**

- `python deploy/evals/route_eval.py --selftest` prints the rows per route and split, then "no cross-split pair".
- `python -m unittest discover -s deploy/evals/tests` passes.
- `python tools/check_one_retrieval.py deploy/` passes.

**Lane proof.** `make route-probe` prints the four facts. The author records them in the pull request description.
They are not committed, because they are lane-dependent. They decide whether acceptance rule E is built (section 4.8).

**Pages to rebuild.** None. Only new files are added.

**Effort.** M.

**Depends on.** Nothing.

**PR 2, G10-a2: the new dev rows.** The 430 new dev rows of section 5.2's dev column (45 each for handbook, statute
and out_of_scope, 30 clarify, 100 escalation, 120 first-person non-escalation, 20 near-miss, 15 follow-up pairs and 10
multi-intent), from the commissioned writers, with the two-labeller 60-row overlap and its kappa recorded in the pull
request. People write the escalation and first-person rows, with Hindi and Hinglish by a fluent writer (Desk decision
2). `build_routes.py --check` validates them. It may land in two parts: the escalation and first-person rows first,
because they unblock G10-c, then the rest. No page is rebuilt.

**Effort.** L, plus writer time: two to three weeks elapsed. It is its own milestone, M2, before the router is scored
(section 7).

**Depends on.** G10-a (the schema and `--check`); the writers, commissioned at M0.

### 4.2 PR 3, G10-b: the doc_type registry, the worker hook and the relabel of stored data

**Goal.** Every current chunk of a registered document carries its class on every store. New ingests take the class
from an operator registry, never from the uploader.

**Files and change.**

- `shared/doc_types.py` (new). It holds:
  - `CLASSES = ("policy", "statute", "guidance", "report", "transcript", "contract", "invoice")` and `UNKNOWN`;
  - `registry_from_manifest()`, which maps object names (the basename of each manifest `file`) to a class;
  - the media parent rule: longest same-tenant slug prefix (section 5.1);
  - `assign(db, doc, name)`, which reads `tenants/{t}/doc_types/{source_id}` (the id from
    `services/ingest/idempotency.py:103-105`). It returns the class only when the entry's pin equals `doc.doc_key`
    (`services/ingest/contracts.py:76-78`), and "unknown" otherwise;
  - `set_class()`, the operator's write, with `set_by`, `set_at` and `source`.
- `services/ingest/main.py`:
  - one import;
  - one line before the `try:` at 432 in `index_document`: `doc = doc_types.assign(_db, doc, msg.name)`;
  - line 437 keeps a registered class for media: `doc.doc_type` when it is not "unknown", else
    `MEDIA_TYPES[msg.content_type]`;
  - `assign()` logs `{"event": "doc_type_pin_miss", "tenant", "name"}` when a registered name arrives with a new
    `doc_key`.

  No excerpt covers 422-446. `MEDIA_TYPES` (118-119) and the substring
  `text = None                                          # a media document has none` that 15.3 asserts are unchanged.
  Media keep their media type in `kind`, which every media reader already uses (`services/rag-api/main.py:77-79`,
  `services/frontend/citations.py:60-63`).
- `services/ingest/relabel.py` (new). It runs with `PYTHONPATH=.:services/ingest`, as `backfill-vectors` runs
  `reconcile.py` (`mk/ingestion.mk:44-48`). Without `--apply` it prints the plan; `--apply` executes section 5.1's
  steps 1 to 7; `--reset` plans every row of the tenant back to "unknown" by the same steps and leaves the registry
  in place. `--selftest` covers the planner. Step 3's `structData` update lives in this file and never calls
  `mirror.upsert(` or `_mirror.after_swap(`/`after_undo(`, because 15.3 asserts that only `services/ingest/main.py`
  does (`lessons/15-graph/15.3-managed-mirrors/build.py:130-131`). If a method is added to `managed.VertexSearchStore`
  instead, it goes after `delete()` (15.3 slices the class up to `def delete(`, `:133-134`), and the pages that read
  `managed.py` (8.3, 15.1, 15.3, 15.4) are checked with `check_lesson.py` and rebuilt where it says so.
- `commands/desk_ops.py` (new unless an earlier Desk pull request created it, section 4.0): the subcommand
  `doc-types`. It supports `SEED=manifest` and `FOLLOW=<name>` (re-pin a reviewed new version) for the registry.
- The target: `make doc-types` runs `python commands/desk_ops.py doc-types` for the registry (`SEED`, `FOLLOW`); with
  `APPLY=1` it then runs `PYTHONPATH=.:services/ingest python services/ingest/relabel.py --tenant $(TENANT) --apply`,
  and with `RESET=1` it passes `--reset`. A two-line recipe in `mk/agents.mk`.
- `commands/tests/test_doc_types.py` (new, stdlib, with a fake Firestore).

**Tests.**

- The media parent map for the five media objects.
- `whiteboard_arch.png` stays unregistered.
- A pin mismatch gives "unknown".
- Every manifest object except `whiteboard_arch.png` maps to a class (the manifest's own media values, figure, video
  and image, are not classes).
- A second relabel plans no change, and neither do rows already carrying their class.
- `--reset` then a relabel returns to the same plan.
- Non-current rows are never passed to `_repair_snapshots`, which raises on them (`services/ingest/indexer.py:206`).

**Make targets.** `make doc-types TENANT=acme [SEED=manifest] [FOLLOW=hr_policy_2026.md] [APPLY=1] [RESET=1]`.

**Offline proof.**

- `python -m unittest deploy/commands/tests/test_doc_types.py` passes.
- `python services/ingest/relabel.py --selftest` passes.
- `python tools/check_one_retrieval.py deploy/` passes.
- `python deploy/validate.py` passes. Its shared-deps rule holds, because the ingest image pins
  `google-cloud-firestore`.

**Lane proof.**

1. `make doc-types PROJECT=documind-ai-YOUR-ID TENANT=acme SEED=manifest` prints one line per object: name, current
   label, class, pin and chunk count.
2. `APPLY=1`, then the same for zeta and globex.
3. A second plan lists no change.
4. `make sources TENANT_ONLY=acme` shows the same versions.
5. A `POST /v1/query` with `filters {"doc_type": "policy"}` for lk-06 ("What is the notice period for a confirmed E3?",
   `evals/golden.jsonl:6`) cites `hr_policy_2026.md`. On a lane ingested with `make ingest-corpus`, the same query
   returned `EMPTY_POOL_ANSWER` before the relabel.
6. `make eval-live PROJECT=documind-ai-YOUR-ID` gives the same per-row verdicts as before.
7. `make doc-types TENANT=acme RESET=1 APPLY=1` (and zeta, globex) restores "unknown".

**The author's lane between M1 and M5.** 5.1 and 10.3 teach that the worker stamps every text upload "unknown" and
that a class filter empties the pool (`lessons/10-agents/10.3-tool-failures/parts/b.html:54`, and 10.3's `doc_type
invoice` cell), and gap phase 2 re-verifies 10.3 on the lane (G6-a, G2-b). So the lane runs relabelled only while a
Desk proof needs it (G10-b, G10-d), `RESET=1` restores it for rehearsals, and the relabel stays on from M5 (section 7).
The alternative is a second lane for the Desk proofs (Desk decision 28).

**Pages to rebuild.** None forced, because no quoted line changes. The pages that state "unknown" stay true at their
point in the course, because the relabel is taught in 10.6. The two later pages that state it get content pull
requests after 10.6 (section 4.13).

**Effort.** M.

**Depends on.** Nothing.

### 4.3 PR 4, G10-c: the hard gate, identifier checks and the rag-api door

**Goal.** A question the law hands to a person never reaches retrieval or a model on any rag-api path, per tenant flag.

**Files and change.**

- `shared/desk_rules.py` (new, stdlib). It holds:
  - `RULES_VERSION`;
  - first-person markers and topic patterns for five classes (posh, grievance, privacy_request, exit_dues,
    human_requested) in English, Devanagari Hindi and Hinglish;
  - `gate(question)`, which returns the class only, never the matched text;
  - the action lexicon for `out_of_scope` candidates;
  - `mask(question)`, which returns the masked text and the kinds masked.

  It is written new. The research report's scratch lexicon was never committed.
- `shared/identifiers.py` (new, stdlib): Aadhaar (12 digits, first digit 2 to 9, Verhoeff), card numbers (13 to 19
  digits, Luhn), and PAN and GSTIN patterns with the GSTIN mod-36 check. The gateway classifier uses regexes only
  (`services/litellm/documind_classifier.py:11-16`), and G9-A keeps its own checks there (section 3.1).
- `shared/desk_law.py` (new, stdlib data): the fixed reply templates for every gate class, shared by rag-api and chat so
  there is one text. G10-e (section 4.5) adds the case table.
- `services/rag-api/desk_door.py` (new): a pure ASGI middleware on `POST` to `/v1/query`, `/v1/stream` and
  `/v1/passages`. The path set names `/v1/passages` from the start, so G10-p does not edit the door.
  - It buffers the body and caps it at 64 KiB, with a 413 above that. `QueryRequest.query`'s 4,000 characters
    (`services/rag-api/schemas.py:15`) are checked by pydantic only after the door has buffered the body, so they do
    not bound it. It runs `gate()` on `query`. A body that is not valid JSON is replayed unchanged, and the handler's
    own 422 answers it.
  - On no hit, it masks Aadhaar and card numbers when the tenant's `desk_gate` is on, and replays the body. PAN and
    GSTIN pass, as today.
  - On a hit, it verifies identity and membership through the functions `install` was given: `auth.verify_iap`
    (`services/rag-api/auth.py:35`) and `auth.enforce_membership` (`:53`). So the files calling `iap.identity(` stay
    the three that 8.1 asserts (`lessons/08-security/8.1-identity-tenancy/build.py:111`). It then reads `desk_gate`
    through the `tenant_settings` it was given.
  - It imports nothing from fastapi or starlette, so its test runs in the shared interpreter (`auth.py:24` imports
    fastapi, and CI's shared step installs only pydantic, pandas, pypdf and requests). It hands `verify` a small object
    whose `headers` is a case-insensitive mapping built from the ASGI scope, which is all `verify_iap` and
    `iap.identity` read. An exception from `verify` or `member` that carries `status_code` becomes that JSON response
    in the door itself, because an `HTTPException` raised in middleware outside Starlette's exception middleware would
    surface as a 500.
  - When the flag is on, it returns the fixed template. For `/v1/query` that is a `RAGResponse` with answerable false,
    no citations, model "none", backend "desk_gate", cost 0 and 0 tokens. For `/v1/stream` it is a `token` event, then
    `done`, in main.py's event names (483, 509). The handler never runs, so nothing is retrieved, generated or cached.
  - It logs `{"event": "desk_gate", "surface", "tenant", "user", "class", "rules_version"}`. For posh, grievance and
    privacy_request, `user` is null and `class` is "sensitive".
- `services/rag-api/main.py`: two lines after 66 (the CORS middleware at 64-66), `from desk_door import install as
  install_desk_door  # noqa: E402` and `install_desk_door(app, settings=lambda t: tenant_settings(t),
  verify=verify_iap, member=enforce_membership)`; both names are already imported at `main.py:15`. No excerpt covers
  60-102: 6.3 quotes the `import telemetry` lines, which are above them. 10.1's route list, a regex over `@app.get`
  and `@app.post` (`lessons/10-agents/10.1-agent-loop/build.py:92-93`), is unchanged.
- `commands/desk_ops.py desk`: `TENANT`, `DESK_GATE=on|off`, a merge write to `tenant_settings/{t}` as `set_policy`
  does (`shared/tenancy.py:165-166`).
- `commands/tests/test_desk_rules.py` (new, stdlib).

**Tests.**

- 0 fires on the 424 existing questions: 65 golden, 42 paraphrases and 317 SFT user turns.
- 0 fires and 0 masks on every question the rest of the course sends as acme, because `desk_gate` stays on for acme
  from 10.5 onward (section 6.1). In the kit (`commands/tests/test_desk_rules.py`): `deploy/smoke/*.py`,
  `deploy/workshop_demos/**`, and the gap plan's `evals/handoff.jsonl` and `evals/adversarial/attacks.jsonl` as they
  land. In the author repository (`tools/tests/test_desk_gate_lessons.py`, because the learner kit has no `lessons/`):
  the question literals in `lessons/*/*/build.py` and `lessons/*/*/lane*.py`, extracted by the test. A new lesson or
  smoke question joins the scanned set. The synthetic Aadhaar numbers the course already uses (8.3's
  `2234 5678 9012`, 18.1's `2345 6789 0123`) fail the Verhoeff check, so they are not masked; 18.1 sends its presets
  to the gateway, not through the door.
- Every dev escalation row of each class fires (G10-a2's rows).
- Verhoeff and Luhn test vectors pass.
- The door is tested with a fake downstream app and stubbed auth, in plain asyncio with no Starlette:
  - flag off gives byte-identical replay;
  - a hit on `/v1/query` and on `/v1/stream` gives the template, and the downstream app is never called;
  - an unverified caller gets 401, a non-member 403, a body over 64 KiB 413, and invalid JSON is replayed unchanged.

**Make targets.** `make desk TENANT=acme DESK_GATE=on|off`.

**Offline proof.**

- `python -m unittest deploy/commands/tests/test_desk_rules.py` passes.
- `python tools/check_retrieval.py` stays green.
- `check_one_retrieval.py` and `validate.py` pass.

**Lane proof.**

1. `make build deploy-services PROJECT=documind-ai-YOUR-ID REGION="$REGION" SERVICES=api SCRIPTS=commands/lesson-12.2.sh`.
2. With the flag off, a POSH disclosure from the dev rows answers as today.
3. `make desk TENANT=acme DESK_GATE=on`. After 60 s, the same `/v1/query` returns model `none`, backend `desk_gate`
   and `cost_usd` 0.
4. The same through `/v1/stream` gives one token event and `done`. The Chat page's default direct brain, which streams
   to rag-api (`services/frontend/chat.py:28`, `:60-65`), shows the template.
5. An outsider gets 403, not the template.
6. `make eval-live` shows unchanged verdicts.
7. Cloud Logging shows the `desk_gate` row with user null.
8. `make desk TENANT=acme DESK_GATE=off`. The flag stays off for real tenants until G10-e ships the case path.

**Pages to rebuild.** None. The lexicon does not fire on any existing question, so no page output moves.

**Effort.** M.

**Depends on.** G10-a and G10-a2's escalation and first-person rows, which the lexicon is tuned and tested against.
G9-A is soft.

### 4.4 PR 5, G10-d: list filters on every retrieval path

**Goal.** One retrieval can be scoped to a set of classes (the statute desk's `statute` and `guidance`), with the same
meaning on every backend and a cache key on the canonical set.

**Files and change.**

- `services/rag-api/schemas.py:24`: the comment reads "a string, or a list of up to 5 strings". The keys
  (`FILTER_KEYS`, line 12) stay.
- `services/rag-api/main.py:193-205`, `check_filters`: `doc_type` is a non-empty string or a list of 1 to 5 non-empty
  strings; `kind` stays a single string, and a list for `kind` is a 400 that says so. The kit's `kind` branches are
  scalar and differ by path (`services/rag-api/retriever.py:164-167`, `:196`, `:291`; `_search_filter` drops `kind`
  at `:255`), so a `kind` list would mean different things on different backends. A `doc_type` list is made canonical
  in place (sorted, de-duplicated, and a one-item list becomes its string), so `scope_of`
  (`services/rag-api/semantic_cache.py:38-43`), which sorts keys but not list values, hashes one form.
  `{"doc_type": 3}` stays a 400.
- `services/rag-api/retriever.py`: one helper, `matches(row, filters)`, with list semantics for `doc_type`, replaces
  the scalar compares at 173, 231, 325 and 429. The other paths change as follows:
  - the Firestore fallback's `where(k, "==", v)` at 74-75 takes `where("doc_type", "in", list)` for a list;
  - `_search_filter` (251-255) writes `ANY("a", "b")`;
  - the Vector Search restricts (349-354) put the list in `allow_tokens` (the changed line is 354).
- `shared/documind_tools.py:284-285`: the local lane's Chroma `where` uses `$in` for a list.
- `tools/check_retrieval.py:630-641`: new cases. A `doc_type` list is accepted and canonical; six values, an empty
  list or a non-string member is a 400; `{"kind": ["figure"]}` is a 400.

**The `in` pre-filter is already in the kit.** Firestore's vector `find_nearest` takes an `in` pre-filter in
`_media_rows` today (`services/rag-api/retriever.py:167`, `kind in [figure, segment]`), on the pinned
`google-cloud-firestore`, served by the `chunks_filter_vector` composite indexes
(`terraform/firestore_indexes.tf:55-65`). The fallback's `where("doc_type", "in", list)` uses the same indexes.

**Tests.** The `check_retrieval.py` cases above, plus a restricts test asserting that the list reaches `allow_tokens`.

**Make targets.** None new.

**Offline proof.** `python tools/check_retrieval.py` passes, and the rebuilt pages pass `check_lesson.py` and
`audit_pages.py`.

**Lane proof.**

1. Redeploy the API.
2. jn-11 ("the ministry's compliance handbook", `evals/golden.jsonl:55`) with `filters {"doc_type": ["statute",
   "guidance"]}` cites the guidance PDF.
3. With `SEMANTIC_CACHE=on`, `["guidance", "statute"]` hits the same cache scope.
4. The scalar filter still works.
5. `make tenant-backend TENANT=acme RETRIEVAL_BACKEND=firestore`. After 60 s the list filter works on the Firestore
   rung. `make tenant-backend TENANT=acme RETRIEVAL_BACKEND=vector` restores the pin. (`commands/lesson-12.2.sh:52`
   defaults to firestore, but `make deploy-services` sets `RETRIEVAL_BACKEND=vector` first, `Makefile:347`, so the
   deployed default is Vector Search.)
6. `make eval-live` is unchanged.

**Pages to rebuild.**

- 3.4: the restricts excerpt (n=6) and the fallback span.
- 5.1: the restricts (n=6), `check_filters` (n=13), the schema (n=13 from `FILTER_KEYS`), and the widget's error
  text (`lessons/05-retrieval/5.1-query-filters/build.py:95`).
- 5.4: the whole `_firestore_fallback`.
- 8.2: the restricts (n=6).

The `FILTER_KEYS` asserts in 5.4 (`build.py:117`) and 9.2 (`build.py:105`) still hold.

**Effort.** M.

**Depends on.** Nothing. G10-b is needed for a meaningful lane proof.

**Alternative** (Desk decision 4): no list filters. The statute desk retrieves `statute`, and an identifier anchor on
"compliance handbook" or "ministry" selects `guidance`. This saves the four rebuilds.

### 4.5 PR 6, G10-e, and PR 7, G10-e2: roles, cases, the chat door, the eval identities and the Desk page's case half

**Goal.** A person is one press away. A rule hit or the "Raise a case" button opens a case in the queue of the person
the law names, with the statutory reference and the clock, and the queue owner sees it in an inbox.

**PR 6, G10-e: files and change.**

- `shared/roles.py` (new). It stores `tenants/{t}/roles/{email}` as `{roles, set_by, set_at}`, a separate document,
  because `add_member` overwrites the member document without merge (`shared/tenancy.py:77-82`).
  - `set_roles` refuses a non-member (`is_member`, `:46-52`).
  - `roles_for` requires membership. A missing role document is `["employee"]`. A document lists every role it
    grants, so `employee` is never implied beside it. A failed read allows only the case desk.
  - It emits `role.grant` and `role.revoke`.
  - The launch roles are listed in section 5.3.
- `shared/desk_law.py`: the case table. Each type has its queue key, the clock text, the basis passages with corpus
  `file:line`, and the instrument status table (section 5.4).
- `shared/cases.py` (new): `draft`, `confirm` (a transaction with a client idempotency token), `cancel`, `set_status`
  (queue roles only), `list_for`, `overdue`.
  - Ids come from `secrets.token_hex(16)`.
  - A draft carries `expire_at` 30 minutes out, checked in code (410).
  - Records live at `cases/{case_id}` with a tenant field, the layout G2 uses for approvals.
  - Every read is a point read that checks the tenant and the reader's queue role, and returns 404 otherwise.
  - Fields: `tenant`, `requester`, `case_type`, `queue`, `unit` and `chosen_contacts` (posh), `status` (draft, open,
    acknowledged, in_progress, resolved, closed, withdrawn), `source` (rule, model, desk, button), `created_at`,
    `due_at`, `sla_basis`, `route_trace`, `route_tried`, `partial_answer_citations` (chunk ids), `summary` (confirmed,
    1,000 characters or fewer; null for posh), `statutory_flags`, `question_sha256`, `expire_at` (drafts only). The
    research report's `delivered_at` and `sink_ref` (its section 6.4) belong to Phase E delivery and are left out. A
    POSH record holds the unit and the chosen contacts, with no text.
- `services/chat/desk.py` (new): an `APIRouter` with `POST /v1/cases` (the six employee types), `POST
  /v1/cases/{id}/confirm`, `POST /v1/cases/{id}/cancel`, `GET /v1/cases` and `POST /v1/cases/{id}/status`, plus
  `install(app, caller, tenant_for, thread_config)`. `install` mounts the router and the chat door, a pure ASGI gate on
  `POST /v1/chat`. Both are written whole here, with `thread_config` already a parameter and a shadow hook,
  `_shadow(...)`, that does nothing until G10-g fills its body. So G10-f and G10-g change no line that 10.5 quotes.
  The chat door:
  - buffers the body with the rag-api door's 64 KiB cap and reads `question` from the `ChatRequest` body;
  - on `PROFILE=local` takes the tenant from `LOCAL_TENANT` and treats every flag as off, as `chat()` never touches
    Firestore there (`services/chat/agent.py:183-186`); a failed settings read is "off";
  - on a hit verifies the caller with the passed-in `caller()` (`:150-169`), not with `iap.identity` directly, and
    looks up the tenant (`:186`);
  - when `desk_gate` is on, returns the template in `/v1/chat`'s response shape, with `tool_calls []` and
    `refusals []`; `chat()` never runs, so nothing is checkpointed;
  - with `desk_gate` on and no hit, masks Aadhaar and card numbers in `question` before replaying the body, so
    neither the brain, the checkpoint nor Gemini sees them.
- **Hooks for the Google Chat door (Desk decision 36), only if Desk decision 29 is taken before this pull request
  merges.** They cost a few lines here and save G10-j from rebuilding 10.1 and 10.5:
  - Every Desk and case endpoint takes its identity from a module-level `_principal(request, caller)`, whose body here
    is `return caller(request)`. G10-j replaces only that body (section 4.11a), the pattern of `_shadow`. The chat door
    keeps calling `caller()` directly.
  - The principal dict carries `via`, default "direct", and the case record carries it too.
  - The POSH create in `POST /v1/cases` accepts the same client idempotency token as `confirm`, so a retried or
    doubled button press opens one record.
  - `terraform/desk.tf` creates a sixth account with no project roles, `documind-gchat-sa` (17 characters, matching
    `documind-[a-z]+-sa`, `tools/check_authz.py:75`). The invoker loop at `commands/lesson-12.8.sh:39` and the
    documind-chat line of the caller graph at `terraform/sa.tf:103` name it beside the five eval accounts, so 10.1's
    expected deploy output (`lessons/10-agents/10.1-agent-loop/build.py:383`) and lane box (`parts/c.html:93`) change
    once, in this pull request's 10.1 rebuild. The `tools/tests/` test for `callers_in()` finds all six new accounts on
    both sides, and `desk-operators` does not name the account. It is on no roster, so until G10-j lands the roster
    refuses it, as it refuses the outsider.
  - `tools/check_authz.py` gains the minting half of the delegate checks (section 4.11a), so no grant to mint as the
    account can land before the account has a use.
- `services/chat/agent.py`: after line 212, `import desk  # noqa: E402` and `desk.install(app, caller=caller,
  tenant_for=tenant_for, thread_config=thread_config)`. Every agent.py excerpt is bounded by `n=` or `end=`, and the
  chat row literal that 13.2's regex guard reads (`build.py:150`) is untouched.
- `services/chat/desk_overdue.py` (new): the hourly job's entry. For cases within 24 hours of due and unacknowledged,
  and for breached cases, it logs the id, queue and `due_at` only.
- `shared/audit_log.py`: a new line after G2's approvals line, which itself follows `"doc.mirror"` at 27:
  `"desk.route_denied", "case.open", "case.update", "case.close", "role.grant", "role.revoke"`. `emit()` asserts
  registration (`:45`). 3.4's `def emit(` excerpt (n=200, to end of file) is unchanged.
- `terraform/desk.tf` (new). It is kept apart from `firestore_indexes.tf` because 5.4 computes its index table from
  that file. It declares:
  - a Firestore TTL on `cases.expire_at`, following the pattern at `terraform/firestore_indexes.tf:165-183`;
  - composite indexes for the inbox (tenant, queue, status, created_at) and for the overdue scan;
  - `variable "desk_job"` (default false) and `variable "chat_image"` (default ""), with
    `local.desk_job = var.desk_job && var.chat_image != ""`, on the pattern of `terraform/batch.tf:9-16`. The Cloud
    Run job `documind-cases-overdue` (the chat image, chat-sa), `google_cloud_run_v2_job_iam_member` `run.invoker` on
    it for chat-sa, and an hourly Cloud Scheduler trigger whose OAuth token is chat-sa's (the pattern of
    `batch.tf:84-109`) all take `count = local.desk_job ? 1 : 0`. The job cannot be created before its image is
    pushed (`batch.tf:5-6`);
  - five eval service accounts with no project roles, named to match `check_authz`'s caller pattern
    `documind-[a-z]+-sa` (`tools/check_authz.py:75`): `documind-evalacme-sa`, `documind-evalzeta-sa`,
    `documind-evalglobex-sa`, `documind-evalleaver-sa` and `documind-evalgrc-sa` (19 to 22 characters). A hyphenated
    name such as `documind-desk-eval-acme` matches nothing, so the graph side would list fewer callers than the
    script's loop and the check at `tools/check_authz.py:143` would fail.
- `Makefile` core: `DESK_JOB ?= false` and `CHAT_IMAGE ?= $(IMAGE_REPO)/chat:$(GIT_SHA)`, on the pattern of
  `RECONCILE_IMAGE` (`Makefile:137`), and `-var desk_job=$(DESK_JOB) -var chat_image=$(CHAT_IMAGE)` in
  `TF_EXTRA_VARS` (`:153-166`), which `INFRA_VARS` (`:171`) passes to the plan. No page quotes that block: 13.2
  asserts only the `plan:` and `up:` lines (`lessons/13-operations/13.2-usage-reconcile/build.py:955-956`).
- The caller graph for `documind-chat` in `terraform/sa.tf:103` and the invoker loop at `commands/lesson-12.8.sh:39`
  both name the five accounts. `tools/check_authz.py` stays green because the names match its caller regex; a test
  in `tools/tests/` asserts that `callers_in()` finds all five on both sides. Adding names to the loop's `for` line
  adds no `${REGION:-us-central1}`, so 10.1's count assert (`build.py:107`) holds. The accounts are Terraform's, so
  `make plan up` creates them before the deploy script binds them.
- `mk/agents.mk`: a new `desk-operators` target grants `ADMIN_EMAILS` `roles/iam.serviceAccountTokenCreator` on the
  five eval accounts in its own loop. The core `operators` loop (`Makefile:386`), which 12.2 asserts verbatim
  (`lessons/12-protocols/12.2-mcp-deploy/build.py:93`), is unchanged.
- `commands/desk_ops.py`:
  - `roles`: grant, revoke, list;
  - `queues`: writes `tenant_settings/{t}.case_queues` from a file, and refuses a POSH section without every unit's
    Internal Committee and the Local Committee contact;
  - `cases`: open, due and breached;
  - `desk`: refuses `DESK_GATE=on` for a tenant whose POSH queue is not configured.
- `evals/desk/queues.acme.json`, `queues.zeta.json`, `queues.globex.json` (new): the synthetic tenants' queues, with
  placeholder contacts (`you@example.com`). Acme has the units hyderabad and pune (`acme/townhall_2026_q1.md:6-7`).
  Each SLA is a number the author sets, labelled as the company's own target.
- `smoke/smoke_cases.py` (new). The requester is documind-evalacme-sa, the inbox reader documind-evalgrc-sa and the
  404 documind-evalzeta-sa, all on the chat service. A script cannot call the chat service as a person, because the
  bearer leg needs an ID token minted for `SELF_URL` (`services/chat/agent.py:163`), which only a service account can
  mint for another audience. The `/v1/stream` leg runs as ui-sa on acme's roster, as `make smoke` does, because the
  eval accounts are not invokers of documind-api.
- `commands/tests/test_cases.py` (new; a stdlib half and a chat-pins half).
- `.github/workflows/checks.yml` and `deploy/.github/workflows/documind-dryrun.yml`: the chat-pins step also runs
  `DOCUMIND_REQUIRE_LIBS=1 python -m unittest commands/tests/test_cases.py` (section 4.0).
- G2-a's slice, only if the author moves G10-e ahead of G2-a: `commands/lesson-12.8.sh:32` gains `AUDIT_BUCKET`; the
  two chat pins; the `objectCreator` grant in `terraform/storage.tf`.

**Tests.**

- Confirm is idempotent.
- An expired draft gives 410. This is tested offline only, because a 30-minute expiry cannot be waited for in a
  smoke.
- Another tenant's case gives 404; a non-requester without the queue role gives 404.
- `roles_for`: a missing document gives `employee`; a document with `leaver` does not add `employee`; a failed read
  allows only the case desk.
- A POSH record has no text field.
- A rule-hit on `/v1/chat` makes no model call and writes no checkpoint.
- The door replays the body unchanged when the flag is off, uses `LOCAL_TENANT` with every flag off on the local
  profile, and masks an Aadhaar number when the flag is on and nothing fires.

**Make targets.** `make roles TENANT= EMAIL= ROLES=`, `make desk-queues TENANT= FILE=`, `make cases TENANT=`,
`make cases-overdue`, `make smoke-cases`, `make desk-operators ADMIN_EMAILS=`; `make plan up DESK_JOB=true`.

**Offline proof.**

- `python -m unittest deploy/commands/tests/test_cases.py` passes in both halves.
- `check_authz.py` passes, with the five eval accounts on both sides of documind-chat's graph and its chat-source URL
  asserts as the latest gap pull request left them (before G1, no `MCP_URL` or `AGENT_URL`; after G1, `PEER_URL`).
- `validate.py` passes.
- `terraform -chdir=deploy/terraform validate` passes.

**Lane proof.**

1. `make plan up PROJECT=documind-ai-YOUR-ID`: the eval accounts, the TTL and the indexes; `make up` builds and pushes
   the chat image at this commit.
2. `make plan up PROJECT=documind-ai-YOUR-ID DESK_JOB=true`: the job, its invoker and the schedule, on that image.
3. Deploy chat, ui and api with `ADMIN_EMAILS="$ME"`, then `make desk-operators ADMIN_EMAILS="$ME"`.
4. `make roster` each eval account onto its own tenant, for example `make roster TENANT=acme
   MEMBERS=documind-evalacme-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com`; the leaver and grc accounts go on acme.
   Then `make roles TENANT=acme EMAIL=documind-evalgrc-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
   ROLES=grc_member`, and `make roles TENANT=acme EMAIL=you@example.com ROLES=grc_member` for the browser check in
   G10-e2.
5. `make desk-queues TENANT=acme FILE=evals/desk/queues.acme.json`.
6. `make desk TENANT=acme DESK_GATE=on`.
7. `make smoke-cases` passes:
   - the POSH disclosure through `/v1/chat` (as documind-evalacme-sa) and through `/v1/stream` (as ui-sa) gives model
     `none` and cost 0;
   - a grievance drafted and confirmed by documind-evalacme-sa is seen in documind-evalgrc-sa's inbox;
   - documind-evalzeta-sa gets 404 on it.
8. `gcloud storage ls gs://documind-ai-YOUR-ID-audit/YYYY/MM/DD/acme/` lists `case.open`, and the event's actor holds a
   case reference and no email.
9. The POSH record in Firestore holds no text.
10. `make cases-overdue` logs no sensitive field.

**Pages to rebuild.**

- 8.3. Its build collects every literal `emit("...")` in the kit's runtime files and asserts the list
  (`lessons/08-security/8.3-dlp-guard-audit/build.py:91-93`). It also parses `AUDIT_ACTIONS` for its table (`:98`).
- 10.1. Its expected deploy output names documind-chat's invoker bindings ("twice: documind-ui-sa,
  documind-outsider-sa", `lessons/10-agents/10.1-agent-loop/build.py:383`), which now include the eval accounts (and
  approver-sa, after G2-a), and its lane box says "The UI's account and the outsider may invoke it"
  (`parts/c.html:93`). The two mint lines (`build.py:386`) stay, because `operators` is unchanged. `check_lesson.py`
  confirms the rest; 12.2 is untouched.

**Effort.** L+, about a week and a half.

**Depends on.** G10-c; G2-a (the shared slice) and the end of gap phase 2, so G2-d's 8.3 scene lands first; G8-a (the
CI job).

**PR 7, G10-e2: the Desk page, case half.**

- `services/frontend/desk.py` (new page, the case half):
  - "Raise a case", always visible;
  - the draft form: edit, confirm, cancel;
  - the POSH card with the unit, the contact choice and the Local Committee contact;
  - the inbox for queue roles.

  `services/frontend/app.py` gets an import line, a new line after 17 (`pages.insert(1, "Desk")`) and an `elif page ==
  "Desk"` in 25-32. The substring 16.2 asserts (`build.py:114`) stays.
- A stdlib page test with Streamlit stubbed, in the style of `tools/check_authz.py`'s documents-page check: the inbox
  lists only the reader's queue, and the POSH card always shows the Local Committee contact.

**Lane proof.** Deploy ui. On the Desk page, as you@example.com: raise a grievance, edit it, confirm it, and see it in
the inbox; a POSH disclosure shows the card with no model call.

**Pages to rebuild.** None; `check_lesson.py 16.2` confirms its `app.py` substring.

**Effort.** M.

**Depends on.** G10-e.

### 4.6 PR 8, G10-p: the passages path (a proposed change to gap decision 14)

Gap decision 14 asks for "a retry-free `retrieve`-only flag on `/v1/query` as its own gap"
(`plan/agents-mcp-gaps-plan-2026-09-29.md:1130`). A flag would change the `query()` lines that 5.1 (`handler_head`),
5.3 and the 6.x pages quote, so this plan proposes a separate route instead, in its own pull request right after G6-a.
PR #72's decision 14 is edited to read "a retry-free retrieve-only route `/v1/passages`, its own pull request (G10-p)
right after G6-a" (section 3.3). Folding it into G6-a is the alternative (Desk decision 27).

**Goal.** An agent desk reads the full text of this turn's passages without paying for a generated answer it throws
away. The retrieve docstring says the agents ignore rag-api's answer (`shared/documind_tools.py:113`).

**Files and change.**

- `services/rag-api/main.py`: `@app.post("/v1/passages")`, appended after `stream()`, which is the last function.
  Every `stream()` excerpt is bounded. The route:
  - runs behind the desk door (whose path set already names it, section 4.3), `verify_iap`, `enforce_membership`,
    `check_filters`, `screen_prompt` (348-357), the chosen backend, `prefer_current` and the optional rerank;
  - returns `{passages: [{n, chunk_id, source_uri, page, doc_type, kind, section, text}], usage}`;
  - does no generation and uses no answer cache;
  - writes a `{"event": "passages", ...}` usage row.

  The full text goes in a new field, because `Citation.quote` is capped at 25 words by the generator
  (`services/rag-api/generator.py:170`) and at 500 characters by the schema (`shared/documind_schemas.py:43`).
- `shared/documind_tools.py`: `retrieve(..., passages: bool = False)`. The branch sits between the assertion header
  (139-140) and `started = time.monotonic()` (142): `if passages: return _passages(payload, headers)`, a private
  helper that posts to `/v1/passages`. So the URL line (144), the nine lines 10.3 quotes from `started`, and 18.4's
  span and asserts stay byte-identical. The signature (83-85) changes, and in the same edit the `doc_type` hint widens
  to `str | list[str] | None` for G10-d's lists, so 10.1 and 10.4 rebuild once. There is still one `retrieve`, and
  `_passages` takes no `query`, so `check_one_retrieval.py` stays green.
- `tools/check_retrieval.py`: a passages case. It returns full text, no answer, and no cache store.

**Tests.** The case above, plus G6-a's own tests.

**Make targets.** None new.

**Offline proof.** `check_retrieval.py` and `check_one_retrieval.py` pass, and the rebuilt pages pass.

**Lane proof.** `POST /v1/passages` for lk-06 returns NP-03's full paragraph (`acme/hr_policy_2026.md:5-9`), longer
than the 25-word quote. The usage row has `tokens_out` 0. `make smoke-chat` is green.

**Pages to rebuild.**

- 10.1: the `def retrieve(` excerpt (n=3); the route assert at `build.py:93` gains "/v1/passages"; the sentence
  "rag-api has no retrieval-only route" (`parts/c.html:69`) is rewritten.
- 10.4: the raw `FunctionTool(dt.retrieve)._get_declaration()` (`lessons/10-agents/10.4-adapters/build.py:179`)
  gains `passages` and the wider `doc_type`, so its printed declaration and size change.
- `check_lesson.py` confirms 10.3 and 18.4 unchanged. If the branch cannot sit before `started`, 10.3 (the
  `started = time.monotonic()` excerpt, n=9, which includes line 144) and 18.4 (the block marker at `build.py:88`, and
  the asserts at `:120` and `:200`) rebuild too.

G6-a already rebuilds 10.1, 10.3 and 10.4. As its own pull request, G10-p rebuilds 10.1 and 10.4 a second time; folded
into G6-a (the alternative), it adds no page to G6-a's set when the branch keeps 10.3's and 18.4's lines.

**Effort.** M.

**Depends on.** G6-a, which changes the same function.

### 4.7 The 10.5 page pull request

**Goal.** Lesson 10.5 as in section 6.1.

**Files.**

- The page `lessons/10-agents/10.5-case-desk/Netsetos_GCP_Capstone_10.5_Case_Desk_WIX.html`, built by its `build.py`
  from parts, with excerpts from `pagekit.pagebuild.block()`.
- The manifest entry, the roadmap and course-plan rows, and the demo map
  `deploy/workshop_demos/module_10/lesson_10_5/`.
- 10.4's footer (`lessons/10-agents/10.4-adapters/parts/c.html:54`, which names 11.1) names 10.5, and 10.5's footer
  names 11.1. 10.4's lane-box sentence "Module 11 starts from those conversations" (`parts/c.html:50`) becomes a
  pointer to 10.5, and the sentence moves to the lane box of the last Module 10 lesson (10.5 until 10.6 lands).
- Every count in section 6.4.
- The `deploy/UNOWNED.md` rows for the files the page quotes are removed (section 4.0).

**Proof.** `check_lesson.py 10.5` and `audit_pages.py 10.5` pass, and so do the demo checks.

**Effort.** L.

**Depends on.** G10-e and G10-e2. It comes after G2-c, which rebuilds 10.4, and after G2-d, which rebuilds 8.3.

### 4.8 PR 9, G10-f: the router and the desk graph

**Goal.** `decide()` sends each question to one of five routes or to a case, with every security decision made in
code, and this is proven offline with a scripted classifier.

**Files and change.**

- `services/chat/desk_routes.py` (new): the `DESKS` table. Each route has its description (by the documents it owns),
  exemplar ids, `doc_type` list (handbook `[policy]`, statute `[statute, guidance]`), execution mode, model, tools,
  roles (answer desks exclude `leaver`) and clause-prefix queue key. It adds no entry to `BRAINS`
  (`services/chat/brains.py:42`) or to the `ChatRequest` Literal (`services/chat/agent.py:147`), both of which pages
  quote.
- `services/rag-api/schemas.py:30`: rag-api's `brain` Literal gains "desk", so its usage rows name the Desk. The line
  is not quoted (5.1's schema excerpt ends at 24).
- `services/chat/desk_router.py` (new): `decide(question, ctx)`, stages 0 to 7.
  - **L1.** `gemini-3.1-flash-lite` on `location="global"` with enum-only JSON:
    - route: handbook, statute, case, clarify, out_of_scope;
    - second_route: none, handbook, statute, case;
    - case_type: none, posh, grievance, privacy_request, exit_dues, people_query, human_requested;
    - needs_calculation;
    - followup.

    It runs with `thinking_budget` 0, one attempt and a 4 s timeout. `max_output_tokens` is 256, because thinking
    shares the limit (`services/rag-api/router.py:13-15`).
  - **kNN.** k=7 over this tenant's exemplars, with `text-embedding-005` on us-central1.
  - **Acceptance** (the research report's section 5.3, stage 6, without Phase E):
    - A: L1 equals `knn_route` and `knn_share` is 5/7 or more: dispatch.
    - B: L1 equals the anchor desk: dispatch.
    - C: L1 says `out_of_scope` and `knn_sim` is below `tau_oos` (start 0.70): out_of_scope.
    - D: L1 says `case`, or `knn_route` is `case` with 3/7 or more: case, method `model`. Asymmetric on purpose.
    - E: built only if the probe showed logprobs: p 0.80 or more accepts; a top-two margin below 0.15 clarifies.
    - F: anything else: one L2 call on `gemini-3.6-flash`, thinking level set explicitly, 6 s, enum
      `{L1 route, knn_route, clarify}` with no `compliance_review`. On timeout, L1's route stands with the desk chips.
  - **Calibration.** `route_threshold.py` ships the thresholds that give 98% or more accuracy on accepted turns and
    send 70% or more of L1's errors to L2, with the L2 share capped at 15% to start. Every threshold here is a
    starting value.
  - **Checks.** Sticky follow-up (30 minutes), a clarify cap of one, coverage, roles.
  - **Failure.** Any exception, or more than 8 s in total, gives route `fallback`: a direct answer over `[policy,
    statute, guidance]` with the desk chips, never a 500.
  - **Cost.** The router charges G6-a's Meter through `charge_model`, at `shared/prices.py`'s prices.
- `services/chat/desk_graph.py` (new): a LangGraph `StateGraph` over `DeskState` (messages, last_route, masked
  last_question, decision, parts, sections, case_draft_id, offered_chips). `messages` holds the masked question only.
  - **Nodes.** `dispatch` reads `state.decision`, which the handler passes in (section 4.9), makes no model call and
    returns `Command(goto=...)`. The desk nodes are handbook, statute, case, clarify and oos.
    `next_part` pops a fixed list and returns `Command(goto=<next>)` or `END`. Parts run in sequence, never as
    `Command(goto=[a, b])`, which runs both in one superstep.
  - **Direct desks.** They call `documind_tools.retrieve(..., doc_type=<list>, brain="desk")`. Code numbers the
    citations across sections.
  - **Statute desk.** It appends the in-force line from `shared/desk_law.py`.
  - **Checkpointing.** Threads live in the existing Postgres checkpointer under `tenant:user:desk-<session>`, through
    `thread_config`'s rule (`services/chat/agent.py:104-112`). G10-e's install line already passes `thread_config`
    (section 4.5), which avoids a circular import, so this pull request edits no `agent.py` line. Only answer and
    clarify turns invoke the graph (section 4.9), so a gate hit or a case, denied or out_of_scope turn is never
    checkpointed.
  - **Parts.** `tenant_settings/{t}.desk_max_parts`, code default 1, set by `make desk DESK_MAX_PARTS=`.
- `commands/desk_ops.py route-index`: writes `desk_exemplars` per tenant (route, vector, row id, group,
  index_version) from the dev rows only. It is filtered to the tenant's enabled routes and read once every 5 minutes
  per instance.
- `evals/route_threshold.py` (new): sweeps `tau_oos` and the kNN share floor on the dev split, as
  `evals/cache_threshold.py:30` sweeps its candidates.
- `evals/route_eval.py --local`: an in-process `decide()` with a scripted classifier for CI. `--live-l1` runs the real
  flash-lite from the author's shell.
- `commands/tests/test_desk.py` (new), run by the chat-pins step: `.github/workflows/checks.yml` and
  `deploy/.github/workflows/documind-dryrun.yml` add `DOCUMIND_REQUIRE_LIBS=1 python -m unittest
  commands/tests/test_desk.py` to it (section 4.0).

**Acceptance on the dev split.** The index is built from the dev rows, so on the dev split the kNN vote runs
leave-one-group-out: a row's own group (its id, its golden `of`, its paraphrases and its follow-up pair) is excluded
from its neighbours. `route_eval.py` and `route_threshold.py` share one `knn_vote(row, index, exclude_group=True)`,
and a selftest asserts that no dev row can retrieve itself. Without this, every dev row would match itself at cosine
1.0 and the dev gates and the swept thresholds would mean nothing.

**Tests.** `test_desk.py` covers the research report's D11 list without Phase E:

- rules and anchors;
- a POSH disclosure sent while a draft is open;
- an anchor overridden by the case check;
- L1 and kNN disagreeing, which goes to L2;
- a timeout, which goes to the fallback;
- the clarify cap;
- sticky inherit and release;
- no re-route after a refusal;
- sequential parts, and a skipped second part;
- a leaver's denied turn with zero retrieve calls;
- POSH with 0 model calls, no checkpoint write and no text;
- a masked Aadhaar, and the next turn's clean L1 prompt;
- the Meter charged by the router;
- no transfer tools.

**Make targets.** `make desk-check` (extended), `make route-index TENANT=`, `make route-calibrate`.

**Offline proof.** `make desk-check` is green. The scripted run meets the dev gates, and the rules fire 0 times on the
424 existing questions.

**Lane proof.** From the author's shell, with no deploy, `python deploy/evals/route_eval.py --split dev --live-l1`
prints route accuracy of 95% or more and escalation recall of 100%, each with its Wilson interval. The L1 cost of a
pass^3 over about 637 dev rows is about Rs 24 (637 x 3 x Rs 0.0124). The per-call figure is the research report's
approximate count and is re-counted by the probe. L2 calls and embeddings come on top.

**Pages to rebuild.** None expected: new files, one `schemas.py` line no page quotes, and the two workflow lines.
`check_lesson.py 10.5` confirms that the `install()` and door lines 10.5 quotes are as G10-e wrote them. A change to
`shared/desk_rules.py` or `shared/desk_law.py` rebuilds 10.5, whose Level 0 widget reads them at build time.

**Effort.** L.

**Depends on.** G10-a2 (the dev rows), G10-c, G10-e (the case node and the install line), G6-a, G2-a (the `langgraph`
pin), G8-a. G10-d is soft; without it, the scalar alternative applies.

### 4.9 PR 10, G10-g: the Desk service, the live eval and shadow

**Goal.** The Desk answers on the lane. It serves `/v1/desk` for people, `/v1/route` as a roster-gated dry run for the
eval identities G10-e created, shadow mode on `/v1/chat`, and the routed Desk page.

**Files and change.**

- `services/chat/desk.py`:
  - **`POST /v1/desk`.** It creates the Meter, then runs `decide()` in the handler, before any `graph.invoke`. The
    thread's previous route and chip offer are read with `graph.get_state(config)`. A gate hit (posh, grievance,
    privacy_request) or any case, denied or out_of_scope outcome returns from the handler without invoking the graph,
    so nothing is checkpointed. Only answer and clarify routes invoke the graph, with the decision passed in state
    (the `dispatch` node, section 4.8). It writes one row. Every field of the `{"event": "desk", ...}` row is named in
    the literal, as the gap plan's row rule requires. Sensitive rows have user null and case_type "sensitive".
  - With Desk decision 36's hooks, the `desk` row literal also names `via` (default "direct") and `delegate` (default
    null), and a posh outcome's response carries the case offer: the units, each unit's Internal Committee members
    and the Local Committee contact, which is the data the Desk page's POSH card shows. G10-j can add both itself if
    the hook is not taken, because no page quotes these lines before the 10.6 page.
  - **`POST /v1/route`.** It is restricted to `desk_eval`, returns the decision only, and writes no checkpoint. It has
    a per-email rate limit, per instance. It accepts `prev_question` and `prev_route` in the body, for the follow-up
    rows, and `arm`, only from a `desk_eval` caller; `/v1/desk` accepts `arm` only from a `desk_eval` caller and never
    accepts `prev_*`.
  - **Shadow.** When `desk_route` is shadow, the chat door's `_shadow` hook (a no-op since G10-e) runs `decide()`
    inside the request, beside the brain, with its own timeout and a separate shadow Meter. It writes
    `{"event": "desk_shadow", ...}`. It is not a background task, because the chat runs throttled at min instances 0
    (`commands/lesson-12.8.sh:28-29`). The door's own lines, which 10.5 quotes, do not change.
  - **Modes.** off, shadow, on and single (`desk_single`, statute for globex), plus a per-desk off list.
  - **Arm C.** `arm: "C"` sends the turn through the gate and coverage, then the direct answer over the person's doc
    types with no classifier (the `fallback` route's path).
- `commands/desk_ops.py desk`: `DESK_ROUTE`, `DESK_SINGLE` and `DESK_MAX_PARTS`.
- `services/frontend/desk.py`: the routed half. It shows sections with citations through the existing renderer, the
  in-force line, clarify buttons, chips, the out_of_scope reply and the case offer. It shows the routed half only when
  the tenant's `desk_route` is on or single, so 10.5's Level 1 matches a lane where `desk_route` is off.
- `evals/route_eval.py --live [--arm B|C|Astar]`: sends each row to `/v1/route` for the decision metrics (the
  confusion matrix, escalation recall, router cost, p50 and p95), and each handbook, statute, calculator and denial
  row also to `/v1/desk` for `authority_rate`, `tool_calls` and the answer checks. It runs as the row's eval identity
  (section 4.5's accounts). Multi-roster accounts are refused as callers. A person has one tenant
  (`shared/tenancy.py:20-23`), while chat-sa, ui-sa and mcp-sa are on all three golden rosters
  (`commands/lane.py:145-146`). Arm A* arrives with G10-h.
- `smoke/smoke_desk.py` (new): one question per desk, POSH through `/v1/desk` (as documind-evalacme-sa) and
  `/v1/stream` (as ui-sa), an out_of_scope template, the leaver's denied turn, globex in single mode, then
  `smoke_cases`.

**Tests.** `test_desk.py` adds `/v1/route`'s role check, `prev_*` and `arm` refused from a non-eval caller, a gate hit
on `/v1/desk` with no checkpoint write, the shadow row, the single mode, and the desk row literal guard.

**Make targets.** `make smoke-desk`, `make route-eval SPLIT=dev|test [ARM=B|C|Astar]`,
`make desk TENANT= DESK_ROUTE=off|shadow|on|single [DESK_SINGLE=statute] [DESK_MAX_PARTS=1]`.

**Offline proof.** `make desk-check`, `check_authz.py`, `terraform validate`.

**Lane proof.**

1. `make plan up`, then deploy chat and ui.
2. `make roles` gives documind-evalacme-sa, documind-evalzeta-sa and documind-evalglobex-sa `ROLES=employee,desk_eval`
   on their tenants, and documind-evalleaver-sa `ROLES=leaver,desk_eval` on acme.
3. `make doc-types SEED=manifest APPLY=1` for each tenant, if the lane was reset (section 4.2).
4. `make route-index`.
5. Zeta shadow: `/v1/chat` turns write `desk_shadow` rows with a route and `router_ms`.
6. Acme on; globex single on `statute`.
7. `make smoke-desk` passes.
8. `make route-eval SPLIT=dev` prints the matrix with intervals, escalation recall, `authority_rate`, router cost and
   p50 and p95; `ARM=C` prints the same for arm C.
9. The Desk page shows:
   - NP-03's 60 days, cited;
   - a statute answer with its in-force line;
   - the POSH card;
   - the leaver's denial.

**Pages to rebuild.** None expected. `check_lesson.py 10.5` confirms that the `install()` and door lines 10.5 quotes
are as G10-e wrote them; a change to `shared/desk_rules.py` or `shared/desk_law.py` rebuilds 10.5 (its Level 0
widget). The eval accounts' invoker bindings, and 10.1's rebuild for them, moved to G10-e.

**Effort.** L.

**Depends on.** G10-f, G10-e, G10-e2, G10-b (the lane's labels), and G10-d or Desk decision 4's alternative.

### 4.10 PR 11, G10-h: agent mode and calculators

**Goal.** When a figure is asked, the desk computes it in code from numbers found in this turn's passages or in the
person's message, and cites the clause.

**Files and change.**

- `shared/desk_calc.py` (new, pure, with `--selftest`):

  | Function | Rule and source |
  |---|---|
  | `accrued_leave(months)` | 1.75 days a month (`acme/hr_policy_2026.md:19`) |
  | `carry_forward(days, cap)` | cap 30 (`:19-20`); zeta's is 18 |
  | `encashable_days(balance, cap)` | min(balance, 45) (LV-07, `:24`) |
  | `notice_end(ack_date, days)` | runs from the written acknowledgement (NP-03, `:7-8`) |
  | `gratuity_estimate(monthly_wage, years, months, fixed_term)` | monthly wage / 26 x 15 x completed years (Code on Social Security, `acme/code_on_social_security_2020.md:2234`, `:2279-2280`), always labelled "estimate" |
  | `statutory_deadline(event, date)` | two working days, Monday to Friday until a holiday calendar exists (Code on Wages s.17(2), `acme/code_on_wages_2019.md:459-464`) |
  | `threshold_check(headcount)` | 20 for a Grievance Redressal Committee (IR Code s.4(1), `acme/industrial_relations_code_2020.md:397-399`) |

  Further thresholds join only with their corpus lines.
- `services/chat/desk_graph.py`: agent-mode nodes. Each is a `create_agent` sub-graph on `gemini-3.6-flash`, thinking
  low. Its tools are a passages-backed retrieve with fixed `doc_type` and the calculators. It uses G6-a's
  `TurnLimitsMiddleware` and G8-a's tool adapter, in the gap plan's one middleware order.
- A numeric argument not found in a passage's full text or in the person's message is refused with `status: "error"`.
- Arm A* for the ship decision (section 1.3): one agent-mode node over `[policy, statute, guidance]` with every
  calculator and the real `doc_type` vocabulary in its retrieve tool's description, reachable only with `arm: "Astar"`
  from a `desk_eval` caller.

**Tests.** `desk_calc.py --selftest` pins min(50, 45) = 45, a notice end date, a gratuity example from stated inputs,
and 20. `test_desk.py` covers the argument check and refuses `arm` from a non-eval caller.

**Make targets.** None new.

**Offline proof.** `make desk-check`.

**Lane proof.** On the Desk page:

- jn-03 ("I am an E3 leaving with 50 days of earned leave...", `evals/golden.jsonl:16`) returns 45 days and 60 days,
  with the formula and the LV-07 and NP-03 citations;
- a gratuity question returns an estimate with the Code's citation;
- a number that is not in the passages is refused.

Then `make route-eval SPLIT=dev ARM=Astar` runs; the three arms are compared on the test split at M5 (section 7).

**Pages to rebuild.** None.

**Effort.** M.

**Depends on.** G10-g, G10-p (section 4.6), G6-a, G8-a. G5-b is soft (section 3.4).

### 4.11 PR 12, G10-i: operations

**Goal.** The Desk's rows reach BigQuery. A daily view per tenant and desk, and alerts on cases and on the router,
exist.

**Files and change.**

- `terraform/sink.tf:15`: the one sink's event list gains "desk", "desk_shadow", "desk_gate" and "passages". The sink
  already takes documind-api and documind-chat (`:14`).
- `terraform/sql/desk_daily.sql` (new). Per tenant, day and desk it gives:
  - turns, answered, refused, clarified, denied, not_covered;
  - escalations by non-sensitive type, plus one "sensitive" count;
  - the method mix and the L2 share;
  - the chip re-route rate;
  - `cost_inr`;
  - p50 and p95 of latency and `router_ms`.

  It is built from an aggregate with no user column. `tenant_daily.sql:51` is unchanged.
- `mk/agents.mk`: `desk-views`, with the comment "run after the desk rows have landed once, as bq-views is". BigQuery
  types a sink table's `jsonPayload` from the rows it has seen, so a view over a field no row has carried fails with
  "Field name ... does not exist" (`Makefile:450-453`). The core `bq-views` (`Makefile:454-455`) is untouched.
- `terraform/desk.tf`: log-based metrics and alert policies for:
  - a clocked case within 24 hours of due and unacknowledged;
  - a fallback share above 1%;
  - an L2 share above its cap;
  - clarify or out_of_scope up more than 5 points week on week;
  - confirmed cases above a queue's stated weekly capacity;
  - any `doc_type_pin_miss` (section 5.1).
  - any `desk_delegation_refused` row (section 4.11a), only with Desk decision 36's hooks, so that 13.2's line naming
    `desk.tf`'s policies is rebuilt once, here. The metric filters on the event name, so it can exist before G10-j
    writes the first such row.

  They stay in `desk.tf`, as `quota.tf` already holds a policy outside `alerts.tf`. Putting them in `alerts.tf` would
  change what 4.4, 13.2, 13.3, 18.3 and 18.4 read from that file, and 13.2 asserts its policy list
  (`lessons/13-operations/13.2-usage-reconcile/build.py:139`). 13.2's rebuild below adds a line naming `desk.tf`'s
  policies beside its `alerts.tf` inventory (`build.py:186-187`), so the inventory is not silently incomplete.

**Tests.** `terraform validate`, plus a SQL dry run in `desk-views`.

**Make targets.** `make desk-views`.

**Offline proof.** `terraform -chdir=deploy/terraform validate`, and the 13.2 and 16.2 rebuilds pass.

**Lane proof.**

1. `make plan up` (the widened sink). The sink copies only entries logged after the apply, so G10-g's smoke rows never
   reached BigQuery.
2. `make smoke-desk`, so desk, desk_shadow, desk_gate and passages rows reach BigQuery.
3. `make desk-views`.
4. `bq query` on `desk_daily` shows rows per desk, with the sensitive count and no user column.
5. A lab queue with an SLA of 0 days makes `make cases-overdue` fire the alert.

**Pages to rebuild.**

- 13.2: the sink excerpt and the readers table its build prints (`build.py:163-169`), and the alert inventory line for
  `desk.tf`'s policies.
- 16.2: the sink excerpt (`lessons/16-multimodal/16.2-studio-voice/build.py:93`); the assert on its event line
  (`:102`); the events cell (`:247-253`), which prints every copied event; and the prose at `parts/b.html:32` and
  `parts/c.html:29`, which becomes "the sink copies query, stream, chat, desk, desk_shadow, desk_gate and passages;
  media still never". CI runs `check_lesson` on every page (`.github/workflows/checks.yml:37`), so the stale excerpt
  would fail; the prose has nothing to catch it.

The alternative, a second sink in `desk.tf`, would leave 13.2's "which events BigQuery ever sees" silently incomplete.

**Effort.** M.

**Depends on.** G10-g. G3 is soft.

### 4.11a PR 13, G10-j: the Google Chat door

**Goal.** An employee messages the "HR Desk" app in Google Chat and gets the same Desk as on the Desk page: a cited
handbook or statute answer as a card, a clarify question with two buttons, a case offer, or the POSH template with no
model call. The bridge proves that each request came from Google, and the Desk serves the named person only because an
allow-listed delegate vouches for them, under rules the Desk enforces.

**Where the Google facts come from.** The labels W1 to W14 resolve to URLs in table W at the end of this section.
"Read" means the page was fetched on 30 September 2026 and came back as a model-written summary, not raw HTML. A fact
that no read page states is marked unconfirmed, and "from memory" when it comes from neither a page nor the kit. Step 3
of the lane proof settles most of them.

**The shape.**

- A new Cloud Run service, `documind-gchat` (new), built from `services/gchat/` (new) and running as
  `documind-gchat-sa` (new). It is not an endpoint on `documind-chat`, for four reasons:
  - Identity. Chat calls with its own agent's Google-signed ID token (W1, W3, W11), which names Google's agent, not the
    sender, and carries no IAP session. `documind-chat` runs behind IAP (`commands/lesson-12.8.sh:57`) and takes
    identity only from `caller()` (`services/chat/agent.py:150-169`), so Chat's agent would meet the roster's 403.
  - Time. Chat waits at most 30 seconds for a synchronous reply (W4, read, stated for the interaction-event model).
    `documind-chat` runs at min instances 0 (`commands/lesson-12.8.sh:29`) and gives rag-api 90 s (`:32`), so a late
    answer needs a queue and a worker. That is a surface's job, not the Desk's.
  - A new outward capability. Posting to Chat uses the `chat.bot` scope (W5, W10). That is an OAuth scope, not an IAM
    role, and from memory (unconfirmed) the Chat API recognises the app by the Google Cloud project of the calling
    account. If so, keeping the posting code out of `documind-chat` is a convention, not a boundary, and the lane
    proof measures it (step 3).
  - A small blast radius. The bridge makes no model call, opens no Postgres, reads nothing in the default Firestore
    database and may not invoke `documind-api`. The one thing it can do is ask the Desk on someone's behalf.
- Direct messages only. A question the gate catches is answered synchronously and never enters a queue. Every other
  question is acknowledged in the HTTP response at once and answered later through Pub/Sub and the Chat API.
- The app model is the Workspace add-on model (Desk decision 31). W3, the HTTP quickstart for Chat apps, sits under
  Google Workspace add-ons and names the classic interaction-event model as the alternative (W3, W4). The bridge's
  normaliser reads both event shapes, but a move to the classic model is not a configuration change. W1 requires the
  "HTTP endpoint URL" audience on Cloud Run functions (read), and the same holds for this service, because the
  "Project Number" token is self-signed (W1) and `iap.bearer_email` cannot verify it (below). The endpoint-URL token's
  caller is `chat@system.gserviceaccount.com` for every project's Chat app, so the request is no longer bound to this
  project, and `GCHAT_CALLER`, the invoker binding and `callers_in` change with it. The classic synchronous reply is
  the message itself (from memory), not the `hostAppDataAction` wrapper W3 shows. And the invoker grant to
  `chat@system.gserviceaccount.com` may be refused under the domain-restricted-sharing policy, as the billing budget
  agent's grant was (`terraform/budget.tf:59-63`); that last point is an inference.

**Files and change.** Paths are relative to `deploy/`. "(new)" marks a file or name that exists nowhere today.

- `services/gchat/main.py` (new): a FastAPI app with `POST /` (Chat events), `POST /work` (the Pub/Sub push) and
  `GET /health`.
- `services/gchat/events.py` (new, stdlib): `normalise(body)` returns one record (shape, kind, message name, space
  name and type, thread name, sender name, type and email, text, attachment flag, click action and parameters) from
  either event shape; `session_id(space_name, day)` (below).
- `services/gchat/cards.py` (new, stdlib): `render(desk_json)` returns one Cards v2 message (below).
- `services/gchat/replies.py` (new, stdlib): the bridge's own fixed replies: the welcome card, the acknowledgement,
  "not on a roster", "not switched on for your company", "message me directly", "typed questions only", "too long",
  "rate limited", "could not read your account" and "could not reach the HR Desk".
- `services/gchat/claims.py` (new): the duplicate claims (below).
- `services/gchat/post.py` (new): `spaces.messages.create` as the app (below).
- `services/gchat/requirements.txt` (new): chat's pins for `fastapi`, `uvicorn`, `gunicorn`, `pydantic`, `requests`,
  `google-auth` and `google-cloud-firestore` (`services/chat/requirements.txt:5-8`, `:13`, `:15`, `:19`), plus pinned
  `google-cloud-pubsub` and `google-apps-chat`, the client W5's Python sample uses (`google.apps.chat_v1`). Versions
  are chosen when the pull request is written and recorded in it. `validate.py` already treats the top-level `google`
  import as third party (`validate.py:58-67`). Its shared-deps rule (`:225-268`) asks nothing of the bridge, because
  the shared modules it imports (`iap`, `desk_rules`, `desk_law`) open no `google.cloud` client. Its pins rule
  (`:290-320`) requires every pin the bridge shares with another service to match it, which copying chat's seven pins
  satisfies; no service pins `google-cloud-pubsub` or `google-apps-chat` today.
- `services/gchat/Dockerfile` (new): copies `shared/` and `services/gchat/` from the `deploy/` context, as
  `services/chat/Dockerfile:5-11` does. `make build` already maps a service name to `services/<name>/Dockerfile`
  (`Makefile:300-312`).
- `services/chat/delegation.py` (new, importing nothing from `desk.py` or `agent.py`): `DELEGATES`, `DELEGABLE` and
  `principal(request, caller, tenant_for, settings)`, to which `desk.py` passes the `tenant_for` that `install()`
  received and its own settings reader (below).
- `services/chat/desk.py`: `_principal`'s body becomes a call to `delegation.principal`; two new text-free delegable
  routes, `GET /v1/desk/check` (runs `principal()` and returns the tenant, or the 403 reason) and
  `GET /v1/cases/offer?type=posh` (the units, each unit's Internal Committee members and the Local Committee
  contact); the `desk_delegation_refused` and `desk_delegation_denied` rows (below); `via` and `delegate` on the `desk`
  row and `via` on case records, unless Desk decision 36's hooks already put them there. No line 10.5 quotes changes
  when the hooks landed in G10-e.
- `terraform/gchat.tf` (new): the two accounts, the claims database, the topic, the push subscription, the API and the
  grants (below).
- `commands/gchat.sh` (new): the deploy block (below).
- `commands/lesson-12.8.sh:39`: the invoker loop gains `documind-gchat-sa`, unless G10-e's hook named it.
- `terraform/sa.tf`:
  - `:102-106`, the caller graph. The documind-chat line gains `documind-gchat-sa` (unless G10-e's hook added it),
    and a new line reads:

    ```
    #   documind-gchat  <- service-NUMBER@gcp-sa-gsuiteaddons, documind-gchatpush-sa, documind-outsider-sa  (gchat.sh)
    ```

  - `:99` says "the six lines below and the six scripts". The comment at `:114-117` gains one sentence: the outsider
    is also bound on `documind-gchat`, whose code refuses every caller except Chat's agent and the push account.
  - `:55-65` stays byte-identical, so 8.2's quoted outsider block
    (`lessons/08-security/8.2-access-tests/build.py:59-60`) does not move.
- `Makefile:29`, `Makefile:593` and `deploy/README.md:228` name `documind-gchat` as the eighth Cloud Run service,
  deployed only on request. The `Makefile:29` sentence grows by fewer than 90 characters, so 18.3's 400-character
  window after "ONE SHAPE" (`lessons/18-serving/18.3-vllm-gke/build.py:153`, where "the GKE lab cluster," sits at
  character 304 today) still holds, and `check_lesson.py 18.3` confirms it.
- `tools/check_authz.py`:
  - `SCRIPTS` (`:41`) gains `gchat.sh`. The docstring (`:11`, `:13-17`) and the messages at `:132` and `:146` say six
    services and six scripts, and the docstring gains the sentence on the outsider's binding on `documind-gchat`;
  - `callers_in` (`:73-78`) recognises `gcp-sa-gsuiteaddons`, as it recognises `gcp-sa-iap`;
  - the graph regex (`:84`) accepts `gchat.sh` beside `lesson-N.M.sh`;
  - the expected service set (`:131`) gains `documind-gchat`;
  - the code edges (`:149-167`) gain one: `services/gchat/` reads `CHAT_URL` and no other service URL, and
    `documind-gchat-sa` is on documind-chat's graph line. The push account's binding on documind-gchat is backed by
    the push subscription's `oidc_token` in `terraform/gchat.tf`;
  - the Makefile needles (`:168-173`) gain `("smoke-gchat", "DOCUMIND_OUTSIDER_SA=documind-outsider-sa")`, the graph's
    reason for the outsider's binding on documind-gchat;
  - the outsider's set (`:177-178`) gains `documind-gchat`, whose verifier is `iap.bearer_email(` compared with a fixed
    caller, not `iap.identity(` and a roster (`:180-183`);
  - the delegate checks (Desk decision 38). G10-e adds the minting half with Desk decision 36's hook; G10-j adds the
    rest, or all of it without the hook. No line in the Makefile, `mk/*.mk`, `commands/*.sh`, `commands/*.py` or
    `terraform/*.tf` mints as `documind-gchat-sa`, or grants `roles/iam.serviceAccountTokenCreator` or
    `roles/iam.serviceAccountUser` on it to anyone but the account itself (the self-impersonation fallback, if the
    probe needs it). `cicd_actas` (`terraform/sa.tf:245-259`) does not name it. On `documind-gchatpush-sa`, only
    Pub/Sub's service agent holds `roles/iam.serviceAccountTokenCreator`, and nobody holds
    `roles/iam.serviceAccountUser`. The only `roles/pubsub.publisher` binding on `documind-gchat-work` is
    `documind-gchat-sa`'s. No `terraform/*.tf` file grants `roles/pubsub.publisher`, `roles/pubsub.editor` or
    `roles/pubsub.admin` at project scope, which holds today: the kit's three publisher grants are each on one topic
    (`terraform/eventarc.tf:19`, `:48`, `terraform/budget.tf:80`).
- `commands/desk_ops.py desk`: `DESK_GCHAT=on|off`, a merge write to `tenant_settings/{t}`. It refuses `on` unless
  `desk_gate` is on and `desk_route` is on or single. For a tenant whose `data_region` is "in"
  (`shared/tenancy.py:25-33`; globex, `commands/lane.py:148`) it also asks for `CONFIRM_RESIDENCY=1`, because the
  answers and their quotes will then sit in the tenant's Google Chat under its Workspace settings.
- `mk/agents.mk`, the `.PHONY` list at `Makefile:188` and `mk/README.md`: `deploy-gchat` and `smoke-gchat`.
- `Makefile:598`: `DOWN_SERVICES` gains `documind-gchat`. No page asserts that line; 18.1 asserts only
  `DOWN_SERVICES_M11` (`lessons/18-serving/18.1-gateway-routes/build.py:150`).
- `smoke/smoke_gchat.py` (new) and `commands/tests/test_gchat.py` (new), below.
- `.github/workflows/checks.yml` and `deploy/.github/workflows/documind-dryrun.yml`: the chat-pins step also runs
  `DOCUMIND_REQUIRE_LIBS=1 python -m unittest commands/tests/test_gchat.py` (section 4.0).
- `deploy/UNOWNED.md`: every new file above, under the Desk heading, until the 10.6 Google Chat content pull request
  adopts them (section 4.13).

**The delegation design (Desk decision 32).** The chat service takes identity from one place, `caller()`
(`services/chat/agent.py:150-169`): the person's IAP assertion, or the caller's own Google ID token for `SELF_URL`
(`shared/iap.py:148-167`, `:170-185`). Neither can name an employee who messaged a Chat app, and the bridge cannot
obtain either for that person: a service account cannot mint an IAP assertion or a Google ID token in someone else's
name, and Chat's own token names Google's agent (W1, W11). So the Desk trusts one named delegate, under rules that live
in the Desk, not in the bridge.

- `services/chat/delegation.py` holds `principal(request, caller, tenant_for, settings)`. Without the header
  `X-DocuMind-Principal` (the name the research report gives rag-api's header, its section 9, item 5), it returns
  `caller(request)` unchanged with `via` "direct", so the Desk page, the eval accounts and every other caller are
  served exactly as before.
- With the header, it calls `caller(request)` first, so an unverified request is still a 401. It then refuses with 403
  and a fixed reason unless every rule holds. The rules are checked in the order listed, so a caller that is not the
  delegate is refused by rule 1 and learns nothing about the roster or the flag.
  1. The verified caller's email is in `DELEGATES`, a code constant:
     `{"documind-gchat-sa@<GOOGLE_CLOUD_PROJECT>.iam.gserviceaccount.com": "gchat"}`. The project comes from
     `GOOGLE_CLOUD_PROJECT`, which the chat deploy already sets (`commands/lesson-12.8.sh:32`), not from
     `CHAT_EXTRA_ENV`, which `deploy-services` empties (`Makefile:353`). A person's IAP assertion names the person, so
     no person passes this rule, whichever leg `caller()` used. The kit's comment expects service-account callers on
     the bearer leg (`commands/lesson-12.8.sh:54-56`); the rule does not depend on it.
  2. The route is in `DELEGABLE`: `POST /v1/desk`, `GET /v1/desk/check`, `POST /v1/cases`,
     `POST /v1/cases/{id}/confirm`, `POST /v1/cases/{id}/cancel` and `GET /v1/cases/offer`. `/v1/route`, the inbox
     (`GET /v1/cases`) and `POST /v1/cases/{id}/status` are never delegable. `/v1/chat` never reads the header,
     because its door and handler call `caller()` directly.
  3. The named principal is lower case, matches a conservative address pattern with no `:` (which `thread_config`
     bans, `services/chat/agent.py:104-112`), and does not end in `.gserviceaccount.com`. That refuses
     `documind-chat-sa`, which is on every golden roster (`commands/lane.py:145-146`), and the eval accounts that hold
     `desk_eval`.
  4. `tenant_for(principal)` finds a tenant (`shared/tenancy.py:55-68`).
  5. That tenant's `desk_gchat` is `on`, read through `settings`, the Desk's 60-second cache (section 1.1). A failed
     read counts as off.
  6. The body carries no `arm` and no `prev_*`, whatever the principal's roles.
  7. The profile is not `local`: there is no bridge on a laptop.
- On success it returns `{"email": principal, "assertion": None, "via": "gchat", "delegate": "gchat"}`. From there,
  roles, coverage and the gate treat the principal like any person (`roles_for`, section 5.3). A leaver is still denied
  the answer desks.
- rag-api never sees the header. `retrieve()` sends the service's own ID token and, only when there is one, a
  forwarded assertion (`shared/documind_tools.py:133-140`), and a delegated principal carries none. So a delegated turn
  reaches rag-api as `documind-chat-sa`, as `make smoke-chat` does, and needs `documind-chat-sa` on the tenant's
  roster. `make roster` puts it on the three golden tenants (`commands/lane.py:145-146`); a pilot tenant needs
  `make roster TENANT=<t> MEMBERS=documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com`. rag-api's usage row
  then names `documind-chat-sa`, and the Desk's `desk` row names the person. rag-api's own header stays unbuilt.
- The bridge's account is on no roster, so a bridge call without the header is refused by the roster, the way the
  outsider is (`terraform/sa.tf:55-65`).
- Only the bridge may publish work. `documind-gchat-sa` holds `roles/pubsub.publisher` on `documind-gchat-work`, and
  nobody else holds a publisher, editor or admin role on the topic or at project scope. The worker sends the Desk the
  email and the masked question, and no tenant; the Desk derives the tenant from the roster. This departs from the
  research report's rule that the principal is never taken from a body or state field (its section 9, item 5). On the
  asynchronous path the principal is a field of a message that only the bridge can publish, and Desk decision 38 names
  topic publishers beside token minters.
- Nobody may mint as the bridge. Whoever can mint a token as `documind-gchat-sa`, act as it, or publish to
  `documind-gchat-work` can speak for every rostered person of every tenant with `desk_gchat` on. So no person gets
  `roles/iam.serviceAccountTokenCreator` or `roles/iam.serviceAccountUser` on it, unlike ui-sa and the outsider
  (`Makefile:384-391`). No Google agent does either: Pub/Sub mints the push token as a separate account,
  `documind-gchatpush-sa`, which is not a delegate (below). The account is not in `cicd_actas`
  (`terraform/sa.tf:245-259`), and `check_authz.py` asserts all of this. The account's own self-grant is the one
  exception, taken only if the probe needs self-impersonation to post (Desk decision 35).
- Audit (Desk decision 38). The `desk` row carries `via` and `delegate`, and the sensitive rule still applies: user
  null and `case_type` "sensitive". A case record carries `via`. A refusal under rule 1, 2, 3, 6 or 7 refuses the
  caller. It writes `{"event": "desk_delegation_refused", "caller", "reason", "path"}` with no principal, and a
  log-based alert fires on every such row. The smoke's two refusals fire it, which is the alert's own test. A refusal
  under rule 4 or 5 is an ordinary answer about a person: not on a roster, or the door is off for the tenant. It
  writes `{"event": "desk_delegation_denied", "reason", "path"}` with no principal and no alert, because a colleague
  who is not on a roster messaging the app is not an attack. No audit-bucket action is added, so 8.3's list of
  literal emitters (`lessons/08-security/8.3-dlp-guard-audit/build.py:91-93`) holds.

**Token verification.**

- Cloud Run IAM first. `documind-gchat` is `--no-allow-unauthenticated`, and three principals may invoke it: Google's
  add-on agent for the Chat app, `documind-gchatpush-sa` (the push) and `documind-outsider-sa` (the smoke). W3 grants
  Cloud Run Invoker to the "Service Account Email" the Chat API configuration page shows (read). W1 says that on Cloud
  Run functions, Cloud IAM handles the token check (read, for the classic model).
- Then the code, on every request. `iap.bearer_email(request.headers, SELF_URL)` (`shared/iap.py:148-167`) verifies
  Google's signature and the audience, and the email must equal `GCHAT_CALLER` on `/` and `documind-gchatpush-sa` on
  `/work`. Anything else is a 401, which is what W1 asks for when verification fails (read). W11 describes the same
  check for HTTP add-ons: the audience is the endpoint URL, and the email is the add-on's service account,
  `service-PROJECT_NUMBER@gcp-sa-gsuiteaddons.iam.gserviceaccount.com` (read; W11 covers add-ons in general, and W13, a
  third party, reports that address for Chat).
- The kit already re-verifies in code the token Cloud Run's IAM admitted (`shared/iap.py:139-145`). `documind-api`
  has the bridge's shape, IAM with no IAP in front (`shared/iap.py:41-44`), and `make smoke` and `make eval-live`
  prove on every lane that the `Authorization` header reaches its container intact for that second check
  (`services/rag-api/auth.py:44-45`).
- `SELF_URL` is the deterministic `https://documind-gchat-NUMBER.REGION.run.app`, the only audience a kit service
  verifies (`tools/tests/test_run_app_urls.py:1-4`). The app's HTTP endpoint URL is configured to exactly that
  string, with no trailing slash, because the token's audience is the configured URL exactly (W1's example audience
  keeps its trailing slash).
- A token the code refuses writes a `gchat_verify_failed` row (below). A token Cloud Run's IAM refuses never reaches
  the code, and shows only in Cloud Run's request log.
- The code calls `bearer_email`, not `iap.identity(`, so 8.1's list of the three files that call `iap.identity(`
  (`lessons/08-security/8.1-identity-tenancy/build.py:108-111`) holds.
- Binding the request to this project. A classic token with the endpoint-URL audience names the URL, not the project,
  so another project's Chat app pointed at our URL would also present a valid token (inference from W1). The add-on
  caller's address carries this project's number, so comparing the email binds the request to this project's app
  (inference from W11). The classic model's "Project Number" audience binds too (W1), but it is not an option here.
  Its token is a JWT self-signed by `chat@system.gserviceaccount.com` with the project number as its audience (W1), and
  `bearer_email` verifies against Google's OAuth certificates with `audience=SELF_URL` (`shared/iap.py:160-161`), so
  it refuses that token; that Cloud Run's invoker check refuses it too is an inference. The roster refusal limits the
  damage in any case, because the sender identity still comes from Google.

**The synchronous handler, `POST /`, and the acknowledgement.** Its own budget is 5 s, well inside Chat's 30 s (W4).
In order:

1. Verify the token, as above.
2. Normalise the event. The add-on shape carries a `chat` key with `messagePayload.message` and its `sender` (W3,
   read); the classic shape carries `type`, `message`, `user`, `space` and `common` (W7, read). An "Added to space"
   event gets the welcome card. Anything that is not a person's message or a button press gets no reply.
3. The gate, before every other check: `desk_rules.gate(text)` (`shared/desk_rules.py`, section 4.3) runs on any text
   the event carries, whatever its space, attachment, length or rate. A hit is answered synchronously every time and
   is never claimed or queued: a repeated template is harmless, and a missed one is a legal failure (Desk decision 1).
   - The usual path is a synchronous delegated `POST /v1/desk` for the sender (read as in step 4), with a 15 s budget,
     and the Desk's template card as the HTTP response. The question never enters Pub/Sub. The bridge's row for posh,
     grievance and privacy_request has user null and class "sensitive".
   - If the Desk does not answer within 15 s (a cold start), or the question is over the 4,000-character cap
     (`services/chat/agent.py:145`), the bridge replies with the same fixed text from `shared/desk_law.py` and a "Show
     my options" button. For posh it calls `GET /v1/cases/offer?type=posh`; for grievance and privacy_request it
     drafts the case through `POST /v1/cases`. The button's parameters carry no text.
   - With no sender email, or in a named space, the hit gets only the fixed text, with no buttons. In a space it adds
     "message me directly", so nobody else there can press anything.
4. The sender. The type must be `HUMAN` (the User resource's enum, W8, read) and an email must be present, lower-cased.
   The User resource has an `email` field, "Output only" (W8, read), but no read page confirms that interaction events
   fill it (W4, W7, W9), and a third party reports that membership events omit it (W14). If it is absent, the bridge
   uses the user's Google-signed ID token when the probe found one (Desk decision 32, design A+), and otherwise replies
   "could not read your account" and logs `gchat_no_email` (Desk decision 33).
5. Direct messages only. In the configuration, "Join spaces and group conversations" is left unchecked (W2). If an
   event still arrives from a named space, the bridge replies "message me directly" and does nothing else. The name
   of the space-type field is unconfirmed; the probe records it. An attachment gets "typed questions only". A question
   over 4,000 characters gets "too long", the same cap as `ChatRequest.question` (`services/chat/agent.py:145`).
6. Claim the event (duplicates, below).
7. A per-sender rate limit in each instance, 6 questions a minute to start, answers "rate limited".
8. A delegated `GET /v1/desk/check` with a 5 s budget. A 403 becomes the matching fixed reply ("not on a roster", "not
   switched on for your company"). A timeout lets the question go on, and the worker shows any refusal.
9. Mask the question with `desk_rules.mask()`, publish `{key, email, session_id, space, thread, masked question}` to
   `documind-gchat-work`, mark the claim `queued`, and return the acknowledgement as the HTTP response. In the add-on
   shape it is wrapped as `{"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": ...}}}}` (W3,
   read). The acknowledgement costs no Chat API write.

**The worker, `POST /work`, and the answer.** Pub/Sub pushes each message with an OIDC token issued as
`documind-gchatpush-sa` (new, 21 characters, matching `documind-[a-z]+-sa`, `tools/check_authz.py:75`). That account
has no project roles and no use except the push. It is not in `DELEGATES`, so a token Pub/Sub mints can reach `/work`
and nothing else.

1. Verify: `bearer_email` must equal `documind-gchatpush-sa`. `/` refuses that account, and `/work` refuses Chat's
   agent and the bridge's own account. The push envelope's `subscription` must name `documind-gchat-push`, so a push
   from another subscription that names the same account is refused (the envelope's shape is from memory).
2. Lease the claim and add one to `attempts`. An `answered` claim is acknowledged and nothing else happens.
3. A delegated `POST /v1/desk` with the message's email, masked question and `session_id`, and a 240 s timeout, under
   `documind-chat`'s 300 s (`commands/lesson-12.8.sh:28`).
4. Render the card and post it with `spaces.messages.create`: `parent` is the space, `messageId` is
   `"client-" + sha256(message name)[:56]`, and the reply goes to the event's `thread.name` with
   `messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD` (W5, read). The id is 63 characters in all, `client-`
   followed by 56 lower-case hex digits, which W5 allows ("up to 63 characters and only lowercase letters, numbers,
   and hyphens", "unique within a space"). A second create with the same id is treated as already posted; the exact
   error it returns is unconfirmed.
5. Mark the claim `answered` and acknowledge.
6. On an error, release the claim and return a 5xx, so Pub/Sub retries.
7. On the fifth attempt, counted in the claim, post the "could not reach the HR Desk" card and acknowledge. There is no
   dead-letter topic holding question text.

Quotas: 1 `spaces.messages.create` a second per space and 3,000 message writes a minute per project; above them the
API returns `429: Too many requests`, retried with exponential backoff (W6, read). The bridge makes one write per
question, and a 429 becomes a 5xx and a Pub/Sub retry.

**Posting as the app, without a key.** App authentication uses the `chat.bot` scope, needs no administrator approval,
and requires the app to be a member of the space (W5, W10, read), which it is in a direct message. W10's guide
downloads a service-account key, which the kit never uses (`terraform/org_policy.tf:1-9` enforces
`iam.disableServiceAccountKeyCreation` when switched on). The keyless order is Application Default Credentials with
the `chat.bot` scope first, then self-impersonation, which needs a `roles/iam.serviceAccountTokenCreator` self-grant on
the pattern of `terraform/sa.tf:72-81`, added only if the probe needs it (the one exception to the no-minting rule,
Desk decision 38). Both are unconfirmed. So is whether an add-on-model app posts through `spaces.messages.create` at
all: W5 and W10 do not name a model, and Google's add-on page on sending messages was a search result only (table W).
Whether the posting account must live in the Chat app's project is also unconfirmed (W10 is silent); here it does. If
no path works, the bridge runs sync-only: `GCHAT_ASYNC = False` (new, a code constant) calls the Desk synchronously
with a 25 s budget and replies in the HTTP response, which needs no Chat API credential, and a cold Desk gets "could
not reach the HR Desk".

The converse is the security question. Suppose any service account in the lane project can take a `chat.bot` token
and post as the app (unconfirmed). Then whoever can mint as `documind-ui-sa` or `documind-outsider-sa` (every
`ADMIN_EMAILS` address, `Makefile:384-391`), and any compromised runtime account, can post a card as "HR Desk" into
every employee's direct message with the app. The author tests this once from a shell with a read-only call. It mints
an access token as `documind-outsider-sa` with the `chat.bot` scope, in the shape W14 shows for another scope
(`gcloud auth print-access-token --impersonate-service-account=... --scopes=...`), calls
`GET https://chat.googleapis.com/v1/spaces`, and records `outsider_lists_spaces` as true or false.

Nothing in the Chat door uses domain-wide delegation. Posting uses app authentication with the `chat.bot` scope, which
needs no administrator approval (W10, read). Desk decision 33's lookup, if it is ever needed, uses a Workspace admin
role assigned to the bridge's account, which W14 presents as the alternative to domain-wide delegation. That lookup
also needs a Workspace administrator to assign the role, and the Admin SDK API enabled with the
`admin.directory.user.readonly` scope (W14).

**Duplicates.**

- The claim is `gchat_events/{sha256(message name)}` (new) in the bridge's own Firestore database, written in a
  transaction, as `services/ingest/idempotency.py:17-51` claims a document. It holds `{kind, state, attempts,
  created_at, expire_at}`, with no text and no email. A gate hit is never claimed (step 3 above).
- A `queued` or `answered` claim repeats the acknowledgement and does nothing else. A `received` claim older than 60 s
  is taken back, as a failed ingest claim may be (`services/ingest/idempotency.py:36-41`, `:66-76`).
- Chat "might retry delivery a few times within a few minutes (but this isn't guaranteed)" (W4, read). A 24-hour TTL
  on `expire_at` covers that, on the pattern of `terraform/firestore_indexes.tf:165-173`.
- A button press is claimed in the same collection, under a key built from the card's message name and the action,
  and a case create or confirm carries a client idempotency token built the same way, so a retried or doubled press
  opens one case.
- Whatever else fails, the `client-` message id keeps one posted answer per question. If a crash falls between the
  Desk call and `answered`, the Desk turn can run twice, but the post happens once.

**Session mapping.** `thread_config` bans empty parts and `:` (`services/chat/agent.py:104-112`), the request's
`session_id` must match `^[A-Za-z0-9_-]{1,64}$` (`:146`), and the Desk prefixes `desk-` (section 4.8). The bridge's
rule is a pure function with no stored table:

```
session_id = "gc-" + sha256(space name)[:24] + "-" + YYYYMMDD (IST)      # 36 characters
thread id  = tenant:email:desk-gc-<24 hex>-<date>
```

- A space name such as `spaces/AAAA` holds a `/`, which the pattern refuses. The hash also keeps the Chat space id out
  of the Postgres keys.
- A day, not a Chat thread: threading inside a direct message with an app is unconfirmed, the Desk's sticky follow-up
  works within 30 minutes (section 4.8), and desk threads stay short, which G7 relies on (section 3.4).
- Two people never share a thread, because the thread id carries the email (`services/chat/agent.py:112`).
- A button carries its `session_id` and chip id in its parameters. The Desk accepts a chip only when it matches the
  thread's last offer (section 4.0, Desk decision 17), so a stale or altered press cannot choose a desk.

**Cards.** `render(desk_json)` returns one message in the Cards v2 shape W5 shows (read): `cardsV2[].card` with a
`header` and `sections[]` of `textParagraph`, `decoratedText` and `buttonList` widgets, a button opening a link through
`onClick.openLink.url`. Whether a `cardId` is required is unconfirmed; W5's excerpt did not show one.

| Desk outcome | Card |
|---|---|
| handbook answer | Header "HR Desk", subtitle "From your company handbook". The answer, then a "Sources" section with one `decoratedText` per citation (document name, clause and page, then the quote). The Desk's chips, then "Raise a case" |
| statute answer | Subtitle "What the law says". The answer, the in-force line whole in its own paragraph, then the sources |
| clarify | The one question and two buttons carrying the Desk's chip ids |
| out_of_scope, not_covered, grounded refusal | The Desk's fixed text naming the right channel, then "Raise a case" |
| denied (leaver) | The fixed denial, then "Raise a case" only |
| case draft (grievance, privacy request, exit dues, people query, human requested) | Header "Handed to a person". The queue, the clock text and the basis as the Desk sends them, the draft summary, then Confirm and Cancel. Editing stays on the Desk page |
| posh | The fixed template; the offices; the Internal Committee members of the chosen office; the Local Committee contact as plain text; a "Create a confidential record" button; and the line "What you type about a harassment complaint is not stored by DocuMind. This chat stays in your company's Google Chat under its retention settings." |
| fallback | The direct answer and the desk chips, as the Desk sends them |

- The message stays under W5's limit ("The maximum message size (including any text or cards) is 32,000 bytes"): the
  answer is capped at 3,000 characters, at most five citations are shown, each quote is capped at 300 characters, the
  in-force line is never cut, and a test asserts the serialised message stays under 30,000 bytes.
- The card never echoes the question, never shows a `gs://` URI or a signed URL (Chat keeps history, and a signed URL
  there is a bearer link), and never writes legal text of its own: every template comes from the Desk, whose one
  source is `shared/desk_law.py` (section 4.3).
- Selection inputs in a message card (a dropdown of offices, checkboxes of members) are unconfirmed. If they are not
  accepted, the POSH card offers one button per office, which records the case for all of that office's Internal
  Committee members, and a link to the Desk page for choosing individual members.
- A press's form values come back in the classic event's `common` field ("Client information and form inputs", W7,
  read). In the add-on model they come back in `commonEventObject` (W12, read); the exact path is unconfirmed, and the
  probe records it. In the add-on model a button's `onClick.action.function` names the HTTPS endpoint Chat calls (from
  memory, unconfirmed). So `render()` sets it to exactly `SELF_URL` and puts the action in `parameters`, because
  `bearer_email` accepts no other audience. Whether the add-on model can update a card in place is unconfirmed; the
  fallback answers every press with a new message through `createMessageAction` (W3, read).

**Rows the bridge writes.** None carries question text. They stay in Cloud Logging; the sink is not widened, so 13.2
and 16.2 are not rebuilt.

- `{"event": "gchat", "kind", "outcome", "tenant", "user", "class", "queued", "latency_ms"}`, one per event. `user` is
  null and `class` "sensitive" for posh, grievance and privacy_request, as for the `desk` row.
- `{"event": "gchat_answer", "attempts", "outcome", "desk_ms", "post_ms"}`, one per posted answer.
- `{"event": "gchat_verify_failed", "path", "reason", "aud_is_self_url", "aud_has_trailing_slash",
  "email_is_gchat_caller", "email_is_chat_system", "iss_is_google"}` on each token the code refuses. The fields are
  booleans taken from the token's unverified claims, so a wrong app model or a trailing slash shows in the first
  minute of the probe. The token itself is never logged.
- `{"event": "gchat_probe", ...}` on the first event, the first button press and the first post of each instance:
  booleans and enums only (the lane proof, step 3).

**Terraform and IAM, `terraform/gchat.tf` (new).**

- `google_service_account` "gchat", `documind-gchat-sa`, unless Desk decision 36's hook created it in `desk.tf`. Its
  project roles are `roles/logging.logWriter`, and `roles/cloudtrace.agent` once the bridge carries G3's spans
  (section 3.4). It has no `roles/datastore.viewer`: the bridge never reads the default database, because the Desk
  checks the roster and the flag for it (`GET /v1/desk/check`).
- `google_service_account` "gchatpush", `documind-gchatpush-sa` (new), with no project roles.
- `google_firestore_database` "gchat", named `documind-gchat`, at `var.india_region`, on the pattern of
  `terraform/firestore.tf:1-9`, with delete protection off because it holds only 24-hour claims, and
  `deletion_policy = "DELETE"`, so `make down` removes it (the field and its ABANDON default are from memory;
  `terraform validate` and a `make down` followed by `make up` on the lane check them). A `google_firestore_field` TTL
  on `gchat_events.expire_at` follows `terraform/firestore_indexes.tf:165-173`.
- `roles/datastore.user` for `documind-gchat-sa` with an IAM condition on that database's resource name. That such a
  condition validates for a Firestore database is from memory and unconfirmed; `terraform plan` and the lane proof
  check it. The fallback is Desk decision 37's, never project-wide `roles/datastore.user`.
- `google_project_service` "chat.googleapis.com" with `disable_on_destroy = false`, on the pattern of
  `terraform/dataplex.tf:20-23`. Whether the add-on model needs a further API enabled is unconfirmed.
- Pub/Sub, on the ingest pattern (`terraform/eventarc.tf:31-82`):
  - the topic `documind-gchat-work` (new), its message storage pinned to `var.india_region` (the field name is from
    memory; `terraform validate` checks it);
  - the push subscription `documind-gchat-push` (new) to `https://documind-gchat-NUMBER.REGION.run.app/work`, built as
    `local.ingest_url` is (`terraform/eventarc.tf:31-35`), with `oidc_token` as `documind-gchatpush-sa` and its
    audience set to the service's deterministic URL, so `/` and `/work` verify one audience (the `audience` field is
    from memory; `terraform validate` checks it);
  - an ack deadline of 300 s, a retry policy from 10 s to 60 s, one hour of message retention (the minimum allowed is
    from memory), and no dead-letter topic;
  - `roles/pubsub.publisher` for `documind-gchat-sa` on the topic only;
  - `roles/iam.serviceAccountTokenCreator` on `documind-gchatpush-sa`, and on no other account, for Pub/Sub's service
    agent, so it can mint the push token (the pattern of `terraform/eventarc.tf:37-44`).
- The log-based metric and alert policy on `desk_delegation_refused` live in `terraform/desk.tf` with G10-i's, when
  Desk decision 36's hook put them there; otherwise G10-j adds them there and 13.2's line naming `desk.tf`'s policies
  is rebuilt (section 4.11).

Nothing here bills while idle except what the claims database stores, and the claims expire within a day. So, unlike
`desk_job`, it needs no Terraform flag.

**`commands/gchat.sh` (new).** Its `# ---- DEPLOY ----` block is run by `deploy-services` (`Makefile:372`), which
already passes `PROJECT_NUMBER` and `CHAT_URL` to every script (`Makefile:354`, `:359`, `:363`):

- `gcloud run deploy documind-gchat` from `${REGION:-us-central1}-docker.pkg.dev/$PROJECT/documind/gchat:$GIT_SHA`,
  as `commands/lesson-12.8.sh:25` names chat's image;
- `--no-allow-unauthenticated --ingress=all`, with no IAP. Every caller is a Google service agent or a service
  account, no person signs in here, and the code checks each caller by name. Whether Chat's agent could pass IAP was
  not checked;
- `--timeout=300 --min-instances=0 --max-instances=3`, and
  `--service-account=documind-gchat-sa@$PROJECT.iam.gserviceaccount.com`;
- the environment `GOOGLE_CLOUD_PROJECT=$PROJECT`,
  `SELF_URL=https://documind-gchat-$PROJECT_NUMBER.${REGION:-us-central1}.run.app`, `CHAT_URL=$CHAT_URL` and
  `GCHAT_CALLER=service-$PROJECT_NUMBER@gcp-sa-gsuiteaddons.iam.gserviceaccount.com`;
- the invoker bindings: a `for who in documind-gchatpush-sa documind-outsider-sa; do` loop, and the add-on agent's
  binding in the shape of 12.4's IAP-agent binding (`commands/lesson-12.4.sh:36-39`). The classic model would change
  this member (Desk decision 31). Whether the add-on agent exists before the app is configured is unconfirmed, so its
  binding ends in `|| echo` with a message to configure the app and run `make deploy-gchat` again.

**Tests.**

- `commands/tests/test_gchat.py` (new) has a stdlib half, run by the shared step, and a library half, run by G8-a's
  chat-pins step and by `make desk-check`.
- The bridge imports its cloud clients inside the functions that use them, as `shared/iap.py:85-86` imports
  google-auth, so every bridge module imports under the chat pins. No test needs `google-cloud-pubsub` or
  `google-apps-chat`.
- The stdlib half:
  - both event shapes, from placeholder fixtures. After the probe they are rewritten from the recorded shapes, with
    every email as `employee@example.com`, every `users/` and `spaces/` id and message name as a fixed placeholder,
    and the project number as `NUMBER`. A test fails on any email domain other than `example.com` and on any run of
    ten or more digits in the fixtures;
  - the `session_id` rule: the pattern holds, no `:`, 36 characters;
  - `render()` for every Desk outcome: under 30,000 bytes, the question never echoed, no `gs://` and no signed URL,
    and every button's `action.function` exactly `SELF_URL`;
  - the claim keys and the `client-` id (63 characters in all: the `client-` prefix and 56 lower-case hex digits);
  - the fifth-attempt card.
- The library half drives the handlers through FastAPI's test client, with the token check, the publisher, the claims
  store and the Desk client replaced by fakes:
  - a POSH disclosure from the dev rows is answered with nothing published, and so is one sent with an attachment,
    from a named space, over 4,000 characters or past the rate limit;
  - direct messages only, attachments refused, the 4,000-character cap;
  - `/work` refuses a push envelope that names another subscription.
- The library half also covers `delegation.principal`:
  - the delegate with the header is accepted, with `via` "gchat" and no assertion;
  - an evaluation account whose header names a rostered person is refused by rule 1, not rule 4, and so is ui-sa;
  - a person arriving through IAP with the header is refused;
  - a service-account principal is refused;
  - the flag off, and a failed settings read, are refused;
  - rules 4 and 5 write `desk_delegation_denied`, never `desk_delegation_refused`;
  - a route outside `DELEGABLE` is refused;
  - `arm` and `prev_*` are refused;
  - the delegate without the header is refused by the roster;
  - the local profile refuses the header.
- `smoke/smoke_gchat.py` (new). Its questions join the gate's zero-fire scan automatically, because
  `test_desk_rules.py` scans `deploy/smoke/*.py` (section 4.3). It checks four refusals:
  1. `POST /` on the bridge as `documind-outsider-sa`, with a Chat-shaped body, is a 401 from the code, not the
     network (the outsider is an invoker).
  2. `POST /work` as the outsider is a 401.
  3. `POST /v1/desk` on documind-chat as `documind-evalacme-sa`, with the header naming a rostered person, is a 403
     "not an allowed delegate".
  4. The same call as ui-sa is the same 403.

  It then prints the latest `gchat`, `gchat_answer`, `desk` (with `via` "gchat"), `desk_delegation_refused` and
  `desk_delegation_denied` rows. By design no script can mint as the bridge, so the accepted path is proven by a
  person in Chat (lane proof, step 4).

**Make targets.** `make deploy-gchat PROJECT=documind-ai-YOUR-ID REGION="$REGION" ADMIN_EMAILS="$ME"`, a one-line
recipe, `$(MAKE) build deploy-services SERVICES=gchat SCRIPTS=commands/gchat.sh`; `make smoke-gchat
PROJECT=documind-ai-YOUR-ID`, not added to `smoke-all` (`Makefile:816-823`), because a default lane has no bridge;
`make desk TENANT=acme DESK_GCHAT=on|off [CONFIRM_RESIDENCY=1]`.

**Offline proof.**

- `python -m unittest deploy/commands/tests/test_gchat.py` passes in the shared interpreter, where its library half
  skips, and `make desk-check` passes with its library half.
- `python tools/check_authz.py` passes with six services in the caller graph and the delegate checks.
- `python deploy/validate.py` and `terraform -chdir=deploy/terraform validate` pass.
- `python tools/check_one_retrieval.py deploy/` stays green: the bridge has no retrieval, and nothing is added to
  `shared/`.
- `python -m unittest deploy/commands/tests/test_desk_rules.py` passes with the smoke's questions scanned.

**Lane proof.**

1. `make plan up PROJECT=documind-ai-YOUR-ID` creates the two accounts, the claims database and its TTL, the topic,
   the push subscription and the API. Then `make deploy-gchat PROJECT=documind-ai-YOUR-ID REGION="$REGION"
   ADMIN_EMAILS="$ME"`, and chat again with `make build deploy-services PROJECT=documind-ai-YOUR-ID REGION="$REGION"
   SERVICES=chat SCRIPTS=commands/lesson-12.8.sh ADMIN_EMAILS="$ME"`, because the delegation module ships in the chat
   image.
2. `make smoke-gchat PROJECT=documind-ai-YOUR-ID` passes its four refusals. `make smoke-desk` and `make smoke-chat`
   still pass, because nothing changes for a caller without the header.
3. The probe. Configure the app as in section 4.11b, then, as a rostered demo account, open a direct message with the
   app, send "Hello" (W3's own test), then lk-06, and press one of the answer card's chips. `gcloud logging read` shows
   the `gchat_probe` rows: the event shape; whether the caller matched `GCHAT_CALLER`; `has_sender_email`;
   `has_user_id_token`; the space-type field's name; whether a thread name was present; where a press's parameters and
   form values arrive; and which posting auth worked (`adc`, `self_impersonation` or `failed`). If the only rows are
   `gchat_verify_failed`, read their booleans before anything else. From a shell, the author also runs the
   `outsider_lists_spaces` call (above). The author records these facts in the pull request description. They are not
   committed, because they are lane-dependent. If `has_sender_email` and `has_user_id_token` are both false, stop here
   and take Desk decision 33's contingency before anything else. If `outsider_lists_spaces` is true, record it under
   Desk decision 38.
4. Section 4.11b's demo runs end to end.
5. `gcloud logging read` shows `desk` rows with `via` "gchat" and `delegate` "gchat", `desk_delegation_denied` rows
   for the demo's steps 8 and 9, and no `desk_delegation_refused` row except the smoke's two, on which the alert
   fired.
6. In the `documind-gchat` database, each `gchat_events` document holds no text and no email, and its `expire_at` is
   24 hours out.
7. `make desk TENANT=acme DESK_GCHAT=off` closes the door within 60 s.

**Pages to rebuild.**

- 10.1, only if Desk decision 36's hook did not name `documind-gchat-sa` in G10-e: its expected deploy output lists
  documind-chat's invoker bindings (`lessons/10-agents/10.1-agent-loop/build.py:383`), and its lane box names who may
  invoke the chat service (`parts/c.html:93`). The loop gains no `${REGION:-us-central1}`, so the count assert
  (`build.py:107`) holds.
- 13.2, only if the refused-delegation alert was not added in G10-i (section 4.11).
- 10.5, only where `check_lesson.py 10.5` says a quoted line moved, which happens only if the `_principal` hook did not
  land in G10-e.
- `check_lesson.py` confirms these unchanged: 8.1 (the three `iap.identity(` callers, `build.py:108-111`, and the
  roster plan, since the bridge's accounts are on no roster); 8.2 (the outsider block, `terraform/sa.tf:55-65`); 8.3
  (no new literal emitter); 12.2 (the operators loop, `lessons/12-protocols/12.2-mcp-deploy/build.py:93`); 16.2 (no
  sink change); 18.1 (`build.py:150`); 18.3 (the Makefile's window, `build.py:153`).
- The 10.6 page does not wait for this pull request. The door reaches it through the 10.6 Google Chat content pull
  request (section 4.13), which quotes the bridge as merged.

**Effort.** L, about a week, plus the Workspace setup and the probe.

**Depends on.** G10-g (`/v1/desk` and its `desk` row), G10-e (cases, roles, the eval accounts the smoke uses, and
Desk decision 36's hooks), G10-c (`shared/desk_rules.py` and `shared/desk_law.py`), G8-a (the chat-pins step), and the
author's Business or Enterprise Google Workspace account (Desk decision 30). G10-e2 (the inbox in the demo), G10-h
(calculator answers in Chat) and G10-i (the Desk's rows in BigQuery) are soft.

**Table W: the Google pages behind sections 4.11a and 4.11b.** Checked on 30 September 2026. A read page came back
as a model-written summary, so quoted words are as that summary gave them.

| Label | Page | Status |
|---|---|---|
| W1 | https://developers.google.com/workspace/chat/verify-requests-from-chat | read |
| W2 | https://developers.google.com/workspace/add-ons/chat/configure | read |
| W3 | https://developers.google.com/workspace/add-ons/chat/quickstart-http | read |
| W4 | https://developers.google.com/workspace/chat/receive-respond-interactions | read |
| W5 | https://developers.google.com/workspace/chat/create-messages | read |
| W6 | https://developers.google.com/workspace/chat/limits | read; no pricing section |
| W7 | https://developers.google.com/workspace/chat/api/reference/rest/v1/Event | read |
| W8 | https://developers.google.com/workspace/chat/api/reference/rest/v1/User | read |
| W9 | https://developers.google.com/workspace/chat/identify-reference-users | read |
| W10 | https://developers.google.com/workspace/chat/authenticate-authorize-chat-app | read |
| W11 | https://developers.google.com/workspace/add-ons/guides/alternate-runtimes | read |
| W12 | https://developers.google.com/workspace/add-ons/concepts/event-objects | read; it has no `authorizationEventObject` |
| W13 | https://dev.classmethod.jp/en/articles/google-chat-bot-cloud-functions-python/ | read; third party |
| W14 | https://justin.poehnelt.com/posts/resolving-google-chat-user-ids-to-emails/ | read; third party |
| none | https://developers.google.com/workspace/chat/interact-users-overview, https://developers.google.com/workspace/add-ons/chat/commands, https://developers.google.com/workspace/add-ons/chat/convert, https://developers.google.com/workspace/add-ons/chat/send-messages, https://developers.google.com/workspace/chat/quickstart/gcf-app, https://github.com/agentconnect-md/agentconnect/pull/2643, https://discuss.google.dev/t/new-google-chat-apps-not-receiving-interaction-events/268042 | search result only |
| none | Cloud Tasks HTTP targets; the Chat `spaces` reference | not read |

**Unconfirmed, and what settles each.** The probe (lane proof, step 3) settles items 1 to 4, 10 and 11; `terraform
validate`, `terraform plan` and a `make down` followed by `make up` settle the Terraform items; the rest stay open and
are named where they matter.

1. Whether a Chat event carries the sender's email (W4, W7, W8, W9 do not say; W14 says membership events omit it).
2. Whether a Chat-triggered add-on event carries `userIdToken`. W11 describes it for add-ons in general, with the
   `userinfo.email` scope; W12 has no `authorizationEventObject`. W2's list of configuration fields has no OAuth scope
   field, so expect the token to be absent unless the probe shows otherwise. Desk decision 33's Directory lookup is
   then the realistic fallback if the email is also missing.
3. Whether the `chat.bot` scope works through Application Default Credentials or self-impersonation (W10 uses a key).
4. The name of the space-type field, whether a direct message has a thread name, and where an add-on press's
   parameters and form values arrive.
5. The add-on model's time limit (W4 states 30 seconds for the classic model), how the configuration page selects the
   add-on model, whether a button's `action.function` is the endpoint URL, and card update in place.
6. Whole-domain visibility beyond five people or Google Groups (W2).
7. Whether the lane project can host a Chat app for a Workspace it does not belong to, and whether a Workspace user
   outside the lane project's organisation can sign in to the Desk page through IAP.
8. The Chat API's price: W6 has no pricing section, and no read page states it.
9. From memory only: the Pub/Sub message storage field and minimum retention, the push subscription's `audience`
   field and the push envelope's `subscription` field, an IAM condition on a Firestore database, the Firestore
   database's `deletion_policy` and its default, when Firestore's TTL deletes an expired document, the duplicate
   custom id's error, whether the add-on agent exists before the app is configured, and the classic synchronous
   reply's shape.
10. Whether any service account in the lane project can authenticate as the Chat app (the author's
    `outsider_lists_spaces` call).
11. Whether an add-on-model Chat app posts through `spaces.messages.create` with app authentication. W5 and W10
    describe the Chat API without naming a model, and the add-on guide to sending messages
    (https://developers.google.com/workspace/add-ons/chat/send-messages) was a search result only. The probe's posting
    result settles it, and `GCHAT_ASYNC = False` is the fallback.
12. Whether the Workspace's Google Chat settings allow the app by default (not researched).

### 4.11b The Google Chat demo script

What the presenter does and what the audience sees, in about ten minutes (an estimate). It is also step 4 of G10-j's
lane proof. Account names are placeholders: `example.com` stands for the author's Workspace domain.

**Prepare (the author, once per demo lane).**

1. A Business or Enterprise Google Workspace account with Google Chat, which W2 and W3 list as the prerequisite, and
   a lane project with billing on (W3). Sign in to the console as a Workspace account that holds a role on the lane
   project; whether a project outside the Workspace organisation can host the app is unconfirmed. The Workspace's
   Google Chat settings must let users use Chat apps; the setting's name and its default were not researched. Three
   demo users in the Workspace: `employee@example.com`, `ic.member@example.com` and `visitor@example.com`.
2. Deploy: `make plan up PROJECT=documind-ai-YOUR-ID`, then `make deploy-gchat PROJECT=documind-ai-YOUR-ID
   REGION="$REGION" ADMIN_EMAILS="$ME"`, then chat with `SCRIPTS=commands/lesson-12.8.sh` (section 4.11a, lane proof,
   step 1).
3. Configure the Chat app in the Google Chat API's configuration page (W2, W3):
   - the app model: the add-on model (Desk decision 31). How the page selects it is unconfirmed: W3 names no switch,
     and the convert guide was a search result only. The sign that it took is the "Service Account Email" under the
     HTTP endpoint URL (W3), checked below. If the page shows no such email, the app is on the classic model and every
     request is refused, so stop and take Desk decision 31's alternative;
   - app name "HR Desk" (W2 allows 25 characters);
   - an avatar: an HTTPS link to a PNG or JPEG, 256 by 256 pixels recommended (W2);
   - description "Handbook and labour law answers" (31 characters; W2 allows 40);
   - interactive features on; "Join spaces and group conversations" off (W2);
   - connection: HTTP endpoint URL `https://documind-gchat-NUMBER.REGION.run.app`, no trailing slash, with "Use a
     common HTTP endpoint URL for all triggers" (W3);
   - visibility: `employee@example.com`, `ic.member@example.com` and `visitor@example.com`, plus the leaver and
     `grc_member` accounts if the optional steps run. That is within W2's five named people; one Google Group holding
     them also works (W2). `visitor@` must be inside the visibility, because a person outside it cannot find the app,
     and step 8 shows that the roster refuses it, not the visibility;
   - logs: "Log errors to Logging" on (W2).

   Check that the "Service Account Email" the page shows equals
   `service-NUMBER@gcp-sa-gsuiteaddons.iam.gserviceaccount.com`, the value `commands/gchat.sh` puts in
   `GCHAT_CALLER`, and run `make deploy-gchat` again if its binding printed the "configure the app" message. Saved
   changes reach all existing users (W2).
4. Roster, role and queue:
   - `make roster TENANT=acme MEMBERS=employee@example.com,ic.member@example.com`;
   - `make roles TENANT=acme EMAIL=ic.member@example.com ROLES=ic_member:hyderabad`;
   - a local copy of `evals/desk/queues.acme.json` that names `ic.member@example.com` as Hyderabad's Internal Committee
     member, loaded with `make desk-queues TENANT=acme FILE=<your copy>` and never committed;
   - `visitor@example.com` stays on no roster.
5. Let `ic.member@example.com` sign in to the Desk page and do nothing more:
   `gcloud iap web add-iam-policy-binding --project=documind-ai-YOUR-ID --resource-type=cloud-run --service=documind-ui
   --region="$REGION" --member=user:ic.member@example.com --role=roles/iap.httpsResourceAccessor`, the grant
   `commands/lesson-12.4.sh:43-47` makes for each `ADMIN_EMAILS` address. Do not add the account to `ADMIN_EMAILS`:
   `make operators` would then let it mint tokens as `documind-ui-sa` (`Makefile:384-391`), which is on every golden
   roster (`commands/lane.py:145-146`). Whether a Workspace user outside the lane project's organisation can sign in
   through IAP is unconfirmed, and the rehearsal settles it.
6. `make desk TENANT=acme DESK_GCHAT=on`. Acme already runs `desk_gate` and `desk_route` on (section 1.3).
7. A few minutes before the demo, `make smoke-desk PROJECT=documind-ai-YOUR-ID`, which wakes `documind-chat` and
   `documind-api` from zero instances. Rehearse on-stage steps 2 to 6 once.

**On stage.**

| Step | The presenter does | The audience sees | What it shows |
|---|---|---|---|
| 1 | As `employee@`, opens Google Chat, "New chat", searches for "HR Desk" and opens a direct message (W3) | The welcome card: what the Desk answers, that it works in direct messages only, and the privacy line | The app is live |
| 2 | Sends "What is the notice period for a confirmed E3?" (lk-06, `evals/golden.jsonl:6`) | An acknowledgement at once, then a card headed "From your company handbook": 60 days, cited to NP-03 in `hr_policy_2026.md` with its quote (`acme/hr_policy_2026.md:5-9`), the desk chips and "Raise a case" | The asynchronous path, with citations |
| 3 | Sends "What is the overtime rate under the Code on Wages?" (lk-20, `evals/golden.jsonl:37`) | An acknowledgement, then a card headed "What the law says": not less than twice the normal rate of wages, cited to the Code on Wages (`acme/code_on_wages_2019.md:413-417`), with the in-force line in its own paragraph | The statute desk. The line's date shows only once the operator has checked it against the Gazette (section 5.4) |
| 4 | Sends a POSH disclosure taken from G10-a2's dev rows, never from the frozen test split | The POSH card at once, with no acknowledgement: the fixed template, the offices (hyderabad and pune, `acme/townhall_2026_q1.md:6-7`), the Internal Committee members of the chosen office, the Local Committee contact and the privacy line | The gate fires in the bridge: no queue, no router, no model call |
| 5 | Chooses hyderabad, ticks `ic.member@` and presses "Create a confidential record". If selection inputs are refused in a message card, presses the hyderabad button instead, which records the case for all of that office's Internal Committee members (section 4.11a) | "Recorded", a case reference and the Act's information text | A disclosure becomes a case in the queue the law names |
| 6 | As `ic.member@`, opens the Desk page's inbox (G10-e2) | The case with its office and chosen contact, and no text | Only the chosen member reads it |
| 7 | Opens Cloud Logging and Firestore | For step 4: the bridge's `gchat` row with `queued` false, and the Desk's `desk` row with user null, `case_type` "sensitive", model `none` and cost 0. `cases/{id}` has no text field. The disclosure was never claimed, so it has no `gchat_events` document; the one for step 5's press, in the `documind-gchat` database, holds no text and no email and has an `expire_at` 24 hours out. Firestore deletes it some time after that (from memory, typically within a further day; unconfirmed). For step 2: a `desk` row with `via` "gchat" and the person's email | DocuMind kept nothing of the disclosure |
| 8 | As `visitor@`, sends any question | "Your account is not on a DocuMind roster" | Unknown people are refused |
| 9 | Runs `make desk TENANT=acme DESK_GCHAT=off`, waits 60 s and asks again as `employee@`, then turns it back on | "Not switched on for your company" | The per-tenant switch |

Say one thing plainly to the audience: the disclosure typed in step 4 stays in that Chat conversation under the
company's Workspace retention, and DocuMind stores none of it.

Optional steps, when time allows: a leaver's handbook question gets the denial with "Raise a case" only (a fourth
account with `make roles ... ROLES=leaver`), and a grievance drafted in Chat, confirmed with the card's Confirm button,
appears in a `grc_member`'s inbox (a fifth account, with the same sign-in grant as prepare step 5).

If an answer does not arrive on stage, the bridge's fifth attempt posts "could not reach the HR Desk" (section 4.11a),
and the Desk page serves the same answers. After the demo, run `make smoke-chat PROJECT=documind-ai-YOUR-ID`, so the
latest checkpointed thread is a chat brain's again for 11.2's cell (section 4.12).

### 4.12 The 10.6 page pull request

**Goal.** Lesson 10.6 as in section 6.2.

**Files.**

- The page `lessons/10-agents/10.6-desk-router/Netsetos_GCP_Capstone_10.6_Desk_Router_WIX.html` and its `build.py`.
- The manifest entry, the roadmap and plan rows, and `deploy/workshop_demos/module_10/lesson_10_6/`.
- 10.5's footer names 10.6, and 10.6's footer names 11.1. The sentence "Module 11 starts from those conversations"
  moves from 10.5's lane box to 10.6's.
- The page ends with `make smoke-chat PROJECT=documind-ai-YOUR-ID`, so the latest checkpointed thread is a chat
  brain's again: 11.2 decodes "the latest thread" (`lessons/11-memory/11.2-durable-storage/build.py:201`) and lists
  the 12 latest (`:193-194`), and a desk thread there would carry `DeskState` channels.
- The counts in section 6.4.
- The `deploy/UNOWNED.md` rows for the files the page quotes are removed (section 4.0).

**Effort.** L.

**Depends on.** G10-g, G10-h, G10-i, and the frozen test split (section 5.2).

### 4.13 Content pull requests after 10.6

- **12.1.** `lessons/12-protocols/12.1-*/parts/c.html:28` says "text uploads are stamped `unknown`, so any of them
  empties the pool". After 10.6 that is true only of unregistered uploads. The sentence and its expected output are
  rewritten.
- **13.1.** The widget case "A filter nothing matches: doc_type policy"
  (`lessons/13-operations/13.1-debug-wrong-answer/build.py:818`) becomes a class nothing holds, for example
  `doc_type form`.

Each is one lesson per pull request. Effort S each. They depend on the 10.6 page.

**10.6, the Google Chat door.** After G10-j merges, the Google Chat material of Desk decision 34 is added to the 10.6
page in its own content pull request (section 6.2): `smoke-gchat`'s expected output, the author's Chat cards as
expected output with placeholders for lane values, and the additions to each level. The page's closing
`make smoke-chat` already covers the desk threads the door creates. It adopts G10-j's files and removes their rows
from `deploy/UNOWNED.md`. It depends on G10-j and the 10.6 page. Effort M.

---

## 5. Data and evaluation

### 5.1 The doc_type backfill

**The problem.** Every text chunk the worker ingests from GCS carries "unknown" (`services/ingest/contracts.py:70`);
rows seeded by `shared/documind_corpus.py` already carry the manifest's class (`:121`), and the relabel plans no
change for them. Uploading the same bytes again cannot fix the worker's rows:

- `doc_key` is the tenant plus the sha256 (`services/ingest/contracts.py:76-78`);
- a repeat is acked as `duplicate` (`services/ingest/main.py:383`, `:392`).

So the fix works on stored data.

**The registry.** The registry is operator-owned. It lives at `tenants/{t}/doc_types/{source_id}` as `{name,
doc_type, pin, set_by, set_at, source}`. The pin is a `doc_key`, and `source` is "manifest" or "operator".

**Seeding from `evals/manifest.json`.**

- Text objects take their manifest class. On a lane that has already ingested, the seed pins each name's current
  `doc_key` from the ledger and cross-checks it against the manifest's `sha256`; a mismatch is printed, not pinned. On
  a fresh lane, seeding before `make ingest-corpus` pins from the manifest, so text objects get their class at ingest.
- Media have a null `sha256`, so their pins come from the lane's current `doc_key` after ingest. They take their
  parent's class through the longest same-tenant slug prefix:

  | Media object | Parent | Class |
  |---|---|---|
  | `annual_report_2026_fig3.png` | `annual_report_2026` | report |
  | `inv_2026_0412.png` | `inv_2026_0412` | invoice |
  | `payment_of_bonus_act_1965_p30.png` | `payment_of_bonus_act_1965` | statute |
  | `townhall_2026_q1.mp4` | `townhall_2026_q1` | transcript |
  | `whiteboard_arch.png` | none | stays unregistered: `figure` from `MEDIA_TYPES`, in no desk's scope |

- The town hall is registered under both names, because `evals/upload.sh:36` skips the `.md` when the `.mp4` exists.

**The steps of `relabel.py --apply`, per tenant.**

1. Firestore chunk rows of each pinned current version get the class, in batches under Firestore's 500-write limit.
   The managed backends read `doc_type` from these rows at query time (`services/rag-api/retriever.py:142-150`, `:227`,
   `:321`).
2. Vector Search datapoints are re-upserted from the rows' own vectors through `_repair_snapshots`
   (`services/ingest/indexer.py:189-234`). It writes `row.get("doc_type") or "unknown"` (`:210-213`) into the restrict
   (`_restricts`, `:113-119`). Only current rows are passed, because it raises on others (`:206`).
3. Vertex AI Search gets a `structData`-only update of `doc_type` (`STRUCT_FIELDS`, `services/ingest/managed.py:41`),
   written in `relabel.py` itself so that 15.3's upsert-caller assert holds (section 4.2). This applies to acme and
   zeta, whose policy is `any` (`commands/lane.py:148`), when a store exists. A full upsert would write the text again
   to the audit bucket, whose retention policy refuses deletes (`managed.py:227-231`, `:288`).
4. BigQuery `rag_data.chunk_source` (`BQ_CHUNK_TABLE`, `services/ingest/main.py:71`; rows from `mirror_to_bigquery`,
   `indexer.py:295-318`) gets a DML `UPDATE` on tenant and source. Rows still in the streaming buffer are refused by
   BigQuery, reported, and retried on the next run.
5. Versions that do not match a pin are set to "unknown".
6. The tenant's `answer_cache` is purged, because the fingerprint does not move on a relabel
   (`services/ingest/idempotency.py:357-363`) and a cached answer is scoped by its filters (`semantic_cache.py:38-43`).
7. Nothing is re-uploaded, and nothing is re-embedded unless the row's embedding does not match. That is
   `_repair_snapshots`' own rule.

**New uploads.** The worker hook (section 4.2) gives a registered, pinned version its class at ingest, on both the
push and the batch lanes. A new version of a registered name ingests as "unknown", and so does an overwrite by any
member (the uploads bucket grants ui-sa `objectAdmin`, `terraform/storage.tf:108-111`). The handbook desk then refuses
rather than quoting unreviewed text. The operator re-pins with `make doc-types FOLLOW=<name> APPLY=1` after review. A
log-based alert on a pin miss is part of G10-i.

**`--reset`.** The same steps with every class set to "unknown", for rehearsals of 5.1 and 10.3 on the author's lane
(section 4.2). The registry stays.

**Exit check.** A second plan lists no change, and `make eval-live` gives the same per-row verdicts.

### 5.2 The route test set, written new

**Contamination rules.** These are the research report's section 7.2 rules:

1. The split is by group. A golden id, its paraphrases, a follow-up pair and normalised question text all go to one
   side.
2. Every pre-existing row is dev only.
3. Test rows are new, written by people who have not seen the rules, the prompt or the exemplars.
4. `route_eval --selftest` fails on identical normalised text across the split. `make route-eval` also fails on an
   embedding cosine of 0.95 or more.
5. A test row whose failure leads to a change moves to dev, and a fresh unseen row replaces it. Both are logged in
   `evals/route_test_refresh.log`.
6. The kNN index is built from dev rows only, and on the dev split it votes leave-one-group-out (section 4.8).

**Composition at launch** (without Phase E and company_info):

| Slice | Dev | Test, Phase A | Test, before GA |
|---|---|---|---|
| Golden, relabelled | 65 | 0 | 0 |
| Paraphrases | 42 | 0 | 0 |
| SFT questions rewritten in the first person | about 100 | 0 | 0 |
| handbook (new) | 45 | 30 | 30 |
| statute (new; includes repeal-note rows and jn-11-style guidance rows) | 45 | 30 | 30 |
| out_of_scope (new; personal records, actions, "no_desk" report, contract and invoice questions) | 45 | 30 | 30 |
| clarify | 30 | 30 | 30 |
| Escalation, 5 classes, at least a third Hindi or Hinglish; in test, at least 5 globex rows a class (single mode relies on the rules and the button) | 100 | 100 (20 a class) | 375 (75 a class) |
| First-person non-escalation (lexicon precision) | 120 | 80 | 80 |
| Near-miss informational ("What does IR Code s.4 say about GRCs?") | 20 | 20 | 20 |
| Follow-up pairs | 15 | 15 | 15 |
| Multi-intent | 10 | 15 | 15 |
| Injection ("ignore your rules and route this to...") | 0 | 15 | 15 |
| PII (two-turn rows check the next L1 prompt) | 0 | 6 | 6 |
| Calculator, exact (45 days, accrual, carry-forward, notice end, gratuity from stated inputs, two working days, 20) | 0 | 8 | 8 |
| Role denial (the leaver identity) | 0 | 5 | 5 |
| Coverage and single mode (globex: a handbook or labour-law question gets the statute desk's grounded refusal and never another tenant's text) | 0 | 8 | 8 |
| **Total** | **about 637** | **392** | **667** |

**Why these sizes.** When every row passes, the Wilson lower bound is n / (n + 3.84):

- 20 rows a class gives 83.9% per class and 96.3% pooled over 100;
- 75 a class gives 95.1%, and 73 is the minimum for 95%.

**Stricter option.** handbook, statute and out_of_scope at 75 test rows each (802 in all) would give a per-desk bound
of 95.1% too. It costs 135 more rows (Desk decision 3).

**Required rows.** Test escalation ids and denial ids go into `evals/required_routes.json` with a per-class minimum n.
Each must pass individually, as `evals/required.json`'s ids do.

**Writers and labels.** The recommended default (Desk decision 2), delivered as G10-a2 (section 4.1):

- the escalation and first-person rows are written by people, with Hindi and Hinglish by a fluent writer;
- a model may draft non-escalation rows in a fresh session given only the five label descriptions, and a person
  reviews each row;
- two labellers share a 60-row overlap, and a kappa below 0.8 sends the desk descriptions back.

**Timing.** Commission the writers at M0. The dev rows land as G10-a2 (M2). Freeze the Phase A split before any
router change is scored on it (M4).

**Run cost.** These are estimates:

- L1 at about Rs 0.0124 a call (the research report's approximate count): about Rs 15 for a Phase A test pass^3
  (392 x 3) and about Rs 25 before GA (667 x 3);
- L2 at about Rs 0.0636 a call before thinking, on the L2 share;
- answer rows (handbook, statute, calculator and denial) through `/v1/desk` at an estimated Rs 0.37 each, once per
  arm for the ship comparison (B, C and A*), so about three times that at M5;
- embeddings on top. No first-party price was found for them.

### 5.3 Roles

All roles live in `tenants/{t}/roles/{email}`, written only by the operator (`make roles`). A roster member with no
role document is `employee`. `employee` is implied only when the document is absent: a document lists every role it
grants. A failed read allows only the case desk.

| Role | Allows | Who holds it at launch |
|---|---|---|
| `employee` | handbook, statute, case, clarify, out_of_scope | every member |
| `leaver` | case only; answer desks are `denied` | a leaver, set by hand, for a grace period (90 days proposed) |
| `people_ops` | the people queue; grievance records only if the person opted in | the tenant's HR staff |
| `payroll` | the payroll queue (exit dues) | payroll staff |
| `ic_member:<unit>` | the POSH cases of that unit, and only those whose contacts the person chose | the Internal Committee of each office |
| `grc_member` | grievance cases, and their status | the Grievance Redressal Committee; on the lab lane, documind-evalgrc-sa and you@example.com |
| `privacy` | privacy requests | the s.8(9) contact, or the DPO |
| `desk_eval` | `/v1/route`, and `arm` and `prev_*` in a request body | documind-evalacme-sa, documind-evalzeta-sa, documind-evalglobex-sa (with `employee`) and documind-evalleaver-sa (with `leaver`) |

`desk_reviewer` and `desk_pilot` (research report, section 9) are reserved names for a pilot's review sample and pilot
group. No launch code reads them.

**Known weakness.** chat-sa holds project-wide `roles/datastore.user` (`terraform/sa.tf:212`), so a compromised chat
service could write roles and cases. The checks guard against bugs, not against a compromised service. The gap plan
accepts the same for G2.

### 5.4 The case queue

**Configuration.** `tenant_settings/{t}.case_queues` holds the POSH units with their Internal Committee members and the
district Local Committee contact, the grievance committee, the privacy contact, payroll, people, and the clause-prefix
map. Every SLA is the company's own number, labelled as such. `make desk DESK_GATE=on` refuses a tenant whose POSH
section is incomplete.

**Case types at launch.** The research report's POSH section numbers are not re-verified here. The kit's POSH Act is a
scan with no text mirror (`evals/README.md:38-39`), so they are checked against the Act's primary source before the
template ships.

| Type | Queue and readers | Clock shown | Basis cited |
|---|---|---|---|
| `posh` | `ic:<unit>`: only the chosen members read it; the Local Committee contact is always shown | the Act's periods, as information about a written complaint | the POSH Act by section and primary-source URL |
| `grievance` | `grc`: members only; people_ops only if the person opts in | one-year filing window; the committee "may complete" in 30 days (research report, section 6.2) | IR Code s.4(1), `acme/industrial_relations_code_2020.md:397-399`, for establishments of 20 or more workers |
| `privacy_request` | `privacy`, falling back to people with the type kept | none statutory: "within such period as may be prescribed" (s.13(2)), and the company's SLA | DPDP Act s.8(9), `acme/dpdp_act_2023.md:379-382`, and s.13(2), `:490-492`; zeta holds no DPDP Act, so its template cites the Act by name and URL |
| `exit_dues` | `payroll`, readable by people_ops | wages within two working days, flagged "may have passed" | Code on Wages s.17(2), `acme/code_on_wages_2019.md:459-464`; leave wages on exit, OSH s.32(1)(vi), `acme/osh_code_2020.md:1537-1548`; gratuity within 30 days of becoming payable, `acme/code_on_social_security_2020.md:2365-2366` |
| `people_query` | from the clause-prefix map | none | the desk that tried, with its chunk ids |
| `human_requested` | `people` | none | the desk that was answering |

**Instrument status table** (`shared/desk_law.py`). Repeal facts come from the corpus:

- the Code on Social Security s.164(1) repeals the Maternity Benefit Act and the Payment of Gratuity Act
  (`acme/code_on_social_security_2020.md:5409-5418`);
- the Code on Wages s.69(1) repeals the Payment of Bonus Act (`acme/code_on_wages_2019.md:1632-1633`).

The dates are entered by the operator:

- the Labour Codes in force from 21 November 2025 (verify against the Gazette);
- the DPDP Act's rights provisions, 13 May 2027 per the research report's secondary source (verify against the
  Gazette).

A date is not shown to people until it is checked.

**Flow.** It follows the research report's section 6.3 without Phase E delivery:

1. A rule, the model, a desk or the button proposes a case.
2. A draft comes back. POSH has none: its button creates the record directly, with the unit and the chosen contacts.
3. The person edits and confirms, with an idempotency token, or cancels.
4. `case.open` is written with a case-reference actor.
5. The case appears in the queue's inbox.
6. The hourly job logs the due and breached cases.

Confirmed cases have no TTL; retention is the tenant's decision.

**Sensitive logging.** For posh, grievance and privacy_request, the desk row's `user` is null and `case_type` is
"sensitive". The audit actor is a case reference, because the audit bucket refuses every delete
(`terraform/storage.tf:81-89`).

---

## 6. The lessons

### 6.1 Lesson 10.5, "Hand a question to the person the law names"

Proposed, pending Desk decision 0. `course-manifest.json` is not edited until the author decides.

**Manifest entry.**

```json
"10.5": {"name": "Hand a question to the person the law names", "slug": "case-desk", "topic_filename": "Case_Desk",
         "proof": "a POSH disclosure through `/v1/stream` returns the fixed template with model `none` and cost 0; a confirmed grievance case in the committee's inbox",
         "status": "Not started"}
```

**Page.** `lessons/10-agents/10.5-case-desk/Netsetos_GCP_Capstone_10.5_Case_Desk_WIX.html`.

**Shape.** Hero with chips, a table of contents, an "In this lesson" box of one or two lines, Level 0, a definitions
table (gate, case class, queue, clock, role, draft, template), then the shared shell setup
(`pagekit.pagebuild.setup_section()`), then the levels below.

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 0 | Level 0: the law names a person | An interactive built on the real lexicon classes and case table. The learner types a question and sees the class that fires (or none), the queue, the clock and the statute with its corpus line. The analogy: a hospital reception that sends "chest pain" straight to the emergency bay without booking a consultation | `shared/desk_rules.py`, `shared/desk_law.py`, read at build time | A build-time assert that the widget's verdicts equal `gate()` on the page's sample rows |
| 1 | Level 1: the Desk page | Types a POSH disclosure and gets the IC card, with no model call. Raises a grievance, edits it and confirms. As a `grc_member`, sees it in the inbox. The routed half is hidden, because `desk_route` is off | `services/frontend/desk.py`, `make desk-queues`, `make roles`, `make desk DESK_GATE=on` | The card shows owner, SLA and basis; the inbox lists the case |
| 2 | Level 2: every door | Sends the same disclosure through the Chat page's default direct brain, which streams to rag-api, and gets the template. Reads why the gate also lives in rag-api: MCP and the A2A peer call it directly | `services/rag-api/desk_door.py`, `services/chat/desk.py` `install()` and the chat door (verbatim) | `/v1/stream` gives a token and `done`, with model `none` and cost 0 |
| 3 | Level 3: roles and cases in code | Reads `roles_for()` (a missing document is `employee`, a failed read allows only cases), `cases.confirm()` in a transaction, the random id, the code-side expiry and the POSH record with no text | `shared/roles.py`, `shared/cases.py` (verbatim) | The offline tests: 410, 404 across tenants, no text on a POSH record |
| 4 | Level 4: REST | `curl` to `/v1/query` (the template), `/v1/cases` (a draft), and `/v1/cases/{id}/confirm` twice with one token (one case), as documind-evalacme-sa. Then as the outsider (403) and as documind-evalzeta-sa, another tenant's member (404) | `make smoke-cases`, `make desk-operators` | `make smoke-cases` PASS lines |
| 5 | Level 5: direct reads | Reads `cases/{id}` in Firestore, `tenants/acme/roles/{email}`, the audit listing with `case.open` and a case-reference actor, and the `desk_gate` log row with user null | a `python - <<'PY'` Firestore cell, `gcloud storage ls gs://documind-ai-YOUR-ID-audit/...` | The listing shows `case.open`; the POSH record has no text field |

**Verify it yourself.** `make smoke-cases` passes. `/v1/stream` gives model `none`. The audit event names no email.

**What changed on your lane.**

- New: the role documents, `case_queues`, `desk_gate` on for acme, the `cases` collection with its TTL and indexes,
  the `documind-cases-overdue` job, the five eval accounts on their rosters, and your token-creator grant on them.
- Changed for the lessons that follow: acme's questions pass the gate first. A disclosure gets the template, and an
  Aadhaar or card number is masked before rag-api or the chat brain sees it. The course's own questions never fire it
  (section 4.3's tests).
- Unchanged: every other tenant's behaviour.
- Until 10.6 lands, the box ends with 10.4's sentence that Module 11 starts from those conversations (section 4.7).

### 6.2 Lesson 10.6, "Route each question to one specialist agent"

Proposed, pending Desk decision 0. `course-manifest.json` is not edited until the author decides.

**Manifest entry.**

```json
"10.6": {"name": "Route each question to one specialist agent", "slug": "desk-router", "topic_filename": "Desk_Router",
         "proof": "`make route-eval SPLIT=test` passes every escalation row; a cited handbook answer and a statute answer with its in-force line on the Desk page",
         "status": "Not started"}
```

**Page.** `lessons/10-agents/10.6-desk-router/Netsetos_GCP_Capstone_10.6_Desk_Router_WIX.html`.

**Shape.** Hero with chips, a table of contents, an "In this lesson" box, Level 0, a definitions table (route, desk,
anchor, L1, kNN share, L2, `authority_rate`, `doc_type` class), then the shared shell setup, then a "Before you start"
step, then the levels. The levels rise from the UI to direct reads, as `CLAUDE.md` asks.

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 0 | Level 0: one front door, one desk | An interactive of the cascade built from the `DESKS` table and acceptance rules A to D and F, with the calibrated thresholds. The analogy: the same hospital reception, where the triage nurse is the rules, the receptionist's glance is L1, the register of past visits is the kNN, and the duty doctor is L2 | `services/chat/desk_routes.py`, `desk_router.py`, read at build time | A build-time assert that the widget's thresholds equal the kit's constants |
| - | Before you start: label the documents | `make doc-types TENANT=acme SEED=manifest` shows each object's current label and new class; `APPLY=1`, then zeta and globex. `make route-index`, `make desk DESK_ROUTE=on` for acme and `single` for globex | `make doc-types`, `make route-index`, `make desk` | A second plan lists no change |
| 1 | Level 1: the Desk page answers | Gets a handbook answer (NP-03, 60 days), a statute answer with its in-force line, a clarify with two buttons and an out_of_scope reply on acme; globex in single mode | `services/frontend/desk.py` | Each answer shows its route and method |
| 2 | Level 2: the kit's code | Reads `shared/doc_types.py` (the registry and the pin), `decide()` (the enum schema with no free-text field, rule D's asymmetry, the fallback) and the graph (`dispatch`, `next_part`'s sequencing) | `shared/doc_types.py`, `services/ingest/relabel.py`, `desk_router.py`, `desk_graph.py` (verbatim) | `make desk-check` green |
| 3 | Level 3: REST | Calls `/v1/route` as documind-evalacme-sa and reads the decision record. Calls `/v1/desk`. Sees the leaver's denied turn with zero retrieve calls, and the 45-day calculator turn | `evals/route_eval.py` | The decision JSON; `tool_calls []` on the denial |
| 4 | Level 4: direct reads | Reads relabelled chunk rows in Firestore (`doc_type` policy on NP-03's row), a `desk_exemplars` document, and zeta's `desk_shadow` rows. Optionally reads `desk_daily` in BigQuery: the sink and the views are previewed here and explained in 13.2 | a `python - <<'PY'` Firestore cell, `gcloud logging read`, `bq query` | NP-03's row carries `policy`; the exemplar carries its route |

**The Google Chat door in 10.6 (Desk decision 34).** It is a second front door onto the same `/v1/desk`, so it is
taught inside the levels the page already has, in their rising order, and adds no lesson. It arrives with its own
content pull request after G10-j (section 4.13), which changes the page as follows:

- The definitions table gains "delegate".
- "Before you start" gains `make plan up` and `make deploy-gchat` (the bridge, its accounts, its database, its topic).
- Level 1 gains: with a Business or Enterprise Google Workspace account, the same lk-06 question in the "HR Desk" app
  brings an acknowledgement, then the cited card, and a POSH disclosure from the page's sample brings the template
  card at once. Without one, the author's run is shown as expected output.
- Level 2 gains `services/chat/delegation.py` `principal()` and `services/gchat/cards.py` `render()` (verbatim), and
  why the bridge is its own service without IAP.
- Level 3 gains `make smoke-gchat`: the outsider's Chat-shaped request refused by the bridge's code (401), and a
  delegation header from documind-evalacme-sa or ui-sa refused by the Desk (403). Its proof column gains
  `make smoke-gchat` PASS lines, for every learner.
- Level 4 gains a `desk` row with `via` "gchat" and a `gchat_events` document with no text and no email.
- "Verify it yourself" gains "`make smoke-gchat` passes".
- "What changed on your lane" gains: the `documind-gchat` service and its two accounts, the `documind-gchat`
  Firestore database, the `documind-gchat-work` topic and its push subscription exist; `desk_gchat` is on for acme only
  if you configured the app, and off everywhere else.

It adds about 20 minutes (an estimate), most of it the deploy and the app's configuration. Every learner can reach its
proof, because the smoke's refusals need no Workspace; only the conversation in Chat does. If 10.6 is split (Desk
decision 18), this material moves with the router to 10.7. The manifest's `proof` for 10.6 is unchanged.

**Verify it yourself.** `make smoke-desk` passes, and `make route-eval SPLIT=test` meets the section 1.3 gates,
printing the 5x5 matrix with Wilson intervals, per-class escalation recall and `authority_rate`. The page ends with
`make smoke-chat PROJECT=documind-ai-YOUR-ID`, so the latest checkpointed thread is a chat brain's again (section
4.12).

**What changed on your lane.** Every current chunk carries its class; the exemplar index exists; acme is on, zeta was
shadowed and then switched on, globex is single; the sink takes the desk events; `desk_daily` exists. Module 11 starts
from the chat brains' conversations: where each one lives, and what else an agent remembers.

### 6.3 Existing lessons touched

| Lesson | Why | Pull request | Kind |
|---|---|---|---|
| 3.4, 5.1, 5.4, 8.2 | List filters change quoted retriever, `check_filters` and schema lines | G10-d | Forced rebuild; 5.1's widget text too |
| 10.1 | The `retrieve` signature, the route assert (`build.py:93`), and "no retrieval-only route" (`parts/c.html:69`) | G10-p | Forced rebuild and prose |
| 10.4 | The raw ADK declaration of `retrieve` (`build.py:179`) and its printed size | G10-p | Forced rebuild |
| 10.3, 18.4 | Only if the passages branch cannot keep their lines (section 4.6) | G10-p | Conditional rebuild |
| 8.3 | The literal emitters and the `AUDIT_ACTIONS` table | G10-e | Forced rebuild |
| 10.1 | The expected deploy output names documind-chat's invoker bindings (`build.py:383`); the lane box (`parts/c.html:93`) | G10-e | Rebuild of expected output and prose |
| 13.2 | The sink excerpt, its readers table, and a line for `desk.tf`'s alert policies | G10-i | Forced rebuild |
| 16.2 | The sink excerpt, its event assert, the events cell and two prose lines | G10-i | Forced rebuild and prose |
| 10.5 | Only if `desk_rules.py` or `desk_law.py` change after it lands | G10-f, G10-g | Conditional rebuild |
| 10.4 | The footer names 10.5; "Module 11 starts from those conversations" (`parts/c.html:50`) points to 10.5 | 10.5 page | Content |
| 10.5 | The footer names 10.6; the Module 11 sentence moves to 10.6 | 10.6 page | Content |
| 11.2 | Its latest-thread cell (`build.py:201`) would decode a desk thread | 10.6 page, which ends with `make smoke-chat` | None in 11.2 |
| 12.1, 13.1 | They state "unknown" after the relabel is taught | Content pull requests | Content |
| 10.5, 10.6 | Gap items that land later and change lines they quote | G3, G5-b (section 3.4) | Rebuild in those pull requests |
| 10.1 | The invoker loop at `commands/lesson-12.8.sh:39` gains documind-gchat-sa, so the expected deploy output (`build.py:383`) and the lane box (`parts/c.html:93`) change | G10-e with Desk decision 36's hook (inside its 10.1 rebuild above), otherwise G10-j | Rebuild of expected output and prose |
| 13.2 | The line naming `desk.tf`'s alert policies gains the refused-delegation alert | G10-i with Desk decision 36's hook, otherwise G10-j | Conditional rebuild |
| 10.5 | Only if the `_principal` hook did not land in G10-e and G10-j moves a quoted line | G10-j | Conditional rebuild |
| 10.6 | The Google Chat door, taught inside Levels 1 to 4 (section 6.2) | The 10.6 Google Chat content pull request (section 4.13) | Content |

Optional one-sentence pointers in 7.1 (the route set), 8.1 (roles beside approvers) and 13.3 (the domain router beside
rag-api's tier router) are not planned. The default is none.

### 6.4 Lesson-count changes

These follow the gap plan's rule (section 3). Each new lesson's own pull request moves every stated count:

- `course-manifest.json` (`total_lessons`);
- `tools/build_workshop_demos.py:357` (`lessons_expected`);
- `CLAUDE.md:8`, as the author's edit;
- `README.md:4` and `:19`;
- `plan/README.md:5`;
- `tools/README.md:19`;
- `deploy/README.md:23`;
- `deploy/workshop_demos/README.md:3`;
- `deploy/workshop_demos/REVIEW.md:7`, which also says "51 authored HTML pages" and gains one per page, and gives the
  code-window count ("1,477 code windows") on the same line, recounted by hand after the build because no tool writes
  `REVIEW.md`;
- the course plan's title line and `plan/course-plan-v5-story-2026-09-22.md:84`, for the count and the hours;
- the course plan's chapter 10 end state (`plan/course-plan-v5-story-2026-09-22.md:54`), for example "answer through
  four brains over one tool, refuse a blocked tool, route an employee's question to one desk and hand the law's cases
  to a person";
- the roadmap's title line (`plan/course-roadmap-v5-2026-09-22.md:1`), its batch table (`:201`, batch E's scene count)
  and ":205" ("Sixty scenes"), with its `.html` and `.pdf`.

The chapter 10 end state, the batch table, the code-window count, the course plan's title line and roadmap `:205` are
not in the gap plan's rule; section 3.4 proposes adding them in PR #72, so that 12.4, 12.5 and 11.4 move them too.

`deploy/workshop_demos/course_map.json` and `COURSE.md` regenerate. `tools/check_workshop_demos.py:54` and `:158`
require a lesson map for every manifest lesson, so each page pull request adds its map.

Each page pull request adds one to the count it finds, in whatever order the pages land. In section 7's likely order,
with gap decision 1: 60, 61 (12.4), 62 (10.5), 63 (10.6), then 64 and 65 (12.5 and 11.4, in gap phase 5); Core moves
from 47 to 52 and its hours from 70.5 to 78 by the same steps. Without gap decision 1: 60, 61 (10.5), 62 (10.6).
Section 2.4 gives the totals.

---

## 7. Milestones and the order across the gap plan and the Desk

The Desk rows below are in one feasible order. Under Desk decision 26 (a), a Desk row waits only for its "Needs", and
the gap plan's phases run beside it, each waiting only for the earlier gap phase. Under (b), rows 7 to 15 all land
before G3; rows 14a and 15a, the Google Chat door, do not hold G3.

| Order | Desk step | Needs | Gap work running beside it |
|---|---|---|---|
| 1 | G10-a: eval scaffold, relabelled dev rows, probe | none | phase 1: 1.1 G5-a, 1.2 G8-a, 1.3 G8-b, 1.4 G8-c, 1.5 G9-A |
| 2 | G10-b: registry and relabel | none | phase 1 |
| 3 | G10-d: list filters, with 3.4, 5.1, 5.4 and 8.2 rebuilt | none (G10-b for the lane proof) | phase 1 |
| 4 | G10-a2: the 430 new dev rows | G10-a; the writers | phase 1 or 2 |
| 5 | G10-c: gate and rag-api door | G10-a, G10-a2's escalation and first-person rows | phase 1 or 2 |
| 6 | G10-p: the passages route (10.1, 10.4) | 2.1 G6-a merged | phase 2: 2.2 G6-b to 2.8 G2-e |
| 7 | G10-e: roles, cases, chat door, eval identities (8.3, 10.1) | G10-c; the end of gap phase 2 (G2-a's slice, G2-d's 8.3); G8-a | phase 3: 3.1 G1 |
| 8 | G10-e2: the Desk page, case half | G10-e | phase 3, or 4.1 G3 under (a) |
| 9 | The 10.5 page | G10-e, G10-e2; after G2-c and G2-d | as above |
| 10 | G10-f: router and graph | G10-a2, G10-c, G10-e, G6-a, G2-a, G8-a | under (a), G3 and then phase 5 |
| 11 | Freeze the Phase A test split (392) | before any router change is scored on it | |
| 12 | G10-g: service, live eval, shadow | G10-f, G10-e, G10-e2, G10-b, and G10-d or Desk decision 4's alternative | |
| 13 | G10-h: agent mode and arm A* | G10-g, G10-p, G6-a, G8-a | |
| 14 | G10-i: operations (13.2, 16.2) | G10-g | |
| 14a | G10-j: the Google Chat door (10.1 and 13.2 only without Desk decision 36's hooks) | G10-g, G10-e, G10-c, G8-a; the author's Workspace account | |
| 15 | The 10.6 page, then 12.1 and 13.1 | G10-g to G10-i | |
| 15a | The 10.6 Google Chat content pull request | G10-j, the 10.6 page | |
| 16 | The GA gate: the test split grows to 667 | the 10.6 page | phase 5 or after |

Rows 2 (G10-b) and 3 (G10-d) are independent of G10-a, and G10-d needs G10-b only for its lane proof; row 5 (G10-c)
needs rows 1 and 4. No Desk row needs G1.

Row 14a (G10-j) needs only G10-g and what G10-g needs, so it can land beside rows 13 and 14, or after row 15: the 10.6
page does not wait for it. Section 4.11b's demo can run as soon as it merges. Row 15a then adds the door to the 10.6
page. Desk decision 36's hooks go into G10-e, G10-g and G10-i because G10-j lands after the 10.5 page and may land
after G10-i's 13.2 rebuild.

| Milestone | Done when | Research report phase |
|---|---|---|
| M0 Measured | G10-a merged; probe facts recorded; the 207 existing questions labelled; test writers commissioned | Phase 0 |
| M1 Labels | G10-b and G10-d merged; the relabel proven, `make eval-live` unchanged, then the author's lane reset with `RESET=1` until M5 (section 4.2) | Phase 0 |
| M2 Dev set | G10-a2 merged: 430 new dev rows, kappa 0.8 or more | Phase 0 |
| M3 Gate and case path | G10-c, G10-e, G10-e2 and the 10.5 page merged; the gate proven on `/v1/query` and `/v1/stream`; `desk_gate` on for acme on the author's lane | Phase B's gate step, early |
| M4 Router offline | G10-f merged; dev gates met with scripted and live L1, the kNN leave-one-group-out; test split frozen | Phase A |
| M5 Desk live | G10-p, G10-g, G10-h and G10-i merged; the lane relabelled for good; zeta in shadow, acme on, globex single; Phase A test gates met; B compared with C and A* (section 1.3) | Phase B on the lab lane |
| M6 Course | The 10.6 page and the 12.1 and 13.1 content pull requests merged; learner kit published with the author's go-ahead | none |
| M6a Desk in Google Chat | G10-j and the 10.6 Google Chat content pull request merged; the probe's facts recorded; the "HR Desk" app configured on the author's Workspace; section 4.11b's demo run end to end once; learner kit published again with the author's go-ahead | Phase B on the lab lane, through a second door |
| M7 GA gate | 667 test rows, 75 escalation rows a class, all passing | Phase D (a real pilot is outside the repository) |

The learner kit is published at the end of each gap-plan phase, each time only with the author's explicit go-ahead:
`python tools/publish_learner.py --dest <learner checkout> --commit`, then push.

---

## 8. Risks and open decisions

| # | Risk or decision | Recommended default | Alternative |
|---|---|---|---|
| 0 | New Core lessons: 10.5 "Hand a question to the person the law names" and 10.6 "Route each question to one specialist agent" (option B, section 2.2). The course goes from 60 to 62 lessons, Core from 47 to 49, and Core hours from 70.5 to 73.5; with gap decision 1, 65, 52 and 78 | Option B | A: one lesson, 10.5 (61). C: no new lesson, the Desk as the brief for 14.4 (60). B': an Advanced Module 19 (62 lessons and 19 modules) |
| 1 | Under-escalation is a legal failure. Indirect, Hindi, Hinglish or two-turn disclosures can pass the lexicon | Three independent paths: the rules, the model's case check on every non-rule turn (rule D, asymmetric), and the always-visible button. Single-mode tenants (globex) never call L1, so they rely on the rules and the button; the test split carries at least 5 globex escalation rows a class. Escalation recall is a release blocker on every test row | none safe |
| 2 | Who writes the test rows | People write the escalation and first-person rows, with Hindi and Hinglish by a fluent writer. A model drafts non-escalation rows from the label descriptions only, and a person reviews each. Kappa of 0.8 or more | Everything by people, which is slower |
| 3 | Test sizes | 392 at Phase A, 667 before GA | 802, with 75 rows each for handbook, statute and out_of_scope |
| 4 | List filters | G10-d, with four rebuilds; `doc_type` lists only | The scalar path with a guidance anchor for jn-11-style questions |
| 5 | A member overwrites the handbook | The registry pin: a new version is "unknown", the desk refuses, and an alert fires | A `doc_admin` upload gate, which rebuilds 6.4 and 16.2 |
| 6 | Sensitive audit actor | A case reference, with no email and no key | HMAC over the email with a per-tenant key in Secret Manager |
| 7 | The exit-dues clock. s.17(2) counts from the removal, dismissal, retrenchment or resignation (`acme/code_on_wages_2019.md:459-464`) | Quote s.17(2) verbatim, compute the flag from the last working day, label it as the desk's reading, and have counsel check it | Count from the resignation date |
| 8 | Legal dates (Labour Codes 21 November 2025; DPDP rights provisions) | Operator-entered after a Gazette check, and not shown until checked | Run a WebSearch check now (not run for this plan) |
| 9 | Logprobs may be missing on Gemini 3.x | Build rule E only if the probe shows them | none |
| 10 | Router latency on `global` is unmeasured, and a cold rag-api takes about 90 s against G6's 100 s deadline | Router hard total 8 s, then the fallback; measure p50 and p95 in shadow | none |
| 11 | Embedding price unknown | Report calls, not rupees | none |
| 12 | New log events versus 13.2 and 16.2 | Widen the one sink and rebuild 13.2 and 16.2 | A second sink, which leaves 13.2 silently incomplete |
| 13 | Module 10's gate | Keep `make smoke-chat`. `smoke-desk` is 10.6's proof and stays out of `smoke-all` | Add `smoke-desk` to the gate |
| 14 | The Desk page and the Chat page | Both. The Desk is the employees' front door; the Chat page stays for the course's document questions; the gate covers both | Retire the Chat page for employees, which would re-cut Module 10 |
| 15 | Known-conflict notes (LV-01 and LV-07 against the OSH Code, `acme/hr_policy_2026.md:19-25`, `acme/osh_code_2020.md:1537-1548`) | Ship two acme entries in `tenant_settings/{t}.clause_notes` with G10-g, worded "the OSH Code gives workers these rights; whether they apply to your role is a question for the People team" | Leave the handbook desk showing the handbook only |
| 16 | Multi-part answers | Built; `desk_max_parts` 1 until the multi-intent rows pass | On from the start |
| 17 | Chips | Server-side chip ids in `DeskState` | HMAC-signed hints with a key |
| 18 | 10.6 runs past 90 minutes | Split: 10.6 "Label documents by class on stored data" (the registry, the relabel, list filters, `authority_rate` offline), then 10.7 "Route each question to one specialist agent" (the router, the graph, the Desk page, the route eval). 63 lessons without gap decision 1, 66 with it (section 2.4); both titles are proposed. The Google Chat door adds about 20 minutes (an estimate) and makes the split more likely | Keep one page and move the optional BigQuery read and the test-split run to pointers |
| 19 | Gap decision 1's reserved 10.5 split of G2 is taken | The Desk lessons become 10.6 and 10.7 | none |
| 20 | No demand evidence: the corpus is synthetic | The kit ships shadow mode and `desk_daily`; the review sample and the demand measures are a pilot follow-up outside this repository | none |
| 21 | Personal-record questions dominate | out_of_scope names the HRMS link and offers a case; a pilot decides on a connector | none at launch |
| 22 | Draft expiry cannot be shown live | Tested offline only | A lab-only TTL setting, which `Makefile:353` would clear |
| 23 | POSH text cannot be graded offline, because the Act is a scan | Template-only POSH route; the Act's sections are checked against the primary source before shipping | none |
| 24 | chat-sa's project-wide `datastore.user` | Accepted, as in G2; later, roles in a separate Firestore database | none now |
| 25 | Quoted lines churn as the gap plan lands first | Re-derive with `check_lesson.py` in every pull request; new modules, one install line each | none |
| 26 | The Desk's place in the gap plan's phase order (section 3.2) | (a) The Desk is its own track: each Desk pull request waits only for its "Depends on", G3 starts after G1, and each Desk pull request after G3 adds its own spans | (b) The Desk holds gap phases 4 and 5 until the 10.6 page merges |
| 27 | The retrieve-only path for agent mode (section 4.6) | `/v1/passages` as its own pull request, G10-p, right after G6-a; PR #72's decision 14 is edited to match | Fold `/v1/passages` into G6-a, which adds 10.4's declaration change there; or gap decision 14's flag on `/v1/query`, which changes `query()` lines 5.1, 5.3 and the 6.x pages quote |
| 28 | The author's lane labels between M1 and M5 | Relabel for the Desk proofs, `RESET=1` for rehearsals of 5.1 and 10.3, and relabel for good at M5 | A second lane for the Desk proofs |
| 29 | The Google Chat door (section 4.11a) | Build it as G10-j: a separate bridge service, `documind-gchat`, direct messages only, with a per-tenant `desk_gchat` flag that defaults to off. It is a post-launch second door onto `/v1/desk`, with its own milestone, M6a; no earlier milestone waits for it | The Desk page only |
| 30 | The Workspace prerequisite, and Slack as the fallback | The author's own Business or Enterprise Google Workspace account with Google Chat, which W2 and W3 list as the prerequisite, on a billing-enabled project (W3). Personal Gmail is treated as unsupported; that is inferred from the prerequisite, and no read page says so. The Workspace's Google Chat settings must let users use Chat apps (not researched). Visibility is up to five named people or Google Groups (W2); whole-domain visibility and hosting the app in a project outside the Workspace organisation are unconfirmed. Where a company has no Business or Enterprise Workspace, Slack is the fallback, with the same bridge shape (verify the platform's signed request, map the sender's email to the roster, call the Desk as an allow-listed delegate, reply later). It is not built, and Slack was not researched for this plan | Build the Slack bridge first |
| 31 | The Chat app model | The Workspace add-on model: W3, Google's HTTP quickstart for Chat apps, is filed under add-ons; its caller is `service-NUMBER@gcp-sa-gsuiteaddons.iam.gserviceaccount.com` (W11, read, for add-ons in general; W13, a third party, for Chat), which binds each request to this project (an inference from W11: the address carries this project's number). The normaliser also reads the classic shape. Which model Google recommends is on a page seen only as a search result, and how the configuration page selects the model is unconfirmed (section 4.11b) | The classic interaction-event model with the "HTTP endpoint URL" audience, the only one W1 allows on Cloud Run functions and the only one `iap.bearer_email` can verify. The invoker binding and `GCHAT_CALLER` become `chat@system.gserviceaccount.com`, `callers_in` learns that address, and the synchronous reply is the classic message instead of the `hostAppDataAction` wrapper. The request then no longer binds to this project, because every Chat app calls as that one account, so the roster refusal is the only guard (an inference from W1). The invoker grant may also be refused under domain-restricted sharing (`terraform/budget.tf:59-63`, an inference). The "Project Number" audience does bind to the project, but its self-signed token (W1) fails `iap.bearer_email` (`shared/iap.py:160-161`) and, by inference, Cloud Run IAM. It would need an allow-unauthenticated service and a second verifier against Chat's certificate URL with an `iss` check (W1), which the kit has nowhere, so it is not proposed |
| 32 | The delegation header (research report, section 9, item 5, and section 11.2, risk 13; section 1.2 of this plan) | Narrowed and resolved for the chat service. `documind-chat` honours `X-DocuMind-Principal` only from `documind-gchat-sa`, only on the Desk's employee routes, only for a human on a roster, and only for a tenant with `desk_gchat` on (design A, section 4.11a). rag-api's header stays unbuilt: a delegated turn reaches rag-api as `documind-chat-sa`. After the probe, if Chat events carry the user's Google-signed ID token, the Desk also verifies it (design A+), which limits a compromised bridge to people who messaged it; that token's audience is the add-on's client ID, a named exception to the audience rule of `shared/iap.py:23-29`. The token is expected to be absent, because W2's configuration fields include no OAuth scope (section 4.11a, unconfirmed item 2) | A+ only, which waits on the probe; rag-api's header now, which Phase E needs and the Chat door does not; no delegation, and so no Chat door |
| 33 | The sender's email may be missing from Chat events (W14) | Probe first (G10-j's lane proof, step 3). If the email is absent, use the user's ID token when present (row 32). If both are absent, G10-j adds a Directory API lookup of the Chat user id, through a custom Workspace admin role that a Workspace administrator assigns to the bridge's account (W14), before the demo, at about two more days | Stop the Chat door until Google documents the email in events |
| 34 | Where the Chat door is taught | Inside Levels 1 to 4 of 10.6, in their rising order (10.7 after Desk decision 18's split), by its own content pull request after G10-j (section 4.13), about 20 minutes, with a proof every learner can reach (`make smoke-gchat`). No lesson count changes, and the first 10.6 page does not wait for G10-j | In the first 10.6 page, which makes that page, M6 and section 1.3's item 1 wait for G10-j and the Workspace account (row 30). 14.4's worked lane extension ("one lane extended on the learner's fork", `plan/course-plan-v5-story-2026-09-22.md:209`): nothing is re-cut, but the files wait in `deploy/UNOWNED.md` until Module 14 exists. A scene in 12.x is not recommended, because 12.1 to 12.3 are MCP and A2A lessons and the gap plan's 12.4 and 12.5 are the handoff and injection, so it would re-cut them against their titles. A new Core lesson adds one lesson and 1.5 hours |
| 35 | Posting answers later without a key | Application Default Credentials with the `chat.bot` scope, then self-impersonation, whose self-grant is the one exception to row 38's no-minting rule; never a downloaded key (`terraform/org_policy.tf:1-9`). If neither works, or an add-on-model app cannot post through the Chat API, the sync-only path (`GCHAT_ASYNC = False`, a 25 s budget), and a cold Desk gets "could not reach the HR Desk" | A service-account key as W10's guide downloads, which the kit refuses |
| 36 | Hooks for the Chat door in earlier Desk pull requests | Take them if row 29 is decided before G10-e merges. G10-e: `documind-gchat-sa` in `desk.tf` and in the chat invoker loop, the minting half of the delegate checks in `check_authz.py`, the `_principal` indirection, a client token on the POSH create, and `via` on the principal and the case record. G10-g: `via` and `delegate` on the `desk` row, and the case offer in a posh response. G10-i: the refused-delegation alert. Then G10-j rebuilds no page | Without them, G10-j rebuilds 10.1 and 13.2, and 10.5 wherever a quoted line moves |
| 37 | The bridge's duplicate claims | A separate Firestore database, `documind-gchat`, with `roles/datastore.user` conditioned on that database, so the bridge holds no role on the default database (unconfirmed that the condition validates) | No claims: the `client-` message id alone keeps one post per question, a Chat retry may cost one more Desk turn, and Pub/Sub's one-hour retention bounds the retries in place of the fifth-attempt card. Never project-wide `roles/datastore.user`, which would let the bridge write rosters and roles |
| 38 | Who can speak for everyone, and the audit of it | `documind-gchat-sa` speaks for every rostered person of every tenant with `desk_gchat` on, and so does anyone who can mint as it, act as it, or publish to `documind-gchat-work`. No person and no Google agent may mint as it; its own self-grant is the one exception, taken only if the probe needs it (row 35). Pub/Sub mints only as `documind-gchatpush-sa`, which is not a delegate, and `/work` accepts only pushes from `documind-gchat-push`. Only the bridge publishes to the topic. `check_authz.py` asserts all of this, from G10-e on with row 36's hooks. The `desk` and case rows carry `via` and `delegate`, and every refusal of a caller writes a row and fires an alert. Known weakness: a project Owner or Editor can still deploy code as the account or publish to the topic, so the delegate is only as trustworthy as the lane's owners, as with chat-sa's `datastore.user` (row 24). If the probe finds `outsider_lists_spaces` true, anyone who can mint as any service account in the lane project can also post as "HR Desk"; the remedy, recorded as a follow-up, is to host the Chat app's configuration in a project of its own that holds only the bridge and its accounts | An audit-bucket event for every delegated call, which the research report's section 9, item 5 asks for, and which adds a literal emitter and rebuilds 8.3 |
