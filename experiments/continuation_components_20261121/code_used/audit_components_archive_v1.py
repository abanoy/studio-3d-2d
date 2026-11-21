"""Reproduce/read-only audit a declared source-only continuation checkpoint.

Run from output with --collect to finish an owned BUILDING archive, or use
--audit --archive PATH after checkout. Does not execute archived programs.
"""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, os, re, stat

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
DEFAULT = ROOT / 'experiments/continuation_sources_20261121'
PACKETS = {
 'source-scenario-d-wire-prep-20261121': '227d1bf5f140ae559495e9654e21de173fcef9829899d3faeef542c52de7db3a',
 'source-character-parts-root-runner-prep-20261121': '3780c38216a755274b0c22a8b48013808d36bf666f0dc6722e8f766b94d9893c',
 'source-character-parts-root-runner-v2-prep-20261121': 'd4a4dcf4efab9182f26373b96294f8f539021e911e19a3baf8c4bc8a2775ce32',
}
TARGETS = ['docs/physics.md', 'docs/scenario_d.md', 'src/first_movie_lesson.gd',
 'tests/height_import_native_smoke.gd', 'tests/first_movie_smoke.gd',
 'tests/scenario_d_smoke.gd', 'tests/scenario_d_wire_unit.gd', 'tests/verify_scenario_d.py']
SOURCES = ['record_import_off_qualification_20261121.py', 'record_followup_docs_20261121.py',
 'record_junko96_partial_20261121.py', 'run_junko105_bridge_controls_20261121.py',
 'prepare_import_off_publication_20261121.py', 'stage_import_off_checkpoint_20261121.py',
 'collect_continuation_root_evidence_20261121.py', 'compare_scenario_d_sample_bits_20261121.py',
 'run_import_off_full_isolated_20261121.py', 'verify_import_off_remote_20261121.py']
PROOFS = ['IMPORT_OFF_FOLLOWUP_QUALIFIED_20261121.json',
 'IMPORT_OFF_FINAL_FUNCTIONAL_CATALOGUE_20261121.json', 'IMPORT_OFF_DOCS_AND_LEDGER_20261121.json',
 'JUNKO105_NATIVE_EXECUTABLE_STAT_20261121.json']
EXT = {'.gd', '.py', '.ps1', '.md', '.txt', '.json', '.log', '.cpp', '.h', '.mjs'}
EXT.update({'.godot','.tscn','.cfg','.bat','.sh','.svg'})
NATIVE_KEYS = {'raw_bones', 'raw_skin', 'raw_source_weights', 'normalized_source_weights',
 'imported_weights', 'inverse_bind_matrices', 'vertex_positions', 'skin_vertices',
 'bone_matrices', 'joint_indices', 'source_slot_ids', 'imported_slot_ids', 'raw_samples',
 'calibration_failure', 'influence_failure'}
README = '''# Continuation source checkpoint, 2026-11-21

This archive preserves exact source packets, compact results, failed attempts,
the programs used to collect/qualify them, and eight current source/doc snapshots.
It contains no owner HAS projects, GLBs, native models, image/audio/movie files,
private collider data, raw pose/skin arrays, executable tools or runtime caches.
The mechanical text/privacy screen supplements an explicit source allowlist; it
does not certify arbitrary source text for every possible confidential string.

The default-off followup has separate scoped PASS receipts: height writer105 /
cold4 / native15, import physics54 on five models, first-movie83+8, and ScenarioD
wire28 / writer30 / cold4. ScenarioD cold-open evaluates all49 canonical stamps
and independently checks all49 physical frames. The original raw text failure
and its measured one-float representation difference are retained. No numeric,
contact, PCM, or final-pixel tolerance was relaxed. The beginner lesson now
explicitly teaches Physics On then Off; import/simulator/parser policy did not
change. These separate scoped runs are not one new aggregate Full.

Current functional source count is1103; canonical Full still has182 groups and
MUST be run on the new revision. Historical435 Full failed an obsolete default-On
height expectation after1961.792s; its113 private jobs were closed and the626 new
UI/camera checks passed within that failed Full. The failure is preserved, not
overwritten by the scoped followup. Formal acceptance remains55/62 and required
implementation52/54; no human/device acceptance is closed here. Historical435
Miku/native-face/easing hosts remain pinned to their old source and must refuse
an advanced Main until explicitly ported; source/API GO is not execution proof.

Junko split-parts remains a source prototype, not an adopted/native-aligned
feature. Root runner v1 refused before any Job/Godot/assertion because Node and
Python reported different Windows device/mode conventions. Version2 retains the
original seals and independently checks full native identities. Its32 synthetic
bridge controls passed. Its105-case run then passed58 domain +38 real headless
World/editor checks (96 total), but refused the reader-copy input types BEFORE
launching the nine-check fresh reader. Both attempted jobs closed/reaped,4526
native identities were preserved, and the lock was removed. This is partial
96 PASS / run FAIL, not105 PASS. Six-model alignment, posed bone-following and
physical GUI input remain unqualified. No later retry is implied at this cutoff.

Restore each `source/<packet>/` directory byte-for-byte to `output/<packet>/` in
an appropriate checkout. Preserve its SOURCE_PINS closure and historical bases;
do not flatten folders or reinterpret authored/unrun status as current adoption.
`root-source/` files restore to `output/`; `root-evidence/` is retained evidence.
`current-targets/` is an exact eight-file snapshot, not an instruction to overwrite
another revision. The separate benchmark snapshot records Junko's partial run.
Runtime hosts require their declared tools, private inputs, revision/catalogue
and ownership checks; this archive does not distribute those inputs or tools.

CONTENTS.json lists every regular payload (excluding itself), original source
where known, byte length and SHA256. Run the copied collector with `--audit
--archive <this directory>` for read-only membership/hash/closure/privacy checks.
To reproduce collection, first run the two retained collection scripts in a
checkout containing the pinned original output packets, then this collector
from output with `--collect`. All historical failures and frozen bytes remain
unchanged. The BUILDING marker is removed only after successful final auditing.
'''

