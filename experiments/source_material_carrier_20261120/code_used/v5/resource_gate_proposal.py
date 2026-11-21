"""UNRUN narrow, packed-PNG material reachability proposal; no Blender import.

Refuses groups, alternate outputs, extra/ORM links, arbitrary computations,
external/UDIM/viewer images, texcoord copies and WebP paths.  It is intentionally
not a shader evaluator, image decoder or full glTF semantic comparator.
"""
import hashlib
import math
import struct
import zlib

from export_hook_proposal import Refusal, need, same_refs

MAX_ENCODED_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_DECODED_BYTES = 64 * 1024 * 1024
MAX_TOTAL_DECODED_BYTES = 128 * 1024 * 1024
PNG_MAGIC = b'\x89PNG\r\n\x1a\n'
MAX_RETAINED_RNA_STRUCTS = 131_072


def _unique_refs(values):
    return len({id(x) for x in values}) == len(values)


def _same_key(left, right):
    return len(left) == len(right) and all(_same_rna_key(a[0], b[0]) and a[1] is b[1] and a[2] == b[2]
                                         for a, b in zip(left, right))


def _same_rna_key(left, right):
    return (type(left) is tuple and type(right) is tuple and len(left) == len(right) == 3 and
            left[0] is right[0] and left[1] is right[1] and left[2] == right[2])


def _same_rna_sequence(left, right):
    return len(left) == len(right) and all(_same_rna_key(a, b) for a, b in zip(left, right))


def _unique_rna_keys(keys):
    return len({(id(key[0]), id(key[1]), key[2]) for key in keys}) == len(keys)


def _same_socket_metadata(left, right):
    return len(left) == len(right) and all(_same_rna_key(a[0], b[0]) and _same_rna_key(a[1], b[1]) and
                                         a[2:] == b[2:] for a, b in zip(left, right))


def _same_mapping(left, right):
    if len(left) != len(right):
        return False
    for (channel, value), (other_channel, other_value) in zip(left, right):
        if channel != other_channel or value[0] != other_value[0]:
            return False
        if value[0] == 'image' and (value[1] is not other_value[1] or value[2] != other_value[2]):
            return False
    return True


def _index(value):
    need(type(value) is int and 0 <= value < 65_536, 'exact_resource_index_required')
    return value


def _default(value):
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        need(math.isfinite(value), 'nonfinite_socket_default')
        return ('float', value.hex())
    # RNA default values can be bpy_prop_array/mathutils values.  Read only this
    # bounded socket default; never image pixels or geometry arrays.
    values = tuple(value)
    need(0 < len(values) <= 4 and all(type(x) in (int, float) and not isinstance(x, bool)
                                    and math.isfinite(x) for x in values), 'unsupported_socket_default')
    return ('vector', tuple(float(x).hex() for x in values))


