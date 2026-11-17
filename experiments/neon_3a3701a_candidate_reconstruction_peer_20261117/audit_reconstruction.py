"""Independent RAM recovery using sealed parent parser/patch helpers; no activation."""
from pathlib import Path
import datetime
import gzip
import hashlib
import importlib.util
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PACKET = ROOT / 'experiments/neon_3a3701a_candidate_reconstruction_20261117'
INDEX_SHA = '69d8f2eef22aa3ad1c0d2576cf4bba04977a4320fed9ff1dcec9afe81f8bcc28'
CANDIDATE = '3a3701ab6edfa81dc883759403c170b8555aab07'
PARENT = '696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'
MAIN = '4fd0052f52a594e86ca77df0e50e12e8d026a874'
PATHS = {'LLM.md', 'docs/REDESIGN-PORT.md', 'tests/color_sampler_smoke.gd'}
HELPER = ROOT / 'experiments/neon_696_candidate_reconstruction_peer_20261117/audit_reconstruction.py'
HELPER_SHA = '431c7f0ac2a3f60a8e6a85a603f2af13504986f3b5a1999864f231356b8edd90'
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


need(sha(HELPER.read_bytes()) == HELPER_SHA, 'Pinned independent696 helpers')
spec = importlib.util.spec_from_file_location('_sealed696_ram_recovery', HELPER)
H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)  # Never call old main.
git_id, tree_entries, tree_bytes, commit_headers = H.git_id, H.tree_entries, H.tree_bytes, H.commit_headers
reconstruct_working, apply_text_patch = H.reconstruct_working, H.apply_text_patch


