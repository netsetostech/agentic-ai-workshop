# Lesson 7.6: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_7.6_Studio_Voice_WIX.html`, reviewed at blob `fbbf9c146875e365f93128d312d1b7bed2f13340`. Learners read that page on the course site; this guide keeps its prose.

The UI has three media features. The Studio turns a prompt into an image through the API, which checks, spends and records it. The chat can read each answer aloud, and it can take a question from the microphone. All three are in the kit already: this lesson exercises them and reads what each one leaves behind.

In this lesson you generate the Studio's own image twice and find its usage rows and its audit event. You send a video through the API's upload door. Then you have an answer read aloud, and transcribe that audio back, first where the UI transcribes and then where it could.

- The Studio and the voice, as the kit builds them

- The words: the Studio, the route, DEMO_MODE, the media bucket, the usage row, the audit event, the door, cached_tts, transcribe, read aloud

- Before you run anything: set up the shell

- The Studio's and the voice's rules, run

- A generated image, and its usage row

- The upload door

- An answer read aloud, and a question nobody hears

- Why it works this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn what the Studio checks before it spends, what it records after, and which of those records reach BigQuery. You will learn how the upload door keeps large files off Cloud Run, how the voice caches what it says, and where the microphone sends its audio. Then you will prove it on your lane: a generated image with its usage row, and an answer read aloud.

### The Studio and the voice, as the kit builds them

An image spent once and recorded twice, a door into the bucket, and a voice with a memory.

The Studio: checked before it spends. The UI's Studio tab sends a prompt to the API's `/v1/media/generate`, as the signed-in person. The route checks, in order:

- The roster. The caller must be on the tenant's roster, the same check every question passes. If not, it answers 403 before anything is spent.

- The audit bucket. Without `AUDIT_BUCKET` it answers 503, before the model is called. The first live generation went wrong the other way round: it failed after the spend.

- DEMO_MODE's cache. The image's name is a hash of the prompt, under the tenant: `acme/gen/HASH.png`. With DEMO_MODE on, an image that already exists under that name is served again, with no model call. `make up` deploys the API with `DEMO_MODE=1`.

- The model. Otherwise `gemini-3.1-flash-image` draws it, and a reply with no image part is a 502.

Recorded twice. The PNG goes into the media bucket, which deletes after 30 days: a cache, not a record. The record is one `media.generate` audit event in the audit bucket, which keeps five years. It holds the prompt's hash, never the prompt. There is also one usage row: `event=media`, `modality image`, `cost_usd 0.039`, or 0 when DEMO_MODE served it. The Studio shows the image through a link it signs for 15 minutes as `documind-ui-sa`.

The upload door. `/v1/media/upload-url` signs a PUT into the uploads bucket, under the caller's tenant, for 15 minutes and one content type. The bytes go straight to the bucket, never through Cloud Run. The kit's own comment says a browser must do that past 32 MB. The bucket's notification then hands the object to the worker, like any upload. Only a bare filename and one of seven content types are signed.

The voice, in the UI's `voice.py`:

- `cached_tts` reads text aloud with Chirp 3 HD, streamed as Ogg Opus. It keeps the audio in the TTS bucket under the SHA-256 of voice, rate, format and text, so the same words in the same voice are synthesised once. The bucket deletes after 30 days. The chat's "Read answers aloud" toggle sends each answer's first 1,500 characters through it, and the Studio's "Read it aloud" offers three voices.

- `transcribe` turns the microphone's recording into the question. It asks Speech-to-Text in `SPEECH_REGION`, which is `asia-south1` on the lane, for Hindi and English (India). It tries `chirp_3`, then `chirp_2`, then `long`, and returns an empty string when all three fail.

A neighbourhood photo studio with a sound booth. The counter checks your membership card before it takes an order, and will not work at all if the order book is missing. A design ordered before is handed over from the prints it kept, free, and the prints are thrown out after a month. Every order, even a free repeat, gets a line on the day's sales slip. Only new work goes into the bound register kept for years, and the register notes a fingerprint of the order, never its words.

In the sound booth, an announcer records scripts, and the recordings are filed by the exact script and voice. The same script in the same voice is played from the shelf. The booth's transcriber, though, sits in a branch where nobody speaks the customers' languages. Every dictation comes back blank, and the slip says nothing about it.

The card is the roster, and the order book is the audit bucket. The kept prints are DEMO_MODE's media bucket, and the sales slip is the usage row. The bound register is the audit events, and the fingerprint is `prompt_sha`. The shelf is the TTS cache, and the transcriber's branch is `SPEECH_REGION`.

#### One Studio request, one answer read aloud, one question spoken

Set each feature's conditions and see what the kit does. The Studio box shows the reply, the model call, and what is recorded. The voice box shows whether the audio is synthesised or read back. The microphone box shows which models are tried, and whether any hears you.

The rules are the kit's: `media.generate`'s branches, `cached_tts`'s cache and `transcribe`'s order of models, ported and compared with the kit's own functions on all 42 combinations. Which location serves which model is Google's: Chirp 3 is GA in the `us` and `eu` multi-regions, and the language table lists Hindi and English (India) in `asia-southeast1` (`chirp_2`) and `eu`. Checked on 24 September 2026.

