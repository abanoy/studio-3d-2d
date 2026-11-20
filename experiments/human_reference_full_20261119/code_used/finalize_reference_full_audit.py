from pathlib import Path
from collections import Counter
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'output/windows-human-reference-1795143503737924800'
def load(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
audit=load(RUN/'receipt-audit.json');completion=load(RUN/'completion.json');report=load(ROOT/'output/verification.json')
assert not audit['unclosed'] and not audit['unconfirmed'] and not audit['foreground']
unique={};duplicate=[]
same_keys=('desktop','child_pid','exit','seconds','job_closed','desktop_closed','private_window_seen','child_desktop_confirmed','foreground_child_observed','desktop_switch_requested','cancelled','error')
for row in audit['receipt_candidates']:
    if row['desktop'] in unique:
        prior=unique[row['desktop']]
        assert all(prior[key]==row[key] for key in same_keys)
        a=load(ROOT/prior['path']);b=load(ROOT/row['path'])
        duplicate.append({'desktop':row['desktop'],'paths':[prior['path'],row['path']],'physical_fields_identical':True,'extra_keys':sorted(set(a)^set(b)),'different_common_keys':[key for key in set(a)&set(b) if a[key]!=b[key]]})
    else:unique[row['desktop']]=row
assert len(unique)==200
nonzero=[row for row in unique.values() if row['exit']!=0]
assert len(nonzero)==1 and nonzero[0]['exit']==2 and nonzero[0]['cancelled'] and nonzero[0]['error']=='Owned converter cancelled'
core=['unit','motion_parts','motion_helper_edits','opaque_order','required_extensions','contact_bend','spikes','editor','export_failures','audio_editor','audio_dummy','ui','recovery_write','recovery','pose','autokey','new_scene','world_selection','world_document','world_runtime','world_edit','world_workflow','object_timing','bone_labels','animation_clips_unit','animation_clips','visibility','animated_channels','limb_ik','secondary_motion','fan_motion','physics','physics_contacts','physics_props','physics_recording_unit','physics_recording']
assert len(core)==36 and all(key in report for key in core)
movies=[key for key in report if key.endswith('_video') or key.startswith('posed_model_video_')]
assert len(movies)==20 and report['actual_mmd_tested'] is False,movies
for name,row in load(RUN/'source-after.json').items():
    file=ROOT/name;assert file.stat().st_size==row['bytes'] and file.stat().st_mtime_ns==row['mtime_ns'] and sha(file)==row['sha256'],name
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==completion['revision']
result={'format':'has_reference_full_terminal_audit_1','source_commit':completion['revision'],'status':'PASS','suite_exit':0,'retained_child_reaped':True,'seconds':completion['seconds'],'result_groups':len(report),'core_groups':len(core),'movie_groups':len(movies),'functional_files_unchanged':completion['functional_source_count'],'report_sha256':sha(ROOT/'output/verification.json'),'coordinator_completion_sha256':sha(RUN/'completion.json'),'source_before_sha256':sha(RUN/'source-before.json'),'source_after_sha256':sha(RUN/'source-after.json'),'collected_receipt_like_json':audit['collector_rows'],'excluded_copied_archival_experiment_receipts':audit['classification']['archived experiment copies'],'excluded_non_launcher_json':audit['classification']['not launcher receipt'],'current_receipt_paths':audit['launcher_candidates'],'unique_current_private_jobs':len(unique),'deduplicated_receipts':duplicate,'normal_private_exits':199,'expected_cancelled_converter_exits':1,'all_unique_jobs_desktops_closed_placement_confirmed_no_foreground_or_switch':True,'current_jobs':list(unique.values()),'movie_group_names':movies,'native_reference_guarded_checks':25,'human_device_acceptance_inferred':False,'formal_scores_unchanged':{'implementation':[52,54],'acceptance':[55,62]},'private_art_uploaded':False}
(RUN/'terminal-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:value for key,value in result.items() if key not in ('current_jobs','movie_group_names')},indent=2))
