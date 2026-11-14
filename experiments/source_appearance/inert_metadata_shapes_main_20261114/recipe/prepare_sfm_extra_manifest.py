from pathlib import Path
import hashlib, json, sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root/'tools'))
from source_mdl_choices import catalogue
base = root/'output/sfm-native-main-rebind-20261113'
core = json.loads((base/'native-core-cases.json').read_bytes())['cases']
wide = json.loads((base/'native-wider-cases.json').read_bytes())['cases']
inventory = json.loads((root/'experiments/source_appearance/next_sfm_candidates_20261114/ordinary-shape-ui/TARGET_INVENTORY.json').read_bytes())
keiki = next(x.copy() for x in core if x['name']=='keiki_tools_chisels-groups-000')
keiki.pop('pose_native_bone_index',None)
keiki['shape_ui']=[{'node':33,'index':0,'name':'Tools','area':'Accessories','target_count':1}]
mima = inventory['native']['mima_head']
raw = Path(mima['native_source']).read_bytes()
assert hashlib.sha256(raw).hexdigest() == mima['native_identity']['sha256']
cat = catalogue(raw,hashlib.sha256(raw).hexdigest(),Path(mima['native_source']).name)
groups = {str(x['index']):0 for x in cat['bodygroups']}
mima_case = dict(name='mima_head-ordinary-shape-ui',source=mima['native_source'],
                 source_sha256=hashlib.sha256(raw).hexdigest(),resource_root=mima['resource_root'],
                 member=Path(mima['native_source']).name,skin=0,bodygroups=groups,
                 use_override=True,expect_all_blank=False,
                 expected_meshes=[{'name':x['name'],'present':True} for x in inventory['cases']['mima_head_historical']['mesh_nodes']],
                 expected_morphs=[{'name':name,'present':True} for name in ['ah 1','ah 2','EEEE']],
                 shape_ui=[{'node':231,'index':index,'name':name,'area':'Mouth','target_count':143}
                           for index,name in [(0,'ah 1'),(1,'ah 2'),(31,'EEEE')]])
junko = next(x.copy() for x in wide if x['name']=='junko_hair-default-no-appearance')
junko['expected_jiggle_rules']=49
nitori = core[0].copy()
nitori['expected_jiggle_rules']=0
cases=[keiki,mima_case,junko,nitori]
for row in cases:
    assert hashlib.sha256(Path(row['source']).read_bytes()).hexdigest()==row['source_sha256']
path=root/'output/sfm-extra-native-inputs-20261114.json'
assert not path.exists()
path.write_text(json.dumps({'format':'has_source_appearance_native_cases_1','cases':cases},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manifest':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cases':[r['name'] for r in cases],'mima_bodygroups':groups}))