def digest(raw): return hashlib.sha256(raw).hexdigest()
def need(ok, why):
    if not ok: raise RuntimeError(why)
def rel(name):
    p = PurePosixPath(name)
    need(type(name) is str and not p.is_absolute() and p.parts, 'relative path')
    for part in p.parts:
        need(part not in ('.', '..') and not any(c in part for c in '\\:<>"|?*') and
             part == part.rstrip(' .') and not re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\..*)?', part), 'path alias')
    need(p.as_posix() == name, 'noncanonical relative path')
    return Path(*p.parts)
def ident(s): return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_mode, s.st_nlink)
def read(p):
    s = p.lstat()
    need(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and not getattr(s, 'st_file_attributes', 0) & 0x400, 'not plain single-link file: '+str(p))
    raw = p.read_bytes(); need(ident(s) == ident(p.lstat()), 'read identity changed')
    return raw
def load(raw):
    def pairs(items):
        d = {}
        for k,v in items:
            need(k not in d, 'duplicate JSON key'); d[k]=v
        return d
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(RuntimeError('nonfinite JSON')))
def files(base):
    seen=set(); result=[]
    def error(e): raise e
    for here, dirs, names in os.walk(base, followlinks=False, onerror=error):
        for n in dirs+names:
            p=Path(here)/n; s=p.lstat()
            need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400, 'reparse/link path')
            name=p.relative_to(base).as_posix(); rel(name)
            need(name.casefold() not in seen, 'case alias'); seen.add(name.casefold())
        for n in names: result.append(Path(here)/n)
    return sorted(result)
def privacy(name, raw):
    need(Path(name).suffix.lower() in EXT or Path(name).name=='project.godot', 'binary/native extension: '+name)
    text=raw.decode('utf-8-sig'); need('\0' not in text, 'NUL binary')
    need(not re.search(r'data:[^\s\"\']{0,90};base64,[A-Za-z0-9+/=]{256,}',text), 'embedded binary')
    if name.endswith('.json'):
        def walk(v):
            if isinstance(v,dict):
                for k,x in v.items():
                    need(not(k in NATIVE_KEYS and isinstance(x,(dict,list)) and x), 'private native array key: '+name+' / '+k)
                    walk(x)
            elif isinstance(v,list):
                need(not(len(v)>512 and all(type(x) in (int,float) for x in v)), 'large native numeric array: '+name)
                for x in v: walk(x)
        walk(load(raw))
def audit(base, building=False):
    raw=read(base/'CONTENTS.json'); inv=load(raw); rows=inv['files']
    expected={r['path'] for r in rows};need(len(expected)==len(rows),'duplicate inventory')
    actual={p.relative_to(base).as_posix() for p in files(base)}-{'CONTENTS.json'}
    if building: actual.discard('BUILDING.json')
    need(expected==actual, 'exact membership mismatch')
    total=0; manifests=0
    for row in rows:
        p=base/rel(row['path']);data=read(p); privacy(row['path'],data)
        need(len(data)==row['bytes'] and digest(data)==row['sha256'], 'payload pin: '+row['path']);total+=len(data)
        if p.name=='SOURCE_PINS.json':
            manifests+=1; m=load(data); declared=m['files']; names=set()
            for r in declared:
                name=r['path'];rel(name);need(name.casefold() not in names,'manifest alias');names.add(name.casefold())
                b=read(p.parent/rel(name));need(len(b)==r['bytes'] and digest(b)==r['sha256'],'inner pin')
            inner={q.relative_to(p.parent).as_posix() for q in files(p.parent)}-{'SOURCE_PINS.json'}
            need(inner=={r['path'] for r in declared},'inner exact closure: '+str(p))
    need(inv['payload_files']==len(rows) and inv['payload_bytes']==total,'inventory totals')
    need(read(base/'CONTENTS.json')==raw,'inventory changed')
    return {'status':'PASS','payload_files':len(rows),'payload_bytes':total,'files_including_inventory':len(rows)+1,
      'source_pins_closures':manifests,'contents_bytes':len(raw),'contents_sha256':digest(raw),
      'membership_hashes_regular_text_alias_and_native_array_checks':True,'Full_1103_run_claimed':False}
