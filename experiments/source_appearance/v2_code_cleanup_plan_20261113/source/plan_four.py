"""Read-only four-root v2 code cleanup planner. This has no delete/move/restore mode."""
from pathlib import Path, PureWindowsPath
import hashlib,json,os,stat,subprocess,time
ROOT=Path(__file__).absolute().parents[3]
TASK=Path(__file__).absolute().parents[1]
REVISION="e9cc7cfb20266b4863bde134bcb30457547a343d"
RUN_IDS=("1794555713647050600-5718442689ac488f931dce81ca1c3101","1794556016763092400-40301e3c9fe24f5a9c7441715f6268ba")
V2=ROOT/"output/sfm-static-appearance-probe-20261113-v2"
CODE_SUFFIXES={".gd",".gdshader",".py",".pyw",".tscn",".godot",".cfg",".toml",".ini",".bat",".ps1",".sh",".yml",".yaml",".txt"}
CODE_NAMES={"LICENSE","COPYING",".gitignore",".gitattributes"}
PRESERVE_PARTS={"output",".godot",".git","__pycache__","generated","cache","caches","recovery","private-desktop","has-cache","reference-cache","profiles","userdata","user-data"}

def require(ok,message):
    if not ok:raise ValueError(message)

def no_reparse(path):
    path=Path(path).absolute()
    for current in (path,*path.parents):
        require(current.exists(),"Missing path in fixed plan: "+str(current))
        info=current.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not info.st_file_attributes&0x400,"Reparse path refused: "+str(current))
    return path

def identity(path):
    path=no_reparse(path);info=path.stat();require(stat.S_ISREG(info.st_mode),"Not a regular file: "+str(path))
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):digest.update(block)
    require(path.stat().st_size==info.st_size and path.stat().st_mtime_ns==info.st_mtime_ns,"File changed while reading: "+str(path))
    return {"path":str(path),"bytes":info.st_size,"mtime_ns":info.st_mtime_ns,"sha256":digest.hexdigest()}

def read_json(path):
    before=identity(path);value=json.loads(path.read_bytes());require(identity(path)==before,"Metadata changed while reading")
    return value,before

def enumerate_files(project):
    no_reparse(project);require(project.is_dir(),"Missing fixed source root")
    files=[];directories=[]
    for base,dirs,names in os.walk(project,followlinks=False):
        no_reparse(base)
        for name in dirs:
            path=no_reparse(Path(base)/name);require(path.resolve().is_relative_to(project.resolve()),"Escaping directory")
            directories.append(str(path))
        for name in names:
            path=no_reparse(Path(base)/name);require(path.resolve().is_relative_to(project.resolve()),"Escaping file")
            files.append(path)
    require(len(files)==len({str(p.relative_to(project)).casefold() for p in files}),"Windows case alias")
    return sorted(files),sorted(directories)

def git_tree():
    raw=subprocess.check_output(["git","ls-tree","-rz","--full-tree",REVISION],cwd=ROOT)
    result={}
    for row in raw.split(b"\0"):
        if not row:continue
        metadata,name=row.split(b"\t",1);mode,kind,oid=metadata.split();name=name.decode()
        result[name]={"mode":mode.decode(),"kind":kind.decode(),"oid":oid.decode()}
    require(len(result)==len({n.casefold() for n in result}),"Git case-colliding names")
    return result

def blob_identities(entries):
    oids=sorted({v["oid"] for v in entries.values() if v["kind"]=="blob" and v["mode"] in ("100644","100755")})
    raw=subprocess.check_output(["git","cat-file","--batch"],input="".join(oid+"\n" for oid in oids).encode(),cwd=ROOT)
    offset=0;result={}
    for oid in oids:
        end=raw.index(b"\n",offset);actual,kind,size=raw[offset:end].decode().split();size=int(size)
        require(actual==oid and kind=="blob","Unexpected Git blob response")
        begin=end+1;data=raw[begin:begin+size]
        require(len(data)==size and raw[begin+size:begin+size+1]==b"\n","Truncated Git blob")
        result[oid]={"bytes":size,"sha256":hashlib.sha256(data).hexdigest()};offset=begin+size+1
    require(offset==len(raw),"Trailing Git batch bytes")
    return result

