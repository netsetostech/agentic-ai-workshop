"""Reviewed experiment boundaries, in main-HTML order, for the whole course.

Teaching boundaries come from the actual numbered HTML headings. The overrides
below preserve lifecycle roles and manual steps that Copy buttons cannot convey. Preparation, final restoration,
conditional repairs and optional extensions have separate directories. Lesson
1.1 has its own authored implementation and retains its authored checks.
"""

# Operations whose source position or generic 'Do it' label hid their lifecycle role.
REQUIRED = {
    # "Upload only if the original checksum still passes" is a fixture guard,
    # not optional recovery. The exact-byte restore must precede the reuse read.
    '1.8': [21],
}
CLEANUP = {
    "1.5": [37,5], "1.8": [44], "2.1": [29], "4.1": [44,5], "4.4": [26,5],
    "4.8": [31,5], "6.2": [31,5], "6.3": [30,5], "6.4": [22,5],
    "5.2": [23,5,8], "12.3": [31,34,5],
    # 10.8: the injected vendor note withdrawn and the chat's two switches off. Run by finish.py after a failure too:
    # on 22 October 2026 a failed demo_07 left the note current in acme and AGENT_FENCE/AGENT_SCRUB on.
    "10.8": [83,5],
    # 10.11: the drill's fault restored and the chat verified, by finish.py after a failure too: on 22 October 2026 a
    # failed rollback left CHAT_MODEL=gemini-3.6-flsh serving all of documind-chat's traffic.
    "10.11": [19,21,5],
    # 11.4: acme's handbook put back to version 1, by finish.py after a failure too: on 22 October 2026 a stopped run
    # left the broken revision 2 answering every acme handbook question.
    "11.4": [20,5],
    # 0.2: the committed golden row back, by finish.py after a failure too: on 23 October 2026 a stopped run left lk-06
    # loosened in the clone.
    "0.2": [36],
}

# Optional sections that stand on their own. An optional file requires the last required file before it, unless its
# section is named here: "setup" means only the lesson's setup/prepare.py, a number means that section's optional file.
# Lesson 17's v3 path (the closing optional steps of 17.1, 17.2 and 17.3) builds, tunes and shows v3 without the v2
# steps it sits beside on the page, so a workshop can run it on its own.
OPTIONAL_AFTER = {"12.1": {7: "setup"}, "12.2": {7: "setup"}, "12.3": {7: "setup", 8: 7}}

