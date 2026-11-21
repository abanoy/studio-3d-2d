"""Version collector source; preserves v1 and does not collect/finalize an archive."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[1]
src=R/'output/collect_after_c315_continuation_20261121.py'
raw=src.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='b894fd19c0beed8c289b0a956959728ab2185e27d715cf2186fbb5575da9875f'
text=raw.decode()
text=text.replace('AFTER_C315_COLLECTION_ALLOWLIST_DRAFT_V1_20261121','AFTER_C315_COLLECTION_ALLOWLIST_DRAFT_V2_20261121')
anchor=" 'source-import-info-full-receipts-prep-20261121':'a460d911b587e17251fa4bade39ec11a3b44f6b5ee47fe2ad31bf9b6fc1c3bdb',\n"
assert text.count(anchor)==1
manifest=R/'output/source-prepared-map-editor-import-info-v2-prep-20261121/SOURCE_PINS.json'
map_sha=hashlib.sha256(manifest.read_bytes()).hexdigest()
text=text.replace(anchor,anchor+" 'source-import-info-missing-texture-v3-prep-20261121':'57db4f1a5d8ee9951f51716deba0de1cdd2130cd6a3345de0697ef3c3afabcf3',\n"+f" 'source-prepared-map-editor-import-info-v2-prep-20261121':'{map_sha}',\n")
anchor="or (path.name=='PRIVATE_REFERENCE.json' and raw==read(ROOT/'output/source-character-pose-follow-prep-20261121/PRIVATE_REFERENCE.json')),path"
assert text.count(anchor)==1
text=text.replace(anchor,"or (path.name=='PRIVATE_REFERENCE.json' and raw==read(ROOT/'output/source-character-pose-follow-prep-20261121/PRIVATE_REFERENCE.json')) or (path.name=='PRIVATE_INPUT_REFERENCE.json' and raw==read(ROOT/'output/source-prepared-map-editor-prep-20261121/PRIVATE_INPUT_REFERENCE.json')),path")
anchor="    names=set();saved=[]\n"
assert text.count(anchor)==1
text=text.replace(anchor,"""    # Recheck exact top-level source closure on EVERY audit/copy, not only at
    # initial allowlist preparation. An extra later file must refuse the claim.
    for packet in value['packets']:
        folder=ROOT/'output'/packet['path'];manifest=read(folder/'SOURCE_PINS.json')
        assert digest(manifest)==packet['manifest_sha256']
        declared=json.loads(manifest)['files'];wanted={'SOURCE_PINS.json'}
        for item in declared:
            rel(item['path']);assert item['path'] not in wanted;wanted.add(item['path'])
            blob=read(folder/rel(item['path']))
            assert len(blob)==item['bytes'] and digest(blob)==item['sha256']
        assert len(wanted)==packet['files'] and len({p.casefold() for p in wanted})==len(wanted)
        assert {p.relative_to(folder).as_posix() for p in tree_files(folder)}==wanted
    names=set();saved=[]
""")
text=text.replace('Pending coordinator/owner53/map-info64 successors and actual results require a new versioned allowlist after closure; this cutoff does not imply completeness.','Source coordinator and map-info64 successors plus MMDv3 included; their later actual results and owner53/MMD combined failure require successor explicit receipts after closure; this cutoff does not imply completeness.')
dst=R/'output/collect_after_c315_continuation_v2_20261121.py';assert not dst.exists()
dst.write_text(text,encoding='utf-8')
print(dst)
