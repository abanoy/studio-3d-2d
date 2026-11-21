"""Source-only bridge splice controls. Executes only isolated pure light phase on fakes."""
import ast
import json
import math
from pathlib import Path
import sys
import textwrap
from types import SimpleNamespace as NS
import unittest
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from source_lights import plan_batches

class Text:
    def __init__(self,name,entities):self.name=name;self.entities=entities
    def as_string(self):return json.dumps(self.entities)
class Output:
    def __init__(self,events):self.events=events;self.raw=None
    def __truediv__(self,name):
        if name!='entities.json':raise AssertionError('unexpected output')
        return self
    def write_text(self,raw,encoding):
        if encoding!='utf-8':raise AssertionError('encoding')
        self.raw=raw;self.events.append('raw_entities_written')
        return len(raw)
def run_phase(texts):
    source=(Path(__file__).resolve().parent/'blender_source_bridge.py').read_text(encoding='utf-8')
    start=source.index('    entity_batches = []\n')
    end=source.index('    # Compile-time tool surfaces',start)
    code=compile(ast.parse(textwrap.dedent(source[start:end])),'<owned-map-light-phase>','exec')
    events=[];out=Output(events);created=[]
    def create(_bpy,prepared):
        events.append('create_lights');created.extend(prepared['lights'])
    values={'bpy':NS(data=NS(texts=texts)),'json':json,'math':math,'light_plan':plan_batches,'create_lights':create,
            'request':{'scale':.01905},'out':out,'map_lights':[],'warnings':[],'suggested_view':None}
    exec(code,values)
    return values,out,created,events
class BridgePhaseTests(unittest.TestCase):
    def test_multitext_global_budget_and_complete_raw_entities(self):
        first=[{'classname':'light','targetname':str(i)} for i in range(40)]
        second=[{'classname':'light','targetname':str(i)} for i in range(40,80)]
        values,out,created,events=run_phase([Text('a_entities.json',first),Text('ignored',[]),Text('b_entities.json',second)])
        self.assertEqual(json.loads(out.raw),first+second)
        self.assertEqual(len(created),64);self.assertEqual(values['planned_lights']['omissions']['budget'],16)
        self.assertEqual(events,['raw_entities_written','create_lights'])
        self.assertEqual(len(values['map_lights']),64)
    def test_invalid_environment_does_not_abort_valid_spot_or_erase_raw(self):
        env={'classname':'light_environment','_light':'-1 -1 -1 -1','_lightHDR':'-1 -1 -1 1'}
        spot={'classname':'light_spot','_cone':'90','_inner_cone':'50'}
        values,out,created,_events=run_phase([Text('a_entities.json',[env,spot])])
        self.assertEqual(json.loads(out.raw),[env,spot]);self.assertEqual(len(created),1)
        self.assertEqual(created[0]['spot_size'],math.pi);self.assertEqual(values['planned_lights']['omissions']['invalid'],1)
        self.assertTrue(any('optional map light omitted' in warning for warning in values['warnings']))
    def test_original_per_text_player_view_selection_is_retained(self):
        texts=[Text('a_entities.json',[{'classname':'info_player_start','origin':'1 2 3'}]),
               Text('b_entities.json',[{'classname':'info_player_deathmatch','origin':'4 5 6'}])]
        values,out,created,_events=run_phase(texts)
        self.assertFalse(created);self.assertEqual(values['suggested_view']['source'],'info_player_deathmatch')
        self.assertEqual(len(json.loads(out.raw)),2)
    def test_native_metadata_is_bound_to_same_actual_omission_report(self):
        tree=ast.parse((Path(__file__).resolve().parent/'blender_source_bridge.py').read_text(encoding='utf-8'))
        matches=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Dict):
                for key,value in zip(node.keys,node.values):
                    if isinstance(key,ast.Constant) and key.value=='static_entity_light_omissions':matches.append(value)
        self.assertEqual(len(matches),1)
        self.assertEqual(ast.dump(matches[0],include_attributes=False),ast.dump(ast.parse("planned_lights['omissions']",mode='eval').body,include_attributes=False))
if __name__=='__main__':unittest.main()
