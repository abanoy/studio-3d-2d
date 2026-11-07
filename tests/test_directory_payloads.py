"""Owned inventory/sync faults; opaque fixture bytes do not prove native decoding."""
from pathlib import Path
import hashlib
import json
import os
import tempfile
import unittest
from unittest import mock
from tools import directory_commit as dc
from tools import directory_payloads as payloads
from tests import test_directory_commit as fixtures


class DirectoryPayloadTests(unittest.TestCase):
    def fixture(self, directory):
        root, args, before, backup, _ = fixtures.DirectoryCommitTests().fixture(directory)
        data = b'opaque inventory payload; no native decoding claim'
        names = ['assets/model.glb', 'assets/particle.json', 'assets/texture.png',
                 'assets/tone.wav', 'references/sheet.png', 'cels/content/ink.png',
                 'cels/content/child.png']
        for name in names:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        manifest = dict(schema_version=8, layers=[dict(cels=[dict(path=names[5])])],
                        world=dict(objects=[dict(path=names[0], sha256=digest)],
                                   effects=[dict(path=names[1], sha256=digest,
                                                 texture_path=names[2], texture_sha256=digest)]),
                        audio=dict(clips=[dict(path=names[3], sha256=digest)]),
                        reference_sheet=dict(path=names[4], sha256=digest),
                        sequence_graph=dict(assets=[dict(scene=dict(layers=[dict(cels=[dict(path=names[6])])]))]),
                        metadata=dict(path='outside-original', note='never glob unrelated files'))
        (root / args[1]).write_text(json.dumps(manifest))
        args = (root, args[1], args[2], dc.sha(root / args[1]), True)
        return root, args, before, backup, names

    def test_collects_declared_nested_particle_audio_reference_files_without_metadata_globbing(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, _, _, names = self.fixture(directory)
            result = payloads.declared(json.loads((root / args[1]).read_bytes()))
            self.assertEqual(set(result), set(names))
            self.assertIsNone(result[names[5]])
            self.assertEqual(result[names[0]], dc.sha(root / names[0]))
            legacy = dict(scene=dict(path=names[0], sha256=result[names[0]]),
                          model=dict(path=names[0], sha256=result[names[0]]),
                          audio=dict(path=names[3], sha256=result[names[0]]))
            self.assertEqual(set(payloads.declared(legacy)), {names[0], names[3]})

    @unittest.skipUnless(os.name == 'posix', 'POSIX payload/directory fd sync; Windows gate remains')
    def test_every_declared_file_and_created_parent_is_synced(self):
        with tempfile.TemporaryDirectory() as directory:
            boundary = Path(directory)
            root = boundary / 'created' / 'project'
            root.mkdir(parents=True)
            root, args, _, _, names = self.fixture(root)
            outside = boundary / 'unrelated-original'
            outside.write_bytes(b'ORIGINAL')
            observed = []
            original = dc.os.fsync
            def sync(handle):
                info = os.fstat(handle)
                observed.append((info.st_dev, info.st_ino))
                return original(handle)
            with mock.patch.object(dc.os, 'fsync', side_effect=sync):
                result = dc.commit(*args, boundary=boundary)
            self.assertTrue(result['ok']); self.assertTrue(result['payload_synced'])
            self.assertEqual(result['files'], len(names)); self.assertEqual(result['assets_verified'], 5)
            for name in names:
                info = (root / name).stat()
                self.assertIn((info.st_dev, info.st_ino), observed)
            directories = payloads.parent_directories({(root / name).parent for name in names} | {root}, root, boundary)
            self.assertEqual(result['directories_synced'], len(directories))
            for path in directories:
                info = path.stat()
                self.assertIn((info.st_dev, info.st_ino), observed)
            info = outside.stat()
            self.assertNotIn((info.st_dev, info.st_ino), observed)
            self.assertEqual(outside.read_bytes(), b'ORIGINAL')

    def test_missing_or_changed_asset_keeps_current_and_backup(self):
        for missing in (True, False):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as directory:
                root, args, before, backup, names = self.fixture(directory)
                if missing: (root / names[0]).unlink()
                else: (root / names[0]).write_bytes(b'changed payload')
                with self.assertRaises(dc.HasError): dc.commit(*args)
                self.assertEqual((root / 'project.json').read_bytes(), before)
                self.assertEqual((root / 'project.backup.json').read_bytes(), backup)

    @unittest.skipUnless(os.name == 'posix', 'Owned symlink fixture; native Windows gate remains')
    def test_linked_managed_file_or_parent_never_touches_external_original(self):
        for parent in (True, False):
            with self.subTest(parent=parent), tempfile.TemporaryDirectory() as directory:
                root, args, before, backup, names = self.fixture(directory)
                outside = root / 'original'
                if parent:
                    outside.mkdir(); (outside / 'ink.png').write_bytes(b'ORIGINAL')
                    (root / 'cels/content/ink.png').unlink(); (root / 'cels/content/child.png').unlink()
                    (root / 'cels/content').rmdir(); (root / 'cels/content').symlink_to(outside, target_is_directory=True)
                else:
                    outside.write_bytes(b'ORIGINAL'); (root / names[0]).unlink(); (root / names[0]).symlink_to(outside)
                with self.assertRaises(dc.HasError): dc.commit(*args)
                self.assertEqual((outside / 'ink.png' if parent else outside).read_bytes(), b'ORIGINAL')
                self.assertEqual((root / 'project.json').read_bytes(), before)
                self.assertEqual((root / 'project.backup.json').read_bytes(), backup)

    @unittest.skipUnless(os.name == 'posix', 'POSIX fsync injection; native Windows gate remains')
    def test_payload_sync_failure_happens_before_either_manifest_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, backup, names = self.fixture(directory)
            asset = (root / names[0]).stat()
            original = dc.os.fsync
            def sync(handle):
                info = os.fstat(handle)
                if (info.st_dev, info.st_ino) == (asset.st_dev, asset.st_ino): raise OSError('injected payload sync failure')
                return original(handle)
            with mock.patch.object(dc.os, 'fsync', side_effect=sync):
                with self.assertRaises(OSError): dc.commit(*args)
            self.assertEqual((root / 'project.json').read_bytes(), before)
            self.assertEqual((root / 'project.backup.json').read_bytes(), backup)

    def test_unsafe_or_conflicting_payload_addresses_refuse(self):
        digest = 'a' * 64
        for name in ['../original', '/tmp/original', 'outside/file', 'assets/../original', 'assets\\original']:
            with self.subTest(name=name), self.assertRaises(dc.HasError):
                payloads.declared(dict(model=dict(path=name, sha256=digest)))
        with self.assertRaises(dc.HasError):
            payloads.declared(dict(model=dict(path='assets/model.glb', sha256=digest),
                                   scene=dict(path='assets/model.glb', sha256='b' * 64)))
        for bad in [dict(audio=None), dict(layers=False), dict(world=[]), dict(sequence_graph=False)]:
            with self.subTest(bad=bad), self.assertRaises(dc.HasError): payloads.declared(bad)

    def test_invalid_parent_boundary_refuses_before_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, backup, _ = self.fixture(directory)
            child = root / 'assets'
            with self.assertRaises(dc.HasError): dc.commit(*args, boundary=child)
            self.assertEqual((root / 'project.json').read_bytes(), before)
            self.assertEqual((root / 'project.backup.json').read_bytes(), backup)

    @unittest.skipUnless(os.name == 'posix', 'Owned hard-link fixture; native Windows gate remains')
    def test_readonly_sync_of_hardlinked_payload_preserves_source_bytes_and_mtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, _, _, names = self.fixture(directory)
            source = root / 'source-original'
            source.write_bytes((root / names[0]).read_bytes()); (root / names[0]).unlink(); os.link(source, root / names[0])
            before = source.read_bytes(); stamp = source.stat().st_mtime_ns
            self.assertTrue(dc.commit(*args)['ok'])
            self.assertEqual(source.read_bytes(), before); self.assertEqual(source.stat().st_mtime_ns, stamp)


if __name__ == '__main__':
    unittest.main()
