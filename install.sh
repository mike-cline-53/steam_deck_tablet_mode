#!/bin/bash
#
# install.sh — Steam Deck Vertical Mode installer
#
# Installs the Onboard on-screen keyboard, creates a Mac-style layout
# (with ⌘ Command key), configures docking, and sets up the tray toggle.
#
# Run this script ON the Steam Deck in Desktop Mode:
#   chmod +x install.sh && ./install.sh

set -euo pipefail

main() {
    echo "=== Steam Deck Vertical Mode — Installer ==="
    echo ""

    install_onboard
    create_mac_layout
    configure_onboard_defaults
    setup_scripts
    create_autostart_entry

    echo ""
    echo "=== Installation Complete ==="
    echo ""
    echo "Usage:"
    echo "  1. Make sure you are in Desktop Mode with an X11 session."
    echo "     (At the SDDM login screen, pick 'Plasma (X11)' if needed.)"
    echo "  2. Run:  python3 ${SCRIPT_DIR}/vertical_mode.py"
    echo "  3. Left-click the tray icon to toggle portrait / landscape."
    echo ""
    echo "Auto-start is already configured. The tray icon will appear"
    echo "next time you enter Desktop Mode."
}

install_onboard() {
    echo "[1/5] Installing Onboard on-screen keyboard..."
    if command -v onboard &>/dev/null; then
        echo "       Onboard is already installed — skipping."
        return
    fi
    sudo steamos-readonly disable
    sudo pacman -S --noconfirm --needed onboard
    sudo steamos-readonly enable
}

create_mac_layout() {
    echo "[2/5] Creating Mac-style keyboard layout..."
    mkdir -p "$LAYOUT_DST"

    if [ ! -d "$LAYOUT_SRC" ]; then
        echo "  WARNING: Onboard layout source directory not found at $LAYOUT_SRC"
        echo "           Skipping layout patching. You may need to set the layout manually."
        return
    fi

    for src_file in "$LAYOUT_SRC"/Compact*; do
        [ -f "$src_file" ] || continue
        base="$(basename "$src_file")"
        dst_file="$LAYOUT_DST/${base/Compact/MacStyle}"
        cp "$src_file" "$dst_file"
    done

    for shared in key_defs.xml word_suggestions.xml; do
        [ -f "$LAYOUT_SRC/$shared" ] && cp "$LAYOUT_SRC/$shared" "$LAYOUT_DST/"
    done

    if [ -f "$LAYOUT_DST/MacStyle.onboard" ]; then
        sed -i 's/Compact-/MacStyle-/g'          "$LAYOUT_DST/MacStyle.onboard"
        sed -i 's/id="Compact"/id="MacStyle"/g'  "$LAYOUT_DST/MacStyle.onboard"
        sed -i 's/label="Super"/label="⌘"/g'     "$LAYOUT_DST/MacStyle.onboard"
    fi

    for svg in "$LAYOUT_DST"/MacStyle-*.svg; do
        [ -f "$svg" ] || continue
        sed -i 's/>Super</>⌘</g'              "$svg"
        sed -i 's/"Super"/"⌘"/g'              "$svg"
        sed -i 's/label="Super"/label="⌘"/g'  "$svg"
    done

    echo "       Layout installed to: $LAYOUT_DST"
}

configure_onboard_defaults() {
    echo "[3/5] Configuring Onboard docking and theme..."
    local layout_file="$LAYOUT_DST/MacStyle.onboard"

    gsettings set org.onboard.window docking-enabled true
    gsettings set org.onboard.window docking-edge "'bottom'"
    gsettings set org.onboard.window docking-shrink-workarea true

    if [ -f "$layout_file" ]; then
        gsettings set org.onboard layout "'$layout_file'"
    fi

    gsettings set org.onboard theme "'/usr/share/onboard/themes/${ONBOARD_THEME}'"

    echo "       Docking: bottom edge, work-area shrink enabled"
}

setup_scripts() {
    echo "[4/5] Making scripts executable..."
    chmod +x "$SCRIPT_DIR/vertical_mode.py"
}

create_autostart_entry() {
    echo "[5/5] Adding to KDE Autostart..."
    local autostart_dir="$HOME/.config/autostart"
    local desktop_file="$autostart_dir/vertical_mode.desktop"
    mkdir -p "$autostart_dir"
    cp "$SCRIPT_DIR/vertical_mode.desktop" "$desktop_file"
    sed -i "s|Exec=.*|Exec=python3 ${SCRIPT_DIR}/vertical_mode.py|" "$desktop_file"
    echo "       Desktop entry copied to $autostart_dir/"
}


# ============================================================================
# USER CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Onboard system layout directory (where built-in layouts live after install)
LAYOUT_SRC="/usr/share/onboard/layouts"

# User layout directory (custom layouts go here, no root needed)
LAYOUT_DST="$HOME/.local/share/onboard/layouts"

# Onboard theme to apply (filename without extension, from /usr/share/onboard/themes/)
ONBOARD_THEME="DarkRoom"


main "$@"
