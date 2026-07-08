# appletini-mega

Apple II accelerator carrier for the Sipeed Tang Mega 60K SOM (Gowin GW5AT-60 FPGA).
Boards are authored in Zener (`.zen`); see `WSL-DEV-SETUP.md` for the toolchain.

## Primary reference sources (outside this repo)

The Tang Mega SOM/dock details — bank/voltage assignments, DDR3 wiring, BTB pinouts,
part numbers — are **not** fully captured in this repo. When a question needs
authoritative SOM/dock data, consult these first (both are on the Windows host, reachable
from WSL under `/mnt/c/`):

- **`/mnt/c/repos/tang_mega_138k_dock`** — Sipeed's dock hardware package: schematics
  (`02_Schematic`), datasheets (`07_Datasheet`), and especially the FPGA
  **`09_Pinout_Length_table`** (ball → bank → net → trace-length). This is the ground
  truth for which FPGA banks the on-SOM DDR3 uses vs. which 1.5 V banks are brought out
  to the connectors. Also has project notes: `CARRIER_PLAN.md`, `INTERFACES.md`,
  `PART_SELECTION_AND_BOOT.md`.
- **`/mnt/c/repos/sipeed_wiki`** — mirror of the Sipeed wiki (`docs/`, `share_docs/`) for
  Tang Mega board overviews, IO-voltage/bank notes, and general SOM documentation.

The Windows paths are `C:/repos/tang_mega_138k_dock` and `C:/repos/sipeed_wiki`.

**SOM mechanical placement** (connector + mounting-hole relative positions, orientation of the "C"):
`docs/som_placement.md` — derived from the dock interactive-BOMs (`03_Designator_drawing/*_ibom.html`,
which are LZString-compressed; decompress in pure Python) cross-checked against the mechanical drawing.
Needed for physical layout of the carrier's mating side.

**CPU socket connector** (the 5V Apple-bus side): `docs/cpu_socket_pinout.md` — full 40-pin DIP
pinouts for the NMOS 6502, W65C02S, and W65C816S side by side (they share one DIP-40 socket; CMOS
parts redefine the NMOS NC/VSS pins). Interface = 2×20 0.1″ header on carrier → ribbon → DIP-40 plug
in the host CPU socket. Flags the pins whose direction flips between parts (pin 3, pin 38) and the
header↔DIP numbering decision (spec header pin N = DIP pin N 1:1). Pinout data is from the WDC
datasheets (authoritative).

## Authoritative FPGA pinout = the installed Gowin toolchain (not the PDFs/dock)

The **ground truth** for ball → bank → I/O-function is the machine-readable JSON shipped with
the Gowin IDE at `/opt/gowin/IDE/data/device/`:

- **60K (this project):** `GW5AT-60B/PBGA484A.json`
- **138K (cross-compat):** `GW5AT-138B/PBGA484A.json`

Each `PIN_DATA` entry is `{INDEX(ball), NAME(func e.g. IOB104B), TYPE, BANK, DIFF, PAIR, ...}`.
Parse with plain `python3 -c` (no openpyxl needed). Prefer this over the dock etch CSV or the
UG983E PDF ball-maps.

**Critical gotcha — the 60K and 138K are DIFFERENT dies in the SAME PG484A footprint.** A given
ball (same physical BTB pin) has a *different* bank number and function name on each die, and the
bank *grouping* differs too (it's a real regrouping, not a clean renumber — e.g. 60K BANK6/7/8
mostly = 138K BANK4 but some balls land in 138K BANK5). So: **bank labels are die-specific.** The
dock etch CSV uses 138K naming; never validate 60K labels against it. Generate/validate the pinmap
per-die straight from the JSON above. `docs/btb_som_pinmap.md` is generated this way (60K
authoritative + 138K annotation column); a one-time audit of the hand-written version found 19 wrong
bank/function labels out of 188 — do not hand-edit, regenerate.

## 60K → 138K upgrade safety

The connector is cross-compatible because the package/footprint is shared, so the carrier's
die-invariant contract is **(1) BTB-pin → ball routing** and **(2) VCCIO rail → voltage**. The bank
number and pad function are die-internal, resolved per-die at `.cst` constraint time — never design
around them, and don't bake them into net identities (use ball- or role-centric net names).

What can actually break on an upgrade: a ball's **special capability** (true-LVDS / DQS / X16) or its
**VCCIO voltage legality** on the other die. Run `python3 tools/pinmap_crossdie.py` — it diffs every
used ball across both Gowin JSONs and flags capability loss (exit non-zero if any). As of this build,
10/188 balls lose LVDS/DQS/X16 on the 138K (mostly config-region pins losing only X16); the shared
3.3 V VCCIO grouping stays legal on both dies.

**Skew / length.** `tools/som_pcb_length.csv` = Sipeed's ball→BTB etch length on the SOM PCB (mil),
parsed from the dock repo's `09_Pinout_Length_table` (parse ONLY `BANK*_<ball>_IO*` nets — `DDR3_A*`
address nets alias real balls). This is die-invariant (shared PCB), so it is the de-skew reference for
either SOM. Coverage is **143/188** balls (the 60K BANK9/3/12 region is unreported). The checker adds
per-ball length, differential-pair intra-skew (all pairs are matched to ~1 ps on the SOM), and flags
long balls. Package pad→ball flight-time differs per die and is NOT in any free data — absorb it in the
FPGA (IODELAY / timing closure / source-sync leveling), never in carrier copper.

