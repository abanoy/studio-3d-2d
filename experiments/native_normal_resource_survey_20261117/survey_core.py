"""Bounded Blender-resource metadata collector. No file IO, pixels or geometry access."""
from dataclasses import dataclass, fields
import hashlib
import json
import ntpath


class SurveyError(ValueError):
    pass


@dataclass(frozen=True)
class Limits:
    images: int = 128
    materials: int = 128
    objects: int = 256
    trees: int = 256
    nodes: int = 2048
    tree_depth: int = 16
    image_references: int = 2048
    external_paths: int = 2048
    packed_per_image: int = 8
    packed_bytes_each: int = 64 * 1024 * 1024
    packed_bytes_total: int = 256 * 1024 * 1024
    string_bytes_each: int = 4096
    string_bytes_total: int = 128 * 1024
    metadata_bytes: int = 512 * 1024


HARD = Limits()


def need(ok, code):
    if not ok: raise SurveyError(code)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def path_metadata(raw, original_blend):
    """Pure lexical classification, not path resolution/existence/identity proof."""
    need(type(raw) is str and type(original_blend) is str, 'PATH_TEXT_TYPE')
    if raw == '': return {'kind': 'EMPTY', 'basename': '', 'original_base_candidate': None}
    if raw.startswith('//'):
        candidate = ntpath.normpath(ntpath.join(ntpath.dirname(original_blend), raw[2:]))
        kind = 'BLEND_RELATIVE'
    elif raw.startswith('\\\\'):
        candidate = None; kind = 'UNSUPPORTED_NETWORK_PATH'
    elif len(raw) >= 3 and raw[1] == ':' and raw[2] in '\\/':
        candidate = ntpath.normpath(raw); kind = 'WINDOWS_ABSOLUTE'
    else:
        candidate = None; kind = 'UNQUALIFIED_RELATIVE_OR_URI'
    # Blender's // prefix denotes a blend-relative path. ntpath would otherwise
    # misread a two-component //directory/file as a complete UNC share.
    return {'kind': kind, 'basename': ntpath.basename(raw[2:] if kind == 'BLEND_RELATIVE' else raw), 'original_base_candidate': candidate}


class Budget:
    def __init__(self, limits):
        need(type(limits) is Limits, 'LIMITS_TYPE')
        for field in fields(Limits):
            value = getattr(limits, field.name)
            need(type(value) is int and 0 <= value <= getattr(HARD, field.name), 'LIMIT_DOMAIN')
        self.limits = limits; self.strings = 0; self.nodes = 0

    def text(self, value):
        need(type(value) is str, 'TEXT_TYPE')
        try: count = len(value.encode('utf-8', errors='strict'))
        except UnicodeError as error: raise SurveyError('TEXT_ENCODING') from error
        need('\0' not in value and count <= self.limits.string_bytes_each, 'TEXT_BOUND')
        self.strings += count
        need(self.strings <= self.limits.string_bytes_total, 'TOTAL_TEXT_BOUND')
        return value

    def integer(self, value, maximum):
        need(type(value) is int and 0 <= value <= maximum, 'INTEGER_BOUND')
        return value

    def boolean(self, value):
        need(type(value) is bool, 'BOOLEAN_TYPE')
        return value

    def collection(self, value, maximum):
        need(len(value) <= maximum, 'COLLECTION_BOUND')
        return list(value)


def pointer(value):
    number = value.as_pointer()
    need(type(number) is int and number > 0, 'RNA_IDENTITY')
    return number


