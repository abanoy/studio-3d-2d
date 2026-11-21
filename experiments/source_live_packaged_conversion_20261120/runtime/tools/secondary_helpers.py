"""Original bounded loose-region assessment and immutable weighted GLB derivation.

Experimental authoring backend, not an automatic material/cloth classifier.
The caller must review a region/anchor before build(). No external resources,
packages, native applications or source-file writes. Existing springs take priority.
"""
from pathlib import Path
import hashlib
import heapq
import json
import math
import os
import struct

MAX_FILE = 128 * 1024 * 1024
MAX_JSON = 16 * 1024 * 1024
MAX_VERTICES = 100000
MAX_INDICES = 600000
IDENTITY = (1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.)
COMPONENTS = {5121: ('B', 1, 255), 5123: ('H', 2, 65535),
              5125: ('I', 4, 4294967295), 5126: ('f', 4, 1)}
WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def finite(value, lo=-100000., hi=100000.):
    if type(value) not in (int, float) or not math.isfinite(value) or not lo <= value <= hi:
        raise ValueError('Invalid or nonfinite helper parameter')
    return float(value)


def integer(value, limit):
    if type(value) is not int or not 0 <= value < limit:
        raise ValueError('Helper reference is out of range')
    return value


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('Duplicate GLB JSON key')
        result[key] = value
    return result


def shape_requested(options):
    return isinstance(options, dict) and any(k in options for k in ('source_morph_defaults', 'morph_weights'))


def point(matrix, p):
    return tuple(sum(matrix[col * 4 + row] * p[col] for col in range(3)) + matrix[12 + row] for row in range(3))


def translation(p):
    result = list(IDENTITY); result[12:15] = p
    return result


def multiply(a, b):
    return [sum(a[k * 4 + row] * b[col * 4 + k] for k in range(4)) for col in range(4) for row in range(4)]


def distance(a, b): return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))
def mix(a, b, t): return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


def bind_origin(m):
    a, b, c, d, e, f, g, h, i = (m[k] for k in (0, 4, 8, 1, 5, 9, 2, 6, 10))
    det = a * (e*i-f*h) - b * (d*i-f*g) + c * (d*h-e*g)
    if abs(det) < 1e-12: raise ValueError('Singular source inverse bind matrix')
    inverse = ((e*i-f*h, c*h-b*i, b*f-c*e), (f*g-d*i, a*i-c*g, c*d-a*f), (d*h-e*g, b*g-a*h, a*e-b*d))
    return tuple(-sum(row[k] * m[12+k] for k in range(3)) / det for row in inverse)


