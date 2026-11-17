# Lesson 3.6: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_3.6_Quote_Checks_WIX.html`, reviewed at blob `57e9f5eb63ef41d359c4f7a586351df4a6732eb6`. Learners read that page on the course site; this guide keeps its prose.

Lesson 3.5 resolved the model's citations and checked one answer's quotes against their rows. This lesson checks a whole source's quotes the way the eval gate can: each quote looked for in the one passage it cites, read back from the same retrieval the answer drew on, with five verdicts. It also treats the prompt that asks for those quotes as a release. Its text has a sha256, its version is a label every answer carries, and a changed text under the old label fails a check that runs offline for Rs 0 and on every push. You will run both quote measures offline, check a source's quotes on your lane, weaken rule 5 in memory and then on a branch, ship it to a candidate that answers as `documind-rag@v4`, compare its quotes with v3's, find its rows, and take it down again.

- A quote is a claim about one passage, and a prompt is a release

- The words: quote, pool, the five verdicts, the three rates, the switch, label, text, registry, candidate

- Before you run anything: set up the shell

- Offline: nine quotes through both measures, and the gate's own lines over a stand-in API

- Your lane: what the UI shows as a quote, then a source's quotes held against their passages

- The prompt's version: the label, the text, its sha256 and the check

- The change in memory: rule 5 weakened on the bench, and the sha256 it would register

- Ship it: v4 on a branch, checked, built, and answering on a candidate

- The rows name the prompt; the candidate taken down, and v4 spent

- Verify it yourself: the checklist

You will learn why a quote is checked against the one passage it cites rather than the whole corpus, what each of `quote_check()`'s five verdicts means, and how a prompt's text is bound to the version label every answer carries. Then you will prove it on your lane: nine quotes offline, a source's quotes on the live revision, a weakened rule 5 in memory and then on a v4 candidate, its quotes compared with v3's, its rows found, and the candidate removed.

### A quote is a claim about one passage, and a prompt is a release

Why a quote is checked where it says it came from, what each place to look can and cannot see, and why a prompt's words carry a version.

A quote says where its words came from. A citation makes two claims: this passage supports the answer, and these are its words. `resolve()` turns the draft's `[Source N]` into a chunk id, a page and a score, one citation a chunk: a passage the draft lists twice keeps its first quote. The quote it copies as the model wrote it, cut to 500 characters, and when the model wrote an empty one it puts the passage's first 500 characters in its place. It does the same for a source the answer cites only in its prose, an `[N]` the draft's list leaves out: the citation is added, and its quote is the passage's opening. Nothing on the request path compares the words with the passage. Rule 5 of the prompt asks for the clause that answers, at most twenty-five words, and the schema describes the field as exact words from that source, but both are requests. So a citation's quote can be the passage's own words, real words from another passage under the wrong number, words the model wrote itself, or the passage's opening standing in for a quote nobody gave. Every caller of `/v1/query` receives it as evidence: the eval gate, the MCP server's `retrieve` tool, and the chat service's agents, which pass the citations on.

Where you look decides what you find. The live gate already looks for each quote somewhere: `judge_citations()` searches the tenant's whole corpus, the text mirrors under `evals/corpus`, and prints `quote_support_rate` as information, not a threshold, because a Doc AI extraction and a pypdf mirror hyphenate differently. The whole corpus is too generous and too strict at once. It passes real words under the wrong source, and it passes a passage's opening that `resolve()` put in for an empty quote or a bare `[N]`, because both are somewhere in the corpus. It fails the generator's own repair, the three dots `_draft()` adds to a quote it cut, and any quote of a PDF whose hyphenation differs from the mirror's. `quote_check()` looks in one place: the passage the citation names, read back from `/v1/passages`, which runs the same retrieval and rerank as `/v1/query` and returns each passage's full text with no model call. That passage is the text the model read, so a quote that is not in it is the model's own doing. It gives one of five verdicts: own, elsewhere, absent, substituted or unread. With `DOCUMIND_EVAL_PASSAGES=1` the live gate reads each answerable row's pool again and prints `quote_passage_rate` beside the corpus rate, still as information.