It follows one request of each kind, not a day's traffic. Whether a model is served in a location can change as Google adds regions. The microphone cell in step 6 asks your lane itself.

### The words: the Studio, the route, DEMO_MODE, the media bucket, the usage row, the audit event, the door, cached_tts, transcribe, read aloud

Ten rows, each with the value it takes on your lane.

One distinction to hold: the audit event records that something was made, and the usage row records what a request cost. A DEMO_MODE hit makes nothing, so it leaves a usage row and no audit event. A generation leaves one of each.

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

You need the shell in the kit's folder, with `PROJECT`, `REGION`, `API` and `ME` set by the setup above, and lesson 7.5's lane.

- Lesson 7.5's video. Step 5 sends `evals/corpus/acme/townhall_2026_q1.mp4`, which `make media MEDIA_ARGS=--video` wrote, through the door. Step 6 asks the town hall question that 7.5 answered from it.

- The UI's speech clients. Step 6's first line installs the UI image's pins of the Speech-to-Text and Text-to-Speech clients. The cells run the UI's own `voice.py` in your shell, with the UI's settings.

- What the lesson changes. It generates one image for acme and writes the answer's audio into the TTS bucket. It re-sends the video's bytes under their own name, which the worker acknowledges, and it saves `~/answer.ogg`.

### The Studio's and the voice's rules, run

The usage row media.py writes, the events that reach BigQuery, and cached_tts with its clients stood in.

#### Definition

The cell does three things with the kit's own files:

- It lifts `_usage()` out of `media.py`, which builds its clients when imported, and writes the row for a generation and for a DEMO_MODE hit.

- It reads the log sink's filter and `tenant_daily`'s `WHERE`, and says which usage events each one takes.

- It imports the UI's `voice.py` with its clients stood in: a bucket in memory, and a voice that counts its calls. Then it reads the Studio's own sentence aloud three times.

#### The code

#### Do it

- The media row carries a price and no tokens: 0.039 for a generation, and 0 with `cached True` for a DEMO_MODE hit. The UI's cost display reads the same price from its own copy of it.

- A media row never reaches `tenant_daily`. The sink copies `query`, `stream`, `chat`, `desk`, `passages`, `desk_shadow` and `desk_gate` (those two on a condition) into BigQuery; `media` still never. The view reads `query`, `stream` and `media`. The view asks for media rows the sink never copies, and the chat rows the sink copies go unread. Lesson 11.5 found it; this lesson's image is one such row.

- `cached_tts` synthesised once and read back once. The Hindi voice reading the same words is another key and another object, because the voice is part of what the key hashes.

### A generated image, and its usage row

The Studio's own prompt, sent twice; the rows in Cloud Logging; the event in the audit bucket; the image.

#### Definition

The cell reads the Studio tab's default prompt out of `studio.py`, and sends it to `/v1/media/generate` twice as `documind-ui-sa`, as the Studio would. It then reads three things back:

- the API's `event=media` usage rows from Cloud Logging;

- the `media.generate` events from the audit bucket;

- a 15-minute link to the image, signed as `documind-ui-sa`, the account the Studio signs with, which may read the media bucket.

The route checks before it spends:

Then it spends, and records:

#### Do it

- The first call drew the image, `cached False`. The second was served from the media bucket, `cached True`, with no model call. The name is the prompt's hash, `9b79e578...`, so anyone in acme who sends these exact words gets this image from the bucket until the 30-day rule deletes it.

- Two usage rows: 0.039 for the spend and 0.0 for the hit, both in Cloud Logging.

- One audit event, for the generation. The hit left none, because nothing was drawn. The event holds the prompt's hash, not the prompt, because the audit bucket is retention-locked for five years.

- The link opens the PNG for 15 minutes.

If this prompt was drawn before, in the Studio or by an earlier run, both calls are hits: two rows at 0, and no audit event. Either way, that is the first proof: a generated image and its usage row.

### The upload door

Two requests the door refuses, then lesson 7.5's video, put straight into the bucket.

#### Definition

The door signs a PUT for one bare filename, under the caller's tenant, bound to one of seven content types:

The cell asks for two URLs the door should refuse: a zip, and a name that is a path into globex. Then it asks for one for the video, PUTs the MP4's bytes to it, and waits for the worker's line about those bytes. It finds the line by the bytes' own SHA-256, the worker's claim key.

#### Do it

- Two refusals, from the route's own checks: the content type is not one of the seven, and the name is not bare. The object's name is the tenant's prefix plus exactly the filename given, so the door refuses a slash or `..` before it signs anything.

- The URL was a PUT into acme's prefix of the uploads bucket, bound to `video/mp4` and 15 minutes. The PUT went straight to the bucket, without passing through Cloud Run.

- The worker took the bucket's event and acknowledged the bytes as a duplicate. Its claim key is the bytes' hash, and lesson 7.5 indexed these bytes already. A new video would be described the way 7.5 showed.

No page of the UI uses this door (step 7).

### An answer read aloud, and a question nobody hears

