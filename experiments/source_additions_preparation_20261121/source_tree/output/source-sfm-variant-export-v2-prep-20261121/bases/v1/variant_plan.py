"""Pure draft HAS appearance-variant contract; no files, engine or native parser.

Inputs must come from a separately qualified all-variant exporter and GLB node/
material inventory. Validating integers does not prove native correspondence.
A plan is computed completely before a future engine adapter makes any writes.
"""
import copy
import json
import re

FORMAT = 'studio_model_variants_1'
INVENTORY = 'studio_variant_asset_inventory_1'
SELECTION = 'studio_variant_selection_1'
PLAN = 'studio_variant_apply_plan_1'
MAX_METADATA = 256 * 1024
MAX_GROUPS = 32
MAX_CHOICES = 64
MAX_TOTAL_CHOICES = 512
MAX_SKINS = 64
MAX_NODES = 4096
MAX_SURFACES = 16384
MAX_MATERIALS = 256


class Refusal(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise Refusal(code)


def fields(value, keys, code):
    need(type(value) is dict, code)
    need(all(type(k) is str for k in value), code)
    need(set(value) == set(keys), code)


def whole(value, low, high, code):
    need(type(value) is int and low <= value <= high, code)
    return value


def label(value, code):
    need(type(value) is str and len(value) <= 1024, code)
    need(all(ord(c) >= 32 and ord(c) != 127 for c in value), code)
    try:
        need(len(value.encode('utf8')) <= 4096, code)
    except UnicodeError:
        raise Refusal(code) from None
    return value  # Keep exact case, spaces and Unicode; IDs are numeric.


def sha(value, code):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None, code)
    return value


def bounded(rows, low, high, code):
    need(type(rows) is list and low <= len(rows) <= high, code)
    return rows


def _inventory(value):
    fields(value, ('format', 'asset_sha256', 'material_count', 'mesh_nodes'), 'inventory_fields')
    need(type(value['format']) is str and value['format'] == INVENTORY, 'inventory_format')
    asset = sha(value['asset_sha256'], 'inventory_asset')
    count = whole(value['material_count'], 1, MAX_MATERIALS, 'inventory_material_count')
    nodes = {}
    total = 0
    for row in bounded(value['mesh_nodes'], 1, MAX_NODES, 'inventory_nodes'):
        fields(row, ('node', 'parent_mesh', 'surface_materials'), 'inventory_node_fields')
        node = whole(row['node'], 0, 99999, 'inventory_node')
        need(node not in nodes, 'inventory_duplicate_node')
        parent = row['parent_mesh']
        if parent is not None:
            whole(parent, 0, 99999, 'inventory_parent')
        mats = bounded(row['surface_materials'], 1, 256, 'inventory_surfaces')
        for mat in mats:
            whole(mat, 0, count - 1, 'inventory_material')
        total += len(mats)
        need(total <= MAX_SURFACES, 'inventory_surface_budget')
        nodes[node] = {'node': node, 'parent_mesh': parent, 'surface_materials': list(mats)}
    for node in nodes:
        visited = set()
        at = node
        while at is not None:
            need(at in nodes and at not in visited, 'inventory_parent_graph')
            visited.add(at)
            at = nodes[at]['parent_mesh']
    return asset, count, nodes


