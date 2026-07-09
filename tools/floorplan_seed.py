#!/usr/bin/env python3
"""
floorplan_seed.py — seed initial footprint positions in layout/layout.kicad_pcb,
clustered by module block, per docs/board_floorplan.md "Concrete floorplan v1".

The `pcb layout` auto-pack jumbles all 136 footprints together with no
human-readable module tag (each KiCad `sheetname` is a bare UUID), so you can't
tell which part belongs to which block. This reads the real hierarchy from the
netlist (`layout/default.net`, `sheetpath names = MODULE.instance.part`), then
moves each footprint into its block's target region so the blocks are visually
separated. Zener preserves manual placement across regen, so run this once after
a fresh `pcb layout ... --no-open`; re-run only if a regen re-packs.

Coordinate frame here = KiCad native: origin top-left, +x right, +y DOWN, mm.
Board rectangle = (0,0)..(152.4, 69.85). The floorplan doc uses a bottom-left
y-up frame; this file is its y-flipped twin (ky = 69.85 - fy).

Blocks & regions (KiCad mm):
  CPU  (Apple bus, 72)  top strip           J1 2x20 header on the top edge
  SOM  (3 connectors)   middle, real DF40 geometry from som_placement.md
  PWR  (18)             left end (barrel)
  USB3 (CH569, 16)      right-mid (nests in the C's mouth)
  PROG (FT2232, 16)     right end
  SDRAM UHI/ULO (5+5)   flanking C2399 (top) / C2400 (bottom)
  MECH (slot J2)        bottom edge
"""
import re, sys, uuid, math, os

PCB = os.path.join(os.path.dirname(__file__), "..", "layout", "layout.kicad_pcb")
NET = os.path.join(os.path.dirname(__file__), "..", "layout", "default.net")
BW, BH = 152.4, 69.85          # card BODY width x height (mm); tab protrudes below BH
# Finger-tab geometry (from the AppleIIBus_Edge footprint's own Edge.Cuts, confirmed
# against the prior board): tab half-width, and the local +y of the tab TOP (where it
# meets the body) — the footprint origin sits at body_bottom + TAB_TOP so its tab-top
# line lands exactly on the body bottom edge. Tab is centred at TAB_X along the bottom.
TAB_HALF = 32.385
TAB_TOP = 3.175
TAB_X = 76.2                    # tab centre (board centre); = chosen slot's X at integration

# --- SOM datum + connector geometry (som_placement.md; frame +x right, +y down,
#     datum = hole-rect centre). Datum placed at KiCad (55, 34.925 = BH/2). ---
DATUM = (55.0, BH / 2)
SOM_CONN = {                    # refdes -> (dx,dy) body-centre offset from datum
    "CN1": (-19.85,  0.00),     # BTB9900 (left, vertical)
    "CN2": ( -6.47, -14.67),    # C2399   (top,  horizontal)
    "CN3": ( -6.47, +14.74),    # C2400   (bottom, horizontal)
}
# Special single-part placements (refdes -> (x, y[, rot])); rot None = keep.
SPECIAL = {
    "J1": (76.0, 4.5, 0.0),     # 2x20 CPU header, top edge, spans x 50.6..101.4
    "J2": (TAB_X, BH + TAB_TOP, 0.0),   # slot: tab-top lands on body bottom edge; tab protrudes below
}
# Grid regions per block: (x0, y0, x1, y1) in KiCad mm. Boxes are NON-OVERLAPPING
# so blocks never bleed into each other; parts are fit strictly inside each box
# (bigs = U/Q/D/L/Y/J/CN in a top row, passives packed below). CPU stays above
# Y19 so it clears the SOM (Y20-49) + SDRAM center.
REGIONS = {
    "CPU":       (30.0, 3.0, 147.0, 19.0),   # top strip (minus J1, placed special)
    "PWR":       (4.0, 22.0, 29.0, 56.0),    # left end (barrel)
    "SDRAM_UHI": (62.0, 21.0, 85.0, 33.0),   # flanks C2399 (top)
    "SDRAM_ULO": (62.0, 40.0, 85.0, 54.0),   # flanks C2400 (bottom)
    "USB3":      (90.0, 23.0, 121.0, 53.0),  # nests in the C's mouth
    "PROG":      (123.0, 34.0, 150.0, 61.0), # right end
}
BIG = re.compile(r"^(U|Q|D|L|Y|J|CN|SW|K)\d")


def load_hierarchy():
    t = open(NET, encoding="utf-8", errors="replace").read()
    ref2blk = {}
    for m in re.finditer(r'\(comp \(ref "([^"]+)"\).*?\(sheetpath \(names "([^"]*)"', t, re.S):
        ref, path = m.group(1), m.group(2)
        top = path.split(".")[0]
        if top == "SDRAM":
            top = "SDRAM_UHI" if ".UHI" in path or "_UHI" in path else \
                  ("SDRAM_ULO" if ".ULO" in path or "_ULO" in path else "SDRAM_UHI")
        ref2blk[ref] = top
    return ref2blk