class GLB:
    def __init__(self, source):
        self.source = Path(source).resolve(strict=True)
        if self.source.stat().st_size > MAX_FILE: raise ValueError('GLB exceeds128MiB')
        self.raw = self.source.read_bytes(); self.sha = hashlib.sha256(self.raw).hexdigest()
        if len(self.raw) < 28 or struct.unpack_from('<4sII', self.raw) != (b'glTF', 2, len(self.raw)):
            raise ValueError('Invalid GLB header')
        chunks = []; offset = 12
        while offset < len(self.raw):
            if offset + 8 > len(self.raw): raise ValueError('Truncated GLB chunk')
            count, kind = struct.unpack_from('<II', self.raw, offset); offset += 8
            if count % 4 or count > len(self.raw) - offset: raise ValueError('Invalid GLB chunk bounds')
            chunks.append((kind, self.raw[offset:offset + count])); offset += count
            if len(chunks) > 2: raise ValueError('Expected embedded JSON/BIN only')
        if [kind for kind, _ in chunks] != [0x4e4f534a, 0x004e4942] or len(chunks[0][1]) > MAX_JSON:
            raise ValueError('Expected bounded embedded JSON/BIN GLB')
        def constant(_): raise ValueError('Nonfinite GLB JSON')
        self.doc = json.loads(chunks[0][1], object_pairs_hook=unique, parse_constant=constant)
        if not isinstance(self.doc, dict) or self.doc.get('asset', {}).get('version') != '2.0':
            raise ValueError('Expected glTF2 asset')
        self.binary = bytearray(chunks[1][1])
        self.bind_origins = {}
        self._spring_nodes = None
        self.morph_operations = 0
        for key, maximum in [('nodes', 100000), ('meshes', 4096), ('skins', 1024), ('accessors', 100000), ('bufferViews', 100000)]:
            values = self.doc.get(key, [])
            if not isinstance(values, list) or len(values) > maximum or any(not isinstance(v, dict) for v in values):
                raise ValueError('Invalid GLB ' + key)
        buffers = self.doc.get('buffers', [])
        if len(buffers) != 1 or 'uri' in buffers[0] or type(buffers[0].get('byteLength')) is not int or not 0 <= buffers[0]['byteLength'] <= len(self.binary):
            raise ValueError('Expected one embedded buffer')
        for view in self.doc.get('bufferViews', []):
            start, count = view.get('byteOffset', 0), view.get('byteLength')
            if view.get('buffer', 0) != 0 or type(start) is not int or type(count) is not int or min(start, count) < 0 or start + count > buffers[0]['byteLength']:
                raise ValueError('Buffer view exceeds embedded data')
        for image in self.doc.get('images', []):
            if not isinstance(image, dict) or 'uri' in image and (not isinstance(image['uri'], str) or not image['uri'].startswith('data:')): raise ValueError('External images are not read by helper authoring')

    def ref(self, key, index): return self.doc[key][integer(index, len(self.doc.get(key, [])))]

    def accessor(self, index, kind=None, maximum=MAX_VERTICES):
        a = self.ref('accessors', index)
        if a.get('sparse'): raise ValueError('Sparse selected geometry/binds need a separate adapter')
        width = WIDTHS.get(a.get('type')); component = COMPONENTS.get(a.get('componentType'))
        count = a.get('count')
        if not width or not component or type(count) is not int or not 0 < count <= maximum or kind and a['type'] != kind:
            raise ValueError('Unsupported helper accessor layout')
        fmt, size, divisor = component; view = self.ref('bufferViews', a.get('bufferView'))
        if view.get('buffer', 0) != 0: raise ValueError('External helper buffer')
        view_start = view.get('byteOffset', 0); view_size = view.get('byteLength'); start = a.get('byteOffset', 0)
        stride = view.get('byteStride', width * size)
        if any(type(v) is not int or v < 0 for v in [view_start, view_size, start, stride]) or stride < width * size or stride > 252:
            raise ValueError('Invalid helper accessor stride')
        if view_start + view_size > self.doc['buffers'][0]['byteLength'] or start + (count - 1) * stride + width * size > view_size:
            raise ValueError('Helper accessor exceeds buffer view')
        normalized = a.get('normalized', False)
        if type(normalized) is not bool or normalized and a['componentType'] not in (5121, 5123):
            raise ValueError('Unsupported normalized helper accessor')
        result = [struct.unpack_from('<' + fmt * width, self.binary, view_start + start + i * stride) for i in range(count)]
        if normalized: result = [tuple(v / divisor for v in row) for row in result]
        if any(not math.isfinite(v) or abs(v) > 100000 for row in result for v in row):
            raise ValueError('Nonfinite or excessive selected geometry')
        return result

    def append(self, rows, kind, component=5126):
        fmt, size, _ = COMPONENTS[component]; width = WIDTHS[kind]
        self.binary.extend(b'\0' * (-len(self.binary) % 4)); start = len(self.binary)
        for row in rows:
            if len(row) != width: raise ValueError('Invalid generated accessor width')
            self.binary.extend(struct.pack('<' + fmt * width, *row))
        views = self.doc.setdefault('bufferViews', []); accessors = self.doc.setdefault('accessors', [])
        views.append({'buffer': 0, 'byteOffset': start, 'byteLength': len(rows) * width * size})
        accessors.append({'bufferView': len(views) - 1, 'componentType': component, 'count': len(rows), 'type': kind})
        return len(accessors) - 1

    def morph_rows(self, view_index, offset, count, width, component, packed=False):
        """Bounded raw morph/sparse rows; never modifies source accessors."""
        view = self.ref('bufferViews', view_index)
        fmt, size, _ = COMPONENTS[component]
        stride = view.get('byteStride', width * size)
        if (type(offset) is not int or offset < 0 or offset % size or
                type(stride) is not int or not width * size <= stride <= 252 or stride % size or
                packed and 'byteStride' in view or view.get('byteOffset', 0) % size or
                offset + (count - 1) * stride + width * size > view['byteLength']):
            raise ValueError('Invalid morph buffer layout or bounds')
        return [struct.unpack_from('<' + fmt * width, self.binary,
                view.get('byteOffset', 0) + offset + i * stride) for i in range(count)]

    def morph_delta(self, index, count):
        accessor = self.ref('accessors', index)
        if (accessor.get('type') != 'VEC3' or accessor.get('componentType') != 5126 or
                type(accessor.get('count')) is not int or accessor['count'] != count or accessor.get('normalized', False)):
            raise ValueError('Morph POSITION must match the source float VEC3 vertices')
        if 'bufferView' in accessor:
            result = self.morph_rows(accessor['bufferView'], accessor.get('byteOffset', 0), count, 3, 5126)
        else:
            if accessor.get('byteOffset', 0) != 0: raise ValueError('Morph without base buffer has a byte offset')
            result = [(0., 0., 0.)] * count
        if 'sparse' in accessor:
            sparse = accessor['sparse']
            if not isinstance(sparse, dict) or type(sparse.get('count')) is not int or not 0 < sparse['count'] <= count:
                raise ValueError('Invalid sparse morph count')
            indices, values = sparse.get('indices'), sparse.get('values')
            if not isinstance(indices, dict) or not isinstance(values, dict) or indices.get('componentType') not in (5121, 5123, 5125):
                raise ValueError('Invalid sparse morph references')
            ids = [r[0] for r in self.morph_rows(indices.get('bufferView'), indices.get('byteOffset', 0), sparse['count'], 1, indices['componentType'], True)]
            if any(not 0 <= v < count or i and v <= ids[i-1] for i, v in enumerate(ids)):
                raise ValueError('Sparse morph indices must be ordered, unique and in range')
            rows = self.morph_rows(values.get('bufferView'), values.get('byteOffset', 0), sparse['count'], 3, 5126, True)
            for i, row in zip(ids, rows): result[i] = row
        if any(not math.isfinite(v) or abs(v) > 100000 for row in result for v in row):
            raise ValueError('Invalid morph POSITION displacement')
        return result

    def morph_weights(self, node_index, options=None):
        options = {} if options is None else options
        if not isinstance(options, dict) or type(options.get('source_morph_defaults', False)) is not bool:
            raise ValueError('Invalid source morph defaults setting')
        overrides = options.get('morph_weights', {})
        if not isinstance(overrides, dict) or len(overrides) > 1024:
            raise ValueError('Invalid morph snapshot')
        for key, value in overrides.items():
            if not isinstance(key, str) or not key.isascii() or not key.isdecimal() or str(int(key)) != key:
                raise ValueError('Morph snapshot needs canonical source node indices')
            other = self.ref('nodes', int(key))
            if 'mesh' not in other or not isinstance(value, list) or len(value) > 2048: raise ValueError('Invalid morph snapshot node')
            other_mesh = self.ref('meshes', other['mesh'])
            if any(len(p.get('targets', [])) != len(value) for p in other_mesh.get('primitives', [])):
                raise ValueError('Morph snapshot weights must match every target')
            for weight in value: finite(weight, -100., 100.)
        node = self.ref('nodes', node_index); mesh = self.ref('meshes', node.get('mesh'))
        counts = [len(p.get('targets', [])) for p in mesh.get('primitives', [])]
        count = counts[0] if counts else 0
        if count > 2048 or any(n != count for n in counts): raise ValueError('Inconsistent or excessive morph targets')
        weights = overrides.get(str(node_index))
        if weights is None:
            weights = node.get('weights', mesh.get('weights', [0.] * count)) if options.get('source_morph_defaults', False) else [0.] * count
        if not isinstance(weights, list) or len(weights) != count:
            raise ValueError('Morph weights must match every target')
        return [finite(w, -100., 100.) for w in weights]

    def shaped_skin(self, node_index, primitive_index, options=None):
        data = self.skin(node_index, primitive_index)
        if options is None or isinstance(options, dict) and not shape_requested(options):
            return data
        weights = self.morph_weights(node_index, options)
        active = [(target, w) for target, w in zip(data[2].get('targets', []), weights) if w != 0 and 'POSITION' in target]
        operations = len(data[4]) * len(active)
        self.morph_operations += operations
        if operations > 2000000 or self.morph_operations > 8000000:
            raise ValueError('Morph review exceeds its bounded vertex evaluation budget')
        positions = [list(p) for p in data[4]]
        for target, weight in active:
            for p, delta in zip(positions, self.morph_delta(target['POSITION'], len(positions))):
                for k in range(3): p[k] += weight * delta[k]
        for p in positions:
            for v in p: finite(v)
        return (*data[:4], [tuple(p) for p in positions], *data[5:])

    def skin(self, node_index, primitive_index):
        node = self.ref('nodes', node_index); mesh = self.ref('meshes', node.get('mesh')); skin = self.ref('skins', node.get('skin'))
        primitive = mesh['primitives'][integer(primitive_index, len(mesh.get('primitives', [])))]
        if primitive.get('mode', 4) != 4 or primitive.get('extensions'): raise ValueError('Selected primitive must be decoded triangles')
        attributes = primitive.get('attributes', {}); positions = self.accessor(attributes.get('POSITION'), 'VEC3')
        indices = [i[0] for i in self.accessor(primitive['indices'], 'SCALAR', MAX_INDICES)] if 'indices' in primitive else list(range(len(positions)))
        if len(indices) % 3 or any(type(i) is not int or not 0 <= i < len(positions) for i in indices): raise ValueError('Invalid triangle indices')
        joints = skin.get('joints', [])
        if not joints or len(joints) > 512 or len(set(joints)) != len(joints): raise ValueError('Invalid or excessive source joints')
        for j in joints: self.ref('nodes', j)
        pairs = [[] for _ in positions]
        for slot in range(2):
            jkey, wkey = 'JOINTS_' + str(slot), 'WEIGHTS_' + str(slot)
            if slot == 1 and jkey not in attributes and wkey not in attributes: break
            ja = self.ref('accessors', attributes.get(jkey)); wa = self.ref('accessors', attributes.get(wkey))
            if ja.get('componentType') not in (5121, 5123) or ja.get('normalized', False) or wa.get('componentType') not in (5121, 5123, 5126): raise ValueError('Invalid skin attribute types')
            if wa['componentType'] != 5126 and not wa.get('normalized'): raise ValueError('Integer weights must be normalized')
            js = self.accessor(attributes[jkey], 'VEC4'); ws = self.accessor(attributes[wkey], 'VEC4')
            if len(js) != len(positions) or len(ws) != len(positions): raise ValueError('Skin attribute count mismatch')
            for i, (jr, wr) in enumerate(zip(js, ws)):
                for j, w in zip(jr, wr):
                    integer(j, len(joints)); finite(w, 0, 1)
                    if w > 0:
                        if j in dict(pairs[i]): raise ValueError('Duplicate weighted joint')
                        pairs[i].append((j, w))
        if any(k.startswith(('JOINTS_', 'WEIGHTS_')) and k.rsplit('_', 1)[-1] not in ('0', '1') for k in attributes): raise ValueError('More than8weights need review')
        if any(abs(sum(w for _, w in row) - 1) > 0.000002 for row in pairs): raise ValueError('Source weights need normalization before helper authoring')
        binds = self.accessor(skin['inverseBindMatrices'], 'MAT4', 1024) if 'inverseBindMatrices' in skin else [IDENTITY] * len(joints)
        if len(binds) < len(joints) or any(any(abs(row[i] - v) > 1e-6 for i, v in zip((3, 7, 11, 15), (0, 0, 0, 1))) for row in binds): raise ValueError('Invalid inverse bind matrices')
        return node, mesh, primitive, skin, positions, indices, pairs, binds[:len(joints)]

    def springs(self):
        extensions = self.doc.get('extensions', {})
        if not isinstance(extensions, dict): raise ValueError('Invalid extension list')
        native = extensions.get('VRMC_springBone', {}).get('springs', []) or extensions.get('VRM', {}).get('secondaryAnimation', {}).get('boneGroups', [])
        extra = self.doc.get('extras', {}).get('has_secondary_helpers_1', {})
        generated = extra.get('springs', [])
        if not isinstance(native, list) or not isinstance(generated, list) or len(native) + len(generated) > 128:
            raise ValueError('Invalid or excessive existing spring chains')
        return native + generated

    def spring_nodes(self):
        """Protect all weighted joints in declared chains, including their tails."""
        if self._spring_nodes is not None: return self._spring_nodes
        result = set()
        for chain in self.springs():
            if not isinstance(chain, dict): raise ValueError('Invalid existing spring chain')
            if 'joints' in chain:
                joints = chain['joints']
                if not isinstance(joints, list) or len(joints) > 512: raise ValueError('Invalid spring joints')
                for row in joints:
                    if not isinstance(row, dict): raise ValueError('Invalid spring joint')
                    result.add(integer(row.get('node'), len(self.doc['nodes'])))
            else:
                roots = chain.get('bones', [])
                if not isinstance(roots, list) or len(roots) > 128: raise ValueError('Invalid legacy spring roots')
                for root in roots:
                    at = integer(root, len(self.doc['nodes'])); seen = set()
                    while True:
                        if at in seen: raise ValueError('Cyclic existing spring chain')
                        seen.add(at); result.add(at)
                        children = self.doc['nodes'][at].get('children', [])
                        if not children: break
                        if not isinstance(children, list) or len(children) != 1: raise ValueError('Branched existing spring chain needs review')
                        at = integer(children[0], len(self.doc['nodes']))
        if len(result) > 512: raise ValueError('Existing spring joints exceed512')
        self._spring_nodes = result
        return result


