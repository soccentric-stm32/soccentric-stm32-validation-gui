# validation-gui

**HWVAL Studio**: a cross-platform (macOS, Windows, Linux) PySide6 desktop
application with a macOS-style look. It runs and records the HWVAL hardware
validation tests over UART, keeps the run history in SQLite, updates
application firmware through the A/B bootloader, flashes firmware over SWD
with OpenOCD, and controls the demo application. The SRS holds the shared
HWLINK protocol (Appendix A).

| | |
|---|---|
| Requirements | [SRS.md](SRS.md) — SRS-GUI-F767 (v0.1 draft) |
| Board | NUCLEO-F767ZI — see [Hardware.md](https://github.com/soccentric-stm32/validation-firmware/blob/HEAD/Hardware.md) |
| Status | **Implemented** — v0.1.0, device simulator included, no pytest suite by project request |
| Stack | Python 3.11+, PySide6 6, pyserial, FlatBuffers, SQLite, OpenOCD ≥ 0.12 |

## Quick start (no hardware)

The simulator implements all three HWLINK roles (HWVAL, BOOT, DEMO) and needs
no ST-LINK, OpenOCD or board.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
python -m hwval_studio

# headless: run the ADC group against the simulated HWVAL
hwval-studio --cli --simulate hwval --group ADC --no-report

# TCP simulator for other tools
hwval-studio --simulator-server --role hwval --server-port 7000
# another client:
hwval-studio --cli --port tcp://127.0.0.1:7000 --info
```

In the GUI choose **Tools → Device Simulator** and connect an in-process
HWVAL, BOOT or DEMO device. The same dialog starts the TCP server.

## Features

* **Connection** — ST-LINK VCP discovery, HWLINK `Hello`, `mode link`
  fallback for HWVAL's text CLI, protocol version check, role detection,
  auto-reconnect, 2 s ping and link-loss reporting.
* **Test catalogue** — groups and 196 test cases read from HWVAL
  (`ListGroups`/`ListTests`), sidebar categories from Appendix D, per-group
  badges and status colours, search by ID/title/group/requirement, harness
  check, sortable table and a details pane.
* **Runs** — single/selected/group/all, levels S/L/E, operator and destructive
  filters (destructive requires confirmation and resets after the run),
  repeat/until-fail, live results, abort, run-failed-again, operator prompt
  sheets, reconnection after reset and `GetResults` recovery.
* **UART update** — A/B slot cards from `GetBootInfo`, local `.img` header and
  CRC validation, downgrade/name-change warnings, 1024-byte chunks with
  retries and progress, activate and 60 s confirmation watch, cancel, history
  records.
* **SWD** — OpenOCD discovery/version check, ST-LINK/target detection,
  option-byte display, flash HWVAL, provision product configuration, restore
  bench configuration, confirmations, live OpenOCD output, one process per
  operation, no RDP/WRP/BOOT_ADD changes.
* **Demo** — status, LEDs LD1/LD2/LD3, patterns and periods, button events,
  faults, heap and task stack high-water marks, clear fault, reset, enter
  bootloader.
* **History** — WAL SQLite in the per-user data folder, write-as-you-go,
  incomplete-run detection, schema version/backup/migration, filters, compare,
  label boards, delete, retention, CSV/JSON export.
* **Reports** — `hwtest.py`-compatible JSON and Markdown, print/PDF, import
  `hwtest.py` JSON.
* **Operator mode** — simplified screen with fixed selection, large result,
  operator prompts, automatic history/report, optional PIN.
* **Preferences** — General, Connection, Tests, Firmware, History, Operator,
  immediate apply, restored window/layout/folders.
* **Look and feel** — light macOS-style theme on all platforms, explicit
  palette/QSS, SVG line icons tinted at run time, bundled Inter and JetBrains
  Mono fonts, HiDPI support, native menu roles and shortcuts, collapsible log
  console with level filter/search/hex dump.
* **CLI** — `hwval-studio --cli` runs a selection or update without a window
  and returns the HWVAL HOST-004 exit codes (0 pass, 1 fail, 2 comms).

## Architecture

```
src/hwval_studio/
  protocol/          COBS framing, request/response, generated FlatBuffers
  core/              Qt-free Client and RunController
  transport/         QThread serial/simulator/socket worker, sync CLI transports
  controller.py      background tasks, signals, retries, history/update/SWD flows
  firmware/          BOOT image validation, OpenOCD process control
  persistence/       SQLite schema, reports and hwtest.py import
  simulator/         HWVAL/BOOT/DEMO device, TCP server, catalogue snapshot
  ui/                theme, widgets, pages, dialogs, main window
  resources/         SVG icons, fonts and licences
  docs/              bundled user guide, test catalogue and third-party licences
protocol/hwlink.fbs  the single generated protocol schema
packaging/           PyInstaller spec, Linux/macOS/Windows builds, udev, MSI
scripts/             protocol generation, app icon rendering
```

The UI never calls pyserial, OpenOCD or SQLite directly. Serial reads/writes
run on a `QThread`; every long operation runs on a background `TaskThread` and
reports through Qt signals. The protocol layer is Qt-free and is shared with
the CLI and simulator.

## Regenerate the protocol bindings

```bash
python scripts/gen_protocol.py --flatc /path/to/flatc
```

The generated Python code is checked in so `pip install -e .` works without
`flatc`; the schema remains the single source (GCON-004). The schema is
append-only within protocol major version 1 (LNK-013).

## Hardware use

1. Install OpenOCD 0.12 or newer (or set its path in Preferences).
2. Connect the NUCLEO-F767ZI over the ST-LINK USB cable.
3. Linux: add the user to `dialout`/`uucp` and install the ST-LINK udev rules
   from `packaging/udev/99-stlink.rules`.
4. Use **Firmware → Flash (SWD)** to install HWVAL (single-bank bench mode),
   or **Tools → Provision Product Configuration** to install BOOT (dual-bank
   product mode).
5. Connect over UART and run tests, update applications or control the demo.

The user guide is bundled in the application (**Help → HWVAL User Guide**)
and in `src/hwval_studio/docs/USER_GUIDE.md`.

## Packaging

Each platform builds its own package with PyInstaller one-folder mode:

```bash
python -m pip install -e ".[packaging]"
packaging/build-linux.sh       # AppImage + .deb
packaging/build-macos.sh       # .app + .dmg
packaging\build-windows.ps1    # one-folder + .msi (WiX)
```

See [packaging/README.md](packaging/README.md). The CI matrix in
`.github/workflows/build.yml` builds macOS arm64/x86_64, Windows x64 and Linux
x86_64. Code signing/notarisation and OpenOCD bundling remain open items
(OPEN-G02, OPEN-G03).

## Related projects

| Repository | Role |
|---|---|
| [validation-firmware](https://github.com/soccentric-stm32/validation-firmware) | HWVAL hardware validation firmware |
| [bootloader](https://github.com/soccentric-stm32/bootloader) | A/B bootloader (UART update, CRC32, trial boot and rollback) |
| [app-c-freertos](https://github.com/soccentric-stm32/app-c-freertos) | FreeRTOS demo application in C (LEDs, button, HWLINK) |
| [app-rust-freertos](https://github.com/soccentric-stm32/app-rust-freertos) | The same demo in Rust (Embassy) |
| [app-c-zephyr](https://github.com/soccentric-stm32/app-c-zephyr) | The same demo on Zephyr RTOS |
| [app-rust-zephyr](https://github.com/soccentric-stm32/app-rust-zephyr) | The same demo in Rust on Zephyr RTOS |
| [validation-gui](https://github.com/soccentric-stm32/validation-gui) | PySide6 GUI: runs HWVAL tests, updates and flashes firmware |
| [factory-station](https://github.com/soccentric-stm32/factory-station) | HWVAL Factory: end-of-line test and provisioning station |

## License

[MIT](LICENSE) © 2026 Sandesh Ghimire. Use it as a starting point for your own
products. Third-party code (STM32CubeF7, FreeRTOS, LwIP, Embassy, Zephyr and
others) is fetched at build time and keeps its own licence.

Author: Sandesh Ghimire <sandesh@soccentric.com>
