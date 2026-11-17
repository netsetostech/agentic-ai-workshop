# Lesson 4.5: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_4.5_Judge_Vs_People_WIX.html`, reviewed at blob `9373ee0af8b4ac195348e64bb5d42699871468d3`. Learners read that page on the course site; this guide keeps its prose.

Lesson 4.2 ran the judge and ended on its own advice: where the gate and the judge disagree, read the row. This lesson measures how often the judge reads a row the way people do. About 20 of a lane's answers are frozen with the full text of the chunks they cite. You label every row on two questions, grounded and answers the question, yes or no. Then the kit sets your labels beside a second reader's and beside the judge's ratings of the same rows: the 2x2, raw agreement, Cohen's kappa, and the bad answers the judge would let through. Once you have labelled, everything runs on files, at Rs 0.

- Agreement with chance taken out: people first, then the judge

- The words: reader, rubric, label, frozen set, row_sha, constructed row, agreement, chance, kappa, the 2x2, the two rates, CUT

- Before you run anything: set up the shell

- Label the frozen rows yourself, blind

- Two people on the same rows: Cohen's kappa

- The judge on the same rows: true-pass, false-pass and the cut

- Your lane's judge on the frozen rows: the ratings step 5 reads until the author's ship

- Kappa by hand, and the judge's own reasons

- How the rows were chosen, why the judge still only advises, and what it costs

- Verify it yourself: the checklist

You will learn why a judge's scores mean something only once they agree with people's on the same rows, how Cohen's kappa takes chance out of agreement, and how a cut on the judge's 1 to 5 metric trades true passes against false ones. Then you label 20 frozen rows yourself and measure your agreement with a second reader and with the judge, at Rs 0.

### Agreement with chance taken out: people first, then the judge

Why a mean cannot say whether the judge is right, and how two readers, then the judge, are held to the same rows.

A judge's mean says how it rated, not whether it rated right. Lesson 4.2's judge ends in an Experiments run of means: the share of answers judged grounded, the average instruction-following score. Those numbers are only as good as the judge, and a judge is a prompt template with a model behind it. To know how far to trust one, you need people's labels on the same rows. Then the judge's verdict on each row can be set beside theirs, row by row, and counted.

People first. Before a judge is held to people, the people are held to each other. Two readers label the same rows from the same guide. If they split often, the question is unclear, or the guide is, and agreeing with either of them says little about a judge. So the kit measures two readers on a rubric before it measures the judge on it.

Raw agreement flatters; kappa takes chance out. Two readers who both say yes to nine rows in ten agree on most rows by chance alone. Cohen's kappa subtracts what chance would give: `kappa = (p_o - p_e) / (1 - p_e)`, where p_o is the share of rows the two label alike and p_e the share they would label alike if each kept their own counts of yes and no and gave them out at random. Take the kit's worked table: 50 rows, 20 both yes, 5 and 10 split, 15 both no. The two readers label 35 of the 50 rows alike, so p_o is 0.70. But one says yes 25 times and the other 30, so chance alone would give p_e = 0.50, and kappa is 0.40. 1 is perfect agreement, 0 is no better than chance, and below 0 is worse than chance.

Then the judge, with people as the reference. Every row lands in one cell of a 2x2: true pass (people pass it, the judge passes it), false fail, false pass and true fail. Two rates come out of it. The true-pass rate is the share of the rows people pass that the judge passes too. The false-pass rate is the share of the rows people fail that the judge passes anyway: the bad answers it would let through, which is the error that matters when a judge vouches for answers. Groundedness is the judge's own 0 or 1. Its second metric, instruction_following in the SDK that lesson 4.2 pins, is scored 1 to 5, so a cut turns it into pass or fail: CUT or more passes. The kit starts at 4, and the cut is yours to move.

At twenty rows, every rate is a range. One row of twenty moves a rate by five points, so the kit prints each rate as k of n with a 95% Wilson interval. Suppose people fail 7 of twenty rows, about a third, and the judge passes none of them: its false-pass rate is `0/7 = 0.0% [0.0%, 35.4%]`, and the true rate could still be as high as 35.4%. That is why the judge stays an adviser in this lesson, as it was in lesson 4.2.

