# AppleTini-Mega — WSL2 Dev Environment Setup

Runbook for standing up the full development toolchain. Execute the install steps
**inside a VS Code + Claude Code session attached to the Ubuntu 24.04 WSL2 distro**
(sudo works interactively there). Canonical copy now lives in the Linux-FS git
clone at `~/repos/appletini-mega/WSL-DEV-SETUP.md` (origin
`git@github.com:jtflanagan/appletini-mega.git`); the loose `/mnt/c/repos/appletini-mega`
copy is stale and not a repo — don't edit it.

## Status (2026-07-07)
- ✅ Steps 0, 2, 3, 4 done. Verilator 5.020 (`--timing`), GTKWave 3.3.116, Icarus 12.0,
  cc65/ca65 2.18, tio 2.7. Trivial Verilator sim runs to `$finish`.
- ✅ Step 6 `pcb` 0.4.4 (pcbc 0.4.4) in `~/.local/bin`. ✅ Step 7 KiCad **10.0.4**.
- ✅ Repo already Linux-FS cloned at `~/repos/appletini-mega` (project-location item settled).
- ✅ Passwordless sudo enabled via `/etc/sudoers.d/flana-nopasswd`.
- ⏳ **Step 5 Gowin**: runtime libs installed, but the EDA tarball still needs a manual
  registered download + license GUI. ⏳ `openFPGALoader.exe` not yet on the WSL PATH.
  ⏳ `build.tcl` template still TODO.

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

## Step 6 — Diode `pcb` (Zener)  ✅ done → 0.4.4
Install via the official shim script (downloads a SHA-256-verified prebuilt binary to
`~/.local/bin`, adds it to PATH; no sudo). The `pcb` shim then fetches the `pcbc`
toolchain per-project on first use:
```bash
curl -fsSL https://raw.githubusercontent.com/diodeinc/pcb/main/install.sh | bash
exec bash && pcb --version   # → pcbc 0.4.4
```
(NB: Ubuntu's apt `pcb` is the unrelated gEDA layout editor — do not use.)

## Step 7 — KiCad 10.x (on 24.04)  ✅ done → 10.0.4
PPA route (the KiCad team versions PPAs per release series; the old generic
`kicad-releases` no longer exists — using it silently falls back to Ubuntu's stock 7.0.11):
```bash
sudo add-apt-repository ppa:kicad/kicad-10.0-releases && sudo apt update && sudo apt install -y kicad
kicad-cli version   # → 10.0.4~ubuntu24.04.1
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
- [ ] Get `openFPGALoader.exe` onto the WSL PATH (symlink or add its Windows dir) so the cross-boundary flash line works.
- [ ] Author `build.tcl` template (device string, options, `.cst`/`.sdc`, reports).
- [x] ~~Confirm KiCad 10 PPA name for 24.04~~ → `ppa:kicad/kicad-10.0-releases`, installs 10.0.4.
- [x] ~~Decide project location~~ → Linux FS at `~/repos/appletini-mega` (fast sim I/O).
