"""Append truthful pickup state and refresh the final1109 source catalogue."""
from pathlib import Path
import hashlib,importlib.util,json,time
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';PARENT=ROOT.parent
adopt=json.loads((OUT/'IMPORT_INFO_ADOPTION_20261121.json').read_bytes());assert adopt['status']=='PASS'
spec=importlib.util.spec_from_file_location('_info_final_sources',ROOT/'experiments/reference_body_20261120/run_full.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
catalogue=F.snapshot();assert len(catalogue)==1109
(OUT/'IMPORT_INFO_FINAL_FUNCTIONAL_CATALOGUE_20261121.json').write_text(json.dumps(catalogue,indent=2)+'\n')
plan=json.loads((OUT/'source-import-info-adoption-plan-prep-20261121/READY_ADOPTION_PLAN.json').read_bytes())
evidence={}
for name,row in plan['required_qualification'].items():
 raw=Path(row['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'] and json.loads(raw)['status']=='PASS';evidence[name]={'bytes':len(raw),'sha256':row['sha256'],'private_origin':row['path']}
record={'format':'has_import_info_increment_1','date':'2026-11-21','status':'ADOPTED_SCOPED_QUALIFIED_FRESH_FULL_REQUIRED','base_revision':adopt['base_revision'],'functional_sources':1109,'canonical_groups':183,
 'feature':'Persistent read-only Import info for the selected model or environment, with available/retained/limited features and missing-resource actions. Resizable in Classic/Neon Simple/Advanced; packed reports survive fresh offline replay.',
 'production_files_modified':3,'production_files_added':2,'functional_files_modified':12,'functional_files_added':6,
 'scopes':{'ordinary_component267':{'CPU':163,'GUI_and_cold':104,'cases':21,'cold_pairs':8},'final_metadata_only_successor':{'CPU':163,'independently_admitted_current_headless_receipts':5},'coordinator_policy':{'prior':17,'new':30,'total':47},'import_ownership':53,'optional_native_missing_texture_wrapper':'PASS: actual persistent report, packed reopen, source-cache-offline relocated reader and unsafe-path refusal','prepared_maps_with_import_info':64,'corrected_contact_gesture':129},
 'final_metadata_successor267_already_passed':False,'whole_new_Full_passed':False,'failed_c315_Full_preserved':True,
 'source_test_changes':'Refresh import test collaborators and the optional missing-texture UI assertion. Correct rotation test input to actual ray/plane geometry; preserve all129 assertions and strict contact/sample/movie limits.',
 'manifest_refresh':'Only four raw/LF PoseEditor digest fields across the two wind/helper manifests; all memberships and other rows exact.',
 'native_fixture_preservation_scope':'Map replay explicitly hashes all admitted prepared and original inputs before/after. Optional MMD wrapper was inspected read-only and copies originals; separate new original-MMD SHA/mtime measurement is not claimed.',
 'formal_implementation':[52,54],'formal_acceptance':[55,62],'stable_requirement_statuses_changed':False,'human_or_device_evidence_substituted':False,'evidence':evidence,'recorded_ns':time.time_ns()}
target=ROOT/'docs/benchmarks/import_info_increment_2026-11-21.json';assert not target.exists();target.write_text(json.dumps(record,indent=2)+'\n')
ledger=ROOT/'docs/completion_checklist.json';value=json.loads(ledger.read_bytes())
assert 'latest_import_info_increment_20261121' not in value
value={'latest_import_info_increment_20261121':{'status':record['status'],'base_revision':adopt['base_revision'],'functional_sources':1109,'canonical_groups':183,'evidence':'docs/benchmarks/import_info_increment_2026-11-21.json','formal_status_changed':False,'scores':'52/54 implementation;55/62 acceptance','next':'Commit/push, verify a fresh remote checkout, stage original historical fixtures read-only, then run all183 groups on the committed source. Failed c315 Full remains failed.'},**value}
ledger.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
section='''
## 2026-11-21 — Import info adopted; new complete verification required

This entry supersedes the earlier running/pending notes. The exact c315 Full
failed four obsolete fixed-pixel rotation gestures after 2,801.18 seconds; all
167 private jobs closed and its source stayed unchanged. That run remains failed.
The corrected ray/plane gesture test independently passed all129 native checks.
The remaining29 standalone wrappers passed in70 private jobs, and all21 final
movie/audio cases passed. These are separate scopes, not a repaired aggregate.

The new user-facing addition is **Import info**, available for the selected World
asset and in pose controls. It is resizable and read-only, explains available
features versus retained data and limitations, names missing-resource actions,
and preserves the complete report in packed HAS files. Async imports retain
their requesting project/sequence ownership. Source remains standardized through
the existing HAS representation; the panel does not promise native fidelity.
See docs/import_info.md and docs/benchmarks/import_info_increment_2026-11-21.json.

Actual qualification:267 ordinary component checks (163 CPU plus104 graphical/
cold checks,21 cases and8 fresh reader pairs), across both themes/workspaces and
100/150% scale. The final metadata-only wrapper successor separately passed163
CPU checks and an independent audit of its five real headless receipts. The
coordinator retains its17 original controls plus30 new negatives (47 pass),
admits only those five authenticated no-window cases, and keeps graphical
placement requirements strict. The final metadata version has not yet passed a
complete267 batch; the new Full will execute it. Import lifecycle53 and optional
native PMX missing-texture recovery/packed offline replay passed in owned headless
jobs. Both gm_construct and ttt_tiny_spaceship_v3 passed32 actual editor checks
each, first on c315 and then with all five Import info production overlays. These
replay the earlier conversion outputs; they are not new conversions or visual
appearance approval. Every attempted job is closed/reaped.

Root adopted exactly16 reviewed files (10 replacements and6 new), then refreshed
only the four PoseEditor digest fields in the two wind/helper port manifests.
Final source count1109; the new canonical suite has183 groups. No other product
source changed. All source packets, initial failed/refused launches, raw safe
logs, the failed Full and corrected scoped results are preserved in the new
experiments/continuation_components_20261121 archive. Root transport failures
remain failures: the first component demanded a window from a headless case;
metadata startup initially omitted the six coordinator files and then the
isolated sibling import path; the optional PMX fixture needed an explicit
headless viewport, followed by a Root stdout-vs-engine-log attribution fix.
No application assertion, contact limit, pixel or audio tolerance was relaxed.

Other completed independent work: Junko static assembly105 is composed96+9, with
the original partial failure retained. Rest-relative math21 and actual separate
Model/Skeleton3D controller66 pass, including54 generated links, ordering,
restoration and Undo. Actual Junko body/dress binding and live secondary-motion
integration remain unqualified. Synthetic ArrayMesh13 and source-policy60 pass.
The old c315 Full-gated Miku/face/easing/review hosts remain CLOSED; do not feed
them failed c315 evidence or silently relabel them for the new source. Hair is
preparing a separate bounded actual body/dress conversion/binding diagnostic.

Next: publish and independently verify this increment, then run a fresh genuine
1109-source/183-group Full from the retrieved commit. Keep prior failed Fulls,
44 unavailable historical-reader skips, private original assets and pending
reviews. After remote verification, remove only audited disposable CPU stages;
the seven-stage cleanup packet covers47,366,153 logical bytes, not a deletion
already performed. No new cleanup is claimed here.

Formal scores stay52/54 implementation and55/62 acceptance until the appropriate
requirements qualify. The seven remaining external IDs are IMPORT-02, IMPORT-03,
ACCEPT-A, ACCEPT-B, ACCEPT-E, ACCEPT-TABLET and ACCEPT-INSTALL. Required actual
observations are native source appearance/rig/material comparison; a timed
novice eight-step and drawing/audio exercise; a learner's real stuck/hint,
Previous/Continue/Fresh exercise; physical tablet pressure/latency/comfort and
audible sync; and a clean approved offline Windows setup/save/reopen/export.
The original19-layer hecatia.kra is available and hash-verified. The missing old
November4 backups are dead, not a request to repeat. Do not interrupt the owner
for manual exercises while independent software work remains.
'''
for name in ('LLM.md','docs/progress_memo.md','docs/RESUME_MASTER_PLAN.md','docs/NEXT_SESSION_PLAN_2026-11-20.md'):
 path=ROOT/name;raw=path.read_bytes();assert section.splitlines()[1].encode() not in raw;path.write_bytes(raw+section.encode())
path=ROOT/'docs/windows_acceptance_followup.md';raw=path.read_bytes();path.write_bytes(raw+b'\n\n## Import information follow-up, 2026-11-21\n\n'+b'Import info is adopted with scoped267 GUI/CPU/cold checks, final-metadata163,\n'+b'policy47, lifecycle53 and supported map editor64 checks. Source is1109 files;\n'+b'canonical Full is183 groups and must run on the new retrieved commit. The c315\n'+b'Full remains failed; separate scoped continuations do not replace it. See\n'+b'[current evidence](benchmarks/import_info_increment_2026-11-21.json). The seven\n'+b'actual human/device/setup gates above remain open; no owner exercise is claimed.\n')
(OUT/'IMPORT_INFO_CHECKPOINT_DOCUMENTATION_20261121.json').write_text(json.dumps({'status':'PASS','functional_sources':1109,'canonical_groups':183,'formal_status_changed':False,'history_files_appended':4,'benchmark':str(target),'recorded_ns':time.time_ns()},indent=2)+'\n')
print(json.dumps({'status':'PASS','functional_sources':1109,'canonical_groups':183}))
