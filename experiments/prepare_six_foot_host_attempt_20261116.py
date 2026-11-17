"""Retain refused attempt2 and reserve a fresh approved-host attempt3."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'experiments/six_foot_domain_json_actual_20261116/run_owned.py'
assert hashlib.sha256(old.read_bytes()).hexdigest()=='1fc38b721334d57924ad3f69db39c3f65eef4d24f819726fdda35d0689d5f465'
body=old.read_text(encoding='utf-8')
token="FOLDER = ROOT/'output/six-foot-domain-20261116-attempt2'"
assert body.count(token)==1
folder=ROOT/'experiments/six_foot_domain_host_actual_20261116';folder.mkdir(exist_ok=False)
target=folder/'run_owned.py';target.write_text(body.replace(token,"FOLDER = ROOT/'output/six-foot-domain-20261116-attempt3'"),encoding='utf-8',newline='\n')
record={'format':'has_root_six_foot_host_attempt_derivative_1','predecessor_driver_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'new_driver_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'only_source_change':'fresh attempt3 output directory; same original approved closure and all480+21 gates','attempt2_refusal':'CIM unavailable under restricted execution before any engine/source staging','native_execution_performed_by_preparer':False}
(folder/'PREPARATION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record))