Moderating a board exam's marking. Before a new examiner marks board papers alone, the head examiner hands over twenty scripts that two senior examiners have already marked, without showing their marks. First the head examiner sets the two seniors side by side: if they split on many scripts, the marking scheme is unclear, and nobody can be judged against it yet. Then the new examiner's marks go beside the seniors'. Agreeing on scripts that everyone passes proves little. What counts is how many weak scripts the new examiner passed. Your sheet and the author's are the two seniors' marks, and the LLM judge is the new examiner.

#### The agreement board: two readers, or the judge against one

The board below holds the kit's judge fixture: 9 synthetic rows, 2 of them constructed, two made-up readers, FX1 and FX2, and the ratings of the stand-in judge the kit's tests use. Pick a rubric and who to set against whom, tap a row to read it, and flip a label to see what one row does. Try these:

- Two people, groundedness. FX1 and FX2 agree on `8/9 = 88.9% [56.5%, 98.0%]`. Chance alone would give 0.59, so kappa is 0.73. The one row they split on, fx-12, is constructed: FX2 passed an answer carrying a sentence its context never said.

- Tap fx-01 and flip FX1's label. Both readers said yes to that row. Agreement falls to `7/9 = 77.8% [45.3%, 93.7%]` and kappa to 0.53: one row of 9 did that.

- Two people, answers the question. Kappa is 0.73 again, and the split is fx-04: half an answer, which FX2 let through and the guide calls a no.

- The judge against FX1, groundedness. Kappa 0.50. The judge passes fx-07, an answer about a sabbatical its context never mentions: the stand-in looks only for digits, and this answer writes its numbers in words. It fails fx-06, a refusal that claims nothing, because the refusal names a year its context does not hold.

- The judge, answers the question: drag the cut. At 4, the false-pass rate is `1/3 = 33.3% [6.1%, 79.2%]`. At 3, fx-04's half answer passes too: `2/3 = 66.7% [20.8%, 93.9%]`, and kappa drops to 0.18. At 1 every row passes, and kappa is 0.00: a judge that passes everything agrees with people no better than chance.

The arithmetic is `agreement.py`'s and `judge_agree.py`'s, ported. The build ran all 80 states of this board, every rubric, side, cut and single flip, through the kit's own functions, and every 2x2 table of up to 20 rows, 10,625 of them, and the board had to print the same counts, rates, intervals and kappas.

The fixture's judge is not Gemini. The kit's tests rate these rows with a stand-in, a fixed rule, so that the tests run anywhere at Rs 0 and their numbers never move. It is crude on purpose, and its blind spot is the one a real judge can share: an unsupported sentence with no figure in it.

It calls no model and reads no lane. The fixture's rows are synthetic, every question ends "(fixture)", and FX1 and FX2 were made up for the kit's tests, so its numbers are a worked example, not a verdict on any judge. From step 3 the same arithmetic runs on the frozen set: your labels, the author's, a peer's and the real judge's ratings, and step 5 puts the author's rows on this board.

### The words: reader, rubric, label, frozen set, row_sha, constructed row, agreement, chance, kappa, the 2x2, the two rates, CUT

Fifteen rows, each with where it lives in the kit.

One distinction to hold: agreement is not accuracy. Kappa says how far two readers agree beyond chance; it does not say which of them is right. People are the reference here because the rubric is theirs, not because a person cannot be wrong: on the board, FX2 passed a constructed sentence.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible.

The shell, in the kit's folder. The UI is not used, and nothing on this page asks the API, so the setup's pin of acme to the kit's index changes nothing here. Every step except step 6 reads files and costs nothing; step 6 needs lesson 4.2's `~/judge-venv` and asks Vertex AI Evaluation for 40 ratings. The lesson reads four files: the frozen set `evals/judge_set.json`, the author's labels `evals/judge_labels.L1.csv`, a peer's `evals/judge_labels.L2.csv` and the judge's ratings `evals/judge_set.ratings.jsonl`. They are recorded from the author's run and are not in the kit yet; once they are, the setup block's `git pull` brings them. Until then you build each one yourself, and every step says how: you freeze your own set (step 3, one judge run over lesson 4.2's saved answers), a colleague labels it as your second reader (step 4), and your lane's judge rates it (step 6, which step 5 then reads). Labelling takes the longest: allow time to read every row's context in full.

