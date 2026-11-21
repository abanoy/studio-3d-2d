"""Atomic composition of explicitly reviewed loose-part setup requests.

Every item is reviewed against the same immutable starting asset. Rebase only the
source checksum while composing disjoint edits through the existing single-item
builder, then publish one final candidate. This module never installs a scene.
"""
from pathlib import Path
import copy
import hashlib
import json
import os
import shutil
import tempfile

import secondary_helpers as helpers

FORMAT = 'studio_secondary_batch_1'
MAX_ITEMS = 128
MAX_NODES = 100000


def _identity(path):
    digest=hashlib.sha256(); total=0
    if not path.is_file() or path.stat().st_size>helpers.MAX_FILE: raise ValueError('Source exceeds128MiB or is not a regular file')
    with path.open('rb') as file:
        while block:=file.read(1024*1024):
            total+=len(block)
            if total>helpers.MAX_FILE: raise ValueError('Source exceeds128MiB')
            digest.update(block)
    return digest.hexdigest(), path.stat().st_mtime_ns


def _region_key(row):
    return tuple(row[k] for k in ('node', 'primitive', 'component'))


def _shape_settings(item):
    defaults = item.get('source_morph_defaults', False)
    if type(defaults) is not bool: raise ValueError('Invalid source morph defaults setting')
    return {'source_morph_defaults': defaults, 'morph_weights': item.get('morph_weights', {})}


def review(source, request):
    """Preview the actual corrected controls instead of regenerating defaults."""
    view = helpers.preview(source, request)
    if view.get('mode') == 'existing_joints':
        if 'points_in_anchor' in request:
            raise ValueError('Existing joints keep their authored chain; remove custom control points')
        return view
    helpers.finite(request.get('strength', .95), .01, 1)
    helpers.finite(request.get('pin_fraction', .2), .01, .4)
    controls = request.get('points_in_anchor', view['points_in_anchor'])
    count = request.get('segments', 3)
    if (not isinstance(controls, list) or len(controls) != count + 1 or
            any(not isinstance(p, (list, tuple)) or len(p) != 3 for p in controls)):
        raise ValueError('Invalid reviewed helper control points')
    controls = [[helpers.finite(v) for v in point] for point in controls]
    length = view['region']['length_in_anchor_units']
    if any(helpers.distance(a, b) < length * .001 for a, b in zip(controls, controls[1:])):
        raise ValueError('Helper chain folds to a zero-length segment; revise its points')
    view['points_in_anchor'] = controls
    return view


def plan(source, request):
    """Validate all original-source proposals and disclose deduplicated chains."""
    glb = helpers.GLB(source)
    if (not isinstance(request, dict) or request.get('format') != FORMAT or
            request.get('reviewed') is not True or request.get('source_sha256') != glb.sha):
        raise ValueError('A reviewed batch and matching original source checksum are required')
    items = request.get('items')
    if not isinstance(items, list) or not 1 <= len(items) <= MAX_ITEMS:
        raise ValueError('Choose1–128reviewed parts')
    operations = []
    weighted = []
    existing = {}
    shape = None
    for ordinal, item in enumerate(items):
        if (not isinstance(item, dict) or item.get('reviewed') is not True or
                item.get('source_sha256') != glb.sha):
            raise ValueError('Every item must be reviewed against the same original source')
        if ordinal == 0: shape = _shape_settings(item)
        if _shape_settings(item) != shape:
            raise ValueError('All parts must use the same reviewed shape snapshot')
        view = review(glb.source, item)
        if not view.get('can_apply', False):
            raise ValueError('Every included part needs a usable reviewed proposal')
        row = view['region']; key = _region_key(row)
        if view.get('mode') == 'existing_joints':
            chain = view['existing_chain']
            identity = (chain['center_node'], *chain['joint_nodes'])
            geometry = {k: chain[k] for k in ('center_node', 'joint_nodes', 'points_in_anchor', 'tail_offset')}
            if identity in existing:
                old = existing[identity]
                if old['geometry'] != geometry:
                    raise ValueError('Shared native joints have inconsistent reviewed endpoints')
                if list(key) not in old['operation']['source_regions']:
                    old['operation']['source_regions'].append(list(key))
                continue
            nodes = set(chain['joint_nodes'])
            if any(nodes & other['nodes'] for other in existing.values()):
                raise ValueError('Native chains overlap; review one shared-joint group')
            operation = {'request': copy.deepcopy(item), 'source_regions': [list(key)],
                         'affected_regions': copy.deepcopy(view['affected_regions']),
                         'mode': 'existing_joints'}
            existing[identity] = {'nodes': nodes, 'geometry': geometry, 'operation': operation}
        else:
            selected = {view['source_vertices'][v] for v in view['selected_vertices']}
            mesh_key = key[:2]
            if any(mesh_key == other['mesh_key'] and selected & other['vertices'] for other in weighted):
                raise ValueError('Weighted selections overlap; refine or remove a duplicate part')
            skin = glb.skin(key[0], key[1])
            influenced = {skin[3]['joints'][j] for v in selected for j, weight in skin[6][v] if weight > 0}
            weighted.append({'mesh_key': mesh_key, 'vertices': selected, 'influenced': influenced})
            operation = {'request': copy.deepcopy(item), 'source_regions': [list(key)], 'mode': 'weighted'}
        operations.append(operation)
    native = set().union(*(group['nodes'] for group in existing.values())) if existing else set()
    if any(native & row['influenced'] for row in weighted):
        raise ValueError('A weighted selection shares moving native joints with an included chain')
    added_skin = sum(int(op['request'].get('segments', 3)) + 1 for op in operations if op['mode'] == 'weighted')
    added_endpoints = sum(op['mode'] == 'existing_joints' for op in operations)
    if len(glb.springs()) + len(operations) > 128: raise ValueError('Batch exceeds128spring chains')
    if len(glb.doc['nodes']) + added_skin + added_endpoints > MAX_NODES:
        raise ValueError('Batch exceeds100000source-node budget')
    if len({j for skin in glb.doc['skins'] for j in skin['joints']}) + added_skin > 512:
        raise ValueError('Batch exceeds512skin-bone budget')
    if len(glb.spring_nodes() | native) + added_skin + added_endpoints > 512:
        raise ValueError('Batch exceeds512spring-node budget')
    return {'format': FORMAT, 'source_sha256': glb.sha, 'requested_items': len(items),
            'operations': operations, 'added_chains': len(operations),
            'added_nodes': added_skin + added_endpoints}


