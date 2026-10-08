# Lesson B.1: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_B.1_Python_Basics_WIX.html`, reviewed at blob `b482dea9a2284388eb04f3568de55f25c04ffeac`. Learners read that page on the course site; this guide keeps its prose.

The DocuMind kit is 11 services and the Python that builds, tests and feeds them, and three habits run through all of it. Every service runs in an environment of its own with pinned libraries; data moves as JSON; and the parts talk to each other over HTTP. This page practises each habit on your laptop, with Python's standard library and the venv the setup block makes, and then shows you the kit's own lines doing the same. You will make a venv and delete it, write and read a file shaped like the kit's golden set, start a small web server and call it, make two calls at once, and give a call the timeout, the retry and the check the kit gives its own.

- What the kit's Python does, in three habits

- The words: venv, site-packages, pin, JSON, JSONL, status code, token, event loop

- Before you run anything: set up your laptop

- The venv: what the setup block built, and why the kit pins

- Files and JSON: pathlib, json and a JSONL file

- One HTTP call: a server on your laptop, and urllib

- Two calls at once: asyncio.gather and asyncio.to_thread

- A call the kit would trust: one retry, a timeout, a checked body

- Verify it yourself: the checklist

You will learn the three habits under every DocuMind service: an environment of its own with pinned libraries, JSON in and out, and HTTP between the parts, with async to keep several calls in flight. Then you will prove each one on your laptop with nothing but Python's standard library, and read the kit's own lines that do the same.

### What the kit's Python does, in three habits

An environment of its own, JSON in and out, HTTP between the parts, and what async adds to the third.

An environment of its own. Each of the kit's 11 services has a folder under `services/`, and in it a `requirements.txt` that names the libraries the service needs, each with `==` and one exact version: 127 lines across the 11 files, and not one of them without a version. 8 of the services build their image from `python:3.12-slim` and install their file into it; the other 3 start from a vendor's image (vLLM, LiteLLM and Ollama). Where two services use the same library they pin the same version, and the kit's dry run fails if they do not. On your laptop a virtual environment, a venv, does the image's job: a folder with its own Python and its own libraries, so that what one project installs cannot break another.

JSON in and out. A question to the DocuMind API is a JSON object, and so is its answer. The golden set the eval gate runs is a file of JSON objects, one per line, and every usage row the API writes to its log is a JSON object that Cloud Logging turns into fields. Python's `json` module does both directions: `json.dumps()` turns a dict into text, and `json.loads()` turns the text back into a dict.

HTTP between the parts. The UI, the chat service, the smoke test and the eval gate all reach the API the same way: an HTTP request to a URL, with an ID token in the `Authorization` header and, for a question, a JSON body; back comes a status code and a JSON body. A call like that spends most of its time waiting for the other side, and async is how one program waits on several calls at once instead of one after another.

A dabbawala's tiffin. Every morning in Mumbai a tiffin leaves a home with one person's lunch in it, packed in its own sealed tins, so that nobody's dal ends up in anybody else's rice. That is a venv: one project's libraries, at the versions it was tested with, in a box of their own. On the lid is a painted code that every dabbawala reads the same way, from the station to the office floor. That is JSON: a format both ends agree on, so what was packed in Andheri is read correctly at Churchgate. The tiffin goes out full and comes back empty in the afternoon: one request, one response, which is HTTP. And no dabbawala carries one tiffin at a time; he carries a crate of them on the same train and hands each one over as its stop comes. That is async: one worker, many deliveries in flight.

#### The three habits in one of the kit's own loops

The eval gate's live half (Module 4 runs it against your lane with `make eval-live`) uses all three in a few dozen lines. Follow one row of the golden set through it. Every value below is read from the kit when this page is built.

Steps 3 to 7 below are these moves on your laptop: the environment (step 3), the file (step 4), the call (step 5), several calls at once (step 6), and the checks a call needs before anyone trusts its answer (step 7). The gate also scores each answer against its row; that half belongs to Module 4.

#### Try it: the kit's pins, file by file

The explorer below holds every `requirements.txt` in the kit as it stood when this page was built: the 11 services' files, and the one under `shared/` for the tool layer in `shared/documind_tools.py`. Pick a file to see what it pins. Then change the chosen library's version, or tick the box to drop its version altogether, and read what the kit's dry run would say: its two checks are ported here rule for rule.

