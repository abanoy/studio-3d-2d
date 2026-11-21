"""Pure candidate seam for one qualified Source NORMAL/bone finalization.

No Blender/SourceIO import, files, operator, runtime launch or adoption occurs.
The caller authenticates dependencies, native inputs, actual frame and gather
relation. Unknown production profiles retain the existing conversion path.
"""
import copy
import hashlib
import json
import math
import re
import types

MAX_GLB = 128 * 1024 * 1024
MAX_POINTS = 200000
MAX_PROOF = 512 * 1024
THRESHOLD = 2e-5
METRIC = 'raw_unnormalized_euclidean_vector_distance'
KNOWN_MDL_SHA256 = '8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'
SOURCEIO_REVISION = 'fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
PROVENANCE = 'normal_finalization'


class Refusal(ValueError):
    def __init__(self, code, summary=None):
        super().__init__(code)
        self.summary = dict(summary or {})


def need(value, code):
    if not value:
        raise Refusal(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def compact(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                     allow_nan=False).encode('ascii')
    need(len(raw) <= MAX_PROOF, 'NORMAL_BONE_PROOF_BUDGET')
    return raw


def eligible_profile(request, native_mdl_sha256):
    """A false return means use the unchanged legacy importer; no IO occurs."""
    return (type(request) is dict and type(native_mdl_sha256) is str and
            native_mdl_sha256 == KNOWN_MDL_SHA256 and
            request.get('sourceio_revision') == SOURCEIO_REVISION and
            type(request.get('scale')) is float and request['scale'] == .01905 and
            request.get('appearance') is None and request.get('source_member') is None)


def admit_identity_normal_frame(container):
    """Reuse the qualified known-family pre-export world-frame boundary."""
    identity = tuple(tuple(float(row == column) for column in range(4)) for row in range(4))
    objects = tuple(container.objects)
    need(len(objects) == 2 and len({id(obj) for obj in objects}) == 2,
         'NORMAL_FRAME_TWO_ACTUAL_OBJECTS_REQUIRED')
    for obj in (*objects, container.armature):
        matrix = tuple(tuple(row) for row in obj.matrix_world)
        need(len(matrix) == 4 and all(len(row) == 4 for row in matrix) and
             all(type(value) is float for row in matrix for value in row) and matrix == identity,
             'NORMAL_FRAME_NONIDENTITY_WORLD_UNQUALIFIED')
    return dict(format='has_actual_identity_source_to_yup_normal_frame_1', mesh_world_identity=True,
        armature_world_identity=True, mesh_count=2, export_yup=True, export_apply=False,
        signed_axis_permutation=[1, 3, -2],
        source_coordinate_policy='sourceio_mdl49_standalone_01905_identity_standard_vtx7_1',
        source_unit_conversion_changed=False, six_foot_normalization_applied=False)


def compose_session_class(hook_module, bone_collector_class):
    """One self/constructor satisfies both collectors' sole-extension checks.

    Dependencies must be authenticated by the actual host. H.install owns the
    only registration. Do not also enter the old bone registration context.
    """
    normal_class = hook_module.ExportHookSession
    need(type(normal_class) is type and type(bone_collector_class) is type and
         not issubclass(bone_collector_class, normal_class), 'COMPOSITE_BASE_CLASSES')

    class CombinedExportSession(normal_class, bone_collector_class):
        def __init__(self, surface, admissions, np, resources, point_admission, expected_options,
                     *, bone_proof, exporter_source_pins):
            normal_class.__init__(self, surface, admissions, np, resources, point_admission, expected_options)
            normal_state = dict(self.__dict__)
            bone_collector_class.__init__(self, bone_proof, exporter_source_pins)
            need(all(key in self.__dict__ and self.__dict__[key] is value
                     for key, value in normal_state.items()), 'COMPOSITE_COLLECTOR_STATE_COLLISION')
            self._production_bone_finish_attempted = False

        def check_both_latches(self):
            self.latch.check()
            need(self.failure is None, 'COMPOSITE_BONE_FAILURE_LATCHED')

        def pre_export_hook(self, settings):
            normal_class.pre_export_hook(self, settings)
            self.latch.check()
            bone_collector_class.pre_export_hook(self, settings)
            self.check_both_latches()

        def finish_bones(self, raw_carrier):
            """For SimpleNamespace(finish=session.finish_bones), no new export."""
            need(self.finished is True and not self._production_bone_finish_attempted,
                 'COMPOSITE_RAW_NORMAL_COMPLETION_OR_REPLAY')
            self._production_bone_finish_attempted = True
            self.check_both_latches()
            result = bone_collector_class.finish(self, raw_carrier)
            self.check_both_latches()
            return result

    return CombinedExportSession


def _relation(expected_source_ids, independent_relation, axes):
    need(type(axes) in (tuple, list) and len(axes) == 3 and
         all(type(value) is int for value in axes) and tuple(axes) == (1, 3, -2),
         'ONLY_ACTUAL_IDENTITY_TO_YUP_FRAME')
    need(type(expected_source_ids) in (list, tuple) and 0 < len(expected_source_ids) <= MAX_POINTS and
         all(type(value) is int and 1 <= value <= MAX_POINTS for value in expected_source_ids) and
         len(set(expected_source_ids)) == len(expected_source_ids), 'INDEPENDENT_SOURCE_IDS_REQUIRED')
    expected = set(expected_source_ids)
    need(type(independent_relation) is dict and 0 < len(independent_relation) <= 64,
         'INDEPENDENT_PRIMITIVE_RELATION_REQUIRED')
    result = {}
    flat = []
    for key, values in independent_relation.items():
        need(type(key) is tuple and len(key) == 2 and all(type(value) is int and 0 <= value < 64 for value in key),
             'PRIMITIVE_RELATION_KEY_DOMAIN')
        need(type(values) in (list, tuple) and 0 < len(values) <= MAX_POINTS and
             all(type(value) is int and value in expected for value in values), 'PRIMITIVE_RELATION_ID_DOMAIN')
        result[key] = tuple(values)
        flat.extend(values)
        need(len(flat) <= MAX_POINTS, 'PRIMITIVE_RELATION_BUDGET')
    need(len(flat) == len(expected) and len(set(flat)) == len(flat) and set(flat) == expected,
         'EXACT_UNIQUE_SOURCE_RELATION_COVERAGE')
    return result


def _raw_bone_proof(value, raw, expected_bone_count):
    need(type(expected_bone_count) is int and 1 <= expected_bone_count <= 256, 'EXPECTED_BONE_COUNT_DOMAIN')
    need(type(value) is dict and value.get('format') == 'has_source_export_crosswalk_draft_1' and
         value.get('status') == 'observed_inactive' and value.get('glb_sha256') == sha(raw) and
         type(value.get('glb_bytes')) is int and value['glb_bytes'] == len(raw), 'ACTUAL_RAW_BONE_PROOF_REQUIRED')
    need(value.get('applied') is False and value.get('native_simulation') is False and
         value.get('HAS_runtime_binding') == 'unattempted' and value.get('export_extras') is False,
         'RAW_BONE_PROOF_SCOPE')
    bones = value.get('bones')
    need(type(value.get('native_bone_count')) is int and value['native_bone_count'] == expected_bone_count and
         type(bones) is list and len(bones) == expected_bone_count and
         all(type(row) is dict and type(row.get('native_index')) is int and
             type(row.get('gltf_node_index')) is int and row['gltf_node_index'] >= 0 for row in bones) and
         sorted(row['native_index'] for row in bones) == list(range(expected_bone_count)) and
         len({row['gltf_node_index'] for row in bones}) == expected_bone_count,
         'COMPLETE_RAW_BONE_NODE_DOMAIN')
    need(PROVENANCE not in value, 'NORMAL_BONE_PROVENANCE_COLLISION')
    compact(value)


def _measure_corrected(correction, corrected, native, relation, axes):
    document, binary = correction.parse_glb(corrected)
    keys = {(mi, pi) for mi, mesh in enumerate(document.get('meshes', []))
            for pi, _ in enumerate(mesh.get('primitives', []))}
    need(keys == set(relation), 'CORRECTED_MEASUREMENT_PRIMITIVE_DOMAIN')
    maximum, count, seen = 0.0, 0, set()
    for mi, pi in sorted(keys):
        primitive = document['meshes'][mi]['primitives'][pi]
        attrs = primitive['attributes']
        need(correction.CARRIER not in attrs, 'FINAL_CARRIER_SEMANTIC_NOT_STRIPPED')
        rows = correction._float_accessor(document, binary, attrs['NORMAL'], 'VEC3')
        ids = relation[(mi, pi)]
        need(len(rows) == len(ids), 'CORRECTED_NORMAL_MEASUREMENT_COUNT')
        for identifier, actual in zip(ids, rows):
            need(1 <= identifier <= len(native.words), 'CORRECTED_NORMAL_NATIVE_ID_DOMAIN')
            wanted = correction.floats(correction.transport_words(native.words[identifier - 1], axes))
            delta = tuple(a - b for a, b in zip(actual, wanted))
            need(all(math.isfinite(value) for value in delta), 'CORRECTED_NORMAL_NONFINITE_DELTA')
            maximum = max(maximum, math.sqrt(sum(value * value for value in delta)))
            count += 1
            seen.add(identifier)
    return dict(format='has_corrected_native_normal_measurement_1', measured=True,
        source_normal_metric=METRIC, source_normal_threshold=THRESHOLD,
        source_normal_max_euclidean_error=maximum, passed=maximum <= THRESHOLD,
        source_points=len(seen), exported_normal_rows=count, compared_components=3 * count,
        measurement_normalization_or_repair_applied=False)


def _measurement(value, source_count):
    allowed = {'format','measured','source_normal_metric','source_normal_threshold',
        'source_normal_max_euclidean_error','passed','source_points','exported_normal_rows',
        'compared_components','measurement_normalization_or_repair_applied'}
    need(type(value) is dict and set(value) <= allowed and
         value.get('measurement_normalization_or_repair_applied',False) is False and
         value.get('format') == 'has_corrected_native_normal_measurement_1' and
         value.get('measured') is True and value.get('source_normal_metric') == METRIC and
         type(value.get('source_normal_threshold')) is float and value['source_normal_threshold'] == THRESHOLD and
         type(value.get('source_normal_max_euclidean_error')) is float and
         math.isfinite(value['source_normal_max_euclidean_error']) and
         0.0 <= value['source_normal_max_euclidean_error'] and type(value.get('passed')) is bool and
         value['passed'] == (value['source_normal_max_euclidean_error'] <= THRESHOLD),
         'ORIGINAL_RAW_EUCLIDEAN_GATE_REQUIRED')
    need(all(type(value.get(key)) is int for key in ('source_points', 'exported_normal_rows', 'compared_components')) and
         value['source_points'] == value['exported_normal_rows'] == source_count and
         value['compared_components'] == 3 * source_count, 'CORRECTED_NORMAL_COMPLETE_MEASUREMENT_REQUIRED')


def finalize_native_normals(raw_carrier, *, correction_module, native, carrier_sha256,
                            expected_source_ids, independent_relation, axes, expected_vvd_sha256,
                            bone_collector, measure_corrected=None, expected_bone_count=69):
    """Finish REAL raw bone proof, correct in RAM, then preservation-bind final SHA.

    Return (new immutable GLB bytes, safe report, PRIVATE rebound bone proof).
    This never mutates the input GLB, source native words or original bone proof.
    The caller must already qualify actual input/domain/frame/resource provenance.
    """
    summary = dict(format='has_source_normal_export_finalization_candidate_1',
        status='REFUSED_UNQUALIFIED', phase='ADMISSION', raw_bone_finish_attempts=0,
        correction_attempts=0, independent_relation_authenticated_by_this_module=False,
        correction_surface_authenticated_by_this_module=False, application_adoption_qualified=False,
        historical_saved_B_identity_inferred=False, generic_source_or_renderer_fidelity_qualified=False,
        original_native_files_written=False, raw_carrier_written=False, exporter_invoked=False)
    try:
        need(type(raw_carrier) is bytes and 28 <= len(raw_carrier) <= MAX_GLB and
             type(carrier_sha256) is str and re.fullmatch('[0-9a-f]{64}', carrier_sha256) is not None and
             sha(raw_carrier) == carrier_sha256, 'PINNED_RAW_CARRIER_REQUIRED')
        need(type(expected_vvd_sha256) is str and re.fullmatch('[0-9a-f]{64}', expected_vvd_sha256) is not None,
             'PINNED_NATIVE_VVD_REQUIRED')
        relation = _relation(expected_source_ids, independent_relation, axes)
        relation_before = compact([dict(mesh=k[0], primitive=k[1], one_based_source_ids=list(v))
                                   for k, v in sorted(relation.items())])
        summary['phase'] = 'RAW_BONE_FINISH'
        summary['raw_bone_finish_attempts'] = 1
        raw_bones = bone_collector.finish(raw_carrier)
        _raw_bone_proof(raw_bones, raw_carrier, expected_bone_count)
        raw_bone_bytes = compact(raw_bones)
        raw_bone_snapshot = copy.deepcopy(raw_bones)
        summary['phase'] = 'EXACT_WORD_CORRECTION'
        summary['correction_attempts'] = 1
        corrected, correction_report = correction_module.correct_glb(raw_carrier, native, carrier_sha256,
            list(expected_source_ids), axes, expected_native_sha256=expected_vvd_sha256,
            verified_primitive_identity_order=relation)
        need(type(corrected) is bytes and 28 <= len(corrected) <= MAX_GLB and
             type(correction_report) is dict and correction_report.get('status') == 'CANDIDATE_DERIVATIVE_UNQUALIFIED' and
             correction_report.get('input_sha256') == carrier_sha256 and
             correction_report.get('output_sha256') == sha(corrected) and
             correction_report.get('source_vvd_sha256') == expected_vvd_sha256 and
             all(correction_report.get(key) is True for key in
                 ('source_word_transport_exact', 'all_original_BIN_bytes_preserved',
                  'non_NORMAL_content_preserved', 'identity_order_matches_supplied_manifest')),
             'EXACT_WORD_CORRECTION_REPORT_REQUIRED')
        summary['phase'] = 'INDEPENDENT_PRESERVATION_AND_WORD_CONTRACTS'
        need(correction_module.preservation_contract(raw_carrier, corrected) is True,
             'NORMAL_ONLY_PRESERVATION_CONTRACT_REQUIRED')
        need(correction_module.corrected_normal_contract(corrected, native, relation, axes) is True,
             'EXACT_SOURCE_NORMAL_WORD_CONTRACT_REQUIRED')
        before, _old_binary = correction_module.parse_glb(raw_carrier)
        after, _new_binary = correction_module.parse_glb(corrected)
        need(all(correction_module.typed_same(before.get(key), after.get(key))
                 for key in ('scene', 'scenes', 'nodes', 'skins')), 'BONE_SCENE_NODE_SKIN_DATA_CHANGED')
        need(compact(raw_bones) == raw_bone_bytes and
             correction_module.typed_same(raw_bones, raw_bone_snapshot), 'RAW_BONE_PROOF_MUTATED')
        need(compact([dict(mesh=k[0], primitive=k[1], one_based_source_ids=list(v))
                      for k, v in sorted(relation.items())]) == relation_before,
             'INDEPENDENT_RELATION_MUTATED')
        summary['phase'] = 'MEASURE_FINAL_RAW_NORMALS'
        measurement = (_measure_corrected(correction_module, corrected, native, relation, axes)
                       if measure_corrected is None else measure_corrected(corrected, native, relation, axes))
        _measurement(measurement, len(expected_source_ids))
        summary['measurement'] = dict(measurement)
        need(measurement['passed'] is True, 'ORIGINAL_RAW_EUCLIDEAN_GATE_REQUIRED')
        need(compact(raw_bones) == raw_bone_bytes and
             correction_module.typed_same(raw_bones, raw_bone_snapshot), 'RAW_BONE_PROOF_MUTATED')
        need(compact([dict(mesh=k[0], primitive=k[1], one_based_source_ids=list(v))
                      for k, v in sorted(relation.items())]) == relation_before,
             'INDEPENDENT_RELATION_MUTATED')
        summary['phase'] = 'PRESERVATION_PROVED_BONE_CHECKSUM_REBIND'
        final_sha = sha(corrected)
        proof_identity = dict(raw_carrier_sha256=carrier_sha256, final_glb_sha256=final_sha,
            private_relation_sha256=sha(relation_before), original_bone_proof_sha256=sha(raw_bone_bytes),
            correction_report_sha256=sha(compact(correction_report)), raw_normal_measurement_sha256=sha(compact(measurement)))
        rebound = copy.deepcopy(raw_bones)
        rebound['glb_sha256'], rebound['glb_bytes'] = final_sha, len(corrected)
        rebound[PROVENANCE] = dict(format='has_preservation_proved_normal_only_bone_rebind_1',
            **proof_identity, bone_node_skin_scene_data_unchanged=True, native_bone_links_rederived=False,
            raw_hook_observed_corrected_bytes=False, source_normal_metric=METRIC,
            source_normal_threshold=THRESHOLD, source_normal_max_euclidean_error=measurement['source_normal_max_euclidean_error'])
        need(all(correction_module.typed_same(value, rebound[key]) for key, value in raw_bones.items()
                 if key not in ('glb_sha256', 'glb_bytes')), 'UNRELATED_BONE_PROOF_FIELD_CHANGED')
        compact(rebound)
        summary.update(status='CANDIDATE_DERIVATIVE_UNQUALIFIED', phase='COMPLETE',
            **proof_identity, raw_carrier_bytes=len(raw_carrier), final_glb_bytes=len(corrected),
            source_points=len(expected_source_ids), primitives=len(relation), native_bones=expected_bone_count,
            normal_word_correction_applied=True, original_normal_only_contract_passed=True,
            exact_native_normal_words_passed=True, raw_Euclidean_gate_passed=True,
            measurement=measurement, final_bone_proof_sha256=sha(compact(rebound)),
            original_raw_bone_proof_unchanged=True, final_checksum_bound_by_preservation=True,
            raw_hook_observed_corrected_bytes=False)
        return corrected, summary, rebound
    except Refusal as error:
        raise Refusal(str(error), summary) from error
    except Exception as error:
        summary['failure_exception_type'] = (type(error).__name__ if type(error).__name__ in
            {'ValueError', 'TypeError', 'KeyError', 'IndexError', 'OverflowError', 'AttributeError',
             'AssertionError', 'RuntimeError'} else 'OTHER')
        raise Refusal('NORMAL_EXPORT_FINALIZATION_API_OR_CONTRACT_FAILED', summary) from error


class _FinalPublicationObservation:
    """Existing augment_plan observation interface; no IO implementation here.

    The caller supplies the admitted strict file-identity reader. Both raw and
    final artifacts must survive; native/runtime rechecks stay on the genuine
    old observation. The old observation and proof are never overwritten.
    """
    def __init__(self, raw_observation, report, raw_path, final_path, identity_reader):
        need(raw_path != final_path and callable(identity_reader) and
             callable(raw_observation.recheck), 'DISTINCT_OWNED_PUBLICATION_IDENTITIES_REQUIRED')
        self.capture = raw_observation.capture
        self.original_sha256 = raw_observation.original_sha256
        need(type(self.original_sha256) is str and re.fullmatch('[0-9a-f]{64}', self.original_sha256) is not None,
             'PUBLICATION_ORIGINAL_SOURCE_IDENTITY')
        self._raw_observation = raw_observation
        self._raw_path, self._final_path = raw_path, final_path
        self._raw_sha, self._final_sha = report['raw_carrier_sha256'], report['final_glb_sha256']
        self._reader = identity_reader

    def publication_identity(self):
        need(self._raw_observation.capture is self.capture and
             self._raw_observation.original_sha256 == self.original_sha256,
             'PUBLICATION_OBSERVATION_SOURCE_CONTEXT_CHANGED')
        self._raw_observation.recheck()
        for path, digest in ((self._raw_path,self._raw_sha),(self._final_path,self._final_sha)):
            row = self._reader(path,digest)
            need(type(row) is tuple and len(row) == 2 and row[0] == path and row[1] == digest,
                 'PUBLICATION_FILE_IDENTITY_READER_DIFFERS')
        self._raw_observation.recheck()
        need(self._raw_observation.capture is self.capture and
             self._raw_observation.original_sha256 == self.original_sha256,
             'PUBLICATION_OBSERVATION_SOURCE_CONTEXT_CHANGED')
        return self._final_sha


def make_publication_state(raw_observation, rebound_bones, finalization_report, *,
                           raw_path, final_path, identity_reader):
    """Produce the EXISTING source_bone_export.augment_plan state interface.

    Call only after writing/rechecking a fresh final GLB. Existing plan_report
    validates source/native identity and binds its integer wire to this final
    SHA. This wrapper makes no new standard, writes no files and enables no
    source physics. Identity-reader/source errors remain hard failures.
    """
    report = finalization_report
    need(type(report) is dict and report.get('format') == 'has_source_normal_export_finalization_candidate_1' and
         report.get('status') == 'CANDIDATE_DERIVATIVE_UNQUALIFIED' and
         report.get('final_checksum_bound_by_preservation') is True and
         report.get('original_raw_bone_proof_unchanged') is True and
         report.get('raw_hook_observed_corrected_bytes') is False and
         report.get('application_adoption_qualified') is False,
         'COMPLETE_NORMAL_FINALIZATION_REQUIRED_FOR_PUBLICATION')
    need(all(type(report.get(key)) is str and re.fullmatch('[0-9a-f]{64}',report[key]) is not None
             for key in ('raw_carrier_sha256','final_glb_sha256','final_bone_proof_sha256')) and
         report['raw_carrier_sha256'] != report['final_glb_sha256'],
         'RAW_AND_FINAL_PUBLICATION_DIGESTS_REQUIRED')
    measurement = report.get('measurement')
    need(type(report.get('source_points')) is int, 'PUBLICATION_SOURCE_COUNT_REQUIRED')
    _measurement(measurement, report['source_points'])
    need(measurement['passed'] is True and report.get('raw_Euclidean_gate_passed') is True,
         'PUBLICATION_RAW_EUCLIDEAN_GATE_REQUIRED')
    need(type(rebound_bones) is dict and sha(compact(rebound_bones)) == report['final_bone_proof_sha256'] and
         rebound_bones.get('glb_sha256') == report['final_glb_sha256'] and
         type(rebound_bones.get('glb_bytes')) is int and rebound_bones['glb_bytes'] == report.get('final_glb_bytes'),
         'PUBLICATION_REBOUND_PROOF_DIGEST_DIFFERS')
    provenance = rebound_bones.get(PROVENANCE)
    need(type(provenance) is dict and provenance.get('format') == 'has_preservation_proved_normal_only_bone_rebind_1' and
         provenance.get('raw_carrier_sha256') == report['raw_carrier_sha256'] and
         provenance.get('final_glb_sha256') == report['final_glb_sha256'] and
         provenance.get('raw_hook_observed_corrected_bytes') is False and
         provenance.get('bone_node_skin_scene_data_unchanged') is True,
         'PUBLICATION_NORMAL_ONLY_PROVENANCE_REQUIRED')
    observation = _FinalPublicationObservation(raw_observation, report, raw_path, final_path, identity_reader)
    # Admit both artifacts now, and recheck each time the ordinary publisher asks.
    need(observation.publication_identity() == report['final_glb_sha256'], 'FINAL_PUBLICATION_IDENTITY_REQUIRED')
    return dict(observation=observation, observed=copy.deepcopy(rebound_bones), reason=None)
