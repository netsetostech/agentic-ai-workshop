#!/usr/bin/env python3
"""Offline checks for the authorization fixes of 12 September 2026 (P2 of the production plan, R03).

    python tools/check_authz.py

No credential and no network: the library calls are replaced by fakes at the seam, and each check
names the code change that would turn it red:

  terraform/sa.tf           no project-level roles/run.invoker for ui, chat, mcp, outsider or agent
                            (the five lists, and every google_project_iam_member); the caller graph in
                            its comment block names the six services, their callers and the script
                            that binds each.
  commands/lesson-*.sh      each service's deploy script (and commands/gchat.sh) binds roles/run.invoker
                            to exactly the callers the graph names - parsed, loops expanded - and no
                            other script binds it. The graph agrees with the code (who reads which URL)
                            and with the Makefile (who the smokes and the eval gate mint as). The
                            outsider is bound only where a verifier and a roster answer, never on the
                            peer, which has neither; and on the Google Chat bridge, whose code verifies
                            the token and refuses every caller but Chat's add-on agent and the push.
  frontend/documents.py     documents_page resolves the tenant ONCE and stops on None: a person on no
                            roster never reaches the uploader, and nothing is filed under "None/".
  frontend/auth.py          tenant_for is not memoised - three calls, three roster queries - so a
                            revoked person loses the tenant within one request.
  mcp/server.py             list_documents filters on the tenant_id FIELD: acme never lists acme_eu_*,
                            and a row without the field (claimed before 12 September 2026) is not listed.
  smoke/smoke_agent.py      the live smoke asks the peer as the outsider, with a token, expects 403,
                            and skips with a line when it cannot mint one.
  the DocuMind Desk         (workshop lesson 5.6) the five eval accounts and the Google Chat bridge's
                            account are callers of documind-chat and of nothing else, on both sides;
                            none holds a project role. Nobody may mint as the bridge's account
                            (minting_as): no line of the Makefile, mk/*.mk, commands/*.sh, commands/*.py
                            or terraform/*.tf mints as it, or grants a minting role on it to anyone but
                            itself, or grants a minting role project-wide; sa.tf's cicd_actas does not
                            name it, and make desk-operators does not either. Its only project roles
                            are logWriter and datastore.user conditioned on its own claims database.
                            (workshop lesson 10.4) Only Pub/Sub's agent may mint as the push account,
                            documind-gchatpush-sa; only the bridge may publish to its work topic; no
                            Pub/Sub publisher, editor or admin role is granted at project scope.

Exit 0 when nothing failed.
"""
from __future__ import annotations

import ast
import datetime
import os
import re
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASSED, SKIPPED = [], []
FIVE = ("documind-ui-sa", "documind-chat-sa", "documind-mcp-sa", "documind-outsider-sa", "documind-agent-sa")
SCRIPTS = ("lesson-12.2.sh", "lesson-12.4.sh", "lesson-12.8.sh", "lesson-7.2.sh", "lesson-8.4.sh", "gchat.sh")
IAP_AGENT = "gcp-sa-iap"
GSUITE_AGENT = "gcp-sa-gsuiteaddons"      # the Workspace add-on agent that calls the Google Chat bridge for the app
SERVICES = ("documind-api", "documind-chat", "documind-mcp", "documind-agent", "documind-ui", "documind-gchat")


def ok(msg):
    PASSED.append(msg)
    print(f"  ok   {msg}")


def skip(msg):
    SKIPPED.append(msg)
    print(f"  skip {msg}")


def read(*parts) -> str:
    return open(os.path.join(ROOT, *parts), encoding="utf-8").read()


def kit_makefile(*parts: str) -> str:
    """The kit's Makefile and mk/*.mk as one text (22 September 2026): the targets of a lane live in mk/<lane>.mk."""
    import glob as _glob
    base = read(*parts) if len(parts) > 1 else read(parts[0])
    root = os.path.join(ROOT, "deploy", "mk")
    return base + "".join("\n" + open(p, encoding="utf-8").read() for p in sorted(_glob.glob(os.path.join(root, "*.mk"))))


def lift(src: str, name: str) -> str:
    """The source of one top-level function, decorators left behind."""
    fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(src, fn)


def callers_in(text: str) -> set[str]:
    """The caller tokens in a piece of text: documind-*-sa accounts, plus IAP's and the add-on service agents."""
    found = set(re.findall(r"documind-[a-z]+-sa\b", text))
    for agent in (IAP_AGENT, GSUITE_AGENT):
        if agent in text:
            found.add(agent)
    return found


def graph_from(sa_tf: str) -> dict[str, tuple[set[str], str]]:
    """sa.tf's caller graph: `#   documind-api  <- a, b, c  (lesson-12.2.sh)` -> service: (callers, script)."""
    out = {}
    for m in re.finditer(r"^#\s+(documind-[a-z]+)\s+<-\s+(.+?)\s+\(((?:lesson-[\d.]+|gchat)\.sh)\)\s*$", sa_tf, re.M):
        out[m.group(1)] = (callers_in(m.group(2)), m.group(3))
    return out


DESK_EVAL = ("documind-evalacme-sa", "documind-evalzeta-sa", "documind-evalglobex-sa", "documind-evalleaver-sa",
             "documind-evalgrc-sa")
GCHAT = "documind-gchat-sa"
GCHAT_PUSH = "documind-gchatpush-sa"          # Pub/Sub's push identity for the bridge: not a delegate
GCHAT_TOPIC = "documind-gchat-work"
PUBSUB_AGENT = "gcp-sa-pubsub"
PUBSUB_WIDE = ("roles/pubsub.publisher", "roles/pubsub.editor", "roles/pubsub.admin")
# The Google Chat bridge's only project roles (terraform/gchat.tf), each with the IAM condition it must carry: None for
# none, else the one expression allowed - its own claims database, never the default one, where rosters and roles live.
BRIDGE_PROJECT_ROLES = {"roles/logging.logWriter": None,
                        "roles/datastore.user": 'resource.name == \\"projects/${var.project_id}/databases/documind-gchat\\"'}
