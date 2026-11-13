"""Headless actual-Godot synthetic imports; no retained/native input preparation."""
from pathlib import Path
import json,subprocess,sys,time,uuid
import support as S
import binding_gate as G
sys.path.insert(0,str(S.TASK/"isolated-v2/tools"))
import secondary_helpers as H
import wind_helper_preview as P

def shape_config(options):
    overrides={str(node):{str(i):float(w)for i,w in enumerate(weights)}for node,weights in options.get("morph_weights",{}).items()}
    return {"format":"studio_source_shape_2","enabled":options.get("source_morph_defaults",False),"overrides":overrides}

def captured(command,folder,timeout=90):
    try:return subprocess.run(command,cwd=S.TASK/"isolated-v2",capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as error:
        def text(value):return value.decode("utf-8",errors="replace")if isinstance(value,bytes)else value or""
        log=text(getattr(error,"stdout",None))+text(getattr(error,"stderr",None))
        with(folder/"process.log").open("x",encoding="utf-8")as stream:stream.write(log)
        S.publish(folder/"execution.json",{"status":"TIMEOUT_UNACCEPTED_RETAIN_ALL"if isinstance(error,subprocess.TimeoutExpired)else"LAUNCH_FAILED_RETAIN_ALL","error":type(error).__name__+": "+str(error),"partial_stdout_stderr_retained":True,"retry":False,"headless":True,"gpu":False})
        raise

def observe(path,shape,folder):
    folder=S.owned(folder);folder.mkdir(parents=True,exist_ok=False)
    plan={"input":str(Path(path).absolute()),"output":str(folder/"snapshot.json"),"sha256":S.stamp(path)["sha256"],"nonce":uuid.uuid4().hex,"shape":shape}
    manifest=folder/"import-plan.json";S.publish(manifest,plan)
    command=[str(S.GODOT),"--headless","--audio-driver","Dummy","--path",str(S.TASK/"isolated-v2"),"--log-file",str(folder/"engine.log"),"--script","res://snapshot.gd","--",str(manifest)]
    S.publish(folder/"command.json",command)
    completed=captured(command,folder)
    log=completed.stdout+completed.stderr
    with(folder/"process.log").open("x",encoding="utf-8")as stream:stream.write(log)
    forbidden=[v for v in("ERROR:","WARNING:","ObjectDB instances leaked","resources still in use","Orphan StringName:")if v in log]
    S.publish(folder/"execution.json",{"exit":completed.returncode,"forbidden_markers":forbidden,"headless":True,"gpu":False,"preservation_checked_independently_at_final":True})
    S.require(completed.returncode==0 and not forbidden,"Headless snapshot failed; all evidence retained: "+str(folder))
    snapshot=json.loads((folder/"snapshot.json").read_bytes())
    S.require(snapshot["nonce"]==plan["nonce"] and snapshot["glb_sha256"]==plan["sha256"] and not snapshot["problems"],"Snapshot identity/problems")
    expected=G.inventory(H.GLB(path).doc);G.validate_snapshot(snapshot,expected,plan["sha256"],shape)
    return snapshot

def main():
    S.require(S.head()==S.REVISION,"Exact reviewed root context required")
    proofs=sorted(S.TASK.glob("synthetic-cpu-*.json"));S.require(proofs,"Synthetic CPU proof required")
    cpu=json.loads(proofs[-1].read_bytes());S.require(cpu["failures"]==cpu["errors"]==0 and cpu["sources_preserved"],"Synthetic CPU controls must pass first")
    private=S.private_sources();own_before=S.own_sources()
    folder=S.owned(S.TASK/"synthetic-imports-v2"/str(time.time_ns()));folder.mkdir(parents=True)
    protected=[];results=[];error=None
    try:
        for row in cpu["synthetic_inputs"]:
            for key in("source","derived"):protected.append(S.stamp(Path(row[key])))
        for i,row in enumerate(cpu["synthetic_inputs"]):
            shape=shape_config(row["shape"])
            first=observe(Path(row["source"]),shape,folder/(str(i)+"-source"))
            second=observe(Path(row["derived"]),shape,folder/(str(i)+"-derived"))
            old,new=H.GLB(row["source"]),H.GLB(row["derived"])
            retained=P.retained_bindings(old,new)
            transfer=G.transfer(first,second,G.inventory(old.doc),G.inventory(new.doc),old.sha,new.sha,P,shape)
            S.publish(folder/(str(i)+"-transfer.json"),transfer)
            results.append({"shape":shape,"source_sha256":old.sha,"candidate_sha256":new.sha,"original_nodes":transfer["original_nodes"],"bound_nodes":transfer["original_bound_nodes"],"added_helper_nodes":transfer["added_helper_nodes"],"retained_glb_nodes":retained["original_nodes"]})
    except Exception as exc:error=type(exc).__name__+": "+str(exc)
    outcome={"status":"PASS"if error is None else"FAILED_RETAIN_ALL","cases":results,"error":error,"scope":"Headless actual imported binding snapshots of self-authored synthetic fixtures only","retained_actual_assets":"UNRUN","gpu":"UNRUN"}
    S.finish(folder,outcome,protected,private,own_before)
    S.require(error is None,error or"Synthetic import failed")
    print(json.dumps({"folder":str(folder),"synthetic_actual_import_pairs":len(results),"status":"PASS"}))
if __name__=="__main__":main()
