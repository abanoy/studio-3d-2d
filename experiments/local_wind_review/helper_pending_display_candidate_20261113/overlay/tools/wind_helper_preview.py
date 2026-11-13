"""OUTPUT-ONLY candidate: preview preparation, never helper Apply or model install.

Existing batch composition handles both one focused request and checked requests.
This module returns a hidden, checksum-bound candidate. Main-view import, actual
Godot binding capture and the helper UI integration remain a separate increment.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import os
import stat
import uuid

import secondary_helpers_batch as batch

FORMAT = 'has_wind_helper_preview_1'
MAX_REQUEST = 1024 * 1024
MAX_PROOF = 16 * 1024 * 1024
MAX_RECEIPT = 4 * 1024 * 1024
CONTEXT = {'actor_id', 'root_instance_id', 'revision', 'frame', 'authored_sha256', 'shape_sha256', 'bindings_sha256'}


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False) + '\n').encode('utf-8')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def regular(path, maximum):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.exists():
            value = part.lstat()
            if stat.S_ISLNK(value.st_mode) or getattr(value, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Preview refuses links/reparse paths')
    if not path.is_file() or path.stat().st_size > maximum:
        raise ValueError('Preview input is missing, nonregular or over budget')
    return path


def identity(path):
    path = regular(path, batch.helpers.MAX_FILE)
    before = path.stat()
    with path.open('rb') as stream: sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Source changed while its identity was read')
    return {'sha256': sha, 'bytes': after.st_size, 'mtime_ns': str(after.st_mtime_ns)}


def owned(path, boundary):
    path, boundary = Path(path).absolute(), Path(boundary).absolute()
    if '..' in path.parts or path == boundary or not path.resolve().is_relative_to(boundary.resolve()):
        raise ValueError('Preview output escapes its owned boundary')
    for part in (path, *path.parents):
        if part.exists():
            value = part.lstat()
            if stat.S_ISLNK(value.st_mode) or getattr(value, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Preview output refuses links/reparse paths')
        if part == boundary: break
    return path


def publish(path, value, maximum):
    raw = encoded(value)
    if len(raw) > maximum: raise ValueError('Preview metadata exceeds its bounded budget')
    if path.exists(): raise ValueError('Preview never replaces a published file')
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    # Caller owns a fresh private job directory; no second writer is supported.
    os.replace(temporary, path)
    return digest(raw)


def shape_settings(item):
    defaults = item.get('source_morph_defaults', False)
    if type(defaults) is not bool: raise ValueError('Invalid reviewed shape default choice')
    return {'source_morph_defaults': defaults, 'morph_weights': copy.deepcopy(item.get('morph_weights', {}))}


def validate_envelope(value):
    if not isinstance(value, dict) or value.get('format') != FORMAT or value.get('purpose') != 'preview_only':
        raise ValueError('This operation is preview-only; Apply/install is not admitted')
    if type(value.get('generation')) is not int or not 0 < value['generation'] < 2**31:
        raise ValueError('Invalid draft generation')
    nonce = value.get('nonce', '')
    if not isinstance(nonce, str) or len(nonce) != 32 or any(c not in '0123456789abcdef' for c in nonce):
        raise ValueError('Invalid job nonce')
    context = value.get('context')
    if not isinstance(context, dict) or set(context) != CONTEXT:
        raise ValueError('Incomplete original-actor context')
    if any(not isinstance(v, str) or not 1 <= len(v) <= 256 for v in context.values()):
        raise ValueError('Context values must be bounded strings, not objects or float IDs')
    for key in ('authored_sha256', 'shape_sha256', 'bindings_sha256'):
        if len(context[key]) != 64 or any(c not in '0123456789abcdef' for c in context[key]):
            raise ValueError('Invalid context digest')
    source = value.get('source', {})
    if not isinstance(source.get('path'), str) or not isinstance(source.get('identity'), dict):
        raise ValueError('Missing immutable source identity')
    if value.get('mode') not in ('focused-single', 'included-batch'):
        raise ValueError('Invalid setup draft mode')
    items = value.get('items')
    if not isinstance(items, list) or not 1 <= len(items) <= batch.MAX_ITEMS or value['mode'] == 'focused-single' and len(items) != 1:
        raise ValueError('Choose one focused request or all checked setup members')
    wanted = value.get('shape_settings')
    for item in items:
        if not isinstance(item, dict) or item.get('reviewed') is not True or item.get('source_sha256') != source['identity'].get('sha256'):
            raise ValueError('Every setup item must be reviewed against the original')
        if encoded(shape_settings(item)) != encoded(wanted):
            raise ValueError('Setup members have different shape snapshots')
    return value


def make_envelope(source, items, context, generation, mode='focused-single', nonce=None):
    value = {'format': FORMAT, 'purpose': 'preview_only', 'generation': generation,
             'nonce': nonce or uuid.uuid4().hex, 'context': copy.deepcopy(context),
             'source': {'path': str(Path(source).absolute()), 'identity': identity(source)},
             'mode': mode, 'items': copy.deepcopy(items),
             'shape_settings': shape_settings(items[0]) if items else {}}
    validate_envelope(value)
    if len(encoded(value)) > MAX_REQUEST: raise ValueError('Draft request exceeds1MiB')
    return value


def parents(nodes):
    result = {}
    for index, node in enumerate(nodes):
        for child in node.get('children', []):
            if type(child) is not int or not 0 <= child < len(nodes) or child in result:
                raise ValueError('Ambiguous original node hierarchy')
            result[child] = index
    return result


def retained_bindings(before, after):
    """GLB-level proof only; imported Godot IDs/base transforms need a second gate."""
    original, candidate = before.doc['nodes'], after.doc['nodes']
    if len(candidate) < len(original): raise ValueError('Candidate lost original nodes')
    old_parents, new_parents = parents(original), parents(candidate)
    bindings = []
    for index, node in enumerate(original):
        local = {key: node[key] for key in ('matrix', 'translation', 'rotation', 'scale') if key in node}
        actual = {key: candidate[index][key] for key in ('matrix', 'translation', 'rotation', 'scale') if key in candidate[index]}
        if encoded(local) != encoded(actual) or old_parents.get(index, -1) != new_parents.get(index, -1):
            raise ValueError('Candidate changed a retained source-node base transform or parent')
        bindings.append({'source_node': index, 'candidate_node': index, 'parent_source_node': old_parents.get(index, -1), 'local': local})
    old_skins, new_skins = before.doc.get('skins', []), after.doc.get('skins', [])
    if len(old_skins) != len(new_skins): raise ValueError('Candidate changed the original skin inventory')
    for source, target in zip(old_skins, new_skins):
        joints = source['joints']
        if target['joints'][:len(joints)] != joints or source.get('skeleton') != target.get('skeleton'):
            raise ValueError('Candidate reordered retained skin bindings')
        old_matrices = before.accessor(source['inverseBindMatrices'], 'MAT4') if 'inverseBindMatrices' in source else [batch.helpers.IDENTITY] * len(joints)
        new_matrices = after.accessor(target['inverseBindMatrices'], 'MAT4') if 'inverseBindMatrices' in target else [batch.helpers.IDENTITY] * len(target['joints'])
        if old_matrices != new_matrices[:len(joints)]: raise ValueError('Candidate changed original inverse bind transforms')
    if after.springs()[:len(before.springs())] != before.springs():
        raise ValueError('Candidate changed an existing declaration')
    return {'format': 'has_wind_retained_source_nodes_1', 'original_nodes': len(original),
            'candidate_nodes': len(candidate), 'bindings': bindings,
            'retained_skins': len(old_skins), 'retained_declarations': len(before.springs()),
            'requires_imported_godot_binding_validation': True}


def operation_map(plan, result, before, after):
    operations, reports = plan['operations'], result['reports']
    if len(operations) != len(reports) or result['batch']['operations'] != [{k: v for k, v in op.items() if k != 'request'} for op in operations]:
        raise ValueError('Candidate reports do not match the reviewed plan')
    # The composer returns ordered reports, but row order is not an identity.
    # Match the reviewed region AND generated request-name identity to the actual
    # candidate declaration. This also distinguishes disjoint patches in one row.
    available = list(reports)
    mapped = []
    for operation in operations:
        expected = batch.review(before.source, operation['request'])
        found = []
        for report in available:
            if not isinstance(report, dict): continue
            region = report.get('region', {})
            if [region.get(k) for k in ('node', 'primitive', 'component')] != [operation['request'].get(k) for k in ('node', 'primitive', 'component')]: continue
            rebased = copy.deepcopy(operation['request']); rebased['source_sha256'] = report.get('source_sha256')
            prefix = ('__HAS_Existing_' if operation['mode'] == 'existing_joints' else '__HAS_Loose_') + hashlib.sha256(json.dumps(rebased, sort_keys=True).encode()).hexdigest()[:12]
            nodes = report.get('helper_nodes')
            if not isinstance(nodes, list) or not nodes or any(type(n) is not int or not len(before.doc['nodes']) <= n < len(after.doc['nodes']) for n in nodes): continue
            if len(set(nodes)) != len(nodes): continue
            if operation['mode'] == 'existing_joints':
                configured = expected['existing_chain']['joint_nodes']
                if report.get('mode') != 'existing_joints' or report.get('configured_nodes') != configured or len(nodes) != 1: continue
                if report.get('changed_vertices') != 0 or report.get('source_skin_preserved') is not True: continue
                if after.doc['nodes'][nodes[0]].get('name') != prefix + '_End': continue
                chain_nodes = configured + nodes
                center = expected['existing_chain']['center_node']
            else:
                if report.get('mode', 'weighted') != 'weighted' or len(nodes) != int(operation['request'].get('segments', 3)) + 1: continue
                if encoded(report.get('points_in_anchor')) != encoded(expected['points_in_anchor']): continue
                if any(after.doc['nodes'][node].get('name') != prefix + '_' + str(i) for i, node in enumerate(nodes)): continue
                stored = after.doc['nodes'][nodes[0]].get('extras', {}).get('has_generated_helper', {}).get('authoring')
                if encoded(stored) != encoded(report): continue
                chain_nodes = nodes; center = expected['region']['anchor_node']
            chains = [chain for chain in after.springs() if chain.get('name') == prefix and [row.get('node') for row in chain.get('joints', [])] == chain_nodes and chain.get('center') == center]
            if len(chains) == 1: found.append(report)
        if len(found) != 1: raise ValueError('A report does not uniquely match its reviewed region and actual candidate chain')
        report = found[0]; available.remove(report)
        entry = {'request_sha256': digest(encoded(operation['request'])),
                 'report_sha256': digest(encoded(report)),
                 'source_regions': copy.deepcopy(operation['source_regions']), 'mode': operation['mode'],
                 'configured_source_nodes': report.get('configured_nodes', []),
                 'candidate_helper_nodes': report['helper_nodes'],
                 'affected_regions': copy.deepcopy(report.get('affected_regions', []))}
        entry['operation_id'] = digest(encoded(entry))
        mapped.append(entry)
    return mapped


def build_candidate(job, owned_root):
    """Run synchronously in one owned helper worker; never call any app API."""
    job = owned(job, owned_root)
    request_path = regular(job / 'request.json', MAX_REQUEST)
    for name in ('candidate', 'bindings.json', 'preview-receipt.json'):
        if (job / name).exists(): raise ValueError('Preview job has already been used')
    raw = request_path.read_bytes(); request = validate_envelope(json.loads(raw))
    source = regular(request['source']['path'], batch.helpers.MAX_FILE)
    if identity(source) != request['source']['identity']: raise ValueError('Original source changed before preparation')
    before = batch.helpers.GLB(source)
    setup = {'format': batch.FORMAT, 'source_sha256': before.sha,
             'source_stamp_ns': request['source']['identity']['mtime_ns'],
             'reviewed': True, 'items': copy.deepcopy(request['items'])}
    plan = batch.plan(source, setup)
    result = batch.build(source, job / 'candidate', setup)
    candidate_path = owned(result['glb'], job)
    after = batch.helpers.GLB(regular(candidate_path, batch.helpers.MAX_FILE))
    if after.sha != result['batch']['final_sha256']: raise ValueError('Candidate checksum does not match its own complete build')
    proof = retained_bindings(before, after)
    operations = operation_map(plan, result, before, after)
    if identity(source) != request['source']['identity'] or digest(request_path.read_bytes()) != digest(raw):
        raise ValueError('Original source or exact draft request changed during preparation')
    proof.update(request_file_sha256=digest(raw), candidate_sha256=after.sha,
                 source_identity=copy.deepcopy(request['source']['identity']), operations=copy.deepcopy(operations))
    proof_sha = publish(job / 'bindings.json', proof, MAX_PROOF)
    receipt = {'format': FORMAT, 'purpose': 'preview_only', 'status': 'prepared_hidden',
               'generation': request['generation'], 'nonce': request['nonce'],
               'request_file_sha256': digest(raw), 'context': copy.deepcopy(request['context']),
               'source': copy.deepcopy(request['source']), 'shape_settings': copy.deepcopy(request['shape_settings']),
               'candidate': {'path': 'candidate/scene.glb', 'identity': identity(candidate_path)},
               'bindings': {'path': 'bindings.json', 'sha256': proof_sha}, 'operations': operations,
               'reports': result['reports'], 'setup_members_built': len(request['items']),
               'managed_asset_created': False, 'authored_edit_created': False, 'render_admitted': False}
    receipt_sha = publish(job / 'preview-receipt.json', receipt, MAX_RECEIPT)
    # The future owned-worker adapter must deliver this completion over its
    # trusted exit0 result/pipe, not recompute it from an editable receipt file.
    return {'receipt': receipt, 'completion': {'format': FORMAT, 'generation': request['generation'],
            'nonce': request['nonce'], 'request_file_sha256': digest(raw), 'receipt_sha256': receipt_sha}}


def check_receipt(job, owned_root, expected_digest, current_context, completed_receipt_sha256):
    job = owned(job, owned_root)
    request_path = regular(job / 'request.json', MAX_REQUEST)
    raw = request_path.read_bytes(); request = validate_envelope(json.loads(raw))
    if digest(raw) != expected_digest: raise ValueError('The original draft request bytes changed')
    receipt_raw = regular(job / 'preview-receipt.json', MAX_RECEIPT).read_bytes()
    if not isinstance(completed_receipt_sha256, str) or len(completed_receipt_sha256) != 64 or digest(receipt_raw) != completed_receipt_sha256:
        raise ValueError('Published receipt changed after trusted worker completion')
    receipt = json.loads(receipt_raw)
    for key in ('format', 'purpose', 'generation', 'nonce', 'context', 'source', 'shape_settings'):
        if encoded(receipt.get(key)) != encoded(request[key]): raise ValueError('Late or mismatched preview receipt: ' + key)
    if receipt.get('request_file_sha256') != expected_digest or receipt.get('status') != 'prepared_hidden' or receipt.get('render_admitted') is not False:
        raise ValueError('Preview receipt has no hidden-only admission identity')
    if current_context != request['context'] or identity(request['source']['path']) != request['source']['identity']:
        raise ValueError('The original actor/draft/source changed before import')
    if receipt['candidate']['path'] != 'candidate/scene.glb' or receipt['bindings']['path'] != 'bindings.json':
        raise ValueError('Preview receipt changed its fixed candidate paths')
    candidate_path = regular(owned(job / receipt['candidate']['path'], job), batch.helpers.MAX_FILE)
    proof_path = regular(owned(job / receipt['bindings']['path'], job), MAX_PROOF)
    if identity(candidate_path) != receipt['candidate']['identity'] or digest(proof_path.read_bytes()) != receipt['bindings']['sha256']:
        raise ValueError('Prepared candidate or bindings changed after publication')
    proof = json.loads(proof_path.read_bytes())
    if proof.get('request_file_sha256') != expected_digest or proof.get('candidate_sha256') != receipt['candidate']['identity']['sha256'] or proof.get('source_identity') != request['source']['identity'] or proof.get('operations') != receipt.get('operations'):
        raise ValueError('Candidate binding proof does not match the exact draft/receipt')
    if receipt.get('managed_asset_created') is not False or receipt.get('authored_edit_created') is not False:
        raise ValueError('Preview is not an authored transaction')
    return receipt


class DraftLease:
    """CPU reference state machine; never starts a process or owns app physics."""
    def __init__(self, owned_root):
        self.owned_root = Path(owned_root).absolute()
        self.generation = 0; self.phase = 'stopped'; self.pending = None; self.prepared = None

    def begin(self, source, items, context, mode='focused-single'):
        self.invalidate('new draft')
        job = owned(self.owned_root / uuid.uuid4().hex, self.owned_root)
        job.mkdir(parents=True, exist_ok=False)
        request = make_envelope(source, items, context, self.generation, mode)
        request_sha = publish(job / 'request.json', request, MAX_REQUEST)
        self.pending = {'job': job, 'request_sha256': request_sha, 'generation': self.generation, 'nonce': request['nonce']}
        self.phase = 'building'
        return copy.deepcopy(self.pending)

    def invalidate(self, reason='cancelled'):
        self.generation += 1; self.phase = 'stopped'; self.pending = None; self.prepared = None
        # Never remove a directory or kill a reused PID from this reference state.
        # The UI's owned-job adapter must confirm exit before any later cleanup.

    def accept(self, current_context, completion):
        if self.phase != 'building' or self.pending is None: raise ValueError('No live draft job')
        try:
            if not isinstance(completion, dict) or completion.get('format') != FORMAT or type(completion.get('generation')) is not int or completion['generation'] != self.generation or completion.get('nonce') != self.pending['nonce'] or completion.get('request_file_sha256') != self.pending['request_sha256']:
                raise ValueError('Late or mismatched trusted worker completion')
            receipt = check_receipt(self.pending['job'], self.owned_root, self.pending['request_sha256'], current_context, completion.get('receipt_sha256'))
            if receipt['generation'] != self.generation or receipt['nonce'] != self.pending['nonce']:
                raise ValueError('Stale draft generation')
        except Exception:
            self.invalidate('receipt rejected')
            raise
        self.prepared = copy.deepcopy(receipt); self.phase = 'prepared_hidden'
        return copy.deepcopy(receipt)


def imported_binding_map(source_table, candidate_table):
    """Pure second-gate predicate for a future actual-Godot snapshot adapter.

    Keys are original source-node indexes (strings), not names or list rows.
    Values contain kind, id and full base transform arrays from live imports.
    """
    if not isinstance(source_table, dict) or not source_table or not isinstance(candidate_table, dict):
        raise ValueError('An actual imported source binding snapshot is required')
    result = {}; seen_source = set(); seen_candidate = set()
    for node, original in source_table.items():
        candidate = candidate_table.get(node)
        if not isinstance(node, str) or not node.isdigit() or not isinstance(original, dict) or original.get('kind') not in ('bone', 'node', 'offset'):
            raise ValueError('Bindings must be keyed by original source-node indexes')
        base = original.get('base')
        if not isinstance(base, list) or len(base) != 16 or any(type(v) not in (float, int) or not math.isfinite(v) for v in base):
            raise ValueError('Imported base transforms need finite complete matrices')
        if not isinstance(candidate, dict) or candidate.get('kind') != original.get('kind') or candidate.get('base') != original.get('base'):
            raise ValueError('An imported retained binding or base transform changed')
        if not isinstance(original.get('id'), str) or not original['id'] or not isinstance(candidate.get('id'), str) or not candidate['id']:
            raise ValueError('Imported bindings are missing or aliased')
        if original['kind'] != 'offset':
            if original['id'] in seen_source or candidate['id'] in seen_candidate: raise ValueError('Imported bone/node bindings alias another source node')
            seen_source.add(original['id']); seen_candidate.add(candidate['id'])
        result[node] = {'source_binding': copy.deepcopy(original), 'candidate_binding': copy.deepcopy(candidate)}
    return result
