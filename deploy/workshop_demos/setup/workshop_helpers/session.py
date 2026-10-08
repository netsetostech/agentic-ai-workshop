"""Persistent IDE runs for one lesson, independent of terminal exports and cwd.

Native Python examples execute in the selected interpreter so breakpoints work.
The kit also has genuine Bash/Make/gcloud workflows. ``shell`` runs those with
the same interpreter on PATH and persists their named variables/functions between
separate IDE launches. It does not turn a source excerpt into executable code.
Local session state and diagnostic output stay under the ignored results tree.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid

from .artifacts import write_json
from .config import lesson_folder, load_config


def secret_name(name):
    """Exclude credentials from persisted variables while retaining token budgets.
    
    Example: secret_name(key)
    """
    upper = name.upper()
    return (bool(re.search(r"PASSWORD|SECRET|CREDENTIAL|PRIVATE_KEY|API_KEY|DATABASE_URL|DSN", upper))
            or upper in {"TOK", "TOKEN", "AUTHORIZATION", "AUTH", "HEADERS"}
            or upper.endswith(("_TOKEN", "_TOK")))


def utc_now():
    """Return an unambiguous timestamp for ordering attempts and cloud observations.
    
    Example: utc_now()
    """
    return datetime.now(timezone.utc).isoformat()


class DemoSession:
    """Open the active run of a lesson and record exactly which file was executed.
    
    Args:
        script: The lesson demo's __file__; its adjacent lesson_map.json supplies
            the reviewed execution order and prerequisite identifiers.
        live: Refresh ADC and resolve project/API settings only when needed.
    
    A process lock prevents simultaneous mutation of the same lesson session.
    Failed attempts remain failed and never satisfy a later prerequisite. Cleanup
    files are allowed after failure. A completed file is not replayed implicitly:
    set REPEAT=True in that demo only after reading its replay implications.
    
    Example: with DemoSession(__file__, live=False) as session: demonstrate(session)
    """

    def __init__(self, script, live=True, repeat=False, config=None):
        """Locate this file in its lesson map and resolve the lesson-specific state directory.
        
        Example: Construct the owning class with the arguments shown above; subsequent methods reuse these settings.
        """
        self.script = Path(script).resolve()
        self.lesson_dir = self.script.parent
        # Lesson-specific preparation/cleanup can live in a setup/ subdirectory.
        if not (self.lesson_dir / "lesson_map.json").exists():
            self.lesson_dir = self.lesson_dir.parent
        self.mapping = json.loads((self.lesson_dir / "lesson_map.json").read_text(encoding="utf-8"))
        relative_script = self.script.relative_to(self.lesson_dir).as_posix()
        self.step = next(item for item in self.mapping["demos"] if item["file"] == relative_script)
        self.config = config or load_config()
        self.live, self.repeat = live, repeat
        self.lesson = self.mapping["lesson"]
        self.base = self.config.results_dir / lesson_folder(self.lesson)
        self.base.mkdir(parents=True, exist_ok=True)
        self.lock = self.base / "session.lock"
        self._lock_fd = None
        self._original_env = None
        self._original_cwd = None
        self._original_path = None

    def __enter__(self):
        """Validate run identity/order before opening any cloud clients or commands.
        
        Example: Use the owning class with a with statement; context entry/exit invokes this method.
        """
        try:
            self._lock_fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise RuntimeError(f"Another attempt holds {self.lock}. If its process was killed, use setup/recover_session.py after checking that no demo is running.") from exc
        try:
            os.write(self._lock_fd, f"pid={os.getpid()}\n{self.script}\n".encode())
            pointer = self.base / "active.json"
            identity = {"project": self.config.project, "tenant": self.config.tenant_id,
                        "kit_root": str(self.config.kit_root), "region": self.config.cloud_run_region}
            if pointer.exists():
                run_id = json.loads(pointer.read_text(encoding="utf-8"))["run_id"]
                if not re.fullmatch(r"[0-9a-f]{16}", run_id):
                    raise RuntimeError("Invalid active session identifier.")
                self.directory = self.base / run_id
                self.state = json.loads((self.directory / "session.json").read_text(encoding="utf-8"))
                if self.state["identity"] != identity:
                    raise RuntimeError("Active lesson belongs to a different project/tenant/kit/region. Restore its settings before starting a new session.")
                if self.state.get("source_sha") != self.mapping.get("source_sha") and self.step.get("category") not in {"cleanup", "recovery"}:
                    raise RuntimeError("Lesson source changed during this run. Finish/recover the saved run before starting the updated sequence.")
                if self.state.get("layout_version", 1) != self.mapping.get("layout_version", 1) and self.step.get("category") not in {"cleanup", "recovery"}:
                    raise RuntimeError("This active run uses the old file layout. Run this lesson's setup/finish.py to restore saved settings, then setup/start_new_session.py before starting the new sequence.")
                if self.state.get("lifecycle_complete") and self.step.get("category") != "cleanup":
                    raise RuntimeError("This lesson run has been finished. Use setup/start_new_session.py for a new run.")
            else:
                self.directory = self.base / uuid.uuid4().hex[:16]
                self.directory.mkdir()
                self.state = {"lesson": self.lesson, "identity": identity, "source_sha": self.mapping.get("source_sha"), "layout_version": self.mapping.get("layout_version", 1),
                              "created_at": utc_now(), "completed": [], "attempts": [], "environment": {}}
                write_json(pointer, {"run_id": self.directory.name})
                self.save()
            completed = set(self.state["completed"])
            if self.step["id"] in completed and not self.repeat:
                raise RuntimeError("This file already completed in the active session. Inspect its output. For a deliberate rerun set REPEAT=True in this file; for a fresh lesson use setup/start_new_session.py after cleanup.")
            if self.step.get("category") not in {"cleanup", "recovery"}:
                missing = set(self.step.get("requires", [])) - completed
                if missing:
                    raise RuntimeError("Run the prerequisite file(s) first: " + ", ".join(sorted(missing)))
            attempt_id = f"{len(self.state['attempts']) + 1:03}_{self.script.stem}"
            self.attempt = self.directory / "attempts" / attempt_id
            self.attempt.mkdir(parents=True)
            self.record = {"id": self.step["id"], "file": self.script.name, "started_at": utc_now(),
                           "status": "running", "directory": str(self.attempt)}
            self.state["attempts"].append(self.record)
            self.save()
            self._original_env = dict(os.environ)
            self._original_cwd = Path.cwd()
            self._original_path = list(sys.path)
            self.env = dict(os.environ)
            self.env.update(self.state["environment"])
            self.env.update({"DEMO_ROOT": str(self.config.kit_root), "PROJECT": self.config.project,
                             "GOOGLE_CLOUD_PROJECT": self.config.project, "REGION": self.config.cloud_run_region,
                             "TENANT": self.config.tenant_id, "WORKSHOP_SESSION_DIR": str(self.directory),
                             "PYTHONUNBUFFERED": "1", "WORKSHOP_PYTHON": sys.executable})
            self.env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
            self.env["WORKSHOP_PERSIST_VARIABLES"] = json.dumps(self.mapping.get("persist_variables", []))
            os.environ.update(self.env)
            os.chdir(self.config.kit_root)
            sys.path.insert(0, str(self.config.kit_root))
            if self.live:
                self.prepare_live()
            print(f"\nLesson {self.lesson}: {self.step['heading']}\nFile: {self.script.name}")
            print("Python:", sys.executable)
            print("Purpose:", self.step["purpose"])
            print("Evidence:", self.attempt, flush=True)
            return self
        except BaseException as exc:
            self.__exit__(type(exc), exc, exc.__traceback__)
            raise

    def __exit__(self, kind, error, traceback):
        """Save the actual outcome and restore only the IDE process's local context.
        
        Example: self.__exit__(type(exc), exc, exc.__traceback__)
        """
        try:
            if hasattr(self, "record"):
                success = error is None or isinstance(error, SystemExit) and error.code in (None, 0)
                self.record.update(status="completed" if success else "failed", finished_at=utc_now())
                if error and not success:
                    self.record["error"] = f"{type(error).__name__}: {error}"
                if success and self.step["id"] not in self.state["completed"]:
                    self.state["completed"].append(self.step["id"])
                names = set(self.mapping.get("persist_variables", [])) | set(self.state["environment"])
                self.state["environment"] = {name: os.environ[name] for name in names
                                             if name in os.environ and not secret_name(name)}
                self.save()
                print("Execution", self.record["status"] + ".", "Compare observations with the README checkpoint; completion is not an automatic claim of live proof.")
                print("Saved:", self.attempt)
                if success and self.step.get("next"):
                    print("Next required file:", self.step["next"])
            if self._original_env is not None:
                os.environ.clear()
                os.environ.update(self._original_env)
                os.chdir(self._original_cwd)
                sys.path[:] = self._original_path
        finally:
            if self._lock_fd is not None:
                os.close(self._lock_fd)
                self._lock_fd = None
                self.lock.unlink(missing_ok=True)
        return False

    def save(self):
        """Atomically checkpoint local state before/after operations, never API tokens.
        
        Example: self.save()
        """
        write_json(self.directory / "session.json", self.state)

    def prepare_live(self):
        """Replace repeated shell exports with validated ADC and explicit project data.
        
        This resolves addresses, not resource creation. A missing deployment is not
        repaired automatically; deployment lessons can still use the project/region
        while creating their services. Actual serving configuration is read only by
        the demos that require it.
        
        Example: self.prepare_live()
        """
        from .auth import checked_credentials, gcloud
        if not self.config.project:
            raise RuntimeError("Set project in setup/config/settings.local.json; use the same rag-shell-venv interpreter that ran bootstrap.py.")
        self.credentials = checked_credentials()
        values = {"ME": gcloud("config", "get-value", "account"),
                  "NUMBER": gcloud("projects", "describe", self.config.project, "--format=value(projectNumber)")}
        values["API"] = self.config.api_base_url or f"https://{self.config.api_service}-{values['NUMBER']}.{self.config.cloud_run_region}.run.app"
        values["API_URL"] = values["API"]
        self.set_environment(**values)

    def set_environment(self, **values):
        """Share explicit settings with later Python and command steps in this lesson.
        
        Example: self.set_environment(**values)
        """
        for key, value in values.items():
            if value is None:
                os.environ.pop(key, None)
                self.state["environment"].pop(key, None)
            else:
                os.environ[key] = str(value)
                if not secret_name(key):
                    self.state["environment"][key] = str(value)
        self.save()

    def identity_token(self, audience=None, outsider=False, include_email=True):
        """Mint a fresh audience-bound token; returning it never persists it to disk.
        
        Example: token = identity_token(config, config.api_base_url) in an authenticated request
        """
        from .auth import gcloud
        account = f"documind-outsider-sa@{self.config.project}.iam.gserviceaccount.com" if outsider else self.config.ui_service_account
        email_flag = ("--include-email",) if include_email else ()
        return gcloud("auth", "print-identity-token", *email_flag, f"--audiences={audience or os.environ['API']}",
                      f"--impersonate-service-account={account}", f"--project={self.config.project}")

    def service_environment(self, service, keys):
        """Read selected literal variables from the sole serving revision as JSON.
        
        Missing values are unset, rather than set to empty strings that change SDK
        defaults. Secrets are neither fetched nor saved. Split traffic is rejected
        because one set of settings could not describe every request.
        
        Example: self.service_environment(service, keys) in the owning lesson/helper context
        """
        from .auth import gcloud
        from .discovery import select_revision
        flags = (f"--project={self.config.project}", f"--region={self.config.cloud_run_region}", "--format=json")
        document = json.loads(gcloud("run", "services", "describe", service, *flags))
        revision = select_revision(document)
        revision_doc = json.loads(gcloud("run", "revisions", "describe", revision, *flags))
        rows = revision_doc["spec"]["containers"][0].get("env", [])
        found = {row["name"]: row["value"] for row in rows if "value" in row and row["name"] in keys and not secret_name(row["name"])}
        self.set_environment(**{key: found.get(key) for key in keys if not secret_name(key)})
        write_json(self.attempt / "serving_configuration.json", {"service": service, "revision": revision, "values": found})
        for key in keys:
            print(key + "=" + found.get(key, "<unset: the service default applies>"))
        return found

    def command(self, args, *, timeout=None, check=True, cwd=None):
        """Run an existing kit/CLI command, showing and retaining its real output.
        
        Pass an argument list, not a shell-quoted string. Nonzero status raises by
        default so the next teaching checkpoint cannot silently continue. Long
        tuning/build commands intentionally have no implicit five-minute timeout.
        
        Example: self.command([sys.executable, 'commands/lane.py', '--project', self.config.project, 'tenant-backend', self.config.tenant_id, 'vector'])
        """
        number = len(list(self.attempt.glob("command_*.log"))) + 1
        path = self.attempt / f"command_{number:02}.log"
        with path.open("w", encoding="utf-8") as output:
            process = subprocess.Popen([str(a) for a in args], cwd=cwd or self.config.kit_root,
                                       env=dict(os.environ), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, encoding="utf-8", errors="replace", start_new_session=os.name == "posix")
            def stream_output():
                """Keep long builds visible while the parent can enforce a timeout.
                
                Example: stream_output() in the owning lesson/helper context
                """
                for line in process.stdout:
                    print(line, end="", flush=True)
                    output.write(line)
                    output.flush()
            reader = threading.Thread(target=stream_output, daemon=True)
            reader.start()
            try:
                status = process.wait(timeout=timeout)
            except BaseException:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGTERM)
                else:
                    process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    if os.name == "posix":
                        os.killpg(process.pid, signal.SIGKILL)
                    else:
                        process.kill()
                    process.wait()
                raise
            finally:
                reader.join(timeout=10)
                if reader.is_alive():
                    raise RuntimeError("A background child retained this command's stdout. Redirect its output explicitly before running it as a lesson service.")
        if check and status:
            raise subprocess.CalledProcessError(status, args)
        return status

    def shell(self, code):
        """Run a lesson's CLI workflow with variables/functions carried to the next file.
        
        Bash is required on the Linux Cloud Workstation for the kit's existing
        pipelines and shell helpers. A failure stops this attempt. State is saved
        on exit, including failure, so the explicit recovery/cleanup file can use
        identifiers that were created before the failing operation.
        
        Example: self.shell(code) in the owning lesson/helper context
        """
        if os.name == "nt" and not os.environ.get("WORKSHOP_TEST_BASH"):
            raise RuntimeError("Run command-based cloud demos on your Linux Cloud Workstation. Native offline Python examples also work here.")
        executable = os.environ.get("WORKSHOP_TEST_BASH") or shutil.which("bash")
        if not executable:
            raise RuntimeError("The kit command workflow requires bash on PATH.")
        state = self.directory / "shell_state.sh"
        exports = self.attempt / "shell_environment.json"
        variables = [name for name in self.mapping.get("persist_variables", [])
                     if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) and not secret_name(name)
                     and name not in {"HOME", "PATH", "PYTHONPATH", "PWD", "OLDPWD", "BASH_ENV", "SHELLOPTS", "BASHOPTS"}]
        names = " ".join(shlex.quote(name) for name in variables)
        seed = f"source {shlex.quote(state.as_posix())}\n" if state.exists() else ""
        # Python steps may have updated environment values since the last shell.
        seed += "\n".join(f"export {key}={shlex.quote(value)}" for key, value in self.state["environment"].items()
                          if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) and not secret_name(key))
        capture = (
            "_workshop_capture() {\n  _workshop_status=$?\n  set +e\n"
            f"  {{ for _workshop_name in {names}; do declare -p \"$_workshop_name\" 2>/dev/null; done; declare -f; }} > {shlex.quote(state.as_posix())}.tmp\n"
            f"  chmod 600 {shlex.quote(state.as_posix())}.tmp\n  mv {shlex.quote(state.as_posix())}.tmp {shlex.quote(state.as_posix())}\n"
            f"  {shlex.quote(Path(sys.executable).as_posix())} -m workshop_helpers.shell_state {shlex.quote(exports.as_posix())}\n"
            "  exit \"$_workshop_status\"\n}\ntrap _workshop_capture EXIT\n"
        )
        common = Path(__file__).with_name("shell_helpers.sh").read_text(encoding="utf-8")
        script = self.attempt / "commands.sh"
        script.write_text("set -eE -o pipefail\n" + seed + "\n" + common + "\n" + capture + "\n" + code + "\n", encoding="utf-8")
        try:
            self.command([executable, script.as_posix()])
        finally:
            if exports.exists():
                after = json.loads(exports.read_text(encoding="utf-8"))
                self.set_environment(**{key: after.get(key) for key in variables})

    def pin_vector(self):
        """Save the current tenant setting before selecting vector for the lesson.
        
        Example: self.pin_vector() in the owning lesson/helper context
        """
        from google.cloud import firestore
        db = firestore.Client(project=self.config.project)
        ref = db.collection("tenant_settings").document(self.config.tenant_id)
        before = ref.get(retry=None, timeout=15).to_dict() or {}
        if "original_backend" not in self.state:
            self.state["original_backend"] = before.get("retrieval_backend", "default")
            self.state["backend_restore_required"] = True
            self.save()
        self.command([sys.executable, "commands/lane.py", "--project", self.config.project,
                      "tenant-backend", self.config.tenant_id, "vector"])
        self.state["pin_ready_after"] = time.time() + 65  # API tenant-settings TTL is 60s.
        self.save()

    def start_local_service(self, args, health_url, *, expected_health=None):
        """Start an owned local process without holding the lesson lock indefinitely.
        
        Logs are redirected before detaching, and the PID is saved before polling.
        A failed health check leaves evidence and an explicit cleanup path; it
        does not pretend the service started. Requires the Linux workstation.
        
        Example: self.start_local_service(args, health_url, expected_health) in the owning lesson/helper context
        """
        import urllib.request
        if os.name != "posix":
            raise RuntimeError("Start this local service in the Linux Cloud Workstation.")
        if self.state.get("local_service"):
            raise RuntimeError("This session already owns a service; run its finish file before starting another.")
        try:
            urllib.request.urlopen(health_url, timeout=2).close()
        except OSError:
            pass
        else:
            raise RuntimeError("A service already answers this address. Stop or inspect it; the lesson will not take ownership of another process.")
        log_path = self.attempt / "local_service.log"
        with log_path.open("wb") as output:
            process = subprocess.Popen(args, cwd=self.config.kit_root, env=dict(os.environ),
                                       stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        self.state["local_service"] = {"pid": process.pid, "args": args, "cwd": str(self.config.kit_root), "log": str(log_path)}
        self.save()
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"Local service exited with {process.returncode}; inspect {log_path}.")
            try:
                with urllib.request.urlopen(health_url, timeout=2) as response:
                    health = json.load(response)
                expected = expected_health if expected_health is not None else {"status": "ok", "profile": "local"}
                if all(health.get(key) == value for key, value in expected.items()):
                    print("Local service ready:", health)
                    return
            except OSError:
                pass
            time.sleep(2)
        raise TimeoutError(f"Local service did not become ready. Inspect {log_path}; cleanup remains available.")

    def stop_local_service(self):
        """Stop only the process group whose command and cwd match this session.
        
        Example: self.stop_local_service() in the owning lesson/helper context
        """
        owned = self.state.get("local_service")
        if not owned:
            print("No local service was started by this session.")
            return
        proc = Path("/proc") / str(owned["pid"])
        if proc.exists():
            command = (proc / "cmdline").read_bytes().split(b"\0")
            if Path(proc / "cwd").resolve() != Path(owned["cwd"]).resolve() or not all(str(arg).encode() in command for arg in owned["args"]):
                raise RuntimeError("PID now belongs to a different command; refusing to stop it.")
            os.killpg(owned["pid"], signal.SIGTERM)
        self.state["local_service"] = None
        self.save()
        print("Stopped this session's local service; log retained:", owned["log"])

    def restore_backend(self):
        """Restore the saved pin; refuse to overwrite an unrelated later pin change.
        
        Example: self.restore_backend() in the owning lesson/helper context
        """
        from google.cloud import firestore
        previous = self.state.get("original_backend")
        if previous is None and not self.state.get("backend_restore_required"):
            print("No tenant pin was changed by this session.")
            return
        if previous not in {"vector", "firestore", "rag_engine", "vertex_search", "default"}:
            raise RuntimeError("No valid original backend was saved for this session.")
        db = firestore.Client(project=self.config.project)
        current = (db.collection("tenant_settings").document(self.config.tenant_id).get(retry=None, timeout=15).to_dict() or {}).get("retrieval_backend", "default")
        if current not in {"vector", previous}:
            raise RuntimeError(f"Backend changed to {current} outside the expected vector pin; inspect before restoring {previous}.")
        self.command([sys.executable, "commands/lane.py", "--project", self.config.project,
                      "tenant-backend", self.config.tenant_id, previous])
        self.state["backend_restore_required"] = False
        self.save()
