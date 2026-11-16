"""Independent, offline privacy/index/alias/evidence verifier. No runtime/Git.

This implementation imports no assembler code and executes no archived driver.
It admits only an exact path whitelist and refuses arbitrary payload aliases.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import math
import re
import stat

HERE=Path(__file__).resolve().parent
PHASES=('math-parse','math-run','native-parse','native-run')
INVENTORIES=('before','math-parse-before','math-parse-after','math-run-before','math-run-after','post-math','native-parse-before','native-parse-after','native-run-before','native-run-after','after')
PREDECESSORS=('full_receipt','full_catalogue','full_closure','FK_receipt','FK_closure','math_receipt','math_closure','leaf_receipt','leaf_closure','state_receipt','state_closure','state_source','state_result')
ALIASES={
 'leaf_candidate.gd':'14053abf4b00c50909468d41372ce77c826bf0ec0b895bec19418a5961b4fae3',
 'leaf_adapter.gd':'6945153a65741f65f15505a1b840ddbf530c483790824d8a98e90a4d53e539e8',
 'weighted_capture.gd':'1ffecc00666a7e9e6957b7354fd0b862eac07b0f16b79200345370348e91aacb',
 'leaf_harness.gd':'2abbb08831586323878cabb504e5400406144ad34e4b890791539b68633f722c',
 'chain_solver.gd':'01635f84e05abe0ecc998b71117eed9c7afc6f5b15d04e8743cdf1c22efa362f',
 'model_adapter.gd':'38a226db7af1843c1f0df04318aaccc726dc88f7c61b9389f8aa029d52a4fe8c',
 'chain_capture.gd':'b1dc120815f9e56b79ca4406dd3a04ddd5b0978510c6e5ca8234b11ae88ff58b',
 'chain_harness.gd':'d25e37499f8a4b076a65e61a1a97c7ad7fb0d27828f1bd7a2bc76e9f6b0a8b5f',
 'math_checks.gd':'062b182c7b876658ec7b54132ec4d0125170b7506ad7bc469f92e2eb4cf61e32',
 'chain_math_entry.gd':'ee5976876afe2dfbe6738fa47cb26e6bddd06e2182916ef1ffc34663af29ce50',
 'run_chain_owned.py':'297d099ff4bdd2f958e436a7bf403af743dcc1f8e3749fa61b84f253de65b721'}
MAGICS=(b'glTF',b'PK\x03\x04',b'BLENDER',b'RIFF',b'OggS',b'\x89PNG',b'\xff\xd8\xff',b'IDST',b'IDSV',b'IDAG',b'\x7fELF',b'MZ')
PAYLOAD_WORDS={'points','pointarray','pointarrays','mask','masks','privatecapture','privatetip','privateaxis','positions','vertexpositions','vertices','normals','weights','indices','triangles','vertexbuffer','indexbuffer','rest','restmatrices','nativerestmatrices','nativerestwordsuint32','restbyrootid','expectedworldbones','expectednativeztips','blendermatrixlocalrowmajor','boneworlds','boneposes','inversebindmatrices','pcm','pixels','imagedata','audiodata','base64','encodeddata','payloadbytes'}


def demand(ok,message):
    if not ok:raise ValueError(message)


def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def load_bytes(path):
    for parent in (path,*path.parents):
        status=parent.lstat()
        demand(not stat.S_ISLNK(status.st_mode) and not getattr(status,'st_file_attributes',0)&0x400,'Link/reparse file refused')
    status=path.stat();demand(path.is_file() and status.st_size<=16*1024*1024,'Only bounded regular files allowed')
    data=path.read_bytes();after=path.stat()
    demand((status.st_size,status.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Concurrent file mutation refused')
    demand(not data.startswith(MAGICS),'Binary/native/media signature refused')
    demand(b'\x00' not in data,'NUL/binary payload refused')
    data.decode('utf-8')
    return data


def inspect_json(value,location='$'):
    if isinstance(value,dict):
        for key,child in value.items():
            demand(isinstance(key,str),'JSON object key must be text')
            normalized=re.sub(r'[^a-z0-9]','',key.lower())
            # Count/scalar/false metadata is allowed; containers or encoded data
            # under coordinate/media aliases are refused even after renaming.
            demand(not(normalized in PAYLOAD_WORDS and isinstance(child,(list,dict,str)) and len(child)>0),'Private payload alias refused at '+location+'/'+key)
            inspect_json(child,location+'/'+key)
    elif isinstance(value,list):
        is_numeric=bool(value) and all(type(x) in (int,float) for x in value)
        demand(not(is_numeric and len(value) in (3,4,9,12,16) and any(type(x) is float for x in value)),'Unexplained numeric coordinate vector at '+location)
        for number,child in enumerate(value):inspect_json(child,location+'/'+str(number))
    elif isinstance(value,float):demand(math.isfinite(value),'Nonfinite scalar refused')
    elif isinstance(value,str):
        demand(not re.fullmatch(r'[A-Za-z0-9+/=]{512,}',value),'Long encoded payload refused')
    else:demand(value is None or type(value) in (bool,int),'Unsupported JSON scalar')


def whitelist():
    allowed={'assemble.py','scan_packet.py','README.md','BENCHMARK.json','SOURCE_PROOF.json','PRIVACY_REPORT.json','INDEX.json'}
    allowed.update('code/'+name for name in ALIASES)
    allowed.update('source/'+name for name in ('frozen-SOURCE-LOCK.json','frozen-packet-INDEX.json','count-audit.json','count-audit.md','ERRATA.md'))
    allowed.update('predecessors/'+name+'.json' for name in PREDECESSORS)
    allowed.update('actual/'+name for name in ('verification.json','result.json','math-result.json','math-verification.json','authoritative-closure.json','COPY-PROVENANCE.json','CURRENT-SOURCE-LOCK.json','FROZEN-FUNCTIONAL-SOURCE.json','PROVENANCE-DRIFT-ACKNOWLEDGMENT.json'))
    for name in PHASES:
        allowed.update('actual/'+name+suffix for suffix in ('-command.json','-engine.log','-owned-start.json','-process.json','-stderr.log','-stdout.log'))
    for name in INVENTORIES:
        allowed.update('actual/'+name+suffix for suffix in ('-inventory-process.json','-inventory-stdout.log','-inventory-stderr.log','-runtime-closure.json'))
    return allowed


def json_file(name):return json.loads(load_bytes(HERE/name))


def verify_evidence():
    verify=json_file('actual/verification.json');native=json_file('actual/result.json');math_result=json_file('actual/math-result.json');closure=json_file('actual/authoritative-closure.json')
    demand(digest(load_bytes(HERE/'actual/verification.json'))=='d40cf9423a8de7f5cdf73621bcd9b63ca8a3d53062c4c2d80eec029ff88040fc','Reviewed actual verification differs')
    demand(verify['passed'] is True and verify['math_result']==math_result and verify['result']==native and verify['current_full_product_qualified'] is False,'Actual result/scope join differs')
    demand(math_result['checks']==4012 and math_result['failures']==[] and math_result['status']=='PASSED_SYNTHETIC_CHAIN_MATH_ONLY','Actual math result does not qualify')
    demand(native['checks']==21087 and native['failures']==0 and native['dynamic_ticks']==1440 and native['rule_evaluations']==5760 and len(native['cases'])==12,'Native gates/counts differ')
    demand(len(verify['preservation'])==9 and all(x is True for x in verify['preservation'].values()),'Nine preservation gates required')
    demand(closure['verification_sha256']==digest(load_bytes(HERE/'actual/verification.json')) and all(closure[x] is True for x in ('validation_passed','all_retained_children_reaped','owned_runtime_commands_absent','runtime_lease_released','no_process_killed','source_preservation_established')),'Authoritative closure join differs')
    demand([row['phase'] for row in verify['phases']]==list(PHASES),'Four exact phase names required')
    for phase in PHASES:
        process=json_file('actual/'+phase+'-process.json');start=json_file('actual/'+phase+'-owned-start.json');command=json_file('actual/'+phase+'-command.json')
        demand(process==next(row for row in verify['phases'] if row['phase']==phase),'Phase process/verification join differs')
        demand(process['exit']==0 and process['passed'] is True and process['retained_Popen_reaped'] is True and not process['timed_out'] and not process['interrupted'] and not process['owned_child_terminated'] and not process['owned_child_forced_kill'] and process['error_markers']==[],'Actual phase was not clean')
        demand(start['pid']==process['pid'] and start['retained_Popen'] is True and start['command']==command,'Retained Popen/command join differs')
        demand('--headless' in command and '--script' in command and '--audio-driver' in command and command[command.index('--audio-driver')+1]=='Dummy','Headless/Dummy command required')
        for suffix in ('-engine.log','-stdout.log','-stderr.log'):
            text=load_bytes(HERE/('actual/'+phase+suffix)).decode()
            demand(not any(word in text for word in ('ERROR:','WARNING:','SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','resources still in use','Pages in use exist at exit')),'Dirty runtime log refused')
            for line in filter(None,text.splitlines()):
                if re.fullmatch(r'Godot Engine v4\.6\.stable\.official\.[0-9a-f]+ - https://godotengine\.org',line):continue
                expected_prefix='CHAIN_MATH ' if phase=='math-run' else 'NATIVE_TWO_PAIR ' if phase=='native-run' else ''
                demand(expected_prefix and line.startswith(expected_prefix),'Unapproved runtime log payload refused')
                summary=json.loads(line[len(expected_prefix):]);inspect_json(summary)
                demand(summary==({'checks':4012,'passed':True} if phase=='math-run' else {'status':'PASSED_NATIVE_TWO_PAIR_READINESS_ONLY','checks':21087,'failures':0,'cases':12}),'Runtime summary differs')
    for label in INVENTORIES:
        receipt=json_file('actual/'+label+'-runtime-closure.json');process=json_file('actual/'+label+'-inventory-process.json')
        demand(receipt['owned_count']==0 and set(receipt)=={'observed_utc','owned_count'},'Inventory must expose only owned count/time')
        demand(json.loads(load_bytes(HERE/('actual/'+label+'-inventory-stdout.log')))==receipt,'Inventory stdout contains extra/private observations')
        demand(process['exit']==0 and process['retained_Popen_reaped'] and not process['owned_inventory_terminated'] and not process['owned_inventory_killed'],'Inventory child not reaped cleanly')
        demand(load_bytes(HERE/('actual/'+label+'-inventory-stderr.log')).strip()==b'','Inventory stderr must be empty')
    drift=json_file('actual/PROVENANCE-DRIFT-ACKNOWLEDGMENT.json')
    demand(drift['root_acknowledged'] is True and drift['current_full_product_suite_claimed'] is False and drift['current_snapshot_is_historical_full_snapshot'] is False,'Historical full was promoted')
    lock=json_file('actual/CURRENT-SOURCE-LOCK.json');functional=json_file('actual/FROZEN-FUNCTIONAL-SOURCE.json');old=json_file('source/frozen-SOURCE-LOCK.json')
    demand(len(lock['files'])==204 and len(old['files'])==202,'Frozen/current lock scopes differ')
    demand(all(row['sha256']==functional['source_sha256'][row['path']] for row in lock['files']),'Current staged/functional hash joins differ')
    demand(digest(load_bytes(HERE/'source/frozen-packet-INDEX.json'))=='5f204a52d82a61174da1dbb33da3c132f636b5d8bc5eba39f7679279599782c0','Frozen index changed')
    need=json_file('SOURCE_PROOF.json');provenance=json_file('actual/COPY-PROVENANCE.json')
    demand(len(provenance['aliases'])==10 and len(need['exact_actual_code_aliases'])==10 and need['actual_leases_copied'] is False,'Wrong alias or lease domain')
    for key,row in provenance['aliases'].items():
        filename=str(row['path']).replace('\\','/').rsplit('/',1)[-1]
        demand(filename in ALIASES and digest(load_bytes(HERE/('code/'+filename)))==row['sha256']==ALIASES[filename],'Actual alias hash does not join archived code')
    for filename,expected in ALIASES.items():demand(digest(load_bytes(HERE/('code/'+filename)))==expected,'Fixed public code hash differs')
    tree=ast.parse(load_bytes(HERE/'code/run_chain_owned.py').decode())
    entry=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MATH_ENTRY' for t in n.targets))
    demand(entry.encode()==load_bytes(HERE/'code/chain_math_entry.gd'),'Generated math entry differs from frozen driver literal')
    for row in need['raw_copies']:
        demand(row['stored'] in whitelist(),'Copy row outside explicit whitelist')
        raw=load_bytes(HERE/row['stored']);demand(len(raw)==row['bytes'] and digest(raw)==row['sha256'],'Raw copy identity differs')
    # Preserved historical proof bytes join the exact frozen driver's constants.
    constants=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROOFS' for t in n.targets))
    for name,(_source,expected) in constants.items():demand(digest(load_bytes(HERE/('predecessors/'+name+'.json')))==expected,'Predecessor hash differs')
    benchmark=json_file('BENCHMARK.json')
    demand(benchmark['authored_intermediate_native25']['has_retained_jiggle_rule'] is False and benchmark['current_full_product_qualified'] is False,'Native25/current full erratum lost')
    demand(benchmark['math_checks']==4012 and benchmark['native_checks']==21087 and benchmark['actor_ticks']==1440 and benchmark['rule_evaluations']==5760,'Benchmark promotes/shrinks actual scope')


def rejection_selfchecks():
    rejected=0
    for sample in ({'points':[[.1,.2,.3]]},{'Native_Rest_Matrices':[1.,0.,0.]},{'payload_bytes':'A'*800},{'unknown_vector':[.1,.2,.3]},{'weights':[.1,.9]}):
        try:inspect_json(sample)
        except ValueError:rejected+=1
    demand(rejected==5,'Synthetic privacy rejection controls failed')
    return rejected


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write-report',action='store_true');args=parser.parse_args()
    actual={p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()}
    allowed=whitelist();expected=allowed-{'INDEX.json','PRIVACY_REPORT.json'} if args.write_report else allowed
    demand(actual==expected,'Packet has missing or unapproved paths: '+str(sorted(actual^expected)))
    rows=[];json_count=0
    for name in sorted(actual-{'INDEX.json','PRIVACY_REPORT.json'}):
        raw=load_bytes(HERE/name)
        if name.endswith('.json'):inspect_json(json.loads(raw));json_count+=1
        if name.endswith('.py'):ast.parse(raw.decode())
        if name.endswith('.gd'):demand(re.search(r'(?m)^\s*(class_name\b|@tool\b)',raw.decode()) is None,'Global/editor registration refused')
        rows.append({'path':name,'bytes':len(raw),'sha256':digest(raw)})
    verify_evidence()
    negative_controls=rejection_selfchecks()
    manifest=digest(canonical(rows))
    if args.write_report:
        report={'format':'has_independent_chain_packet_privacy_report_1','passed':True,'inspected_payload_files':len(rows),'json_payloads_recursively_scanned':json_count,'strict_whitelist':True,'binary_native_media_or_NUL_payloads':0,'private_coordinate_payloads':0,
                'source_alias_and_generated_entry_joins':11,'actual_math_checks':4012,'actual_native_checks':21087,'all_four_actual_children_reaped_closed':True,'current_full_product_qualification_claimed':False,
                'payload_manifest_sha256':manifest,'synthetic_privacy_rejection_controls_passed':negative_controls,'actual_ROOT_LEASE_or_private_inputs_copied':False,'scanner_imported_assembler_or_executed_driver':False,'runtime_CIM_network_Git_actions':False}
        with (HERE/'PRIVACY_REPORT.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2,allow_nan=False);f.write('\n')
    else:
        report=json_file('PRIVACY_REPORT.json');index=json_file('INDEX.json')
        demand(report['passed'] is True and report['payload_manifest_sha256']==manifest,'Independent privacy report differs')
        expected_index=[]
        for name in sorted(actual-{'INDEX.json'}):
            raw=load_bytes(HERE/name);expected_index.append({'path':name,'bytes':len(raw),'sha256':digest(raw)})
        demand(index['files']==expected_index and index['file_count']==len(expected_index) and index['bytes']==sum(row['bytes'] for row in expected_index),'Final index differs')
    print(json.dumps({'passed':True,'payload_files':len(rows),'recursive_JSON_files':json_count,'source_aliases_verified':11,'privacy_negative_controls':negative_controls,'payload_manifest_sha256':manifest,'INDEX_sha256':digest(load_bytes(HERE/'INDEX.json')) if (HERE/'INDEX.json').exists() else None}))


if __name__=='__main__':main()
