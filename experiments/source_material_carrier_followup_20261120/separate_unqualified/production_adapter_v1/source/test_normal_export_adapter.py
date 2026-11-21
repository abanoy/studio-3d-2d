"""Pure finalization seam tests: synthetic VVD/GLB and fake observed bones.

Uses the unchanged real normal corrector/contracts, never a native asset,
Blender, NumPy, source importer, operator or file output. Fake bone evidence
stands in only for the separately qualified raw collector; it proves no host API.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V = load('_has_adapter_test_vvd', ROOT / 'experiments/native_normal_carrier_strategy_20261117/vvd_normals.py')
with patch.dict(sys.modules, {'vvd_normals': V}):
    C = load('_has_adapter_test_corrector', ROOT / 'experiments/native_normal_carrier_strategy_20261117/normal_identity_carrier.py')
A = load('_has_normal_finalizer_under_test', HERE / 'normal_export_adapter.py')


def sha(raw): return hashlib.sha256(raw).hexdigest()


def native_fixture():
    normals = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (-0.0, 0.0, 1.0))
    raw = bytearray(struct.pack('<4s15I', b'IDSV', 4, 17, 1, 3, *([0] * 7), 0, 0, 64, 0) + bytes(3 * 48))
    for index, normal in enumerate(normals): struct.pack_into('<3f', raw, 64 + index * 48 + 28, *normal)
    raw = bytes(raw)
    return C.source_from_vvd(raw, sha(raw), 17)


def carrier_fixture(bone_count=69):
    binary, views, accessors = bytearray(), [], []
    def add(raw, component, kind, count):
        binary.extend(bytes(-len(binary) % 4)); offset = len(binary); binary.extend(raw)
        views.append(dict(buffer=0, byteOffset=offset, byteLength=len(raw)))
        accessors.append(dict(bufferView=len(views) - 1, componentType=component, count=count, type=kind))
        return len(accessors) - 1
    def f32(values): return struct.pack('<' + 'f' * len(values), *values)
    attrs = dict(POSITION=add(f32([0., 0., 0., 1., 0., 0., 0., 1., 0.]), 5126, 'VEC3', 3),
        NORMAL=add(f32([0., 1., 0.] * 3), 5126, 'VEC3', 3),
        TEXCOORD_0=add(f32([0., 0., 1., 0., 0., 1.]), 5126, 'VEC2', 3),
        JOINTS_0=add(bytes([0, 0, 0, 0] * 3), 5121, 'VEC4', 3),
        WEIGHTS_0=add(f32([1., 0., 0., 0.] * 3), 5126, 'VEC4', 3))
    attrs[C.CARRIER] = add(C.encode_ids([0, 1, 2]), 5126, 'SCALAR', 3)
    indices = add(struct.pack('<3H', 0, 1, 2), 5123, 'SCALAR', 3)
    identity = [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]
    inverse = add(f32(identity * bone_count), 5126, 'MAT4', bone_count)
    nodes = [dict(name='mesh', mesh=0, skin=0), dict(name='armature', children=[2])]
    for index in range(bone_count):
        node = dict(name='bone_' + str(index), translation=[0, 1, 0])
        if index + 1 < bone_count: node['children'] = [index + 3]
        nodes.append(node)
    document = dict(asset=dict(version='2.0', generator='synthetic finalizer fixture'),
        buffers=[dict(byteLength=len(binary))], bufferViews=views, accessors=accessors,
        meshes=[dict(name='synthetic_mesh', primitives=[dict(attributes=attrs, indices=indices, mode=4, material=0)])],
        nodes=nodes, skins=[dict(joints=list(range(2, 2 + bone_count)), inverseBindMatrices=inverse, skeleton=2)],
        scenes=[dict(nodes=[0, 1])], scene=0,
        materials=[dict(pbrMetallicRoughness=dict(baseColorFactor=[0.2, 0.3, 0.4, 1.0]))])
    return C.pack_glb(document, bytes(binary))


def bone_proof(raw, count=69):
    doc, _ = C.parse_glb(raw)
    return dict(format='has_source_export_crosswalk_draft_1', status='observed_inactive',
        glb_sha256=sha(raw), glb_bytes=len(raw), native_mdl_sha256='2' * 64, native_bone_count=count,
        bones=[dict(native_index=index, native_parent_index=index - 1, native_name='bone_' + str(index),
                    gltf_node_index=index + 2, skin_memberships=[dict(skin_index=0, joint_slot=index)])
               for index in range(count)],
        armature_gltf_node_index=1, selected_scene=0, selected_scene_roots=doc['scenes'][0]['nodes'],
        scene_container_sha256=sha(json.dumps(dict(scene=0, scenes=doc['scenes']), sort_keys=True).encode()),
        target_skin_mesh_nodes=[dict(skin_index=0, reachable_skinned_mesh_nodes=[0])],
        applied=False, native_simulation=False, HAS_runtime_binding='unattempted', export_extras=False)


class Bones:
    def __init__(self, raw, events, proof=None):
        self.raw, self.events = raw, events
        self.proof = bone_proof(raw) if proof is None else proof
        self.final = copy.deepcopy(C.parse_glb(raw)[0])
        self.failure = None
        self.finish_calls = 0
    def finish(self, raw):
        self.events.append('bones'); self.finish_calls += 1
        if self.failure: raise ValueError('synthetic latched bone failure')
        if raw != self.raw: raise ValueError('must finish bones against raw bytes')
        return copy.deepcopy(self.proof)


class Corrector:
    """Log orchestration while real frozen functions enforce content."""
    def __init__(self, events):
        self.events = events
        self.preserve_result = self.word_result = True
        self.output_change = None
        self.bypass_preservation = self.bypass_words = False
    def __getattr__(self, name): return getattr(C, name)
    def correct_glb(self, *args, **kwargs):
        self.events.append('correct')
        raw, report = C.correct_glb(*args, **kwargs)
        if self.output_change:
            doc, binary = C.parse_glb(raw); self.output_change(doc)
            raw = C.pack_glb(doc, binary); report = dict(report, output_sha256=sha(raw))
        return raw, report
    def preservation_contract(self, before, after):
        self.events.append('preserve')
        if not self.bypass_preservation: C.preservation_contract(before, after)
        return self.preserve_result
    def corrected_normal_contract(self, output, native, relation, axes):
        self.events.append('words')
        if not self.bypass_words: C.corrected_normal_contract(output, native, relation, axes)
        return self.word_result


class FinalizerTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.raw, self.native = carrier_fixture(), native_fixture()
        self.relation, self.axes, self.ids = {(0, 0): [1, 2, 3]}, (1, 3, -2), [1, 2, 3]
        self.bones, self.corrector = Bones(self.raw, self.events), Corrector(self.events)

    def finalize(self, **changes):
        kwargs = dict(correction_module=self.corrector, native=self.native, carrier_sha256=sha(self.raw),
            expected_source_ids=self.ids, independent_relation=self.relation, axes=self.axes,
            expected_vvd_sha256=self.native.source_sha256, bone_collector=self.bones)
        kwargs.update(changes)
        return A.finalize_native_normals(self.raw, **kwargs)

    def measured(self, **changes):
        report = dict(format='has_corrected_native_normal_measurement_1', measured=True,
            source_normal_metric='raw_unnormalized_euclidean_vector_distance',
            source_normal_threshold=2e-5, source_normal_max_euclidean_error=0.0,
            passed=True, source_points=3, exported_normal_rows=3, compared_components=9)
        report.update(changes)
        def measure(output, native, relation, axes):
            self.events.append('measure')
            self.assertIs(native, self.native); self.assertEqual(relation, self.relation); self.assertEqual(tuple(axes), self.axes)
            self.assertTrue(C.corrected_normal_contract(output, native, relation, axes))
            return dict(report)
        return measure

    def test_real_correction_and_contracts_rebind_69_bones_to_final_hash_without_mutation(self):
        before_proof, before_final = copy.deepcopy(self.bones.proof), copy.deepcopy(self.bones.final)
        before_relation, before_ids = copy.deepcopy(self.relation), list(self.ids)
        output, report, rebound = self.finalize()
        self.assertNotEqual(output, self.raw)
        self.assertTrue(C.preservation_contract(self.raw, output))
        self.assertTrue(C.corrected_normal_contract(output, self.native, self.relation, self.axes))
        self.assertEqual(self.events[:4], ['bones', 'correct', 'preserve', 'words'])
        self.assertEqual(self.bones.finish_calls, 1)
        self.assertEqual(rebound['glb_sha256'], sha(output)); self.assertEqual(rebound['glb_bytes'], len(output))
        self.assertNotEqual(rebound['glb_sha256'], before_proof['glb_sha256'])
        self.assertEqual(rebound['bones'], before_proof['bones']); self.assertEqual(rebound['native_bone_count'], 69)
        self.assertIsNot(rebound, self.bones.proof); self.assertIsNot(rebound['bones'], self.bones.proof['bones'])
        for key, value in before_proof.items():
            if key not in ('glb_sha256', 'glb_bytes'): self.assertEqual(rebound[key], value)
        self.assertIsInstance(rebound['normal_finalization'], dict)
        self.assertEqual(self.bones.proof, before_proof); self.assertEqual(self.bones.final, before_final)
        self.assertEqual(self.relation, before_relation); self.assertEqual(self.ids, before_ids)
        encoded = json.dumps(report, allow_nan=False)
        self.assertNotIn('bone_68', encoded); self.assertNotIn('skin_memberships', encoded)
        self.assertNotIn('component_bytes', encoded); self.assertLess(len(encoded), 16384)

    def test_bone_raw_proof_is_completed_before_normal_correction_and_measured_after_contracts(self):
        output, _, _ = self.finalize(measure_corrected=self.measured())
        self.assertEqual(self.events, ['bones', 'correct', 'preserve', 'words', 'measure'])
        self.assertNotEqual(sha(output), sha(self.raw))

    def test_latched_bone_failure_cannot_fall_back_to_unproved_normal_publication(self):
        self.bones.failure = ('preflight', 'synthetic failure')
        with self.assertRaises(ValueError): self.finalize()
        self.assertEqual(self.events, ['bones'])

    def test_raw_bone_checksum_or_length_mismatch_refuses_before_correction(self):
        for field, value in (('glb_sha256', '0' * 64), ('glb_bytes', len(self.raw) + 1)):
            with self.subTest(field=field):
                bones = Bones(self.raw, [], dict(self.bones.proof, **{field: value}))
                with self.assertRaises(ValueError): self.finalize(bone_collector=bones)
        self.assertNotIn('correct', self.events)

    def test_raw_bone_status_native_count_or_catalogue_ambiguity_refuses(self):
        for edit in ('status', 'count', 'duplicate', 'bool_index', 'noninactive'):
            with self.subTest(edit=edit):
                proof = copy.deepcopy(self.bones.proof)
                if edit == 'status': proof['status'] = 'proof_unavailable'
                elif edit == 'count': proof['native_bone_count'] = 68
                elif edit == 'duplicate': proof['bones'][1]['native_index'] = 0
                elif edit == 'bool_index': proof['bones'][0]['gltf_node_index'] = True
                else: proof['applied'] = True
                with self.assertRaises(ValueError): self.finalize(bone_collector=Bones(self.raw, [], proof))

    def test_existing_finalization_namespace_is_never_overwritten(self):
        proof = dict(self.bones.proof, normal_finalization={'owner': 'already present'})
        with self.assertRaises(ValueError): self.finalize(bone_collector=Bones(self.raw, [], proof))

    def test_wrong_carrier_or_native_hash_and_unverified_relation_refuse(self):
        cases = (dict(carrier_sha256='0' * 64), dict(expected_vvd_sha256='0' * 64),
                 dict(independent_relation={(0, 0): [2, 1, 3]}), dict(expected_source_ids=[1, 2]))
        for changes in cases:
            with self.subTest(changes=list(changes)):
                with self.assertRaises(ValueError): self.finalize(**changes)

    def test_preservation_and_word_contract_must_return_exact_true(self):
        for field, value in (('preserve_result', False), ('preserve_result', 1), ('word_result', False), ('word_result', 1)):
            with self.subTest(field=field, value=value):
                corrector = Corrector([]); setattr(corrector, field, value)
                with self.assertRaises(ValueError): self.finalize(correction_module=corrector)

    def test_type_only_scene_node_or_skin_drift_cannot_rebind_even_if_contract_facade_claims_true(self):
        for change in (lambda doc: doc.update(scene=0.0),
                       lambda doc: doc['nodes'][2].update(translation=[0.0, 1, 0]),
                       lambda doc: doc['skins'][0].update(skeleton=2.0)):
            with self.subTest(change=change):
                corrector = Corrector([]); corrector.output_change = change
                corrector.bypass_preservation = corrector.bypass_words = True
                with self.assertRaises(ValueError): self.finalize(correction_module=corrector)

    def test_declared_measurement_must_be_raw_euclidean_and_original_exact_threshold(self):
        for change in (dict(measured=False), dict(source_normal_metric='max_component'),
                       dict(source_normal_threshold=2.1e-5), dict(source_normal_threshold=True),
                       dict(source_normal_max_euclidean_error=float('nan')), dict(passed=True, source_normal_max_euclidean_error=3e-5)):
            with self.subTest(change=change):
                with self.assertRaises(ValueError): self.finalize(measure_corrected=self.measured(**change))

    def test_two_subthreshold_component_errors_do_not_bypass_original_euclidean_gate(self):
        error = math.sqrt(2 * (1.5e-5) ** 2)
        self.assertGreater(error, 2e-5)
        with self.assertRaises(ValueError):
            self.finalize(measure_corrected=self.measured(passed=False, source_normal_max_euclidean_error=error))

    def test_measurement_source_and_exported_component_counts_cannot_be_fabricated(self):
        for change in (dict(source_points=2), dict(exported_normal_rows=2), dict(compared_components=8), dict(passed=1)):
            with self.subTest(change=change):
                with self.assertRaises(ValueError): self.finalize(measure_corrected=self.measured(**change))


    def test_default_measurer_checks_raw_vector_distance_not_each_component(self):
        corrected, _ = C.correct_glb(self.raw, self.native, sha(self.raw), self.ids, self.axes,
            expected_native_sha256=self.native.source_sha256, verified_primitive_identity_order=self.relation)
        document, binary = C.parse_glb(corrected)
        binary = bytearray(binary)
        normal = document['accessors'][document['meshes'][0]['primitives'][0]['attributes']['NORMAL']]
        view = document['bufferViews'][normal['bufferView']]
        offset = view.get('byteOffset', 0) + normal.get('byteOffset', 0)
        # The first independent native direction is +X. Change its two zero
        # components by nearest F32 values; each is below the historical bound.
        struct.pack_into('<3f', binary, offset, 1.0, 1.5e-5, 1.5e-5)
        changed = C.pack_glb(document, bytes(binary))
        actual = struct.unpack_from('<3f', binary, offset)
        expected = math.sqrt(actual[1] ** 2 + actual[2] ** 2)
        self.assertLess(max(abs(actual[1]), abs(actual[2])), 2e-5)
        self.assertGreater(expected, 2e-5)
        report = A._measure_corrected(C, changed, self.native, self.relation, self.axes)
        self.assertFalse(report['passed'])
        self.assertEqual(report['source_normal_max_euclidean_error'], expected)
        self.assertEqual((report['source_points'], report['exported_normal_rows'], report['compared_components']), (3, 3, 9))

    def test_corrector_cannot_mutate_the_observed_raw_bone_proof_before_rebind(self):
        proof = copy.deepcopy(self.bones.proof)
        class SameProofBones:
            def finish(inner, raw):
                self.assertIs(raw, self.raw)
                return proof
        class MutatingCorrector(Corrector):
            def correct_glb(inner, *args, **kwargs):
                output, report = super().correct_glb(*args, **kwargs)
                proof['bones'][0]['gltf_node_index'] = 999
                return output, report
        with self.assertRaises(A.Refusal) as caught:
            self.finalize(bone_collector=SameProofBones(), correction_module=MutatingCorrector([]))
        self.assertEqual(str(caught.exception), 'RAW_BONE_PROOF_MUTATED')
        self.assertEqual(caught.exception.summary['phase'], 'INDEPENDENT_PRESERVATION_AND_WORD_CONTRACTS')

    def test_measurement_cannot_mutate_the_frozen_gather_relation(self):
        def mutation(output, native, relation, axes):
            relation[(0, 0)] = (2, 1, 3)
            return dict(format='has_corrected_native_normal_measurement_1', measured=True,
                source_normal_metric='raw_unnormalized_euclidean_vector_distance',
                source_normal_threshold=2e-5, source_normal_max_euclidean_error=0.0, passed=True,
                source_points=3, exported_normal_rows=3, compared_components=9)
        original = copy.deepcopy(self.relation)
        with self.assertRaises(A.Refusal) as caught:
            self.finalize(measure_corrected=mutation)
        self.assertEqual(str(caught.exception), 'INDEPENDENT_RELATION_MUTATED')
        self.assertEqual(self.relation, original)


class ProfileAndCompositionTests(unittest.TestCase):
    def test_only_exact_known_profile_is_eligible_and_unknowns_keep_legacy_route(self):
        request = dict(sourceio_revision=A.SOURCEIO_REVISION, scale=.01905, appearance=None, source_member=None)
        self.assertTrue(A.eligible_profile(request, A.KNOWN_MDL_SHA256))
        for change in (dict(scale=1.0), dict(scale=True), dict(sourceio_revision='other'),
                       dict(appearance={}), dict(source_member='other.mdl')):
            with self.subTest(change=change):
                self.assertFalse(A.eligible_profile(dict(request, **change), A.KNOWN_MDL_SHA256))
        self.assertFalse(A.eligible_profile(request, '0' * 64))
        self.assertFalse(A.eligible_profile(None, A.KNOWN_MDL_SHA256))

    def test_actual_identity_frame_requires_two_distinct_mesh_worlds_and_same_armature_world(self):
        def identity(): return [[float(row == column) for column in range(4)] for row in range(4)]
        def container():
            return types.SimpleNamespace(objects=[types.SimpleNamespace(matrix_world=identity()),
                types.SimpleNamespace(matrix_world=identity())], armature=types.SimpleNamespace(matrix_world=identity()))
        actual = container(); frame = A.admit_identity_normal_frame(actual)
        self.assertEqual(frame['signed_axis_permutation'], [1, 3, -2])
        self.assertFalse(frame['source_unit_conversion_changed']); self.assertFalse(frame['six_foot_normalization_applied'])
        for edit in ('object', 'armature', 'duplicate', 'integer'):
            with self.subTest(edit=edit):
                actual = container()
                if edit == 'object': actual.objects[0].matrix_world[0][3] = .001
                elif edit == 'armature': actual.armature.matrix_world[0][0] = 2.0
                elif edit == 'duplicate': actual.objects[1] = actual.objects[0]
                else: actual.objects[1].matrix_world[0][0] = 1
                with self.assertRaises(ValueError): A.admit_identity_normal_frame(actual)

    def composite(self, *, collide=False):
        events = []
        class Latch:
            failed = False
            def check(self):
                if self.failed: raise ValueError('synthetic H latch')
        class Normal:
            def __init__(self, surface, admissions, np, resources, point_admission, options):
                self.normal_args = (surface, admissions, np, resources, point_admission, options)
                self.normal_events, self.h_pre_count = events, 0
                self.latch, self.finished = Latch(), False
                events.append(('Hinit', self))
            def pre_export_hook(self, settings):
                if settings.get('gltf_user_extensions') != [self]: raise ValueError('H sole self')
                self.h_pre_count += 1; events.append(('Hpre', self))
                self.latch.check()
            def finish(self, raw, expected_sha):
                self.latch.check()
                if self.h_pre_count != 1: raise ValueError('H preflight missing')
                self.finished = True; events.append(('Hfinish', self))
                return ('normal-complete', raw, expected_sha)
        class Bone:
            def __init__(self, proof, source_pins):
                self.bone_args, self.failure, self.b_pre_count, self.b_finish_count = (proof, source_pins), None, 0, 0
                events.append(('Binit', self))
                if collide: self.finished = True
            def pre_export_hook(self, settings):
                if self.failure is not None: return
                if settings.get('gltf_user_extensions') != [self]: raise ValueError('B sole self')
                self.b_pre_count += 1; events.append(('Bpre', self))
            def finish(self, raw):
                if self.failure is not None: raise ValueError('synthetic bone latch')
                self.b_finish_count += 1; events.append(('Bfinish', self))
                return dict(fake_raw_bone_result_only=True, input=raw)
        combined = A.compose_session_class(types.SimpleNamespace(ExportHookSession=Normal), Bone)
        args = tuple(object() for _ in range(6)); proof, pins = object(), object()
        session = combined(*args, bone_proof=proof, exporter_source_pins=pins)
        return session, events, args, proof, pins

    def test_single_composite_self_initializes_both_and_requires_H_completion_before_one_shot_bones(self):
        session, events, args, proof, pins = self.composite()
        self.assertEqual(session.normal_args, args); self.assertEqual(session.bone_args, (proof, pins))
        self.assertEqual([name for name, _ in events], ['Hinit', 'Binit'])
        self.assertTrue(all(value is session for _, value in events))
        settings = dict(gltf_user_extensions=[session])
        session.pre_export_hook(settings)
        self.assertEqual((session.h_pre_count, session.b_pre_count), (1, 1))
        with self.assertRaises(ValueError): session.finish_bones(b'synthetic raw')
        result = session.finish(b'synthetic raw', 'known synthetic pin')
        self.assertEqual(result, ('normal-complete', b'synthetic raw', 'known synthetic pin'))
        bone_result = session.finish_bones(b'synthetic raw')
        self.assertTrue(bone_result['fake_raw_bone_result_only']); self.assertEqual(session.b_finish_count, 1)
        with self.assertRaises(ValueError): session.finish_bones(b'synthetic raw')
        self.assertEqual(session.b_finish_count, 1)
        self.assertTrue(all(value is session for _, value in events))

    def test_both_failure_latches_and_wrong_extension_self_refuse(self):
        session, _, _, _, _ = self.composite(); session.latch.failed = True
        with self.assertRaises(ValueError): session.pre_export_hook(dict(gltf_user_extensions=[session]))
        self.assertEqual(session.b_pre_count, 0)
        session, _, _, _, _ = self.composite(); session.failure = ('bone', 'latched')
        with self.assertRaises(ValueError): session.pre_export_hook(dict(gltf_user_extensions=[session]))
        session, _, _, _, _ = self.composite()
        with self.assertRaises(ValueError): session.pre_export_hook(dict(gltf_user_extensions=[object()]))
        session, _, _, _, _ = self.composite()
        session.pre_export_hook(dict(gltf_user_extensions=[session])); session.finish(b'raw', 'pin')
        session.failure = ('bone', 'late failure')
        with self.assertRaises(ValueError): session.finish_bones(b'raw')
        self.assertEqual(session.b_finish_count, 0)

    def test_base_state_collision_refuses_instead_of_overwriting_H_lifecycle(self):
        with self.assertRaises(ValueError): self.composite(collide=True)


if __name__ == '__main__':
    unittest.main()
