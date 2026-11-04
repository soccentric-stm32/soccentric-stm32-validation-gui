"""All platform-specific code lives here (GNFR-008)."""

from __future__ import annotations

import platform
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QWidget


def is_macos() -> bool:
    return sys.platform == "darwin"


def is_windows() -> bool:
    return sys.platform.startswith("win")


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def platform_name() -> str:
    return {"darwin": "macOS", "win32": "Windows"}.get(sys.platform, "Linux")


def native_menu_bar() -> bool:
    return is_macos()


def modifier_symbols() -> tuple[str, str]:
    if is_macos():
        return "⌘", "⌥"
    return "Ctrl+", "Alt+"


def serial_permission_hint(port: str, error: str) -> str:
    lowered = error.lower()
    if "permission" not in lowered and "access is denied" not in lowered:
        return ""
    if is_linux():
        return (
            f"Cannot open {port}: permission denied.\n\n"
            "Add your user to the serial group and log in again:\n"
            "  sudo usermod -aG dialout $USER      (Debian/Ubuntu)\n"
            "  sudo usermod -aG uucp $USER         (Arch/Fedora variants)\n\n"
            "Install the ST-LINK udev rules if the probe is not accessible.\n"
            "See the user guide (Help > HWVAL User Guide)."
        )
    if is_macos():
        return (
            f"Cannot open {port}: permission denied.\n\n"
            "Check that no other application (serial terminal, debugger) holds the port. "
            "On macOS the ST-LINK VCP is usually /dev/cu.usbmodem*."
        )
    return (
        f"Cannot open {port}: access denied.\n\n"
        "Close any serial terminal or debugger using the port, then retry."
    )


def bring_to_front(widget: QWidget) -> None:
    widget.show()
    widget.raise_()
    widget.activateWindow()
    if is_macos():
        try:
            from AppKit import NSApp

            NSApp.activateIgnoringOtherApps_(True)
        except Exception:
            pass


def alert_sound() -> None:
    QApplication.beep()


def request_attention(widget: QWidget) -> None:
    """Bounce the Dock icon on macOS or flash the taskbar button elsewhere."""
    if is_macos():
        try:
            from AppKit import NSApp, NSInformationalRequest

            NSApp.requestUserAttention_(NSInformationalRequest)
            return
        except Exception:
            pass
    if is_windows():
        try:
            import ctypes

            hwnd = int(widget.winId())
            ctypes.windll.user32.FlashWindow(hwnd, True)
        except Exception:
            pass


def _windows_taskbar_progress(widget: QWidget, value: int, maximum: int) -> bool:
    try:
        import ctypes
        from ctypes import POINTER, Structure, c_int, c_ulonglong, c_void_p, wintypes

        class _GUID(Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", wintypes.BYTE * 8),
            ]

        clsid = _GUID(
            0x56FDF344,
            0xFD6D,
            0x11D0,
            (wintypes.BYTE * 8)(0x95, 0x8A, 0x00, 0x60, 0x97, 0xC9, 0xA0, 0x90),
        )
        iid = _GUID(
            0xEA1AFB91,
            0x9E28,
            0x4B86,
            (wintypes.BYTE * 8)(0x90, 0xE9, 0x9E, 0x9F, 0x8A, 0x5E, 0xEA, 0x84),
        )
        global _TASKBAR
        if "_TASKBAR" not in globals():
            ctypes.windll.ole32.CoInitialize(None)
            pointer = c_void_p()
            ctypes.windll.ole32.CoCreateInstance(
                ctypes.byref(clsid), None, 1, ctypes.byref(iid), ctypes.byref(pointer)
            )
            _TASKBAR = pointer
        hwnd = int(widget.winId())
        vtable = ctypes.cast(_TASKBAR, POINTER(POINTER(c_void_p))).contents
        set_state = ctypes.WINFUNCTYPE(ctypes.HRESULT, c_void_p, c_int)(vtable[9])
        if maximum <= 0:
            set_state(hwnd, 0)  # TBPF_NOPROGRESS
        else:
            set_state(hwnd, 2)  # TBPF_NORMAL
            set_value = ctypes.WINFUNCTYPE(ctypes.HRESULT, c_void_p, c_ulonglong, c_ulonglong)(vtable[8])
            set_value(hwnd, int(value), int(maximum))
        return True
    except Exception:
        return False


def set_progress(widget: QWidget, value: int, maximum: int) -> None:
    """Show progress in the Dock tile (macOS) or taskbar/window title."""
    if is_macos():
        try:
            from AppKit import NSApp

            if maximum <= 0:
                NSApp.dockTile().setBadgeLabel_(None)
            else:
                NSApp.dockTile().setBadgeLabel_(f"{int(100 * value / maximum)}%")
            return
        except Exception:
            pass
    if is_windows() and _windows_taskbar_progress(widget, value, maximum):
        return
    if maximum > 0:
        widget.setWindowTitle(f"[{int(100 * value / maximum)}%] HWVAL Studio")
    else:
        widget.setWindowTitle("HWVAL Studio")


def reveal_path(path: str | Path) -> bool:
    p = Path(path)
    if p.is_file():
        p = p.parent
    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))


def open_url(url: str) -> bool:
    return QDesktopServices.openUrl(QUrl(url))


def default_monospace() -> str:
    if is_macos():
        return "SF Mono"
    if is_windows():
        return "Consolas"
    return "DejaVu Sans Mono"


def python_version_text() -> str:
    return f"Python {platform.python_version()} on {platform_name()} {platform.machine()}"
