"""Unrun stdlib-only material-library inspection helper; no IO or host imports.

Root owns authenticating B/helper/types and the disposable native job. Append is
an in-memory inspection operation, never a rollback/no-transient-read proof.
No geometry labels, SourceIO, image buffers, export, save or shader edits.
"""
import hashlib
import json
import math
import struct
import zlib

MAX_MATERIALS = 4
MAX_IMAGES = 128
MAX_ENCODED_BYTES = MAX_DECODED_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = MAX_TOTAL_DECODED_BYTES = 128 * 1024 * 1024
PNG_MAGIC = b'\x89PNG\r\n\x1a\n'


class Refusal(ValueError):
    def __init__(self, code, summary=None):
        super().__init__(code)
        self.code = code
        self.summary = None if summary is None else dict(summary)


def need(ok, code):
    if not ok:
        raise Refusal(code)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                     allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def _text(value, maximum=1024):
    need(type(value) is str and len(value) <= maximum and len(value.encode('utf-8')) <= maximum * 4,
         'BOUNDED_METADATA_TEXT_REQUIRED')
    return value


def _default(value):
    if value is None or type(value) in (bool, int, str):
        if type(value) is str: _text(value)
        return (type(value).__name__, value)
    if type(value) is float:
        need(math.isfinite(value), 'NONFINITE_SOCKET_DEFAULT')
        return ('float', value.hex())
    result = tuple(value)
    need(0 < len(result) <= 4 and all(type(v) in (int, float) and math.isfinite(v) for v in result),
         'BOUNDED_SOCKET_DEFAULT_REQUIRED')
    return ('vector', tuple(float(v).hex() for v in result))


def _socket(socket, owner, tree, types):
    need(isinstance(socket, types.NodeSocket) and socket.node is owner and socket.id_data is tree,
         'ACTUAL_CONNECTED_SOCKET_OWNER_REQUIRED')
    return socket


def _graph(material, types):
    need(type(material) is types.Material and material.original is material and material.library is None and
         material.use_nodes is True and material.animation_data is None,
         'LOCAL_ORIGINAL_NONANIMATED_MATERIAL_REQUIRED')
    tree = material.node_tree
    need(type(tree) is types.ShaderNodeTree and tree.original is tree and tree.library is None and
         tree.is_embedded_data is True and tree.animation_data is None,
         'LOCAL_EMBEDDED_MATERIAL_NODE_TREE_REQUIRED')
    need(type(material.use_backface_culling) is bool, 'BACKFACE_CULLING_BOOLEAN_REQUIRED')
    need(2 <= len(tree.nodes) <= 3 and 1 <= len(tree.links) <= 3, 'SIMPLE_COMPLETE_GRAPH_BUDGET')
    nodes, links = tuple(tree.nodes), tuple(tree.links)
    need(2 <= len(nodes) <= 3 and len({id(n) for n in nodes}) == len(nodes) and
         1 <= len(links) <= 3 and len({id(link) for link in links}) == len(links), 'SIMPLE_COMPLETE_GRAPH_BUDGET')
    allowed = (types.ShaderNodeOutputMaterial, types.ShaderNodeBsdfPrincipled, types.ShaderNodeTexImage)
    need(all(type(node) in allowed and node.id_data is tree and node.mute is False for node in nodes),
         'UNSUPPORTED_NODE_OR_OWNER_OR_MUTED_GRAPH')
    need(all(type(link) is types.NodeLink and link.id_data is tree and link.is_valid is True for link in links),
         'ACTUAL_VALID_LINK_AND_SOCKET_REFERENCES_REQUIRED')
    outputs = [node for node in nodes if type(node) is types.ShaderNodeOutputMaterial]
    shaders = [node for node in nodes if type(node) is types.ShaderNodeBsdfPrincipled]
    images = [node for node in nodes if type(node) is types.ShaderNodeTexImage]
    need(len(outputs) == len(shaders) == 1 and len(images) <= 1 and
         outputs[0].is_active_output is True and outputs[0].target == 'ALL', 'UNAMBIGUOUS_ACTIVE_OUTPUT_REQUIRED')
    output, shader = outputs[0], shaders[0]
    expected = [(_socket(shader.outputs['BSDF'], shader, tree, types),
                 _socket(output.inputs['Surface'], output, tree, types))]
    reached = []
    if images:
        texture = images[0]
        need(texture.interpolation == 'Linear' and texture.extension == 'REPEAT' and texture.projection == 'FLAT' and
             type(texture.image) is types.Image, 'SUPPORTED_ACTUAL_TEXTURE_IMAGE_REQUIRED')
        reached.append(texture.image)
        expected.append((_socket(texture.outputs['Color'], texture, tree, types),
                         _socket(shader.inputs['Base Color'], shader, tree, types)))
        alpha = _socket(shader.inputs['Alpha'], shader, tree, types)
        alpha_links = [link for link in links if link.to_socket is alpha]
        if alpha_links:
            expected.append((_socket(texture.outputs['Alpha'], texture, tree, types), alpha))
    need(all(type(link) is types.NodeLink and link.id_data is tree and link.is_valid is True and
             any(link.from_node is node for node in nodes) and any(link.to_node is node for node in nodes) and
             _socket(link.from_socket, link.from_node, tree, types) is link.from_socket and
             _socket(link.to_socket, link.to_node, tree, types) is link.to_socket for link in links),
         'ACTUAL_VALID_LINK_AND_SOCKET_REFERENCES_REQUIRED')
    need(len(links) == len(expected) and all(sum(link.from_socket is start and link.to_socket is end
         for link in links) == 1 for start, end in expected), 'EXACT_SIMPLE_GRAPH_LINKS_REQUIRED')
    node_rows = []
    for node in nodes:
        need(len(node.inputs) <= 128, 'SOCKET_SNAPSHOT_BUDGET')
        inputs = tuple(node.inputs)
        need(len(inputs) <= 128 and len({id(socket) for socket in inputs}) == len(inputs), 'SOCKET_SNAPSHOT_BUDGET')
        defaults = []
        for socket in inputs:
            _socket(socket, node, tree, types)
            defaults.append((_text(socket.identifier), _text(socket.name),
                             _default(getattr(socket, 'default_value', None))))
        node_rows.append((node, type(node), _text(node.name), tuple(defaults)))
    # Private reference snapshot. It is not a renderer or complete shader evaluator.
    snapshot = dict(material=material, tree=tree, nodes=nodes, links=links, images=tuple(reached),
                    node_rows=tuple(node_rows), backface_culling=material.use_backface_culling)
    serial = dict(material=_text(material.name), backface_culling=material.use_backface_culling,
                  nodes=[(type(node).__name__, name, defaults) for node, _kind, name, defaults in node_rows],
                  links=[(next(i for i, node in enumerate(nodes) if node is link.from_node), _text(link.from_socket.identifier),
                          next(i for i, node in enumerate(nodes) if node is link.to_node), _text(link.to_socket.identifier)) for link in links])
    return snapshot, serial


