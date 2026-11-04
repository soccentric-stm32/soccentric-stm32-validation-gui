# HWVAL Studio user guide

HWVAL Studio is the desktop host for the NUCLEO-F767ZI validation platform.
It talks to the board over the ST-LINK virtual COM port (USART3) with the
HWLINK protocol and uses OpenOCD over SWD only for flashing and provisioning.

## 1. Connect

1. Plug the NUCLEO-F767ZI into the PC with the ST-LINK USB cable.
2. Start HWVAL Studio. Press **Refresh Ports** if the board was plugged in
   after the application started. ST-LINK VCPs are listed first and marked
   **ST-LINK**.
3. Select the port and press **Connect**.

The application sends `Hello` and identifies the running firmware:

| Role | What you can do |
|---|---|
| HWVAL | Read the catalogue, run tests, harness check, device overview |
| BOOTLOADER | Update an application image over UART, activate a slot |
| DEMO | Control LEDs, read status/faults, enter the bootloader |

HWVAL normally starts in its text CLI. HWVAL Studio sends `mode link` and
retries `Hello` automatically. If there is no HWLINK device, use
**Tools → Serial Console** to inspect the text output.

To use the simulator without hardware, choose **Tools → Device Simulator**
and connect the in-process HWVAL/BOOT/DEMO device. The same dialog can start a
TCP simulator on `127.0.0.1:7000`; connect other tools to
`tcp://127.0.0.1:7000`.

## 2. Run tests

The sidebar is built from the catalogue reported by HWVAL. Select **All
Tests** or a group.

* **Run Group** runs every test of the selected group.
* **Run Selected** runs the rows selected in the table.
* **Run All…** in the Tests menu runs the full catalogue.
* The **S / L / E** buttons filter the standard, lab and extended levels.
* **Operator tests** enable tests that ask you to press a button or connect
  equipment. **Destructive** tests are off by default and need a
  confirmation that names the affected tests. The toggle resets after a run.
* **Repeat** repeats the selection; **Until fail** stops after the first
  failure.
* **Abort** (⌘. / Ctrl+.) asks the device to stop. Unfinished tests are marked
  NOT RUN.

During a run the table, group badges, details pane and toolbar activity view
update live. Double-click a row (or use the context menu) to copy the test ID
or result, run the test again, or open the run history filtered to that test.

Operator prompts open as a sheet with the instruction, an icon for the action
type, answer buttons and a countdown. If the window is not focused the
application beeps, comes to the front and requests attention. A button prompt
closes automatically when the board reports the B1 press.

The **Details** pane shows the description, level/flags, harness needs,
measured value, limits, reason, requirement IDs, duration and log lines.

## 3. Firmware update over UART

Open **Firmware → Update (UART)**.

* Two cards show slot A/B: name, version, build time, commit, size, state and
  the last boot outcome.
* Choose a `.img` file or drag it onto the page. The 256-byte header is
  checked locally (magic, layout, header CRC32, image CRC32, vector table).
* The application warns when the image version is not newer than the active
  slot, or when the image name changes.
* **Update Firmware** sends `UpdateBegin`, 1024-byte `UpdateData` chunks and
  `UpdateEnd`. Every request is retried up to three times with the same
  sequence number. A chunk may wait for a sector erase; progress events
  restart the timeout.
* **Activate and reboot after verification** is enabled by default. The
  application then reconnects and watches the trial boot until the slot is
  confirmed or rejected (60 s).
* **Cancel** sends `UpdateAbort`; the active slot is unchanged.

When HWVAL is connected (bench configuration, single-bank flash), the page
explains that UART update needs the product configuration and points to
**Tools → Provision Product Configuration**.

When DEMO is connected, the application sends `EnterBootloader`, reconnects
to BOOT and then uploads.

All attempts and outcomes are recorded in the local history database.

## 4. Flash and provision over SWD

Open **Firmware → Flash (SWD)**.

1. Install OpenOCD 0.12 or newer and put it on `PATH`, or set its path in
   **Preferences → Firmware**. Use **Check OpenOCD** to verify.
2. **Detect ST-LINK and Target** shows DEV_ID, REV_ID, flash size and the
   option bytes (read-only).
3. **Flash HWVAL** switches to single-bank flash if needed, mass-erases,
   programs and verifies an `.elf`, `.hex` or `.bin` at `0x0800 0000`, then
   resets.
4. **Provision Product Configuration** sets nDBANK=0 and nDBOOT=1, mass-erases,
   programs and verifies `boot.hex` at `0x0800 0000`, and resets. Connect to
   BOOT over UART afterwards to load the first application.
5. **Restore Bench Configuration** sets nDBANK=1, mass-erases and optionally
   flashes HWVAL.

