"""Publish only compact source and actual metadata, preserving earlier attempts."""
from pathlib import Path
import gzip, hashlib, json, shutil, subprocess

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
PACK=BASE/"review-ready"
PACK.mkdir(exist_ok=False)
records=[]
def digest(data):return hashlib.sha256(data).hexdigest()
def put(source,name):
    raw=source.read_bytes();name=Path(name)
    encoded=gzip.compress(raw,mtime=0) if len(raw)>65536 else raw
    codec="gzip" if len(raw)>65536 else "identity"
    if codec=="gzip":name=Path(str(name)+".gz")
    path=PACK/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(encoded)
    records.append({"path":name.as_posix(),"codec":codec,"bytes":len(encoded),"sha256":digest(encoded),"raw_bytes":len(raw),"raw_sha256":digest(raw),"original":str(source)})

for file in ("src/import_placement.gd","tests/import_placement_smoke.gd","tests/verify_import_placement.py"):
    put(ROOT/file,"source/"+file)
for file in ("execute.py","build_packet.py"):
    put(BASE/file,"coordinator/"+file)
attempts={
 "headless-1794614880788286000":"earlier_headless_before_failure_reporting_refinement",
 "private-1794614887307076000":"restricted_context_pre_child_failure",
 "private-1794614922339824800":"final_host_private_pass",
}
for folder,label in attempts.items():
    attempt=BASE/folder
    for source in sorted(attempt.rglob("*")):
        if source.is_file() and source.suffix in (".json",".log"):
            put(source,"actual/"+label+"/"+source.relative_to(attempt).as_posix())
for receipt in (ROOT/"output/private-desktop").glob("import_placement_smoke_*.json"):
    value=json.loads(receipt.read_bytes())
    if value.get("desktop")=="HAS_Test_b69c358f795b4750b5981a41f949fa09":
        assert value["exit"]==2 and "Create private test desktop" in value["error"] and "child_pid" not in value
        put(receipt,"actual/restricted_context_pre_child_failure/denied-private-desktop.json")

diff=subprocess.check_output(["git","diff","--","src/import_placement.gd","tests/import_placement_smoke.gd","tests/verify_import_placement.py"],cwd=ROOT)
(PACK/"candidate.patch").write_bytes(diff)
final=json.loads((BASE/"private-1794614922339824800/result.json").read_bytes())
assert final["passed"] and final["source_unchanged"] and final["report"]["checks"]==43
summary={"format":"has_import_placement_inset_actual_1","context":"uncommitted working source on 1caeb44b12e9ebf2db944c769810010975f5abaa; not a committed full-suite pass","source_files":981,"final_private_checks":43,"final_private_failures":0,"bounds_checks":20,"original_checks":23,"prepared_native_map_checks_in_original":3,"movie":final["report"]["video"],"source_preserved":True,"engine_error_leak_markers":[],"private_child_pid":6304,"private_exit":0,"private_job_desktop_closed":True,"pre_child_failure":{"exit":2,"reason":"restricted context CreateDesktop access denied; no child created; first verifier masked this with missing engine.log","preserved":True},"scope":"Per-axis non-inverting AABB clearance for actor and wall candidate rejection; normal support/view/Undo/HAS/movie regressions retained. Does not establish native Source shader/jiggle fidelity or resolve the pending native app matrix.","payloads":"source and metadata only; no original native inputs, media, GLB/HAS, or runtime copies","records":records}
(PACK/"SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
(PACK/"README.md").write_text("Thin imported props retain a centered, nonnegative clearance box on each axis. Both actor and wall overlap paths use the helper. Exhausted axes collapse without expanding. Zero-volume bounds inside an occupied volume remain intersections.\n\nFinal actual check: headless20/0 followed by private43/0, clean engine logs, exact981-file source preservation, private child6304 exit0 with Job and desktop closed. Original placement coverage includes the available prepared GMod map3 checks and48-frame1080p24 H264 movie.\n\nEarlier standalone headless20 passed before a verifier-only failure-reporting refinement. The first private attempt was blocked before child creation by CreateDesktop access denied in the restricted context; its receipt and the missing-engine-log exception are preserved separately. The approved host retry passed.\n\nThis packet is an uncommitted working-main checkpoint. Native app Core14 retry and the later full canonical run remain separate. The pending native integration and broad fidelity claims are not inferred here.\n\nFiles above64KiB use deterministic gzip with original raw SHA256 and size in SUMMARY.json. INDEX.json covers every other packet file.\n",encoding="utf-8")
index={"format":"has_metadata_source_packet_index_1","files":[{"path":p.relative_to(PACK).as_posix(),"bytes":p.stat().st_size,"sha256":digest(p.read_bytes())} for p in sorted(PACK.rglob("*")) if p.is_file()]}
(PACK/"INDEX.json").write_text(json.dumps(index,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"folder":str(PACK),"files":len(index["files"]),"bytes":sum(p["bytes"] for p in index["files"]),"index_sha256":digest((PACK/"INDEX.json").read_bytes())},indent=2))
