"""Authorized owned GLB weight/topology reads; publish counts/hashes only."""
from pathlib import Path
import hashlib
import json
import math
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = ROOT / 'output/source-0x31-native-chains-20261115-attempt1/read-only-inputs'
SELECTED = (8,17,18,26,27)
PARENTS = {8:7,17:7,18:17,26:25,27:26}
GLB = '4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d'
PARAM = 'b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    metadata_raw = (INPUTS / 'parameters.json').read_bytes(); assert sha(metadata_raw) == PARAM
    native = json.loads(metadata_raw)['native_parameters']; bones = native['bones']
    assert len(bones) == 69 and len(native['source_jiggle']['rules']) == 49
    children = {i:[j for j,b in enumerate(bones) if b['parent'] == i] for i in range(69)}
    subtrees = {}
    for index in SELECTED:
        assert bones[index]['parent'] == PARENTS[index]
        pending = [index]; selected = set()
        while pending:
            value = pending.pop(); assert value not in selected
            selected.add(value); pending.extend(children[value])
        assert selected <= set(SELECTED); subtrees['subtree'+str(index)] = selected
    groups = {'union':set(SELECTED),'front8':{8},'pair17_18':{17,18},'pair26_27':{26,27},**subtrees}
    raw = (INPUTS / 'scene.glb').read_bytes(); assert sha(raw) == GLB
    magic,version,length = struct.unpack_from('<III',raw,0)
    assert (magic,version,length) == (0x46546c67,2,len(raw))
    size,kind = struct.unpack_from('<II',raw,12); assert kind == 0x4e4f534a
    doc = json.loads(raw[20:20+size]); offset = 20+size
    size,kind = struct.unpack_from('<II',raw,offset); assert kind == 0x004e4942 and offset+8+size == len(raw)
    binary = memoryview(raw)[offset+8:]
    crosswalk = native['source_export_crosswalk']['bones']; assert len(crosswalk) == 69
    by_node = {row['gltf_node_index']:row['native_index'] for row in crosswalk}
    assert len(by_node) == 69 and set(by_node.values()) == set(range(69)) and len(doc['skins']) == 1
    node_parents = {}
    for parent,node in enumerate(doc['nodes']):
        for child in node.get('children',[]):
            assert child not in node_parents; node_parents[child] = parent
    for row in crosswalk:
        index = row['native_index']; parent = node_parents.get(row['gltf_node_index']); seen = set()
        while parent is not None and parent not in by_node:
            assert parent not in seen; seen.add(parent); parent = node_parents.get(parent)
        assert (-1 if parent is None else by_node[parent]) == bones[index]['parent'] == row['native_parent_index']
    slots = [by_node[node] for node in doc['skins'][0]['joints']]
    assert len(slots) == len(set(slots)) == 69
    def values(index,permitted):
        acc = doc['accessors'][index]; assert acc['type'] == 'VEC4' and acc['componentType'] in permitted
        assert not acc.get('normalized',False) and 'sparse' not in acc
        fmt,width = permitted[acc['componentType']]; view = doc['bufferViews'][acc['bufferView']]
        start = view.get('byteOffset',0)+acc.get('byteOffset',0); stride = view.get('byteStride',4*width)
        assert view.get('buffer',0) == 0 and stride >= 4*width
        assert start+(acc['count']-1)*stride+4*width <= view.get('byteOffset',0)+view['byteLength'] <= len(binary)
        return (struct.unpack_from('<'+fmt*4,binary,start+i*stride) for i in range(acc['count']))
    counts = {k:{'vertices':0,'weighted_to_selected':0,'shared_with_other_bones':0,'unaffected':0} for k in groups}
    masks = {k:bytearray() for k in groups}; overlap_front_pairs = 0; surfaces = 0
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            surfaces += 1; attributes = primitive['attributes']
            assert 'JOINTS_1' not in attributes and 'WEIGHTS_1' not in attributes
            joint_acc = doc['accessors'][attributes['JOINTS_0']]; weight_acc = doc['accessors'][attributes['WEIGHTS_0']]
            assert joint_acc['count'] == weight_acc['count']
            for joints,weights in zip(values(attributes['JOINTS_0'],{5121:('B',1),5123:('H',2)}), values(attributes['WEIGHTS_0'],{5126:('f',4)})):
                assert all(0 <= slot < len(slots) for slot in joints)
                assert all(math.isfinite(weight) and weight >= 0 for weight in weights) and abs(sum(weights)-1) < 0.00001
                hit = {}
                for key,selection in groups.items():
                    selected = sum(weight for slot,weight in zip(joints,weights) if slots[slot] in selection)
                    other = sum(weight for slot,weight in zip(joints,weights) if slots[slot] not in selection)
                    row = counts[key]; row['vertices'] += 1; row['weighted_to_selected'] += selected > 0
                    row['shared_with_other_bones'] += selected > 0 and other > 0; row['unaffected'] += selected == 0
                    masks[key].append(1 if selected > 0 else 0); hit[key] = selected > 0
                overlap_front_pairs += hit['front8'] and (hit['pair17_18'] or hit['pair26_27'])
    assert surfaces == 4 and all(row['vertices'] == 9661 for row in counts.values())
    assert counts['front8']['weighted_to_selected'] == 152
    assert counts['pair17_18']['weighted_to_selected'] == 184 and counts['pair26_27']['weighted_to_selected'] == 358
    for key,row in counts.items():
        assert row['weighted_to_selected']+row['unaffected'] == 9661
        row['descendant_closed_mask_sha256'] = sha(masks[key])
    public = {'format':'has_native_five_draft_weight_profile_1','status':'CPU_MEASURED_COUNTS_PROPOSED_BACKEND_UNPARSED_UNRUN',
              'source_paths':[str(INPUTS/'parameters.json'),str(INPUTS/'scene.glb')],
              'parameters_sha256':PARAM,'glb_sha256':GLB,'native_bones':69,'retained_rules':49,
              'selected_native_indices':list(SELECTED),'expected_parents':{str(k):v for k,v in PARENTS.items()},
              'selection_descendant_closed':True,'unselected_world_bones_expected_exact':64,
              'surfaces':surfaces,'influence_counts':counts,'front8_overlap_with_either_pair_vertices':overlap_front_pairs,
              'masks_or_points_or_weights_or_rest_arrays_or_native_media_published':False,
              'raw_metadata_activation_changed':False,'actual_five_rule_motion_tested':False}
    with (HERE/'PUBLIC_PROFILE.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(public,stream,indent=2); stream.write('\n')
    assert sha((INPUTS/'parameters.json').read_bytes()) == PARAM and sha((INPUTS/'scene.glb').read_bytes()) == GLB
    print(json.dumps({'passed':True,'source_only':True,'union':counts['union'],'front_pair_overlap':overlap_front_pairs}))


if __name__ == '__main__':
    main()
