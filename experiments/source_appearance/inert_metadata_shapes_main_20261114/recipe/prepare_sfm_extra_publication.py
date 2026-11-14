from pathlib import Path
import gzip,hashlib,json,shutil
root=Path(__file__).resolve().parents[1]
launch=root/'output/sfm-extra-native-launch-20261114T013526736'
run=launch/'run'
target=root/'output/sfm-extra-main-publication-20261114-v2'
assert not target.exists()
target.mkdir()
aliases=[]
def retain(source,relative):
 assert source.is_file() and source.suffix.lower() in {'.json','.log','.txt','.py','.ps1','.md'}
 raw=source.read_bytes(); dest=target/relative
 if len(raw)>65536:
  dest=Path(str(dest)+'.gz'); encoded=gzip.compress(raw,mtime=0);assert gzip.decompress(encoded)==raw
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(encoded)
  aliases.append({'source':str(source.relative_to(root)),'stored':dest.relative_to(target).as_posix(),'original_bytes':len(raw),'original_sha256':hashlib.sha256(raw).hexdigest()})
 else:
  dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
for source in sorted(run.iterdir()):
 if source.is_file() and source.suffix.lower() in {'.json','.log','.txt'}:retain(source,'native/'+source.name)
for folder in [run/'writer',*sorted((run/'readers').iterdir())]:
 for source in sorted(folder.iterdir()):
  if source.is_file() and source.suffix.lower() in {'.json','.log','.txt'}:
   retain(source,'native/'+source.relative_to(run).as_posix())
for folder in sorted((run/'cases').iterdir()):
 for source in sorted(folder.iterdir()):
  if source.is_file() and source.suffix.lower() in {'.json','.log','.txt'}:retain(source,'native/'+source.relative_to(run).as_posix())
 for source in sorted((folder/'conversion-metadata').iterdir()):
  if source.is_file() and source.suffix.lower() in {'.json','.log','.txt'}:retain(source,'native/'+source.relative_to(run).as_posix())
receipts=list((run/'Studio/output/private-desktop').glob('*.json'))
assert len(receipts)==5
for source in receipts:retain(source,'private-receipts/'+source.name)
for source in sorted(launch.iterdir()):
 if source.is_file():retain(source,'coordinator/'+source.name)
for name in ['prepare_sfm_extra_manifest.py','start_sfm_extra_native_owned.ps1','close_sfm_extra_native_owned.ps1','check_sfm_extra_actual_reports.py','check_sfm_extra_baselines.py','prepare_sfm_extra_publication.py']:
 retain(root/'output'/name,'recipe/'+name)
retain(root/'output/sfm-extra-native-inputs-20261114.json','input-manifest-original.json')
shutil.copytree(root/'output/sfm-inert-cpu-publication-20261114',target/'cpu')
(target/'GZIP_ROUNDTRIP.json').write_text(json.dumps({'format':'has_metadata_lossless_gzip_1','files':aliases},indent=2)+'\n',encoding='utf-8')
(target/'README.md').write_text('''# Completed import cleanup, inactive jiggle retention and ordinary native shape controls

This packet contains scoped source/test metadata and lossless logs only. Actual four-model app run passes117writer+124reader static checks plus154 separately named feature checks (96shape,58jiggle), four fresh readers/eight packed+linked opens and one48-frame1080p24H264/AAC movie. All4136source/hash/size/timestamp/HEAD entries and eight preservation gates match, five private jobs close. Keiki Tools and three Mima controls are authored through attached Amount/Apply UI, linear middle geometry, Undo/Redo/reset, imported-default Off, protected peers and exact cold-frame12 pixels. Junko retains49inactive rules, independently joined to1421float32 values:67269compactmetadata bytes and137044actual nested report bytes. Native runtime binding/simulation is not implemented. Nitori no-rule report and three derived GLBs match earlier actual baselines, allowing only the explicitly new input-alias field in the report. The historical no-rule validator in cpu/ predates this bridge. Earlier count-wrapper failure and explicit resource symlink skip remain recorded. Complete default verification of this new increment is next; prior full9f covers the previous static increment. Native artwork/mesh/HAS/image/audio/video/runtime binaries remain local; no original Source shader/controller/artist fidelity is inferred.
''',encoding='utf-8')
rows=[{'path':p.relative_to(target).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(target.rglob('*')) if p.is_file()]
(target/'INDEX.json').write_text(json.dumps({'format':'has_metadata_source_packet_index_1','files':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'packet':str(target),'files':len(rows),'bytes':sum(r['bytes'] for r in rows),'index_sha256':hashlib.sha256((target/'INDEX.json').read_bytes()).hexdigest(),'lossless_gzip':len(aliases)}))
