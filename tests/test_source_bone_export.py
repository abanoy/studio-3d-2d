"""Authored adapter/runtime-file races and exact-once export controls; CPU only."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
import source_bone_export as E
import source_bone_metadata as M
import source_jiggle_crosswalk as C
import source_mdl_snapshot as S
from test_source_jiggle_crosswalk import host_fixture, prove, export_fixture, begin_export, final_hook, glb, Mesh


class BoneExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="has-export-adapter-")
        self.addCleanup(self.temp.cleanup); self.folder = Path(self.temp.name)
        self.path = self.folder/"authored.mdl"; self.path.write_bytes(b"authored capture, not a native asset")
        self.capture = S.capture_selected_mdl(str(self.path))
        self.profile = patch.object(C, "JUNKO_SHA256", self.capture.native_sha256)
        self.profile.start(); self.addCleanup(self.profile.stop)
        self.request = {"sha256": "a"*64, "scale": M.SCALE, "sourceio": str(self.folder),
                        "sourceio_revision": M.J.SOURCEIO_REVISION}

    def observation(self):
        proof = prove(host_fixture())
        value = object.__new__(E.ExportObservation)
        value.capture = self.capture; value.original_sha256 = self.request["sha256"]
        value.source_pins = (); value.exporter_pins = (); value.proof = proof
        value.collector = C.ExportCollector(proof, dict(C.EXPORTER_PINS))
        module = ModuleType("io_scene_gltf2")
        value.module = module; value.bpy = NS(context=NS(preferences=NS(addons={module.__name__: module})))
        value.failure = None; value.glb_file = None
        return value, module

    def test_other_mdl_no_rule_or_bsp_never_loads_runtime_or_installs_hooks(self):
        for capture in (None, S.NotInspected("initial-selected-mdl-unreadable"), self.capture):
            with patch.object(C, "JUNKO_SHA256", "0"*64), patch.object(E, "ExportObservation", side_effect=AssertionError("no runtime")):
                self.assertEqual(E.prepare({}, capture, None, None, None, {"state": "none"}), (None, None))

    def test_qualified_default_prepares_once_and_appearance_archive_scale_omit(self):
        marker = object()
        with patch.object(E, "ExportObservation", return_value=marker) as constructor:
            self.assertEqual(E.prepare(self.request, self.capture, None, None, None, {"state": "retained"}), (marker, None))
            self.assertEqual(constructor.call_count, 1)
        for changes in ({"scale": .01}, {"appearance": {}}, {"source_member": "models/hair.mdl"}):
            with patch.object(E, "ExportObservation", side_effect=AssertionError("unsupported profile")):
                self.assertEqual(E.prepare({**self.request, **changes}, self.capture, None, None, None, {"state": "retained"}),
                                 (None, "unsupported_profile"))

    def test_initial_pin_or_proof_refusal_is_bounded_optional(self):
        for error in (C.CrosswalkError("private path must not leak"), FileNotFoundError("private path"), ImportError("addon absent")):
            with patch.object(E, "ExportObservation", side_effect=error):
                result, reason = E.prepare(self.request, self.capture, None, None, None, {"state": "retained"})
                self.assertIsNone(result); self.assertEqual(reason, "source_pins_unsupported")
                self.assertNotIn(b"private", M.omission(reason))

    def test_capture_identity_change_precedes_optional_scale_refusal(self):
        self.path.write_bytes(b"changed")
        with self.assertRaises(S.SourceIdentityError):
            E.prepare({**self.request, "scale": .01}, self.capture, None, None, None, {"state": "retained"})

    def test_constructor_identity_errors_are_never_optional(self):
        for error in (S.SourceIdentityError("captured bytes changed"), C.SourceIdentityError("observed pin changed")):
            with patch.object(E, "ExportObservation", side_effect=error), self.assertRaises(type(error)):
                E.prepare(self.request, self.capture, None, None, None, {"state": "retained"})

    def test_pin_initial_mismatch_refuses_and_matching_capture_rechecks(self):
        path = self.folder/"factory.py"; path.write_bytes(b"authored factory")
        expected = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()}
        pins = E.capture_pins(self.folder, expected); E.recheck_pins(pins)
        with self.assertRaises(C.CrosswalkError): E.capture_pins(self.folder, {path.name: "0"*64})
        self.assertEqual(path.read_bytes(), b"authored factory")

    def test_same_size_mtime_pin_mutation_is_fatal_and_missing_pin_is_fatal(self):
        path = self.folder/"reader.py"; path.write_bytes(b"sourceA")
        pins = E.capture_pins(self.folder, {path.name: hashlib.sha256(path.read_bytes()).hexdigest()})
        info = path.stat(); path.write_bytes(b"sourceB"); os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns))
        with self.assertRaises(C.SourceIdentityError): E.recheck_pins(pins)
        path.unlink()
        with self.assertRaises(C.SourceIdentityError): E.recheck_pins(pins)

    def test_owned_registration_calls_export_once_with_explicit_safe_kwargs(self):
        value, module = self.observation(); calls = []
        def operator(**kwargs):
            calls.append(kwargs)
            self.assertIs(module.glTF2ExportUserExtension(), value.collector)
            return {"FINISHED"}
        arguments = {"export_extras": False, "export_animations": False, "export_yup": True}
        with patch.dict(sys.modules, {module.__name__: module}): self.assertEqual(value.export(operator, arguments), {"FINISHED"})
        self.assertEqual(calls, [{**arguments, **E.EXPLICIT_KWARGS}])
        self.assertFalse(hasattr(module, "glTF2ExportUserExtension"))
        self.assertFalse(calls[0]["export_gpu_instances"])

    def test_unavailable_registration_calls_original_export_exactly_once(self):
        value, module = self.observation(); module.glTF2ExportUserExtension = object(); calls = []
        with patch.dict(sys.modules, {module.__name__: module}): value.export(lambda **kw: calls.append(kw), {"export_extras": False})
        self.assertEqual(calls, [{"export_extras": False}]); self.assertEqual(value.failure, "proof_unavailable")

    def test_real_export_failure_escapes_without_retry_and_registration_is_removed(self):
        value, module = self.observation(); calls = []
        def operator(**kwargs): calls.append(kwargs); raise RuntimeError("real export refused")
        with patch.dict(sys.modules, {module.__name__: module}), self.assertRaisesRegex(RuntimeError, "real export refused"):
            value.export(operator, {})
        self.assertEqual(len(calls), 1); self.assertFalse(hasattr(module, "glTF2ExportUserExtension"))

    def test_registration_owner_change_omits_without_repeating_export(self):
        value, module = self.observation(); calls = []
        def operator(**kwargs): calls.append(kwargs); module.glTF2ExportUserExtension = object()
        with patch.dict(sys.modules, {module.__name__: module}): value.export(operator, {})
        self.assertEqual(len(calls), 1); self.assertEqual(value.failure, "proof_unavailable")
        self.assertIsNone(value.complete(self.folder/"does-not-need-read.glb"))

    def test_final_glb_mutation_after_observation_is_fatal(self):
        value, _ = self.observation()
        proof = value.proof; exported = export_fixture(proof); begin_export(exported, proof); final_hook(exported)
        value.collector = exported.collector
        path = self.folder/"scene.glb"; path.write_bytes(glb(exported))
        observed = value.complete(path); self.assertIsNotNone(observed)
        self.assertEqual(value.publication_identity(), observed["glb_sha256"])
        before = path.stat(); data = bytearray(path.read_bytes()); data[-1] ^= 1
        path.write_bytes(data); os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        with self.assertRaises(C.SourceIdentityError): value.publication_identity()

    def test_missing_late_hook_omits_proof_and_never_writes_any_file(self):
        value, _ = self.observation(); path = self.folder/"scene.glb"; path.write_bytes(b"not used")
        before = set(self.folder.iterdir())
        self.assertIsNone(value.complete(path)); self.assertEqual(value.failure, "proof_unavailable")
        self.assertEqual(set(self.folder.iterdir()), before)

    def test_same_capture_and_original_context_required_before_report_omission(self):
        value, _ = self.observation(); state = {"observation": value, "observed": None, "reason": "proof_unavailable"}
        with self.assertRaises(C.SourceIdentityError): E.augment_plan({}, state, self.capture, "0"*64, "\r\n")
        with self.assertRaises(C.SourceIdentityError): E.augment_plan({}, state, object(), self.request["sha256"], "\r\n")

    def test_final_source_recheck_cannot_escape_through_proof_omission(self):
        value, _ = self.observation(); value.failure = "proof_unavailable"
        state = {"observation": value, "observed": None, "reason": "proof_unavailable"}
        self.path.write_bytes(b"changed")
        with self.assertRaises(S.SourceIdentityError): E.augment_plan({}, state, self.capture, self.request["sha256"], "\r\n")

    def test_declared_sourceio_revision_must_match_qualified_profile(self):
        with patch.object(E, "ExportObservation", side_effect=AssertionError("unqualified revision")):
            self.assertEqual(E.prepare({**self.request, "sourceio_revision": "unqualified"}, self.capture, None, None, None,
                                      {"state": "retained"}), (None, "source_pins_unsupported"))

    def test_oversized_optional_GLB_refuses_before_opening_or_allocating(self):
        value, _ = self.observation()
        path = NS(stat=lambda: NS(st_size=128*1024*1024+1),
                  open=lambda *args: self.fail("Oversized optional GLB must not be opened"))
        self.assertIsNone(value.complete(path))
        self.assertEqual(value.failure, "proof_unavailable")

    def test_actual_factory_alias_origin_and_container_object_are_separate_gates(self):
        namespace = {}
        factory_path = self.folder/"blender_bindings/models/mdl44/import_mdl.py"
        exec(compile("def create_armature(): pass\n", str(factory_path), "exec"), namespace)
        factory = namespace["create_armature"]
        left = NS(create_armature=factory); right = NS(create_armature=factory)
        exporter = ModuleType("io_scene_gltf2"); exporter.__file__ = str(E.EXPORTER_ROOT/"__init__.py")
        bpy = NS(context=NS(preferences=NS(addons={exporter.__name__: exporter})))
        mdl = object(); container = NS(mdl=mdl, armature=object()); proof = prove(host_fixture())
        modules = {"SourceIO.blender_bindings.models.mdl44.import_mdl": left,
                   "SourceIO.blender_bindings.models.mdl49.import_mdl": right, exporter.__name__: exporter}
        with patch.dict(sys.modules, modules), patch.object(E, "capture_pins", return_value=()), \
                patch.object(C, "prove_native_blender", return_value=proof) as prover, \
                patch.object(E.importlib, "import_module", return_value=exporter):
            value = E.ExportObservation(self.request, self.capture, mdl, container, bpy)
            self.assertIs(value.capture, self.capture)
            self.assertEqual(prover.call_args_list[0].args[:4], (self.capture.raw, self.capture.native_sha256, mdl, container.armature))
            right.create_armature = lambda: None
            with self.assertRaisesRegex(C.CrosswalkError, "factory_alias_or_origin"):
                E.ExportObservation(self.request, self.capture, mdl, container, bpy)
            right.create_armature = factory; container.mdl = object()
            with self.assertRaisesRegex(C.CrosswalkError, "container_armature_join"):
                E.ExportObservation(self.request, self.capture, mdl, container, bpy)
            container.mdl = mdl; exporter.__file__ = str(self.folder/"unapproved-addon.py")
            with self.assertRaisesRegex(C.CrosswalkError, "exporter_extension_origin"):
                E.ExportObservation(self.request, self.capture, mdl, container, bpy)

    def test_plain_exporter_flat_classes_pass_and_unknown_classes_latch(self):
        proof = prove(host_fixture()); value = export_fixture(proof)
        prefix = "io_scene_gltf2.io.com.gltf2_io"
        flat = lambda name, item: type(name, (NS,), {"__module__": prefix})(**vars(item))
        value.nodes = [flat("Node", item) for item in value.nodes]
        value.skin = flat("Skin", value.skin); value.skin.joints = [value.nodes[1], value.nodes[3], value.nodes[4]]
        value.gltf = flat("Gltf", value.gltf); value.gltf.nodes = value.nodes; value.gltf.skins = [value.skin]
        value.gltf.scenes = [flat("Scene", item) for item in value.gltf.scenes]
        value.gltf.meshes = [type("Mesh", (Mesh,), {"__module__": prefix})()]
        value.settings["vtree"].nodes["owner"].node = value.nodes[2]
        value.collector = E.ObservedCollector(proof, dict(C.EXPORTER_PINS))
        value.settings["gltf_user_extensions"] = [value.collector]
        begin_export(value, proof); final_hook(value)
        self.assertIsNone(value.collector.failure)
        self.assertEqual(len(value.collector.finish(glb(value))["bones"]), 3)
        bad = export_fixture(proof); bad.collector = E.ObservedCollector(proof, dict(C.EXPORTER_PINS))
        bad.settings["gltf_user_extensions"] = [bad.collector]
        begin_export(bad, proof); final_hook(bad)
        self.assertEqual(bad.collector.failure[0], "types")
        with self.assertRaises(C.CrosswalkError): bad.collector.finish(glb(bad))


if __name__ == "__main__": unittest.main(verbosity=2)
