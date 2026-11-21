from pathlib import Path
import hashlib,importlib.util,json,os,random,struct,sys,time
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT),str(ROOT/'tools'),str(ROOT/'tests')]
import secondary_helpers as H
from test_secondary_helpers import write_glb
import verify_generated_secondary_motion as CPU
import verify_import_capability as V
research=Path(__file__).with_name('feasible_bins.py')
spec=importlib.util.spec_from_file_location('packed_proposal',research);proposal=importlib.util.module_from_spec(spec);spec.loader.exec_module(proposal)
folder=ROOT/'output'/('packed-weight-readback-'+str(time.time_ns()));folder.mkdir()
source=folder/'authored.glb'
rows=[[1.,0.,0.,0.],[proposal.f32(.1),proposal.f32(.8),proposal.f32(.1),0.],
      [proposal.f32(.2),proposal.f32(.3),proposal.f32(.4),proposal.f32(.1)],
      [proposal.f32(1/3)]*3+[0.],[proposal.f32(.99999),proposal.f32(.00001),0.,0.]]
rng=random.Random(20261122)
for _ in range(5):
    raw=[rng.random() for _ in range(4)];rows.append([proposal.f32(v/sum(raw)) for v in raw])
cases=[];refused=0
for index,row in enumerate(rows):
    cases.append({'name':f'source_{index}','weights':row,'joints':[0,2,4,6],'slots':4,'prediction':proposal.profile(row)})
    for part,fraction in enumerate([.13,.5,.87]):
        naive=proposal.ordinary_split(row,fraction)
        cases.append({'name':f'naive_{index}_{part}','weights':naive,'joints':list(range(8)),'slots':8,'prediction':proposal.profile(naive)})
        solved=proposal.solve(row,fraction)
        if solved['status']=='PREDICTED_FEASIBLE':
            values=solved['candidate']
            cases.append({'name':f'solved_{index}_{part}','weights':values,'joints':list(range(8)),'slots':8,'prediction':proposal.profile(values)})
        else:refused+=1
for row in cases:
    row['prediction']['readback_bits']=[struct.unpack('<I',struct.pack('<f',v))[0] for v in row['prediction']['readback']]
doc={'asset':{'version':'2.0','generator':'HAS authored packed-weight readback'},'scene':0,
     'scenes':[{'nodes':[0]}],'nodes':[{'name':'Fixture','children':[1]},{'name':'Armature','children':list(range(2,10))}]+
     [{'name':f'FixtureJ{i}'} for i in range(8)],'skins':[{'joints':list(range(2,10)),'skeleton':1}],
     'meshes':[],'accessors':[],'bufferViews':[]}
write_glb(source,doc,bytes(4));g=H.GLB(source)
g.doc['skins'][0]['inverseBindMatrices']=g.append([H.IDENTITY]*8,'MAT4')
for row in cases:
    node=len(g.doc['nodes']);g.doc['nodes'][0]['children'].append(node)
    g.doc['nodes'].append({'name':row['name'],'mesh':len(g.doc['meshes']),'skin':0})
    attrs={'POSITION':g.append([[-.2,0.,0.],[.2,0.,0.],[0.,1.,0.]],'VEC3')}
    for slot in range(row['slots']//4):
        attrs[f'JOINTS_{slot}']=g.append([row['joints'][slot*4:slot*4+4]]*3,'VEC4',5123)
        attrs[f'WEIGHTS_{slot}']=g.append([row['weights'][slot*4:slot*4+4]]*3,'VEC4')
    g.doc['meshes'].append({'name':row['name'],'primitives':[{'attributes':attrs,'indices':g.append([[0],[1],[2]],'SCALAR',5123)}]})
write_glb(source,g.doc,bytes(g.binary))
recipe=folder/'public_rows.json';recipe.write_text(json.dumps({'cases':cases,'solver_refusals':refused},indent=2)+'\n')
files=[research,Path(__file__),Path(__file__).with_name('packed_weight_probe.gd'),source,recipe]
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};frozen,_=V.source_blobs();env=dict(os.environ)
result={'status':'FAIL','cases':[]};primary=None
try:
    CPU.case(folder,'readback',str(Path(__file__).with_name('packed_weight_probe.gd')),'PACKED_WEIGHT_PROBE ',4+4*len(cases),[str(source),str(recipe)],result['cases'])
    result.update(status='PASS',actual_cases=len(cases),source_rows=len(rows),solver_refusals=refused)
except BaseException as error:
    result['error']=str(error);primary=error
finally:
    result['program_inputs_preserved']=before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    result['source_preservation_failures']=V.sources_unchanged(frozen)
    result['environment_preserved']=dict(os.environ)==env
    result['input_hashes']=before
    if not result['program_inputs_preserved'] or result['source_preservation_failures'] or not result['environment_preserved']:result['status']='FAIL'
    (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'folder':str(folder),'status':result['status'],'actual_cases':result.get('actual_cases'),'error':result.get('error')}))
if primary:raise primary
if result['status']!='PASS':raise RuntimeError('Preservation failed')
