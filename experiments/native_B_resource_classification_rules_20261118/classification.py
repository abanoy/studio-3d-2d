"""Pure, bounded classification of saved resource/ownership metadata.

No bpy, IO, path normalization, external lookup, model mutation or acceptance.
The caller remains responsible for authenticating the three saved input bodies.
"""
from dataclasses import dataclass, fields
import hashlib
import json


REQUIRED = 'REQUIRED_EXTERNAL_REFERENCE'
PROVENANCE = 'LOCAL_APPENDED_ASSET_PROVENANCE'
VIEWER = 'INTERNAL_VIEWER_EDITOR_OBSERVATION'
UNRESOLVED = 'UNRESOLVED'
CATEGORIES = (REQUIRED, PROVENANCE, VIEWER, UNRESOLVED)
UNKNOWN_VIEWER_SCOPES = ['non_IMAGE_EDITOR_UI', 'implicit_viewer_producer_semantics']


class ClassificationError(ValueError):
    """Fixed public error code; never include private evidence in errors."""


def need(ok, code):
    if not ok:
        raise ClassificationError(code)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


@dataclass(frozen=True)
class Limits:
    input_bytes_each: int = 512 * 1024
    output_bytes: int = 512 * 1024
    nodes: int = 60_000
    text_bytes: int = 1024 * 1024
    text_bytes_each: int = 4096
    depth: int = 24
    rows: int = 4096


HARD = Limits()


def _bounded_inputs(values, limits):
    need(type(limits) is Limits, 'LIMITS_TYPE')
    for field in fields(Limits):
        value = getattr(limits, field.name)
        need(type(value) is int and 0 <= value <= getattr(HARD, field.name), 'LIMIT_DOMAIN')
    nodes = text_bytes = 0
    active = set()

    def visit(value, depth):
        nonlocal nodes, text_bytes
        nodes += 1
        need(nodes <= limits.nodes and depth <= limits.depth, 'INPUT_STRUCTURE_BOUND')
        if type(value) is str:
            try:
                size = len(value.encode('utf-8'))
            except UnicodeError:
                raise ClassificationError('INPUT_TEXT_ENCODING') from None
            text_bytes += size
            need('\0' not in value and size <= limits.text_bytes_each
                 and text_bytes <= limits.text_bytes, 'INPUT_TEXT_BOUND')
        elif type(value) in (dict, list):
            need(id(value) not in active and len(value) <= limits.rows, 'INPUT_COLLECTION_BOUND')
            active.add(id(value))
            if type(value) is dict:
                for key, child in value.items():
                    need(type(key) is str, 'INPUT_KEY_TYPE')
                    visit(key, depth + 1)
                    visit(child, depth + 1)
            else:
                for child in value:
                    visit(child, depth + 1)
            active.remove(id(value))
        else:
            need(value is None or type(value) is bool
                 or (type(value) is int and -(2**63) <= value < 2**64), 'INPUT_JSON_TYPE')

    raw = []
    for value in values:
        need(type(value) is dict, 'INPUT_OBJECT_REQUIRED')
        visit(value, 0)
        encoded = canonical(value)
        need(len(encoded) <= limits.input_bytes_each, 'INPUT_BYTES_BOUND')
        raw.append(encoded)
    return raw


def _list(value):
    need(type(value) is list, 'EVIDENCE_LIST_TYPE')
    return value


def _integer(value, maximum=2**64 - 1):
    need(type(value) is int and 0 <= value <= maximum, 'EVIDENCE_INTEGER')
    return value


def _text(value):
    need(type(value) is str, 'EVIDENCE_TEXT')
    return value


def _observation(value, suffix=None):
    need(type(value) is dict and set(value) == {'status', 'value'}, 'PROPERTY_OBSERVATION_SCHEMA')
    if value['status'] == 'UNOBSERVED':
        need(value['value'] is None, 'PROPERTY_UNOBSERVED_VALUE')
        return False
    need(value['status'] == 'OBSERVED' and type(value['value']) is str
         and bool(value['value']), 'PROPERTY_OBSERVATION_VALUE')
    return suffix is None or value['value'].endswith(suffix)


