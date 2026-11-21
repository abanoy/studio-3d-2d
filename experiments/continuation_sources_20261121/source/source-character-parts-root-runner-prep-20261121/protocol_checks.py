"""Strict historical105-input admission, owned reader handoff and log checks."""
from pathlib import Path
import hashlib,json,os,re,stat
KIT_MANIFEST=(2493,'0a9489d5bf7c2ab398549a7e2e8e3f1f25f8c70e508b152ef04e44418e4fd0fe')
PROTOCOL_PIN=(8816,'57acb0e3c9f90bc126bb0ab20b9ed8a8f6da601e793993181863ff60dc777b63')
BAD=re.compile(r'SCRIPT ERROR|SHADER ERROR|FAIL |ObjectDB instances leaked|_set_transient_exclusive_child|^ERROR:',re.M)
MAX_LOG=8*1024*1024

def need(ok,label):
    if not ok:raise RuntimeError(label)
def identity(path):
    s=path.lstat();return tuple(str(x) for x in (s.st_dev,s.st_ino,s.st_nlink,s.st_mode,s.st_size,s.st_mtime_ns))
def tree(H,root,max_entries=50000):
    root=H.safe(root);need(root.is_dir(),'INPUT_TREE_REQUIRED')
    result={};folded=set();visited=0
    def error(value):raise value
    for folder,dirs,files in os.walk(root,followlinks=False,onerror=error):
        for item in dirs+files:
            visited+=1;need(visited<=max_entries,'BOUNDED_TREE_ENTRIES')
            path=H.safe(Path(folder)/item);name=path.relative_to(root).as_posix();H.rel(name)
            need(name.casefold() not in folded,'INPUT_CASE_ALIAS');folded.add(name.casefold())
            if path.is_dir():continue
            s=path.lstat();need(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'INPUT_REGULAR_SINGLE_LINK')
            result[name]=path
    return result

def pin_table(H,document):
    need(type(document) is list,'MANIFEST_FILES_ARRAY');rows={}
    for row in document:
        need(type(row) is dict,'MANIFEST_ROW');name=H.rel(row['path'])
        need(name not in rows and type(row.get('bytes')) is int and row['bytes']>=0
             and re.fullmatch('[0-9a-f]{64}',row.get('sha256','')) is not None,'MANIFEST_PIN')
        rows[name]=row
    need(len({x.casefold() for x in rows})==len(rows),'MANIFEST_CASE_ALIAS')
    return rows

def source_manifest(H,folder,pin):
    raw=H.read(folder/'SOURCE_PINS.json',*pin);doc=H.parse(raw);rows=pin_table(H,doc['files'])
    need(set(tree(H,folder))==set(rows)|{'SOURCE_PINS.json'},'EXACT_FROZEN_SOURCE_CLOSURE')
    for name,row in rows.items():H.read(folder/name,row['bytes'],row['sha256'])
    return doc