def _grid(refs, x0, y0, x1, y1):
    """Fit refs strictly inside the box, packing rows to match its aspect."""
    n = len(refs)
    if not n:
        return {}
    W, H = max(x1 - x0, 1.0), max(y1 - y0, 1.0)
    cols = max(1, min(n, round((n * W / H) ** 0.5)))
    rows = int(math.ceil(n / cols))
    px, py = W / cols, H / rows
    return {r: (x0 + px * (i % cols + 0.5), y0 + py * (i // cols + 0.5))
            for i, r in enumerate(refs)}


def grid_positions(refs, region):
    """Big parts (ICs/connectors) in a top row; passives packed in the box below.
    Everything stays strictly inside `region` so blocks never overlap."""
    x0, y0, x1, y1 = region
    bigs = sorted([r for r in refs if BIG.match(r)])
    small = sorted([r for r in refs if not BIG.match(r)])
    pos = {}
    big_h = 0.0
    if bigs:
        bcols = max(1, min(len(bigs), int((x1 - x0) // 11) or 1))
        brows = int(math.ceil(len(bigs) / bcols))
        big_h = min(brows * 8.0, (y1 - y0) * 0.5)
        pos.update(_grid(bigs, x0, y0, x1, y0 + big_h))
    pos.update(_grid(small, x0, y0 + big_h + (1.0 if bigs else 0.0), x1, y1))
    return pos


def compute_all():
    ref2blk = load_hierarchy()
    byblk = {}
    for r, b in ref2blk.items():
        byblk.setdefault(b, []).append(r)
    pos = {}
    # SOM connectors — real geometry
    for r, (dx, dy) in SOM_CONN.items():
        pos[r] = (DATUM[0] + dx, DATUM[1] + dy, None)
    # specials
    for r, v in SPECIAL.items():
        pos[r] = v
    # gridded blocks
    for blk, region in REGIONS.items():
        refs = [r for r in byblk.get(blk, []) if r not in pos]
        for r, (x, y) in grid_positions(refs, region).items():
            pos[r] = (x, y, None)
    return pos, ref2blk


def apply(pos, move=True):
    t = open(PCB, encoding="utf-8", errors="replace").read()
    chunks = t.split("(footprint ")
    out = [chunks[0]]
    n = 0
    for ch in chunks[1:]:
        mref = re.search(r'\(property "Reference" "([^"]+)"', ch)
        ref = mref.group(1) if mref else None
        if move and ref in pos:
            x, y, rot = pos[ref]
            def repl(m, x=x, y=y, rot=rot):
                keep = m.group(3)
                r = rot if rot is not None else (keep if keep else None)
                return f"(at {x:.3f} {y:.3f}" + (f" {r})" if r not in (None, "") else ")")
            ch, k = re.subn(r'\(at (-?\d[\d.]*) (-?\d[\d.]*)(?: (-?\d[\d.]*))?\)', repl, ch, count=1)
            n += k
        out.append("(footprint " + ch)
    t = "".join(out)
    # Board outline on Edge.Cuts: full top/left/right edges + a bottom edge SPLIT to
    # leave a gap for the finger tab (the AppleIIBus_Edge footprint draws the tab's
    # sides/chamfers/insertion edge itself, protruding below the body). Idempotent:
    # strip any prior board-level Edge.Cuts gr_line lying on the body perimeter first.
    e = 0.01
    def _on_perim(x, y):
        return abs(x) < e or abs(x - BW) < e or abs(y) < e or abs(y - BH) < e
    def _strip(m):
        pts = [(float(m.group(1)), float(m.group(2))), (float(m.group(3)), float(m.group(4)))]
        return "" if all(_on_perim(*p) for p in pts) else m.group(0)
    t = re.sub(r'\(gr_line \(start (\S+) (\S+)\) \(end (\S+) (\S+)\)'
               r'[^\n]*Edge\.Cuts[^\n]*\)\n?', _strip, t)
    tl, tr = TAB_X - TAB_HALF, TAB_X + TAB_HALF     # tab gap in the body bottom edge
    segs = [((0, 0), (BW, 0)),        # top
            ((BW, 0), (BW, BH)),      # right
            ((BW, BH), (tr, BH)),     # bottom-right (up to tab)
            ((tl, BH), (0, BH)),      # bottom-left  (tab gap between tl..tr)
            ((0, BH), (0, 0))]        # left
    lines = ""
    for (ax, ay), (bx, by) in segs:
        lines += (f'\n\t(gr_line (start {ax} {ay}) (end {bx} {by}) '
                  f'(stroke (width 0.12) (type default)) (layer "Edge.Cuts") '
                  f'(uuid "{uuid.uuid4()}"))')
    t = t.rstrip()
    assert t.endswith(")"), "unexpected pcb tail"
    t = t[:-1] + lines + "\n)\n"
    open(PCB, "w", encoding="utf-8").write(t)
    return n


if __name__ == "__main__":
    # --outline-only: just (re)draw the board rectangle, don't touch any part
    # positions (use after a sync regen has wiped the outline but you've already
    # arranged parts by hand in KiCad — a full run would reset them to the grid).
    outline_only = "--outline-only" in sys.argv[1:]
    if outline_only:
        apply({}, move=False)
        print("re-added board outline rectangle 152.4 x 69.85 mm (positions untouched)")
    else:
        pos, ref2blk = compute_all()
        moved = apply(pos, move=True)
        from collections import Counter
        c = Counter(ref2blk.values())
        print(f"placed {moved} footprints across {len(c)} blocks:")
        for b, n in sorted(c.items(), key=lambda kv: -kv[1]):
            print(f"  {b:12} {n}")
        print("+ board outline rectangle 152.4 x 69.85 mm on Edge.Cuts")
