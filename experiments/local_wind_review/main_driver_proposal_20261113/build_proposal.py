"""Build output-only proposed files. Does not run Godot, workers, or GPU work."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PACKET = ROOT / 'experiments/local_wind_review/production_port_candidate_20261112'
DEST = OUT / 'proposed/tests'
DEST.mkdir(parents=True, exist_ok=True)

common = (PACKET / 'overlay/tests/wind_review_gpu_common.gd').read_text(encoding='utf-8')
original = common
needle = '\tfolder=request.folder\n\troot.size=Vector2i(1800,1100)'
replacement = '''\tfolder=request.folder
\tvar actual:=ProjectSettings.globalize_path("res://").replace("\\\\","/").simplify_path().trim_suffix("/")
\tvar expected:=str(request.get("project_root","")).replace("\\\\","/").simplify_path().trim_suffix("/")
\tmetrics["project_root"]=actual
\tcheck(not expected.is_empty() and (actual.to_lower()==expected.to_lower() if OS.get_name()=="Windows" else actual==expected),"the actual res root is the requested main checkout")
\tvar initial_layout:=ProjectSettings.globalize_path("res://output/test-preferences/workspace-%d.json" % OS.get_process_id())
\tmetrics["fresh_startup_workspace"]=not FileAccess.file_exists(initial_layout)
\tcheck(metrics.fresh_startup_workspace,"startup cannot reuse an earlier process workspace")
\troot.size=Vector2i(1800,1100)'''
assert common.count(needle) == 1
common = common.replace(needle, replacement)
needle = '\troot.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false\n\tapp.has_project.cache_root=folder.path_join(label+"-cache");app.workspace_layout.path=folder.path_join(label+"-layout.json")'
replacement = '\troot.add_child(app)\n\tapp.has_project.cache_root=folder.path_join(label+"-cache");app.workspace_layout.path=folder.path_join(label+"-layout.json")\n\tawait settled();app.home.hide();app.autosave_enabled.button_pressed=false'
assert common.count(needle) == 1
common = common.replace(needle, replacement)
(DEST / 'wind_review_gpu_common.gd').write_text(common, encoding='utf-8', newline='\n')
(OUT / 'common-adaptation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), common.splitlines(True), fromfile='a/tests/wind_review_gpu_common.gd', tofile='b/tests/wind_review_gpu_common.gd')), encoding='utf-8')

reference = (PACKET / 'reference/verify_gpu_prototype.py').read_text(encoding='utf-8')
tree = ast.parse(reference)
pieces = {node.name: ast.get_source_segment(reference, node) for node in tree.body if isinstance(node, ast.FunctionDef)}
stage = pieces['stage_native'].replace('STUDIO', 'ROOT').replace("SOURCES['backhair'][1]", "WIND_REVIEW_PINS['backhair']['source']")
stage = stage.replace("len(after.springs())==2 and after.binary==before.binary", "len(after.springs())==2 and after.springs()[:1]==before.springs() and after.binary==before.binary")

header = '''"""Exact main-project Wind Review verification; choose the mode explicitly.

