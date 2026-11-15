"""Read-only audit and compact metadata/source publication of completed native app runs.

No Godot/Blender/runtime process is launched and no model/media payload is copied.
"""
from pathlib import Path
import array, datetime, gzip, hashlib, json, math, sys, wave

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
REVISION="8d4fde001258f501602bd94bd80d925683062f15"
BAD=("ERROR:","FAIL ","SCRIPT ERROR","SHADER ERROR","ObjectDB instances leaked","unclaimed string names","Pages in use exist at exit","resources still in use","Traceback (most recent call last)")
phase,run_arg,launch_arg,wanted_writer,wanted_readers,wanted_sha=sys.argv[1:]
RUN=Path(run_arg).resolve(strict=True);LAUNCH=Path(launch_arg).resolve(strict=True)
wanted_writer=int(wanted_writer);wanted_readers=int(wanted_readers)
DEST=BASE/phase;DEST.mkdir(exist_ok=False)
failures=[];checks=[];records=[]
def load(path):return json.loads(Path(path).read_bytes())
def sha(path):
    with Path(path).open("rb") as stream:return hashlib.file_digest(stream,"sha256").hexdigest()
def check(value,label):
    checks.append({"check":label,"passed":bool(value)})
    if not value:failures.append(label)
def same(a,b):return Path(a).resolve()==Path(b).resolve()
def relative(path,root):return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
def put(source,name):
    source=Path(source);raw=source.read_bytes();encoded=gzip.compress(raw,mtime=0) if len(raw)>65536 else raw
    codec="gzip" if len(raw)>65536 else "identity";name=Path(str(name)+(".gz" if codec=="gzip" else ""))
    path=DEST/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(encoded)
    records.append({"path":name.as_posix(),"codec":codec,"bytes":len(encoded),"sha256":hashlib.sha256(encoded).hexdigest(),"raw_bytes":len(raw),"raw_sha256":hashlib.sha256(raw).hexdigest(),"original":str(source)})

value=load(RUN/"verification.json");before=load(RUN/"source-before.json");after=load(RUN/"source-after.json")
snapshot=load(RUN/"snapshot-source-before.json");preserved=load(RUN/"preservation-after.json")
studio=RUN/"Studio";snapshot_sha=sha(RUN/"snapshot-source-before.json")
check(sha(RUN/"verification.json")==wanted_sha,"aggregate raw SHA256 matches root terminal notification")
check(value["passed"] is True and value["errors"]==[] and value["source_context"]=="main_working_source_snapshot","aggregate terminal pass/errors/source context")
check(before==after==value["source_before"]==preserved["sources"] and before["revision"]==REVISION,"full exact current-main before/after and HEAD join")
check(len(value["preservation"])==8 and all(v is True for v in value["preservation"].values()),"all eight preservation gates")
check({k:v for k,v in snapshot.items() if k!="override.cfg"}=={k:v["sha256"] for k,v in before["files"].items()},"snapshot source map matches every recorded main file")
snapshot_mismatches=[name for name,digest in snapshot.items() if not (studio/name).is_file() or sha(studio/name)!=digest]
check(not snapshot_mismatches,"every actual snapshot source file including isolated profile still matches its manifest")
runtime=load(RUN/"runtimes-before.json");environment=load(RUN/"runtime-environment.json")
check(runtime==preserved["runtimes"] and same(runtime["sourceio_root"],environment["HYBRID_SOURCEIO"]),"approved runtime before/after maps and declared SourceIO root join")
originals=load(RUN/"originals-before.json");owned_stamps=load(RUN/"owned-inputs-before.json")
check(originals==preserved["originals"]==value["original_families"],"original family before/after maps join")
case_plan=load(RUN/"owned-cases.json")["cases"];original_plan=load(RUN/"input-manifest.json")["cases"]
admission=load(RUN/"manifest-admission.json");writer=value["writer"];cases=writer["result"]["cases"]
check(len(case_plan)==len(original_plan)==len(cases) and [x["name"] for x in case_plan]==[x["name"] for x in cases],"all admitted names and actual writer cases join in order")
check(writer["result"]["checks"]==wanted_writer==admission["writer_expected_checks"] and writer["result"]["failures"]==0,"exact writer count from admitted case formula")
check(len(value["readers"])==wanted_readers,"exact fresh reader process count")

