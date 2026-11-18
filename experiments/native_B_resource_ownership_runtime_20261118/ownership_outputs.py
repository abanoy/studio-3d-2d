"""Separate additive metadata output; failures retain the parent's exact bytes."""
import hashlib
from ownership_metadata import collect_ownership_metadata
from survey_core import Limits, canonical, need


def collect_separate(bpy, private, public, limits=Limits()):
    baseline_private = canonical(private); baseline_public = canonical(public)
    try:
        extra, summary = collect_ownership_metadata(bpy, private, public, limits)
        need(summary['original_resource_summary'] == public
             and extra['original_issues'] == private['issues'], 'ORIGINAL_RESOURCE_OUTPUTS_CHANGED')
    except Exception:
        # Never serialize exception messages: they can contain private names/paths.
        extra = {'format': 'has_private_B_resource_ownership_unobserved_1',
                 'error_code': 'OWNERSHIP_COLLECTION_FAILED', 'original_resource_outputs_retained': True}
        summary = {'format': 'has_B_resource_ownership_unobserved_summary_1',
                   'ownership_observation': 'UNOBSERVED', 'error_code': 'OWNERSHIP_COLLECTION_FAILED',
                   'status': public['status'], 'profile_issues': public['profile_issues'],
                   'resource_profile_decision_changed': False,
                   'strict31_native_qualified': False, 'normal_tolerance_or_fidelity_qualified': False,
                   'export_repair_carrier_or_adoption_qualified': False}
    need(canonical(private) == baseline_private and canonical(public) == baseline_public,
         'ORIGINAL_RESOURCE_OUTPUTS_CHANGED')
    raw = canonical(extra); need(len(raw) <= limits.metadata_bytes, 'OWNERSHIP_OUTPUT_BOUND')
    return raw, summary


def validate_public(public, source_private_sha, source_public_sha, claims, profile, source_summary):
    """Pure public/binding check, including failure outputs without qualification."""
    need(type(public) is dict and set(public) == {'format', 'profile', 'ownership_metadata_collected',
         'source_resource_private_sha256', 'source_resource_public_sha256', 'summary', 'claims'},
         'EXACT_OWNERSHIP_OUTPUT_SCHEMA')
    need(public['format'] == 'has_session_B_resource_ownership_diagnostic_summary_1'
         and public['profile'] == profile and type(public['ownership_metadata_collected']) is bool
         and public['source_resource_private_sha256'] == source_private_sha
         and public['source_resource_public_sha256'] == source_public_sha
         and type(public['claims']) is dict and set(public['claims']) == set(claims)
         and all(value is False for value in public['claims'].values()), 'OWNERSHIP_OUTPUT_BINDING')
    summary = public['summary']
    need(type(summary) is dict and summary['status'] == source_summary['status']
         and type(summary['profile_issues']) is int
         and summary['profile_issues'] == source_summary['profile_issues'], 'ORIGINAL_RESOURCE_DECISION_CHANGED')
    need(summary['resource_profile_decision_changed'] is False
         and all(summary[key] is False for key in ('strict31_native_qualified',
                 'normal_tolerance_or_fidelity_qualified', 'export_repair_carrier_or_adoption_qualified')),
         'OWNERSHIP_QUALIFICATION_REFUSED')
    need((summary['format'] == 'has_B_resource_ownership_metadata_summary_1')
         is public['ownership_metadata_collected'], 'OWNERSHIP_COLLECTION_STATUS')
    if not public['ownership_metadata_collected']:
        need(summary['format'] == 'has_B_resource_ownership_unobserved_summary_1'
             and set(summary) == {'format', 'ownership_observation', 'error_code', 'status', 'profile_issues',
                  'resource_profile_decision_changed', 'strict31_native_qualified',
                  'normal_tolerance_or_fidelity_qualified', 'export_repair_carrier_or_adoption_qualified'}
             and summary['error_code'] == 'OWNERSHIP_COLLECTION_FAILED'
             and summary['ownership_observation'] == 'UNOBSERVED', 'OWNERSHIP_UNOBSERVED_REQUIRED')
    else:
        need(canonical(summary['original_resource_summary']) == canonical(source_summary),
             'ORIGINAL_RESOURCE_SUMMARY_CHANGED')
    return public


def write_outputs(stage, bpy, private, survey, claims, profile, request_sha, save):
    """Host calls only after both unchanged resource files and markers exist."""
    resource_private = stage / 'PRIVATE_RESOURCES.json'; resource_public = stage / 'PUBLIC_RESOURCES.json'
    parent_private_sha = hashlib.sha256(resource_private.read_bytes()).hexdigest()
    parent_public_sha = hashlib.sha256(resource_public.read_bytes()).hexdigest()
    need(parent_private_sha == survey['private_metadata_sha256'], 'PARENT_PRIVATE_OUTPUT_BINDING')
    raw, summary = collect_separate(bpy, private, survey)
    public = {'format': 'has_session_B_resource_ownership_diagnostic_summary_1', 'profile': profile,
              'ownership_metadata_collected': summary['format'] == 'has_B_resource_ownership_metadata_summary_1',
              'source_resource_private_sha256': parent_private_sha,
              'source_resource_public_sha256': parent_public_sha, 'summary': summary,
              'claims': {key: False for key in claims}}
    validate_public(public, parent_private_sha, parent_public_sha, claims, profile, survey)
    with (stage / 'PRIVATE_OWNERSHIP_METADATA.json').open('xb') as stream: stream.write(raw)
    public_path = stage / 'PUBLIC_OWNERSHIP_METADATA.json'; save(public_path, public)
    binding = {'format': 'has_session_B_ownership_output_binding_1', 'request_sha256': request_sha,
               'private_bytes': len(raw), 'private_sha256': hashlib.sha256(raw).hexdigest(),
               'public_sha256': hashlib.sha256(public_path.read_bytes()).hexdigest()}
    save(stage / 'PUBLIC_OWNERSHIP_BINDING.json', binding)
    need(hashlib.sha256(resource_private.read_bytes()).hexdigest() == parent_private_sha
         and hashlib.sha256(resource_public.read_bytes()).hexdigest() == parent_public_sha,
         'ORIGINAL_RESOURCE_FILES_CHANGED')
    return public, binding