def main():
    index_raw, bodies = H.packet(PACKET, INDEX_SHA, 11)
    metadata = json.loads(gzip.decompress(bodies['RECONSTRUCTION.json.gz']))
    need(metadata['candidate'] == CANDIDATE and metadata['parent_reconstruction'] == {
        'commit': PARENT, 'packet': 'experiments/neon_696_candidate_reconstruction_20261117',
        'INDEX_sha256': H.INDEX_SHA, 'main_checkpoint': MAIN}, 'Exact parent recovery binding')
    for key in ('main_application_merge', 'full_suite_pass_claimed', 'focused_result_read_or_claimed_here',
                'private_art_native_media_included'):
        need(metadata[key] is False, 'No result or adoption promotion')
    commit = bodies['COMMIT.txt']; target_tree, parents = commit_headers(commit)
    need(git_id('commit', commit) == CANDIDATE and parents == [PARENT] and target_tree == metadata['tree'],
         'Raw commit reconstructs exact candidate and sole parent')
    need(H.read_object('commit', CANDIDATE) == commit, 'Retained immutable candidate commit')
    trees = H.Trees()
    before696, chain = H.verify_parent(trees)  # Existing public375/fe9/00bf RAM chain.
    parent_index, parent_bodies = H.packet(H.PACKET, H.INDEX_SHA, 9)
    publication_reads = []
    for name, raw in {'INDEX.json': parent_index, **parent_bodies}.items():
        request = MAIN + ':experiments/neon_696_candidate_reconstruction_20261117/' + name
        actual = subprocess.check_output([str(H.B.GIT), '--no-optional-locks', '-c', 'core.fsmonitor=false',
            'cat-file', 'blob', request], cwd=ROOT, timeout=30, creationflags=H.B.ReadOnlyGit.CREATE_NO_WINDOW)
        need(actual == raw, 'Parent packet exactly retained in public main4fd')
        publication_reads.append({'object': request, 'bytes': len(actual)})
    parent = json.loads(gzip.decompress(parent_bodies['RECONSTRUCTION.json.gz']))
    parent_tree, unused = commit_headers(parent_bodies['COMMIT.txt'])
    need(git_id('commit', parent_bodies['COMMIT.txt']) == PARENT and parent_tree == parent['tree'], 'Exact696 commit/tree')
    old_parent = {}; new_parent = {}; parent_replacements = {}
    for row in parent['files']:
        raw = gzip.decompress(parent_bodies[row['payload']]); reconstruct_working(raw, row)
        mode, old_id = trees.at(before696, row['path'].split('/')); need(mode == b'100644', 'Parent text mode')
        old_parent[row['path']] = H.read_object('blob', old_id); new_parent[row['path']] = raw
        parent_replacements[tuple(row['path'].split('/'))] = git_id('blob', raw)
    need(trees.rebuild(before696, parent_replacements) == parent_tree
         and apply_text_patch(parent_bodies['candidate.patch'], old_parent) == new_parent,
         'Published696 parent independently reconstructs in RAM')
    rows = metadata['files']; need(len(rows) == 3 and {row['path'] for row in rows} == PATHS, 'Exact three text files')
    previous = {}; new = {}; replacements = {}; facts = []
    for row in rows:
        raw = gzip.decompress(bodies[row['payload']]); working = reconstruct_working(raw, row)
        need(H.read_object('blob', row['git_blob']) == raw, 'Exact candidate blob')
        mode, old_id = trees.at(parent_tree, row['path'].split('/'))
        need(mode == b'100644' and old_id == row['parent_git_blob'], 'Exact original regular path')
        previous[row['path']] = H.read_object('blob', old_id); new[row['path']] = raw
        need(previous[row['path']] != raw, 'Each selected path really changes')
        replacements[tuple(row['path'].split('/'))] = row['git_blob']
        facts.append({'path': row['path'], 'git_blob': row['git_blob'], 'blob_bytes': len(raw),
            'blob_sha256': sha(raw), 'working_bytes': len(working), 'working_sha256': sha(working),
            'working_recipe_kind': row['working_recipe']['kind'],
            'Git_CRLF_lines': raw.count(b'\r\n'), 'selected_CRLF_lines': len(row['working_recipe'].get('zero_based_lines', []))})
    need(trees.rebuild(parent_tree, replacements) == target_tree, 'Only three replacements rebuild exact candidate tree')
    need(apply_text_patch(bodies['candidate.patch'], previous) == new, 'Byte-exact unified patch in RAM')
    raw_tree_rows = metadata['exact_raw_changed_tree_objects']
    need(len(raw_tree_rows) == 3 and {row['path'] for row in raw_tree_rows} == {'/', 'docs/', 'tests/'}, 'Exact changed raw tree scope')
    for row in raw_tree_rows:
        encoded = bodies[row['payload']]
        raw = bytes.fromhex(encoded.decode('ascii').rstrip('\n'))
        need(encoded == (raw.hex() + '\n').encode() and len(raw) == row['raw_bytes']
             and sha(raw) == row['raw_sha256'] and git_id('tree', raw) == row['git_tree']
             and H.read_object('tree', row['git_tree']) == raw, 'Exact raw archived Git tree')
    test = 'tests/color_sampler_smoke.gd'
    before = b'picker.arm();click(native_point);await settled()'
    after = b'picker.arm();click(native_point+Vector2(.5,.5));await settled()'
    need(previous[test].count(before) == new[test].count(after) == 1 and new[test].replace(after, before, 1) == previous[test],
         'Only one exact pixel-center click expression changes; every assertion/threshold/fixture remains exact')
    test_row = next(row for row in rows if row['path'] == test)
    need(test_row['working_sha256'] == '102ec02e262644a641f6ecc43020940c33834a59b695cfdc0d2d889cc8cae781', 'Root source pin')
    baseline = (ROOT / 'experiments/native_five_full_actual_20261116/run/source-before.json.gz').read_bytes()
    need(sha(baseline) == '0ff288cd27a5aaf6230a4cec798c2555371506e072864e8545492a291d5c2512', 'Public retained52 source map')
    source_map = json.loads(gzip.decompress(baseline))['source_sha256']
    need(len(source_map) == 1019 and all(sha((ROOT / name).read_bytes()) == digest for name, digest in source_map.items()),
         'Root Main1019 functional source unchanged')
    need((PACKET / 'INDEX.json').read_bytes() == index_raw and all((PACKET / name).read_bytes() == raw for name, raw in bodies.items()),
         'Packet unchanged during validation')
    need(sha(HELPER.read_bytes()) == HELPER_SHA and sha(H.B.GIT.read_bytes()) == H.B.GIT_SHA, 'Pinned helpers/tool preserved')
    report = {'format': 'has_3a3701a_independent_RAM_reconstruction_1',
        'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'PASS_LOCAL_TEXT_RECOVERY',
        'candidate': CANDIDATE, 'tree': target_tree, 'sole_parent': PARENT, 'packet_INDEX_sha256': INDEX_SHA,
        'changed_text_files': 3, 'exact_raw_changed_trees': 3, 'commit_tree_patch_blobs_and_EOL_recipes_exact': True,
        'one_pixel_center_click_expression_only_in_test': True, 'app_helper_wind_and_all_other_committed_paths_unchanged': True,
        'main_functional_unchanged': 1019, 'retained_parent_publication': MAIN, 'deep_parent_RAM_chain': chain,
        'text_files': facts, 'typed_ReadOnlyGit_unique_requests': len(H.GIT.reads),
        'typed_ReadOnlyGit_requests': H.GIT.reads, 'main_publication_reads': publication_reads,
        'actual_focused_or_full_native_result_observed': False, 'Git_mutations_network_process_or_current_outputs_accessed': False,
        'product_merge_copy_cold187_or_branch_upload_claimed': False,
        'limits': ['Text recoverability and source scope only; no actual focused/full or native fidelity qualification.',
                   'Published parent bytes checked against retained local main4fd; no fresh network availability claim.',
                   'Exact working recipes were reconstructed from archived blobs; this audit did not reread Review working files.']}
    with (HERE / 'AUDIT.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print(json.dumps({key: report[key] for key in ('status', 'candidate', 'tree', 'changed_text_files', 'main_functional_unchanged',
                                                 'typed_ReadOnlyGit_unique_requests')}))


if __name__ == '__main__':
    main()