A teal pin is pinned by at least one other file, and the number after it counts the files that pin that library. The page opens on rag-api's `google-genai==2.22.0`, the version the setup block installs on your laptop. Type `2.20.0` in the version box and the pins check fails the way `validate.py` does, naming every file and its version. Tick the box instead and the requirements check warns. The requirements check reads the 11 service files; the pins check reads those and `shared/requirements.txt`, 12 files. The port was compared with `validate.py` itself on all 258 one-pin changes (every pin given another version, then none) when this page was built.

It reads the files and applies the two checks; it is not pip. It cannot tell you whether a version exists, or whether a set of versions can be installed together. pip answers those when an image is built, and the dry run builds every Python image with Docker when it runs in CI.

### The words: venv, site-packages, pin, JSON, JSONL, status code, token, event loop

Ten terms, each with where it shows up in the kit.

Three of these words are the habits from step 1, and the rest are how they work. Each habit gets a cell of its own below, run on your laptop, followed by the kit's lines that do the same thing at full size.

### Before you run anything: set up your laptop

Every cell on this page runs on your own laptop, in a bash shell: the Terminal on macOS or Linux, WSL or Git Bash on Windows, or Cloud Shell in a browser. The Python is 3.12, the version the kit's services run in their images (`python:3.12-slim`), inside a virtual environment of its own, `~/basics-venv`, so nothing is installed into the Python your system uses. Most cells need no account and no network. The cells that call Gemini need the Google Cloud project you create in lesson 0.1 and Application Default Credentials, and their labels say so.

Set up the venv once. The block below finds a Python 3.12 or newer, makes the venv the first time and activates it every time after. Then it installs the two libraries the Basics pages use, at fixed versions: numpy for the arithmetic, and google-genai, at the version the kit pins, for the calls to Gemini. The last line proves both import.

The cells that call Gemini need two more things: your project from lesson 0.1, and Application Default Credentials, the sign-in Google's client libraries read. Run the block below once, after lesson 0.1, in the same shell; the browser opens for the sign-in. It uses the gcloud CLI, which lesson 0.2 installs on a laptop and Cloud Shell already has. As in the kit, Gemini 3 models are called on the `global` location and the embedding model on `us-central1`.

### The venv: what the setup block built, and why the kit pins

The setup block read one line at a time; the venv asked where it lives; a second venv made, asked and deleted; then the kit's images, its pins and the check that holds them.

#### What the setup block did

The block you ran in the setup section is six lines, and each one is a habit of the kit's, scaled down to one laptop.

#### Where am I? The venv, asked from inside

Inside a venv, `sys.prefix` is the venv's folder and `sys.base_prefix` is the Python it was made from; outside one, both name the same folder. Python's documentation says that comparing the two is enough to know whether you are in a venv. The cell below asks that, then asks where `python` and the two libraries come from, and what google-genai brought with it.

The first five lines are the venv doing its job. The last two are the reason the kit pins. You asked pip for two libraries and pinned both. google-genai 2.22.0 brought 10 more, and its own metadata pins none of them: each comes with a range of versions it accepts, and sniffio with no limit at all. For `google-auth` the range is 2.56.0 or newer, but older than 3.0.0. pip took the newest version inside that range on the day the setup block ran: 2.60.0 when this page was built, perhaps a newer one on your laptop. That is fine for a scratch venv. It is not fine for a service, where "the newest on the day" means two builds a week apart can run different code. The kit pins `google-auth==2.57.1` in 7 of its 11 services, so each of those images gets exactly that version, whatever is newest.

#### A venv is a folder: make one, ask it, delete it

The cell below makes a second venv in a temporary folder, without even pip in it, and asks that venv's Python the same questions from the inside. Then it deletes the folder. Neither your system's Python nor `~/basics-venv` changes, because a venv is only a folder that points at a base Python; Python's documentation calls venvs disposable, meant to be deleted and made again rather than moved or copied.

The new venv ran the same base Python as yours and still could not see numpy, because it had a `site-packages` of its own with nothing in it. `include-system-site-packages = false` is the line in `pyvenv.cfg` that keeps the base Python's own libraries out as well. Deleting the folder removed the venv completely, and nothing else noticed.

