"""Read-only ownership observations after the unchanged resource survey.

No blend load, path open/stat/resolve, image buffer or geometry operation.
Original survey outputs remain caller-owned and unchanged even on failure.
"""
import hashlib
import json
from survey_core import Budget, Limits, SurveyError, canonical, need, pointer


def collect_ownership_metadata(bpy, resource_private, resource_public, limits=Limits()):
    budget = Budget(limits)
    baseline_raw = canonical(resource_private)
    need(len(baseline_raw) <= limits.metadata_bytes and
         resource_private['format'] == 'has_private_B_resource_metadata_survey_1', 'RESOURCE_BASELINE_FORMAT_BOUND')
    need(resource_public['private_metadata_sha256'] == hashlib.sha256(baseline_raw).hexdigest(),
         'RESOURCE_BASELINE_IDENTITY')
    need(resource_public['profile_issues'] == len(resource_private['issues']) and
         resource_public['status'] == ('RESOURCE_PROFILE_REFUSED' if resource_private['issues'] else 'METADATA_SURVEY_ONLY') and
         resource_public['native_profile_fidelity_export_or_adoption_qualified'] is False,
         'RESOURCE_BASELINE_STATUS')
    images = budget.collection(bpy.data.images, limits.images)
    materials = budget.collection(bpy.data.materials, limits.materials)
    image_ids = {pointer(image): i for i, image in enumerate(images)}
    need(len(image_ids) == len(images) and len(images) == len(resource_private['images']), 'IMAGE_IDENTITY')
    need(all(resource_private['images'][i]['session_identity'] == pointer(image)
             for i, image in enumerate(images)), 'STALE_RESOURCE_IMAGES')
    material_ids = {pointer(value) for value in materials}
    registry = {}; descriptors = {}; paths = []; weak = []; ui = []; edges = 0

    def data_path(value, property=''):
        try: return {'status': 'OBSERVED', 'value': budget.text(value.path_from_module(property))}
        except (ValueError, AttributeError): return {'status': 'UNOBSERVED', 'value': None}

    def register(value):
        key = pointer(value)
        if key not in registry:
            need(len(registry) < limits.external_paths, 'OWNER_ID_BOUND')
            registry[key] = value
            descriptors[key] = {'session_identity': key,
                                'rna_type': budget.text(value.bl_rna.identifier),
                                'name_full': budget.text(value.name_full),
                                'data_path': data_path(value),
                                'linked_library_present': value.library is not None}
        return key

    users = bpy.data.user_map()
    need(type(users) is dict and len(users) <= limits.external_paths, 'USER_MAP_BOUND')
    graph = {}
    for value, owners in users.items():
        need(type(owners) in (set, frozenset) and len(owners) <= limits.image_references, 'USER_SET_TYPE_BOUND')
        key = register(value); need(key not in graph, 'DUPLICATE_USER_KEY_IDENTITY')
        owner_keys = [register(owner) for owner in owners]
        need(len(set(owner_keys)) == len(owner_keys), 'DUPLICATE_USER_IDENTITY')
        edges += len(owner_keys); need(edges <= limits.image_references, 'TOTAL_USER_EDGE_BOUND')
        graph[key] = sorted(owner_keys)
    need(set(image_ids) <= set(graph), 'IMAGE_USER_MAP_COVERAGE_UNOBSERVED')

    # This API can replace paths only when a visitor returns a string. Every
    # branch below returns None, including malformed/budget failure branches.
    visitor_error = []
    def visit(owner, raw, _reserved):
        if not visitor_error:
            try:
                need(len(paths) < limits.external_paths, 'OWNED_PATH_BOUND')
                paths.append({'owner': register(owner), 'raw': budget.text(raw)})
            except Exception as error:
                visitor_error.append(error)
        return None

    # Omit SKIP_WEAK_REFERENCES explicitly; retain SKIP_PACKED. This records
    # owner IDs for weak-reference paths as metadata without loading them.
    bpy.data.file_path_foreach(visit, flags={'SKIP_PACKED'})
    if visitor_error: raise visitor_error[0]
    # UI references are not inferred from ID.users or image names. Only this
    # explicitly observed editor property is covered; other UI is unobserved.
    screens = budget.collection(bpy.data.screens, limits.objects)
    ui_items = 0; ui_areas = 0
    for screen in screens:
        owner_key = register(screen)
        for a, area in enumerate(budget.collection(screen.areas, limits.objects)):
            ui_areas += 1; need(ui_areas <= limits.nodes, 'TOTAL_UI_AREA_BOUND')
            for s, space in enumerate(budget.collection(area.spaces, limits.objects)):
                ui_items += 1; need(ui_items <= limits.nodes, 'TOTAL_UI_SPACE_BOUND')
                if budget.text(space.type) == 'IMAGE_EDITOR' and space.image is not None:
                    key = pointer(space.image)
                    need(key in image_ids, 'UI_IMAGE_OUTSIDE_BASELINE')
                    ui.append({'owner': owner_key, 'area': a, 'space': s,
                               'image': image_ids[key], 'property_data_path': data_path(space, 'image')})

    for key in sorted(registry):
        owner = registry[key]; reference = owner.library_weak_reference
        if reference is not None:
            weak.append({'owner': key, 'rna_type': budget.text(reference.bl_rna.identifier),
                         'property_data_path': data_path(owner, 'library_weak_reference'),
                         'filepath': budget.text(reference.filepath),
                         'id_name': budget.text(reference.id_name)})

    joins = []
    need(set(resource_private['external_path_references']) == {'all', 'unpacked'}, 'RESOURCE_PATH_TABLES')
    for label, values in resource_private['external_path_references'].items():
        for i, value in enumerate(budget.collection(values, limits.external_paths)):
            raw = value['raw']
            exact = sorted({row['owner'] for row in paths if row['raw'] == raw}) if raw else []
            exact_weak = [j for j, row in enumerate(weak) if raw and row['filepath'] == raw and row['owner'] in exact]
            joins.append({'path_class': budget.text(label), 'path_index': i,
                          'exact_raw_owner_ids': exact, 'exact_owner_and_library_weak_reference_rows': exact_weak,
                          'status': 'EXACT_RAW_OWNER_METADATA' if exact else 'OWNER_UNOBSERVED',
                          'nested_reference_property_status': 'OBSERVED_LIBRARY_WEAK_REFERENCE' if exact_weak else 'UNOBSERVED'})
    viewers = []
    for image_key, index in sorted(image_ids.items(), key=lambda row: row[1]):
        image = resource_private['images'][index]
        if image['source'] != 'VIEWER': continue
        seen = set(); pending = list(graph[image_key])
        while pending:
            key = pending.pop()
            if key in seen: continue
            seen.add(key); need(len(seen) <= limits.external_paths, 'REACHABILITY_BOUND')
            pending.extend(next_key for next_key in graph.get(key, ()) if next_key not in seen)
        viewers.append({'image': index, 'source': image['source'], 'type': image['type'],
                        'original_users': image['users'],
                        'original_material_node_references': [dict(row) for row in resource_private['material_image_references'] if row['image'] == index],
                        'direct_id_users': graph[image_key], 'reachable_material_ids': sorted(seen & material_ids),
                        'reachable_other_id_owners': sorted(seen - material_ids - {image_key}),
                        'image_editor_references': [dict(row) for row in ui if row['image'] == index],
                        'unobserved_owner_scopes': ['non_IMAGE_EDITOR_UI', 'implicit_viewer_producer_semantics'],
                        'resource_excluded_or_accepted': False})
    private = {'format': 'has_private_B_resource_ownership_metadata_1',
               'source_resource_private_sha256': hashlib.sha256(baseline_raw).hexdigest(),
               'original_issues': json.loads(canonical(resource_private['issues'])),
               'owners': [descriptors[key] for key in sorted(descriptors)],
               'weak_enabled_path_observations': sorted(paths, key=lambda row: (row['owner'], row['raw'])),
               'ID_library_weak_references': weak, 'external_reference_owner_joins': joins,
               'viewer_reachability': viewers, 'image_editor_references': ui,
               'all_resource_survey_rows_and_status_retained': True,
               'external_path_contents_opened_or_statted': False, 'resource_paths_modified': False,
               'pixel_geometry_matrix_weight_arrays_read': False,
               'filename_or_basename_role_inference': False,
               'unobserved_reference_kinds_are_unresolved': True}
    raw = canonical(private); need(len(raw) <= limits.metadata_bytes, 'FINAL_OWNERSHIP_METADATA_BOUND')
    need(canonical(resource_private) == baseline_raw, 'RESOURCE_BASELINE_CHANGED')
    public = {'format': 'has_B_resource_ownership_metadata_summary_1',
              'status': resource_public['status'], 'profile_issues': resource_public['profile_issues'],
              'original_resource_summary': dict(resource_public),
              'owners': len(descriptors), 'weak_path_observations': len(paths),
              'ID_library_weak_references': len(weak), 'viewer_images': len(viewers),
              'image_editor_references': len(ui),
              'ownership_metadata_bytes': len(raw), 'ownership_metadata_sha256': hashlib.sha256(raw).hexdigest(),
              'resource_profile_decision_changed': False, 'separate_native_context_admission_required': True,
              'strict31_native_qualified': False, 'normal_tolerance_or_fidelity_qualified': False,
              'export_repair_carrier_or_adoption_qualified': False}
    return private, public
