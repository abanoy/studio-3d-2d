"""Narrow SourceIO/exporter admission for an optional inactive Junko crosswalk.

Only this qualified SHA/default scale/profile installs read-only export hooks.
Other inputs keep the original export call. Identity changes after observation
escape all optional fallback paths. Nothing writes a sidecar or applies physics.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import importlib
from pathlib import Path
import sys

import source_jiggle_crosswalk as C
import source_bone_metadata as M
import source_mdl_snapshot as Capture

EXPORTER_ROOT = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\5.1\scripts\addons_core\io_scene_gltf2")
EXPLICIT_KWARGS = {"export_skins": True, "export_armature_object_remove": False,
                   "export_rest_position_armature": True, "export_hierarchy_flatten_bones": False,
                   "export_hierarchy_flatten_objs": False, "export_leaf_bone": False,
                   "export_gpu_instances": False, "export_use_gltfpack": False,
                   "export_draco_mesh_compression_enable": False, "export_def_bones": False}


@dataclass(frozen=True)
class PinnedFile:
    path: Path
    identity: tuple
    sha256: str


def _read_pin(path):
    # Every file is a fixed source pin; no tree traversal or arbitrary extras.
    before = path.stat()
    C.require(path.is_file() and 0 <= before.st_size <= 4*1024*1024, "runtime_pin_file_domain")
    raw = path.read_bytes(); after = path.stat()
    signature = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
    if signature(before) != signature(after) or len(raw) != before.st_size:
        raise C.SourceIdentityError("runtime_source_changed_during_capture")
    return PinnedFile(path, signature(after), hashlib.sha256(raw).hexdigest())


def capture_pins(root, expected):
    rows = tuple(_read_pin(root/name) for name in expected)
    C.require({name: row.sha256 for name, row in zip(expected, rows)} == expected,
              "runtime_source_pins_unsupported")
    return rows


def recheck_pins(rows):
    for expected in rows:
        try:
            actual = _read_pin(expected.path)
        except (OSError, C.CrosswalkError) as error:
            raise C.SourceIdentityError("observed_runtime_source_no_longer_verifiable") from error
        if actual != expected:
            raise C.SourceIdentityError("observed_runtime_source_identity_changed")


class ObservedCollector(C.ExportCollector):
    def gather_gltf_extensions_hook(self, gltf, export_settings):
        super().gather_gltf_extensions_hook(gltf, export_settings)
        if self.failure is not None: return
        def verify_types():
            prefix = "io_scene_gltf2.io.com.gltf2_io."
            C.require(type(gltf).__module__+"."+type(gltf).__name__ == prefix+"Gltf",
                      "unsupported_exporter_flat_Gltf_type")
            for key, expected in (("nodes", "Node"), ("skins", "Skin"), ("scenes", "Scene"), ("meshes", "Mesh")):
                C.require(all(type(item).__module__+"."+type(item).__name__ == prefix+expected
                              for item in getattr(gltf, key)), "unsupported_exporter_flat_"+key+"_type")
        self._hook("types", verify_types)


class ExportObservation:
    def __init__(self, request, capture, mdl, container, bpy):
        Capture.recheck_selected_mdl(capture)
        self.capture = capture; self.original_sha256 = request["sha256"]; self.bpy = bpy
        self.runtime = Path(request["sourceio"]).resolve(strict=True)
        self.source_pins = capture_pins(self.runtime, C.SOURCEIO_PINS)
        self.exporter_pins = capture_pins(EXPORTER_ROOT, C.EXPORTER_PINS)
        factory44 = sys.modules["SourceIO.blender_bindings.models.mdl44.import_mdl"].create_armature
        factory49 = sys.modules["SourceIO.blender_bindings.models.mdl49.import_mdl"].create_armature
        C.require(factory44 is factory49 and Path(factory44.__code__.co_filename).resolve() ==
                  self.runtime/"blender_bindings/models/mdl44/import_mdl.py", "actual_factory_alias_or_origin_differs")
        C.require(getattr(container, "mdl", None) is mdl and container.armature is not None,
                  "actual_mdl_container_armature_join")
        self.proof = C.prove_native_blender(capture.raw, capture.native_sha256, mdl, container.armature,
                                           request["scale"], dict(C.SOURCEIO_PINS))
        self.collector = ObservedCollector(self.proof, dict(C.EXPORTER_PINS))
        self.module = importlib.import_module("io_scene_gltf2")
        C.require(Path(self.module.__file__).resolve() == EXPORTER_ROOT/"__init__.py" and
                  self.module.__name__ in bpy.context.preferences.addons.keys() and
                  sys.modules.get(self.module.__name__) is self.module and
                  not hasattr(self.module, "glTF2ExportUserExtension") and
                  not hasattr(self.module, "glTF2ExportUserExtensions"), "unsupported_exporter_extension_origin_or_registration")
        self.failure = None; self.glb_file = None

    def recheck(self):
        Capture.recheck_selected_mdl(self.capture)
        recheck_pins(self.source_pins); recheck_pins(self.exporter_pins)

    @contextmanager
    def export_context(self):
        self.recheck()
        # Exporter's callback dispatcher can swallow hook failures. The collector
        # latches them and finish outside bpy refuses metadata without re-export.
        with C.temporary_export_extension(self.module, self.bpy.context.preferences.addons.keys(), self.collector):
            yield

    def export(self, operator, arguments):
        """Call the ordinary exporter exactly once; registration is optional."""
        self.recheck()
        registration = C.temporary_export_extension(self.module, self.bpy.context.preferences.addons.keys(), self.collector)
        try:
            registration.__enter__()
        except C.SourceIdentityError:
            raise
        except C.CrosswalkError:
            self.failure = "proof_unavailable"
            return operator(**arguments)
        try:
            return operator(**arguments, **EXPLICIT_KWARGS)
        finally:
            # Preserve real export exceptions and never retry the operator.
            error = sys.exc_info()
            try:
                registration.__exit__(*error)
            except C.SourceIdentityError:
                raise
            except C.CrosswalkError:
                self.failure = "proof_unavailable"

    def complete(self, path):
        self.recheck()
        if self.failure is not None: return None
        try:
            C.require(20 <= path.stat().st_size <= 128*1024*1024, "optional_GLB_read_budget")
            with path.open("rb") as stream: raw = stream.read(128*1024*1024+1)
            result = self.collector.finish(raw)
        except C.SourceIdentityError:
            raise
        except (C.CrosswalkError, OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
            self.failure = "proof_unavailable"
            return None
        self.glb_file = _read_glb_identity(path, result["glb_sha256"])
        self.recheck()
        return result

    def publication_identity(self):
        self.recheck()
        if self.glb_file is not None:
            path, expected = self.glb_file
            _read_glb_identity(path, expected)
            return expected
        return None


def _read_glb_identity(path, expected):
    # No second model copy or sidecar; hash the final ordinary GLB in place.
    try:
        before = path.stat()
        with path.open("rb") as stream: actual = hashlib.file_digest(stream, "sha256").hexdigest()
        after = path.stat()
    except OSError as error:
        raise C.SourceIdentityError("observed_GLB_no_longer_verifiable") from error
    if (before.st_size, before.st_mtime_ns, before.st_dev, before.st_ino) != \
            (after.st_size, after.st_mtime_ns, after.st_dev, after.st_ino) or actual != expected:
        raise C.SourceIdentityError("observed_GLB_identity_changed")
    return path, expected


def prepare(request, capture, mdl, container, bpy, jiggle_inspection):
    """Return an eligible observation or a bounded optional omission code."""
    if type(capture) is not Capture.MdlCapture or capture.native_sha256 != C.JUNKO_SHA256:
        return None, None
    # Raw identity must be checked even if a later profile/pin gate refuses.
    Capture.recheck_selected_mdl(capture)
    if request.get("scale") != M.SCALE or request.get("appearance") is not None or request.get("source_member") is not None:
        return None, "unsupported_profile"
    if request.get("sourceio_revision") != M.J.SOURCEIO_REVISION:
        return None, "source_pins_unsupported"
    if jiggle_inspection.get("state") != "retained": return None, "jiggle_not_retained"
    try:
        return ExportObservation(request, capture, mdl, container, bpy), None
    except (Capture.SourceIdentityError, C.SourceIdentityError):
        raise
    except (C.CrosswalkError, OSError, ValueError, TypeError, KeyError, AttributeError, ImportError):
        return None, "source_pins_unsupported"


def augment_plan(planned, state, capture, original_sha256, newline):
    if state is None: return planned
    observation = state["observation"]
    if observation is not None and (observation.capture is not capture or observation.original_sha256 != original_sha256):
        raise C.SourceIdentityError("crosswalk_observation_context_identity_changed")
    glb_sha256 = observation.publication_identity() if observation is not None else None
    if state["observed"] is None:
        return {**planned, "crosswalk_note_bytes": M.omission(state["reason"] or "proof_unavailable")}
    return M.plan_report(planned, state["observed"], expected_original_sha256=observation.original_sha256,
                         expected_native_sha256=capture.native_sha256,
                         expected_glb_sha256=glb_sha256, newline=newline)
