import hashlib,importlib.util,json,pathlib,time
root=pathlib.Path(__file__).resolve().parent.parent
p=root/'output/verify_source_carrier_checkpoint_20261120.py'
spec=importlib.util.spec_from_file_location('_root_publication_readers',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert m.git('rev-parse','HEAD').decode().strip()=='5f6a0efba5205f2b1ad4dda73271d968993db4c7'
paths=[v.decode('utf8') for v in m.git('diff','--name-only','-z',m.BASE).split(b'\0') if v]
assert paths and len(set(paths))==len(paths) and all(v.startswith('output/') for v in paths)
rows={}
for name in sorted(paths):
    raw,info=m.read_stable(root/name)
    rows[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'mtime_ns':info.st_mtime_ns}
d={'format':'has_preserved_preexisting_tracked_output_baseline_1','revision':m.BASE,'captured_ns':time.time_ns(),'files':len(rows),'entries':rows,'scope':'Existing tracked output modifications before the carrier publication; excluded from staging and required unchanged at publication.','source_or_application_change_authorized':False}
target=root/'output/source-carrier-preserved-tracked-output-baseline-20261120.json'; assert not target.exists(); raw=(json.dumps(d,sort_keys=True,indent=2)+'\n').encode(); target.write_bytes(raw)
print(json.dumps({'files':len(rows),'output_bytes':sum(v['bytes'] for v in rows.values()),'baseline_bytes':len(raw),'baseline_sha256':hashlib.sha256(raw).hexdigest(),'application_or_native_run':False}))