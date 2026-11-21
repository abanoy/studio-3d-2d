"""Explicit regular-file Node/libuv Windows seal profile and native guard.

Only the historical comparison projects device32 and suffix-inferred execute
bits. The independent native registry retains full device64 and raw mode.
Atime is deliberately excluded: reading an admitted file may advance it.
"""
from pathlib import Path
import os,re,stat

PROFILE='node_libuv_win32_regular_bigint_stat_1'
FIELDS=('dev','ino','nlink','mode','size','mtime_ns')
# This bridge admits inferred execute bits only for the two measured tools.
EXECUTABLE_PATHS=frozenset(('c:/a/tools/godot/godot_v4.6-stable_win64.exe',
                           'c:/program files/python313/python.exe'))

def need(value,label):
    if not value:raise RuntimeError(label)

def native_values(values):
    need(type(values) is tuple and len(values)==6,'NATIVE_SIX_FIELDS')
    need(all(type(x) is int and x>=0 for x in values),'NATIVE_NONNEGATIVE_INTEGERS')
    dev,ino,links,mode,size,mtime=values
    need(dev<2**64 and 0<ino<2**128 and links==1 and size<2**63
         and mode<2**32 and mtime<2**64,'NATIVE_FIELD_BOUNDS')
    need(stat.S_ISREG(mode),'NATIVE_REGULAR_SINGLE_LINK')
    return values

def parse_seal(values):
    need(type(values) in (list,tuple) and len(values)==6,'PRODUCER_SIX_FIELDS')
    need(all(type(x) is str and re.fullmatch(r'0|[1-9][0-9]*',x) for x in values),'PRODUCER_DECIMAL_STRINGS')
    parsed=native_values(tuple(int(x) for x in values))
    need(parsed[0]<2**32 and parsed[3] in (stat.S_IFREG|0o444,stat.S_IFREG|0o666),'PRODUCER_NODE_PROFILE')
    return tuple(values)

def native_identity(path):
    info=Path(path).lstat()
    need(not getattr(info,'st_file_attributes',0)&0x400,'NATIVE_REPARSE_REFUSED')
    return native_values((info.st_dev,info.st_ino,info.st_nlink,info.st_mode,info.st_size,info.st_mtime_ns))

def project(values,path):
    dev,ino,links,mode,size,mtime=native_values(values)
    key=str(Path(path)).replace('\\','/').casefold()
    inferred=0o111 if key in EXECUTABLE_PATHS else 0
    need(mode&0o111==inferred,'UNEXPECTED_NATIVE_EXECUTE_PROFILE')
    base_mode=mode&~0o111
    need(base_mode in (stat.S_IFREG|0o444,stat.S_IFREG|0o666),'UNEXPECTED_NATIVE_PERMISSION_PROFILE')
    return tuple(str(x) for x in (dev&0xffffffff,ino,links,base_mode,size,mtime))

def assert_seal(values,path,expected):
    need(project(values,path)==parse_seal(expected),'SEALED_NODE_PROFILE_IDENTITY')

def same_native(expected,actual):
    need(native_values(expected)==native_values(actual),'FULL_NATIVE_IDENTITY_CHANGED')

class NativeGuard:
    def __init__(self,H):
        need(os.name=='nt','WINDOWS_PRODUCER_PROFILE_ONLY')
        self.H=H;self.original=H.read;self.rows={}
    def read(self,path,*args,**kwargs):
        path=self.H.safe(path);key=str(path);before=native_identity(path)
        if key in self.rows:same_native(self.rows[key],before)
        raw=self.original(path,*args,**kwargs)
        same_native(before,native_identity(path))
        self.rows.setdefault(key,before)
        return raw
    def sealed(self,path,expected):
        path=self.H.safe(path);values=native_identity(path)
        assert_seal(values,path,expected)
        if str(path) in self.rows:same_native(self.rows[str(path)],values)
        return values
    def preserve(self):
        failures=[]
        for key,expected in tuple(self.rows.items()):
            try:same_native(expected,native_identity(self.H.safe(key)))
            except Exception as error:failures.append({'path':key,'error_type':type(error).__name__,'error':str(error)})
        return failures
    def document(self):
        return {'format':'has_full_native_identity_guard_1','producer_profile':PROFILE,
                'fields':list(FIELDS),'atime_excluded':True,
                'full_native_device_and_raw_mode':True,
                'files':{key:[str(x) for x in value] for key,value in sorted(self.rows.items())}}

