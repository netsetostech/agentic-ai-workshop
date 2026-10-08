"""The stand-in lane for lesson 9.3's build. The lesson deploys nothing; its one live step reads the lane with gcloud,
and this file stands in for those reads with what Terraform and the Makefile would have left on a lane after make up:

  the cluster        gcloud container clusters describe documind-autopilot: gke.tf's defaults - gke_autopilot=false, so a
                     regional Standard control plane in REGION and one node pool, documind-lab, of one e2-standard-2 in
                     REGION-a with a 30 GB pd-standard boot disk, on documind-vpc
  documind-vllm      gcloud run services describe: not found (make deploy-vllm is optional, D3, and the lesson runs neither)
  the vLLM image     gcloud artifacts docker images list: none (make build-vllm has not run)

    import lane183; lane183.install_client()      # before the cell's own code
"""
import json
import os
import subprocess


def cluster(region: str) -> dict:
    return {"name": "documind-autopilot", "location": region, "status": "RUNNING", "network": "documind-vpc",
            "subnetwork": "documind-subnet", "currentNodeCount": 1, "autopilot": {},
            "nodePools": [{"name": "documind-lab", "initialNodeCount": 1, "locations": [f"{region}-a"], "status": "RUNNING",
                           "config": {"machineType": "e2-standard-2", "diskSizeGb": 30, "diskType": "pd-standard",
                                      "imageType": "COS_CONTAINERD"},
                           "management": {"autoRepair": True, "autoUpgrade": True}}]}


def install_client() -> None:
    real_run = subprocess.run

    def run(cmd, *a, **kw):
        c = list(cmd) if isinstance(cmd, (list, tuple)) else []
        if c[:5] == ["gcloud", "container", "clusters", "describe", "documind-autopilot"]:
            region = c[c.index("--region") + 1]
            if any(x.startswith("--format=value(autopilot.enabled)") for x in c):
                return subprocess.CompletedProcess(c, 0, "\n", "")
            return subprocess.CompletedProcess(c, 0, json.dumps(cluster(region), indent=2) + "\n", "")
        if c[:5] == ["gcloud", "run", "services", "describe", "documind-vllm"]:
            return subprocess.CompletedProcess(c, 1, "", "ERROR: (gcloud.run.services.describe) Cannot find service [documind-vllm]\n")
        if c[:5] == ["gcloud", "artifacts", "docker", "images", "list"]:
            return subprocess.CompletedProcess(c, 0, "[]\n", "Listed 0 items.\n")
        return real_run(cmd, *a, **kw)
    subprocess.run = run
    os.environ.setdefault("LANE183", "1")
