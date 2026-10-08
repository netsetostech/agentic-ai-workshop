# Lesson 1.1: Understand source, tenant, page and chunk contracts

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_tenant_something_you_are_never_something_you_send.py](demo_03_tenant_something_you_are_never_something_you_send.py) | Tenant: something you are, never something you send |
| 4 | [demo_04_source_the_object_path_is_the_document_s_identity.py](demo_04_source_the_object_path_is_the_document_s_identity.py) | Source: the object path is the document's identity |
| 5 | [demo_05_version_the_bytes_decide_and_the_same_file_in_two_tenants_proves_it.py](demo_05_version_the_bytes_decide_and_the_same_file_in_two_tenants_proves_it.py) | Version: the bytes decide, and the same file in two tenants proves it |
| 6 | [demo_06_page_and_section_where_inside_the_document.py](demo_06_page_and_section_where_inside_the_document.py) | Page and section: where inside the document |
| 7 | [demo_07_chunk_the_unit_a_question_can_find.py](demo_07_chunk_the_unit_a_question_can_find.py) | Chunk: the unit a question can find |
| 8 | [demo_08_why_it_is_built_this_way_the_failures_behind_each_rule.py](demo_08_why_it_is_built_this_way_the_failures_behind_each_rule.py) | Why it is built this way: the failures behind each rule |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

Module 0 deployment and seeded HR/Code on Wages documents. Section 5 requires the exact amendment uploaded in the ACME UI before Run. Later sections use those saved generations.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/finish.py](setup/finish.py) — Run this before changing lessons or deleting local results. Both restoration
operations are attempted even if one fails. Fixture uploads and roster entries
remain as the HTML intends; this file deletes no documents, chunks or evidence.
It can also restore a backend saved by the old 13-file lesson 1.1 sequence.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

Use the existing rag-shell-venv interpreter after workshop_demos/setup/bootstrap.py.
Project/region come from setup/config/settings.local.json, not shell exports.
This saves ACME's existing retrieval backend and pins it to Vector Search.
If SEMANTIC_CACHE=on, it temporarily disables that API-wide setting by creating
a Cloud Run revision; setup/finish.py restores it and the backend, even after a
failed demo. No cache entries are deleted. Keep the local results directory.