# Marked optional on the page, or conditional repairs. These never run implicitly
# as part of a required demo. Every remaining source window must be assigned.
# A fourth element, when present, is the file's purpose; the default names the category.
EXTRAS = {
    "1.5": [("optional", "large_pdf_down_the_batch_lane", [31],
             "Optional, and it costs money (the page's own box): join the CGST and IT Acts into a 270-page PDF and upload it "
             "to acme. The worker queues it for the batch lane. Where the batch job is declared it parses all 270 pages at once: "
             "about Rs 34 on the OCR processor or Rs 230 on the Layout Parser, plus embeddings. The page leaves the PDF in "
             "acme's uploads. Decide before you run it.")],
    "1.7": [("recovery", "recover_missing_note", [27])],
    "1.8": [("recovery", "inspect_incomplete_restore", [25]),
            ("optional", "incomplete_undo", [26,27,28,29]),
            ("optional", "nightly_job_and_backfill", [35]),
            ("optional", "module_validation", [39]),
            ("recovery", "repair_module_baseline", [40]),
            ("recovery", "run_isolated_reindex_smoke", [42])],
    "2.1": [("recovery", "repair_deployed_index_id", [5])],
    "4.1": [("optional", "generate_evaluation_candidates", [41])],
    "6.4": [("recovery", "repair_replay_reader", [16])],
    "10.4": [("optional", "google_chat_door", [8],
              "Optional: turn the Google Chat door on. Plan with GCHAT_DOOR=true beside DESK_JOB=true and apply, deploy "
              "chat again so documind-gchat-sa may call it, then make deploy-gchat. Keep GCHAT_DOOR=true on every later "
              "make plan and make up. The Workspace part, the door's smoke and its rows need it."),
             ("optional", "hr_desk_in_google_chat", [25],
              "Optional, and only with the door on, a Business or Enterprise Google Workspace account and a Chat app you "
              "configured in the Google Cloud console: deploy the Google Chat bridge again so it admits the app's add-on "
              "agent, put your Workspace address on acme's roster, switch desk_gchat on for acme, and print the two "
              "questions to send the HR Desk app. Without Workspace, skip it: the page's expected conversation shows what "
              "it does, and make smoke-gchat proves the door's refusals with the door on."),
             ("optional", "google_chat_door_refusals", [62],
              "Optional, only with the door on, and no Workspace needed: make smoke-gchat's four refusals and the door's "
              "latest rows. It refuses on a lane whose last apply had the door off."),
             ("optional", "google_chat_door_rows", [73],
              "Optional, only with the door on: the desk rows that came through the Google Chat door, then the bridge's "
              "claims in its own Firestore database; reads only.")],
    "5.3": [("recovery", "grant_the_build_account", [13],
              "Only if the build stopped at storage.objects.get (the page's box): once, as a project owner, grant the "
              "project's default build account read access to its source in the PROJECT_cloudbuild bucket, push access "
              "to the documind repository and log writing. Then run the build and deploy again.")],
    "7.2": [("recovery", "repair_graph_baseline", [25])],
    "10.8": [("optional", "the_peer_row_at_a_local_peer", [53],
              "Optional, the author's shell: three tabs at once - the kit's MCP server in the local profile, the kit's "
              "peer against it on your own Gemini credentials, and the attack runner's peer row - so it does not run as "
              "one script. The page's recorded row shows what it does."),
             ("optional", "the_peer_against_the_poisoned_server", [75],
              "Optional, the author's shell: the kit's peer on your machine against the poisoned server, in three tabs, with "
              "TOOL_PINS off and then on. The pin checks before it prove the same refusal without a model call.")],
    "10.10": [("optional", "the_authors_live_run", [70, 72],
               "Optional, the author's run: the live loop on a model-only Gemini API key the author creates for the run and "
               "deletes after it, typed at the prompt and never echoed, under a rupee cap from the batch-1 dry run; then the "
               "reviewer on its patch. It bills that key's project. Without such a key, skip it: the page's recorded run "
               "shows what it does, and the required steps before it prove the loop refuses to start without one.")],
    # 12.4's "Red" path, after a promote on a green gate: on 23 October 2026 it ran anyway and reverted the version that
    # had just gone live, and put a v3 candidate under the candidate tag.
    "12.4": [("recovery", "the_gate_red_revert_the_version", [56],
              "Only when make gate was red: no promote, the commit with the new version reverted, and documind-api's "
              "template back to v3. A green gate promotes in the file before, and nothing here runs.")],
}