# The roles that let their holder mint a token as an account, act as it, or give either to someone else.
MINT_ROLES = ("roles/iam.serviceAccountTokenCreator", "roles/iam.serviceAccountOpenIdTokenCreator",
              "roles/iam.serviceAccountUser", "roles/iam.workloadIdentityUser", "roles/iam.serviceAccountAdmin",
              "roles/iam.serviceAccountKeyAdmin")
MINT_WORDS = ("impersonate", "print-identity-token", "print-access-token", "generateidtoken", "generateaccesstoken",
              "signjwt", "signblob", "impersonated_credentials", "target_principal", "keys create", "_sa=")


def _make_defs(texts: dict[str, str]) -> dict[str, str]:
    """NAME -> value of every `NAME = ...`, `?=`, `:=` and `+=` in the Makefile and mk/*.mk (continuations joined)."""
    defs: dict[str, str] = {}
    for path, text in texts.items():
        if not (path.endswith("Makefile") or path.endswith(".mk")):
            continue
        for m in re.finditer(r"^([A-Z][A-Z0-9_]*)\s*([:?+]?)=[ \t]*(.*)$", text.replace("\\\n", " "), re.M):
            defs[m.group(1)] = (defs.get(m.group(1), "") + " " if m.group(2) == "+" else "") + m.group(3).strip()
    return defs


def _mints(stmt: str, account: str) -> str | None:
    """Why one shell, make or Python statement lets someone mint as `account`, or None."""
    low = stmt.lower()
    if "projects add-iam-policy-binding" in low and any(r.lower() in low for r in MINT_ROLES):
        return "grants a minting role project-wide, which covers every account"
    if account not in stmt:
        return None
    target = re.search(r"service-accounts\s+(?:add-iam-policy-binding|set-iam-policy)\s+(\S+)", stmt)
    if target and account in target.group(1):
        member = re.search(r"--member[= ]\"?([^\"\s]+)", stmt)
        if not (member and account in member.group(1)):
            return "grants a role on it to someone else"
    elif "projects add-iam-policy-binding" in low:
        return "grants it a project role"
    elif any(w in low for w in MINT_WORDS):
        return "mints as it"
    return None


def _tf_blocks(text: str):
    """(type, name, body) of every top-level terraform resource block, a counted resource's [0] read as the resource
    (the Google Chat door's are counted on var.gchat_door)."""
    for m in re.finditer(r'^resource "(\w+)" "(\w+)" \{\n(.*?)^\}', text, re.M | re.S):
        yield m.group(1), m.group(2), re.sub(r"\b(google_\w+\.\w+)\[0\]", r"\1", m.group(3))


def _tf_local(texts: dict[str, str], name: str) -> str:
    """The text of `name = {...}` or `name = [...]` in any locals block, on one line or across several."""
    for path, text in texts.items():
        if path.endswith(".tf"):
            m = (re.search(r"^[ \t]+" + re.escape(name) + r"[ \t]*=[ \t]*(\[[^\n]*\]|\{[^\n]*\})[ \t]*$", text, re.M)
                 or re.search(r"^\s+" + re.escape(name) + r"\s*=\s*([\[{].*?^\s+[\]}])", text, re.M | re.S))
            if m:
                return m.group(1)
    return ""


def bridge_project_role(kind: str, body: str) -> bool:
    """Whether a terraform block is one of the Google Chat bridge's two project grants, condition and all."""
    role = re.search(r'role\s*=\s*"([^"]+)"', body)
    if kind != "google_project_iam_member" or not role or role.group(1) not in BRIDGE_PROJECT_ROLES:
        return False
    want = BRIDGE_PROJECT_ROLES[role.group(1)]
    cond = re.search(r"^\s*condition\s*\{(.*?)^\s*\}", body, re.M | re.S)
    if want is None:
        return cond is None
    expr = re.search(r'^\s*expression\s*=\s*"(.*)"\s*$', cond.group(1), re.M) if cond else None
    return bool(expr) and expr.group(1) == want