#### The kit's environment: an image and one file

None of the kit's Dockerfiles makes a venv. A service's image is its environment: a fixed Python, one `requirements.txt` installed into it, and nothing installed afterwards. This is the top of rag-api's Dockerfile:

Two of those lines do your setup block's work. `FROM python:3.12-slim` fixes the Python, as the second line of the block did. `RUN pip install --no-cache-dir -r requirements.txt` installs the pins, as the fifth line did, but from a file instead of the command line. Nothing is activated, because the image holds one Python for one service. The other side of that is strict: a library the code imports but the file does not name is simply not there. The chat service learned it the hard way, and kept the note at the top of its file:

#### Pinned, and pinned the same: two of the dry run's checks

The kit holds these files to two rules: every line carries a version, and a library that two files share carries the same version in both. Both rules are checks in `validate.py`, the kit's offline dry run, which lesson 0.2 runs on your clone with `make dryrun`. The second check's docstring gives its reason: two services on two versions of google-genai, and a demo that fails with a 400 that gets blamed on the model.

The explorer in step 1 runs exactly these two rules, which is how it can show you what one drifted pin would do. Notice the tools the two functions reach for: `SERVICES.rglob("requirements.txt")` to find every file of that name in a folder tree, `read_text(encoding="utf-8").splitlines()` to read one, and a regular expression to split `name==version`. Those are the next step's tools.

You asked your venv where it lives and got four plain answers: it is a venv, its `python` is the one on `PATH`, its libraries are in its own `site-packages`, and the two you pinned are the versions you asked for. You made a venv from nothing and deleted it, which is all a venv is. And you read the two rules the kit adds for services, where "whatever pip picks today" is not good enough: pin every line, and pin a shared library to the same version everywhere.

### Files and JSON: pathlib, json and a JSONL file

A path as an object, JSON's kinds of value and their Python twins, and a JSONL file written and read back the way the kit writes and reads its golden set.

pathlib makes a path an object. `Path.home()` is your home folder on any operating system, and `/` joins parts, so `Path.home() / "basics-b1"` needs no slash or backslash typed by hand. The path itself can make the folder, open the file, read it whole and report its size. JSON is text with a few kinds of value, and the `json` module turns each into a Python type and back:

A JSONL file, JSON Lines, is one JSON value per line: UTF-8, a newline after each value, no blank lines. The shape suits datasets. Rows are written and read one at a time, a new row is one more line at the end, and each line can be checked on its own. The kit keeps 5 of its datasets this way, 948 lines in all, the golden set among them.

#### Write four golden rows, read them back

The cell below takes four rows of the kit's `evals/golden.jsonl` (a lookup, a join, a refusal and an isolation row), writes them to `~/basics-b1/golden_sample.jsonl` the way the kit writes the real file, and reads them back the way the eval gate does. Then it deletes one comma from a copy of line 1, to show what `json.loads` says about a broken line.

Line 1 of your file is byte for byte line 1 of the kit's golden set: the same dict, with its keys in the same order, through the same `json.dumps`. The JSON `true` came back as Python's `True` and the array as a list, as the table promised. And the error says what is wrong and where: line 1, because `json.loads` was given one line, and column 35, where it found `"question"` when it wanted a comma.

#### The kit's writer and reader

Three details are worth copying. `newline="\n"` makes the file the same bytes on Windows as on Linux; without it, Python on Windows ends every line with `\r\n`. `ensure_ascii=False` writes a ₹ or a Hindi word as itself, in UTF-8, where the default writes the escape `\u20b9` in its place; the golden set happens to be plain ASCII, so your file's bytes are the same either way. And the reader's `if line.strip()` skips a blank line instead of failing on it, so a file that ends with an extra empty line still loads.

#### JSON is also the kit's log line

The same `json.dumps` carries the kit's telemetry. rag-api logs bare JSON to standard output, one object per line, and Cloud Run stores each line as a structured entry whose fields can be searched and filtered; the usage row every answer writes is `json.dumps(row)`:

That one line is where the kit's cost reporting starts. A log sink copies every row whose `event` field is `query` into BigQuery, where the `tenant_daily` view adds them up per tenant and per day, in rupees as well as dollars. The `event` field is there to filter on only because the row was written as JSON.

