# Lesson B.1: Run Python the way the kit does: venvs, JSON and HTTP calls

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| 3 | [demo_03_the_venv_what_the_setup_block_built_and_why_the_kit_pins.py](demo_03_the_venv_what_the_setup_block_built_and_why_the_kit_pins.py) | The venv: what the setup block built, and why the kit pins |
| 4 | [demo_04_files_and_json_pathlib_json_and_a_jsonl_file.py](demo_04_files_and_json_pathlib_json_and_a_jsonl_file.py) | Files and JSON: pathlib, json and a JSONL file |
| 5 | [demo_05_one_http_call_a_server_on_your_laptop_and_urllib.py](demo_05_one_http_call_a_server_on_your_laptop_and_urllib.py) | One HTTP call: a server on your laptop, and urllib |
| 6 | [demo_06_two_calls_at_once_asyncio_gather_and_asyncio_to_thread.py](demo_06_two_calls_at_once_asyncio_gather_and_asyncio_to_thread.py) | Two calls at once: asyncio.gather and asyncio.to_thread |
| 7 | [demo_07_a_call_the_kit_would_trust_one_retry_a_timeout_a_checked_body.py](demo_07_a_call_the_kit_would_trust_one_retry_a_timeout_a_checked_body.py) | A call the kit would trust: one retry, a timeout, a checked body |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### demo_03_the_venv_what_the_setup_block_built_and_why_the_kit_pins.py

Inside a venv, sys.prefix is the venv's folder and sys.base_prefix is the Python it was made from; outside one, both name the same folder. Python's documentation says that comparing the two is enough to know whether you are in a venv. The cell below asks that, then asks where python and the two libraries come from, and what google-genai brought with it. The cell below makes a second venv in a temporary folder, without even pip in it, and asks that venv's Python the same questions from the inside. Then it deletes the folder. Neither your system's Python nor ~/basics-venv changes, because a venv is only a folder that points at a base Python; Python's documentation calls venvs disposable, meant to be deleted and made again rather than moved or copied.

**`step_01_where_am_i_the_venv_asked_from_inside(session)` — The venv: what the setup block built, and why the kit pins / Where am I? The venv, asked from inside**

Inside a venv, sys.prefix is the venv's folder and sys.base_prefix is the Python it was made from; outside one, both name the same folder. Python's documentation says that comparing the two is enough to know whether you are in a venv. The cell below asks that, then asks where python and the two libraries come from, and what google-genai brought with it.

Operation: bash — run on your laptop, in the shell where the setup block activated ~/basics-venv.

Expected shape, not a promised result:

```text
python 3.12, running from a venv: True
`python` on PATH is the venv's: True
site-packages is inside the venv: True
numpy 2.5.3, installed in that site-packages: True
google-genai 2.22.0, installed in that site-packages: True
google-genai brought 10 more: anyio, distro, google-auth, httpx, pydantic, requests, sniffio, tenacity, typing-extensions, websockets
its rule for google-auth is google-auth[requests]<3.0.0,>=2.56.0; pip chose 2.60.0
```

**`step_02_a_venv_is_a_folder_make_one_ask_it_delete(session)` — The venv: what the setup block built, and why the kit pins / A venv is a folder: make one, ask it, delete it**

The cell below makes a second venv in a temporary folder, without even pip in it, and asks that venv's Python the same questions from the inside. Then it deletes the folder. Neither your system's Python nor ~/basics-venv changes, because a venv is only a folder that points at a base Python; Python's documentation calls venvs disposable, meant to be deleted and made again rather than moved or copied.

Operation: bash — run on your laptop: a second venv in a temporary folder, deleted at the end.

Expected shape, not a promised result:

```text
made throwaway-venv: pyvenv.cfg says include-system-site-packages = false
its python: running from a venv True, numpy importable False, packages installed 0
made from the same base Python as this venv: True
deleted: throwaway-venv exists False; numpy still imports here: True
```

### demo_04_files_and_json_pathlib_json_and_a_jsonl_file.py

