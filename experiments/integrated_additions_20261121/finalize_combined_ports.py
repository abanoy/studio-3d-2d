from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(root/'tests'))
changes=[]
for name in ['wind_review_port_files.json','helper_preview_port_files.json']:
    path=root/'tests'/name;doc=json.loads(path.read_bytes())
    for row in doc['files']:
        raw=(root/row['path']).read_bytes();actual=hashlib.sha256(raw).hexdigest()
        if row['path']=='src/world_selection.gd':
            changes.append({'manifest':name,'path':row['path'],'before':row['sha256'],'after':actual})
            row.update(sha256=actual,lf_sha256=hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest())
        else:assert actual==row['sha256'],row['path']
    path.write_bytes((json.dumps(doc,indent=2)+'\n').encode())
import verify_wind_review as wind,verify_helper_preview as helper
assert len(wind.runtime_hashes())==54 and len(helper.validate_port(root))==70
(root/'output/final-caption-port-refresh.json').write_bytes((json.dumps({'status':'PASS','only_caption_leaf_changed':True,'changes':changes},indent=2)+'\n').encode())
print('All54/70 final source pins exact; only corrected caption leaf refreshed.')
