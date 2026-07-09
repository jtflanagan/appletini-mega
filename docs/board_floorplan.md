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

`Board()` has no outline parameter — the **edge cuts are drawn in KiCad**, and Zener preserves manual
placement/outline across regenerations. So: `pcb layout appletini_mega.zen` generates the real board
(all footprints + ratsnest) and opens KiCad; draw the 6.000"×2.750" outline + finger tab, place the
`AppleIIBus_Edge` slot footprint on the bottom edge, then floorplan the big blocks. `pcb layout --temp`
gives a throwaway practice board. **Open method:** bring the card edge in as a Zener component
(footprint + 50 NC pads, excluded from BOM) so the toolchain always places it — vs. a hand-added
mechanical footprint. Leaning toward the Zener component.

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

## Open questions (to resolve as we floorplan)

1. **SOM face + position** (first domino), then the derived placement of SDRAM0/1, CH569, FT2232.
2. **Connector egress plan** — which edge each of {USB3, 2× USB-C, barrel jack, CPU ribbon} sits on,
   given the card is vertical inside the case, with the finger tab down.
3. **Slot pitch / height budget** for the //e — does the SOM stack (3 mm standoff + module height)
   clear the neighboring card?

## Ingested (2026-07-08)

- **Card edge** is now an independent Zener component: `components/AppleII/AppleIIBus_Edge/`
  (footprint copied from the prior board + a **full, canonical //e-named 50-pin symbol** so it can
  be lifted cleanly into another project as a real slot connector; pin 35 COLORREF/M2B0[IIgs],
  pin 39 USER1/M2SEL[IIgs], pin 19 SYNC slot-7). Instantiated in `modules/mechanical.zen` as
  **J_SLOT**, all 50 fingers **unconnected** (mechanical only). No `/mnt/c` dependency. Builds clean.
