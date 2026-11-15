"""Owned metadata coordinator for the leased thin-bounds placement checks."""
from pathlib import Path
import ast, datetime, hashlib, json, os, subprocess, sys, time

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
def write(path,value):
    path.write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8")
def snapshot():
    paths=[p for part in ("src","tests","tools","examples","data") for p in (ROOT/part).rglob("*") if p.is_file() and p.suffix!=".pyc" and "__pycache__" not in p.parts]
    paths += [ROOT/name for name in ("run.py","main.tscn","project.godot")]
    return {str(p.relative_to(ROOT)).replace("\\","/"):{"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size} for p in sorted(paths)}
mode=sys.argv[1]
assert mode in ("headless","private")
attempt=OUT/(mode+"-"+str(time.time_ns()));attempt.mkdir(parents=True,exist_ok=False)
before=snapshot();write(attempt/"source-before.json",before)
ast.parse((ROOT/"tests/verify_import_placement.py").read_text(encoding="utf-8"))
os.environ.update(HYBRID_GODOT=r"C:\a\tools\Godot\Godot_v4.6-stable_win64.exe",HYBRID_PYTHON=r"C:\Program Files\Python313\python.exe",HYBRID_FFMPEG=r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",PYTHONDONTWRITEBYTECODE="1")
sys.path.insert(0,str(ROOT))
from run import command
if mode=="headless":
    args=command("tests/import_placement_smoke.gd",headless=True,extra=["--log-file",str(attempt/"engine.log"),"--","--bounds-only"])
    timeout=35
else:
    args=[sys.executable,"-B",str(ROOT/"tests/verify_import_placement.py"),"--output",str(attempt/"wrapper")]
    timeout=180
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
write(attempt/"invocation.json",{"mode":mode,"command":args,"start":start,"timeout":timeout,"source_scope":"src/tests/tools/examples/data and run.py/main.tscn/project.godot; docs excluded"})
result={"mode":mode,"passed":False,"start":start}
try:
    completed=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
    console=completed.stdout+completed.stderr
    (attempt/"console.log").write_text(console,encoding="utf-8")
    result["exit"]=completed.returncode
    logs=[attempt/"engine.log"] if mode=="headless" else list((attempt/"wrapper").glob("*engine.log"))
    bad=("ERROR:","SCRIPT ERROR","SHADER ERROR","FAIL ","ObjectDB instances leaked","another exclusive child")
    result["bad_markers"]={str(p.relative_to(attempt)):[s for s in bad if s in p.read_text(encoding="utf-8",errors="replace")] for p in logs}
    result["console_bad_markers"]=[s for s in bad if s in console]
    assert completed.returncode==0,console
    assert not result["console_bad_markers"] and all(not values for values in result["bad_markers"].values())
    if mode=="headless":
        report=json.loads(next(line.removeprefix("IMPORT_PLACEMENT_BOUNDS ") for line in console.splitlines() if line.startswith("IMPORT_PLACEMENT_BOUNDS ")))
        assert report=={"checks":20,"failures":0,"thin_planar_actual_plan":True},report
    else:
        report=json.loads((attempt/"wrapper/verification.json").read_text(encoding="utf-8"))
        assert report["failures"]==0 and report["headless_bounds"]["checks"]==20 and report["bounds"]["checks"]==20
    result["report"]=report
    result["passed"]=True
except BaseException as error:
    result["exception"]={"type":type(error).__name__,"message":str(error)}
    raise
finally:
    after=snapshot();write(attempt/"source-after.json",after)
    result.update(finish=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_unchanged=before==after,source_files=len(before))
    result["passed"]=result["passed"] and result["source_unchanged"]
    write(attempt/"result.json",result)
    print(json.dumps({"folder":str(attempt),"passed":result["passed"],"source_unchanged":result["source_unchanged"],"source_files":len(before),"exit":result.get("exit"),"exception":result.get("exception")},indent=2))
assert result["passed"]
