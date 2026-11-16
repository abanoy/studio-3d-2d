"""Bounded source-only deep-chain successor; never invokes an engine/parser/Git.

The authorized GLB is read only to validate crosswalk/topology and count skin
influences. Native coordinates, rests, geometry, media and arrays are not emitted.
"""
from pathlib import Path
from collections import Counter
import ast
import difflib
import hashlib
import json
import math
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ACTUAL = ROOT / 'output/source-0x31-native-chains-20261115-attempt1'
STUDIO = ACTUAL / 'Studio'
INPUTS = ACTUAL / 'read-only-inputs'
SELECTED = (35,36,37,60,61,62,63)
BRANCHES = ((35,36,37),(60,61,62,63))
PARENTS = {35:34,36:35,37:36,60:59,61:60,62:61,63:62}
GLB_SHA = '4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d'
REPORT_SHA = 'b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed'
DONORS = {
    'chain_solver.gd':'01635f84e05abe0ecc998b71117eed9c7afc6f5b15d04e8743cdf1c22efa362f',
    'model_adapter.gd':'38a226db7af1843c1f0df04318aaccc726dc88f7c61b9389f8aa029d52a4fe8c',
    'chain_capture.gd':'b1dc120815f9e56b79ca4406dd3a04ddd5b0978510c6e5ca8234b11ae88ff58b',
    'chain_harness.gd':'d25e37499f8a4b076a65e61a1a97c7ad7fb0d27828f1bd7a2bc76e9f6b0a8b5f',
    'leaf_candidate.gd':'14053abf4b00c50909468d41372ce77c826bf0ec0b895bec19418a5961b4fae3',
    'leaf_adapter.gd':'6945153a65741f65f15505a1b840ddbf530c483790824d8a98e90a4d53e539e8',
    'weighted_capture.gd':'1ffecc00666a7e9e6957b7354fd0b862eac07b0f16b79200345370348e91aacb',
    'leaf_harness.gd':'2abbb08831586323878cabb504e5400406144ad34e4b890791539b68633f722c'}
READS = []


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    READS.append({'path':str(path),'bytes':len(raw),'sha256':sha(raw)})
    return raw


def save(name, obj):
    with (HERE / name).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(obj,stream,indent=2,allow_nan=False); stream.write('\n')


def text(name, value):
    with (HERE / name).open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(value)


def change(value, old, new, count=1):
    assert value.count(old) == count, (old,value.count(old),count)
    return value.replace(old,new)