You wrote a dataset with `pathlib` and `json.dumps`, one object per line, and read it back with a list comprehension over the file: the kit's writer and reader, at the scale of four rows. You saw JSON's types land as Python's, and a broken line fail loudly instead of quietly. The same two functions write the kit's request bodies and its log, which is why they carry most of the next two steps.

### One HTTP call: a server on your laptop, and urllib

A request and a response with both ends written by you; the status codes the kit tests for; then the kit's own call, and the token it carries.

An HTTP request is a method (`GET` to read, `POST` to send something), a URL, a set of headers and, for a POST, a body. The response is a status code, its own headers and a body. Everything else is one of those: the ID token is a header, the question is the body. `127.0.0.1` is the loopback address, your own machine, and a server bound to it can be called only from that machine, so nothing in this step leaves your laptop.

The cell below starts a stand-in API in a background thread, with `http.server` from the standard library and three routes: `GET /health`; `POST /v1/query`, which refuses a request that has no bearer token; and a 404 for anything else. Then it calls the server four times with `urllib.request`, the way the kit's smoke test calls the real API: health, a question with a token (the eval gate's request body for row lk-01), the same question with no token, and a path that does not exist. The server keeps its own log, so you see each call from both ends.

Four things in that output are most of what this course needs from HTTP. The `200`s carry JSON bodies that `json.loads` turns straight into dicts. The server read your body as a dict too, and the `Content-Type` header is how it knew to expect JSON. The `401` and the `404` are answers, not crashes: urllib raises `HTTPError` for any 4xx or 5xx, and Python's documentation describes that exception as a response as well, with the status in `e.code` and the body readable from it, which is why `call()` catches it and returns both. And `http.server` is for exactly this kind of test: its documentation says it is not recommended for production, and rag-api runs FastAPI under gunicorn instead.

One line in the cell is not in the kit: the opener built with an empty `ProxyHandler`. `urlopen` sends a request through any proxy your shell's `HTTP_PROXY` names, which many company laptops set, and a proxy cannot reach your laptop's `127.0.0.1`. The opener calls the server directly, whatever the shell says.

#### The kit's call, and the token it carries

The smoke test that lesson 0.4 runs against your lane is built from the same parts, and its docstring says so:

Set the two side by side. The kit's `call()` builds a `Request`, adds the bearer token and the JSON content type, opens it with a 30-second timeout, and turns an `HTTPError` into a status and a body instead of a crash. That is your `call()`, with one more branch at the end for a call that got no answer at all; step 7 adds the same branch. The token is the part your stand-in faked. On a lane it is a Google-signed ID token, and the smoke test asks gcloud for one: minted as the UI's service account, for the API's own URL, with the account's email inside.

The image carries the one-line version of your first call as well. The container's health check, which Docker runs inside it, opens `/health` with urllib, and the line after it starts the server that answers:

You ran both ends of an HTTP call on one laptop. The client sent a method, a path, headers and a JSON body; the server read them and answered with a status and a JSON body; and the two refusals came back as data you could print, not as a crashed program. That is the smoke test's `call()`, minus a real token, and the next step makes two such calls at once.

### Two calls at once: asyncio.gather and asyncio.to_thread

Why waiting is the expensive part of a call, why `async def` alone changes nothing, and how the kit keeps a blocking call off its event loop.

A call to the API, or to Gemini, is mostly waiting: the request goes out, the other side works, the answer comes back, and your program does nothing in between. Two calls made one after the other wait twice. asyncio lets one program wait on both at once. A function written `async def` is a coroutine; inside it, `await` marks each place where it waits; and the event loop that `asyncio.run()` starts runs another coroutine while one waits. `asyncio.gather()` runs several and returns their results as a list, in the order you passed them, not the order they finished.

There is one catch, and the cell below is built to show it. The loop can switch only at an `await`, and urllib is synchronous: it never awaits, so while it waits it holds the whole thread, loop and all. `asyncio.to_thread()` is the way out. It runs an ordinary blocking function in a separate thread and gives the loop something to await, which is what Python's documentation says it is for. The cell's server takes half a second over every answer, a stand-in for a slow model, and notes whether a request arrived while another was still being served.

