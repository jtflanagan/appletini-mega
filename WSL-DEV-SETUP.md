# AppleTini-Mega — WSL2 Dev Environment Setup

Runbook for standing up the full development toolchain. Execute the install steps
**inside a VS Code + Claude Code session attached to the Ubuntu 24.04 WSL2 distro**
(sudo works interactively there). This file lives on the Windows side and is
reachable from WSL at `/mnt/c/repos/appletini-mega/WSL-DEV-SETUP.md`.

## Toolchain partition (decided)

| Runs in **WSL2 (Linux)** | Stays on **native Windows** |
|---|---|
| RTL editing | USB flashing (`openFPGALoader.exe` / Gowin Programmer) |
| Verilator + GTKWave simulation | GAO (on-chip logic analyzer, GUI, needs live board) |
| Gowin `gw_sh` headless synth/PnR/bitstream | Serial terminal on the live board (USB-UART) |
| Zener `pcb` (PCB-as-code) + KiCad 10 layout | — |
| cc65/ca65 (6502 software/ROMs) | — |

Cross-boundary flash from the single WSL session (no session switching):
```bash
openFPGALoader.exe -b tangmega138k "$(wslpath -w build/apple2.fs)"
```
`usbipd-win` is already installed on Windows if USB-into-WSL is ever preferred instead.

## Board / target
- **Sipeed Tang Mega 138K**, FPGA **Gowin GW5AST-LV138PG484AC1/I0** (Arora V).
- Gowin EDA floor: Education V1.9.9+ / commercial V1.9.11.03+.

---

## Step 0 — Get to Ubuntu 24.04
Recommended (lower risk than in-place `do-release-upgrade`, keeps 22.04 as fallback;
893 GB free so space is a non-issue):
```powershell
wsl --install Ubuntu-24.04      # run in Windows PowerShell
```
Then set it default (optional): `wsl --set-default Ubuntu-24.04`.
> In-place alternative from within 22.04: `sudo do-release-upgrade`.

## Step 1 — Attach VS Code + Claude Code
Install the **WSL** extension, `Ctrl+Shift+P` → **WSL: Connect to WSL** →
open the project folder in the **Linux** filesystem (`~/appletini-mega`, not `/mnt/c`)
for fast sim I/O. Claude Code re-initializes Linux-side.

## Step 2 — Base build deps
```bash
sudo apt update && sudo apt install -y \
  build-essential git cmake python3 python3-pip \
  autoconf flex bison libfl-dev zlib1g-dev help2man ccache
```

## Step 3 — Simulation toolchain
```bash
sudo apt install -y verilator gtkwave iverilog
verilator --version   # 24.04 ships 5.x (has --timing); source-build only if you need newest
```
Optional modern waveform viewer: **Surfer** (`cargo install surfer` or release binary).

## Step 4 — Apple II extras
```bash
sudo apt install -y cc65 tio      # 6502 assembler/C toolchain + serial terminal
```
(`tio` is for reference; the live-board USB-UART is driven Windows-side.)

## Step 5 — Gowin EDA (Linux) + floating license  ⚠️ the involved one
1. Download the **Linux** edition tarball from
   https://www.gowinsemi.com/en/support/download_eda/ (registration) or the
   Sipeed mirror (dl.sipeed.com). Get a version that supports GW5AST-138.
2. Extract to `/opt/gowin` and add to PATH:
   ```bash
   sudo mkdir -p /opt/gowin && sudo tar -xf Gowin_V*_linux.tar.gz -C /opt/gowin
   echo 'export PATH="/opt/gowin/IDE/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
   ```
3. Likely runtime libs: `sudo apt install -y libpng16-16 libfreetype6 libglu1-mesa libxrender1 libxi6 libsm6`.
4. **License = floating, NOT node-locked** (avoids WSL2 MAC problem). Launch the
   GUI **once** under WSLg to set it, then headless `gw_sh` inherits the config:
   ```bash
   gw_ide     # GUI via WSLg → choose "Float Lic" → server gowinlic.sipeed.com  port 10559
   ```
5. Verify headless: `gw_sh` should start the Tcl shell. Build flow uses
   `set_device GW5AST-LV138PG484AC1/I0` … `run all` (see `build.tcl`, TODO).

Reference for Linux/container quirks: github.com/homelith/dockerized-gowin-template

## Step 6 — Diode `pcb` (Zener)
Install the Rust binary release from github.com/diodeinc/pcb (script or `cargo install`).
Verify: `pcb --version`. (NB: Ubuntu's apt `pcb` is the unrelated gEDA layout editor — do not use.)

## Step 7 — KiCad 10.x (on 24.04)
PPA route (verify exact PPA for v10):
```bash
sudo add-apt-repository ppa:kicad/kicad-releases && sudo apt update && sudo apt install -y kicad
kicad-cli version
```
Flatpak fallback: `flatpak install flathub org.kicad.KiCad`.
Zener requires **KiCad 10.x** for layout gen/edit.

## Step 8 — End-to-end verification
- `verilator --version` (5.x) and a trivial sim → `wave.fst` → open in GTKWave via WSLg.
- `gw_sh` headless: run a minimal `build.tcl` producing a `.fs` bitstream.
- `pcb --version` and a hello-world `.zen` → KiCad layout.
- `kicad-cli version`.
- Flash test from WSL: `openFPGALoader.exe --detect` (runs Windows-side, sees USB).

---

## Open items to nail during setup
- [ ] Exact Gowin Linux download/version for GW5AST-138 + confirm floating-license config path for headless `gw_sh`.
- [ ] Confirm KiCad 10 PPA name for 24.04 (else flatpak).
- [ ] Author `build.tcl` template (device string, options, `.cst`/`.sdc`, reports).
- [ ] Decide project location: clone into Linux FS vs work on `/mnt/c` (sim I/O speed vs single path for Windows tools).
