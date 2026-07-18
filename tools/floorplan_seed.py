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
intended floorplan positions live in docs/board_floorplan.md "Concrete floorplan v2"
(SOM centered; the on-board SOM anchor here uses SOM_DATUM_X = board centre).

Also draws the board outline + finger tab (body = 152.4x69.85 mm rectangle with a
38.1x12.7 mm notch cut from the upper-right corner; the 2.55" tab protrudes ~7.5 mm
below, the AppleIIBus_Edge slot J2 filling a gap in the bottom edge). Coordinate
frame = KiCad native (origin top-left, +y DOWN, mm); the whole board is shifted by
ORIGIN so the body rectangle is centred on the A4-landscape sheet.

Backporting hand placement (group membership = "not yet placed"):
The Zener sync groups all parts by schematic sheet. Those KiCad groups double as the
"un-placed / staging" flag: to place a part you drag its tray onto the board and remove
it from its group ("Remove from Group" in KiCad) — so ungrouped == placed. When you're
happy, run `floorplan_seed.py --capture`: it snapshots every UNGROUPED footprint's
position/rotation into placements.json in the repo root (BOARD frame = absolute minus
ORIGIN) — repo root, not layout/, so wiping layout/ for a fresh sync keeps your placement.
Thereafter a plain `floorplan_seed.py` run applies those overrides instead of the trays
(placements.json is the source of truth for placed parts) AND removes the placed parts
from their groups, so "ungrouped == placed" survives the next sync. Un-captured parts
stay grouped in their trays; a newly-added schematic part shows up grouped in a tray.
To un-place a part, add it back to a group (or delete its placements.json entry).

