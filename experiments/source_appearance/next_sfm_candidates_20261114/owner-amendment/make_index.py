from pathlib import Path
import hashlib,json
BASE=Path(__file__).resolve().parent
def stamp(path):
 data=Path(path).read_bytes();return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
summary=json.loads((BASE/'SUMMARY.json').read_bytes())
assert summary['Godot_parse']=='UNRUN' and summary['actual_checks'] is None
for name,row in summary['source'].items():assert stamp(BASE/'source'/name)==row
index={'format':'has_metadata_source_packet_index_1','files':[{'path':p.relative_to(BASE).as_posix(),**stamp(p)} for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='INDEX.json']}
assert not any('__pycache__' in x['path'] or x['path'].endswith('.pyc') for x in index['files'])
(BASE/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'folder':str(BASE),'files':len(index['files']),'bytes':sum(x['bytes'] for x in index['files']),'index_sha256':stamp(BASE/'INDEX.json')['sha256'],'source':summary['source'],'execution':'UNRUN'},indent=2))
