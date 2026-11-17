"""Freeze an explicit text/source allowlist from two completed root runs only."""
from pathlib import Path
import hashlib
import json
from archive_checks import check,require

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]
REVIEW=MAIN.parent/'has-neon-review-20261116-c2d52ff'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    require(not (HERE/'INPUTS.json').exists(),'Fresh immutable recipe only')
    roots={'MAIN':MAIN,'REVIEW':REVIEW}; paths=[]
    for dirname in ('neon-scene-mask-diagnostic-20261117-attempt1','neon-scene-view106-20261117-attempt1'):
        folder=REVIEW/'output'/dirname
        paths.extend(('REVIEW',p.relative_to(REVIEW).as_posix()) for p in folder.iterdir() if p.is_file() and p.suffix in ('.json','.log'))
    paths.append(('REVIEW','output/neon-scene-mask-diagnostic-20261117-attempt1/case/result.json'))
    child='output/scene-view/1794884325741516800/'
    for name in ('unit.json','result.json','source-sha256.json','scene_view_unit-command.json','scene_view_smoke-command.json','scene_view_unit-engine.log','scene_view_smoke-engine.log','scene_view_unit.log','scene_view_smoke.log'):
        paths.append(('REVIEW',child+name))
    for name in ('scene_view_diagnostic_0ed86dca87e24d778e9be683015de1ad.json','scene_view_smoke_d2e3009fb20f4ffa816db464d6a477e1.json'):
        paths.append(('REVIEW','output/private-desktop/'+name))
    for name in ('tests/scene_view_smoke.gd','tests/scene_view_unit.gd','tests/verify_scene_view.py','src/canvas_view.gd','src/canvas_raster.gd','src/scene_view.gd','src/studio_theme.gd','project.godot','run.py','tools/private_desktop.py','experiments/neon_scene_mask_diagnostic_20261117/scene_view_diagnostic.gd'):
        paths.append(('REVIEW',name))
    for name in ('experiments/neon_scene_mask_diagnostic_20261117/scene_view_diagnostic.gd','experiments/neon_scene_mask_diagnostic_20261117/SOURCE_PROOF.json','experiments/neon_scene_view106_actual_20261117/CANDIDATE_COMMIT.json','experiments/run_neon_scene_followup_20261117.py'):
        paths.append(('MAIN',name))
    # Exact sealed source packet includes its rejected unexecuted encoding draft
    # and historical102/4 scalar. Neither is classified as an additional native job.
    source=MAIN/'experiments/neon_scene_view_mask_fixture_20261117'
    require(sha((source/'INDEX.json').read_bytes())=='7849518bedabab652731a739cec1e5b38cb34e38b01a257c2ca2314a360a120b','Pinned source packet changed')
    paths.extend(('MAIN',p.relative_to(MAIN).as_posix()) for p in source.iterdir() if p.is_file())
    rows=[]; raw={}; bindings={}
    for root,name in sorted(set(paths)):
        path=roots[root]/name
        require(path.suffix in ('.json','.log','.py','.gd','.md','.txt','.godot'),'Nontext input refused')
        before=path.stat();data=path.read_bytes();after=path.stat()
        require((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Input changed during read')
        data.decode('utf-8-sig',errors='strict')
        row={'root':root,'path':name,'bytes':len(data),'sha256':sha(data),'mtime_ns':before.st_mtime_ns}
        rows.append(row);key=root+':'+name;raw[key]=data;bindings[key]=row
    summary=check(raw,bindings,str(REVIEW))
    spec={'format':'has_scene106_closed_text_archive_recipe_1','scope':'EXPLICIT_TWO_COMPLETED_SCENE_FOLDERS_PLUS_DERIVED_CHILD_RECEIPTS_AND_PUBLIC_SOURCE','roots':{k:str(v) for k,v in roots.items()},'inputs':rows,'expected_summary':summary,'tool_provenance':{'kind':'Declared exact preflight pins in archived root followup driver source; not an independent contemporaneous executable attestation','python_sha256':'03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9','powershell_sha256':'2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233','Godot_sha256':'63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf','Godot_log_version':'4.6.stable.official.89cea1439','binary_files_included':False},'limitations':['Diagnostic has source_unchanged assertion and pinned diagnostic source proof, but no complete independent before/after1029 manifest.','Original current filesystem mtimes supplement raw receipt bytes and do not establish process birth or total chronology beyond retained engine log order.','Unit invocation is headless without private desktop receipt; no receipt or job count is fabricated for it.','No canonical full-suite result, merge, native asset or simulation qualification is asserted.'],'active_full_output_read':False}
    with (HERE/'INPUTS.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(spec,stream,indent=2);stream.write('\n')
    print(json.dumps({'inputs':len(rows),'INPUTS_sha256':sha((HERE/'INPUTS.json').read_bytes()),'summary':summary},indent=2))
if __name__=='__main__':main()
