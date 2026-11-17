"""Independent public-text reconstruction audit. Git cat-file reads only."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PACKET = ROOT / 'experiments/neon_fe9_candidate_reconstruction_20261117'
INDEX_SHA = '156772da327880b276cea24dfa7ec22d6742943e781304f32ae2608253f913b5'
CANDIDATE = 'fe9aace86f7a349c90a951ff26d76f746d1e4701'
PARENT = '375ec05e925159850ff3b0abf2e8f98f9d2ce129'
PATHS = {'LLM.md', 'docs/REDESIGN-PORT.md', 'tests/source_bone_bindings_unit.gd'}


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def git_id(kind, raw):
    return hashlib.sha1(kind.encode() + b' ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def read_object(kind, oid):
    need(kind in ('commit', 'tree', 'blob') and re.fullmatch('[0-9a-f]{40}', oid), 'Object request domain')
    raw = subprocess.check_output(['git', 'cat-file', kind, oid], cwd=REVIEW,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
    need(git_id(kind, raw) == oid, 'Git object identity')
    return raw


def tree_entries(raw):
    entries = []; offset = 0; names = set()
    while offset < len(raw):
        space = raw.index(b' ', offset); zero = raw.index(b'\0', space)
        mode, name = raw[offset:space], raw[space + 1:zero]
        need(name and b'/' not in name and name not in names, 'Tree name domain')
        oid = raw[zero + 1:zero + 21]; need(len(oid) == 20, 'Tree object width')
        entries.append((mode, name, oid.hex())); names.add(name); offset = zero + 21
    need(offset == len(raw), 'Tree trailing bytes')
    return entries


def tree_bytes(entries):
    return b''.join(mode + b' ' + name + b'\0' + bytes.fromhex(oid) for mode, name, oid in entries)


def commit_headers(raw):
    need(b'\0' not in raw and b'\n\n' in raw, 'Commit text shape')
    header, message = raw.split(b'\n\n', 1); header.decode('utf-8', 'strict'); message.decode('utf-8', 'strict')
    lines = header.split(b'\n')
    trees = [line[5:].decode('ascii') for line in lines if line.startswith(b'tree ')]
    parents = [line[7:].decode('ascii') for line in lines if line.startswith(b'parent ')]
    need(len(trees) == 1, 'One root tree required')
    need(all(re.fullmatch('[0-9a-f]{40}', value) for value in trees + parents), 'Commit ID domain')
    return trees[0], parents


def reconstruct_working(blob, row):
    need(type(row) is dict and row['blob_bytes'] == len(blob) and type(row['blob_bytes']) is int,
         'Blob byte identity')
    need(sha(blob) == row['blob_sha256'] and git_id('blob', blob) == row['git_blob'], 'Blob digests')
    need(b'\r' not in blob and b'\0' not in blob, 'LF public text blob')
    blob.decode('utf-8', 'strict')
    recipe = row['working_recipe']; selected = recipe['zero_based_lines']
    need(recipe['kind'] == 'LF_blob_with_selected_CRLF_lines' and type(selected) is list, 'Recipe profile')
    lines = blob.splitlines(keepends=True)
    need(all(type(i) is int and 0 <= i < len(lines) and lines[i].endswith(b'\n') for i in selected), 'CRLF line domain')
    need(selected == sorted(set(selected)), 'CRLF line uniqueness/order')
    selected_set = set(selected)
    result = b''.join(line[:-1] + b'\r\n' if i in selected_set else line for i, line in enumerate(lines))
    need(type(row['working_bytes']) is int and len(result) == row['working_bytes'] and sha(result) == row['working_sha256'], 'Working reconstruction identity')
    need(result.replace(b'\r\n', b'\n') == blob, 'Working normalization inverse')
    return result


def apply_text_patch(raw, original_by_path):
    """Small strict parser for this no-rename, LF, final-newline unified patch."""
    need(b'\0' not in raw and b'GIT binary patch' not in raw and b'\r' not in raw, 'Text patch profile')
    lines = raw.splitlines(keepends=True); position = 0; outputs = {}
    while position < len(lines):
        head = lines[position].decode('utf-8').rstrip('\n')
        match = re.fullmatch(r'diff --git a/(.+) b/(.+)', head)
        need(match is not None and match[1] == match[2] and match[1] in original_by_path, 'Patch path header')
        name = match[1]; need(name not in outputs, 'Duplicate patch path')
        position += 1
        need(re.fullmatch(rb'index [0-9a-f]+\.\.[0-9a-f]+ 100644\n', lines[position]) is not None, 'Patch mode/index')
        position += 1
        need(lines[position] == ('--- a/' + name + '\n').encode() and lines[position + 1] == ('+++ b/' + name + '\n').encode(), 'Patch file aliases')
        position += 2; source = original_by_path[name].splitlines(keepends=True); cursor = 0; output = []
        while position < len(lines) and not lines[position].startswith(b'diff --git '):
            hunk = re.fullmatch(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n', lines[position])
            need(hunk is not None, 'Hunk shape'); position += 1
            old_start = int(hunk[1]); old_count = int(hunk[2] or b'1')
            new_start = int(hunk[3]); new_count = int(hunk[4] or b'1')
            start = old_start - 1 if old_count else old_start
            need(cursor <= start <= len(source), 'Hunk old start'); output.extend(source[cursor:start]); cursor = start
            need(len(output) == (new_start - 1 if new_count else new_start), 'Hunk new start')
            consumed = produced = 0
            while position < len(lines) and not lines[position].startswith((b'@@ ', b'diff --git ')):
                line = lines[position]; position += 1
                need(line[:1] in (b' ', b'-', b'+') and line.endswith(b'\n'), 'Patch line profile')
                if line[:1] in (b' ', b'-'):
                    need(cursor < len(source) and source[cursor] == line[1:], 'Patch original context')
                    cursor += 1; consumed += 1
                if line[:1] in (b' ', b'+'): output.append(line[1:]); produced += 1
            need((consumed, produced) == (old_count, new_count), 'Hunk counts')
        output.extend(source[cursor:]); outputs[name] = b''.join(output)
    need(set(outputs) == set(original_by_path), 'Complete patch file set')
    return outputs


def verify_parent_chain(metadata, fe9_blobs, expected_fe9_tree):
    """Recover4ed→375→fe9 trees in RAM; no Git objects are written."""
    need(metadata['main_application_merge'] is False and metadata['full_suite_pass_claimed'] is False
         and metadata['private_art_native_media_included'] is False
         and metadata['review_branch_push'] == 'NOT_ATTEMPTED_AFTER_PRIOR_BRANCH_REJECTION', 'Bounded publication status')
    folder_relative = 'experiments/neon_375_candidate_reconstruction_20261117'
    folder = ROOT / folder_relative
    parent_index_raw = (folder / 'INDEX.json').read_bytes()
    need(sha(parent_index_raw) == 'ef5b48263fbeec32fc7c5197fdd59508a3a2b258397470de9930b17cf0cb332f', 'Exact published375 packet INDEX')
    parent_index = json.loads(parent_index_raw); bodies = {'INDEX.json': parent_index_raw}
    need(len(parent_index['files']) == 7, 'Exact375 payload count')
    for row in parent_index['files']:
        raw = (folder / row['path']).read_bytes(); need(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Published375 packet payload')
        bodies[row['path']] = raw
    readback_raw = (ROOT / 'experiments/neon_375_checkpoint_remote_20261117/COMPLETE_READBACK.json').read_bytes()
    need(sha(readback_raw) == 'efb5fb94aee5e143deb0cb4dff17141ba1d35c29079694fdc830f92ac5a6157c', 'Retained exacte8 readback proof')
    readback = json.loads(readback_raw)
    need(readback['commit'] == 'e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a' and readback['file_count'] == len(readback['files']) == 534, 'Published main checkpoint proof')
    by_path = {row['path']: row for row in readback['files']}
    for name, raw in bodies.items():
        relative = folder_relative + '/' + name; proof = by_path[relative]
        need(proof['independent_remote_bytes_exact'] is True and proof['bytes'] == len(raw) and proof['sha256'] == sha(raw)
             and proof['git_blob'] == git_id('blob', raw), '375 packet published byte proof')
        committed = subprocess.check_output(['git', 'cat-file', 'blob', readback['commit'] + ':' + relative], cwd=REVIEW,
                                           creationflags=subprocess.CREATE_NO_WINDOW)
        need(committed == raw, 'Exact375 packet bytes in e8 Git tree')
    parent_metadata = json.loads(gzip.decompress(bodies['RECONSTRUCTION.json.gz']))
    ultimate = '4ed3a63b716f696daa1699a76443d6f1abb9b096'
    need(parent_metadata['candidate'] == PARENT and parent_metadata['parent_available_remote'] == ultimate, '375→4ed base identity')
    parent_commit = bodies['COMMIT.txt']; need(git_id('commit', parent_commit) == PARENT, 'Recovered375 commit SHA')
    parent_root, parent_parents = commit_headers(parent_commit)
    need(parent_parents == [ultimate] and parent_root == parent_metadata['tree'], 'Recovered375 sole parent/tree')
    base_root, unused = commit_headers(read_object('commit', ultimate))
    reconstructed_trees = {}; loaded_base_trees = set()
    def source_entries(oid):
        if oid not in reconstructed_trees:
            reconstructed_trees[oid] = read_object('tree', oid); loaded_base_trees.add(oid)
        return tree_entries(reconstructed_trees[oid])
    def rebuild(oid, replacements, prefix=()):
        entries = []
        for mode, name, child in source_entries(oid):
            key = prefix + (name.decode('utf-8', 'strict'),)
            if key in replacements:
                need(mode == b'100644', 'Recovered regular text mode'); child = replacements[key]
            elif any(path[:len(key)] == key for path in replacements):
                need(mode == b'40000', 'Recovered directory mode'); child = rebuild(child, replacements, key)
            entries.append((mode, name, child))
        raw = tree_bytes(entries); result = git_id('tree', raw); reconstructed_trees[result] = raw
        return result
    parent_replacements = {}
    for row in parent_metadata['files']:
        raw = gzip.decompress(bodies[row['payload']]); reconstruct_working(raw, row)
        parent_replacements[tuple(row['path'].split('/'))] = git_id('blob', raw)
    need(len(parent_replacements) == 3 and rebuild(base_root, parent_replacements) == parent_root, '375 recoverable from4ed and public packet only')
    fe9_replacements = {tuple(name.split('/')): git_id('blob', raw) for name, raw in fe9_blobs.items()}
    need(rebuild(parent_root, fe9_replacements) == expected_fe9_tree, 'Fe9 recoverable from reconstructed375 tree')
    return {'main_checkpoint': readback['commit'], 'retained_main_readback_sha256': sha(readback_raw),
            'published375_packet_files_verified': len(bodies), '375_packet_INDEX_sha256': sha(parent_index_raw),
            'ultimate_base_commit': ultimate, '375_rebuilt_root_tree': parent_root, 'fe9_rebuilt_root_tree': expected_fe9_tree,
            'both_recovery_steps_in_RAM': True, 'Git_objects_written': False,
            'wording_limit': 'Fe9 scope string says known remote parent; its direct375 parent is instead recovered through the explicit e8-published packet. README and parent_reconstruction correctly describe that chain.'}


def main():
    index_raw = (PACKET / 'INDEX.json').read_bytes(); need(sha(index_raw) == INDEX_SHA, 'Exact packet INDEX')
    index = json.loads(index_raw); payloads = index['files']
    need(len(payloads) == 7 and len({row['path'] for row in payloads}) == 7, 'Seven unique payloads')
    before = {}
    for row in payloads:
        relative = Path(row['path']); need(not relative.is_absolute() and '..' not in relative.parts, 'Payload path boundary')
        raw = (PACKET / relative).read_bytes()
        need(type(row['bytes']) is int and len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Payload bytes/digest')
        before[row['path']] = raw
    need({p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*') if p.is_file()} == {'INDEX.json'} | set(before), 'Closed packet set')
    metadata_raw = gzip.decompress(before['RECONSTRUCTION.json.gz']); metadata = json.loads(metadata_raw)
    need(metadata['format'] == 'has_text_candidate_reconstruction_1' and metadata['candidate'] == CANDIDATE and metadata['parent_reconstruction'] == {'commit': PARENT, 'main_checkpoint': 'e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a', 'packet': 'experiments/neon_375_candidate_reconstruction_20261117'}, 'Metadata candidate/parent')
    commit = before['COMMIT.txt']; need(git_id('commit', commit) == CANDIDATE, 'Exact commit bytes')
    tree, parents = commit_headers(commit); need(parents == [PARENT] and tree == metadata['tree'], 'Exact sole parent/root tree')
    need(read_object('commit', CANDIDATE) == commit, 'Actual local candidate commit object')
    parent_tree, unused_parent_parents = commit_headers(read_object('commit', PARENT))
    parent_cache = {}
    def entries(oid):
        if oid not in parent_cache: parent_cache[oid] = tree_entries(read_object('tree', oid))
        return parent_cache[oid]
    def at(oid, parts):
        matches = [(mode, child) for mode, name, child in entries(oid) if name == parts[0].encode()]
        need(len(matches) == 1, 'Parent tree path exists'); mode, child = matches[0]
        if len(parts) == 1: return mode, child
        need(mode == b'40000', 'Parent path directory mode'); return at(child, parts[1:])
    rows = metadata['files']; need(type(rows) is list and len(rows) == 3 and {r['path'] for r in rows} == PATHS, 'Three exact text paths')
    replacement = {}; old_blobs = {}; new_blobs = {}; facts = []
    for row in rows:
        blob = gzip.decompress(before[row['payload']]); working = reconstruct_working(blob, row)
        need(read_object('blob', row['git_blob']) == blob, 'Actual local text blob')
        mode, old_oid = at(parent_tree, row['path'].split('/')); need(mode == b'100644', 'Unchanged regular text mode')
        old_blobs[row['path']] = read_object('blob', old_oid); new_blobs[row['path']] = blob
        need(old_blobs[row['path']] != blob, 'Each listed path changes')
        replacement[tuple(row['path'].split('/'))] = row['git_blob']
        current = (REVIEW / row['path']).read_bytes()
        facts.append({'path': row['path'], 'git_blob': row['git_blob'], 'blob_bytes': len(blob), 'blob_sha256': sha(blob),
                      'working_bytes': len(working), 'working_sha256': sha(working),
                      'selected_CRLF_lines': len(row['working_recipe']['zero_based_lines']),
                      'current_readonly_working_bytes_match_retained_recipe': current == working})
    changed_tree_count = 0
    def replace_tree(oid, prefix=()):
        nonlocal changed_tree_count
        rows = []
        for mode, name, child in entries(oid):
            text = name.decode('utf-8', 'strict'); path = prefix + (text,)
            if path in replacement: child = replacement[path]
            elif any(key[:len(path)] == path for key in replacement):
                need(mode == b'40000', 'Reconstruction directory mode')
                child = replace_tree(child, path)
            rows.append((mode, name, child))
        raw = tree_bytes(rows); result = git_id('tree', raw)
        if result != oid: changed_tree_count += 1
        # Local target tree must carry exactly these independently built bytes.
        need(read_object('tree', result) == raw, 'Rebuilt tree bytes match actual local tree')
        return result
    need(replace_tree(parent_tree) == tree, 'Exact candidate root from parent plus only three replacements')
    need(apply_text_patch(before['candidate.patch'], old_blobs) == new_blobs, 'Patch reproduces all candidate text blobs')
    old_expression = b'GOLDEN_GLB.replace("\\n", "")'
    new_expression = b'GOLDEN_GLB.replace("\\r", "").replace("\\n", "")'
    fixture_old = old_blobs['tests/source_bone_bindings_unit.gd']; fixture_new = new_blobs['tests/source_bone_bindings_unit.gd']
    need(fixture_old.count(old_expression) == fixture_new.count(new_expression) == 1
         and fixture_new.replace(new_expression, old_expression) == fixture_old, 'Only one authored fixture expression changed')
    chain_facts = verify_parent_chain(metadata, new_blobs, tree)
    for row in payloads: need((PACKET / row['path']).read_bytes() == before[row['path']], 'Packet unchanged after audit')
    need((PACKET / 'INDEX.json').read_bytes() == index_raw, 'INDEX unchanged after audit')
    report = {'format': 'has_fe9_public_text_reconstruction_peer_audit_1',
              'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'PASS_LOCAL_TEXT_RECONSTRUCTION',
              'packet_index_sha256': INDEX_SHA, 'payload_files': len(payloads), 'payload_bytes': sum(len(r) for r in before.values()),
              'builder_sha256': sha((ROOT / 'experiments/backup_neon_fe9_candidate_20261117.py').read_bytes()),
              'candidate_commit': CANDIDATE, 'sole_parent_commit': PARENT, 'candidate_tree': tree, 'parent_tree': parent_tree,
              'three_blobs_match_local_Git_objects': True, 'independent_parent_plus_three_blob_tree_reconstruction': True,
              'changed_tree_objects': changed_tree_count, 'patch_applied_in_RAM_exactly': True, 'working_EOL_recipes_reconstruct_exactly': True,
              'fixture_changes_only_one_expression': True, 'parent_recovery_chain': chain_facts, 'text_files': facts,
              'packet_immutable': True, 'Git_operations': 'Local cat-file commit/tree/blob reads only',
              'remote_access_or_push_or_Git_mutation': False, 'checkout_or_native_process_or_CIM_mutation': False,
              'media_private_native_array_or_original_asset_payloads_included': False,
              'limits': ['The direct375 parent is recovered through its e8-published packet;4ed is the ultimate base. No current remote availability observation.',
                         'This is a delta reconstruction from the specified parent, not a standalone full repository backup.',
                         'Working EOL recipes are separate from Git blob bytes; reproducing a working-byte hash requires applying the recipe after reconstructing the Git tree.',
                         'Publication authorization and automatic approval rejection are not overridden or tested by this audit.',
                         'No native/full test, feature correctness, merge or redesign adoption qualification follows from text reconstruction.']}
    (HERE / 'AUDIT.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('status', 'payload_files', 'payload_bytes', 'candidate_commit', 'candidate_tree', 'packet_immutable')}))


if __name__ == '__main__': main()