def _new_json(path, value):
    encoded = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with path.open('xb') as file: file.write(encoded); file.flush(); os.fsync(file.fileno())


def build(source, output, request):
    """Produce one complete candidate or fail without installing any revision.

    The returned single reports retain their actual intermediate source SHA. The
    batch manifest separately records their common original review checksum.
    Keep generated_helpers as the last single report and append reports to the
    existing helper-history array when the UI later installs the candidate.
    """
    source = Path(source).resolve(strict=True); original = _identity(source)
    expected_stamp = request.get('source_stamp_ns') if isinstance(request, dict) else None
    if expected_stamp is not None and expected_stamp != str(original[1]):
        raise ValueError('Original source changed since inspection')
    reviewed = plan(source, request)
    output = Path(output).absolute()
    if output.exists() or output.is_symlink(): raise ValueError('Choose a new batch folder; existing files are never replaced')
    output.parent.mkdir(parents=True, exist_ok=True)
    parent = output.parent.resolve(strict=True); output = parent/output.name
    reports = []
    with tempfile.TemporaryDirectory(prefix='.has-secondary-batch-', dir=parent) as temporary:
        staging = Path(temporary).resolve(strict=True)
        current = source
        for index, operation in enumerate(reviewed['operations']):
            rebased = copy.deepcopy(operation['request'])
            rebased['source_sha256'] = helpers.GLB(current).sha
            value = helpers.build(current, staging/f'step-{index}', rebased)
            reports.append(value['report'])
            previous = current; current = Path(value['glb'])
            if previous != source:
                # Only the prior fixed-name folder inside this owned staging root.
                old = previous.parent.resolve(strict=True)
                if old.parent != staging: raise ValueError('Invalid intermediate cleanup path')
                shutil.rmtree(old)
        final_sha = helpers.GLB(current).sha
        if _identity(source) != original: raise ValueError('Original source changed during batch preparation')
        manifest = {'format': FORMAT, 'source_sha256': original[0], 'source_mtime_ns': original[1], 'source_stamp_ns': str(original[1]),
                    'final_sha256': final_sha, 'requested_items': reviewed['requested_items'],
                    'operations': [{k: v for k, v in op.items() if k != 'request'} for op in reviewed['operations']],
                    'reports': reports}
        created = False
        try:
            output.mkdir(exist_ok=False); created = True
            with current.open('rb') as incoming, (output/'scene.glb').open('xb') as outgoing:
                shutil.copyfileobj(incoming, outgoing); outgoing.flush(); os.fsync(outgoing.fileno())
            _new_json(output/'helpers.json', reports[-1])
            _new_json(output/'batch.json', manifest)
            if _identity(output/'scene.glb')[0] != final_sha: raise ValueError('Batch candidate copy did not verify')
            if _identity(source) != original: raise ValueError('Original source changed during batch publication')
        except BaseException:
            if created:
                owned = output.resolve(strict=True)
                if owned.parent != parent or owned != output or output.is_symlink(): raise ValueError('Invalid output cleanup path')
                shutil.rmtree(owned)
            raise
    return {'glb': str(output/'scene.glb'), 'report': reports[-1], 'reports': reports, 'batch': manifest}