def admit(H,kit):
    source_manifest(H,kit,KIT_MANIFEST)
    protocol=H.parse(H.read(kit/'PROTOCOL.json',*PROTOCOL_PIN))
    need(protocol.get('expected_total_checks')==105 and len(protocol.get('jobs',[]))==3,'EXACT105_PROTOCOL')
    stage=H.safe(Path(protocol['stage']));need(stage.parent==H.ROOT.parent and stage.name=='has-character-parts-headless-435-1795255808748','EXACT_OWNED_SEALED_STAGE')
    # Stage metadata must match the separately frozen protocol-kit copies exactly.
    for leaf in ('BASELINE_SOURCE1102.json','MAIN_AT_SEAL.json','PROTOCOL.json','RUNTIME_BEFORE.json','SOURCE_SNAPSHOT.json','USED_RUNTIME_PINS.json'):
        expected=H.read(kit/leaf);H.read(stage/leaf,len(expected),H.sha(expected))
    candidate_pin=H.read(kit/'CANDIDATE_SOURCE_PINS.json')
    source_manifest(H,H.ROOT/'output/source-character-parts-editor-prep-20261121',(len(candidate_pin),H.sha(candidate_pin)))
    baseline=H.parse(H.read(kit/'BASELINE_SOURCE1102.json'))['files']
    need(len(baseline)==1102,'EXACT_HISTORICAL_BASE1102')
    base_paths=tree(H,stage/'Base1102');need(set(base_paths)==set(baseline),'EXACT_BASE1102_MEMBERSHIP')
    for name,row in baseline.items():
        raw=H.read(base_paths[name],row['bytes'],row['sha256'])
        need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_sha1'],'BASE_GIT_BLOB_BYTES')
    targets=H.parse(H.read(kit/'CANDIDATE_TARGETS.json'))['targets'];need(len(targets)==8,'EXACT_EIGHT_TARGETS')
    expected={name:{'bytes':row['bytes'],'sha256':row['sha256']} for name,row in baseline.items()}
    for row in targets:
        name=H.rel(row['path'])
        if row['operation']=='replace':need(expected.get(name)=={'bytes':row['base_bytes'],'sha256':row['base_sha256']},'TARGET_BASE')
        else:need(row['operation']=='new' and name not in expected,'TARGET_NEW_COLLISION')
        expected[name]={'bytes':row['bytes'],'sha256':row['sha256']}
    snapshot=H.parse(H.read(kit/'SOURCE_SNAPSHOT.json'));need(len(expected)==1108 and set(snapshot['files'])==set(expected),'EXACT1108_COMPOSITION')
    for name,row in expected.items():need(all(snapshot['files'][name][key]==value for key,value in row.items()),'SNAPSHOT_TARGET_BYTES')
    runtimes=H.parse(H.read(kit/'RUNTIME_BEFORE.json'))['files'];profiles=set();count=0
    scripts=('character_parts_unit.gd','character_parts_editor_smoke.gd','character_parts_reader.gd')
    for index,job in enumerate(protocol['jobs']):
        need(job['name']==('unit','controls','reader')[index] and job['expected_checks']==(58,38,9)[index],'EXACT_CASE_ORDER_COUNTS')
        studio=H.safe(Path(job['studio']));need(studio==stage/job['name']/'Studio' and Path(job['cwd'])==studio,'EXACT_STUDIO_CWD')
        args=job['args'];need(args[0]=='C:/a/tools/Godot/Godot_v4.6-stable_win64.exe' and args.count('--headless')==1
             and '--editor' not in args and '--import' not in args and args[args.index('--path')+1]==job['studio']
             and args[args.index('--script')+1]=='res://tests/'+scripts[index],'EXACT_HEADLESS_SCRIPT_ARGV')
        need(job['profile'] not in profiles,'DISTINCT_PROFILES');profiles.add(job['profile'])
        if index:need(args[-2:]==[job['casefolder'],job['profile']],'SCRIPT_CASE_AND_PROFILE_ARGS')
        need(Path(job['casefolder'])==studio/'output/case','OWNED_CASE_FOLDER')
        need(not Path(job['casefolder']).exists() and not Path(args[args.index('--log-file')+1]).exists(),'FRESH_CASE_AND_ENGINE_LOG')
        rows=runtimes[job['name']];need(set(rows)==set(expected)|{'override.cfg'},'EXACT1109_RUNTIME_SEAL')
        need(set(tree(H,studio))==set(rows),'EXACT_UNEXECUTED_RUNTIME_MEMBERSHIP')
        for name,row in rows.items():
            path=studio/H.rel(name);need(identity(path)==tuple(row['identity']),'SEALED_RUNTIME_IDENTITY')
            H.read(path,row['bytes'],row['sha256']);count+=1
            if name!='override.cfg':need({key:row[key] for key in ('bytes','sha256')}==expected[name],'RUNTIME_COMPOSITION_BYTES')
        override=H.read(studio/'override.cfg').decode();need(json.dumps(job['profile']) in override,'EXACT_CUSTOM_PROFILE')
    need(count==3327,'EXACT3327_RUNTIME_INPUTS')
    used=H.parse(H.read(kit/'USED_RUNTIME_PINS.json'))['used_executables'];need(len(used)==2,'EXACT_TWO_EXECUTABLES')
    for row in used:
        path=H.safe(Path(row['path']));need(identity(path)==tuple(row['identity']),'USED_EXECUTABLE_IDENTITY')
        H.read(path,row['bytes'],row['sha256'],limit=1024*1024*1024)
    return protocol,baseline,expected,runtimes,used