def collect_resources(bpy, original_blend, limits=Limits()):
    """Return detailed private metadata and a path/name-free scalar summary.

    The host separately qualifies the owned blend load and source/closure gates.
    No discovered external pathname is opened, statted, copied or reloaded here.
    """
    budget = Budget(limits); original_blend = budget.text(original_blend)
    def retained_path(raw):
        value = path_metadata(raw, original_blend)
        for key in ('basename', 'original_base_candidate'):
            if value[key] is not None: budget.text(value[key])
        return value
    need(len(bpy.data.libraries) == 0, 'LINKED_LIBRARIES_REFUSED')
    images = budget.collection(bpy.data.images, limits.images)
    materials = budget.collection(bpy.data.materials, limits.materials)
    objects = budget.collection(bpy.context.scene.objects, limits.objects)
    image_ids = {pointer(image): i for i, image in enumerate(images)}
    need(len(image_ids) == len(images), 'DUPLICATE_IMAGE_IDENTITY')
    issues = []; image_rows = []; packed = []; total_packed = 0; path_classes = {}
    for i, image in enumerate(images):
        need(image.library is None, 'LINKED_IMAGE_REFUSED')
        raw = budget.text(image.filepath); raw_source = budget.text(image.filepath_raw)
        group = path_classes.setdefault(raw, len(path_classes))
        row = {'index': i, 'session_identity': pointer(image), 'name': budget.text(image.name),
               'source': budget.text(image.source), 'type': budget.text(image.type),
               'filepath': raw, 'filepath_raw': raw_source, 'raw_filepath_class': group,
               'path': retained_path(raw), 'raw_path': retained_path(raw_source),
               'alpha_mode': budget.text(image.alpha_mode),
               'color_space': budget.text(image.colorspace_settings.name),
               'dirty': budget.boolean(image.is_dirty), 'has_loaded_data': budget.boolean(image.has_data),
               'use_multiview': budget.boolean(image.use_multiview),
               'is_multiview': budget.boolean(image.is_multiview), 'is_stereo_3d': budget.boolean(image.is_stereo_3d),
               'users': budget.integer(image.users, 1_000_000),
               'pixel_properties': 'UNOBSERVED_AVOID_IMBUF_ACQUISITION', 'packed': []}
        if row['source'] != 'FILE' or row['type'] != 'IMAGE': issues.append({'image': i, 'code': 'UNSUPPORTED_IMAGE_SOURCE_OR_TYPE'})
        if row['dirty']: issues.append({'image': i, 'code': 'DIRTY_IMAGE_REFUSED'})
        if raw != raw_source: issues.append({'image': i, 'code': 'FILEPATH_ALIAS_PROFILE_REFUSED'})
        if any(row[key] for key in ('use_multiview', 'is_multiview', 'is_stereo_3d')): issues.append({'image': i, 'code': 'MULTIVIEW_REFUSED'})
        for detail in (row['path'], row['raw_path']):
            if detail['kind'].startswith('UNSUPPORTED') or detail['kind'].startswith('UNQUALIFIED'):
                issues.append({'image': i, 'code': 'PATH_PROFILE_REFUSED'})
        items = budget.collection(image.packed_files, limits.packed_per_image)
        if not raw and not items: issues.append({'image': i, 'code': 'EMPTY_FILE_IMAGE_WITHOUT_PACKED_DATA'})
        if len(items) > 1: issues.append({'image': i, 'code': 'MULTI_PACKED_PROFILE_REFUSED'})
        need((image.packed_file is None) == (len(items) == 0), 'PACKED_POINTER_COUNT_MISMATCH')
        for j, item in enumerate(items):
            handle = item.packed_file
            size = budget.integer(handle.size, limits.packed_bytes_each)
            need(size > 0, 'EMPTY_PACKED_PAYLOAD')
            total_packed += size; need(total_packed <= limits.packed_bytes_total, 'TOTAL_PACKED_BOUND')
            detail = {'part': j, 'bytes': size, 'filepath': budget.text(item.filepath),
                      'view': budget.integer(item.view, 16), 'tile_number': budget.integer(item.tile_number, 1_000_000)}
            detail['path'] = retained_path(detail['filepath'])
            if detail['path']['kind'].startswith(('UNSUPPORTED', 'UNQUALIFIED')):
                issues.append({'image': i, 'packed_part': j, 'code': 'PACKED_PATH_PROFILE_REFUSED'})
            row['packed'].append(detail); packed.append((handle, size, detail))
        if items: need(pointer(image.packed_file) == pointer(items[0].packed_file), 'FIRST_PACKED_IDENTITY_MISMATCH')
        image_rows.append(row)
    # Every stored byte count is admitted before requesting any packed-data copy.
    for handle, size, detail in packed:
        data = handle.data
        stored_size = handle.size
        need(type(data) is bytes and len(data) == size and type(stored_size) is int and stored_size == size, 'PACKED_BYTES_CHANGED')
        detail['sha256'] = hashlib.sha256(data).hexdigest()
    nonempty_packed_classes = {}
    for row in image_rows:
        if row['filepath'] and len(row['packed']) == 1:
            nonempty_packed_classes.setdefault(row['raw_filepath_class'], set()).add(row['packed'][0]['sha256'])
    conflicting_classes = sorted(key for key, hashes in nonempty_packed_classes.items() if len(hashes) > 1)
    for key in conflicting_classes: issues.append({'raw_filepath_class': key, 'code': 'SAME_RAW_PATH_CONFLICTING_PACKED_BYTES'})
    tree_rows = []; material_rows = []; refs = []; tree_ids = {}; stack = set()
    def tree(node_tree, depth):
        need(depth <= limits.tree_depth, 'NODE_TREE_DEPTH')
        key = pointer(node_tree)
        need(key not in stack, 'CYCLIC_NODE_TREE_REFUSED')
        if key in tree_ids: return tree_ids[key]
        need(node_tree.library is None, 'LINKED_NODE_TREE_REFUSED')
        need(len(tree_rows) < limits.trees, 'NODE_TREE_COUNT')
        index = len(tree_rows); tree_ids[key] = index; stack.add(key)
        row = {'index': index, 'session_identity': key, 'name': budget.text(node_tree.name),
               'type': budget.text(node_tree.bl_idname), 'nodes': []}; tree_rows.append(row)
        need(row['type'] == 'ShaderNodeTree', 'UNSUPPORTED_NODE_TREE_TYPE')
        nodes = budget.collection(node_tree.nodes, limits.nodes)
        budget.nodes += len(nodes); need(budget.nodes <= limits.nodes, 'TOTAL_NODE_BOUND')
        for n, node in enumerate(nodes):
            node_row = {'index': n, 'name': budget.text(node.name), 'type': budget.text(node.bl_idname)}
            if node_row['type'] in ('ShaderNodeTexImage', 'ShaderNodeTexEnvironment'):
                image = node.image
                if image is not None:
                    need(pointer(image) in image_ids, 'IMAGE_REFERENCE_OUTSIDE_DATA')
                    node_row['image'] = image_ids[pointer(image)]
                    refs.append({'tree': index, 'node': n, 'image': node_row['image']})
                    need(len(refs) <= limits.image_references, 'IMAGE_REFERENCE_BOUND')
            elif node_row['type'] == 'ShaderNodeGroup' and node.node_tree is not None:
                node_row['group_tree'] = tree(node.node_tree, depth + 1)
            elif node_row['type'] in ('ShaderNodeScript', 'ShaderNodeTexIES'):
                issues.append({'tree': index, 'node': n, 'code': 'UNSUPPORTED_EXTERNAL_NODE'})
            row['nodes'].append(node_row)
        stack.remove(key)
        return index
    for i, material in enumerate(materials):
        need(material.library is None, 'LINKED_MATERIAL_REFUSED')
        row = {'index': i, 'name': budget.text(material.name), 'use_nodes': budget.boolean(material.use_nodes)}
        if material.node_tree is not None: row['tree'] = tree(material.node_tree, 0)
        material_rows.append(row)
    paths = {}
    for label, include_packed in (('all', True), ('unpacked', False)):
        values = bpy.blend_paths(absolute=False, packed=include_packed, local=False)
        need(type(values) is list and len(values) <= limits.external_paths, 'EXTERNAL_PATH_COUNT')
        paths[label] = [{'raw': budget.text(raw), **retained_path(raw)} for raw in values]
    visible = [budget.text(obj.name) for obj in objects if obj.type == 'MESH' and not obj.hide_render and not obj.hide_get()]
    if sorted(visible) != ['Hat.smd', 'hair.smd']: issues.append({'code': 'VISIBLE_MESH_PROFILE_REFUSED'})
    image_paths = {row[key] for row in image_rows for key in ('filepath', 'filepath_raw') if row[key]}
    image_paths.update(item['filepath'] for row in image_rows for item in row['packed'] if item['filepath'])
    for label in paths:
        for i, entry in enumerate(paths[label]):
            if entry['kind'].startswith(('UNSUPPORTED', 'UNQUALIFIED')): issues.append({'path_class': label, 'path_index': i, 'code': 'EXTERNAL_PATH_PROFILE_REFUSED'})
            if entry['raw'] and entry['raw'] not in image_paths: issues.append({'path_class': label, 'path_index': i, 'code': 'UNCLASSIFIED_EXTERNAL_REFERENCE_REFUSED'})
    private = {'format': 'has_private_B_resource_metadata_survey_1', 'images': image_rows,
               'materials': material_rows, 'node_trees': tree_rows, 'material_image_references': refs,
               'external_path_references': paths, 'visible_mesh_names': visible, 'issues': issues,
               'external_path_contents_opened_or_statted': False, 'resource_paths_modified': False,
               'pixel_geometry_matrix_weight_arrays_read': False, 'packed_payloads_included': False}
    raw = canonical(private); need(len(raw) <= limits.metadata_bytes, 'FINAL_METADATA_BOUND')
    public = {'format': 'has_B_resource_metadata_survey_summary_1',
              'status': 'RESOURCE_PROFILE_REFUSED' if issues else 'METADATA_SURVEY_ONLY',
              'images': len(images), 'materials': len(materials), 'node_trees': len(tree_rows),
              'material_image_references': len(refs), 'packed_parts': len(packed), 'packed_bytes': total_packed,
              'raw_filepath_classes': len(path_classes), 'empty_path_packed_images': sum(not row['filepath'] and bool(row['packed']) for row in image_rows),
              'raw_path_classes_with_conflicting_packed_content': len(conflicting_classes),
              'distinct_nonempty_basenames': len({row['path']['basename'] for row in image_rows if row['path']['basename']}),
              'external_paths_including_packed': len(paths['all']), 'unpacked_external_paths': len(paths['unpacked']),
              'profile_issues': len(issues), 'private_metadata_bytes': len(raw), 'private_metadata_sha256': hashlib.sha256(raw).hexdigest(),
              'external_dependency_content_identity': 'UNOBSERVED_NOT_OPENED',
              'native_profile_fidelity_export_or_adoption_qualified': False}
    return private, public
