# appletini-mega — board floorplan & placement (WORKING DRAFT)

Status: **in progress.** This doc gets nailed down *before* we assign SOM banks or BTB balls —
which balls are "good" for a given bus depends on connector escape direction, which depends on
where the SOM and the consuming parts physically sit. Sequence: **floorplan → region/bank
assignment → ball assignment → route.** See `docs/som_placement.md` for the SOM's internal
connector geometry (the anchor this builds on).

## Deployment model (decided 2026-07-08)

The carrier is an **Apple II/IIgs peripheral-slot card**, inserted vertically into one of the
machine's card slots. The slot is used for **mechanical support** (the case is designed to hold
cards this way and keep them out of the way) — *not* as the CPU-bus interface.

- Standard **gold slot-edge fingers** on the bottom edge — real fingers (not bare PCB), both for
  looks and so the slot contacts never rub raw laminate.
- **Which slot is a free variable**, chosen at integration time by whichever is best placed to run
  the ribbon to the CPU socket with minimal fuss.
- The **CPU bus** is taken at the **vacated CPU socket** via the 2×20 header → ribbon → DIP-40 plug
  (see `cpu_socket.zen`). The ribbon is expected to be **short** — just enough slack to seat easily,
  not a 12" run.

### Why the bus goes through the CPU socket, not the slot
The slot *does* carry most CPU-bus signals, but a slot card is a **peripheral**, not the CPU. An
accelerator must *be* the CPU — drive the bus as master from the CPU socket with the real CPU
removed. The slot can only ever make us a peripheral (or a transient /DMA master), so it can't
serve the accelerator function. Slot = mechanics (+ maybe power/ground, TBD below).

## Card mechanicals (from the prior AppleTini board)

Reference: `/mnt/c/repos/appletini/v5/AppleTini_board_v5_2/*.kicad_pcb` (prior board). ⚠ **Reuse ONLY
two things: the edge-cut outline and the `AppleIIBus_Edge` slot footprint.** That board mated to an
**Alchitry Au** via Hirose connectors (J2/J3/J4) — the Au's connector geometry is unrelated to the
Tang Mega SOM's three DF40 connectors, so the prior board's **internal placement is NOT a reference**.
SOM + subsystem placement is a clean-sheet exercise driven by `docs/som_placement.md` (the DF40
C2399/C2400/BTB9900 geometry).

- Prior outline: **4.000" × 2.750"** (101.6 × 69.85 mm) rectangle. The **2.750" height is the Apple II
  card standard → FIXED axis** (vertical in the case). **Length grows** — start target **6.000"
  (152.4 mm)** (was 4"; allowed longer, up to ~7").
- Slot edge = footprint **`AppleIIBus_Edge`** (`/mnt/c/repos/appletini/v3/appletini_board/appletini.pretty/
  AppleIIBus_Edge.kicad_mod`): **50 pads = 25 fingers × 2 sides** (F.Cu + B.Cu), **0.1" (2.54 mm) pitch,
  2.400" pad span**, tab ~2.55" wide with insertion chamfers + its own Edge.Cuts. Reuse as-is.
- **Slot is mechanical-only** → those 50 finger pads carry **NO nets** (floating gold, per the
  single-star-point grounding decision).
