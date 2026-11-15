"""Input/provenance guards only; real native models are covered by GPU suites."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import native_fixture_plans as plans


class NativeFixturePlansTests(unittest.TestCase):
    def setUp(self):
        self.workspace = plans.ROOT
        self.temp = tempfile.TemporaryDirectory(prefix='fixture plans — ', dir=self.workspace / 'output')
        self.root = Path(self.temp.name).resolve()
        assert self.root.is_relative_to(self.workspace / 'output')
        self.output = self.root / 'output'
        self.output.mkdir()
        self.root_patch = patch.object(plans, 'ROOT', self.root)
        self.fixture_patch = patch.object(plans, 'fixture_output', lambda: self.output)
        self.root_patch.start()
        self.fixture_patch.start()
        self.project = self.output / 'sfm-smoke/project'
        self.asset = self.project / 'assets/native.glb'
        self.asset.parent.mkdir(parents=True)
        self.asset.write_bytes(b'input-identity-only')
        self.row = {'kind': 'model', 'path': 'assets/native.glb',
                    'sha256': hashlib.sha256(self.asset.read_bytes()).hexdigest(),
                    'rotation_xyzw': [.707, 0, 0, .707],
                    'metadata': {'native_parameters': {'profile': 'input-only'}, 'preserve': [1, 2]}}
        self.save_project()
        catalogue = self.output / 'catalogue'
        catalogue.mkdir()
        (catalogue / 'catalogue-plans.json').write_text(json.dumps([
            {'label': 'Authored'}, {'label': 'SFM', 'source': str(self.asset)}]), encoding='utf-8')
        (self.output / 'shape-catalog-verification.json').write_text(json.dumps({'folder': str(catalogue)}), encoding='utf-8')

    def tearDown(self):
        self.fixture_patch.stop()
        self.root_patch.stop()
        assert self.root.resolve().is_relative_to(self.workspace / 'output')
        self.temp.cleanup()

    def save_project(self):
        (self.project / 'project.json').write_text(json.dumps({'world': {'objects': [self.row]}}), encoding='utf-8')

    def test_current_checksum_selects_exact_saved_orientation_and_metadata(self):
        (self.output / 'import-height-audit.json').write_text(json.dumps({'folder': 'absent historical cache'}), encoding='utf-8')
        result = plans.catalogue_native_plans()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['rotation_xyzw'], self.row['rotation_xyzw'])
        self.assertEqual(result[0]['metadata'], self.row['metadata'])
        self.assertEqual(result[0]['source_sha256'], self.row['sha256'])

    def test_changed_asset_refuses_instead_of_reusing_metadata(self):
        self.asset.write_bytes(b'changed')
        with self.assertRaisesRegex(AssertionError, 'checksum differs'):
            plans.catalogue_native_plans()

    def test_project_path_cannot_escape_its_own_directory(self):
        outside = self.project.parent / 'outside.glb'
        outside.write_bytes(self.asset.read_bytes())
        self.row['path'] = '../outside.glb'
        self.save_project()
        with self.assertRaisesRegex(AssertionError, 'escapes its project'):
            plans.catalogue_native_plans()

    def test_missing_declared_native_asset_is_not_silently_skipped(self):
        self.asset.unlink()
        with self.assertRaises(FileNotFoundError):
            plans.catalogue_native_plans()

    def test_recorded_manifest_preserves_exact_models_and_requires_declared_count(self):
        recording = self.output / 'recording'
        recording.mkdir()
        packed = recording / 'native-recording.has'
        models = [{'kind': 'model', 'name': 'input only', 'pose_keys': [{'frame': 12, 'value': .12345678901234567}]}]
        with zipfile.ZipFile(packed, 'w') as archive:
            archive.writestr('project.json', json.dumps({'world': {'objects': models}}))
        report = self.output / 'physics-recording-result.json'
        report.write_text(json.dumps({'folder': str(recording), 'native_models': 1}), encoding='utf-8')
        actual, source = plans.recorded_native_models()
        self.assertEqual(actual, models)
        self.assertEqual(source, packed)
        report.write_text(json.dumps({'folder': str(recording), 'native_models': 2}), encoding='utf-8')
        with self.assertRaisesRegex(AssertionError, 'missing'):
            plans.recorded_native_models()


if __name__ == '__main__':
    unittest.main()
