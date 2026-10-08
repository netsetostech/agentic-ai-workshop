"""Build lesson 0.3 from its three parts, the shared template and verbatim kit excerpts.

The lane does not exist yet when this lesson starts, so the page carries its own setup section (the operator shell
from lesson 0.2), not 1.1's, which builds the API URL and mints tokens for a deployed lane.

Everything the page counts is read from the kit at build time, as text, offline: the service accounts, their roles
and grants, and the resource instances the Terraform declares for the values make plan passes (terraform/*.tf, the
Makefile, mk/*.mk); the account each service runs as and who may call it (the seven deploy scripts make up runs);
the buckets, the Firestore indexes and TTL fields, the stores and the switches; the APIs make apis enables; the
roster make roster writes (commands/lane.py's own dry run). The hourly items and their prices come from
lessons/00-setup/standing_cost.py, the one standing cost 0.1 and 0.4 state too: each size parsed from the kit's
Terraform, at Google's Mumbai (asia-south1) list prices read on 7 October 2026 and the kit's USD_INR
(shared/prices.py). What only a live lane can print comes from pb.recorded(): the author's one run from a blank
project, listed in RUN_LIST.md.
"""
import html
import json
import re
import subprocess
import sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, window  # noqa: E402

LESSON = "0.3"
PROJ, ME, REGION = "documind-ai-YOUR-ID", "you@example.com", "asia-south1"

title = ("<title>Lesson 0.3 Understand the project, identities and resource map, and deploy the lane - the accounts, "
         "the stores, one checked plan and the UI behind IAP | Netsetos</title>\n")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the resource map explorer: one account at a time, the stores it may touch lit */
.rm-l{display:flex;flex-direction:column;gap:4px;font-size:var(--small-size);color:var(--navy);max-width:460px;}
.rm-l select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.rm-sum{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal);margin:10px 0 8px;overflow-wrap:anywhere;}
.rm-stores{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px;}
.rm-st{font-size:12px;line-height:1.35;padding:4px 9px;border:1px dashed var(--border);border-radius:14px;color:var(--slate-light);background:var(--card);}
.rm-st.on{border:1px solid var(--teal);background:var(--teal-light);color:var(--teal-dark);font-weight:700;}
.rm-out{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;}
.rm-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 11px;font-size:12.5px;line-height:1.5;min-width:0;overflow-wrap:anywhere;}
.rm-box b{display:block;font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;}
.rm-box ul{margin:0;padding-left:16px;font-size:12.5px;}
.rm-box li{margin:0 0 2px;}
"""


def kit(rel: str) -> str:
    return (KIT / rel).read_text(encoding="utf-8")


def esc(s) -> str:
    return html.escape(str(s), quote=False)


WORDS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty twenty-one twenty-two twenty-three".split()


def word(n: int) -> str:
    return WORDS[n] if n < len(WORDS) else f"{n:,}"


# ====================================================================== the Makefile and mk/*.mk, as one text
MAKEFILE = kit("Makefile")
MK = MAKEFILE + "".join("\n" + p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))


def make_default(name: str) -> str:
    """The value a Makefile `NAME ?= value` (or `NAME = value`) line gives when nothing overrides it."""
    m = re.search(r"^" + re.escape(name) + r"\s*\??=\s*(.*)$", MK, re.M)
    assert m, name
    return m.group(1).strip()


SERVICES = make_default("SERVICES").split()
SCRIPTS = re.findall(r"commands/[\w.-]+\.sh", re.search(r"^SCRIPTS\s*=\s*((?:.*\\\n)*.*)$", MAKEFILE, re.M).group(1))
UP_TARGETS = re.search(r"^up: guard-project\n\t\$\(INFRA\) apply .*\n\t\$\(MAKE\) ([a-z -]+)$", MAKEFILE, re.M).group(1).split()
assert SERVICES and len(SCRIPTS) == len(SERVICES), (SERVICES, SCRIPTS)
assert UP_TARGETS[0] == "drift" and "deploy-services" in UP_TARGETS, UP_TARGETS

# the Terraform variables make plan passes, and the Makefile variable behind each (TF_EXTRA_VARS, with agents.mk's appends)
PASSES = dict(re.findall(r"-var '?(\w+)=\$\((\w+)\)", MK))

# ====================================================================== the Terraform, as text
TFDIR = KIT / "terraform"


def strip_comments(text: str) -> str:
    """Drop # comments outside strings and heredocs, keeping every line."""
    out, heredoc = [], None
    for line in text.splitlines():
        if heredoc:
            out.append(line)
            if line.strip() == heredoc:
                heredoc = None
            continue
        kept, q = [], False
        for i, ch in enumerate(line):
            if ch == '"' and (i == 0 or line[i - 1] != "\\"):
                q = not q
            if ch == "#" and not q:
                break
            kept.append(ch)
        line = "".join(kept)
        m = re.search(r"<<-?(\w+)\s*$", line)
        if m:
            heredoc = m.group(1)
        out.append(line)
    return "\n".join(out)


def tf_blocks(text: str):
    """Top-level blocks of one file: (kind, labels, body)."""
    res = []
    for m in re.finditer(r'^(resource|data|variable|output|locals|terraform|provider|module)\b([^{\n]*)\{', text, re.M):
        depth, i = 1, m.end()
        while depth:
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            elif c == '"':
                j = i + 1
                while text[j] != '"':
                    j += 2 if text[j] == "\\" else 1
                i = j
            elif c == "<" and re.match(r"<<-?(\w+)", text[i:]):
                tag = re.match(r"<<-?(\w+)", text[i:]).group(1)
                i = re.search(r"^\s*" + tag + r"\s*$", text[i:], re.M).end() + i - 1
            i += 1
        res.append((m.group(1), re.findall(r'"([^"]*)"', m.group(2)), text[m.end():i - 1]))
    return res


def expr_after(body: str, name: str, indent: str = "  "):
    """The expression of `name = ...` at the given indentation, joined across lines until its brackets balance."""
    m = re.search(r"^" + indent + re.escape(name) + r"\s*=\s*", body, re.M)
    if not m:
        return None
    i, depth, out = m.end(), 0, []
    while i < len(body):
        c = body[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        if c == "\n" and depth == 0:
            break
        out.append(c)
        i += 1
    return " ".join("".join(out).split())


FILES = OrderedDict((p.name, tf_blocks(strip_comments(p.read_text(encoding="utf-8")))) for p in sorted(TFDIR.glob("*.tf")))
ALL_BLOCKS = [(f, k, l, b) for f, bl in FILES.items() for (k, l, b) in bl]
RESOURCES = [(f, l[0], l[1], b) for f, k, l, b in ALL_BLOCKS if k == "resource"]
LOCALS = {}
for f, k, l, b in ALL_BLOCKS:
    if k == "locals":
        for m in re.finditer(r"^  (\w+)\s*=", b, re.M):
            LOCALS[m.group(1)] = expr_after(b, m.group(1))


def lit(v):
    v = (v or "").strip()
    if v in ("true", "false"):
        return v == "true"
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1]
    if v.startswith("["):
        return re.findall(r'"([^"]*)"', v)
    return v


# the variables: the .tf defaults, then what make plan passes with the Makefile's own defaults
TFVARS = {}
for f, k, l, b in ALL_BLOCKS:
    if k == "variable":
        d = expr_after(b, "default")
        TFVARS[l[0]] = lit(d) if d is not None else None
BASE_VARS = dict(TFVARS)
for tfvar, mkvar in PASSES.items():
    if tfvar in ("project_id", "region", "alert_emails"):
        continue
    v = make_default(mkvar)
    BASE_VARS[tfvar] = "set by make" if "$(" in v else lit(v)
BASE_VARS["alert_emails"] = [ME]          # ALERT_EMAILS_JSON: the setup block's ADMIN_EMAILS, one address
BASE_VARS["region"] = REGION


class Eval:
    """Just enough HCL to count the instances a count or for_each expression makes in this kit."""

    def __init__(self, variables):
        self.v = variables

    def __call__(self, e):
        e = " ".join(str(e).split())
        q = self._top(e, "?")
        if q is not None:
            rest = e[q + 1:]
            c = self._top(rest, ":")
            return self(rest[:c]) if self(e[:q]) else self(rest[c + 1:])
        if e.startswith("(") and e.endswith(")"):
            return self(e[1:-1])
        if " && " in e:
            return all(self(x) for x in e.split(" && "))
        if " || " in e:
            return any(self(x) for x in e.split(" || "))
        m = re.fullmatch(r"(.+?) (==|!=) (.+)", e)
        if m:
            a, b = self(m.group(1)), self(m.group(3))
            return (a == b) if m.group(2) == "==" else (a != b)
        m = re.fullmatch(r"contains\((\[.*?\]), (.+)\)", e)
        if m:
            return self(m.group(2)) in self(m.group(1))
        m = re.fullmatch(r"length\((.+)\) > 0", e)
        if m:
            return len(self(m.group(1))) > 0
        m = re.fullmatch(r"toset\((.+)\)", e)
        if m:
            return sorted(set(self(m.group(1))))
        if e.startswith("["):
            return re.findall(r'"([^"]*)"', e) if '"' in e else ([1] if e == "[1]" else [])
        if e.startswith("{"):
            inner, keys = e[1:-1], []
            for mm in re.finditer(r"(?:^|(?<=[\s,{]))([A-Za-z_][\w-]*)\s*=", inner):
                pre = inner[:mm.start()]
                if pre.count("{") == pre.count("}") and pre.count("[") == pre.count("]"):
                    keys.append(mm.group(1))
            return keys
        if e.startswith("var."):
            return self.v[e[4:]]
        if e.startswith("local."):
            return self(LOCALS[e[6:]])
        if e.startswith('"'):
            return e.strip('"')
        if re.fullmatch(r"-?\d+", e):
            return int(e)
        if e in ("true", "false"):
            return e == "true"
        if re.fullmatch(r"google_\w+\.\w+", e):            # for_each over another resource's instances
            t, n = e.split(".")
            body = next(b for f, rt, rn, b in RESOURCES if (rt, rn) == (t, n))
            return self(expr_after(body, "for_each"))
        raise ValueError(f"cannot evaluate: {e}")

    @staticmethod
    def _top(e, ch):
        depth = 0
        for i, c in enumerate(e):
            if c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
            elif c == ch and depth == 0:
                return i
        return None