### Label the frozen rows yourself, blind

A blank sheet of the frozen rows, filled in a spreadsheet, then checked against the set.

#### Definition

`make label-sheet` writes a CSV with one row per frozen answer: its id, your reader id, the two label columns, an optional note, then the question, the answer, the context that answer cites, and `row_sha`, a hash of those three. Every reader reads the same rows: you, the author and a peer from the same guide, and the judge through its own template. The sheet does not say which rows are constructed, and the target never overwrites a sheet that exists, so running it twice cannot wipe your labels. `--check` then holds the filled sheet to the frozen set: every row once, each labelled on the same answer, yes or no in both columns, one reader id. The author's and the peer's sheets ship in a public kit, so a reader id is a short pseudonym of letters, digits, `-` and `_`, and the check refuses an email.

#### The code

Steps 4 to 8 print the author's labels, a peer's and the judge's ratings of these very rows, and steps 5 and 8 mark the constructed ones. Read any of them first and your labels are no longer your own. Fill your sheet, check it, then go on.

#### Do it first: a frozen set, your own while the kit has none

While your kit has no `evals/judge_set.json`, freeze your own. `make judge` with `--save-rows` rates lesson 4.2's saved answers, `evals/reports/judge72.json`, and writes every rated row beside its question, context and answer. If that file is gone, `--reuse` collects the answers afresh, 65 questions to your API, about Rs 29.01. Each row gets two Evaluation requests either way. `--freeze` then picks 20 of the rated rows by the rules in step 8 and writes them to `evals/reports/judge_set.json`. Git ignores that folder, so the author's set can arrive later without a clash. The kit's targets read your set while the kit has none, and the author's once it ships. Skip the block if the first line says a set is there.

#### Do it: your sheet

Open `evals/reports/judge_labels.csv` in a spreadsheet or a text editor. For each row, read the context first, then the answer, then the question again, and write `yes` or `no` under both label columns. Write a note on any row you hesitate over, now: step 4 prints it beside the other reader's. Here is one filled row of the kit's fixture, as a sheet holds it:

The answer refuses, so it claims nothing: grounded, yes. But the context holds the cap, so a refusal does not answer the question: no. The reader's note says why: "the cap is in the context". Save the sheet as CSV with every column kept and in the same order. A spreadsheet may add a byte-order mark, Windows line endings or a capitalised YES; the check reads all three. Then check it:

`exists and may hold labels: nothing written` from `make label-sheet` means you made the sheet before, and your labels are in it; delete it only to start again. `evals/judge_set.json: not found` means there is no frozen set yet, the kit's or yours: run the block before the sheet, which freezes your own. `N problem(s) against the frozen set` from `--check` lists each row and what is wrong with it: a blank, a word other than yes or no, a row missing or there twice, two reader ids, or `labelled on another answer`, which means the sheet was made from another freeze.

`make label-sheet` wrote one row for each frozen answer, with the guide printed above it, and `--check` counted your yes and no for each rubric. Those counts already matter. A reader who says yes to nearly every row leaves little room for agreement beyond chance, as step 4 shows. The author's line is the same check on the sheet the kit ships. Your sheet sits in `evals/reports/`, which git ignores, so the kit stays clean.

### Two people on the same rows: Cohen's kappa

The author's sheet is your second reader; the kit counts your agreement with it, then takes chance out.

#### Definition

`make judge-agree PEOPLE=1` reads two sheets of the same frozen rows: yours, and by default the author's, `evals/judge_labels.L1.csv`. For each rubric it prints the 2x2 of the two readers' labels, raw agreement with its Wilson interval, the agreement chance alone would give, Cohen's kappa, and the rows the two differ on, with both notes. The arithmetic is `evals/agreement.py`: standard library only and counted in whole rows, so the worked table gives exactly 0.40, and two readers who each gave every row one and the same label get `undefined`, never a perfect 1. `AGAINST=` names another reader's sheet. The kit also ships a peer's, `evals/judge_labels.L2.csv`, labelled once and blind; with the author's, it makes the recorded pair.