Every flash-changing operation asks for confirmation and states that all
flash contents are lost. The application never changes RDP, WRP or
BOOT_ADD, and has no UI for them. OpenOCD runs as a separate process, its
output is shown live, and it is stopped after each operation so the ST-LINK
is released.

The serial link is closed before an SWD operation resets the target and
reopened afterwards.

## 5. Demo application

The **Firmware → Demo App** page is enabled when DEMO is connected.

* Status: version, uptime, running slot, trial state, reset cause, fault,
  heap and task stack high-water marks, refreshed every second.
* LD1 and LD2 mirror the board. Choose a pattern and a period (50–5000 ms).
  LD3 is reserved for fault indication. **Apply to all** sets all three.
* **Clear Fault**, **Reset** and **Enter Bootloader**.

## 6. History and reports

**Data → History** lists stored runs (date, board, firmware, selection,
totals, overall, mode, operator) with filters for board, date range, result,
firmware version and mode. Select one run to open it read-only, two runs to
compare and highlight changed results, or export/delete runs. **Label Board…**
sets a friendly device name.

**Data → Reports** previews the Markdown report and can:

* export JSON and Markdown reports with the same content and naming as
  `hwtest.py` (`hwval_<UID8>_<date>.json/.md`);
* export the whole run history as CSV or JSON;
* import a `hwtest.py` JSON report;
* print a report or save it to PDF through the platform print dialog.

Measured values and limits are stored numerically with their unit, so future
trend plots need no schema change.

## 7. Operator mode

**View → Operator Mode** (⇧⌘O) switches to the simplified screen:

* board identity and operator name;
* one large **Run** button and a progress indicator;
* the current test title and a large PASS/FAIL result;
* the list of failed tests.

The run selection is fixed in **Preferences → Operator** by an engineer
(levels and operator tests; destructive tests are never allowed). Operators
cannot change it and cannot access firmware flashing, provisioning, the
serial console or preferences. Every operator run is saved automatically and
optionally exported to the configured folder.

Start directly in operator mode with `hwval-studio --operator` or the
**Start in operator mode** preference. If a PIN is set in Preferences, it is
required to leave operator mode.

## 8. Preferences

Preferences use macOS-style tabs and apply immediately:

* **General** — start in operator mode, show log on start, confirm before
  quitting during a run.
* **Connection** — default port, auto-connect, fast 921600 baud.
* **Tests** — default levels, operator tests, repeat and until-fail.
* **Firmware** — OpenOCD path, image folder, auto-activate.
* **History** — database location, retention (keep all or last N days),
  auto-export folder.
* **Operator** — fixed run selection, exit PIN, operator names, auto-export.

Window size, position, sidebar width, splitter positions and the selected
sidebar item are restored on the next start.

## 9. Log and troubleshooting

The collapsible log console shows timestamped protocol events, OpenOCD
output and errors. Filter by level, search, copy, clear, and enable **Hex**
to see raw HWLINK frames at debug level.

The rotating log file (`5 × 5 MB`) is in the platform log folder
(**Help → Show Log Folder**). Uncaught exceptions are logged with a
traceback and shown in a dialog with **Copy details**.

Common problems:

* **Permission denied on Linux** — add your user to `dialout` (Debian/Ubuntu)
  or `uucp` (some distributions), install the ST-LINK udev rules, and log in
  again.
* **No HWLINK device** — HWVAL may still be in text mode; the application
  tries `mode link`. Use the Serial Console if the firmware has no HWLINK
  support.
* **OpenOCD missing** — install it with `brew install openocd`,
  `winget install OpenOCD.OpenOCD`, `apt install openocd` or
  `dnf install openocd`, or set the path in Preferences.
* **Option bytes could not be written** — some OpenOCD builds cannot write
  F767 option bytes (OPEN-G04). Set nDBANK/nDBOOT with
  STM32CubeProgrammer, then repeat the operation.

## 10. Keyboard shortcuts

See **Help → Keyboard Shortcuts**. On Windows/Linux, use Ctrl instead of ⌘
and Alt instead of ⌥.

| Action | Shortcut |
|---|---|
| Connect / Disconnect | ⌘K / ⇧⌘K |
| Run Selected | ⌘R |
| Run Group | ⌥⌘R |
| Run All… | ⇧⌘R |
| Abort | ⌘. |
| Find | ⌘F |
| Preferences | ⌘, |
| Show/Hide Sidebar | ⌃⌘S |
| Show/Hide Log | ⇧⌘L |
| Operator Mode | ⇧⌘O |
| Firmware Update | ⇧⌘U |
| Export Report | ⇧⌘E |
| Zoom In / Out / Actual | ⌘+ / ⌘− / ⌘0 |
| Close / Quit | ⌘W / ⌘Q |