def instances(body, ev):
    """(how many instances, their keys or None, the gating expression or None)."""
    c, f = expr_after(body, "count"), expr_after(body, "for_each")
    if c is not None:
        return int(ev(c)), None, c
    if f is not None:
        keys = ev(f)
        return len(keys), keys, f
    return 1, None, None


def census(variables):
    ev = Eval(variables)
    rows = []
    for f, rt, rn, b in RESOURCES:
        n, keys, gate = instances(b, ev)
        rows.append((f, rt, rn, n, keys, gate))
    return rows


BASE = census(BASE_VARS)
N_RESOURCES = sum(r[3] for r in BASE)
BY_TYPE = Counter()
BY_FILE = Counter()
for f, rt, rn, n, keys, gate in BASE:
    BY_TYPE[rt] += n
    BY_FILE[f] += n


def count_of(rtype: str, rows=BASE) -> int:
    return sum(r[3] for r in rows if r[1] == rtype)


def res(rtype: str, rname: str):
    return next((f, b) for f, rt, rn, b in RESOURCES if (rt, rn) == (rtype, rname))


# ====================================================================== identities
SA_ADDR = {}                 # terraform name -> [account ids] (a for_each makes several)
SA_INFO = OrderedDict()      # account id -> {...}
for f, rt, rn, n, keys, gate in census({**BASE_VARS, "gchat_door": True}):
    if rt != "google_service_account":
        continue
    body = res(rt, rn)[1]
    acc = expr_after(body, "account_id").strip('"')
    disp = expr_after(body, "display_name")
    names = []
    if keys:
        dmap = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', LOCALS[expr_after(body, "for_each").split(".", 1)[1]]))
        for k in keys:
            names.append((acc.replace("${each.key}", k), dmap[k]))
    else:
        names.append((acc, disp.strip('"')))
    base_n = next(r[3] for r in BASE if (r[1], r[2]) == (rt, rn))
    SA_ADDR[rn] = [a for a, _ in names]
    for a, d in names:
        SA_INFO[a] = {"tf": rn, "file": f, "display": d, "gate": gate if base_n == 0 else None, "on": base_n > 0,
                      "gate_expr": gate}
N_SA = sum(1 for a in SA_INFO.values() if a["on"])
N_SA_ALL = len(SA_INFO)
assert N_SA == count_of("google_service_account")


def sa_ref(text: str):
    """The account a Terraform member or target names: google_service_account.X.email / .name, X[0] included."""
    m = re.search(r"google_service_account\.(\w+)(?:\[0\])?\.(?:email|name)", text or "")
    return SA_ADDR[m.group(1)][0] if m and len(SA_ADDR[m.group(1)]) == 1 else None


# project roles: every google_project_iam_member, a literal role or each.value over toset(local.X_roles); the
# Google Chat door's two (GCHAT_DOOR) are read with the door on, so its accounts show what they would hold
PROJECT_ROLES = {a: [] for a in SA_INFO}
for f, rt, rn, n, keys, gate in census({**BASE_VARS, "gchat_door": True}):
    if rt != "google_project_iam_member" or n == 0:
        continue
    body = res(rt, rn)[1]
    who = sa_ref(expr_after(body, "member"))
    if not who:
        continue
    role = expr_after(body, "role")
    roles = keys if role == "each.value" else [role.strip('"')]
    cond = re.search(r'condition \{\s*title\s*=\s*"([^"]+)"', body)
    for r in roles:
        r = r + (f" (only where the condition {cond.group(1)} holds)" if cond else "")
        if r not in PROJECT_ROLES[who]:
            PROJECT_ROLES[who].append(r)

# bucket names, then the grants on one bucket
BUCKETS = OrderedDict()
for f, rt, rn, b in RESOURCES:
    if rt == "google_storage_bucket":
        BUCKETS[rn] = {"name": expr_after(b, "name").strip('"').replace("${var.project_id}", "PROJECT"),
                       "location": expr_after(b, "location"), "body": b, "file": f}
BUCKET_GRANTS = {a: [] for a in SA_INFO}
for f, rt, rn, b in RESOURCES:
    if rt == "google_storage_bucket_iam_member":
        bucket = re.search(r"google_storage_bucket\.(\w+)\.name", expr_after(b, "bucket")).group(1)
        who = sa_ref(expr_after(b, "member"))
        BUCKET_GRANTS[who].append((BUCKETS[bucket]["name"], expr_after(b, "role").strip('"')))

# secrets: the six holders (secrets.tf), the checkpoint DSN (cloudsql.tf), and who may read which
SECRET_NAMES = BASE_VARS["secret_names"]
SECRET_GRANTS = {a: [] for a in SA_INFO}
for f, rt, rn, b in RESOURCES:
    if rt != "google_secret_manager_secret_iam_member":
        continue
    who = sa_ref(expr_after(b, "member"))
    sid = expr_after(b, "secret_id")
    if sid == "each.value.id":
        names = list(SECRET_NAMES)
    elif "checkpoint_dsn" in sid:
        names = [expr_after(res("google_secret_manager_secret", "checkpoint_dsn")[1], "secret_id").strip('"')]
    else:
        names = [re.search(r'\["([^"]+)"\]', sid).group(1)]
    SECRET_GRANTS[who] += names

# grants on one database or dataset: Spanner (spanner.tf), BigQuery (dataplex.tf)
DATA_GRANTS = {a: [] for a in SA_INFO}
sp_body = res("google_spanner_database_iam_member", "graph_users")[1]
sp_role = expr_after(sp_body, "role").strip('"')
for k, v in re.findall(r"(\w+)\s*=\s*(google_service_account\.\w+\.email)", expr_after(sp_body, "for_each")):
    DATA_GRANTS[sa_ref(v)].append(("Spanner database documind (instance documind-graph)", sp_role))
for f, rt, rn, n, keys, gate in BASE:
    b = res(rt, rn)[1]
    if rt == "google_bigquery_dataset_iam_member":
        who = sa_ref(expr_after(b, "member"))
        if who:
            ds = re.search(r"google_bigquery_dataset\.(\w+)\.dataset_id", expr_after(b, "dataset_id")).group(1)
            DATA_GRANTS[who].append((f"BigQuery dataset {ds}", expr_after(b, "role").strip('"')))
    if rt == "google_artifact_registry_repository_iam_member" and n:
        DATA_GRANTS[sa_ref(expr_after(b, "member"))].append(("Artifact Registry repository documind", expr_after(b, "role").strip('"')))

# grants ON an account: who may act as it (serviceAccountUser) or mint its tokens (serviceAccountTokenCreator)
ACTORS = {a: [] for a in SA_INFO}
for f, rt, rn, n, keys, gate in BASE:
    if rt != "google_service_account_iam_member" or n == 0:
        continue
    b = res(rt, rn)[1]
    role = expr_after(b, "role").strip('"').replace("roles/iam.", "")
    member = expr_after(b, "member")
    who = sa_ref(member) or ("Pub/Sub's service agent" if "gcp-sa-pubsub" in member else
                             "the GitHub repository you name (Workload Identity Federation)" if "principalSet" in member else member)
    target = expr_after(b, "service_account_id")
    if target == "each.value":
        fe = expr_after(b, "for_each")
        targets = [sa_ref(v) or "the Compute Engine default account" for v in re.findall(r"=\s*([\w.]+)", LOCALS[fe.split(".", 1)[1]] if fe.startswith("local.") else fe)]
    else:
        targets = [sa_ref(target)]
    for t in targets:
        if t in ACTORS:
            ACTORS[t].append((who, role))
OPERATOR_TARGETS = re.search(r"for sa in (documind-[a-z-]+(?: documind-[a-z-]+)*); do \\\n\s+gcloud iam service-accounts add-iam-policy-binding \$\$sa@",
                             MAKEFILE).group(1).split()
for t in OPERATOR_TARGETS:
    ACTORS[t].append(("each address in ADMIN_EMAILS (make operators, run by make up)", "serviceAccountTokenCreator"))

N_ACTAS = len(Eval(BASE_VARS)(LOCALS["cicd_actas"]))

# ====================================================================== the seven services, from the deploy scripts make up runs
SVC = OrderedDict()
for script in SCRIPTS:
    text = kit(script)
    deploy = re.search(r"^# ---- DEPLOY ----$(.*?)(?=^# ---- [A-Z_]+ ----$|\Z)", text, re.M | re.S).group(1)
    for m in re.finditer(r"^gcloud run deploy (documind-[a-z]+) \\\n((?:.*\\\n)*.*)$", deploy, re.M):
        name, flags = m.group(1), m.group(2)
        sa = re.search(r"--service-account=([a-z0-9-]+)@", flags).group(1)
        get = lambda flag: (re.search(r"--" + flag + r"=(\S+)", flags) or [None, None])[1]  # noqa: E731
        env = re.search(r'--set-env-vars="?([^"\n]*)', flags)
        env = env.group(1) if env else ""
        calls = [s for k, s in (("RAG_API_URL=", "documind-api"), ("MCP_URL=", "documind-mcp"), ("CHAT_URL=", "documind-chat"))
                 if re.search(r"(^|\|)" + k, env) or (k == "CHAT_URL=" and "|CHAT_URL=$CHAT_URL|" in env)]
        iap = "--iap" in flags or bool(re.search(r"run services update " + name + r" .*--iap", deploy))
        SVC[name] = {"script": script, "sa": sa, "ingress": get("ingress") or "all (the default)", "iap": iap,
                     "min": get("min-instances"), "max": get("max-instances"), "region": get("region"),
                     "image": get("image"), "calls": calls, "invokers": [], "vpc": "--vpc-connector" in flags}
    # who may call each service: the for-loops, then single bindings
    loops = list(re.finditer(r"for (?:who|sa) in ((?:[a-z0-9-]+\s*(?:\\\n\s*)?)+); do\n(.*?)\ndone", deploy, re.S))
    for m in loops:
        names = m.group(1).replace("\\", " ").split()
        target = re.search(r"run services add-iam-policy-binding (documind-[a-z]+)", m.group(2))
        if target:
            SVC[target.group(1)]["invokers"] += names
    rest = deploy
    for m in loops:
        rest = rest.replace(m.group(0), "")
    for m in re.finditer(r"run services add-iam-policy-binding (documind-[a-z]+) \\\n(?:.*\\\n)*?.*--member=\"serviceAccount:([^@\"]+)@([^\"]*)\"", rest):
        SVC[m.group(1)]["invokers"].append("IAP's service agent" if m.group(3).startswith("gcp-sa-iap.") else m.group(2))