Regen note (pcb v0.4.5): a *sync* regen (plain `pcb layout`) preserves footprint
positions but WIPES board graphics (outline + labels) and RE-GROUPS every part. Open the
seeded board with `pcb layout appletini_mega.zen --no-sync`. After a sync, run a plain
`floorplan_seed.py` FIRST to restore the outline + captured positions + re-ungroup placed
parts (do this before --capture, or the guard will refuse). `--outline-only` redraws just
the outline (footprints untouched).
"""
import re, sys, uuid, os, json, math
from collections import defaultdict

PCB = os.path.join(os.path.dirname(__file__), "..", "layout", "layout.kicad_pcb")
NET = os.path.join(os.path.dirname(__file__), "..", "layout", "default.net")
# Hand-tuned placement overrides captured from KiCad (--capture); see load_placements.
# Lives in the REPO ROOT (not layout/) so `rm -rf layout` for a fresh sync keeps it.
PLACE = os.path.join(os.path.dirname(__file__), "..", "placements.json")
BW, BH = 152.4, 69.85           # card BODY rectangle (mm); tab protrudes below BH
NOTCH_W, NOTCH_H = 38.1, 12.7    # rectangular notch removed from the UPPER-RIGHT corner
NOTCH_X = BW - NOTCH_W           # inner (left) x of the notch = 114.3 mm

# Board placement on the KiCad sheet. paper "A4" in layout.kicad_pcb = A4 LANDSCAPE
# (297 x 210 mm). ORIGIN shifts the whole board frame so the body rectangle is centred
# on the sheet; every generated coord (footprints, outline, labels) is emitted at
# board-frame + ORIGIN, so this is the single source of truth for where the board sits.
PAGE_W, PAGE_H = 297.0, 210.0
ORIGIN_X = round((PAGE_W - BW) / 2, 4)   # 72.3   -> body centred horizontally
ORIGIN_Y = round((PAGE_H - BH) / 2, 4)   # 70.075 -> body centred vertically
SOM_DATUM_X = BW / 2            # floorplan-v2: SOM CENTERED (was 55.0, left-of-centre in v1)
TAB_HALF, TAB_TOP = 32.385, 3.175       # finger-tab half-width + top offset (from footprint)
TAB_EDGE_GAP = 9.525                    # 0.375" from the tab's RIGHT edge to the card's right edge
TAB_X = BW - TAB_EDGE_GAP - TAB_HALF     # tab centre -> right side of the card (= 110.49 mm)

# Blocks in power<->USB spine order, with the label drawn over each tray.
BLOCKS = [
    ("PWR",       "POWER  (barrel + 2x MPM3620A buck: 5V / 3.3V)"),
    ("SDRAM_ULO", "SDRAM0 = U_LO / DQ[15:0]  (-> C2399, top)"),
    ("SDRAM_UHI", "SDRAM1 = U_HI / DQ[31:16] (-> C2400, bottom)"),
    ("SOM",       "SOM DF40 connectors  (CN1=BTB9900 CN2=C2399 CN3=C2400)"),
    ("USB3",      "USB3 / CH569  (+30MHz xtal)"),
    ("PROG",      "FT2232  (JTAG + UART)"),
    ("CPU",       "APPLE BUS  (level shifters + J_CPU FFC + deadman)"),
]
WMAX = {"CPU": 130.0, "SOM": 80.0}      # per-block max row width when packing a tray
TRAY_TOP = 92.0                          # trays start below the board+tab
TRAY_GAP = 10.0                          # vertical gap between trays
PAD = 2.0                                # gap between parts within a tray

# POWER block placed ON the board under the notch (see place_power): the barrel jack anchors
# on the notch's short side so its DC cable clears via the notch; the rail parts are
# CONSTRUCTIVELY clustered around the buck (tight hot loop, small feedback loop), with the
# input-protection chain feeding in from the jack side and the LDO downstream. Board frame.
PWR_LEFT, PWR_TOP = 98.0, 16.0   # board-frame left/top edge of the clustered block
PWR_CLEAR = 0.5                  # body-to-body gap when nudging parts apart (mm)
# MPM3620A (QFN20) key pin LOCAL positions by role, from its .kicad_mod pads. Each rail's
# passives are placed at these pins. Regenerate if the module footprint changes.
MODULE_PINS = {"IN": (-0.27, -1.65), "OUT": (1.23, 1.85), "FB": (-1.43, -0.95), "EN": (-0.78, -1.85)}


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


def fp_uuid(blk):
    # the footprint's OWN uuid = the first (uuid ...) in the block (before any pad /
    # property uuid); this is what KiCad group (members ...) lists reference.
    m = re.search(r'\(uuid "([0-9a-f-]{36})"', blk)
    return m.group(1) if m else None


def fp_name(blk):
    # library footprint name (after the "lib:" nickname), e.g. "POWER-JACK".
    m = re.match(r'\(footprint "([^"]+)"', blk)
    return m.group(1).split(":")[-1] if m else ""


def iter_groups(t):
    """Yield (start, end, block, members_span) for each top-level (group ...). members_span
    is the (i,j) slice of the block covering its (members ...) sub-block, or None."""
    i = 0
    while True:
        j = t.find("(group ", i)
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
        blk = t[j:k + 1]
        mj = blk.find("(members")
        span = None
        if mj >= 0:
            md, mk = 0, mj
            while mk < len(blk):
                if blk[mk] == "(":
                    md += 1
                elif blk[mk] == ")":
                    md -= 1
                    if md == 0:
                        break
                mk += 1
            span = (mj, mk + 1)
        yield j, k + 1, blk, span
        i = k + 1


def grouped_uuids(t):
    """Set of footprint uuids that are a member of some KiCad group."""
    uu = set()
    for _, _, blk, span in iter_groups(t):
        if span:
            uu.update(re.findall(r'"([0-9a-f-]{36})"', blk[span[0]:span[1]]))
    return uu


def translate_zone_pts(blk, dx, dy):
    """Translate every (xy x y) inside this footprint's (zone ...) blocks by (dx,dy).
    KiCad footprint zones use absolute board coords (unlike pads/graphics, which are
    footprint-relative), so they must move explicitly when the footprint is moved."""
    def shift_xy(s):
        return re.sub(r'\(xy (-?\d[\d.]*) (-?\d[\d.]*)\)',
                      lambda p: f"(xy {float(p.group(1)) + dx:.6g} {float(p.group(2)) + dy:.6g})", s)
    out, i = [], 0
    while True:
        j = blk.find("(zone", i)
        if j < 0:
            out.append(blk[i:]); break
        out.append(blk[i:j])
        d, k = 0, j
        while k < len(blk):
            if blk[k] == "(":
                d += 1
            elif blk[k] == ")":
                d -= 1
                if d == 0:
                    break
            k += 1
        out.append(shift_xy(blk[j:k + 1]))
        i = k + 1
    return "".join(out)


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


def sheet_instances(top):
    """{zen_instance_name: ref} for one schematic sheet, read from the netlist sheetpath.
    The LEAF instance is parts[-2] (the segment before the component-type leaf), which works
    at any nesting depth: 'PWR.F_IN.MF-...' -> F_IN, and nested-module parts like
    'PWR.U_BUCK.C_IN1.C' -> C_IN1, 'PWR.U_BUCK.TPS563208.TPS563208DDCR' -> TPS563208.
    Leaf instance names are unique within a sheet here, so this is an unambiguous name->ref."""
    t = open(NET, encoding="utf-8", errors="replace").read()
    out = {}
    for m in re.finditer(r'\(comp \(ref "([^"]+)"\).*?\(sheetpath \(names "([^"]*)"', t, re.S):
        parts = m.group(2).split(".")
        if len(parts) > 2 and parts[0] == top:
            out[parts[-2]] = m.group(1)
    return out


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


def place_power(inst2ref, sizes):
    """Constructive placement of the PWR rail parts (modules/power.zen): the input-protection
    chain (jack / fuse / FET / TVS) feeds two MPM3620A buck-module rails (5 V and 3.3 V) placed
    side by side, each with its 5 passives (Cin / Cout / EN pull-up / FB divider) clustered at the
    module's pins. Returns {ref:(x,y,rot)} in LOCAL board-frame coords (KiCad, +y DOWN)."""
    has = lambda n: n in inst2ref
    R = lambda n: inst2ref[n]
    place, boxes = {}, []
    def ebox(ref, x, y, rot):
        w, h = sizes[ref]
        if rot in (90, 270):
            w, h = h, w
        return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    def clash(b):
        return any(b[0] < c[2] - 1e-6 and c[0] < b[2] - 1e-6 and b[1] < c[3] - 1e-6 and c[1] < b[3] - 1e-6
                   for c in boxes)
    def put(ref, x, y, rot=0, ux=0.0, uy=0.0):
        n = math.hypot(ux, uy) or 1.0
        ux, uy = ux / n, uy / n
        for k in range(200):                       # step outward until it clears neighbours
            cx, cy = x + ux * 0.4 * k, y + uy * 0.4 * k
            b = ebox(ref, cx, cy, rot)
            if not clash(b):
                place[ref] = (round(cx, 3), round(cy, 3), rot)
                boxes.append(b)
                return
        place[ref] = (round(x, 3), round(y, 3), rot)
        boxes.append(ebox(ref, x, y, rot))

    def module(prefix, cx):
        """place one MPM3620A rail cluster (module IC + 5 passives), module centred at (cx, 0)."""
        if not has(prefix):
            return
        put(R(prefix), cx, 0, 0)
        def at(suffix, pin, rot=0):                # start the passive at a module pin, push out
            ref = prefix + suffix
            if not has(ref):
                return
            px, py = MODULE_PINS[pin]
            put(R(ref), cx + px, py, rot, px, py)
        at("_CIN", "IN", 90)                        # input cap at IN
        at("_COUT", "OUT", 90)                      # output cap at OUT
        at("_REN", "EN", 90)                        # EN pull-up
        at("_RTOP", "FB", 90)                       # feedback divider at FB...
        if has(prefix + "_RBOT") and has(prefix + "_RTOP"):
            x0, y0, _ = place[R(prefix + "_RTOP")]
            put(R(prefix + "_RBOT"), x0, y0 - 1.8, 90, 0, -1)   # ...R_BOT stacked below R_TOP

    module("U_BUCK5", 0.0)                           # 12V -> 5V rail cluster
    module("U_BUCK33", 13.0)                         # 12V -> 3.3V rail cluster, to the right
    # input protection chain LEFT of the modules: TVS -> FET (+ gate R) -> fuse (toward the jack)
    lead = (min(b[0] for b in boxes) if boxes else -4.0) - 2.0
    for n in ("D_IN", "Q_RP", "F_IN"):
        if not has(n):
            continue
        lead -= sizes[R(n)][0] / 2
        put(R(n), lead, 0, 0, -1, 0)
        lead -= sizes[R(n)][0] / 2 + PWR_CLEAR + 0.4
    # gate divider straddles the FET: R_RP (to GND) above, R_RP_TOP (to the P12V source) below
    if has("R_RP") and has("Q_RP"):
        x0, y0, _ = place[R("Q_RP")]; put(R("R_RP"), x0, y0 + sizes[R("Q_RP")][1] / 2 + 1.2, 0, 0, 1)
    if has("R_RP_TOP") and has("Q_RP"):
        x0, y0, _ = place[R("Q_RP")]; put(R("R_RP_TOP"), x0, y0 - sizes[R("Q_RP")][1] / 2 - 1.2, 0, 0, -1)
    return place