receipt_rows=[];job_rows=[];frame_rows=[];case_rows=[];legacy_default_warning=[]
physical_receipts={str(p.resolve()):p for p in (studio/"output/private-desktop").glob("*.json")}
aggregate_receipts={str(Path(x["path"]).resolve()):x for x in value["receipts"]}
check(set(physical_receipts)==set(aggregate_receipts) and len(physical_receipts)==wanted_readers+1,"all physical private receipts exactly match aggregate inventory")
for path_key,path in sorted(physical_receipts.items()):
    rec=load(path);entry=aggregate_receipts[path_key]
    clean=(rec.get("format")=="studio_private_desktop_1" and rec.get("exit")==0 and rec.get("private_window_seen") is True and rec.get("child_desktop_confirmed") is True and rec.get("foreground_child_observed") is False and rec.get("desktop_switch_requested") is False and rec.get("job_closed") is True and rec.get("desktop_closed") is True and not rec.get("error") and not rec.get("monitor_error"))
    check(clean and rec==entry["receipt"] and sha(path)==entry["sha256"],"raw private receipt hash/closure: "+path.name)
    receipt_rows.append({"path":str(path),"sha256":sha(path),**rec})
    put(path,"actual/receipts/"+path.name)

for index,record in enumerate([writer,*value["readers"]]):
    folder=RUN/"writer" if index==0 else RUN/"readers"/f"{index:02d}"
    job=load(folder/"job.json");actual=load(folder/"result.json");raw_record=load(folder/"process-verification.json");cmd=load(folder/"command.json")
    label="writer" if index==0 else f"reader{index:02d}"
    check(raw_record==record and actual==record["result"],label+" raw process/result equals aggregate")
    check(record["exit"]==0 and record["timed_out"] is False and record["retained_Popen_reaped"] is True and record["execution_error"] is None and record["error_markers"]==[] and record["strict_result_binding"] is True,label+" actual retained process completed cleanly")
    check(actual["job_sha256"]==sha(folder/"job.json") and same(actual["job_path"],folder/"job.json") and same(actual["project_root"],studio) and actual["source_revision"]==job["source_revision"]==REVISION and actual["source_manifest_sha256"]==job["source_manifest_sha256"]==snapshot_sha and actual["mode"]==job["mode"] and same(job["folder"],folder),label+" exact request/root/mode/source/digest binding")
    receipt_key=str(Path(record["receipt_path"]).resolve())
    check(receipt_key in aggregate_receipts and record["receipt"]==aggregate_receipts[receipt_key]["receipt"] and same(cmd[cmd.index("--receipt")+1],record["receipt_path"]) and same(cmd[cmd.index("--path")+1],studio),label+" invocation and physical receipt join")
    log_markers={name:[line for line in (folder/name).read_text(encoding="utf-8",errors="replace").splitlines() if any(token in line for token in BAD)] for name in ("engine.log","stdout.log")}
    check(all(not lines for lines in log_markers.values()),label+" actual stdout and engine log error/leak scan")
    if index==0:
        check(job["cases"]==case_plan and actual["actual_app"] is True and actual["actual_source_dialog"] is True and actual["actual_native_conversion"] is True,label+" real dialog and conversion mode")
    else:
        check(actual["checks"]==(34 if index==1 else 30) and actual["failures"]==0 and actual["actual_app"] is True and actual["actual_native_conversion"] is False and actual["actual_source_dialog"] is False,label+" exact cold-reader checks and no conversion")
        expected=load(job["expected"])
        check([x["mode"] for x in actual["reader_modes"]]==["packed","linked"] and all(x["checks"]==14 and x["failures"]==0 and x["frames"]==[0,24] and x["passed"] is True for x in actual["reader_modes"]),label+" both cold save modes and original reference frames")
        for mode in actual["reader_modes"]:
            check(mode["project_sha256"]==expected["projects"][mode["mode"]]["sha256"]==sha(expected["projects"][mode["mode"]]["path"]),label+" actual saved package hash "+mode["mode"])
            for frame in (0,24):
                writer_picture=Path(expected["pictures"][str(frame)]["path"]);reader_picture=folder/(mode["mode"]+f"-{frame}.png")
                equal=sha(writer_picture)==sha(reader_picture)
                check(equal,label+f" raw PNG bytes exactly equal independent writer reference {mode['mode']} frame{frame}")
                frame_rows.append({"reader":label,"case":expected["name"],"mode":mode["mode"],"frame":frame,"writer_png_sha256":sha(writer_picture),"reader_png_sha256":sha(reader_picture),"writer_pixel_sha256":expected["pictures"][str(frame)]["pixel_sha256"],"exact_png_bytes":equal,"width":1920,"height":1080})
    job_rows.append({"job":label,"folder":str(folder),"job_sha256":sha(folder/"job.json"),"result_sha256":sha(folder/"result.json"),"checks":actual["checks"],"failures":actual["failures"],"receipt_path":record["receipt_path"],"receipt_sha256":sha(record["receipt_path"]),"source_manifest_sha256":snapshot_sha,"error_markers":log_markers})
    for name in ("job.json","command.json","result.json","process-verification.json","engine.log","stdout.log"):
        put(folder/name,"actual/jobs/"+label+"/"+name)