def collect(base):
    need((base/'BUILDING.json').is_file(),'requires owned BUILDING marker')
    origins={}
    for receipt, key in [('CONTINUATION_ARCHIVE_COLLECTION_20261121.json','paths'),('CONTINUATION_ROOT_EVIDENCE_COLLECTION_20261121.json','files')]:
        for row in load(read(OUT/receipt))[key]:
            raw=read(base/rel(row['path']));need(len(raw)==row['bytes'] and digest(raw)==row['sha256'],'prior copy changed')
            origins[row['path']]= 'output/'+row['path'][7:] if row['path'].startswith('source/') else row['path']
    def copy(p,name,source=None):
        raw=read(p);privacy(name,raw);t=base/rel(name);t.parent.mkdir(parents=True,exist_ok=True)
        if t.exists(): need(read(t)==raw,'existing differs: '+name)
        else:
            with t.open('xb') as stream: need(stream.write(raw)==len(raw),'short write')
        need(read(p)==raw and read(t)==raw,'copy changed');origins[name]=source or str(p)
    for name,pin in PACKETS.items():
        source=OUT/name; raw=read(source/'SOURCE_PINS.json');need(digest(raw)==pin,'packet manifest')
        for row in load(raw)['files']:
            p=source/rel(row['path']); data=read(p);need(len(data)==row['bytes'] and digest(data)==row['sha256'],'packet source pin')
            copy(p,'source/'+name+'/'+row['path'],'output/'+name+'/'+row['path'])
        copy(source/'SOURCE_PINS.json','source/'+name+'/SOURCE_PINS.json','output/'+name+'/SOURCE_PINS.json')
    for name in SOURCES: copy(OUT/name,'root-source/'+name,'output/'+name)
    for name in PROOFS: copy(OUT/name,'root-evidence/'+name,'output/'+name)
    catalogue=load(read(OUT/'IMPORT_OFF_FINAL_FUNCTIONAL_CATALOGUE_20261121.json'));need(len(catalogue)==1103,'current functional domain')
    for name in TARGETS:
        raw=read(ROOT/name)
        if name in catalogue: need(len(raw)==catalogue[name]['bytes'] and digest(raw)==catalogue[name]['sha256'],'current catalogue target')
        copy(ROOT/name,'current-targets/'+name,name)
    name='docs/benchmarks/character_parts_headless_2026-11-21.json';copy(ROOT/name,'current-targets/'+name,name)
    run=ROOT.parent/'has-character-parts-headless-435-1795255808748/RootRun-1795259996694407600'
    copy(run/'PUBLIC_RESULT.json','root-evidence/results/junko96-partial.json',str(run/'PUBLIC_RESULT.json'))
    for case in ('unit','controls'):
        for n in ('CASE_RESULT.json','OWNERSHIP.json','godot-stdout.log','godot-stderr.log','wrapper-stdout.log','wrapper-stderr.log'):
            copy(run/'jobs'/case/n,'root-evidence/junko96/'+case+'/'+n)
    bridge=OUT/'junko105-bridge-controls-1795259982688930700'
    for n in ('RESULT.json','stdout.log','stderr.log'): copy(bridge/n,'root-evidence/junko-bridge32/'+n)
    copy(Path(__file__),'code_used/finalize_continuation_archive_20261121.py','output/finalize_continuation_archive_20261121.py')
    readme=base/'README.md'
    if readme.exists(): need(read(readme)==README.encode(),'README differs')
    else: readme.write_bytes(README.encode())
    origins['README.md']='generated source-only cutoff description'
    rows=[]
    for p in files(base):
        name=p.relative_to(base).as_posix()
        if name in ('BUILDING.json','CONTENTS.json'):continue
        raw=read(p);privacy(name,raw)
        rows.append({'path':name,'source':origins.get(name,'preserved pre-existing declared source/evidence'), 'bytes':len(raw),'sha256':digest(raw)})
    value={'format':'has_continuation_source_archive_1','functional_source_count':1103,'canonical_Full_groups':182,
      'new_Full_status':'NOT_RUN_REQUIRED','native_inputs_art_and_binaries_copied':False,
      'junko_status_at_cutoff':'BRIDGE32_PASS;DOMAIN58_EDITOR38_PASS;RUN_FAIL_READER_COPY_REFUSED_BEFORE_LAUNCH',
      'payload_files':len(rows),'payload_bytes':sum(r['bytes'] for r in rows),'files':rows}
    contents=base/'CONTENTS.json';need(not contents.exists(),'never replace frozen inventory')
    contents.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    result=audit(base,True)
    marker=base/'BUILDING.json';need(marker.resolve().parent==base.resolve() and stat.S_ISREG(marker.lstat().st_mode),'marker boundary')
    marker.unlink()
    need(audit(base)==result,'final audit changed')
    return result
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,default=DEFAULT)
    g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--collect',action='store_true');g.add_argument('--audit',action='store_true')
    args=ap.parse_args();print(json.dumps(collect(args.archive) if args.collect else audit(args.archive),indent=2))
