"""Pinned private-root placement bootstrap; no Source/Blender imports at import time."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import sys
sys.dont_write_bytecode=True
WORKER_PIN=(72518,'2c890e5065203473802fd799d21f274eb6d4c8d0c4644d8ecf767b411afd58ea')
SENTINEL_PIN=(17989,'034122697e8fa0e7a855ea42b51eddc351b647ae5f7641cad8d02994a51fc3c3')
ENV_KEYS=frozenset({'PYTHONDONTWRITEBYTECODE','NO_BPY','BLENDER_USER_CONFIG','APPDATA','LOCALAPPDATA','TEMP','TMP'})
def need(ok,code):
    if not ok:raise ValueError(code)
def pinned(role,expected=None):
    need(type(role) is dict and set(role)=={'path','bytes','sha256'},'BOOTSTRAP_PIN_SCHEMA')
    raw=Path(role['path']).read_bytes()
    need(len(raw)==role['bytes'] and hashlib.sha256(raw).hexdigest()==role['sha256'],'BOOTSTRAP_SOURCE_PIN_DIFFERS')
    if expected:need((role['bytes'],role['sha256'])==expected,'BOOTSTRAP_KNOWN_SOURCE_REQUIRED')
    return raw

def load_factory(config):
    # Exact same admitted stdlib-only factory as the proven live bootstrap.
    worker=config['worker'];raw=pinned(worker,WORKER_PIN)
    sentinel=pinned(config['sentinel'],SENTINEL_PIN)
    spec=importlib.util.spec_from_file_location('_map_placement_source',worker['path'])
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    exec(compile(raw,worker['path'],'exec',dont_inherit=True),module.__dict__)
    return module.placement_sentinel(sentinel.decode('utf8'))

def execute(config):
    need(type(config) is dict and set(config)=={'format','worker','sentinel','preparer','args','placement','environment'},'BOOTSTRAP_CONFIG_SCHEMA')
    need(config['format']=='has_map_prepare_hidden_bootstrap_1','BOOTSTRAP_FORMAT')
    need(type(config['args']) is list and 0<len(config['args'])<=64 and all(type(arg) is str and len(arg)<=4096 and '\x00' not in arg for arg in config['args']),'BOOTSTRAP_ARGS')
    environment=config['environment']
    need(type(environment) is dict and set(environment)==ENV_KEYS and all(type(value) is str and len(value)<=4096 and '\x00' not in value for value in environment.values()),'BOOTSTRAP_ENV_SCHEMA')
    need(environment['PYTHONDONTWRITEBYTECODE']=='1' and environment['NO_BPY']=='1','BOOTSTRAP_OWNED_ENVIRONMENT')
    pinned(config['preparer'])
    factory=load_factory(config)
    placement=None
    original_argv=sys.argv
    # Only these seven owned-runtime keys are set in this CHILD process. Parent
    # environment (including present-but-empty GIT_CONFIG_VALUE_*) is untouched.
    for key,value in environment.items():os.environ[key]=value
    try:
        with factory() as placement:
            sys.path.insert(0,str(Path(config['preparer']['path']).parent))
            sys.argv=[config['preparer']['path'],*config['args']]
            runpy.run_path(config['preparer']['path'],run_name='__main__')
    finally:
        sys.argv=original_argv
        result={'format':'has_map_prepare_hidden_placement_1','policy':placement,
                'worker_verified_hidden_sentinel_closed':placement is not None and placement.get('destroyed_in_finally') is True,
                'placement_is_for_root_python_preparer':True,'blender_gui_or_render_claim':False}
        with Path(config['placement']).open('x',encoding='utf8') as stream:json.dump(result,stream,sort_keys=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--config-sha256',required=True);args=parser.parse_args()
    raw=Path(args.config).read_bytes();need(hashlib.sha256(raw).hexdigest()==args.config_sha256,'BOOTSTRAP_CONFIG_PIN')
    execute(json.loads(raw))
if __name__=='__main__':main()