**`demonstrate(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

Save settings before mutation so a partial preparation remains recoverable.

Example: demonstrate(session)

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Retain the authored contract assertions and exact-generation checks.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_tenant_something_you_are_never_something_you_send.py

Write the kit roster, compare member/outsider/anonymous calls, then read membership.
The roster changes membership/policy; the member query can incur model work.
Expected: admitted member; API JSON refusal for an outsider; Cloud Run refusal without a token.

**`establish_roster(session)` — Tenant: something you are, never something you send / Call it: the roster from the shell, and two REST calls**

HTML 3: use the kit's actual roster command, including its documented policies.

Example: establish_roster(cloud) runs after the preceding function in demonstrate().
Failures propagate; compare the saved/printed evidence with this section.

Operation: bash — run in the operator shell.

IDE adaptation: Retain the authored contract assertions and exact-generation checks.

**`compare_access(session)` — Tenant: something you are, never something you send / Call it: the roster from the shell, and two REST calls**

HTML 3: identical bodies, three identities; the refusal body identifies the gate.

Example: compare_access(cloud) runs after the preceding function in demonstrate().
Failures propagate; compare the saved/printed evidence with this section.

Operation: bash — run in the operator shell.

IDE adaptation: Retain the authored contract assertions and exact-generation checks.

Expected shape, not a promised result:

```text
...,"latency_ms":1840,"stages":{"retrieval_backend":"vector",...},"cache_hit":"none"}
HTTP 200
{"detail":"not a member of this tenant"}
HTTP 403
<html><head><meta http-equiv="content-type" content="text/html;charset=utf-8">
<title>403 Forbidden</title> ...
HTTP 403
```

**`inspect_membership(session)` — Tenant: something you are, never something you send / Read it in Firestore**

HTML 3: read the forward roster, UI reverse lookup and tenant settings.

Example: inspect_membership(cloud) runs after the preceding function in demonstrate().
Failures propagate; compare the saved/printed evidence with this section.

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

IDE adaptation: Retain the authored contract assertions and exact-generation checks.

Expected shape, not a promised result:

```text
documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com | {'email': 'documind-mcp-sa@...', 'added_at': DatetimeWithNanoseconds(...)}
documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com  | {'email': 'documind-ui-sa@...', 'added_at': DatetimeWithNanoseconds(...)}
you@your-company.com                                        | {'email': 'you@your-company.com', 'added_at': DatetimeWithNanoseconds(...)}
tenant for you: ['acme']
{'data_region': 'any', 'data_region_set_at': DatetimeWithNanoseconds(...)}
```

### demo_04_source_the_object_path_is_the_document_s_identity.py

Read one HR source through Storage, the sources API and the Firestore ledger.
This section reads cloud state; it does not upload a new file.
Expected: tenant-scoped rows with matching indexed generation, document key and URI.

**`trace_source(session)` — Source: the object path is the document's identity / Call it: the bucket, then the API**

HTML 4: consume complete responses before printing selected rows; no head/pipefail.

Example: trace_source(cloud) runs after the preceding function in demonstrate().
Failures propagate; compare the saved/printed evidence with this section.

Operation: bash — run in the operator shell.

IDE adaptation: Retain the authored contract assertions and exact-generation checks.

Expected shape, not a promised result:

```text
gs://documind-ai-YOUR-ID-uploads/acme/annual_report_2026.md
gs://documind-ai-YOUR-ID-uploads/acme/code_on_wages_2019.pdf
gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md
...
1758540123456789    40096    text/markdown
{
    "tenant_id": "acme",
    "versions": 18,
    "fingerprint": "3fd2258b1264f744",
    "last_event": "ingest_ok",
    "data_region": "any",
    "sources": [
        {
            "name": "acme/hr_policy_2026.md",
            "status": "indexed",
            "doc_key": "acme_497809ff...",
            "generation": "1758540123456789",
            "chunks": 283,
            "reused": 0,
            "embedded": 283,
            "retired": 0,
            "effective_from": null,
            "embedding": "text-embedding-005@1",
            "indexed_at": "2026-09-22T...",
            "mirrored": {}
        },
        ...
```

### demo_05_version_the_bytes_decide_and_the_same_file_in_two_tenants_proves_it.py

Upload evals/demo/gratuity_amendment_2026.md through the ACME UI first.
This file verifies those exact bytes, uploads them to Zeta, waits for both saved
generations and inspects their claims. Existing identical fixtures are reused;
different bytes are not overwritten. The uploads remain after cleanup.
ACME_UPLOAD="operator" is a labelled alternative, not proof of the UI path.
Expected: equal content hashes, distinct tenant keys, indexed claims and current rows.

**`upload_same_bytes(session)` — Version: the bytes decide, and the same file in two tenants proves it / Do it: one file, two tenants**

Check ACME first so a missing UI step cannot leave an unexplained Zeta-only run.

Example: upload_same_bytes(cloud) runs after the preceding function in demonstrate().
Failures propagate; compare the saved/printed evidence with this section.

Operation: bash — run in the operator shell, in $DEMO_ROOT.

Manual action: Upload evals/demo/gratuity_amendment_2026.md in the ACME UI before Run. ACME_UPLOAD="operator" is an explicitly labelled alternative.

IDE adaptation: Retain the authored contract assertions and exact-generation checks.

Expected shape, not a promised result:

```text
5b62d236e0c1...  evals/demo/gratuity_amendment_2026.md
acme    acme_5b62d236e0c1...    3    3
zeta    zeta_5b62d236e0c1...    3    3
```

**`inspect_indexed_versions(session)` — Version: the bytes decide, and the same file in two tenants proves it / Read it in Firestore**

Upload completion is not indexing; wait for matching ledger, claim and chunks.

Example: inspect_indexed_versions(cloud, versions) runs after the preceding function in demonstrate().
Failures propagate; compare the saved/printed evidence with this section.

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

IDE adaptation: Retain the authored contract assertions and exact-generation checks.

Expected shape, not a promised result:

```text
acme indexed 3 acme gs://documind-ai-YOUR-ID-uploads/acme/gratuity_amendment_2026.md
zeta indexed 3 zeta gs://documind-ai-YOUR-ID-uploads/zeta/gratuity_amendment_2026.md
```

### demo_06_page_and_section_where_inside_the_document.py

Ask the Markdown and PDF questions, resolve every citation to its current row,
then inspect section/page locators. The two questions incur retrieval/generation work.
Expected: citations refer to the intended seeded sources and agree with stored page fields.

**`inspect_citations(session)` — Page and section: where inside the document / Call it: a question, and the page on each citation**

HTML 6: ask both source questions and resolve each citation back to Firestore.

Example: inspect_citations(cloud) runs after the preceding function in demonstrate().
Failures propagate; compare the saved/printed evidence with this section.

Operation: bash — run in the operator shell.

IDE adaptation: Retain the authored contract assertions and exact-generation checks.

Expected shape, not a promised result:

```text
A confirmed employee at grade E3 or above serves a notice period of 60 days [Source 1].
acme:497809ff...#1 hr_policy_2026.md page None | NP-03 — Notice period Confirmed employees at
acme:497809ff...#2 hr_policy_2026.md page None | PB-02 — Probation ...
```

**`inspect_locators(session)` — Page and section: where inside the document / Read it in Firestore**

HTML 6: section labels locate Markdown passages; page numbers locate PDF passages.

Example: inspect_locators(cloud) runs after the preceding function in demonstrate().
Failures propagate; compare the saved/printed evidence with this section.

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

IDE adaptation: Retain the authored contract assertions and exact-generation checks.

Expected shape, not a promised result:

```text
hr_policy_2026.md -> 283 current chunks
     0  locator=preamble   page_start=None  section=None
     1  locator=NP-03      page_start=None  section=NP-03 — Notice period
     2  locator=PB-02      page_start=None  section=PB-02 — Probation
     3  locator=LV-01      page_start=None  section=LV-01 — Earned leave
     ...
code_on_wages_2019.pdf -> 67 current chunks
     0  locator=p1-0       page_start=1     section=None
     1  locator=p1-1       page_start=1     section=None
     2  locator=p2-0       page_start=2     section=None
```

### demo_07_chunk_the_unit_a_question_can_find.py

Compare accepted and refused filters, then compare the exact ACME/Zeta versions
created in section 5. Queries can incur model work; the remaining operations read state.
Expected: disjoint tenant chunk IDs, equal hash multisets and refusal of tenant_id as a filter.
The doc_type=policy empty match is valid only for the stock unknown-stamped corpus.

**`compare_filters(session)` — Chunk: the unit a question can find / Call it: a filter the contract allows, one that finds nothing, and one it refuses**

HTML 7: an allowed field can match nothing; tenant_id is never an allowed filter.

Example: compare_filters(cloud) runs after the preceding function in demonstrate().
Failures propagate; compare the saved/printed evidence with this section.

Operation: bash — run in the operator shell.

IDE adaptation: Retain the authored contract assertions and exact-generation checks.

Expected shape, not a promised result:

```text
True ['acme:497809ff...#1', 'acme:497809ff...#2', 'acme:497809ff...#4']
False []
{"detail":"unknown filter key(s) tenant_id; allowed: doc_type, kind"}
```

**`compare_tenant_chunks(session)` — Chunk: the unit a question can find / Read it in Firestore: the twin rows from step 5**

HTML 7: use section 5's exact keys, then compare IDs and the multiset of text hashes.

Example: compare_tenant_chunks(cloud) runs after the preceding function in demonstrate().
Failures propagate; compare the saved/printed evidence with this section.

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

IDE adaptation: Retain the authored contract assertions and exact-generation checks.

Expected shape, not a promised result:

```text
rows: 3 3
ids in common: set()
same hashes: True
tenant_id              acme
doc_key                acme_5b62d236e0c1...
current                True
locator                preamble
chunk_hash             9c1e6f2a...
embedding_model        text-embedding-005
embedding_task_type    RETRIEVAL_DOCUMENT
schema_version         2
id: acme:5b62d236e0c1...#0 | vector dims: 768
```

### demo_08_why_it_is_built_this_way_the_failures_behind_each_rule.py

Run the actual kit validators locally. This extends the section explanation and
verification checklist into Python: rewrapping changes bytes but preserves chunk
identity; a root-level upload event is rejected for lacking a tenant prefix.
No live poison object is uploaded and no worker-log result is claimed.

**`prove_local_contract_rules(session)` — Why it is built this way: the failures behind each rule / Local proofs from the explanation and checklist**

Call the actual kit validators; rewrapping changes bytes but preserves chunk identity.

Example: prove_local_contract_rules() checks whitespace-only rewrapping locally.
Failures propagate; compare the saved/printed evidence with this section.

Operation: Local Python; no network.

IDE adaptation: Retain the authored contract assertions and exact-generation checks.

Expected shape, not a promised result:

```text
Rewrapping retains the chunk hash; a root object is refused.
```

### setup/finish.py

Run this before changing lessons or deleting local results. Both restoration
operations are attempted even if one fails. Fixture uploads and roster entries
remain as the HTML intends; this file deletes no documents, chunks or evidence.
It can also restore a backend saved by the old 13-file lesson 1.1 sequence.

**`demonstrate(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

Attempt each pending restore independently, retaining flags for any failure.

Example: demonstrate(session)

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Retain the authored contract assertions and exact-generation checks.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_1.1_Contracts_WIX.html`. All 36 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `77b8143fc03414b24b415247dcdb9fa88ec56b1b`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
