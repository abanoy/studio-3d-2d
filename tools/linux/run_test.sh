#!/bin/bash
# Usage: run.sh <projectdir> <test>   (Linux mirror of tests/verify.py + run.py command())
set -u
P=$(realpath "$1"); T=$2
export HYBRID_PYTHON="${HYBRID_PYTHON:-$(command -v python3)}"  # main's tools/*.py (recovery_processes, save workers) run on Linux; liveness_shim.sh kept only for old snapshots
GODOT=${GODOT:?set GODOT to a Godot 4.6 Linux binary}
mkdir -p "$P/output/fixtures" "$P/examples"  # snapshot lacks examples/; --demo-room writes res://examples/room.glb
python3 - "$P/output/fixtures" <<'PY'
import array,math,struct,sys,wave,pathlib
f=pathlib.Path(sys.argv[1])
raw=array.array("h",(int(16000*math.sin(2*math.pi*1000*n/44100)) for n in range(22050)))
with wave.open(str(f/"voice — тест.wav"),"wb") as w:
    w.setparams((1,2,44100,0,"NONE","not compressed")); w.writeframes(raw.tobytes())
p=b"WAVEfmt "+struct.pack("<IHHIIHH",16,3,1,44100,176400,4,32)+b"data"+struct.pack("<I",400)+bytes(400)
(f/"float.wav").write_bytes(b"RIFF"+struct.pack("<I",len(p))+p)
PY
[ "$T" = recovery ] && { "$0" "$P" recovery_write | tail -1; }  # verify.py order: writer first
case $T in
  ui) S=""; X="-- --ui-smoke --demo-room"; M="UI_SMOKE ";;
  editor) S=""; X="-- --smoke --demo-room"; M='"failures":0';;
  recovery) S=""; X="-- --recovery-smoke --demo-room"; M="RECOVERY_SMOKE ";;
  recovery_write) S=""; X="-- --recovery-smoke --recovery-write --demo-room"; M="RECOVERY_WRITE failures=0";;
  pose) S=""; X="-- --pose-smoke --demo-room"; M="POSE_SMOKE ";;
  new_scene) S=tests/new_scene_smoke.gd; X="--"; M="NEW_SCENE_SMOKE ";;
  world_selection) S=tests/world_selection_smoke.gd; X="--"; M="WORLD_SELECTION_SMOKE ";;
  autokey) S=tests/autokey_smoke.gd; X="--"; M="AUTOKEY_SMOKE ";;
  object_timing) S=tests/object_timing_smoke.gd; X="--"; M="OBJECT_TIMING ";;
  *) echo "unknown test $T"; exit 2;;
esac
LOG="$P/output/$T-stdout.log"
cd "$P"
timeout 290 xvfb-run -a -s "-screen 0 1920x1080x24" "$GODOT" --rendering-driver opengl3 --path "$P" \
  --log-file "$P/output/$T-engine.log" ${S:+--script $S} $X >"$LOG" 2>&1
RC=$?
grep -E "PASS|FAIL|SCRIPT ERROR|ERROR:|$M" "$LOG" | head -80
ok=1; [ $RC -eq 0 ] || ok=0; grep -q "$M" "$LOG" || ok=0
grep -qE "SCRIPT ERROR|SHADER ERROR|Shader compilation failed|FAIL |ObjectDB instances leaked" "$LOG" && ok=0
[ "$T" != editor ] && [ "$T" != recovery_write ] && ! grep -q '"failures":0' "$LOG" && ok=0
[ $ok = 1 ] && echo "RESULT PASS $T (exit $RC)" || echo "RESULT FAIL $T (exit $RC) log=$LOG"