# Instructions requiring a human action outside Python, read from the main page.
# These pauses sit INSIDE the right experiment, before its dependent operation.
MANUAL = {
    ("2.5",10): "In the deployed UI's Chat page, signed in as yourself, ask: How much can I claim per trip for domestic travel? Wait for the cited answer, then type done to read the API's log for the minutes since.",
    ("3.2",6): "In the deployed UI's Chat page, signed in as yourself, ask exactly: I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve? Wait for the cited answer, then type done to read its stream row from the API's log.",
    ("1.5",22): "The poison retries are asynchronous. Wait a few minutes after the drill, then type done to read its retry records. This does not prove a dead letter has arrived.",
    ("1.5",35): "Dead-letter delivery can take about an hour. Inspect the drill's dead letter only once it has landed. Stop here and rerun this demo later; the steps already completed will not run again.",
    ("3.8",17): "In the ACME UI, Documents -> Upload: choose ~/pune_visitor_rules.md created in the previous step, then Index documents. Refresh until indexed. If your browser runs elsewhere, download the file from the workstation first; in WSL, the browser's file picker opens \\\\wsl.localhost\\<your distribution>\\home\\<you>\\. A pasted copy is fine: the demo follows the version your upload wrote. Type done after the UI checkpoint.",
    ("3.8",23): "In the deployed UI Chat, ask the visitor-badge question from this lesson and wait for the cited answer. Type done to compare the browser and operator API records.",
    ("3.8",28): "Open the answer's citation/source in the UI and inspect the signed link. Type done to render and inspect the transcript from Python.",
    ("4.5",14): "Open evals/reports/judge_labels.csv in a spreadsheet or editor. For every row read the context, then the answer, then the question, and write yes or no under both groundedness and answers_the_question, blind: before reading any other reader's labels. Save it as CSV with every column kept. Type done to check it against the frozen set.",
    ("4.5",25): "Only while the kit has no author's sheet: your colleague fills evals/reports/judge_labels.peer.csv the same way, blind, from the guide alone and without seeing yours. Type done to check their sheet and count your agreement with it.",
    ("4.6",29): "Sign in through the deployed UI as the lesson's rostered person and submit the example question. Type done before inspecting the person's assertion path.",
    ("5.6",20): "In the deployed UI, signed in as yourself, choose Desk: acme has the gate's rules with nothing switched on, and your roles are read on every request, so there is nothing to wait for. Paste the sentence the previous section printed into Tell the Desk and Send: the fixed reply comes back and the POSH card opens under Raise a case. Choose Hyderabad and yourself, and Create a confidential record; then, under What is it about?, raise a grievance, check it and Send; in Your inbox, change the grievance to Acknowledged and Update. Type done to run the gate on your machine and through both doors.",
    ("10.4",25): "Only with a Business or Enterprise Google Workspace account. First configure the Chat app in the Google Cloud console, on your lane's project (Google Chat API, Configuration), as the page's step 4 lists: the name HR Desk, the add-on model, the HTTP endpoint URL https://documind-gchat-NUMBER.REGION.run.app with no trailing slash, and the app available to your Workspace address. Set WS in this cell to that address. Type done to deploy the bridge again, roster the address on acme and switch the door on; then, in Google Chat, send HR Desk the lk-06 question and the POSH line it prints.",
    ("10.10",11): "Write the body spec.md describes in $WS/shared/desk_calc.py (the workspace the first cell printed), replacing the hurried one: by hand, or with Gemini CLI started in the workspace with no flags, which asks before every edit and command. Approve each edit to the function, and decline anything that reaches for gcloud, git or the network. Type done to run the fast test and both oracles: the strong one passes only for a body that does what spec.md says.",
    ("10.4",34): "Wait five minutes after make desk switched acme's router on: the chat service reads the switches within 60 s and the example index within 5 minutes. Then open the deployed UI in a new tab, so the Desk starts a new conversation, sign in as yourself and choose Desk. Under Ask the Desk, ask What is the notice period? first, and if the reply asks which desk you mean, press the handbook's button. Ask the lk-06 question the previous section printed: one handbook answer with its citations. Ask the lk-17 question: a statute answer with a line for each Act it cites. Ask the lk-10 question: it is turned away at once, with a Raise a case button. Type done to run the router's rules on your machine.",
    ("6.8",11): "In the deployed UI's Chat page, signed in as yourself, set Brain to langgraph and ask: After how many years of continuous service is gratuity payable? When the answer is in, ask: Is it payable to a contract employee? Type done to read your thread back from the checkpointer: without the two questions there is no thread, and every later step of this lesson has nothing to read.",
    ("4.8",12):"Open the deployed admin DLP tab and inspect the synthetic note's findings. Type done to compare them with the source fields printed next.",
    ("11.6",22): "The next read is Cloud Monitoring fifteen minutes after make off. Stop and rerun this demo later if you like; completed shutdown steps will not run again. After done, it waits only for whatever is left of the fifteen minutes.",
    ("9.4",20): "The next read is Cloud Monitoring at least ten minutes after make off. Stop and rerun this demo later if you like; completed comparison/shutdown steps are retained. After done, it waits only for whatever is left of the ten minutes.",
}