def components(positions, indices):
    """Weld coincident seam vertices for topology only; never weld source geometry."""
    parent = list(range(len(positions))); welded = {}; ids = []
    extent = max(max(p[k] for p in positions) - min(p[k] for p in positions) for k in range(3))
    epsilon = max(extent * 1e-7, 1e-9)
    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i, p in enumerate(positions):
        key = tuple(round(v / epsilon) for v in p); representative = welded.setdefault(key, i); parent[i] = representative; ids.append(representative)
    graph = {i: {} for i in welded.values()}; edges = {}
    for offset in range(0, len(indices), 3):
        tri = [ids[i] for i in indices[offset:offset + 3]]
        for a, b in zip(tri, tri[1:] + tri[:1]):
            if a == b: continue
            x, y = find(a), find(b); parent[max(x, y)] = min(x, y)
            length = distance(positions[a], positions[b]); graph[a][b] = graph[b][a] = length
            edge = tuple(sorted((a, b))); edges[edge] = edges.get(edge, 0) + 1
    groups = {}
    for i in range(len(positions)): groups.setdefault(find(ids[i]), []).append(i)
    if len(groups) > 1024: raise ValueError('More than1024regions need a narrower mesh selection')
    return list(groups.values()), ids, graph, edges


def existing_chain(glb, skin, pairs, selected):
    """Offer one reviewed native chain; do not infer motion or rewrite its skin."""
    parents = {}
    for ni, node in enumerate(glb.doc['nodes']):
        for child in node.get('children', []):
            if type(child) is not int or not 0 <= child < len(glb.doc['nodes']) or child in parents:
                return None
            parents[child] = ni
    weighted = {skin['joints'][j] for v in selected for j, w in pairs[v] if w > 0}
    if not 3 <= len(weighted) <= 65 or weighted & glb.spring_nodes(): return None
    depths = {}
    for node in weighted:
        at = node; seen = set()
        while at in parents:
            if at in seen or len(seen) >= 512: return None
            seen.add(at); at = parents[at]
        depths[node] = len(seen)
    ordered = sorted(weighted, key=lambda n: (depths[n], n))
    if any(parents.get(b) != a for a, b in zip(ordered, ordered[1:])): return None
    center, joints = ordered[0], ordered[1:]
    binds = glb.accessor(skin['inverseBindMatrices'], 'MAT4', 1024) if 'inverseBindMatrices' in skin else [IDENTITY] * len(skin['joints'])
    indices = [skin['joints'].index(n) for n in ordered]
    origins = [bind_origin(binds[i]) for i in indices]
    if any(distance(a, b) < 1e-6 for a, b in zip(origins, origins[1:])): return None
    tail = tuple(origins[-1][k] + (origins[-1][k] - origins[-2][k]) * .5 for k in range(3))
    points = [point(binds[indices[0]], p) for p in origins[1:] + [tail]]
    tail_offset = point(binds[indices[-1]], tail)
    if any(not math.isfinite(v) or abs(v) > 100000 for p in points + [tail_offset] for v in p): return None
    return {'center_node': center, 'center_name': str(glb.doc['nodes'][center].get('name', ''))[:256],
            'joint_nodes': joints, 'joint_names': [str(glb.doc['nodes'][n].get('name', ''))[:256] for n in joints],
            'points_in_anchor': points, 'tail_offset': tail_offset,
            'method': 'reviewed existing weighted hierarchy with an unweighted terminal endpoint'}


