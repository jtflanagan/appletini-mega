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
- ✅ **Step 5 Gowin** V1.9.12.03: extracted, 3 WSL2 packaging fixes applied (freetype,
  xcb runpath, license_config_gui rpath), Sipeed floating license configured and **verified
  headless** — `gw_sh` opens the Tcl console with no license error and accepts
  `set_device -name GW5AST-138B GW5AST-LV138PG484AC1/I0`.
- ⏳ `openFPGALoader.exe` not yet on the WSL PATH. ⏳ `build.tcl` template still TODO.

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

## Step 5 — Gowin EDA (Linux) + floating license  ✅ done (⚠️ was the involved one)
Using **Gowin_V1.9.12.03_linux** (supports GW5AST-138). ✅ extracted, ✅ all 3 WSL2
packaging fixes below applied, ✅ Sipeed floating license configured, ✅ `gw_sh` verified
headless. Three separate Gowin-packaging bugs had to be worked around (3a/3b/3c) — the raw
install does **not** run on Ubuntu 24.04 out of the box.
1. Download the **Linux** edition tarball from
   https://www.gowinsemi.com/en/support/download_eda/ (registration) or the
   Sipeed mirror (dl.sipeed.com). Get a version that supports GW5AST-138.
2. Extract to `/opt/gowin` and add to PATH:
   ```bash
   sudo mkdir -p /opt/gowin && sudo tar -xf Gowin_V*_linux.tar.gz -C /opt/gowin
   echo 'export PATH="/opt/gowin/IDE/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
   ```
3. Runtime libs: `sudo apt install -y libpng16-16 libfreetype6 libglu1-mesa libxrender1 libxi6 libsm6`.
   (`libcrypto.so.10`/OpenSSL 1.0 is bundled under `/opt/gowin/IDE/lib` — no system pkg needed.)
   Plus the Qt **xcb** platform-plugin deps, or `gw_ide` fails with
   `Could not load the Qt platform plugin "xcb"` under WSLg:
   ```bash
   sudo apt install -y libxcb-shape0 libxcb-xkb1 libxkbcommon-x11-0 libxcb-util1 \
     libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-cursor0
   ```
3a. **WSL2/Ubuntu-24.04 freetype fix (required).** Out of the box `gw_sh`/`gw_ide` die with
   `libfontconfig.so.1: undefined symbol: FT_Done_MM_Var` — Gowin ships an old bundled
   `libfreetype.so.6` that the system `libfontconfig` (needs the newer symbol) can't use.
   Point the bundled path at the system lib:
   ```bash
   sudo mv /opt/gowin/IDE/lib/libfreetype.so.6 /opt/gowin/IDE/lib/libfreetype.so.6.gowin-bak
   sudo ln -s /lib/x86_64-linux-gnu/libfreetype.so.6 /opt/gowin/IDE/lib/libfreetype.so.6
   ```
3b. **Qt xcb-plugin runpath fix (required for `gw_ide` GUI).** After the xcb apt deps,
   the GUI still fails: `Could not load the Qt platform plugin "xcb"` → really
   `libQt5XcbQpa.so.5: cannot open shared object file`. The lib IS bundled in
   `/opt/gowin/IDE/lib`, but the plugin's `RUNPATH` is `$ORIGIN/../../lib`, which from
   `plugins/qt/platforms/` wrongly resolves to `/opt/gowin/IDE/plugins/lib`. Fix the path
   with a directory symlink (durable, no `LD_LIBRARY_PATH` pollution):
   ```bash
   sudo ln -s /opt/gowin/IDE/lib /opt/gowin/IDE/plugins/lib
   ```
   (`gw_ide` then launches under WSLg with no env vars. WSLg Wayland is also present if
   you ever prefer `QT_QPA_PLATFORM=wayland`. Harmless runtime warning:
   `QXcbIntegration: Cannot create platform OpenGL context` — xcb falls back to software GL,
   fine for dialogs/license.)
3c. **`license_config_gui` bogus RPATH fix (required to set the license).** The license
   dialog spawns `/opt/gowin/IDE/bin/license_config_gui`, which ships a hardcoded build-machine
   RPATH (`/tools/Qt/5.15.14.official/...`) instead of `$ORIGIN/../lib` like the other bins, so
   it dies with `libQt5Widgets.so.5: cannot open shared object file`. Patch its rpath:
   ```bash
   sudo apt install -y patchelf
   sudo patchelf --set-rpath '$ORIGIN:$ORIGIN/../lib' /opt/gowin/IDE/bin/license_config_gui
   ```
3d. **Make the install tree writable (required to save the license).** Because we extracted
   as root, `/opt/gowin` is root-owned and the license GUI can't write its config →
   `failed to write settings to the config file: gwlicense.ini`. Take ownership (single-user box):
   ```bash
   sudo chown -R "$USER:$USER" /opt/gowin
   ```
4. **License = floating, NOT node-locked** (avoids WSL2 MAC problem). Sipeed runs a public
   floating license server for Tang board owners — there is **nothing to register/download**;
   pointing the client at it *is* the license. The config file is **`/opt/gowin/IDE/bin/gwlicense.ini`**
   (NOT `~/.config`), format `lic="host:port"`. The stock file ships pointing at a dead
   placeholder host (`jinan3016`) — that is the source of the initial "Connection timeout".
   Either set it via `gw_ide` (Help ▸ Manage License → "Float Lic" → `gowinlic.sipeed.com` : `10559`),
   or just write the file directly and skip the GUI entirely:
   ```bash
   printf '[license]\nlic="gowinlic.sipeed.com:10559"\n' > /opt/gowin/IDE/bin/gwlicense.ini
   ```
   (Pre-flight the server: `bash -c 'exec 3<>/dev/tcp/gowinlic.sipeed.com/10559' && echo reachable`.)
5. Verified headless: `echo exit | gw_sh` opens `*** GOWIN Tcl Command Line Console ***`
   with **no** "License verification failed", and
   `set_device -name GW5AST-138B GW5AST-LV138PG484AC1/I0` is accepted (the part number alone is
   ambiguous — `138B` and `138C` are distinct silicon revs; confirm which the Tang Mega 138K uses).
   The `QXcbIntegration: Cannot create platform OpenGL context` line printed even headless is harmless.
   Build flow: `set_device -name … <part>` … `run all` (see `build.tcl`, TODO).

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
- [ ] Get `openFPGALoader.exe` onto the WSL PATH (symlink or add its Windows dir) so the cross-boundary flash line works.
- [ ] Author `build.tcl` template (device string, options, `.cst`/`.sdc`, reports).
- [ ] Confirm whether the Tang Mega 138K is `-name GW5AST-138B` or `GW5AST-138C` (both parse; needs board/silicon check).
- [x] ~~Exact Gowin download + headless floating-license path~~ → V1.9.12.03; license in `/opt/gowin/IDE/bin/gwlicense.ini` = `lic="gowinlic.sipeed.com:10559"`; `gw_sh` verified.
- [x] ~~Confirm KiCad 10 PPA name for 24.04~~ → `ppa:kicad/kicad-10.0-releases`, installs 10.0.4.
- [x] ~~Decide project location~~ → Linux FS at `~/repos/appletini-mega` (fast sim I/O).