assert list(SVC) == [f"documind-{s}" if s != "api" else "documind-api" for s in SERVICES] or len(SVC) == len(SERVICES), list(SVC)
assert all(SVC[s]["sa"] in SA_INFO for s in SVC), {s: SVC[s]["sa"] for s in SVC}
for s, v in SVC.items():
    SA_INFO[v["sa"]]["runs"] = s
N_SERVICES = len(SVC)

# sa.tf's caller graph, the six lines check_authz.py reads, against the scripts: they must agree for the services make up deploys
GRAPH = {m.group(1): [x.strip() for x in m.group(2).split(",")]
         for m in re.finditer(r"^#\s+(documind-[a-z]+)\s+<- (.+?)\s+\((?:lesson-[\d.]+\.sh|gchat\.sh)\)$", kit("terraform/sa.tf"), re.M)}
for s, v in SVC.items():
    if s in GRAPH and s != "documind-ui":
        assert sorted(GRAPH[s]) == sorted(v["invokers"]), (s, GRAPH[s], v["invokers"])

# ====================================================================== the stores
FS_INDEXES = []   # (resource, collection, vector?)
for f, rt, rn, n, keys, gate in BASE:
    if rt != "google_firestore_index":
        continue
    b = res(rt, rn)[1]
    coll = expr_after(b, "collection")
    vec = "vector_config" in b
    if coll == "each.value.collection":
        lmap = LOCALS[expr_after(b, "for_each").split(".", 1)[1]]
        for k in keys:
            c = re.search(k + r'\s*=\s*\{\s*collection\s*=\s*"([^"]+)"', lmap).group(1)
            FS_INDEXES.append((rn, c, vec, f))
    else:
        FS_INDEXES += [(rn, coll.strip('"'), vec, f)] * n
N_FS_INDEXES, N_FS_VECTOR = len(FS_INDEXES), sum(1 for x in FS_INDEXES if x[2])
assert N_FS_INDEXES == count_of("google_firestore_index")
TTL_FIELDS = []   # (collection, database, file, on by default)
for f, rt, rn, n, keys, gate in census({**BASE_VARS, "gchat_door": True}):
    if rt == "google_firestore_field":
        b = res(rt, rn)[1]
        if "ttl_config" in b:
            base_n = next(r[3] for r in BASE if (r[1], r[2]) == (rt, rn))
            db = "documind-gchat" if "gchat" in expr_after(b, "database") else "(default)"
            TTL_FIELDS.append((expr_after(b, "collection").strip('"'), db, f, base_n > 0))
N_TTL = sum(1 for t in TTL_FIELDS if t[3])

N_SQL = count_of("google_sql_database_instance")
SQL = [(expr_after(b, "name").strip('"'), f, re.search(r'tier\s*=\s*"([^"]+)"', b).group(1),
        re.search(r'availability_type\s*=\s*"([^"]+)"', b).group(1), re.search(r"disk_size\s*=\s*(\d+)", b).group(1))
       for f, rt, rn, b in RESOURCES if rt == "google_sql_database_instance"]
SP_BODY = res("google_spanner_instance", "graph")[1]
SPANNER_PU = int(re.search(r"processing_units\s*=\s*(\d+)", SP_BODY).group(1))
SPANNER_CONFIG = re.search(r'config\s*=\s*"([^"]+)"', SP_BODY).group(1)
SPANNER_EDITION = re.search(r'edition\s*=\s*"([^"]+)"', SP_BODY).group(1)
VEC_DEPLOY = res("google_vertex_ai_index_endpoint_deployed_index", "documind")[1]
VEC_REPLICAS = int(re.search(r"min_replica_count\s*=\s*(\d+)", VEC_DEPLOY).group(1))
assert VEC_REPLICAS == int(re.search(r"max_replica_count\s*=\s*(\d+)", VEC_DEPLOY).group(1))
SHARD_MACHINE = OrderedDict(re.findall(r"(SHARD_SIZE_\w+)\s*=\s*\"([\w-]+)\"", LOCALS["vector_machine_by_shard"]))
VEC_INDEX = res("google_vertex_ai_index", "documind")[1]
VEC_DIMS = int(re.search(r"dimensions\s*=\s*(\d+)", VEC_INDEX).group(1))
assert "shard_size" not in VEC_INDEX                        # the page says the service chooses: true while vector.tf names none
GKE_POOL = res("google_container_node_pool", "lab")[1]
GKE_MACHINE = re.search(r'machine_type\s*=\s*"([^"]+)"', GKE_POOL).group(1)
GKE_DISK = int(re.search(r"disk_size_gb\s*=\s*(\d+)", GKE_POOL).group(1))
GKE_DISK_TYPE = re.search(r'disk_type\s*=\s*"([^"]+)"', GKE_POOL).group(1)
GKE_NODES = int(re.search(r"node_count\s*=\s*(\d+)", GKE_POOL).group(1))
CONN = res("google_vpc_access_connector", "conn")[1]
CONN_MIN = int(re.search(r"min_instances\s*=\s*(\d+)", CONN).group(1))
CONN_MAX = int(re.search(r"max_instances\s*=\s*(\d+)", CONN).group(1))
assert "machine_type" not in CONN                           # the page prices the documented default, e2-micro
BQ_DATASETS = [expr_after(b, "dataset_id").strip('"') for f, rt, rn, b in RESOURCES if rt == "google_bigquery_dataset"]
BQ_TABLES = [expr_after(b, "table_id").strip('"') for f, rt, rn, b in RESOURCES if rt == "google_bigquery_table"]
DATA_STORES = [f"documind-{t}" for t in Eval(BASE_VARS)(LOCALS["managed_tenants"])]
MANAGED_TENANTS = make_default("MANAGED_TENANTS").split()
N_SECRETS = count_of("google_secret_manager_secret")
N_METRICS, N_ALERTS = count_of("google_logging_metric"), count_of("google_monitoring_alert_policy")

# ====================================================================== the switches: off on a first lane, refused once applied and then left off
SWITCHES = re.search(r"^SWITCHES = \(([^)]*)\)", kit("commands/infrastructure.py"), re.M).group(1)
SWITCHES = re.findall(r'"(\w+)"', SWITCHES)
MK_TO_TF = {mk: tf for tf, mk in PASSES.items()}
SWITCH_ROWS = []
for sw in SWITCHES:
    tfvar = MK_TO_TF[sw]
    on = census({**BASE_VARS, tfvar: True})
    added = [(f, rt, rn, n2 - n1) for (f, rt, rn, n1, *_), (_, _, _, n2, *__) in zip(BASE, on) if n2 != n1]
    SWITCH_ROWS.append((sw, tfvar, make_default(sw), added))
assert all(r[2] == "false" for r in SWITCH_ROWS), SWITCH_ROWS

# ====================================================================== the APIs make apis enables, and the ones preflight checks
ENABLE = re.search(r"^# ---- ENABLE_APIS ----$(.*?)^# ---- APPLY ----$", kit("commands/lesson-12.1.sh"), re.M | re.S).group(1)
APIS = re.findall(r"([a-z0-9]+)\.googleapis\.com", ENABLE)
assert len(APIS) == len(set(APIS))
PREFLIGHT = kit("smoke/preflight.sh")
CHECKED = re.search(r"for api in ((?:[a-z]+\s*\\?\s*)+); do", PREFLIGHT).group(1).replace("\\", " ").split()
assert set(CHECKED) <= set(APIS), set(CHECKED) - set(APIS)

# ====================================================================== what make roster writes: commands/lane.py's own dry run
r = subprocess.run([sys.executable, "commands/lane.py", "--project", PROJ, "roster", "--tenant", "acme", "--members", ME, "--dry-run"],
                   cwd=str(KIT), capture_output=True, text=True, encoding="utf-8")
assert r.returncode == 0, r.stderr[-600:]
ROSTER_DRY = r.stdout.replace(PROJ.lower(), PROJ).rstrip("\n")
N_ROSTER = len(re.findall(r"^would put ", ROSTER_DRY, re.M))

# ====================================================================== the printed lines the page predicts, from the code that prints them
INFRA = kit("commands/infrastructure.py")
PREPARE_EXPECTED = "\n".join([
    "PASS: saved confirmed inputs to /home/you/deploy_module_rag/terraform/runbook-project.auto.tfvars.json",
    "CI trust: YOUR-GITHUB-USER/YOUR-REPO (ID NUMBER) / refs/heads/main"])
assert 'print(f"PASS: saved confirmed inputs to {self.inputs}")' in INFRA
assert "print(f\"CI trust: {confirmed['github_repository']} (ID {confirmed['github_repository_id']}) / {confirmed['deploy_ref']}\")" in INFRA
ok_lines = []
for m in re.finditer(r'ok "([^"]+)"', PREFLIGHT):
    t = m.group(1)
    t = (t.replace("$tool", "{tool}").replace("$tfv", "VERSION").replace("$acct", ME).replace("$PROJECT", PROJ)
          .replace("$TFSTATE_BUCKET", PROJ + "-tfstate"))
    if "{tool}" in t:
        ok_lines += ["  ok    " + t.format(tool=x) for x in re.search(r"for tool in ([a-z ]+); do", PREFLIGHT).group(1).split()]
    else:
        ok_lines.append("  ok    " + t)
PREFLIGHT_EXPECTED = "\n".join(ok_lines + ["", re.search(r'echo "(preflight clean[^"]*)"', PREFLIGHT).group(1),
                                           re.search(r'echo "(not checkable from here[^"]*)"', PREFLIGHT).group(1)])
