"""Read-only positional deform observations and tentative same-model region matches.

Uses explicit labelled seeds, never names as hidden ground truth. Not a native
controller evaluator, emote detector, cross-model learner or normal editor action.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import time

from secondary_helpers import GLB, integer, unique

AREAS = ('Brows', 'Eyes', 'Mouth', 'Body', 'Clothing', 'Hair', 'Accessories', 'Other')
MAX_OPERATIONS = 64_000_000
MAX_TARGETS = 4096


def seed_index(seeds, source_sha):
    if not isinstance(seeds, dict) or seeds.get('format') != 'studio_deform_seeds_1' or seeds.get('source_sha256') != source_sha:
        raise ValueError('Deform labels must identify the exact source SHA256')
    rows = seeds.get('controls')
    if not isinstance(rows, list) or len(rows) > MAX_TARGETS:
        raise ValueError('Invalid or excessive deform labels')
    result = {}
    for row in rows:
        if not isinstance(row, dict): raise ValueError('Invalid deform label')
        node = integer(row.get('node'), 100000); target = integer(row.get('target'), 2048)
        if (not isinstance(row.get('native_name'), str) or len(row['native_name']) > 512 or
                row.get('area') not in AREAS or row.get('provenance') not in ('Name estimate', 'Manual choice', 'Provisional observed annotation')):
            raise ValueError('Deform labels need explicit area, name and provenance')
        key = (node, target)
        if key in result: raise ValueError('Duplicate deform label identity')
        result[key] = row.copy()
    return result


def region_guess(query_mask, labelled_masks):
    """Identity masks only: never compare vertex IDs across different mesh nodes."""
    count = query_mask.bit_count()
    if not count: return {'area': 'Other', 'reason': 'No positional movement above threshold', 'matches': []}
    unions = {}; best = {}
    for seed, mask in labelled_masks:
        area = seed['area']
        if area == 'Other' or not mask: continue
        unions[area] = unions.get(area, 0) | mask
        common = (query_mask & mask).bit_count()
        similarity = common / math.sqrt(count * mask.bit_count())
        if area not in best or similarity > best[area]['similarity']:
            best[area] = {'area': area, 'similarity': similarity, 'seed_node': seed['node'],
                          'seed_target': seed['target'], 'seed_name': seed['native_name'],
                          'seed_provenance': seed['provenance']}
    matches = sorted(best.values(), key=lambda row: (-row['similarity'], row['area']))
    for row in matches: row['query_coverage'] = (query_mask & unions[row['area']]).bit_count() / count
    result = {'area': 'Other', 'reason': 'Insufficient labelled region evidence', 'matches': matches}
    if not matches: return result
    winner = matches[0]; runner = matches[1]['similarity'] if len(matches) > 1 else 0.
    mixed = any(row['query_coverage'] > .25 for row in matches[1:])
    if mixed: result['reason'] = 'Movement overlaps multiple labelled areas'
    elif winner['similarity'] >= .65 and winner['query_coverage'] >= .7 and winner['similarity'] - runner >= .15:
        result.update(area=winner['area'], reason='Tentative same-model changed-region match')
    return result


def observe(source, seeds=None, cancelled=None):
    started = time.monotonic(); glb = GLB(source)
    def checkpoint():
        if cancelled is not None and cancelled(): raise ValueError('Deform study cancelled')
    checkpoint()
    labels = seed_index(seeds, glb.sha) if seeds is not None else {}
    used = set(); rows = []; operations = 0; target_count = 0
    nodes = glb.doc.get('nodes', [])
    for node_id, node in enumerate(nodes):
        checkpoint()
        if 'mesh' not in node: continue
        mesh = glb.ref('meshes', node['mesh']); primitives = mesh.get('primitives', [])
        if not isinstance(primitives, list) or len(primitives) > 4096: raise ValueError('Invalid deform mesh primitives')
        # Validate exact count/default structure using the shared existing decoder.
        weights = glb.morph_weights(node_id, {'source_morph_defaults': False})
        if not weights: continue
        count = len(weights); target_count += count
        if target_count > MAX_TARGETS: raise ValueError('Deform study exceeds4096target budget')
        names = mesh.get('extras', {}).get('targetNames', [])
        if not isinstance(names, list) or len(names) not in (0, count) or any(not isinstance(name, str) or len(name) > 512 for name in names):
            raise ValueError('Deform target names do not match their identities')
        names = names or ['Shape ' + str(i + 1) for i in range(count)]
        geometry = []; vertex_count = 0; lower = [math.inf] * 3; upper = [-math.inf] * 3
        for primitive in primitives:
            if not isinstance(primitive, dict) or not isinstance(primitive.get('attributes'), dict): raise ValueError('Invalid deform primitive')
            points = glb.accessor(primitive['attributes'].get('POSITION'), 'VEC3')
            vertex_count += len(points)
            if vertex_count > 500000: raise ValueError('Deform part exceeds500000vertex budget')
            for point in points:
                for axis in range(3): lower[axis] = min(lower[axis], point[axis]); upper[axis] = max(upper[axis], point[axis])
            geometry.append((primitive, points))
        if not vertex_count: raise ValueError('Deform part has no neutral vertices')
        scale = math.sqrt(sum((upper[i] - lower[i]) ** 2 for i in range(3)))
        epsilon = max(scale * 1e-6, 1e-10)
        masks = []; part_rows = []
        for target_id, name in enumerate(names):
            checkpoint()
            operations += vertex_count
            if operations > MAX_OPERATIONS: raise ValueError('Deform study exceeds64million vertex-target comparisons; no partial report written')
            mask_bytes = bytearray((vertex_count + 7) // 8); offset = 0; changed = 0
            center = [0.] * 3; delta_mean = [0.] * 3; affected_min = [math.inf] * 3; affected_max = [-math.inf] * 3
            maximum = 0.; normal_or_tangent = False; has_position = False; signed_bounds = {1: None, -1: None}
            for primitive, points in geometry:
                target = primitive['targets'][target_id]
                if not isinstance(target, dict): raise ValueError('Invalid deform target')
                normal_or_tangent |= any(key != 'POSITION' for key in target)
                if 'POSITION' not in target:
                    for sign in (1, -1):
                        bounds = signed_bounds[sign]
                        for point in points:
                            if bounds is None:
                                bounds = [list(point), list(point)]; signed_bounds[sign] = bounds
                            else:
                                for axis in range(3): bounds[0][axis] = min(bounds[0][axis], point[axis]); bounds[1][axis] = max(bounds[1][axis], point[axis])
                    offset += len(points); continue
                has_position = True; deltas = glb.morph_delta(target['POSITION'], len(points))
                for vertex, (point, delta) in enumerate(zip(points, deltas)):
                    if cancelled is not None and vertex % 4096 == 0: checkpoint()
                    distance = math.sqrt(sum(value * value for value in delta)); maximum = max(maximum, distance)
                    # Evaluate both signs from the SAME neutral point, not serially.
                    for sign in (1, -1):
                        after = [point[i] + sign * delta[i] for i in range(3)]
                        if any(not math.isfinite(value) or abs(value) > 100000 for value in after): raise ValueError('Deform produces invalid signed geometry')
                        bounds = signed_bounds[sign]
                        if bounds is None: signed_bounds[sign] = [after.copy(), after.copy()]
                        else:
                            for axis in range(3): bounds[0][axis] = min(bounds[0][axis], after[axis]); bounds[1][axis] = max(bounds[1][axis], after[axis])
                    if distance <= epsilon: continue
                    identity = offset + vertex; mask_bytes[identity // 8] |= 1 << (identity % 8); changed += 1
                    for axis in range(3):
                        center[axis] += point[axis]; delta_mean[axis] += delta[axis]
                        affected_min[axis] = min(affected_min[axis], point[axis]); affected_max[axis] = max(affected_max[axis], point[axis])
                offset += len(points)
            key = (node_id, target_id); label = labels.get(key)
            if label:
                if label['native_name'] != name: raise ValueError('Deform label belongs to a different native target')
                used.add(key)
            masks.append(int.from_bytes(mask_bytes, 'little'))
            row = {'node': node_id, 'mesh': node['mesh'], 'target': target_id, 'native_name': name,
                   'status': 'position_observed' if changed else 'below_position_threshold' if has_position else 'position_unsupported', 'position_supported': has_position,
                   'changed_vertices': changed, 'vertex_count': vertex_count, 'epsilon': epsilon,
                   'changed_mask_sha256': hashlib.sha256(mask_bytes).hexdigest(),
                   'mean_neutral_position': [value / changed for value in center] if changed else None,
                   'mean_positive_displacement': [value / changed for value in delta_mean] if changed else None,
                   'maximum_displacement': maximum, 'affected_neutral_bounds': [affected_min, affected_max] if changed else None,
                   'positive_position_bounds': signed_bounds[1], 'negative_position_bounds': signed_bounds[-1],
                   'nonposition_effects_unevaluated': normal_or_tangent, 'seed': label}
            part_rows.append(row)
        # Self is always excluded: labels cannot be used as their own evidence.
        for index, row in enumerate(part_rows):
            candidates = [(other['seed'], masks[j]) for j, other in enumerate(part_rows) if j != index and other['seed']]
            row['region_estimate'] = region_guess(masks[index], candidates)
        rows.extend(part_rows)
    if used != set(labels): raise ValueError('Deform labels refer to missing target identities')
    if hashlib.sha256(Path(source).read_bytes()).hexdigest() != glb.sha: raise ValueError('Source changed during deform study')
    return {'format': 'studio_deform_observations_1', 'source_sha256': glb.sha, 'coordinate_space': 'per-node neutral mesh local; not posed/head-normalized',
            'target_count': len(rows), 'signed_position_probes': sum(2 for row in rows if row['position_supported']), 'vertex_target_comparisons': operations,
            'seconds': time.monotonic() - started, 'rows': rows, 'source_unchanged': True,
            'native_controller_evaluation': False, 'cross_model_validation': False, 'probability_calibrated': False,
            'notes': ['Signed probes are mathematical positional observations, not a declaration of native control ranges.',
                      'Normals/tangents/material/UV/bone/native corrective behavior is not evaluated.',
                      'Scores compare labelled changed-vertex regions on this same node only; not expression intent.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path); parser.add_argument('output', type=Path); parser.add_argument('--seeds', type=Path)
    options = parser.parse_args()
    if options.output.exists() or options.output.resolve() == options.source.resolve(): raise ValueError('Choose a new report path')
    seeds = None
    if options.seeds:
        if options.seeds.stat().st_size > 1024 * 1024: raise ValueError('Deform seed file exceeds1MiB')
        seeds = json.loads(options.seeds.read_text(encoding='utf-8'), object_pairs_hook=unique)
    report = observe(options.source, seeds)
    with options.output.open('x', encoding='utf-8') as stream: json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({'targets': report['target_count'], 'comparisons': report['vertex_target_comparisons'], 'report': str(options.output)}))


if __name__ == '__main__': main()