A prompt is a release, and its version is a label. `SYSTEM` starts every prompt `generate()` sends, with `DATED_RULE` after it when a packed passage carries a date; the two are 604 characters. `config.py` names them `documind-rag@v3`, and the label goes wherever an answer goes: `/version` reports it, every usage row carries its version, the answer cache's scope includes it so that an answer made under one version is never served under another, and `tenant_daily` groups by it. A label is worth that only if it names one text. `prompt_versions.json` maps each label to the sha256 of its text, `make prompt-version` checks the code against it offline, and the same rule runs as a unit test on every push of the learner repository. Change one character and the sha256 changes; keep the label and the check fails, naming the next version and the line to register. A registered line never changes, so `v3` names one text for good.

A sub-editor, and the style guide's control number. A reporter files a story that quotes the council and cites "minute 14". The sub-editor opens minute 14, not the whole archive, and lays the quote over it. Minute 14's words: it stands. Minute 9's words under minute 14's number: a misattribution, true words in the wrong place, which a search of the whole archive would have passed. Words in no minute: the reporter's own sentence in quotation marks. "See the minutes" where the quote should be: nothing was quoted, whatever page is stapled to it. And a minute the archive could not produce that day is not judged, and not passed either.

The reporters write to a style guide with a control number on its cover. Change one word and it is a new issue with a new number, filed beside the old one and never written over it, and every story is stamped with the number of the issue it was written under. When readers complain about last Tuesday's stories, the stamp says which guide was in force. The sub-editor is `quote_check()`, the archive search is `judge_citations()`, the control number is the prompt's version, the filing cabinet is the registry, and the stamp is `prompt_version` on every usage row.

#### The quote check: a citation and its quote against six passages, by quote_check()'s rule

The bench holds a citation as `/v1/query` returns one: the passage it names and the quote it carries. It runs `quote_check()`'s steps in order against six passages of acme's handbook, cut by the kit's chunker and given the ids the ingest worker mints, and prints the verdict and the step that decided it. Beside each case is what `judge_citations()` said about the same quote over acme's whole corpus, 1.9 million characters, when this page was built. The cases are the nine that step 3 runs; type your own quote to see where it lands.

The six passages stand in for the pool `/v1/passages` returns for lk-06's question; on your lane the reranker chooses them, and step 4 reads yours. The ids take the worker's form, `acme:`, the handbook's sha256, then the passage's position, as your lane's do. The rule is ported from `quote_check()` and checked against it on every case when this page was built; the corpus column of a typed quote is exact only when its words are in one of the seven passages this page holds.

#### The version strip: prompt_pin's rule, live, and where the label goes

The strip holds what `make prompt-version` reads: `SYSTEM` and `DATED_RULE` as `generator.py` sets them, `prompt_version` as `config.py` sets it, and the registry. It does not hold the registry's history in git, which `make prompt-version` also reads for the version it offers next (step 8). It hashes the text with the same sha256, prints what `prompt_pin.py` would print, and follows the label to the places the service writes it. The first five cases are the states step 7 walks through; three more are cases the kit's own test checks, and the last is one space.

The sha256 is a JavaScript port, checked against Python's `hashlib` when this page was built, and the verdict lines are `prompt_pin.check()`'s, checked against the script itself on every case. The cache scope is `semantic_cache.scope_of()` for the UI's request, no filters and a top_k of 5. The strip reads nothing of your clone; `make prompt-version` does.

Neither calls a model or your lane. The quotes in the first are written by hand, and what a model quotes for a given pool is steps 4, 6 and 7's business. The second hashes the text in the page; whether your clone's files agree with your registry is what `make prompt-version` tells you, in step 5.

### The words: quote, pool, the five verdicts, the three rates, the switch, label, text, registry, candidate

Fourteen rows, each with the value it takes on your lane.

One distinction to hold: the quote check judges the model's words against the text it read, and the version check judges the code's text against its label. Neither needs a model call. The first is information the gate prints; the second fails the dry run on every push.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson reads the chunk ids of acme's answers and of the passages read back beside them, so point acme at the kit's own index for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; every gate and bench on this page asks as documind-ui-sa.

