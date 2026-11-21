from pathlib import Path
import json,time
out=Path(__file__).resolve().parent;text=(out/'run_import_info_metadata163_v2_20261121.py').read_text()
old="[sys.executable,'-I','-S','-B','-u',str(studio/'experiments/reference_body_20261120/test_receipt_provenance.py')]"
new="[sys.executable,'-I','-S','-B','-u','-c',\"import sys,runpy;sys.path.insert(0,sys.argv[1]);sys.argv=[sys.argv[2]];runpy.run_path(sys.argv[0],run_name='__main__')\",str(studio/'experiments/reference_body_20261120'),str(studio/'experiments/reference_body_20261120/test_receipt_provenance.py')]"
assert text.count(old)==1;text=text.replace(old,new).replace('has-import-info-metadata163-v2-','has-import-info-metadata163-v3-').replace("'has_import_info_metadata163_root_v2_1'","'has_import_info_metadata163_root_v3_1'")
target=out/'run_import_info_metadata163_v3_20261121.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
(out/'IMPORT_METADATA_SECOND_STARTUP_REFUSAL_20261121.json').write_text(json.dumps({'status':'TEST_IMPORT_FAILED_ZERO_ASSERTIONS','checks':0,'GPU_jobs':0,'stage':'C:/a/Programming/cloudflare/has-import-info-metadata163-v2-1795268935629484300','tool_result':'0dbe5f exit1','cause':'Root isolated Python removes implicit sibling import path. Exact untouched policy test could not import receipt_provenance.','successor':'Explicit exact owned sibling path in isolated interpreter before running unchanged policy test.','recorded_ns':time.time_ns()},indent=2)+'\n')
print(str(target))