converted=[]
for original,planned,case in zip(original_plan,case_plan,cases):
    name=case["name"];folder=Path(planned["folder"]);catalogue=load(folder/"catalogue.json")
    source=Path(planned["source"]);resource_root=Path(planned["resource_root"])
    original_source=Path(original["source"]);original_root=Path(original["resource_root"])
    source_sha=sha(source);owned_key=relative(source,RUN/"inputs");original_key=relative(original_source,original_root)
    check(source.is_relative_to(RUN/"inputs") and resource_root.is_relative_to(RUN/"inputs") and relative(source,resource_root)==original_key and owned_stamps[owned_key]==originals[str(original_root)][original_key] and source_sha==owned_stamps[owned_key]["sha256"]==catalogue["native_mdl_sha256"],name+" owned MDL/catalogue/original resource hash and relative path join")
    check(case["checks"]==admission["per_case_expected_checks"][name] and case["failures"]==0 and case["passed"] is True,name+" exact admitted case assertions")
    info={"name":name,"checks":case["checks"],"source_sha256":source_sha,"requested_skin":planned["skin"],"requested_numeric_bodygroups":planned["bodygroups"],"all_blank_refused":case["all_blank_refused"],"conversion_started":case["conversion_started"],"phases":case["completed_phases"]}
    if case["conversion_started"]:
        converted.append(case);request=load(case["conversion_request"]);parameters=load(case["parameters"]);expected=load(case["expected"]);widget=load(folder/"widget-request.json")
        changed=planned["use_override"] and (planned["skin"]!=0 or any(v!=0 for v in planned["bodygroups"].values()))
        native=parameters["native_parameters"]
        check(same(request["original_source"],source) and request["sha256"]==source_sha and same(request["sourceio"],environment["HYBRID_SOURCEIO"]),name+" conversion source/runtime request binding")
        check(all(Path(mount).resolve().is_relative_to(RUN/"inputs") or Path(mount).resolve().is_relative_to(studio/"output/compatibility") for mount in request["mounts"]),name+" no installed fallback mounts")
        check((request.get("appearance")==widget and widget.get("bodygroups")==planned["bodygroups"] and widget.get("skin")==planned["skin"] and widget.get("source_sha256")==source_sha and widget.get("native_mdl_sha256")==source_sha) if changed else ("appearance" not in request and widget=={}),name+" actual controls/request preserves default omission and numeric overrides")
        named={group["name"]:planned["bodygroups"].get(str(int(group["index"])),0) for group in catalogue["bodygroups"]}
        check(native["selected_skin"]==planned["skin"] and native["selected_bodygroup_indices"]==named and (not changed or native["selected_native_bodygroup_indices"]==planned["bodygroups"]),name+" actual converter retained skin/named/numeric bodygroup choices")
        check(expected["parameters"]==parameters and expected["glb_sha256"]==sha(Path(case["bundle"])/"scene.glb") and expected["name"]==name and same(expected["input_source"],source),name+" portable actor expectation/report and actual derived GLB hash join")
        for mesh in planned.get("expected_meshes",[]):check((mesh["name"] in case["meshes"])==mesh["present"],name+" exact native-derived mesh identity "+mesh["name"])
        for morph in planned.get("expected_morphs",[]):check((morph["name"] in case["morphs"])==morph["present"],name+" actual morph identity "+morph["name"])
        check(case["completed_phases"]==["metadata","controls","conversion","adoption","undo","redo","reference_0","reference_24","packed_save","packed_open_cached","linked_save"],name+" complete ordinary import/history/save phases")
        if changed and any("Default skin/bodygroup only" in line for line in parameters.get("limits",[])):legacy_default_warning.append(name)
        info.update(default_appearance_omitted=not changed,actual_numeric_bodygroups=native.get("selected_native_bodygroup_indices"),actual_named_bodygroups=native["selected_bodygroup_indices"],actual_skin=native["selected_skin"],glb_sha256=expected["glb_sha256"],meshes=case["meshes"],morphs=case["morphs"],reference_frames=expected["pictures"],projects=expected["projects"])
    else:
        check(planned["expect_all_blank"] is True and case["all_blank_refused"] is True and case["completed_phases"]==["metadata","controls","all_blank_refusal"],name+" actual all-blank GUI refusal before conversion/adoption")
    for item in sorted(folder.iterdir()):
        if item.is_file() and item.name in {"catalogue.json","expected.json","widget-request.json","writer-result.json"}:put(item,"actual/cases/"+folder.name+"/"+item.name)
    metadata=folder/"conversion-metadata"
    if metadata.exists():
        for item in sorted(metadata.iterdir()):
            if item.is_file() and item.suffix in (".json",".log"):
                if item.suffix==".log":check(not any(token in item.read_text(encoding="utf-8",errors="replace") for token in BAD),name+" retained conversion log error/leak scan")
                put(item,"actual/cases/"+folder.name+"/conversion-metadata/"+item.name)
    case_rows.append(info)
