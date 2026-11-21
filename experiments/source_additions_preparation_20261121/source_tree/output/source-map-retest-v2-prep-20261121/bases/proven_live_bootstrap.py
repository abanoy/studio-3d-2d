import hashlib,importlib.util,json,runpy,sys
from pathlib import Path
sys.dont_write_bytecode=True
config=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text(encoding='utf8'))
def pinned(path,count,digest):
    raw=Path(path).read_bytes()
    if len(raw)!=count or hashlib.sha256(raw).hexdigest()!=digest: raise ValueError('LIVE_CHILD_SOURCE_PIN_DIFFERS')
    return raw
worker_path=config['worker']['path']
raw=pinned(worker_path,config['worker']['bytes'],config['worker']['sha256'])
spec=importlib.util.spec_from_file_location('_live_placement_source',worker_path)
W=importlib.util.module_from_spec(spec);sys.modules[spec.name]=W
exec(compile(raw,worker_path,'exec',dont_inherit=True),W.__dict__)
sentinel=pinned(config['sentinel']['path'],config['sentinel']['bytes'],config['sentinel']['sha256'])
pinned(config['candidate']['path'],config['candidate']['bytes'],config['candidate']['sha256'])
placement=None
try:
    with W.placement_sentinel(sentinel.decode('utf8'))() as placement:
        import bpy
        if bpy.app.background is not True or bpy.app.online_access is not False or bpy.context.preferences.filepaths.use_scripts_auto_execute is not False:
            raise ValueError('LIVE_FACTORY_OFFLINE_CONTEXT_REQUIRED')
        sys.path.insert(0,config['tools']);sys.path.insert(0,str(Path(config['candidate']['path']).parent))
        sys.argv=[config['candidate']['path'],'--',config['conversion_request']]
        runpy.run_path(config['candidate']['path'],run_name='__main__')
finally:
    result={'format':'has_live_normal_hidden_placement_1','policy':placement,
            'worker_verified_hidden_sentinel_closed':placement is not None and placement.get('destroyed_in_finally') is True}
    with Path(config['placement']).open('x',encoding='utf8') as stream:json.dump(result,stream,sort_keys=True)
