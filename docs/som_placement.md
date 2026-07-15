# Tang Mega 60K/138K SOM — connector & mounting-hole placement

Physical placement of the SOM's board-to-board connectors and mounting holes, for laying out
the carrier's mating side. **Confidence: high** — derived from the two official dock
interactive-BOMs (`03_Designator_drawing/*_ibom.html`, LZString-decompressed) which agree
pin-for-pin, cross-referenced with the SOM assembly drawing's text layer for the C2399/C2400/
BTB9900 identities, and corroborated by the SOM mechanical drawing (`04_Mechanical_drawing/
Tang_Mega_138K_60K_SOM.pdf`): hole rectangle 41.00×31.00 mm and C2399↔C2400 centre-to-centre
29.41 mm both match the drawing dimensions exactly.

## Coordinate frame

All coordinates are **mm, relative to the centre of the 4-hole mounting rectangle** (the datum),
as seen **looking down at the top of the carrier with the SOM mounted on top** (standard mezzanine).
`+x = right, +y = down` (KiCad top-view convention). In this reference orientation **BTB9900 is on
the left, C2399 on top, C2400 on the bottom, and the "C" opens to the right.**

You may rotate the whole SOM footprint freely when you place it — rotate all coordinates together.
The **invariants** (connector identity, pin-1 corner, and which row is inner/outer of the C) hold
under any rotation. Only *mirroring* (mounting the SOM on the opposite board face) flips inner↔outer.

## Board & mounting holes

- SOM board outline ≈ **45 × 35 mm**, roughly centred on the datum → spans (−22.5,−17.5)…(+22.5,+17.5).
- **4 × Ø2.15 mm mounting holes**, a **41.00 × 31.00 mm** rectangle (inset ~2 mm from the edges):

| Hole | (x, y) |
|---|---|
| top-left     | (−20.50, −15.50) |
| top-right    | (+20.50, −15.50) |
| bottom-left  | (−20.50, +15.50) |
| bottom-right | (+20.50, +15.50) |

## Connectors

All three cluster on the **left half** of the SOM (x ≈ −21…+3); the right half (the open mouth of
the C) carries no connectors. Pad field of each 100-pin part is 19.6 mm long (50×0.4 mm) × 3.2 mm
(2 rows); the 80-pin is 15.6 mm × 3.2 mm. Pin-1 is at the end of the P1-row nearest BTB9900.

| SOM ref | pins | orient | body centre (x,y) | pad-field span | pin-1 corner | pin-1 row |
|---|---|---|---|---|---|---|
| **C2399** | 100 | horizontal (top)    | (−6.47, −14.67) | x[−16.3,+3.3] y[−16.2,−13.1] | (−16.27, −13.13) | **INNER** (y≈−13.1) |
| **BTB9900** | 80 | vertical (left)     | (−19.85,  0.00) | x[−21.4,−18.3] y[−7.8,+7.8]  | (−21.39, −7.77)  | **OUTER** (x≈−21.4) |
| **C2400** | 100 | horizontal (bottom) | (−6.47, +14.74) | x[−16.3,+3.3] y[+13.2,+16.3] | (−16.27, +16.28) | **OUTER** (y≈+16.3) |

Row → edge, per connector (row = the P-number half; see [btb_som_pinmap.md](btb_som_pinmap.md)):

- **C2399** (top): P1–P50 row = **inner** (toward SOM centre); P51–P100 row = outer (toward top edge).
- **C2400** (bottom): P1–P50 row = **outer** (toward bottom edge); **P51–P100 row = inner**.
- **BTB9900** (left): P1–P40 row = outer (toward left edge); P41–P80 row = inner.

## The orientation finding (why this matters)

On **C2400**, the "awkward" pins — all 16 BANK9 **1.5 V** balls (P52–P86), the ADC (P92–P98), and
the config pins (P69–P75) — live on the **P51–P100 row = the INNER edge of the C**, facing the SOM
interior. The **clean SDRAM1 field (P1–P50) is the OUTER row**, facing the board perimeter.

