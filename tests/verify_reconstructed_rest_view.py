"""Focused generated-only, owned headless checks for reconstructed rest meshes."""
from pathlib import Path
import hashlib,json,os,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
import verify_generated_secondary_motion as CPU
from verify_camera_interactions import source_inputs,sources_unchanged
import secondary_reconstruction as R
from test_secondary_helpers import mixed_fixture

def main():
    folder=ROOT/'output'/('reconstructed-rest-view-'+str(time.time_ns()));folder.mkdir();source=folder/'source.glb';g=mixed_fixture(source)
    request={'source_sha256':g.sha,'reviewed':True,'node':3,'primitive':1,'component':0,'segments':3,'reconstruct_weights':True}
    candidate=Path(R.build(source,folder/'Candidate',request)['glb'])
    ancestor_request=dict(request,points_in_anchor=[[0,5,0],[0,4,0],[0,3,0],[0,0,0]])
    ancestor=Path(R.build(source,folder/'Ancestor',ancestor_request)['glb']);protected={p:(CPU.stamp(p.stat()),hashlib.sha256(p.read_bytes()).hexdigest()) for p in (source,candidate,ancestor)}
    frozen=source_inputs();env=dict(os.environ);result={'status':'FAIL','cases':[],'graphics_used':False,'owner_assets_used':False};error=None
    try:
        CPU.case(folder,'unit','tests/reconstructed_rest_view_smoke.gd','RECONSTRUCTED_REST_VIEW ',28,[str(source),str(candidate),str(ancestor)],result['cases'])
        CPU.case(folder,'selection','tests/selection_mesh_view_unit.gd','SELECTION_MESH_VIEW ',8,[],result['cases'])
        result['status']='PASS'
    except BaseException as issue:error=issue;result['error']=str(issue)
    finally:
        result['source_preservation_failures']=sources_unchanged(frozen);result['parent_environment_preserved']=dict(os.environ)==env;result['generated_inputs_preserved']=all((CPU.stamp(p.stat()),hashlib.sha256(p.read_bytes()).hexdigest())==pin for p,pin in protected.items());result['checks']=sum(case.get('checks',0) for case in result['cases'])
        if result['source_preservation_failures'] or not result['parent_environment_preserved'] or not result['generated_inputs_preserved']:result['status']='FAIL'
        (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':result['checks'],'result':str(folder/'verification.json')}))
    if error:raise error
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
