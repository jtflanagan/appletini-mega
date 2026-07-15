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
endpoints — J2 origin = `(TAB_X, body_bottom + 3.175)`. `TAB_X` is derived from **`TAB_EDGE_GAP =
9.525 mm (0.375″)` between the tab's right edge and the card's right edge** → tab on the **right side**
of the card, centre at 110.49 mm (tab spans X[78.10, 142.88]). Change `TAB_EDGE_GAP` if the target
slot wants the tab elsewhere.
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
| **SDRAM U_LO** (32-bit bank) | 1× AS4C16M16SA | **C2399** (BANK1/2) | Data DQ[15:0] + DQM0/1 bank-local, escape toward C2399. **Sources the SHARED cmd/clk/addr bus** that also feeds U_HI (see the shared-bus note, 2026-07-10). |
| **SDRAM U_HI** (32-bit bank) | 1× AS4C16M16SA | **C2400** (BANK6/7/8) | Data DQ[31:16] + DQM2/3 bank-local; C2400 clean field (P1–P50) is the OUTER row → escapes outward. Its cmd/clk/addr are **not** bank-local — they arrive via the shared bus from U_LO/C2399. |
| **USB3 bridge** | CH569 + 30 MHz xtal + USB3 conn | HSPI connector (BANK2 region) | short 90 Ω SS pair to the edge connector |
| **Programming** | FT2232H + 12 MHz xtal + USB-C | config/JTAG balls | |
| **Power** | 12 V barrel → 2× MPM3620A buck (5 V + 3.3 V) | barrel at an accessible edge | integrated-inductor modules (shielded); keep the CIN hot-loop tight and don't slot the ground reference under BTB traces — see **Power block placement** below |
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

## Concrete floorplan v1 (2026-07-08) — SUPERSEDED by v2 below

> **Superseded 2026-07-09 by floorplan-v2** (SOM centered; USB/bridges moved to the LEFT
> against BTB9900; SDRAM to the right; CPU header near the slot). Kept for the rationale
> (SOM orientation, top-mount, grounding) which v2 inherits unchanged. Read v2 for the
> actual block placement.

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

## Concrete floorplan v2 (2026-07-09) — CURRENT

