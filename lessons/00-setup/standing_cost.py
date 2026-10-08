"""The lane's standing cost: what bills by the hour while the lane exists, with no traffic at all. One source for the
three Module 0 lessons that state it (0.1's per day and per weekend, 0.3's hourly items, 0.4's daily cost of a lane
left up), so they cannot disagree.

Every size is parsed from the kit's Terraform at build time - vector.tf's deployed index (its replicas, and the
machine its shard size names), spanner.tf's instance (edition and processing units), cloudsql.tf's and gateway.tf's
instances (tier and disk), gke.tf's regional cluster and its lab pool (nodes, machine and disk) and network.tf's
connector (its minimum instances) - times the official Mumbai list price below, at the kit's USD_INR
(shared/prices.py). A build imports it as `import standing_cost as sc` after putting this folder on sys.path.
"""
import json
import math
import re

from pagekit.pagebuild import KIT

_FILES = ("terraform/vector.tf", "terraform/spanner.tf", "terraform/cloudsql.tf", "terraform/gateway.tf",
          "terraform/gke.tf", "terraform/network.tf", "shared/prices.py", "gke/README.md")
src = {p: (KIT / p).read_text(encoding="utf-8") for p in _FILES}


def one(pattern: str, text: str, flags: int = 0) -> str:
    """The one match of a pattern's first group: a kit fact the pages state, or the build stops."""
    found = re.findall(pattern, text, flags)
    assert len(found) == 1, (pattern, found)
    return found[0]


def r0(x: float) -> int:
    """Half up, as the widgets' Math.round rounds, so a page and its meter print the same rupees."""
    return int(math.floor(x + 0.5))


USD_INR = int(one(r"^USD_INR = (\d+)\b", src["shared/prices.py"], re.M))

# Official list prices, USD, Mumbai (asia-south1), read on 7 October 2026 from the region tables each pricing page
# embeds for its region selector ("Mumbai (asia-south1)"); Iowa's figures were checked against the same tables. The
# course's lane runs its services in asia-south1 (1.1's setup block exports REGION=asia-south1, and the kit's
# workshop_demos/setup/config/settings.example.json names cloud_run_region asia-south1), so make up is run with
# REGION=asia-south1 rather than the Makefile's us-central1 default; spanner.tf pins regional-asia-south1 either way.
# Re-verify before a cohort.
LANE_REGION = json.loads((KIT / "workshop_demos/setup/config/settings.example.json").read_text(encoding="utf-8"))["cloud_run_region"]
assert LANE_REGION == "asia-south1", LANE_REGION      # the prices below are Mumbai's: a lane elsewhere needs its own
PRICES = {
    # https://cloud.google.com/vertex-ai/pricing#vectorsearch - Vector Search, index serving, per node hour by machine
    "vs:e2-standard-2": 0.1126804, "vs:e2-standard-16": 0.9014432,
    # https://cloud.google.com/spanner/pricing - compute capacity, regional, Enterprise, per node hour; 1 node is
    # 1,000 processing units (https://docs.cloud.google.com/spanner/docs/compute-capacity)
    "spanner:ENTERPRISE": 1.722,
    # https://cloud.google.com/sql/pricing - MySQL and PostgreSQL, shared-core db-f1-micro per hour; SSD storage capacity
    # per GiB hour (zonal). A running instance's IPv4 address is free: the page bills "IPv4 addresses while idle".
    "sql:db-f1-micro": 0.0126, "sql:ssd_gib": 0.000279452,
    # https://cloud.google.com/kubernetes-engine/pricing - "A flat cluster management fee of $0.10 per cluster per hour";
    # the free tier's credit applies "only ... to zonal and Autopilot clusters" (gke.tf's is regional Standard). The
    # kit's gke/README.md prices the same fee (asserted below).
    "gke:cluster": 0.10,
    # https://cloud.google.com/products/compute/pricing/general-purpose - E2 on demand, per hour
    "ce:e2-standard-2": 0.08048436, "ce:e2-micro": 0.010060545,
    # https://cloud.google.com/compute/disks-image-pricing - standard provisioned space, per GiB hour
    "pd:standard_gib": 0.000065753,
}
# Serverless VPC Access connectors: https://cloud.google.com/vpc/pricing - "Connector instances bill as Compute Engine
# VMs"; e2-micro is the default instance type (https://docs.cloud.google.com/vpc/docs/configure-serverless-vpc-access).
assert float(one(r"Autopilot cluster fee \(after the free-tier credit\) \| \$([\d.]+)", src["gke/README.md"])) == PRICES["gke:cluster"]