This is the favourable case: the 100 MHz SDRAM1 bus escapes **outward** into open board (short, clean,
length-matchable), while the timing-trivial 1.5 V/ADC/config pins **via-drop inward under the SOM**
(they don't care about the stub/length). See `tools/pinmap_crossdie.py` for per-ball capability/length.

```
        BTB9900          C2399  (top, P1-50 row = inner)
        (left,           ┌──────────────────────────┐  ← P51-100 (outer)
         vertical)    1──┤ P1-50 .......... inner    │
      ┌─┐  P1-40(outer)  └──────────────────────────┘
      │ │1
      │ │           · datum (0,0) = hole-rect centre      C opens right →
      │ │           (SOM interior / FPGA above)
      └─┘  P41-80(inner) ┌──────────────────────────┐  ← P1-50 (outer)
                      1──┤ P51-100 ....... INNER     │  ← *awkward pins* (BANK9 1.5V/ADC/cfg)
                         └──────────────────────────┘
                         C2400 (bottom)
   ●(−20.5,−15.5)  holes  ●(+20.5,−15.5)   ·   ●(−20.5,+15.5)   ●(+20.5,+15.5)
```

## Routing & placement strategy (layout phase)

FR4 prop delay ≈ **6–7 ps/mm** (inner stripline ~7, outer microstrip ~6); max flight across the
178 mm board ≈ **1.2 ns** — 6–8× smaller than any interface period. So **total signal delay is
never the binding constraint on this board**; placement is free from a delay standpoint, and skew
is the only thing to manage. Everything here is delay-tolerant:

| Interface | Rate / type | Total-delay budget | Skew budget | Match to |
|---|---|---|---|---|
| **SDR SDRAM** (AS4C16M16SA-**7B**, ≤143 MHz) | common-clock, latency-absorbed | ~5 ns one-way (≈ >700 mm) → **whole board** | tCK−tIS−tIH ≈ **4.7 ns @143 / 7.7 ns @100** | ±5–10 mm (30–60× overkill) |
| **CH569 HSPI** (120 MHz SDR) | **source-synchronous** | **irrelevant** (clock flies with data) | ~½ UI (several ns) | ±~5 mm; keep <~75–100 mm for crosstalk |
| **USB3 SS** (5 Gbps) | diff, embedded clock | **as short as possible** | intra-pair **<5 mil (~0.13 mm)** | the real constraint |
| **USB2** (FT2232, 480 Mbps) | diff, robust | forgiving (inches) | loose | 90 Ω diff, no stubs |
| JTAG / UART / Apple bus | ≤~30 MHz / 1–2.8 MHz | whole board | none meaningful | route freely |

SDRAM AC (datasheet): tAC 5.4 ns, tOH 2.5 ns, tIS ≈1.5 ns, tIH 0.8 ns. HSPI = **SDR, not DDR**,
source-synchronous (3.8 Gbps = 32 × 120 MHz × 1; TX/RX clock forwarded) — per the CH569 datasheet.

### Priority order (tightest → loosest)

**USB3 SS ≫ CH569 30 MHz crystal > HSPI ≫ SDRAM ≈ USB2 > JTAG / UART / Apple bus.**

- **SDRAM is the most forgiving thing on the board** — common-clock, ns-scale skew budget, flight
  absorbed by latency. **Deprioritise its placement freely**, especially **SDRAM1** (alone on
  C2400): put it wherever routing falls out, trivial or no length-matching. SDRAM0 (BANK1) shares
  C2399 with the HSPI (BANK2) egress, so it neighbours the HSPI fan-out but is equally deprioritisable.
- **The demanding part of CH569 is NOT the HSPI** (source-sync SDR, as loose as the SDRAM) — it's
  the **USB3 SS pairs** and the **30 MHz crystal** (jitter feeds the USB3 PLL). The HSPI's slack is
  what *buys* the freedom to place CH569 for USB3.

### Placement plan

- **CH569 hard against the board edge at its USB-C**, oriented **USB3 side → connector** (90 Ω diff,
  <5 mil intra-pair, no stubs, continuous ground, guard moat, 100 nF AC-couple on TX) and **HSPI
  side → SOM**. The HSPI 32-bit bus stretches back to BANK2 (C2399 / BTB9900) — its forgiving budget
  lets CH569 live at the connector, not the SOM. Crystal in its own quiet pocket beside CH569, away
  from the SS pairs and the 32 HSPI lines.
- **SDRAM takes whatever's left** — under the SOM, far corner, wherever.
- **Opening-direction degree of freedom:** the C opens along the *axis* of C2399/C2400, so a chip
  placed in/toward the opening sits **end-on** to those connectors and can take **both rows** with a
  clean parallel fan-in (no outer-crosses-inner layer dance). Broadside placement forces the far row
  to cross the near row. Use end-on when a chip needs both rows; broadside-outward (outer row → open
  board) when one row suffices (e.g. SDRAM1, mostly its outer row).

### USB connectors — group both USB-C on the same edge

The **USB3 (CH569)** and **FT2232 (JTAG + UART programmer/console)** USB-C ports belong on the
**same board edge** — user-facing I/O grouped for cabling/enclosure. Both are **data-only** (board
is 12 V-barrel powered) → CC-pulldown resistors + ESD on each; no power-input routing.

- **USB3 gets the clean fenced corner** (above). Place the **FT2232 beside it on the same edge but
  outside the USB3 SS keep-out** — the SS moat / reference-plane island separates them.
- **FT2232 placement follows its USB-C, not its JTAG target:** keep **USB2 D+/D− short** to the
  connector (90 Ω diff — forgiving, but the fastest thing FT2232 does at 480 Mbps), and let the slow
  single-ended signals stretch:
  - **JTAG (ch A: TCK/TMS/TDI/TDO) → BTB9900** (BANK12, P3–P9, SOM left edge) — a long cross-board run
    is fine at JTAG speeds.
  - **UART (ch B) → console** header — route freely.
- Keep USB2 D+/D− from running **parallel to the USB3 SS pairs** (cross at 90° if unavoidable); USB2
  at 480 Mbps is an order of magnitude below USB3 and coexists fine as long as it stays out of the SS fence.

### Power — opposite edge from the USB connectors (external design input)

**External requirement:** the power circuitry (barrel jack → input protection → **MP2315** buck 5 V →
**AMS1117** 3.3 V LDO + bulk caps) sits on the **opposite board edge from the USB connectors.** Adopted —
board becomes **power end ↔ SOM + Apple bus (middle) ↔ USB end.** Rationale and consequences:

- **Primary reason = EMI/SI.** The MP2315 switching node is the board's main noise source; the USB3 SS
  pairs and the CH569 30 MHz crystal are the most noise-sensitive nets. Maximum separation keeps switcher
  noise off both by construction. (Bonus: power cable at one end, USB at the other.)
- **The 5 V rail is short — only two destinations:** the **SOM `VBUS_SOM` (C2400 P91/93/95/97/99**,
  ≈1 A for the 3–6 W load) and the **local AMS1117 input** in the power corner. It does **not** reach the
  USB end (host-supplied VBUS) or the Apple interface (5 V tapped locally at the CPU socket). So the heavy
  5 V stays near the power end / SOM — a short mid-board run.
- **The 3.3 V rail is the distributed one:** LDO → per-bank **VCCIO** (VCCO_1/2 = C2399 P1, VCCO_6/7/8 =
  C2400 P1, VCCO_4/5 = BTB9900 P29, +VCCIO_138B5 = C2400 P67 if BANK9 used) + **CH569 + FT2232** at the USB
  end + level-shifter low side. Low current but it traverses the board — **plane/pour it**, local decoupling
  at each load. Bulk caps at the regulators.
- **External 5 V sources (not from the power circuitry):** Apple level-shifter **high side = CPU-socket 5 V**
  (references the Apple II's own rail → correct translation thresholds, and offloads that current from the
  barrel supply); each **USB-C VBUS = host-supplied** (Pi5 for USB3, PC for FT2232) — used for **VBUS-present
  detect only** (Rd on CC + VBUS sense + ESD). The carrier never drives VBUS on either port.

### Stackup — 6-layer for now (8-layer is the documented escalation)

**Decision:** build on **6-layer, `SIG-GND-PWR-SIG-GND-SIG`** (plane-isolated signal layers); revisit
8-layer **only if a routing trial shows 6 can't fit** — decide empirically at the routing phase, don't
pre-commit.

**Why this 6-layer arrangement** (not the 4-signal `SIG-GND-SIG-SIG-GND-SIG` variant): the board is
**~85 % wide parallel buses** (SDRAM0/1 ~39 each, HSPI ~40, Apple ~50 = ~170 of ~200 nets), which want
to route *together, one direction, length-matched*. The 4-signal stack forces its two adjacent middle
layers to route **orthogonally (H/V)** to tame broadside crosstalk — hostile to buses. At 6 layers you
can't have 4 *isolated* signal layers (needs 7+), so it's **3 plane-isolated layers (this) vs 4-with-a-
pair** — and for a bus board, 3 clean bus-friendly layers win.

**Layer roles** (match layer quality to signal criticality):
- **L1, L6** (SIG, **ground-referenced**): fast buses (SDRAM, HSPI) + **USB3 SS** + escapes.
- **L4** (SIG, **power-referenced**): the **Apple bus** + slow/forgiving nets — at 1–2.8 MHz the power
  reference and any plane split are immaterial. (The one compromised layer gets the one bus that can't feel it.)
- **L3** (PWR): keep **solid 3.3 V under L4's bus regions**; push the 5 V island up into the power corner.
- **Dielectric** (per the arrangement being used): thin S–G / P–S / G–S sandwiches, thick between →
  per-layer impedance control + symmetric (warp-resistant). Trades away GND–PWR buried capacitance — fine,
  the PDN is light (SOM self-powers its core); discrete decoupling covers it.

**Escalation → 8-layer** if three signal layers can't absorb ~170 bus signals + the 0.4 mm escapes:
`SIG-GND-SIG-GND-PWR-SIG-GND-SIG` — **4 plane-isolated signal layers** (no H/V tax), 3 GND + 1 PWR with
buried cap, L3 dual-ground-referenced (cleanest). Cost delta at proto qty is tens of dollars.

**Open DFM item:** confirm whether the 0.4 mm DF40 escape needs **microvias / via-in-pad (HDI)** or if
through-vias suffice (the 3.2 mm inter-row gap suggests maybe) — that via decision is the real cost lever,
~independent of 6 vs 8 layers. Check with the fab before committing the escape strategy.
- **Keep the switcher hot loop tight locally** (input cap–inductor–FET–output cap, minimal loop area,
  small switch node) — separation handles far-field, loop discipline handles near-field.
- **Filter the CH569 USB3 analog-PHY supply locally** (ferrite + caps at the chip); the long run from the
  far regulator + local filtering keeps switcher ripple off the PHY.
- **Thermal watch:** the AMS1117 drops 5→3.3 V (≈1.7 V × I₃ᵥ₃); if the 3.3 V rail (VCCIO of the fast buses
  + CH569 + FT2232) approaches ~0.5–1 A that's ~1–2 W in a SOT-223 — give it copper pour, and consider a
  switching 3.3 V reg if the load is high. Budget the 3.3 V current before committing the LDO.

## Connector pin-1 / footprint handedness — RESOLVED (2026-07-08)

Placing the three DF40 receptacles, a **pad-numbering bug** surfaced in the imported
**100-pin footprint** (`components/HRS_Hirose/DF40C-100DS-0_4V_51`). The DF40 receptacle is
**NOT polarized** (Hirose datasheet Note 4) — it is mechanically symmetric, so pin 1 is purely a
numbering convention and a mirror-flipped import is silent.

**Ground truth** = the dock interactive-BOM (`03_Designator_drawing/*_ibom.html`, LZString-decompress
in pure Python; pads carry a `pin1` flag + world `pos`), which mates with the real SOM. Findings, all
relative to each connector body centre:

| Conn | dock pin-1 | our footprint pin-1 (native) | verdict |
|---|---|---|---|
| **80-pin** (BTB9900) | (−1.54, −7.8) @ 270° → left-top | native (−7.8, +1.32) = left | **pin-1 corner OK** |
| **100-pin** (C2399/C2400) | (−9.8, +1.54) = **left**/+y | (+9.8, +1.6) = **right**/+y | **mirror-numbered — FIXED** |

The 100-pin pin-1 corner was a pure left–right mirror; fixed to the left/+y corner (matches the dock).

**Zigzag numbering fix (2026-07-11 — both footprints).** After the mirror fix the pads were still
numbered in a **serpentine / U-shape** order (top row 1→N/2 left-to-right, bottom row N→N/2+1 back
left-to-right). That is wrong for DF40: the real part is an **aligned zigzag** — **odd pins (1,3,5…)
along one row, even pins (2,4,6…) along the other, with pin 1 and pin 2 facing each other** at the
left end (datasheet Note 4: non-polarized; 0.4 mm pitch, B = 19.6/15.6 mm ⇒ 50/40 pads per row,
rows column-aligned). **Fix (applied to both `.kicad_mod`, `tools/floorplan_seed.py` untouched):**
for column `k` (0 = leftmost, pitch 0.4 mm), top-row pad = `2k+1`, bottom-row pad = `2k+2`. Pin 1
does not move (stays left/+y), so the pin-1 silk dot is unchanged. `btb_som_pinmap.md`/`som_btb.zen`
use the real Hirose contact numbering, so correcting the footprint makes the existing net→pad map
physically correct — **no `.zen`/pinmap change needed.**

⚠ **This is a footprint-body edit** — a plain `pcb layout` sync will NOT pull it (bodies are
preserved across regen). Close KiCad, then `rm -rf layout && pcb layout appletini_mega.zen --no-open
&& python3 tools/floorplan_seed.py` for a clean regen.

**Placement rotations (in `tools/floorplan_seed.py`):** CN1 (BTB9900) = **270°**, CN2 (C2399) /
CN3 (C2400) = **0°**. ⚠ **The pcb/KiCad layout pipeline rotates pad POSITIONS by the footprint
angle but NOT the pad bodies** — a rotated footprint (CN1) also needs the angle set on every
*pad* (`(at x y 270)`), or the pads render in their unrotated orientation. `floorplan_seed.py`
does this automatically for any footprint it rotates. ⚠ `pcb layout` preserves existing footprint *bodies* across regen — after a
footprint edit you must **`rm -rf layout`** (clean regen) to pull the change.