assert "$" not in PREFLIGHT_EXPECTED, PREFLIGHT_EXPECTED

# ====================================================================== what bills by the hour, in rupees
# The standing cost is shared with 0.1 and 0.4, so the three pages state one figure: lessons/00-setup/standing_cost.py
# parses the sizes from the Terraform and prices them at Mumbai's list prices (its docstring says how). Step 10 shows
# its items an hour; the sizes this page reads for the store table above must be the module's, or the build stops.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import standing_cost as sc  # noqa: E402
assert dict(SHARD_MACHINE) == sc.SHARD_MACHINE and VEC_REPLICAS == sc.VS_REPLICAS
assert (SPANNER_PU, SPANNER_EDITION, SPANNER_CONFIG) == (sc.SP_PU, sc.SP_EDITION, sc.SP_CONFIG)
assert sorted((n, t, a, int(d)) for n, f, t, a, d in SQL) == sorted(sc.SQL) and N_SQL == len(sc.SQL)
assert (GKE_NODES, GKE_MACHINE, GKE_DISK, GKE_DISK_TYPE, CONN_MIN) == (sc.GKE_NODES, sc.GKE_MACHINE, sc.GKE_DISK_GB, sc.GKE_DISK_TYPE, sc.CONN_MIN)
USD_INR = sc.USD_INR
SMALL, MEDIUM = sc.SHARDS                   # "small" and "medium": the two shard sizes the module prices
USD_H = {k: u for k, *_, u in sc.ITEMS if k != "index"}   # every item's dollars an hour but the index's (sc.INDEX_USD)
# the pricing pages the module's prices were read from, each named in its comments, linked from the table
PRICE_URLS = {
    "vs": "https://cloud.google.com/vertex-ai/pricing", "spanner": "https://cloud.google.com/spanner/pricing",
    "sql": "https://cloud.google.com/sql/pricing", "ce": "https://cloud.google.com/products/compute/pricing/general-purpose",
    "pd": "https://cloud.google.com/compute/disks-image-pricing",
    "gke": "https://cloud.google.com/kubernetes-engine/pricing", "vpc": "https://cloud.google.com/vpc/pricing",
}
assert all(u in Path(sc.__file__).read_text(encoding="utf-8") for u in PRICE_URLS.values())
# the kit's own Cloud SQL figure, quoted in step 10, against one instance's month at the module's prices
SQL_USD_MONTH = tuple(int(x) for x in re.search(r"roughly \$(\d+)-(\d+) \(Rs", kit("terraform/cloudsql.tf")).groups())
SQL_MONTH = USD_H["sql"] / len(sc.SQL) * sc.MONTH_H
assert SQL_MONTH > SQL_USD_MONTH[1], (SQL_MONTH, SQL_USD_MONTH)      # the page says the list price is above the comment's


def inr(usd: float) -> float:
    return usd * USD_INR


def rs(x: float) -> str:
    return f"{x:,.2f}"


def usd(x: float) -> str:
    """A list price as the page prints it: every digit the source gives, never fewer than two decimals, never 5e-05."""
    s = ("%.10f" % x).rstrip("0")
    whole, frac = s.split(".")
    return f"${whole}.{frac.ljust(2, '0')}"


# ====================================================================== HTML pieces
def code(s) -> str:
    return "<code>" + esc(s) + "</code>"


def table(head, rows, labels=None) -> str:
    """A comp-table in its scroll wrapper; every cell after the first carries its column's data-label."""
    labels = labels or head
    out = ['<div class="tw"><div class="tw-scroll" tabindex="0"><table class="comp-table">',
           "<thead><tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr></thead>", "<tbody>"]
    for r in rows:
        cells = [f"<td>{r[0]}</td>"] + [f'<td data-label="{esc(labels[i])}">{c}</td>' for i, c in enumerate(r[1:], 1)]
        out.append("<tr>" + "".join(cells) + "</tr>")
    out.append('</tbody></table></div><span class="scroll-hint">&#8596; SWIPE</span></div>')
    return "\n".join(out) + "\n"