def preserve_runtime_membership(H,protocol,expected):
    for job in protocol['jobs']:
        names=set(tree(H,Path(job['studio'])))
        need(set(expected)|{'override.cfg'}<=names,'RUNTIME_SOURCE_DISAPPEARED')
        extras=names-(set(expected)|{'override.cfg'})
        need(all(name.startswith(('output/','.godot/')) for name in extras),'UNEXPECTED_SOURCE_OR_ROOT_WRITE')

def copy_reader(H,protocol,record):
    writer=protocol['jobs'][1];reader=protocol['jobs'][2]
    source=H.safe(Path(writer['casefolder']));target=Path(reader['casefolder'])
    need(source.is_dir() and not target.exists(),'FRESH_READER_HANDOFF')
    selected={}
    for name,path in tree(H,source/'snapshot',max_entries=128).items():selected['snapshot/'+name]=path
    selected['expected-world.json']=H.safe(source/'expected-world.json')
    need(1<len(selected)<=64,'BOUNDED_READER_FILES')
    total=0;blobs={}
    for name,path in selected.items():
        need(path.suffix.lower() in ('.json','.glb'),'ONLY_SYNTHETIC_PROJECT_INPUT_TYPES')
        raw=H.read(path,limit=64*1024*1024);total+=len(raw);need(total<=64*1024*1024,'READER_BYTE_BUDGET')
        blobs[name]=raw
    parent=Path(reader['studio'])/'output'
    if not parent.exists():H.safe(parent,missing=True);parent.mkdir()
    H.safe(target,missing=True);target.mkdir(exist_ok=False)
    copies=[]
    for name,raw in blobs.items():
        destination=target/H.rel(name);destination.parent.mkdir(parents=True,exist_ok=True);H.new(destination,raw)
        copies.append({'path':name,'bytes':len(raw),'sha256':H.sha(raw),'source_identity':identity(selected[name]),'copy_identity':identity(destination)})
    need(set(tree(H,target))==set(selected),'EXACT_READER_HANDOFF_MEMBERSHIP')
    H.json_new(record/'READER_INPUTS.json',{'files':copies,'source':str(source),'target':str(target),'total_bytes':total})
    return target,set(selected)

def validate_logs(H,job,record):
    stdout=H.read(record/'godot-stdout.log',limit=MAX_LOG).decode('utf-8','replace')
    stderr=H.read(record/'godot-stderr.log',limit=MAX_LOG).decode('utf-8','replace')
    engine=H.read(Path(job['args'][job['args'].index('--log-file')+1]),limit=MAX_LOG).decode('utf-8','replace')
    need(not BAD.search(stdout+'\n'+stderr+'\n'+engine),'ENGINE_ASSERTION_OR_LEAK')
    marker=job['expected_marker'];hits=[line[len(marker):] for line in stdout.splitlines() if line.startswith(marker)]
    need(len(hits)==1,'EXACT_ONE_MARKER');value=H.parse(hits[0]);count=job['expected_checks']
    need(type(value.get('checks')) is int and value['checks']==count and type(value.get('failures')) is int and value['failures']==0,'EXACT_CASE_COUNT')
    need(sum(line.startswith('PASS ') for line in stdout.splitlines())==count,'EXACT_PASS_LINE_COUNT')
    if job['name']!='unit':
        leaf='result.json' if job['name']=='controls' else 'reader-result.json'
        need(H.parse(H.read(Path(job['casefolder'])/leaf,limit=1024*1024))==value,'SAVED_RESULT_EQUALS_MARKER')
        need(value.get('synthetic_only') is True and value.get('bone_following_qualified') is False,'SYNTHETIC_SCOPE')
        if job['name']=='controls':need(value.get('headless_controls') is True and value.get('native_pixels_or_input_qualified') is False
                                       and value.get('actual_six_MDL_conversion_or_alignment_qualified') is False,'CONTROL_SCOPE')
        else:need(value.get('actual_six_MDL_alignment_qualified') is False,'READER_SCOPE')
    return value
