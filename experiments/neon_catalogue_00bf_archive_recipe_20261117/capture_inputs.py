"""Freeze only the named closed00bf public scalar/source/log/receipt files."""
from pathlib import Path
import hashlib
import json
from archive_checks import ROOT_RUN, check, load, require

HERE = Path(__file__).resolve().parent
MAIN = HERE.parents[1]
REVIEW = MAIN.parent / 'has-neon-review-20261116-c2d52ff'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    require(not (HERE / 'INPUTS.json').exists(), 'Never replace frozen inputs')
    folder = REVIEW / ROOT_RUN; root = load((folder / 'verification.json').read_bytes())
    names = ['verification.json', 'source-before.json', 'source-after.json']
    for label in ('catalogue', 'comparison', 'height'):
        names += [label + suffix for suffix in ('-command.json', '-start.json', '-process.json', '-report.json', '-stdout.log', '-stderr.log')]
    for label in ('before', 'catalogue-after', 'comparison-after', 'height-after', 'after'):
        names += [label + suffix for suffix in ('-closure.json', '-scope-stdout.log', '-scope-stderr.log')]
    selected = {('REVIEW', (folder / name).relative_to(REVIEW).as_posix()) for name in names}
    public_children = {
        'catalogue': ('result.json', 'reader-result.json', 'shape_catalog_unit.log', 'shape_catalog_smoke.log', 'shape_catalog_smoke-reader.log'),
        'comparison': ('result.json', 'teardown-result.json', 'draft-reader.json', 'engine.log', 'teardown-engine.log', 'draft-reader.log'),
        'height': ('result.json', 'engine.log', 'reader.log', 'native.log', 'command.json', 'reader-command.json', 'native-command.json'),
    }
    for row in root['rows']:
        child = Path(row['report']['folder']); require(child.is_relative_to(REVIEW / 'output'), 'Saved child boundary')
        selected.update(('REVIEW', (child / name).relative_to(REVIEW).as_posix()) for name in public_children[row['label']])
        for value in row['report']['private_receipts']:
            receipt = Path(value); require(receipt.is_relative_to(REVIEW / 'output/private-desktop'), 'Saved physical receipt boundary')
            selected.add(('REVIEW', receipt.relative_to(REVIEW).as_posix()))
    selected.update(('REVIEW', 'tests/' + name) for name in ('verify_shape_catalog.py', 'verify_shape_comparison.py', 'verify_character_height.py', 'native_fixture_root.py'))
    selected.update(('MAIN', 'experiments/' + name) for name in ('run_neon_catalogue_followup_20261117.py', 'run_neon_scene_followup_20261117.py', 'neon_shape_catalog_fixture_actual_inputs_20261117/PREPARATION.json'))
    excluded_names = {'plans.json', 'catalogue-plans.json', 'native-plans.json', 'expected.json', 'positions.json', 'draft.json', 'raw-vrm.json', 'parameters.json'}
    roots = {'MAIN': MAIN, 'REVIEW': REVIEW}; rows = []; raw = {}
    for alias, relative in sorted(selected):
        path = roots[alias] / relative
        require(path.resolve().is_relative_to(roots[alias]) and path.suffix in ('.json', '.log', '.py') and path.name not in excluded_names, 'Exact source/scalar/log domain')
        for item in (path, *path.parents):
            if item == roots[alias].parent: break
            require(not item.is_symlink() and not getattr(item.lstat(), 'st_file_attributes', 0) & 0x400, 'Input reparse refused')
        before = path.stat(); data = path.read_bytes(); after = path.stat()
        require(len(data) <= 2 * 1024 * 1024 and b'\0' not in data, 'Bounded public text only'); data.decode('utf-8-sig')
        require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'Original changed during capture')
        rows.append({'root': alias, 'path': relative, 'bytes': len(data), 'sha256': sha(data), 'mtime_ns': before.st_mtime_ns})
        raw[alias + ':' + relative] = data
    summary = check(raw, str(REVIEW))
    spec = {'format': 'has_catalogue_00bf_closed_text_archive_recipe_1', 'scope': 'EXACT_CLOSED_CATALOGUE_COMPARISON_HEIGHT_SOURCE_SCALAR_LOG_COMMAND_AND_PHYSICAL_RECEIPTS',
            'roots': {key: str(value) for key, value in roots.items()}, 'inputs': rows, 'expected_summary': summary,
            'excluded_generated_or_native_input_filenames': sorted(excluded_names), 'models_media_original_native_arrays_or_upcoming_full_outputs_read': False}
    with (HERE / 'INPUTS.json').open('x', encoding='utf-8', newline='\n') as stream: json.dump(spec, stream, indent=2); stream.write('\n')
    print(json.dumps({'input_bindings': len(rows), 'INPUTS_sha256': sha((HERE / 'INPUTS.json').read_bytes()), 'summary': summary}, indent=2))


if __name__ == '__main__': main()
