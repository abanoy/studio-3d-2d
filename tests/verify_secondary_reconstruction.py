"""Focused owned reconstruction checks. Optional native inputs remain private."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT))
import secondary_reconstruction as R
import verify_generated_secondary_motion as CPU
import verify_import_capability as V

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path);p.add_argument('--region',type=int,nargs=3);p.add_argument('--gui',action='store_true');p.add_argument('--gui-only',action='store_true');p.add_argument('--advanced',action='store_true');o=p.parse_args()
    V.need(bool(o.source)==bool(o.region),'Source and explicit reviewed region must be supplied together');V.need(not o.gui_only or o.gui,'GUI-only must explicitly select GUI');V.need(not o.gui or o.source is not None,'Protected native GUI scope requires source')
    folder=ROOT/'output'/('secondary-reconstruction-'+str(time.time_ns()));folder.mkdir();result={'status':'FAIL','cases':[],'whole_back_hair_complete':False};primary=None;env=dict(os.environ);frozen,blobs=V.source_blobs();protected=None;runtime=None
    try:
        if not o.gui_only:
            process=subprocess.run([sys.executable,'-I','-S','-B',str(ROOT/'tests/test_secondary_reconstruction.py'),'-v'],cwd=ROOT,capture_output=True,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            (folder/'unit-stdout.log').write_bytes(process.stdout);(folder/'unit-stderr.log').write_bytes(process.stderr)
            V.need(process.returncode==0 and b'Ran 11 tests' in process.stderr and b'\nOK' in process.stderr,'Eleven pure reconstruction controls required');result['pure_checks']=11
        if o.source:
            source=o.source.resolve(strict=True);protected=(CPU.stamp(source.stat()),hashlib.sha256(V.read(source)).hexdigest());g=R.H.GLB(source)
            if o.gui:V.need(o.region==[131,1,2] and g.sha=='a329cd47bd74b05278a6e501b9503d8e0b9231bf6adc647307d573170166a3ec','This optional UI fixture requires the protected Junko first-component source')
            recipe={'format':R.FORMAT,'source_sha256':g.sha,'reviewed':True,'regions':[dict(zip(('node','primitive','component'),o.region))],'segments':4}
            (folder/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n');plan=R.prepare(source,recipe);candidate=R.build(source,folder/'Candidate',recipe)
            item,data,selected,_=plan['views'][0];spec={'source_vertices':len(data[4]),'reviewed_vertices':len(selected),'positions':data[4],'selected_vertices':selected,'expected_chains':len(plan['anchors']),'expected_guide_bones':len(plan['anchors'])*5}
            spec_path=folder/'PRIVATE_VERTEX_SPEC.json';spec_path.write_text(json.dumps(spec))
            if not o.gui_only:CPU.case(folder,'native','tests/secondary_reconstruction_native_smoke.gd','SECONDARY_RECONSTRUCTION_NATIVE ',12,[candidate['glb'],str(spec_path),str(source)],result['cases'])
            if o.gui:
                (folder/'Cases').mkdir();runtime=V.studio(folder,'Studio',blobs)
                flags=[str(source)]+(['--advanced'] if o.advanced else [])
                V.run_case(folder,'gui',runtime,'tests/secondary_reconstruction_controls_smoke.gd','SECONDARY_RECONSTRUCTION_CONTROLS ',19,flags,False,result,None)
            V.need(protected==(CPU.stamp(source.stat()),hashlib.sha256(V.read(source)).hexdigest()),'Protected original changed')
        result['status']='PASS'
    except BaseException as error:primary=error;result['error']=str(error)
    finally:
        result['checks']=result.get('pure_checks',0)+sum(row.get('checks',0) for row in result['cases']);result['source_preservation_failures']=V.sources_unchanged(frozen);result['parent_environment_preserved']=dict(os.environ)==env
        result['runtime_preserved']=runtime is None or all(V.read(runtime/name)==raw for name,raw in blobs.items());result['protected_source_preserved']=protected is None or protected==(CPU.stamp(o.source.resolve().stat()),hashlib.sha256(V.read(o.source.resolve())).hexdigest())
        if result['source_preservation_failures'] or not result['runtime_preserved'] or not result['parent_environment_preserved'] or not result['protected_source_preserved']:result['status']='FAIL'
        (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':result['checks'],'result':str(folder/'verification.json')}))
    if primary:raise primary
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