- Card inserts **vertically**, finger tab **down** into the slot; card stands up. Tall parts + the SOM
  stack must fit the **card-to-card slot pitch** (⚠ confirm for the //e).
- Cable connectors (USB3 to Pi5, 2× USB-C, 12 V barrel) on an **accessible edge**; the **CPU-ribbon
  header** where the ribbon drops cleanly to the //e CPU-socket area.

## Layout workflow (Zener-native)

`Board()` has no outline parameter — the **edge cuts are drawn in KiCad**. `pcb layout
appletini_mega.zen` generates the real board (all footprints + ratsnest) and opens KiCad; draw the
6.000"×2.750" outline + finger tab, place the `AppleIIBus_Edge` slot footprint on the bottom edge,
then floorplan the big blocks. `pcb layout --temp` gives a throwaway practice board.

**⚠ Regen preservation (tested, pcb v0.4.5) — NOT what the earlier note claimed:** a **sync** regen
(plain `pcb layout`) **preserves footprint positions** but **regenerates all board-level graphics from
scratch — it WIPES the Edge.Cuts outline** (and any other `gr_line`/`gr_*` you added by editing the
file; unclear if a KiCad-*drawn*-and-saved outline survives — assume not). Positions survive because
Zener matches footprints by stable path/uuid; board graphics are not tracked. Consequences:
- To **open the seeded board without re-packing**, use **`pcb layout appletini_mega.zen --no-sync`**
  (resolves the existing file, no regen) — this keeps both positions AND the outline.
- Only run a **sync** (`pcb layout`, default) when the `.zen`/netlist changed. After a sync, the
  outline is gone but your placement is intact → restore just the outline with
  **`python3 tools/floorplan_seed.py --outline-only`** (does not touch positions).

### `tools/floorplan_seed.py` — labeled staging trays (2026-07-08, rev 2)

The `pcb layout` auto-pack piles all 136 footprints together with **no human-readable module tag**
(each KiCad `sheetname` is a bare UUID), so you can't tell which part belongs to which block. This
tool reads the real hierarchy from `layout/default.net` (`sheetpath names = MODULE.instance.part`) and
sorts the footprints into **labeled, non-overlapping staging trays**.

**Why trays, not floorplan positions (learned the hard way):** 136 *real* footprints — a 52 mm 2×20
header, 8 mm ICs, 23 mm DF40s, dozens of 0402s — **do not fit legibly at their floorplan positions on
a 152×70 mm board.** Packed that tight the bodies overlap into mush and you can't tell the blocks
apart (rev 1 tried this — it failed). So instead each block is laid out as a tidy cluster with spacing
taken from **each footprint's real bounding box** (row-packed, zero body overlap), stacked in a column
of labeled trays **below the board**, ordered along the power↔USB spine. A `gr_text` label over each
tray names the block. You then **drag each recognizable, labeled cluster onto the board** at the
floorplan-v1 position from the table above. The `--outline-only` mode redraws just the outline.

- **On the board already:** the **SOM DF40 connectors** (CN1=BTB9900, CN2=C2399, CN3=C2400 at their
  real `som_placement.md` geometry about datum (55, 34.9)) and the **slot J2** (it forms the tab) —
  both labeled in place. Everything else is in a tray.
- **Trays (top→bottom):** POWER · SDRAM0 · SDRAM1 · USB3/CH569 · FT2232 · APPLE BUS.

**Board outline + finger tab (seeded, matches the prior board's geometry):** the card **body** is the
152.4 × 69.85 mm (6.000″ × 2.750″) rectangle; the **2.55″ finger tab protrudes ~7.5 mm below** the
body bottom edge. The seeder draws the top/left/right edges full and the **bottom edge in two pieces
with a gap** for the tab (gap = TAB_X ± 32.385 mm), positions the `AppleIIBus_Edge` slot (J2) so its
own Edge.Cuts (tab verticals + 45° insertion chamfers + insertion edge) land exactly on the gap
endpoints — J2 origin = `(TAB_X, body_bottom + 3.175)`. `TAB_X` (tab centre, default board centre
76.2) = the chosen slot's X at integration; nudge it in the script if the target slot isn't centred.
The tab's `body_bottom + 3.175` offset and ±32.385 half-width come from the footprint's own geometry,
cross-checked against `/mnt/c/repos/appletini/v5/AppleTini_board_v5_2` (tab gap 64.76 mm, protrusion
7.5 mm, slot origin 3.18 mm below the body edge — all reproduced).

**Usage (from a fresh generate):**
```
pcb layout appletini_mega.zen --no-open      # generate (packed), don't open
python3 tools/floorplan_seed.py              # sort into labeled trays + draw outline
pcb layout appletini_mega.zen --no-sync      # open in KiCad, preserving everything
```
Run the **full** seeder only for the *initial* sort — after you've dragged clusters onto the board,
a re-run would reset them back into the trays; use `--outline-only` instead. The trays are a sorting
aid, not placement — drag each labeled cluster to its floorplan-v1 spot; positions then persist across
syncs (board graphics/labels do not — see the regen note above).

**Open method (card edge):** the slot is already a Zener component (`AppleIIBus_Edge`, footprint + 50
NC pads, excluded from BOM) instantiated as `J_SLOT`/`J2` — the toolchain always places it, so the
seeder just positions it on the bottom edge.

## Grounding topology — OPEN, and important

With the card in a slot *and* the ribbon at the CPU socket, there are **two candidate ground paths
to the Apple motherboard**: the slot fingers and ribbon pin 21 (VSS). Tying **both** creates a
ground loop across the (very noisy) motherboard between the slot region and the CPU-socket region —
this is the mechanism behind the "extra ground strap made my card noisier" experience.

The level shifters' 5 V domain must reference the Apple ground **at the CPU socket** for the bus
levels to be valid, so ribbon pin 21 is the ground that has to be there. Leaning:

- **Single-point ground through ribbon pin 21** as the carrier↔Apple reference (matches the
  "single ground return is actually an advantage" finding for `cpu_socket`).
- Slot edge: **do not also tie signal ground through the slot** (mechanical-only, or handle its
  power/ground pins very deliberately) to avoid the second path.

This needs an explicit decision once we know whether the slot edge is used electrically at all.

## Blocks to place + their affinities

| Block | Parts | Wants to be near | Notes |
|---|---|---|---|
| **SOM** | GW5AT-60 module (45×35 mm, 3 mm standoffs) | — (free variable) | position dictates where the rest lands; C2399 top / C2400 bottom / BTB9900 left, "C" opens right |
| **SDRAM0** | 1× AS4C16M16SA | **C2399** (BANK1/2) | bank-local, escapes toward C2399 |
| **SDRAM1** | 1× AS4C16M16SA | **C2400** (BANK6/7/8) | bank-local; C2400 clean field (P1–P50) is the OUTER row → escapes outward |
| **USB3 bridge** | CH569 + 30 MHz xtal + USB3 conn | HSPI connector (BANK2 region) | short 90 Ω SS pair to the edge connector |
| **Programming** | FT2232H + 12 MHz xtal + USB-C | config/JTAG balls | |
| **Power** | 12 V barrel → MP2315 buck → AMS1117 | barrel at an accessible edge | keep buck switching away from USB3 SS + any analog |
| **CPU-socket / Apple bus** | 2×20 header + 5×'245 + 2×'T45 + deadman | CPU-ribbon edge | the Apple-bus block; header near where the ribbon exits toward the CPU socket |

Everything hangs off the SOM's three left-side connectors, so **SOM position is the first domino**;
once it's placed, the SDRAMs/CH569/FT2232 fall out of bank-locality and the connector edges fall out
of cable egress.

## Envelope / height constraints

- SOM sits on 3 mm standoffs over the carrier (BTB stack) + its own component height; the underside
  of the carrier is usable. Which **face** the SOM goes on (and whether it clears the neighboring
  slot card) is open — depends on slot pitch of the target machine.
- ~30% area utilization expected; **routing density**, not area, is the real constraint (6-layer).

## Decisions locked (2026-07-08)

- **Primary bring-up target = Apple //e** (place to suit //e + IIgs; layouts similar enough).
- **Slot edge = purely mechanical, not even ground.** Interface with the (noisy) motherboard ONLY at
  the single star-point of the CPU socket. → resolves the grounding topology: **single-point ground
  via ribbon pin 21**, slot fingers floating.
- **Outline = 2.750" height (fixed) × 6.000" length (start target)**, reusing the prior board's
  `AppleIIBus_Edge` slot footprint.
- **SOM orientation = HORIZONTAL, reference orientation, "C" opens toward the USB (right) end.**
  SOM long-axis runs along the board length → only **35 mm tall**, which is what buys the ~19 mm
  top strip the Apple-bus block needs. (The vertical/90°-rotated alternative gives the cleanest
  two-sided SDRAM escape but leaves only ~13 mm at the top and forces USB onto the top edge — not
  worth it, since SDRAM is the *most forgiving* bus and shouldn't drive the floorplan.)
- **Machine-facing end = TOP edge, center.** The 2×20 CPU-ribbon header sits on the **top long edge**
  (opposite the slot fingers) and the ribbon drops over the top toward the //e CPU socket. Leaves both
  short ends free for the power↔USB spine.
- **SOM mounting face = TOP of the carrier (LOCKED).** Apple II cards project **upward** out of the
  slot with a **consistent component side** (each card's tall face looks at the next card's bare back),
  so the ~1″ //e slot pitch easily clears a one-sided ~8–10 mm SOM stack. → **Top-mount** the SOM (and
  every tall part). This keeps inner/outer rows exactly as documented in `som_placement.md` (a
  bottom-mount mirror would flip them and lose the SDRAM1-escapes-outward geometry). **Design rule:**
  all tall parts (SOM, barrel jack, USB-C, 2×20 header, electrolytics) on the **top/component face**;
  **bottom face = low-profile SMD only** (min profile — small decoupling may still tuck under the SOM in
  the ~3 mm standoff gap).

## Concrete floorplan v1 (2026-07-08)

Working frame: **origin = bottom-left corner, +x right, +y up, mm.** Board = `(0,0)…(152.4, 69.85)`.
(KiCad's page frame is y-down; convert when placing. These are *target* regions to floorplan **to**
in KiCad after `pcb layout` generates the footprints — not final routed positions.)

```
 y69.85 ┌───────────────────────────────────────────────────────────────┐
        │  ┌───────── Apple level-shifter strip ─────────┐  ┌ 2×20 CPU ┐ │  ← ribbon
        │  │ 5×'245  2×'T45  deadman                     │  │  HEADER  │ │    exits top
 ~51    │  └─────────────────────────────────────────────┘  └──────────┘ │
        │ ┌─POWER──┐  ┌──────────── SOM 45×35 ───────────┐  ┌── USB end ─┐│
        │ │ barrel │  │ ▔C2399 (top): SDRAM0 + HSPI/BK2  │  │ CH569  SS ►││→USB3
        │ │ MP2315 │ B│                                  │M │ 30M xtal   ││
        │ │ AMS1117│ T│    FPGA (under SOM)       mouth  │► │ FT2232     ││→USB-C
        │ │  bulk  │ B│                                  │O │            ││→USB-C
        │ └────────┘ 9│ ▁C2400 (bot): SDRAM1 + VBUS + sp │U └────────────┘│
 ~15    │      5V→    │      + Apple spill (BK6/7/8→138B5)│T  ↑SDRAM1 may   │
        │            9└──────────────────────────────────┘   nest in mouth │
 ~12    │  · · · · · · · · · · finger keep-out · · · · · · · · · · · · · · ·│
 y0     └═════════════════[ slot fingers, bottom edge ]═══════════════════┘
       x0                                                              x152.4
```

**Block targets** (bottom-left origin, mm; ± a few mm — refine visually in KiCad):

| Block | X range | Y range | Anchor / why |
|---|---|---|---|
| **SOM body** (45×35) | 32.5 – 77.5 | 15.5 – 50.5 | **datum (hole-rect centre) = (55, 33).** Left-of-centre so the C's mouth + right end have room. |
| — BTB9900 (L, vert) | ~32.5 (x) | ~25 – 41 | SOM left edge → faces the power/left region; JTAG+config+BANK12 escape left. |
| — C2399 (top, horiz) | ~38.5 – 58 | ~48 – 50.5 | SDRAM0 (BANK1/2) + HSPI (BANK2). Outer row (P51–100) faces **up** toward the Apple strip. |
| — C2400 (bot, horiz) | ~38.5 – 58 | ~15.5 – 18 | SDRAM1 + VBUS_SOM (P91–99, inner) + Apple spill. Outer row (P1–50) faces **down**. |
| **Power** | 2 – 30 | 15 – 50 | Barrel jack on the **left short edge**; 5 V runs mid-board to C2400 VBUS pins (~40 mm, ok). |
| **CH569 + 30 MHz xtal** | 85 – 120 | 20 – 48 | Nests in the mouth, end-on to C2399 for HSPI; xtal in a quiet pocket away from the SS pair. |
| **USB3 USB-C** | ~148 – 152 | ~38 – 50 | **Right short edge.** Short 90 Ω SS pair from CH569, guard moat, <5 mil intra-pair. |
| **FT2232 + its USB-C** | 118 – 150 | 14 – 34 | Same right edge, **outside** the USB3 SS keep-out. JTAG runs L across board to BTB9900 (slow, fine). |
| **Apple shifter strip** | 30 – 105 | 51 – 62 | Top strip. A-side ← FPGA GPIO (spill on C2400, routes up on L4 — power-ref layer, immune at 1–2.8 MHz). |
| **2×20 CPU header** | ~50 – 101 | 62 – 69.85 | **Top edge, centre** (~50.8 mm long). B-side = socket 5 V + gnd via ribbon pin 21. |
| **Slot fingers** | ~45.7 – 106.7 | 0 – ~2 (pads) | Bottom edge, centred (final X follows the target slot); keep-out up to y≈12. Floating. |

**Deferred/forgiving:** SDRAM1 is drawn under C2400 but is the *most forgiving* bus — if the finger
keep-out squeezes the under-SOM band, **nest it in the mouth** (right of the SOM) instead; either works.

## Open questions (updated 2026-07-08)

1. ~~SOM face + position~~ → **resolved** (horizontal, datum (55,33), top-mount pending Q3).
2. **Connector egress — mostly resolved:** barrel = **left short edge**; USB3 + FT2232 USB-C = **right
   short edge**; CPU ribbon = **top edge centre**. Still to confirm at KiCad time: exact USB-C spacing on
   the right edge and the barrel-jack height vs case.
3. ~~Slot pitch / height budget~~ → **resolved:** top-mount locked (see lock above). ~1″ pitch + the
   consistent-component-side convention clears the one-sided SOM stack; tall parts go top, bottom stays
   low-profile.
4. **Slot-finger X position** along the bottom edge — set by the chosen slot's connector location; drawn
   centred for now, adjust once the target slot is picked.

## Ingested (2026-07-08)

- **Card edge** is now an independent Zener component: `components/AppleII/AppleIIBus_Edge/`
  (footprint copied from the prior board + a **full, canonical //e-named 50-pin symbol** so it can
  be lifted cleanly into another project as a real slot connector; pin 35 COLORREF/M2B0[IIgs],
  pin 39 USER1/M2SEL[IIgs], pin 19 SYNC slot-7). Instantiated in `modules/mechanical.zen` as
  **J_SLOT**, all 50 fingers **unconnected** (mechanical only). No `/mnt/c` dependency. Builds clean.