def existing_affected(glb, proposal, shape=None):
    """Enumerate all geometry sharing the rotating native joints for disclosure."""
    nodes = set(proposal['joint_nodes']); regions = []; vertices = []; lines = set(); total = 0
    for ni, node in enumerate(glb.doc['nodes']):
        if 'mesh' not in node or 'skin' not in node: continue
        mesh = glb.ref('meshes', node['mesh'])
        for pi in range(len(mesh.get('primitives', []))):
            data = glb.shaped_skin(ni, pi, shape)
            skin, positions, indices, pairs, binds = data[3], data[4], data[5], data[6], data[7]
            total += len(positions)
            if total > 500000: raise ValueError('Shared-joint review exceeds500kvertices; choose a narrower asset')
            topology = components(glb.skin(ni, pi)[4] if shape_requested(shape) else positions, indices)
            groups = topology[0]
            for ci, whole in enumerate(groups):
                touched = [v for v in whole if any(skin['joints'][j] in nodes for j, w in pairs[v])]
                if not touched: continue
                if len(regions) >= 1024 or len(vertices) + len(whole) > 10000:
                    raise ValueError('Shared-joint preview exceeds its bounded region/vertex budget')
                summary = region(glb, ni, pi, ci, context=(data, topology))[-1]
                regions.append({'node': ni, 'primitive': pi, 'component': ci,
                                'material_name': summary['material_name'], 'vertices': len(whole),
                                'affected_vertices': len(touched)})
                selected = set(whole); mapping = {v: len(vertices) + i for i, v in enumerate(whole)}
                for v in whole:
                    vertices.append([[skin['joints'][j], *point(binds[j], positions[v]), w] for j, w in pairs[v]])
                for at in range(0, len(indices), 3):
                    tri = indices[at:at + 3]
                    if all(v in selected for v in tri):
                        for a, b in zip(tri, tri[1:] + tri[:1]): lines.add(tuple(sorted((mapping[a], mapping[b]))))
    if not regions: raise ValueError('Existing chain does not affect any reviewed geometry')
    return regions, vertices, sorted(lines)


