"""Pure CPU bridge for the closed carrier skin/graph/animation input domain.

This is not a complete glTF conformance validator or a native correspondence gate.
"""
import hashlib
import math
import re
import struct
from collections import deque

from semantic_compare import Refusal, Snapshot, freeze, need, parse_json_document, compare_non_normal

MAX_GLB = 128 * 1024 * 1024
MAX_TABLE = 65536
MAX_EDGES = 262144
MAX_COMPONENT_VISITS = 8_000_000


def read_semantic_glb(raw):
    """Preserve the original JSON chunk through strict lexical parsing."""
    need(type(raw) is bytes and 28 <= len(raw) <= MAX_GLB, 'Bounded GLB bytes required')
    need(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Exact GLB2 header required')
    size, kind = struct.unpack_from('<I4s', raw, 12)
    need(kind == b'JSON' and size % 4 == 0 and 20 + size + 8 <= len(raw), 'JSON-first two-chunk profile')
    try:
        doc = parse_json_document(raw[20:20 + size])
    except (RecursionError, OverflowError) as error:
        raise Refusal('JSON depth/numeric profile') from error
    at = 20 + size
    count, kind = struct.unpack_from('<I4s', raw, at)
    need(kind == b'BIN\0' and count % 4 == 0 and at + 8 + count == len(raw), 'One exact BIN chunk required')
    binary = raw[at + 8:]
    buffers = doc.get('buffers')
    need(type(buffers) is list and len(buffers) == 1 and type(buffers[0]) is dict, 'One embedded buffer')
    declared = buffers[0].get('byteLength')
    need(type(declared) is int and declared > 0 and declared <= len(binary) <= declared + 3, 'BIN bounds')
    need(not any(binary[declared:]), 'Zero BIN padding required')
    return doc, binary


def _index(value, count):
    need(type(value) is int and 0 <= value < count, 'Exact in-domain integer reference')
    return value


def _rows(snapshot, index):
    accessor, token = snapshot.accessor(index)
    component = accessor['componentType']
    code = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}[component]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[accessor['type']]
    return accessor, list(struct.iter_unpack('<' + code * width, token['component_bytes']))


def qualify_input_domain(document, binary, carrier=False):
    """Qualify the stated closed domain, bound to exact input content and rest data."""
    need(type(carrier) is bool, 'Explicit carrier role required')
    try:
        return _qualify(document, binary, carrier)
    except (RecursionError, OverflowError, KeyError, IndexError, TypeError, struct.error) as error:
        raise Refusal('Closed domain depth/numeric profile') from error


