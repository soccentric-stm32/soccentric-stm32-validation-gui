# soccentric-stm32-validation-gui

HWVAL Studio: a cross-platform (macOS, Windows, Linux) PySide6 desktop app with a macOS-style look. It runs and records the HWVAL hardware validation tests over UART, keeps the run history in SQLite, updates application firmware through the bootloader, and flashes firmware over SWD with OpenOCD. The SRS also holds the shared HWLINK protocol (Appendix A).

| | |
|---|---|
| Requirements | [SRS.md](SRS.md) — SRS-GUI-F767 (v0.1 draft) |
| Board | NUCLEO-F767ZI — see [Hardware.md](https://github.com/soccentric-stm32/soccentric-stm32-validation-firmware/blob/HEAD/Hardware.md) |
| Status | Specification only; no implementation yet |

## Related projects

| Repository | Role |
|---|---|
| [soccentric-stm32-validation-firmware](https://github.com/soccentric-stm32/soccentric-stm32-validation-firmware) | HWVAL hardware validation firmware |
| [soccentric-stm32-bootloader](https://github.com/soccentric-stm32/soccentric-stm32-bootloader) | A/B bootloader (UART update, CRC32, trial boot and rollback) |
| [soccentric-stm32-application](https://github.com/soccentric-stm32/soccentric-stm32-application) | FreeRTOS demo application (LEDs, button, HWLINK) |
| [soccentric-stm32-validation-gui](https://github.com/soccentric-stm32/soccentric-stm32-validation-gui) | PySide6 GUI: runs HWVAL tests, updates and flashes firmware |

Author: Sandesh Ghimire <sandesh@soccentric.com>