def region(glb, node_index, primitive_index, component_index, anchor=None, context=None, vertex_mask=None, shape=None):
    data, topology = context if context else (glb.shaped_skin(node_index, primitive_index, shape), None)
    node, mesh, primitive, skin, positions, indices, pairs, binds = data
    # Keep component IDs and UV seam identity stable as shapes move. Distances,
    # controls and attachment coordinates use the evaluated shape instead.
    groups, welded, graph, edges = topology if topology else components(glb.skin(node_index, primitive_index)[4] if shape_requested(shape) else positions, indices)
    whole = groups[integer(component_index, len(groups))]
    selected = whole
    if vertex_mask is not None:
        if not isinstance(vertex_mask, list) or not 3 <= len(vertex_mask) <= MAX_VERTICES or any(type(v) is not int for v in vertex_mask):
            raise ValueError('Choose at least3vertices in one connected patch')
        chosen = set(vertex_mask)
        if len(chosen) != len(vertex_mask) or not chosen.issubset(set(whole)): raise ValueError('Patch has duplicate or out-of-region vertices')
        # UV seams must keep their coincident vertices together. Source geometry
        # is never welded; only the edit mask expands across these seam copies.
        seam = {welded[v] for v in chosen}; selected = [v for v in whole if welded[v] in seam]
    if len(selected) < 3: raise ValueError('Region has no usable triangle surface')
    totals = {}
    for v in selected:
        for j, w in pairs[v]: totals[j] = totals.get(j, 0) + w
    joint = max(totals, key=totals.get) if anchor is None else skin['joints'].index(anchor)
    protected = glb.spring_nodes()
    already_rigged = any(skin['joints'][j] in protected for v in selected for j, w in pairs[v])
    coords = {v: point(binds[joint], positions[v]) for v in selected}
    representatives = set(welded[v] for v in selected)
    if vertex_mask is not None:
        reached = set(); pending = [min(representatives)]
        while pending:
            v = pending.pop()
            if v in reached: continue
            reached.add(v); pending.extend(other for other in graph[v] if other in representatives and other not in reached)
        if reached != representatives: raise ValueError('Choose one connected patch; set up separate parts in separate steps')
        chosen = set(selected)
        if not any(all(v in chosen for v in indices[i:i+3]) for i in range(0,len(indices),3)): raise ValueError('Patch must include a triangle surface')
    start = min(representatives, key=lambda v: (sum(x * x for x in coords[v]), v))
    bounds = [[min(coords[v][k] for v in selected) for k in range(3)], [max(coords[v][k] for v in selected) for k in range(3)]]
    axis = max(range(3), key=lambda k: bounds[1][k] - bounds[0][k])
    # Seed the whole attachment cross-section, rather than one corner. A single
    # seed makes a rigidly attached strip peel diagonally across its root seam.
    # This remains a reviewed geometric estimate, not a clothing classifier.
    band = max((bounds[1][axis] - bounds[0][axis]) * .03, 1e-9)
    cut_boundary = {v for v in representatives if any(other not in representatives for other in graph[v])} if vertex_mask is not None else set()
    roots = sorted(cut_boundary or {v for v in representatives if abs(coords[v][axis] - coords[start][axis]) <= band})
    root_set = set(roots)
    distances = {v: 0. for v in roots}; queue = [(0., v) for v in roots]; heapq.heapify(queue)
    while queue:
        value, v = heapq.heappop(queue)
        if value != distances[v]: continue
        for other in graph[v]:
            if other not in representatives: continue
            next_value = value + distance(coords[v], coords[other])
            if next_value < distances.get(other, math.inf): distances[other] = next_value; heapq.heappush(queue, (next_value, other))
    length = max(distances.values())
    if length < 1e-6: raise ValueError('Patch has no free span; include a free hem or edge before adding joints')
    coverage = min(dict(pairs[v]).get(joint, 0) for v in selected)
    if id(skin) not in glb.bind_origins: glb.bind_origins[id(skin)] = [bind_origin(m) for m in binds]
    rig_points = [point(binds[joint], p) for p in glb.bind_origins[id(skin)]]
    rig_span = math.sqrt(sum((max(p[k] for p in rig_points) - min(p[k] for p in rig_points)) ** 2 for k in range(3)))
    relative_length = length / rig_span if rig_span > 1e-6 else 0.
    # A region spanning another existing joint can be ordinary body geometry or
    # an already articulated part. Do not advertise it as a missing loose rig.
    nearby = False
    for j, origin in enumerate(glb.bind_origins[id(skin)]):
        p = point(binds[joint], origin)
        if j != joint and distance(p, coords[start]) > length * .5 and min(distance(p, coords[v]) for v in selected) < length * .3:
            nearby = True; break
    extents = sorted((bounds[1][k] - bounds[0][k] for k in range(3)), reverse=True)
    boundary = sum(1 for (a, b), count in edges.items() if count == 1 and a in distances and b in distances)
    material_name = ''
    if 'material' in primitive:
        name = glb.ref('materials', primitive['material']).get('name', '')
        if isinstance(name, str): material_name = name[:128]
    report = {'node': node_index, 'primitive': primitive_index, 'component': component_index,
              'material_name': material_name,
              'vertices': len(selected), 'anchor_node': skin['joints'][joint], 'anchor_name': str(glb.doc['nodes'][skin['joints'][joint]].get('name', ''))[:256],
              'anchor_min_weight': coverage, 'length_in_anchor_units': length, 'bounds_in_anchor': bounds,
              'length_relative_to_rig': relative_length,
              'attachment_vertices': sum(welded[v] in root_set for v in selected),
              'attachment_method': 'pinned cut boundary' if cut_boundary else 'nearest-anchor cross-section within3percent of longest local extent',
              'elongation': extents[0] / max(extents[1], 1e-9), 'boundary_edges': boundary,
              'existing_joint_near_free_region': nearby,
              'already_rigged': already_rigged,
              'suggested': not already_rigged and coverage >= .95 and extents[0] > 2 * extents[1] and boundary > 0 and not nearby and relative_length >= .06,
              'assessment': 'Geometry/weights suggest a strand or panel; review attachment and stiffness. Length cannot establish looseness.'}
    proposal = existing_chain(glb, skin, pairs, selected)
    if proposal is not None: report['existing_chain'] = proposal
    if vertex_mask is not None: report['vertex_mask'] = selected
    return data, selected, welded, distances, coords, joint, report


