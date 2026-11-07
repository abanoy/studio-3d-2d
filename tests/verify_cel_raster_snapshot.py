"""Headless cold-raster staging checks; optional owned 32-cel measurement fixtures."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--benchmark',choices=['sparse','noise','all'])
    options=parser.parse_args()
    folder=(options.output or ROOT/'output/cel-raster-snapshot'/str(time.time_ns())).resolve()
    folder.mkdir(parents=True,exist_ok=False)
    reports={}
    def run(script,label,marker,extra=()):
        target=folder/label;target.mkdir()
        args=command(script,headless=True,extra=['--log-file',str(target/'engine.log'),'--',str(target),*extra])
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        log=result.stdout+result.stderr;(target/'run.log').write_text(log,encoding='utf-8')
        assert result.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        report=json.loads(next(s[len(marker):] for s in log.splitlines() if s.startswith(marker)))
        assert report.get('failures',0)==0 and report.get('ok',True)
        reports[label]=report
    run('tests/cel_raster_snapshot_unit.gd','unit','CEL_RASTER_SNAPSHOT_UNIT ')
    run('tests/cel_raster_policy_unit.gd','policy','CEL_RASTER_POLICY_UNIT ')
    run('tests/cel_raster_adaptive_unit.gd','adaptive','CEL_RASTER_ADAPTIVE_UNIT ')
    run('tests/cel_raster_save_unit.gd','save','CEL_RASTER_SAVE_UNIT ')
    run('tests/cel_raster_read_unit.gd','read','CEL_RASTER_READ_UNIT ')
    run('tests/drawing_overlay_cache_unit.gd','overlay-regression','DRAWING_OVERLAY_CACHE_UNIT ')
    run('tests/cel_raster_metadata_unit.gd','metadata','CEL_RASTER_METADATA_UNIT ')
    run('tests/cel_raster_owner_unit.gd','owner','CEL_RASTER_OWNER_UNIT ')
    run('tests/cel_raster_reader_unit.gd','reader-regression','CEL_RASTER_READER_UNIT ')
    for kind in ['sparse','noise']:
        if options.benchmark in [kind,'all']:
            run('tests/cel_raster_snapshot_benchmark.gd',kind,'CEL_RASTER_SNAPSHOT_BENCHMARK ',['--noise'] if kind=='noise' else [])
    proof={'scope':'Opt-in cold raster staging foundation only; live cel storage remains eager. No app/Undo/GPU acceptance claim.','reports':reports,'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['tests/cel_raster_policy_unit.gd','tests/cel_raster_adaptive_unit.gd','src/storage.gd','src/fill_editor.gd','src/drawing_selection_editor.gd','src/drawing_transform_editor.gd','src/cel_clipboard.gd','tests/cel_raster_save_unit.gd','src/app.gd','src/renderer.gd','src/color_sampler.gd','src/onion_editor.gd','src/sequence_runtime.gd','src/tutorials.gd','src/drawing_overlay_cache.gd','tests/cel_raster_read_unit.gd','src/cel_timing_editor.gd','src/cel_patch.gd','src/recovery.gd','src/layer_editor.gd','src/sequence_editor.gd','tests/cel_raster_metadata_unit.gd','src/drawing.gd','src/cel_raster_owner.gd','tests/cel_raster_owner_unit.gd','src/cel_raster_reader.gd','src/cel_raster_snapshot.gd','src/cel_raster_snapshot_cache.gd','tests/cel_raster_snapshot_unit.gd','tests/cel_raster_snapshot_benchmark.gd']}}
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
    print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
