"""CPU-only semantic preservation for a deliberately closed embedded glTF profile.

Inputs are parsed JSON documents and immutable BIN bytes in RAM. This module has
no file reader/writer, GLB packer, native launcher or model reconstruction code.
"""
import copy
import hashlib
import json
import math
import re
import struct

CARRIER = '_HAS_NATIVE_NORMAL_ID'
COMPONENTS = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2),
              5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4)}
ARITY = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
TEXTURE_FIELDS = {'baseColorTexture', 'metallicRoughnessTexture', 'normalTexture',
                  'occlusionTexture', 'emissiveTexture'}
ALLOWED_EXTENSIONS = {'KHR_materials_unlit', 'KHR_texture_transform'}


class Refusal(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise Refusal(message)


def freeze(value, internal=False):
    """Preserve JSON numeric types and IEEE signed zero; dictionary order is immaterial."""
    kind = type(value)
    if value is None: return ('null',)
    if kind is bool: return ('bool', value)
    if kind is int: return ('int', value)
    if kind is float:
        need(math.isfinite(value), 'Nonfinite JSON number')
        return ('float64', struct.pack('<d', value))
    if kind is str: return ('str', value)
    if kind is list: return ('list', tuple(freeze(x, internal) for x in value))
    if kind is dict:
        need(all(type(k) is str for k in value), 'Non-string JSON key')
        return ('dict', tuple((k, freeze(value[k], internal)) for k in sorted(value)))
    if internal and kind is bytes: return ('component-bytes', value)
    raise Refusal('Unsupported JSON value type')


def integer(value, minimum=0):
    need(type(value) is int and value >= minimum, 'Integer index/count/offset required')
    return value


def parse_json_document(raw):
    """Strict optional JSON-chunk reader; does not read a file or construct a GLB."""
    need(type(raw) is bytes and len(raw) <= 64 * 1024 * 1024, 'Bounded UTF-8 JSON bytes required')
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'Duplicate JSON object key')
            result[key] = value
        return result
    def number(token):
        need(token != '-0', 'Lexical integer negative zero refused before sign information is lost')
        return int(token)
    def invalid(token):
        raise Refusal('Nonfinite JSON token: ' + token)
    try:
        document = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_int=number, parse_constant=invalid)
    except (UnicodeError, ValueError) as error:
        raise Refusal('Strict JSON parse refused') from error
    need(type(document) is dict, 'Top-level JSON object required')
    freeze(document)
    return document


def fields(value, allowed):
    need(type(value) is dict and set(value) <= set(allowed) | {'name', 'extras', 'extensions'}, 'Unsupported object fields')