def minting_as(texts: dict[str, str], account: str) -> list[str]:
    """Every line of the kit that would let someone mint a token as `account` or act as it: a mint or an impersonation
    naming it (a make variable expanded one level, a for loop's list expanded into its body), a minting role granted on
    it to anyone but itself, a minting role granted project-wide, a project role held by it (for the Google Chat
    bridge's account, any but BRIDGE_PROJECT_ROLES), or its name in sa.tf's cicd_actas. texts: path -> text of the
    Makefile, mk/*.mk, commands/*.sh, commands/*.py and terraform/*.tf. Returns "path: why" lines; empty when nobody
    can."""
    defs, found = _make_defs(texts), []

    def expand(text):
        return re.sub(r"\$\(([A-Z][A-Z0-9_]*)\)", lambda m: defs.get(m.group(1), m.group(0)), text)

    for path, text in sorted(texts.items()):
        joined = text.replace("\\\n", " ")
        if path.endswith("Makefile") or path.endswith(".mk"):
            joined = expand(joined)
        code = "\n".join("" if ln.lstrip().startswith("#") else ln for ln in joined.splitlines())
        for ln in code.splitlines():
            why = _mints(ln, account)
            if why:
                found.append(f"{path}: {why}: {ln.strip()[:120]}")
        for m in re.finditer(r"\bfor\s+(\w+)\s+in\s+([^;\n]+);\s*do\b", code):
            if not any(account in w for w in m.group(2).split()):
                continue
            end = re.search(r"\bdone\b", code[m.end():])
            body = code[m.end(): m.end() + (end.start() if end else len(code))]
            body = re.sub(r"\$\$?\{?" + m.group(1) + r"\b\}?", account, body)
            for ln in body.splitlines():
                why = _mints(ln, account)
                if why:
                    found.append(f"{path}: {why} (for {m.group(1)} in ...): {ln.strip()[:120]}")
    tf = {p: t for p, t in texts.items() if p.endswith(".tf")}
    refs = {f"google_service_account.{name}." for t in tf.values() for kind, name, body in _tf_blocks(t)
            if kind == "google_service_account" and re.search(r'account_id\s*=\s*"' + re.escape(account) + '"', body)}
    names = tuple(refs) + (account,)
    for path, text in sorted(tf.items()):
        for kind, name, body in _tf_blocks(text):
            each = re.search(r"for_each\s*=\s*(?:toset\()?local\.(\w+)", body)
            scope = body + ("\n" + _tf_local(tf, each.group(1)) if each else "")
            role = re.search(r'role\s*=\s*"([^"]+)"', body)
            member = re.search(r"members?\s*=\s*(.+)", body)
            if kind.startswith("google_service_account_iam_") and any(n in scope.split("member")[0] or
                                                                         (each and n in scope) for n in names):
                if kind.endswith("_policy"):
                    found.append(f"{path}: {kind}.{name} sets the whole IAM policy of {account}")
                elif not (member and any(n in member.group(1) for n in names)) and (role is None or role.group(1) in MINT_ROLES):
                    found.append(f"{path}: {kind}.{name} grants {role.group(1) if role else 'a role'} on {account}")
            if kind.startswith("google_project_iam_"):
                roles_here = [role.group(1)] if role else re.findall(r'"(roles/[^"]+)"', scope)
                if any(r in MINT_ROLES for r in roles_here):
                    found.append(f"{path}: {kind}.{name} grants a minting role project-wide, which covers {account}")
                if member and any(n in member.group(1) for n in names) and not (account == GCHAT and
                                                                               bridge_project_role(kind, body)):
                    found.append(f"{path}: {kind}.{name} gives {account} a project role")
    actas = _tf_local(tf, "cicd_actas")
    if any(n in actas for n in names):
        found.append(f"terraform/sa.tf: cicd_actas names {account}: the deploy identity could act as it")
    return found


def gchat_door_problems(tf_all: dict[str, str], texts: dict[str, str]) -> list[str]:
    """What breaks the Google Chat door's push and queue rules (workshop lesson 10.4), or []. tf_all: path -> text of
    terraform/*.tf; texts: that plus the Makefile, mk/*.mk, commands/*.sh and commands/*.py. A topic or project grant
    is read wherever it names the work topic, by reference or by its name."""
    found = []
    blocks = [(path, kind, name, body) for path, t in sorted(tf_all.items()) for kind, name, body in _tf_blocks(t)]
    push = minting_as(texts, GCHAT_PUSH)
    grants = [(kind, name, body) for _, kind, name, body in blocks
              if kind.startswith("google_service_account_iam_") and ("google_service_account.gchatpush." in body or GCHAT_PUSH in body)]
    if len(grants) != 1:
        found.append(f"one grant on {GCHAT_PUSH} expected (Pub/Sub's agent mints the push token), found {[n for _, n, _ in grants]}")
    else:
        kind, name, body = grants[0]
        if not (kind == "google_service_account_iam_member" and '"roles/iam.serviceAccountTokenCreator"' in body
                and re.search(r"member\s*=\s*\S*" + PUBSUB_AGENT, body)):
            found.append(f"{kind}.{name}: only Pub/Sub's agent may mint as {GCHAT_PUSH}")
        allowed = f"{kind}.{name} grants roles/iam.serviceAccountTokenCreator on {GCHAT_PUSH}"
        found += [f"someone but Pub/Sub's agent could mint as the push account: {v}" for v in push if allowed not in v]
    publishers = [(kind, name, body) for _, kind, name, body in blocks
                  if kind.startswith("google_pubsub_topic_iam_") and ("google_pubsub_topic.gchat_work" in body or GCHAT_TOPIC in body)]
    if not (len(publishers) == 1 and publishers[0][0] == "google_pubsub_topic_iam_member"
            and '"roles/pubsub.publisher"' in publishers[0][2] and "google_service_account.gchat.email" in publishers[0][2]):
        found.append(f"{GCHAT_TOPIC}: one binding, roles/pubsub.publisher for {GCHAT}, expected; found {[n for _, n, _ in publishers]}")
    for path, kind, name, body in blocks:
        if kind.startswith("google_project_iam_"):
            each = re.search(r"for_each\s*=\s*(?:toset\()?local\.(\w+)", body)
            scope = body + ("\n" + _tf_local(tf_all, each.group(1)) if each else "")
            if any(r in scope for r in PUBSUB_WIDE):
                found.append(f"{path}: {kind}.{name} grants a Pub/Sub publishing role project-wide")
    for path, text in sorted(texts.items()):
        for ln in text.replace("\\\n", " ").splitlines():
            low = ln.lower()
            if "add-iam-policy-binding" in low and (GCHAT_TOPIC in ln or ("projects add-iam-policy-binding" in low
                                                                         and any(r in ln for r in PUBSUB_WIDE))):
                found.append(f"{path}: a Pub/Sub grant on {GCHAT_TOPIC} or project-wide: {ln.strip()[:120]}")
    sub = next((b for _, k, n, b in blocks if k == "google_pubsub_subscription" and n == "gchat_push"), "")
    if "google_service_account.gchatpush.email" not in sub or "dead_letter_policy" in sub:
        found.append("the push subscription mints as the push account, and dead-letters nothing")
    return found


