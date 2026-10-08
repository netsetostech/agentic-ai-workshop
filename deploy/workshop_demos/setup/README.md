# Setup and reusable functions

Run these files with the same interpreter as the demos. They replace repeated shell setup without hiding the lesson's experiment.

| File or helper | Why it exists | When to use it |
|---|---|---|
| `bootstrap.py` | Installs `workshop_helpers` into the selected interpreter; preserves local settings | First setup, or after changing interpreters |
| `install_dependencies.py` | Installs a chosen set of the kit's own requirements using that same interpreter | When the operator/local lane dependencies are missing |
| `authenticate.py` | Refreshes Python ADC through interactive gcloud login | On an ADC reauthentication error |
| `check_setup.py` | Checks Firestore, uploads access and serving API configuration | Before lessons on an already deployed lane |
| `update_kit.py` | Updates the currently tracked Git branch without discarding edits | For an authorized kit refresh |
| `start_new_session.py` | Archives the active pointer after cleanup, retaining all evidence | To restart a lesson from its first example |
| `recover_session.py` | Verifies a stopped process before removing its leftover lock | After a terminated IDE process left a lock |
| `DemoSession` | Makes separate Run/Debug launches share one lesson's identity and progress | Every demo entry point |
| `session.set_environment(**values)` | Shares nonsecret values with later Python and command checkpoints | When a Python example changes a lesson variable |
| `session.service_environment(service, keys)` | Reads literal settings from the actual serving revision as JSON | Before comparing the API's retrieval/embedding configuration |
| `session.command(args)` | Executes a CLI argument list with visible output and real exit status | Make, gcloud and existing kit scripts |
| `session.shell(code)` | Preserves reviewed variables and functions across Bash workflows | Multi-command examples from the main HTML |
| `session.pin_vector()` / `restore_backend()` | Saves and restores the actual prior tenant pin | Lessons that temporarily demonstrate the vector lane |
| `session.start_local_service()` / `stop_local_service()` | Owns a local process without holding an IDE run open indefinitely | Module 0's local chat experiment |
| `workshop_helpers.reconciliation` | Explains decisions using the kit's real planner | Lesson 1.8's offline queued/default/known-bytes examples |
| `steps.wait_after(session, identifier, seconds)` | Uses the shutdown timestamp from this lesson, even in a previous section file | Monitoring observations after a required idle interval |
| `cleanup.finish_lesson(session)` | Calls the mapped cleanup files and attempts every remaining restoration | The lesson's `setup/finish.py` entry point |
| `lesson31.contract_step(function)` | Supplies clients/saved versions while retaining authored contract functions and step checkpoints | Lesson 1.1's numbered contract examples |

`config/settings.example.json` documents the accepted configuration keys. Bootstrap creates the ignored `settings.local.json`; `WORKSHOP_DEMO_CONFIG` can select a different local file if needed. `kit_root: "auto"` resolves relative to the installed helper, independent of the IDE working directory. The selected interpreter's directory is placed first on PATH for child commands.

Setup does not create an index, invent an endpoint ID or renew credentials invisibly. A lesson either discovers its resource from the serving configuration or runs the real kit provisioning step that introduces it. Split traffic requires an explicit decision because one environment snapshot cannot describe two serving revisions.

The original small helper modules (`config`, `auth`, `discovery`, `api`, `artifacts`, `kit`, `context`, `reconciliation`) provide reusable operations. `DemoSession` adds cross-file state, ordered attempts and the CLI bridge used by the full course. Native examples execute in the lesson's `demonstrate` function so their educational logic remains visible to the debugger.

## Grouped experiments

`steps.run_steps(session, steps)` calls the lesson’s named functions and saves a checkpoint after each successful function. `manual_checkpoint()` pauses for browser actions or delayed observations. Failed/interrupted functions need explicit retry after inspection; successful functions are skipped on resume. Cleanup tries every restoration and reports all failures. Each source cell keeps an independent import path/module context, so successive examples can load the kit’s different `config` modules without reusing the wrong one.

`steps.backup_files()` and `restore_files()` preserve exact learner bytes before/after evaluation edits. `gates.expect_failure()` validates the intended nonzero exit and diagnostic; `gates.live_gate()` retains fresh evaluation reports for inspection. `poison` limits the lesson 1.5 drill and cleanup to its saved object generation. All state, ownership records and logs stay in the ignored results directory.

For lessons 2.2–2.4, 3.4, 3.5 and 3.7, preparation saves and temporarily disables an enabled answer cache to expose retrieval/generation. This can create an API revision and affects its tenants; finish restores the original setting. Module 6's caching lessons (6.2–6.4) intentionally demonstrate caching and are unchanged. Lesson 2.3 checks actual response stages before accepting a comparison.