#### The code

#### Do it: the worked table, and the kit's own tests

#### Do it: you against the author, then the author against the peer

#### Do it, while the kit has no author's sheet: a colleague as your second reader

Until the author's sheet ships, kappa needs a second person. Make a colleague a sheet of the same rows under their own pseudonym. They label it blind, from the guide alone, without seeing yours. Then check their sheet and count your agreement with it. The author-against-peer line above waits for the recorded pair.

Read kappa before agree. On a rubric where both readers say yes to most rows, agreement can look high while kappa stays low, because chance alone would supply most of it. Then read the rows the two of you differ on, with both notes: each is a slip, a place where the guide is unclear, or a real judgement call. The author and the peer are the recorded pair: two people who labelled the same rows blind, once each. Where careful readers split often on a rubric, the rubric is the problem, not the readers, and the judge's agreement with either of them on it is worth little until the guide is sharper. One row moves kappa a long way at this size: on the board, flipping one of nine rows took it from 0.73 to 0.53.

### The judge on the same rows: true-pass, false-pass and the cut

The judge's ratings of the frozen rows, held to your labels and to the author's, at a cut you choose.

#### Definition

Lesson 4.2's judge kept only means. `judge.py --save-rows` writes every row it rated beside its question, context and answer, with each metric's score and the judge's explanation, and the author's run of it rated the frozen rows once: `evals/judge_set.ratings.jsonl`, which ships with the kit once it is recorded. Until then the ratings are your lane's own: run step 6 first, whose second line is this step's comparison against your sheet, and read `RUN=evals/reports/judge_set.ratings.jsonl` into every `make judge-agree` here. `make judge-agree`, without `PEOPLE`, sets those ratings against one sheet, yours by default, and your labels are the reference. Groundedness is the judge's own 0 or 1. Its second metric is whichever of FULFILLMENT, INSTRUCTION_FOLLOWING or QUESTION_ANSWERING_QUALITY the SDK names, scored 1 to 5, and it passes at `CUT` or more, 4 unless you say otherwise. For each rubric the kit prints the 2x2, the true-pass and false-pass rates with their intervals, raw agreement and kappa, the false-pass rate on constructed and natural rows apart, and the rows you and the judge differ on. A rating counts only where the judge rated the very answer you labelled, the same `row_sha`. The command exits 0 whatever the agreement: it measures the judge and gates nothing.

#### The code

#### Do it: the judge against you, then against the author

#### Change it: move the cut

`CUT=3` passes the second metric at 3 or more, and `SWEEP=1` adds every cut from 1 to 5 under the two blocks, the current one marked. There is nothing to restore: a run without `CUT` is back at 4.

Read the false-pass rate first: of the answers people failed, how many the judge would have waved through. A looser cut passes more rows, so the true-pass and false-pass rates can only rise together; a stricter one can only lower both. Kappa sums the trade up but hides which way the judge errs, so read the two rates. Constructed rows test groundedness on purpose: each carries one sentence its context does not hold, cited as if it did, so a judge that passes them is passing invented facts. Then set your two runs side by side. If the judge agrees with the author more than with you, read the rows where you and the author differ before you blame the judge.

#### The cut, row by row, on the author's rows

The same board as step 1, on the frozen set, with the author as the first reader and the peer as the second. Set it to the judge and answers the question, drag the cut, and watch which rows change sides.

They join this board when the frozen set, the two sheets and the judge's ratings are recorded: [awaiting the author's run: data/judge_set.json]

### Your lane's judge on the frozen rows: the ratings step 5 reads until the author's ship

The same rows through Vertex AI Evaluation on your project, then your judge's ratings against your labels.

#### Definition

