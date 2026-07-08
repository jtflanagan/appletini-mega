# Tang Mega 60K SOM — BTB physical pin map (all 280 pins)

Transcribed from the SOM schematic (BTB Connector sheet) + the dock schematic `SOM_BTB0`/`SOM_BTB1&2` sheets. NOT from the KiCad repo.

Carrier mating receptacles: **2x DF40HC(3.0)-100DS-0.4V(51)** + **1x DF40HC(3.0)-80DS-0.4V(51)**, 0.4 mm pitch, 3.0 mm stack height.

**Source of truth:** the bank/function columns are generated from the installed Gowin device JSON — `/opt/gowin/IDE/data/device/GW5AT-60B/PBGA484A.json` (60K) and `GW5AST-138C/PBGA484A.json` (138K). Do not hand-edit them; regenerate.

**Columns:** `Ball` = PG484A ball = the physical BTB pin (identical on both dies). `SOM-PCB len` = Sipeed's ball→BTB etch length on the SOM module PCB, mil (a **de-skew reference** — the SOM PCB #30354 is shared, so this length applies to *both* dies; ~180 ps/in on FR4). `60K` = bank/function on the GW5AT-60 (authoritative for this build). `138K` = the *same ball* on the GW5AST-138 (cross-upgrade path). `VCCO_n/m` / `VCCIO_*` = per-bank VCCIO rail (3.3 V default). `NC` = no SOM connection. DONE=`G11`, READY=`U12` (both BANK3 on 60K, dual-purpose I/O).

