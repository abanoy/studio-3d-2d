"""Independent five-blob RAM reconstruction; bounded typed Git cat-file only."""
from pathlib import Path
import datetime
import gzip
import hashlib
import importlib.util
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PACKET = ROOT / 'experiments/neon_696_candidate_reconstruction_20261117'
INDEX_SHA = '94a74d55d78f411d3da89a31e838bdbce863b4a682697be988de9d8556bf314d'
CANDIDATE = '696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'
PARENT = '00bf0f916a549f5e858cb39dd91a149071fd5181'
MAIN_PUBLICATION = 'a41a204bffb98614abfa80e0e6340078b1d719f1'
PATHS = {'LLM.md', 'docs/REDESIGN-PORT.md', 'src/app.gd',
         'tests/helper_preview_port_files.json', 'tests/wind_review_port_files.json'}
BASE_SOURCE = ROOT / 'experiments/neon_00bf_candidate_reconstruction_peer_20261117/audit_reconstruction.py'
BASE_SHA = 'c0e0c2bd9648bcfffb970e32c99caae9d2658f170c8211b14c680e908104850a'


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()


need(sha(BASE_SOURCE.read_bytes()) == BASE_SHA, 'Exact sealed parent peer source')
spec = importlib.util.spec_from_file_location('_sealed_00bf_peer_helpers', BASE_SOURCE)
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)  # No main call.
R = B.R
git_id, tree_entries, tree_bytes, commit_headers = R.git_id, R.tree_entries, R.tree_bytes, R.commit_headers


class LoggedGit(B.ReadOnlyGit):
    def __init__(self): self.reads = []; self.cache = {}
    def check_output(self, args, **options):
        key = tuple(args)
        if key not in self.cache:
            self.cache[key] = super().check_output(args, **options)
            self.reads.append({'kind': args[2], 'object': args[3], 'bytes': len(self.cache[key])})
        return self.cache[key]


GIT = LoggedGit(); R.subprocess = GIT
read_object = R.read_object
packet = B.packet


def reconstruct_working(blob, row):
    """Keep exact CRLF Git blobs exact; retain the original strict LF recipe."""
    need(type(row) is dict and type(row['blob_bytes']) is int and row['blob_bytes'] == len(blob), 'Blob byte identity')
    need(sha(blob) == row['blob_sha256'] and git_id('blob', blob) == row['git_blob'], 'Blob digests')
    need(b'\0' not in blob and b'\r' not in blob.replace(b'\r\n', b''), 'Public text without NUL or lone CR')
    blob.decode('utf-8', 'strict')
    recipe = row['working_recipe']; need(type(recipe) is dict, 'Literal working recipe')
    if recipe.get('kind') == 'exact':
        need(set(recipe) == {'kind'}, 'Exact recipe has no conversion fields')
        working = blob
        need(type(row['working_bytes']) is int and len(working) == row['working_bytes']
             and sha(working) == row['working_sha256'], 'Exact raw working identity')
        return working
    need(set(recipe) == {'kind', 'zero_based_lines'} and recipe['kind'] == 'LF_blob_with_selected_CRLF_lines', 'Explicit LF recipe required')
    return R.reconstruct_working(blob, row)


