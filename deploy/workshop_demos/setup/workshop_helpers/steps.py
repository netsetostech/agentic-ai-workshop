"""Run documented functions as one resumable experiment in the IDE.

The lesson keeps the teaching code. This helper supplies only orchestration:
successful functions are checkpoints, manual actions pause, and a failed or
interrupted function needs an explicit retry decision because it may have made
partial changes. These checkpoints cannot make cloud operations transactional.
"""
from contextlib import contextmanager
from datetime import datetime
import hashlib
import os
from pathlib import Path
import sys
import time

from .session import secret_name, utc_now


class ManualCheckpoint(RuntimeError):
    """A browser action or asynchronous wait has not been acknowledged yet.
    
    Example: ManualCheckpoint('Action pending; rerun this demo when ready.')
    """


def wait_after(session, identifier, seconds):
    """Sleep only what remains of ``seconds`` since a lesson step completed.

The page sleeps a fixed interval after an operation such as make off. The IDE also
pauses there, so a learner who stopped and came back has already waited: count
from the recorded completion instead of starting the interval again.

Example: section 6 calls wait_after(session, "source_17", 600) after section 5
has shut down the lane. The original timestamp is retained across IDE launches.
"""
    checkpoints = session.state.get("function_checkpoints", {})
    matches = [group[identifier] for group in checkpoints.values() if identifier in group]
    if len(matches) > 1:
        raise RuntimeError(f"Ambiguous step {identifier}; inspect this lesson's saved checkpoints.")
    record = matches[0] if matches else {}
    if record.get("status") != "completed" or not record.get("finished_at"):
        raise RuntimeError(f"{identifier} has not completed in this lesson; the interval starts when it does.")
    elapsed = time.time() - datetime.fromisoformat(record["finished_at"]).timestamp()
    if elapsed < seconds:
        print(f"Waiting {seconds - elapsed:.0f}s more: {seconds // 60} minutes after {identifier} completed.", flush=True)
        time.sleep(seconds - elapsed)
    else:
        print(f"{elapsed / 60:.0f} minutes have passed since {identifier} completed; no further wait.")


def manual_checkpoint(instruction):
    """Pause before a dependent read; EOF/stop never counts as completed work.
    
    Example: manual_checkpoint("Upload the exact visitor note, then refresh until indexed")
    """
    print("\nMANUAL CHECKPOINT:", instruction, flush=True)
    try:
        answer = input("Type done after completing that action, or stop to resume later: ")
    except (EOFError, KeyboardInterrupt) as error:
        raise ManualCheckpoint("Action pending; rerun this demo when ready.") from error
    if answer.strip().lower() != "done":
        raise ManualCheckpoint("Action pending; rerun this demo when ready.")


@contextmanager
def native_context(session):
    """Give each source cell its original import/cwd boundary, with real breakpoints.
    
    Cells formerly ran in separate interpreters and can import kit modules with
    generic names such as config/retriever. Remove newly loaded kit modules after
    each cell so a previous cell's import path cannot select the next one's module.
    Third-party modules and the workshop helper itself remain loaded normally.
    
    Example: native_context(session)
    """
    before_path, before_cwd, before_modules = list(sys.path), Path.cwd(), dict(sys.modules)
    kit = session.config.kit_root.resolve()
    try:
        yield
    finally:
        sys.path[:] = before_path
        os.chdir(before_cwd)
        for name, module in list(sys.modules.items()):
            if name.startswith("workshop_helpers") or module is before_modules.get(name):
                continue
            filename = getattr(module, "__file__", None)
            if filename and Path(filename).resolve().is_relative_to(kit):
                if name in before_modules:
                    sys.modules[name] = before_modules[name]
                else:
                    sys.modules.pop(name, None)