check(len(converted)==wanted_readers and [load(RUN/"readers"/f"{i:02d}"/"job.json")["expected"] for i in range(1,wanted_readers+1)]==[row["expected"] for row in converted],"every successful writer case joins exactly one fresh reader")
check(sum(row["checks"] for row in cases)+1==wanted_writer and sum(row["result"]["checks"] for row in value["readers"])==34+(wanted_readers-1)*30,"writer+reader aggregate count arithmetic")

movie=value["movie"];ffprobe=load(RUN/"readers/01/ffprobe.stdout.log")
video=next(x for x in ffprobe["streams"] if x["codec_type"]=="video")
check(movie["video"]==video and (video["codec_name"],video["width"],video["height"],video["r_frame_rate"],video["nb_read_frames"],float(video["duration"]))==("h264",1920,1080,"24/1","48",2.0) and any(x["codec_type"]=="audio" and x["codec_name"]=="aac" for x in ffprobe["streams"]),"raw ffprobe movie/audio stream contract")
check(movie["movie_sha256"]==sha(movie["movie"]),"actual movie file hash joins aggregate")
with wave.open(str(RUN/"readers/01/decoded.wav"),"rb") as audio:
    check(audio.getnchannels()==1 and audio.getsampwidth()==2 and audio.getframerate()==48000,"actual decoded audio PCM metadata")
    samples=array.array("h",audio.readframes(audio.getnframes()))
if sys.byteorder!="little":samples.byteswap()
onset=next((i/48000 for i,x in enumerate(samples) if abs(x)>2000),None);rms=math.sqrt(sum(v*v for v in samples[52800:57600])/4800)
check(onset==movie["onset_seconds"] and rms==movie["rms_at_1_1s"] and abs(onset-1)<.002 and 4000<rms<12000,"independently recomputed retained audio onset/RMS equals aggregate")
for item in (RUN/"readers/01").iterdir():
    if item.is_file() and (item.name.startswith("ffprobe") or item.name.startswith("audio-decode")) and item.suffix in (".json",".log"):put(item,"actual/movie-proof/"+item.name)