def apply_text_patch(raw, original_by_path):
    """Strict LF structural headers with byte-exact LF/CRLF hunk payloads."""
    need(b'\0' not in raw and b'GIT binary patch' not in raw, 'Public unified text patch only')
    lines = raw.splitlines(keepends=True); position = 0; outputs = {}
    def line():
        need(position < len(lines), 'Truncated patch'); return lines[position]
    while position < len(lines):
        head = line(); need(b'\r' not in head and head.endswith(b'\n'), 'LF patch header required')
        match = re.fullmatch(rb'diff --git a/(.+) b/(.+)\n', head)
        need(match is not None and match[1] == match[2], 'Exact unrenamed patch path')
        name = match[1].decode('utf-8', 'strict')
        need(name in original_by_path and name not in outputs, 'Exact unique patch membership'); position += 1
        index = re.fullmatch(rb'index ([0-9a-f]{7,40})\.\.([0-9a-f]{7,40}) 100644\n', line())
        need(index is not None, 'Regular-file LF patch index'); position += 1
        need(line() == ('--- a/' + name + '\n').encode(), 'Old path alias'); position += 1
        need(line() == ('+++ b/' + name + '\n').encode(), 'New path alias'); position += 1
        source_raw = original_by_path[name]; source = source_raw.splitlines(keepends=True); cursor = 0; output = []
        while position < len(lines) and not line().startswith(b'diff --git '):
            hunk = re.fullmatch(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\r\n]*\n', line())
            need(hunk is not None, 'LF hunk shape'); position += 1
            old_start, old_count = int(hunk[1]), int(hunk[2] or b'1')
            new_start, new_count = int(hunk[3]), int(hunk[4] or b'1')
            start = old_start - 1 if old_count else old_start
            need(cursor <= start <= len(source), 'Hunk old start'); output.extend(source[cursor:start]); cursor = start
            need(len(output) == (new_start - 1 if new_count else new_start), 'Hunk new start')
            consumed = produced = 0
            while position < len(lines) and not line().startswith((b'@@ ', b'diff --git ')):
                payload = line(); position += 1
                need(payload[:1] in (b' ', b'-', b'+') and payload.endswith(b'\n')
                     and b'\r' not in payload.replace(b'\r\n', b''), 'Exact LF/CRLF payload line')
                if payload[:1] in (b' ', b'-'):
                    need(cursor < len(source) and source[cursor] == payload[1:], 'Original patch context including EOL')
                    cursor += 1; consumed += 1
                if payload[:1] in (b' ', b'+'): output.append(payload[1:]); produced += 1
            need((consumed, produced) == (old_count, new_count), 'Exact hunk counts')
        output.extend(source[cursor:]); result = b''.join(output)
        need(git_id('blob', source_raw).startswith(index[1].decode())
             and git_id('blob', result).startswith(index[2].decode()), 'Patch index binds actual old/new blobs')
        outputs[name] = result
    need(set(outputs) == set(original_by_path), 'Complete patch file set')
    return outputs


class Trees:
    def __init__(self): self.cache = {}; self.changed = set()
    def entries(self, oid):
        if oid not in self.cache: self.cache[oid] = tree_entries(read_object('tree', oid))
        return self.cache[oid]
    def at(self, oid, parts):
        found = [(mode, child) for mode, name, child in self.entries(oid) if name == parts[0].encode()]
        need(len(found) == 1, 'Exact parent path'); mode, child = found[0]
        if len(parts) == 1: return mode, child
        need(mode == b'40000', 'Parent directory mode'); return self.at(child, parts[1:])
    def rebuild(self, oid, replacements, prefix=()):
        result = []
        for mode, name, child in self.entries(oid):
            key = prefix + (name.decode('utf-8', 'strict'),)
            if key in replacements:
                need(mode == b'100644', 'Regular changed text mode'); child = replacements[key]
            elif any(path[:len(key)] == key for path in replacements):
                need(mode == b'40000', 'Rebuilt directory mode'); child = self.rebuild(child, replacements, key)
            result.append((mode, name, child))
        raw = tree_bytes(result); rebuilt = git_id('tree', raw)
        need(read_object('tree', rebuilt) == raw, 'RAM tree equals actual retained object')
        if rebuilt != oid: self.changed.add(rebuilt)
        return rebuilt


def published_packet(relative, index_sha, count):
    folder = ROOT / relative; index, bodies = packet(folder, index_sha, count)
    for name, raw in {'INDEX.json': index, **bodies}.items():
        actual = GIT.check_output(['git', 'cat-file', 'blob', MAIN_PUBLICATION + ':' + relative + '/' + name],
                                 cwd=B.REVIEW, creationflags=GIT.CREATE_NO_WINDOW)
        need(actual == raw, 'Parent packet exact in retained published main tree')
    return index, bodies


