"""Configuration independent of shell exports and the IDE working directory."""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re

SETUP_DIR = Path(__file__).resolve().parents[1]
WORKSHOP_DIR = SETUP_DIR.parent


def lesson_folder(lesson: str) -> str:
    """Name a lesson's folder under the results directory and under workshop_demos, Basics included.

    Example: lesson_folder("B.1") is "module_B/lesson_B_1"; lesson_folder("0.2") is "module_00/lesson_0_2".
    """
    match = re.fullmatch(r"(B|[0-9]{1,2})\.([0-9]{1,2})", lesson)
    if not match:
        raise ValueError(f"Not a lesson id such as 4.4 or B.1: {lesson!r}")
    major, minor = match.groups()
    module = "module_B" if major == "B" else f"module_{int(major):02}"
    return f"{module}/lesson_{major}_{minor}"


@dataclass(frozen=True)
class DemoConfig:
    """Hold validated kit paths, project, region, service names and local result locations for every lesson.
    
    Example: config = load_config(); print(config.kit_root, config.project)
    """
    project: str
    cloud_run_region: str
    tenant_id: str
    kit_root: Path
    uploads_bucket: str
    api_service: str
    ingest_service: str
    api_revision: str
    ingest_revision: str
    api_base_url: str
    api_audience: str
    ui_service_account: str
    results_dir: Path
    poll_seconds: float
    ingest_wait_seconds: float
    answer_wait_seconds: float
    max_hash_bytes: int


def load_config(path=None) -> DemoConfig:
    """Merge local settings with defaults, validate the tenant/kit paths and return resolved configuration.
    
    Example: config = load_config() reads settings.local.json and retains its explicit project
    """
    path = Path(path or os.environ.get("WORKSHOP_DEMO_CONFIG") or
                SETUP_DIR / "config" / "settings.local.json")
    defaults = json.loads((SETUP_DIR / "config" / "settings.example.json").read_text())
    if path.exists():
        supplied = json.loads(path.read_text(encoding="utf-8"))
        extra = set(supplied) - set(defaults)
        if extra:
            raise ValueError(f"Unknown configuration keys: {sorted(extra)}")
        defaults.update(supplied)
    raw = defaults
    tenant = raw["tenant_id"]
    if not isinstance(tenant, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", tenant):
        raise ValueError("tenant_id must be a single tenant prefix, such as acme.")
    root = Path(raw["kit_root"]).expanduser() if raw["kit_root"] != "auto" else WORKSHOP_DIR.parent
    if not root.is_absolute():
        root = WORKSHOP_DIR / root
    root = root.resolve()
    if not (root / "services" / "ingest" / "reconcile.py").is_file():
        raise FileNotFoundError(
            f"Kit not found at {root}. Extract workshop_demos directly inside your "
            "deploy_module_rag folder, or set kit_root in setup/config/settings.local.json."
        )
    project = str(raw["project"]).strip()
    results = Path(raw["results_dir"]).expanduser()
    if not results.is_absolute():
        results = WORKSHOP_DIR / results
    for name in ("poll_seconds", "ingest_wait_seconds", "answer_wait_seconds"):
        if float(raw[name]) <= 0:
            raise ValueError(f"{name} must be positive.")
    if int(raw["max_hash_bytes"]) < 0:
        raise ValueError("max_hash_bytes must be zero (unlimited) or positive.")
    return DemoConfig(
        project=project, cloud_run_region=str(raw["cloud_run_region"]), tenant_id=tenant,
        kit_root=root, uploads_bucket=raw["uploads_bucket"] or f"{project}-uploads",
        api_service=raw["api_service"], ingest_service=raw["ingest_service"],
        api_revision=raw["api_revision"], ingest_revision=raw["ingest_revision"],
        api_base_url=raw["api_base_url"], api_audience=raw["api_audience"],
        ui_service_account=raw["ui_service_account"] or f"documind-ui-sa@{project}.iam.gserviceaccount.com",
        results_dir=results.resolve(), poll_seconds=float(raw["poll_seconds"]),
        ingest_wait_seconds=float(raw["ingest_wait_seconds"]), answer_wait_seconds=float(raw["answer_wait_seconds"]),
        max_hash_bytes=int(raw["max_hash_bytes"]),
    )
