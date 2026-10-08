#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_responsive.py - static audit of the mobile/desktop responsive layer of a
self-contained HTML page (a Netsetos lesson, or any page embedded as an
auto-height iframe).

What makes this different from verify_v6.py: it is srcdoc-aware. Every animation
embedded as srcdoc='...' is unescaped and audited as its own document, because the
per-document rules (viewport meta, color-scheme, the reduced-motion block, the hover
gate, touch floors) are supposed to be repeated inside every one of them and nothing
was checking that.

Usage:
    python audit_responsive.py <file.html> [more.html ...]
    python audit_responsive.py --json <file.html>
    python audit_responsive.py --only R05,R21 <file.html>
    python audit_responsive.py --no-srcdoc <file.html>

Exit code: 0 if no FAIL, 1 if any FAIL, 2 on usage error.
Severity: FAIL blocks shipping. WARN needs a written justification. INFO is context.
"""

import sys
import re
import json
import html as _html
import os

FAIL, WARN, INFO, PASS = "FAIL", "WARN", "INFO", "PASS"


# --------------------------------------------------------------------------
# document model
# --------------------------------------------------------------------------

class Doc(object):
    """One HTML document: the page itself, or one unescaped srcdoc."""

    def __init__(self, name, text, kind, line_offset=0):
        self.name = name          # "page" or "srcdoc#1 (line 812)"
        self.text = text
        self.kind = kind          # "page" | "srcdoc"
        self.line_offset = line_offset
        self._style = None
        self._views = {}

    def line_of(self, idx):
        return self.text.count("\n", 0, idx) + 1 + (self.line_offset if self.kind == "srcdoc" else 0)

    @property
    def style(self):
        """Every <style> body, with its offset in the original text."""
        if self._style is None:
            self._style = [(m.start(1), m.group(1)) for m in
                           re.finditer(r"<style[^>]*>(.*?)</style>", self.text, re.S | re.I)]
        return self._style

    def style_text(self):
        """All CSS, comments stripped. Offsets are NOT preserved - use view('css') for lines."""
        css = "\n".join(b for _, b in self.style)
        return strip_comments(css)

    # -- masked views ------------------------------------------------------
    # Every view keeps the original length and line numbering, so line_of()
    # stays correct; irrelevant regions are blanked instead of removed.

    def view(self, which):
        """'prose' = displayed code blocks blanked (they contain sample CSS/JS
        that must never be audited as if it were live).
        'css'  = prose mask + <script> bodies blanked + CSS comments blanked.
        'js'   = everything except <script> bodies blanked."""
        if which in self._views:
            return self._views[which]
        t = blank_ranges(self.text, ranges_of(self.text, r"<(pre|code|textarea)\b[^>]*>(.*?)</\1>", 2))
        if which == "prose":
            v = t
        elif which == "css":
            v = blank_ranges(t, ranges_of(t, r"<script[^>]*>(.*?)</script>", 1))
            v = blank_comments(v)
        elif which == "js":
            spans = ranges_of(t, r"<script[^>]*>(.*?)</script>", 1)
            keep = set()
            for s, e in spans:
                keep.add((s, e))
            v = list(" " * len(t))
            for s, e in keep:
                for i in range(s, e):
                    v[i] = t[i]
            for i, ch in enumerate(t):
                if ch == "\n":
                    v[i] = "\n"
            v = "".join(v)
        else:
            v = t
        self._views[which] = v
        return v

    def find(self, pattern, flags=re.I, where=None):
        hay = self.view(where) if where else self.text
        return [(m, self.line_of(m.start())) for m in re.finditer(pattern, hay, flags)]


def ranges_of(text, pattern, group):
    return [(m.start(group), m.end(group)) for m in re.finditer(pattern, text, re.S | re.I)]


def blank_ranges(text, spans):
    if not spans:
        return text
    out = list(text)
    for s, e in spans:
        for i in range(s, e):
            if out[i] != "\n":
                out[i] = " "
    return "".join(out)


def blank_comments(text):
    spans = [(m.start(), m.end()) for m in re.finditer(r"/\*.*?\*/", text, re.S)]
    spans += [(m.start(), m.end()) for m in re.finditer(r"<!--.*?-->", text, re.S)]
    return blank_ranges(text, spans)


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", " ", css, flags=re.S)


SRCDOC_RE = re.compile(r"""srcdoc\s*=\s*(['"])(.*?)\1""", re.S | re.I)


def split_documents(text, path, follow_srcdoc=True):
    """Return [page_doc, srcdoc_doc, ...] with srcdoc bodies blanked out of the page."""
    docs = []
    blanked = text
    subs = []
    if follow_srcdoc:
        for i, m in enumerate(SRCDOC_RE.finditer(text), 1):
            raw = m.group(2)
            inner = _html.unescape(raw)
            line = text.count("\n", 0, m.start(2)) + 1
            subs.append((m.start(2), m.end(2), i, inner, line))
    # blank srcdoc bodies in the page copy but keep the line count identical
    if subs:
        out = []
        last = 0
        for s, e, _i, _inner, _ln in subs:
            out.append(text[last:s])
            out.append("\n" * text.count("\n", s, e))
            last = e
        out.append(text[last:])
        blanked = "".join(out)

    docs.append(Doc("page", blanked, "page"))
    for _s, _e, i, inner, line in subs:
        docs.append(Doc("srcdoc#%d (page line %d)" % (i, line), inner, "srcdoc", line_offset=line - 1))
    return docs


# --------------------------------------------------------------------------
# CSS helpers
# --------------------------------------------------------------------------

AT_RE = re.compile(r"@media[^{]*\{", re.I)


def media_blocks(css):
    """[(query, body_start, body_end, body)] for every top-level @media block."""
    blocks = []
    for m in AT_RE.finditer(css):
        query = css[m.start():m.end() - 1].strip()
        depth = 1
        i = m.end()
        n = len(css)
        while i < n and depth:
            c = css[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            i += 1
        blocks.append((query, m.end(), i - 1, css[m.end():i - 1]))
    return blocks


def outside_media(css):
    """The CSS that is at global scope (every @media block removed)."""
    spans = [(s, e) for _q, s, e, _b in media_blocks(css)]
    if not spans:
        return css
    spans.sort()
    out = []
    last = 0
    for s, e in spans:
        # cut the whole at-rule, not only its body
        head = css.rfind("@media", 0, s)
        out.append(css[last:head if head >= 0 else s])
        last = e + 1
    out.append(css[last:])
    return "".join(out)


def query_widths(query):
    """[(kind, value)] for max-width / min-width terms in a media query."""
    return [(k, float(v)) for k, v in re.findall(r"(max|min)-width\s*:\s*([0-9.]+)px", query, re.I)]


def narrow_blocks(css, at_most=740):
    """Media blocks that describe a narrow tier (max-width <= at_most)."""
    out = []
    for q, s, e, b in media_blocks(css):
        for kind, val in query_widths(q):
            if kind == "max" and val <= at_most:
                out.append((q, val, b))
                break
    return out


def decl(css, prop):
    """All values declared for a property, as (value, index)."""
    return [(m.group(1).strip(), m.start()) for m in
            re.finditer(r"(?<![\w-])" + re.escape(prop) + r"\s*:\s*([^;{}]+)", css, re.I)]


def rules_for(css, selector_re):
    """[(selector, body)] for rules whose selector matches."""
    out = []
    for m in re.finditer(r"([^{}@]+)\{([^{}]*)\}", css):
        sel = m.group(1).strip()
        if re.search(selector_re, sel, re.I):
            out.append((sel, m.group(2)))
    return out


# --------------------------------------------------------------------------
# gates
# --------------------------------------------------------------------------

GATES = []


def gate(gid, title, scope="both", ref=""):
    """scope: 'page' | 'srcdoc' | 'both'."""
    def deco(fn):
        fn.gid, fn.title, fn.scope, fn.ref = gid, title, scope, ref
        GATES.append(fn)
        return fn
    return deco


def R(sev, msg, line=None):
    return (sev, msg, line)


# ---- document setup -------------------------------------------------------

@gate("R01", "viewport meta present", ref="F01")
def r01(d):
    hits = d.find(r"<meta[^>]+name=[\"']viewport[\"'][^>]*>")
    if not hits:
        return [R(FAIL, "no viewport meta - the document lays out at a ~980px synthetic viewport and no media query fires")]
    return [R(PASS, "%d viewport meta" % len(hits), hits[0][1])]


@gate("R02", "viewport left zoomable", ref="F02")
def r02(d):
    out = []
    for m, ln in d.find(r"<meta[^>]+name=[\"']viewport[\"'][^>]*>"):
        tag = m.group(0)
        if re.search(r"user-scalable\s*=\s*(no|0)", tag, re.I):
            out.append(R(FAIL, "viewport locks zoom (user-scalable=no) - WCAG 1.4.4", ln))
        if re.search(r"maximum-scale\s*=\s*([0-4](\.\d+)?)\b", tag, re.I):
            out.append(R(FAIL, "viewport caps zoom (maximum-scale) - WCAG 1.4.4", ln))
    return out or [R(PASS, "pinch-zoom available")]


@gate("R03", "color-scheme opt-out", ref="F03 / A2")
def r03(d):
    css = d.style_text()
    has_css = bool(re.search(r"color-scheme\s*:\s*light", css, re.I))
    has_meta = bool(d.find(r"<meta[^>]+name=[\"']color-scheme[\"']"))
    if d.kind == "page":
        if not has_css and not has_meta:
            return [R(FAIL, "no color-scheme opt-out - Android force-dark will invert the palette")]
        if not has_css:
            return [R(WARN, "color-scheme meta present but no `:root{color-scheme:light}`")]
        if not has_meta:
            return [R(WARN, "`:root{color-scheme:light}` present but no color-scheme meta")]
        return [R(PASS, "meta + CSS")]
    if not has_css:
        return [R(FAIL, "srcdoc has no `color-scheme:light` - the opt-out does not inherit across the iframe boundary")]
    return [R(PASS, "srcdoc carries its own color-scheme")]


@gate("R04", "transparent html/body", scope="page", ref="F04 / A3")
def r04(d):
    out = []
    css = d.style_text()
    for sel_re, name in ((r"^\s*html\b", "html"), (r"(^|,)\s*body\b", "body")):
        for sel, body in rules_for(css, sel_re):
            for prop in ("background", "background-color"):
                for val, _i in decl(body, prop):
                    v = val.strip().lower()
                    if v and v not in ("transparent", "none", "0 0", "initial", "unset"):
                        if not v.startswith(("transparent", "none")):
                            out.append(R(FAIL, "opaque %s background `%s: %s` - renders as vertical seams against the white host wrapper" % (name, prop, val.strip())))
    return out or [R(PASS, "html/body transparent")]


@gate("R05", "no-scrollport violations", ref="no-scrollport.md")
def r05(d):
    out = []
    css_checks = [
        (r"position\s*:\s*fixed", FAIL, "position:fixed - the ICB is the whole document here, so it behaves as position:absolute (F43)"),
        (r"position\s*:\s*sticky", WARN, "position:sticky is inert here - no scrollport, so it renders in flow and never sticks. Harmless at top:0, misleading anywhere else (F16)"),
        (r"(?<![\w.-])[0-9.]+(vh|svh|lvh|dvh)\b", FAIL, "viewport-height unit - equals the height the parent just wrote, so the handshake feeds itself (F46)"),
        (r"animation-timeline\s*:", WARN, "scroll-driven animation - inert without a scrollport"),
    ]
    js_checks = [
        (r"window\s*\.\s*innerHeight|(?<![\w.$])innerHeight\b", FAIL, "innerHeight - same circularity as vh (F46)"),
        (r"documentElement\s*\.\s*scrollHeight", FAIL, "documentElement.scrollHeight is floored at the viewport - one-way ratchet (F09 / H1)"),
        (r"\.scrollIntoView\s*\(", WARN, "scrollIntoView is a no-op in the embed - post netsetos-scroll-to instead (F15)"),
    ]
    for pat, sev, msg in css_checks:
        for _m, ln in d.find(pat, where="css"):
            out.append(R(sev, msg, ln))
    for pat, sev, msg in js_checks:
        for _m, ln in d.find(pat, where="js"):
            out.append(R(sev, msg, ln))
    # IntersectionObserver with the default root can never fire a leave event here
    io_hits = d.find(r"new\s+IntersectionObserver", where="js")
    if io_hits:
        has_root = bool(re.search(r"root\s*:", d.view("js")))
        has_parent = "netsetos-parent-scroll" in d.text
        if not has_root and not has_parent:
            out.append(R(WARN, "IntersectionObserver with the default root - everything is permanently intersecting, no leave event ever fires (F44)", io_hits[0][1]))
    # A scroll listener on the DOCUMENT is dead code here. One on an
    # overflow-x:auto pan container is legitimate (that element really does
    # scroll), so only flag window/document listeners.
    doc_scroll = d.find(r"(window|document|self)\s*\.\s*addEventListener\s*\(\s*['\"]scroll['\"]", where="js")
    doc_scroll += d.find(r"(window|document)\s*\.\s*onscroll\s*=", where="js")
    if doc_scroll and "netsetos-parent-scroll" not in d.text:
        out.append(R(FAIL, "document-level scroll listener with no netsetos-parent-scroll path - scrollTop is 0 forever inside the embed, so this never fires (F14)", doc_scroll[0][1]))
    return out or [R(PASS, "no scrollport-dependent features")]


# ---- breakpoint architecture ---------------------------------------------

@gate("R06", "breakpoint ladder present and ordered", ref="device-tiers.md")
def r06(d):
    css = d.style_text()
    blocks = media_blocks(css)
    if not blocks:
        return [R(FAIL, "no @media block at all - the page has one layout")]
    maxes = []
    for q, s, _e, _b in blocks:
        for kind, val in query_widths(q):
            if kind == "max":
                maxes.append((val, s, q))
    if not maxes:
        return [R(FAIL, "no max-width rung - nothing adapts to a narrow screen")]
    out = []
    seq = [v for v, _s, _q in maxes]
    # Only the config rungs have to be ordered: two blocks that both re-declare
    # :root fight at equal specificity, so the narrower one must come later. A
    # later repeat of a wider query that carries no :root (the CLS reserve block,
    # for instance) is legitimate and must not be flagged.
    config = []
    for q, s, e, b in blocks:
        if not re.search(r":root\s*\{", b):
            continue
        for kind, val in query_widths(q):
            if kind == "max":
                config.append((val, q))
                break
    prev = None
    for val, q in config:
        if prev is not None and val > prev:
            out.append(R(FAIL, "config rung `%s` re-declares :root after a narrower rung already did - at equal specificity the narrower tier loses the cascade" % q.strip()))
            break
        prev = val
    tiers = sorted(set(seq), reverse=True)
    if d.kind == "page":
        if not any(abs(v - 640) < 1 for v in seq):
            out.append(R(WARN, "no ~640px phone rung (found %s)" % tiers))
        if not any(abs(v - 380) < 1 for v in seq):
            out.append(R(WARN, "no ~380px small-phone nudge rung (found %s)" % tiers))
    else:
        if not any(abs(v - 740) < 1 for v in seq):
            out.append(R(WARN, "srcdoc has no ~740px rung - the animation control row stacks later than the page tier and needs its own (found %s)" % tiers))
    return out or [R(PASS, "rungs %s, in descending order" % tiers)]


@gate("R07", "min-width rung paired without a fractional dead band", ref="device-tiers.md 2.3")
def r07(d):
    css = d.style_text()
    mins = []
    maxs = set()
    for q, _s, _e, _b in media_blocks(css):
        for kind, val in query_widths(q):
            (mins if kind == "min" else maxs).add(val) if False else None
            if kind == "min":
                mins.append(val)
            else:
                maxs.add(val)
    out = []
    for v in mins:
        if (v - 1) in maxs:
            out.append(R(WARN, "min-width:%gpx paired with max-width:%gpx leaves fractional widths (%.2fpx) unowned - use min-width:%.2fpx" % (v, v - 1, v - 0.5, v - 0.98)))
    return out or [R(PASS, "no integer-only rung pairing")]


@gate("R08", "phone tier re-declares :root", ref="3.4")
def r08(d):
    css = d.style_text()
    tiers = narrow_blocks(css, 740 if d.kind == "srcdoc" else 640)
    if not tiers:
        return [R(INFO, "no narrow tier to inspect")]
    for _q, _v, body in tiers:
        if re.search(r":root\s*\{", body):
            return [R(PASS, "narrow tier re-declares :root")]
    return [R(WARN, "narrow tier sets no :root block - sizes are probably being changed on components instead of tokens (F37)")]


@gate("R09", "small-tier block is config only", scope="page", ref="B11")
def r09(d):
    css = d.style_text()
    out = []
    for q, val, body in narrow_blocks(css, 400):
        if val > 420:
            continue
        structural = re.findall(r"(?<![\w-])(display|flex-direction|flex-wrap|position|grid-template-areas|content)\s*:", body, re.I)
        if structural:
            out.append(R(WARN, "`%s` adds structure (%s) - the small tier is for config nudges only" % (q.strip(), ", ".join(sorted(set(s.lower() for s in structural))))))
    return out or [R(PASS, "small tier carries no structural rules")]


# ---- overflow -------------------------------------------------------------

@gate("R10", "overflow-x guard on body at global scope, never on html", ref="F05 F06 F07 / E1")
def r10(d):
    css = d.style_text()
    out = []
    for sel, body in rules_for(css, r"^\s*html\b"):
        if re.search(r"overflow(-x|-y)?\s*:\s*(clip|hidden)", body, re.I):
            out.append(R(FAIL, "overflow on `html` - CSS Overflow 3 forces overflow-y to clip too, and a handshake undershoot then amputates the page bottom (F07)"))
    glob = outside_media(css)
    if re.search(r"overflow-x\s*:\s*(clip|hidden)", glob, re.I):
        if not re.search(r"@supports\s+not\s*\(\s*overflow\s*:\s*clip", css, re.I) and "clip" in glob:
            out.append(R(WARN, "`overflow-x:clip` with no `@supports not (overflow:clip)` fallback for older engines"))
        out.append(R(PASS, "body overflow guard at global scope"))
    else:
        scoped = any(re.search(r"overflow-x\s*:\s*(clip|hidden)", b, re.I) for _q, _v, b in narrow_blocks(css, 900))
        if scoped:
            out.append(R(FAIL, "overflow-x guard is scoped to a narrow tier - the 100vw-versus-scrollbar overflow it absorbs is global, so desktop ships a horizontal scrollbar (E1)"))
        else:
            sev = FAIL if d.kind == "page" else WARN
            out.append(R(sev, "no `body{overflow-x:clip}` guard anywhere (F05)"))
    if not re.search(r"display\s*:\s*flow-root", css, re.I):
        out.append(R(WARN, "body has no `display:flow-root` - child margin collapse corrupts the body-box height measurement (H2)"))
    return out


@gate("R11", "universal min-width:0 in the narrow tier", ref="F05 / E2")
def r11(d):
    css = d.style_text()
    tiers = narrow_blocks(css, 740 if d.kind == "srcdoc" else 640)
    if not tiers:
        return [R(INFO, "no narrow tier")]
    for _q, _v, body in tiers:
        if re.search(r"\*\s*\{[^}]*min-width\s*:\s*0", body, re.I):
            return [R(PASS, "*{min-width:0} present")]
    return [R(WARN, "no `*{min-width:0}` in the narrow tier - flex/grid children default to min-width:auto and refuse to shrink (F05)")]


@gate("R12", "wrap discipline", ref="F06 / D6")
def r12(d):
    css = d.style_text()
    if re.search(r"overflow-wrap|word-break|hyphens", css, re.I):
        return [R(PASS, "wrap rules present")]
    sev = FAIL if re.search(r"overflow-x\s*:\s*clip", css, re.I) else WARN
    return [R(sev, "no overflow-wrap/word-break rule anywhere - a long token or bare URL overflows and, under overflow-x:clip, is silently cut with no scrollbar (F06)")]


@gate("R13", "replaced-element caps", ref="E3")
def r13(d):
    css = d.style_text()
    missing = [t for t in ("img", "svg", "iframe", "video", "table")
               if not rules_for(css, r"(^|,)\s*%s\b" % t)]
    caps = re.search(r"(img|svg|iframe|video)[^{}]*\{[^}]*max-width\s*:\s*100%", css, re.I)
    if caps:
        return [R(PASS, "replaced elements capped at 100%")]
    return [R(WARN, "no `max-width:100%` cap on img/svg/iframe/video - any intrinsically sized media defines the scroll width (F05); missing rules for: %s" % ", ".join(missing))]


@gate("R14", "horizontal scrollers contained and reachable", ref="F30 F49 / E4 G4")
def r14(d):
    css = d.style_text()
    out = []
    scrollers = [(sel, body) for sel, body in rules_for(css, r".")
                 if re.search(r"overflow-x\s*:\s*(auto|scroll)", body, re.I)]
    if not scrollers:
        return [R(INFO, "no horizontal scroller")]
    for sel, body in scrollers:
        if not re.search(r"overscroll-behavior(-x)?\s*:\s*contain", body, re.I):
            out.append(R(WARN, "`%s` scrolls horizontally with no `overscroll-behavior-x:contain` - the swipe chains to the host page and fires the back gesture (F30)" % sel.strip()[:60]))
    cls = set()
    for sel, _b in scrollers:
        cls.update(re.findall(r"\.([A-Za-z0-9_-]+)", sel))
    reachable = 0
    for c in cls:
        if re.search(r"class=[\"'][^\"']*\b%s\b[^\"']*[\"'][^>]*tabindex" % re.escape(c), d.text) or \
           re.search(r"tabindex[^>]*class=[\"'][^\"']*\b%s\b" % re.escape(c), d.text):
            reachable += 1
    if cls and reachable == 0:
        out.append(R(WARN, "no horizontal scroller carries `tabindex=\"0\"` - a keyboard user cannot reach the off-screen half (F49); scrollers: %s" % ", ".join(sorted(cls))[:120]))
    return out or [R(PASS, "%d scroller(s) contained and reachable" % len(scrollers))]


@gate("R15", "table becomes cards on phones", scope="page", ref="F23 F24 / E8")
def r15(d):
    tables = d.find(r"<table\b")
    if not tables:
        return [R(INFO, "no table")]
    out = []
    css = d.style_text()
    tds = len(re.findall(r"<td\b", d.text, re.I))
    labels = len(re.findall(r"data-label\s*=", d.text, re.I))
    rows = len(re.findall(r"<tr\b", d.text, re.I))
    firstcol = rows  # first td per row is exempt
    expected = max(0, tds - firstcol)
    if labels < expected:
        out.append(R(FAIL, "%d <td> in %d rows need %d data-label attributes, found %d - the stacked-card transform has nothing to print (F24)" % (tds, rows, expected, labels), tables[0][1]))
    if not re.search(r"td::before\s*\{[^}]*content\s*:\s*attr\(\s*data-label", css, re.I):
        out.append(R(FAIL, "no `td::before{content:attr(data-label)}` card transform in the phone tier (F23)"))
    if not re.search(r"clip-path\s*:\s*inset\(\s*50%", css, re.I):
        out.append(R(WARN, "thead is not hidden with `clip-path:inset(50%)` - either it stays visible as a broken row, or `display:none` takes it away from screen readers (F24)"))
    if not re.search(r"overflow-x\s*:\s*auto", css, re.I):
        out.append(R(WARN, "no horizontal scroll wrapper for the desktop/tablet width where the table is still tabular (F23)"))
    return out or [R(PASS, "%d table(s) with the card transform" % len(tables))]


@gate("R16", "scroll hint reserves its own band", ref="F27 / E7")
def r16(d):
    css = d.style_text()
    if not re.search(r"scroll-hint|svg-hint|\.hint\b", css, re.I):
        return [R(INFO, "no hint chip")]
    if re.search(r"padding-bottom\s*:\s*var\(\s*--hint-clear", css, re.I) or \
       re.search(r"--hint-clear\s*:", css, re.I):
        return [R(PASS, "hint clearance reserved")]
    return [R(WARN, "hint chip with no reserved band - it sits on the last line of code, which is exactly where a long line runs (F27)")]


# ---- touch ----------------------------------------------------------------

CONTROL_TOKENS = ("--touch", "--btn-min", "--tab-min", "--anim-min-tap", "--dot-min")


@gate("R17", "44px touch floor in the narrow tier", ref="F19 F21 / F1 F2")
def r17(d):
    css = d.style_text()
    tiers = narrow_blocks(css, 740 if d.kind == "srcdoc" else 640)
    if not tiers:
        return [R(INFO, "no narrow tier")]
    out = []
    seen = {}
    for _q, _v, body in tiers:
        for tok in CONTROL_TOKENS:
            for val, _i in decl(body, tok):
                m = re.match(r"\s*([0-9.]+)px", val)
                if m:
                    seen[tok] = float(m.group(1))
    if not seen:
        out.append(R(WARN, "no touch-floor token (%s) declared in the narrow tier" % "/".join(CONTROL_TOKENS[:3])))
    for tok, v in sorted(seen.items()):
        if v < 44:
            out.append(R(FAIL, "`%s:%gpx` in the narrow tier is below the 44px touch floor (F19)" % (tok, v)))
    # a class-level min-height silently outranks a token applied at element level
    for _q, _v, body in tiers:
        for sel, b in rules_for(body, r"\."):
            for val, _i in decl(b, "min-height"):
                m = re.match(r"\s*([0-9.]+)px\s*$", val)
                if m and float(m.group(1)) < 44:
                    out.append(R(FAIL, "`%s{min-height:%s}` - a class selector beats the element-level token, so this control stays under 44px. Use `min-height:max(%s,var(--touch))` (F19)" % (sel.strip()[:40], val.strip(), val.strip())))
    return out or [R(PASS, "touch floors at 44px+: %s" % ", ".join("%s=%g" % kv for kv in sorted(seen.items())))]


@gate("R18", "iOS focus-zoom guard on inputs", ref="F22 / F7")
def r18(d):
    if not d.find(r"<(input|select|textarea)\b"):
        return [R(INFO, "no form control")]
    css = d.style_text()
    if re.search(r"(input|select|textarea)[^{}]*\{[^}]*font-size\s*:\s*16px", css, re.I):
        return [R(PASS, "inputs at 16px")]
    return [R(FAIL, "form control without `font-size:16px` - iOS zooms the page on focus and never zooms back (F22)")]


@gate("R19", "every hover effect gated behind hover:hover and pointer:fine", ref="F17 / F5")
def r19(d):
    css = d.style_text()
    # `@media (hover:hover)` contains the literal ":hover"; blank every prelude
    # before counting, or a correctly gated file reports a phantom loose rule.
    scan = re.sub(r"@media[^{]*\{", lambda m: " " * len(m.group(0)), css)
    gated_spans = []
    for q, s, e, _b in media_blocks(css):
        if re.search(r"hover\s*:\s*hover", q, re.I) and re.search(r"pointer\s*:\s*fine", q, re.I):
            gated_spans.append((s, e))
    out = []
    loose = 0
    for m in re.finditer(r":hover\b", scan):
        i = m.start()
        if not any(s <= i <= e for s, e in gated_spans):
            loose += 1
    partial = [q for q, _s, _e, _b in media_blocks(css)
               if re.search(r"hover\s*:\s*hover", q, re.I) and not re.search(r"pointer\s*:\s*fine", q, re.I)]
    if partial:
        out.append(R(WARN, "hover block `%s` does not also require `pointer:fine` - stylus and coarse hybrids report hover:hover" % partial[0].strip()[:70]))
    if loose:
        out.append(R(FAIL, "%d `:hover` rule(s) outside `@media (hover:hover) and (pointer:fine)` - a tapped element latches the hover state and looks permanently selected (F17)" % loose))
    return out or [R(PASS, "all hover rules gated")]


@gate("R20", "press affordance for touch", ref="F18 / F6")
def r20(d):
    css = d.style_text()
    if re.search(r":active\b", css):
        return [R(PASS, ":active feedback present")]
    return [R(WARN, "no `:active` state - with hover correctly gated off, touch gets no acknowledgement at all (F18)")]


# ---- motion and modes -----------------------------------------------------

@gate("R21", "reduced motion honored, and not with animation:none", ref="F33 F34 / I1")
def r21(d):
    css = d.style_text()
    blocks = [(q, b) for q, _s, _e, b in media_blocks(css) if re.search(r"prefers-reduced-motion", q, re.I)]
    out = []
    if not blocks:
        return [R(FAIL, "no `@media (prefers-reduced-motion: reduce)` block - and it does not inherit across an iframe boundary, so every srcdoc needs its own (F33)")]
    for _q, b in blocks:
        if re.search(r"animation\s*:\s*none", b, re.I):
            out.append(R(FAIL, "`animation:none` in the reduce block discards forwards-fill end states - elements freeze in their pre-animation position. Use the .01ms convention (F34)"))
    if d.find(r"prefers-reduced-motion") and "matchMedia" in d.text:
        pass
    elif d.find(r"requestAnimationFrame|setInterval"):
        out.append(R(WARN, "JS animation with no `matchMedia('(prefers-reduced-motion: reduce)')` check - CSS alone cannot stop a JS tween (I2)"))
    return out or [R(PASS, "reduce block present, .01ms convention")]


@gate("R22", "forced-colors rescue", ref="F35 / I6")
def r22(d):
    css = d.style_text()
    if any(re.search(r"forced-colors", q, re.I) for q, _s, _e, _b in media_blocks(css)):
        return [R(PASS, "forced-colors block present")]
    clipped = re.search(r"-webkit-background-clip\s*:\s*text|background-clip\s*:\s*text", css, re.I)
    sev = FAIL if clipped else WARN
    return [R(sev, "no `@media (forced-colors: active)` block%s (F35)" % (" and the file uses a gradient-clipped headline, which disappears entirely under high contrast" if clipped else ""))]


@gate("R23", "print tier", scope="page", ref="F36 / I7")
def r23(d):
    css = d.style_text()
    blocks = [b for q, _s, _e, b in media_blocks(css) if re.search(r"\bprint\b", q, re.I)]
    if not blocks:
        return [R(WARN, "no `@media print` block - printing keeps the chrome and clips every code line (F36)")]
    out = []
    if not re.search(r"white-space\s*:\s*pre-wrap", blocks[0], re.I):
        out.append(R(WARN, "print block does not wrap code - paper is the narrowest device and the one place code must wrap (I7)"))
    if not re.search(r"break-inside\s*:\s*avoid", blocks[0], re.I):
        out.append(R(WARN, "print block has no `break-inside:avoid` on cards and tables (G13)"))
    return out or [R(PASS, "print tier complete")]


# ---- animation embeds and the handshake -----------------------------------

@gate("R24", "height reporter measures the body box", scope="page", ref="F08 F09 / H1 H5")
def r24(d):
    if not re.search(r"postMessage", d.text):
        return [R(WARN, "no postMessage anywhere - if this page is embedded, the host cannot size it")]
    out = []
    if re.search(r"documentElement\s*\.\s*scrollHeight", d.view("js")):
        out.append(R(FAIL, "height is measured from documentElement.scrollHeight, which is floored at the viewport - the handshake becomes a one-way ratchet (F09 / H1)"))
    elif not re.search(r"getBoundingClientRect", d.view("js")):
        out.append(R(FAIL, "height is not measured from a body bounding rect (F09 / H1)"))
    if not re.search(r"self\s*!==\s*top|window\s*!==\s*(window\.)?top|self\s*!=\s*top", d.text):
        out.append(R(WARN, "height reporter is not guarded with `self !== top` - it will post from the standalone preview too (H5)"))
    if not re.search(r"try\s*\{[^}]*postMessage", d.text, re.S):
        out.append(R(WARN, "postMessage is not wrapped in try/catch (H5)"))
    for ev in ("resize", "orientationchange", "load"):
        if not re.search(r"['\"]%s['\"]" % ev, d.text):
            out.append(R(WARN, "height reporter never re-fires on `%s` (H6)" % ev))
    if not re.search(r"fonts\s*\.\s*ready", d.text):
        out.append(R(WARN, "height is never re-measured after `document.fonts.ready` - the webfont swap changes every line box (F39)"))
    return out or [R(PASS, "body-rect reporter, guarded, full retrigger set")]


@gate("R25", "resize listener guards on a real width change", ref="F47")
def r25(d):
    if not re.search(r"addEventListener\s*\(\s*['\"]resize['\"]", d.text):
        return [R(INFO, "no resize listener")]
    if re.search(r"clientWidth|innerWidth", d.text):
        return [R(PASS, "resize handler reads a width")]
    return [R(WARN, "resize handler does no width comparison - the Android URL bar fires resize dozens of times per scroll with no width change (F47)")]


@gate("R26", "per-embed CLS reserve, tiered to the animation breakpoint", scope="page", ref="F13 / H9")
def r26(d):
    embeds = d.find(r"<div[^>]*class=[\"'][^\"']*anim-embed")
    if not embeds:
        return [R(INFO, "no animation embed")]
    out = []
    css = d.style_text()
    paired = len(re.findall(r"--anim-ratio-d\s*:", d.text))
    if paired < len(embeds):
        out.append(R(WARN, "%d animation embed(s) but only %d inline `--anim-ratio-d` pair(s) - one global ratio reserves the wrong height for differently shaped embeds (F13)" % (len(embeds), paired)))
    swap = None
    for q, _s, _e, b in media_blocks(css):
        if "anim-ratio-m" in b:
            for kind, val in query_widths(q):
                if kind == "max":
                    swap = val
    if swap is None:
        out.append(R(WARN, "no tier swaps `--anim-ratio-m` in - the phone reserve is typically 15-19% taller than desktop for the same animation (H9)"))
    elif abs(swap - 740) > 1:
        out.append(R(WARN, "the CLS reserve swaps at %gpx of page width but the animation flips its layout at 740px of iframe width - between those two the parent reserves the short ratio for a tall frame (H9)" % swap))
    return out or [R(PASS, "%d embed(s) with tiered reserves" % len(embeds))]


@gate("R27", "first embed eager, later embeds lazy", scope="page", ref="F13 / H10")
def r27(d):
    frames = [(m, ln) for m, ln in d.find(r"<iframe\b[^>]*>")]
    anim = [(m, ln) for m, ln in frames if "srcdoc" in m.group(0).lower()]
    if not anim:
        return [R(INFO, "no srcdoc iframe")]
    out = []
    first, first_ln = anim[0]
    if re.search(r"loading\s*=\s*[\"']lazy", first.group(0), re.I):
        out.append(R(FAIL, "the first animation carries loading=\"lazy\" - it is above the fold and the deferral costs a visible pop-in (F13)", first_ln))
    for m, ln in anim[1:]:
        if not re.search(r"loading\s*=\s*[\"']lazy", m.group(0), re.I):
            out.append(R(WARN, "later animation is eager - every frame after the first should be lazy (H10)", ln))
    for m, ln in anim:
        if not re.search(r"scrolling\s*=\s*[\"']no", m.group(0), re.I):
            out.append(R(WARN, "iframe without `scrolling=\"no\"` - a nested scrollbar appears and steals vertical swipes", ln))
        if not re.search(r"\btitle\s*=", m.group(0), re.I):
            out.append(R(WARN, "iframe without a `title` attribute", ln))
    return out or [R(PASS, "%d embed(s), first eager, rest lazy" % len(anim))]


@gate("R28", "two message names, one per hop", ref="B03 / H7")
def r28(d):
    if d.kind == "srcdoc":
        if "netsetos-embed-height" in d.text:
            return [R(FAIL, "srcdoc posts `netsetos-embed-height`, the page-to-host name - the two hops must not share a name (B03)")]
        if "postMessage" in d.text and "netsetos-anim-height" not in d.text:
            return [R(WARN, "srcdoc posts a message that is not `netsetos-anim-height` - the lesson router will not recognise it")]
        return [R(PASS, "srcdoc uses the inner hop name")]
    if d.find(r"<iframe[^>]*srcdoc") and "netsetos-anim-height" not in d.text:
        return [R(WARN, "page embeds srcdoc animations but never listens for `netsetos-anim-height`")]
    return [R(PASS, "message names distinct")]


# ---- SVG legibility -------------------------------------------------------

@gate("R29", "SVG labels stay above the 9px rendered floor", ref="F28 / G1 G0")
def r29(d):
    vbs = [(float(m.group(1)), ln) for m, ln in d.find(r"viewBox\s*=\s*[\"']\s*[-0-9.]+\s+[-0-9.]+\s+([0-9.]+)")]
    if not vbs:
        return [R(INFO, "no SVG viewBox")]
    css = d.style_text()
    floors = []
    for tok in ("--pan-floor", "--svg-min"):
        for val, _i in decl(css, tok):
            m = re.match(r"\s*(?:var\([^,]+,\s*)?([0-9.]+)px", val)
            if m and float(m.group(1)) > 0:
                floors.append(float(m.group(1)))
    # Only font sizes written INSIDE an <svg> count: they are user units, which is
    # what the scale applies to. A `font-size:9px` on a page chip is a CSS pixel and
    # would make the arithmetic nonsense.
    svg_spans = ranges_of(d.text, r"<svg\b.*?</svg>", 0)
    svg_text = "".join(d.text[s:e] for s, e in svg_spans)
    sizes = []
    for m in re.finditer(r"font-size\s*[:=]\s*[\"']?\s*([0-9.]+)(px)?", svg_text, re.I):
        v = float(m.group(1))
        if 4 <= v <= 40:
            sizes.append(v)
    if not sizes:
        return [R(INFO, "no font-size inside the SVG markup - labels may be styled from the stylesheet, check legibility by hand")]
    smallest = min(sizes)
    vb = max(v for v, _l in vbs)
    out = []
    relayout = bool(re.search(r"matchMedia", d.text)) and len(set(v for v, _l in vbs)) > 1
    if floors:
        floor = max(floors)
        rendered = floor / vb * smallest
        if rendered < 9:
            out.append(R(FAIL, "pan floor %gpx against a %g-unit viewBox renders %g-unit labels at %.1fpx, under the 9px hard floor. Either re-layout in portrait, or raise the floor to %.0fpx (F28 / G0)" % (floor, vb, smallest, rendered, 9.0 * vb / smallest)))
        else:
            out.append(R(PASS, "pan floor %gpx renders the smallest label at %.1fpx" % (floor, rendered)))
    else:
        # no floor at all: the SVG scales freely down to the phone width
        rendered = 360.0 / vb * smallest
        sev = FAIL if rendered < 9 else WARN
        out.append(R(sev, "no `--pan-floor`/`--svg-min` and no portrait re-layout: at 360px the %g-unit viewBox renders %g-unit labels at %.1fpx (F28)" % (vb, smallest, rendered)))
    if smallest < 11:
        out.append(R(WARN, "smallest SVG label is %g units - the authoring rule is 13 units for primary labels and 11 for secondary (G0)" % smallest))
    if not relayout and floors:
        out.append(R(WARN, "pan-with-floor is the fallback; portrait re-layout is the rule. No second viewBox found (D4)"))
    return out


@gate("R30", "matchMedia layout switch subscribes to change and re-measures", ref="F29 / 6.5")
def r30(d):
    js = d.view("js")
    # Only a WIDTH matchMedia is a layout switch. A one-off reduced-motion probe
    # needs no change listener and must not be flagged.
    if not re.search(r"matchMedia\s*\(\s*['\"][^'\"]*(max|min)-width", js, re.I):
        return [R(INFO, "no width-based matchMedia layout switch")]
    out = []
    if not re.search(r"addEventListener\s*\(\s*['\"]change['\"]|addListener\s*\(", js):
        out.append(R(FAIL, "matchMedia with no `change` subscription - rotating the phone or resizing the host column crosses the breakpoint without reloading the frame, so the geometry never swaps (F29)"))
    if not re.search(r"matchMedia\s*\([^)]*\)\s*\|\||matchMedia\s*\?|window\.matchMedia\s*&&", js):
        out.append(R(WARN, "no null-object fallback for a missing `matchMedia` - the diagram blanks instead of degrading (G2)"))
    return out or [R(PASS, "layout switch subscribes to change")]


@gate("R31", "scene stacking scoped to the active scene", ref="F32 / B17")
def r31(d):
    css = d.style_text()
    out = []
    for _q, _v, body in narrow_blocks(css, 900):
        for sel, b in rules_for(body, r"\.scene\b"):
            if re.search(r"display\s*:\s*(block|flex|grid)", b, re.I) and ".active" not in sel:
                out.append(R(FAIL, "`%s{display:...}` in a narrow tier overrides the base `.scene{display:none}` at equal specificity - every scene renders stacked (F32)" % sel.strip()[:40]))
    return out or [R(PASS, "scene visibility unaffected by the narrow tier")]


# ---- polish ---------------------------------------------------------------

@gate("R32", "font delivery", ref="F39 / A5 G14")
def r32(d):
    if "fonts.googleapis.com" not in d.text:
        return [R(INFO, "no webfont")]
    out = []
    if not re.search(r"preconnect[^>]+fonts\.gstatic\.com[^>]*crossorigin", d.text, re.I) and \
       not re.search(r"crossorigin[^>]+fonts\.gstatic\.com", d.text, re.I):
        out.append(R(WARN, "no crossorigin preconnect to fonts.gstatic.com, where the woff2 files actually live - a full DNS+TLS round trip per frame on a cold mobile connection (G14)"))
    if not re.search(r"display=swap", d.text, re.I):
        out.append(R(WARN, "webfont without `&display=swap` - text is invisible until the font lands"))
    if re.search(r"<svg[^>]*>.*?font-family\s*:\s*['\"]?(Playfair|DM Sans|JetBrains)", d.text, re.S | re.I):
        out.append(R(WARN, "a swapping webfont is used inside an SVG - label widths change after first paint and can collide with the geometry (G14)"))
    return out or [R(PASS, "fonts preconnected and swapping")]


@gate("R33", "text inflation pinned", ref="A4")
def r33(d):
    if re.search(r"text-size-adjust", d.style_text(), re.I):
        return [R(PASS, "text-size-adjust pinned")]
    return [R(WARN, "no `-webkit-text-size-adjust:100%` - iOS Safari inflates text in narrow blocks on rotate (A4)")]


@gate("R34", "safe-area insets where the layout is edge to edge", ref="G4 / 5.8")
def r34(d):
    css = d.style_text()
    edge = any(re.search(r"--media-gutter\s*:\s*0", b) or re.search(r"--pad-x\s*:\s*0", b)
               for _q, _v, b in narrow_blocks(css, 640))
    if not edge:
        return [R(INFO, "layout is not edge to edge on phones")]
    if "env(safe-area-inset" in css:
        return [R(PASS, "safe-area insets honored")]
    return [R(WARN, "full-bleed on phones with no `env(safe-area-inset-*)` anywhere - on a notched phone in landscape the left edge of a code block sits under the sensor housing (G4)")]


@gate("R35", "dead config tokens", ref="F37 / G9")
def r35(d):
    css = d.style_text()
    declared = set()
    for m in re.finditer(r"(--[A-Za-z0-9_-]+)\s*:", css):
        declared.add(m.group(1))
    used = set(re.findall(r"var\(\s*(--[A-Za-z0-9_-]+)", css))
    dead = sorted(declared - used)
    if not dead:
        return [R(PASS, "%d tokens, all consumed" % len(declared))]
    return [R(WARN, "%d declared token(s) never read - wire them or delete them, or the config block's promise stops being true (G9): %s" % (len(dead), ", ".join(dead[:12]) + (" ..." if len(dead) > 12 else "")))]


@gate("R36", "order does not desync tab order", ref="F52")
def r36(d):
    hits = [(m, ln) for m, ln in d.find(r"(?<![\w-])order\s*:\s*[0-9]")]
    if not hits:
        return [R(PASS, "no flex/grid order reordering")]
    return [R(WARN, "%d `order:` declaration(s) - visual order and DOM/tab order now disagree at exactly the width where the reordering was needed (F52); reorder the DOM and use order to restore desktop instead" % len(hits), hits[0][1])]


@gate("R37", "raster images carry intrinsic size", ref="F51")
def r37(d):
    imgs = d.find(r"<img\b[^>]*>")
    if not imgs:
        return [R(INFO, "no raster image")]
    bad = [ln for m, ln in imgs if not (re.search(r"\bwidth\s*=", m.group(0), re.I) and re.search(r"\bheight\s*=", m.group(0), re.I))]
    if bad:
        return [R(WARN, "%d <img> without both width and height attributes - `height:auto` then discards the aspect ratio instead of preserving it, and every image shifts the layout (F51); first at line %d" % (len(bad), bad[0]))]
    return [R(PASS, "%d image(s) with intrinsic size" % len(imgs))]


@gate("R38", "focus does not scroll the host unpredictably", scope="page", ref="F48")
def r38(d):
    if "netsetos-scroll-to" not in d.text:
        return [R(WARN, "no `netsetos-scroll-to` path - a keyboard user tabbing below the fold triggers a UA scroll-into-view that the embed cannot perform, so the host column jumps by an amount the page does not control (F48)")]
    if not re.search(r"['\"]focusin['\"]", d.text):
        return [R(WARN, "`netsetos-scroll-to` exists for clicks but there is no `focusin` handler - the keyboard path is still unhandled (F48)")]
    return [R(PASS, "click and focus scroll paths both routed to the host")]


@gate("R39", "no em-dashes", ref="B27")
def r39(d):
    # escapes, not literals, so this file obeys the rule it enforces
    hits = d.find("[\\u2014\\u2013\\u2015]|&mdash;|&ndash;")
    if hits:
        return [R(FAIL, "%d em/en dash(es), first at line %d - house rule is hyphens only, including inside srcdoc" % (len(hits), hits[0][1]), hits[0][1])]
    return [R(PASS, "hyphens only")]


@gate("R40", "srcdoc quoting", scope="page", ref="D6 / B23")
def r40(d):
    dq = d.find(r"srcdoc\s*=\s*\"")
    if dq:
        return [R(WARN, "%d double-quoted `srcdoc=\"...\"` - convert to single-quoted with 5-entity escaping at next assembly (B23)" % len(dq), dq[0][1])]
    if d.find(r"srcdoc\s*=\s*'"):
        return [R(PASS, "single-quoted srcdoc")]
    return [R(INFO, "no srcdoc")]


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------

def audit(path, follow_srcdoc=True, only=None):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    docs = split_documents(text, path, follow_srcdoc)
    results = []
    for d in docs:
        for fn in GATES:
            if only and fn.gid not in only:
                continue
            if fn.scope != "both" and fn.scope != d.kind:
                continue
            try:
                rows = fn(d) or []
            except Exception as exc:                      # a gate must never take the run down
                rows = [R(WARN, "gate crashed: %s: %s" % (type(exc).__name__, exc))]
            for sev, msg, line in rows:
                results.append({
                    "gate": fn.gid, "title": fn.title, "ref": fn.ref,
                    "doc": d.name, "severity": sev, "message": msg, "line": line,
                })
    return results


SEV_ORDER = {FAIL: 0, WARN: 1, INFO: 2, PASS: 3}


def render(path, results, verbose=False):
    counts = {FAIL: 0, WARN: 0, INFO: 0, PASS: 0}
    for r in results:
        counts[r["severity"]] += 1
    print("")
    print("=" * 78)
    print("responsive audit  %s" % path)
    print("=" * 78)
    docs = []
    for r in results:
        if r["doc"] not in docs:
            docs.append(r["doc"])
    for doc in docs:
        rows = [r for r in results if r["doc"] == doc]
        shown = [r for r in rows if verbose or r["severity"] in (FAIL, WARN)]
        head = "-- %s  (%d FAIL, %d WARN)" % (
            doc,
            sum(1 for r in rows if r["severity"] == FAIL),
            sum(1 for r in rows if r["severity"] == WARN))
        print("")
        print(head)
        if not shown:
            print("   clean")
            continue
        shown.sort(key=lambda r: (SEV_ORDER[r["severity"]], r["gate"]))
        for r in shown:
            loc = (" line %d" % r["line"]) if r["line"] else ""
            print("   [%-4s] %s%s  %s" % (r["severity"], r["gate"], loc, r["message"]))
            if r["ref"]:
                print("            ref: %s" % r["ref"])
    print("")
    print("-" * 78)
    print("TOTAL  %d FAIL   %d WARN   %d PASS   %d INFO   across %d document(s)"
          % (counts[FAIL], counts[WARN], counts[PASS], counts[INFO], len(docs)))
    print("")
    return counts[FAIL]


def main(argv):
    args = [a for a in argv[1:]]
    as_json = "--json" in args
    verbose = "--verbose" in args or "-v" in args
    follow = "--no-srcdoc" not in args
    only = None
    if "--only" in args:
        i = args.index("--only")
        only = set(x.strip().upper() for x in args[i + 1].split(","))
        del args[i:i + 2]
    files = [a for a in args if not a.startswith("-")]
    if not files:
        print(__doc__)
        return 2
    worst = 0
    payload = {}
    for path in files:
        if not os.path.exists(path):
            print("no such file: %s" % path)
            return 2
        res = audit(path, follow_srcdoc=follow, only=only)
        payload[path] = res
        if as_json:
            worst = max(worst, sum(1 for r in res if r["severity"] == FAIL))
        else:
            worst = max(worst, render(path, res, verbose))
    if as_json:
        print(json.dumps(payload, indent=1))
    return 1 if worst else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
