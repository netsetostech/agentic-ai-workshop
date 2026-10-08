# Lesson 7.5: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_7.5_Video_Clip_WIX.html`, reviewed at blob `139fc0392978c735a000f0aed33bb4a541f5ad5a`. Learners read that page on the course site; this guide keeps its prose.

A video has no text for the kit to parse. So the ingest worker has Gemini describe it: segments of at most a minute, each with a start, an end and a summary that quotes every number said. The summary is what the kit retrieves and the model reads. A citation of it carries the video's path and the seconds, and the UI opens the video at the second the segment starts.

In this lesson you build acme's town hall video, send it through the worker and read its segments against the ground truth. Then you ask the golden set's town hall question and check that the cited clip starts where the CFO says it. Last, you turn Module 7's gate green.

- A video, described; a citation that opens it at its second

- The words: media as a document, segment, summary, media_url, start and end, kind, the pill, the ground truth, the media rows, the gate

- Before you run anything: set up the shell

- From a segment to a pill, run

- The clip built, the transcript withdrawn, the video heard

- The clip at its second

- make smoke-media, green

- Why video works this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn how a video becomes evidence: segments with times and quoting summaries, the rows that carry them, and the citation that opens the clip. You will learn the three checks that validate it: the kind of citation, the second it points at, and the gate. Then you will prove it on your lane: an answer whose pill reads `[Clip N, mm:ss]`, a clip that holds the moment the ground truth names, and `make smoke-media` green.

### A video, described; a citation that opens it at its second

What the worker makes of a video, what a citation of it carries, and how to check it.

Media is a document, described rather than parsed. The worker picks its path by the content type the upload's event carries. An image becomes one `figure` chunk, and a video or an MP3 becomes `segment` chunks. For a video it makes one Gemini call, `gemini-3.6-flash` by default:

- Gemini reads the video from the bucket (`from_uri`) at low media resolution, which is enough for what is said and roughly when.

- It returns segments of at most 60 seconds. Each has a start and an end in seconds, and a two-sentence summary of what is said and shown.

- The summary quotes every number, percentage, amount and name exactly as spoken. The kit's comment says why: the first live town hall came back as "a slight contraction" where the speaker said "fell 5.2 per cent". The segment was found and the figure was gone.