The UI's own voice.py, in your shell: an answer spoken twice, then its audio transcribed back.

#### Definition

The first cell asks the town hall question as `documind-ui-sa`. It reads the answer aloud with the UI's own `cached_tts`, twice, and saves the audio as `~/answer.ogg`. The text is the answer's first 1,500 characters, as the chat's toggle reads it.

Play it: in Cloud Shell, `cloudshell download ~/answer.ogg` hands the file to your browser. That is the second proof: an answer read aloud.

The second cell gives that audio to the UI's own `transcribe`, first where the UI runs it, then in `eu`. `eu` is a location Google lists `chirp_3` in, for Hindi and English (India). The audio leaves India for that one call: a synthetic voice reading an answer about acme, whose policy is `any` (lesson 7.3). This is the function:

- The answer was read aloud: the first time a miss, synthesised and written to the TTS bucket; the second time a hit, the same bytes read back.

- In `asia-south1`, `transcribe()` returned an empty string. None of its three models answered there, and it swallowed each error without a word. That is what the chat's microphone does on your lane: it records, transcribes nothing, and asks nothing.

- In `eu`, the same function returned the answer's words. The function is sound; the location is not.

#### In the UI

Open the UI and try the same features by hand:

- Studio. Press Generate with the default prompt. It is the prompt step 4 drew, so it is a DEMO_MODE hit: the caption says cache hit, $0.000. Then press Speak under "Read it aloud" to play the Studio's sentence in the voice you pick.

- Chat. Turn on "Read answers aloud" in the sidebar and ask a question: the answer plays under it.

- The microphone. Press Speak and say a question. Nothing is asked, for the reason the second cell showed.

### Why it works this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- Check before you spend. The roster, then the audit bucket, then the cache: the model is the last thing the route calls. A refusal costs nothing.

- The audit event is the record; the image is a cache. The media bucket forgets in 30 days and the audit bucket keeps five years. The audit event holds the prompt's hash, because a locked bucket can never be cleaned of a prompt someone regrets.

- DEMO_MODE makes a demo one bill. The kit's comment: the same prompt eight times would be eight bills, and eight chances for the network to embarrass you.

- The door keeps large files off Cloud Run. A signed PUT goes to the bucket, and from there the worker's path is the same as any upload's.

- Speech is cached by what it says. The same words in the same voice are synthesised once, and replayed free until the bucket's 30-day rule deletes them.

- The UI holds no image model of its own. The Studio calls the API, which checks, spends and records, so the rules live in one place.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does. The first point's region facts are Google's, checked on its pages on 24 September 2026.

- The microphone cannot be heard on the lane as deployed. The UI transcribes in `asia-south1` (`SPEECH_REGION`, set when the UI is deployed). Google's pages list none of `transcribe()`'s three models there for Hindi or English (India). Chirp 3 is GA in the `us` and `eu` multi-regions, `chirp_2` serves `us-central1`, `europe-west4` and `asia-southeast1`, and the language table lists these languages only in `asia-southeast1` and `eu`. Moving speech-to-text out of India is a residency decision, so the kit should make it deliberately, not leave the feature silently off.

- The failure says nothing. `transcribe()` catches every error, logs none and returns an empty string, so the chat asks nothing and shows nothing.

- Media rows never reach BigQuery. The sink copies `query`, `stream`, `chat`, `desk`, `passages`, `desk_shadow` and `desk_gate` (those two on a condition); `media` still never. `tenant_daily` reads `query`, `stream` and `media`. The Studio's spend is in Cloud Logging only, and `tenant_daily` has no image cost. Lesson 11.5 found it.

- Speech is metered and audited nowhere. `voice.py` writes no usage row, and `media.transcribe` is a registered audit action that nothing emits. Every synthesis and every recognition is billed to the project under the UI's account, and attributed to no tenant.

- DEMO_MODE's cache knows the prompt, not the model. The image's name is the prompt's hash under the tenant. After `IMAGE_MODEL` changes, a prompt drawn before is served the old model's image for up to 30 days, and each hit leaves a usage row but no audit event.

- Nothing in the UI uses the upload door. The Documents page uploads through Streamlit, whose limit is set to 200 MB, though `media.py` itself says that past 32 MB the browser must PUT straight to the bucket. No page calls `/v1/media/upload-url`; only `make smoke-media` does. Both buckets' CORS names `https://documind.example.com`, so a browser PUT from the lane's UI would be refused.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

acme's media folder holds one generated image, which the bucket deletes after 30 days. Cloud Logging holds its two usage rows, and the audit bucket holds its event for five years. The town hall video's object has a new generation with the same bytes: the worker acknowledged it, and the nightly walk will record the generation. The TTS bucket holds the answer's audio for 30 days, `~/answer.ogg` is in your home directory, and the operator venv has the UI's two speech clients. Module 8 changes the pipeline and measures it, starting with lesson 8.1: the ingest events through Pub/Sub, mapped to Kafka.

Netsetos GenAI on GCP · Module 7 Graph and multimodal · Lesson 7.6 Exercise implemented Studio and voice features · v5.0

Next: Lesson 8.1 Run the ingest events through Pub/Sub, mapped to Kafka.
