from pathlib import Path
import hashlib,json,os,re,stat,subprocess,sys,time
sys.dont_write_bytecode=True
TASK=Path(__file__).absolute().parents[1]
ROOT=TASK.parents[1]
REVISION="4fa5efc175c0da53fcd61087e9685c89f4614db3"
GODOT=Path(r"C:\a\tools\Godot\Godot_v4.6-stable_win64.exe")
PYTHON=Path(r"C:\Program Files\Python313\python.exe")
PROTOCOL="experiments/local_wind_review/helper_draft_protocol_20261113/candidate/tools/wind_helper_preview.py"
def require(ok,message):
    if not ok:raise ValueError(message)
def no_reparse(path):
    path=Path(path).absolute()
    for p in(path,*path.parents):
        if p.exists():
            info=p.lstat();require(not stat.S_ISLNK(info.st_mode) and not info.st_file_attributes&0x400,"Reparse path refused")
    return path
def owned(path):
    path=no_reparse(path);require(".."not in path.parts and path.resolve().is_relative_to(TASK.resolve()) and path.resolve()!=TASK.resolve(),"Owned boundary")
    return path
def stamp(path):
    path=no_reparse(path);info=path.stat();require(path.is_file(),"Regular input missing")
    data=path.read_bytes();require((path.stat().st_size,path.stat().st_mtime_ns)==(info.st_size,info.st_mtime_ns),"Changed while read")
    return {"path":str(path),"bytes":len(data),"mtime_ns":info.st_mtime_ns,"sha256":hashlib.sha256(data).hexdigest()}
def publish(path,value):
    path=owned(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8",newline="\n")as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write("\n")
def git_blob(name):return subprocess.check_output(["git","show",REVISION+":"+name],cwd=ROOT)
def head():return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
def private_sources():
    receipt=TASK/"source-copy-v2.json";before=stamp(receipt)
    plan=json.loads(receipt.read_bytes());require(stamp(receipt)==before,"Frozen source-copy receipt changed")
    plan["_receipt_identity"]=before
    for row in plan["files"]:require(stamp(Path(row["path"]))==row,"Private frozen source changed")
    return plan

def own_sources():return {p.name:stamp(p)for p in sorted((TASK/"source").iterdir())if p.is_file()}
def preservation(protected,private,own_before):
    gates={}
    def inspect(name,func):
        try:gates[name]={"passed":bool(func())}
        except Exception as error:gates[name]={"passed":False,"error":type(error).__name__+": "+str(error)}
    for i,record in enumerate(protected):inspect("original_"+str(i),lambda record=record:stamp(Path(record["path"]))==record)
    if "_receipt_identity"in private:inspect("private_source_receipt",lambda:stamp(Path(private["_receipt_identity"]["path"]))==private["_receipt_identity"])
    for i,record in enumerate(private["files"]+private["runtime_executables"]):inspect("private_or_runtime_"+str(i),lambda record=record:stamp(Path(record["path"]))==record)
    inspect("own_source_membership",lambda:set(own_sources())==set(own_before))
    for name,record in own_before.items():inspect("own_"+name,lambda record=record:stamp(Path(record["path"]))==record)
    inspect("root_head",lambda:head()==REVISION)
    return {"passed":all(v["passed"]for v in gates.values()),"gates":gates,"own_source_before":own_before}
def finish(folder,outcome,protected,private,own_before):
    result=preservation(protected,private,own_before);outcome["preservation"]=result
    if not result["passed"]:outcome["status_before_preservation"]=outcome["status"];outcome["status"]="FAILED_PRESERVATION_RETAIN_ALL"
    publish(folder/"result.json",outcome)
    require(result["passed"],"Preservation failed; all receipts retained")
    return outcome

def freeze():
    require(head()==REVISION,"Root HEAD must remain reviewed4fa")
    project=owned(TASK/"isolated-v2");require(not project.exists(),"Fresh isolated source required");project.mkdir()
    pending=["src/scene3d.gd","src/model.gd","src/source_shape.gd","src/secondary_rig.gd"]
    seen=set();records=[]
    while pending:
        name=pending.pop()
        if name in seen:continue
        seen.add(name);raw=git_blob(name);target=project/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("xb")as stream:stream.write(raw)
        records.append(stamp(target))
        for match in re.finditer(rb'(?:preload|load)\("res://([^"\r\n]+)"\)',raw):
            child=match[1].decode();require(child.startswith("src/")and child.endswith(".gd"),"Unexpected source dependency: "+child);pending.append(child)
    aliases={"tools/secondary_helpers.py":"tools/secondary_helpers.py","tools/secondary_helpers_batch.py":"tools/secondary_helpers_batch.py",PROTOCOL:"tools/wind_helper_preview.py","tests/test_secondary_helpers.py":"tests/test_secondary_helpers.py"}
    for name,destination in aliases.items():
        raw=git_blob(name);target=project/destination;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("xb")as stream:stream.write(raw)
        records.append(stamp(target))
    project_file=project/"project.godot"
    project_file.write_text('config_version=5\n[application]\nconfig/name="HAS imported binding gate"\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="HAS Binding Gate '+str(time.time_ns())+'"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n',encoding="utf-8")
    records.append(stamp(project_file))
    target=project/"snapshot.gd";target.write_bytes((TASK/"source/snapshot.gd").read_bytes());records.append(stamp(target))
    require(head()==REVISION,"Root HEAD changed while copying")
    result={"source_revision":REVISION,"mode":"exact Git blobs in literal script dependency closure plus exact archived protocol, existing builders and authored fixture factory","project":str(project),"files":records,"runtime_executables":[stamp(GODOT),stamp(PYTHON)],"main_source_modified":False}
    publish(TASK/"source-copy-v2.json",result);return result
if __name__=="__main__":
    result=freeze();print(json.dumps({"copied_files":len(result["files"]),"revision":result["source_revision"],"no_runtime_started":True}))