def run_steps(session, steps, *, retry_failed=False, cleanup=False, finalize=True):
    """Call ordered ``(identifier, function)`` pairs and save each actual outcome.
    
    On resume, completed functions are skipped. Set RETRY_FAILED_STEP=True in the
    demo only after inspecting the failed function's logs/resources. REPEAT=True
    deliberately replays the entire file. Cleanup attempts every restoration even
    if one fails, retaining failures for the next cleanup attempt. A single cleanup
    section uses finalize=False; setup/finish.py closes the entire run afterward.
    
    Example: run_steps(session, [("read", inspect_rows), ("compare", compare_rows)])
    """
    all_progress = session.state.setdefault("function_checkpoints", {})
    if session.live and session.script.name.startswith("demo_"):
        while session.state.get("pin_ready_after", 0) > time.time():
            remaining = session.state["pin_ready_after"] - time.time()
            print(f"Allowing the API tenant-setting cache to expire: {remaining:.0f}s", flush=True)
            time.sleep(min(5, max(0, remaining)))
    progress = all_progress.setdefault(session.step["id"], {})
    if session.repeat:
        progress.clear()
    errors = []
    for identifier, function in steps:
        previous = progress.get(identifier, {})
        if previous.get("status") == "completed":
            print("Already completed:", function.__name__)
            continue
        if previous.get("status") in {"failed", "running"} and not retry_failed and not cleanup:
            raise RuntimeError(f"{function.__name__} previously failed or was interrupted. Inspect its partial effects and evidence, then set RETRY_FAILED_STEP=True to retry that function. Completed functions will stay skipped.")
        record = {"function": function.__name__, "status": "running", "started_at": utc_now(),
                  "attempt": str(session.attempt)}
        progress[identifier] = record
        session.save()
        print(f"\n--- {function.__name__} ---", flush=True)
        try:
            with native_context(session):
                function(session)
        except ManualCheckpoint:
            record.update(status="waiting", finished_at=utc_now())
            raise
        except BaseException as error:
            if isinstance(error, SystemExit) and error.code in (None, 0):
                record.update(status="completed", finished_at=utc_now())
            else:
                record.update(status="failed", finished_at=utc_now(), error=f"{type(error).__name__}: {error}")
                if not cleanup or isinstance(error, (KeyboardInterrupt, SystemExit)):
                    raise
                errors.append(f"{function.__name__}: {error}")
                print("Restoration failed; attempting the remaining cleanup:", error)
        else:
            record.update(status="completed", finished_at=utc_now())
        finally:
            names = set(session.mapping.get("persist_variables", [])) | set(session.state["environment"])
            session.state["environment"] = {key: os.environ[key] for key in names
                                             if key in os.environ and not secret_name(key)}
            session.save()
    if errors:
        raise RuntimeError("Cleanup incomplete:\n" + "\n".join(errors))
    if cleanup and finalize:
        session.state["lifecycle_complete"] = True
        session.save()


def backup_files(session, relative_paths):
    """Save exact learner bytes once before a lesson edits its local fixtures.
    
    This preserves pre-existing edits; restoration must never mean git checkout.
    Only explicitly listed paths inside the kit can be saved or restored.
    
    Example: backup_files(session, ["evals/golden.jsonl"]) saves exact existing bytes
    """
    saved = session.state.setdefault("file_backups", {})
    directory = session.directory / "original_files"
    directory.mkdir(exist_ok=True)
    for relative in relative_paths:
        path = (session.config.kit_root / relative).resolve()
        if not path.is_relative_to(session.config.kit_root.resolve()):
            raise ValueError("Backup path must stay inside the kit")
        if relative in saved:
            continue
        data = path.read_bytes() if path.exists() else None
        target = directory / hashlib.sha256(relative.encode()).hexdigest()
        if data is not None:
            target.write_bytes(data)
        saved[relative] = {"path": str(target), "existed": data is not None}
        session.save()


def restore_files(session):
    """Keep a copy of the lesson edits, then restore each exact original backup.
    
    Example: restore_files(session) restores those saved bytes and retains the lesson edits
    """
    for relative, saved in session.state.get("file_backups", {}).items():
        if saved.get("restored"):
            continue
        path = (session.config.kit_root / relative).resolve()
        if not path.is_relative_to(session.config.kit_root.resolve()):
            raise ValueError("Restoration path must stay inside the kit")
        if path.exists():
            (session.attempt / (hashlib.sha256(relative.encode()).hexdigest() + ".lesson-edited")).write_bytes(path.read_bytes())
        if saved["existed"]:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(Path(saved["path"]).read_bytes())
        else:
            path.unlink(missing_ok=True)
        saved["restored"] = True
        session.save()
        print("Restored exact original:", relative)
