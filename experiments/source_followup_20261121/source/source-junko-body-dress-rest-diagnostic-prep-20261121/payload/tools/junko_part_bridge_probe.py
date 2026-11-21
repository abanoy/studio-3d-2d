"""Root-only native part identity observation around the unchanged bridge.

This script runs only inside approved background Blender. Exact two native SHA
profiles, actual SourceIO constructor pointers and ordinary glTF export hooks
are checked. It publishes a PRIVATE diagnostic, never a product crosswalk.
"""
from pathlib import Path
import hashlib
import importlib
import json
import runpy
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import source_bone_export as B
import source_jiggle_crosswalk as C
import source_mdl_snapshot as Capture
import junko_part_rest_diagnostic as RestDiagnostic

PROFILES = {
    'd916863f801d0894009fad43c587ae630bf05556f484ebae4803734bd15c8af7': ('body', 145),
    'be03e608fc7fc0316a5441e65d01cef355e076b4eff17dd5b57fbf4defb35fdf': ('dress', 112),
}


class PartObservation(B.ExportObservation):
    def __init__(self, request, capture, mdl, container, bpy):
        role, count = PROFILES[capture.native_sha256]
        Capture.recheck_selected_mdl(capture)
        self.capture = capture
        self.original_sha256 = request['sha256']
        self.bpy = bpy
        self.role = role
        self.runtime = Path(request['sourceio']).resolve(strict=True)
        self.source_pins = B.capture_pins(self.runtime, C.SOURCEIO_PINS)
        self.exporter_pins = B.capture_pins(B.EXPORTER_ROOT, C.EXPORTER_PINS)
        factory44 = sys.modules['SourceIO.blender_bindings.models.mdl44.import_mdl'].create_armature
        factory49 = sys.modules['SourceIO.blender_bindings.models.mdl49.import_mdl'].create_armature
        C.require(factory44 is factory49 and Path(factory44.__code__.co_filename).resolve() ==
                  self.runtime / 'blender_bindings/models/mdl44/import_mdl.py',
                  'actual_factory_alias_or_origin_differs')
        C.require(getattr(container, 'mdl', None) is mdl and container.armature is not None,
                  'actual_mdl_container_armature_join')
        with RestDiagnostic.capture(C, request):
            self.proof = C.prove_native_blender(capture.raw, capture.native_sha256, mdl,
                                               container.armature, request['scale'],
                                               dict(C.SOURCEIO_PINS),
                                               C.Profile(capture.native_sha256, count))
        self.collector = B.ObservedCollector(self.proof, dict(C.EXPORTER_PINS))
        self.module = importlib.import_module('io_scene_gltf2')
        C.require(Path(self.module.__file__).resolve() == B.EXPORTER_ROOT / '__init__.py' and
                  self.module.__name__ in bpy.context.preferences.addons.keys() and
                  sys.modules.get(self.module.__name__) is self.module and
                  not hasattr(self.module, 'glTF2ExportUserExtension') and
                  not hasattr(self.module, 'glTF2ExportUserExtensions'),
                  'unsupported_exporter_extension_origin_or_registration')
        self.failure = None
        self.glb_file = None
        self.private_written = False


def prepare(request, capture, mdl, container, bpy, _jiggle_inspection):
    C.require(type(capture) is Capture.MdlCapture and capture.native_sha256 in PROFILES,
              'exact_two_selected_native_profiles_required')
    C.require(request.get('sha256') == capture.native_sha256 and request.get('scale') == 0.01905 and
              request.get('source_member') is None and request.get('appearance') is None and
              request.get('sourceio_revision') == 'fe24260b97ac03b899d9b5d4f0fd7b34772f3647',
              'standalone_default_source_profile_required')
    C.require(tuple(bpy.app.version[:2]) == (5, 1), 'Blender51_required')
    return PartObservation(request, capture, mdl, container, bpy), None


def augment_plan(planned, state, capture, original_sha256, _newline):
    observation = state['observation']
    C.require(type(observation) is PartObservation and observation.capture is capture and
              observation.original_sha256 == original_sha256 and not observation.private_written,
              'exact_private_observation_context_required')
    observed = state['observed']
    C.require(type(observed) is dict and observed.get('native_mdl_sha256') == capture.native_sha256 and
              observed.get('glb_sha256') == observation.publication_identity(),
              'complete_export_identity_proof_required')
    # Existing complete() latches optional hook failures. This diagnostic makes
    # those failures fatal, never optional success or a fabricated crosswalk.
    C.require(observation.failure is None, 'private_export_observation_failed')
    proof = dict(observed)
    proof.update(private_do_not_publish=True, diagnostic_part_role=observation.role,
                 native_profile_promotion=False, HAS_runtime_binding='unattempted',
                 native_simulation=False, follow_controller_applied=False)
    raw = json.dumps(proof, ensure_ascii=True, separators=(',', ':'), allow_nan=False).encode('ascii') + b'\n'
    C.require(len(raw) <= 128 * 1024 + 1024, 'bounded_private_proof_required')
    output = observation.glb_file[0].parent / 'PRIVATE_part_export_binding.json'
    with output.open('xb') as stream:
        stream.write(raw)
    observation.private_written = True
    print('JUNKO_PART_EXPORT_IDENTITY ' + json.dumps({
        'role': observation.role, 'bones': len(observation.proof.bindings),
        'native_sha256': capture.native_sha256, 'glb_sha256': proof['glb_sha256'],
        'private_proof_sha256': hashlib.sha256(raw).hexdigest(),
        'runtime_binding_qualified': False, 'native_simulation': False,
    }, separators=(',', ':')), flush=True)
    # Leave ordinary jiggle/report publication untouched. This scoped draft
    # is deliberately absent from product native_parameters/source crosswalks.
    return {**planned, 'crosswalk_note_bytes': None}


def main():
    original_prepare = B.prepare
    original_augment = B.augment_plan
    B.prepare = prepare
    B.augment_plan = augment_plan
    try:
        runpy.run_path(str(HERE / 'blender_source_bridge.py'), run_name='__main__')
    finally:
        B.prepare = original_prepare
        B.augment_plan = original_augment


if __name__ == '__main__':
    main()