def load_placements():
    """Hand-tuned overrides captured from KiCad via `--capture`: {ref: [bx, by, rot]}
    in BOARD frame (ORIGIN is re-applied on top, so overrides follow the board if it is
    re-centred). rot is null for an unrotated part. Missing file -> no overrides."""
    if not os.path.exists(PLACE):
        return {}
    with open(PLACE, encoding="utf-8") as f:
        return json.load(f)


def capture():
    """Snapshot the position/rotation of every UNGROUPED footprint into placements.json
    (BOARD frame = absolute minus ORIGIN). Group membership is the "not yet placed" flag:
    the Zener sync groups all parts by sheet, and you remove a part from its group in KiCad
    when you place it — so ungrouped == placed. A plain `floorplan_seed.py` run then restores
    those positions and re-ungroups the placed parts, so a re-sync no longer scrambles them.

    Returns (captured, skipped) counts, or None if it refused (see the guard below)."""
    t = open(PCB, encoding="utf-8", errors="replace").read()
    grouped = grouped_uuids(t)
    out, skipped = {}, 0
    for _, _, blk in iter_fp(t):
        ref = fp_ref(blk)
        if not ref:
            continue
        if fp_uuid(blk) in grouped:
            skipped += 1
            continue
        m = re.search(r'\(at (-?\d[\d.]*) (-?\d[\d.]*)((?: -?\d[\d.]*)?)\)', blk)
        rot = float(m.group(3)) if m.group(3).strip() else None
        if rot is not None and rot == int(rot):
            rot = int(rot)                       # keep 270 as 270, not 270.0
        out[ref] = [round(float(m.group(1)) - ORIGIN_X, 4),
                    round(float(m.group(2)) - ORIGIN_Y, 4), rot]
    # Guard: nothing ungrouped but we already have saved placements => you almost certainly
    # just ran a sync (which re-groups everything) and haven't restored yet. Overwriting now
    # would wipe placements.json, so refuse and tell you to restore first.
    if not out and load_placements():
        return None
    with open(PLACE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    return len(out), skipped


def compute():
    t = open(PCB, encoding="utf-8", errors="replace").read()
    sizes = {fp_ref(b): fp_size(b) for _, _, b in iter_fp(t) if fp_ref(b)}
    fpname = {fp_ref(b): fp_name(b) for _, _, b in iter_fp(t) if fp_ref(b)}
    byblk = load_blocks()
    place = {}
    labels = []            # (x, y, text)
    # SOM connectors keep real DF40 geometry on the board (they anchor the SOM).
    # CN1 (BTB9900, 80-pin) is VERTICAL -> rotate 270deg so pin 1 lands outer(left)-top
    # per som_placement.md; CN2/CN3 (100-pin) are horizontal at native rotation.
    som_rot = {"CN1": 270}
    for r, (dx, dy) in {"CN1": (-19.85, 0), "CN2": (-6.47, -14.67), "CN3": (-6.47, 14.74)}.items():
        place[r] = (SOM_DATUM_X + dx, BH / 2 + dy, som_rot.get(r))
    place["J2"] = (TAB_X, BH + TAB_TOP)          # slot: forms the tab in the outline
    # SOM mounting holes: 41x31mm rectangle on the SAME datum as CN1-3 (som_placement.md /
    # the SOM mechanical drawing). Placed by instance name -> ref so they track the BTB
    # connectors under any SOM move. +x right, +y down; datum = hole-rect centre.
    # They live on the SOM sheet (not MECH) so the sync groups them WITH CN1/CN2/CN3 --
    # same group = the constellation stages and drags as one rigid unit in KiCad.
    mech = sheet_instances("SOM")
    for inst, (dx, dy) in {"MH_TL": (-20.5, -15.5), "MH_TR": (20.5, -15.5),
                           "MH_BL": (-20.5, 15.5), "MH_BR": (20.5, 15.5)}.items():
        if inst in mech:
            place[mech[inst]] = (SOM_DATUM_X + dx, BH / 2 + dy)
    labels.append((30.0, 12.0, "SOM DF40 connectors (on board): CN1=BTB9900 CN2=C2399 CN3=C2400"))
    labels.append((TAB_X - 24, BH - 2, "slot finger tab (mechanical)"))
    # POWER on-board: barrel jack on the notch's short side (cable clears via the notch),
    # rail parts clustered just below + right of it under the notch's lower edge.
    pwr = byblk.get("PWR", [])
    jack = next((r for r in pwr if "JACK" in fpname.get(r, "").upper()), None)
    if jack:
        jw, jh = sizes[jack]
        place[jack] = (NOTCH_X - jw / 2 - 1.0, NOTCH_H / 2, 180)   # against the notch short side
    inst2ref = {i: r for i, r in sheet_instances("PWR").items() if r != jack and r not in place}
    local = place_power(inst2ref, sizes)         # buck-centred constructive cluster (local)
    if local:
        def box(r):
            x, y, rot = local[r]
            w, h = sizes[r]
            if rot in (90, 270):
                w, h = h, w
            return x - w / 2, y - h / 2
        minx = min(box(r)[0] for r in local)     # translate cluster's top-left to PWR_LEFT/TOP,
        miny = min(box(r)[1] for r in local)     # i.e. below the jack, just under the notch edge
        ddx, ddy = PWR_LEFT - minx, PWR_TOP - miny
        for r, (x, y, rot) in local.items():
            place[r] = (x + ddx, y + ddy, rot)
        # any PWR part place_power didn't handle -> tack on at the block's right edge
        stragglers = [r for r in pwr if r != jack and r not in place]
        sx = max((place[r][0] for r in local), default=PWR_LEFT) + 5.0
        for r in stragglers:
            place[r] = (sx, PWR_TOP, 0); sx += 4.0
        labels.append((PWR_LEFT, PWR_TOP - 2.0, "POWER: 2x MPM3620A buck hot-loop + FB + protection clustered (rough draft)"))
    # everything else -> labeled trays below the board
    y = TRAY_TOP
    for key, text in BLOCKS:
        if key == "PWR":                         # placed on-board under the notch, above
            continue
        refs = [r for r in byblk.get(key, []) if r not in place]
        if not refs:
            continue
        pos, tw, th = pack_tray(refs, sizes, WMAX.get(key, 62.0))
        labels.append((0.0, y - 2.0, text))
        for r, (dx, dy) in pos.items():
            place[r] = (dx, y + dy)
        y += th + TRAY_GAP
    # hand-tuned overrides win over the algorithmic tray/anchor positions (board frame).
    # A ref only in placements.json (e.g. a part deleted from the schematic) is ignored;
    # a ref only in the schematic (a newly added part) keeps its computed tray slot.
    for r, v in load_placements().items():
        if r in place:
            place[r] = (v[0], v[1]) if v[2] is None else (v[0], v[1], v[2])
    # shift the whole board frame so the body rectangle is centred on the sheet
    place = {r: (round(v[0] + ORIGIN_X, 4), round(v[1] + ORIGIN_Y, 4), *v[2:])
             for r, v in place.items()}
    labels = [(x + ORIGIN_X, y + ORIGIN_Y, text) for x, y, text in labels]
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
    def on_perim(x, y, ox, oy):
        # body rectangle edges (+ the two interior notch edges) for a frame at (ox,oy)
        x, y = x - ox, y - oy
        return (abs(x) < e or abs(x - BW) < e or abs(y) < e or abs(y - BH) < e
                or abs(x - NOTCH_X) < e or abs(y - NOTCH_H) < e)
    def strip_edge(m):
        p = [(float(m.group(1)), float(m.group(2))), (float(m.group(3)), float(m.group(4)))]
        # strip if the segment lies on the outline at the OLD (0,0) frame (pre-centre
        # files) or the current centred frame -> migration + re-runs both stay clean
        for ox, oy in ((0.0, 0.0), (ORIGIN_X, ORIGIN_Y)):
            if all(on_perim(qx, qy, ox, oy) for qx, qy in p):
                return ""
        return m.group(0)
    t = re.sub(r'\(gr_line \(start (\S+) (\S+)\) \(end (\S+) (\S+)\)[^\n]*Edge\.Cuts[^\n]*\)\n?',
               strip_edge, t)
    t = drop_blocks(t, "(gr_text", lambda b: 'layer "Cmts.User"' in b)
    # board outline (board frame): top edge notched at the upper-right corner, right +
    # left, and the bottom edge split around the finger-tab gap. Emitted at +ORIGIN.
    tl, tr = TAB_X - TAB_HALF, TAB_X + TAB_HALF
    segs = [((0, 0), (NOTCH_X, 0)),               # top edge up to the notch
            ((NOTCH_X, 0), (NOTCH_X, NOTCH_H)),   # notch: down
            ((NOTCH_X, NOTCH_H), (BW, NOTCH_H)),  # notch: across to the right edge
            ((BW, NOTCH_H), (BW, BH)),            # right edge (starts below the notch)
            ((BW, BH), (tr, BH)),                 # bottom: right of the tab
            ((tl, BH), (0, BH)),                  # bottom: left of the tab
            ((0, BH), (0, 0))]                    # left edge
    add = ""
    for (ax, ay), (bx, by) in segs:
        sx, sy, ex, ey = (round(ax + ORIGIN_X, 4), round(ay + ORIGIN_Y, 4),
                          round(bx + ORIGIN_X, 4), round(by + ORIGIN_Y, 4))
        add += (f'\n\t(gr_line (start {sx:g} {sy:g}) (end {ex:g} {ey:g}) (stroke (width 0.12) '
                f'(type default)) (layer "Edge.Cuts") (uuid "{uuid.uuid4()}"))')
    for x, y, text in labels:
        add += (f'\n\t(gr_text "{text}" (at {x:.2f} {y:.2f}) (layer "Cmts.User") '
                f'(uuid "{uuid.uuid4()}") (effects (font (size 3 3) (thickness 0.5)) '
                f'(justify left bottom)))')
    t = t.rstrip()
    assert t.endswith(")"), "unexpected pcb tail"
    return t[:-1] + add + "\n)\n"


def ungroup_placed(t, placements):
    """Drop every placed ref (a key of `placements`) from the KiCad groups it belongs to;
    delete groups that end up empty. Leaves un-captured parts grouped."""
    if not placements:
        return t
    ref2uuid = {fp_ref(b): fp_uuid(b) for _, _, b in iter_fp(t) if fp_ref(b)}
    drop = {ref2uuid[r] for r in placements if r in ref2uuid}
    out, i = [], 0
    for a, b, blk, span in iter_groups(t):
        out.append(t[i:a]); i = b
        if not span:
            out.append(blk); continue
        mblk = blk[span[0]:span[1]]
        kept = [u for u in re.findall(r'"([0-9a-f-]{36})"', mblk) if u not in drop]
        if not kept:                                   # group emptied -> delete it
            while i < len(t) and t[i] in " \t\r\n":
                i += 1
            continue
        newm = "(members\n\t\t\t" + "\n\t\t\t".join(f'"{u}"' for u in kept) + "\n\t\t)"
        out.append(blk[:span[0]] + newm + blk[span[1]:])
    out.append(t[i:])
    return "".join(out)


_FP_FILES = {}
def _fp_file(name):
    """Path to a library <name>.kicad_mod under components/, or None (cached walk)."""
    if not _FP_FILES:
        base = os.path.join(os.path.dirname(__file__), "..", "components")
        for root, _, files in os.walk(base):
            for f in files:
                if f.endswith(".kicad_mod"):
                    _FP_FILES.setdefault(f[:-len(".kicad_mod")], os.path.join(root, f))
    return _FP_FILES.get(name)


PAD_AT_RE = (r'\(pad\s+"[^"]*"\s+\S+\s+\S+\s*\(at\s+'
             r'(-?\d[\d.]*)\s+(-?\d[\d.]*)(?:\s+(-?\d[\d.]*))?\)')


def inherent_pad_angles(blk):
    """{(local_x, local_y): inherent_angle} from the footprint's LIBRARY .kicad_mod. Used
    to bake a rotated placement's pad-body angle = inherent + footprint_rotation (the value
    KiCad renders). Keyed by LOCAL pad position (rotation-invariant), so it never reads the
    placed pad's current angle -> re-running restore is idempotent. {} if the lib isn't found
    (falls back to inherent 0, i.e. the old behaviour, for those parts)."""
    m = re.match(r'\(footprint "([^"]+)"', blk)
    path = _fp_file(m.group(1).split(":")[-1]) if m else None
    if not path or not os.path.exists(path):
        return {}
    lib = open(path, encoding="utf-8", errors="replace").read()
    out = {}
    for pm in re.finditer(PAD_AT_RE, lib):
        out[(round(float(pm.group(1)), 4), round(float(pm.group(2)), 4))] = \
            float(pm.group(3)) if pm.group(3) else 0.0
    return out


def run(move=True):
    place, labels = compute() if move else ({}, [])
    t = open(PCB, encoding="utf-8", errors="replace").read()
    if move:
        out, last, n = [], 0, 0
        for a, b, blk in iter_fp(t):
            out.append(t[last:a])
            ref = fp_ref(blk)
            if ref in place:
                val = place[ref]
                x, y = val[0], val[1]
                rot = val[2] if len(val) > 2 else None
                # Footprint zones (keepouts) store ABSOLUTE board coords, so a plain
                # (at) edit leaves them behind. Translate every zone xy by the move delta.
                om = re.search(r'\(at (-?\d[\d.]*) (-?\d[\d.]*)', blk)
                dx, dy = x - float(om.group(1)), y - float(om.group(2))
                if dx or dy:
                    blk = translate_zone_pts(blk, dx, dy)
                # This layout pipeline rotates pad POSITIONS by the footprint angle but NOT
                # the pad bodies, so a rotated footprint needs each pad's body angle set to
                # its BAKED absolute angle = inherent + rot (mod 360). Reading inherent from
                # the library (keyed by local pad pos) — NOT by adding to the current angle —
                # keeps this correct for pads with a non-zero inherent angle (e.g. the power
                # jack's 180/270 pads) and idempotent across re-runs.
                if rot:
                    inh = inherent_pad_angles(blk)
                    def pad_rot(m, r=rot, inh=inh):
                        key = (round(float(m.group(2)), 4), round(float(m.group(3)), 4))
                        a = (inh.get(key, 0.0) + r) % 360
                        if a == int(a):
                            a = int(a)
                        return f"{m.group(1)}(at {m.group(2)} {m.group(3)}{f' {a}' if a else ''})"
                    blk = re.sub(r'(\(pad\s+"[^"]*"\s+\S+\s+\S+\s*)\(at\s+'
                                 r'(-?\d[\d.]*)\s+(-?\d[\d.]*)(?:\s+-?\d[\d.]*)?\)', pad_rot, blk)
                def repl(m, x=x, y=y, rot=rot):
                    tail = f" {rot}" if rot is not None else m.group(3)
                    return f"(at {x:.3f} {y:.3f}{tail})"
                blk, k = re.subn(r'\(at (-?\d[\d.]*) (-?\d[\d.]*)((?: -?\d[\d.]*)?)\)',
                                 repl, blk, count=1)
                n += k
            out.append(blk); last = b
        out.append(t[last:])
        t = "".join(out)
    # Remove the PLACED parts (those in placements.json) from the per-sheet KiCad groups
    # the sync creates, and delete any group left empty. Un-captured parts stay grouped as
    # staging, so "ungrouped == placed" survives a re-sync (which re-groups everything).
    t = ungroup_placed(t, load_placements())
    t = outline_and_labels(t, labels)
    open(PCB, "w", encoding="utf-8").write(t)
    return len(place), labels


if __name__ == "__main__":
    if "--capture" in sys.argv[1:]:
        res = capture()
        if res is None:
            print("REFUSED: no ungrouped footprints, but placements.json is non-empty.")
            print("  You likely just synced (which re-groups everything). Run a plain")
            print("  `floorplan_seed.py` first to restore + re-ungroup, then --capture.")
            sys.exit(1)
        n, skipped = res
        print(f"captured {n} placed (ungrouped) footprints -> {os.path.relpath(PLACE)}"
              f"  ({skipped} still grouped, left in trays)")
        print("  re-run `floorplan_seed.py` (no flag) any time to restore them + ungroup")
    elif "--outline-only" in sys.argv[1:]:
        run(move=False)
        print("re-added board outline + tab; placed parts ungrouped (footprints untouched)")
    else:
        n, labels = run(move=True)
        print(f"placed {n} footprints (placements.json overrides + labeled trays) + outline/tab:")
        for _, _, text in labels:
            print(f"  • {text}")
        print("  (captured parts placed & ungrouped; the rest stay grouped in trays)")