The shell in the kit's folder, inside `rag-shell-venv`, with `NUMBER`, `REGION`, `API`, `ME` and the token function `tok` from the setup block, and acme pinned to the kit's own index with the setup section's `make tenant-backend` line. Steps 3 and 5 run offline. Step 6's bench imports the API's generator in your shell, so it needs rag-api's pins, which Module 0's install put in the venv. Step 7 makes a branch of your clone, so start from a clean `main`: `git status --short` prints nothing. It also builds one image with Cloud Build. The two scoped gates and the bench ask 10 questions each; everything else reads files, reports or logs.

### Offline: nine quotes through both measures, and the gate's own lines over a stand-in API

resolve()'s copy, _draft()'s cut, judge_citations() over the corpus and quote_check() over the pool; then live() scoped to the handbook with the switch on, against an API the cell plays itself, for Rs 0.

#### Definition

Four pieces of the kit decide what a quote can be and how it is judged. `resolve()` copies the draft's quote into the citation, or the passage's first 500 characters when the draft's is empty, and adds a citation with that opening for a source the answer cites only as an `[N]`, `[N, M]` or `[Source N]` in its prose; a chunk gets one citation, its first quote. `_draft()` cuts an over-long quote to the contract's 200 characters and ends it with three dots. `judge_citations()` collapses the quote's whitespace, folds its case and looks for it in the tenant's corpus text: the gate's quote support, counted per cited row. `quote_check()` makes the same match against one passage, the one the citation names, after two steps of its own. A quote equal to the passage's first 500 characters is substituted, and a trailing `...` is dropped before the match, because the document never wrote it.

The first cell runs nine quotes through both functions, against six of the handbook's passages cut by the kit's chunker. The second runs the gate itself: `run_eval.live()` scoped to the handbook's 10 rows with the switch on, with `ask()` and `passages()` replaced by an API the cell plays. Each row is answered with its figure and one citation made by the real `resolve()`, and four of the citations are planted. Both outputs below were produced when this page was built, by the same code on a copy of the same files.

#### The code

#### Do it: nine quotes, two measures

The two measures agreed on five quotes and parted on four. The sentence under its own passage, and the same passage's words across a line break in capitals, are own and supported: collapsing whitespace and folding case is all either does to the words. The paraphrase, revision 2's figure and the elision are absent and unsupported: words the model wrote, in no passage and nowhere in the corpus. Revision 2's figure is the dangerous one, a fluent sentence one number away from the passage the model read.

The four that part are why the passage check exists. The same sentence under `[2]` is supported by the corpus, which cannot see that `[2]` does not say it. The quote `resolve()` filled in is supported too, because it is the passage's own opening, though nothing was quoted. `_draft()`'s cut is own once its three dots are dropped, and the corpus calls it unsupported: a false alarm on the generator's own repair. The passage the pool did not hold is supported by the corpus and unread by `quote_check()`, which judges only what it can hold against the passage named.

#### Do it: the gate's own lines, over a stand-in API

The cell plays the API. Each row's `/v1/query` reply carries the row's figure and one citation, made by `resolve()` from a draft, so its quote reaches the gate exactly as rag-api would hand it on. Each row's `/v1/passages` reply is six handbook passages, the row's own clause first. Four rows are planted: lk-04 quotes its probation sentence under NP-03's number, lk-06 paraphrases, lk-08 leaves the quote empty, and lk-09's pool comes back without the passage it cites. The other six quote the first sentence of their clause.

All thresholds met, exit 0: every row was answered, validly cited and held its figure, so nothing the gate judges went wrong. Under the thresholds, `quote_support_rate` said 90.0%. Of the four planted quotes it caught only the paraphrase, because the misattributed sentence, the filled-in opening and the cited-but-unread one are all somewhere in acme's corpus. `quote_passage_rate` said 66.7%, six of nine read quotes in the passage they cite, and named the other three by kind, leaving the unread one out of the count. `must_retrieve_recall` fell to 95.0% for the same row: WFH-01 is the anchor its pool came back without. That is the manifest's proof in run_eval's own words: a quote the cited passage does not contain, flagged by the quote measure, on a run the gate passes. The report the cell wrote, `evals/reports/standin36.json`, keeps each citation's verdict as `check`; step 4 reads yours the same way.

### Your lane: what the UI shows as a quote, then a source's quotes held against their passages

The Chat page's citations, the scoped gate with the switch on, on the live revision, and every citation's verdict read from its report.

#### Definition