The cell below takes four rows of the kit's evals/golden.jsonl (a lookup, a join, a refusal and an isolation row), writes them to ~/basics-b1/golden_sample.jsonl the way the kit writes the real file, and reads them back the way the eval gate does. Then it deletes one comma from a copy of line 1, to show what json.loads says about a broken line.

**`step_01_write_four_golden_rows_read_them_back(session)` — Files and JSON: pathlib, json and a JSONL file / Write four golden rows, read them back**

The cell below takes four rows of the kit's evals/golden.jsonl (a lookup, a join, a refusal and an isolation row), writes them to ~/basics-b1/golden_sample.jsonl the way the kit writes the real file, and reads them back the way the eval gate does. Then it deletes one comma from a copy of line 1, to show what json.loads says about a broken line.

Operation: bash — run on your laptop: writes ~/basics-b1/golden_sample.jsonl.

Expected shape, not a promised result:

```text
wrote ~/basics-b1/golden_sample.jsonl: 875 bytes, 4 lines
read back: 4 rows, equal to what was written: True
line 1 on disk: {"id": "lk-01", "shape": "lookup", "question": "What is the per-trip cap on domestic travel reimbursement?", "tenant": "acme", "must_contain": ["40,000"], "must_retrieve": ["EXP-12", "hr_policy_2026"], "answerable": true}
lk-01: answerable True is a bool, must_contain ['40,000'] is a list
iso-01 asks zeta what lk-01 asks acme: it must contain ['25,000'], never ['40,000']
answerable: 3 of 4 | shapes: lookup, join, refusal, isolation
the line with one comma lost: Expecting ',' delimiter (line 1, column 35)
```

### demo_05_one_http_call_a_server_on_your_laptop_and_urllib.py

An HTTP request is a method (GET to read, POST to send something), a URL, a set of headers and, for a POST, a body. The response is a status code, its own headers and a body. Everything else is one of those: the ID token is a header, the question is the body. 127.0.0.1 is the loopback address, your own machine, and a server bound to it can be called only from that machine, so nothing in this step leaves your laptop. The cell below starts a stand-in API in a background thread, with http.server from the standard library and three routes: GET /health; POST /v1/query, which refuses a request that has no bearer token; and a 404 for anything else. Then it calls the server four times with urllib.request, the way the kit's smoke test calls the real API: health, a question with a token (the eval gate's request body for row lk-01), the same question with no token, and a path that does not exist. The server keeps its own log, so you see each call from both ends.

**`step_01_one_http_call_a_server_on_your_laptop_and(session)` — One HTTP call: a server on your laptop, and urllib / One HTTP call: a server on your laptop, and urllib**

An HTTP request is a method (GET to read, POST to send something), a URL, a set of headers and, for a POST, a body. The response is a status code, its own headers and a body. Everything else is one of those: the ID token is a header, the question is the body. 127.0.0.1 is the loopback address, your own machine, and a server bound to it can be called only from that machine, so nothing in this step leaves your laptop. The cell below starts a stand-in API in a background thread, with http.server from the standard library and three routes: GET /health; POST /v1/query, which refuses a request that has no bearer token; and a 404 for anything else. Then it calls the server four times with urllib.request, the way the kit's smoke test calls the real API: health, a question with a token (the eval gate's request body for row lk-01), the same question with no token, and a path that does not exist. The server keeps its own log, so you see each call from both ends.

Operation: bash — run on your laptop: a server on 127.0.0.1, stopped at the end; nothing leaves the machine.

Expected shape, not a promised result:

```text
GET  /health           -> 200 {"status": "ok"}
POST /v1/query   token -> 200 {"received": {"query": "What is the per-trip cap on domestic travel reimbursement?", "tenant_id": "acme", "top_k": 6}, "content_type": "application/json"}
POST /v1/query         -> 401 {"detail": "no bearer token"}
GET  /v1/missing       -> 404 {"detail": "no route GET /v1/missing"}
the server's log: GET /health 200 | POST /v1/query 200 | POST /v1/query 401 | GET /v1/missing 404
```

### demo_06_two_calls_at_once_asyncio_gather_and_asyncio_to_thread.py

