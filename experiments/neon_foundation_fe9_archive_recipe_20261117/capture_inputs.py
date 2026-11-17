"""Freeze closed focused-foundation text only; no native/golden/media bodies."""
from pathlib import Path
import hashlib
import json
from archive_checks import ROOT_RUN, check, load, require

HERE = Path(__file__).resolve().parent
MAIN = HERE.parents[1]
REVIEW = MAIN.parent / 'has-neon-review-20261116-c2d52ff'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def safe_file(path, root):
    require(path.is_absolute() and path.resolve().is_relative_to(root), 'Owned input boundary')
    for item in (path, *path.parents):
        if item == root.parent: break
        require(not item.is_symlink() and not getattr(item.lstat(), 'st_file_attributes', 0) & 0x400, 'Input reparse refused')
    require(path.is_file(), 'Regular input required')


def main():
    require(not (HERE / 'INPUTS.json').exists(), 'Never replace frozen inputs')
    folder = REVIEW / ROOT_RUN
    result = load((folder / 'verification.json').read_bytes()); report = result['rows'][0]['report']
    child = Path(report['folder']); require(child == folder / 'source-choices', 'Exact derived completed child')
    # Root's completed driver emits only these scalar/source/log files. No glob
    # reaches an upcoming full or copies generated fixture data.
    names = ['verification.json', 'source-before.json', 'source-after.json', 'foundation-command.json', 'foundation-start.json',
             'foundation-process.json', 'foundation-report.json', 'foundation-stdout.log', 'foundation-stderr.log']
    for label in ('before', 'foundation-after', 'after'):
        names += [label + '-closure.json', label + '-scope-stdout.log', label + '-scope-stderr.log']
    selected = {('REVIEW', (folder / name).relative_to(REVIEW).as_posix()) for name in names}
    child_names = ['verification.json', 'catalogue.log', 'appearance.log', 'resource-write.log', 'bridge-bootstrap.log', 'jiggle-cpu.log',
                   'crosswalk-cpu.log', 'bindings-headless.log', 'unit.log', 'ui.log', 'unit/engine.log', 'unit/result.json',
                   'ui/command.json', 'ui/engine.log', 'ui/stdout.log', 'ui/result.json', 'ui/source-before.json', 'ui/verification.json',
                   'jiggle-cpu/verification.json', 'crosswalk-cpu/verification.json',
                   'bindings-headless/verification.json', 'bindings-headless/source-before.json', 'bindings-headless/source-after.json',
                   'bindings-headless/bindings/fixture/result.json']
    for group, logs in [('jiggle-cpu', ('metadata', 'bridge', 'capture', 'capture_review')), ('crosswalk-cpu', ('metadata', 'collector', 'adapter'))]:
        child_names += [group + '/' + label + '.log' for label in logs]
    for case in ('bindings', 'helper'):
        child_names.append('bindings-headless/' + case + '/verified.json')
        for stage in ('parse', 'run'):
            child_names += ['bindings-headless/' + case + '/' + stage + suffix for suffix in ('-command.json', '-process.json', '-console.log', '-engine.log')]
    selected.update(('REVIEW', (child / name).relative_to(REVIEW).as_posix()) for name in child_names)
    for label, field in [('catalogue', 'folder'), ('appearance', 'run')]:
        statuses = [load(line) for line in (child / (label + '.log')).read_bytes().splitlines() if line.startswith(b'{')]
        require(len(statuses) == 1, 'One recorded CPU folder')
        derived = Path(statuses[0][field]); require(derived.is_relative_to(REVIEW / 'output'), 'Derived CPU path outside review')
        selected.add(('REVIEW', (derived / 'result.json').relative_to(REVIEW).as_posix()))
    receipt = Path(report['reports']['ui']['private_receipt']); require(receipt.is_relative_to(REVIEW / 'output/private-desktop'), 'Derived private receipt boundary')
    selected.add(('REVIEW', receipt.relative_to(REVIEW).as_posix()))
    for name in ('tests/verify_source_choice_foundation.py', 'tests/verify_source_bone_bindings.py', 'tests/verify_source_choices.py',
                 'tests/verify_source_jiggle_cpu.py', 'tests/verify_source_bone_crosswalk_cpu.py'):
        selected.add(('REVIEW', name))
    for name in ('experiments/run_neon_source_foundation_followup_20261117.py', 'experiments/run_neon_scene_followup_20261117.py'):
        selected.add(('MAIN', name))
    roots = {'MAIN': MAIN, 'REVIEW': REVIEW}; rows = []; raw = {}
    for alias, relative in sorted(selected):
        path = roots[alias] / relative; safe_file(path, roots[alias])
        require(path.suffix in ('.json', '.log', '.py'), 'Only declared source/scalar/log payloads')
        before = path.stat(); data = path.read_bytes(); after = path.stat()
        require(len(data) <= 2 * 1024 * 1024 and b'\0' not in data, 'Bounded public text only'); data.decode('utf-8-sig')
        require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'Original changed during capture')
        row = {'root': alias, 'path': relative, 'bytes': len(data), 'sha256': sha(data), 'mtime_ns': before.st_mtime_ns}
        rows.append(row); raw[alias + ':' + relative] = data
    summary = check(raw, str(REVIEW))
    spec = {'format': 'has_foundation_fe9_closed_text_archive_recipe_1', 'scope': 'EXACT_CLOSED_FOCUSED_FOUNDATION_SOURCE_SCALAR_LOG_AND_ONE_PRIVATE_RECEIPT',
            'roots': {key: str(value) for key, value in roots.items()}, 'inputs': rows, 'expected_summary': summary,
            'decoded_golden_GLB_source_art_media_native_or_worker_request_arrays_included': False, 'upcoming_full_output_read': False}
    with (HERE / 'INPUTS.json').open('x', encoding='utf-8', newline='\n') as stream: json.dump(spec, stream, indent=2); stream.write('\n')
    print(json.dumps({'input_bindings': len(rows), 'INPUTS_sha256': sha((HERE / 'INPUTS.json').read_bytes()), 'summary': summary}, indent=2))


if __name__ == '__main__': main()