The UI streams. `/v1/stream` sends its citations from the packed passages before the model writes a token, and each carries its passage's first 240 characters as its quote. So on the Chat page there is no model quote to check: the Sources list shows the first 200 of those characters, a passage's heading and opening words, whatever the model relied on. A model's quote exists only on `/v1/query`, which is what the gate asks.

`SOURCE=` scopes the gate to the rows that cite one document: 10 for the handbook, all acme and all answerable, with no refusal, media or isolation row among them, so three of the nine thresholds have no rows behind them and are not judged. With `DOCUMIND_EVAL_PASSAGES=1` the gate reads each answerable row's pool once more after the last row, answered or refused, as documind-ui-sa, from `/v1/passages`: one embedding and one rerank a row, and no model call. The two retrievals are the same code with the same question and the same top_k of 6, and with the rewrite stage off, as it is on your lane, they search the same words. The pool read back is the pool the answer drew on, and a citation whose passage is not in it is unread, never a verdict.

#### The code

#### Do it: one question in the UI

Open the UI at `https://documind-ui-NUMBER.asia-south1.run.app`, signed in as yourself, and ask What is the notice period for a confirmed E3? When the answer is in, open Sources. Each source's text is the opening of a passage, a handbook section's heading first, cut at 200 characters, whatever words the model relied on; hover a `[1]` pill in the answer and its tooltip shows the first 120 characters of the same opening. Those citations were made before the answer existed. The question is golden rows lk-06 and vr-01, which the gate asks next through `/v1/query`.

#### Do it: the scoped gate, the switch on

#### Do it: every citation's verdict

The cell reads the report the gate wrote and prints each citation's verdict, the position of the passage it names, and the quote's first words; then any row whose pool could not be read or came back without one of its anchors.

Ten answers came back from the live revision, each with its citations, and every quote was held against the passage it names. If every read quote is own, rule 5 is holding on this source and `quote_passage_rate` says 100.0%: the model copied each clause from the passage it cited. Any other verdict names its row and its words. Elsewhere is a citation number one passage away from its words; absent is a sentence the model composed; substituted is a citation that came with no quote, or only as an `[N]` in the answer's prose. Where the two `[info]` rates differ, one measure passed a quote the other did not, and the reader's lines say which. None of it moved the gate's verdict, which is the thresholds' alone. The report is step 6's input: the bench answers these same rows with rule 5 weakened.

### The prompt's version: the label, the text, its sha256 and the check

config.py's two fields, the places the label goes, the text it names, prompt_pin.py's rule and the registry, and make prompt-version for Rs 0.

#### Definition

`config.py` declares `prompt_id` and `prompt_version`, and the service never reads the prompt's text to label an answer. `/version` joins the two fields; `usage_row()` writes the version on every row it makes, query, stream and passages rows alike; the stream's last event carries the label; `scope_of()` puts the version in the answer cache's scope; and `tenant_daily` groups the rows by it. The text those labels stand for is `generator.py`'s: `generate()` and `generate_stream()` start every prompt with `SYSTEM` followed by `DATED_RULE`, with nothing between, the rule only when a packed passage carries a date.

`prompt_pin.py` reads both strings and both fields by AST, without importing the API, hashes the 604 characters in UTF-8, and looks the label up in `prompt_versions.json`. It refuses to guess: if either prompt line in `generate()` or `generate_stream()` changes shape, it stops with exit 2 rather than hash a text the model may no longer receive. And it checks the code, not a service. A `PROMPT_VERSION` in a service's environment would override `config.py`'s default; the deploy scripts set none, the one target that does, `make prompt-candidate PROMPT_VERSION=` (lesson 12.4), sets it on a no-traffic candidate revision, and step 7 checks that your service has none. Lesson 9.1's gateway backend also sends a JSON rule of its own, which is not hashed. And it binds one prompt: the query rewrite's of lesson 2.5 and the Desk router's of lesson 10.4 each carry a `PROMPT_VERSION` of their own, `2026-10-08.1` and `2026-10-01.1`, with no registry behind them, so the discipline of step 7 is theirs to keep by hand.

#### The code

#### Do it: the check

