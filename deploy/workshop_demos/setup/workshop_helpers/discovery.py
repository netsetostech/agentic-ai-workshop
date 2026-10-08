"""Read a serving revision as JSON; never silently use the newest candidate."""
from dataclasses import dataclass
import json
from .auth import gcloud

PUBLIC_KEYS = {
    "SELF_URL", "SEMANTIC_CACHE", "RETRIEVAL_BACKEND", "RETRIEVAL_CURRENT_ONLY",
    "RETRIEVAL_MODE", "MANAGED_MIRROR", "RAG_LOCATION", "SEARCH_LOCATION",
    "AUDIT_BUCKET", "RETENTION_DAYS", "EMBEDDING_MODEL", "REGION",
    "VECTOR_INDEX_ENDPOINT", "VECTOR_DEPLOYED_INDEX_ID",
}


@dataclass(frozen=True)
class ServingConfig:
    """Describe the inspected traffic-serving revision and its permitted literal environment values.
    
    Example: ServingConfig(service_name, revision, service.get('status', {}).get('url', ''), env)
    """
    service: str
    revision: str
    service_url: str
    environment: dict


def select_revision(service, override=""):
    """Select the sole traffic-serving revision; reject split traffic or a stale explicit override.
    
    Example: select_revision(service, revision_override)
    """
    active = {item.get("revisionName") for item in service.get("status", {}).get("traffic", [])
              if item.get("percent", 0) > 0}
    if len(active) != 1 or None in active:
        raise RuntimeError("This diagnostic requires one serving revision. Service traffic is split or absent.")
    serving = active.pop()
    if override and override != serving:
        raise RuntimeError("The pinned revision is not the sole serving revision. Refresh settings.local.json.")
    return serving


def read_serving(config, service_name, revision_override=""):
    """Read the chosen revision and retain only reviewed literal environment values.
    
    Example: serving = read_serving(config, "documind-api")
    """
    flags = (f"--project={config.project}", f"--region={config.cloud_run_region}", "--format=json")
    service = json.loads(gcloud("run", "services", "describe", service_name, *flags))
    revision = select_revision(service, revision_override)
    if not revision.startswith(service_name + "-"):
        raise ValueError("Selected revision does not belong to the requested service.")
    document = json.loads(gcloud("run", "revisions", "describe", revision, *flags))
    containers = document.get("spec", {}).get("containers", [])
    if len(containers) != 1:
        raise RuntimeError("This diagnostic expects a single application container.")
    env = {}
    for row in containers[0].get("env", []):
        key = row["name"].upper()
        if key not in PUBLIC_KEYS:
            continue
        if "value" not in row:
            raise RuntimeError(f"{key} is a referenced value; configure this diagnostic for explicit settings before continuing.")
        env[key] = row["value"]
    return ServingConfig(service_name, revision, service.get("status", {}).get("url", ""), env)