While the kit has no ratings, this step is how the judge's ratings reach you, and step 5 reads them. Once the author's ship, they are one judge: the author's run of the Evaluation service, at one time, with one template. Yours may rate differently, because a judge is its template and its model, and both move. `make judge-frozen` sends the frozen rows, as frozen, to Vertex AI Evaluation from lesson 4.2's venv. `--reuse` loads them from the frozen set, the kit's `evals/judge_set.json` or your own `evals/reports/judge_set.json`, so nothing asks the API, and `--no-enrich` keeps each row's context as the readers saw it instead of reading the cited chunks again from Firestore. It costs two Evaluation requests a row, 40 in all, in `us-central1`, and writes one Experiments run in `documind-eval` whose name starts `api-frozen-` and ends with the templates' hash, as in lesson 4.2. Your ratings go to `evals/reports/judge_set.ratings.jsonl`, so the author's file stays as it was.

#### The code

#### Do it

Once the author's ratings ship, two judges have rated the same frozen rows: the author's run and yours. If the template hashes in the two run names differ, they are different judges, and their agreement with you can differ for that reason alone. Set your run's false-pass rate beside the author's capture's, both against your own sheet. A judge whose agreement moves with its template has to be measured again each time the SDK changes, which is why the hash rides in every run name.

### Kappa by hand, and the judge's own reasons

Two standard-library cells over the files themselves, with no kit function between you and the count.

The first cell reads your sheet and the author's with Python's `csv` module, counts p_o and p_e by hand, and checks the result against the kit's `cohen_kappa()`. It is this lesson's arithmetic in a screenful, and it runs anywhere Python does.

The second reads the judge's ratings file directly and prints each row where the judge and you disagree, with the judge's score and its own explanation. It is lesson 4.2's advice made concrete: where they disagree, read the row. It skips `judge_agree.py`'s `row_sha` check, because both files come from the same frozen set.

The hand count matched `cohen_kappa()`, because kappa is nothing but counts: how many rows alike, and how many yes and no each reader gave. The judge's explanations are what a mean never shows. On a false pass, read whether the judge missed the unsupported sentence or read the context differently from you; on a false fail, whether it marked a refusal down for a figure it named. Neither cell writes anything.

### How the rows were chosen, why the judge still only advises, and what it costs

The freeze's rules and the author's freeze, the limits of twenty rows, and the rupees.

#### How the rows were chosen

The frozen set came from the author's lane: `judge.py --save-rows` on the live revision's answers to all 65 golden rows, and on a `gemini-3.1-flash-lite` candidate's answers to the same rows, for more failures. `build_judge_set.py --freeze` then picked about 20 rows, one per question, without looking at the judge's ratings: rows chosen by the judge's own verdict would bias every rate measured against it. A natural failure is found by the gate's own figure and refusal rules, run on the frozen answer. Natural failures seldom fail groundedness, so constructed rows make up that third, each with one of 5 sentences, used only where its key phrase is absent from that row's context and answer.

#### Why the judge still only advises

- Twenty rows are a sample, not a calibration. With about 7 failing rows on a rubric, even a judge that passes none of them has a false-pass rate of `0/7 = 0.0% [0.0%, 35.4%]`. A cut picked by reading the sweep on these same rows is also fitted to them: with no rows held out, it is a starting value, which is what the kit calls its default.

- A new template is a new judge. Every run name carries the templates' hash. When it changes, the agreement measured here belongs to the old judge.

- The labels measure; they never tune. No prompt, threshold or model on this page is changed from them.

- Only computed checks block. Lesson 4.2's gate decides a release; `judge_agree.py` exits 0 whatever the agreement.

#### What it costs

### Verify it yourself: the checklist

Ten checks, each one block above, each with the value that proves it on your lane.

On your machine: `evals/reports/judge_labels.csv`, your labels, which git ignores. If you ran step 6, also `evals/reports/judge_set.ratings.jsonl`, ignored too, and one run in the Experiments experiment `documind-eval` whose name starts `api-frozen-`, which stays until you delete it. Nothing asked the API, so no usage rows were written, and nothing deployed changed. Nothing in the kit changed either, so the setup block's `git pull` keeps working. Module 4 now turns from quality to security: lesson 4.6 traces an authenticated identity into tenant membership.

Netsetos GenAI on GCP · Module 4 Evals and safety · Lesson 4.5 Check the LLM judge against people · v5.0

Next: Lesson 4.6 Trace authenticated identity into tenant membership.
