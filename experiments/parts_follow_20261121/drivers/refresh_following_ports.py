"""Bind the explicitly reviewed feature/following dependencies, retaining all guards."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tests'))
changes=[]
for driver,manifest,assignment in [('verify_wind_review.py','wind_review_port_files.json','PORT_RUNTIME_FILES'),('verify_helper_preview.py','helper_preview_port_files.json','RUNTIME_FILES')]:
    source=root/'tests'/driver
    old=subprocess.check_output(['git','show','HEAD:tests/'+driver],cwd=root).decode().splitlines()
    new=source.read_text().splitlines()
    # No executable assertions, path policy, native-input checks or process guards change.
    assert [line for line in old if not line.startswith(assignment+' ') and not line.startswith(assignment+'=')]==[line for line in new if not line.startswith(assignment+' ') and not line.startswith(assignment+'=')]
    spec=importlib.util.spec_from_file_location('port_'+assignment,source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    runtime=getattr(module,assignment)
    test=module.PORT_TEST_FILES if assignment=='PORT_RUNTIME_FILES' else module.TEST_FILES
    path=root/'tests'/manifest;doc=json.loads(path.read_bytes());by_name={r['path']:r for r in doc['files']}
    for name in runtime+test:
        if name not in by_name:
            row={'path':name,'category':'runtime' if name in runtime else 'test'}
            doc['files'].append(row);by_name[name]=row
        row=by_name[name];data=(root/name).read_bytes();prior=row.get('sha256')
        row['sha256']=hashlib.sha256(data).hexdigest();row['lf_sha256']=hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()
        if prior!=row['sha256']:changes.append({'manifest':manifest,'path':name,'before':prior,'after':row['sha256']})
    path.write_bytes((json.dumps(doc,indent=2)+'\n').encode())
    proof=module.runtime_hashes() if assignment=='PORT_RUNTIME_FILES' else module.validate_port(root)
    assert len(proof)==(33 if assignment=='PORT_RUNTIME_FILES' else 48)
(root/'output/FOLLOWING_REVIEWED_PORT_CHANGES.json').write_bytes((json.dumps({'status':'EXACT_BINDINGS_PASS','wind_files':33,'helper_files':48,'driver_assertions_unchanged':True,'changes':changes},indent=2)+'\n').encode())
print('Exact reviewed bindings PASS: Wind33/helper48; all other driver lines unchanged')
