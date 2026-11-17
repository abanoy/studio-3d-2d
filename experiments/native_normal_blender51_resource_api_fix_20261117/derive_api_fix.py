"""Source-only API correction; never import bpy, launch, or read native inputs."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT = ROOT / 'experiments/native_normal_resource_survey_20261117'
PARENT_SHA = 'b6069eb8c87d7599d10165de987ab2d9924fb377890e12a4cb2f0bdaf9ab735c'
PUBLIC_BLENDER_SOURCE = Path(r'C:\Program Files\Blender Foundation\Blender 5.1\5.1\scripts\modules\bpy\utils\__init__.py')
COPY_NAMES = ('export_provenance.py', 'loaded_survey.py', 'probe_resources.py',
              'stager.py', 'survey_admission.py', 'setter_support.py', 'placement_sentinel.py')
RULES = {
    'survey_core.py': [(b'bpy.blend_paths(absolute=False, packed=include_packed, local=False)',
                        b'bpy.utils.blend_paths(absolute=False, packed=include_packed, local=False)')],
    'test_resources.py': [(b'    bpy.blend_paths = blend_paths', b'    bpy.utils = NS(blend_paths=blend_paths)'),
                          (b'bpy = fixture(); old = bpy.blend_paths', b'bpy = fixture(); old = bpy.utils.blend_paths'),
                          (b'    bpy.blend_paths = changed', b'    bpy.utils.blend_paths = changed')],
}


def sha(raw): return hashlib.sha256(raw).hexdigest()


def parent_sources():
    index_raw = (PARENT / 'INDEX.json').read_bytes()
    assert sha(index_raw) == PARENT_SHA, 'Original sealed survey INDEX differs'
    rows = {row['path']: row for row in json.loads(index_raw)['files']}
    result = {}
    for name in (*COPY_NAMES, *RULES):
        raw = (PARENT / name).read_bytes(); row = rows[name]
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256'], name
        result[name] = raw
    return result


def render(name, raw):
    for before, after in RULES.get(name, []):
        assert raw.count(before) == 1, 'Exact single literal required: ' + name
        raw = raw.replace(before, after)
    return raw


def inverse(name, raw):
    for before, after in reversed(RULES.get(name, [])):
        assert raw.count(after) == 1, 'Exact single inverse required: ' + name
        raw = raw.replace(after, before)
    return raw


def source_evidence():
    raw = PUBLIC_BLENDER_SOURCE.read_bytes()
    unit = ast.parse(raw)
    exports = next(ast.literal_eval(node.value) for node in unit.body
                   if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '__all__' for t in node.targets))
    assert 'blend_paths' in exports
    assert any(isinstance(node, ast.ImportFrom) and node.module == '_bpy'
               and any(alias.name == 'blend_paths' for alias in node.names) for node in unit.body)
    return {'role': 'installed_public_Blender_5_1_bpy_utils_source', 'path': str(PUBLIC_BLENDER_SOURCE),
            'bytes': len(raw), 'sha256': sha(raw), 'blend_paths_in_utils_all': True,
            'utils_imports_blend_paths_from_bpy_extension': True,
            'module_imported_or_executed': False}


def main():
    sources = parent_sources(); rows = {}
    for name, original in sources.items():
        derived = render(name, original)
        assert inverse(name, derived) == original
        compile(derived, name, 'exec')
        with (HERE / name).open('xb') as stream: stream.write(derived)
        rows[name] = {'parent_sha256': sha(original), 'derived_sha256': sha(derived),
                      'bytes': len(derived), 'whole_source_inverse_exact': True,
                      'literal_changes': len(RULES.get(name, []))}
    evidence = {'format': 'has_B_resource_Blender51_API_source_derivation_1',
                'parent_INDEX_sha256': PARENT_SHA, 'sources': rows,
                'public_Blender_source': source_evidence(),
                'original_31_assertion_bodies_changed': False,
                'collector_change': 'bpy.blend_paths -> bpy.utils.blend_paths at the sole path enumeration call',
                'test_changes': 'Namespace the fixture callable and its existing mutation hook; retain every assertion',
                'native_input_or_private_output_read': False, 'bpy_imported': False,
                'native_or_process_or_CIM_or_Git_action': False}
    with (HERE / 'DERIVATION.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(evidence, stream, indent=2); stream.write('\n')
    print(json.dumps({'source_files': len(rows), 'collector_literal_changes': 1,
                      'test_mock_literal_changes': 3, 'all_inverses_exact': True}))


if __name__ == '__main__': main()
