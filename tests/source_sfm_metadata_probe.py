"""Read-only native MDL metadata inspection; no game preflight or mesh conversion."""
from pathlib import Path
import argparse,importlib.util,json,hashlib,os,sys
p=argparse.ArgumentParser(description=__doc__);p.add_argument("--sourceio",type=Path,required=True);p.add_argument("--inventory",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--asset-root",type=Path,required=True);args=p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else None)
if args.output.exists():raise FileExistsError(args.output)
os.environ['NO_BPY']='1'
root=args.sourceio.resolve(strict=True);spec=importlib.util.spec_from_file_location('SourceIO',root/'__init__.py',submodule_search_locations=[str(root)]);module=importlib.util.module_from_spec(spec);sys.modules['SourceIO']=module;spec.loader.exec_module(module)
from SourceIO.library.models.mdl.v49 import MdlV49
from SourceIO.library.utils import MemoryBuffer
inventory=json.loads(args.inventory.read_text());results=[]
for package in inventory:
 folder=Path(package['folder']).resolve(strict=True)
 if not folder.is_relative_to(args.asset_root.resolve(strict=True)):raise ValueError('Sample folder escaped the explicit asset root')
 for model in package['models']:
  path=(folder/model['path']).resolve(strict=True)
  if not path.is_relative_to(folder):raise ValueError('Model escaped its sample folder')
  before=hashlib.sha256(path.read_bytes()).hexdigest();row={'archive':package['archive_name'],'model':model['path'],'sha256':before}
  try:
   mdl=MdlV49.from_buffer(MemoryBuffer(path.read_bytes()));parents=[b.parent_id for b in mdl.bones];valid=all(-1<=p<len(parents) for p in parents)
   for i in range(len(parents)):
    seen=set();current=i
    while current!=-1:
     if current in seen or not 0<=current<len(parents):valid=False;break
     seen.add(current);current=parents[current]
   row.update(bones=len(mdl.bones),valid_hierarchy=valid,materials=len(mdl.materials),material_search_paths=list(mdl.materials_paths),flex_names=len(mdl.flex_names),flex_controllers=len(mdl.flex_controllers),body_parts=len(mdl.body_parts),material_names=[m.name for m in mdl.materials],procedural_bones=sum(b.procedural_rule_type!=0 for b in mdl.bones))
  except Exception as error:row['error']=type(error).__name__+': '+str(error)
  assert hashlib.sha256(path.read_bytes()).hexdigest()==before
  results.append(row)
summary={'models':len(results),'parsed':sum('error'not in r for r in results),'errors':[r for r in results if 'error'in r],'invalid_hierarchies':[r for r in results if r.get('valid_hierarchy') is False],'source_sha256_unchanged':True,'scope':'Read-only pinned SourceIO native MDL49 metadata parser. Not mesh/material conversion, app import, posing, installed-game or rendered fidelity acceptance.'}
args.output.write_text(json.dumps({'summary':summary,'models':results},indent=2));print(json.dumps(summary,indent=2))