# An earlier lesson creates these inputs; this dependency is not an invitation to
# rerun its mutation automatically. The preparation documentation names it.
PREREQUISITES = {
    "1.2": "Module 0 deployment and the seeded HR handbook/Code on Wages corpus.",
    "1.3": "The seeded original handbook and live ingest worker; this lesson temporarily reissues it.",
    "1.4": "Module 0's deployed Vector Search index, Firestore indexes and audit/mirror configuration.",
    "1.5": "Lesson 1.4's upload evidence; batch-job availability determines whether a large PDF remains queued.",
    "1.6": "The original handbook and unchanged golden set; the live gate deliberately fails for revision 3.",
    "1.7": "The handbook history from 1.6 and the smoke note from 1.4. Use the conditional repair only if the note is absent.",
    "1.8": "A deployed lane. This lesson creates its own smoke-note fixture and does not depend on ~/lesson34_note.md.",
    "2.1": "The intended Terraform state/index deployment; preflight rejects empty or mismatched endpoint IDs.",
    "2.2": "Loaded invoice and HR fixtures, a hybrid-capable index, and the API's actual serving configuration.",
    "2.3": "The loaded HR/PDF corpus and Ranking API access. Saved answer/pool files are produced in this lesson.",
    "3.8": "An ACME browser login through IAP and a deployed Streamlit UI, API and ingest lane.",
    "4.1": "A clean evaluation working set. The lesson backs up its four editable files and restores the exact originals.",
    "4.2": "The live deployed lane, the golden set, and the CI account/access needed by the source's optional CI inspection.",
    "4.4": "Lesson 4.2's judge environment and a single baseline revision; no other lesson should own the candidate tag.",
    "5.4": "The deployed chat lane from 5.1; framework dependencies are installed by this lesson's preparation.",
    "5.5": "The deployed chat lane; the framework failure harness runs in its own lesson venv.",
    "5.7": "The deployed chat lane and access to the example models; adapters use a separate framework venv.",
    "5.6": "Module 5's deployed chat lane and lesson 1.1's roster. Step 3 applies the Desk's Terraform, redeploys rag-api, the UI and the chat service, declares the hourly overdue job, and loads acme's queues and roles, leaving desk_gate unwritten so acme has the gate's rules and no model check; keep DESK_JOB=true on every later plan, and on make reconcile-job and make batch-job.",
    "10.4": "Lesson 5.6's Desk: acme's case queues, the gate's rules for acme (desk_gate unwritten), your roles, and token rights for the eval accounts. Step 3 pulls the kit, rebuilds and redeploys rag-api, the UI and the chat service, then applies its Terraform with DESK_JOB=true (optionally with GCHAT_DOOR=true too, then the door's bridge with make deploy-gchat), rosters evalglobex and evalleaver, applies the doc_type registry to acme, zeta and globex, builds acme's and zeta's example index, and switches acme's router on and globex to the statute desk alone; step 8 gives zeta its queues and turns its router to shadow, then on; zeta keeps the gate's rules.",
    "6.5": "Module 5's deployed chat lane and the framework venv created during preparation.",
    "6.6": "A lane with the durable conversation store configured; read configuration before inspecting SQL.",
    "6.7": "The durable conversation storage from 6.6; the example redeploys the chat service.",
    "5.2": "The deployed retrieval API for local MCP calls; preparation installs fastmcp in the selected interpreter.",
    "11.4": "The original HR fixture; the controlled version change is undone before completion.",
    "11.5": "A deployed usage/audit lane and the intended alert notification channel; inspect the alert plan before apply.",
    "7.2": "The Firestore graph from 7.1 and an explicitly configured Spanner graph for the alternative path.",
    "7.3": "Configured RAG Engine/Vertex AI Search mirrors and tenant residency policies that permit those regions.",
    "7.4": "The managed mirrors from 7.3 and the original Zeta handbook; update and withdrawal are intentional.",
    "7.5": "Configured media ingestion services; this lesson builds its own synthetic video with make media before indexing it.",
    "7.6": "The deployed Studio/voice capabilities described on the page; browser/microphone permissions remain user actions.",
    "12.1": "Baseline evaluation evidence and the kit's sanitized training examples; no tuning job is submitted here. The optional v3 file (step 7) calls gemini-3.1-pro-preview once a chunk.",
    "12.2": "The reviewed sanitized datasets from 12.1. Submission creates a billed tuning job; resume polling the saved job instead of resubmitting. The optional v3 job (step 7) needs 12.1's v3 and is a second billed job.",
    "12.3": "The tuned endpoint from 12.2, its ~/poll172.log and the uncontaminated evaluation baseline. The optional steps 7 and 8 need the v3 endpoint in ~/poll172v3.log (12.2's step 7).",
    "9.1": "The intended gateway backend services and IAM configuration.",
    "9.2": "The supplied model/tokenizer when using that path, or the page's stock-model alternative; GPU deployment is billed.",
    "9.3": "Read the vLLM/GKE definitions even if the optional GKE cluster has not been deployed; absence is not a serving comparison.",
    "9.4": "Actual configured comparison backends and monitoring read access; shutdown does not instantly imply zero instances.",
}
