"""Normalize source-declared MMD groups to prepared standard deform bindings.

No Blender dependency here. Source names are exact identities, never fuzzy matches.
"""
import math

FORMAT = 'studio_expression_presets_1'
EXTRA = 'studio_expression_groups'
MAX_GROUPS = 256
MAX_BINDINGS = 2048


def normalize(groups, document):
    result = {'format': FORMAT, 'entries': [], 'error': ''}
    if len(groups) > MAX_GROUPS:
        result['error'] = 'Embedded expression groups exceed 256 entries.'
        return result
    known = {}
    for group in groups:
        known.setdefault(group['name'], []).append(group)
    targets = {}
    for node_id, node in enumerate(document.get('nodes', [])):
        if 'mesh' not in node:
            continue
        mesh = document['meshes'][node['mesh']]
        names = mesh.get('extras', {}).get('targetNames', [])
        if len(names) != len(set(names)):
            result['error'] = 'An exported mesh has ambiguous expression target names.'
            return result
        for index, name in enumerate(names):
            targets.setdefault(name, []).append((node_id, index))
    operations = 0

    def expand(group, path):
        nonlocal operations
        if group['name'] in path or len(path) >= 32:
            raise ValueError('Cyclic or excessively nested expression group.')
        if len(known[group['name']]) != 1:
            raise ValueError('Ambiguous native expression group name.')
        path = path + (group['name'],)
        leaves = {}
        for reference in group['binds']:
            operations += 1
            if operations > 16384:
                raise ValueError('Expression group expansion exceeds its work budget.')
            weight = reference['weight']
            if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not math.isfinite(weight) or abs(weight) > 100:
                raise ValueError('Invalid native expression weight.')
            if weight == 0:
                continue
            kind, name = reference['kind'], reference['name']
            if kind == 'vertex_morphs':
                if name not in targets:
                    raise ValueError('An expression vertex target was not exported: ' + name)
                child = {key: (1., name) for key in targets[name]}
            elif kind == 'group_morphs':
                if name not in known or len(known[name]) != 1:
                    raise ValueError('Missing or ambiguous nested expression group: ' + name)
                child = expand(known[name][0], path)
            else:
                description = {'bone_morphs': 'bone movement', 'uv_morphs': 'texture-coordinate changes',
                               'material_morphs': 'material or color changes'}.get(kind, 'native effects')
                raise ValueError('This expression needs unsupported ' + description + '.')
            for key, (amount, native_name) in child.items():
                amount = leaves.get(key, (0., native_name))[0] + amount * weight
                if not math.isfinite(amount) or abs(amount) > 100:
                    raise ValueError('Resolved expression weight exceeds the supported range.')
                leaves[key] = (amount, native_name)
        return leaves

    total = 0
    for index, group in enumerate(groups):
        entry = {'id': 'mmd:group:' + str(index), 'native_name': group['name'],
                 'label': group.get('english_name') or group['name'], 'preset': '',
                 'group': 'native group', 'binary': False,
                 'overrides': {'blink': 'none', 'mouth': 'none', 'look': 'none'},
                 'binds': [], 'error': ''}
        try:
            leaves = expand(group, ())
            entry['binds'] = [{'node': str(node), 'index': str(target), 'weight': weight,
                               'native_name': name} for (node, target), (weight, name) in sorted(leaves.items()) if weight != 0]
            if not entry['binds']:
                raise ValueError('This expression has no supported nonzero vertex bindings.')
            total += len(entry['binds'])
            if total > MAX_BINDINGS:
                result['error'] = 'Resolved expressions exceed 2048 bindings.'
                return result
        except ValueError as error:
            entry['binds'] = []  # Refuse the complete pose; never apply a partial group.
            entry['error'] = str(error)
        result['entries'].append(entry)
    return result
