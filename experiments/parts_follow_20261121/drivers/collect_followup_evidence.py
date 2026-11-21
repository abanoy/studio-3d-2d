"""Copy explicitly selected text receipts; never collect native artwork/arrays."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'experiments/parts_follow_20261121'
PACKET.mkdir(exist_ok=True)
def copy(source,name):
    source=Path(source);target=PACKET/name
    assert source.is_file() and source.suffix in ('.json','.log','.py','.ps1')
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
    assert target.read_bytes()==source.read_bytes()
follow=ROOT.parent/'has-parts-follow-20261121'
for leaf in ['result.json','ownership.json','engine.log']:
    copy(follow/'output/character-parts-follow-1795279957952541500'/leaf,'initial_cpu/'+leaf)
for name,epoch in [('final_cpu','1795281957096324400'),('cpu_timing','1795281981818221300')]:
    for leaf in ['result.json','ownership.json','engine.log']:
        copy(follow/'output'/('character-parts-follow-'+epoch)/leaf,name+'/'+leaf)
for leaf in ['result.json','ownership.json','engine.log']:
    copy(follow/'output/character-parts-1795282066093572800'/leaf,'final_static/'+leaf)
for name,epoch in [('neon','1795280589197763000'),('classic','1795280979129511000'),('restricted_launch_refusal','1795280961444882400')]:
    case=follow/'output'/('part-follow-gui-'+epoch)
    for leaf in ['verification.json','writer-engine.log','reader-engine.log','writer-launcher.log','reader-launcher.log']:
        if (case/leaf).is_file():copy(case/leaf,name+'/'+leaf)
for name,epoch in [('corrected_neon','1795281678152210900'),('corrected_classic','1795281749492683000')]:
    for leaf in ['verification.json','writer-engine.log','reader-engine.log','writer-launcher.log','reader-launcher.log']:
        copy(ROOT/'output'/('part-follow-gui-'+epoch)/leaf,name+'/'+leaf)
copy(ROOT/'output/FOLLOWER_NATIVE_CAPTURE_IDENTITY.json','capture_identity.json')
for name in ['refresh_following_ports.py','check_following_ports.py','run_scoped_ports.py']:
    copy(ROOT/'output'/name,'drivers/'+name)
copy(ROOT/'output/FOLLOWING_REVIEWED_PORT_CHANGES.json','ports/exact_bindings.json')
copy(ROOT/'output/following-port-check-1795281737359885200/result.json','ports/binding_refusals.json')
copy(ROOT/'output/wind-review/graphical-1795281906235582000/verification.json','ports/wind_graphical.json')
copy(ROOT/'output/helper-preview/graphical-1795282110844823700-89d374d3/verification.json','ports/helper_graphical.json')
copy(ROOT/'output/following-port-graphical-1795281906085570400/completion.json','ports/outer_completion.json')
port=ROOT.parent/'has-port-followup-20261121'
copy(port/'output/port-preflight-1795280126126742500/result.json','ports/shipping243_preflight.json')
copy(port/'docs/benchmarks/reviewed_port_refresh_2026-11-21.json','ports/shipping243_CPU_review.json')
copy(__file__,'drivers/collect_followup_evidence.py')
full=ROOT.parent/'has-import-info-full-20261121-243e6a1e/output'
inner=full/'windows-reference-body-1795278347019144700'
for leaf in ['completion.json','source-before.json','stderr.log','stdout.log']:
    copy(inner/leaf,'failed_full243/'+leaf)
assert (inner/'source-before.json').read_bytes()==(inner/'source-after.json').read_bytes()
copy(full/'root-full-launch-1795278346795369100/completion.json','failed_full243/outer_completion.json')
copy(full/'wind-review/graphical-1795279676694898200/verification.json','failed_full243/wind_refusal.json')
for source,name in [('FAILED_FEATURE_CLEANUP_REMOVED_20261121.json','cleanup/actual_removed.json'),('ARCHIVE_FOLLOWUP_REMOTE_VERIFIED_20261121.json','publication/remote_c061.json'),('cleanup_failed_feature_runs.ps1','cleanup/cleanup_failed_feature_runs.ps1'),('preflight_old_full_cleanup.py','cleanup/refused_old_full_preflight.py')]:
    copy(ROOT/'output'/source,name)
copy(ROOT.parent/'has-secondary-contact-20261121/output/secondary-contact-visual-1795280320854606800/verification.json','pending_miku/adverse_skin_contact.json')
refusal={'status':'REFUSED_NOT_REMOVED','target':str(ROOT.parent/'has-import-info-full-20261121-2f1acbd'),'reason':'Initial read-only fast directory audit refused a metadata-test reparse redirect and link-count values other than one. No removal attempted. Later explicit Path.stat reports AGENTS.md link count1, so fast scan values do not establish actual hardlinks. Further precise alias/dependency audit required.','aliases':['output/private-metadata-windows/1795270574291047100/owned metadata [unicode]/redirect'],'alias_resolves_inside_same_checkout':True,'actual_hardlinks_not_established':True,'flagged_link_count_examples':['.gitattributes','.gitignore','AGENTS.md','CODEX_CUSTOM_ANIMATION_STUDIO_SPEC.md','CREDITS.md'],'unknown_non_generated_files':0,'actual_removal':False}
(PACKET/'cleanup/old_full_refused.json').write_bytes((json.dumps(refusal,indent=2)+'\n').encode())
rows=[]
for path in sorted(PACKET.rglob('*')):
    if path.is_file() and path.name!='CONTENTS.json':
        data=path.read_bytes();rows.append({'path':path.relative_to(PACKET).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(PACKET/'CONTENTS.json').write_bytes((json.dumps({'format':'has_explicit_text_receipts_1','files':rows},indent=2)+'\n').encode())
print(json.dumps({'files':len(rows),'bytes':sum(row['bytes'] for row in rows)}))