class SimplePackedResources:
    """Keep actual source sockets/images and actual emitted glTF refs.

    `tickets` comes from the future authenticated private resource admission,
    never from filenames or current output. Each exact schema row contains the
    actual Image reference and independently pinned packed-byte SHA256/length.
    Metadata and graph identities are captured before any ordinary exporter call.
    All stored records are private; public final output contains counts only.
    """
    def __init__(self, materials, tickets, bpy_types, search_module, encode_module, gltf_module, *, allow_shared_images=False):
        need(type(materials) is tuple and 1 <= len(materials) <= 128 and _unique_refs(materials),
             'bounded_distinct_source_materials_required')
        need(type(tickets) is list and len(tickets) <= 128, 'bounded_resource_tickets_required')
        self.materials = materials
        self.types = bpy_types
        self.search = search_module
        self.encode = encode_module
        self.gltf = gltf_module
        need(type(allow_shared_images) is bool, 'shared_image_profile_requires_boolean')
        self.shared_images_enabled = allow_shared_images
        self.shared_cache = None
        # One original wrapper per typed owner/C pointer; owners and wrappers
        # stay strongly held for this frozen operation. No addresses are public.
        self._rna_refs = {}
        self._rna_pointer_types = {}
        self.tickets = []
        for row in tickets:
            need(type(row) is dict and set(row) == {'image', 'packed_sha256', 'encoded_bytes'},
                 'exact_resource_ticket_schema_required')
            need(type(row['packed_sha256']) is str and len(row['packed_sha256']) == 64 and
                 all(c in '0123456789abcdef' for c in row['packed_sha256']), 'resource_sha_required')
            need(type(row['encoded_bytes']) is int and 8 <= row['encoded_bytes'] <= MAX_ENCODED_BYTES,
                 'encoded_resource_budget')
            need(all(row['image'] is not prior['image'] for prior in self.tickets), 'image_ticket_alias')
            self.tickets.append(dict(row))
        need(sum(row['encoded_bytes'] for row in self.tickets) <= MAX_TOTAL_BYTES, 'total_encoded_resource_budget')
        self.graphs = [self._graph(material) for material in materials]
        reached_images = [image for graph in self.graphs for image in graph['images']]
        need(allow_shared_images or _unique_refs(reached_images), 'source_image_shared_between_materials_outside_profile')
        reached = {id(image) for image in reached_images}
        need(reached == {id(row['image']) for row in self.tickets}, 'unreachable_or_unadmitted_image_ticket')
        if allow_shared_images:
            # One bounded color/optional-Alpha binding per admitted graph. Charge
            # every expected direct packed encode before the first ImBuf getter,
            # even when multiple graphs reach the same actual Image ID.
            planned_bytes = sum(next(row['encoded_bytes'] for row in self.tickets if row['image'] is image)
                                for image in reached_images)
            need(planned_bytes <= MAX_TOTAL_BYTES, 'shared_binding_encoded_budget')
        names = [row['image'].name for row in self.tickets]
        need(len(names) == len(set(names)), 'distinct_source_images_share_exporter_name')
        # Inspect ALL bounded encoded headers before ANY size/channels getter can
        # acquire/decode an ImBuf.  RGBA F32 is a conservative prospective budget.
        headers = [self._packed_png(row) for row in self.tickets]
        need(sum(width * height * 16 for _, _, width, height in headers) <= MAX_TOTAL_DECODED_BYTES,
             'aggregate_prospective_decoded_image_budget')
        for row in self.tickets:
            row['snapshot'] = self._image_snapshot(row)
        self.descriptors = []
        self.images = []
        self.image_bindings = []
        self.textures = []
        self.infos = []
        self.gathered_materials = []
        self.references = {'image': [], 'texture': [], 'material': []}

    def _rna_key(self, value, owner, base, exact=None):
        need(isinstance(owner, self.types.ID) and owner is owner.original and owner.library is None,
             'nonlocal_or_invalid_rna_owner_ID')
        concrete = type(value)
        need(isinstance(value, base) and getattr(self.types, concrete.__name__, None) is concrete and
             (exact is None or concrete in exact), 'unadmitted_concrete_rna_type')
        need(value.id_data is owner, 'rna_struct_owner_ID_changed')
        pointer = value.as_pointer()
        need(type(pointer) is int and 0 < pointer < 2**64, 'bounded_actual_rna_pointer_required')
        owner_pointer = (id(owner), pointer)
        need(owner_pointer not in self._rna_pointer_types or self._rna_pointer_types[owner_pointer] is concrete,
             'rna_pointer_concrete_type_changed')
        self._rna_pointer_types[owner_pointer] = concrete
        key = (owner, concrete, pointer)
        signature = (id(owner), id(concrete), pointer)
        if signature in self._rna_refs:
            need(_same_rna_key(self._rna_refs[signature][0], key), 'retained_rna_key_alias')
        else:
            need(len(self._rna_refs) < MAX_RETAINED_RNA_STRUCTS, 'retained_rna_struct_budget')
            self._rna_refs[signature] = (key, value)
        return key

    def _node_key(self, node, tree):
        exact = (self.types.ShaderNodeOutputMaterial, self.types.ShaderNodeBsdfPrincipled,
                 self.types.ShaderNodeTexImage)
        return self._rna_key(node, tree, exact, exact)

    def _socket_metadata(self, socket, tree, node_key, output, ordinal):
        key = self._rna_key(socket, tree, self.types.NodeSocket)
        need(_same_rna_key(self._node_key(socket.node, tree), node_key) and
             type(socket.is_output) is bool and socket.is_output is output and
             type(socket.identifier) is str and 0 < len(socket.identifier) <= 256,
             'socket_node_direction_or_identifier_changed')
        return (key, node_key, output, ordinal, socket.identifier)

    def _graph(self, material):
        need(material is material.original and material.library is None and material.use_nodes is True and
             material.node_tree is not None and material.animation_data is None,
             'nonlocal_aliased_or_animated_material')
        tree = material.node_tree
        need(isinstance(tree, self.types.NodeTree) and tree is tree.original,
             'actual_original_node_tree_ID_required')
        need(type(material.use_backface_culling) is bool, 'exact_backface_culling_scalar_required')
        need(tree.library is None and tree.animation_data is None, 'linked_or_animated_node_tree')
        nodes, links = tuple(tree.nodes), tuple(tree.links)
        need(2 <= len(nodes) <= 3 and len(links) <= 3, 'simple_graph_budget')
        output_type = self.types.ShaderNodeOutputMaterial
        principled_type = self.types.ShaderNodeBsdfPrincipled
        image_type = self.types.ShaderNodeTexImage
        need(all(type(node) in (output_type, principled_type, image_type) and node.mute is False for node in nodes),
             'unsupported_node_or_muted_graph')
        node_keys = tuple(self._node_key(node, tree) for node in nodes)
        link_keys = tuple(self._rna_key(link, tree, self.types.NodeLink) for link in links)
        need(_unique_rna_keys(node_keys) and _unique_rna_keys(link_keys), 'simple_graph_budget')
        all_sockets, default_keys, snapshots = [], [], []
        for node, node_key in zip(nodes, node_keys):
            inputs, outputs = tuple(node.inputs), tuple(node.outputs)
            need(len(inputs) <= 256 and len(outputs) <= 256, 'bounded_node_socket_collections')
            input_metadata = tuple(self._socket_metadata(socket, tree, node_key, False, index)
                                   for index, socket in enumerate(inputs))
            output_metadata = tuple(self._socket_metadata(socket, tree, node_key, True, index)
                                    for index, socket in enumerate(outputs))
            all_sockets.extend(input_metadata + output_metadata)
            default_keys.append(tuple(row[0] for row in input_metadata))
            defaults = tuple((socket, _default(getattr(socket, 'default_value', None))) for socket in inputs)
            snapshots.append((node, type(node), node.mute, getattr(node, 'image', None), defaults,
                              getattr(node, 'is_active_output', None), getattr(node, 'target', None),
                              getattr(node, 'interpolation', None), getattr(node, 'extension', None),
                              getattr(node, 'projection', None)))
        need(_unique_rna_keys([row[0] for row in all_sockets]), 'duplicate_rna_socket_membership')
        def socket_key(socket, node, output):
            node_key = self._node_key(node, tree)
            key = self._rna_key(socket, tree, self.types.NodeSocket)
            matches = [row for row in all_sockets if _same_rna_key(row[0], key) and
                       _same_rna_key(row[1], node_key) and row[2] is output]
            need(len(matches) == 1 and _same_socket_metadata(
                (self._socket_metadata(socket, tree, node_key, output, matches[0][3]),), (matches[0],)),
                 'foreign_socket_or_wrong_collection_membership')
            return key
        outputs = [node for node in nodes if type(node) is output_type]
        shaders = [node for node in nodes if type(node) is principled_type]
        textures = [node for node in nodes if type(node) is image_type]
        need(len(outputs) == len(shaders) == 1 and len(textures) <= 1 and
             outputs[0].is_active_output is True and outputs[0].target == 'ALL', 'ambiguous_active_output')
        output, shader = outputs[0], shaders[0]
        shader_key, output_key = self._node_key(shader, tree), self._node_key(output, tree)
        expected = [(socket_key(shader.outputs['BSDF'], shader, True), socket_key(output.inputs['Surface'], output, False))]
        socket_rows, images = [], []
        if textures:
            tex = textures[0]
            need(tex.image is not None and tex.interpolation == 'Linear' and tex.extension == 'REPEAT' and
                 tex.projection == 'FLAT', 'unsupported_texture_configuration')
            images.append(tex.image)
            color = socket_key(shader.inputs['Base Color'], shader, False)
            alpha_key = socket_key(shader.inputs['Alpha'], shader, False)
            tex_color = socket_key(tex.outputs['Color'], tex, True)
            tex_alpha = socket_key(tex.outputs['Alpha'], tex, True)
            expected.append((tex_color, color))
            socket_rows.append((shader.inputs['Base Color'], tex.image, 'color'))
            alpha = [(self._rna_key(link.from_socket, tree, self.types.NodeSocket),
                      self._rna_key(link.to_socket, tree, self.types.NodeSocket)) for link in links
                     if _same_rna_key(self._rna_key(link.to_socket, tree, self.types.NodeSocket), alpha_key)]
            if alpha:
                need(len(alpha) == 1 and _same_rna_key(alpha[0][0], tex_alpha), 'unsupported_alpha_mapping')
                expected.append((tex_alpha, alpha_key))
                socket_rows.append((shader.inputs['Alpha'], tex.image, 'alpha'))
        edges = []
        for link in links:
            from_key, to_key = self._node_key(link.from_node, tree), self._node_key(link.to_node, tree)
            need(sum(_same_rna_key(from_key, key) for key in node_keys) == 1 and
                 sum(_same_rna_key(to_key, key) for key in node_keys) == 1 and link.is_valid is True,
                 'foreign_link_endpoint_or_invalid_link')
            start = socket_key(link.from_socket, link.from_node, True)
            end = socket_key(link.to_socket, link.to_node, False)
            edges.append((from_key, start, to_key, end, link.is_valid))
        # Same complete directed edge policy; only non-ID identity changed.
        need(len(links) == len(expected) and all(
            sum(_same_rna_key(edge[1], start) and _same_rna_key(edge[3], end) for edge in edges) == 1
            for start, end in expected), 'unsupported_or_extra_graph_link')
        row_keys = tuple((self._rna_key(row[0], tree, self.types.NodeSocket), row[1], row[2]) for row in socket_rows)
        return dict(material=material, tree=tree, nodes=nodes, links=links, node_keys=node_keys, link_keys=link_keys,
                    backface_culling=material.use_backface_culling, edges=tuple(edges), snapshot=tuple(snapshots),
                    default_keys=tuple(default_keys), socket_metadata=tuple(all_sockets), sockets=tuple(socket_rows),
                    socket_keys=row_keys, images=tuple(images))

    def _packed_png(self, ticket):
        image = ticket['image']
        need(isinstance(image, self.types.Image) and image is image.original, 'actual_original_image_ID_required')
        parts = tuple(image.packed_files)
        need(len(parts) == 1, 'exact_single_packed_image_required')
        part = parts[0]
        self._rna_key(part, image, self.types.ImagePackedFile)
        packed = image.packed_file
        other_packed = part.packed_file
        need(packed is not None and other_packed is not None and _same_rna_key(
            self._rna_key(packed, image, self.types.PackedFile),
            self._rna_key(other_packed, image, self.types.PackedFile)), 'exact_single_packed_image_required')
        need(type(packed.size) is int and packed.size == ticket['encoded_bytes'], 'packed_image_size_changed')
        need(type(other_packed.size) is int and other_packed.size == packed.size, 'packed_alias_size_changed')
        raw = packed.data
        need(type(raw) is bytes and len(raw) == packed.size and len(raw) >= 33 and raw.startswith(PNG_MAGIC) and
             hashlib.sha256(raw).hexdigest() == ticket['packed_sha256'], 'packed_png_hash_or_magic_changed')
        alias_raw = other_packed.data
        need(type(alias_raw) is bytes and alias_raw == raw, 'packed_alias_payload_changed')
        need(raw[8:16] == struct.pack('>I', 13) + b'IHDR' and
             zlib.crc32(raw[12:29]) == struct.unpack('>I', raw[29:33])[0], 'png_ihdr_structure_or_crc')
        width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', raw[16:29])
        need(0 < width <= 16384 and 0 < height <= 16384 and depth == 8 and color in (2, 6) and
             compression == filtering == interlace == 0 and width * height * 16 <= MAX_DECODED_BYTES,
             'png_ihdr_profile_or_prospective_decoded_budget')
        return part, packed, width, height

    def _image_snapshot(self, ticket):
        image = ticket['image']
        need(image.library is None and image.source == 'FILE' and image.type == 'IMAGE' and
             image.is_dirty is False and getattr(image, 'animation_data', None) is None,
             'unqualified_external_viewer_or_animated_image')
        need(type(image.name) is str and 0 < len(image.name) <= 256 and
             type(image.filepath) is str and type(image.filepath_raw) is str,
             'image_metadata_type')
        # AUTO MIME uses raw suffix before encode(). A packed PNG named .jpg or
        # .webp can otherwise enter pixel/temp re-encoding before the late hook.
        need(all(path == '' or path.casefold().endswith('.png')
                 for path in (image.filepath, image.filepath_raw)), 'packed_png_auto_mime_path_conflict')
        part, packed, width, height = self._packed_png(ticket)
        need(image.has_data is True, 'source_image_buffer_missing')
        size = tuple(image.size)
        need(len(size) == 2 and size == (width, height) and all(type(value) is int for value in size) and
             type(image.channels) is int and image.channels in (3, 4), 'image_dimensions_or_channels')
        return (image, image.name, image.filepath, image.filepath_raw, image.source, image.type,
                image.is_dirty, image.has_data, image.alpha_mode, image.colorspace_settings.name,
                size, image.channels, part, packed, packed.size, ticket['packed_sha256'],
                part.filepath, part.view, part.tile_number,
                self._rna_key(part, image, self.types.ImagePackedFile), self._rna_key(packed, image, self.types.PackedFile))

    def check_unchanged(self):
        for graph in self.graphs:
            current = self._graph(graph['material'])
            need(current['material'] is graph['material'] and current['tree'] is graph['tree'] and
                 type(current['backface_culling']) is bool and current['backface_culling'] is graph['backface_culling'] and
                 _same_rna_sequence(current['node_keys'], graph['node_keys']) and
                 _same_rna_sequence(current['link_keys'], graph['link_keys']) and
                 _same_socket_metadata(current['socket_metadata'], graph['socket_metadata']) and
                 len(current['edges']) == len(graph['edges']) and all(
                     _same_rna_sequence(a[:4], b[:4]) and a[4] is b[4] for a, b in zip(current['edges'], graph['edges'])) and
                 len(current['snapshot']) == len(graph['snapshot']), 'material_graph_identity_changed')
            for index, (actual, expected) in enumerate(zip(current['snapshot'], graph['snapshot'])):
                need(_same_rna_key(current['node_keys'][index], graph['node_keys'][index]) and
                     actual[1] is expected[1] and actual[2] is expected[2] and
                     actual[3] is expected[3] and actual[5:] == expected[5:] and
                     _same_rna_sequence(current['default_keys'][index], graph['default_keys'][index]) and
                     len(actual[4]) == len(expected[4]) and all(
                         a[1] == b[1] for a, b in zip(actual[4], expected[4])),
                     'material_graph_or_socket_default_changed')
        for ticket in self.tickets:
            actual, expected = self._image_snapshot(ticket), ticket['snapshot']
            need(actual[0] is expected[0] and _same_rna_key(actual[19], expected[19]) and
                 _same_rna_key(actual[20], expected[20]) and actual[1:12] == expected[1:12] and actual[14:19] == expected[14:19],
                 'image_metadata_or_packed_bytes_changed')

    def _socket_key(self, sockets):
        need(type(sockets) is tuple and 0 < len(sockets) <= 2, 'bounded_actual_socket_tuple_required')
        found = []
        owner = None
        for wrapper in sockets:
            need(type(wrapper) is self.search.NodeSocket and type(wrapper.group_path) is list and
                 len(wrapper.group_path) == 1, 'exact_root_nodesocket_context_required')
            matches = [(graph, row) for graph in self.graphs for row in graph['socket_keys']
                       if wrapper.group_path[0] is graph['tree'] and _same_rna_key(
                           self._rna_key(wrapper.socket, graph['tree'], self.types.NodeSocket), row[0])]
            need(len(matches) == 1, 'socket_not_in_preflight_reachable_graph')
            graph, row = matches[0]
            metadata = [item for item in graph['socket_metadata'] if _same_rna_key(item[0], row[0])]
            need(len(metadata) == 1, 'socket_metadata_membership_missing')
            expected = metadata[0]
            actual = self._socket_metadata(wrapper.socket, graph['tree'], expected[1], expected[2], expected[3])
            need(_same_socket_metadata((actual,), (expected,)), 'exporter_socket_metadata_changed')
            node = wrapper.socket.node
            members = tuple(node.outputs if expected[2] else node.inputs)
            member_keys = tuple(self._rna_key(item, graph['tree'], self.types.NodeSocket) for item in members)
            need(expected[3] < len(member_keys) and _same_rna_key(member_keys[expected[3]], row[0]) and
                 sum(_same_rna_key(item, row[0]) for item in member_keys) == 1 and
                 sum(_same_rna_key(self._node_key(item, graph['tree']), expected[1])
                     for item in graph['tree'].nodes) == 1, 'exporter_socket_foreign_node_or_membership')
            need(owner is None or owner is graph, 'cross_material_socket_composition')
            owner = graph
            found.append(row)
        need(_unique_rna_keys([row[0] for row in found]), 'duplicate_shader_socket')
        # BaseColor precedes optional Alpha. Alpha-only would need RGB FillWhite
        # and the exporter's pixel/temp composition path, outside this profile.
        kinds = tuple(row[2] for row in found)
        need(kinds in (('color',), ('color', 'alpha')), 'unsupported_socket_channel_order')
        return tuple((row[0], row[1], row[2]) for row in found)

    def before_image_data(self, sockets, use_tile):
        self.check_unchanged()
        need(use_tile is None, 'udim_tile_not_admitted')
        self._socket_key(sockets)  # All image refs already authorized before original.
        if self.shared_images_enabled:
            need(self.shared_cache is not None, 'shared_image_attested_cache_missing')
            self.shared_cache.before_descriptor(sockets)

    def _descriptor(self, descriptor, key):
        e = self.encode
        need(type(descriptor) is e.ExportImage and descriptor.original is None and
             descriptor.numpy_calc is None and type(descriptor.stored) is dict and not descriptor.stored and
             type(descriptor.fills) is dict, 'unsupported_export_image_computation_or_original')
        expected = {}
        for _, image, kind in key:
            if kind == 'color':
                expected = {channel: ('image', image, channel) for channel in range(image.channels)}
            else:
                if not expected:
                    expected = {channel: ('white',) for channel in range(3)}
                expected[3] = ('image', image, 3)
        actual = {}
        for channel, fill in descriptor.fills.items():
            need(type(channel) in (int, e.Channel) and type(channel) is not bool and 0 <= channel <= 3,
                 'unsupported_descriptor_destination_channel')
            channel = int(channel)  # Exact already admitted int/IntEnum, not arbitrary coercion.
            need(channel not in actual, 'duplicate_descriptor_channel')
            if type(fill) is e.FillImage:
                need(type(fill.src_chan) in (int, e.Channel) and type(fill.src_chan) is not bool and
                     0 <= fill.src_chan <= 3, 'unsupported_source_channel')
                actual[channel] = ('image', fill.image, int(fill.src_chan))
            elif type(fill) is e.FillWhite:
                actual[channel] = ('white',)
            else:
                raise Refusal('unsupported_image_fill_type')
        mapping = tuple((channel, actual[channel]) for channel in sorted(actual))
        expected_mapping = tuple((channel, expected[channel]) for channel in sorted(expected))
        need(_same_mapping(mapping, expected_mapping), 'complete_image_channel_mapping_differs')
        return mapping

    def after_image_data(self, sockets, result):
        need(type(result) is tuple and len(result) == 2 and result[1] is None, 'non_udim_image_descriptor_tuple_required')
        key = self._socket_key(sockets)
        descriptor = result[0]
        mapping = self._descriptor(descriptor, key)
        need(all(row['descriptor'] is not descriptor for row in self.descriptors), 'descriptor_cache_or_alias_refused')
        self.descriptors.append(dict(descriptor=descriptor, key=key, mapping=mapping))
        if self.shared_images_enabled:
            need(self.shared_cache is not None, 'shared_image_attested_cache_missing')
            self.shared_cache.after_descriptor(sockets, descriptor, mapping)

    def image(self, image, descriptor, sockets):
        key = self._socket_key(sockets)
        found = [row for row in self.descriptors if row['descriptor'] is descriptor and _same_key(row['key'], key)]
        need(len(found) == 1 and _same_mapping(self._descriptor(descriptor, key), found[0]['mapping']), 'missing_or_changed_early_image_descriptor')
        need(type(image) is self.gltf.Image and image.mime_type == 'image/png' and image.uri is None and
             image.buffer_view is not None and image.extensions in (None, {}) and image.extras is None,
             'unqualified_webp_external_or_image_extension')
        if self.shared_images_enabled:
            need(self.shared_cache is not None, 'shared_image_attested_cache_missing')
            self.shared_cache.image_hook(image, descriptor, sockets)
            need(all(not _same_key(row['key'], key) for row in self.image_bindings), 'repeated_shared_socket_hook')
            self.image_bindings.append(dict(image=image, descriptor=descriptor, key=key))
            if all(row['image'] is not image for row in self.images):
                self.images.append(dict(image=image, descriptor=descriptor, key=key))
        else:
            need(all(row['image'] is not image for row in self.images), 'repeated_image_hook')
            self.images.append(dict(image=image, descriptor=descriptor, key=key))

    def texture(self, texture, sockets):
        key = self._socket_key(sockets)
        rows = self.image_bindings if self.shared_images_enabled else self.images
        found = [row for row in rows if row['image'] is texture.source and _same_key(row['key'], key)]
        need(type(texture) is self.gltf.Texture and len(found) == 1 and
             texture.extensions in (None, {}) and texture.extras is None,
             'unobserved_image_or_extension_texture')
        need(all(row['texture'] is not texture for row in self.textures), 'repeated_texture_hook')
        self.textures.append(dict(texture=texture, image=texture.source, key=key))

    def texture_info(self, info, sockets):
        key = self._socket_key(sockets)
        found = [row for row in self.textures if row['texture'] is info.index and _same_key(row['key'], key)]
        need(type(info) is self.gltf.TextureInfo and len(found) == 1 and info.tex_coord in (None, 0) and
             type(info.tex_coord) in (type(None), int) and info.extensions in (None, {}) and info.extras is None,
             'unsupported_or_unobserved_texture_info')
        need(all(row['info'] is not info for row in self.infos), 'repeated_texture_info_hook')
        self.infos.append(dict(info=info, texture=info.index, key=key))

    def material(self, material, blender_material):
        self.check_unchanged()
        graph = [row for row in self.graphs if row['material'] is blender_material]
        need(type(material) is self.gltf.Material and len(graph) == 1 and
             material.extensions in (None, {}) and material.extras is None and
             material.normal_texture is None and material.occlusion_texture is None and
             material.emissive_texture is None and material.pbr_metallic_roughness is not None and
             material.pbr_metallic_roughness.metallic_roughness_texture is None,
             'unsupported_gathered_material_profile')
        info = material.pbr_metallic_roughness.base_color_texture
        if graph[0]['images']:
            matches = [row for row in self.infos if row['info'] is info and
                       all(any(_same_rna_key(socket, expected[0]) for expected in graph[0]['socket_keys'])
                           for socket, _, _ in row['key'])]
            need(len(matches) == 1, 'material_texture_reachability_missing')
        else:
            need(info is None, 'unexpected_texture_on_untextured_material')
        need(all(row['material'] is not material and row['source'] is not blender_material
                 for row in self.gathered_materials), 'repeated_or_aliased_material_hook')
        self.gathered_materials.append(dict(material=material, source=blender_material, info=info))

    def bind_primitive_materials(self, materials, internal, gathered):
        for row, primitive in zip(internal, gathered):
            # Authentic scalar dtype admission is the extractor/binder's job.
            slot = row['material']
            source = materials[slot]
            found = [record for record in self.gathered_materials if record['source'] is source]
            need(len(found) == 1 and primitive.material is found[0]['material'],
                 'final_material_deepcopy_or_unobserved_slot')

    def _reference_index(self, kind, value):
        found = [index for actual, index in self.references[kind] if actual is value]
        need(len(found) == 1, 'missing_nested_actual_resource_reference')
        return found[0]

    def reference(self, kind, value, index):
        if self.shared_images_enabled:
            need(self.shared_cache is not None, 'shared_image_attested_cache_missing')
            self.shared_cache.begin_references()
        _index(index)
        table = {'image': self.images, 'texture': self.textures, 'material': self.gathered_materials}[kind]
        found = [row for row in table if row[kind] is value]
        need(len(found) == 1, 'unobserved_root_resource_reference')
        if kind == 'texture':
            expected = self._reference_index('image', found[0]['image'])
            need(type(value.source) is int and value.source == expected, 'texture_image_reference_differs')
        elif kind == 'material' and found[0]['info'] is not None:
            info = found[0]['info']
            record = [row for row in self.infos if row['info'] is info]
            need(len(record) == 1 and type(info.index) is int and
                 info.index == self._reference_index('texture', record[0]['texture']), 'material_texture_reference_differs')
        for actual, prior in self.references[kind]:
            if actual is value:
                need(prior == index, 'resource_reference_reassigned')
                return
            need(prior != index, 'distinct_resource_objects_alias_final_index')
        self.references[kind].append((value, index))

    def finalize(self, document):
        try:
            return self._finalize(document)
        except BaseException:
            if self.shared_images_enabled and self.shared_cache is not None:
                self.shared_cache.failed = True
            raise

    def _finalize(self, document):
        bindings = self.image_bindings if self.shared_images_enabled else self.images
        if self.shared_images_enabled:
            need(self.shared_cache is not None, 'shared_image_attested_cache_missing')
            self.shared_cache.finish()
        need(len(self.gathered_materials) == len(self.materials) and
             len(bindings) == len(self.descriptors) == len(self.textures) == len(self.infos),
             'missing_expected_resource_hook_after_operator')
        reached = {id(image) for row in bindings for _, image, _ in row['key']}
        need(reached == {id(row['image']) for row in self.tickets}, 'missing_expected_source_image_after_operator')
        for kind, key, table in (('image', 'images', self.images), ('texture', 'textures', self.textures),
                                 ('material', 'materials', self.gathered_materials)):
            need(type(document.get(key, [])) is list and len(document.get(key, [])) == len(table) == len(self.references[kind]),
                 'serialized_resource_cardinality_differs')
            need({index for _, index in self.references[kind]} == set(range(len(table))), 'resource_table_coverage_differs')
        for row in self.textures:
            index = self._reference_index('texture', row['texture'])
            source = document['textures'][index].get('source')
            need(type(source) is int and source == self._reference_index('image', row['image']), 'serialized_texture_source_differs')
        for row in self.gathered_materials:
            index = self._reference_index('material', row['material'])
            serialized = document['materials'][index].get('pbrMetallicRoughness', {}).get('baseColorTexture')
            if row['info'] is None:
                need(serialized is None, 'serialized_unexpected_basecolor_texture')
            else:
                need(type(serialized) is dict and type(serialized.get('index')) is int and
                     serialized['index'] == row['info'].index and serialized.get('texCoord', 0) == 0,
                     'serialized_material_texture_differs')
        result = dict(format='has_narrow_actual_resource_reference_observation_2',
                    materials=len(self.gathered_materials), source_images=len(self.tickets),
                    images=len(self.images), textures=len(self.textures),
                    complete_shader_evaluator=False, full_semantic_equivalence=False,
                    resource_global_unreachability_proved=False)
        if self.shared_images_enabled:
            result.update(format='has_narrow_shared_actual_resource_reference_observation_3',
                          image_bindings=len(bindings), cache_observation=self.shared_cache.summary())
        return result
