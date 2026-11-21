"""Prepare FBX/OBJ/glTF into the existing self-contained GLB/model contract."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from generic_assets import dependencies,digest,MAX_TOTAL,words,map_parts,local_file


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--asset-root',type=Path);parser.add_argument('--scale',type=float,default=1)
    parser.add_argument('--obj-up',choices=['Y','Z'],default='Y')
    parser.add_argument('--blender',default=os.environ.get('HYBRID_BLENDER',r'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe'))
    parser.add_argument('--status-file',type=Path);parser.add_argument('--cancel-file',type=Path)
    args=parser.parse_args()
    try:
        source=args.source.resolve(strict=True);root=(args.asset_root or source.parent).resolve(strict=True)
        if not .0001<=args.scale<=10000:raise ValueError('Scale must be0.0001–10000')
        if source.suffix.lower()=='.fbx':
            with source.open('rb') as stream:
                if not stream.read(23).startswith(b'Kaydara FBX Binary'):raise ValueError('Blender supports binary FBX here. Export ASCII FBX as binary FBX or glTF first.')
        items=dependencies(source,root)
        if args.cancel_file and args.cancel_file.exists():raise RuntimeError('Import cancelled before staging')
        output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
        for item in items:
            dest=output/'native'/item['relative'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(item['path'],dest)
            if digest(dest)!=item['sha256']:raise RuntimeError('Source changed while staging')
        # Keep original MTL bytes separately; confine the importer's working map
        # paths to staged images, independent of differing OBJ/MTL base-path rules.
        for item in items:
            if Path(item['path']).suffix.lower()!='.mtl':continue
            original=Path(item['path']);saved=output/'original'/item['relative'];saved.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original,saved)
            lines=[]
            for line in original.read_text(encoding='utf-8-sig',errors='replace').splitlines():
                tokens=words(line)
                if tokens and (tokens[0].lower().startswith('map_') or tokens[0].lower() in ('bump','disp','decal','norm')):
                    options,name=map_parts(tokens[1:]);image=local_file(original.parent,name,root)
                    line=' '.join([tokens[0],*options,(output/'native'/image.relative_to(root)).as_posix()])
                lines.append(line)
            (output/'native'/item['relative']).write_text('\n'.join(lines)+'\n',encoding='utf-8')
        request={'source':str(output/'native'/source.relative_to(root)),'original_source':str(source),'asset_root':str(root),
                 'output':str(output),'scale':args.scale,'obj_up':args.obj_up,'dependencies':items,'source_sha256':digest(source)}
        req=output/'conversion-request.json';req.write_text(json.dumps(request),encoding='utf-8')
        env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',BLENDER_USER_CONFIG=str(output/'blender-config'))
        command=[args.blender,'--background','--factory-startup','--disable-autoexec','--offline-mode','--python-exit-code','1','--python',str(Path(__file__).with_name('blender_generic_bridge.py')),'--',str(req)]
        with (output/'conversion.log').open('w',encoding='utf-8') as log:
            process=subprocess.Popen(command,cwd=output,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            (output/'worker.json').write_text(json.dumps({'blender_pid':process.pid}))
            start=time.monotonic()
            try:
                while process.poll() is None:
                    if args.cancel_file and args.cancel_file.exists():raise RuntimeError('Import cancelled; previous scene preserved')
                    if time.monotonic()-start>300:raise RuntimeError('Import timed out after300seconds')
                    time.sleep(.1)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:process.wait(timeout=10)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
        if process.returncode or not (output/'scene.glb').is_file():raise RuntimeError('Conversion failed; see '+str(output/'conversion.log'))
        if (output/'scene.glb').stat().st_size>128*1024*1024:raise ValueError('Prepared GLB exceeds128MiB')
        report=json.loads((output/'parameters.json').read_text(encoding='utf-8'))
        all_items=report['dependencies']
        if len(all_items)>2048 or sum(i['bytes'] for i in all_items)>MAX_TOTAL:raise ValueError('Dependency budget exceeded')
        if any(digest(i['path'])!=i['sha256'] for i in all_items):raise RuntimeError('Original dependency changed during preparation')
        result={'ok':True,'glb':str(output/'scene.glb')}
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:result={'ok':False,'error':str(error)}
    if args.status_file:args.status_file.write_text(json.dumps(result),encoding='utf-8')
    print(json.dumps(result));return 0 if result['ok'] else 1


if __name__=='__main__':raise SystemExit(main())