def main():
    raw_report = read(INPUTS / 'parameters.json'); assert sha(raw_report) == REPORT_SHA
    report = json.loads(raw_report)
    native = report['native_parameters']; bones = native['bones']; rules = native['source_jiggle']['rules']
    assert len(bones) == 69 and len(rules) == 49 and report['scale'] == 0.01905
    assert native['source_jiggle']['applied'] is False and native['source_jiggle']['full_native_rule_layout_verified'] is False
    rule_by_id = {rule['native_bone_index']:rule for rule in rules}; assert len(rule_by_id) == 49
    children = {i:[j for j,b in enumerate(bones) if b['parent'] == i] for i in range(69)}
    descendants = {}
    for index in SELECTED:
        assert bones[index]['parent'] == PARENTS[index]
        pending = [index]; seen = set()
        while pending:
            item = pending.pop(); assert item not in seen; seen.add(item); pending.extend(children[item])
        descendants[index] = seen
        assert seen <= set(SELECTED)
    assert descendants[35] == set(BRANCHES[0]) and descendants[60] == set(BRANCHES[1])
    assert children[37] == children[63] == []
    rows = []
    active = ('length','tip_mass','yaw_stiffness','yaw_damping','pitch_stiffness','pitch_damping','angle_limit','along_stiffness','along_damping')
    for index in SELECTED:
        rule = rule_by_id[index]
        assert rule['native_parent_index'] == PARENTS[index]
        assert rule['raw_rule_flags'] == 49 and rule['unknown_rule_flag_bits'] == 0
        rows.append({'native_index':index,'name':bones[index]['name'],'parent':PARENTS[index],
                     'children':children[index],'descendant_closed_subtree':sorted(descendants[index]),
                     'raw_flags':49,'active_and_along_parameters':{key:rule['parameters'][key] for key in active},
                     'native_prefix_sha256':rule['binary_provenance']['prefix_sha256']})
    assert Counter(row['active_and_along_parameters']['yaw_stiffness'] for row in rows) == {50.0:3,100.0:4}
    raw = read(INPUTS / 'scene.glb'); assert sha(raw) == GLB_SHA
    magic,version,total = struct.unpack_from('<III',raw,0)
    assert magic == 0x46546c67 and version == 2 and total == len(raw)
    jsize,jkind = struct.unpack_from('<II',raw,12); assert jkind == 0x4e4f534a
    gltf = json.loads(raw[20:20+jsize]); offset = 20+jsize
    bsize,bkind = struct.unpack_from('<II',raw,offset); assert bkind == 0x004e4942
    assert offset+8+bsize == len(raw)
    binary = memoryview(raw)[offset+8:]
    crosswalk = native['source_export_crosswalk']['bones']
    assert len(crosswalk) == 69 and native['source_export_crosswalk']['glb_sha256'] == GLB_SHA
    by_node = {row['gltf_node_index']:row['native_index'] for row in crosswalk}
    assert len(by_node) == 69 and set(by_node.values()) == set(range(69))
    node_parent = {}
    for parent,node in enumerate(gltf['nodes']):
        for child in node.get('children',[]):
            assert child not in node_parent; node_parent[child] = parent
    for row in crosswalk:
        index = row['native_index']; node = row['gltf_node_index']
        assert row['native_parent_index'] == bones[index]['parent'] and row['native_name'] == bones[index]['name']
        parent = node_parent.get(node)
        seen = set()
        while parent is not None and parent not in by_node:
            assert parent not in seen; seen.add(parent); parent = node_parent.get(parent)
        assert (-1 if parent is None else by_node[parent]) == bones[index]['parent']
    assert len(gltf['skins']) == 1
    slots = [by_node[node] for node in gltf['skins'][0]['joints']]
    assert len(slots) == len(set(slots)) == 69
    def accessor(index, permitted):
        acc = gltf['accessors'][index]
        assert acc['componentType'] in permitted and acc['type'] == 'VEC4'
        assert not acc.get('normalized',False) and 'sparse' not in acc
        fmt,size = permitted[acc['componentType']]; view = gltf['bufferViews'][acc['bufferView']]
        assert view.get('buffer',0) == 0
        start = view.get('byteOffset',0)+acc.get('byteOffset',0); stride = view.get('byteStride',4*size)
        assert stride >= 4*size and start+(acc['count']-1)*stride+4*size <= view.get('byteOffset',0)+view['byteLength'] <= len(binary)
        return [struct.unpack_from('<'+fmt*4,binary,start+i*stride) for i in range(acc['count'])]
    groups = {'union':set(SELECTED),'branch35_36_37':set(BRANCHES[0]),'branch60_61_62_63':set(BRANCHES[1])}
    groups.update({'subtree'+str(index):descendants[index] for index in SELECTED})
    masks = {key:bytearray() for key in groups}
    counts = {key:{'vertices':0,'weighted_to_selected':0,'shared_with_other_bones':0,'unaffected':0} for key in groups}
    surfaces = 0; branch_overlap = 0
    for mesh in gltf['meshes']:
        for primitive in mesh['primitives']:
            surfaces += 1; attributes = primitive['attributes']
            assert 'JOINTS_1' not in attributes and 'WEIGHTS_1' not in attributes
            js = accessor(attributes['JOINTS_0'],{5121:('B',1),5123:('H',2)})
            ws = accessor(attributes['WEIGHTS_0'],{5126:('f',4)})
            assert len(js) == len(ws)
            for joints,weights in zip(js,ws):
                assert all(0 <= slot < len(slots) for slot in joints)
                assert all(math.isfinite(weight) and weight >= 0 for weight in weights)
                assert abs(sum(weights)-1.0) < 0.00001
                hit = {}
                for key,selected in groups.items():
                    a = sum(weight for slot,weight in zip(joints,weights) if slots[slot] in selected)
                    b = sum(weight for slot,weight in zip(joints,weights) if slots[slot] not in selected)
                    count = counts[key]; count['vertices'] += 1; count['weighted_to_selected'] += a > 0
                    count['shared_with_other_bones'] += a > 0 and b > 0; count['unaffected'] += a == 0
                    masks[key].append(1 if a > 0 else 0); hit[key] = a > 0
                branch_overlap += hit['branch35_36_37'] and hit['branch60_61_62_63']
    assert surfaces == 4 and all(count['vertices'] == 9661 for count in counts.values())
    for key,count in counts.items():
        assert count['weighted_to_selected']+count['unaffected'] == count['vertices']
        count['descendant_closed_mask_sha256'] = sha(masks[key])
    profile = {'format':'has_native_deep_chain_source_profile_1',
               'status':'CPU_METADATA_AND_INFLUENCE_COUNTS_ONLY_GDSCRIPT_UNPARSED_UNRUN',
               'native_bones':69,'retained_rules':49,'selected_rule_count':7,'source_scale':0.01905,
               'selected':rows,'branches':[list(branch) for branch in BRANCHES],
               'selection_descendant_closed':True,'unselected_world_bones_expected_exact':62,
               'surfaces':surfaces,'influence_counts':counts,'cross_branch_shared_vertex_count':branch_overlap,
               'GLTF_crosswalk_parent_and_skin69_verified':True,
               'native_arrays_or_masks_or_geometry_or_rest_or_media_published':False,
               'glb_sha256':GLB_SHA,'parameters_sha256':REPORT_SHA,
               'native_metadata_activation_changed':False}
    save('PUBLIC_PROFILE.json',profile)
    donor = {}
    for name,expected in DONORS.items():
        data = read(STUDIO / name); assert sha(data) == expected
        donor[name] = data.decode('utf-8-sig')
        if name not in {'model_adapter.gd','chain_harness.gd'}:
            with (HERE / name).open('xb') as stream: stream.write(data)
    adapter = donor['model_adapter.gd']
    adapter = change(adapter,'Exact69-bone Junko pair profile only.','Exact69-bone Junko seven-rule deep-chain profile only.')
    adapter = change(adapter,'const SELECTED := [17,18,26,27]','const SELECTED := [35,36,37,60,61,62,63]')
    adapter = change(adapter,'const EXPECTED_PARENTS := {17:7,18:17,26:25,27:26}','const EXPECTED_PARENTS := {35:34,36:35,37:36,60:59,61:60,62:61,63:62}')
    adapter = change(adapter,'resolution.bindings[17].skeleton','resolution.bindings[35].skeleton')
    adapter = adapter.replace('Exact measured native17/18 and26/27 pairs required','Exact measured three-rule and four-rule subtrees required')
    old = '\t# Refuse additional descendants: these selected parents have exactly one\n\t# direct child, and both selected child bones are leaves in the exact profile.\n'
    new = '\t# Every selected non-leaf has exactly one selected child; both subtrees\n\t# are descendant-closed, including all three/four rule owners.\n'
    adapter = change(adapter,old,new)
    adapter = change(adapter,'var expected: Array = [18] if index == 17 else [27] if index == 26 else []',
                     'var expected: Array = {35:[36],36:[37],37:[],60:[61],61:[62],62:[63],63:[]}[index]')
    adapter = adapter.replace('bounded two-pair profile','bounded deep-chain profile')
    adapter = change(adapter,'if parameters.size() != 4: return {"error":"All four exact retained0x31 rules required"}',
                     'if parameters.size() != 7: return {"error":"All seven exact retained0x31 rules required"}')
    adapter = adapter.replace('Complete computed four-rule result required','Complete computed seven-rule result required')
    text('model_adapter.gd',adapter)
    harness = donor['chain_harness.gd']
    harness = change(harness,'const ChainCapture = preload("res://chain_capture.gd")',
                     'const ChainCapture = preload("res://chain_capture.gd")\nconst BRANCHES := [[35,36,37],[60,61,62,63]]')
    harness = harness.replace('PASSED_NATIVE_TWO_PAIR_READINESS_ONLY','PASSED_NATIVE_DEEP_CHAIN_READINESS_ONLY')
    harness = harness.replace('FAILED_NATIVE_TWO_PAIR_READINESS','FAILED_NATIVE_DEEP_CHAIN_READINESS')
    harness = harness.replace('has_actual_native_two_pair_readiness_1','has_actual_native_deep_chain_readiness_1')
    harness = change(harness,'"native_pairs":[[17,18],[26,27]]','"native_chains":BRANCHES,"selected_rule_count":7')
    harness = harness.replace('NATIVE_TWO_PAIR ','NATIVE_DEEP_CHAIN ')
    start = harness.index('func owned_pose('); end = harness.index('\nfunc unselected_bytes(',start)
    owned = '''func owned_pose(resolution: RefCounted, later: bool) -> Dictionary:
\tvar pose := {}
\tfor spec in [{"native":7,"axis":Vector3.RIGHT,"a":0.17,"b":-0.11},
\t\t{"native":34,"axis":Vector3.UP,"a":0.13,"b":-0.07},
\t\t{"native":35,"axis":Vector3.RIGHT,"a":-0.16,"b":0.14},{"native":36,"axis":Vector3.UP,"a":0.2,"b":-0.18},
\t\t{"native":37,"axis":Vector3.FORWARD,"a":0.12,"b":0.23},
\t\t{"native":58,"axis":Vector3.UP,"a":0.09,"b":-0.13},{"native":59,"axis":Vector3.RIGHT,"a":-0.1,"b":0.16},
\t\t{"native":60,"axis":Vector3.UP,"a":0.13,"b":-0.07},{"native":61,"axis":Vector3.FORWARD,"a":0.12,"b":0.23},
\t\t{"native":62,"axis":Vector3.RIGHT,"a":-0.16,"b":0.14},{"native":63,"axis":Vector3.UP,"a":0.2,"b":-0.18},
\t\t{"native":8,"axis":Vector3.UP,"a":0.09,"b":-0.13}]:
\t\tpose[resolution.by_native[spec.native]] = {"position":[0.0004,-0.0007,0.0003] if spec.native in [37,63] else [0.0,0.0,0.0],
\t\t\t"rotation_xyzw":quaternion_array(Quaternion(spec.axis,spec.b if later else spec.a))}
\treturn pose
'''
    harness = harness[:start]+owned+harness[end:]
    harness = change(harness,'profile.selected[17]','profile.selected[35]')
    harness = change(harness,'rule_evaluations += 4','rule_evaluations += 7')
    harness = harness.replace('four desired/math','seven desired/math').replace('four native+Z','seven native+Z').replace('all65 unselected','all62 unselected')
    harness = harness.replace('pair_baselines','branch_baselines').replace('pair_captures','branch_captures').replace('pair_rows','branch_rows').replace('pair_index','branch_index')
    harness = harness.replace('"native_pair"','"native_chain"').replace('"pairs"','"branches"').replace('"private_pairs"','"private_branches"')
    harness = change(harness,'var indices: Array = [17,18] if branch_index == 0 else [26,27]','var indices: Array = BRANCHES[branch_index]')
    harness = change(harness,'var capture := ChainCapture.capture(actor,[resolution.bindings[indices[0]],resolution.bindings[indices[1]]])',
                     'var branch_bindings: Array = []\n\t\tfor index in indices: branch_bindings.append(resolution.bindings[index])\n\t\tvar capture := ChainCapture.capture(actor,branch_bindings)')
    harness = harness.replace('results.control.private_pairs','results.control.private_branches').replace('results[name].private_pairs','results[name].private_branches')
    harness = harness.replace('each actual pair weighted','each actual branch weighted').replace('Each pair external-input','Each branch external-input')
    old = '\t# Native17 has parent7, so its shared-Skeleton context can reuse the exact\n\t# empty-builtin guard unchanged. Bridge independently checks native26\'s\n\t# actual parent25, retained authored/unsimulated in this bounded subset.\n'
    new = '\t# Native17 is an unchanged, unsimulated context sentinel with parent7.\n\t# It reuses the qualified shared-Skeleton empty-builtin guard unchanged;\n\t# the bridge separately validates all seven selected native parents.\n'
    harness = change(harness,old,new)
    harness = harness.replace('Owned keyed pair fixture','Owned keyed deep-chain fixture')
    harness = change(harness,'var bindings := [resolution.bindings[17],resolution.bindings[18],resolution.bindings[26],resolution.bindings[27]]',
                     'var bindings: Array = []\n\tfor index in Bridge.SELECTED: bindings.append(resolution.bindings[index])')
    union = counts['union']
    harness = change(harness,'baseline.affected != 542 or baseline.shared != 340 or baseline.unaffected != 9119',
                     f'baseline.affected != {union["weighted_to_selected"]} or baseline.shared != {union["shared_with_other_bones"]} or baseline.unaffected != {union["unaffected"]}')
    harness = change(harness,'var branch_baselines := [ChainCapture.capture(actor,[bindings[0],bindings[1]]),ChainCapture.capture(actor,[bindings[2],bindings[3]])]',
                     'var branch_baselines: Array = []\n\tfor indices in BRANCHES:\n\t\tvar branch_bindings: Array = []\n\t\tfor index in indices: branch_bindings.append(resolution.bindings[index])\n\t\tbranch_baselines.append(ChainCapture.capture(actor,branch_bindings))')
    first = counts['branch35_36_37']; second = counts['branch60_61_62_63']
    harness = change(harness,'var expected: Array = [184,118,9477] if branch_index == 0 else [358,222,9303]',
                     f'var expected: Array = [{first["weighted_to_selected"]},{first["shared_with_other_bones"]},{first["unaffected"]}] if branch_index == 0 else [{second["weighted_to_selected"]},{second["shared_with_other_bones"]},{second["unaffected"]}]')
    harness = harness.replace('Actual pair influence counts','Actual branch influence counts').replace('owned pair probe','owned deep-chain probe')
    harness = harness.replace('Fresh root-owned pair lease/result','Fresh root-owned deep-chain lease/result')
    harness = harness.replace('has_native_two_pair_readiness_lease_1','has_native_deep_chain_readiness_lease_1')
    harness = harness.replace('ROOT_APPROVED_AFTER_FULL_FK_MATH_LEAF_AND_CLOSURE','ROOT_APPROVED_AFTER_FRESH_FULL_FK_MATH_LEAF_PAIR_AND_CLOSURE')
    harness = change(harness,'["full_status","FK_status","math_status","leaf_status"]','["full_status","FK_status","math_status","leaf_status","pair_status"]')
    harness = change(harness,'"leaf_receipt","root_closure","chain_solver"','"leaf_receipt","pair_receipt","root_closure","chain_solver"')
    harness = harness.replace('Incomplete pair source lock','Incomplete deep-chain source lock').replace('Changed locked pair input','Changed locked deep-chain input')
    harness = harness.replace('Changed staged pair source','Changed staged deep-chain source').replace('Exact fresh pair result path','Exact fresh deep-chain result path')
    harness = harness.replace('Native two-pair bounded refusal','Native deep-chain bounded refusal')
    text('chain_harness.gd',harness)
    for name,updated in [('model_adapter.gd',adapter),('chain_harness.gd',harness)]:
        patch = ''.join(difflib.unified_diff(donor[name].splitlines(True),updated.splitlines(True),fromfile='qualified-pair/'+name,tofile='source-only-deep/'+name))
        text(name+'.patch',patch)
    predecessor = json.loads(read(ACTUAL / 'verification.json'))
    assert predecessor['passed'] and predecessor['math_passed'] and predecessor['native_passed']
    assert predecessor['result']['checks'] == 21087 and predecessor['result']['failures'] == 0
    assert predecessor['result']['dynamic_ticks'] == 1440 and predecessor['result']['rule_evaluations'] == 5760
    for path in HERE.glob('*.py'): ast.parse(path.read_text())
    assert '\t\t\tcheck(error.basis <= EPS' in harness and 'tip_error <= EPS*root_size' in harness
    assert 'difference.affected_max > MOTION_MIN*root_size' in harness
    assert 'difference.affected_max > MOTION_MIN*root_scale' in harness
    assert 'parameters.size() != 7' in adapter and 'profile.parameters.size()' in adapter
    assert 'private_pairs' not in harness and 'pair_baselines' not in harness
    budget = {'root_placements':2,'profiles_per_placement':6,'ticks_per_profile':120,
              'selected_rule_count':7,'proposed_actor_ticks':1440,'proposed_rule_evaluations':10080,
              'proposed_assertions':34047,'actual_run':False,
              'assertion_derivation':'Per profile69 baseline +120*(3*7+2) tick gates +1 unaffected +4 Off/binding; add2 branch gates for each of5 nonzero profiles; per root add8 external-response +1 repeat; two roots plus1 final source check.'}
    save('STATIC_PREPARATION.json',{'format':'has_deep_chain_static_preparation_1','status':'SOURCE_ONLY_GDSCRIPT_UNPARSED_UNRUN',
                                  'qualified_pair_run_reference':str(ACTUAL),'qualified_pair_checks':21087,
                                  'qualified_pair_math_checks':4012,'budget':budget,
                                  'same_EPS_motion_Off_repeat_gates':True,'no_production_edits_or_engines_or_Git':True,
                                  'template_approval':'UNAPPROVED_MUST_REBASE_SOURCE_LOCK_TO_FRESH_FULL_BEFORE_ROOT_RUN'})
    save('SOURCE_PROVENANCE.json',{'format':'has_deep_chain_source_provenance_1','files_read':READS,
                                 'unchanged_donor_sha256':{k:v for k,v in DONORS.items() if k not in {'model_adapter.gd','chain_harness.gd'}},
                                 'derived_donors_sha256':{k:v for k,v in DONORS.items() if k in {'model_adapter.gd','chain_harness.gd'}},
                                 'GDScript':'UNPARSED_UNRUN','raw_GLTF_or_skin_arrays_serialized':False})
    files = {}
    for key,name in [('candidate','leaf_candidate.gd'),('adapter','leaf_adapter.gd'),('capture','weighted_capture.gd'),('harness','leaf_harness.gd'),
                     ('chain_solver','chain_solver.gd'),('model_adapter','model_adapter.gd'),('chain_capture','chain_capture.gd'),('chain_harness','chain_harness.gd')]:
        files[key] = {'path':str(HERE / name),'sha256':sha((HERE / name).read_bytes())}
    for key,name,digest in [('glb','scene.glb',GLB_SHA),('parameters','parameters.json',REPORT_SHA)]:
        files[key] = {'path':str(INPUTS / name),'sha256':digest}
    for key in ['source_lock','mdl','vvd','full_receipt','FK_receipt','math_receipt','leaf_receipt','pair_receipt','root_closure']:
        files[key] = {'path':'REPLACE_WITH_FRESH_ELIGIBLE_ABSOLUTE_'+key,'sha256':'0'*64}
    save('ROOT_LEASE_UNAPPROVED_TEMPLATE.json',{'format':'has_native_deep_chain_readiness_lease_1','phase':'UNAPPROVED_SOURCE_ONLY_TEMPLATE',
                                             'full_status':'UNRUN','FK_status':'UNRUN','math_status':'UNRUN','leaf_status':'UNRUN','pair_status':'UNRUN',
                                             'root_closed_all':False,'expires_unix':0,
                                             'engine_sha256':'REPLACE_WITH_ROOT_VERIFIED_APPROVED_ENGINE_SHA256',
                                             'files':files,'public_result':'REPLACE_WITH_FRESH_ABSOLUTE_ROOT_RESULT'})
    # Verify inputs and donor source remained identical throughout this CPU read.
    for row in READS:
        again = Path(row['path']).read_bytes(); assert sha(again) == row['sha256'] and len(again) == row['bytes']
    print(json.dumps({'status':'SOURCE_ONLY_DEEP_CHAIN_PREPARED_GDSCRIPT_UNPARSED_UNRUN','counts':counts,
                      'cross_branch_shared_vertex_count':branch_overlap,'proposed_checks':34047,
                      'proposed_ticks':1440,'proposed_rule_evaluations':10080}))


if __name__ == '__main__':
    main()
