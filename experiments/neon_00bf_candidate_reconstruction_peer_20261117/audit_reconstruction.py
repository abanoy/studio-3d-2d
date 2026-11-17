"""Independent RAM tree/patch/EOL audit. Local Git cat-file reads only."""
from pathlib import Path
import datetime
import gzip
import hashlib
import importlib.util
import json
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PACKET = ROOT / 'experiments/neon_00bf_candidate_reconstruction_20261117'
INDEX_SHA = 'e6837fe45e7a5ce112078e84b8f2bbd52c1271a33f52f6be903819dd4d25cb52'
CANDIDATE = '00bf0f916a549f5e858cb39dd91a149071fd5181'
PARENT = 'fe9aace86f7a349c90a951ff26d76f746d1e4701'
PATHS = {'LLM.md', 'docs/REDESIGN-PORT.md', 'tests/verify_character_height.py', 'tests/verify_shape_catalog.py'}
REFERENCE = ROOT / 'experiments/neon_fe9_candidate_reconstruction_peer_20261117/audit_reconstruction.py'
REFERENCE_SHA = '0dc428d3562609a217af556ce679357e84542c649af7733e36c03cf75b71a6c4'
GIT = Path(r'C:\Program Files\Git\cmd\git.EXE')
GIT_SHA = '544548de8c9bed98eb90531729a2955f554e7009338788b68777258ea61867e4'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


need(sha(REFERENCE.read_bytes()) == REFERENCE_SHA, 'Pinned prior independent RAM audit source')
_spec = importlib.util.spec_from_file_location('_pinned_fe9_RAM_audit', REFERENCE)
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)  # Definitions only; its main is never called.
git_id = R.git_id
tree_entries = R.tree_entries
tree_bytes = R.tree_bytes
commit_headers = R.commit_headers
reconstruct_working = R.reconstruct_working
apply_text_patch = R.apply_text_patch


class ReadOnlyGit:
    CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW

    def check_output(self, args, **options):
        need(type(args) is list and len(args) == 4 and args[:2] == ['git', 'cat-file']
             and args[2] in ('commit', 'tree', 'blob'), 'Only local typed cat-file reads')
        request = args[3]
        need(type(request) is str and re.fullmatch(r'[a-f0-9]{40}(?::[A-Za-z0-9_./-]+)?', request)
             and '..' not in request and '\\' not in request, 'Bounded object identifier')
        need(Path(options.get('cwd')).resolve() == REVIEW.resolve(), 'Only reviewed repository object reads')
        need(sha(GIT.read_bytes()) == GIT_SHA, 'Exact approved read-only Git tool')
        options['timeout'] = 30
        raw = subprocess.check_output([str(GIT), '--no-optional-locks', '-c', 'core.fsmonitor=false', *args[1:]], **options)
        need(len(raw) <= 16 * 1024 * 1024 and sha(GIT.read_bytes()) == GIT_SHA, 'Bounded object/tool unchanged')
        return raw


R.subprocess = ReadOnlyGit()
read_object = R.read_object


