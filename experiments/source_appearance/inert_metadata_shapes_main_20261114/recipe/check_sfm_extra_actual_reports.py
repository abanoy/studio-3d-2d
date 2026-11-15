from pathlib import Path
import importlib.util,json
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('native_join',root/'tests/verify_source_jiggle_native_report.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
run=root/'output/sfm-extra-native-launch-20261114T013526736/run'
rows=[]
for pattern,count in [('03-*',49),('04-*',0)]:
 bundle=next((run/'cases').glob(pattern))/'conversion-metadata'
 d=m.verify((bundle/'conversion-request.json').resolve(),(bundle/'parameters.json').resolve(),count)
 target=run/('independent-jiggle-'+str(count)+'.json')
 assert not target.exists()
 target.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
 rows.append(d)
report=json.loads((run/'verification.json').read_bytes())
summary={'actual_joins':rows,'source_files':len(report['source_before']['files']),
         'writer_checks':report['writer']['result']['checks'],
         'reader_checks':sum(x['result']['checks'] for x in report['readers']),
         'named_writer':len(report['named_checks']['writer']),
         'named_readers':sum(len(x) for x in report['named_checks']['readers']),
         'private_jobs':1+len(report['readers']),
         'preserved':report['preservation'],'passed':report['passed']}
(run/'root-extra-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary))