def preservation_reason(relative):
    if any(part.casefold() in PRESERVE_PARTS for part in relative.parts):return "always_retained_runtime_generated_or_private_path"
    if relative.name not in CODE_NAMES and relative.suffix.casefold() not in CODE_SUFFIXES:return "conservative_non_code_asset_media_metadata_or_other_payload"
    return None

def main():
    require(TASK==ROOT/"output/sfm-v2-code-cleanup-plan-20261113","Unexpected plan output root")
    no_reparse(TASK)
    require(subprocess.check_output(["git","rev-parse",REVISION+"^{commit}"],cwd=ROOT,text=True).strip()==REVISION,"Source commit missing")
    tree=git_tree()
    # Read only potentially eligible code blobs, never reconstruct files.
    entries={name:value for name,value in tree.items() if not preservation_reason(Path(name))}
    blobs=blob_identities(entries)
    before_head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    results=[];protected=[]
    for run_id in RUN_IDS:
        run=no_reparse(V2/"runs"/run_id)
        manifest,manifest_id=read_json(run/"manifest.json");protected.append(manifest_id)
        require(manifest["root_revision"]==REVISION and manifest["source_mode"]=="exact_git_revision" and manifest["copied_source_is_exact_git_revision"] is True,"Unexpected historical source context")
        for mode in ("writer","reader"):
            project=no_reparse(run/(mode+"-source"))
            require(project.resolve().is_relative_to((V2/"runs").resolve()) and Path(manifest["projects"][mode]["path"])==project,"Fixed root/manifest mismatch")
            files,directories=enumerate_files(project);listed=manifest["projects"][mode]["files"]
            candidates=[];retained=[]
            for path in files:
                relative=path.relative_to(project);name=relative.as_posix();record=identity(path)
                record.update({"relative_path":name,"project":str(project)})
                reason=preservation_reason(relative)
                if reason is None and name not in listed:reason="unlisted_in_original_source_manifest"
                if reason is None and record["sha256"]!=listed[name]:reason="source_manifest_hash_differs"
                if reason is None and (name not in tree or tree[name]["kind"]!="blob" or tree[name]["mode"] not in ("100644","100755")):reason="not_an_ordinary_exact_commit_blob"
                if reason is None:
                    blob=blobs[tree[name]["oid"]]
                    if (record["bytes"],record["sha256"])!=(blob["bytes"],blob["sha256"]):reason="exact_commit_blob_differs"
                if reason is not None:
                    record["retain_reason"]=reason;retained.append(record)
                else:
                    record.update({"git_commit":REVISION,"git_path":name,"git_oid":tree[name]["oid"],"git_mode":tree[name]["mode"],"original_manifest_sha256":listed[name],"reconstruction":"git cat-file blob "+tree[name]["oid"]+"; write raw bytes only to a fresh owned reconstruction destination; verify recorded SHA256/length"})
                    candidates.append(record)
            require(len(candidates)+len(retained)==len(files),"Unclassified file")
            # Historical job receipts are evidence only; live process use is NOT assessed here.
            command_path=run/mode/"command.json"
            closure={"status":"NO_RETAINED_PHASE_COMMAND_OR_JOB_RECEIPT","not_a_closed_job_attestation":True,"root_requires_fresh_independent_process_use_revalidation":True}
            if command_path.exists():
                command,command_id=read_json(command_path);protected.append(command_id)
                require(command.count("--receipt")==1,"Ambiguous private receipt argument")
                receipt_path=no_reparse(Path(command[command.index("--receipt")+1]))
                require(receipt_path.resolve().is_relative_to((project/"output/private-desktop").resolve()),"Receipt outside expected preserved output")
                receipt,receipt_id=read_json(receipt_path);protected.append(receipt_id)
                require(receipt.get("job_closed") is True and receipt.get("desktop_closed") is True and receipt.get("foreground_child_observed") is False,"Historical private closure is not cleanly attested")
                closure={"status":"HISTORICAL_PRIVATE_JOB_AND_DESKTOP_CLOSED","receipt_identity":receipt_id,"receipt":receipt,"command_identity":command_id,"source_root":str(project),"root_requires_fresh_independent_process_use_revalidation":True}
            results.append({"run_id":run_id,"mode":mode,"source_root":str(project),"original_manifest":manifest_id,"historical_closure":closure,
                            "whole_tree_nonreparse_contained":True,"files_observed":len(files),"directories_observed":len(directories),"directories_never_candidates":directories,
                            "candidate_files":candidates,"candidate_bytes":sum(r["bytes"] for r in candidates),"retained_files":retained,"retained_bytes":sum(r["bytes"] for r in retained)})
    # Full observed identities/membership are checked a second time, with zero source writes.
    for project in results:
        paths,directories=enumerate_files(Path(project["source_root"]))
        all_records=project["candidate_files"]+project["retained_files"]
        require({str(p) for p in paths}=={r["path"] for r in all_records} and directories==project["directories_never_candidates"],"Membership changed during planning")
        for record in all_records:require(identity(Path(record["path"]))=={key:record[key] for key in ("path","bytes","mtime_ns","sha256")},"Source/generated/private file changed during planning")
    for record in protected:require(identity(Path(record["path"]))==record,"Historical receipt changed during planning")
    after_head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip();require(before_head==after_head,"Root HEAD changed during planning")
    plan={"format":"has_four_v2_git_code_cleanup_plan_1","status":"PLAN_ONLY_NO_CLEANUP_AUTHORIZED_OR_PERFORMED","historical_source_commit":REVISION,"root_head_before":before_head,"root_head_after":after_head,
          "exact_source_roots":len(results),"whole_paths_nonreparse_contained":True,"source_private_generated_all_observed_files_unchanged":True,
          "candidate_files":sum(len(r["candidate_files"]) for r in results),"candidate_bytes":sum(r["candidate_bytes"] for r in results),
          "retained_files":sum(len(r["retained_files"]) for r in results),"retained_bytes":sum(r["retained_bytes"] for r in results),
          "candidate_policy":{"suffixes":sorted(CODE_SUFFIXES),"exact_names":sorted(CODE_NAMES),"always_retained_parts":sorted(PRESERVE_PARTS),"not_all_git_reconstructible_files_are_candidates":True},
          "preconditions_before_any_cleanup":["Publish and remotely verify this exact plan/source and historical Git blobs","Root independently revalidates no process is using any of the four source roots","Revalidate every path, membership, file hash/length/stamp and Git blob against this frozen plan","Use exact candidate paths only; never directory deletion or recursive/glob selection","Preserve every retained/unlisted/new file and all directories; no retry that broadens scope"],
          "protected_evidence":protected,"projects":results,"deletion_move_kill_git_mutation":False,"v3_or_other_source_roots_touched":False}
    target=TASK/"PLAN.json"
    with target.open("x",encoding="utf-8",newline="\n") as stream:json.dump(plan,stream,indent=2);stream.write("\n")
    print(json.dumps({"plan":str(target),"sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"candidate_files":plan["candidate_files"],"candidate_bytes":plan["candidate_bytes"],"retained_files":plan["retained_files"],"retained_bytes":plan["retained_bytes"],"closed_historical_jobs":sum(r["historical_closure"]["status"]=="HISTORICAL_PRIVATE_JOB_AND_DESKTOP_CLOSED" for r in results),"reader_no_phase_receipt":sum(r["historical_closure"]["status"]=="NO_RETAINED_PHASE_COMMAND_OR_JOB_RECEIPT" for r in results)}))

if __name__=="__main__":main()