The first two runs took the same time, and the server never had both requests at once: putting a blocking call inside `async def` changes how it is written, not how it behaves. Only the third run overlapped, and it finished in about 1 wait instead of 2 because the two waits happened together. All three returned `['a', 'b']` in that order, which for `gather` is a promise, not luck.

#### asyncio in the kit

The kit's services run on event loops. rag-api's last Dockerfile line, in step 5, starts gunicorn with 2 uvicorn workers: 2 processes, each with an event loop that serves many requests at once. So the kit follows the two rules your cell just proved. First, a plain script that needs an async library enters the loop with `asyncio.run()`, the way the MCP smoke test (Module 5) calls an async client:

Second, on a loop, a blocking call goes to a thread. When the chat service's door needs to know whose question it is holding, it asks the roster, and the roster is a Firestore query that holds its thread until Firestore answers:

So the door never calls it on the loop. It awaits it in a thread, and the loop goes on serving every other request in that worker meanwhile:

And where two pieces of work should overlap inside one request, the chat service starts the second as a task of its own. Every turn the door hands to the chat brain also runs the routed Desk's shadow hook, which does nothing unless the tenant has the Desk in shadow mode, and then decides what the Desk would have done and logs it without touching the answer (lesson 10.4). `asyncio.create_task` starts the hook beside the turn, the `finally` makes the request wait for both, and `_quietly` makes sure the hook can never fail the turn:

You timed the same two calls three ways and saw that only threads waiting together save time, however the code is spelled. The kit's services live on event loops, so they do the same: a script enters the loop with `asyncio.run()`, a blocking roster read goes to `asyncio.to_thread()`, and a side task runs beside the turn with `create_task` and is awaited before the request ends.

### A call the kit would trust: one retry, a timeout, a checked body

Three ways a real service lets a caller down, and the kit's rule for each, run against a server that misbehaves on purpose.

The call in step 5 assumed the server answers, answers once and answers well. A real service can be briefly overloaded, can hang, or can answer `200` with an empty body. The kit's eval gate has a rule for each: give every call a timeout; retry a 5xx, a timeout or a transport error once, after a pause, and never a 4xx; and count a 200 as a failed request until its body has the right shape. The last two date from 12 September 2026, the day its docstring says the gate "learned to fail". The cell below gives a stand-in server three routes that misbehave on purpose and calls each one under those rules.

The blip cost one retry and the caller never saw it. The hang cost two timeouts and came back as data, status 0 and the exception's name, instead of freezing the program. The empty 200 was the most dangerous of the three: its status said success, and only the shape check said it was not an answer.

#### The kit's rules, in its own words

The docstring gives the reason in a line: "one retry separates a blip from an outage, more would hide one." With three or five retries the hang above would have taken much longer and still failed, and a real outage would have looked like a slow day. A 4xx is not retried at all: it says the request itself was refused, and sending it again changes nothing.

The kit's shared tool layer, which every agent brain calls to search the documents, uses the `requests` library instead of urllib. It keeps the timeout (`RAG_TIMEOUT_S`, 20 seconds unless it is set) and, like the cell's `get()`, returns a failure as data, so the agent can explain it instead of the turn dying on an exception. It does not retry, and it mints a fresh ID token for every call, for a reason its docstring gives:

You gave a call the three things the kit never leaves out: a timeout, so a hang ends; one retry, so a blip passes and an outage still shows; and a check of the body, so a 200 has to earn the word "answer". Every HTTP call the later modules make, from the smoke test to the agents' tools, is built on these rules.

### Verify it yourself: the checklist

Ten checks, each one cell above, each with the line that proves it on your laptop.

One new folder, `~/basics-b1`, holding `golden_sample.jsonl`: 875 bytes, four rows. The throwaway venv was made and deleted inside its cell, and the three servers listened on `127.0.0.1` only while their cells ran. Nothing was installed beyond the setup block's two libraries, nothing left your machine, and nothing cost anything. Lesson B.2 uses the same `~/basics-venv` to count a sentence's tokens and price them, and to compare two embeddings; those cells call Gemini, so they need your project from lesson 0.1 and the sign-in from the second half of the setup section.

Netsetos GenAI on GCP · Basics · Lesson B.1 Run Python the way the kit does: venvs, JSON and HTTP calls · v5.0

Next: Lesson B.2 Turn text into tokens and embeddings.