The label `config.py` serves under is registered to the sha256 of the text `generator.py` sets: `documind-rag@v3` names these 604 characters and no others. The check read no service and called no model; it compared three files, which is why it costs nothing and can run on every push. Make echoed the recipe before running it, so the first line is the command you could run without make. A clone whose prompt was edited and whose version was not would print another sha256 and exit 1. Step 7 does that on purpose.

### The change in memory: rule 5 weakened on the bench, and the sha256 it would register

The same 10 rows, their pools held fixed, the kit's own generate() with v4's rule 5 in memory, every quote checked, and the edited text's sha256.

#### Definition

The change this lesson ships rewrites rule 5. Today it reads "A quote is the clause that answers - at most twenty-five words, never a whole section." In v4 it reads "A quote sums up the clause that answers - at most fifteen words, in plain language." The change reads like a style improvement, shorter and plainer citations, and it is the kind of change that can move every quote without moving a single figure, so none of the gate's thresholds would see it. Before anything is built, the prompt bench of lessons 3.1 to 3.3 measures it in memory. `--from-report` takes the rows of step 4's report; the bench reads each row's pool once from `/v1/passages` and holds it fixed; the kit's own `generate()`, imported in your shell, answers from it with `SYSTEM` edited in memory. `--drop-rule 5` takes the kit's rule out and `--add-rule` appends the new one, renumbered, which gives exactly the text step 7 commits. `--no-baseline` runs that arm alone, since step 4 measured the kit's text on the same rows.

Every answer is judged by the gate's rule and every quote by `quote_check()` against the row's pool. The arm also prints the sha256 of its `SYSTEM` followed by `DATED_RULE`, hashed as a version's text is hashed. This page computed it from the same edit when it was built: `269dec90134e07beb3449813e1eb156c803568aa370bb52baa3a87aab8b2f6e8`, for 601 characters. No version names that text yet. `generator.py` is never written; the bench checks its bytes before and after, and says so.

#### The code

#### Do it: the weakened rule, on the same rows

The edit arm's prompt sha256 is the one this page computed, `269dec90134e...`, so the text the bench measured is the text step 7 registers as v4, byte for byte. The quotes line is the measurement. If fewer of the ten rows' quotes are own than in step 4, the summary rule changed what the model quotes, and pass k/10 says whether it changed anything the gate scores. If they are all still own, the schema's own description of the field, exact words from that source, held the model to the clause without rule 5's help, and step 7's candidate will most likely show the same. The bench wrote no usage row for its answers, which were made in your shell. Its ten pool reads are rows of the live revision, labelled v3, with no tokens; step 8 finds them.

### Ship it: v4 on a branch, checked, built, and answering on a candidate

Four files in one commit, the check that refuses the old label, the registry's new line, the test the dry run runs, one image, and a revision with no traffic that answers as documind-rag@v4.

#### Definition

A prompt change in this kit is four files. `generator.py`'s `SYSTEM` is the text served. `evals/make_trainset.py` keeps a copy of it, and the test holds the two equal, so a model tuned on the training set is served behind the prompt it was trained behind (lesson 12.1). `config.py`'s `prompt_version` is the label. And `prompt_versions.json` gets one new line, the label and the new text's sha256, beside v3's, which does not change. `make prompt-version` refuses the edit until the version moves and its line is there, and `test_prompt_versions.py`, which the dry run runs on every push, refuses it the same way.

Then the release path of lesson 4.3. `make build` makes the API's image with Cloud Build, tagged with the commit's short sha, and `make release-candidate` puts it on a revision with no traffic and records the revision's name. A new revision keeps the service's environment and changes only what the update names, so a `PROMPT_VERSION` set on the service would come along and label every v4 answer as something else: the first command of the build cell reads the service's environment for one. Nothing here moves traffic.

#### The code

#### Do it: the branch, and rule 5 in both copies

#### Do it: the check refuses the old label

The text changed and `prompt_version` did not, so `documind-rag@v3` now points at a sha256 that is not this text's. The check names the version to set and the exact line to add. Error 1 is `prompt_pin.py`'s exit code; make reports it and exits 2 itself.

#### Do it: name it v4, register it, and check again

The cell sets the version and adds the line, taking the sha256 from `prompt_pin`'s own reader of the two strings, so the registry gets exactly what the check will compute. Then the check, and the unit test the dry run runs on every push of the learner repository.

#### Do it: commit

#### Do it: build the image, and stage the candidate