Each segment becomes a row. The summary is its text, the part that is embedded, retrieved, reranked and quoted. The row also keeps `media_url` (the video's `gs://` path), `start`, `end` and a locator such as `t22-58`. DLP scans the summaries before anything is indexed. An image's pixels are scanned too, but a video's frames are not.

A citation that opens the clip. The model reads a segment's summary under a `[Source N]` header that names the file, and cites it as `[N]`, like any source. It never sees the video or the time. The Citation the API returns carries `kind: segment`, `media_url`, `start` and `end`. The Streamlit UI turns these into two things:

- a pill in the answer, `[Clip N, mm:ss]`: N is the source's number and mm:ss its start;

- under Sources, the video itself, playing from that second, through a link it signs for 15 minutes.

A segment among the sources also makes the usage row's modality `video`.

Validating it: three checks.

- The kind. Golden row mm-03 asks the town hall question and requires a segment citation (`must_cite_kind`). `run_eval`'s `media_kind_rate` must reach 0.80, and mm-03 is a required row that must pass on its own.

- The second. Nothing in the kit checks it, so this lesson does. `make media` writes the ground truth beside the video: each speaker turn's start and end, measured from the synthesised audio.

- The gate. `make smoke-media` generates an image as a member and has the outsider refused. It asks a figure question, lists the media documents through the MCP server, and uploads through a signed URL that the worker then indexes.

The transcript on your lane. The video is synthesised from `townhall_2026_q1.md`, and `upload.sh` keeps that transcript home once the video exists. But your lane's corpus went up in Module 1, before the video existed, so the transcript is in acme's index as text. Step 4 withdraws it, so the town hall is in acme's corpus only as a video.

A cricket broadcaster's highlights logger. Nobody searches ten hours of match footage. A logger watches the match and writes a note for each passage of play: the time it starts and ends, and a line with the numbers exactly as they happened. "Kohli drives for four, 87 off 64" is a useful note; "a fine knock" is not, because nobody searching for 87 will ever find it.

When the producer asks for "Kohli's 87", the editor searches the notes, not the tape. The note says where to cue it, so the clip starts at that ball. At the end of the day, the official scorecard says what really happened and when, and anyone can check that each cue lands on the right over.

The logger is the worker's Gemini call. The notes are the segments' summaries, and their times are `start` and `end`. The search is retrieval, and the cue is the pill with the player's start. The scorecard is the ground truth `make media` writes, and checking a cue against it is validating the second.

#### What does a citation turn into?

Set a citation's fields, as the API would return them, and see what the kit makes of it:

- the pill the UI draws in the answer;

- what it shows under Sources: the image, the video from a second, or a link;

- the usage row's modality;

- whether a media row of the golden set counts it.

The rendering is the kit's: `_label`, `_mmss` and the Sources branch of `render_with_citations` from `services/frontend/citations.py`, `modality_of` from the API and `run_eval`'s kind check. The panel's port was compared with the kit's code, with the UI's module run whole, on all 9720 combinations of these settings.

It draws one citation, not an answer. Which sources are packed, and which one the model cites, are your lane's to decide. The link it describes is signed by the UI's own account. An API caller gets the `gs://` path instead (step 7).

### The words: media as a document, segment, summary, media_url, start and end, kind, the pill, the ground truth, the media rows, the gate

Ten rows, each with the value it takes on your lane.

One distinction to hold: the API says where the clip is, as `media_url`, `start` and `end`. The UI makes it something a person can open: a signed link, and a player at the second. Everything this lesson checks is in the first. Step 5 builds the second in your shell.

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

You need the shell in the kit's folder, with `PROJECT`, `REGION`, `API` and `ME` set by the setup above.

- Text-to-Speech. `make apis` enabled `texttospeech.googleapis.com` in Module 0. `make media` calls it with your Application Default Credentials.

- Three packages. Step 4's first line installs Pillow, the Text-to-Speech client and a static ffmpeg, because Cloud Shell has no ffmpeg. The three figures are already drawn and committed, so the drawing libraries are not needed.

- The pin window. The setup moved acme to the kit's own index, which is where the worker writes the video's segments. Step 5 asks acme there.

- What the lesson changes. It adds the town hall video to acme and withdraws the transcript. `make smoke-media` then leaves a generated image in the media bucket and a small probe image in acme's corpus.

### From a segment to a pill, run

The kit's answer contract and the UI's own pill, over three packed sources: a table row, a figure and a clip.

#### Definition

The cell resolves a model's draft against three packed sources, as rag-api does, with the kit's `resolve()`. Then it draws the answer with the UI's own `_label` and `_mmss`, lifted out of `citations.py`, which imports Streamlit. It also names the usage row's modality with the API's `modality_of`. The draft cites the clip, and also a source that is not in the context. Last, the cell applies `run_eval`'s rule for a media row twice: once to an answer citing the clip, once to one citing the table row.

#### The code

#### Do it

- `resolve()` kept the clip's fields: `kind: segment`, the `media_url`, `start` 200.7 and `end` 238.0. They come from the packed chunk the model cited, never from the model. The draft's `[Source 7]` was dropped, because nothing was packed as source 7.

- The UI turned `[3]` into `[Clip 3, 03:20]`. The number is the source's place in the context. The time is its start, cut to the whole second. Under Sources the video plays from second 200, captioned with the clip's window.

- Each kind draws its own pill: a figure `[Fig 2]`, and a text chunk stays `[1]`. A segment with no start draws `[Clip 3, ?]` and plays from second 0.

- `modality_of()`: any segment among the sources makes the row `video`, and a figure without one makes it `image`.

- `run_eval`'s rule is about the kind alone. Citing the clip counts for mm-03. Citing the table row, with the same words, does not.

### The clip built, the transcript withdrawn, the video heard

The town hall synthesised with its ground truth, the text version taken down, the video through the worker, and its segments read back.

#### Definition

`make media MEDIA_ARGS=--video` runs `evals/build_media.py`:

- It keeps the three committed figures.

- It picks two Chirp 3 HD voices by name from the API's list, and synthesises each speaker turn of `townhall_2026_q1.md`, with 0.7 seconds between turns.

- It draws four slides, the first saying the video is synthetic, and muxes slides and speech with ffmpeg.

- It writes the ground truth beside the video: each turn's start and end, measured from the audio it made.

Next, the transcript goes. `upload.sh` keeps a transcript home once its video exists, as it keeps a PDF's text mirror home, but it removes nothing already sent:

`make retire` withdraws it as lesson 7.4 showed. The rows are retired, acme's two managed stores delete their copies, and the ledger row becomes a tombstone. The object stays in the bucket, and `make restore` would bring it back.

Then the video goes up as a new document. `make reindex` copies it into acme's uploads and waits for the worker's line. The worker's media branch describes it in one Gemini call:

Last, read the video's rows from acme's index, and hold them against the ground truth:

- The clip and its ground truth exist. The voices were picked by name, five turns were timed as they were synthesised, and the MP4 was written with `townhall_2026_q1.segments.json` beside it. Both are gitignored. `upload.sh` never sends the JSON, and the nightly walk skips it.

- The transcript is withdrawn: its 1 chunk retired, its copies deleted from acme's stores, its ledger row a tombstone.

- The worker heard the video: `ingest_ok` with 5 chunks, 0 reused and 5 embedded. Each segment's summary is one embedding. Nothing was reused, because this is a new document.

- The segments pass the checks this lesson makes. Each is at most a minute and starts before it ends, and the last one ends within a second of the speech. The EMEA line is quoted in the segment over Arjun's turn.

- Your segments are Gemini's. It cuts your video its own way, so your count, edges and wording differ from these. The checks are what should hold.

### The clip at its second

Golden row mm-03's question, asked as the UI asks it, then checked three ways: the kind, the second and a link that opens there.

#### Definition

The cell asks mm-03's question through `/v1/stream` as `documind-ui-sa`. It reads the events the UI reads, the packed sources first and then the tokens, and draws the answer with the UI's own `_label`. Then it checks three things:

- the kind, by `run_eval`'s rule;

- the second: the cited clip's window against the ground truth's turn in which the CFO says "5.2 per cent";

- a link that opens the video at that second.

The link is a V4 URL signed for 15 minutes as `documind-ui-sa`, the account the UI signs with, which can read the uploads bucket. `#t=` and the start are appended to it. That is a media fragment: the browser's player starts there, and the fragment is never sent to the server, so the signature still holds.

What the model saw of the clip is its summary, under a header that names the file and nothing more:

The time lives only in the citation's fields, and the UI's player reads it from there:

#### Do it

- The pool held the video's segments beside a figure and text. The answer cites the segment with the EMEA line, and the UI draws it as `[Clip 4, 00:22]`. Your number and second are your lane's.

- The kind check passes: a segment was cited, which is what mm-03 asks of the live gate.

- The second check passes: the clip's window holds the turn in which the ground truth puts the CFO's "5.2 per cent".

- The link opens the video there. Paste it into a browser within 15 minutes and the video starts at the clip's second.

That is the first proof: the clip at its second.

### make smoke-media, green

Module 7's gate: five checks against the API and the MCP server.

#### Definition

`make smoke-media` runs `smoke/smoke_media.py` against your API and MCP server, with the tokens minted as `documind-ui-sa` and `documind-outsider-sa`. It makes five checks:

- an image generated as a roster member;

- the same request refused for the outsider, by the roster, not the network;

- a figure question answered with a figure citation;

- the media documents listed through the MCP server's `list_documents`;

- a signed upload URL, a PUT to it, and the worker indexing what was put.

Its MCP legs need fastmcp, which lesson 5.2 installed.

#### Do it

- The image was generated and recorded. The object is named by a hash of the prompt, so the same prompt always makes the same name. The API runs with `DEMO_MODE=1`, as `make up` deploys it, so only the first run draws and pays: every later run is served from the media bucket, `cached=True`, for nothing (lesson 7.6).

- The outsider got a 403 from the roster, after the network had let it in.

- The figure question was answered with a `figure` citation whose `media_url` is the PNG's `gs://` path.

- The MCP listing counts the video among acme's media documents, 21 indexed documents in all on the stand-in; yours include your own uploads.

- The signed PUT went into acme's uploads, and the worker indexed it. The probe image is the same bytes every run, so from the second run on the worker acknowledges it as a document it already holds.

That is the second proof: `make smoke-media` green. The gate asks only the figure question. The clip's citation is step 5's to check.

### Why video works this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- Describe, do not parse. A video has no text layer. A description can be embedded, retrieved and quoted, and the asset rides beside it for a person to open.

- The summary quotes every number. A paraphrase loses the figure the question asks for. What is not in the segment's text cannot be retrieved by it.

- Low media resolution. What was said, and roughly when, does not need text read off the slides. The kit's comment calls resolution a frame-sampling dial, and low is the cheaper setting.

- At most a minute a segment. A citation then opens the reader close to the moment, and a minute's summary is short enough to quote.

- The API says where; the UI opens it. The Citation carries `media_url`, `start` and `end`, and the UI signs a 15-minute link as its own account. No link outlives its quarter of an hour.

- One contract. `kind`, `media_url`, `start` and `end` are optional on the Citation, so every text citation written before them comes through unchanged.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- No gate asks for a clip. `make smoke-media` asks one question, the figure one. A lane whose video was never heard still passes it. Only mm-03 in `make eval-live` asks for a segment.

- Nothing checks the second. `run_eval` asks for a segment of any kind, anywhere in any video. No code in the kit reads the ground truth `build_media.py` writes; `upload.sh` and the walk only skip it. Step 5's check is this lesson's own.

- Gemini's times are kept as given. The worker's `Segment` has no validator. Nothing checks that a segment starts before it ends, keeps to the minute the prompt asks for, or ends inside the video.

- The model is never told when. The `[Source N]` header names the file, a page, a section and a date, never a segment's start. A question about when something was said cannot be answered, though the citation carries the second.

- `media_url` is a `gs://` path, not a link. The Citation's comment calls it a signed URL. But the worker stores the object's path, and the API signs only its upload door, never a citation. The Streamlit UI signs it. A curl caller, the MCP server or an agent gets a path it cannot open without read access to the bucket.

- A video's frames are not scanned. DLP reads an image's pixels, but `inspect_image` returns nothing for a video. Only the summaries are scanned, so text on a slide that is neither spoken nor summarised never reaches DLP.

- A transcript already sent stays beside its video. `upload.sh` skips the transcript once the MP4 exists, but removes nothing, and the walk has no rule for the pair. Step 4 withdraws it by hand.

- Describing media is metered nowhere. The worker reads no usage from its Gemini call, so the cost of hearing a video, or captioning a figure, reaches the bill and no usage row. `tenant_daily` cannot see it.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

acme's corpus now holds the town hall as a video: its segments are in acme's index, and the transcript is withdrawn (`make restore SOURCE=acme/townhall_2026_q1.md` would bring it back). Your kit clone holds the MP4 and its ground truth under `evals/corpus/acme/`, both gitignored. `make smoke-media` left a generated image in the media bucket, and the probe image in acme's corpus. Lesson 7.6 exercises the Studio and the voice features: a generated image and its usage row, and an answer read aloud.

Netsetos GenAI on GCP · Module 7 Graph and multimodal · Lesson 7.5 Query a video clip and validate media citations · v5.0

Next: Lesson 7.6 Exercise implemented Studio and voice features.
