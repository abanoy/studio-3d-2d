"""Freeze Root conversion runner sources only; no runtime/imports/Git."""
from pathlib import Path
import hashlib,json,shutil,ast
R=Path(__file__).resolve().parents[1]
D=R/'output/source-junko-stage-a-root-driver-prep-20261121'
K=R/'output/source-character-parts-root-runner-v2-prep-20261121'
P=R/'output/source-junko-body-dress-native-binding-prep-20261121'
def pin(raw):return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
assert not D.exists();D.mkdir()
sources={
 'run_stage_a.py':R/'output/run_junko_stage_a_20261121.py',
 'gated_converter_worker.py':R/'output/junko_stage_a_gated_worker_20261121.py',
 'root_native_job.py':K/'root_native_job.py',
 'approved_job_layout.py':K/'approved_job_layout.py',
 'BASELINE_SOURCE1109.json':R/'output/IMPORT_INFO_FINAL_FUNCTIONAL_CATALOGUE_20261121.json',
 'CANDIDATE_SOURCE_PINS.json':P/'SOURCE_PINS.json',
 'ROOT_PROTOCOL.md':P/'ROOT_PROTOCOL.md',
}
assert pin(sources['BASELINE_SOURCE1109.json'].read_bytes())['sha256']=='23ea7fe6c4e92c8184f421ce9425173d25c409c49d24dd150e5cafd3966685b2'
assert pin(sources['CANDIDATE_SOURCE_PINS.json'].read_bytes())['sha256']=='9989f3f2746e37666dc541ef44990a71d757f4d4d7eaa035e0525a81eb357913'
assert pin(sources['root_native_job.py'].read_bytes())['sha256']=='fe9a9da0b545fbc1c2b21d09e93dd931b52c5a9e4681c5f0d106c3e43d67f34b'
assert pin(sources['approved_job_layout.py'].read_bytes())['sha256']=='c3bad5ab1792f7103a9bf31eef283ee8b928bd4557b6e53c18b9c0718d92ae61'
for name,source in sources.items():
 raw=source.read_bytes()
 if name.endswith('.py'):ast.parse(raw,filename=name)
 (D/name).write_bytes(raw)
(D/'code_used').mkdir();shutil.copyfile(__file__,D/'code_used'/Path(__file__).name)
(D/'README.md').write_text('''# Root-only Junko Body/Dress StageA runner

Source only; author has launched no runtime or conversion. Exact candidate9989f3,
current1109 catalogue23ea7f and approved Job/layout bytes are required. Root supplies
the actual newly published40hex revision matching these same1109 source bytes/nsmtime.
An added/changed functional source requires a versioned successor, not a waived guard.
This independently scoped CPU component does not consume or waive any failed Full.

Run pinned existing Python313 with -I -S -B run_stage_a.py --self-sha256 <driverSHA>
--source-manifest-sha256 <thisSOURCE_PINSSHA> --revision <exactpublishedMainHEAD>
--root-cpu-component-confirmed. Do not run it before Root has reviewed the source.

One pure16-case stdlib/mock job precedes two separate720-second owned preparer jobs.
Each wrapper waits for the exact assigned Root Job/nonce/PID/birth gate before any
Python child can start. Existing16process4GiB kill-on-close/no-breakaway native Job
code is byte-exact. Retained child/wrapper handles, active0 and Job close must be
proved before the next command. Conversions remain background/factory/offline
Blender through the ordinary preparer, with no render, GPU, desktop or app launch.

The owned runtime has114 source files, a574-file SourceIO copy,99 exact native
copies and a120-file reference-only exporter backup. The actual registered exporter
remains the installed authenticated path; the reference copy never shadows imports.
Every existing original file, including original caches, is individually pinned
privately in addition to the source-only catalogue membership. All1109 Main sources,
originalSDK/exporter/native/executable bytes/native64 identities/nsmtime and copied
runtime/source/input bytes are reread after the component. Access times are excluded.

The private proof and final GLB are independently reconciled across every native
index/parent/exported node/skin membership, alongside the actual exporter marker and
complete ordinary status/report/blend. No source_export_crosswalk is promoted into
the model report. StageA success means conversion/export-binding only. Godot rest,
inverse-bind, actual skin calibration and54-link pose following remain separate.

All projects,GLBs,blend files, textures, original identities, logs, parameters and
PRIVATE_part_export_binding.json remain in the new owned local stage. Public result
contains only scalar/metadata job records,counts,hashes and preservation flags; no
bone/skin/morph/material/native-word arrays or art. Never upload the private stage.
No cleanup, installs, downloads, Main writes or installed exporter changes occur.
''',encoding='utf-8')
plan={'format':'has_junko_stage_a_driver_check_plan_1','status':'SOURCE_ONLY_UNRUN_PENDING_PEER','pure_unit_cases':16,'native_conversions':2,'jobs':3,'conversion_timeout_seconds':720,'inner_ordinary_preparer_timeout_seconds':600,'max_processes':16,'job_memory_bytes':4294967296,'root_main_functional_sources':1109,'runtime_source_files':114,'native_input_files':99,'sourceio_copied_files':574,'exporter_reference_copied_files':120,'actual_exporter_installed_readonly':True,'renders_or_GPU_requested':False,'Full_prerequisite_or_claim':False,'native_Godot_binding_or_follow_qualified':False}
(D/'CHECK_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
rows=[{'path':p.relative_to(D).as_posix(),**pin(p.read_bytes())} for p in sorted(D.rglob('*')) if p.is_file()]
(D/'SOURCE_PINS.json').write_text(json.dumps({'format':'has_junko_stage_a_root_source_pins_1','status':'SOURCE_ONLY_UNRUN_PENDING_PEER','files':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'folder':str(D),'files':len(rows)+1,'payload_bytes':sum(r['bytes'] for r in rows),'manifest':pin((D/'SOURCE_PINS.json').read_bytes()),'driver':pin((D/'run_stage_a.py').read_bytes()),'worker':pin((D/'gated_converter_worker.py').read_bytes()),'AST_sources_only_pass':4},indent=2))
