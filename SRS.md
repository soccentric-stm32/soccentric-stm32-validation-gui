# Software Requirements Specification — HWVAL Studio (Host GUI)

| | |
|---|---|
| **Document** | SRS-GUI-F767 |
| **Version** | 0.1 (draft) |
| **Author** | Sandesh Ghimire <sandesh@soccentric.com> |
| **Date** | 2026-11-03 |
| **Status** | Draft for review |
| **Target** | NUCLEO-F767ZI running HWVAL, BOOT or DEMO |
| **Software base** | Python ≥ 3.11, PySide6 (Qt 6), pyserial, flatbuffers, SQLite (Python `sqlite3`), OpenOCD ≥ 0.12 |

---

## Contents

1. [Introduction](#1-introduction)
2. [Overall description](#2-overall-description)
3. [Architecture requirements](#3-architecture-requirements)
4. [Look and feel](#4-look-and-feel)
5. [Main window](#5-main-window)
6. [Menu bar](#6-menu-bar)
7. [Connection and device detection](#7-connection-and-device-detection)
8. [Test and validation](#8-test-and-validation)
9. [Firmware update over UART (bootloader)](#9-firmware-update-over-uart-bootloader)
10. [Flashing and provisioning over SWD](#10-flashing-and-provisioning-over-swd)
11. [Demo application control](#11-demo-application-control)
12. [Run history (SQLite)](#12-run-history-sqlite)
13. [Reports](#13-reports)
14. [Operator mode](#14-operator-mode)
15. [Preferences and persistence](#15-preferences-and-persistence)
16. [Packaging and distribution](#16-packaging-and-distribution)
17. [Non-functional requirements](#17-non-functional-requirements)
18. [Future: plots and graphs](#18-future-plots-and-graphs)
19. [Verification matrix](#19-verification-matrix)
- [Appendix A — HWLINK protocol](#appendix-a--hwlink-protocol)
- [Appendix B — Change requests to HWVAL](#appendix-b--change-requests-to-hwval)
- [Appendix C — Database schema](#appendix-c--database-schema)
- [Appendix D — Sidebar and test groups](#appendix-d--sidebar-and-test-groups)
- [Appendix E — Keyboard shortcuts](#appendix-e--keyboard-shortcuts)
- [Appendix F — Open items](#appendix-f--open-items)

---

## 1. Introduction

### 1.1 Purpose

This document specifies **HWVAL Studio** (working name), a cross-platform
desktop application for macOS, Windows and Linux. Its main purpose is to run
and record the HWVAL hardware validation tests (SRS-HWVAL-F767) on the
NUCLEO-F767ZI over UART. It also updates application firmware through the A/B
bootloader (SRS-BOOT-F767), flashes firmware over SWD, and controls the demo
application (SRS-DEMO-F767).

### 1.2 Scope

The GUI shall:

- connect to the board over the ST-LINK VCP using the HWLINK protocol
  (Appendix A);
- detect which firmware is running (HWVAL, BOOT or DEMO) and offer the
  matching features;
- list every HWVAL test component in a sidebar and run single tests, groups,
  or everything, with live results and operator prompts;
- keep every run in a local SQLite database and export reports;
- update applications through the bootloader over UART;
- flash HWVAL and provision the bootloader over SWD with OpenOCD;
- look and behave like a native macOS application on all three platforms,
  in a light theme, with SVG icons and a full menu bar;
- provide an engineer mode and a simplified operator mode.

Plots and graphs of measured values are planned for a later version (§18).

### 1.3 Definitions

| Term | Meaning |
|---|---|
| **GUI** | HWVAL Studio, the application specified here |
| **HWVAL** | Hardware validation firmware, SRS-HWVAL-F767 |
| **BOOT** | A/B bootloader, SRS-BOOT-F767 |
| **DEMO** | FreeRTOS demo application, SRS-DEMO-F767 |
| **Role** | Which firmware answers on the link: `HWVAL`, `BOOTLOADER` or `DEMO` |
| **HWLINK** | The framing and FlatBuffers protocol of Appendix A |
| **Run** | One execution of a selection of HWVAL tests, stored as one history record |
| **Engineer mode** | Full UI with all features |
| **Operator mode** | Simplified UI for production use (§14) |
| **Bench configuration** | Flash in single-bank mode with HWVAL ([BOOT] §2.5) |
| **Product configuration** | Flash in dual-bank mode with BOOT and apps ([BOOT] §2.5) |

### 1.4 Requirement conventions

**shall / should / may**; IDs `<AREA>-<NNN>`; verification methods **T**
(test — automated, e.g. pytest-qt or against the device simulator), **D**
(demonstration on each platform), **I** (inspection), **A** (analysis).

### 1.5 References

| ID | Document |
|---|---|
| [HW] | [validation-firmware/Hardware.md](https://github.com/soccentric-stm32/validation-firmware/blob/HEAD/Hardware.md) |
| [HWVAL] | [validation-firmware/SRS.md](https://github.com/soccentric-stm32/validation-firmware/blob/HEAD/SRS.md) — SRS-HWVAL-F767 |
| [BOOT] | [bootloader/SRS.md](https://github.com/soccentric-stm32/bootloader/blob/HEAD/SRS.md) — SRS-BOOT-F767 |
| [DEMO] | [app-c-freertos/SRS.md](https://github.com/soccentric-stm32/app-c-freertos/blob/HEAD/SRS.md) — SRS-DEMO-F767 |
| [HIG] | Apple Human Interface Guidelines (macOS) — visual reference only |
| [QT] | Qt 6 / PySide6 documentation |
| [OOCD] | OpenOCD user guide, `stm32f2x` flash driver (covers STM32F7) |
| [FB] | FlatBuffers documentation (Python and flatcc) |

---

## 2. Overall description

### 2.1 Product perspective

```
+---------------------------------- HWVAL Studio ----------------------------------+
|  UI (PySide6)                                                                    |
|   sidebar · test pages · firmware pages · history · operator mode · preferences |
|        │ signals/slots                                                           |
|  Services:  HwvalService   BootService   DemoService   SwdService   HistoryStore |
|        │                                                  │            │         |
|  HWLINK protocol (codec, request/response, events)        │         SQLite       |
|        │                                                  │                      |
|  Serial transport (pyserial, worker thread)          OpenOCD process             |
+--------│--------------------------------------------------│----------------------+
         │ ST-LINK VCP (USART3)                             │ ST-LINK SWD
         v                                                  v
                         NUCLEO-F767ZI (HWVAL | BOOT | DEMO)
```

### 2.2 Users

| User | Use |
|---|---|
| Firmware / hardware engineer | Bring-up, single tests, fault finding, firmware updates (engineer mode) |
| Test technician / production operator | Run the standard suite, answer prompts, read PASS/FAIL (operator mode) |
| Developer of the GUI | Runs it against the device simulator (ARC-006) |

### 2.3 Constraints

| ID | Constraint |
|---|---|
| GCON-001 | The GUI shall be written in Python ≥ 3.11 with PySide6 (Qt 6). No other GUI toolkit shall be used. |
| GCON-002 | The GUI shall run on macOS (12 or later, Apple silicon and Intel), Windows (10 and 11, x64) and Linux (x86-64; Ubuntu 22.04/24.04 and Fedora as reference). |
| GCON-003 | The board shall be reached over UART (ST-LINK VCP) for all test, update and demo functions, and over SWD through OpenOCD for flashing and provisioning only. |
| GCON-004 | Protocol code shall be generated from the single schema `protocol/hwlink.fbs` (Appendix A.5); hand-written encoders are not allowed. |
| GCON-005 | Third-party icons and fonts shall have licences that permit redistribution on all three platforms. Apple SF Symbols and SF fonts shall not be bundled. |

### 2.4 Assumptions

| ID | Assumption |
|---|---|
| GASM-001 | The ST-LINK VCP works in both directions (HWVAL CL-010 resolved). |
| GASM-002 | OpenOCD is installed by the user or found on `PATH`; the GUI does not bundle it in v0.1 (Appendix F, OPEN-G02). |
| GASM-003 | On Linux the user has permission to open the serial port and the ST-LINK (group `dialout`/`uucp` and the ST-LINK udev rules). |
| GASM-004 | HWVAL implements the change requests of Appendix B (adopted in HWVAL SRS v0.2, §6.4). |

---

## 3. Architecture requirements

| ID | Requirement | Method |
|---|---|---|
| ARC-001 | The code shall be split into layers: transport, protocol, services, persistence and UI. The UI shall not call pyserial, OpenOCD or SQLite directly. | I |
| ARC-002 | Serial I/O shall run in a worker thread (`QThread`); results reach the UI only through Qt signals. The UI thread shall never block on I/O. | I, T |
| ARC-003 | OpenOCD shall run as a separate process (`QProcess`) with its output streamed to the log, and shall be stopped when each operation ends so that the ST-LINK is not held (HWVAL CL-006). | T |
| ARC-004 | Each firmware role shall have its own service class (`HwvalService`, `BootService`, `DemoService`) on top of one shared `LinkSession`. | I |
| ARC-005 | The protocol layer shall be usable without Qt, so that the command-line tools (`bootctl.py`, [BOOT] BHOST-004) and tests can use it. | I |
| ARC-006 | The project shall include a device simulator that implements the HWVAL, BOOT and DEMO roles over a virtual serial pair or a socket, for development and CI. | T |
| ARC-007 | The GUI shall provide a command-line entry point (`hwval-studio --cli …`) to run a test selection or a firmware update without a window, with the exit codes of HWVAL HOST-004 (0 pass, 1 fail, 2 comms). | T |

---

## 4. Look and feel

### 4.1 Style

| ID | Requirement | Method |
|---|---|---|
| LNF-001 | The GUI shall look like a native macOS application on **all** platforms: source-list sidebar, unified toolbar, rounded controls, macOS spacing and typography ([HIG] as visual reference). | D |
| LNF-002 | The GUI shall use a **light theme only** in v0.1, built from a single set of colour tokens (background, sidebar, separator, text primary/secondary, accent, pass, fail, skip, n/a, warning). Dark mode shall be possible later by swapping tokens. | I, D |
| LNF-003 | Reference palette: window `#FFFFFF`, sidebar `#F5F5F7`, separators `#E5E5EA`, primary text `#1D1D1F`, secondary text `#6E6E73`, accent `#007AFF`, pass `#34C759`, fail `#FF3B30`, skip `#FF9F0A`, n/a `#8E8E93`. | I |
| LNF-004 | The light theme shall be applied regardless of the OS dark-mode setting, using an explicit Qt palette and QSS, so that the app looks the same on every platform. | D |
| LNF-005 | Fonts: the system font on macOS; a bundled open-licence font with similar metrics (e.g. Inter) on Windows and Linux. Monospace (results, logs): the system monospace on macOS, a bundled open-licence monospace (e.g. JetBrains Mono) elsewhere. | D |
| LNF-006 | Controls shall follow macOS forms: push buttons with 6 px radius, segmented controls for filters, toggle switches for on/off settings, popup buttons for choices, search field with a magnifier and clear button, sheets or centred modal dialogs for confirmations. | D |
| LNF-007 | The native window frame shall be kept on every platform (no frameless custom title bar). On macOS the toolbar shall be unified with the title bar. | D |
| LNF-008 | The GUI shall support HiDPI / Retina displays and fractional scaling on Windows and Linux without blurry icons or text. | D |
| LNF-009 | Result states shall never be shown by colour alone: each has an icon and a text label (PASS, FAIL, SKIP, N/A, RUNNING, NOT RUN). | I |

### 4.2 Icons

| ID | Requirement | Method |
|---|---|---|
| ICN-001 | **All** icons (sidebar, toolbar, menus, buttons, status, app icon source) shall be SVG files bundled with the app. No raster icons except the generated platform app icons (`.icns`, `.ico`, `.png`) built from the SVG master. | I |
| ICN-002 | Icons shall be monochrome line icons in one consistent style (stroke width, 16/20/24 px grid) and shall be tinted at run time from the colour tokens (normal, secondary, accent, selected-on-accent). | I, D |
| ICN-003 | Every sidebar item of Appendix D shall have its own icon; unknown groups reported by HWVAL shall get a generic "chip" icon. | I |
| ICN-004 | Icons shall be original or from a permissively licensed set (e.g. Lucide, Tabler); the licence file shall ship with the app (GCON-005). | I |

---

## 5. Main window

### 5.1 Layout

```
+--------------------------------------------------------------------------------+
| ● ● ●   [◧]  [Port: ttyACM0 ▾] [Connect]   ( HWVAL 1.0.0 · Ready )   [▶][■] 🔍  |  toolbar
+-------------------+------------------------------------------------------------+
| DEVICE            |  ⊙ ADC                               12 tests · 10 ✓ 1 ✗ 1 –|
|   Overview        |  [Run Group] [Run Selected]  Level [S|L|E]  ☐ Operator ☐ Dest.|
| TEST & VALIDATION |  +--------------------------------------------------------+ |
|   All Tests       |  | ✓ ADC.001  Internal channels VREFINT/TEMP   S   12 ms  | |
| ▸ CPU & SYSTEM    |  | ✗ ADC.004  DAC1 → ADC1 loopback             L   40 ms  | |
| ▾ ANALOG          |  | – ADC.007  External reference               E   SKIP   | |
|     ADC      ✓10 ✗1|  +--------------------------------------------------------+ |
|     DAC           |  Details: measured 1.212 V, limits 1.18–1.24 V, ADC-004    |
| ▸ COMMUNICATION   |                                                            |
| FIRMWARE          |                                                            |
|   Update (UART)   |                                                            |
|   Flash (SWD)     |                                                            |
|   Demo App        |                                                            |
| DATA              |                                                            |
|   History         |                                                            |
|   Reports         |                                                            |
+-------------------+------------------------------------------------------------+
| ▾ Log (collapsible console)                                                    |
+--------------------------------------------------------------------------------+
```

### 5.2 Requirements

| ID | Requirement | Method |
|---|---|---|
| WIN-001 | The main window shall have a toolbar, a sidebar on the left, a content area on the right, and a collapsible log console at the bottom. | D |
| WIN-002 | The toolbar shall contain: sidebar toggle, port popup, Connect/Disconnect button, a centred activity view (role, firmware version, state, progress of the current run or update), Run and Abort buttons, and a search field. | D |
| WIN-003 | The sidebar shall be a macOS-style source list with uppercase section headers (DEVICE, TEST & VALIDATION, FIRMWARE, DATA), collapsible category groups, a rounded selection highlight, and per-item badges (Appendix D). | D |
| WIN-004 | The sidebar shall be resizable between 200 and 360 px and collapsible (View › Hide Sidebar). | D |
| WIN-005 | Sidebar items that do not apply to the connected role shall be shown disabled with a tooltip explaining why (e.g. test groups while BOOT is connected). | T |
| WIN-006 | The window shall have a minimum size of 1024 × 680 and remember its size, position, sidebar width, splitter positions and selected item (§15). | T |
| WIN-007 | The log console shall show timestamped protocol events, OpenOCD output and errors, with level filter, search, copy and clear. Raw frame hex dump shall be available at debug level. | D |
| WIN-008 | Long operations shall show progress in the activity view and, on macOS, in the Dock tile; on Windows in the taskbar button. | D |
| WIN-009 | The GUI shall show non-blocking notifications (in-window banner) for events such as "device reset", "reconnected", "update finished". Errors that need action shall use a modal sheet/dialog. | D |

---

## 6. Menu bar

### 6.1 Placement

| ID | Requirement | Method |
|---|---|---|
| MNU-001 | On macOS the menu bar shall be the native global menu bar, with an application menu named after the app. On Windows and Linux it shall be a menu bar inside the main window. | D |
| MNU-002 | Menu items shall use Qt menu roles so that About, Preferences and Quit move to the application menu on macOS and appear under Help, Edit and File on Windows/Linux. | D |
| MNU-003 | Every menu item shall have an SVG icon where the platform shows menu icons (Windows/Linux), and a keyboard shortcut where Appendix E lists one, shown with platform symbols (⌘⌥⇧ on macOS, Ctrl/Alt/Shift elsewhere). | D |
| MNU-004 | Items that do not apply in the current state shall be disabled, not hidden. | T |

### 6.2 Menus

| Menu | Items |
|---|---|
| **HWVAL Studio** (macOS only) | About HWVAL Studio · Check for Updates… (disabled in v0.1) · Preferences… · Services · Hide / Hide Others / Show All · Quit |
| **File** | New Window (macOS) · Open Report… · Export Report… (JSON, Markdown) · Export Run History… (CSV, JSON) · Import Results (JSON from `hwtest.py`)… · Open Recent › · Page Setup / Print Report… · Close Window · Quit (Windows/Linux) |
| **Edit** | Undo · Redo · Cut · Copy · Paste · Select All · Copy Test ID · Copy Result as Text · Find… · Find Next · Preferences… (Linux; Windows uses Tools › Options…) |
| **View** | Show/Hide Sidebar · Show/Hide Log · Show/Hide Details Pane · Operator Mode · Sort By › · Show Only › (Failed, Skipped, Not Run) · Zoom In / Zoom Out / Actual Size · Enter Full Screen |
| **Device** | Connect · Disconnect · Refresh Ports · Baud Rate › · Device Information · Reset Device · Enter Bootloader · Harness Check |
| **Tests** | Run Selected · Run Group · Run All… · Run Failed Again · Repeat… · Abort · Allow Destructive Tests… · Level Filter › (S, L, E) · Allow Operator Tests · Clear Results |
| **Tools** | Firmware Update (UART)… · Flash Firmware (SWD)… · Provision Product Configuration… · Restore Bench Configuration… · Read Option Bytes · Serial Console · Device Simulator (developer builds) · Options… (Windows) |
| **Window** (macOS) | Minimize · Zoom · Bring All to Front · list of windows |
| **Help** | HWVAL Studio Help · HWVAL User Guide · Test Catalogue · Keyboard Shortcuts · Show Log Folder · Show Database Folder · Report an Issue… · About HWVAL Studio (Windows/Linux) |

| ID | Requirement | Method |
|---|---|---|
| MNU-010 | All menus and items of §6.2 shall exist and work, except those marked disabled for v0.1. | T, D |
| MNU-011 | Edit commands shall work in every text field, table and the log console (standard Qt edit actions routed to the focused widget). | T |
| MNU-012 | Help › HWVAL User Guide and Test Catalogue shall open the bundled copies of `docs/USER_GUIDE.md` and `docs/TEST_CATALOGUE.md` rendered in a help window. | D |

---

## 7. Connection and device detection

| ID | Requirement | Method |
|---|---|---|
| CON-001 | The port popup shall list serial ports with description, and shall mark ST-LINK VCPs (USB VID `0x0483`) first, refreshing automatically when ports appear or disappear. | T |
| CON-002 | Connect shall open the port at 115200 8N1, send HWLINK `Hello`, and read the role from `HelloReply`. | T |
| CON-003 | When no `HelloReply` arrives within 500 ms, the GUI shall send the HWVAL text command `mode link` (Appendix B, CR-01) and retry `Hello`. If that fails too, it shall report "no HWLINK device" and offer the Serial Console. | T |
| CON-004 | The GUI shall refuse a device whose protocol major version differs from its own, showing both versions; a newer minor version shall be accepted with a notice. | T |
| CON-005 | After identification the GUI shall show role, firmware name and version, git commit, build date, chip UID, DEV_ID/REV_ID and flash mode (single/dual bank) in Device › Overview. | T |
| CON-006 | The GUI should switch to 921600 baud with `SetBaud` for bulk transfers (firmware update, large result lists) and back to 115200 afterwards; this shall be a preference. | T |
| CON-007 | The GUI shall detect a device reset (link silence, serial re-enumeration or a new `HelloReply`) and reconnect automatically within 5 s, keeping the session context (current run, update in progress). | T |
| CON-008 | The GUI shall send `Ping` every 2 s when idle and show "link lost" in the activity view after 3 missed replies. | T |
| CON-009 | Auto-connect to the last used port on start-up shall be a preference (default on). | T |
| CON-010 | Only one GUI window may hold a given port; a second window shall show the port as busy. | T |

---

## 8. Test and validation

### 8.1 Test catalogue

| ID | Requirement | Method |
|---|---|---|
| TST-001 | On connecting to HWVAL the GUI shall read all groups and test cases (`ListGroups`, `ListTests`) and build the sidebar test groups from them (Appendix D). The catalogue shall not be hard-coded. | T |
| TST-002 | For each test the GUI shall show: status icon, ID, title, level (S/L/E), operator flag, destructive flag, timeout, last duration, last result and reason, and verified requirement IDs. | T |
| TST-003 | The catalogue shall be cached per firmware version, so that the History view can show titles for runs made with older firmware. | T |
| TST-004 | The search field shall filter tests by ID, title, group or requirement ID across all groups. | T |
| TST-005 | Device › Harness Check shall show which harness wires are fitted (`GetHarness`) and mark tests whose wire is missing. | T |

### 8.2 Group pages

| ID | Requirement | Method |
|---|---|---|
| TST-010 | Selecting a sidebar group shall show its page: icon, name, test count, PASS/FAIL/SKIP/N/A counts, and the test table. | D |
| TST-011 | "All Tests" shall show every test of every group in one table with a group column. | D |
| TST-012 | The test table shall support multi-selection, sorting by any column, and a context menu: Run, Run Repeatedly…, Copy ID, Copy Result, Show in History. | T |
| TST-013 | A details pane shall show for the selected test: description, level and flags, needed harness wire or equipment, last result with measured value, limits, reason, requirement IDs, duration, and the log lines of that test. | D |
| TST-014 | Sidebar badges shall show per-group counts of the current session (e.g. ✓10 ✗1) and a coloured status dot: grey not run, blue running, green all pass, red any fail, orange skips only. | D |

### 8.3 Running tests

| ID | Requirement | Method |
|---|---|---|
| TST-020 | The user shall be able to run: one test, the selected tests, one group, several groups, or all tests. | T |
| TST-021 | Filters shall be: levels (S, L, E), allow operator tests, allow destructive tests, repeat count, until-fail. They map to HWVAL `Run` options (HWVAL CLI-025, CLI-026). | T |
| TST-022 | Destructive tests shall be off by default. Turning them on shall need a confirmation that lists what will be changed ([HWVAL] SAFE-005), and shall reset to off after the run. | T |
| TST-023 | During a run the GUI shall update the table, badges, details and activity view live from `TestStarted`/`TestResult` events, and show elapsed time and progress (n of total). | T |
| TST-024 | Abort (toolbar, menu, ⌘. / Ctrl+.) shall send `Abort`; the GUI shall show "aborting…" until `RunFinished` arrives and mark unfinished tests NOT RUN. | T |
| TST-025 | When a test resets the MCU ([HWVAL] TFW-007), the GUI shall reconnect (CON-007), read the results with `GetResults`, and continue the run view without losing results. | T |
| TST-026 | The GUI shall not allow a second run while one is active, and shall not allow firmware operations during a run. | T |
| TST-027 | "Run Failed Again" shall re-run the tests that failed in the last run. | T |
| TST-028 | A run with no operator and no destructive tests shall run unattended to completion without any dialog. | T |

### 8.4 Operator prompts

| ID | Requirement | Method |
|---|---|---|
| TST-030 | An `OperatorPrompt` event shall open a modal sheet showing the test ID, the instruction text, an illustration icon for the action type (observe LED, press button, connect cable), the valid answers as buttons, and a countdown of the remaining timeout. | D |
| TST-031 | The answer shall be sent with `OperatorAnswer`. When the timeout runs out the sheet shall close and the test shall show SKIP `NO_OPERATOR` as reported by HWVAL. | T |
| TST-032 | Prompts for "press B1" shall close automatically when HWVAL reports the press. | T |
| TST-033 | The GUI shall play the system alert sound and bring the window to the front (and bounce the Dock icon on macOS) when a prompt appears and the window is not focused. | D |

---

## 9. Firmware update over UART (bootloader)

| ID | Requirement | Method |
|---|---|---|
| FW-001 | The Firmware › Update page shall show both slots as cards: name, version, build date, commit, size, state badge (Active, Pending, Confirmed, Rejected, Empty, Invalid) from `GetBootInfo`, and the last boot outcome (e.g. rolled back). | D |
| FW-002 | The user shall choose an image file (`.img`) by button or drag and drop. The GUI shall parse and check the header locally ([BOOT] §5.1, IMG-001…003) and show its fields before upload. | T |
| FW-003 | When DEMO (or any app with `EnterBootloader`) is connected, the GUI shall send `EnterBootloader` and reconnect to BOOT automatically before the update. When HWVAL is connected (bench configuration) the page shall explain that UART update needs the product configuration and offer Tools › Provision Product Configuration. | T |
| FW-004 | Upload shall send `UpdateBegin`, `UpdateData` chunks of 1024 bytes and `UpdateEnd`, with a progress bar showing bytes, speed and remaining time. | T |
| FW-005 | Each request shall be retried up to 3 times on timeout (same sequence number, [LINK] A.4). The timeout for `UpdateData` shall cover a sector erase ([BOOT] UPD-003, OPEN-B02). | T |
| FW-006 | After a successful `UpdateResult`, the GUI shall offer "Activate and reboot" (automatic when the preference is set), then reconnect, identify the new firmware, and watch until the slot is Confirmed or Rejected (timeout 60 s), and report the outcome. | T |
| FW-007 | Cancel shall send `UpdateAbort`; the active slot stays unchanged ([BOOT] UPD-008). | T |
| FW-008 | The GUI shall warn (and require confirmation) when the image version is lower than or equal to the active slot's version, or when the image name differs from the active slot's name. | T |
| FW-009 | Every update attempt and its outcome shall be recorded in the history database (Appendix C, `firmware_ops`). | T |

---

## 10. Flashing and provisioning over SWD

| ID | Requirement | Method |
|---|---|---|
| SWD-001 | The GUI shall find OpenOCD on `PATH` or at a path set in Preferences, check its version (≥ 0.12), and show a clear message with install hints per platform when it is missing. | T |
| SWD-002 | The Firmware › Flash (SWD) page shall detect the ST-LINK probe and target (`stlink` interface, `stm32f7x` target), read and show `DEV_ID`, `REV_ID`, flash size and the option bytes (RDP, nDBANK, nDBOOT, BOOT_ADD0/1, WRP). | T |
| SWD-003 | **Flash HWVAL** shall: check that the file is an HWVAL image (`.elf`, `.hex` or `.bin` at `0x0800 0000`), switch the option bytes to single-bank (`nDBANK = 1`) if needed, program, verify and reset. | T |
| SWD-004 | **Provision Product Configuration** shall: set dual-bank (`nDBANK = 0`, `nDBOOT = 1`), mass-erase, program and verify `boot.hex` at `0x0800 0000`, reset, connect over UART to BOOT, and optionally load a first application image through §9. | T |
| SWD-005 | **Restore Bench Configuration** shall set single-bank (`nDBANK = 1`), mass-erase, and optionally flash HWVAL. | T |
| SWD-006 | Every operation that changes option bytes or erases flash shall need a confirmation that names the change and states that all flash contents will be lost. | T |
| SWD-007 | The GUI shall never change RDP, write protection, or `BOOT_ADD0/1`, and shall have no UI for them. | I |
| SWD-008 | The serial link shall be closed before an SWD operation that resets the target and reopened afterwards. | T |
| SWD-009 | OpenOCD output shall be shown live in the log console; a failed step shall stop the sequence and show the OpenOCD error. | T |
| SWD-010 | Every SWD operation shall be recorded in `firmware_ops` (Appendix C). | T |

---

## 11. Demo application control

| ID | Requirement | Method |
|---|---|---|
| DMO-001 | The Firmware › Demo App page shall be enabled when DEMO is connected. | T |
| DMO-002 | It shall show `Status` (version, uptime, running slot, trial state, reset cause, last fault, task stack high-water marks, heap), refreshed every 1 s. | D |
| DMO-003 | It shall show LD1, LD2 and LD3 as on-screen LEDs mirroring the board, with a pattern popup and a period slider (50–5000 ms) for LD1 and LD2, and an "All" control ([DEMO] LED-003, LED-004). | D |
| DMO-004 | `ButtonEvent`s shall be shown as a banner and update the pattern controls. | T |
| DMO-005 | Buttons: Clear Fault, Reset, Enter Bootloader (opens the Update page). | T |

---

## 12. Run history (SQLite)

| ID | Requirement | Method |
|---|---|---|
| HIS-001 | Every run shall be stored in a SQLite database in the per-user application data folder (Qt `AppDataLocation`), schema in Appendix C. | T |
| HIS-002 | Results shall be written as they arrive (one transaction per result), in WAL mode, so that a crash or power loss keeps all results received so far. An interrupted run shall be marked `INCOMPLETE` on the next start. | T |
| HIS-003 | The database shall carry a schema version (`PRAGMA user_version`) and the GUI shall migrate older schemas forward automatically, after making a backup copy. | T |
| HIS-004 | The History page shall list runs (date, board UID, firmware version, selection, totals, overall PASS/FAIL, duration, mode, operator name) with filters by board, date range, result and firmware version. | D |
| HIS-005 | Opening a run shall show all its results in the same table layout as a live run, read-only. | D |
| HIS-006 | Two runs shall be comparable side by side, highlighting tests whose result changed. | T |
| HIS-007 | Runs shall be exportable (Export Report, Export Run History) and deletable (with confirmation; deletion is permanent). | T |
| HIS-008 | The GUI shall record each board seen (UID, DEV_ID, REV_ID, first/last seen, optional user label). | T |
| HIS-009 | Measured values shall be stored as numbers with unit when HWVAL provides them (Appendix B, CR-03), so that §18 plots need no schema change. | I |
| HIS-010 | A retention preference (keep all / keep last N days) shall exist; default keep all. | T |

---

## 13. Reports

| ID | Requirement | Method |
|---|---|---|
| REP-001 | The GUI shall export a run as JSON and Markdown with the same content and naming as `hwtest.py` (`hwval_<UID8>_<date>.json/.md`, [HWVAL] HOST-001), so that existing tooling keeps working. | T |
| REP-002 | The report shall include: GUI and firmware versions, board UID and identity, date/time, operator name (if set), filters, per-group and overall totals, the FAIL list with measured/limits/reason, the SKIP list with reasons, and the full result table. | T |
| REP-003 | File › Print Report shall print or save to PDF through the platform print dialog. | D |
| REP-004 | File › Import Results shall import a `hwtest.py` JSON report into the history. | T |

---

## 14. Operator mode

| ID | Requirement | Method |
|---|---|---|
| OPM-001 | View › Operator Mode shall switch to a simplified screen: board identity, operator name field, one large **Run** button, a progress indicator, the current test title, and a large PASS / FAIL result with the list of failed tests. | D |
| OPM-002 | The operator run selection (levels, operator allowed, destructive never) shall be fixed in Preferences by an engineer; operators cannot change it. | T |
| OPM-003 | Operator prompts shall use the same sheets as TST-030 with larger text and buttons. | D |
| OPM-004 | Each operator run shall be saved to history automatically, and the report exported automatically to a configured folder if set. | T |
| OPM-005 | The app may be started directly in operator mode (`--operator` or a preference). Leaving operator mode may require a PIN set in Preferences (optional). | T |
| OPM-006 | Operator mode shall hide firmware flashing, provisioning, destructive tests, the Serial Console and Preferences. | T |

---

## 15. Preferences and persistence

| ID | Requirement | Method |
|---|---|---|
| PRF-001 | Preferences shall be a macOS-style window with toolbar tabs: General, Connection, Tests, Firmware, History, Operator. | D |
| PRF-002 | **General:** start in operator mode, show log on start, confirm before quit during a run. **Connection:** default port, auto-connect, fast baud on/off. **Tests:** default level filter, operator tests on/off. **Firmware:** OpenOCD path, image/firmware folders, auto-activate after upload. **History:** database location, retention, auto-export folder. **Operator:** run selection, PIN, operator name list. | T |
| PRF-003 | Preferences and window state shall be stored with `QSettings` in the platform-native location and restored on start-up. | T |
| PRF-004 | Preference changes shall apply immediately (macOS style, no OK/Apply buttons). | D |
| PRF-005 | The last used folders for each file dialog shall be remembered separately. | T |

---

## 16. Packaging and distribution

| ID | Requirement | Method |
|---|---|---|
| PKG-001 | The GUI shall be built with PyInstaller (one-folder mode) into: a macOS `.app` inside a `.dmg`; a Windows installer `.msi`; a Linux `.AppImage`. A `.deb` should also be produced. | D |
| PKG-002 | Each package shall be built on its own OS (CI matrix for macOS arm64 + x86_64, Windows x64, Linux x86-64). | I |
| PKG-003 | Packages shall include: generated protocol code, all SVG icons and fonts with licences, the help documents, and the HWVAL test catalogue. | I |
| PKG-004 | The Windows installer shall add a Start-menu entry and uninstaller; the `.dmg` shall have a drag-to-Applications layout; the AppImage shall include a `.desktop` file and icon. | D |
| PKG-005 | Version number, build date and git commit shall be embedded and shown in About. | T |
| PKG-006 | The Linux package documentation shall include the ST-LINK udev rule and the serial-group step (GASM-003); the GUI shall show these hints when opening a port fails with a permission error. | D |
| PKG-007 | The source tree shall also run directly with `python -m hwval_studio` from a virtual environment (`pyproject.toml` with pinned dependency versions). | T |

---

## 17. Non-functional requirements

| ID | Requirement | Method |
|---|---|---|
| GNFR-001 | **Start-up:** the main window shall appear within 3 s on a typical laptop (packaged build). | T |
| GNFR-002 | **Responsiveness:** no UI-thread operation shall take longer than 100 ms; result events shall be shown within 200 ms of arrival. | T |
| GNFR-003 | **Scale:** the GUI shall handle a run of 2000 results and a history of 10 000 runs without the tables becoming slow (model/view with lazy loading). | T |
| GNFR-004 | **Robustness:** unplugging the board, a device reset, or a malformed frame shall never crash the GUI; it shall report and recover (CON-007). | T |
| GNFR-005 | **Logging:** a rotating log file (5 × 5 MB) in the platform log folder; uncaught exceptions shall be logged with a traceback and shown in an error dialog with "Copy details". | T |
| GNFR-006 | **Accessibility:** all functions shall be reachable by keyboard; widgets shall have accessible names; text shall scale with View › Zoom. | D |
| GNFR-007 | **Code quality:** type hints throughout; `ruff` and `mypy --strict` clean on the GUI's own code; pytest + pytest-qt tests for protocol, services and main UI flows against the simulator (ARC-006), with ≥ 80 % line coverage of non-UI code. | I, T |
| GNFR-008 | **Portability:** no platform-specific code outside one `platform` module (menu roles, fonts, Dock/taskbar progress, paths). | I |
| GNFR-009 | **Licences:** a third-party licence list (PySide6 LGPL, pyserial, flatbuffers, fonts, icons) shall be shown in About and shipped in the packages. | I |
| GNFR-010 | **Documentation:** a user guide (with screenshots per platform) and a developer README (architecture, simulator, packaging). | I |

---

## 18. Future: plots and graphs

Not required in v0.1. The design shall leave room for:

- trends of a measured value per test across runs and boards (from `results.measured_value`);
- live waveforms from ADC/DAC/timer tests (would need a streaming HWLINK message);
- histograms of durations and pass rates per group.

| ID | Requirement | Method |
|---|---|---|
| FUT-001 | The content area shall support adding a "Charts" tab per group page without changing the page structure. | I |
| FUT-002 | The chosen plotting library (e.g. QtCharts or pyqtgraph) shall be decided before §18 starts (Appendix F, OPEN-G05). | — |

---

## 19. Verification matrix

| Area | Requirements | Main method |
|---|---|---|
| Architecture | ARC-001…007 | I, T |
| Look and feel | LNF-001…009, ICN-001…004 | D, I |
| Window and menus | WIN-001…009, MNU-001…012 | D, T |
| Connection | CON-001…010 | T |
| Tests | TST-001…033 | T, D |
| UART update | FW-001…009 | T |
| SWD | SWD-001…010 | T |
| Demo | DMO-001…005 | T, D |
| History | HIS-001…010 | T |
| Reports | REP-001…004 | T, D |
| Operator mode | OPM-001…006 | T, D |
| Preferences | PRF-001…005 | T, D |
| Packaging | PKG-001…007 | D, I |
| Non-functional | GNFR-001…010 | T, I |
| Protocol | LNK-001…020 (Appendix A) | T |

---

## Appendix A — HWLINK protocol

This appendix is **normative** for the GUI, HWVAL, BOOT and DEMO. It replaces
the earlier framing sketch (SOF + length) discussed for the bootloader.

### A.1 Physical link

| ID | Requirement |
|---|---|
| LNK-001 | UART 8N1, no flow control, 115200 baud after reset; `SetBaud` may select 921600. Both sides revert to 115200 if no valid frame arrives within 5 s after a baud change. |
| LNK-002 | The link carries only HWLINK frames, except on HWVAL, which starts in its text CLI and switches with the text command `mode link` (Appendix B, CR-01). |

### A.2 Framing

Each frame is encoded with **COBS** and terminated by a `0x00` byte. Before
COBS encoding a frame is:

| Field | Size | Meaning |
|---|---|---|
| `proto` | 1 | Protocol major version (`1`) |
| `flags` | 1 | bit 0 = response, bit 1 = event, others 0 |
| `seq` | 2 | Little-endian sequence number |
| `payload` | n | FlatBuffer with root `Message` and file identifier `HWLK` |
| `crc32` | 4 | Little-endian CRC-32/ISO-HDLC over `proto…payload` (same as `zlib.crc32`) |

| ID | Requirement |
|---|---|
| LNK-003 | The decoded frame shall be at most 2048 bytes; larger frames shall be discarded. |
| LNK-004 | A receiver shall resynchronise on the next `0x00` after any error; frames with a bad CRC shall be dropped silently. |
| LNK-005 | Every received FlatBuffer shall pass the verifier before use; failures shall be answered with `Nak MALFORMED`. |

### A.3 Messages

`Message` is a table with one field `body` of union type `Body`. Every
request, response and event is one member of `Body`.

**Common (all roles)**

| Request | Response | Notes |
|---|---|---|
| `Hello` (host name, GUI version, protocol minor) | `HelloReply` (role, firmware name, version, commit, build time, UID, DEV_ID, REV_ID, flash mode, protocol major/minor, max frame) | |
| `Ping` | `Pong` (uptime ms) | |
| `SetBaud` (rate) | `Ack`, then switch | |
| `Reset` | `Ack`, then reset | |
| — | `Ack` (seq) / `Nak` (seq, error code, detail text) | |
| — | `Log` event (level, text) | |
| — | `Progress` event (operation, done, total) | |

**HWVAL role** (Appendix B)

| Request | Response / events |
|---|---|
| `GetDeviceInfo` | `DeviceInfo` (identity, option bytes, clocks, reset cause, uptime) |
| `ListGroups` | `GroupList` (code, name, test count) |
| `ListTests` (group, page) | `TestList` (id, group, title, level, operator, destructive, timeout ms, needs, reqs; paged) |
| `GetHarness` | `HarnessInfo` (64-bit fitted mask, wire names) |
| `Run` (ids, groups, all, levels, allow operator, allow destructive, repeat, until fail) | `Ack`; then events `RunStarted` (total), `TestStarted` (id), `TestResult` (id, result, duration, reason, measured {value, unit, text}, limits {min, max, unit, text}, reqs), `OperatorPrompt` (prompt id, test id, kind, text, answers, timeout), `RunFinished` (totals, aborted) |
| `OperatorAnswer` (prompt id, answer) | `Ack` |
| `Abort` | `Ack` |
| `GetResults` | `ResultList` (paged, all results of the session) |
| `ClearResults` | `Ack` |
| `GetReport` | `Report` |
| `GetSetting` / `SetSetting` (key, value) | `Setting` / `Ack` |
| `EnterTextMode` | `Ack`, then the text CLI resumes |

**BOOTLOADER role** — [BOOT] §9.1: `GetBootInfo`, `UpdateBegin`,
`UpdateData`, `UpdateEnd`, `UpdateResult`, `Activate`, `UpdateAbort`.

**DEMO role** — [DEMO] §8.1: `GetStatus`, `SetLed`, `SetLedAll`,
`ClearFault`, `EnterBootloader`, `ButtonEvent`.

### A.4 Exchange rules

| ID | Requirement |
|---|---|
| LNK-006 | The host sends requests with `seq` 1…65535 (wrapping, 0 skipped); the device echoes `seq` in the response. Events use `seq = 0`. |
| LNK-007 | The host shall have at most one request outstanding, except `Abort`, `OperatorAnswer` and `Ping`, which may be sent while a `Run` is active. |
| LNK-008 | Default response timeout 500 ms; the host retries up to 3 times with the **same** `seq`. A device that receives a repeated `seq` shall resend its last response without executing the request again. |
| LNK-009 | Operation-specific timeouts (flash erase, verification, test runs) are covered by `Progress` events at least every 500 ms; the host timeout restarts on each `Progress`. |
| LNK-010 | Paged lists carry `page`, `page_count`; the host requests pages in order. |

### A.5 Schema

| ID | Requirement |
|---|---|
| LNK-011 | There shall be exactly one schema file, `protocol/hwlink.fbs`, shared by all four repositories; which repository owns it and how the others consume it is OPEN-G08. |
| LNK-012 | Python code shall be generated with `flatc --python`; C code with `flatcc` (builder + verifier); generation shall run as part of each build. |
| LNK-013 | Schema changes shall be backward compatible within a major version (only add fields at the end, never remove or reorder); the minor version shall be raised on every change. |
| LNK-014 | `HelloReply.role` shall be an enum: `HWVAL = 1`, `BOOTLOADER = 2`, `DEMO = 3`; other values are reserved for future applications. |

### A.6 Error codes

| Code | Meaning |
|---|---|
| `MALFORMED` | Verifier failed or fields missing |
| `UNSUPPORTED` | Message not supported by this role |
| `BAD_ARGUMENT` | A field is out of range |
| `BAD_STATE` | Not allowed now (e.g. `Run` while running, `Activate` before `UpdateEnd`) |
| `BUSY` | Device is busy; retry later |
| `NOT_FOUND` | Unknown test ID, group or setting |
| `BAD_HEADER`, `BAD_LAYOUT`, `BAD_VECTORS` | Image rejected ([BOOT] IMG-001…003) |
| `OUT_OF_ORDER` | Unexpected `UpdateData` offset |
| `FLASH_ERROR` | Flash erase/program/verify failed |
| `CRC_MISMATCH` | Image CRC check failed |
| `WRONG_FLASH_MODE` | BOOT running with single-bank flash |

### A.7 Protocol tests

| ID | Requirement |
|---|---|
| LNK-015 | Encoder/decoder round-trip tests for every message, in Python and C, using shared test vectors. |
| LNK-016 | Framing tests: COBS edge cases, maximum frame, bad CRC, garbage between frames, split and merged reads. |
| LNK-017 | Retry and duplicate-`seq` tests against the simulator. |
| LNK-018 | Baud switch and revert tests. |
| LNK-019 | Version mismatch tests (CON-004). |
| LNK-020 | Throughput test: ≥ 60 KB/s effective payload at 921600 baud for `UpdateData`. |

---

## Appendix B — Change requests to HWVAL

The GUI needs these changes in HWVAL (SRS-HWVAL-F767). All of them were
adopted into HWVAL SRS v0.2 (§6.4 and the requirements listed below) and shall
be implemented before GUI acceptance.

| CR | Change | Adopted as |
|---|---|---|
| CR-01 | New CLI command `mode link`: switches USART3 from the text CLI to HWLINK framing. `EnterTextMode` (or 5 s of `0x00`-free text input starting with `\r`) returns to the text CLI. The existing `mode interactive|script` modes stay. | CLI-034, LINK-001, LINK-002, OPEN-011 |
| CR-02 | Implement the HWVAL message set of Appendix A.3 on top of the existing test framework; every `RESULT` line field (TFW-010/011) shall be available in `TestResult`. | LINK-003…LINK-006 |
| CR-03 | Measured values and limits shall be provided as structured `{value, unit}` and `{min, max, unit}` where numeric, plus the existing text. | TFW-013, LINK-006 |
| CR-04 | After a reset caused by a test (TFW-007), HWVAL in link mode shall restart in link mode and report the stored results through `GetResults` and a `RunFinished` or a resumed run. | LINK-010 |
| CR-05 | In link mode, destructive confirmations (SAFE-005) and equipment confirmations (ENV-003, SAFE-009) shall be sent as `OperatorPrompt` events. | LINK-008, SAFE-012 |
| CR-06 | `HelloReply` shall report role `HWVAL` and flash mode `SINGLE_BANK`. | LINK-007 |
| CR-07 | `B1` presses during "press button" prompts shall be reported so the GUI can close the prompt (TST-032). | LINK-009 |
| CR-08 | The flatcc runtime shall fit within the HWVAL footprint and RAM floors (NFR-003, NFR-004); `check_footprint.py` shall still pass. | LINK-012, NFR-011 |
| CR-09 | Fix or work around the VCP board→host solder bridge (CL-010) on the bench board. | OPEN-009 |

---

## Appendix C — Database schema

```sql
-- PRAGMA user_version = 1; PRAGMA journal_mode = WAL;

CREATE TABLE devices (
  uid           TEXT PRIMARY KEY,          -- 96-bit UID, hex
  dev_id        INTEGER, rev_id INTEGER,
  label         TEXT,
  first_seen    TEXT NOT NULL,             -- ISO 8601 UTC
  last_seen     TEXT NOT NULL
);

CREATE TABLE runs (
  id            INTEGER PRIMARY KEY,
  uid           TEXT NOT NULL REFERENCES devices(uid),
  started_at    TEXT NOT NULL,
  finished_at   TEXT,
  status        TEXT NOT NULL,             -- RUNNING, COMPLETE, ABORTED, INCOMPLETE
  overall       TEXT,                      -- PASS, FAIL
  fw_name       TEXT, fw_version TEXT, fw_commit TEXT,
  gui_version   TEXT NOT NULL,
  mode          TEXT NOT NULL,             -- ENGINEER, OPERATOR, CLI
  operator_name TEXT,
  selection     TEXT NOT NULL,             -- JSON: ids, groups, filters
  n_pass INTEGER DEFAULT 0, n_fail INTEGER DEFAULT 0,
  n_skip INTEGER DEFAULT 0, n_na   INTEGER DEFAULT 0
);

CREATE TABLE results (
  id            INTEGER PRIMARY KEY,
  run_id        INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  test_id       TEXT NOT NULL,
  group_code    TEXT NOT NULL,
  iteration     INTEGER NOT NULL DEFAULT 1,
  result        TEXT NOT NULL,             -- PASS, FAIL, SKIP, N/A, NOT_RUN
  duration_ms   INTEGER,
  reason        TEXT,
  measured_value REAL, measured_unit TEXT, measured_text TEXT,
  limit_min REAL, limit_max REAL, limit_unit TEXT, limits_text TEXT,
  reqs          TEXT,                      -- comma-separated requirement IDs
  finished_at   TEXT NOT NULL
);
CREATE INDEX results_run  ON results(run_id);
CREATE INDEX results_test ON results(test_id);

CREATE TABLE catalogue (                   -- TST-003
  fw_version    TEXT NOT NULL,
  test_id       TEXT NOT NULL,
  group_code    TEXT NOT NULL,
  title         TEXT, level TEXT, operator INTEGER, destructive INTEGER,
  timeout_ms    INTEGER, reqs TEXT,
  PRIMARY KEY (fw_version, test_id)
);

CREATE TABLE firmware_ops (                -- FW-009, SWD-010
  id            INTEGER PRIMARY KEY,
  uid           TEXT,
  at            TEXT NOT NULL,
  kind          TEXT NOT NULL,             -- UART_UPDATE, SWD_FLASH, PROVISION, RESTORE_BENCH
  file_name     TEXT, file_sha256 TEXT,
  image_name    TEXT, image_version TEXT,
  slot          TEXT,                      -- A, B, or NULL
  outcome       TEXT NOT NULL,             -- OK, FAILED, CANCELLED, ROLLED_BACK
  detail        TEXT
);
```

---

## Appendix D — Sidebar and test groups

The sidebar is built from `ListGroups` (TST-001). This table gives the
category, display name and icon for each HWVAL group code; groups not listed
go to **Other** with the generic chip icon (ICN-003).

| Section / category | Group codes (display name) |
|---|---|
| **DEVICE** | Overview (identity, option bytes, clocks, harness) |
| **TEST & VALIDATION** › All Tests | every test |
| › CPU & System | DEV (Device Identity), CORE (Cortex-M7 Core), FRT (FreeRTOS), CACHE (Caches & TCM), MPU, INT (Interrupts & EXTI), DMA, DBG (Debug) |
| › Memory | RAM, FLS (Flash), OB (Option Bytes), OTP, QSPI (Quad-SPI), FMC, SD (SDMMC) |
| › Clocks & Power | CLK (Clocks), PWR (Power), RST (Reset), WDG (Watchdogs), RTC |
| › GPIO & Board I/O | GPIO, LED (LEDs), BTN (Buttons) |
| › Analog | ADC, DAC |
| › Timers | TIM (Timers), LPTIM (Low-Power Timer) |
| › Communication | UART, SPI, I2S, I2C, CAN, SAI, SPDIF |
| › Connectivity | ETH (Ethernet), USB (USB OTG FS), USBHS (USB OTG HS) |
| › Graphics & Media | LTDC, DMA2D, JPEG, DCMI |
| › Other Peripherals | CRC, RNG, CEC, DFSDM, MDIOS |
| › Board | STLK (ST-LINK), BRD (Board) |
| **FIRMWARE** | Update (UART), Flash (SWD), Demo App |
| **DATA** | History, Reports |

## Appendix E — Keyboard shortcuts

macOS shown; on Windows/Linux ⌘ = Ctrl, ⌥ = Alt.

| Action | Shortcut |
|---|---|
| Connect / Disconnect | ⌘K / ⇧⌘K |
| Run Selected | ⌘R |
| Run Group | ⌥⌘R |
| Run All… | ⇧⌘R |
| Abort | ⌘. |
| Find | ⌘F |
| Preferences | ⌘, |
| Show/Hide Sidebar | ⌃⌘S (Ctrl+Alt+S elsewhere) |
| Show/Hide Log | ⇧⌘L |
| Operator Mode | ⇧⌘O |
| Firmware Update | ⇧⌘U |
| Export Report | ⇧⌘E |
| Zoom In / Out / Actual | ⌘+ / ⌘− / ⌘0 |
| Close Window / Quit | ⌘W / ⌘Q |

## Appendix F — Open items

| ID | Item | Status |
|---|---|---|
| OPEN-G01 | Final product name (working name "HWVAL Studio"). | Open |
| OPEN-G02 | Bundle OpenOCD in the packages, or require a separate install. | Open |
| OPEN-G03 | Code signing and notarisation (macOS Developer ID, Windows Authenticode). Without them users see Gatekeeper/SmartScreen warnings. | Open |
| OPEN-G04 | Confirm OpenOCD can write `nDBANK`/`nDBOOT` on the F767 ([BOOT] OPEN-B05); fallback STM32CubeProgrammer CLI. | Open |
| OPEN-G05 | Plotting library for §18 (QtCharts vs pyqtgraph). | Deferred |
| OPEN-G06 | Dark theme (tokens prepared, LNF-002). | Deferred |
| OPEN-G07 | Check the PySide6 LGPL obligations for the PyInstaller bundles (dynamic linking, licence text, relinking). | Open |
| OPEN-G08 | Home of the shared schema `protocol/hwlink.fbs` now that each project is its own repository (e.g. a `soccentric-stm32-protocol` repository used as a git submodule). | Open |