**Length coverage:** the table (`tools/som_pcb_length.csv`, from the dock repo's `09_Pinout_Length_table`) length-reports **143 of the 188** BTB I/O balls; the ~45 blanks are the 60K BANK9 (1.5 V) / BANK3 / BANK12 region, which Sipeed didn't length-match. Covered balls span 136–942 mil (~145 ps). Run `tools/pinmap_crossdie.py` for per-ball length + differential-pair intra-skew + capability divergence in one report.

**⚠ Cross-die caveat:** the 60K and 138K are *different dies in the same PG484A footprint*. A ball's bank NUMBER and function NAME differ between them (e.g. W22 = 60K `BANK7/IOB104B` = 138K `BANK4/IOB124B`), and bank *boundaries* move (60K BANK6/7/8 ≈ 138K BANK4, but a few balls land in 138K BANK5; 60K BANK9 splits across 138K BANK5/6). So **bank labels are die-specific — design against the ball and the VCCIO rail, not the bank number.** See `CLAUDE.md` for the upgrade-safety method.


## C2399 — 100-pin — BANK1/2 (SDRAM0 side) + Q0/Q1 SerDes

| Pin | Ball | SOM-PCB len (mil) | 60K (bank/func) | 138K / GW5AST-138 | Notes |
|--:|:--|--:|:--|:--|:--|
| 1 |  |  |  |  | VCCIO rail VCCO_1/2 |
| 2 |  |  |  |  | GND |
| 3 |  |  |  |  | GND |
| 4 | C20 | 290 | BANK2/IOT131B | BANK2/IOR47B |  |
| 5 | A21 | 297 | BANK2/IOT135B | BANK2/IOR44B |  |
| 6 | D20 | 291 | BANK2/IOT131A | BANK2/IOR47A |  |
| 7 | B21 | 297 | BANK2/IOT135A | BANK2/IOR44A |  |
| 8 |  |  |  |  | GND |
| 9 |  |  |  |  | GND |
| 10 | D19 | 330 | BANK2/IOT120B | BANK2/IOR29B |  |
| 11 | A20 | 291 | BANK2/IOT122B | BANK2/IOR40B |  |
| 12 | E19 | 332 | BANK2/IOT120A | BANK2/IOR29A |  |
| 13 | B20 | 291 | BANK2/IOT122A | BANK2/IOR40A |  |
| 14 |  |  |  |  | GND |
| 15 |  |  |  |  | GND |
| 16 | C19 | 226 | BANK2/IOT115B | BANK2/IOR31B |  |
| 17 | A19 | 250 | BANK2/IOT113B | BANK2/IOR38B |  |
| 18 | C18 | 226 | BANK2/IOT115A | BANK2/IOR31A |  |
| 19 | A18 | 249 | BANK2/IOT113A | BANK2/IOR38A |  |
| 20 |  |  |  |  | GND |
| 21 |  |  |  |  | GND |
| 22 | E17 | 365 | BANK1/IOT89B | BANK2/IOR13B |  |
| 23 | B18 | 285 | BANK1/IOT104B | BANK2/IOR24B |  |
| 24 | F16 | 366 | BANK1/IOT89A | BANK2/IOR13A |  |
| 25 | B17 | 284 | BANK1/IOT104A | BANK2/IOR24A |  |
| 26 |  |  |  |  | GND |
| 27 |  |  |  |  | GND |
| 28 | D16 | 303 | BANK1/IOT87B | BANK2/IOR6B |  |
| 29 | C17 | 361 | BANK1/IOT106B | BANK2/IOR26B |  |
| 30 | E16 | 305 | BANK1/IOT87A | BANK2/IOR6A |  |
| 31 | D17 | 361 | BANK1/IOT106A | BANK2/IOR26A |  |
| 32 |  |  |  |  | GND |
| 33 |  |  |  |  | GND |
| 34 | D15 | 280 | BANK1/IOT82B | BANK2/IOR4B |  |
| 35 | A16 | 247 | BANK1/IOT99B | BANK2/IOR20B |  |
| 36 | D14 | 278 | BANK1/IOT82A | BANK2/IOR4A |  |
| 37 | A15 | 244 | BANK1/IOT99A | BANK2/IOR20A |  |
| 38 |  |  |  |  | GND |
| 39 |  |  |  |  | GND |
| 40 | F15 | 363 | BANK1/IOT91A | BANK2/IOR1A |  |
| 41 | B16 | 316 | BANK1/IOT97B | BANK2/IOR22B |  |
| 42 | F14 | 403 | BANK1/IOT80B | BANK2/IOR11B |  |
| 43 | B15 | 316 | BANK1/IOT97A | BANK2/IOR22A |  |
| 44 | F13 | 404 | BANK1/IOT80A | BANK2/IOR11A |  |
| 45 |  |  |  |  | GND |
| 46 |  |  |  |  | GND |
| 47 | A14 | 255 | BANK1/IOT95B | BANK2/IOR15B |  |
| 48 | J16 | 575 | BANK5/IOR47A | BANK3/IOR109A |  |
| 49 | A13 | 256 | BANK1/IOT95A | BANK2/IOR15A |  |
| 50 | J17 | 586 | BANK5/IOR39B | BANK3/IOR58B |  |
| 51 |  |  |  |  | GND |
| 52 | K17 | 590 | BANK5/IOR39A | BANK3/IOR58A |  |
| 53 | B13 | 336 | BANK1/IOT93B | BANK2/IOR17B |  |
| 54 | H15 | 535 | BANK4/IOR22B | BANK3/IOR101B |  |
| 55 | C13 | 332 | BANK1/IOT93A | BANK2/IOR17A |  |
| 56 | J15 | 532 | BANK4/IOR22A | BANK3/IOR101A |  |
| 57 |  |  |  |  | GND |
| 58 | H14 | 640 | BANK4/IOR26B | BANK3/IOR103B |  |
| 59 | C15 | 522 | BANK1/IOT85B | BANK2/IOR8B |  |
| 60 | J14 | 639 | BANK4/IOR26A | BANK3/IOR103A |  |
| 61 | C14 | 521 | BANK1/IOT85A | BANK2/IOR8A |  |
| 62 | G16 | 533 | BANK4/IOR24B | BANK3/IOR105B |  |
| 63 |  |  |  |  | GND |
| 64 | G15 | 531 | BANK4/IOR24A | BANK3/IOR105A |  |
| 65 | E14 | 512 | BANK1/IOT78B | BANK2/IOR2B |  |
| 66 | G13 | 478 | BANK4/IOR20B | BANK3/IOR98B |  |
| 67 | E13 | 512 | BANK1/IOT78A | BANK2/IOR2A |  |
| 68 | H13 | 480 | BANK4/IOR20A | BANK3/IOR98A |  |
| 69 |  |  |  |  | GND |
| 70 |  |  |  |  | GND |
| 71 |  |  |  |  | SerDes Q1_REFCLKM_1 |
| 72 |  |  |  |  | SerDes Q0_LN3_RXM_I |
| 73 |  |  |  |  | SerDes Q1_REFCLKP_1 |
| 74 |  |  |  |  | SerDes Q0_LN3_RXP_I |
| 75 |  |  |  |  | GND |
| 76 |  |  |  |  | GND |
| 77 |  |  |  |  | SerDes Q1_LN1_TXM_O |
| 78 |  |  |  |  | SerDes Q0_LN2_RXM_I |
| 79 |  |  |  |  | SerDes Q1_LN1_TXP_O |
| 80 |  |  |  |  | SerDes Q0_LN2_RXP_I |
| 81 |  |  |  |  | GND |
| 82 |  |  |  |  | GND |
| 83 |  |  |  |  | SerDes Q1_LN2_TXM_O |
| 84 |  |  |  |  | SerDes Q0_LN1_RXM_I |
| 85 |  |  |  |  | SerDes Q1_LN2_TXP_O |
| 86 |  |  |  |  | SerDes Q0_LN1_RXP_I |
| 87 |  |  |  |  | GND |
| 88 |  |  |  |  | GND |
| 89 |  |  |  |  | SerDes Q1_LN3_TXM_O |
| 90 |  |  |  |  | SerDes Q0_LN0_RXM_I |
| 91 |  |  |  |  | SerDes Q1_LN3_TXP_O |
| 92 |  |  |  |  | SerDes Q0_LN0_RXP_I |
| 93 |  |  |  |  | GND |
| 94 |  |  |  |  | GND |
| 95 |  |  |  |  | SerDes Q1_LN0_TXM_O |
| 96 |  |  |  |  | SerDes Q0_REFCLKM_0 |
| 97 |  |  |  |  | SerDes Q1_LN0_TXP_O |
| 98 |  |  |  |  | SerDes Q0_REFCLKP_0 |
| 99 |  |  |  |  | GND |
| 100 |  |  |  |  | GND |


## C2400 — 100-pin — BANK6/7/8 (SDRAM1 side), BANK9 1.5V IO, ADC

| Pin | Ball | SOM-PCB len (mil) | 60K (bank/func) | 138K / GW5AST-138 | Notes |
|--:|:--|--:|:--|:--|:--|
| 1 |  |  |  |  | VCCIO rail VCCO_6/7/8 |
| 2 | W22 | 485 | BANK7/IOB104B | BANK4/IOB124B |  |
| 3 | Y22 | 231 | BANK8/IOB99B | BANK4/IOB131B |  |
| 4 | W21 | 482 | BANK7/IOB104A | BANK4/IOB124A |  |
| 5 | Y21 | 233 | BANK8/IOB99A | BANK4/IOB131A |  |
| 6 | V20 | 729 | BANK8/IOB95B | BANK4/IOB120B |  |
| 7 | AB22 | 136 | BANK8/IOB97B | BANK4/IOB129B |  |
| 8 | U20 | 728 | BANK8/IOB95A | BANK4/IOB120A |  |
| 9 | AB21 | 139 | BANK8/IOB97A | BANK4/IOB129A |  |
| 10 | M17 | 942 | BANK5/IOR56A | BANK3/IOR73A |  |
| 11 | AA21 | 173 | BANK7/IOB102B | BANK4/IOB126B |  |
| 12 | P17 | 915 | BANK6/IOB140B | BANK4/IOB135B |  |
| 13 | AA20 | 174 | BANK7/IOB102A | BANK4/IOB126A |  |
| 14 | N17 | 914 | BANK6/IOB140A | BANK4/IOB135A |  |
| 15 | AB20 | 183 | BANK8/IOB85B | BANK4/IOB110B |  |
| 16 | M16 | 849 | BANK5/IOR52B | BANK3/IOR67B |  |
| 17 | AA19 | 181 | BANK8/IOB85A | BANK4/IOB110A |  |
| 18 | M15 | 845 | BANK5/IOR52A | BANK3/IOR67A |  |
| 19 | W20 | 289 | BANK8/IOB93B | BANK4/IOB122B |  |
| 20 | N15 | 800 | BANK6/IOB134B | BANK4/IOB146A |  |
| 21 | W19 | 290 | BANK8/IOB93A | BANK4/IOB122A |  |
| 22 | N13 | 711 | BANK6/IOB138A | BANK4/IOB142A |  |
| 23 | AB18 | 162 | BANK8/IOB77B | BANK4/IOB108B |  |
| 24 | N14 | 711 | BANK6/IOB138B | BANK4/IOB142B |  |
| 25 | AA18 | 167 | BANK8/IOB77A | BANK4/IOB108A |  |
| 26 | Y17 |  | BANK7/IOB122A | BANK5/IOB91A |  |
| 27 | Y19 | 243 | BANK8/IOB87B | BANK4/IOB116B |  |
| 28 | AB17 |  | BANK7/IOB108A | BANK5/IOB80B |  |
| 29 | Y18 | 242 | BANK8/IOB87A | BANK4/IOB116A |  |
| 30 | AA16 |  | BANK7/IOB106A | BANK5/IOB78B |  |
| 31 | W17 | 310 | BANK8/IOB79B | BANK4/IOB106B |  |
| 32 | M13 | 814 | BANK5/IOR50A | BANK3/IOR56A |  |
| 33 | V17 | 312 | BANK8/IOB79A | BANK4/IOB106A |  |
| 34 | L13 | 817 | BANK5/IOR50B | BANK3/IOR56B |  |
| 35 | U18 | 381 | BANK8/IOB75B | BANK4/IOB112B |  |
| 36 | AB16 |  | BANK7/IOB108B | BANK5/IOB80A |  |
| 37 | U17 | 376 | BANK8/IOB75A | BANK4/IOB112A |  |
| 38 | AA15 |  | BANK7/IOB106B | BANK5/IOB83A |  |
| 39 | W16 |  | BANK7/IOB126A | BANK5/IOB72B |  |
| 40 | AB15 |  | BANK8/IOB89A | BANK5/IOB83B |  |
| 41 | U16 |  | BANK6/IOB134A | BANK5/IOB76B |  |
| 42 | Y16 |  | BANK7/IOB122B | BANK5/IOB78A |  |
| 43 | T16 |  | BANK2/IOT146A | BANK5/IOB76A |  |
| 44 | W15 |  | BANK7/IOB126B | BANK5/IOB72A |  |
| 45 | T15 |  | BANK6/IOB132A | BANK5/IOB70B |  |
| 46 | V15 |  | BANK6/IOB130A | BANK5/IOB68B |  |
| 47 |  |  |  |  | GND |
| 48 | W14 |  | BANK8/IOB91A | BANK5/IOB85A |  |
| 49 | R16 | 522 | BANK6/IOB142B | BANK4/IOB140B |  |
| 50 | U15 |  | BANK6/IOB130B | BANK5/IOB68A |  |
| 51 | P15 | 521 | BANK6/IOB142A | BANK4/IOB140A |  |
| 52 | Y14 |  | BANK9/IOB56B | BANK5/IOB85B |  |
| 53 |  |  |  |  | GND |
| 54 | V14 |  | BANK8/IOB91B | BANK5/IOB66B |  |
| 55 | R14 | 500 | BANK6/IOB146B | BANK4/IOB133B |  |
| 56 | Y13 |  | BANK9/IOB56A | BANK5/IOB87A |  |
| 57 | P14 | 502 | BANK6/IOB146A | BANK4/IOB133A |  |
| 58 | AA14 |  | BANK8/IOB89B | BANK5/IOB87B |  |
| 59 |  |  |  |  | GND |
| 60 | AA13 |  | BANK9/IOB54B | BANK5/IOB89A |  |
| 61 | K14 | 768 | BANK4/IOR36B | BANK3/IOR60B |  |
| 62 | AB13 |  | BANK9/IOB54A | BANK5/IOB89B |  |
| 63 | K13 | 768 | BANK4/IOR36A | BANK3/IOR60A |  |
| 64 | Y12 |  | BANK9/IOB52A | BANK5/IOB60B |  |
| 65 |  |  |  |  | GND |
| 66 | AB12 |  | BANK9/IOB18A | BANK5/IOB51B |  |
| 67 |  |  |  |  | VCCIO rail VCCIO_138B5 |
| 68 | V10 |  | BANK9/IOB71B | BANK5/IOB58A |  |
| 69 | U9 |  | BANK3/IOR11B | BANK10/IOB177B |  |
| 70 | W11 |  | BANK9/IOB35A | BANK5/IOB62A |  |
| 71 | U10 |  | BANK3/IOR7A | BANK10/IOB177A |  |
| 72 | Y11 |  | BANK9/IOB20B | BANK5/IOB60A |  |
| 73 | U11 |  | BANK3/IOR7B | BANK10/IOB175A |  |
| 74 | W10 |  | BANK9/IOB35B | BANK5/IOB58B |  |
| 75 | U8 |  | BANK3/IOR11A | BANK10/IOB179A |  |
| 76 | AB11 |  | BANK9/IOB18B | BANK5/IOB51A |  |
| 77 |  |  |  |  | NC |
| 78 | AA11 |  | BANK9/IOB20A | BANK5/IOB56B |  |
| 79 |  |  |  |  | GND |
| 80 | AB10 |  | BANK9/IOB3B | BANK5/IOB53B |  |
| 81 |  |  |  |  | GND |
| 82 | AA10 |  | BANK9/IOB1B | BANK5/IOB56A |  |
| 83 |  |  |  |  | GND |
| 84 | AA9 |  | BANK9/IOB1A | BANK5/IOB53A |  |
| 85 |  |  |  |  | GND |
| 86 | W12 |  | BANK9/IOB52B | BANK5/IOB62B |  |
| 87 |  |  |  |  | GND |
| 88 | V13 |  | BANK7/IOB124B | BANK5/IOB66A |  |
| 89 |  |  |  |  | NC |
| 90 | T14 |  | BANK6/IOB132B | BANK5/IOB70A |  |
| 91 |  |  |  |  | 5V |
| 92 | N9 |  | ADCTN | ADCTN | ADCTN |
| 93 |  |  |  |  | 5V |
| 94 | N10 |  | ADCTP | ADCTP | ADCTP |
| 95 |  |  |  |  | 5V |
| 96 | M9 |  | ADCVN | ADCVN | ADCVN |
| 97 |  |  |  |  | 5V |
| 98 | L10 |  | ADCVP | ADCVP | ADCVP |
| 99 |  |  |  |  | 5V |
| 100 |  |  |  |  | GND |


## BTB9900 — 80-pin — JTAG/config (BANK12/3), HSPI (BANK5), RGMII/JOYCON

| Pin | Ball | SOM-PCB len (mil) | 60K (bank/func) | 138K / GW5AST-138 | Notes |
|--:|:--|--:|:--|:--|:--|
| 1 |  |  |  |  | GND |
| 2 |  |  |  |  | GND |
| 3 | T13 |  | BANK12/IOR3A | BANK10/IOB169B |  |
| 4 | V19 | 387 | BANK8/IOB81B | BANK4/IOB114B |  |
| 5 | U13 |  | BANK12/IOR3B | BANK10/IOB169A |  |
| 6 | V18 | 387 | BANK8/IOB81A | BANK4/IOB114A |  |
| 7 | V12 |  | BANK12/IOR1A | BANK10/IOB173A |  |
| 8 |  |  |  |  | GND |
| 9 | R13 |  | BANK12/IOR1B | BANK10/IOB173B |  |
| 10 | U22 |  | BANK7/IOB117A | BANK4/IOB104A |  |
| 11 |  |  |  |  | GND |
| 12 | T18 | 327 | BANK6/IOB144B | BANK4/IOB138B |  |
| 13 | U21 | 300 | BANK7/IOB115B | BANK4/IOB97B |  |
| 14 | R18 | 329 | BANK6/IOB144A | BANK4/IOB138A |  |
| 15 | T21 | 303 | BANK7/IOB115A | BANK4/IOB97A |  |
| 16 |  |  |  |  | GND |
| 17 |  |  |  |  | GND |
| 18 | R17 | 424 | BANK6/IOB136B | BANK4/IOB144B |  |
| 19 | T20 | 343 | BANK7/IOB111B | BANK4/IOB102B |  |
| 20 | P16 | 426 | BANK6/IOB136A | BANK4/IOB144A |  |
| 21 |  |  |  |  | GND |
| 22 |  |  |  |  | GND |
| 23 | R19 | 383 | BANK7/IOB113B | BANK4/IOB99B |  |
| 24 | L14 | 612 | BANK5/IOR48A | BANK3/IOR62A |  |
| 25 | P19 | 382 | BANK7/IOB113A | BANK4/IOB99A |  |
| 26 | L15 | 609 | BANK5/IOR48B | BANK3/IOR62B |  |
| 27 |  |  |  |  | GND |
| 28 | N20 | 256 | BANK5/IOR70A | BANK3/IOR94A |  |
| 29 |  |  |  |  | VCCIO rail VCCO_4/5 |
| 30 | M20 | 256 | BANK5/IOR70B | BANK3/IOR94B |  |
| 31 | N22 | 323 | BANK5/IOR63A | BANK3/IOR89A |  |
| 32 | L16 | 588 | BANK4/IOR34A | BANK3/IOR65A |  |
| 33 | M22 | 327 | BANK5/IOR63B | BANK3/IOR89B |  |
| 34 | K16 | 588 | BANK4/IOR34B | BANK3/IOR65B |  |
| 35 |  |  |  |  | GND |
| 36 | P20 | 274 | BANK7/IOB124A | BANK4/IOB92A |  |
| 37 | M21 | 301 | BANK5/IOR68A | BANK3/IOR71A |  |
| 38 |  |  |  |  | GND |
| 39 | L21 | 300 | BANK5/IOR68B | BANK3/IOR71B |  |
| 40 | N18 | 329 | BANK5/IOR72A | BANK3/IOR92A |  |
| 41 | L19 | 400 | BANK5/IOR61A | BANK3/IOR85A |  |
| 42 | N19 | 330 | BANK5/IOR72B | BANK3/IOR92B |  |
| 43 | L20 | 396 | BANK5/IOR61B | BANK3/IOR85B |  |
| 44 | M18 | 310 | BANK5/IOR66A | BANK3/IOR87A |  |
| 45 | K21 | 307 | BANK5/IOR59A | BANK3/IOR76A |  |
| 46 | L18 | 310 | BANK5/IOR66B | BANK3/IOR87B |  |
| 47 | K22 | 304 | BANK5/IOR59B | BANK3/IOR76B |  |
| 48 | K18 | 308 | BANK5/IOR57A | BANK3/IOR83A |  |
| 49 | J22 | 329 | BANK5/IOR45A | BANK3/IOR74A |  |
| 50 | K19 | 306 | BANK5/IOR57B | BANK3/IOR83B |  |
| 51 | H22 | 326 | BANK5/IOR45B | BANK3/IOR74B |  |
| 52 | H17 | 375 | BANK4/IOR32A | BANK3/IOR96A |  |
| 53 | J20 | 393 | BANK5/IOR54A | BANK3/IOR78A |  |
| 54 | H18 | 378 | BANK4/IOR32B | BANK3/IOR96B |  |
| 55 | J21 | 388 | BANK5/IOR54B | BANK3/IOR78B |  |
| 56 | J19 | 270 | BANK5/IOR41A | BANK3/IOR80A |  |
| 57 | G17 | 700 | BANK4/IOR30A | BANK3/IOR107A |  |
| 58 | H19 | 270 | BANK5/IOR41B | BANK3/IOR80B |  |
| 59 | G18 | 704 | BANK4/IOR30B | BANK3/IOR107B |  |
| 60 |  |  |  |  | GND |
| 61 | N12 |  | BANK3/IOR9B | BANK10/IOB179B |  |
| 62 | H20 | 230 | BANK5/IOR43A | BANK3/IOR69A |  |
| 63 |  |  |  |  | GND |
| 64 | G20 | 229 | BANK5/IOR43B | BANK3/IOR69B |  |
| 65 | G21 | 304 | BANK2/IOT144A | BANK2/IOR53A |  |
| 66 |  |  |  |  | GND |
| 67 | G22 | 301 | BANK2/IOT144B | BANK2/IOR53B |  |
| 68 | F19 | 261 | BANK2/IOT124A | BANK2/IOR33A |  |
| 69 | F18 | 631 | BANK2/IOT117A | BANK2/IOR35A |  |
| 70 | F20 | 262 | BANK2/IOT124B | BANK2/IOR33B |  |
| 71 | E18 | 630 | BANK2/IOT117B | BANK2/IOR35B |  |
| 72 | F21 | 242 | BANK2/IOT142A | BANK2/IOR55A |  |
| 73 | C22 | 331 | BANK2/IOT133A | BANK2/IOR42A |  |
| 74 | E22 | 138 | BANK2/IOT140A | BANK2/IOR49A |  |
| 75 | B22 | 330 | BANK2/IOT133B | BANK2/IOR42B |  |
| 76 | D22 | 137 | BANK2/IOT140B | BANK2/IOR49B |  |
| 77 | G11 |  | BANK3/IOR9A | BANK10/IOB171B | DONE (config, dual-purpose I/O) |
| 78 | E21 | 198 | BANK2/IOT138A | BANK2/IOR51A |  |
| 79 | U12 |  | BANK3/IOR5B | BANK10/IOB171A | READY (config, dual-purpose I/O) |
| 80 | D21 | 195 | BANK2/IOT138B | BANK2/IOR51B |  |