def install(H):
    guard=NativeGuard(H);H.read=guard.read;return guard

def validate_witnesses(H,guard,folder,protocol,runtimes,used):
    document=H.parse(H.read(folder/'WITNESS_INPUTS.json'))
    need(document.get('format')=='has_root_junko105_native_identity_witness_inputs_1','WITNESS_INPUT_FORMAT')
    need(type(document.get('files')) is list and len(document['files'])==2,'WITNESS_INPUT_COUNT')
    values=[]
    for row,leaf in zip(document['files'],('JUNKO105_PREFLIGHT_IDENTITY_REFUSAL_20261121.json','JUNKO105_NATIVE_EXECUTABLE_STAT_20261121.json')):
        need(row['path']=='output/'+leaf,'WITNESS_EXACT_PATH')
        values.append(H.parse(H.read(H.ROOT/row['path'],row['bytes'],row['sha256'])))
    refusal,executables=values
    need(refusal.get('status')=='PREFLIGHT_REFUSED_ZERO_ASSERTIONS_NO_JOB_CREATED'
         and refusal.get('error')=='SEALED_RUNTIME_IDENTITY' and refusal.get('count')==3327
         and type(refusal.get('differences')) is list and len(refusal['differences'])==3327,'EXACT_ORIGINAL_PREFLIGHT_REFUSAL')
    jobs={job['name']:job for job in protocol['jobs']};seen=set()
    for row in refusal['differences']:
        case=row['case'];name=H.rel(row['path']);key=(case,name)
        need(case in jobs and name in runtimes[case] and key not in seen,'WITNESS_RUNTIME_MEMBERSHIP')
        seen.add(key);path=Path(jobs[case]['studio'])/name
        need(row.get('hash_matches') is True and tuple(row['expected'])==tuple(runtimes[case][name]['identity']),'WITNESS_RUNTIME_SEAL_HASH')
        actual=tuple(int(x) for x in parse_native_strings(row['actual']))
        assert_seal(actual,path,row['expected']);same_native(actual,guard.sealed(path,row['expected']))
    need(seen=={(case,name) for case,rows in runtimes.items() for name in rows},'EXACT3327_WITNESS_CLOSURE')
    need(executables.get('format')=='has_root_native_executable_stat_bridge_witness_1'
         and type(executables.get('rows')) is list and len(executables['rows'])==2,'EXACT_EXECUTABLE_WITNESS')
    by_path={str(Path(row['path'])):row for row in used};seen=set()
    for row in executables['rows']:
        key=str(Path(row['path']));need(key in by_path and key not in seen,'EXECUTABLE_WITNESS_MEMBERSHIP');seen.add(key)
        seal=by_path[key]
        need(row.get('hash_matches') is True and row['sha256']==seal['sha256']
             and tuple(row['recorded_node_identity'])==tuple(seal['identity']),'EXECUTABLE_WITNESS_PIN')
        actual=tuple(int(x) for x in parse_native_strings(row['actual_native_identity']))
        assert_seal(actual,key,seal['identity']);same_native(actual,guard.sealed(key,seal['identity']))
    need(seen==set(by_path),'EXACT_TWO_EXECUTABLE_WITNESS_CLOSURE')
    return {'producer_profile':PROFILE,'runtime_witness_rows':3327,'executable_witness_rows':2,
            'original_seal_rewritten':False,'native64_and_raw_mode_match_Root_witness':True}

def parse_native_strings(values):
    need(type(values) is list and len(values)==6 and all(type(x) is str and re.fullmatch(r'0|[1-9][0-9]*',x) for x in values),'NATIVE_WITNESS_DECIMAL_STRINGS')
    native_values(tuple(int(x) for x in values));return values
