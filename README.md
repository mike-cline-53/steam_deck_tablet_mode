# Steam Deck Tablet Mode

A system tray application that toggles the Steam Deck between standard landscape and portrait (tablet) mode in Desktop Mode. When switching to portrait, the screen rotates, touchscreen input is remapped, and a docked on-screen keyboard appears at the bottom of the display.

Designed for holding the Deck vertically with the left grip at the bottom -- putting the USB-C port and headphone jack near the top-left, out of the way.

## Features

- **One-click toggle** via system tray icon (left-click to switch, right-click for menu)
- **Screen rotation** using xrandr, calibrated for the Steam Deck's natively-portrait panel
- **Touchscreen remapping** so touch input stays accurate in both orientations
- **Docked on-screen keyboard** ([Onboard](https://github.com/onboard-osk/onboard)) that reserves screen space so windows don't overlap it
- **Auto-restores landscape** on quit
- **Works on both LCD and OLED** Steam Deck models (auto-detects touchscreen device)

## Requirements

- Steam Deck in **Desktop Mode** with an **X11 session** (Wayland is not yet supported; Onboard requires X11)
- SteamOS 3.x

## Quick Start

### One-liner install

Open Konsole on the Steam Deck (in Desktop Mode) and run:

```bash
git clone https://github.com/mike-cline-53/steam_deck_tablet_mode.git ~/steam_deck_tablet_mode && cd ~/steam_deck_tablet_mode && bash install.sh
```

> **Note:** If you hit pacman keyring errors, run this first:
> `sudo pacman-key --init && sudo pacman-key --populate archlinux holo`

### Manual install

#### 1. Transfer files to the Steam Deck

From your computer (replace `<DECK_IP>` with your Deck's IP address):

```bash
scp -r . deck@<DECK_IP>:~/Documents/steamdeck/
```

> To find the Deck's IP: open Konsole on the Deck and run `ip -4 addr show wlan0`.
> SSH must be started first: `sudo systemctl start sshd` (and set a password with `passwd` if you haven't).

#### 2. Run the installer

On the Steam Deck (via SSH or Konsole):

```bash
cd ~/Documents/steamdeck
chmod +x install.sh
bash ./install.sh
```

This will:
- Install the Onboard on-screen keyboard via pacman
- Initialize the pacman keyring if needed (`sudo pacman-key --init && sudo pacman-key --populate archlinux holo`)
- Create a Mac-style keyboard layout with Command key labels
- Configure Onboard docking (bottom edge, DarkRoom theme)
- Add the tray toggle to KDE Autostart

#### 3. Use it

```bash
python3 vertical_mode.py
```

A monitor icon appears in the system tray. Left-click to toggle between landscape and portrait. The tray icon will auto-start on subsequent Desktop Mode sessions.

## Configuration

All user-configurable values are grouped at the bottom of `vertical_mode.py`:

| Variable | Default | Description |
|---|---|---|
| `DISPLAY_OUTPUT` | `"eDP"` | xrandr display output name |
| `PORTRAIT_ROTATION` | `"inverted"` | xrandr rotation for portrait (left grip down) |
| `LANDSCAPE_ROTATION` | `"right"` | xrandr rotation for standard landscape |
| `TOUCHSCREEN_DEVICE_FALLBACK` | `"FTS3528:00 2808:1015"` | xinput device name if auto-detection fails |
| `PORTRAIT_CTM` | `"-1 0 1 0 -1 1 0 0 1"` | Touchscreen coordinate transform for portrait |
| `LANDSCAPE_CTM` | `"0 1 0 -1 0 1 0 0 1"` | Touchscreen coordinate transform for landscape |
| `KEYBOARD_LAYOUT` | `"Small"` | Onboard layout name |
| `KEYBOARD_THEME` | `"DarkRoom"` | Onboard theme (works well on OLED) |
| `KEYBOARD_LAUNCH_DELAY_MS` | `800` | Delay after rotation before showing keyboard |

## File Overview

| File | Purpose |
|---|---|
| `vertical_mode.py` | Main application -- PyQt5 system tray toggle |
| `install.sh` | SteamOS installer (Onboard, layout, docking config, autostart) |
| `vertical_mode.desktop` | KDE autostart desktop entry |
| `notes.md` | Project notes and hardware reference links |

## Troubleshooting

**Screen boots upside down:** KDE may have saved a wrong rotation. Delete the kscreen config and reboot:
```bash
rm -rf ~/.local/share/kscreen/*
```

**Tray icon is invisible:** The script needs the Breeze icon theme. This is set automatically, but if running over SSH make sure `DISPLAY` and `XAUTHORITY` are exported.

**Keyboard doesn't appear:** Check that Onboard is installed (`which onboard`) and that `start-minimized` is not enabled:
```bash
gsettings set org.onboard start-minimized false
```

**Wayland session:** Onboard does not support Wayland. At the SDDM login screen, select "Plasma (X11)" instead.

**pacman keyring errors during install:** Initialize the keyring first:
```bash
sudo pacman-key --init
sudo pacman-key --populate archlinux holo
```

## Hardware Reference

Official Valve Steam Deck CAD files (CC BY-NC-SA 4.0):
https://gitlab.steamos.cloud/SteamDeck/hardware

## License

MIT License. See [LICENSE](LICENSE) for details.