def classify(resource_private, resource_public, ownership, limits=Limits()):
    """Return separate (private detail, public scalar summary); never mutate inputs.

    Invalid/stale evidence raises ClassificationError. Valid but insufficient or
    ambiguous evidence yields UNRESOLVED. Labels describe observed references;
    REQUIRED does not prove existence, export use, portability or content identity.
    """
    original = _bounded_inputs((resource_private, resource_public, ownership), limits)
    try:
        result = _classify(resource_private, resource_public, ownership, original)
    except (KeyError, TypeError, IndexError):
        raise ClassificationError('EVIDENCE_SCHEMA') from None
    raw = canonical(result)
    need(len(raw) <= limits.output_bytes, 'OUTPUT_BYTES_BOUND')
    need(original == [canonical(item) for item in (resource_private, resource_public, ownership)],
         'INPUT_MUTATION')
    counts = {category: sum(row['classification'] == category for row in result['rows'])
              for category in CATEGORIES}
    summary = {'format': 'has_B_resource_classification_summary_1',
               'status': resource_public['status'], 'profile_issues': resource_public['profile_issues'],
               'source_resource_private_sha256': hashlib.sha256(original[0]).hexdigest(),
               'source_resource_public_sha256': hashlib.sha256(original[1]).hexdigest(),
               'source_ownership_sha256': hashlib.sha256(original[2]).hexdigest(),
               'classification_rows': len(result['rows']), 'counts': counts,
               'original_issue_rows_retained': len(result['original_issues']),
               'classification_bytes': len(raw), 'classification_sha256': hashlib.sha256(raw).hexdigest(),
               'resource_profile_decision_changed': False, 'resources_excluded_or_accepted': False,
               'external_content_identity_or_existence_observed': False,
               'strict31_normal_fidelity_export_repair_carrier_or_adoption_qualified': False,
               'actual_native_execution_by_classifier': False}
    need(len(canonical(summary)) <= limits.output_bytes, 'OUTPUT_BYTES_BOUND')
    return result, summary