release=load(RUN/"graphics-lease-released.json");launch=load(LAUNCH/"launch.json")
check(release["verification_sha256"]==wanted_sha and release["authoritative_coordinator_and_owned_workers_absent"] is True and release["all_private_jobs_clean"] is True and release["lease_released"] is True and release["no_process_killed"] is True and release["coordinator_pid"]==launch["pid"] and release["coordinator_creation_utc"]==launch["creation_utc"] and launch["source_commit"]==REVISION,"authoritative lease closure joins exact coordinator creation/source/result")
for item in LAUNCH.iterdir():
    if item.is_file() and item.suffix in (".json",".log"):put(item,"actual/root-launch/"+item.name)
for item in RUN.iterdir():
    if item.is_file() and item.suffix==".json":put(item,"actual/root/"+item.name)
sources=("run.py","project.godot","src/source_choice_dialog.gd","src/source_import.gd","src/import_placement.gd","src/has_project.gd","tools/source_appearance.py","tools/source_archive.py","tools/blender_source_bridge.py","tools/prepare_source.py","tools/source_installation.py","tools/has_project.py","tools/build_owner_review_snapshot.py","tests/source_choices_native_smoke.gd","tests/verify_source_choices_native.py")
for name in sources:
    check(sha(studio/name)==before["files"][name]["sha256"],"included authoritative snapshot source "+name)
    put(studio/name,"source/"+name)
put(Path(__file__),"coordinator/audit_and_packet.py")
summary={"format":"has_source_choices_native_app_actual_audit_1","phase":phase,"run":str(RUN),"source_revision":REVISION,"source_context":"main_working_source_snapshot","aggregate_sha256":wanted_sha,"passed":not failures,"audit_assertions":len(checks),"failures":failures,"source_files":len(before["files"]),"snapshot_source_files":len(snapshot),"private_jobs":len(receipt_rows),"writer_checks":wanted_writer,"reader_checks":34+(wanted_readers-1)*30,"case_count":len(cases),"converted_cases":len(converted),"refused_all_blank_cases":len(cases)-len(converted),"source_preservation":value["preservation"],"source_manifest_sha256":snapshot_sha,"movie":movie,"audio_independently_recomputed":{"onset_seconds":onset,"rms_at_1_1s":rms},"receipts":receipt_rows,"jobs":job_rows,"cases":case_rows,"cold_frame_hashes":frame_rows,"legacy_metadata_caveat":{"default_only_limit_text_on_selected_variants":legacy_default_warning,"impact":"Any selected variants retaining a generic default-only limitation would be listed here; an empty list means none were found. Actual numeric requests, selected metadata, GLB identity and cold frame joins are retained. No native shader/jiggle fidelity claim."},"excluded":"No model/GLB/HAS/PNG/audio/movie/runtime bytes copied. Native extra-feature motion/assembly/artist fidelity and the separate25worker-only passes are not inferred.","checks":checks,"payload_records":records}
(DEST/"AUDIT.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
(DEST/"README.md").write_text(f"Actual {phase} static Source appearance app transport at source {REVISION}. Writer{wanted_writer}/0; {wanted_readers} fresh cold readers ({summary['reader_checks']}/0); {len(receipt_rows)} clean private jobs. Audit independently joins raw requests, results, physical receipts, source manifests, source copies, conversion parameters and frame/package hashes; audio onset/RMS is recomputed from retained decoded PCM without launching a runtime.\n\nOnly source and metadata/logs are included. Files above64KiB use deterministic gzip; AUDIT.json records exact original raw hashes and sizes. INDEX.json covers every other packet file. Any selected variants retaining generic default-only limitation text are listed in the audit; an empty list means none were found. This does not establish native shader/jiggle/assembly fidelity. The earlier25worker-only checks and old failed app attempts remain separate.\n",encoding="utf-8")
index={"format":"has_metadata_source_packet_index_1","files":[{"path":p.relative_to(DEST).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(DEST.rglob("*")) if p.is_file()]}
(DEST/"INDEX.json").write_text(json.dumps(index,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"packet":str(DEST),"audit_passed":not failures,"audit_assertions":len(checks),"failures":failures,"index_sha256":sha(DEST/"INDEX.json"),"files":len(index["files"]),"bytes":sum(x["bytes"] for x in index["files"]),"legacy_limit_text_cases":legacy_default_warning},indent=2))
raise SystemExit(0 if not failures else 1)
