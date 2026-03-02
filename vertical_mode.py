#!/usr/bin/env python3
"""
Steam Deck Vertical Mode Toggle

System tray application that toggles between landscape and portrait (vertical)
mode on the Steam Deck in Desktop Mode (X11). Manages screen rotation,
touchscreen input remapping, and a docked Onboard on-screen keyboard with
a Mac-style Command key layout.

Usage:
    python3 vertical_mode.py

    Left-click the tray icon to toggle between portrait and landscape.
    Right-click for a context menu with toggle and quit options.
    Quitting always restores landscape orientation.
"""

import os
import re
import subprocess
import signal
import sys

from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer


class VerticalModeToggle:

    def __init__(self):
        self.is_portrait = False
        self.keyboard_process = None
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        QIcon.setThemeName("breeze")

        if not self._check_display_server():
            sys.exit(1)

        self.touchscreen_device = self._detect_touchscreen()
        self._setup_tray()

    def _check_display_server(self):
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if session_type == "wayland":
            QMessageBox.warning(
                None,
                "Vertical Mode — Wayland Detected",
                "This tool requires an X11 session.\n\n"
                "To switch:\n"
                "1. Log out of Desktop Mode\n"
                "2. At the SDDM login screen, click the session selector\n"
                "   (bottom-left corner)\n"
                "3. Choose 'Plasma (X11)'\n"
                "4. Log back in and re-launch this tool",
            )
            return False
        return True

    def _detect_touchscreen(self):
        """Parse xinput list to find the touchscreen device name."""
        try:
            output = subprocess.check_output(["xinput", "list"], text=True)
            for line in output.splitlines():
                if "touch" not in line.lower():
                    continue
                match = re.search(r"↳\s*(.+?)\s+id=", line)
                if match:
                    return match.group(1).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        return TOUCHSCREEN_DEVICE_FALLBACK

    def _setup_tray(self):
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon.fromTheme("video-display"))
        self.tray.setToolTip("Vertical Mode: Landscape")

        menu = QMenu()

        self.toggle_action = QAction("Switch to Portrait")
        self.toggle_action.triggered.connect(self.toggle_mode)
        menu.addAction(self.toggle_action)

        menu.addSeparator()

        quit_action = QAction("Quit (Restore Landscape)")
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_click)
        self.tray.show()

    def _on_tray_click(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_mode()

    def _run_cmd(self, cmd, error_context="Command"):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(
                    f"[vertical_mode] {error_context} failed: "
                    f"{result.stderr.strip()}",
                    file=sys.stderr,
                )
                return False
            return True
        except FileNotFoundError:
            print(
                f"[vertical_mode] {error_context}: "
                f"'{cmd[0]}' not found",
                file=sys.stderr,
            )
            return False

    def _rotate_screen(self, portrait=True):
        orientation = PORTRAIT_ROTATION if portrait else LANDSCAPE_ROTATION
        self._run_cmd(
            ["xrandr", "--output", DISPLAY_OUTPUT, "--rotate", orientation],
            "Screen rotation",
        )

    def _remap_touchscreen(self, portrait=True):
        matrix = PORTRAIT_CTM if portrait else LANDSCAPE_CTM
        self._run_cmd(
            [
                "xinput", "set-prop", self.touchscreen_device,
                "--type=float", "Coordinate Transformation Matrix",
            ] + matrix.split(),
            "Touchscreen remap",
        )

    def _resolve_layout_path(self):
        """Return the Onboard layout file path, preferring the user directory."""
        for base in [
            os.path.expanduser("~/.local/share/onboard/layouts"),
            "/usr/share/onboard/layouts",
        ]:
            path = os.path.join(base, f"{KEYBOARD_LAYOUT}.onboard")
            if os.path.exists(path):
                return path
        return f"/usr/share/onboard/layouts/{KEYBOARD_LAYOUT}.onboard"

    def _configure_onboard(self):
        """Set Onboard docking, layout, and theme via gsettings."""
        layout_path = self._resolve_layout_path()
        pairs = [
            ("org.onboard.window", "docking-enabled", "true"),
            ("org.onboard.window", "docking-edge", "'bottom'"),
            ("org.onboard.window", "docking-shrink-workarea", "true"),
            ("org.onboard.window", "force-to-top", "true"),
            ("org.onboard", "start-minimized", "false"),
            ("org.onboard", "layout", f"'{layout_path}'"),
            ("org.onboard", "theme", f"'/usr/share/onboard/themes/{KEYBOARD_THEME}.theme'"),
        ]
        for schema, key, value in pairs:
            self._run_cmd(
                ["gsettings", "set", schema, key, value],
                f"gsettings {schema} {key}",
            )

    def _launch_keyboard(self):
        self._configure_onboard()
        layout_path = self._resolve_layout_path()
        env = os.environ.copy()
        env.setdefault("DISPLAY", ":0")
        try:
            self.keyboard_process = subprocess.Popen(
                ["onboard", "--layout", layout_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
            )
        except FileNotFoundError:
            QMessageBox.warning(
                None,
                "Onboard Not Found",
                "The Onboard on-screen keyboard is not installed.\n\n"
                "Run install.sh on your Steam Deck to install it.",
            )

    def _kill_keyboard(self):
        if self.keyboard_process:
            self.keyboard_process.terminate()
            try:
                self.keyboard_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.keyboard_process.kill()
            self.keyboard_process = None
        self._run_cmd(["pkill", "-f", "onboard"], "Kill onboard")

    def toggle_mode(self):
        if self.is_portrait:
            self._kill_keyboard()
            self._rotate_screen(portrait=False)
            self._remap_touchscreen(portrait=False)
            self.toggle_action.setText("Switch to Portrait")
            self.tray.setToolTip("Vertical Mode: Landscape")
            self.tray.setIcon(QIcon.fromTheme("video-display"))
        else:
            self._rotate_screen(portrait=True)
            self._remap_touchscreen(portrait=True)
            QTimer.singleShot(KEYBOARD_LAUNCH_DELAY_MS, self._launch_keyboard)
            self.toggle_action.setText("Switch to Landscape")
            self.tray.setToolTip("Vertical Mode: Portrait")
            self.tray.setIcon(QIcon.fromTheme("phone"))
        self.is_portrait = not self.is_portrait

    def quit_app(self):
        if self.is_portrait:
            self._kill_keyboard()
            self._rotate_screen(portrait=False)
            self._remap_touchscreen(portrait=False)
        self.tray.hide()
        self.app.quit()

    def run(self):
        signal.signal(signal.SIGINT, lambda *_: self.quit_app())
        signal.signal(signal.SIGTERM, lambda *_: self.quit_app())
        sys.exit(self.app.exec_())


# ============================================================================
# USER CONFIGURATION
# Modify these values to match your Steam Deck model and preferences.
# Find display name with:   xrandr --listmonitors
# Find touchscreen with:    xinput list | grep -i touch
# ============================================================================

# Display output name reported by xrandr
DISPLAY_OUTPUT = "eDP"

# Rotation values for xrandr. The Steam Deck's panel is natively portrait,
# so Desktop Mode uses "right" for landscape. "inverted" gives portrait
# with the left grip at the bottom (USB-C near top-left).
PORTRAIT_ROTATION = "inverted"
LANDSCAPE_ROTATION = "right"

# Fallback touchscreen xinput device name (used when auto-detection fails).
# OLED default: "FTS3528:00 2808:1015"
TOUCHSCREEN_DEVICE_FALLBACK = "FTS3528:00 2808:1015"

# Touchscreen coordinate transformation matrices (3x3 affine, flattened).
# For "inverted" portrait: -1 0 1 0 -1 1 0 0 1
# For "right" landscape:    0 1 0 -1 0 1 0 0 1
PORTRAIT_CTM = "-1 0 1 0 -1 1 0 0 1"
LANDSCAPE_CTM = "0 1 0 -1 0 1 0 0 1"

# Onboard on-screen keyboard layout.
# "Small" is a good fit for the Deck's screen. "MacStyle" is a patched Compact
# layout with ⌘ Command keys (created by install.sh).
KEYBOARD_LAYOUT = "Small"

# Onboard theme. "DarkRoom" works well with the OLED display.
KEYBOARD_THEME = "DarkRoom"

# Delay in milliseconds after rotating before launching the keyboard.
# Gives the compositor time to update the display geometry.
KEYBOARD_LAUNCH_DELAY_MS = 800


if __name__ == "__main__":
    toggle = VerticalModeToggle()
    toggle.run()
