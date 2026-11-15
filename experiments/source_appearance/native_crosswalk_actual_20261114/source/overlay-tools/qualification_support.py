"""UNRUN diagnostic bridge support; execute only in a newly attested owned worker.

Writes diagnostics outside the bundle. No project/report/solver adapter or
production sidecar contract. This file is not imported by current Studio.
"""
from contextlib import contextmanager
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys

import source_jiggle_crosswalk as C
import source_mdl_snapshot as Capture

EXPORTER_ROOT = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\5.1\scripts\addons_core\io_scene_gltf2")
SETTINGS = {"gltf_extras": False, "gltf_skins": True, "gltf_yup": True,
            "gltf_animations": False, "gltf_armature_object_remove": False,
            "gltf_rest_position_armature": True, "gltf_flatten_bones_hierarchy": False,
            "gltf_flatten_obj_hierarchy": False, "gltf_leaf_bone": False,
            "gltf_gpu_instances": False, "gltf_use_gltfpack": False,
            "gltf_draco_mesh_compression": False}


def digest(path):
    path = Path(path); before = path.stat()
    value = hashlib.sha256(path.read_bytes()).hexdigest(); after = path.stat()
    C.require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), "diagnostic_source_changed_during_read")
    return value


def pins(root, expected):
    actual = {name: digest(root/name) for name in expected}
    C.require(actual == expected, "diagnostic_runtime_source_pins_differ")
    return actual


class ObservedCollector(C.ExportCollector):
    def gather_gltf_extensions_hook(self, gltf, export_settings):
        super().gather_gltf_extensions_hook(gltf, export_settings)
        if self.failure is None:
            self.actual_settings = {key: export_settings[key] for key in SETTINGS}
            self.actual_types = {"gltf": type(gltf).__module__+"."+type(gltf).__name__,
                                 "nodes": sorted({type(n).__module__+"."+type(n).__name__ for n in gltf.nodes}),
                                 "skins": sorted({type(n).__module__+"."+type(n).__name__ for n in gltf.skins}),
                                 "scenes": sorted({type(n).__module__+"."+type(n).__name__ for n in gltf.scenes}),
                                 "meshes": sorted({type(n).__module__+"."+type(n).__name__ for n in gltf.meshes})}
            expected = {"gltf": "io_scene_gltf2.io.com.gltf2_io.Gltf",
                        "nodes": ["io_scene_gltf2.io.com.gltf2_io.Node"],
                        "skins": ["io_scene_gltf2.io.com.gltf2_io.Skin"],
                        "scenes": ["io_scene_gltf2.io.com.gltf2_io.Scene"],
                        "meshes": ["io_scene_gltf2.io.com.gltf2_io.Mesh"]}
            if self.actual_types != expected:
                self.failure = ("actual_types", "CrosswalkError", "unexpected_installed_exporter_flat_object_types")


class Qualification:
    def __init__(self, request, capture, mdl, container, bpy):
        C.require(type(capture) is Capture.MdlCapture and capture.native_sha256 == C.JUNKO_SHA256,
                  "diagnostic_requires_exact_independent_Junko_capture")
        Capture.recheck_selected_mdl(capture)
        self.request = request; self.capture = capture; self.bpy = bpy
        self.bundle = Path(request["output"]).resolve(strict=True); self.case = self.bundle.parent
        C.require(self.bundle.name == "bundle" and request.get("source_member") is None,
                  "diagnostic_only_owned_standalone_bundle")
        observer_path = Path(os.environ["HAS_BACKGROUND_OBSERVER_REQUEST"]).resolve(strict=True)
        C.require(observer_path == self.case/"blender-observer-request.json" and
                  digest(observer_path) == os.environ["HAS_BACKGROUND_OBSERVER_SHA256"], "diagnostic_observer_binding")
        self.observer = json.loads(observer_path.read_bytes())
        C.require(self.observer["conversion_request_sha256"] == digest(self.bundle/"conversion-request.json"), "diagnostic_conversion_request_binding")
        self.attestation_path = self.case/"blender-desktop-attestation.json"
        attestation = json.loads(self.attestation_path.read_bytes())
        C.require(attestation["nonce"] == self.observer["nonce"] and attestation["self"]["pid"] == os.getpid(), "diagnostic_Blender_self_binding")
        self.runtime = Path(request["sourceio"]).resolve(strict=True)
        self.source_pins = pins(self.runtime, C.SOURCEIO_PINS)
        self.exporter_pins = pins(EXPORTER_ROOT, C.EXPORTER_PINS)
        factory44 = sys.modules["SourceIO.blender_bindings.models.mdl44.import_mdl"].create_armature
        factory49 = sys.modules["SourceIO.blender_bindings.models.mdl49.import_mdl"].create_armature
        C.require(factory44 is factory49 and Path(factory44.__code__.co_filename).resolve() ==
                  self.runtime/"blender_bindings/models/mdl44/import_mdl.py", "diagnostic_actual_factory_alias_or_origin_differs")
        C.require(getattr(container, "mdl", None) is mdl and container.armature is not None,
                  "diagnostic_actual_mdl_container_armature_join")
        self.factory = {"alias_identity": True, "module": factory44.__module__,
                        "code_filename": factory44.__code__.co_filename, "first_line": factory44.__code__.co_firstlineno,
                        "mdl_type": type(mdl).__module__+"."+type(mdl).__name__}
        self.proof = C.prove_native_blender(capture.raw, capture.native_sha256, mdl,
                                           container.armature, request["scale"], self.source_pins)
        self.collector = ObservedCollector(self.proof, self.exporter_pins)

    @contextmanager
    def export_context(self):
        # This imports only the already approved, source-pinned installed addon
        # in the future Blender worker. The draft itself has not been executed.
        module = importlib.import_module("io_scene_gltf2")
        C.require(Path(module.__file__).resolve() == EXPORTER_ROOT/"__init__.py", "diagnostic_exporter_module_origin")
        with C.temporary_export_extension(module, self.bpy.context.preferences.addons.keys(), self.collector):
            yield
        C.require(self.collector.failure is None, "diagnostic_export_hook_refused_"+repr(self.collector.failure))

    def complete(self, capture):
        C.require(capture is self.capture, "diagnostic_capture_object_changed")
        Capture.recheck_selected_mdl(capture)
        result = self.collector.finish((self.bundle/"scene.glb").read_bytes())
        pins(self.runtime, C.SOURCEIO_PINS); pins(EXPORTER_ROOT, C.EXPORTER_PINS)
        result.update(format="has_Junko_crosswalk_private_diagnostic_1", diagnostic_only=True,
                      nonce=self.observer["nonce"], input_lock_sha256=self.observer["input_lock_sha256"],
                      root_revision=self.observer["root_revision"], original_source_sha256=self.request["sha256"],
                      conversion_request_sha256=digest(self.bundle/"conversion-request.json"),
                      Blender_attestation_sha256=digest(self.attestation_path), actual_factory=self.factory,
                      actual_export_settings=self.collector.actual_settings, actual_exporter_types=self.collector.actual_types,
                      production_parameters_augmented=False, HAS_adoption="UNRUN", native_solver="UNRUN")
        encoded = json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2).encode("utf-8")
        C.require(len(encoded) <= 1024*1024, "diagnostic_JSON_budget")
        folder = self.case/"diagnostics"; folder.mkdir(exist_ok=False)
        with (folder/"crosswalk-proof.json").open("xb") as stream: stream.write(encoded)
        print("STUDIO_CROSSWALK_DIAGNOSTIC_READY", json.dumps({"native_bones": len(result["bones"]), "glb_sha256": result["glb_sha256"]}), flush=True)
