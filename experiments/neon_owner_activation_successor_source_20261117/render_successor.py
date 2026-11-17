"""Pure RAM byte renderer. It neither qualifies facts nor reads or writes files."""
import ast
import hashlib
import json
import re

PARENTS = {
    'executor': ('6b5e6c8a04760e44632967d9e700120cf8958c6a53a74fc3904fb09765054372',
                 'qualified_inputs.py', 'APPROVED_ACTIVATION_SHA256',
                 '15fcdbe33334476957f0ed7bd88a3161a35363d673bf6eb9e520455ec232ec26'),
    'validator': ('7b12445a5c7f49076c5510f7d998c9d285b8d1297c56912a8488786d57f31888',
                  'validation_admission.py', 'APPROVED_VALIDATION_ACTIVATION_SHA256',
                  '7c203314018aa5396e12e26cccbb3a5b09d7fa6855f5cbd54d84b5d164a25b0b'),
}
EXECUTOR_EXTRAS = {'OWNER_ARCHIVE_CATALOGUE.json', 'MERGED_WORKING_RECIPE.json',
                   'REVIEWED52_TO_CANDIDATE_DELTA.json'}


def need(ok, detail):
    if not ok:
        raise ValueError(detail)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, allow_nan=False) + '\n').encode('utf-8')


def parse(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'Duplicate source index key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite source index')))


def activation_literal(raw, name, approved):
    """Replace exactly the inactive assignment, then prove byte and AST inverses."""
    need(type(raw) is bytes and type(approved) is str and re.fullmatch('[a-f0-9]{64}', approved), 'Exact source bytes and approved SHA256')
    tree = ast.parse(raw)
    targets = [node for node in tree.body if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    need(len(targets) == 1 and len(targets[0].targets) == 1
         and isinstance(targets[0].value, ast.Constant) and targets[0].value.value is None,
         'Exactly one inactive activation assignment')
    node = targets[0].value
    lines = raw.splitlines(keepends=True)
    start = sum(map(len, lines[:node.lineno - 1])) + node.col_offset
    end = sum(map(len, lines[:node.end_lineno - 1])) + node.end_col_offset
    need(raw[start:end] == b'None', 'Exact original activation literal')
    literal = repr(approved).encode('ascii')
    changed = raw[:start] + literal + raw[end:]
    need(changed[:start] + b'None' + changed[start + len(literal):] == raw, 'Activation raw byte inverse')
    normal = ast.parse(changed)
    normalized = [node for node in normal.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    normalized[0].value = ast.Constant(None)
    need(ast.dump(normal, include_attributes=False) == ast.dump(tree, include_attributes=False), 'Only activation literal may change')
    return changed


def render(kind, parent_files, activation_raw, approved_activation_sha256, extra_payloads=None):
    """Return a new filename-to-bytes map; the caller must review before writing."""
    need(kind in PARENTS and type(parent_files) is dict, 'Known sealed parent and RAM file map')
    index_sha, code_name, gate, code_sha = PARENTS[kind]
    need(type(activation_raw) is bytes and 0 < len(activation_raw) <= 8 * 1024 * 1024
         and type(approved_activation_sha256) is str
         and approved_activation_sha256 == sha(activation_raw), 'Root-reviewed exact activation bytes/hash required')
    need(type(parent_files.get('INDEX.json')) is bytes and sha(parent_files['INDEX.json']) == index_sha, 'Exact sealed parent INDEX')
    rows = parse(parent_files['INDEX.json'])['files']
    need(type(rows) is list and all(type(row) is dict for row in rows), 'Parent source index rows')
    names = [row['path'] for row in rows]
    need(len(set(names)) == len(names) and set(parent_files) == set(names) | {'INDEX.json'}, 'Exact closed parent membership')
    for row in rows:
        raw = parent_files[row['path']]
        need(type(raw) is bytes and type(row['bytes']) is int and len(raw) == row['bytes']
             and sha(raw) == row['sha256'], 'Exact parent payload bytes')
    need(sha(parent_files[code_name]) == code_sha, 'Sealed inactive gate source')
    extra_payloads = {} if extra_payloads is None else extra_payloads
    need(type(extra_payloads) is dict and set(extra_payloads) == (EXECUTOR_EXTRAS if kind == 'executor' else set()), 'Exact successor-only source metadata roles')
    need(all(type(raw) is bytes and len(raw) <= 16 * 1024 * 1024 for raw in extra_payloads.values()), 'Bounded source metadata bytes')
    result = {name: parent_files[name] for name in names}
    result[code_name] = activation_literal(result[code_name], gate, approved_activation_sha256)
    result.update(extra_payloads)
    result['ACTIVATION.json'] = activation_raw
    result['ACTIVATION_DERIVATION.json'] = encoded({
        'format': 'has_literal_only_activation_source_derivation_1', 'kind': kind,
        'parent_INDEX_sha256': index_sha, 'activation_sha256': approved_activation_sha256,
        'changed_source': code_name, 'before_sha256': code_sha, 'after_sha256': sha(result[code_name]),
        'sole_source_change': gate + ': None to exact reviewed activation SHA256',
        'raw_byte_and_whole_AST_inverse': True, 'all_other_parent_payloads_byte_exact': True,
        'parent_CPU_and_readiness_documents_are_historical': True,
        'semantic_qualification_or_actual_activation_or_copy_or187_executed': False})
    need(len(result) <= 256 and all(len(raw) <= 16 * 1024 * 1024 for raw in result.values())
         and sum(map(len, result.values())) <= 64 * 1024 * 1024, 'Existing validator packet resource ceilings')
    result['INDEX.json'] = encoded({'format': 'has_literal_only_activation_successor_source_packet_1',
        'parent_INDEX_sha256': index_sha, 'activation_sha256': approved_activation_sha256,
        'qualification': 'RENDERED_BYTES_ONLY_ROOT_REVIEW_AND_ORIGINAL_ADMISSION_REQUIRED',
        'payload_files': len(result), 'payload_bytes': sum(map(len, result.values())),
        'files': [{'path': name, 'bytes': len(raw), 'sha256': sha(raw)} for name, raw in sorted(result.items())]})
    return result
