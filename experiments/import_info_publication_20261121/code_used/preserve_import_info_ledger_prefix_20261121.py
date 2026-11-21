from pathlib import Path
import json,subprocess
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'docs/completion_checklist.json'
base=subprocess.check_output(['git','show','c31576d0c1d84030d51ec886f2f3976a60a70c7b:docs/completion_checklist.json'],cwd=ROOT)
old=json.loads(base);current=json.loads(path.read_bytes());key='latest_import_info_increment_20261121'
assert set(current)==set(old)|{key} and all(current[k]==v for k,v in old.items())
newline=b'\r\n' if base.startswith(b'{\r\n') else b'\n';assert base.startswith(b'{'+newline)
entry=json.dumps({key:current[key]},indent=2,ensure_ascii=False).encode();assert entry.startswith(b'{\n') and entry.endswith(b'\n}')
body=entry[2:-2].replace(b'\n',newline)
raw=b'{'+newline+body+b','+newline+base[1+len(newline):]
assert json.loads(raw)==current and raw.endswith(base[1+len(newline):]);path.write_bytes(raw)
print('PASS exact historical ledger byte suffix preserved; only the new progress prefix added')