def packet(folder, index_sha, count):
    index_raw = (folder / 'INDEX.json').read_bytes()
    need(sha(index_raw) == index_sha, 'Exact packet INDEX')
    rows = json.loads(index_raw)['files']
    need(len(rows) == count and len({r['path'] for r in rows}) == count, 'Exact unique payload scope')
    bodies = {}
    for row in rows:
        name = row['path']
        need(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts, 'Payload path scope')
        raw = (folder / name).read_bytes()
        need(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Exact payload bytes')
        bodies[name] = raw
    need({p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()} == {'INDEX.json'} | set(bodies), 'Exact closed packet membership')
    return index_raw, bodies


def main():
    index_raw, bodies = packet(PACKET, INDEX_SHA, 8)
    metadata = json.loads(gzip.decompress(bodies['RECONSTRUCTION.json.gz']))
    need(metadata['format'] == 'has_text_candidate_reconstruction_1' and metadata['candidate'] == CANDIDATE,
         'Candidate metadata domain')
    need(metadata['parent_reconstruction'] == {'commit': PARENT, 'packet': 'experiments/neon_fe9_candidate_reconstruction_20261117', 'main_publication': 'PENDING_WITH_THIS_INCREMENT'},
         'Explicit unpublished direct-parent reconstruction chain')
    need(metadata['main_application_merge'] is False and metadata['full_suite_pass_claimed'] is False
         and metadata['private_art_native_media_included'] is False
         and metadata['review_branch_push'] == 'NOT_ATTEMPTED_AFTER_PRIOR_BRANCH_REJECTION', 'Publication/qualification limits')
    commit = bodies['COMMIT.txt']
    need(git_id('commit', commit) == CANDIDATE and read_object('commit', CANDIDATE) == commit, 'Exact local commit bytes')
    target_tree, parents = commit_headers(commit)
    need(parents == [PARENT] and target_tree == metadata['tree'], 'Exact sole parent and root tree')
    parent_tree, unused = commit_headers(read_object('commit', PARENT))
    cache = {}

    def entries(oid):
        if oid not in cache:
            cache[oid] = tree_entries(read_object('tree', oid))
        return cache[oid]

    def at(oid, parts):
        found = [(mode, child) for mode, name, child in entries(oid) if name == parts[0].encode()]
        need(len(found) == 1, 'Parent source path exists')
        mode, child = found[0]
        if len(parts) == 1:
            return mode, child
        need(mode == b'40000', 'Parent directory mode')
        return at(child, parts[1:])

    rows = metadata['files']
    need(type(rows) is list and len(rows) == 4 and {r['path'] for r in rows} == PATHS, 'Exact four changed public text files')
    new_blobs, old_blobs, replacements, facts = {}, {}, {}, []
    for row in rows:
        blob = gzip.decompress(bodies[row['payload']])
        working = reconstruct_working(blob, row)
        need(read_object('blob', row['git_blob']) == blob, 'Actual retained candidate blob')
        mode, old_oid = at(parent_tree, row['path'].split('/'))
        need(mode == b'100644', 'Preserved regular text mode')
        old_blobs[row['path']] = read_object('blob', old_oid)
        need(old_blobs[row['path']] != blob, 'Each listed path really changes')
        new_blobs[row['path']] = blob
        replacements[tuple(row['path'].split('/'))] = row['git_blob']
        facts.append({'path': row['path'], 'blob_sha256': sha(blob), 'blob_bytes': len(blob),
                      'git_blob': row['git_blob'], 'working_sha256': sha(working), 'working_bytes': len(working),
                      'selected_CRLF_lines': len(row['working_recipe']['zero_based_lines'])})

    def rebuild(oid, prefix=()):
        result = []
        for mode, name, child in entries(oid):
            key = prefix + (name.decode('utf-8', 'strict'),)
            if key in replacements:
                child = replacements[key]
            elif any(p[:len(key)] == key for p in replacements):
                need(mode == b'40000', 'Rebuilt directory mode')
                child = rebuild(child, key)
            result.append((mode, name, child))
        raw = tree_bytes(result)
        oid = git_id('tree', raw)
        need(read_object('tree', oid) == raw, 'RAM rebuilt tree equals local object')
        return oid

    need(rebuild(parent_tree) == target_tree, 'Parent plus only four replacements produces exact candidate tree')
    need(apply_text_patch(bodies['candidate.patch'], old_blobs) == new_blobs, 'Unified patch independently reproduces all four blobs')
    parent_folder = ROOT / 'experiments/neon_fe9_candidate_reconstruction_20261117'
    unused_index, parent_bodies = packet(parent_folder, R.INDEX_SHA, 7)
    parent_metadata = json.loads(gzip.decompress(parent_bodies['RECONSTRUCTION.json.gz']))
    parent_blobs = {r['path']: gzip.decompress(parent_bodies[r['payload']]) for r in parent_metadata['files']}
    for row in parent_metadata['files']:
        reconstruct_working(parent_blobs[row['path']], row)
    need(parent_metadata['candidate'] == PARENT and parent_metadata['tree'] == parent_tree
         and git_id('commit', parent_bodies['COMMIT.txt']) == PARENT, 'Retained direct-parent packet identity')
    chain = R.verify_parent_chain(parent_metadata, parent_blobs, parent_tree)
    for name, raw in bodies.items():
        need((PACKET / name).read_bytes() == raw, 'Packet source unchanged after audit')
    need((PACKET / 'INDEX.json').read_bytes() == index_raw, 'Packet INDEX unchanged')
    report = {'format': 'has_00bf_public_text_reconstruction_peer_audit_1',
              'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'PASS_LOCAL_TEXT_RECONSTRUCTION', 'packet_index_sha256': INDEX_SHA,
              'candidate_commit': CANDIDATE, 'sole_parent_commit': PARENT, 'candidate_tree': target_tree,
              'payload_files': 8, 'payload_bytes': sum(map(len, bodies.values())), 'changed_public_text_files': 4,
              'four_blobs_and_exact_commit_match_local_Git': True, 'parent_plus_four_replacements_exact_tree': True,
              'unified_patch_in_RAM_exact': True, 'working_EOL_recipes_exact': True,
              'parent_recovery_chain': chain, 'text_files': facts, 'packet_immutable': True,
              'source_reference_sha256': REFERENCE_SHA, 'approved_readonly_Git_sha256': GIT_SHA,
              'Git_operations': 'Local typed cat-file commit/tree/blob reads only; no writes or remote calls',
              'current_working_source_native_CIM_engine_or_active_full_reads': False,
              'wording_correction': 'The immutable metadata scope string says three files; actual diff/blob list contains four. The direct fe9 parent is reconstructed through its packet pending the same checkpoint;375 is recovered through the verified e8-main packet, and4ed is the ultimate remote base. No direct fe9/00bf review branch publication is claimed.',
              'qualification_limits': 'Text recovery only; no complete full-suite PASS, merge, native fidelity or successor behavior claim.'}
    with (HERE / 'AUDIT.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print(json.dumps({k: report[k] for k in ('status', 'candidate_commit', 'candidate_tree', 'changed_public_text_files', 'packet_immutable')}))


if __name__ == '__main__':
    main()
