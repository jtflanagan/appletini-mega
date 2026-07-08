# CPU socket connector — 6502 / 65C02 / 65C816 pinouts

The carrier interfaces to the target Apple II/IIgs by **replacing its CPU**: a soft CPU in the
GW5AT-60 drives the machine's bus through the vacated CPU socket. Physically that is a **2×20
0.1″ (2.54 mm) header on the carrier → ribbon cable → a 40-pin DIP plug** seated in the host's
CPU socket.

All three target CPUs share the **same 40-pin DIP footprint** (0.6″ row spacing), so one socket
adapter serves any of them. What differs is the *function* of a handful of pins — WDC's CMOS parts
reclaimed the NMOS 6502's `NC` and one `VSS` pin for new signals. Those deltas are the whole reason
this table exists: **the carrier must be wired to satisfy the superset**, then the soft CPU decides
which signals it actually asserts.

- **NMOS 6502** — the original Apple ][ / ][+ and early //e CPU. Pin 1 = VSS, pins 5 & 36 = NC.
- **65SC02** — the reduced-core CMOS 6502 (Rockwell/GTE/NCR "SC" part), the **stock CPU in the
  //e Platinum**. ⚠ It is **pin-identical to the NMOS 6502** — pins 1/5/36 are VSS/NC, it does
  **not** have VPB/MLB/BE. "65C02" is therefore ambiguous: only WDC's "S" part adds pins.
- **W65C02S** — WDC's full CMOS part (Enhanced //e and hobbyist boards). This is the *only*
  common 6502-class part that drives the extra pins: **VPB (1), MLB (5), BE (36)**. Rockwell
  R65C02 adds the bit-manipulation *instructions* but its pinout is essentially 6502-compatible
  — verify pins 1/5/36 against the specific datasheet if you target one.
- **W65C816S** — the IIgs / accelerator CPU; same DIP-40 body but redefines 7 pins for its
  24-bit address / 16-bit modes. This is the part an accelerator most wants to emulate.

The table below shows **NMOS 6502 / W65C02S / W65C816S**. For a **65SC02** (or a plain
R65C02), read the **6502 column** for pins 1, 5, and 36 — they are VSS/NC there, not VPB/MLB/BE.

> Bus timing is trivial for this design (host φ0 is ~1.023 MHz on a //e, up to 2.8 MHz on a IIgs).
> The design constraint is **5 V TTL ↔ 3.3 V level shifting + direction control**, not speed. See
> [appletini-mega-project](../../../.claude/projects/-home-flana/memory/appletini-mega-project.md)
> for the "spill-pin" bank strategy and `CARRIER_PLAN.md` in the dock repo.

## Full 40-pin DIP pinout (all three parts side by side)

Direction is **as seen from the CPU** (I = input to CPU, O = output from CPU, I/O = bidirectional,
P = power/ground). When emulating, the FPGA takes the CPU's role, so invert this to get the FPGA
direction: CPU outputs become FPGA outputs, CPU inputs become FPGA inputs.

Physical DIP layout: pins **1–20 down the left** side, **21–40 up the right** side (pin 1 marked by
the notch; pin 40 sits opposite pin 1).

| DIP pin | NMOS 6502 | W65C02S | W65C816S | Dir | Notes |
|--:|:--|:--|:--|:--:|:--|
| 1  | VSS *(gnd)* | **VPB** | **VPB** | O¹ | 6502: ground. CMOS: Vector Pull (low during vector fetch) |
| 2  | RDY | RDY | RDY | I/O | Ready; bidirectional on CMOS (WAI drives it) — pull-up needed |
| 3  | φ1 (out) | φ1 (out) | **ABORTB** | ² | 6502/02: Phase-1 clock out. 816: Abort input (active low) |
| 4  | /IRQ | IRQB | IRQB | I | Interrupt request (active low) |
| 5  | **NC** | **MLB** | **MLB** | O³ | 6502: no-connect. CMOS: Memory Lock (active low, RMW cycles) |
| 6  | /NMI | NMIB | NMIB | I | Non-maskable interrupt (active low, edge) |
| 7  | SYNC | SYNC | **VPA** | O | 6502/02: SYNC (opcode fetch). 816: Valid Program Address |
| 8  | VCC | VDD | VDD | P | +5 V |
| 9  | A0 | A0 | A0 | O | Address bus bit 0 |
| 10 | A1 | A1 | A1 | O | |
| 11 | A2 | A2 | A2 | O | |
| 12 | A3 | A3 | A3 | O | |
| 13 | A4 | A4 | A4 | O | |
| 14 | A5 | A5 | A5 | O | |
| 15 | A6 | A6 | A6 | O | |
| 16 | A7 | A7 | A7 | O | |
| 17 | A8 | A8 | A8 | O | |
| 18 | A9 | A9 | A9 | O | |
| 19 | A10 | A10 | A10 | O | |
| 20 | A11 | A11 | A11 | O | |
| 21 | VSS *(gnd)* | VSS | VSS | P | Ground |
| 22 | A12 | A12 | A12 | O | |
| 23 | A13 | A13 | A13 | O | |
| 24 | A14 | A14 | A14 | O | |
| 25 | A15 | A15 | A15 | O | Address bus bit 15 (top of 16-bit bus) |
| 26 | D7 | D7 | D7 | I/O | Data bus bit 7. 816: also bank address (BA7) in first half-cycle |
| 27 | D6 | D6 | D6 | I/O | |
| 28 | D5 | D5 | D5 | I/O | |
| 29 | D4 | D4 | D4 | I/O | |
| 30 | D3 | D3 | D3 | I/O | |
| 31 | D2 | D2 | D2 | I/O | |
| 32 | D1 | D1 | D1 | I/O | |
| 33 | D0 | D0 | D0 | I/O | Data bus bit 0. 816: also bank address (BA0) in first half-cycle |
| 34 | R/W | RWB | RWB | O | Read/Write (high = read, low = write) |
| 35 | **NC** | **NC** | **E** | O⁴ | 816: Emulation status (high = 6502 emulation mode) |
| 36 | **NC** | **BE** | **BE** | I⁵ | 6502: no-connect. CMOS: Bus Enable (high = buffers active) |
| 37 | φ0 (in) | PHI2 (in) | PHI2 (in) | I | System clock input — the CPU's timing reference |
| 38 | SO | SOB | **MX** | ⁶ | 6502/02: Set Overflow input. 816: M/X status output |
| 39 | φ2 (out) | φ2 (out) | **VDA** | O⁷ | 6502/02: Phase-2 clock out. 816: Valid Data Address |
| 40 | /RES | RESB | RESB | I | Reset (active low) |

**Per-pin direction footnotes** (differ across parts). "6502-class" below = NMOS 6502 **and**
65SC02 (both have VSS/NC at pins 1/5/36); "WDC-S" = W65C02S and W65C816S:
1. Pin 1: NMOS 6502 & 65SC02 = **ground (P)**; WDC-S = **VPB output (O)**. ⚠ Never tie this pin to
   ground on the carrier — a WDC part drives it. (We drive VPB when emulating one; hold it low
   otherwise, since the socket pin is ground/NC.)
2. Pin 3: 6502-class & W65C02S = φ1 clock **output (O)**; 816 = ABORTB **input (I)**.
3. Pin 5: NMOS 6502 & 65SC02 = **NC**; WDC-S = MLB **output (O)**.
4. Pin 35: 6502-class & W65C02S = **NC**; 816 = E **output (O)**.
5. Pin 36: NMOS 6502 & 65SC02 = **NC**; WDC-S = BE **input (I)** — pull/drive high for normal operation.
6. Pin 38: 6502-class & W65C02S = SO **input (I)**; 816 = MX **output (O)**. ⚠ Direction reverses.
7. Pin 39: 6502-class & W65C02S = φ2 clock **output (O)**; 816 = VDA **output (O)**.

## The pins that change between parts (the delta)

These are the only positions where wiring/level-shifter direction is *not* the same for all three.
Design the carrier for the **worst case at each pin** (bidirectional or switchable shifter where a
pin is O on one part and I on another):

"6502-class" column = NMOS 6502 **and 65SC02** (identical at these pins). Design the carrier for
the **worst case** at each pin.

| DIP pin | 6502-class | W65C02S | W65C816S | Design implication on carrier |
|--:|:--|:--|:--|:--|
| 1  | GND | VPB (O) | VPB (O) | **Never ground.** VPB is a CPU output → carrier drives it (output group); firmware holds it low in 6502/65SC02 mode where the socket pin is ground. |
| 3  | φ1 out (O) | φ1 out (O) | ABORTB (I) | Direction flips: O for 6502/02, I for 816. |
| 5  | NC | MLB (O) | MLB (O) | CPU→carrier when populated; safe to leave floating for NMOS. |
| 7  | SYNC (O) | SYNC (O) | VPA (O) | Always CPU→carrier; meaning changes, direction doesn't. |
| 35 | NC | NC | E (O) | CPU→carrier (816 only); NC otherwise. |
| 36 | NC | BE (I) | BE (I) | carrier→CPU; **hold high** for normal bus operation. |
| 38 | SO (I) | SOB (I) | MX (O) | Direction flips: I for 6502/02, O for 816. |
| 39 | φ2 out (O) | φ2 out (O) | VDA (O) | Always CPU→carrier; meaning changes, direction doesn't. |

Pins **3** and **38** are the two that literally reverse direction between the 6502/02 family and
the 816 — those two shifter channels must be **direction-switchable** (or the soft CPU must know
which part it is emulating and the carrier must route them through a bidirectional shifter such as a
TXS/TXB-class device with a mode select).

## Carrier-side signal grouping (for level-shifter allocation)

Grouped by direction relative to the **soft CPU in the FPGA** (opposite of the CPU-perspective
column above). This is what drives shifter part choice and the ~40-pin Apple-bus budget.

- **FPGA → host, unidirectional (drive out):** A0–A15 (16), R/W (1) — 17 lines. Fast, one-way
  (74LVC245-class or fixed-dir shifter).
- **FPGA ↔ host, bidirectional (data):** D0–D7 (8) — direction gated by R/W + φ2 phase.
  Needs a true bidirectional/direction-controlled shifter (74LVC245 with DIR = f(R/W, φ2), or auto-dir).
- **host → FPGA (sense in):** φ0/PHI2 clock (1), /RES (1), /IRQ (1), /NMI (1), RDY (1, but also
  driveable), plus the Apple slot control lines that reach the socket region (/INH, DMA, etc. —
  these come from the slot/motherboard, not strictly the CPU socket; see `CARRIER_PLAN.md`).
- **FPGA → host, part-specific outputs:** SYNC/VPA, φ2/VDA, φ1, MLB, VPB, E — assert only what the
  emulated part defines; the host mostly ignores most of these.
- **carrier → host control:** BE held high.

Approx budget at the socket itself: **16 addr + 8 data + R/W + clock + 4 interrupt/reset/ready ≈ 30
mandatory**, the rest of the "~40 Apple bus" count in the plan comes from slot-side control lines.

## 2×20 header ↔ DIP-40 numbering (design decision, TODO at layout)

A 2×20 0.1″ header does **not** number like a DIP. Two conventions must be reconciled:

- **DIP-40:** pins 1→20 down one side, 21→40 up the other (pin 40 opposite pin 1).
- **2×20 shrouded IDC header:** pin 1 at the keyed corner, then it alternates row-to-row —
  odd pins (1,3,…,39) in one row, even pins (2,4,…,40) in the other. A ribbon + IDC-to-DIP
  adapter carries this straight through only if the adapter is built for it.

**Recommendation:** define the carrier header so **header pin N = DIP pin N (1:1)**, and pick/spec
a DIP-40 ribbon adapter (e.g. an IDC-to-DIP "clip" or a machined DIP plug on ribbon) whose wiring
realizes that mapping. Document the exact adapter part before committing copper — a mismatch here
silently swaps address/data lines. Add a **pin-1 key** on the shrouded header and a keyed cable to
make backwards insertion impossible. This is deferred to the layout/wiring phase.

## Level-shifter chip allocation (implemented in `modules/cpu_socket.zen`)

The carrier *is* the CPU: a soft CPU in the GW5AT-60 drives the socket through
`FPGA (3.3 V) → LXC translators → 100 Ω series → 2×20 header → ribbon → DIP-40 plug`. All
translation uses **SN74LXC8T245** octal transceivers (genuine dual-supply — cannot use plain
single-rail LVC245, which won't output true 5 V) plus two **SN74LXC1T45** single-bit parts for
the direction-flip pins.

Convention: **A side = FPGA (VCCA = 3.3 V), B side = socket (VCCB = the host's socket 5 V on
DIP pin 8)**. Taking VCCB from the *host* means every translator goes Hi-Z (LXC `Ioff`) whenever
the Apple is off — we physically cannot back-drive a dead machine. `DIR` high = A→B (drive out).

Because a '245 shares one `DIR` across all 8 bits, channels are grouped by direction:

| Ref | Part | Signals | DIR |
|---|---|---|---|
| U_OUT1 | LXC8T245 | A0–A7 | tied high (out) |
| U_OUT2 | LXC8T245 | A8–A15 | tied high (out) |
| U_OUT3 | LXC8T245 | R/W, SYNC/VPA, φ2o/VDA, MLB, E, **VPB** (2 spare) | tied high (out) |
| U_IN | LXC8T245 | φ0/PHI2, /RES (sense), /IRQ, /NMI, RDY, BE (2 spare) | tied low (in) |
| U_DATA | LXC8T245 | D0–D7 | `CPU_DATA_DIR` (FPGA; ≈ ~R/W, confirm at bring-up) |
| U_FLIP3 | LXC1T45 | pin 3 (φ1o ↔ ABORTB) | `CPU_P3_DIR` (FPGA) |
| U_FLIP38 | LXC1T45 | pin 38 (SO ↔ MX) | `CPU_P38_DIR` (FPGA) |

**Pins 3 & 38 each get their own single-bit translator** because in *both* CPU families one is an
output while the other is an input (they're always opposite), so a shared-`DIR` 2-bit part cannot
serve them — each needs its own firmware-controlled direction. **Pin 1 (VPB)** is a driven CPU
output on the WDC parts, so it sits in the output group; on an NMOS 6502 or 65SC02 the same socket
pin is hard ground, so 6502-class firmware must hold VPB low and the series resistor bounds any mistake.

**Fail-safe (wrong-model firmware must not damage anything):**
- 100 Ω series resistor on every **driven** socket line (all outputs, D0–D7, and the two flip pins)
  — limits bus-fight current *and* ≈source-terminates the fast LXC edges into the ~100 Ω ribbon; RC
  negligible at ≤2.8 MHz. The six U_IN inputs (φ0/PHI2, /RES, /IRQ, /NMI, RDY, BE) are **omitted**:
  their DIR is hard-strapped to sense so firmware can never drive them toward the host, and a
  near-end resistor would not terminate a host-driven line anyway.
- Global `~OE` pulled **high** → all octal buffers Hi-Z until the FPGA drives it low.
  (The LXC1T45 flip parts have **no** `~OE` — they rely on series-R + correct `DIR` alone.)
- `CPU_DATA_DIR` / `CPU_P3_DIR` / `CPU_P38_DIR` pulled **low** = default "sense, never drive host".

**Deadman reset:** a 2N7002 (Q_RES) open-drain holds socket /RES (pin 40) low. Its gate is pulled
high by the **host's 5 V** (not the carrier 3.3 V), so reset is asserted whenever the Apple is
powered — even if the carrier boots later or never. The 3.3 V GPIO must **not** touch the 5 V gate,
so the release path is an **inverting open-drain buffer** (SN74LVC1G06, VCC = 3.3 V, output tolerant
to 5.5 V): `F_RES_REL (FPGA, pull-down) → buffer → gate (pull-up to 5 V) → Q_RES`.

| condition | buffer out | gate | Q_RES | /RES |
|---|---|---|---|---|
| `F_RES_REL` low (default / crash / 3V3 down) | Hi-Z | 5 V | ON | **held low** |
| `F_RES_REL` high (firmware releases) | sinks low | low | OFF | released |
| host 5 V up, carrier 3.3 V down | Hi-Z (Ioff) | 5 V | ON | **held low** |

The buffer must be **inverting** ('06, not the non-inverting '07): with the input pulled *down*,
inverting is what makes "default = reset held" fail-safe. /RES is also sensed on U_IN so firmware
can read the host reset button.

**Host-5V detect:** a 2N7002 common-source inverter (Q_5VDET) off socket 5 V drives
`CPU_5V_ABSENT` — **LOW = host 5 V present, HIGH = host unpowered** (inverted). Clean rail-to-rail
3.3 V logic (never exceeds 3.3 V at the FPGA), ~5 µA quiescent and only while the host is on — no
resistive-divider standing current, no analog threshold. Firmware checks it before enabling the bus.

> Ground return: only DIP pin 21 (VSS) is a guaranteed ground in the 1:1 cable (as on a real
> 6502). Adding interleaved grounds to the ribbon would require breaking header-pin-N = DIP-pin-N.

## Sources

- **W65C816S Datasheet** (WDC, Mar 13 2024) — Figure 2-2 "40 Pin DIP Pinout" and Table 2-2 "Pin
  Function Table". <https://www.westerndesigncenter.com/wdc/documentation/w65c816s.pdf>
- **W65C02S Datasheet** (WDC, Apr 8 2022) — Section 3 "Pin Function Description".
  <https://www.westerndesigncenter.com/wdc/documentation/w65c02s.pdf>
- **MOS 6502 40-pin DIP pinout** — cross-checked against
  <https://whichpin.com/6502> and the MOS MCS6500-family pin configuration.