#### Do it: the label on both URLs

The workflow's own check, by hand: each URL's `/version`, with a token minted for the live URL, beside this checkout's short sha.

#### Do it: the candidate's quotes

#### Do it: v3 against v4, quote by quote

The prompt change went out the way any release does, as one image on a revision nobody is sent to, and it took its version with it: the candidate's `/version` says `documind-rag@v4` and this branch's commit, while the live revision still says `documind-rag@v3`. Its gate is the decision a release would take, and the thresholds decide it alone. If they pass, `make promote` would be allowed to move traffic whatever the quotes did, because quote support is information. The comparison is what the information is for: two rates over the same ten questions, and each row's verdicts side by side with the quote v4 wrote.

A drop from v3's rate to v4's with the gate still green is a prompt change that made the quotes worse, and nothing in the kit that blocks it. Whether it should block is the decision this lesson leaves with you. The kit keeps both rates as `[info]`, and its reasons are in its code: the corpus measure trips on hyphenation and on the generator's own repair, and the passage measure judges only the quotes whose pool came back. A threshold on the passage rate would need a floor measured on your lane, and a rule for the rows it could not read.

### The rows name the prompt; the candidate taken down, and v4 spent

Cloud Logging's rows by revision, event and version; the tag removed and main checked out; why v4's line outlives the candidate; and what it all cost.

#### Definition

Every usage row carries `prompt_version`, and Cloud Logging keeps each with the revision that wrote it. The candidate's rows say v4, on the candidate's revision: its ten answers and its ten pool reads, though a pool read sends no prompt. The live revision's rows say v3, and among them are the bench's pool reads, made for answers that used v4's text in your shell and left no row of their own. That is what the label is for. `tenant_daily` groups the same rows by `prompt_version`, so a question about last Tuesday's answers starts from the version that made them.

#### Do it: the rows, by revision, event and version

#### Do it: take the candidate down

Removing the tag ends the candidate's URL. Deleting `.candidate-revision` means a stray `make promote` stops with an error instead of moving traffic to v4. Then `main` again, whose four files say v3, and the check on them. The branch stays.

#### v4 is spent

The candidate is gone, and its rows are not: they say v4, for as long as Cloud Logging keeps them. So on this lane v4 names the summary rule, for good. Back on `main` the registry holds v3 alone, but `make prompt-version` never offers a label the registry has held in any commit your clone's git keeps: on any branch, in the reflog or in the stash. The branch you kept holds v4's line, so the next change on `main` is offered v5; this page's build made that change on `main` of its copy and was offered v5. The kit's own test covers the rest: v5 again once the branch is deleted, because the reflog still holds its commit, and v4 only where nothing git keeps has v4's line, as in a copy outside git. A candidate's branch on one laptop is not in a teammate's clone, so on a team's repository a candidate's registry line is still merged even when the candidate is not. The version strip reads the file alone, as a copy outside git would: its sixth case shows the next change with v4's line and without it.

#### What it costs

About Rs 13 of model calls in all, for 30 answers, and the build. The query embedding and the Ranking API bill on their own lines for every answer and every pool read, and no usage row prices them.

### Verify it yourself: the checklist

Twelve checks, each one block above, each with the value that proves it on your lane.

In the cloud: one image in Artifact Registry, `api:COMMIT`, built by Cloud Build from the branch; one more documind-api revision, with no traffic and no tag, which answered as `documind-rag@v4`; and usage rows. The candidate's say v4: its ten answers and ten pool reads. The live revision's say v3: step 4's ten answers and ten pool reads, the bench's ten pool reads, and your UI question. Nothing served users from v4. On your machine: the branch `prompt-v4`, one commit ahead of `main` and the only record of v4's text and its registry line, kept on purpose; `main` as it was, so the setup block's `git pull` keeps working; and three reports under `evals/reports/`, which git ignores. `.candidate-revision` is gone. Put acme's pin back now, with the setup section's pin-back window. Lesson 3.7 returns the same answer as it is written, on the stream whose citations step 4 read in the UI, and serves it still when a part on the way fails.

Netsetos GenAI on GCP · Module 3 Generation · Lesson 3.6 Check quotes and version prompts · v5.0

Next: Lesson 3.7 Stream answers and handle failures.