def bindings_in(script: str) -> dict[str, set[str]]:
    """service -> callers bound roles/run.invoker by `gcloud run services add-iam-policy-binding` in a script,
    a `for VAR in a b c; do` loop expanded to its list."""
    text = script.replace("\\\n", " ")
    out: dict[str, set[str]] = {}
    for m in re.finditer(r"gcloud run services add-iam-policy-binding\s+(\S+)([^\n]*)", text):
        service, rest = m.group(1), m.group(2)
        if "roles/run.invoker" not in rest:
            continue
        mem = re.search(r'--member[= ]"?serviceAccount:([^"\s]+)', rest)
        assert mem, f"{service}: an invoker binding without a service-account --member"
        var = re.match(r"\$(\w+)@", mem.group(1))
        if var:
            loops = [lm for lm in re.finditer(r"for\s+(\w+)\s+in\s+([^;\n]+);\s*do", text[:m.start()]) if lm.group(1) == var.group(1)]
            assert loops, f"{service}: --member uses ${var.group(1)} outside a for loop"
            callers = set(loops[-1].group(2).split())
        else:
            callers = callers_in(mem.group(1))
        out.setdefault(service, set()).update(callers)
    return out


def main() -> int:
    # ------------------------------------------------------------------ sa.tf: no project-level invoker
    sa_tf = read("deploy", "terraform", "sa.tf")
    code_only = re.sub(r"#[^\n]*", "", sa_tf)                         # the comments may still SAY run.invoker
    lists = {m.group(1): re.findall(r'"(roles/[^"]+)"', m.group(2))
             for m in re.finditer(r"(\w+_roles)\s*=\s*\[(.*?)\]", code_only, re.S)}
    for who in ("ui", "chat", "mcp", "outsider", "agent"):
        assert f"{who}_roles" in lists, f"sa.tf: no {who}_roles list"
        assert "roles/run.invoker" not in lists[f"{who}_roles"], f"sa.tf: {who}_roles still grants roles/run.invoker at project scope"
    for m in re.finditer(r'resource "google_project_iam_member" "(\w+)" \{(.*?)\n\}', code_only, re.S):
        assert 'role     = "roles/run.invoker"' not in m.group(2) and '"roles/run.invoker"' not in m.group(2), \
            f"sa.tf: google_project_iam_member.{m.group(1)} grants roles/run.invoker project-wide"
    assert "roles/run.invoker" not in code_only, "sa.tf: roles/run.invoker appears outside a comment"
    assert lists["outsider_roles"] == [], f"sa.tf: the outsider carries a project role: {lists['outsider_roles']}"
    for who, keep in (("ui", "roles/datastore.user"), ("chat", "roles/aiplatform.user"), ("mcp", "roles/datastore.viewer"), ("agent", "roles/aiplatform.user")):
        assert keep in lists[f"{who}_roles"], f"sa.tf: {who}_roles lost {keep} - only the invoker was to go"
    ok("sa.tf: no project-level roles/run.invoker for ui, chat, mcp, outsider or agent - the five lists and every google_project_iam_member; the other roles stayed; the outsider carries nothing at project scope")

    # ------------------------------------------------------------------ sa.tf: the caller graph, and the scripts agree
    graph = graph_from(sa_tf)
    assert set(graph) == set(SERVICES), f"sa.tf: the caller graph names {sorted(graph)} - six services expected"
    scripts = {s: read("deploy", "commands", s) for s in SCRIPTS}
    bound: dict[str, tuple[set[str], str]] = {}
    for name, text in scripts.items():
        for service, callers in bindings_in(text).items():
            assert service not in bound, f"{service} is bound in two scripts: {bound[service][1]} and {name}"
            bound[service] = (callers, name)
    assert set(bound) == set(graph), f"the scripts bind {sorted(bound)}, the graph names {sorted(graph)}"
    for service, (callers, script) in graph.items():
        got, in_script = bound[service]
        assert in_script == script, f"{service}: the graph says {script}, the binding is in {in_script}"
        assert got == callers, f"{service}: sa.tf's graph names {sorted(callers)}, {script} binds {sorted(got)}"
    for caller in FIVE:
        assert any(caller in c for c, _ in graph.values()), f"{caller} reaches no service at all - the project grant was removed and nothing replaced it"
    ok("the six deploy scripts bind roles/run.invoker per service to exactly the callers sa.tf's graph names (loops expanded), one script per service: "
       + "; ".join(f"{s} <- {', '.join(sorted(c))}" for s, (c, _) in sorted(graph.items())))

    # the graph against the code: who reads which URL
    fe = "".join(read("deploy", "services", "frontend", f) for f in ("chat.py", "documents.py", "studio.py"))
    assert 'os.environ["RAG_API_URL"]' in fe and 'os.environ.get("CHAT_URL"' in fe and "/v1/chat" in fe
    tools_src = read("deploy", "shared", "documind_tools.py")
    assert 'os.environ.get("RAG_API_URL"' in tools_src and "/v1/query" in tools_src
    chat_dir = os.path.join(ROOT, "deploy", "services", "chat")
    chat_src = "".join(read(chat_dir, f) for f in sorted(os.listdir(chat_dir)) if f.endswith(".py"))
    assert "documind_tools" in chat_src and "MCP_URL" not in chat_src and "AGENT_URL" not in chat_src, "the chat service grew a second URL - the graph must follow"
    mcp_src = read("deploy", "services", "mcp", "server.py")
    assert "documind_tools.retrieve(" in mcp_src and "MCP_URL" not in mcp_src
    agent_src = read("deploy", "services", "agent", "agent.py")
    assert 'os.environ.get("MCP_URL"' in agent_src and "RAG_API_URL" not in agent_src, "the peer learned a second URL - the graph must follow"
    for caller, callee in (("documind-ui-sa", "documind-api"), ("documind-ui-sa", "documind-chat"), ("documind-chat-sa", "documind-api"),
                           ("documind-mcp-sa", "documind-api"), ("documind-agent-sa", "documind-mcp")):
        assert caller in graph[callee][0], f"the code has {caller} calling {callee}; the graph and the script do not bind it"
    assert "documind-agent-sa" not in graph["documind-api"][0], "the peer never knows the API's URL"
    assert "documind-chat-sa" not in graph["documind-mcp"][0], "the chat service has no MCP_URL"
    assert "documind-mcp-sa" not in graph["documind-chat"][0] | graph["documind-agent"][0] | graph["documind-mcp"][0]
    assert graph["documind-ui"][0] == {IAP_AGENT}, "a person reaches the UI through IAP alone"
    gchat_dir = os.path.join(ROOT, "deploy", "services", "gchat")
    gchat_src = "".join(read(gchat_dir, f) for f in sorted(os.listdir(gchat_dir)) if f.endswith(".py"))
    assert 'os.environ.get("CHAT_URL"' in gchat_src and all(u not in gchat_src for u in ("RAG_API_URL", "MCP_URL", "AGENT_URL")), \
        "the Google Chat bridge reads CHAT_URL and no other service's URL - the graph must follow"
    assert "documind_tools" not in gchat_src and "tenancy" not in gchat_src, "the bridge retrieves nothing and reads no roster"
    assert graph["documind-gchat"][0] == {GSUITE_AGENT, GCHAT_PUSH, "documind-outsider-sa"}, \
        "documind-gchat is called by Chat's add-on agent, Pub/Sub's push account and the outsider, and by nobody else"
    assert GCHAT_PUSH not in set().union(*(c for s, (c, _) in graph.items() if s != "documind-gchat")), \
        "the push account reaches the bridge and nothing else"
    mk = kit_makefile("deploy", "Makefile")
    for target, needle in (("smoke-mcp", "DOCUMIND_IMPERSONATE_SA=documind-ui-sa"), ("smoke-mcp", "DOCUMIND_OUTSIDER_SA=documind-outsider-sa"),
                           ("smoke-chat", "DOCUMIND_OUTSIDER_SA=documind-outsider-sa"), ("smoke-agent", "DOCUMIND_IMPERSONATE_SA=documind-ui-sa"),
                           ("eval-live", "impersonate-service-account=documind-outsider-sa"),
                           ("smoke-gchat", "DOCUMIND_OUTSIDER_SA=documind-outsider-sa")):
        block = mk.split(f"\n{target}:", 1)[1].split("\n\n", 1)[0]
        assert needle in block, f"Makefile {target}: {needle} - the graph's reason for a ui-sa/outsider binding"
    ok("the graph is the code's: the UI reads RAG_API_URL and CHAT_URL, chat and mcp reach the API through the ONE retrieve(), the peer reads MCP_URL and nothing else, the Google Chat bridge reads CHAT_URL and nothing else; ui-sa on mcp and the peer, and the outsider on api, chat, mcp and the bridge, are what the Makefile mints as")

    # the outsider: only where a verifier and a roster answer, never on the peer
    knocks = {s for s, (c, _) in graph.items() if "documind-outsider-sa" in c}
    assert knocks == {"documind-api", "documind-chat", "documind-mcp", "documind-gchat"}, f"the outsider is bound on {sorted(knocks)}"
    assert "documind-outsider-sa" not in bound["documind-agent"][0], "the outsider can invoke documind-agent - the peer answers as acme"
    verifiers = {"documind-api": (("rag-api", "auth.py"), ("rag-api", "main.py")), "documind-chat": (("chat", "agent.py"),), "documind-mcp": (("mcp", "server.py"),)}
    gchat_main = read("deploy", "services", "gchat", "main.py")
    assert "iap.bearer_email(request.headers" not in gchat_main and "iap.bearer_email(headers, SELF_URL)" in gchat_main \
        and "if email != want:" in gchat_main and "iap.identity(" not in gchat_src, \
        "documind-gchat: the outsider may knock only where the code verifies the token and compares it with a fixed caller"
    for s in knocks - {"documind-gchat"}:
        src = "".join(read("deploy", "services", *p) for p in verifiers[s])
        assert "iap.identity(" in src and ("tenancy." in src or "enforce_membership(" in src), f"{s}: the outsider may knock only where a verifier and a roster answer"
    assert "iap.identity(" not in agent_src and "tenancy" not in agent_src, "the peer verifies nobody - which is why the outsider must not reach it"
    ok("the outsider is bound on the API, the chat service and the MCP server - each verifies the token (shared/iap.identity) and refuses by the roster - and on the Google Chat bridge, which verifies it (shared/iap.bearer_email) and refuses every caller but its two; never on the peer, which has no roster to refuse it with")

    # ------------------------------------------------------------------ the DocuMind Desk's six callers (workshop lesson 5.6)
    desk_tf = read("deploy", "terraform", "desk.tf")
    for acct in DESK_EVAL + (GCHAT,):
        on = {s for s, (c, _) in graph.items() if acct in c}
        assert on == {"documind-chat"}, f"{acct} is a caller of {sorted(on)} - the chat service only"
        assert acct in bound["documind-chat"][0], f"lesson-12.8.sh does not bind {acct} on documind-chat"
    assert re.search(r'account_id\s*=\s*"documind-\$\{each\.key\}-sa"', desk_tf) and \
        all(f"{a[len('documind-'):-len('-sa')]} " in desk_tf for a in DESK_EVAL), "terraform/desk.tf no longer declares the five eval accounts"
    assert f'account_id   = "{GCHAT}"' in desk_tf, "terraform/desk.tf no longer declares the Google Chat bridge's account"
    tf_all = {f"terraform/{f}": read("deploy", "terraform", f) for f in sorted(os.listdir(os.path.join(ROOT, "deploy", "terraform"))) if f.endswith(".tf")}
    bridge_roles = []
    for kind, name, body in (b for t in tf_all.values() for b in _tf_blocks(t)):
        if kind.startswith("google_project_iam_"):
            assert "google_service_account.desk_eval" not in body and "google_service_account.gchatpush." not in body \
                and GCHAT_PUSH not in body, f"{kind}.{name} gives a Desk account a project role"
            if "google_service_account.gchat." in body or GCHAT in body:
                assert bridge_project_role(kind, body), \
                    f"{kind}.{name} gives the Google Chat bridge a project role other than {sorted(BRIDGE_PROJECT_ROLES)} as conditioned"
                bridge_roles.append(re.search(r'role\s*=\s*"([^"]+)"', body).group(1))
    assert sorted(bridge_roles) == sorted(set(bridge_roles)), f"the bridge's project roles are granted twice: {bridge_roles}"
    ok("the Desk's five eval accounts and the Google Chat bridge's account are callers of documind-chat and nothing else, in sa.tf's graph and lesson-12.8.sh's loop; terraform/desk.tf declares them; no eval account and not the push account holds a project role, and the bridge holds only "
       + ", ".join(sorted(bridge_roles)) + " (datastore.user conditioned on its own claims database)")

    kit = os.path.join(ROOT, "deploy")
    texts = {"Makefile": read("deploy", "Makefile"), **tf_all}
    for sub, pattern in (("mk", ".mk"), ("commands", ".sh"), ("commands", ".py")):
        for f in sorted(os.listdir(os.path.join(kit, sub))):
            if f.endswith(pattern):
                texts[f"{sub}/{f}"] = read("deploy", sub, f)
    violations = minting_as(texts, GCHAT)
    assert violations == [], "someone could mint as the Google Chat bridge's account:\n  " + "\n  ".join(violations)
    desk_ops_block = mk.split("\ndesk-operators:", 1)[1].split("\n\n", 1)[0]
    assert "DESK_EVAL_SAS" in desk_ops_block and GCHAT not in _make_defs({"mk/agents.mk": mk})["DESK_EVAL_SAS"], \
        "make desk-operators would let the operators mint as the bridge"
    ok(f"nobody may mint as {GCHAT}: no mint, impersonation or minting grant on it in the Makefile, mk/*.mk, commands/*.sh, commands/*.py or terraform/*.tf ({len(texts)} files, loops and make variables expanded), no minting role project-wide, not in cicd_actas, not in make desk-operators")

    # ------------------------------------------------------------------ the Google Chat door's push and queue (workshop lesson 10.4)
    problems = gchat_door_problems(tf_all, texts)
    assert not problems, "the Google Chat door:\n  " + "\n  ".join(problems)
    door = [(kind, name, body) for kind, name, body in _tf_blocks(tf_all["terraform/gchat.tf"])] + \
        [b for b in _tf_blocks(desk_tf) if b[:2] == ("google_service_account", "gchat")]
    assert re.search(r'variable "gchat_door" \{\n  type += bool\n  default += false\n', tf_all["terraform/gchat.tf"]) and len(door) > 1 \
        and all(re.match(r"  count += var\.gchat_door \? 1 : 0\n", body) for _, _, body in door), \
        "the Google Chat door is opt-in: every resource of gchat.tf, and documind-gchat-sa, counts on var.gchat_door (default false)"
    ok(f"the Google Chat door: only Pub/Sub's agent may mint as {GCHAT_PUSH} (the push token; no project role), only {GCHAT} publishes to {GCHAT_TOPIC}, no Pub/Sub publisher, editor or admin role is granted project-wide, and the push subscription mints as the push account with no dead-letter topic; all {len(door)} of its resources count on var.gchat_door, false by default")

    # ------------------------------------------------------------------ frontend/documents.py: the tenant once, a stop on None
    docs_src = read("deploy", "services", "frontend", "documents.py")

    class _Stop(Exception):
        pass

    class _Status:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def update(self, **kw): pass

    class _St:
        def __init__(self, files): self.files, self.errors, self.writes = files, [], []
        def title(self, *a, **k): pass
        def error(self, msg, *a, **k): self.errors.append(msg)
        def stop(self): raise _Stop()
        def file_uploader(self, *a, **k): return self.files
        def button(self, *a, **k): return a[0] == "Index documents"
        def info(self, *a, **k): pass
        def rerun(self): raise AssertionError("refresh was not selected")
        def status(self, *a, **k): return _Status()
        def write(self, msg, *a, **k): self.writes.append(msg)

    class _Blob:
        def __init__(self, name): self.name, self.chunk_size = name, None
        generation = 1
        def upload_from_file(self, f, content_type=None, timeout=None, rewind=False):
            assert rewind is True
            self.sent = content_type

    class _Bucket:
        name = "proj-uploads"
        def __init__(self): self.blobs = []
        def blob(self, name):
            b = _Blob(name); self.blobs.append(b); return b

    def run_page(tenant, files):
        st, bucket, asked, versions, parsed = _St(files), _Bucket(), [], [], []
        ns = {"st": st, "BUCKET": bucket, "tenant_for": lambda e: asked.append(e) or tenant,
              "versions_section": lambda t: versions.append(t), "parse_layout": lambda uri: parsed.append(uri) or object(),
              "extract_chunks": lambda doc, uri: [{"id": f"{uri}#0", "text": "x"}], "embed_batch": lambda chunks: chunks}
        constants = [n for n in ast.parse(docs_src).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MIME_TYPES" for t in n.targets)]
        exec(compile(ast.Module(body=constants, type_ignores=[]), "<UI constants>", "exec"), ns)
        exec(lift(docs_src, "upload_document"), ns)
        exec(lift(docs_src, "documents_page"), ns)
        stopped = False
        try:
            ns["documents_page"]({"email": "priya@acme.in", "sub": "1"})
        except _Stop:
            stopped = True
        return stopped, st, bucket, asked, versions, parsed

    files = [types.SimpleNamespace(name="hr_policy_2026.pdf", type="application/pdf"),
             types.SimpleNamespace(name="fig3.png", type="image/png")]
    stopped, st, bucket, asked, versions, parsed = run_page(None, files)
    assert stopped, "documents_page rendered for a person on no roster"
    assert st.errors and "not a member" in st.errors[0], st.errors
    assert not versions and not bucket.blobs and not parsed, "something ran before the roster answered"
    stopped, st, bucket, asked, versions, parsed = run_page("acme", files)
    assert not stopped and not st.errors
    assert asked == ["priya@acme.in"], f"tenant_for called {len(asked)} times - once, at the top"
    assert versions == ["acme"] and [b.name for b in bucket.blobs] == ["acme/hr_policy_2026.pdf", "acme/fig3.png"], (versions, [b.name for b in bucket.blobs])
    assert parsed == [], "the worker, not the browser, must parse every upload"
    assert [b.sent for b in bucket.blobs] == ["application/pdf", "image/png"]
    assert "None/" not in "".join(b.name for b in bucket.blobs)
    ok("frontend/documents.py: documents_page resolves the tenant once, stops with a message when there is none (nothing rendered, nothing stored), and files every upload under {tenant}/{name}")

    # ------------------------------------------------------------------ frontend/auth.py: tenant_for is not memoised
    auth_src = read("deploy", "services", "frontend", "auth.py")
    tf_node = next(n for n in ast.parse(auth_src).body if isinstance(n, ast.FunctionDef) and n.name == "tenant_for")
    decos = [ast.unparse(d) for d in tf_node.decorator_list]
    assert not any("cache_data" in d for d in decos), f"frontend tenant_for is memoised: {decos} - a revoked person keeps the tenant until it expires"

    class _FakeSt:                                   # cache_data memoises for real, so a re-added decorator is caught by behaviour too
        def cache_data(self, **kw):
            def deco(f):
                memo = {}
                def wrapped(*a):
                    if a not in memo:
                        memo[a] = f(*a)
                    return memo[a]
                return wrapped
            return deco

        def cache_resource(self, **kw):
            return lambda f: f

    queries = []

    class _Doc:
        reference = types.SimpleNamespace(parent=types.SimpleNamespace(parent=types.SimpleNamespace(id="acme")))

    class _Query:
        def __init__(self, email): self.email = email
        def limit(self, n): return self
        def get(self):
            queries.append(self.email)
            return [_Doc()] if self.email == "priya@acme.in" else []

    class _Group:
        def where(self, field, op, value):
            assert (field, op) == ("email", "=="), (field, op)
            return _Query(value)

    class _Db:
        def collection_group(self, name):
            assert name == "members", name
            return _Group()

    fake_fs = types.ModuleType("google.cloud.firestore")
    fake_fs.Client = lambda *a, **k: _Db()
    saved = {k: sys.modules.get(k) for k in ("google", "google.cloud", "google.cloud.firestore")}
    try:
        g = sys.modules.get("google") or types.ModuleType("google")
        gc = sys.modules.get("google.cloud") or types.ModuleType("google.cloud")
        g.__path__ = getattr(g, "__path__", []); gc.__path__ = getattr(gc, "__path__", [])
        prior_attr = getattr(gc, "firestore", None)
        g.cloud, gc.firestore = gc, fake_fs
        sys.modules["google"], sys.modules["google.cloud"], sys.modules["google.cloud.firestore"] = g, gc, fake_fs
        ns = {"st": _FakeSt()}
        exec(lift(auth_src, "tenant_for"), ns)
        if "_roster_db" in auth_src:
            exec(lift(auth_src, "_roster_db"), ns)
        assert ns["tenant_for"]("Priya@acme.in") == "acme", "the email is lower-cased before the roster lookup"
        assert ns["tenant_for"]("nobody@zeta.in") is None
        assert ns["tenant_for"]("Priya@acme.in") == "acme"
        assert queries == ["priya@acme.in", "nobody@zeta.in", "priya@acme.in"], f"three calls, {len(queries)} roster queries - the answer is memoised"
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
        if saved["google.cloud"] is not None:
            if prior_attr is None:
                delattr(saved["google.cloud"], "firestore") if hasattr(saved["google.cloud"], "firestore") else None
            else:
                saved["google.cloud"].firestore = prior_attr
    ok("frontend/auth.py: tenant_for carries no st.cache_data; three calls are three roster queries (a revoked person loses the tenant on the next rerun); the email is lower-cased")

    # ------------------------------------------------------------------ mcp/server.py: list_documents by the tenant_id field
    class FieldFilter:                               # the attribute names of google.cloud.firestore_v1.base_query.FieldFilter
        def __init__(self, field_path, op_string, value): self.field_path, self.op_string, self.value = field_path, op_string, value

    T = datetime.datetime(2026, 9, 12, 9, 0, 0)
    rows = [("acme_" + "a" * 8, {"tenant_id": "acme", "status": "indexed", "gcs_uri": "gs://b/acme/hr_policy_2026.md", "chunks": 12, "indexed_at": T}),
            ("acme_eu_" + "b" * 8, {"tenant_id": "acme_eu", "status": "indexed", "gcs_uri": "gs://b/acme_eu/gdpr_notice.md", "chunks": 4, "indexed_at": T}),
            ("acme_" + "c" * 8, {"status": "indexed", "gcs_uri": "gs://b/acme/claimed_before_the_field.md", "chunks": 1, "indexed_at": T}),
            ("zeta_" + "d" * 8, {"tenant_id": "zeta", "status": "failed", "gcs_uri": "gs://b/zeta/x.md", "error": "boom", "failed_at": T})]
    predicates = []

    class _Snap:
        def __init__(self, id_, d): self.id, self._d = id_, d
        def to_dict(self): return dict(self._d)

    class _Coll:
        def __init__(self, pred=None): self.pred = pred
        def where(self, *args, **kwargs):
            f = kwargs.get("filter")
            pred = (f.field_path, f.op_string, f.value) if f is not None else tuple(args)
            predicates.append(pred)
            return _Coll(pred)
        def stream(self):
            for id_, d in rows:
                if self.pred is None or (self.pred[1] == "==" and d.get(self.pred[0]) == self.pred[2]):
                    yield _Snap(id_, d)

    class _FsDb:
        def collection(self, name):
            assert name == "documents", name
            return _Coll()

    class ToolError(Exception):
        pass

    audited = []
    bq = types.ModuleType("google.cloud.firestore_v1.base_query"); bq.FieldFilter = FieldFilter
    saved = {k: sys.modules.get(k) for k in ("google", "google.cloud", "google.cloud.firestore_v1", "google.cloud.firestore_v1.base_query")}
    try:
        g = sys.modules.get("google") or types.ModuleType("google")
        gc = sys.modules.get("google.cloud") or types.ModuleType("google.cloud")
        fv1 = sys.modules.get("google.cloud.firestore_v1") or types.ModuleType("google.cloud.firestore_v1")
        for mod in (g, gc, fv1):
            mod.__path__ = getattr(mod, "__path__", [])
        g.cloud, gc.firestore_v1, fv1.base_query = gc, fv1, bq
        sys.modules.update({"google": g, "google.cloud": gc, "google.cloud.firestore_v1": fv1, "google.cloud.firestore_v1.base_query": bq})
        ns = {"ToolError": ToolError, "_caller": lambda: {"email": "ui-sa@p.iam.gserviceaccount.com", "via": "iam"},
              "_tenant_for": lambda caller, tenant: tenant or "acme", "documind_tools": types.SimpleNamespace(PROFILE="gcp"),
              "_db": lambda: _FsDb(), "_audit": lambda caller, tenant, tool, extra: audited.append((tenant, tool, extra)),
              "_local_documents": lambda t: (_ for _ in ()).throw(AssertionError("the local lane was taken"))}
        exec(lift(mcp_src, "list_documents"), ns)
        out = ns["list_documents"]()
        assert predicates and predicates[-1] == ("tenant_id", "==", "acme"), f"list_documents did not query by the tenant_id field: {predicates}"
        assert [d["file"] for d in out["documents"]] == ["hr_policy_2026.md"], [d["file"] for d in out["documents"]]
        assert out["documents"][0]["chunks"] == 12 and out["documents"][0]["at"] == "2026-09-12T09:00:00" and out["tenant"] == "acme"
        out = ns["list_documents"](status="all", tenant="zeta")
        assert predicates[-1] == ("tenant_id", "==", "zeta") and [d["file"] for d in out["documents"]] == ["x.md"] and out["documents"][0]["error"] == "boom"
        try:
            ns["list_documents"](status="nope")
            raise AssertionError("an unknown status was accepted")
        except ToolError:
            pass
        assert audited and audited[0] == ("acme", "list_documents", {"status": "indexed", "documents": 1}), audited[0]
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    ok("mcp/server.py: list_documents queries documents by the tenant_id field - acme lists hr_policy_2026.md, not acme_eu's row and not a row claimed before the field existed; the status filter and the audit row unchanged")

    # ------------------------------------------------------------------ smoke/smoke_agent.py: the outsider, with a token, 403
    sm = read("deploy", "smoke", "smoke_agent.py")
    assert 'os.environ.get("DOCUMIND_OUTSIDER_SA"' in sm
    block = sm.split("# 5. the outsider WITH a token", 1)
    assert len(block) == 2, "smoke_agent.py has no fifth check: the outsider with a token"
    tail = block[1]
    assert "send(outsider, QUESTION)" in tail and '(ok if status == 403 else bad)("outsider refused at the door"' in tail, "the outsider check does not expect 403 on a task"
    assert '[SKIP] outsider refused at the door' in tail and "DOCUMIND_OUTSIDER_SA" in tail, "no clear skip line when the token cannot be minted"
    assert tail.index("[SKIP]") < tail.index("send(outsider, QUESTION)"), "the skip must come before the call, not after a failure"
    ns = {}
    exec(lift(sm, "outsider_account"), ns)
    acct = ns["outsider_account"]
    assert acct("documind-ui-sa@proj.iam.gserviceaccount.com") == "documind-outsider-sa@proj.iam.gserviceaccount.com"
    assert acct("documind-ui-sa@proj.iam.gserviceaccount.com", "x@y.iam.gserviceaccount.com") == "x@y.iam.gserviceaccount.com"
    assert acct("") == ""
    assert "five checks" in sm.splitlines()[1]
    ok("smoke/smoke_agent.py: a fifth check sends a task as the outsider with a token and expects 403 at the door; the account is DOCUMIND_OUTSIDER_SA or the member's project's documind-outsider-sa; a clear [SKIP] line when no token can be minted")

    print(f"\n{len(PASSED)} passed, {len(SKIPPED)} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
