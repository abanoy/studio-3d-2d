from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).absolute().parents[3]
TASK=Path(__file__).absolute().parents[1]
BEFORE=ROOT/"output/encoder-existing-output-20261113/before"
def stamp(path):
    raw=path.read_bytes(); info=path.stat()
    return {"path":str(path),"bytes":len(raw),"mtime_ns":info.st_mtime_ns,"sha256":hashlib.sha256(raw).hexdigest()}
files=sorted(p for p in BEFORE.rglob("*") if p.is_file())
assert len(files)<=20
first=[stamp(p) for p in files]
ffmpeg=Path(r"C:\Program Files\ffmpeg\bin\ffmpeg.exe")
exe_before=stamp(ffmpeg)
strings=[s.decode("ascii") for s in re.findall(rb"[\x20-\x7e]{5,}",ffmpeg.read_bytes())]
versions=[s for s in strings if re.fullmatch(r"%s version N-[0-9]+-g[0-9a-f]+-[0-9]+",s)]
assert len(versions)==1
result={"scope":"Read-only preserved snapshot/executable bytes; no engine/FFmpeg/media runtime",
        "preserved_snapshot_files":first,"snapshot_files_unchanged":first==[stamp(p) for p in files],
        "ffmpeg_executable":exe_before,"ffmpeg_ascii_build_string":versions[0],
        "ffmpeg_executable_unchanged":exe_before==stamp(ffmpeg),
        "ascii_string_is_runtime_version_attestation":False}
path=TASK/"local-observations.json"
with path.open("x",encoding="utf-8",newline="\n") as stream:json.dump(result,stream,indent=2);stream.write("\n")
print(json.dumps({"path":str(path),"snapshot_files":len(files),"preserved":result["snapshot_files_unchanged"] and result["ffmpeg_executable_unchanged"],"ffmpeg_build_string":versions[0]}))
