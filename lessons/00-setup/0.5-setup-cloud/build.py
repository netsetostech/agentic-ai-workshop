"""Build lesson 0.5 from its three parts, the author's three setup guides under their own names,, the shared template and verbatim kit excerpts.

Set up the cloud lane end to end from Cloud Shell, in three phases that each end in a checkpoint. Phase 1 (1-infra-setup):
the project, the tools, Python 3.12 in ~/rag-shell-venv and the kit cloned from main into ~/deploy_module_rag, with
the settings saved to ~/rag-env.sh. Phase 2 (2-terraform-apply): the APIs, the state bucket, one saved Terraform plan, its apply
and the vector index check. Phase 3 (3-build-and-deploy): pin GIT_SHA, the kit's regression gate, seven images under that tag,
the seven Cloud Run services with the UI, the admin console and chat behind IAP, the tenant rosters, the four targets make up
finishes with (the index wait, the managed stores, the usage views, the vector count), and the checks. Brought to the kit of
14 October 2026: the kit's state bucket and prefix, its inputs file, the short GIT_SHA its Makefile tags with, the chat and
peer deploys as commands/lesson-12.8.sh and lesson-8.4.sh make them.

At build time: the Makefile's service list and up recipe, the roster target and commands/lane.py's roster_plan are quoted verbatim
(pagebuild.block), and the standing cost comes from lessons/00-setup/standing_cost.py, the one source 0.1, 0.3 and 0.4
state it from, so the pages agree.

    python pagekit/build.py 0.5
"""
import html
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit.pagebuild import block, filler, finish, part, window  # noqa: E402,F401

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import standing_cost as sc  # noqa: E402

LESSON = "0.5"
title = ("<title>Lesson 0.5 Set up the cloud lane end to end: clone in Cloud Shell, create the infrastructure with "
         "Terraform, deploy every service and the UI - three phases, one pinned commit, the rosters | Netsetos</title>\n")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the three phases: one rail, three stations; it stacks on a phone */
