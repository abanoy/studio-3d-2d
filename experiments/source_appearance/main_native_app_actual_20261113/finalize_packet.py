"""Freeze the two completed metadata audits without any runtime/source mutation."""
from pathlib import Path
import gzip,hashlib,json,shutil
BASE=Path(__file__).resolve().parent
DEST=BASE/"review-ready";DEST.mkdir(exist_ok=False)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_bytes())
def write(path,value):Path(path).write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8")
audits=[load(BASE/name/"AUDIT.json") for name in ("core14","wider11")]
assert all(a["passed"] and not a["failures"] and not a["legacy_metadata_caveat"]["default_only_limit_text_on_selected_variants"] for a in audits)
for name in ("core14","wider11"):
    shutil.copytree(BASE/name,DEST/name)
    child=DEST/name
    audit=load(child/"AUDIT.json")
    for rec in audit["payload_records"]:
        data=(child/rec["path"]).read_bytes()
        assert len(data)==rec["bytes"] and hashlib.sha256(data).hexdigest()==rec["sha256"]
        raw=gzip.decompress(data) if rec["codec"]=="gzip" else data
        assert len(raw)==rec["raw_bytes"] and hashlib.sha256(raw).hexdigest()==rec["raw_sha256"]
    if name=="core14":
        # The first audit found zero stale warnings but used a generic caveat
        # sentence. Clarify only the narrative; preserve the original index.
        shutil.copy2(child/"INDEX.json",DEST/"core14-index-before-narrative-clarification.json")
        prior={file:sha(child/file) for file in ("AUDIT.json","README.md")}
        audit["legacy_metadata_caveat"]["impact"]="No selected variant retained generic default-only limitation text. The list is empty. Actual numeric requests, selected metadata, GLB identity and cold frame joins are retained. No native shader/jiggle fidelity claim."
        write(child/"AUDIT.json",audit)
        text=(child/"README.md").read_text(encoding="utf-8")
        text=text.replace("Generic converter 'Default skin/bodygroup only' limitation strings are retained unchanged and explicitly identified as stale on selected variants. This does not reduce the recorded static choice assertions or establish native shader/jiggle/assembly fidelity.","No changed variant retained generic default-only limitation text; the audit list is empty. This does not establish native shader/jiggle/assembly fidelity.")
        (child/"README.md").write_text(text,encoding="utf-8")
        write(DEST/"core14-narrative-clarification.json",{"scope":"Only audit prose was clarified after an empty warning list; no actual report, source, check, receipt, artifact, or assertion changed.","before":prior,"after":{file:sha(child/file) for file in prior},"actual_executed_coordinator":"core14/coordinator/audit_and_packet.py remains the exact executed version"})
        index={"format":"has_metadata_source_packet_index_1","files":[{"path":p.relative_to(child).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(child.rglob("*")) if p.is_file() and p.name!="INDEX.json"]}
        write(child/"INDEX.json",index)
core=Path(audits[0]["run"]);wider=Path(audits[1]["run"])
source_same=load(core/"source-before.json")==load(wider/"source-before.json")
runtime_same=load(core/"runtimes-before.json")==load(wider/"runtimes-before.json")
assert source_same and runtime_same
summary={"format":"has_source_choices_native_app_combined_actual_1","source_revision":audits[0]["source_revision"],"source_context":"main_working_source_snapshot","full_source_and_mtime_and_HEAD_exact_across_runs":source_same,"approved_runtime_maps_exact_across_runs":runtime_same,"source_files":audits[0]["source_files"],"actual_native_cases":sum(a["case_count"] for a in audits),"converted_cases":sum(a["converted_cases"] for a in audits),"all_blank_GUI_refusals":sum(a["refused_all_blank_cases"] for a in audits),"writer_checks":sum(a["writer_checks"] for a in audits),"cold_reader_checks":sum(a["reader_checks"] for a in audits),"total_actual_app_checks":sum(a["writer_checks"]+a["reader_checks"] for a in audits),"fresh_cold_readers":sum(a["converted_cases"] for a in audits),"clean_private_jobs":sum(a["private_jobs"] for a in audits),"metadata_audit_joins":sum(a["audit_assertions"] for a in audits),"exact_cold_frame_PNG_joins":sum(len(a["cold_frame_hashes"]) for a in audits),"derived_movies":[{"phase":a["phase"],"movie_sha256":a["movie"]["movie_sha256"],"video":{"codec":"h264","width":1920,"height":1080,"frames":48,"fps":"24/1","duration_seconds":2.0},"aac":True,**a["audio_independently_recomputed"]} for a in audits],"per_phase":[{"name":a["phase"],"aggregate_sha256":a["aggregate_sha256"],"writer_checks":a["writer_checks"],"reader_checks":a["reader_checks"],"private_jobs":a["private_jobs"],"audit_assertions":a["audit_assertions"],"packet_index_sha256":sha(DEST/a["phase"]/"INDEX.json")} for a in audits],"scope":"Actual static skin/bodygroup UI choices and real SourceIO conversion; ordinary Add/Undo/Redo with protected peer/draw/audio/camera state; packed open then linked save; owned native inputs/caches offline for every fresh reader; exact derived frame/package/report joins; two audio-gated movies. Keiki mesh/Tools morph identity and the admitted normal bone23 pose are covered. No native Source shader/jiggle/controller/assembly/artist fidelity claim.","separate_evidence":"Earlier25background worker-only cases and the failed bootstrap/thin-AABB app attempts are separate preserved checkpoints, not merged into this app pass. The complete canonical default run after8d4fde0 is still pending.","metadata_builder_attempt":"One output-only builder attempt referenced a nonexistent optional source filename, before producing an audit/index. Partial metadata is retained at sibling core14-attempt1-metadata-script-failure; the allowlist was corrected to source_installation.py. No product/runtime test was run or affected.","publication_payload_rule":"Only text source/JSON/metadata/logs and deterministic gzip of them. No model/GLB/HAS/PNG/audio/movie/runtime payloads."}
assert summary["actual_native_cases"]==25 and summary["converted_cases"]==22 and summary["all_blank_GUI_refusals"]==3 and summary["writer_checks"]==680 and summary["cold_reader_checks"]==668 and summary["total_actual_app_checks"]==1348 and summary["clean_private_jobs"]==24 and summary["exact_cold_frame_PNG_joins"]==88
write(DEST/"SUMMARY.json",summary)
(DEST/"README.md").write_text("Actual static Source appearance integration passed on source8d4fde0:25cases,22conversions and3all-blank GUI refusals;680writer+668cold-reader checks;24clean private jobs. Both phases used exactly the same3279source-file/hash/nsmtime/HEAD map and approved-runtime map. Independent read-only metadata audits passed629joins, including88rawPNG byte-equality joins to original writer references and recomputed audio onset/RMS.\n\nBothmovies are48-frame1920×1080 H264 at24fps withAAC; onset1.0000416666666667s. No media or native/runtime payload is included. Each child AUDIT.json records all raw-file hashes, portable actor/reference metadata and exact receipts. Files above64KiB are losslessly deterministic gzip; raw size/SHA256 is retained. Child and outer indices cover every other payload file.\n\nThe earlier25worker-only cases, previous failed app attempts, and pending later canonical default run remain separate. This proves static import-time choices and derived editor/persistence/render transport; native shader, procedural jiggle, controller, assembly and artist fidelity remain outside this claim.\n",encoding="utf-8")
shutil.copy2(BASE/"audit_and_packet.py",DEST/"audit_and_packet.py")
shutil.copy2(Path(__file__),DEST/"finalize_packet.py")
shutil.copy2(BASE/"core14-attempt1-metadata-script-failure/FAILURE.json",DEST/"metadata-builder-attempt1-failure.json")
allowed={".gd",".py",".godot",".json",".md",".log",".gz"}
assert all(p.suffix in allowed for p in DEST.rglob("*") if p.is_file())
index={"format":"has_metadata_source_packet_index_1","files":[{"path":p.relative_to(DEST).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(DEST.rglob("*")) if p.is_file()]}
write(DEST/"INDEX.json",index)
print(json.dumps({"folder":str(DEST),"files":len(index["files"]),"bytes":sum(x["bytes"] for x in index["files"]),"index_sha256":sha(DEST/"INDEX.json"),"counts":{k:summary[k] for k in ("total_actual_app_checks","clean_private_jobs","metadata_audit_joins","exact_cold_frame_PNG_joins")}},indent=2))
