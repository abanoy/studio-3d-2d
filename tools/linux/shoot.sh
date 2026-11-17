#!/bin/bash
# Usage (from the repo root): GODOT=/path/to/Godot_v4.6-stable_linux.x86_64 tools/linux/shoot.sh <outdir>
# Screenshots Simple Draw / Camera / Pose and Advanced Draw at 1440x900 under xvfb (draw.png, camera.png,
# pose.png, advanced.png + shoot.log). Never touches prefs: user:// goes to a temp dir deleted afterwards,
# display.cfg and recovery go to output/neon-shoot/ (git-ignored). SHOOT_MODEL=0 skips the 2-bone fixture model.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$(mkdir -p "${1:?usage: shoot.sh <outdir>}" && cd "$1" && pwd)
P=$(pwd)
[ -f "$P/project.godot" ] || { echo "run from the repo root"; exit 2; }
GODOT=${GODOT:?set GODOT to a Godot 4.6 Linux binary}
mkdir -p "$P/output" "$P/examples"   # --demo-room writes res://examples/room.glb (git-ignored? see git status)
# Isolate user:// so the owner's / tests' display.cfg, recent projects etc. are neither read nor written.
ISO=$(mktemp -d "${TMPDIR:-/tmp}/neonshoot.XXXXXX")
export XDG_DATA_HOME="$ISO/data" XDG_CONFIG_HOME="$ISO/config" XDG_CACHE_HOME="$ISO/cache"
export HYBRID_PYTHON="${HYBRID_PYTHON:-$(command -v python3)}"
LOG="$OUT/shoot.log"
timeout 200 xvfb-run -a -s "-screen 0 1600x1000x24" "$GODOT" --rendering-driver opengl3 --path "$P" \
  --resolution 1440x900 --position 0,0 --log-file "$ISO/engine.log" \
  --script "$HERE/shoot.gd" -- --demo-room --shoot-out "$OUT" >"$LOG" 2>&1
RC=$?
grep -E "SHOT|SHOOT|SCRIPT ERROR|ERROR:" "$LOG" | grep -v "audio_driver_alsa\|ERR_CANT_OPEN" | head -40
rm -rf "$ISO"
ls -1 "$OUT"/*.png 2>/dev/null
grep -q SHOOT_DONE "$LOG" && echo "shoot OK (exit $RC)" || { echo "shoot FAILED (exit $RC) log=$LOG"; exit 1; }
