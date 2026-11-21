"""Synthetic guards only: no Blender, SDK, MDL, converter or child process."""
from pathlib import Path
import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import junko_part_bridge_probe as P

BODY = next(key for key, value in P.PROFILES.items() if value[0] == 'body')
DRESS = next(key for key, value in P.PROFILES.items() if value[0] == 'dress')


class Guards(unittest.TestCase):
    def setUp(self):
        self.request = {'sha256': BODY, 'scale': .01905, 'source_member': None,
                        'appearance': None,
                        'sourceio_revision': 'fe24260b97ac03b899d9b5d4f0fd7b34772f3647'}
        file = P.Capture.FileSnapshot('<synthetic>', 1, 0, 0, 1)
        self.capture = P.Capture.MdlCapture(file, b'x', BODY)
        self.bpy = types.SimpleNamespace(app=types.SimpleNamespace(version=(5, 1, 0)))

    def invoke(self):
        with mock.patch.object(P, 'PartObservation', return_value='synthetic-observation') as factory:
            result = P.prepare(self.request, self.capture, object(), object(), self.bpy, {})
            self.assertEqual(result, ('synthetic-observation', None))
            factory.assert_called_once()

    def refuse(self):
        with mock.patch.object(P, 'PartObservation') as factory:
            with self.assertRaises(P.C.CrosswalkError):
                P.prepare(self.request, self.capture, None, None, self.bpy, {})
            factory.assert_not_called()

    def test_body_profile(self):
        self.assertEqual(P.PROFILES[BODY], ('body', 145)); self.invoke()

    def test_dress_profile(self):
        self.request['sha256'] = DRESS
        self.capture = P.Capture.MdlCapture(self.capture.file, b'x', DRESS)
        self.assertEqual(P.PROFILES[DRESS], ('dress', 112)); self.invoke()

    def test_no_third_profile(self):
        self.capture = P.Capture.MdlCapture(self.capture.file, b'x', '0' * 64); self.refuse()

    def test_capture_type(self):
        self.capture = types.SimpleNamespace(native_sha256=BODY); self.refuse()

    def test_original_sha(self):
        self.request['sha256'] = DRESS; self.refuse()

    def test_scale(self):
        self.request['scale'] = 1.; self.refuse()

    def test_archive_member(self):
        self.request['source_member'] = 'models/x.mdl'; self.refuse()

    def test_appearance(self):
        self.request['appearance'] = {}; self.refuse()

    def test_sdk_revision(self):
        self.request['sourceio_revision'] = 'unknown'; self.refuse()

    def test_blender_version(self):
        self.bpy.app.version = (5, 2, 0); self.refuse()

    def publisher(self, directory):
        observation = object.__new__(P.PartObservation)
        observation.capture = self.capture; observation.original_sha256 = BODY
        observation.private_written = False; observation.failure = None; observation.role = 'body'
        observation.proof = types.SimpleNamespace(bindings=[None])
        observation.glb_file = (Path(directory) / 'scene.glb', '1' * 64)
        observation.publication_identity = lambda: '1' * 64
        observed = {'native_mdl_sha256': BODY, 'glb_sha256': '1' * 64}
        return observation, {'observation': observation, 'observed': observed}

    def test_private_only_publication_preserves_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            observation, state = self.publisher(directory)
            planned = {'report': {'ordinary': True}, 'report_bytes': b'ordinary', 'note_bytes': None}
            with contextlib.redirect_stdout(io.StringIO()) as log:
                result = P.augment_plan(planned, state, self.capture, BODY, '\n')
            self.assertEqual(planned, {'report': {'ordinary': True}, 'report_bytes': b'ordinary', 'note_bytes': None})
            self.assertIs(result['report'], planned['report'])
            self.assertEqual(result['report_bytes'], b'ordinary')
            self.assertIsNone(result['crosswalk_note_bytes'])
            proof = json.loads((Path(directory) / 'PRIVATE_part_export_binding.json').read_bytes())
            self.assertTrue(proof['private_do_not_publish'])
            self.assertFalse(proof['native_profile_promotion'])
            self.assertFalse(proof['native_simulation'])
            self.assertEqual(proof['HAS_runtime_binding'], 'unattempted')
            self.assertTrue(observation.private_written)
            self.assertEqual(len(log.getvalue().splitlines()), 1)

    def test_missing_final_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            _, state = self.publisher(directory); state['observed'] = None
            with self.assertRaises(P.C.CrosswalkError): P.augment_plan({}, state, self.capture, BODY, '\n')
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_wrong_final_glb(self):
        with tempfile.TemporaryDirectory() as directory:
            _, state = self.publisher(directory); state['observed']['glb_sha256'] = '2' * 64
            with self.assertRaises(P.C.CrosswalkError): P.augment_plan({}, state, self.capture, BODY, '\n')
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_latched_export_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            observation, state = self.publisher(directory); observation.failure = 'proof_unavailable'
            with self.assertRaises(P.C.CrosswalkError): P.augment_plan({}, state, self.capture, BODY, '\n')
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_existing_private_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            _, state = self.publisher(directory)
            path = Path(directory) / 'PRIVATE_part_export_binding.json'; path.write_bytes(b'keep')
            with self.assertRaises(FileExistsError): P.augment_plan({}, state, self.capture, BODY, '\n')
            self.assertEqual(path.read_bytes(), b'keep')

    def test_repeat_publication_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            observation, state = self.publisher(directory); observation.private_written = True
            with self.assertRaises(P.C.CrosswalkError): P.augment_plan({}, state, self.capture, BODY, '\n')
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