class Snapshot:
    def __init__(self, document, binary, carrier):
        need(type(document) is dict and type(binary) is bytes, 'JSON object and immutable BIN bytes required')
        self.original = freeze(document)
        self.doc = copy.deepcopy(document)
        self.binary = binary
        self.carrier = carrier
        self.used_accessors = set()
        self.used_views = set()
        self.normal_hashes = []
        self.primitive_count = 0
        self.carrier_count = 0
        self.image_bytes = 0
        fields(self.doc, {'asset', 'scene', 'scenes', 'nodes', 'meshes', 'materials', 'textures', 'images',
                          'samplers', 'skins', 'animations', 'cameras', 'accessors', 'bufferViews', 'buffers',
                          'extensionsUsed', 'extensionsRequired'})
        fields(self.doc.get('asset'), {'version', 'minVersion', 'generator', 'copyright'})
        need(self.doc['asset'].get('version') == '2.0' and self.doc['asset'].get('minVersion', '2.0') == '2.0', 'glTF 2.0 only')
        self.extension_profile(self.doc)
        for name in ('scenes', 'nodes', 'meshes', 'materials', 'textures', 'images', 'samplers',
                     'skins', 'animations', 'cameras', 'accessors', 'bufferViews', 'buffers'):
            need(type(self.doc.get(name, [])) is list, 'Resource table must be a list')
        need(len(self.doc.get('buffers', [])) == 1, 'One embedded BIN buffer only')
        buffer = self.doc['buffers'][0]
        fields(buffer, {'byteLength', 'uri'})
        need('uri' not in buffer, 'External/data URI buffer refused')
        declared = integer(buffer.get('byteLength'), 1)
        need(declared <= len(binary) <= declared + 3 and len(binary) <= 256 * 1024 * 1024, 'BIN length/padding/profile bound')
        self.declared = declared
        for view in self.doc.get('bufferViews', []):
            fields(view, {'buffer', 'byteOffset', 'byteLength', 'byteStride', 'target'})
            need(not view.get('extensions') and type(view.get('buffer')) is int and view['buffer'] == 0, 'Uncompressed embedded view only')
            offset = integer(view.get('byteOffset', 0))
            length = integer(view.get('byteLength'), 1)
            need(offset % 4 == 0 and offset + length <= declared, 'View alignment/range')
            if 'byteStride' in view:
                stride = integer(view['byteStride'], 4)
                need(stride <= 252 and stride % 4 == 0, 'Unsupported view stride')
            if 'target' in view: need(type(view['target']) is int and view['target'] in (34962, 34963), 'Unsupported view target')

    def extension_profile(self, value, path=()):
        if type(value) is list:
            for i, child in enumerate(value): self.extension_profile(child, path + (i,))
        elif type(value) is dict:
            extensions = value.get('extensions', {})
            need(type(extensions) is dict, 'Extension object required')
            for name, body in extensions.items():
                need(name in ALLOWED_EXTENSIONS and type(body) is dict, 'Unknown accessor/view reference extension refused')
                if name == 'KHR_materials_unlit':
                    need(len(path) == 2 and path[0] == 'materials' and body == {}, 'Unlit extension outside supported material profile')
                else:
                    need(path and path[0] == 'materials' and path[-1] in TEXTURE_FIELDS and set(body) <= {'offset', 'rotation', 'scale', 'texCoord'}, 'Texture transform profile')
                    if 'texCoord' in body: integer(body['texCoord'])
            for key in ('extensionsUsed', 'extensionsRequired'):
                if key in value:
                    need(type(value[key]) is list and all(type(x) is str and x in ALLOWED_EXTENSIONS for x in value[key]), 'Unknown declared extension refused')
                    need(len(value[key]) == len(set(value[key])), 'Duplicate extension declaration')
            for key, child in value.items():
                if key not in ('extras', 'extensions'): self.extension_profile(child, path + (key,))

    def ref(self, index, table):
        index = integer(index)
        need(index < len(self.doc.get(table, [])), 'Resource reference outside table')
        return index

    def view(self, index):
        index = self.ref(index, 'bufferViews')
        self.used_views.add(index)
        return self.doc['bufferViews'][index]

    def accessor(self, index):
        index = self.ref(index, 'accessors')
        self.used_accessors.add(index)
        accessor = self.doc['accessors'][index]
        fields(accessor, {'bufferView', 'byteOffset', 'componentType', 'count', 'type', 'normalized', 'min', 'max'})
        need('sparse' not in accessor and not accessor.get('extensions'), 'Sparse/extended accessor refused')
        component = accessor.get('componentType')
        need(type(component) is int and component in COMPONENTS and accessor.get('type') in ARITY, 'Unsupported accessor component or shape')
        normalized = accessor.get('normalized', False)
        need(type(normalized) is bool and (not normalized or component in (5120, 5121, 5122, 5123)), 'Unsupported normalized component')
        count = integer(accessor.get('count'), 1)
        need(count <= 2_000_000 and (accessor['type'] != 'MAT4' or component == 5126), 'Unsupported matrix/count profile')
        view = self.view(accessor.get('bufferView'))
        offset = integer(accessor.get('byteOffset', 0))
        size = COMPONENTS[component][1]
        element = ARITY[accessor['type']] * size
        stride = view.get('byteStride', element)
        need(stride >= element and stride % size == 0 and (view.get('byteOffset', 0) + offset) % size == 0, 'Accessor stride/alignment')
        need(offset + (count - 1) * stride + element <= view['byteLength'], 'Accessor outside view')
        start = view.get('byteOffset', 0) + offset
        packed = b''.join(self.binary[start + i * stride:start + i * stride + element] for i in range(count))
        if component == 5126:
            need(all(math.isfinite(x[0]) for x in struct.iter_unpack('<f', packed)), 'Nonfinite F32 component')
        for key in ('min', 'max'):
            if key in accessor:
                need(type(accessor[key]) is list and len(accessor[key]) == ARITY[accessor['type']] and
                     all(type(x) in (int, float) and math.isfinite(x) for x in accessor[key]), 'Malformed min/max metadata')
        metadata = {k: copy.deepcopy(v) for k, v in accessor.items() if k not in ('bufferView', 'byteOffset')}
        view_metadata = {k: copy.deepcopy(v) for k, v in view.items() if k not in ('buffer', 'byteOffset', 'byteLength', 'byteStride')}
        token = {'metadata': metadata, 'view_metadata': view_metadata, 'component_bytes': packed}
        return accessor, token

    def channel(self, index, component, kind, count=None):
        accessor, token = self.accessor(index)
        need(accessor['componentType'] in component and accessor['type'] in kind, 'Channel type differs from supported semantic')
        if count is not None: need(accessor['count'] == count, 'Channel count differs from vertex/joint count')
        return accessor, token

    def attributes(self, primitive):
        attrs = primitive.get('attributes')
        need(type(attrs) is dict and 'POSITION' in attrs and 'NORMAL' in attrs, 'POSITION and NORMAL required')
        collisions = [name for name in attrs if name.casefold() == CARRIER.casefold()]
        need(collisions == ([CARRIER] if self.carrier else []), 'Owned carrier missing, preexisting or case-colliding')
        position, _ = self.channel(attrs['POSITION'], {5126}, {'VEC3'})
        count = position['count']
        result = {}
        for semantic, index in attrs.items():
            need(type(semantic) is str, 'Attribute semantic must be a string')
            accessor, token = self.accessor(index)
            need(accessor['count'] == count, 'Vertex attribute count differs')
            component, kind = accessor['componentType'], accessor['type']
            if semantic == CARRIER:
                need(component == 5126 and kind == 'SCALAR' and not accessor.get('normalized', False), 'Carrier must be raw F32 SCALAR')
                ids = [x[0] for x in struct.iter_unpack('<f', token['component_bytes'])]
                need(all(1 <= value <= 200_000 and value.is_integer() for value in ids), 'Carrier ID representation refused')
                self.carrier_count += 1
                continue
            if semantic in ('POSITION', 'NORMAL', 'TANGENT'):
                need(component == 5126 and kind == ('VEC4' if semantic == 'TANGENT' else 'VEC3') and not accessor.get('normalized', False), 'Geometric attribute profile')
            elif re.fullmatch(r'TEXCOORD_\d+', semantic):
                need(kind == 'VEC2' and component in (5121, 5123, 5126) and (component == 5126 or accessor.get('normalized') is True), 'UV attribute profile')
            elif re.fullmatch(r'COLOR_\d+', semantic):
                need(kind in ('VEC3', 'VEC4') and component in (5121, 5123, 5126) and (component == 5126 or accessor.get('normalized') is True), 'Color attribute profile')
            elif re.fullmatch(r'JOINTS_\d+', semantic):
                need(kind == 'VEC4' and component in (5121, 5123) and not accessor.get('normalized', False), 'Joint attribute profile')
            elif re.fullmatch(r'WEIGHTS_\d+', semantic):
                need(kind == 'VEC4' and component in (5121, 5123, 5126) and (component == 5126 or accessor.get('normalized') is True), 'Weight attribute profile')
            else:
                need(semantic.startswith('_') and kind != 'MAT4', 'Unknown standard attribute semantic')
            if semantic == 'NORMAL':
                self.normal_hashes.append(hashlib.sha256(token['component_bytes']).hexdigest())
                token['component_bytes'] = b'NORMAL_PAYLOAD_REQUIRES_SEPARATE_GATE'
                token['metadata'].pop('min', None)
                token['metadata'].pop('max', None)
            result[semantic] = token
        return result, count

    def canonical(self):
        result = copy.deepcopy(self.doc)
        need(self.doc.get('meshes'), 'At least one supported mesh required')
        for mesh_index, mesh in enumerate(self.doc.get('meshes', [])):
            fields(mesh, {'primitives', 'weights'})
            need(type(mesh.get('primitives')) is list and mesh['primitives'], 'Primitive list required')
            for primitive_index, primitive in enumerate(mesh['primitives']):
                fields(primitive, {'attributes', 'indices', 'material', 'mode', 'targets'})
                need(type(primitive.get('mode', 4)) is int and primitive.get('mode', 4) == 4 and not primitive.get('extensions'), 'Uncompressed triangle primitives only')
                output = result['meshes'][mesh_index]['primitives'][primitive_index]
                output['attributes'], count = self.attributes(primitive)
                if 'indices' in primitive:
                    accessor, token = self.channel(primitive['indices'], {5121, 5123, 5125}, {'SCALAR'})
                    need(not accessor.get('normalized', False) and accessor['count'] % 3 == 0, 'Triangle index profile')
                    code = COMPONENTS[accessor['componentType']][0]
                    need(all(x[0] < count for x in struct.iter_unpack('<' + code, token['component_bytes'])), 'Index outside vertex array')
                    output['indices'] = token
                else: need(count % 3 == 0, 'Non-indexed triangle count')
                if 'material' in primitive: self.ref(primitive['material'], 'materials')
                need(type(primitive.get('targets', [])) is list, 'Morph target list required')
                for target_index, target in enumerate(primitive.get('targets', [])):
                    need(type(target) is dict and target and set(target) == {'POSITION'}, 'Only authored position morph targets supported')
                    _, token = self.channel(target['POSITION'], {5126}, {'VEC3'}, count)
                    output['targets'][target_index]['POSITION'] = token
                self.primitive_count += 1
        for i, skin in enumerate(self.doc.get('skins', [])):
            fields(skin, {'joints', 'inverseBindMatrices', 'skeleton'})
            need(type(skin.get('joints')) is list and skin['joints'], 'Joint list required')
            for index in skin['joints']: self.ref(index, 'nodes')
            if 'skeleton' in skin: self.ref(skin['skeleton'], 'nodes')
            if 'inverseBindMatrices' in skin:
                _, token = self.channel(skin['inverseBindMatrices'], {5126}, {'MAT4'}, len(skin['joints']))
                result['skins'][i]['inverseBindMatrices'] = token
        for i, animation in enumerate(self.doc.get('animations', [])):
            fields(animation, {'channels', 'samplers'})
            need(type(animation.get('samplers')) is list and type(animation.get('channels')) is list, 'Animation lists required')
            for j, sampler in enumerate(animation['samplers']):
                fields(sampler, {'input', 'output', 'interpolation'})
                need(sampler.get('interpolation', 'LINEAR') in ('LINEAR', 'STEP', 'CUBICSPLINE'), 'Animation interpolation profile')
                _, inputs = self.channel(sampler.get('input'), {5126}, {'SCALAR'})
                _, outputs = self.channel(sampler.get('output'), {5126}, {'SCALAR', 'VEC3', 'VEC4'})
                result['animations'][i]['samplers'][j].update(input=inputs, output=outputs)
            for channel in animation['channels']:
                fields(channel, {'sampler', 'target'})
                index = integer(channel.get('sampler'))
                need(index < len(animation['samplers']), 'Animation sampler reference')
                fields(channel.get('target'), {'node', 'path'})
                self.ref(channel['target'].get('node'), 'nodes')
                need(channel['target'].get('path') in ('translation', 'rotation', 'scale', 'weights'), 'Animation target profile')
        for i, image in enumerate(self.doc.get('images', [])):
            fields(image, {'bufferView', 'mimeType', 'uri'})
            need('uri' not in image and image.get('mimeType') in ('image/png', 'image/jpeg'), 'Embedded PNG/JPEG image profile only')
            view = self.view(image.get('bufferView'))
            need('byteStride' not in view and 'target' not in view, 'Image view profile')
            offset = view.get('byteOffset', 0)
            encoded = self.binary[offset:offset + view['byteLength']]
            self.image_bytes += len(encoded)
            result['images'][i]['bufferView'] = {'view_metadata': {k: v for k, v in view.items() if k not in ('buffer', 'byteOffset', 'byteLength')}, 'encoded_bytes': encoded}
        self.other_references()
        need(self.used_accessors == set(range(len(self.doc.get('accessors', [])))) and self.used_views == set(range(len(self.doc.get('bufferViews', [])))), 'Unreferenced/unknown accessor or view refused')
        result.pop('accessors', None)
        result.pop('bufferViews', None)
        result['buffers'][0].pop('byteLength')
        return freeze(result, internal=True)

    def other_references(self):
        if 'scene' in self.doc: self.ref(self.doc['scene'], 'scenes')
        for scene in self.doc.get('scenes', []):
            fields(scene, {'nodes'})
            need(type(scene.get('nodes', [])) is list, 'Scene node list required')
            for node in scene.get('nodes', []): self.ref(node, 'nodes')
        for node in self.doc.get('nodes', []):
            fields(node, {'camera', 'children', 'skin', 'matrix', 'mesh', 'rotation', 'scale', 'translation', 'weights'})
            need(type(node.get('children', [])) is list, 'Node children list required')
            for key, table in [('camera', 'cameras'), ('mesh', 'meshes'), ('skin', 'skins')]:
                if key in node: self.ref(node[key], table)
            for child in node.get('children', []): self.ref(child, 'nodes')
            for key, length in [('matrix', 16), ('translation', 3), ('rotation', 4), ('scale', 3)]:
                if key in node:
                    need(type(node[key]) is list and len(node[key]) == length and all(type(x) in (int, float) and math.isfinite(x) for x in node[key]), 'Unsupported node transform')
            need('matrix' not in node or not {'translation', 'rotation', 'scale'} & node.keys(), 'Matrix/TRS overlap refused')
        for sampler in self.doc.get('samplers', []):
            fields(sampler, {'magFilter', 'minFilter', 'wrapS', 'wrapT'})
            for key, values in [('magFilter', {9728, 9729}), ('minFilter', {9728, 9729, 9984, 9985, 9986, 9987}),
                                ('wrapS', {33071, 33648, 10497}), ('wrapT', {33071, 33648, 10497})]:
                if key in sampler: need(type(sampler[key]) is int and sampler[key] in values, 'Unsupported texture sampler')
        for camera in self.doc.get('cameras', []):
            fields(camera, {'type', 'perspective', 'orthographic'})
            kind = camera.get('type')
            need(kind in ('perspective', 'orthographic') and kind in camera and (('orthographic' if kind == 'perspective' else 'perspective') not in camera), 'Unsupported camera type')
            fields(camera[kind], {'aspectRatio', 'yfov', 'zfar', 'znear'} if kind == 'perspective' else {'xmag', 'ymag', 'zfar', 'znear'})
        for texture in self.doc.get('textures', []):
            fields(texture, {'sampler', 'source'})
            if 'source' in texture: self.ref(texture['source'], 'images')
            if 'sampler' in texture: self.ref(texture['sampler'], 'samplers')
        for material in self.doc.get('materials', []):
            fields(material, {'pbrMetallicRoughness', 'normalTexture', 'occlusionTexture', 'emissiveTexture', 'emissiveFactor', 'alphaMode', 'alphaCutoff', 'doubleSided'})
            def texture_info(info):
                fields(info, {'index', 'texCoord', 'scale', 'strength'})
                self.ref(info.get('index'), 'textures')
                if 'texCoord' in info: integer(info['texCoord'])
            for key in TEXTURE_FIELDS & material.keys(): texture_info(material[key])
            if 'pbrMetallicRoughness' in material:
                pbr = material['pbrMetallicRoughness']
                fields(pbr, {'baseColorFactor', 'baseColorTexture', 'metallicFactor', 'roughnessFactor', 'metallicRoughnessTexture'})
                for key in TEXTURE_FIELDS & pbr.keys(): texture_info(pbr[key])


def compare_non_normal(before_document, before_binary, after_document, after_binary):
    before = Snapshot(before_document, before_binary, carrier=False)
    after = Snapshot(after_document, after_binary, carrier=True)
    need(before.canonical() == after.canonical(), 'Decoded non-NORMAL content/order/types/metadata changed')
    need(freeze(before_document) == before.original and freeze(after_document) == after.original, 'Input document mutated')
    return {'format': 'has_carrier_non_normal_semantic_comparison_1', 'passed': True,
            'primitives': before.primitive_count, 'owned_carrier_channels': after.carrier_count,
            'image_encoded_bytes_preserved': before.image_bytes,
            'accessor_view_offset_stride_relayout_allowed': True,
            'all_other_typed_JSON_preserved': True, 'decoded_component_bytes_and_order_exact': True,
            'NORMAL_payload_and_minmax_comparison_performed': False,
            'normal_fidelity_qualified': False, 'native_carrier_correspondence_qualified': False,
            'before_normal_component_SHA256': before.normal_hashes,
            'after_normal_component_SHA256': after.normal_hashes,
            'no_native_run_or_GLB_generation': True}