.rail{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0;margin:22px 0 26px;border:1px solid var(--border);border-radius:14px;overflow:hidden;background:var(--card);}
.rail-st{padding:16px 16px 14px;border-right:1px solid var(--border);min-width:0;position:relative;}
.rail-st:last-child{border-right:0;}
.rail-st .rn{font-family:var(--display);font-size:30px;line-height:1;color:var(--teal);}
.rail-st h4{margin:8px 0 4px;font-size:16px;color:var(--navy);}
.rail-st p{margin:0 0 8px;font-size:var(--small-size);line-height:1.5;color:var(--slate);}
.rail-st .rw{font-family:var(--mono);font-size:12px;color:var(--teal-dark);background:var(--teal-light);border-radius:6px;padding:4px 7px;display:inline-block;overflow-wrap:anywhere;}
.rail-st:nth-child(2){background:#f8fafc;}
.rail-st:nth-child(3){background:var(--teal-light);}
@media (max-width:640px){
  .rail{grid-template-columns:1fr;}
  .rail-st{border-right:0;border-bottom:1px solid var(--border);}
  .rail-st:last-child{border-bottom:0;}
}
/* why a block differs from the earlier runbook: one quiet line under the step, not a warning */
.fixnote{margin:10px 0 18px;padding:8px 12px;border-left:3px solid var(--teal);background:#f8fafc;border-radius:0 8px 8px 0;font-size:var(--small-size);line-height:1.55;color:var(--slate);}
.fixnote-t{font-family:var(--mono);font-size:var(--kicker-size);font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--teal-dark);margin-right:4px;}
"""

PARTS = [part(LESSON, name) for name in ("1-infra-setup", "2-terraform-apply", "3-build-and-deploy")]

# ---------------------------------------------------------------- verbatim kit excerpts
EXCERPTS = {
    "services": ("deploy/Makefile - the seven services", block("Makefile", "SERVICES   =", n=4)),
    "roster_target": ("deploy/mk/ingestion.mk - the roster target", block("mk/ingestion.mk", "roster: guard-project", n=2)),
    "roster_plan": ("deploy/commands/lane.py - roster_plan, what the roster writes", block("commands/lane.py", "def roster_plan")),
    "up_target": ("deploy/Makefile - what make up runs after the apply", block("Makefile", "up: guard-project", n=3)),
}
UP_TARGETS = EXCERPTS["up_target"][1].split("\n")[2].split()     # whole target names: "bq-views" is not "bq-views-when-ready"
for target in ("wait-index", "roster", "managed-stores", "bq-views-when-ready", "vector-status"):
    assert target in UP_TARGETS, EXCERPTS["up_target"][1]
CLOSING = re.search(r"^make (wait-index [^\\\n]*?)\s*\\$", PARTS[2], re.M).group(1).split()
assert CLOSING == ["wait-index", "managed-stores", "bq-views-when-ready", "vector-status"] and set(CLOSING) <= set(UP_TARGETS), CLOSING
TRUST = re.search(r"<!--BASH bash - Inputs.*?<!--/BASH-->", PARTS[1], re.S).group(0)    # T4: the learner's fork, never the author's repository
assert 'TF_VAR_github_repository="$GH_REPO"' in TRUST and 'TF_VAR_github_repository_id="$GH_REPO_ID"' in TRUST, TRUST
assert '"netsetos/agents_workshop_learner" ]]' in TRUST and not re.search(r"TF_VAR_github_repository(_id)?='", TRUST), TRUST
SERVICES = EXCERPTS["services"][1].split("=", 1)[1].split("\n")[0].split()
assert SERVICES == ["ingest", "api", "admin", "ui", "chat", "mcp", "agent"], SERVICES
PLAN = EXCERPTS["roster_plan"][1]
assert 'GOLDEN_TENANTS' in PLAN and 'policies = [("acme", "any"), ("zeta", "any"), ("globex", "in")]' in PLAN, PLAN
assert 'GOLDEN_TENANTS = ("acme", "zeta", "globex")' in (Path(__file__).resolve().parents[3] / "deploy/commands/lane.py").read_text()


# ---------------------------------------------------------------- the standing cost, shared with 0.1, 0.3 and 0.4
def rs(x: float) -> str:
    return f"{x:,.2f}"


NUMBERS = {
    "N_SERVICES": str(len(SERVICES)),
    "HOUR_SMALL": rs(sc.HOURLY["small"] * sc.USD_INR), "HOUR_MEDIUM": rs(sc.HOURLY["medium"] * sc.USD_INR),
    "DAY_SMALL": f"{sc.PER_DAY['small']:,}", "DAY_MEDIUM": f"{sc.PER_DAY['medium']:,}",
}


# ---------------------------------------------------------------- bash windows: copy button, comments dimmed
def bash(label: str, code: str) -> str:
    out = []
    for line in html.escape(code.strip("\n"), quote=False).split("\n"):
        out.append(re.sub(r"(^|\s)(#[^\n'\"]*)$", r'\1<span class="cm">\2</span>', line))
    return ('<div class="cw"><div class="ch-bar"><span>' + html.escape(label) + '</span>'
            '<button class="cp" type="button">copy</button></div><pre tabindex="0">' + "\n".join(out) + "</pre></div>\n")


def expected(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.strip("\n"), quote=False) + "</pre></div>\n")


def render(text: str) -> str:
    text = re.sub(r"<!--BASH (.*?)-->\n(.*?)\n<!--/BASH-->", lambda m: bash(m.group(1).strip(), m.group(2)), text, flags=re.S)
    text = re.sub(r"<!--EXPECT (.*?)-->\n(.*?)\n<!--/EXPECT-->", lambda m: expected(m.group(1).strip(), m.group(2)), text, flags=re.S)
    text = filler(EXCERPTS)(text)
    for k, v in NUMBERS.items():
        text = text.replace(f"%%{k}%%", v)
    return text


finish(LESSON, title, EXTRA_CSS, "".join(render(p) for p in PARTS))