def _classify(r, public, o, original):
    need(r['format'] == 'has_private_B_resource_metadata_survey_1'
         and public['format'] == 'has_B_resource_metadata_survey_summary_1'
         and o['format'] == 'has_private_B_resource_ownership_metadata_1', 'INPUT_FORMAT')
    source_sha = hashlib.sha256(original[0]).hexdigest()
    issues = _list(r['issues'])
    need(public['private_metadata_sha256'] == source_sha
         and o['source_resource_private_sha256'] == source_sha
         and o['original_issues'] == issues, 'SOURCE_BINDING')
    need(type(public['profile_issues']) is int and public['profile_issues'] == len(issues)
         and public['status'] == ('RESOURCE_PROFILE_REFUSED' if issues else 'METADATA_SURVEY_ONLY')
         and public['native_profile_fidelity_export_or_adoption_qualified'] is False,
         'ORIGINAL_DECISION_BINDING')
    for key in ('all_resource_survey_rows_and_status_retained', 'unobserved_reference_kinds_are_unresolved'):
        need(o[key] is True, 'OWNERSHIP_SCOPE')
    for key in ('external_path_contents_opened_or_statted', 'resource_paths_modified',
                'pixel_geometry_matrix_weight_arrays_read', 'filename_or_basename_role_inference'):
        need(o[key] is False, 'OWNERSHIP_SCOPE')
    owners = {}
    for owner in _list(o['owners']):
        key = _integer(owner['session_identity'])
        need(key > 0 and key not in owners, 'OWNER_IDENTITY')
        _text(owner['rna_type']); _observation(owner['data_path'])
        need(type(owner['linked_library_present']) is bool, 'OWNER_LIBRARY_TYPE')
        owners[key] = owner
    images = _list(r['images']); image_ids = set()
    for index, image in enumerate(images):
        key = _integer(image['session_identity'])
        need(type(image['index']) is int and image['index'] == index and key > 0 and key not in image_ids
             and key in owners and owners[key]['rna_type'] == 'Image', 'IMAGE_IDENTITY')
        image_ids.add(key)
        for field in ('source', 'type', 'filepath', 'filepath_raw'):
            _text(image[field])
        _integer(image['users']); _list(image['packed'])
    paths = r['external_path_references']
    need(type(paths) is dict and set(paths) == {'all', 'unpacked'}, 'PATH_TABLES')
    for values in paths.values():
        for value in _list(values):
            _text(value['raw'])
    observations = {}
    for observed in _list(o['weak_enabled_path_observations']):
        key = _integer(observed['owner']); raw = _text(observed['raw'])
        need(key in owners, 'STALE_PATH_OWNER')
        observations.setdefault(raw, []).append(key)
    weak = _list(o['ID_library_weak_references'])
    for descriptor in weak:
        need(_integer(descriptor['owner']) in owners, 'STALE_WEAK_OWNER')
        _text(descriptor['rna_type']); _text(descriptor['filepath']); _text(descriptor['id_name'])
        _observation(descriptor['property_data_path'])
    joins = {}
    for join in _list(o['external_reference_owner_joins']):
        label = join['path_class']; index = _integer(join['path_index'])
        need(label in paths and index < len(paths[label]) and (label, index) not in joins, 'PATH_JOIN_IDENTITY')
        raw = paths[label][index]['raw']
        need(all(type(key) is int and key > 0 for key in _list(join['exact_raw_owner_ids']))
             and all(type(key) is int and key >= 0 for key in _list(join['exact_owner_and_library_weak_reference_rows'])),
             'PATH_JOIN_INTEGER')
        exact = sorted(set(observations.get(raw, []))) if raw else []
        exact_weak = [i for i, descriptor in enumerate(weak)
                      if raw and descriptor['filepath'] == raw and descriptor['owner'] in exact]
        need(join['exact_raw_owner_ids'] == exact
             and join['exact_owner_and_library_weak_reference_rows'] == exact_weak
             and join['status'] == ('EXACT_RAW_OWNER_METADATA' if exact else 'OWNER_UNOBSERVED')
             and join['nested_reference_property_status'] == (
                 'OBSERVED_LIBRARY_WEAK_REFERENCE' if exact_weak else 'UNOBSERVED'), 'PATH_JOIN_EVIDENCE')
        joins[label, index] = (exact, exact_weak)
    need(len(joins) == sum(len(values) for values in paths.values()), 'PATH_JOIN_COVERAGE')
    ui = _list(o['image_editor_references'])
    ui_keys = set()
    for witness in ui:
        key = (_integer(witness['owner']), _integer(witness['area']), _integer(witness['space']))
        need(key[0] in owners and owners[key[0]]['rna_type'] == 'Screen'
             and key not in ui_keys and _integer(witness['image']) < len(images), 'UI_IDENTITY')
        ui_keys.add(key); _observation(witness['property_data_path'])
    refs = _list(r['material_image_references'])
    for reference in refs:
        need(_integer(reference['image']) < len(images), 'MATERIAL_IMAGE_IDENTITY')
    viewers = {}
    for viewer in _list(o['viewer_reachability']):
        index = _integer(viewer['image'])
        need(index < len(images) and index not in viewers, 'VIEWER_IDENTITY')
        image = images[index]
        need(image['source'] == 'VIEWER' and viewer['source'] == image['source']
             and viewer['type'] == image['type'] and type(viewer['original_users']) is int
             and viewer['original_users'] == image['users']
             and viewer['original_material_node_references'] == [row for row in refs if row['image'] == index]
             and viewer['image_editor_references'] == [row for row in ui if row['image'] == index]
             and viewer['unobserved_owner_scopes'] == UNKNOWN_VIEWER_SCOPES
             and viewer['resource_excluded_or_accepted'] is False, 'VIEWER_BINDING')
        for field in ('direct_id_users', 'reachable_material_ids', 'reachable_other_id_owners'):
            values = _list(viewer[field])
            need(all(type(key) is int and key in owners for key in values)
                 and len(set(values)) == len(values), 'STALE_VIEWER_OWNER')
        need(all(owners[key]['rna_type'] == 'Material' for key in viewer['reachable_material_ids']),
             'VIEWER_MATERIAL_TYPE')
        viewers[index] = viewer
    need(set(viewers) == {i for i, image in enumerate(images) if image['source'] == 'VIEWER'}, 'VIEWER_COVERAGE')
    rows = []
    for label, values in paths.items():
        for index, value in enumerate(values):
            raw = value['raw']; exact, exact_weak = joins[label, index]
            category = UNRESOLVED; reason = 'INSUFFICIENT_OR_AMBIGUOUS_PATH_EVIDENCE'
            if raw and len(exact) == 1 and len(observations.get(raw, [])) == 1:
                owner = owners[exact[0]]
                matched_images = [image for image in images if image['session_identity'] == exact[0]
                                  and image['source'] == 'FILE' and image['type'] == 'IMAGE'
                                  and image['filepath'] == raw and image['filepath_raw'] == raw
                                  and not image['packed']]
                file_claimants = [image for image in images if image['source'] == 'FILE'
                                  and raw in (image['filepath'], image['filepath_raw'])]
                unpacked = any(item['raw'] == raw for item in paths['unpacked'])
                if len(exact_weak) == 1:
                    descriptor = weak[exact_weak[0]]
                    if (not owner['linked_library_present'] and descriptor['rna_type'] == 'LibraryWeakReference'
                            and descriptor['id_name'] and _observation(descriptor['property_data_path'], '.library_weak_reference')
                            and len([item for item in weak if item['owner'] == exact[0]]) == 1
                            and not file_claimants and owner['rna_type'] != 'Library'):
                        category = PROVENANCE; reason = 'EXACT_OBSERVED_WEAK_PROPERTY_ON_LOCAL_ID'
                elif (not exact_weak and unpacked
                      and ((owner['rna_type'] == 'Library' and not file_claimants)
                           or (len(matched_images) == 1 and len(file_claimants) == 1))):
                    category = REQUIRED; reason = ('TYPED_UNPACKED_LIBRARY_OWNER' if owner['rna_type'] == 'Library'
                                                    else 'TYPED_UNPACKED_FILE_IMAGE_OWNER')
            rows.append({'kind': 'external_path', 'path_class': label, 'path_index': index,
                         'classification': category, 'reason': reason,
                         'owner_ids': exact, 'weak_reference_rows': exact_weak,
                         'unobserved_scopes': ['external_content_identity_and_existence', 'export_dependency_relevance']})
    for index, image in enumerate(images):
        category = UNRESOLVED; reason = 'IMAGE_KIND_OR_REFERENCE_EVIDENCE_UNRESOLVED'
        scopes = ['export_dependency_relevance']
        if index in viewers:
            viewer = viewers[index]; scopes = list(UNKNOWN_VIEWER_SCOPES)
            witness = viewer['image_editor_references']
            if (image['type'] in ('RENDER_RESULT', 'COMPOSITING')
                    and not image['filepath'] and not image['filepath_raw'] and not image['packed']
                    and not owners[image['session_identity']]['linked_library_present']
                    and all(not viewer[field] for field in ('direct_id_users', 'original_material_node_references',
                                                           'reachable_material_ids', 'reachable_other_id_owners'))
                    and witness):
                category = VIEWER; reason = 'TYPED_INTERNAL_IMAGE_WITH_EXPLICIT_EDITOR_WITNESS'
        elif image['source'] == 'FILE' and image['type'] == 'IMAGE' and image['filepath'] and not image['packed']:
            if any(row['classification'] == REQUIRED and row['owner_ids'] == [image['session_identity']]
                   for row in rows if row['kind'] == 'external_path'):
                category = REQUIRED; reason = 'TYPED_UNPACKED_FILE_IMAGE_OWNER'
        row = {'kind': 'image', 'image': index, 'classification': category,
               'reason': reason, 'unobserved_scopes': scopes}
        if index in viewers:
            row['IMAGE_EDITOR_witness_count'] = len(viewers[index]['image_editor_references'])
            row['IMAGE_EDITOR_property_path_statuses'] = [item['property_data_path']['status']
                                                         for item in viewers[index]['image_editor_references']]
        rows.append(row)
    return {'format': 'has_private_B_resource_classification_1',
            'source_resource_private_sha256': source_sha,
            'source_resource_public_sha256': hashlib.sha256(original[1]).hexdigest(),
            'source_ownership_sha256': hashlib.sha256(original[2]).hexdigest(),
            'original_resource_status': public['status'], 'original_issues': json.loads(canonical(issues)),
            'rows': rows, 'resource_profile_decision_changed': False,
            'resources_excluded_or_accepted': False, 'filename_role_inference_used': False,
            'full_graph_or_global_unreachability_proven': False,
            'strict31_normal_fidelity_export_repair_carrier_or_adoption_qualified': False}
