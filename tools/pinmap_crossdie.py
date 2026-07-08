#!/usr/bin/env python3
"""
Cross-die pin checker for the Tang Mega SOM (GW5AT-60 <-> GW5AST-138, both PBGA484A).

The BTB connector is die-agnostic: a given ball is the same physical pin on both dies.
But the bank NUMBER, the pad FUNCTION, and the pin's special capabilities differ per die.
This script reads the balls the carrier actually uses (from modules/som_btb.zen) and reports,
per ball, the 60K vs 138K view plus anything that could break on an upgrade.

Ground truth = the Gowin IDE device JSON (NOT the PDFs or the dock etch CSV, which is 138K-only):
  /opt/gowin/IDE/data/device/GW5AT-60B/PBGA484A.json      (60K, this build)
  /opt/gowin/IDE/data/device/GW5AST-138C/PBGA484A.json    (138K, upgrade target)

Usage:  python3 tools/pinmap_crossdie.py
Exit code is non-zero if any UPGRADE-RISK rows are found.
"""
import json, re, sys, os

HERE = os.path.dirname(__file__)
G60  = "/opt/gowin/IDE/data/device/GW5AT-60B/PBGA484A.json"
G138 = "/opt/gowin/IDE/data/device/GW5AST-138C/PBGA484A.json"
ZEN  = os.path.join(HERE, "..", "modules", "som_btb.zen")
LEN  = os.path.join(HERE, "som_pcb_length.csv")   # shared SOM-PCB ball->BTB etch length (mil)

PS_PER_MIL = 0.180 / 1.0          # ~180 ps/inch = 0.180 ps/mil on FR4
LONG_MIL   = 800                  # advisory: high absolute SOM-side delay
PAIR_SKEW_MIL = 25                # advisory: notable intra-pair SOM-side skew

def load(p):
    return {e["INDEX"]: e for e in json.load(open(p))["PIN_DATA"]}

def load_len():
    d = {}
    for ln in open(LEN):
        if ln.startswith(("#", "ball")):
            continue
        b, v = ln.strip().split(",")
        d[b] = float(v)
    return d

def caps(e):
    """Capabilities a signal might genuinely depend on and that can differ between dies.

    ADC_INPUT is deliberately excluded: it's present on almost all 60K general I/O (an on-chip
    routing feature, not a per-ball property the carrier depends on), so tracking its "loss"
    just drowns out the real signal. The 4 dedicated ADC pins (N9/N10/M9/L10) are separate.
    """
    c = set()
    if e.get("TRUELVDS"): c.add("LVDS")   # true differential output
    if e.get("DQS", "NONE") not in ("NONE", "", None): c.add("DQS")  # source-sync / DDR strobe
    if e.get("X16"): c.add("X16")         # x16 memory-interface capable
    return c

def main():
    g60, g138 = load(G60), load(G138)
    length = load_len()
    func2ball = {e["NAME"]: e["INDEX"] for e in g60.values()}   # 60K function name -> ball

    # The 188 general-I/O balls = SOM_<ball> nets in som_btb.zen (excludes SOM_DONE/READY/ADC* roles).
    balls, seen = [], set()
    for m in re.finditer(r'Net\("SOM_([A-Z]{1,2}\d{1,2})"\)', open(ZEN).read()):
        b = m.group(1)
        if b not in seen and g60.get(b, {}).get("TYPE") == "I/O":
            seen.add(b); balls.append(b)

    risks, covered = [], []
    print(f"{'ball':4} {'len(mil)':>8} {'60K (bank/func)':20} {'138K (bank/func)':20} flags")
    print("-" * 78)
    for b in sorted(balls):
        e6, e8 = g60.get(b), g138.get(b)
        s6 = f"BANK{e6['BANK']}/{e6['NAME']}"
        s8 = f"BANK{e8['BANK']}/{e8['NAME']}" if e8 and e8.get("BANK") is not None else "ABSENT"
        L = length.get(b)
        if L is not None:
            covered.append(b)
        flags = []
        if not e8 or e8.get("TYPE") != "I/O":
            flags.append("!!NOT-IO-ON-138K")
        else:
            lost = caps(e6) - caps(e8)
            if lost:
                flags.append("!!LOSES:" + ",".join(sorted(lost)))
        if flags:
            risks.append(b)
        if L is not None and L >= LONG_MIL:
            flags.append(f"long({L:.0f}mil~{L*PS_PER_MIL:.0f}ps)")
        lc = f"{L:.0f}" if L is not None else "—"
        print(f"{b:4} {lc:>8} {s6:20} {s8:20} {' '.join(flags)}")

    # differential-pair intra-skew on the (shared) SOM PCB — matters for LVDS/DQS/source-sync
    pairs, pseen = [], set()
    for b in covered:
        partner = func2ball.get(g60[b].get("PAIR", ""))
        if partner in length and partner in balls and frozenset((b, partner)) not in pseen:
            pseen.add(frozenset((b, partner)))
            pairs.append((b, partner, abs(length[b] - length[partner])))
    pairs.sort(key=lambda x: -x[2])

    print("-" * 78)
    vals = [length[b] for b in covered]
    if vals:
        span = max(vals) - min(vals)
        print(f"length: {len(covered)}/{len(balls)} balls covered | span {min(vals):.0f}-{max(vals):.0f} mil "
              f"(~{span * PS_PER_MIL:.0f} ps ball-to-ball) | {len(balls) - len(covered)} uncovered (no Sipeed length)")
    notable = [p for p in pairs if p[2] >= PAIR_SKEW_MIL]
    worst = pairs[0][2] if pairs else 0
    print(f"diff pairs (both balls used+covered): {len(pairs)} | worst intra-pair SOM skew "
          f"{worst:.0f} mil (~{worst * PS_PER_MIL:.1f} ps) | >= {PAIR_SKEW_MIL} mil: {len(notable)}")
    for b, p, d in (notable or pairs)[:5]:
        tag = "compensate on carrier" if d >= PAIR_SKEW_MIL else "already tight"
        print(f"    {b}/{p}: {d:.0f} mil (~{d * PS_PER_MIL:.1f} ps) — {tag}")
    print(f"capability upgrade-risk: {len(risks)} balls: {risks}")
    print("\nNotes:")
    print(" - SOM-PCB len is SHARED between 60K & 138K (one PCB). Compensate it + your carrier trace in copper.")
    print(" - Bank NUMBER differences are harmless for routing; the ball is the physical pin.")
    print(" - Package (pad->ball) flight-time differs per die and is NOT in this data — absorb it per-die in the")
    print("   FPGA (IODELAY / timing closure / source-sync leveling), not in carrier copper.")
    print(" - Uncovered balls have no published SOM length; measure or avoid for the tightest skew groups.")
    return 1 if risks else 0

if __name__ == "__main__":
    sys.exit(main())
