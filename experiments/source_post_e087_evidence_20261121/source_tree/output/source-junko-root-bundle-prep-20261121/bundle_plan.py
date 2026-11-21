"""Pure exact-family Junko bundle planning. No filesystem/SDK/model conversion.

A plan is not a World record or permission to merge skeletons. The host must
qualify all six conversions, one common source frame, an inert group asset and
ordinary history/cold storage before applying it. Existing defaults are untouched.
"""
import copy
import hashlib
import json
import math

class Refusal(ValueError):
    pass

EXPECTED = {
    'body': ('junko', 'd916863f801d0894009fad43c587ae630bf05556f484ebae4803734bd15c8af7'),
    'hair': ('junko hair', '8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'),
    'dress': ('junko dress', 'be03e608fc7fc0316a5441e65d01cef355e076b4eff17dd5b57fbf4defb35fdf'),
    'skirt': ('junko skirt', 'b753091a9e32e84cb81ae182df0b6c7c341feb0e51e5b2e190eccff2f92b397b'),
    'miniskirt': ('junko miniskirt', '55d13238fe67c4ead4ac6c2cb6c4ac43d7f2275d722021af5ce030e93cf1745d'),
    'mask': ('junko char mask', '8cb588d2e45268c79d83632cae4e0545d953025c9ea48a3bf42a1975a74db0f2'),
}
ORDER = tuple(EXPECTED)
OUTFITS = ('dress', 'skirt', 'miniskirt')
FORMAT = 'has_unapplied_static_character_bundle_plan_1'

def need(value, code):
    if not value:
        raise Refusal(code)

def identifier(value):
    return type(value) is str and 0 < len(value) <= 128 and all(ord(c)>=32 and c not in '/\\:' for c in value)

def number(value, high):
    return type(value) in (int, float) and math.isfinite(value) and 0 < value <= high

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def reviewed_outfit(value):
    if value is None:
        return None
    need(type(value) is list and len(value)<=len(OUTFITS), 'explicit_outfit_list_required')
    need(all(type(role) is str and role in OUTFITS for role in value) and len(set(value))==len(value), 'unknown_or_duplicate_outfit')
    return [role for role in OUTFITS if role in value]

def primary_models(paths):
    """Only six exact MDL entrypoints become parts; sidecars/materials stay dependencies."""
    need(type(paths) is list and len(paths)<=4096, 'bounded_input_inventory_required')
    result = {}; seen = set()
    for name in paths:
        need(type(name) is str and name and not name.startswith(('/', '\\')) and ':' not in name and '\\' not in name and '..' not in name.split('/'), 'relative_inventory_path_required')
        folded = name.casefold()
        need(folded not in seen, 'case_ambiguous_input_path'); seen.add(folded)
        if not folded.endswith('.mdl'):
            continue
        stem = folded.rsplit('/', 1)[-1][:-4]
        role = next((role for role, (label, _sha) in EXPECTED.items() if label==stem), None)
        need(role is not None and role not in result, 'unknown_or_duplicate_primary_model')
        result[role] = name
    need(set(result)==set(EXPECTED), 'all_six_primary_families_required')
    return {role: result[role] for role in ORDER}

def build(audit, part_ids, *, group_id, common_source_unit_scale, root_reference_scale=1.0, outfit=None, show_mask=False):
    need(type(audit) is dict and audit.get('format')=='has_cpu_only_junko_six_family_bundle_audit_1', 'exact_bundle_audit_required')
    need(audit.get('six_family_headers_and_checksums_verified') is True and audit.get('source_conversion_performed') is False, 'header_audit_scope_required')
    records = audit.get('records')
    need(type(records) is list and len(records)==6 and all(type(row) is dict for row in records), 'six_records_required')
    by_role = {}
    for row in records:
        role = row.get('role')
        need(type(role) is str and role in EXPECTED and role not in by_role, 'unique_role_required')
        label, checksum = EXPECTED[role]
        need(row.get('label')==label and row.get('mdl_sha256')==checksum and row.get('family_checksums_match') is True and row.get('mdl_version')==49 and row.get('vvd_version')==4 and row.get('dx90_version')==7, 'exact_source_family_required')
        by_role[role] = row
    paths = primary_models([row['mdl_relative'] for row in records])
    need(type(part_ids) is dict and set(part_ids)==set(EXPECTED) and all(identifier(value) for value in part_ids.values()), 'complete_actor_ids_required')
    need(identifier(group_id) and len(set(part_ids.values()))==6 and group_id not in part_ids.values(), 'distinct_bundle_and_part_ids_required')
    need(number(common_source_unit_scale, 1.0) and number(root_reference_scale, 1000.0), 'explicit_positive_common_units_required')
    need(type(show_mask) is bool, 'explicit_mask_visibility_required')
    selected = reviewed_outfit(outfit)
    parts = []
    for role in ORDER:
        parts.append({'role':role, 'id':part_ids[role], 'label':EXPECTED[role][0], 'source_mdl':paths[role],
            'source_mdl_sha256':EXPECTED[role][1], 'parent_id':group_id,
            'visible':role in ('body','hair') or role=='mask' and show_mask or selected is not None and role in selected,
            'local_source_origin':'preserve', 'relative_scale':1.0, 'individual_height_normalization':'none',
            'pose_owner':'self', 'morph_owner':'self', 'simulation_owner':'self', 'bone_following':'none'})
    plan = {'format':FORMAT, 'source_audit_sha256':digest(audit), 'application_adopted':False,
        'root':{'id':group_id, 'kind':'group', 'inert_group_asset_required':True,
                'common_source_unit_scale':float(common_source_unit_scale), 'reference_scale':float(root_reference_scale),
                'height_reference_role':'body', 'height_reference_applied_to':'bundle_root_only'},
        'parts':parts, 'outfit_review_required':selected is None, 'reviewed_outfit':selected,
        'same_source_origin_conversion_qualified':False, 'posed_bone_following_qualified':False,
        'skeleton_merge_performed':False, 'final_conversion_or_storage_qualified':False}
    plan['plan_sha256'] = digest(plan)
    return plan

def validate(plan):
    need(type(plan) is dict and plan.get('format')==FORMAT and type(plan.get('plan_sha256')) is str, 'static_bundle_plan_required')
    copied = copy.deepcopy(plan); expected = copied.pop('plan_sha256')
    need(digest(copied)==expected, 'plan_changed')
    need(plan.get('application_adopted') is False and plan.get('skeleton_merge_performed') is False and plan.get('posed_bone_following_qualified') is False, 'planning_scope_changed')
    parts = plan.get('parts')
    need(type(parts) is list and len(parts)==6 and {row.get('role') for row in parts}==set(EXPECTED), 'plan_parts_changed')
    return True

def outfit_visibility_operations(plan, outfit, frame):
    validate(plan)
    need(type(frame) is int and 0<=frame<=1_000_000, 'whole_visibility_frame_required')
    selected = reviewed_outfit(outfit)
    need(selected is not None, 'reviewed_outfit_required')
    by_role = {row['role']: row for row in plan['parts']}
    return {'format':'has_unapplied_bundle_visibility_operation_1', 'frame':frame,
        'before_plan_sha256':plan['plan_sha256'], 'operations':[
            {'id':by_role[role]['id'], 'visible':role in selected, 'frame':frame} for role in OUTFITS],
        'root_transform_changed':False, 'pose_or_physics_changed':False, 'asset_removed':False,
        'one_existing_world_object_history_transaction_required':True, 'applied':False}