Install under this checkout's tests directory with the companion fixture resolver
append and reviewed port-file manifest. Graphical mode requires the coordinator's
released single lease. No visible fallback or partial-native acceptance.
"""
from pathlib import Path
import argparse, array, hashlib, importlib.util, json, math, os, shutil, stat, subprocess, sys, time, wave
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from native_fixture_plans import wind_review_native_plans, WIND_REVIEW_PINS

SCRIPTS = ['tests/wind_review_gpu_common.gd', 'tests/wind_review_gpu_motion.gd', 'tests/wind_review_gpu_lifecycle.gd', 'tests/wind_review_gpu_primary.gd']
UNITS = [('tests/wind_review_unit.gd', 'WIND_REVIEW_UNIT', 51), ('tests/wind_review_hooks_unit.gd', 'WIND_REVIEW_HOOKS_UNIT', 14), ('tests/wind_review_review_unit.gd', 'WIND_REVIEW_AUDIT_UNIT', 29)]
# The original830 assertions are unchanged; two root/startup checks per job add12.
COUNTS = {'procedural':62, 'vrm0':47, 'vrm1':47, 'backhair':49, 'lifecycle':546, 'primary':91}
ERRORS = ['ERROR:', 'SCRIPT ERROR', 'SHADER ERROR', 'FAIL ', 'ObjectDB instances leaked', 'unclaimed string names', 'Object was freed while a signal is being emitted', '_set_transient_exclusive_child', 'Pages in use exist at exit']
ALLOW_EOL = False

def require(ok, message):
    if not ok: raise RuntimeError(message)

def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()

def identity(path):
    info = Path(path).stat()
    return {'sha256':sha(path), 'bytes':info.st_size, 'mtime_ns':info.st_mtime_ns}

def guard(path, boundary):
    path, boundary = Path(path).absolute(), Path(boundary).absolute()
    require('..' not in path.parts and path != boundary and path.resolve().is_relative_to(boundary.resolve()), 'Path escapes fresh owned output: '+str(path))
    for part in (path, *path.parents):
        if part.exists():
            info = part.lstat()
            require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400, 'Link/reparse output refused: '+str(part))
        if part == boundary: break
    return path

def write_json(path, value):
    guard(path, ROOT/'output'/'wind-review')
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\\n',encoding='utf-8')

def revision():
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()

def source_manifest():
    names = [p for part in ('src','tests','tools','data','examples') for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts]
    names += [ROOT/name for name in ('run.py','project.godot','main.tscn','launch.pyw','dependencies.json')]
    return {p.relative_to(ROOT).as_posix():identity(p) for p in sorted(set(names))}

def runtime_hashes():
    proof = json.loads((ROOT/'tests/wind_review_port_files.json').read_bytes())
    require(proof['format']=='has_wind_review_main_port_files_1' and len(proof['files'])==16,'Wrong reviewed port source manifest')
    result = {}
    for row in proof['files']:
        name=row['path']; path=ROOT/name; data=path.read_bytes(); actual=hashlib.sha256(data).hexdigest()
        exact=actual==row['sha256']
        require(exact or ALLOW_EOL and hashlib.sha256(data.replace(b'\\r\\n',b'\\n')).hexdigest()==row['lf_sha256'], 'Unreviewed main port bytes: '+name)
        result[name]={'sha256':actual,'reviewed_sha256':row['sha256'],'reconstruction':'exact bytes' if exact else 'explicit --allow-checkout-eol; CRLF-to-LF only'}
    return result

def runner():
    path=ROOT/'run.py'; spec=importlib.util.spec_from_file_location('wind_review_main_run',path)
    run=importlib.util.module_from_spec(spec); spec.loader.exec_module(run)
    require(run.ROOT.resolve()==ROOT.resolve() and Path(run.__file__).resolve()==path.resolve(),'Runner did not bind this main checkout')
    return run

def checked_command(run,script,target,headless=False,extra=()):
    args=run.command(script,headless=headless,extra=list(extra))
    require(args.count('--path')==1 and Path(args[args.index('--path')+1]).resolve()==ROOT.resolve(),'Command --path differs from actual main')
    if not headless:
        require(os.name=='nt' and len(args)>3 and Path(args[1]).resolve()==(ROOT/'tools/private_desktop.py').resolve() and args.count('--receipt')==1,'No approved private Windows desktop; visible fallback refused')
        args[args.index('--receipt')+1]=str(target/'private-receipt.json')
    return args

def invoke(args,target,timeout):
    write_json(target/'command.json',args)
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
    try:
        process=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
        output=process.stdout+process.stderr; code=process.returncode
    except subprocess.TimeoutExpired as error:
        def as_text(value): return value.decode('utf-8','replace') if isinstance(value,bytes) else value or ''
        output=as_text(error.stdout)+as_text(error.stderr)+'\\nERROR: Wind verifier process timeout\\n';code=124
    (target/'process.log').write_text(output,encoding='utf-8')
    engine=target/'engine.log'
    combined=output+('\\n'+engine.read_text(encoding='utf-8',errors='replace') if engine.is_file() else '')
    return code,output,[marker for marker in ERRORS if marker in combined]

def headless_checks(folder,run):
    rows=[]
    for script,marker,count in UNITS:
        target=folder/Path(script).stem;target.mkdir()
        args=checked_command(run,script,target,True,['--log-file',str(target/'engine.log')])
        code,text,errors=invoke(args,target,120)
        lines=[line[len(marker)+1:] for line in text.splitlines() if line.startswith(marker+' ')]
        result=json.loads(lines[-1]) if lines else {}
        ok=code==0 and not errors and result.get('checks')==count and result.get('failures')==0
        row={'script':script,'exit':code,'result':result,'error_markers':errors,'passed':ok};rows.append(row)
        write_json(folder/'headless-verification.json',rows)
        require(ok,'Headless unit failed; inspect '+str(target))
    return rows

def parse_checks(folder,run):
    rows=[]
    for script in ['src/app.gd',*SCRIPTS]:
        target=folder/(Path(script).stem+'-parse');target.mkdir()
        args=checked_command(run,script,target,True,['--check-only','--log-file',str(target/'engine.log')])
        code,text,errors=invoke(args,target,60)
        row={'script':script,'exit':code,'error_markers':errors,'gpu':False,'passed':code==0 and not errors};rows.append(row)
        write_json(folder/'parse-verification.json',rows)
        require(row['passed'],'Syntax preparation failed; inspect '+str(target))
    return rows

def verify_originals(plan):
    if plan is None:return True
    return identity(plan['manifest'])==plan['manifest_identity'] and all(identity(row['source'])==row['source_identity'] and identity(row['parameters'])==row['parameters_identity'] for row in plan['inputs'].values())
'''

gpu = '''
def execute_gpu(folder,run,inputs):
    staged=stage_native(folder,inputs);tone=folder/'known-tone.wav';audio(tone)
    jobs=[('procedural',SCRIPTS[1],{}),('vrm0',SCRIPTS[1],staged['vrm0']),('vrm1',SCRIPTS[1],staged['vrm1']),('backhair',SCRIPTS[1],staged['backhair']),('lifecycle',SCRIPTS[2],{}),('primary',SCRIPTS[3],{**staged['vrm1'],'raise_y':2.5})]
    rows=[]
    for name,script,data in jobs:
        target=folder/name;target.mkdir()
        request={'mode':name,'folder':str(target).replace('\\\\','/'),'audio':str(tone).replace('\\\\','/'),'project_root':str(ROOT).replace('\\\\','/'),**data}
        request_path=target/'request.json';write_json(request_path,request)
        args=checked_command(run,script,target,False,['--audio-driver','Dummy','--log-file',str(target/'engine.log'),'--',str(request_path)])
        code,text,errors=invoke(args,target,330)
        result=json.loads((target/'result.json').read_bytes()) if (target/'result.json').is_file() else {}
        receipt_path=target/'private-receipt.json'
        receipt=json.loads(receipt_path.read_bytes()) if receipt_path.is_file() else {}
        clean=receipt.get('exit')==0 and receipt.get('child_desktop_confirmed') is True and receipt.get('foreground_child_observed') is False and receipt.get('job_closed') is True and receipt.get('desktop_closed') is True
        actual=result.get('metrics',{}).get('project_root','')
        correct_root=bool(actual) and Path(actual).resolve()==ROOT.resolve()
        ok=code==0 and not errors and clean and correct_root and result.get('mode')==name and result.get('checks')==COUNTS[name] and result.get('failures')==0 and result.get('metrics',{}).get('fresh_startup_workspace') is True
        row={'mode':name,'script':script,'exit':code,'checks':result.get('checks'),'failures':result.get('failures'),'project_root':actual,'correct_main_root':correct_root,'private_receipt':str(receipt_path),'clean_isolation':clean,'error_markers':errors,'passed':ok}
        write_json(target/'verification.json',row);rows.append(row);write_json(folder/'execution-progress.json',rows)
        print(('PASS ' if ok else 'FAIL ')+name,flush=True)
        if not ok:break
    return rows

def main():
    global ALLOW_EOL
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['headless','prepare','graphical'],required=True)
    parser.add_argument('--lease-confirmed',action='store_true')
    parser.add_argument('--allow-checkout-eol',action='store_true')
    parser.add_argument('--inputs-manifest',type=Path)
    options=parser.parse_args();ALLOW_EOL=options.allow_checkout_eol
    require((ROOT/'project.godot').is_file(),'Install proposed driver under the actual main tests directory first')
    require(options.mode!='graphical' or os.name=='nt' and options.lease_confirmed,'Graphical mode needs Windows and the coordinator released lease')
    family=ROOT/'output'/'wind-review';guard(family,ROOT/'output');family.mkdir(exist_ok=True)
    folder=guard(family/(options.mode+'-'+str(time.time_ns())),family);folder.mkdir(exist_ok=False)
    before_sources=source_manifest();before_revision=revision();before_inputs=None;bindings={};units=[];parses=[];results=[];error=''
    write_json(folder/'source-before.json',before_sources)
    try:
        bindings=runtime_hashes();run=runner()
        if options.mode in ('headless','graphical'):units=headless_checks(folder,run)
        if options.mode in ('prepare','graphical'):parses=parse_checks(folder,run)
        if options.mode=='graphical':
            before_inputs=wind_review_native_plans(options.inputs_manifest)
            write_json(folder/'native-originals-before.json',before_inputs)
            results=execute_gpu(folder,run,before_inputs['inputs'])
    except Exception as failure:
        error=type(failure).__name__+': '+str(failure)
    finally:
        if (folder/'execution-progress.json').is_file():results=json.loads((folder/'execution-progress.json').read_bytes())
        after_sources=source_manifest();after_revision=revision()
        try:inputs_unchanged=verify_originals(before_inputs)
        except Exception as failure:inputs_unchanged=False;error=error or str(failure)
        complete=options.mode!='graphical' or len(results)==6 and all(row['passed'] for row in results)
        passed=not error and bool(bindings) and complete and before_sources==after_sources and before_revision==after_revision and inputs_unchanged
        attempted=any((folder/name/'command.json').is_file() for name in COUNTS)
        observed=any(isinstance(row.get('checks'),int) and row['checks']>0 for row in results)
        report={'format':'has_wind_review_main_1','mode':options.mode,'passed':passed,'error':error,'folder':str(folder),'project_root':str(ROOT),'revision_before':before_revision,'revision_after':after_revision,'reviewed_port_bindings':bindings,'headless':units,'parse':parses,'results':results,'all_functional_sources_hash_size_mtime_unchanged':before_sources==after_sources,'native_inputs_checked':before_inputs is not None,'native_prepared_inputs_unchanged':inputs_unchanged if before_inputs is not None else None,'gpu_requested':options.mode=='graphical','graphical_process_attempted':attempted,'gpu_used':True if observed else None if attempted else False,'private_art_uploaded':False,'historical_gpu_checks':830,'expected_main_gpu_checks_with_root_startup_guards':842,'scope':'Phase1: temporary preview of already declared groups; original830 checks plus12 explicit main-root/startup guards. PNG export, in-memory recovery sink, original-only start/cancel recording; no movie or persisted recovery-worker claim. Pending helper-before-Apply, permanent exclusions, native jiggle/assembly, artist/device/installation acceptance remain open.'}
        write_json(folder/'source-after.json',after_sources);write_json(folder/'verification.json',report)
    print('WIND_REVIEW_MAIN '+json.dumps({'folder':str(folder),'verification':str(folder/'verification.json'),'mode':options.mode,'passed':passed,'gpu_used':report['gpu_used']}),flush=True)
    return 0 if passed else 1

if __name__=='__main__':raise SystemExit(main())
'''
driver = header + '\n' + pieces['audio'] + '\n\n' + stage + '\n' + gpu
ast.parse(driver)
(DEST / 'verify_wind_review.py').write_text(driver, encoding='utf-8', newline='\n')

manifest=json.loads((PACKET/'manifest.json').read_bytes())
files=[]
for row in manifest['overlay_files']:
    name=row['path']
    data=(DEST/'wind_review_gpu_common.gd').read_bytes() if name=='tests/wind_review_gpu_common.gd' else (PACKET/row['candidate_path']).read_bytes()
    files.append({'path':name,'sha256':hashlib.sha256(data).hexdigest(),'lf_sha256':hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest(),'category':row['category']})
(DEST/'wind_review_port_files.json').write_text(json.dumps({'format':'has_wind_review_main_port_files_1','source_packet':'experiments/local_wind_review/production_port_candidate_20261112','files':files},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'proposal':str(DEST),'driver_ast':True,'original_case_assertions_retained':True,'common_added_checks':2,'reviewed_files':len(files)}))
