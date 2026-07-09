#!/usr/bin/env python3
"""
floorplan_seed.py — sort layout/layout.kicad_pcb footprints into labeled,
non-overlapping per-block STAGING TRAYS so you can see what belongs to which
block and drag each cluster onto the board.

Why trays, not final positions: `pcb layout` auto-packs all 136 footprints into
one pile with no human-readable module tag (each KiCad `sheetname` is a bare
UUID). And 136 *real* footprints (a 52 mm header, 8 mm ICs, 23 mm DF40s, dozens
of 0402s) simply do not fit legibly at their floorplan positions on a 152x70 mm
board — packed that tight the bodies overlap into mush. So this instead lays each
block out as a tidy, correctly-spaced cluster (spacing from each footprint's real
bounding box) in a labeled tray BELOW the board, ordered along the power<->USB
spine. You then drag each recognizable, labeled cluster onto the board. The
intended floorplan positions live in docs/board_floorplan.md "Concrete floorplan v1".

Also draws the board outline + finger tab (body = 152.4x69.85 mm rectangle; the
2.55" tab protrudes ~7.5 mm below, the AppleIIBus_Edge slot J2 filling a gap in
the bottom edge). Coordinate frame = KiCad native (origin top-left, +y DOWN, mm).

Regen note (pcb v0.4.5): a *sync* regen (plain `pcb layout`) preserves footprint
positions but WIPES board graphics (outline + these labels). Open the seeded board
with `pcb layout appletini_mega.zen --no-sync`. After a sync, restore just the
outline with `--outline-only` (positions untouched); re-run the full tool only for
the initial sort (it resets positions to the trays).
"""
import re, sys, uuid, os
from collections import defaultdict

PCB = os.path.join(os.path.dirname(__file__), "..", "layout", "layout.kicad_pcb")
NET = os.path.join(os.path.dirname(__file__), "..", "layout", "default.net")
BW, BH = 152.4, 69.85           # card BODY rectangle (mm); tab protrudes below BH
TAB_HALF, TAB_TOP = 32.385, 3.175       # finger-tab half-width + top offset (from footprint)
TAB_EDGE_GAP = 9.525                    # 0.375" from the tab's RIGHT edge to the card's right edge
TAB_X = BW - TAB_EDGE_GAP - TAB_HALF     # tab centre -> right side of the card (= 110.49 mm)

# Blocks in power<->USB spine order, with the label drawn over each tray.
BLOCKS = [
    ("PWR",       "POWER  (barrel / MP2315 / AMS1117)"),
    ("SDRAM_UHI", "SDRAM0  (-> C2399)"),
    ("SDRAM_ULO", "SDRAM1  (-> C2400)"),
    ("SOM",       "SOM DF40 connectors  (CN1=BTB9900 CN2=C2399 CN3=C2400)"),
    ("USB3",      "USB3 / CH569  (+30MHz xtal)"),
    ("PROG",      "FT2232  (JTAG + UART)"),
    ("CPU",       "APPLE BUS  (level shifters + 2x20 header + deadman)"),
]
WMAX = {"CPU": 130.0, "SOM": 80.0}      # per-block max row width when packing a tray
TRAY_TOP = 92.0                          # trays start below the board+tab
TRAY_GAP = 10.0                          # vertical gap between trays
PAD = 2.0                                # gap between parts within a tray


def iter_fp(t):
    """Yield (start, end, block_text) for each footprint via paren matching."""
    i = 0
    while True:
        j = t.find("(footprint ", i)
        if j < 0:
            break
        d, k = 0, j
        while k < len(t):
            if t[k] == "(":
                d += 1
            elif t[k] == ")":
                d -= 1
                if d == 0:
                    break
            k += 1
        yield j, k + 1, t[j:k + 1]
        i = k + 1


def fp_ref(blk):
    m = re.search(r'\(property "Reference" "([^"]+)"', blk)
    return m.group(1) if m else None


def fp_rot(blk):
    m = re.search(r'\(at\s+-?\d[\d.]*\s+-?\d[\d.]*\s+(-?\d[\d.]*)\)', blk)
    return float(m.group(1)) if m else 0.0


def fp_size(blk):
    """(w, h) of the footprint incl rotation, from pads + graphic points."""
    pts = []
    for m in re.finditer(r'\(pad\s+"[^"]*"\s+\S+\s+\S+\s*\(at\s+(-?\d[\d.]*)\s+(-?\d[\d.]*)'
                         r'(?:\s+-?\d[\d.]*)?\)\s*\(size\s+(-?\d[\d.]*)\s+(-?\d[\d.]*)\)', blk, re.S):
        x, y, w, h = map(float, m.groups())
        pts += [(x - w / 2, y - h / 2), (x + w / 2, y + h / 2)]
    for m in re.finditer(r'\((?:start|end|center|xy)\s+(-?\d[\d.]*)\s+(-?\d[\d.]*)\)', blk):
        pts.append((float(m.group(1)), float(m.group(2))))
    if not pts:
        return 3.0, 3.0
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    return (h, w) if round(fp_rot(blk)) % 180 == 90 else (w, h)


def load_blocks():
    t = open(NET, encoding="utf-8", errors="replace").read()
    byblk = defaultdict(list)
    for m in re.finditer(r'\(comp \(ref "([^"]+)"\).*?\(sheetpath \(names "([^"]*)"', t, re.S):
        ref, path = m.group(1), m.group(2)
        top = path.split(".")[0]
        if top == "SDRAM":
            top = "SDRAM_ULO" if ("ULO" in path) else "SDRAM_UHI"
        byblk[top].append(ref)
    return byblk


