#!/data/data/com.termux/files/usr/bin/bash
# Auto-start hook for the Termux:Boot app.
# One-time setup: see "Autostart on boot" in deploy/README.md.
termux-wake-lock

REPO_DIR="$HOME/jo-pirat-forum"
mkdir -p "$HOME/.jo-pirat-forum"

cd "$REPO_DIR" || exit 1
bash deploy/run_forum.sh >> "$HOME/.jo-pirat-forum/boot.log" 2>&1
