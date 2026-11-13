from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).absolute().parents[3]
TASK=Path(__file__).absolute().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(TASK/"source"))
from glb_reference import GLB
import probe_driver as D
RUN=ROOT/"output/sfm-static-appearance-probe-20261113-v2/runs/1794556016763092400-40301e3c9fe24f5a9c7441715f6268ba"
def identity(path):
    raw=path.read_bytes();info=path.stat()
    return {"path":str(path),"bytes":len(raw),"mtime_ns":info.st_mtime_ns,"sha256":hashlib.sha256(raw).hexdigest()}
manifest=RUN/"manifest.json"
meta=json.loads(manifest.read_bytes())
paths=[manifest,RUN/"actual-verification.json",RUN/"writer/result.json",RUN/"writer/execution.json",RUN/"writer/process.log"]
paths += [Path(c["input_glb"]) for c in meta["cases"]]
paths += [TASK/"source"/name for name in D.CODE]
start=[identity(p) for p in paths]
layouts=[]
for case in meta["cases"]:
    raw=Path(case["input_glb"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==case["glb_sha256"]
    proof=GLB(raw).layout_proof()
    layouts.append({"case":case["key"],"input_glb_sha256":case["glb_sha256"],"independent_layout":proof})
result=json.loads((RUN/"writer/result.json").read_bytes())
log=(RUN/"writer/process.log").read_text()
summary={"status":"FAILED_V2_WRITER_NOT_ACCEPTED", "run_folder_local_only":str(RUN),
         "checks":result["checks"],"failures":result["failures"],"app_cases":result["app_cases"],
         "failed_predicates":[line for line in log.splitlines() if line.startswith("FAIL ")],
         "raw_capture_cases":result["raw_captures"],
         "maximum_raw_world_error":max(p["symmetric_max_nearest_error"] for g in result["geometry"] for p in g["primitives"]),
         "old_raw_tolerance_unchanged":.0002,
         "retrospective_exact_verbose_count":D.classify_log(log,True)["classified_packed_vertex_verbose"]["count"],
         "retrospective_classification_does_not_accept_old_run":True,
         "root_reported_same_image_nitori_significant_samples":9,
         "required_same_image_significant_samples_exclusive":100,
         "threshold_unchanged":.02,
         "default_app_context":"New unshaded black background; as-supplied gloves-only component and coincident opaque black glow",
         "relative_path_attempt_local_only":"output/sfm-static-appearance-probe-20261113-v2/runs/1794555713647050600-5718442689ac488f931dce81ca1c3101",
         "v3_prepare_parse_gpu_app":"UNRUN","native_fidelity":"UNTESTED"}
finish=[identity(p) for p in paths]
assert start==finish
for name,value in (("ACTUAL12-LAYOUT-PROOF.json",{"scope":"Read-only actual derived GLB byte layouts, no model runtimes/preparation","cases":layouts,"all12_passed":len(layouts)==12,"inputs_and_source_unchanged":True,"protected_before":start,"protected_after":finish}), ("PRESERVED-V2-FAILURE.json",summary)):
    with (TASK/name).open("x",encoding="utf-8",newline="\n") as f:json.dump(value,f,indent=2);f.write("\n")
print(json.dumps({"actual_layouts":len(layouts),"unchanged":start==finish,"v2_failed_checks":summary["failures"],"v2_verbose_lines":summary["retrospective_exact_verbose_count"],"v3_engines":"UNRUN"}))