def verify_parent(trees):
    read_object('commit', MAIN_PUBLICATION)
    index, bodies = published_packet('experiments/neon_00bf_candidate_reconstruction_20261117', B.INDEX_SHA, 8)
    metadata = json.loads(gzip.decompress(bodies['RECONSTRUCTION.json.gz']))
    need(metadata['candidate'] == PARENT and git_id('commit', bodies['COMMIT.txt']) == PARENT, 'Direct parent packet commit')
    parent_tree, parents = commit_headers(bodies['COMMIT.txt']); need(parents == [B.PARENT] and parent_tree == metadata['tree'], 'Direct parent sole parent/tree')
    need(read_object('commit', PARENT) == bodies['COMMIT.txt'], 'Direct parent retained commit bytes')
    unused, fe9_bodies = published_packet('experiments/neon_fe9_candidate_reconstruction_20261117', R.INDEX_SHA, 7)
    fe9 = json.loads(gzip.decompress(fe9_bodies['RECONSTRUCTION.json.gz']))
    fe9_tree, unused = commit_headers(fe9_bodies['COMMIT.txt'])
    need(fe9['candidate'] == B.PARENT and fe9['tree'] == fe9_tree and git_id('commit', fe9_bodies['COMMIT.txt']) == B.PARENT, 'Published fe9 commit/tree')
    fe9_blobs = {row['path']: gzip.decompress(fe9_bodies[row['payload']]) for row in fe9['files']}
    for row in fe9['files']: reconstruct_working(fe9_blobs[row['path']], row)
    deep = R.verify_parent_chain(fe9, fe9_blobs, fe9_tree)
    parent_blobs = {}; previous = {}; replacements = {}
    for row in metadata['files']:
        blob = gzip.decompress(bodies[row['payload']]); reconstruct_working(blob, row)
        mode, oid = trees.at(fe9_tree, row['path'].split('/')); need(mode == b'100644', 'Parent packet path mode')
        previous[row['path']] = read_object('blob', oid); parent_blobs[row['path']] = blob
        replacements[tuple(row['path'].split('/'))] = git_id('blob', blob)
    need(len(replacements) == 4 and trees.rebuild(fe9_tree, replacements) == parent_tree, 'RAM fe9 plus four blobs reconstructs00bf')
    need(apply_text_patch(bodies['candidate.patch'], previous) == parent_blobs, 'Parent00bf patch exact in RAM')
    return parent_tree, {'retained_main_commit': MAIN_PUBLICATION, 'published00bf_packet_entries': 9,
                         'published_fe9_packet_entries': 8, '00bf_RAM_reconstruction': True, 'deep_chain': deep}