def inspect(source, shape=None):
    glb = GLB(source); rows = []; skipped = []; total = 0
    def result(truncated=False):
        return {'format': 'studio_secondary_assessment_1', 'source_sha256': glb.sha, 'existing_springs': bool(glb.springs()), 'regions': rows, 'skipped': skipped, 'truncated': truncated}
    for ni, node in enumerate(glb.doc.get('nodes', [])):
        if len(skipped) >= 1024:
            skipped.append({'reason': 'Assessment stopped at1024unsupported sections'}); return result(True)
        if 'mesh' not in node: continue
        if 'skin' not in node: skipped.append({'node': ni, 'reason': 'Unskinned mesh: anchor/rig authoring is still required'}); continue
        mesh = glb.ref('meshes', node['mesh'])
        for pi in range(len(mesh.get('primitives', []))):
            try:
                data = glb.shaped_skin(ni, pi, shape); total += len(data[4])
                if total > 500000:
                    skipped.append({'node': ni, 'primitive': pi, 'reason': 'Assessment stopped at500kvertices; choose a narrower asset'}); return result(True)
                topology = components(glb.skin(ni, pi)[4] if shape_requested(shape) else data[4], data[5]); groups = topology[0]
                for ci, values in enumerate(groups):
                    if len(rows) >= 1024:
                        skipped.append({'node': ni, 'primitive': pi, 'reason': 'Assessment stopped at1024regions'}); return result(True)
                    if len(values) >= 3: rows.append(region(glb, ni, pi, ci, context=(data, topology))[-1])
            except ValueError as error: skipped.append({'node': ni, 'primitive': pi, 'reason': str(error)})
    return result()


def control_points(coords, distances, count):
    length = max(distances.values()); controls = []
    for i in range(count + 1):
        target = i / count; values = sorted(distances, key=lambda v: abs(distances[v] / length - target))
        near = values[:max(1, sum(abs(distances[v] / length - target) <= .08 for v in values))]
        controls.append([sum(coords[v][k] for v in near) / len(near) for k in range(3)])
    return controls


def preview(source, request):
    glb = GLB(source)
    if request.get('source_sha256') != glb.sha: raise ValueError('Model changed; inspect it again')
    data, selected, welded, distances, coords, joint, summary = region(glb, request.get('node'), request.get('primitive'), request.get('component'), request.get('anchor_node'), vertex_mask=request.get('vertex_mask'), shape=request)
    node, mesh, primitive, skin, positions, indices, pairs, binds = data
    use_existing = request.get('use_existing_joints', False)
    if type(use_existing) is not bool: raise ValueError('Invalid existing-joint choice')
    if use_existing:
        proposal = summary.get('existing_chain')
        if not proposal: raise ValueError('This part has no available unconfigured linear joint chain')
        if len(glb.spring_nodes() | set(proposal['joint_nodes'])) + 1 > 512:
            raise ValueError('Existing chain endpoint exceeds512spring-node budget')
        if 'vertex_mask' in request: raise ValueError('Review the whole shared-joint group instead of a smaller patch')
        affected, vertices, lines = existing_affected(glb, proposal, request)
        summary = dict(summary, anchor_node=proposal['center_node'], anchor_name=proposal['center_name'])
        bindings = sorted({proposal['center_node']} | {int(influence[0]) for vertex in vertices for influence in vertex})
        return {'format': 'studio_secondary_preview_1', 'mode': 'existing_joints', 'region': summary,
                'vertices': vertices, 'source_vertices': list(range(len(vertices))),
                'selected_vertices': list(range(len(vertices))), 'can_apply': True, 'edges': lines,
                'points_in_anchor': proposal['points_in_anchor'], 'existing_chain': proposal,
                'affected_regions': affected, 'affected_vertices': sum(r['affected_vertices'] for r in affected),
                'anchors': [{'node': n, 'name': str(glb.doc['nodes'][n].get('name', ''))[:256],
                             'available': n == proposal['center_node']} for n in bindings]}
    can_apply = not summary['already_rigged'] and summary['anchor_min_weight'] >= .01
    if not request.get('review_only', False):
        if summary['already_rigged']: raise ValueError('This region already uses spring joints; its existing rig and weights were kept')
        if summary['anchor_min_weight'] < .01: raise ValueError('This part has no usable weights at that attachment; choose one of its weighted joints')
    whole = components(glb.skin(request.get('node'), request.get('primitive'))[4] if shape_requested(request) else positions, indices)[0][integer(request.get('component'),1024)]
    if len(whole) > 5000: raise ValueError('Part preview exceeds5000vertices; a narrower region editor is still required')
    count = request.get('segments', 3)
    if type(count) is not int or not 2 <= count <= 8: raise ValueError('Use2–8helper segments')
    selected_set = set(selected); mapping = {v: i for i, v in enumerate(whole)}; lines = set()
    for at in range(0, len(indices), 3):
        tri = indices[at:at + 3]
        if not all(v in selected_set for v in tri): continue
        for a, b in zip(tri, tri[1:] + tri[:1]): lines.add(tuple(sorted((mapping[a], mapping[b]))))
    vertices = []
    for v in whole:
        vertices.append([[skin['joints'][j], *point(binds[j], positions[v]), w] for j, w in pairs[v]])
    return {'format': 'studio_secondary_preview_1', 'region': summary, 'vertices': vertices, 'source_vertices': whole,
            'selected_vertices': [mapping[v] for v in selected], 'can_apply': can_apply, 'edges': sorted(lines),
            'points_in_anchor': control_points(coords, distances, count),
            'anchors': [{'node': j, 'name': str(glb.doc['nodes'][j].get('name', ''))[:256],
                         'available': min(dict(pairs[v]).get(ji, 0) for v in selected) >= .01}
                        for ji, j in enumerate(skin['joints'])]}