def _qualify(document, binary, carrier):
    need(type(document) is dict, 'Document object required')
    for name in ('nodes', 'meshes', 'skins', 'scenes', 'animations', 'accessors', 'bufferViews'):
        need(type(document.get(name, [])) is list and len(document.get(name, [])) <= MAX_TABLE, 'Domain table bound')
    # Bound the parent's decoding and reference traversal before it can allocate
    # packed component copies for repeated accessor uses.
    accessors = document.get('accessors', [])
    estimated = edges_estimated = primitive_entries = channel_entries = 0
    def cost(index):
        nonlocal estimated
        accessor = accessors[_index(index, len(accessors))]
        need(type(accessor) is dict and type(accessor.get('count')) is int and 1 <= accessor['count'] <= 2_000_000, 'Accessor cost domain')
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}.get(accessor.get('type'))
        need(width is not None, 'Accessor shape domain')
        estimated += accessor['count'] * width * 2
        need(estimated <= MAX_COMPONENT_VISITS, 'Preflight decoded component bound')
    for node in document.get('nodes', []):
        need(type(node) is dict and type(node.get('children', [])) is list, 'Node preflight shape')
        edges_estimated += len(node.get('children', []))
    for scene in document.get('scenes', []):
        need(type(scene) is dict and type(scene.get('nodes', [])) is list, 'Scene preflight shape')
        edges_estimated += len(scene.get('nodes', []))
    for skin in document.get('skins', []):
        need(type(skin) is dict and type(skin.get('joints')) is list, 'Skin preflight shape')
        edges_estimated += len(skin['joints'])
        if 'inverseBindMatrices' in skin: cost(skin['inverseBindMatrices'])
    need(edges_estimated <= MAX_EDGES, 'Preflight reference edge bound')
    for mesh in document.get('meshes', []):
        need(type(mesh) is dict and type(mesh.get('primitives')) is list, 'Mesh preflight shape')
        primitive_entries += len(mesh['primitives'])
        need(primitive_entries <= MAX_EDGES, 'Preflight primitive entry bound')
        for primitive in mesh['primitives']:
            need(type(primitive) is dict and type(primitive.get('attributes')) is dict and type(primitive.get('targets', [])) is list, 'Primitive preflight shape')
            for index in primitive['attributes'].values(): cost(index)
            if 'indices' in primitive: cost(primitive['indices'])
            for target in primitive.get('targets', []):
                need(type(target) is dict, 'Morph preflight shape')
                for index in target.values(): cost(index)
    for animation in document.get('animations', []):
        need(type(animation) is dict and type(animation.get('samplers')) is list and type(animation.get('channels')) is list, 'Animation preflight shape')
        channel_entries += len(animation['channels'])
        need(channel_entries <= MAX_EDGES, 'Preflight channel entry bound')
        for sampler in animation['samplers']:
            need(type(sampler) is dict, 'Sampler preflight shape')
            cost(sampler.get('input')); cost(sampler.get('output'))
    original = freeze(document)
    snapshot = Snapshot(document, binary, carrier)
    snapshot.canonical()  # Unchanged structural/accessor/material preservation profile.
    doc = snapshot.doc
    nodes, meshes, skins = (doc.get(name, []) for name in ('nodes', 'meshes', 'skins'))
    need(all(len(doc.get(name, [])) <= MAX_TABLE for name in
             ('nodes', 'meshes', 'skins', 'scenes', 'animations', 'accessors', 'bufferViews')), 'Domain table bound')
    need(nodes and meshes, 'Instantiated node/mesh domain required')
    parents = [None] * len(nodes)
    child_lists = []
    edges = 0
    for i, node in enumerate(nodes):
        children = node.get('children', [])
        need(len(children) == len(set(children)), 'Duplicate child reference')
        for child in children:
            _index(child, len(nodes))
            need(child != i and parents[child] is None, 'Node must have at most one parent')
            parents[child] = i
        child_lists.append(children)
        edges += len(children)
        need(edges <= MAX_EDGES, 'Graph edge bound')
    queue = deque(i for i, parent in enumerate(parents) if parent is None)
    order = []
    while queue:
        i = queue.popleft(); order.append(i); queue.extend(child_lists[i])
    need(len(order) == len(nodes), 'Cyclic node graph')
    roots = [None] * len(nodes)
    for i in order:
        roots[i] = i if parents[i] is None else roots[parents[i]]

    begin, end = [0] * len(nodes), [0] * len(nodes)
    clock = 0
    for root in (i for i, parent in enumerate(parents) if parent is None):
        stack = [(root, False)]
        while stack:
            node, leaving = stack.pop()
            if leaving:
                end[node] = clock
            else:
                begin[node] = clock; clock += 1
                stack.append((node, True)); stack.extend((child, False) for child in reversed(child_lists[node]))
    def ancestor(parent, node):
        return begin[parent] <= begin[node] < end[parent]

    tree_members = {}
    for i, root in enumerate(roots): tree_members.setdefault(root, []).append(i)
    scene_members = []; scene_total = 0; node_scenes = [[] for _ in nodes]
    for scene in doc.get('scenes', []):
        scene_roots = scene.get('nodes', [])
        need(len(scene_roots) == len(set(scene_roots)), 'Duplicate scene root')
        need(all(parents[_index(i, len(nodes))] is None for i in scene_roots), 'Scene entries must be graph roots')
        scene_total += sum(len(tree_members[i]) for i in scene_roots)
        need(scene_total <= MAX_EDGES, 'Cumulative scene membership bound')
        scene_members.append({node for root in scene_roots for node in tree_members[root]})
        for node in scene_members[-1]: node_scenes[node].append(len(scene_members) - 1)
    need(scene_members, 'Scene ownership domain required')
    for skin in skins:
        joints = skin['joints']
        need(len(joints) == len(set(joints)), 'Duplicate skin joint')
        need(len({roots[i] for i in joints}) == 1, 'Skin joints must share a graph tree')
        if 'skeleton' in skin:
            need(all(ancestor(skin['skeleton'], i) for i in joints), 'Skeleton must be ancestor of all joints')

    mesh_targets = []
    for mesh in meshes:
        counts = [len(p.get('targets', [])) for p in mesh['primitives']]
        need(len(set(counts)) == 1, 'Uniform morph target count per mesh')
        targets = counts[0]; mesh_targets.append(targets)
        if 'weights' in mesh:
            need(type(mesh['weights']) is list and len(mesh['weights']) == targets and
                 all(type(v) in (int, float) and math.isfinite(v) for v in mesh['weights']), 'Mesh morph weight domain')
    owning_pairs = set(); component_visits = 0; primitive_visits = 0
    skin_sets = [set(skin['joints']) for skin in skins]
    need({node['mesh'] for node in nodes if 'mesh' in node} == set(range(len(meshes))), 'Unused mesh has no ownership domain')
    for node_id, node in enumerate(nodes):
        if 'skin' in node: need('mesh' in node, 'Skin requires mesh owner')
        if 'weights' in node:
            need('mesh' in node and type(node['weights']) is list and len(node['weights']) == mesh_targets[node['mesh']] and
                 all(type(v) in (int, float) and math.isfinite(v) for v in node['weights']), 'Node morph weight domain')
        if 'mesh' not in node: continue
        mesh_id = node['mesh']
        for primitive in meshes[mesh_id]['primitives']:
            primitive_visits += 1
            need(primitive_visits <= MAX_EDGES, 'Primitive owner visit bound')
            attrs = primitive['attributes']
            for name in attrs:
                match = re.fullmatch(r'(JOINTS|WEIGHTS)_(\d+)', name)
                if match:
                    need(len(match[2]) <= 4 and match[2] == str(int(match[2])), 'Canonical bounded skin attribute set')
            joint_sets = {int(name[7:]) for name in attrs if re.fullmatch(r'JOINTS_\d+', name)}
            weight_sets = {int(name[8:]) for name in attrs if re.fullmatch(r'WEIGHTS_\d+', name)}
            need(joint_sets == weight_sets, 'Joint and weight sets must pair')
            if not joint_sets:
                need('skin' not in node, 'Skinned primitive requires joint/weight attributes')
                continue
            need('skin' in node and joint_sets == set(range(len(joint_sets))), 'Contiguous skinned attributes require owning skin')
            skin_id = node['skin']; skin = skins[skin_id]
            containing = node_scenes[node_id]
            component_visits += len(skin['joints']) * len(containing)
            need(component_visits <= MAX_COMPONENT_VISITS, 'Skin membership visit bound')
            need(containing and all(skin_sets[skin_id] <= scene_members[i] for i in containing), 'Skin joints outside owning scene')
            for set_id in sorted(joint_sets):
                component_visits += doc['accessors'][attrs[f'JOINTS_{set_id}']]['count'] * 8
                need(component_visits <= MAX_COMPONENT_VISITS, 'Skinned component visit bound')
                _, values = _rows(snapshot, attrs[f'JOINTS_{set_id}'])
                need(all(0 <= joint < len(skin['joints']) for row in values for joint in row), 'Joint component outside owning skin')
                accessor, weights = _rows(snapshot, attrs[f'WEIGHTS_{set_id}'])
                limit = {5121: 255, 5123: 65535, 5126: 1}[accessor['componentType']]
                need(all(0 <= weight <= limit for row in weights for weight in row), 'Skin weight component outside range')
            owning_pairs.add((node_id, mesh_id, skin_id))

    channel_count = 0
    for animation in doc.get('animations', []):
        targets_seen = set()
        need({channel['sampler'] for channel in animation['channels']} == set(range(len(animation['samplers']))), 'Unused animation sampler has no target domain')
        for channel in animation['channels']:
            target = channel['target']; node_id, path = target['node'], target['path']
            need((node_id, path) not in targets_seen, 'Duplicate animation node/path channel')
            targets_seen.add((node_id, path)); node = nodes[node_id]
            sampler = animation['samplers'][channel['sampler']]
            component_visits += doc['accessors'][sampler['input']]['count'] + doc['accessors'][sampler['output']]['count'] * 4
            need(component_visits <= MAX_COMPONENT_VISITS, 'Animation component visit bound')
            input_desc, times = _rows(snapshot, sampler['input'])
            need(all(row[0] >= 0 for row in times) and all(a[0] < b[0] for a, b in zip(times, times[1:])), 'Animation times strictly increasing/nonnegative')
            output, values = _rows(snapshot, sampler['output'])
            factor = 3 if sampler.get('interpolation', 'LINEAR') == 'CUBICSPLINE' else 1
            components = 1
            if path == 'weights':
                need('mesh' in node and mesh_targets[node['mesh']] > 0, 'Weights animation requires morph mesh')
                components = mesh_targets[node['mesh']]; kind = 'SCALAR'
            else:
                need('matrix' not in node, 'Animated TRS node cannot declare matrix')
                kind = 'VEC4' if path == 'rotation' else 'VEC3'
            need(output['type'] == kind and output['count'] == input_desc['count'] * factor * components,
                 'Animation output shape/count incompatible with target')
            channel_count += 1
    need(freeze(document) == original, 'Domain validator mutated input')
    rest = {'node_parents': parents,
            'node_transforms': [{k: node[k] for k in ('matrix', 'translation', 'rotation', 'scale') if k in node} for node in nodes],
            'skins': [], 'mesh_skin_owners': [list(row) for row in sorted(owning_pairs)]}
    for skin in skins:
        item = dict(skin)
        if 'inverseBindMatrices' in skin:
            _, token = snapshot.accessor(skin['inverseBindMatrices']); item['inverseBindMatrices'] = token
        rest['skins'].append(item)
    return {'format': 'has_closed_skin_graph_animation_domain_1', 'passed': True,
            'nodes': len(nodes), 'skins': len(skins), 'skinned_owners': len(owning_pairs), 'animation_channels': channel_count,
            'typed_document_sha256': hashlib.sha256(repr(original).encode()).hexdigest(),
            'binary_sha256': hashlib.sha256(binary).hexdigest(),
            'rest_skin_binding_sha256': hashlib.sha256(repr(freeze(rest, internal=True)).encode()).hexdigest(),
            'full_gltf_conformance_qualified': False, 'native_correspondence_qualified': False,
            'normal_fidelity_or_adoption_qualified': False}


def compare_qualified_non_normal(before_raw, carrier_raw):
    before, before_bin = read_semantic_glb(before_raw)
    after, after_bin = read_semantic_glb(carrier_raw)
    left = qualify_input_domain(before, before_bin, False)
    right = qualify_input_domain(after, after_bin, True)
    return {'before_domain': left, 'carrier_domain': right,
            'preservation': compare_non_normal(before, before_bin, after, after_bin),
            'before_glb_sha256': hashlib.sha256(before_raw).hexdigest(),
            'carrier_glb_sha256': hashlib.sha256(carrier_raw).hexdigest(),
            'native_normal_repair_or_adoption_qualified': False}