Chosen after the first wiring pass. Same SOM orientation/mount/grounding decisions as v1
(all still locked), but a different block arrangement that is **more bank-coherent**: the two
subsystems that talk to **BTB9900** (the SOM's LEFT connector) — **CH569/HSPI** (BANK5) and
**FT2232/JTAG+config** (BANK12/3) — move to the **left** so their buses escape straight into
BTB9900; the two **SDRAMs** (C2399 BANK1/2, C2400 BANK6/7/8, the top/bottom connectors) sit to
the **right** in the C's mouth; the Apple-bus glue fills the far right. This drops the long
cross-board HSPI/JTAG runs that v1 implied (v1 put USB on the right, away from BTB9900).

Working frame: **origin = bottom-left, +x right, +y up, mm.** Board = `(0,0)…(152.4, 69.85)`.

```
 y69.85 ┌───────────────────────────────────────────────────────────────┐
        │ ┌─ POWER ──┐                                ┌ SDRAM0 → C2399 ┐  │
        │ │ barrel   │        ┌──── SOM 45×35 ────┐   │  (AS4C16M16)   │  │
 ~50    │ │ MP2315   │      C2399(top) ▔▔▔▔▔▔▔▔▔   └────────────────┘     │
        │ │ AMS1117  │   B  ┌───────────────────┐   ┌── Apple glue ──┐   │
        │ ├──────────┤   T  │  FPGA (under SOM) │M  │ 5×'245 2×'T45  │   │
 ~35    │ │ CH569 SS►│──9│──│                   │►O │ deadman        │   │→ (ribbon
        │ │ 30M xtal │   9  │                   │U  └────────────────┘    │  drops to
        │ ├──────────┤   0  └───────────────────┘   ┌ SDRAM1 → C2400 ┐   │  CPU skt)
 ~18    │ │ FT2232   │   0  C2400(bot) ▁▁▁▁▁▁▁▁▁    │  (AS4C16M16)   │   │
        │ │ USB-C ►  │                              └────────────────┘   │
 ~13    │ └──────────┘   ┌═ 2×20 CPU HEADER (horiz, near slot) ═┐         │
 ~12    │ · · · · · · · · · · · finger keep-out · · · · · · · · · · · · · ·│
 y0     └═════════════════[ slot fingers, bottom edge ]═══════════════════┘
       x0  ← left: power + the two BTB9900 bridges          right: SDRAM + glue →  x152.4
```

**Block targets** (bottom-left origin, mm; ± a few mm — refine in KiCad):

| Block | X range | Y range | Anchor / why |
|---|---|---|---|
| **SOM body** (45×35) | ~53.7 – 98.7 | ~17.4 – 52.4 | **datum = board centre (76.2, 34.9).** Centered; C opens right into the SDRAM field. |
| — BTB9900 (CN1, L, vert) | ~56.4 (x) | ~27 – 43 | SOM left edge → faces the left bridges; HSPI(BANK5)+JTAG/config(BANK12/3) escape left. |
| — C2399 (CN2, top, horiz) | ~63 – 76 | ~48 – 51 | SDRAM0 (BANK1/2). |
| — C2400 (CN3, bot, horiz) | ~63 – 76 | ~19 – 22 | SDRAM1 (BANK6/7/8). |
| **Power** | 2 – 28 | ~42 – 68 | Upper-left corner; barrel on the left short edge. |
| **CH569 + SS USB3** | 2 – 30 | ~24 – 42 | Mid-left; short HSPI run right into BTB9900; SS pair to a left-edge USB conn. |
| **FT2232 + USB-C** | 2 – 30 | ~4 – 24 | Bottom-left; JTAG/UART up into BTB9900. |
| **SDRAM U_LO** (→ C2399) | ~100 – 126 | ~38 – 52 | Upper-right, against C2399 (top). Data+DQM bank-local BANK1/2 (+2 borrowed BANK4); sources the shared cmd/clk/addr bus. |
| **SDRAM U_HI** (→ C2400) | ~100 – 126 | ~16 – 30 | Lower-right, against C2400 (bottom). Data+DQM bank-local BANK6/7/8; shared bus arrives from U_LO/C2399 — keep the two devices vertically close to bound the shared-bus stubs. |
| **Apple glue** (5×'245, 2×'T45, deadman) | ~126 – 150 | ~16 – 55 | Far right, past the SDRAMs. A-side ← FPGA GPIO on C2400 spill. |
| **2×20 CPU header** | ~95 – 146 | ~13 – 19 | **Horizontal, low/right near the slot** — ribbon drops toward the //e CPU socket. |
| **Slot fingers** | ~78 – 143 | 0 – ~2 | Bottom edge (tab centre 110.49). Floating (mechanical only). |

**Change vs v1 / open at KiCad time:**
- USB/bridges moved **right → left**; SDRAM moved **mouth → clean right field**; CPU header moved
  from the **top edge** (v1 lock) to **horizontal near the slot** — this revises the v1 "machine-facing
  end = top edge" note; the ribbon now exits low toward the motherboard CPU socket. Confirm the ribbon
  reach and that the header/glue clear the finger keep-out (y≲12).
- "SDRAM0 near C2 / SDRAM1 near C1" (as stated) is read as U_LO↔C2399(top), U_HI↔C2400(bottom) —
  the *data*+DQM halves are forced by bank locality (U_LO=BANK1/2, U_HI=BANK6/7/8), matching the
  wiring in `appletini_mega.zen`. As of 2026-07-10 the two are one 32-bit bank on a shared
  cmd/clk/addr bus — see the shared-bus note below.
- Seeder (`tools/floorplan_seed.py`) updated: SOM anchor datum → board centre (76.2). Trays are still
  a staging aid below the board — drag each labeled cluster to its target above.

## SDRAM = one 32-bit bank on a shared bus (2026-07-10)

The two AS4C16M16SA x16 devices were formerly wired as **two independent 16-bit buses**
(each with its own command/clock/address, point-to-point and bank-local). They are now
**teamed into a single 32-bit-wide bank** (`modules/sdram.zen`), the standard way to build a
32-bit datapath from two x16 parts:

- **Shared, one net → BOTH devices:** `CLK`, `CKE`, `A[12:0]`, `BA[1:0]`, `N_CS`, `N_RAS`,
  `N_CAS`, `N_WE`. Sourced from **U_LO's BANK1/2 balls on C2399** and fanned across to U_HI.
- **Independent:** the 32 data bits (U_LO=DQ[15:0], U_HI=DQ[31:16]) and the **4 DQM byte
  write enables** (DQM0/1 on U_LO, DQM2/3 on U_HI — one per byte lane of the word).
- U_HI's 21 former command/address balls on C2400 are **freed** (dropped from the ball map).

**Floorplan / routing consequences:**
- The shared cmd/clk/addr bus is **no longer point-to-point or bank-local** — it spans from
  C2399 (top) across the right field to C2400 (bottom). Route it as a **fly-by / T-topology
  multidrop bus**, and place **U_LO and U_HI vertically close** (they already sit ~8 mm apart,
  ~38–52 and ~16–30 mm) to bound the stub/branch lengths.
- Series **termination** on the shared address/clock lines now matters (two loads on a shared
  net at 143 MHz) — reserve pad space near the branch point / at the far device. It did not
  matter before (single-load point-to-point).
- **CLK** is the most sensitive shared net: match U_LO and U_HI clock-branch lengths, or
  absorb the residual skew in the FPGA (per CLAUDE.md's skew guidance — never in carrier
  copper beyond what's matchable).
- Data + DQM stay bank-local point-to-point, unchanged: U_LO escapes toward C2399, U_HI's
  data escapes outward on the C2400 clean field (P1–P50).

This is an intentional trade: a shared bus costs a cross-field multidrop route + termination
but halves the FPGA ball count for control (~21 balls freed) and gives a true 32-bit word with
4-byte write granularity. SDRAM remains the most forgiving of the board's buses.

## Power block placement (2026-07-12)

The power stage is **two `MPM3620A` integrated-inductor buck modules** off the protected 12 V
rail — 5 V and 3.3 V, independent (not cascaded) — plus the shared input-protection chain
(barrel → PPTC fuse → reverse-polarity P-FET → SMBJ12A TVS). See `modules/power.zen`. The
inductor + VCC/bootstrap caps are *inside* each module (QFN-20 3×5 mm), so a rail is only **5
external parts**: `CIN` (10 µF), `COUT` (22 µF), `REN` (EN pull-up), and the `RTOP`/`RBOT` FB
divider. `SW`/`BST`/`VCC` are left unconnected (no external parts).

**Why proximity to the bucks is low-risk (and what actually is):** the shielded module buries the
switching node and inductor, so radiated near-field is low — the real aggressor is the **`CIN`
input hot-loop** (highest di/dt on the board), the rail traces, and the module's ground return.
"Keep BTB traces away from power" therefore means *keep them off the same layer as the hot-loop/
rails and out of the buck's ground return* — a stackup constraint you can satisfy at almost any
X/Y placement, not a keep-out that pins the floorplan. See the BTB-vs-power reasoning in the
grounding discussion above; the forgiving BTB bundles (JTAG/config/UART, Apple-bus spill) are the
ones that may share turf with power, while the SDRAM shared clock/address bus wants breathing room.

### Per-module escape map (real `MPM3620AGQV-Z` pads, +y up)
```
              SW ···················· OUT        <- TOP edge = OUTPUT corner (pad 9)
      FB(1) -+                          +- NC(10)
     VCC(2) -+       MPM3620A           +- BST(11)
    AGND(3) -+       (2.9 x 3.7 mm)     +- PGND(12)
             PG  EN  IN  NC  PGND  PGND         <- BOTTOM edge = INPUT + POWER-GND
```
Key fact: **IN (pad 16) and PGND (pads 13/14, + 12 on the right edge) share the bottom edge** —
that is where the `CIN` hot-loop lives, and it is the single most important placement on the block.
`OUT` (pad 9) is the top-right corner; `FB` (pad 1) is mid-left.

### The 5 passives, per rail
| Part (`power.zen`) | Value | Placement | Why |
|---|---|---|---|
| `*_CIN` | 10 µF 0805 | hug the bottom edge, straddle IN(16)↔PGND(13/14) | the hot loop — minimize IN→cap→PGND area |
| `*_REN` | 100 k 0402 | at EN(17), tie up to the P12V/IN rail | EN and IN share the edge — trivial |
| `*_COUT` | 22 µF 0805 | at OUT(9) top-right corner, return to PGND(12) | output cap; its return is the right-edge ground |
| `*_RTOP`/`*_RBOT` | 0402 divider | off the left edge at FB(1); RBOT ground to AGND(3) | keep the FB node tiny and quiet; tap RTOP from COUT/OUT with a thin sense trace |

### Dual-rail arrangement
Both modules same orientation, input edges facing the protection chain / P12V feed, outputs
escaping toward their loads. `D_IN` (TVS) sits at the P12V node where the bus splits to the two
`CIN`s, so it clamps the whole bus.
```
 barrel -> F_IN -> Q_RP -> D_IN --+-------------------+---   P12V pour
        (fuse)  (P-FET) (TVS)      |                   |
                             [CIN 10uF]           [CIN 10uF]
                         ||=IN | PGND=||       ||=IN | PGND=||
                         ||  U_BUCK5   ||       ||  U_BUCK33  ||
                         ||=====OUT====||       ||=====OUT====||
                      REN | FB-div |          REN | FB-div |
                        [COUT 22uF]             [COUT 22uF]
                           |                       |
                          P5V ->                 P3V3 ->
                     (VBUS_SOM +             (VCCIO / SDRAM /
                      Apple 5V side)          CH569 / FT2232)
```

### Input-protection chain placement (jack → `F_IN` → `Q_RP` → `D_IN`)

The chain's internal geometry matters for one reason: **the surge return loop**. When `D_IN`
clamps, it dumps tens of amps of di/dt into GND, and that current has to get back to the barrel
jack's **sleeve** pin. Whatever area that loop encloses becomes `V = L·di/dt` injected into the
board's ground reference — the same reference the SOM and SDRAM use. It is set by geometry, not
by part choice, and nothing downstream undoes it.

**The plane is what makes `D_IN`-at-the-P12V-split legal.** The stock app-note rule is "put the
TVS at the connector," and on a 2-layer board it is correct — the return has to crawl back through
whatever copper happens to exist. Here the solid GND plane under the power block (next section)
lets the surge return image-follow the outbound trace, so the loop stays tight even with `D_IN`
at the far end of the chain, clamping the whole bus where it splits to the two `CIN`s. That is
what buys the arrangement above — but it is **conditional**, and rules 1–2 are the condition.

1. **`D_IN`'s anode vias straight down into the plane** — a small via array at the pad, not a
   trace running off to a distant via. Same for the **jack's sleeve pin**. Those two pads are the
   surge loop's endpoints; everything else here is detail.
2. **The plane between the jack and `D_IN` must be unbroken.** "Don't slot that plane" (stack
   point 3 below) is usually said about the buck's PGND return; it applies at least as hard to the
   surge path. A split anywhere under the chain forces the return to detour around it and the loop
   area you were relying on the plane to keep small comes straight back.
3. **Physical order = schematic order, one direction, no doubling back:** jack → `F_IN` → `Q_RP` →
   `D_IN` → P12V out to the `CIN`s, as a straight run *away* from the jack. (The seeder's rough
   draft currently lands `F_IN` to the *left* of the jack with `Q_RP` back underneath it, so the
   path reverses on itself — harmless in a draft, worth straightening at real placement.)
4. **Keep the chain compact.** Length here is inductance in the only path that carries surge
   current.
5. **`R_RP`/`R_RP_TOP` hug `Q_RP`'s gate.** The divider midpoint is a ~50 kΩ node sitting next to
   the highest-di/dt event on the board. Keep the gate trace short and off `D_IN`'s clamp path and
   the `CIN` hot loops. The seeder already stacks the pair directly above/below `Q_RP`.
6. **Don't split the chain across faces.** The jack is tall → top face per the design rule above.
   The chain is all low-profile SMD and *could* go bottom, but every face change adds vias and loop
   area to the surge path. Keep it on top with the jack.
7. **Copper.** ~0.68 A nominal (both rails, ~90 % eff), 2.2 A at `F_IN`'s trip point — that alone
   wants ~1 mm of 1 oz outer — and `D_IN`'s clamp current is tens of amps for microseconds. Pour
   this path; don't route it at minimum width, and stitch generously at any layer change.
8. **Mechanical.** Someone will yank the DC cable. Generous annular ring on the jack's
   through-holes; don't crowd 0402s into the strain path.

### What the 6-layer stack buys (the 2-layer references can't show this)
1. **Solid GND plane on the layer directly under the modules** = the return reference; PGND
   current returns straight down, not sideways through a pour. This alone handles most of the
   "buck near BTB traces" concern.
2. **Via-stitch every PGND pad straight into that plane** (small array at pads 12/13/14) — also
   the thermal path (both rails are lightly loaded, ~55 % / ~28 % of 2 A, so this runs cool).
3. **Don't slot that plane.** If a P12V/P5V island is needed, put it on a *different* layer than
   the one nearby BTB signals reference — keep the ground reference under the power block unbroken.
4. **AGND vs PGND:** both land on `GND` in the netlist, but on copper reference `RBOT`/FB to the
   AGND(3) pad and stitch AGND to the plane at one quiet point near the module.

### Seeder support
`tools/floorplan_seed.py` → `place_power()` drops this whole cluster pre-assembled (module IC + 5
passives at the pin positions above, protection chain fanned in from the jack). `MODULE_PINS` holds
the IN/OUT/FB/EN pad coordinates — regenerate it if the module footprint changes. The block
currently anchors at the **upper-right notch** (barrel jack on the notch short-edge so its DC cable
clears via the notch); this supersedes the v2 "barrel on the left short edge" note — power location
is still a free variable, but the *internal cluster geometry* above is placement-independent.

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
