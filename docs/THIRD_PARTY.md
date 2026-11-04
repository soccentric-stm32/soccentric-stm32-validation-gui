# Third-party licences

HWVAL Studio is MIT licensed. The following third-party components are used
and distributed with the application. The full licence texts are included in
the packages and in this folder.

| Component | Use | Licence | Source |
|---|---|---|---|
| PySide6 / Qt 6 | GUI toolkit | LGPL-3.0 (or commercial) | https://www.qt.io/qt-for-python |
| pyserial | Serial port access | BSD-3-Clause | https://github.com/pyserial/pyserial |
| FlatBuffers Python runtime | HWLINK payload encoding | Apache-2.0 | https://github.com/google/flatbuffers |
| Inter | UI font (Windows/Linux) | SIL Open Font License 1.1 | https://github.com/rsms/inter |
| JetBrains Mono | Monospace font (Windows/Linux) | SIL Open Font License 1.1 | https://github.com/JetBrains/JetBrainsMono |
| Lucide-style line icons | UI icons (original SVG paths) | MIT-compatible / original | drawn for this project |
| OpenOCD | SWD flashing (external program) | GPL-2.0 (not bundled in v0.1) | https://openocd.org |

## Notes

* The SVG icons under `resources/icons` are original line drawings in a
  Lucide-compatible 24 px grid. They may be redistributed under the MIT
  licence of this project.
* On macOS the system font (SF Pro) and system monospace font are used; Apple
  fonts and SF Symbols are not bundled.
* OpenOCD is invoked as a separate process and is not bundled in v0.1. The
  user installs it separately (see the user guide).
* PySide6 is dynamically linked. See the LGPL-3.0 text shipped with PySide6
  for the relinking and notice obligations.

The licence texts for the fonts are in `resources/fonts/OFL-Inter.txt` and
`resources/fonts/OFL-JetBrainsMono.txt`. The PySide6, pyserial and FlatBuffers
licence texts are shipped by their packages and listed in the platform
installers.