def validate_manifest(value, inventory):
    """Return a detached canonical manifest or refuse the entire declaration."""
    asset, count, nodes = _inventory(inventory)
    fields(value, ('format', 'asset_sha256', 'default_skin', 'skins', 'groups', 'surfaces'), 'manifest_fields')
    need(type(value['format']) is str and value['format'] == FORMAT, 'manifest_format')
    need(sha(value['asset_sha256'], 'manifest_asset') == asset, 'manifest_asset_mismatch')
    skins = []
    for index, row in enumerate(bounded(value['skins'], 1, MAX_SKINS, 'manifest_skins')):
        fields(row, ('id', 'name'), 'skin_fields')
        need(type(row['id']) is int and row['id'] == index, 'skin_ids')
        skins.append({'id': index, 'name': label(row['name'], 'skin_name')})
    default_skin = whole(value['default_skin'], 0, len(skins) - 1, 'default_skin')
    groups = []
    owned = set()
    total_choices = 0
    for group_id, group in enumerate(bounded(value['groups'], 0, MAX_GROUPS, 'manifest_groups')):
        fields(group, ('id', 'name', 'default', 'choices'), 'group_fields')
        need(type(group['id']) is int and group['id'] == group_id, 'group_ids')
        choices = []
        for choice_id, row in enumerate(bounded(group['choices'], 1, MAX_CHOICES, 'group_choices')):
            fields(row, ('id', 'name', 'blank', 'nodes'), 'choice_fields')
            need(type(row['id']) is int and row['id'] == choice_id, 'choice_ids')
            need(type(row['blank']) is bool, 'choice_blank_type')
            bound = bounded(row['nodes'], 0, MAX_NODES, 'choice_nodes')
            need(row['blank'] == (len(bound) == 0), 'choice_blank_nodes')
            local = []
            for node in bound:
                whole(node, 0, 99999, 'choice_node')
                need(node in nodes and node not in owned, 'choice_node_ownership')
                local.append(node)
                owned.add(node)
            choices.append({'id': choice_id, 'name': label(row['name'], 'choice_name'),
                            'blank': row['blank'], 'nodes': sorted(local)})
        total_choices += len(choices)
        need(total_choices <= MAX_TOTAL_CHOICES, 'choice_budget')
        default = whole(group['default'], 0, len(choices) - 1, 'group_default')
        groups.append({'id': group_id, 'name': label(group['name'], 'group_name'),
                       'default': default, 'choices': choices})
    # First profile does not hide ancestors of another mesh. Otherwise a node
    # visibility write could silently affect geometry outside its own choice.
    for node in nodes:
        at = nodes[node]['parent_mesh']
        while at is not None:
            need(at not in owned, 'controlled_mesh_has_mesh_descendant')
            at = nodes[at]['parent_mesh']
    surfaces = {}
    for row in bounded(value['surfaces'], 1, MAX_SURFACES, 'manifest_surfaces'):
        fields(row, ('node', 'surface', 'materials'), 'surface_fields')
        node = whole(row['node'], 0, 99999, 'surface_node')
        need(node in nodes, 'surface_node_missing')
        surface = whole(row['surface'], 0, len(nodes[node]['surface_materials']) - 1, 'surface_index')
        key = (node, surface)
        need(key not in surfaces, 'surface_duplicate')
        mats = bounded(row['materials'], len(skins), len(skins), 'surface_skin_count')
        for mat in mats:
            whole(mat, 0, count - 1, 'surface_material')
        need(mats[default_skin] == nodes[node]['surface_materials'][surface], 'default_material_mismatch')
        surfaces[key] = {'node': node, 'surface': surface, 'materials': list(mats)}
    expected = {(node, surface) for node, row in nodes.items()
                for surface in range(len(row['surface_materials']))}
    need(set(surfaces) == expected, 'surface_coverage')
    result = {'format': FORMAT, 'asset_sha256': asset, 'default_skin': default_skin,
              'skins': skins, 'groups': groups,
              'surfaces': [surfaces[key] for key in sorted(surfaces)]}
    encoded = json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('ascii')
    need(len(encoded) <= MAX_METADATA, 'manifest_metadata_budget')
    return result


def _selection(value, manifest):
    fields(value, ('format', 'skin', 'groups'), 'selection_fields')
    need(type(value['format']) is str and value['format'] == SELECTION, 'selection_format')
    skin = whole(value['skin'], 0, len(manifest['skins']) - 1, 'selection_skin')
    need(type(value['groups']) is dict and all(type(k) is str for k in value['groups']), 'selection_groups')
    need(set(value['groups']) == {str(row['id']) for row in manifest['groups']}, 'selection_group_coverage')
    chosen = {}
    for row in manifest['groups']:
        key = str(row['id'])
        chosen[key] = whole(value['groups'][key], 0, len(row['choices']) - 1, 'selection_choice')
    return {'format': SELECTION, 'skin': skin, 'groups': chosen}


def default_selection(manifest, inventory):
    made = validate_manifest(manifest, inventory)
    return {'format': SELECTION, 'skin': made['default_skin'],
            'groups': {str(row['id']): row['default'] for row in made['groups']}}


def _plan(manifest, selected):
    controlled = set()
    visible = set()
    for group in manifest['groups']:
        for row in group['choices']:
            controlled.update(row['nodes'])
        visible.update(group['choices'][selected['groups'][str(group['id'])]]['nodes'])
    return {'format': PLAN, 'asset_sha256': manifest['asset_sha256'],
            'selection': copy.deepcopy(selected),
            'visibility': [{'node': node, 'visible': node in visible} for node in sorted(controlled)],
            'materials': [{'node': row['node'], 'surface': row['surface'],
                           'material': row['materials'][selected['skin']]} for row in manifest['surfaces']]}


def plan_selection(manifest, inventory, selected):
    """No engine writes, filenames, decoded arrays or resource names in output."""
    made = validate_manifest(manifest, inventory)
    return _plan(made, _selection(selected, made))


def plan_change(manifest, inventory, current, *, skin=None, groups=None):
    """Build complete before/after plans; rejected requests mutate no input."""
    made = validate_manifest(manifest, inventory)
    before = _selection(current, made)
    after = copy.deepcopy(before)
    if skin is not None:
        after['skin'] = whole(skin, 0, len(made['skins']) - 1, 'selection_skin')
    if groups is not None:
        need(type(groups) is dict and all(type(k) is str for k in groups), 'change_groups')
        need(set(groups) <= set(after['groups']), 'change_unknown_group')
        after['groups'].update(groups)
    after = _selection(after, made)
    return {'format': 'studio_variant_transition_plan_1',
            'before': _plan(made, before), 'after': _plan(made, after),
            'changed': before != after}
