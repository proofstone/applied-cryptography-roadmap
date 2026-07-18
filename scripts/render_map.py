#!/usr/bin/env python3
"""Deterministic SVG renderer for the roadmap path map.

The map is data, not a drawing: edit SECTIONS / EDGES below and re-run to
regenerate assets/roadmap.svg. No external dependencies, no randomness, no
timestamps — the same input always produces byte-identical output, so the
committed SVG and this script never drift.

    python scripts/render_map.py            # writes assets/roadmap.svg
    python scripts/render_map.py --check    # exit 1 if the SVG is stale
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# --- data -------------------------------------------------------------------
# Each section is (id, title, track). `track` picks the accent color.
# ⭐ in a title marks a section that contains a flagship milestone.
SECTIONS = [
    ("§0", "Orientation", "spine"),
    ("§1", "Symmetric: XOR, ECB, CBC", "symmetric"),
    ("§2", "The padding oracle ⭐", "attack"),
    ("§3", "Randomness that isn't", "symmetric"),
    ("§4", "Hashes & length extension ⭐", "symmetric"),
    ("§5", "Keys, passwords, mgmt", "ops"),
    ("§6", "Public key: RSA/DSA/DH ⭐", "pubkey"),
    ("§7", "Elliptic curves", "pubkey"),
    ("§8", "Crypto on the web", "web"),
    ("§9", "Post-quantum ⭐", "pqc"),
    ("§10", "The honest ceiling", "spine"),
]

# Directed edges by section id (drawn as connectors down the spine).
EDGES = [
    ("§0", "§1"), ("§1", "§2"), ("§2", "§3"), ("§3", "§4"),
    ("§4", "§6"), ("§6", "§7"), ("§7", "§8"), ("§8", "§10"),
    ("§6", "§9"),
]

TRACK_FILL = {
    "spine": "#e8eef7",
    "symmetric": "#dcefe4",
    "attack": "#f7dfe0",
    "ops": "#efe7da",
    "pubkey": "#e9e3f5",
    "web": "#dce9f5",
    "pqc": "#fde8c8",
}
TRACK_STROKE = {
    "spine": "#5b7aa8",
    "symmetric": "#4f9b74",
    "attack": "#c15862",
    "ops": "#9c7a3e",
    "pubkey": "#7a5fb0",
    "web": "#3d7bb5",
    "pqc": "#d08a2e",
}
TEXT = "#1b2430"
MUTED = "#5a6472"

# --- layout -----------------------------------------------------------------
BOX_W, BOX_H = 280, 52
V_GAP = 32
LEFT = 60
TOP = 116
WIDTH = 780
FONT = "-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build() -> str:
    n = len(SECTIONS)
    height = TOP + n * (BOX_H + V_GAP) + 40
    ypos = {sid: TOP + i * (BOX_H + V_GAP) for i, (sid, _, _) in enumerate(SECTIONS)}
    box_x = LEFT
    cx = box_x + BOX_W // 2

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
        f'width="{WIDTH}" height="{height}" font-family="{FONT}" '
        f'role="img" aria-label="Applied cryptography roadmap path map">'
    )
    parts.append(f'<rect width="{WIDTH}" height="{height}" fill="none"/>')

    # arrow marker
    parts.append(
        f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{MUTED}"/></marker></defs>'
    )

    # title
    parts.append(
        f'<text x="{LEFT}" y="42" font-size="21" font-weight="700" '
        f'fill="{TEXT}">Working engineer → shipping cryptography safely</text>'
    )
    parts.append(
        f'<text x="{LEFT}" y="66" font-size="13" fill="{MUTED}">'
        f'Every node is a milestone with a pass/fail flag. ⭐ = flagship break. '
        f'🔀 = fork. Spine = OWASP A04 checklist.</text>'
    )

    # order fork above §0/§1
    parts.append(
        f'<text x="{LEFT}" y="94" font-size="12" fill="{TRACK_STROKE["pubkey"]}" '
        f'font-weight="600">🔀 Pick your order: A = Cryptopals-first · '
        f'B = CryptoHack-first — both merge into §1.</text>'
    )

    # edges first (behind boxes)
    for a, b in EDGES:
        if b == "§9" and a == "§6":
            # side branch: curve out to the right to §9
            xr = box_x + BOX_W + 40
            parts.append(
                f'<path d="M {box_x + BOX_W} {ypos[a] + BOX_H // 2} '
                f'C {xr} {ypos[a] + BOX_H // 2}, {xr} {ypos[b] + BOX_H // 2}, '
                f'{box_x + BOX_W} {ypos[b] + BOX_H // 2}" '
                f'fill="none" stroke="{MUTED}" stroke-width="1.6" '
                f'stroke-dasharray="5 4" marker-end="url(#arrow)"/>'
            )
        else:
            parts.append(
                f'<line x1="{cx}" y1="{ypos[a] + BOX_H}" x2="{cx}" y2="{ypos[b]}" '
                f'stroke="{MUTED}" stroke-width="1.8" marker-end="url(#arrow)"/>'
            )

    # §5 sidebar note (deployment-facing, runs alongside)
    y5 = ypos["§5"]
    parts.append(
        f'<text x="{box_x + BOX_W + 24}" y="{y5 + BOX_H // 2 + 4}" font-size="12" '
        f'fill="{MUTED}">deployment-facing · runs alongside</text>'
    )

    # §9 differentiator note
    y9 = ypos["§9"]
    parts.append(
        f'<text x="{box_x + BOX_W + 24}" y="{y9 + BOX_H // 2 - 4}" font-size="12" '
        f'fill="{TRACK_STROKE["pqc"]}" font-weight="600">read anytime after §6</text>'
    )
    parts.append(
        f'<text x="{box_x + BOX_W + 24}" y="{y9 + BOX_H // 2 + 12}" font-size="12" '
        f'fill="{MUTED}">precision: read NIST, not the blogs</text>'
    )

    # §10 fork-out annotation
    y10 = ypos["§10"]
    parts.append(
        f'<text x="{box_x + BOX_W + 24}" y="{y10 + BOX_H // 2 + 4}" font-size="12" '
        f'fill="{TRACK_STROKE["spine"]}" font-weight="600">🔀 design fork → Ph.D. (Kamara)</text>'
    )

    # boxes
    for sid, title, track in SECTIONS:
        y = ypos[sid]
        parts.append(
            f'<rect x="{box_x}" y="{y}" width="{BOX_W}" height="{BOX_H}" rx="10" '
            f'fill="{TRACK_FILL[track]}" stroke="{TRACK_STROKE[track]}" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{box_x + 16}" y="{y + 32}" font-size="15" font-weight="700" '
            f'fill="{TRACK_STROKE[track]}">{esc(sid)}</text>'
        )
        parts.append(
            f'<text x="{box_x + 62}" y="{y + 32}" font-size="14" font-weight="600" '
            f'fill="{TEXT}">{esc(title)}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


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
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