def pack_tray(refs, sizes, wmax):
    """Row-pack refs into a cluster; return {ref:(dx,dy)} centres + (w,h)."""
    order = sorted(refs, key=lambda r: -sizes[r][1])     # tall first
    pos = {}
    cx = cy = rowh = tw = 0.0
    for r in order:
        w, h = sizes[r]
        if cx > 0 and cx + w > wmax:
            cy += rowh + PAD
            cx = rowh = 0.0
        pos[r] = (cx + w / 2, cy + h / 2)
        cx += w + PAD
        rowh = max(rowh, h)
        tw = max(tw, cx - PAD)
    return pos, tw, cy + rowh


def compute():
    t = open(PCB, encoding="utf-8", errors="replace").read()
    sizes = {fp_ref(b): fp_size(b) for _, _, b in iter_fp(t) if fp_ref(b)}
    byblk = load_blocks()
    place = {}
    labels = []            # (x, y, text)
    # SOM connectors keep real DF40 geometry on the board (they anchor the SOM)
    for r, (dx, dy) in {"CN1": (-19.85, 0), "CN2": (-6.47, -14.67), "CN3": (-6.47, 14.74)}.items():
        place[r] = (55.0 + dx, BH / 2 + dy)
    place["J2"] = (TAB_X, BH + TAB_TOP)          # slot: forms the tab in the outline
    labels.append((30.0, 12.0, "SOM DF40 connectors (on board): CN1=BTB9900 CN2=C2399 CN3=C2400"))
    labels.append((TAB_X - 24, BH - 2, "slot finger tab (mechanical)"))
    # everything else -> labeled trays below the board
    y = TRAY_TOP
    for key, text in BLOCKS:
        refs = [r for r in byblk.get(key, []) if r not in place]
        if not refs:
            continue
        pos, tw, th = pack_tray(refs, sizes, WMAX.get(key, 62.0))
        labels.append((0.0, y - 2.0, text))
        for r, (dx, dy) in pos.items():
            place[r] = (dx, y + dy)
        y += th + TRAY_GAP
    return place, labels


def drop_blocks(t, opener, cond):
    """Remove every paren-block starting with `opener` for which cond(block) is True."""
    out, i = [], 0
    while True:
        j = t.find(opener, i)
        if j < 0:
            out.append(t[i:]); break
        out.append(t[i:j])
        d, k = 0, j
        while k < len(t):
            if t[k] == "(":
                d += 1
            elif t[k] == ")":
                d -= 1
                if d == 0:
                    break
            k += 1
        blk = t[j:k + 1]
        i = k + 1
        if cond(blk):
            while i < len(t) and t[i] in " \t\r\n":
                i += 1
        else:
            out.append(blk)
    return "".join(out)


def outline_and_labels(t, labels):
    # strip our prior board graphics: perimeter Edge.Cuts gr_lines + Cmts.User labels
    e = 0.01
    def on_perim(x, y):
        return abs(x) < e or abs(x - BW) < e or abs(y) < e or abs(y - BH) < e
    def strip_edge(m):
        p = [(float(m.group(1)), float(m.group(2))), (float(m.group(3)), float(m.group(4)))]
        return "" if all(on_perim(*q) for q in p) else m.group(0)
    t = re.sub(r'\(gr_line \(start (\S+) (\S+)\) \(end (\S+) (\S+)\)[^\n]*Edge\.Cuts[^\n]*\)\n?',
               strip_edge, t)
    t = drop_blocks(t, "(gr_text", lambda b: 'layer "Cmts.User"' in b)
    # board outline: full top/left/right + bottom edge split around the tab gap
    tl, tr = TAB_X - TAB_HALF, TAB_X + TAB_HALF
    segs = [((0, 0), (BW, 0)), ((BW, 0), (BW, BH)), ((BW, BH), (tr, BH)),
            ((tl, BH), (0, BH)), ((0, BH), (0, 0))]
    add = ""
    for (ax, ay), (bx, by) in segs:
        add += (f'\n\t(gr_line (start {ax} {ay}) (end {bx} {by}) (stroke (width 0.12) '
                f'(type default)) (layer "Edge.Cuts") (uuid "{uuid.uuid4()}"))')
    for x, y, text in labels:
        add += (f'\n\t(gr_text "{text}" (at {x:.2f} {y:.2f}) (layer "Cmts.User") '
                f'(uuid "{uuid.uuid4()}") (effects (font (size 3 3) (thickness 0.5)) '
                f'(justify left bottom)))')
    t = t.rstrip()
    assert t.endswith(")"), "unexpected pcb tail"
    return t[:-1] + add + "\n)\n"


def run(move=True):
    place, labels = compute() if move else ({}, [])
    t = open(PCB, encoding="utf-8", errors="replace").read()
    if move:
        out, last, n = [], 0, 0
        for a, b, blk in iter_fp(t):
            out.append(t[last:a])
            ref = fp_ref(blk)
            if ref in place:
                x, y = place[ref]
                blk, k = re.subn(r'\(at (-?\d[\d.]*) (-?\d[\d.]*)((?: -?\d[\d.]*)?)\)',
                                 lambda m: f"(at {x:.3f} {y:.3f}{m.group(3)})", blk, count=1)
                n += k
            out.append(blk); last = b
        out.append(t[last:])
        t = "".join(out)
    t = outline_and_labels(t, labels)
    open(PCB, "w", encoding="utf-8").write(t)
    return len(place), labels


if __name__ == "__main__":
    if "--outline-only" in sys.argv[1:]:
        run(move=False)
        print("re-added board outline + tab (positions & labels untouched)")
    else:
        n, labels = run(move=True)
        print(f"sorted {n} footprints into {len(labels)} labeled trays + board outline/tab:")
        for _, _, text in labels:
            print(f"  • {text}")
        print("  (SOM DF40s + slot J2 left at their board positions)")