def main():
    index_raw, bodies = packet(PACKET, INDEX_SHA, 9)
    metadata = json.loads(gzip.decompress(bodies['RECONSTRUCTION.json.gz']))
    need(metadata['format'] == 'has_text_candidate_reconstruction_1' and metadata['candidate'] == CANDIDATE
         and metadata['parent_reconstruction'] == {'commit': PARENT, 'packet': 'experiments/neon_00bf_candidate_reconstruction_20261117', 'main_checkpoint': MAIN_PUBLICATION}, 'Exact696 parent/publication metadata')
    need(metadata['main_application_merge'] is False and metadata['full_suite_pass_claimed'] is False
         and metadata['private_art_native_media_included'] is False
         and metadata['review_branch_push'] == 'NOT_ATTEMPTED_AFTER_PRIOR_BRANCH_REJECTION', 'No result/merge/publication promotion')
    commit = bodies['COMMIT.txt']; need(git_id('commit', commit) == CANDIDATE and read_object('commit', CANDIDATE) == commit, 'Exact candidate commit')
    target_tree, parents = commit_headers(commit); need(parents == [PARENT] and target_tree == metadata['tree'], 'Exact candidate sole parent/tree')
    trees = Trees(); parent_tree, chain = verify_parent(trees)
    rows = metadata['files']; need(type(rows) is list and len(rows) == 5 and {row['path'] for row in rows} == PATHS, 'Exact five public text paths')
    old = {}; new = {}; replacements = {}; facts = []
    for row in rows:
        blob = gzip.decompress(bodies[row['payload']]); working = reconstruct_working(blob, row)
        need(read_object('blob', row['git_blob']) == blob, 'Exact candidate Git blob')
        mode, previous = trees.at(parent_tree, row['path'].split('/')); need(mode == b'100644', 'Original regular text mode')
        old[row['path']] = read_object('blob', previous); need(old[row['path']] != blob, 'Each listed file really changes')
        new[row['path']] = blob; replacements[tuple(row['path'].split('/'))] = row['git_blob']
        expected_recipe = 'exact' if row['path'] == 'src/app.gd' else 'LF_blob_with_selected_CRLF_lines'
        need(row['working_recipe']['kind'] == expected_recipe, 'Per-file Git/working EOL profile')
        if row['path'] == 'src/app.gd':
            need(blob == working and blob.count(b'\r\n') == blob.count(b'\n') > 0, 'Raw CRLF app Git blob preserved exactly')
        facts.append({'path': row['path'], 'git_blob': row['git_blob'], 'blob_bytes': len(blob), 'blob_sha256': sha(blob),
                      'working_bytes': len(working), 'working_sha256': sha(working), 'working_recipe_kind': expected_recipe,
                      'Git_blob_CRLF_lines': blob.count(b'\r\n'), 'Git_blob_LF_bytes': blob.count(b'\n'),
                      'selected_CRLF_lines': len(row['working_recipe'].get('zero_based_lines', []))})
    need(trees.rebuild(parent_tree, replacements) == target_tree, 'Parent plus only five replacements gives exact696 tree')
    need(apply_text_patch(bodies['candidate.patch'], old) == new, 'Byte-exact LF/CRLF unified patch in RAM')
    before = b'\tif scene_view:scene_view.sync()\r\n\trefresh_view_row()\r\n'
    after = b'\tif scene_view:scene_view.sync()\r\n\trefresh_camera_inspector()\r\n\trefresh_view_row()\r\n'
    need(old['src/app.gd'].count(before) == new['src/app.gd'].count(after) == 1
         and new['src/app.gd'].replace(after, before, 1) == old['src/app.gd'], 'Exactly one existing inspector refresh inserted')
    for name in ('tests/helper_preview_port_files.json', 'tests/wind_review_port_files.json'):
        previous = json.loads(old[name]); actual = json.loads(new[name]); changed = json.loads(old[name])
        app_rows = [row for row in changed['files'] if row['path'] == 'src/app.gd']; need(len(app_rows) == 1, 'One existing app manifest row')
        app_rows[0]['sha256'] = sha(new['src/app.gd']); app_rows[0]['lf_sha256'] = sha(new['src/app.gd'].replace(b'\r\n', b'\n'))
        need(changed == actual and previous != actual, 'Only exact app raw/LF pins changed in each unchanged manifest')
    for name, raw in bodies.items(): need((PACKET / name).read_bytes() == raw, 'Packet payload changed during audit')
    need((PACKET / 'INDEX.json').read_bytes() == index_raw and sha(BASE_SOURCE.read_bytes()) == BASE_SHA
         and sha(B.GIT.read_bytes()) == B.GIT_SHA, 'Packet/helper/Git tool unchanged')
    report = {'format': 'has_696_independent_public_RAM_reconstruction_audit_1',
              'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'PASS_LOCAL_TEXT_RECONSTRUCTION',
              'packet_INDEX_sha256': INDEX_SHA, 'candidate_commit': CANDIDATE, 'sole_parent_commit': PARENT,
              'candidate_tree': target_tree, 'payload_files': 9, 'payload_bytes': sum(map(len, bodies.values())),
              'changed_public_text_files': 5, 'five_blobs_commit_and_rebuilt_tree_exact_local_objects': True,
              'RAM_unified_patch_preserves_CRLF_payload_and_binds_old_new_blob_headers': True,
              'app_Git_blob_CRLF_and_working_recipe_exact_preserved': True, 'four_other_LF_selected_CRLF_recipes_exact': True,
              'app_only_one_refresh_call_and_manifests_only_two_app_pin_fields_each': True,
              'retained_parent_publication_and_recovery_chain': chain, 'text_files': facts,
              'readonly_Git_unique_requests': len(GIT.reads), 'readonly_Git_requests': GIT.reads,
              'Git_operations': 'Bounded local typed cat-file commit/tree/blob reads only, no optional locks or fsmonitor',
              'Git_mutation_network_current_working_source_active_full_native_or_CIM_reads': False,
              'packet_immutable': True, 'source_reference_sha256': BASE_SHA,
              'limits': ['Text recoverability only; no focused/current full/native behavior or fidelity test was run.',
                         'Current696 full is root-reported RUNNING1029, not independently observed here; no full PASS/merge/adoption is claimed.',
                         'a41 parent publication was checked against retained local commit bytes, not a new remote availability observation.',
                         'An exact CRLF Git blob is not normalized to LF; working identity is separate from any LF comparison hash.']}
    with (HERE / 'AUDIT.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print(json.dumps({key: report[key] for key in ('status', 'candidate_commit', 'candidate_tree', 'changed_public_text_files', 'readonly_Git_unique_requests', 'packet_immutable')}))


if __name__ == '__main__': main()