V = src["terraform/vector.tf"]
SHARD_MACHINE = dict(re.findall(r"(SHARD_SIZE_[A-Z]+)\s+= \"([a-z0-9-]+)\"", V))
assert SHARD_MACHINE == {"SHARD_SIZE_SMALL": "e2-standard-2", "SHARD_SIZE_MEDIUM": "e2-standard-16", "SHARD_SIZE_LARGE": "e2-highmem-16"}
assert "shard_size" not in V.split('resource "google_vertex_ai_index" "documind" {', 1)[1].split("index_update_method", 1)[0]
VS_REPLICAS = int(one(r"min_replica_count = (\d+)", V))
assert int(one(r"max_replica_count = (\d+)", V)) == VS_REPLICAS
SP = src["terraform/spanner.tf"]
SP_PU = int(one(r"processing_units = (\d+)", SP))
SP_EDITION = one(r'edition\s+= "([A-Z_]+)"', SP)
SP_CONFIG = one(r'config\s+= "([a-z0-9-]+)"', SP)
assert SP_CONFIG == "regional-asia-south1"
SQL = []
for f in ("terraform/cloudsql.tf", "terraform/gateway.tf"):
    t = src[f]
    name = one(r'resource "google_sql_database_instance" "\w+" \{\s*name\s+= "([\w-]+)"', t)
    SQL.append((name, one(r'tier\s+= "([\w-]+)"', t), one(r'availability_type = "(\w+)"', t), int(one(r"disk_size\s+= (\d+)", t))))
assert all(s[1:] == SQL[0][1:] for s in SQL) and SQL[0][1:3] == ("db-f1-micro", "ZONAL"), SQL
assert sum((KIT / "terraform" / p.name).read_text(encoding="utf-8").count('resource "google_sql_database_instance"')
           for p in sorted((KIT / "terraform").glob("*.tf"))) == len(SQL) == 2
SQL_TIER, SQL_GB = SQL[0][1], SQL[0][3]
G = src["terraform/gke.tf"]
POOL = G.split('resource "google_container_node_pool" "lab" {', 1)[1]
GKE_NODES = int(one(r"node_count\s+= (\d+)", POOL))
GKE_MACHINE = one(r'machine_type\s+= "([\w-]+)"', POOL)
GKE_DISK_TYPE = one(r'disk_type\s+= "([\w-]+)"', POOL)
GKE_DISK_GB = int(one(r"disk_size_gb\s+= (\d+)", POOL))
assert "location   = var.region" in G and one(r'variable "gke_autopilot" \{.*?default\s+= (\w+)', G, re.S) == "false"
assert GKE_DISK_TYPE == "pd-standard"
NET = src["terraform/network.tf"]
CONN_MIN = int(one(r"min_instances = (\d+)", NET))
assert "machine_type" not in NET                   # so the API's default instance type, e2-micro

_WORDS = "zero one two three four five six seven eight nine ten eleven twelve".split()
ITEMS = [  # key, label, declared in, size as the page says it, USD an hour (the index's depends on its shard)
    ("index", "Vector Search deployed index", "vector.tf",
     f"{VS_REPLICAS} replica on the shard's machine", None),
    ("spanner", "Spanner graph instance", "spanner.tf",
     f"{SP_EDITION.title()}, {SP_PU} processing units", PRICES[f"spanner:{SP_EDITION}"] * SP_PU / 1000),
    ("sql", f"Cloud SQL, {_WORDS[len(SQL)]} instances", "cloudsql.tf, gateway.tf",
     f"{len(SQL)} x {SQL_TIER}, {SQL_GB} GB SSD each", len(SQL) * (PRICES[f"sql:{SQL_TIER}"] + SQL_GB * PRICES["sql:ssd_gib"])),
    ("gkefee", "GKE cluster fee", "gke.tf",
     "a regional Standard cluster", PRICES["gke:cluster"]),
    ("gkenode", "GKE lab node", "gke.tf",
     f"{GKE_NODES} x {GKE_MACHINE}, {GKE_DISK_GB} GB {GKE_DISK_TYPE}", GKE_NODES * (PRICES[f"ce:{GKE_MACHINE}"] + GKE_DISK_GB * PRICES["pd:standard_gib"])),
    ("conn", "Serverless VPC Access connector", "network.tf",
     f"{CONN_MIN} x e2-micro, its minimum", CONN_MIN * PRICES["ce:e2-micro"]),
]
SHARDS = {"small": SHARD_MACHINE["SHARD_SIZE_SMALL"], "medium": SHARD_MACHINE["SHARD_SIZE_MEDIUM"]}
INDEX_USD = {k: VS_REPLICAS * PRICES[f"vs:{m}"] for k, m in SHARDS.items()}
REST_USD = sum(u for k, *_, u in ITEMS if k != "index")
HOURLY = {k: INDEX_USD[k] + REST_USD for k in SHARDS}
DAY_H, WEEKEND_H, MONTH_H = 24, 48, 730            # a weekend: Saturday and Sunday; a month: the price pages' 730 hours
PER_DAY = {k: r0(HOURLY[k] * DAY_H * USD_INR) for k in SHARDS}
PER_WEEKEND = {k: r0(HOURLY[k] * WEEKEND_H * USD_INR) for k in SHARDS}
PER_MONTH = {k: r0(HOURLY[k] * MONTH_H * USD_INR) for k in SHARDS}


def item_usd(key: str, shard: str) -> float:
    """One item's dollars an hour; the index's depends on the shard size the service chose."""
    return INDEX_USD[shard] if key == "index" else next(u for k, *_, u in ITEMS if k == key)