A call to the API, or to Gemini, is mostly waiting: the request goes out, the other side works, the answer comes back, and your program does nothing in between. Two calls made one after the other wait twice. asyncio lets one program wait on both at once. A function written async def is a coroutine; inside it, await marks each place where it waits; and the event loop that asyncio.run() starts runs another coroutine while one waits. asyncio.gather() runs several and returns their results as a list, in the order you passed them, not the order they finished. There is one catch, and the cell below is built to show it. The loop can switch only at an await, and urllib is synchronous: it never awaits, so while it waits it holds the whole thread, loop and all. asyncio.to_thread() is the way out. It runs an ordinary blocking function in a separate thread and gives the loop something to await, which is what Python's documentation says it is for. The cell's server takes half a second over every answer, a stand-in for a slow model, and notes whether a request arrived while another was still being served.

**`step_01_two_calls_at_once_asyncio_gather_and_async(session)` — Two calls at once: asyncio.gather and asyncio.to_thread / Two calls at once: asyncio.gather and asyncio.to_thread**

A call to the API, or to Gemini, is mostly waiting: the request goes out, the other side works, the answer comes back, and your program does nothing in between. Two calls made one after the other wait twice. asyncio lets one program wait on both at once. A function written async def is a coroutine; inside it, await marks each place where it waits; and the event loop that asyncio.run() starts runs another coroutine while one waits. asyncio.gather() runs several and returns their results as a list, in the order you passed them, not the order they finished. There is one catch, and the cell below is built to show it. The loop can switch only at an await, and urllib is synchronous: it never awaits, so while it waits it holds the whole thread, loop and all. asyncio.to_thread() is the way out. It runs an ordinary blocking function in a separate thread and gives the loop something to await, which is what Python's documentation says it is for. The cell's server takes half a second over every answer, a stand-in for a slow model, and notes whether a request arrived while another was still being served.

Operation: bash — run on your laptop: the same kind of server, slowed down on purpose.

Expected shape, not a promised result:

```text
one after the other            ['a', 'b']  about 2 waits, both in flight at once: False
gather over blocking calls     ['a', 'b']  about 2 waits, both in flight at once: False
gather over asyncio.to_thread  ['a', 'b']  about 1 wait, both in flight at once: True
```

### demo_07_a_call_the_kit_would_trust_one_retry_a_timeout_a_checked_body.py

Three ways a real service lets a caller down, and the kit's rule for each, run against a server that misbehaves on purpose. The call in step 5 assumed the server answers, answers once and answers well. A real service can be briefly overloaded, can hang, or can answer 200 with an empty body. The kit's eval gate has a rule for each: give every call a timeout; retry a 5xx, a timeout or a transport error once, after a pause, and never a 4xx; and count a 200 as a failed request until its body has the right shape. The last two date from 12 September 2026, the day its docstring says the gate "learned to fail". The cell below gives a stand-in server three routes that misbehave on purpose and calls each one under those rules.

**`step_01_a_call_the_kit_would_trust_one_retry_a_tim(session)` — A call the kit would trust: one retry, a timeout, a checked body / A call the kit would trust: one retry, a timeout, a checked body**

Three ways a real service lets a caller down, and the kit's rule for each, run against a server that misbehaves on purpose. The call in step 5 assumed the server answers, answers once and answers well. A real service can be briefly overloaded, can hang, or can answer 200 with an empty body. The kit's eval gate has a rule for each: give every call a timeout; retry a 5xx, a timeout or a transport error once, after a pause, and never a 4xx; and count a 200 as a failed request until its body has the right shape. The last two date from 12 September 2026, the day its docstring says the gate "learned to fail". The cell below gives a stand-in server three routes that misbehave on purpose and calls each one under those rules.

Operation: bash — run on your laptop: a server that misbehaves on purpose.

Expected shape, not a promised result:

```text
/flaky -> 200 {"answer": "", "citations": [], "answerable": false, "confidence": "low"} | asked 2 times | an answer: True
/hang  -> 0 {"error": "TimeoutError"} | asked 2 times | an answer: False
/empty -> 200 {} | asked 1 time | an answer: False
```

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_B.1_Python_Basics_WIX.html`. All 35 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `b482dea9a2284388eb04f3568de55f25c04ffeac`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