def build(source, output, request):
    glb = GLB(source); original_stat = glb.source.stat().st_mtime_ns
    if not isinstance(request, dict) or request.get('source_sha256') != glb.sha or request.get('reviewed') is not True:
        raise ValueError('A reviewed region and matching source checksum are required')
    if len(glb.springs()) >= 128: raise ValueError('Additional helpers exceed128spring chains')
    if type(request.get('use_existing_joints', False)) is not bool: raise ValueError('Invalid existing-joint choice')
    if request.get('use_existing_joints', False): return build_existing(glb, output, request, original_stat)
    count = request.get('segments', 3); integer(count - 1 if type(count) is int else None, 8)
    if count < 2: raise ValueError('Use2–8helper segments')
    strength = finite(request.get('strength', .95), .01, 1); pin = finite(request.get('pin_fraction', .2), .01, .4)
    data, selected, welded, distances, coords, joint, summary = region(glb, request.get('node'), request.get('primitive'), request.get('component'), request.get('anchor_node'), vertex_mask=request.get('vertex_mask'), shape=request)
    node, mesh, primitive, skin, positions, indices, pairs, binds = data
    if summary['already_rigged']: raise ValueError('This region already uses spring joints; its existing rig and weights were kept')
    if sum(n.get('mesh') == node['mesh'] for n in glb.doc['nodes']) != 1:
        raise ValueError('This geometry is shared by multiple source nodes; make a separate mesh revision before adding helpers')
    if min(dict(pairs[v]).get(joint, 0) for v in selected) < .01: raise ValueError('Selected region is not attached to that anchor')
    if len(set(j for s in glb.doc['skins'] for j in s['joints'])) + count + 1 > 512: raise ValueError('Helpers exceed512bone budget')
    length = max(distances.values()); controls = request.get('points_in_anchor')
    if controls is None:
        controls = control_points(coords, distances, count)
    if not isinstance(controls, list) or len(controls) != count + 1 or any(not isinstance(p, (list, tuple)) or len(p) != 3 for p in controls): raise ValueError('Invalid reviewed helper control points')
    controls = [tuple(finite(v) for v in p) for p in controls]
    if any(distance(a, b) < length * .001 for a, b in zip(controls, controls[1:])): raise ValueError('Helper chain folds to a zero-length segment; revise its points')
    nodes = glb.doc['nodes']; first = len(nodes); base = len(skin['joints']); names = {n.get('name', '') for n in nodes}
    prefix = '__HAS_Loose_' + hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()[:12]
    if any(prefix + '_' + str(i) in names for i in range(count + 1)): raise ValueError('Generated helper identity collision')
    report = {'format': 'studio_generated_helpers_1', 'source_sha256': glb.sha, 'region': summary,
              'points_in_anchor': controls, 'strength': strength, 'pin_fraction': pin,
              'method': 'reviewed welded topology/geodesic bands; anchor-weight transfer; linear joint blend',
              'changed_vertices': 0, 'helper_nodes': list(range(first, first + count + 1))}
    if shape_requested(request):
        report['review_morph_weights'] = glb.morph_weights(request.get('node'), request)
    for i, p in enumerate(controls):
        parent = nodes[skin['joints'][joint]] if i == 0 else nodes[-1]
        parent.setdefault('children', []).append(len(nodes))
        nodes.append({'name': prefix + '_' + str(i), 'translation': [p[k] - (controls[i - 1][k] if i else 0) for k in range(3)],
                      'extras': {'has_generated_helper': {'source_sha256': glb.sha, 'chain': prefix, 'joint': i, 'authoring': report if i == 0 else {}}}})
        skin['joints'].append(first + i)
        generated_bind = multiply(translation([-v for v in p]), binds[joint])
        if any(not math.isfinite(v) or abs(v) > 100000 for v in generated_bind): raise ValueError('Generated helper transforms exceed the supported coordinate range')
        binds.append(generated_bind)
    for v in selected:
        s = distances[welded[v]] / length; fraction = min(1., s / pin); transfer = strength * fraction * fraction * (3 - 2 * fraction)
        weights = dict(pairs[v]); old = weights[joint]; weights[joint] = old * (1 - transfer)
        u = min(count - 1., s * count); left = min(count - 1, int(u)); right = min(count - 1, left + 1); t = u - left
        weights[base + left] = weights.get(base + left, 0) + old * transfer * (1 - t)
        weights[base + right] = weights.get(base + right, 0) + old * transfer * t
        pairs[v] = [(j, w) for j, w in weights.items() if w > 0]
        if len(pairs[v]) > 8: raise ValueError('Reviewed weight transfer would exceed8influences; no weights were discarded')
        report['changed_vertices'] += int(transfer > 0)
    if report['changed_vertices'] == 0: raise ValueError('Reviewed region produces no effective weights')
    # Keep mesh indices stable for retained native expression/material bindings.
    # Shared source instances require a separate ownership workflow, not a silent
    # clone that would invalidate extension references to the original mesh.
    attributes = primitive['attributes']; slots = 8 if max(map(len, pairs)) > 4 or 'JOINTS_1' in attributes else 4
    for slot in range(slots // 4):
        js, ws = [], []
        for row in pairs:
            padded = row + [(0, 0.)] * (slots - len(row)); part = padded[slot * 4:slot * 4 + 4]
            js.append([j for j, w in part]); ws.append([w for j, w in part])
        attributes['JOINTS_' + str(slot)] = glb.append(js, 'VEC4', 5123)
        attributes['WEIGHTS_' + str(slot)] = glb.append(ws, 'VEC4')
    skin['inverseBindMatrices'] = glb.append(binds, 'MAT4')
    # Keep imported VRM0/1 and older HAS chains byte-for-byte in their original
    # JSON fields. Generated additions have their own native HAS asset metadata,
    # so adding a chain never shadows a legacy VRM0 secondaryAnimation block.
    spring = glb.doc.setdefault('extras', {}).setdefault('has_secondary_helpers_1', {'specVersion': '1.0', 'springs': []})
    spring['springs'].append({'name': prefix, 'center': skin['joints'][joint], 'joints': [{'node': first + i, 'stiffness': 1., 'dragForce': .45, 'hitRadius': .005} for i in range(count + 1)]})
    glb.binary.extend(b'\0' * (-len(glb.binary) % 4)); glb.doc['buffers'][0]['byteLength'] = len(glb.binary)
    encoded = json.dumps(glb.doc, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode(); encoded += b' ' * (-len(encoded) % 4)
    if len(encoded) > MAX_JSON: raise ValueError('Derived GLB JSON exceeds16MiB; simplify the asset metadata first')
    raw = struct.pack('<4sII', b'glTF', 2, 28 + len(encoded) + len(glb.binary)) + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded + struct.pack('<II', len(glb.binary), 0x004e4942) + glb.binary
    if len(raw) > MAX_FILE: raise ValueError('Derived asset exceeds128MiB')
    if hashlib.sha256(glb.source.read_bytes()).hexdigest() != glb.sha or glb.source.stat().st_mtime_ns != original_stat: raise ValueError('Source changed during helper authoring')
    output = Path(output).resolve()
    if output == glb.source or output.exists(): raise ValueError('Choose a new derived asset folder; existing files are never replaced')
    output.mkdir(parents=True, exist_ok=False)
    temporary = output / 'scene.glb.tmp'
    with temporary.open('xb') as f: f.write(raw); f.flush(); os.fsync(f.fileno())
    os.replace(temporary, output / 'scene.glb')
    (output / 'helpers.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return {'glb': str(output / 'scene.glb'), 'report': report}


def build_existing(glb, output, request, original_stat):
    if request.get('use_existing_joints') is not True: raise ValueError('Invalid existing-joint choice')
    if len(glb.doc['nodes']) >= 100000: raise ValueError('Existing endpoint exceeds100000source-node budget')
    value = preview(glb.source, request); proposal = value['existing_chain']
    nodes = glb.doc['nodes']; first = len(nodes); parent = proposal['joint_nodes'][-1]
    prefix = '__HAS_Existing_' + hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()[:12]
    if any(n.get('name') == prefix + '_End' for n in nodes): raise ValueError('Existing-chain endpoint identity collision')
    nodes[parent].setdefault('children', []).append(first)
    nodes.append({'name': prefix + '_End', 'translation': list(proposal['tail_offset']),
                  'extras': {'has_generated_helper_endpoint': {'source_sha256': glb.sha, 'chain': prefix}}})
    report = {'format': 'studio_generated_helpers_1', 'mode': 'existing_joints', 'source_sha256': glb.sha,
              'region': value['region'], 'method': proposal['method'], 'helper_nodes': [first],
              'configured_nodes': proposal['joint_nodes'], 'points_in_anchor': proposal['points_in_anchor'],
              'affected_regions': value['affected_regions'], 'affected_vertices': value['affected_vertices'],
              'changed_vertices': 0, 'source_skin_preserved': True}
    spring = glb.doc.setdefault('extras', {}).setdefault('has_secondary_helpers_1', {'specVersion': '1.0', 'springs': []})
    spring['springs'].append({'name': prefix, 'center': proposal['center_node'],
                             'joints': [{'node': n, 'stiffness': 1., 'dragForce': .45, 'hitRadius': .005}
                                        for n in proposal['joint_nodes'] + [first]]})
    # No accessor, skin, material, morph or binary buffer is rewritten. The only
    # new scene node is an unweighted tail so the last native skin bone rotates.
    encoded = json.dumps(glb.doc, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()
    encoded += b' ' * (-len(encoded) % 4)
    if len(encoded) > MAX_JSON: raise ValueError('Derived GLB JSON exceeds16MiB; simplify the asset metadata first')
    raw = struct.pack('<4sII', b'glTF', 2, 28 + len(encoded) + len(glb.binary)) + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded + struct.pack('<II', len(glb.binary), 0x004e4942) + glb.binary
    if len(raw) > MAX_FILE: raise ValueError('Derived asset exceeds128MiB')
    if hashlib.sha256(glb.source.read_bytes()).hexdigest() != glb.sha or glb.source.stat().st_mtime_ns != original_stat:
        raise ValueError('Source changed during helper authoring')
    output = Path(output).resolve()
    if output == glb.source or output.exists(): raise ValueError('Choose a new derived asset folder; existing files are never replaced')
    output.mkdir(parents=True, exist_ok=False); temporary = output / 'scene.glb.tmp'
    with temporary.open('xb') as f: f.write(raw); f.flush(); os.fsync(f.fileno())
    os.replace(temporary, output / 'scene.glb')
    (output / 'helpers.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return {'glb': str(output / 'scene.glb'), 'report': report}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('source'); parser.add_argument('--request'); parser.add_argument('--output')
    args = parser.parse_args()
    if args.request:
        if not args.output: parser.error('--request requires a fresh --output folder')
        if Path(args.request).stat().st_size > 1024 * 1024: parser.error('Request exceeds1MiB')
        print(json.dumps(build(args.source, args.output, json.loads(Path(args.request).read_text(encoding='utf-8'))), indent=2))
    else: print(json.dumps(inspect(args.source), indent=2))
