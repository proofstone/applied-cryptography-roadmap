#!/usr/bin/env python3
"""Deterministic SVG renderer for the roadmap path map.

The map is data, not a drawing: edit SECTIONS / EDGES below and re-run to
regenerate assets/roadmap.svg. No external dependencies, no randomness, no
timestamps — the same input always produces byte-identical output, so the
committed SVG and this script never drift.

    python scripts/render_map.py            # writes assets/roadmap.svg
    python scripts/render_map.py --check    # exit 1 if the SVG is stale

────────────────────────────────────────────────────────────────────────────
FIVE RULES THIS FILE MUST KEEP. Breaking any of them is silent — the SVG still
renders, and the site still builds green, while the map stops working.

1.  NO <g transform> ANYWHERE, AND NO GROUPS AROUND NODES.
    proofstone.dev inlines this SVG and appends its own clickable <rect> per
    section, in the ROOT coordinate system, copied from the section box's own
    x/y/width/height. A group transform would move the drawing but not the
    hotspot, so the box would render in one place and be clickable in another —
    with a green build, because the hotspot was still counted.

2.  A SECTION'S <rect> AND ITS "§N" <text> ARE ADJACENT.
    The site joins hotspots to README sections on the "§N" label, found by
    looking for a <rect> immediately followed by a <text> starting with it.
    Only <title>/<desc> may sit between. Anything else and that section
    silently loses its link.
    Corollary, and it matters on this map: the two ORDER cards below are not
    sections. They are geometry — the fork drawn instead of described — and
    their <rect> is followed by ordinary text, so the parser passes over them.
    Coverage here is 11 hotspots for 11 §-sections and the fork must not
    change that.

3.  GEOMETRY IS PLAIN NUMBERS.
    x/y/width/height are read with a regex that accepts digits and a dot and
    nothing else. No units, no percentages, no negatives, no var().

4.  COLOUR GOES THROUGH var(<token>, <fallback>).
    Inlined on the site the SVG inherits the page's theme tokens; standalone on
    GitHub var() does not resolve and the baked-in literal keeps it light.

5.  NO EMOJI.
    Flagship sections carry a drawn FLAGSHIP stamp. The ⭐ and 🔀 in the README
    stay — they are the data the site reads.
────────────────────────────────────────────────────────────────────────────

WHY THIS MAP IS SHAPED DIFFERENTLY FROM THE OTHERS IN THE SERIES

This roadmap opens with a choice the other two do not have: which order you
walk it in. The README's own dependency block puts it first —

    Order A (Cryptopals-first) ─┐
    Order B (CryptoHack-first) ─┴─► §1 ─► §2 ─► §3 ─► §4
                                                       │
      §5 Keys / passwords  (deployment-facing; alongside) ──┤
                                                       ▼
                          §6 ─► §7 ─► §8
                                                       │
      §9 Post-quantum  (read anytime after §6) ────────┤
                                                       ▼
                                        §10 The honest ceiling

— so the fork is drawn as two cards converging on §1 rather than written as a
caption, and §5 and §9 sit off to the side because that is what "runs
alongside" and "read anytime" mean. The spine stays a spine: the attack-ordered
chain that the OWASP checklist imposes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# --- data -------------------------------------------------------------------
# (id, short label for the map, lane, flagship?)
# `flagship` marks a section that CONTAINS a ⭐ milestone in the README:
# §2 (M2.1), §4 (M4.1), §6 (M6.2), §9 (M9.1) — four starred milestones, one
# each. Labels are short on purpose: the site names each hotspot from the
# README's own section heading, so this text only has to work as a picture.
SECTIONS = [
    ("§0",  "Orientation",       "spine", False),
    ("§1",  "Symmetric",         "spine", False),
    ("§2",  "The padding oracle", "spine", True),
    ("§3",  "Randomness",        "spine", False),
    ("§4",  "Hashes & MACs",     "spine", True),
    ("§5",  "Keys & passwords",  "aside", False),
    ("§6",  "Public key",        "spine", True),
    ("§7",  "Elliptic curves",   "spine", False),
    ("§8",  "Crypto on the web", "spine", False),
    ("§9",  "Post-quantum",      "aside", True),
    ("§10", "The honest ceiling", "spine", False),
]

# The attack-ordered chain the checklist imposes.
EDGES = [
    ("§1", "§2"), ("§2", "§3"), ("§3", "§4"), ("§4", "§6"),
    ("§6", "§7"), ("§7", "§8"), ("§8", "§10"),
]
# Alongside: real sections, but you choose when. Dashed already means that here.
# Each aside edge gets its OWN vertical corridor in the gap between the two
# columns. Sharing one made three separate relationships read as a single
# trunk with branches, which is the opposite of what they are.
ASIDES = [("§5", "§6", 430), ("§6", "§9", 405), ("§9", "§10", 380)]

# --- layout -----------------------------------------------------------------
W = 820
H = 1064

SPINE_X, SPINE_W = 40, 320
ASIDE_X, ASIDE_W = 440, 320
NODE_H, FLAG_H = 56, 72

POS = {
    "§0":  (SPINE_X, 104, SPINE_W, NODE_H),
    "§1":  (SPINE_X, 296, SPINE_W, NODE_H),
    "§2":  (SPINE_X, 382, SPINE_W, FLAG_H),
    "§3":  (SPINE_X, 488, SPINE_W, NODE_H),
    "§4":  (SPINE_X, 574, SPINE_W, FLAG_H),
    "§5":  (ASIDE_X, 488, ASIDE_W, NODE_H),
    "§6":  (SPINE_X, 692, SPINE_W, FLAG_H),
    "§7":  (SPINE_X, 798, SPINE_W, NODE_H),
    "§8":  (SPINE_X, 884, SPINE_W, NODE_H),
    "§9":  (ASIDE_X, 798, ASIDE_W, NODE_H),
    "§10": (SPINE_X, 970, SPINE_W, NODE_H),
}

# The fork, as geometry. NOT sections — see rule 2.
ORDER_Y, ORDER_H = 190, 44
ORDERS = [
    (SPINE_X, "Order A", "Cryptopals-first"),
    (ASIDE_X, "Order B", "CryptoHack-first"),
]

PAPER = "var(--map-paper, #f7f3ea)"
NODE = "var(--map-node, #efe8d9)"
SPINE_FILL = "var(--map-node-spine, #e7ded0)"
INK = "var(--map-ink, #3a3128)"
LINE = "var(--map-line, #6b6152)"
ACCENT = "var(--accent, #9d3b1f)"
GOLD = "var(--gold, #7a5809)"

SANS = ("'IBM Plex Sans',-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,"
        "Helvetica,Arial,sans-serif")
MONO = "'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def flagship_stamp(x: float, y: float) -> str:
    """Drawn stamp in place of ⭐ (rule 5). Rotation is on the elements
    themselves, never on a wrapping group (rule 1)."""
    cx, cy = x + 44, y - 5
    return (
        f'<rect x="{x}" y="{y - 13}" width="88" height="17" rx="2" fill="none" '
        f'stroke="{GOLD}" stroke-width="1.2" transform="rotate(-3 {cx} {cy})"/>'
        f'<text x="{cx}" y="{y - 1}" transform="rotate(-3 {cx} {cy})" '
        f'text-anchor="middle" font-family="{MONO}" font-size="9" letter-spacing="1.5" '
        f'font-weight="600" fill="{GOLD}">FLAGSHIP</text>'
    )


def connector(a_id: str, b_id: str, dashed: bool, corridor: float | None = None) -> str:
    """Manhattan connectors only — a line follows an axis or turns a right
    angle. No diagonal sticks: this is a drawing, not a graph dump."""
    ax, ay, aw, ah = POS[a_id]
    bx, by, bw, bh = POS[b_id]
    acx, bcx = ax + aw / 2, bx + bw / 2
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    common = (f'fill="none" stroke="{LINE}" stroke-width="1.8"{dash} '
              f'marker-end="url(#arw)"')

    if abs(acx - bcx) < 1:                       # straight down the spine
        return (f'<line x1="{acx}" y1="{ay + ah}" x2="{bcx}" y2="{by}" '
                f'stroke="{LINE}" stroke-width="1.8"{dash} marker-end="url(#arw)"/>')
    cx = corridor if corridor is not None else (min(ax, bx) - 30)
    if bx > ax:                                  # spine out to the aside column
        return (f'<path d="M {ax + aw} {ay + ah / 2} L {cx} {ay + ah / 2} '
                f'L {cx} {by + bh / 2} L {bx} {by + bh / 2}" {common}/>')
    # aside back onto the spine
    return (f'<path d="M {ax} {ay + ah / 2} L {cx} {ay + ah / 2} '
            f'L {cx} {by + bh / 2} L {bx + bw} {by + bh / 2}" {common}/>')


def build() -> str:
    p: list[str] = []
    a = p.append

    a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
      f'width="{W}" height="{H}" font-family="{SANS}" '
      f'role="img" aria-label="Applied Cryptography roadmap path map">')

    # Filled, not none: in dark theme the map has to BE dark, or it lands as a
    # light rectangle on a dark page.
    a(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')

    a(f'<text x="{SPINE_X}" y="46" font-size="23" font-weight="700" fill="{INK}">'
      f'Working engineer &#8594; shipping cryptography safely</text>')
    a(f'<text x="{SPINE_X}" y="72" font-size="13" fill="{LINE}">'
      f'Every node is a milestone with a pass/fail flag.</text>')

    a(f'<defs><marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" '
      f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
      f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{LINE}"/></marker></defs>')

    # ── the fork, drawn ──────────────────────────────────────────────────────
    # Two cards that converge on §1. Dashed, because this is a choice, and the
    # rest of the series already uses dashed for exactly that. They carry no
    # "§N" label, so the site's parser does not see them as sections (rule 2).
    x0, y0, w0, h0 = POS["§0"]
    s1x, s1y, s1w, s1h = POS["§1"]
    join_y = ORDER_Y + ORDER_H + 30
    a(f'<line x1="{x0 + w0 / 2}" y1="{y0 + h0}" x2="{x0 + w0 / 2}" y2="{ORDER_Y}" '
      f'stroke="{LINE}" stroke-width="1.8"/>')
    for ox, name, sub in ORDERS:
        a(f'<rect x="{ox}" y="{ORDER_Y}" width="{SPINE_W}" height="{ORDER_H}" rx="6" '
          f'fill="{PAPER}" stroke="{LINE}" stroke-width="1.4" stroke-dasharray="5 4"/>')
        a(f'<text x="{ox + 16}" y="{ORDER_Y + 27}" font-family="{MONO}" font-size="11" '
          f'letter-spacing="1" fill="{ACCENT}">{esc(name.upper())}</text>')
        a(f'<text x="{ox + 96}" y="{ORDER_Y + 27}" font-size="14" fill="{INK}">'
          f'{esc(sub)}</text>')
        a(f'<line x1="{ox + SPINE_W / 2}" y1="{ORDER_Y + ORDER_H}" '
          f'x2="{ox + SPINE_W / 2}" y2="{join_y}" stroke="{LINE}" stroke-width="1.8"/>')
    # the two paths meet, then one arrow enters §1
    a(f'<line x1="{SPINE_X + SPINE_W / 2}" y1="{join_y}" '
      f'x2="{ASIDE_X + ASIDE_W / 2}" y2="{join_y}" stroke="{LINE}" stroke-width="1.8"/>')
    a(f'<line x1="{s1x + s1w / 2}" y1="{join_y}" x2="{s1x + s1w / 2}" y2="{s1y}" '
      f'stroke="{LINE}" stroke-width="1.8" marker-end="url(#arw)"/>')
    a(f'<text x="{SPINE_X + SPINE_W / 2 + 16}" y="{ORDER_Y - 10}" font-family="{MONO}" '
      f'font-size="10" letter-spacing="1" fill="{LINE}">'
      f'PICK ONE, ONCE &#183; BOTH REACH THE SAME SECTIONS</text>')

    for a_id, b_id in EDGES:
        a(connector(a_id, b_id, dashed=False))
    for a_id, b_id, corridor in ASIDES:
        a(connector(a_id, b_id, dashed=True, corridor=corridor))

    for sid, title, lane, flag in SECTIONS:
        x, y, w, h = POS[sid]
        fill = SPINE_FILL if lane == "spine" else NODE

        a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
          f'fill="{fill}" stroke="{INK}" stroke-width="1.6"/>')

        # RULE 2: this <text> must stay immediately after the <rect> above.
        ty = (y + 32) if flag else (y + h / 2 + 5)
        a(f'<text x="{x + 16}" y="{ty}" font-family="{MONO}" font-size="13" '
          f'font-weight="600" fill="{ACCENT}">{esc(sid)}</text>')
        a(f'<text x="{x + 58}" y="{ty}" font-size="16" font-weight="600" '
          f'fill="{INK}">{esc(title)}</text>')

        if flag:
            a(flagship_stamp(x + w - 104, y + h - 12))

    x5, y5, w5, h5 = POS["§5"]
    a(f'<text x="{x5 + 16}" y="{y5 + h5 + 22}" font-size="12" fill="{LINE}">'
      f'deployment-facing &#183; runs alongside</text>')
    x9, y9, w9, h9 = POS["§9"]
    a(f'<text x="{x9 + 16}" y="{y9 + h9 + 22}" font-size="12" fill="{LINE}">'
      f'read any time after &#167;6</text>')
    # Under the node, not beside it: the §9 corridor arrives on that right edge.
    x10, y10, w10, h10 = POS["§10"]
    a(f'<text x="{x10 + 16}" y="{y10 + h10 + 22}" font-size="12" fill="{LINE}">'
      f'or fork out, honestly &#8212; that exit is in the README too</text>')

    # legend
    ly = H - 26
    a(f'<line x1="{SPINE_X}" y1="{ly - 24}" x2="{W - 40}" y2="{ly - 24}" '
      f'stroke="{LINE}" stroke-width="1" opacity="0.4"/>')
    a(f'<line x1="{SPINE_X}" y1="{ly - 4}" x2="{SPINE_X + 26}" y2="{ly - 4}" '
      f'stroke="{LINE}" stroke-width="1.8" marker-end="url(#arw)"/>')
    a(f'<text x="{SPINE_X + 36}" y="{ly}" font-size="12" fill="{LINE}">attack order</text>')
    a(f'<line x1="{SPINE_X + 156}" y1="{ly - 4}" x2="{SPINE_X + 182}" y2="{ly - 4}" '
      f'stroke="{LINE}" stroke-width="1.8" stroke-dasharray="5 4" marker-end="url(#arw)"/>')
    a(f'<text x="{SPINE_X + 192}" y="{ly}" font-size="12" fill="{LINE}">'
      f'alongside &#183; your timing</text>')
    a(flagship_stamp(SPINE_X + 380, ly + 2))
    # "break" would overclaim: the README says a flagship is "the famous, hard
    # breaks (plus the one precision milestone that most sets this map apart)"
    # — and M9.1, reading the NIST source, is that precision milestone, not a
    # break. "Flagship milestone" is the README's own term and covers all four.
    a(f'<text x="{SPINE_X + 484}" y="{ly}" font-size="12" fill="{LINE}">'
      f'section with a flagship milestone</text>')

    a("</svg>")
    return "\n".join(p) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if committed SVG differs from freshly rendered")
    args = ap.parse_args()

    out = Path(__file__).resolve().parent.parent / "assets" / "roadmap.svg"
    svg = build()

    if args.check:
        if not out.exists() or out.read_text(encoding="utf-8") != svg:
            print("roadmap.svg is stale — run: python scripts/render_map.py", file=sys.stderr)
            return 1
        print("roadmap.svg up to date.")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n" is explicit: on Windows the default translates every "\n" to
    # "\r\n", so the file stops matching the blob and every line of the map
    # shows up as changed. .gitattributes pins the same thing from git's side.
    out.write_text(svg, encoding="utf-8", newline="\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
