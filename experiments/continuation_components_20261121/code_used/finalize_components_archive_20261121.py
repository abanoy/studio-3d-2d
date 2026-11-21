"""Finalize the explicitly collected text-only component checkpoint."""
from pathlib import Path
import hashlib,importlib.util,json,shutil,time
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
STAGE=OUT/'after-c315-archive-staging-import-info-20261121'
DEST=ROOT/'experiments/continuation_components_20261121'
spec=importlib.util.spec_from_file_location('_component_archive_audit',OUT/'finalize_continuation_archive_20261121.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
A.EXT.update({'.godot','.tscn','.cfg','.bat','.sh','.svg'})
assert STAGE.resolve().parent==OUT.resolve() and DEST.resolve().parent==(ROOT/'experiments').resolve() and not DEST.exists()
allow=A.load(A.read(STAGE/'PENDING_CONTENTS.json'));assert A.digest(A.read(STAGE/'PENDING_CONTENTS.json'))=='601040ffafc5532bf529d15826e3d40e4c294fb326bc1dfb31c6f3423988bdeb'
for row in allow['files']:
 raw=A.read(STAGE/A.rel(row['path']));assert len(raw)==row['bytes'] and A.digest(raw)==row['sha256']
assert {p.relative_to(STAGE).as_posix() for p in A.files(STAGE)}=={'BUILDING.json','PENDING_CONTENTS.json'}|{r['path'] for r in allow['files']}
shutil.copytree(STAGE,DEST)
(DEST/'PENDING_CONTENTS.json').rename(DEST/'COLLECTION_ALLOWLIST.json')
origins={r['path']:r['source'] for r in allow['files']};origins['COLLECTION_ALLOWLIST.json']='Exact frozen V3 collector allowlist; historical status/cutoff notes retained'
def copy(source,name):
 raw=A.read(source);A.privacy(name,raw);target=DEST/A.rel(name);target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():assert A.read(target)==raw
 else:
  with target.open('xb') as stream:assert stream.write(raw)==len(raw)
 assert A.read(source)==raw and A.read(target)==raw;origins[name]=str(source)
for folder,pin in [('source-import-info-adoption-plan-prep-20261121','120d7c264df132aaec06f18104e481dfbeea081955fa479d005e41193a99171d'),('source-junko-body-dress-native-binding-prep-20261121','9989f3f2746e37666dc541ef44990a71d757f4d4d7eaa035e0525a81eb357913')]:
 base=OUT/folder;raw=A.read(base/'SOURCE_PINS.json');assert A.digest(raw)==pin;manifest=A.load(raw)
 for row in manifest['files']:
  value=A.read(base/A.rel(row['path']));assert len(value)==row['bytes'] and A.digest(value)==row['sha256'];copy(base/A.rel(row['path']),'source/'+folder+'/'+row['path'])
 copy(base/'SOURCE_PINS.json','source/'+folder+'/SOURCE_PINS.json')
for name in ['refresh_import_info_pose_pins_20261121.py','IMPORT_INFO_POSE_PIN_REFRESH_20261121.json','IMPORT_INFO_POSE_PIN_REFRESH_SOURCE_PEER_20261121.json','IMPORT_INFO_ADOPTION_20261121.json','IMPORT_INFO_FINAL_FUNCTIONAL_CATALOGUE_20261121.json','record_import_info_checkpoint_20261121.py','IMPORT_INFO_CHECKPOINT_DOCUMENTATION_20261121.json']:
 copy(OUT/name,'root-addendum/'+name)
copy(Path(__file__),'code_used/finalize_components_archive_20261121.py')
audit_source=(OUT/'finalize_continuation_archive_20261121.py').read_text()
anchor="EXT = {'.gd', '.py', '.ps1', '.md', '.txt', '.json', '.log', '.cpp', '.h', '.mjs'}"
assert audit_source.count(anchor)==1;audit_source=audit_source.replace(anchor,anchor+"\nEXT.update({'.godot','.tscn','.cfg','.bat','.sh','.svg'})")
(DEST/'code_used/audit_components_archive.py').write_text(audit_source)
origins['code_used/audit_components_archive.py']='Exact earlier read-only archive auditor with declared authored-text extensions added; audit mode only'
readme='''# Component continuation checkpoint — November 21, 2026

Import info is adopted in the current source: select a World asset to inspect
available features, stored data, compatibility limits and missing-resource
actions. Its window resizes without changing authored state. It supports both
themes/workspaces, and packed reports survive a fresh offline reader.

The new source has1109 functional files and183 canonical verification groups.
The exact16-file adoption passed, followed by four PoseEditor hash-field updates
in the two existing port manifests. The full new aggregate is still required.
Formal scores remain52/54 implementation and55/62 acceptance.

Actual independent scopes:267 ordinary component checks across21 cases/eight
cold pairs; final metadata-only successor163 CPU plus five independently audited
headless receipts; coordinator47 controls; lifecycle53 and optional native PMX
missing-texture packed/offline wrapper; two actual editor map checks32each,
both before and after Import info composition; corrected native contact129;
29 remaining standalone wrappers/70 private jobs; final21 movie/audio checks.
These do not repair or replace the failed c315 Full. Its four failed gestures,
all167 private receipts and source preservation are retained.

Earlier failures remain inspectable: first import receipt classificationFAIL0;
headless path refusal; metadata startup missing coordinator files/isolated import
path; native PMX headless viewport errors; Root's redundant inherited-stdout
check after the unchanged native wrapper had already passed. Later passes are
separate records. The optional wrapper's two marker checks are attributed to its
actual engine-log validation, not invented inherited stdout.

Junko static assembly105 is composed96+9. Math21 and actual separate skeleton66
pass; real54-joint body/dress binding and SecondaryLive integration do not.
The new two-part native export diagnostic is reviewed source only and UNRUN at
this archive cutoff. Old c315 Full-gated Miku/face/easing/review hosts stay closed.
Synthetic ArrayMesh13/source-policy60 are not native motion or artist evidence.

Collection_allowlist metadata and source freeze-time UNRUN fields are historical.
Its inherited final cutoff sentence is stale: this archive DOES contain the later
actual267, policy47+CPU163, map-info64 and lifecycle53/native-wrapper receipts.
The Root addendum records subsequent adoption and source-pin refresh explicitly.

No owner project, native asset, image/movie/audio, converted geometry, executable,
SDK runtime or private pose/skin/collider array is included. Private inputs remain
protected on this PC; only scalar provenance and exact source/compact logs are
published. Authoring/runtime namespaces and failed/scoped/full results remain
separate. There is no new human/device or native appearance approval.

After retrieval, audit without executing archived application programs:

    python -B code_used/audit_components_archive.py --audit --archive <this folder>

CONTENTS.json gives every payload's raw SHA256. The Root source catalogue pins
the final1109 functional files. Current application files live at repository root;
frozen candidates retain their explicit old base revisions and are not imports
to apply blindly. See docs/RESUME_MASTER_PLAN.md for the next actual work.
'''
(DEST/'README.md').write_text(readme,encoding='utf-8');origins['README.md']='Generated truthful source/scoped-result cutoff'
rows=[]
for path in A.files(DEST):
 name=path.relative_to(DEST).as_posix()
 if name=='BUILDING.json':continue
 raw=A.read(path);A.privacy(name,raw);rows.append({'path':name,'source':origins.get(name,'Frozen declared component payload'),'bytes':len(raw),'sha256':A.digest(raw)})
contents={'format':'has_continuation_component_archive_1','functional_sources':1109,'canonical_groups':183,'new_Full_status':'REQUIRED_NOT_RUN','private_native_art_or_binaries_included':False,'payload_files':len(rows),'payload_bytes':sum(r['bytes'] for r in rows),'files':rows}
(DEST/'CONTENTS.json').write_text(json.dumps(contents,indent=2)+'\n')
result=A.audit(DEST,True);marker=DEST/'BUILDING.json';assert marker.resolve().parent==DEST.resolve();marker.unlink();assert A.audit(DEST)==result
result.update(format='has_components_archive_finalization_1',archive=str(DEST),new_Full_claimed=False,recorded_ns=time.time_ns())
(OUT/'IMPORT_INFO_COMPONENT_ARCHIVE_FINAL_20261121.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
