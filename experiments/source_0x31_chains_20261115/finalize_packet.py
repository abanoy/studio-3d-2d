"""Fresh compact index; no app/parser/process/Git activity."""
from pathlib import Path
import ast
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name,value):
    with (HERE/name).open("x",encoding="utf-8",newline="\n") as f:json.dump(value,f,indent=2,allow_nan=False);f.write("\n")


def main():
    result=json.loads((HERE/"CPU_RESULT_two_pairs.json").read_bytes())
    assert result["checks"]==3681 and result["failures"]==0 and result["completed_actor_steps"]==1424 and result["completed_rule_evaluations"]==3088
    for path in HERE.glob("*.py"):ast.parse(path.read_text(encoding="utf-8-sig"))
    gd=[]
    for path in sorted(HERE.glob("*.gd")):
        source=path.read_text(encoding="utf-8-sig")
        assert not re.search(r"(?m)^\s*(class_name\b|@tool\b)",source)
        assert source.splitlines()[0].startswith("extends ")
        gd.append({"path":path.name,"sha256":sha(path),"engine_parsed":False,"engine_run":False})
    assert not (HERE/"project.godot").exists()
    lease=json.loads((HERE/"ROOT_LEASE_TEMPLATE.json").read_bytes())
    for name in ("chain_solver","model_adapter","chain_capture","chain_harness"):
        path=HERE/(name+".gd")
        lease["files"][name]={"path":str(path),"sha256":sha(path)}
    save("ROOT_LEASE_READY_TEMPLATE.json",lease)
    readpins=json.loads((HERE/"READ_SOURCE_HASHES.json").read_bytes())["files"]
    read_drift=[pin["path"] for pin in readpins if sha(ROOT/pin["path"])!=pin["sha256"]]
    sourcepins=json.loads((HERE/"SOURCE_LOCK.json").read_bytes())["files"]
    source_drift=[pin["path"] for pin in sourcepins if sha(ROOT/pin["path"])!=pin["sha256"]]
    save("STATIC_FINAL.json",{"status":"SOURCE_PREPARED_CPU_SYNTHETIC_PASSED_NEW_GDSCRIPT_UNPARSED_UNRUN","root_declared_HEAD_context":"9de4e6c","new_GDScript":gd,
         "python_AST_only":True,"CPU_result":{"file":"CPU_RESULT_two_pairs.json","sha256":sha(HERE/"CPU_RESULT_two_pairs.json"),"checks":3681,"failures":0,"completed_actor_steps":1424,"rule_evaluations":3088},
         "source_read_drift_at_handoff":read_drift,"full_source_snapshot_drift_at_handoff":source_drift,
         "concurrency_note":"Root/peer own production integration. Root must review/resnapshot any production drift before granting a fresh source-matched engine lease.",
         "actual_engine_parser_process_inspection_or_Git_invoked":False,"native_arrays_or_SDK_source_copied":False,"production_source_modified_by_this_child":False,
         "actual_native_two_pair_dynamics":"UNRUN_NOT_QUALIFIED","normal_fidelity_2e5_gate":"HISTORICAL_FAILED_UNCHANGED",
         "known_limits":["Source caller goal-policy parity unavailable in local SDK packet","Native25 stays authored/unsimulated; not all49 native rules","Float32 adapter requires actual new-chain validation","No body/fan/Record/seek/HAS/GPU/artist acceptance"],
         "root_next_step":"Source review; close existing runtime lease; review source drift; stage exact packet; fresh locked synthetic headless math attempt, then bounded actual pair attempt. Preserve every first failure."})
    files=[{"path":p.name,"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(HERE.iterdir()) if p.is_file() and p.name!="INDEX.json"]
    save("INDEX.json",{"format":"has_source_0x31_two_chain_source_preparation_1","status":"CPU_SYNTHETIC_ONLY_NEW_GDSCRIPT_UNPARSED_UNRUN","files":files,"private_native_geometry_or_oracles_in_packet":False})
    print(json.dumps({"index_sha256":sha(HERE/"INDEX.json"),"ready_lease_sha256":sha(HERE/"ROOT_LEASE_READY_TEMPLATE.json"),"GDScript_files":len(gd),"source_read_drift":read_drift,"full_source_drift":source_drift,"bytes":sum(p["bytes"] for p in files)}))


if __name__=="__main__":main()