def output(label: str, text: str) -> str:
    """A read-only window for what a command prints: plain text, no highlighting."""
    return ('<div class="cw"><div class="ch-bar"><span>' + esc(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + esc(text) + "</pre></div>\n")


def region_of(v) -> str:
    return "REGION" if v and v.startswith("${REGION") else (v or "the gcloud default")


def instances_of(v) -> str:
    lo = "MIN_INSTANCES (0)" if v["min"] == "${MIN_INSTANCES:-0}" else (v["min"] or "0 (the default)")
    return f"min {lo}, max {v['max'] or 'the default'}"


def who_list(names) -> str:
    out = []
    for n in names:
        tag = " (skipped while it does not exist: GCHAT_DOOR)" if n in SA_INFO and not SA_INFO[n]["on"] else ""
        out.append(code(n) + tag if n.startswith("documind-") else esc(n))
    return ", ".join(out) or "nobody: no run.invoker binding in its script"


SERVICE_ROWS = []
for s, v in SVC.items():
    SERVICE_ROWS.append([code(s), code(v["sa"]), esc(v["ingress"]) + (", IAP" if v["iap"] else ""), esc(instances_of(v)),
                         who_list(v["invokers"]), ", ".join(code(c) for c in v["calls"]) or "none named", code(v["script"]),
                         esc(region_of(v["region"]))])
SERVICE_TABLE = table(["Service", "Runs as", "Ingress", "Instances", "Who may call it", "Calls", "Deployed by", "Region"], SERVICE_ROWS)

# the other accounts: what each is for, read from where the kit uses it
USED = {}
for f, rt, rn, b in RESOURCES:
    for m in re.finditer(r"service_account(?:_email)?\s*=\s*google_service_account\.(\w+)(?:\[0\])?\.email", b):
        USED.setdefault(SA_ADDR[m.group(1)][0], set()).add(f"{rt}.{rn} ({f})")
for m in re.finditer(r"--service-account[ =](documind-[a-z0-9-]+)@", MK):
    tgt = re.findall(r"^([a-z][\w-]*):", MK[:m.start()], re.M)[-1]
    USED.setdefault(m.group(1), set()).add(f"make {tgt}")


def group_of(a: str) -> str:
    i, used = SA_INFO[a], USED.get(a, ())
    if i.get("runs"):
        return "runs one of the services make up deploys"
    if not i["on"]:
        return "declared only with GCHAT_DOOR=true"
    if "eval" in a or "outsider" in a:
        return "a fixture: an identity the tests call as"
    if "cicd" in a:
        return "the pipeline's identity"
    if any(u.startswith("make deploy-") for u in used):
        return "runs a service deployed on request"
    if any(u.startswith(("google_cloud_run_v2_job.", "google_container_")) for u in used):
        return "runs a job or a node"
    return "declared, and used by no target yet"


GROUP_ORDER = ["runs one of the services make up deploys", "runs a job or a node", "the pipeline's identity",
               "a fixture: an identity the tests call as", "runs a service deployed on request",
               "declared, and used by no target yet", "declared only with GCHAT_DOOR=true"]
ORDERED = sorted(SA_INFO, key=lambda a: (GROUP_ORDER.index(group_of(a)),
                                         list(SVC).index(SA_INFO[a]["runs"]) if SA_INFO[a].get("runs") else 0, a))
assert all(group_of(a) in GROUP_ORDER for a in SA_INFO)
GROUP_N = Counter(group_of(a) for a in SA_INFO)
# the accounts that reach every bucket through a storage role on the project: the prose of step 5 names why each holds one
WIDE = sorted(a for a in SA_INFO if SA_INFO[a]["on"] and any(r.startswith("roles/storage.") for r in PROJECT_ROLES[a]))
assert WIDE == ["documind-admin-sa", "documind-ingest-sa", "documind-mcp-sa"], WIDE

SA_ROWS = []
for a in ORDERED:
    i = SA_INFO[a]
    used = sorted(USED.get(a, ()))
    what = (f"runs {code(i['runs'])}" if i.get("runs") else
            ("used by " + ", ".join(code(u) for u in used)) if used else "used by nothing make up deploys")
    SA_ROWS.append([code(a), esc(i["display"]), esc(group_of(a)), what, code("terraform/" + i["file"]),
                    str(len([r for r in PROJECT_ROLES[a]]))])
SA_TABLE = table(["Account", "Its display name", "Kind", "What uses it", "Declared in", "Project roles"], SA_ROWS)

# buckets: what storage.tf declares about each, and who may touch it
BUCKET_ROWS = []
PROJECT_WIDE_STORAGE = {a: [r for r in PROJECT_ROLES[a] if r.startswith("roles/storage.")] for a in SA_INFO}
for rn, bk in BUCKETS.items():
    b = bk["body"]
    traits = []
    if "versioning { enabled = true }" in b:
        traits.append("versioned")
    for d, t, cls in re.findall(r"lifecycle_rule \{\s*condition \{ age = (\d+) \}\s*action \{\s*type\s*=\s*\"(\w+)\"(?:\s*storage_class\s*=\s*\"(\w+)\")?", b):
        traits.append(f"to {cls} after {d} days" if t == "SetStorageClass" else f"{t.lower()}d after {d} days")
    if "retention_policy" in b:
        secs = int(re.search(r"retention_period = (\d+)", b).group(1))
        traits.append(f"retention {secs // (365 * 86400)} years, locked only with AUDIT_LOCK=true")
    if "force_destroy               = false" in b:
        traits.append("force_destroy false")
    if 'public_access_prevention    = "enforced"' in b:
        traits.append("public access prevented")
    named = [f"{code(a)} {esc(r.replace('roles/storage.', ''))}" for a in SA_INFO for (bn, r) in BUCKET_GRANTS[a] if bn == bk["name"]]
    wide = sorted({a for a, rr in PROJECT_WIDE_STORAGE.items() if rr and SA_INFO[a]["on"]})
    BUCKET_ROWS.append([code(bk["name"]), esc(region_of(bk["location"].replace("var.india_region", "asia-south1"))),
                        esc(", ".join(traits)), ", ".join(named) or "none by name",
                        ", ".join(code(a) for a in wide)])
BUCKET_TABLE = table(["Bucket", "Where", "What storage.tf sets", "Granted on this bucket", "Reaches every bucket (a project role)"], BUCKET_ROWS)

# Firestore: the indexes by collection, with the TTL fields beside them
coll_rows = OrderedDict()
for rn, coll, vec, f in FS_INDEXES:
    c = coll_rows.setdefault(coll, {"n": 0, "vec": 0, "files": set()})
    c["n"] += 1
    c["vec"] += vec
    c["files"].add(f)
for coll, db, f, on in TTL_FIELDS:
    if on:
        coll_rows.setdefault(coll, {"n": 0, "vec": 0, "files": set()})
FS_ROWS = []
for coll, c in sorted(coll_rows.items(), key=lambda x: (-x[1]["n"], x[0])):
    ttl = next((t for t in TTL_FIELDS if t[0] == coll and t[3]), None)
    FS_ROWS.append([code(coll), str(c["n"]), str(c["vec"]), code("expire_at") if ttl else "none",
                    ", ".join(code("terraform/" + x) for x in sorted(c["files"] | ({ttl[2]} if ttl else set())))])
FS_ROWS.append(["<strong>in all</strong>", f"<strong>{N_FS_INDEXES}</strong>", f"<strong>{N_FS_VECTOR}</strong>",
                f"<strong>{N_TTL} TTL fields</strong>", ""])
FS_TABLE = table(["Collection", "Composite indexes", "of them vector (768-d)", "TTL field", "Declared in"], FS_ROWS)

# the stores and the other things a plan creates once
RES_FILES = OrderedDict()
for f, n in BY_FILE.items():
    RES_FILES[f] = n
FILE_NOTES = {
    "sa.tf": "the runtime accounts, the pipeline's, and their project roles and actAs",
    "secrets.tf": "six secret holders, created empty, and who may read them",
    "firestore_indexes.tf": "the indexes and TTL fields of the default database",
    "storage.tf": "the five buckets and the grants on each",
    "alerts.tf": "log metrics, alert policies and one e-mail channel per ADMIN_EMAILS address",
    "desk.tf": "the case queue's indexes and TTL fields, the five Desk eval accounts",
    "desk_alerts.tf": "the Desk's log metrics and the alerts that need no switch",
    "off.tf": "the nightly off job, its schedule and its account",
    "gateway.tf": "the gateway's account, its Cloud SQL instance, the vLLM engine's account",
    "dataplex.tf": "the rag_data dataset, four tables and the quality scan",
    "eventarc.tf": "the upload notification, two topics and the push subscription with its dead-letter queue",
    "cloudsql.tf": "the chat checkpointer's Cloud SQL instance and its DSN secret",
    "managed.tf": "the RAG Engine APIs and agent, a Vertex AI Search data store per mirrored tenant",
    "spanner.tf": "the Spanner instance, its graph database and three database users",
    "gke.tf": "the regional Standard cluster, one node and the node account",
    "wif.tf": "the GitHub workload identity pool and provider, and the pipeline's token grants",
    "network.tf": "the VPC, its subnet and the Serverless VPC Access connector",
    "vector.tf": "the Vector Search index, its endpoint and the deployed index",
    "sink.tf": "the observability dataset and the log sink into it",
    "clouddeploy.tf": "the delivery pipeline and its two targets",
    "budget.tf": "the billing budget",
    "docai.tf": "one Document AI processor, chosen by RESIDENCY",
    "firestore.tf": "the default Firestore database, delete-protected",
    "model_armor.tf": "the Model Armor template",
    "registry.tf": "the documind Docker repository",
}
FILE_ROWS = [[code("terraform/" + f), str(n), esc(FILE_NOTES.get(f, ""))] for f, n in sorted(RES_FILES.items(), key=lambda x: (-x[1], x[0])) if n]
ZERO_FILES = [f for f, n in RES_FILES.items() if n == 0]
FILE_ROWS.append(["<strong>in all</strong>", f"<strong>{N_RESOURCES}</strong>", "with one address in ADMIN_EMAILS; "
                  + ", ".join(code(f) for f in ZERO_FILES) + " add nothing until a switch or a variable turns them on"])
FILE_TABLE = table(["File", "Instances", "What they are"], FILE_ROWS)
assert set(FILE_NOTES) >= {f for f, n in RES_FILES.items() if n}, {f for f, n in RES_FILES.items() if n} - set(FILE_NOTES)

TYPE_TEXT = "\n".join(f"{n:4d}  {t}" for t, n in sorted(BY_TYPE.items(), key=lambda x: (-x[1], x[0])) if n) + f"\n{N_RESOURCES:4d}  in all"

# the other stores and the things a plan creates once, each with its file and its region
RESIDENCY = make_default("RESIDENCY")
DOCAI = {k: (loc, typ) for k, loc, typ in re.findall(r'(\w+)\s*=\s*\{\s*location\s*=\s*"([^"]+)",\s*type\s*=\s*"([^"]+)"\s*\}', LOCALS["docai"])}
RAG_LOCATION = make_default("RAG_LOCATION")
DLQ_ATTEMPTS = int(re.search(r"max_delivery_attempts\s*=\s*(\d+)", kit("terraform/eventarc.tf")).group(1))
REG = kit("terraform/registry.tf")
REG_KEEP = int(re.search(r"keep_count = (\d+)", REG).group(1))
REG_DAYS = int(re.search(r'older_than = "(\d+)s"', REG).group(1)) // 86400
OBS_DAYS = int(re.search(r"default_table_expiration_ms = (\d+)", kit("terraform/sink.tf")).group(1)) // 86_400_000
BUDGET = kit("terraform/budget.tf")
THRESHOLDS = [float(x) for x in re.findall(r"threshold_percent = ([0-9.]+)", BUDGET)]
SUBNET = re.search(r'ip_cidr_range = "([^"]+)"', kit("terraform/network.tf")).group(1)
OFF = kit("terraform/off.tf")
OFF_AT = re.search(r'schedule    = "0 (\d+) \* \* \*"', OFF).group(1)
sql_desc = "; ".join(f"{code(n)}, {esc(t)}, {esc(a.lower())}, {d} GB" for n, f, t, a, d in SQL)
STORE_ROWS = [
    ["Vector Search", f"index {code('documind-chunks')}, {VEC_DIMS} dimensions, streaming updates; a public endpoint; the deployed index, {word(VEC_REPLICAS)} replica",
     code("vector.tf"), "REGION", "yes: the deployed index"],
    ["Cloud SQL", f"{word(N_SQL)} instances: {sql_desc}; the chat service's checkpointer and the gateway's spend logs",
     code("cloudsql.tf") + ", " + code("gateway.tf"), "REGION", "yes: both instances"],
    ["Spanner", f"instance {code('documind-graph')}, {esc(SPANNER_EDITION.title())}, {SPANNER_PU} processing units, and the graph database", code("spanner.tf"),
     esc(SPANNER_CONFIG), "yes"],
    ["BigQuery", f"{' and '.join(code(d) for d in BQ_DATASETS)}: {len(BQ_TABLES)} declared tables, the log sink's table ({OBS_DAYS}-day expiry) and a quality scan",
     code("dataplex.tf") + ", " + code("sink.tf"), "asia-south1", "no: storage and queries"],
    ["Vertex AI Search", "a data store per mirrored tenant: " + ", ".join(code(d) for d in DATA_STORES), code("managed.tf"), "global", "no: storage"],
    ["RAG Engine", "a corpus each for " + " and ".join(MANAGED_TENANTS) + f", made by {code('make managed-stores')} during make up, not by Terraform",
     code("Makefile"), esc(RAG_LOCATION), "no: storage"],
    ["Document AI", f"one processor: RESIDENCY={esc(RESIDENCY)} picks {code(DOCAI[RESIDENCY][1])} in {code(DOCAI[RESIDENCY][0])}", code("docai.tf"),
     esc(DOCAI[RESIDENCY][0]), "no: per page"],
    ["Artifact Registry", f"repository {code('documind')}: keeps the {REG_KEEP} newest versions, deletes after {REG_DAYS} days", code("registry.tf"), "REGION", "no: storage"],
    ["Pub/Sub", f"{code('documind-ingest')} and its push subscription to the worker; {DLQ_ATTEMPTS} attempts, then {code('documind-ingest-dlq')}",
     code("eventarc.tf"), "global", "no: per message"],
    ["Secret Manager", f"{N_SECRETS} secrets: {len(SECRET_NAMES)} empty holders and the checkpoint DSN", code("secrets.tf") + ", " + code("cloudsql.tf"), "automatic", "no"],
    ["Network", f"{code('documind-vpc')}, a {esc(SUBNET)} subnet, the Serverless VPC Access connector (min {CONN_MIN}, max {CONN_MAX})",
     code("network.tf"), "REGION", "yes: the connector's instances"],
    ["GKE", f"{code('documind-autopilot')}, a regional Standard cluster despite its name, with {GKE_NODES} {code(GKE_MACHINE)} node", code("gke.tf"), "REGION", "yes: the fee and the node"],
    ["The off switch", f"Cloud Run job {code('documind-off')}, scheduled {OFF_AT}:00 IST, and its account", code("off.tf"), "REGION", "no: seconds a night"],
    ["Monitoring", f"{N_METRICS} log metrics, {N_ALERTS} alert policies, one e-mail channel per address in ADMIN_EMAILS",
     code("alerts.tf") + ", " + code("desk_alerts.tf"), "global", "no"],
    ["Budget", f"{code('BUDGET_AMOUNT')} ({esc(make_default('BUDGET_AMOUNT'))}) in the billing account's currency; alerts at "
     + ", ".join(f"{int(t * 100)}%" for t in THRESHOLDS[:-1]) + f" and a {int(THRESHOLDS[-1] * 100)}% forecast", code("budget.tf"), "the billing account", "no"],
]
STORE_TABLE = table(["Store", "What Terraform declares", "File", "Where", "Bills by the hour"], STORE_ROWS)
BUILT_TWICE = [s for s in SCRIPTS if "gcloud builds submit --config=cloudbuild.yaml" in kit(s)]

# the switches
SW_TARGET ={"DESK_JOB": "make desk-job", "RECONCILE_JOB": "make reconcile-job", "BATCH_JOB": "make batch-job"}
KIND_NAMES = {   # a resource type as a sentence names it: (one, many)
    "google_cloud_run_v2_job": ("Cloud Run job", "Cloud Run jobs"), "google_cloud_run_v2_job_iam_member": ("grant to run the job", "grants to run the job"),
    "google_cloud_scheduler_job": ("schedule", "schedules"), "google_monitoring_alert_policy": ("alert policy", "alert policies"),
    "google_service_account": ("service account", "service accounts"), "google_project_iam_member": ("project role grant", "project role grants"),
    "google_firestore_database": ("Firestore database", "Firestore databases"), "google_firestore_field": ("TTL field", "TTL fields"),
    "google_project_service": ("API turned on", "APIs turned on"), "google_pubsub_topic": ("Pub/Sub topic", "Pub/Sub topics"),
    "google_pubsub_topic_iam_member": ("grant to publish to it", "grants to publish"), "google_service_account_iam_member": ("token grant", "token grants"),
    "google_pubsub_subscription": ("push subscription", "push subscriptions"),
}
SWITCH_TABLE_ROWS = []
for sw, tfvar, dflt, added in SWITCH_ROWS:
    kinds = Counter()
    for f, rt, rn, d in added:
        kinds[rt] += d
    SWITCH_TABLE_ROWS.append([code(sw), code(f"var.{tfvar}"), code(dflt), str(sum(d for *_, d in added)),
                              esc(", ".join(f"{word(n)} {KIND_NAMES[k][n > 1]}" for k, n in kinds.items())),
                              code(SW_TARGET[sw]) if sw in SW_TARGET else f"{code('make plan')} then {code('make up')} with {code(sw + '=true')}"])
SWITCH_TABLE = table(["Switch", "Terraform variable", "Default", "Adds", "What", "How it is turned on"], SWITCH_TABLE_ROWS)
N_SWITCHES = len(SWITCHES)

# make up, in order
UP_WHAT = {
    "drift": "plans again after the apply and prints whether anything is still to change; it never fails the run",
    "secrets": "adds a random first version to the empty cookie-secret, which the UI's deploy mounts",
    "build": f"builds the {word(N_SERVICES)} images with Cloud Build, one after another, tagged with the kit's commit",
    "deploy-services": f"runs the DEPLOY block of each of the {word(len(SCRIPTS))} scripts: every service as its own account, its callers bound, IAP on the UI; then make operators",
    "wait-index": "waits until no Firestore composite index is still CREATING",
    "roster": f"writes {N_ROSTER} memberships and three data-region policies (below)",
    "managed-stores": "puts RAG Engine in serverless mode, creates a corpus each for " + " and ".join(MANAGED_TENANTS) + ", and pins acme to RAG Engine and zeta to Vertex AI Search",
    "bq-views": "creates the tenant_daily view over the log sink's table",
    "vector-status": "prints the Vector Search index (0 datapoints on a new lane) and its deployed index",
}
assert list(UP_WHAT) == UP_TARGETS, UP_TARGETS
assert "shared.tenancy backend acme rag_engine" in MAKEFILE and "shared.tenancy backend zeta vertex_search" in MAKEFILE
UP_TABLE = table(["#", "Target", "What it does"], [[str(i), code("make " + t), esc(UP_WHAT[t])] for i, t in enumerate(UP_TARGETS, 1)],
                 ["#", "Target", "What it does"])


# what bills by the hour: the module's items, in its order and under its names
def link(k: str, text: str = "page") -> str:
    """A link to one of the pricing pages the module's prices were read from."""
    return f'<a href="{PRICE_URLS[k]}" target="_blank" rel="noopener">{text}</a>'


COST_CELLS = {   # the module's items: what the kit declares, the unit prices, Rs an hour
    "index": (f"{word(VEC_REPLICAS)} replica{'s' if VEC_REPLICAS > 1 else ''} (min = max = {VEC_REPLICAS}); the machine follows the index's shard size, which {code('terraform/vector.tf')} leaves to the service",
              f"per node hour, Vertex AI pricing ({link('vs')})",
              "<br>".join(f"{s.upper()}: {code(m)} at {usd(sc.PRICES['vs:' + m])}, Rs {rs(inr(sc.INDEX_USD[s]))}" for s, m in sc.SHARDS.items())),
    "spanner": (f"{SPANNER_EDITION.title()}, {SPANNER_PU} processing units = {SPANNER_PU / 1000:g} node, {code(SPANNER_CONFIG)} ({code('terraform/spanner.tf')})",
                f"{usd(sc.PRICES['spanner:' + SPANNER_EDITION])} per node hour, {SPANNER_EDITION.title()}, regional ({link('spanner')})",
                f"Rs {rs(inr(USD_H['spanner']))}"),
    "sql": (", ".join(f"{code(n)} {esc(t)}, {esc(a.lower())}, {d} GB ({code('terraform/' + f)})" for n, f, t, a, d in SQL),
            f"{usd(sc.PRICES['sql:' + sc.SQL_TIER])} per instance hour and {usd(sc.PRICES['sql:ssd_gib'])} per GiB hour of zonal SSD, Cloud SQL pricing ({link('sql')})",
            f"Rs {rs(inr(USD_H['sql']))} for both"),
    "gkefee": (f"one regional Standard cluster ({code('terraform/gke.tf')}); the free-tier credit covers only zonal and Autopilot clusters ({link('gke', 'GKE pricing')})",
               f"{usd(sc.PRICES['gke:cluster'])} per cluster hour (the kit's {code('gke/README.md')} gives the same)",
               f"Rs {rs(inr(USD_H['gkefee']))}"),
    "gkenode": (f"{word(GKE_NODES)} {code(GKE_MACHINE)} in one zone, with a {GKE_DISK} GiB {code(GKE_DISK_TYPE)} boot disk ({code('terraform/gke.tf')})",
                f"{usd(sc.PRICES['ce:' + GKE_MACHINE])} per hour, E2 on demand ({link('ce')}), and {usd(sc.PRICES['pd:standard_gib'])} per GiB hour of standard disk ({link('pd')})",
                f"Rs {rs(inr(USD_H['gkenode']))}"),
    "conn": (f"min {CONN_MIN} instances, max {CONN_MAX}; no machine type, so the default {code('e2-micro')} ({code('terraform/network.tf')}); connector instances bill as Compute Engine VMs ({link('vpc', 'VPC pricing')})",
             f"{usd(sc.PRICES['ce:e2-micro'])} per instance hour ({link('ce')})",
             f"Rs {rs(inr(USD_H['conn']))} for {word(CONN_MIN)}"),
}
assert [k for k, *_ in sc.ITEMS] == list(COST_CELLS), [k for k, *_ in sc.ITEMS]   # an item the module adds needs its row here
COST_ROWS = [[esc(label), *COST_CELLS[k]] for k, label, *_ in sc.ITEMS]
COST_ROWS.append(["<strong>An hour of the lane</strong>", "everything above, idle or busy", f"at Rs {USD_INR} to the dollar (<code>shared/prices.py</code>)",
                  "; ".join(f"<strong>Rs {rs(inr(sc.HOURLY[s]))}</strong> with a {s.upper()} shard" for s in sc.SHARDS)])
COST_TABLE = table(["Item", "What the kit declares", "Unit price", "Rs an hour (list prices for Mumbai)"], COST_ROWS,
                   ["Item", "What the kit declares", "Unit price", "Rs an hour"])

# ====================================================================== the explorer: every account, what it runs, what it may touch
STORES = OrderedDict([("fs", "Firestore (default)")] + [("b-" + bk["name"].split("-", 1)[1], bk["name"]) for bk in BUCKETS.values()] + [
    ("vertex", "Vertex AI: Gemini, embeddings, Vector Search"), ("search", "Vertex AI Search"), ("docai", "Document AI"),
    ("dlp", "Sensitive Data Protection"), ("armor", "Model Armor"), ("sql", f"Cloud SQL ({N_SQL} instances)"),
    ("spanner", "Spanner"), ("bq", "BigQuery"), ("secrets", "Secret Manager"), ("run", "Cloud Run services (change them)"),
    ("deliver", "Cloud Build, Artifact Registry, Cloud Deploy"), ("gke", "GKE cluster")])


def touches(a: str):
    t = set()
    for r in PROJECT_ROLES[a]:
        if " (only where" in r:              # an IAM condition narrows it to something this map does not draw (gchat.tf: its own database)
            continue
        r = r.split(" ")[0]
        if r.startswith("roles/datastore."):
            t.add("fs")
        if r.startswith("roles/storage."):
            t |= {k for k in STORES if k.startswith("b-")}
        for pre, k in (("roles/aiplatform.user", "vertex"), ("roles/discoveryengine.", "search"), ("roles/documentai.", "docai"),
                       ("roles/dlp.", "dlp"), ("roles/modelarmor.", "armor"), ("roles/cloudsql.", "sql"), ("roles/bigquery.", "bq"),
                       ("roles/secretmanager.", "secrets"), ("roles/run.developer", "run"), ("roles/cloudbuild.", "deliver"),
                       ("roles/artifactregistry.", "deliver"), ("roles/clouddeploy.", "deliver"), ("roles/container.clusterAdmin", "gke")):
            if r.startswith(pre):
                t.add(k)
    for bn, _ in BUCKET_GRANTS[a]:
        t.add("b-" + bn.split("-", 1)[1])
    if SECRET_GRANTS[a]:
        t.add("secrets")
    for what, _ in DATA_GRANTS[a]:
        t.add({"Spanner": "spanner", "BigQuery": "bq", "Artifact": "deliver"}[what.split(" ")[0]])
    return [k for k in STORES if k in t]


def ul(items):
    return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>" if items else "<ul><li>none</li></ul>"


def detail(a: str):
    i = SA_INFO[a]
    boxes = []
    if i.get("runs"):
        v = SVC[i["runs"]]
        boxes.append(("Runs", ul([f"{code(i['runs'])}, deployed by {code(v['script'])}", f"ingress {esc(v['ingress'])}" + (", IAP in front" if v["iap"] else ""),
                                  esc(instances_of(v)), "calls " + (", ".join(code(c) for c in v["calls"]) or "no other service by URL")])))
        boxes.append(("Who may call it (run.invoker)", ul([who_list(v["invokers"])])))
    else:
        used = sorted(USED.get(a, ()))
        boxes.append(("Runs", ul([esc(group_of(a))] + ([f"used by {code(u)}" for u in used] or ["no service make up deploys"]))))
    boxes.append((f"Project roles ({len(PROJECT_ROLES[a])})", ul([code(r.split(' ')[0]) + esc(r[len(r.split(' ')[0]):]) for r in PROJECT_ROLES[a]])))
    grants = ([f"bucket {code(b)}: {code(r)}" for b, r in BUCKET_GRANTS[a]] + [f"secret {code(s)}: {code('roles/secretmanager.secretAccessor')}" for s in SECRET_GRANTS[a]]
              + [f"{esc(w)}: {code(r)}" for w, r in DATA_GRANTS[a]])
    boxes.append(("Grants on one resource", ul(grants)))
    boxes.append(("Who may act as it or mint its tokens", ul([f"{code(w) if w.startswith(('documind-', 'sa-')) else esc(w)}: {code(r)}" for w, r in ACTORS[a]])))
    return "".join(f'<div class="rm-box"><b>{t}</b>{body}</div>' for t, body in boxes)


def summary(a: str) -> str:
    i = SA_INFO[a]
    head = f"{a}  |  {i['display']}  |  terraform/{i['file']}"
    if not i["on"]:
        head += "  |  not on a default lane: GCHAT_DOOR=true declares it"
    return head + f"  |  touches {len(touches(a))} of {len(STORES)} stores"


EXPLORER = {a: {"sum": summary(a), "touch": touches(a), "html": detail(a)} for a in ORDERED}
DEFAULT = "documind-ui-sa"
assert DEFAULT in EXPLORER
opts, last = [], None
for a in ORDERED:
    g = group_of(a)
    if g != last:
        if last is not None:
            opts.append("</optgroup>")
        opts.append(f'<optgroup label="{esc(g)}">')
        last = g
    opts.append(f'<option value="{a}"{" selected" if a == DEFAULT else ""}>{a}{" (GCHAT_DOOR only)" if not SA_INFO[a]["on"] else ""}</option>')
opts.append("</optgroup>")
RM_OPTIONS = "\n".join(opts)
RM_CHIPS = "".join(f'<span class="rm-st{" on" if k in EXPLORER[DEFAULT]["touch"] else ""}" data-k="{k}">{esc(v)}</span>' for k, v in STORES.items())

# ====================================================================== verbatim kit excerpts
EXCERPTS = {
    "mk_region": ("the kit's Makefile - where the services run, and where the data rests", block("Makefile", "# REGION is where the SERVICES run", n=8)),
    "mk_apis": ("the kit's Makefile - the apis target", block("Makefile", "# The APIs a fresh project needs, from 12.1's ENABLE_APIS block", n=4)),
    "apis_two_calls": ("commands/lesson-12.1.sh - the ENABLE_APIS block's own note", block("commands/lesson-12.1.sh", "# Two calls, not one:", n=6)),
    "mk_preflight": ("the kit's Makefile - the preflight target", block("Makefile", "# Read-only: is everything `make up` needs in place?", n=4)),
    "infra_trust": ("commands/infrastructure.py - validate_trust(): the three values a new lane's CI trust needs", block("commands/infrastructure.py", "def validate_trust(value):")),
    "infra_prepare": ("commands/infrastructure.py - prepare(): read the project, save the confirmed inputs", block("commands/infrastructure.py", "    def prepare(self):", n=9)),
    "sa_first": ("terraform/sa.tf - the first accounts, one per service", block("terraform/sa.tf", "# Three service accounts, one per service", n=17)),
    "sa_outsider": ("terraform/sa.tf - the outsider: an account IAM admits and no roster lists", block("terraform/sa.tf", "# The eval gate's OUTSIDER", n=11)),
    "sa_graph": ("terraform/sa.tf - the caller graph, one line per service", block("terraform/sa.tf", "#   documind-api    <- documind-ui-sa", n=6)),
    "sa_actas": ("terraform/sa.tf - actAs, named account by account", block("terraform/sa.tf", "  cicd_actas = {", end="  admin_roles = [") + "\n...\n"
                 + block("terraform/sa.tf", "# actAs, scoped to named accounts - NOT project-wide.", n=7)),
    "sa_ui_roles": ("terraform/sa.tf - the UI's project roles, and the reasons for the ones it lacks", block("terraform/sa.tf", "  ui_roles = [", end="  api_roles = [")),
    "desk_eval": ("terraform/desk.tf - the five Desk eval accounts", block("terraform/desk.tf", "  desk_eval_accounts = {", end="# The Google Chat door's account, declared only")),
    "storage_audit": ("terraform/storage.tf - the audit bucket: five years, locked only on purpose", block("terraform/storage.tf", 'resource "google_storage_bucket" "audit" {', n=14)),
    "fs_vector": ("terraform/firestore_indexes.tf - a vector index on chunks", block("terraform/firestore_indexes.tf", 'resource "google_firestore_index" "chunks_vector" {', n=22)),
    "fs_ttl": ("terraform/firestore_indexes.tf - two of the TTL fields", block("terraform/firestore_indexes.tf", "# TTL for superseded/staged chunk rows.", n=18)),
    "vector_deploy": ("terraform/vector.tf - the deployed index, and the machine its shard size picks", block("terraform/vector.tf", "locals {", end="# These two outputs are the whole contract")),
    "cloudsql_cost": ("terraform/cloudsql.tf - what the checkpointer's instance costs, by the kit's own account", block("terraform/cloudsql.tf", "# WHAT THIS COSTS.", n=4)),
    "spanner_cost": ("terraform/spanner.tf - the Spanner instance: provisioned, and billed by the hour", block("terraform/spanner.tf", "# WHAT THIS COSTS.", end="resource \"google_spanner_database\" \"graph\" {")),
    "gke_pool": ("terraform/gke.tf - the one node", block("terraform/gke.tf", 'resource "google_container_node_pool" "lab" {', n=19)),
    "network_conn": ("terraform/network.tf - the connector", block("terraform/network.tf", 'resource "google_vpc_access_connector" "conn" {', n=8)),
    "gke_readme": ("gke/README.md - the kit's own price table for the cluster fee", block("gke/README.md", "| Autopilot cluster fee (after the free-tier credit) | $0.10 |", n=1)),
    "readme_bills": ("README.md - the one shape, and what bills while it exists", block("README.md", "TENANT= RETRIEVAL_BACKEND=` moves one tenant by hand. It bills while it exists - the Vector Search", n=3)),
    "infra_switches": ("commands/infrastructure.py - the switches a plan must keep", block("commands/infrastructure.py", "# The Makefile's switches that declare resources only while true", n=2)),
    "mk_extra_vars": ("the kit's Makefile - the Terraform variables make plan passes", block("Makefile", "TF_EXTRA_VARS = -var audit_lock=$(AUDIT_LOCK) \\", n=14) + "\n...\n"
                      + block("Makefile", "INFRA = $(PY) commands/infrastructure.py", n=3)),
    "agents_vars": ("mk/agents.mk - the four switches it appends to that list", "\n".join(
        block("mk/agents.mk", line, n=1) for line in ("TF_EXTRA_VARS += -var desk_job=$(DESK_JOB)", "TF_EXTRA_VARS += -var desk_router_alerts=",
                                                       "TF_EXTRA_VARS += -var desk_gate_alerts=", "TF_EXTRA_VARS += -var gchat_door="))),
    "mk_plan": ("the kit's Makefile - the plan target", block("Makefile", "# Use the committed deploy files as-is.", n=6)),
    "infra_plan": ("commands/infrastructure.py - plan(): a unique saved plan, checked, then selected", block("commands/infrastructure.py", "    def plan(self):", end="    def check(self):")),
    "infra_inspect": ("commands/infrastructure.py - inspect_plan(): what the check refuses", block("commands/infrastructure.py", "def inspect_plan(plan, expected):")),
    "mk_up": ("the kit's Makefile - the up target", block("Makefile", "# First run make plan and review its output.", n=7)),
    "infra_apply": ("commands/infrastructure.py - apply(): check twice, then apply exactly that file", block("commands/infrastructure.py", "    def apply(self):", n=6)),
    "mk_services": (f"the kit's Makefile - the {word(N_SERVICES)} services and the scripts that deploy them", block("Makefile", "# The services make up builds and deploys, in the order they must come up", end=".PHONY: dryrun")),
    "mk_build": ("the kit's Makefile - the build target", block("Makefile", "# Cloud Build every image make up deploys.", end="# A checkout that was never connected")),
    "cloudbuild": ("cloudbuild.yaml - one config, a Dockerfile named per service", block("cloudbuild.yaml", "steps:", end="substitutions:")),
    "deploy_loop": ("the kit's Makefile - deploy-services: the DEPLOY block of each script, run as it is", block("Makefile", "deploy-services: guard-project tf-backend", n=2)
                    + "\n...\n" + block("Makefile", "	for f in $(SCRIPTS); do \\", n=2) + "\n...\n" + block("Makefile", "	  sh -ec \"$$(sed -n", n=2)
                    + "\n...\n" + block("Makefile", "	$(MAKE) operators", n=1)),
    "ui_deploy": ("commands/lesson-12.4.sh - the UI: IAP on the service itself", block("commands/lesson-12.4.sh", "gcloud run deploy documind-ui \\", n=4)
                  + "\n...\n" + block("commands/lesson-12.4.sh", "  --service-account=documind-ui-sa@$PROJECT.iam.gserviceaccount.com \\", n=1)),
    "ui_iap": ("commands/lesson-12.4.sh - who invokes it, and who may sign in", block("commands/lesson-12.4.sh", "# IAP's service agent is what invokes the service once IAP is on")),
    "mk_operators": ("the kit's Makefile - make operators, the last step of deploy-services", block("Makefile", "# The people who operate this deployment mint identity tokens", n=12)),
    "mk_roster": ("mk/ingestion.mk - the roster target", block("mk/ingestion.mk", "# The roster is the tenancy boundary the surfaces enforce", n=5)),
    "roster_plan": ("commands/lane.py - roster_plan(): the memberships and policies make roster writes", block("commands/lane.py", "    sa = lambda name:", n=7)),
    "chat_gate": ("services/frontend/chat.py - what the UI shows a signed-in person", block("services/frontend/chat.py", "def chat_page(user):", n=9)),
    "mk_bq_views": ("the kit's Makefile - the bq-views target", block("Makefile", "# The SQL that terraform does not own.", n=7)),
}
assert EXCERPTS["infra_inspect"][1].rstrip().endswith('"remove state to bypass this check.")'), EXCERPTS["infra_inspect"][1][-80:]
assert EXCERPTS["infra_plan"][1].rstrip().endswith("""print("Review the displayed changes, then run this command with 'apply' instead of 'plan'.")""")
assert EXCERPTS["mk_up"][1].rstrip().endswith("bq-views vector-status")
assert EXCERPTS["ui_iap"][1].rstrip().endswith("done")
assert EXCERPTS["chat_gate"][1].rstrip().endswith('st.caption(f"Tenant: **{tenant_id}**")'), EXCERPTS["chat_gate"][1][-60:]
assert EXCERPTS["sa_graph"][1].count("<-") == 6
assert "$0.10" in EXCERPTS["gke_readme"][1] and "Cloud SQL" in EXCERPTS["readme_bills"][1]
fill = filler(EXCERPTS, window)

# ====================================================================== what only the author's live run can print (RUN_LIST.md)
REC = {name: pb.recorded(LESSON, name + ".txt") for name in (
    "make_plan_summary", "plan_by_type", "make_up_tail", "run_services", "vector_shard",
    "ui_unauthenticated", "iap_policy", "ui_signed_in", "make_roster")}
m = re.search(r"Plan: (\d+) to add, (\d+) to change, (\d+) to destroy", REC["make_plan_summary"])
if m and int(m.group(1)) != N_RESOURCES:
    print(f"NOTE: the recorded plan adds {m.group(1)}; the files declare {N_RESOURCES} for one ADMIN_EMAILS address - reconcile before publishing")

# ====================================================================== the tokens the parts carry
T = {
    "N_SA": str(N_SA), "N_SA_WORD": word(N_SA), "N_SA_ALL": str(N_SA_ALL), "N_SERVICES": str(N_SERVICES), "N_SERVICES_WORD": word(N_SERVICES),
    "N_BUCKETS": str(len(BUCKETS)), "N_BUCKETS_WORD": word(len(BUCKETS)), "N_FS_INDEXES": str(N_FS_INDEXES), "N_FS_VECTOR": str(N_FS_VECTOR),
    "N_TTL": str(N_TTL), "N_TTL_WORD": word(N_TTL), "N_RESOURCES": str(N_RESOURCES), "N_APIS": str(len(APIS)), "N_APIS_CHECKED": str(len(CHECKED)),
    "N_SWITCHES": str(N_SWITCHES), "N_SWITCHES_WORD": word(N_SWITCHES), "N_ACTAS": str(N_ACTAS), "N_ACTAS_WORD": word(N_ACTAS),
    "N_ROSTER": str(N_ROSTER), "N_SQL_WORD": word(N_SQL), "N_SECRETS": str(N_SECRETS), "N_METRICS": str(N_METRICS), "N_ALERTS": str(N_ALERTS),
    "N_SCRIPTS_WORD": word(len(SCRIPTS)), "N_UP": str(len(UP_TARGETS)), "N_UP_WORD": word(len(UP_TARGETS)),
    "N_STORES": str(len(STORES)), "N_FILES": str(sum(1 for n in BY_FILE.values() if n)), "N_TYPES": str(sum(1 for n in BY_TYPE.values() if n)),
    "N_RES_SA_TF": str(BY_FILE["sa.tf"]), "N_SA_DOOR": str(N_SA_ALL), "N_PROJECT_IAM": str(count_of("google_project_iam_member")),
    "GCHAT_ADDS": str(sum(d for *_, d in next(r for r in SWITCH_ROWS if r[0] == "GCHAT_DOOR")[3])),
    "SPANNER_PU": str(SPANNER_PU), "SPANNER_CONFIG": SPANNER_CONFIG, "VEC_DIMS": str(VEC_DIMS), "VEC_REPLICAS": str(VEC_REPLICAS),
    "GKE_MACHINE": GKE_MACHINE, "CONN_MIN": str(CONN_MIN), "CONN_MAX": str(CONN_MAX),
    "MACHINE_SMALL": sc.SHARDS[SMALL], "MACHINE_MEDIUM": sc.SHARDS[MEDIUM],
    "USD_INR": str(USD_INR), "SQL_MONTH": f"{SQL_MONTH:.2f}", "SQL_LO": str(SQL_USD_MONTH[0]), "SQL_HI": str(SQL_USD_MONTH[1]),
    "N_SHARDS_WORD": word(len(sc.SHARDS)),
    "BQ_DATASETS": " and ".join(f"<code>{d}</code>" for d in BQ_DATASETS), "N_BQ_TABLES": str(len(BQ_TABLES)),
    "DATA_STORES": " and ".join(f"<code>{d}</code>" for d in DATA_STORES), "MANAGED_TENANTS": " and ".join(MANAGED_TENANTS),
    "SERVICE_NAMES": ", ".join(f"<code>{s}</code>" for s in SVC),
    "STORE_TABLE": STORE_TABLE, "BUILT_TWICE": " and ".join(code(s) for s in BUILT_TWICE), "OFF_AT": OFF_AT,
    "MIN_FLOORED": (lambda xs: ", ".join(xs[:-1]) + " and " + xs[-1] if len(xs) > 1 else "".join(xs))(
        [code(s) for s, v in SVC.items() if v["min"] == "${MIN_INSTANCES:-0}"]),
    "N_SERVICES_CAP": word(N_SERVICES).capitalize(), "N_BUCKETS_CAP": word(len(BUCKETS)).capitalize(), "CONN_MIN_WORD": word(CONN_MIN),
    "N_WIDE_WORD": word(len(WIDE)).capitalize(), "N_JOBS_WORD": word(GROUP_N["runs a job or a node"]),
    "N_FIXTURES_WORD": word(GROUP_N["a fixture: an identity the tests call as"]),
    "N_ONREQ_WORD": word(GROUP_N["runs a service deployed on request"]), "N_UNUSED_WORD": word(GROUP_N["declared, and used by no target yet"]),
    "SERVICE_TABLE": SERVICE_TABLE, "SA_TABLE": SA_TABLE, "BUCKET_TABLE": BUCKET_TABLE, "FS_TABLE": FS_TABLE, "FILE_TABLE": FILE_TABLE,
    "SWITCH_TABLE": SWITCH_TABLE, "UP_TABLE": UP_TABLE, "COST_TABLE": COST_TABLE,
    "RM_OPTIONS": RM_OPTIONS, "RM_CHIPS": RM_CHIPS, "RM_SUM": esc(EXPLORER[DEFAULT]["sum"]), "RM_DETAIL": EXPLORER[DEFAULT]["html"],
    "OUT_TYPES": output("text - the instances terraform/*.tf declares for a blank lane, by type (computed from the files at build time)", TYPE_TEXT),
    "OUT_PREPARE": output("expected - the two lines prepare prints (your repository, its id and your home directory)", PREPARE_EXPECTED),
    "OUT_PREFLIGHT": output("expected - make preflight on a project ready for make plan", PREFLIGHT_EXPECTED),
    "OUT_ROSTER_DRY": output("expected - the dry run, computed from commands/lane.py at build time", ROSTER_DRY),
    "REC_PLAN": output("output - make plan on a blank project, the summary lines (the author's run)", REC["make_plan_summary"]),
    "REC_PLAN_TYPES": output("output - the saved plan, counted by type (the author's run)", REC["plan_by_type"]),
    "REC_UP": output("output - the last lines of make up from a blank project, and how long it took (the author's run)", REC["make_up_tail"]),
    "REC_SERVICES": output("output - the services, and the account each runs as (the author's run)", REC["run_services"]),
    "REC_SHARD": output("output - the shard size the service chose, and the machine it deployed (the author's run)", REC["vector_shard"]),
    "REC_UI_CURL": output("output - the UI without a sign-in (the author's run)", REC["ui_unauthenticated"]),
    "REC_IAP": output("output - who may pass IAP on documind-ui (the author's run)", REC["iap_policy"]),
    "REC_UI_VIEW": output("output - what each kind of visitor saw in the browser (the author's notes)", REC["ui_signed_in"]),
    "REC_ROSTER": output("output - make roster on the new lane (the author's run)", REC["make_roster"]),
}


def tokens(text: str) -> str:
    def rep(m):
        return T[m.group(1)]
    return re.sub(r"%%(\w+)%%", rep, text)


JS = """<script>
(function(){
  'use strict';
  var D = %s;
  var sel = document.getElementById('rm-sel');
  if (!sel) return;
  var sum = document.getElementById('rm-sum'), out = document.getElementById('rm-out'), chips = document.querySelectorAll('.rm-st');
  function render(){
    var a = D[sel.value]; if (!a) return;
    sum.textContent = a.sum;
    Array.prototype.forEach.call(chips, function(c){
      if (a.touch.indexOf(c.getAttribute('data-k')) >= 0) c.classList.add('on'); else c.classList.remove('on');
    });
    out.innerHTML = a.html;
  }
  sel.addEventListener('change', render);
  render();
})();
</script>
""" % json.dumps(EXPLORER, sort_keys=False).replace("<", "\\u003c")   # no markup inside the script: the div count stays the page's own

body = "".join(fill(tokens(pb.part(LESSON, p))) for p in ("a", "b", "c"))
finish(LESSON, title, EXTRA_CSS, body, JS)
