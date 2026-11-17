"""Read/pin exact public scalar evidence; write only the source recipe manifest."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]
NEON=Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
META=['verification.json','before-closure.json','after-closure.json','job.json',
    'app-command.json','app-process.json','app-start.json','app-stderr.log','app-stdout.log','app-engine.log',
    'parse-command.json','parse-process.json','parse-start.json','parse-stderr.log','parse-stdout.log','parse-engine.log']


def main():
    rows=[]
    cases=[]
    def add(root,path,dest,compress=False):
        source=root/path
        assert source.is_file() and not source.is_symlink(),source
        assert source.suffix in {'.json','.log','.gd','.py','.ps1','.md','.patch'}
        rows.append({'root':'main' if root==MAIN else 'neon','path':path,'archive_path':dest+('.gz' if compress else ''),
            'bytes':source.stat().st_size,'sha256':sha(source),'gzip_exact_original':compress})
    full='output/windows-neon-c2d52ff-20261117T000859'
    for name in ['state.json','launch.json','preparation.json','root-birth-observation.json','authoritative-host-closure.json','partial-receipt-inventory.json',
            'canonical.log','coordinator.stderr.log','coordinator.stdout.log','source-before.json','source-after.json']:
        add(NEON,full+'/'+name,'original-full/'+name,name in ['canonical.log','source-before.json','source-after.json'])
    assert sha(NEON/full/'object-timing-original-result.json')=='df40715344819ab69260e7909c8189010e636d8db1447903ffe0b6dc7bb5ec0a'
    add(NEON,full+'/object-timing-original-result.json','original-full/object-timing-original-result.json')
    state=json.loads((NEON/full/'state.json').read_bytes())
    closed=json.loads((NEON/full/'authoritative-host-closure.json').read_bytes())
    receipts=json.loads((NEON/full/'partial-receipt-inventory.json').read_bytes())
    assert state['suite_exit']==1 and state['source_unchanged'] is True and closed['physical_jobs']==24 and closed['all_jobs_and_desktops_closed'] is True
    assert receipts['physical_jobs']==24 and len(receipts['receipts'])==24
    for i,row in enumerate(receipts['receipts']):
        assert sha(NEON/row['path'])==row['sha256']
        add(NEON,row['path'],f'original-full/receipts/{i:02d}-'+Path(row['path']).name)
    # The canonical log is immutable and contains the complete exact 28/2 result and failed predicates.
    canonical=(NEON/full/'canonical.log').read_text(encoding='utf-8',errors='strict')
    assert '"checks":28,"failures":2' in canonical and canonical.count('FAIL last object row click lies inside the visible scrolled track viewport')==1
    cases.append({'name':'original-full','status':'FAILED','checks_in_failed_fixture':28,'fixture_failures':2,'physical_jobs':24,
        'physical_exit0':receipts['physical_exit0'],'physical_cancel_exit2':receipts['Krita_cancel_exit2_pending_exact_phase_join'],
        'closed':True,'closure':'original-full/authoritative-host-closure.json','raw_failure_log':'original-full/canonical.log.gz'})
    for label,folder,expected in [('original-behavior','neon-behavior-original-20261116-attempt1',13),
            ('candidate-v1','neon-behavior-candidate-20261116-attempt1',1),
            ('diagnostic-only','neon-behavior-diagnostic-20261116-attempt1',1),
            ('fixture-v2','neon-behavior-fixture-20261116-attempt1',1),
            ('boundary-v3','neon-behavior-boundary-v3-20261116-attempt1',0)]:
        base='output/'+folder
        for name in META:
            if (NEON/base/name).is_file():add(NEON,base+'/'+name,label+'/'+name)
        add(NEON,base+'/app-result/result.json',label+'/result.json')
        result=json.loads((NEON/base/'app-result/result.json').read_bytes())
        verify=json.loads((NEON/base/'verification.json').read_bytes())
        assert result['checks']==32 and result['failures']==expected and result['complete_assertion_set'] is True
        assert verify['source_unchanged'] is True and verify['receipt']['job_closed'] is True and verify['receipt']['desktop_closed'] is True
        cases.append({'name':label,'checks':32,'failures':expected,'status':'FOCUSED_PASS' if expected==0 else 'FAILED_ASSERTIONS_RETAINED',
            'result_sha256':sha(NEON/base/'app-result/result.json'),'result':label+'/result.json','verification':label+'/verification.json'})
    geometry='output/neon-geometry-20261116-attempt1'
    for name in ['verification.json','before-closure.json','after-closure.json','source-before.json','rail-applied.json']:
        add(NEON,geometry+'/'+name,'geometry/'+name,name=='source-before.json')
    for label,count in [('inset',12384),('compact',14),('rail',45)]:
        for phase in ['parse','app']:
            for suffix in ['command.json','process.json','start.json','stderr.log','stdout.log','engine.log']:
                name=phase+'-'+suffix
                if (NEON/geometry/label/name).is_file():add(NEON,geometry+'/'+label+'/'+name,'geometry/'+label+'/'+name)
        name='result.json' if label=='inset' else 'app-result/result.json'
        add(NEON,geometry+'/'+label+'/'+name,'geometry/'+label+'/result.json')
        result=json.loads((NEON/geometry/label/name).read_bytes())
        assert result['checks']==count and result['failures']==0
        cases.append({'name':'geometry-'+label,'checks':count,'failures':0,'status':'PASSED','result':'geometry/'+label+'/result.json'})
    six='output/six-foot-domain-20261116-attempt3'
    for name in ['verification.json','SOURCE.json','SOURCE-BEFORE.json','SOURCE-AFTER.json','before-closure.json','after-closure.json',
            'before-inventory-stdout.log','before-inventory-stderr.log','after-inventory-stdout.log','after-inventory-stderr.log']:
        add(MAIN,six+'/'+name,'separate-six-foot/'+name,name.startswith('SOURCE'))
    for label,count in [('domain',480),('boundary',21)]:
        for phase in ['parse','run']:
            for suffix in ['command.json','process.json','start.json','stderr.log','stdout.log','engine.log']:
                name=label+'-'+phase+'-'+suffix
                add(MAIN,six+'/'+name,'separate-six-foot/'+name)
        add(MAIN,six+'/Studio/output/'+label+'/result.json','separate-six-foot/'+label+'-result.json')
        result=json.loads((MAIN/six/'Studio/output'/label/'result.json').read_bytes())
        assert result['checks']==count and result['failures']==0
        cases.append({'name':'separate-six-foot-'+label,'checks':count,'failures':0,'status':'PASSED',
            'result':'separate-six-foot/'+label+'-result.json','qualifies_neon_full_suite':False})
    # UI review receipts/labels only. Screenshots themselves are deliberately excluded.
    ui='output/neon-corrected-ui-20261116-attempt1'
    for name in ['verification.json','before-closure.json','after-closure.json','app-command.json','app-process.json','app-start.json','app-stderr.log','app-stdout.log','engine.log']:
        add(NEON,ui+'/'+name,'synthetic-ui/'+name)
    cases.append({'name':'synthetic-ui','status':'AUTOMATED_REVIEW_ONLY','manual_owner_result':'DEFERRED_NO_RESULT','verification':'synthetic-ui/verification.json'})
    aliases=[]
    for packet in ['neon_redesign_review_20261116','neon_redesign_refresh_fixture_20261116','neon_redesign_refresh_boundary_v3_20261116',
            'neon_redesign_geometry_review_20261116','neon_redesign_geometry_successor_20261116','neon_workspace_suite_integration_20261117',
            'six_foot_domain_json_transport_20261116','six_foot_domain_json_actual_20261116']:
        index=MAIN/'experiments'/packet/'INDEX.json'
        if index.is_file():
            path='experiments/'+packet+'/INDEX.json'
            add(MAIN,path,'code-aliases/'+packet+'-INDEX.json')
            aliases.append({'packet':packet,'index_sha256':sha(index),'archive_index':'code-aliases/'+packet+'-INDEX.json'})
    context={name:{'sha256':sha(NEON/name),'bytes':(NEON/name).stat().st_size,
        'lf_sha256':hashlib.sha256((NEON/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()}
        for name in ['src/app.gd','src/pose_editor.gd','src/studio_theme.gd','src/workspace_layout.gd','tests/object_timing_smoke.gd','tests/wind_review_port_files.json']}
    value={'format':'has_neon_actual_archive_recipe_inputs_1','roots':{'main':str(MAIN),'neon':str(NEON)},'files':rows,'cases':cases,
        'code_aliases':aliases,'candidate_context_at_recipe_preparation':context,
        'v3_pending':False,'v3_focused_checks':32,'v3_focused_failures':0,'corrected_full_suite_pending':True,
        'no_art_media_native_arrays_or_projects_selected':True}
    assert len({row['archive_path'] for row in rows})==len(rows)
    (HERE/'INPUTS.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'known_exact_files':len(rows),'cases':len(cases),'uncompressed_bytes':sum(r['bytes'] for r in rows),'input_manifest_sha256':sha(HERE/'INPUTS.json')}))


if __name__=='__main__':main()
