from pathlib import Path
import hashlib,json
OUT=Path(__file__).resolve().parent;source=OUT/'run_part_follow_skeleton66_20261121.py';raw=source.read_bytes()
replacements=[
 (b'import hashlib,json,os,stat,subprocess,time',b'import hashlib,json,os,stat,subprocess,time,sys\nparse_only="--parse-only" in sys.argv'),
 (b'source-character-pose-follow-controller-prep-20261121',b'source-character-pose-follow-controller-v2-prep-20261121'),
 (b'98e123065b42cdccd38e8e5348b27ac6fcc6db50517789786bbf3a7ea0a94963',b'36d195a0bf9cc2a22053e3de53ddd937b9a54562acda64005053c36f01f5afa5'),
 (b"'has-part-follow-skeleton66-'+str(time.time_ns())",b"('has-part-follow-skeleton66-v2-parse-' if parse_only else 'has-part-follow-skeleton66-v2-')+str(time.time_ns())"),
 (b"with (stage/'stdout.log').open('xb') as out",b"if parse_only:argv.insert(argv.index('--script'),'--check-only')\nwith (stage/'stdout.log').open('xb') as out"),
 (b"result={'format':'has_part_follow_skeleton66_root_1'",b"if parse_only:passed=code==0 and preserved and not any(x in logs for x in ('ERROR:','SCRIPT ERROR','FAIL ','ObjectDB instances leaked')) and not any(x.startswith('PASS ') for x in stdout.splitlines())\nresult={'scope':'HEADLESS_PARSE_ONLY_ZERO_ASSERTIONS' if parse_only else 'SYNTHETIC_MODEL_SKELETON66','parse_only':parse_only,'format':'has_part_follow_skeleton66_root_v2_1'")]
for before,after in replacements:
 assert raw.count(before)==1,before;raw=raw.replace(before,after,1)
target=OUT/'run_part_follow_skeleton66_v2_20261121.py';assert not target.exists();target.write_bytes(raw)
compile(raw,str(target),'exec')
print(json.dumps({'status':'DRIVER_PREPARED_NOT_EXECUTED','path':str(target),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}))
