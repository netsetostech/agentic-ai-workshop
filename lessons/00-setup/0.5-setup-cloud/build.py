"""Build lesson 0.5 from its part, the shared template and verbatim kit excerpts.

Set up the cloud lane end to end, in one sitting, from Cloud Shell: copy the kit into ~/deploy_module_rag, create the
infrastructure with Terraform through the kit's checked plan (make plan, then make up), and deploy every service and
the UI behind IAP; then prove it with make smoke and switch it off. Lessons 0.1 to 0.4 teach each part slowly; this page
is the one runbook that strings them together, for a learner (or an instructor) who has to stand a lane up today.

At build time: the Makefile's up target and service list are quoted verbatim (pagebuild.block), and the standing cost
comes from lessons/00-setup/standing_cost.py, the one source 0.1, 0.3 and 0.4 state it from, so the four pages agree.

    python pagekit/build.py 0.5
"""
import html
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit.pagebuild import block, filler, finish, part, window  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import standing_cost as sc  # noqa: E402

LESSON = "0.5"
title = ("<title>Lesson 0.5 Set up the cloud lane end to end: clone in Cloud Shell, create the infrastructure with "
         "Terraform, deploy every service and the UI - one runbook, start to switch-off | Netsetos</title>\n")

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
"""

PART = part(LESSON, "a")

# ---------------------------------------------------------------- verbatim kit excerpts
EXCERPTS = {
    "up": ("deploy/Makefile - the up target", block("Makefile", "up: guard-project", n=3)),
    "services": ("deploy/Makefile - what make up builds and deploys", block("Makefile", "SERVICES   =", n=4)),
    "operators": ("deploy/Makefile - the operators target", block("Makefile", "operators: guard-project", n=8)),
    "bqviews": ("deploy/Makefile - bq-views, and why it can stop make up", block("Makefile", "# The SQL that terraform does not own.", n=7)),
}
UP = EXCERPTS["up"][1]
assert "drift secrets build deploy-services wait-index roster managed-stores bq-views vector-status" in UP, UP
SERVICES = EXCERPTS["services"][1].split("=", 1)[1].split("\n")[0].split()
assert SERVICES == ["ingest", "api", "admin", "ui", "chat", "mcp", "agent"], SERVICES
UP_STEPS = UP.splitlines()[-1].split("$(MAKE)")[1].split()

# ---------------------------------------------------------------- the standing cost, shared with 0.1, 0.3 and 0.4
def rs(x: float) -> str:
    return f"{x:,.2f}"


rows = []
for key, label, where, size, _ in sc.ITEMS:
    small, medium = sc.item_usd(key, "small") * sc.USD_INR, sc.item_usd(key, "medium") * sc.USD_INR
    cost = rs(small) if abs(small - medium) < 1e-9 else f"{rs(small)} (SMALL) / {rs(medium)} (MEDIUM)"
    rows.append(f'<tr><td>{html.escape(label)}</td><td data-label="Declared in"><code>{html.escape(where)}</code></td>'
                f'<td data-label="Size">{html.escape(size)}</td><td data-label="Rs an hour">{cost}</td></tr>')
COST_ROWS = "\n".join(rows)
H_SMALL, H_MED = rs(sc.HOURLY["small"] * sc.USD_INR), rs(sc.HOURLY["medium"] * sc.USD_INR)
NUMBERS = {
    "N_SERVICES": str(len(SERVICES)),
    "SERVICE_LIST": ", ".join(f"<code>documind-{s}</code>" for s in SERVICES),
    "UP_STEPS": ", ".join(f"<code>{s}</code>" for s in UP_STEPS),
    "N_UP_STEPS": str(len(UP_STEPS)),
    "HOUR_SMALL": H_SMALL, "HOUR_MEDIUM": H_MED,
    "DAY_SMALL": f"{sc.PER_DAY['small']:,}", "DAY_MEDIUM": f"{sc.PER_DAY['medium']:,}",
    "USD_INR": str(sc.USD_INR),
    "COST_ROWS": COST_ROWS,
}


# ---------------------------------------------------------------- bash windows: copy button, comments dimmed
def bash(label: str, code: str) -> str:
    out = []
    for line in html.escape(code.strip("\n"), quote=False).split("\n"):
        out.append(re.sub(r"(^|\s)(#[^\n]*)$", r'\1<span class="cm">\2</span>', line))
    return ('<div class="cw"><div class="ch-bar"><span>' + html.escape(label) + '</span>'
            '<button class="cp" type="button">copy</button></div><pre tabindex="0">' + "\n".join(out) + "</pre></div>\n")


def expected(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.strip("\n"), quote=False) + "</pre></div>\n")


BLOCKS = {}
for m in re.finditer(r"<!--BASH (.*?)-->\n(.*?)\n<!--/BASH-->", PART, re.S):
    BLOCKS[m.group(0)] = bash(m.group(1).strip(), m.group(2))
for m in re.finditer(r"<!--EXPECT (.*?)-->\n(.*?)\n<!--/EXPECT-->", PART, re.S):
    BLOCKS[m.group(0)] = expected(m.group(1).strip(), m.group(2))

body = PART
for raw, rendered in BLOCKS.items():
    body = body.replace(raw, rendered)
body = filler(EXCERPTS)(body)
for k, v in NUMBERS.items():
    body = body.replace(f"%%{k}%%", v)

finish(LESSON, title, EXTRA_CSS, body)