def _same_originals(enumeration, before, after):
    if set(before) != set(after):
        return False
    prior_pointers = {row[1] for rows in before.values() for row in rows}
    survivors = {key: tuple(row for row in rows if row[1] in prior_pointers) for key, rows in after.items()}
    return enumeration._unchanged(before, survivors)


def _added(before, after):
    pointers = {row[1] for rows in before.values() for row in rows}
    return {key: tuple(row for row in rows if row[1] not in pointers) for key, rows in after.items()}


def _png(raw):
    need(type(raw) is bytes and len(raw) >= 33 and raw.startswith(PNG_MAGIC) and
         raw[8:16] == struct.pack('>I', 13) + b'IHDR' and
         zlib.crc32(raw[12:29]) == struct.unpack('>I', raw[29:33])[0], 'PNG_SIGNATURE_IHDR_OR_CRC_REQUIRED')
    width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', raw[16:29])
    need(0 < width <= 16384 and 0 < height <= 16384 and depth == 8 and color in (2, 6) and
         compression == filtering == interlace == 0 and width * height * 16 <= MAX_DECODED_BYTES,
         'PNG_HEADER_OR_PROSPECTIVE_RGBA_F32_BUDGET')
    return width, height


def inspect_material_library(bpy, owned_path, material_names, enumeration_module):
    """Append four admitted Materials only, inspect; return PRIVATE refs/summary.

    Root authenticates owned_path, enumeration_module and genuine bpy.types.
    A refusal carries safe counts in error.summary. No rollback or hidden-read
    guarantee follows from a post-append refusal; the owned process is disposable.
    """
    summary = dict(format='has_material_only_library_inspection_summary_1', status='REFUSED',
                   requested_materials=0, append_requested=False, append_completed=False,
                   before_id_count=0, after_id_count=0, added_id_counts={}, surviving_originals_unchanged=False,
                   inspected_material_graphs=0, reached_images=0, shared_image_references=0,
                   packed_bytes_copied=0, prospective_rgba_f32_bytes=0,
                   material_binding_qualified=False, resource_equivalence_qualified=False,
                   native_or_historical_point_identity_qualified=False, exporter_qualified=False,
                   normal_fidelity_qualified=False, application_adoption_qualified=False,
                   transient_ID_or_C_level_read_absence_qualified=False, image_buffer_getters_used=False,
                   blend_saved=False, exporter_invoked=False, external_filepath_retrieval_attempted=False)
    before = after = None
    try:
        need(type(material_names) is tuple and len(material_names) == MAX_MATERIALS and
             len(set(material_names)) == len(material_names) and all(type(name) is str and
             0 < len(name) <= 1024 and _text(name) == name for name in material_names), 'EXACT_FOUR_ADMITTED_MATERIAL_NAMES')
        summary['requested_materials'] = len(material_names)
        types = bpy.types
        for name in ('Material', 'Image', 'ShaderNodeTree', 'ShaderNodeOutputMaterial', 'ShaderNodeBsdfPrincipled',
                     'ShaderNodeTexImage', 'NodeLink', 'NodeSocket', 'ImagePackedFile', 'PackedFile'):
            need(isinstance(getattr(types, name), type), 'GENUINE_HOST_TYPE_CLASSES_REQUIRED')
        before, before_count = enumeration_module._census(bpy)
        summary['before_id_count'] = before_count
        requested = list(material_names)  # Allocate before assigning anything to the library context.
        destination = keys = None
        with bpy.data.libraries.load(str(owned_path), link=False) as (source, destination):
            keys = enumeration_module._library_keys(destination)
            enumeration_module._empty_requests(destination, keys)
            need(enumeration_module._library_keys(source) == keys and 'materials' in keys,
                 'COMPLETE_LIBRARY_SOURCE_DESTINATION_SCHEMA_REQUIRED')
            available = source.materials
            need(type(available) is list and len(available) == MAX_MATERIALS and
                 all(type(name) is str for name in available) and len(set(available)) == MAX_MATERIALS and
                 set(available) == set(material_names), 'EXACT_OWNED_LIBRARY_MATERIAL_CATALOGUE_CHANGED')
            summary['append_requested'] = True
            destination.materials = requested
        # No Python statement follows request assignment inside the context.
        summary['append_completed'] = True
        after, after_count = enumeration_module._census(bpy)
        summary['after_id_count'] = after_count
        additions = _added(before, after)
        summary['added_id_counts'] = {key: len(rows) for key, rows in additions.items() if rows}
        summary['surviving_originals_unchanged'] = _same_originals(enumeration_module, before, after)
        need(summary['surviving_originals_unchanged'], 'PREEXISTING_ID_REFERENCE_OR_METADATA_CHANGED')
        need(enumeration_module._library_keys(destination) == keys and destination.materials is requested and
             type(requested) is list and len(requested) == MAX_MATERIALS, 'RETURNED_REQUEST_LIST_IDENTITY_REQUIRED')
        for key in keys:
            if key in ('materials', 'version'): continue
            value = getattr(destination, key)
            need(type(value) is list and not value, 'UNREQUESTED_DESTINATION_LIST_CHANGED')
        need(all(key in ('materials', 'images') or not rows for key, rows in additions.items()),
             'UNSUPPORTED_ADDED_ID_CATEGORY')
        new_materials = tuple(row[0] for row in additions.get('materials', ()))
        new_images = tuple(row[0] for row in additions.get('images', ()))
        need(len(new_materials) == MAX_MATERIALS and len(new_images) <= MAX_IMAGES and
             len({id(value) for value in requested}) == MAX_MATERIALS and
             all(type(value) is types.Material and value.library is None and value.original is value and
                 value.name == name and sum(candidate is value for candidate in new_materials) == 1
                 for value, name in zip(requested, material_names)), 'EXACT_NEW_LOCAL_RETURNED_MATERIAL_REFERENCES')
        need(all(type(image) is types.Image and image.library is None for image in new_images),
             'ONLY_NEW_LOCAL_IMAGE_DEPENDENCIES_ALLOWED')
        graphs, serial, reached = [], [], []
        for material in requested:
            graph, data = _graph(material, types)
            need(all(graph['tree'] is not prior['tree'] for prior in graphs), 'ALIASED_EMBEDDED_MATERIAL_TREES')
            graphs.append(graph); serial.append(data); reached.extend(graph['images'])
            summary['inspected_material_graphs'] += 1
        unique_images = []
        for image in reached:
            need(sum(candidate is image for candidate in new_images) == 1, 'GRAPH_IMAGE_NOT_NEW_LOCAL_DEPENDENCY')
            if all(image is not prior for prior in unique_images): unique_images.append(image)
        need(len(unique_images) == len(new_images), 'UNREACHED_ADDED_IMAGE_DEPENDENCY')
        summary['reached_images'] = len(unique_images)
        summary['shared_image_references'] = len(reached) - len(unique_images)
        tickets, encoded_total = [], 0
        for image in unique_images:
            need(image.source == 'FILE' and image.type == 'IMAGE' and image.library is None,
                 'PACKED_FILE_IMAGE_PROFILE_REQUIRED')
            name, filepath = _text(image.name), _text(image.filepath)
            need(len(image.packed_files) == 1, 'EXACT_SINGLE_CONNECTED_PACKED_FILE_REQUIRED')
            parts = tuple(image.packed_files)
            need(len(parts) == 1 and type(parts[0]) is types.ImagePackedFile and
                 type(image.packed_file) is types.PackedFile and image.packed_file is parts[0].packed_file,
                 'EXACT_SINGLE_CONNECTED_PACKED_FILE_REQUIRED')
            packed = image.packed_file
            count = packed.size
            need(type(count) is int and 33 <= count <= MAX_ENCODED_BYTES, 'PACKED_ENCODED_SIZE_BUDGET')
            encoded_total += count
            need(encoded_total <= MAX_TOTAL_BYTES, 'AGGREGATE_PACKED_ENCODED_BUDGET')
            tickets.append((image, name, filepath, parts[0], packed, count))
        # Every encoded size has been admitted before the first .data access.
        images, prospective = [], 0
        for image, name, filepath, part, packed, count in tickets:
            raw = packed.data  # Exactly one byte copy; never image.size/channels/pixels.
            summary['packed_bytes_copied'] += len(raw) if type(raw) is bytes else 0
            need(type(raw) is bytes and len(raw) == count, 'EXACT_PACKED_BYTE_COPY_REQUIRED')
            width, height = _png(raw)
            prospective += width * height * 16
            need(prospective <= MAX_TOTAL_DECODED_BYTES, 'AGGREGATE_PROSPECTIVE_RGBA_F32_BUDGET')
            digest = hashlib.sha256(raw).hexdigest()
            images.append(dict(image=image, packed_part=part, packed=packed, name=name, filepath=filepath,
                               encoded_bytes=count, encoded_sha256=digest, width=width, height=height))
        summary['prospective_rgba_f32_bytes'] = prospective
        for material, prior, prior_serial in zip(requested, graphs, serial):
            current, current_serial = _graph(material, types)
            need(current['tree'] is prior['tree'] and current_serial == prior_serial and
                 all(len(current[key]) == len(prior[key]) and all(a is b for a, b in zip(current[key], prior[key]))
                     for key in ('nodes', 'links', 'images')), 'GRAPH_CHANGED_DURING_INSPECTION')
        final, final_count = enumeration_module._census(bpy)
        need(enumeration_module._unchanged(after, final), 'ID_CENSUS_CHANGED_DURING_INSPECTION')
        summary['after_id_count'] = final_count
        summary['material_names_sha256'] = _digest(material_names)
        summary['graph_metadata_sha256'] = _digest(serial)
        summary['packed_observation_sha256'] = _digest([(row['name'], row['filepath'], row['encoded_bytes'],
            row['encoded_sha256'], row['width'], row['height']) for row in images])
        summary['status'] = 'INSPECTED_MATERIAL_ONLY_NARROW_GRAPH_AND_PACKED_PNG_HEADERS'
        return dict(materials=tuple(requested), graphs=tuple(graphs), images=tuple(images), summary=summary)
    except Exception as error:
        # Context exit may have added IDs before raising. Record surviving state
        # when observable; never remove IDs to make a refusal look successful.
        if before is not None:
            try:
                observed, count = enumeration_module._census(bpy)
                summary['after_id_count'] = count
                summary['added_id_counts'] = {key: len(rows) for key, rows in _added(before, observed).items() if rows}
                summary['surviving_originals_unchanged'] = _same_originals(enumeration_module, before, observed)
            except Exception:
                summary['post_failure_census_unavailable'] = True
        code = error.code if isinstance(error, Refusal) else 'MATERIAL_INSPECTION_API_REFUSAL'
        summary['status'], summary['refusal_code'] = 'REFUSED', code
        raise Refusal(code, summary) from error
