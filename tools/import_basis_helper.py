"""Strict reference preservation for the existing-joint helper derivative.

No fitting or posed-instance measurements. A complete source GLB and candidate
are compared independently of the helper builder. Weighted derivations are not
admitted by this deliberately narrow proof.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import re

import secondary_helpers as helpers

FORMAT = 'studio_import_basis_preservation_1'
PAYLOAD = 'studio_import_basis_preservation_payload_1'
METHOD = 'exact_existing_joint_endpoints_1'
MAX_ENDPOINTS = 128


def encoded(value):
    # JSON token spelling distinguishes Boolean/integer/float and signed zero.
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('utf-8')


def same(left, right):
    return encoded(left) == encoded(right)


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def _snapshot(path):
    value = Path(path).resolve(strict=True)
    before = value.stat()
    glb = helpers.GLB(value)
    after = value.stat()
    fields = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    require(fields(before) == fields(after), 'Reference source changed during preservation review')
    return glb, fields(after)


def _check_unchanged(glb, stamp):
    now = glb.source.stat()
    require((now.st_dev, now.st_ino, now.st_size, now.st_mtime_ns) == stamp
            and hashlib.sha256(glb.source.read_bytes()).hexdigest() == glb.sha,
            'Reference source changed during preservation review')


def check_existing_derivative(source, candidate, parent_sha256, source_sha256):
    """Return a hash-bound proof only for additive unweighted endpoint setup.

    All original binary bytes and JSON semantics are exact, except appending
    fresh unweighted leaf children and additive HAS spring declarations. That
    preserves geometry, source root/rest/skin/morph data in every original node.
    It does not authenticate SDK behavior, posed measurements or native fidelity.
    """
    require(sha(parent_sha256) and sha(source_sha256) and parent_sha256 != source_sha256,
            'Distinct exact reference source identities required')
    before, before_stamp = _snapshot(source)
    after, after_stamp = _snapshot(candidate)
    require(before.source != after.source and before.sha == parent_sha256 and after.sha == source_sha256,
            'Reference preservation source identity differs')
    # Retain the existing combined native/HAS spring-count admission too.
    before.springs()
    after.springs()
    require(bytes(before.binary) == bytes(after.binary),
            'Adding weighted joints needs a separate reference-preservation proof')
    original = before.doc
    result = copy.deepcopy(after.doc)
    old_nodes = original.get('nodes', [])
    new_nodes = result.get('nodes', [])
    count = len(old_nodes)
    require(0 < count <= 100000 and count < len(new_nodes) <= min(100000, count + MAX_ENDPOINTS),
            'Reference preservation requires bounded additive endpoint nodes')
    endpoints = set(range(count, len(new_nodes)))
    attached = set()
    for index, old in enumerate(old_nodes):
        current = new_nodes[index]
        require(type(old) is dict and type(current) is dict, 'Invalid retained reference node')
        old_children = old.get('children', [])
        children = current.get('children', [])
        require(type(old_children) is list and type(children) is list
                and same(children[:len(old_children)], old_children),
                'An original reference hierarchy changed')
        for child in children[len(old_children):]:
            require(type(child) is int and child in endpoints and child not in attached,
                    'Only uniquely attached new unweighted endpoints may be added')
            attached.add(child)
        if 'children' in old:
            current['children'] = copy.deepcopy(old_children)
        else:
            current.pop('children', None)
        require(same(current, old), 'An original reference root/rest/node field changed')
    require(attached == endpoints, 'Every new endpoint needs one original parent')
    for index in sorted(endpoints):
        node = new_nodes[index]
        require(type(node) is dict and set(node) == {'name', 'translation', 'extras'},
                'New endpoint must have no mesh, skin, scale, rotation or children')
        require(type(node['name']) is str and re.fullmatch('__HAS_Existing_[0-9a-f]{12}_End', node['name']),
                'Unknown reference endpoint identity')
        position = node['translation']
        require(type(position) is list and len(position) == 3
                and all(type(v) in (int, float) and math.isfinite(v) and abs(v) <= 100000 for v in position),
                'Bounded endpoint translation required')
        extra = node['extras']
        require(type(extra) is dict and set(extra) == {'has_generated_helper_endpoint'},
                'Unknown endpoint metadata')
        details = extra['has_generated_helper_endpoint']
        require(type(details) is dict and set(details) == {'source_sha256', 'chain'}
                and sha(details['source_sha256']) and details['chain'] == node['name'][:-4],
                'Endpoint provenance differs')
    new_nodes[:] = new_nodes[:count]
    old_extras = original.get('extras', {})
    extras = result.get('extras', {})
    require(type(old_extras) is dict and type(extras) is dict, 'Reference extras must be objects')
    old_helpers = old_extras.get('has_secondary_helpers_1')
    added_helpers = extras.get('has_secondary_helpers_1')
    require(type(added_helpers) is dict and type(added_helpers.get('springs')) is list,
            'Additive helper declaration required')
    old_springs = old_helpers.get('springs', []) if type(old_helpers) is dict else []
    springs = added_helpers['springs']
    require(type(old_springs) is list and len(springs) == len(old_springs) + len(endpoints)
            and len(springs) <= MAX_ENDPOINTS and same(springs[:len(old_springs)], old_springs),
            'Original reference motion declarations changed')
    declared = set()
    for spring in springs[len(old_springs):]:
        require(type(spring) is dict and set(spring) == {'name', 'center', 'joints'}
                and type(spring['center']) is int and 0 <= spring['center'] < count,
                'Invalid additive existing-joint declaration')
        joints = spring['joints']
        require(type(joints) is list and 3 <= len(joints) <= 512, 'Bounded existing-joint chain required')
        for ordinal, row in enumerate(joints):
            require(type(row) is dict and set(row) == {'node', 'stiffness', 'dragForce', 'hitRadius'}
                    and type(row['node']) is int
                    and same({k: row[k] for k in ('stiffness', 'dragForce', 'hitRadius')},
                             {'stiffness': 1., 'dragForce': .45, 'hitRadius': .005}),
                    'Unknown new helper declaration')
            require(0 <= row['node'] < count if ordinal < len(joints) - 1 else row['node'] in endpoints,
                    'Existing-joint declaration changes original ownership')
        end = joints[-1]['node']
        require(end not in declared and after.doc['nodes'][end]['name'] == spring['name'] + '_End',
                'Endpoint declaration identity differs')
        declared.add(end)
    require(declared == endpoints, 'Every endpoint needs its exact added declaration')
    if old_helpers is None:
        require(set(added_helpers) == {'specVersion', 'springs'} and added_helpers['specVersion'] == '1.0',
                'Unknown new helper container')
        extras.pop('has_secondary_helpers_1')
    else:
        added_helpers['springs'] = copy.deepcopy(old_springs)
        require(same(added_helpers, old_helpers), 'Existing helper container changed')
    if 'extras' not in original:
        require(not extras, 'New unrelated reference extras are unsupported')
        result.pop('extras', None)
    require(same(result, original), 'Reference geometry/skin/morph/material or scene fields changed')
    _check_unchanged(before, before_stamp)
    _check_unchanged(after, after_stamp)
    payload = {
        'format': PAYLOAD, 'method': METHOD,
        'parent_sha256': before.sha, 'source_sha256': after.sha,
        'geometry_root_rest_skin_morph_preserved': True, 'exact_binary_preserved': True,
        'source_document_sha256': hashlib.sha256(encoded(original)).hexdigest(),
        'source_binary_sha256': hashlib.sha256(bytes(before.binary)).hexdigest(),
        'original_nodes': count, 'appended_unweighted_endpoints': len(endpoints),
        'original_springs': len(old_springs), 'candidate_springs': len(springs),
    }
    text = encoded(payload).decode('ascii')
    return {'format': FORMAT, 'parent_sha256': before.sha, 'source_sha256': after.sha,
            'preservation_sha256': hashlib.sha256(text.encode()).hexdigest(), 'payload': text}
