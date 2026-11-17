"""Read-only observation after a separately admitted owned blend load.

This helper neither loads a blend nor accesses any resource pathname. Its
caller must prove pre-load admission; post-load RNA checks cannot provide it.
"""
import known_handler_policy as H
from export_provenance import classify_public_reference
from survey_core import Limits, canonical, collect_resources, need


def inspect_loaded_owned_scene(bpy, original_blend, owned_blend, public_reference, limits=Limits(), *, factory_baseline):
    """Pure host checks plus metadata queries; output only, no file writes."""
    need(bpy.app.background is True, 'BACKGROUND_REQUIRED')
    need(bpy.app.online_access is False, 'OFFLINE_REQUIRED')
    need(bpy.app.autoexec_fail is False, 'AUTOEXEC_FAILURE_REFUSED')
    need(bpy.context.preferences.filepaths.use_scripts_auto_execute is False, 'AUTOEXEC_DISABLED_REQUIRED')
    need(type(owned_blend) is str and bpy.data.filepath == owned_blend, 'OWNED_BLEND_PATH_REQUIRED')
    # This helper collects metadata without invoking handlers. The owned load
    # may already have invoked the exact matched installed factory callbacks.
    H.check_live(bpy.app.handlers, factory_baseline, 'AFTER_OWNED_B_OPEN')
    provenance = classify_public_reference(public_reference)
    private, public = collect_resources(bpy, original_blend, limits)
    # A second inventory detects changed RNA metadata or packed-data words. It
    # is read-only and remains bounded; no evaluated geometry is requested.
    again, again_public = collect_resources(bpy, original_blend, limits)
    need(canonical(private) == canonical(again) and canonical(public) == canonical(again_public), 'RESOURCE_OBSERVATION_CHANGED')
    public.update(resource_observation_repeated_exactly=True, export_branch=provenance['export_branch'],
                  original_export_options_observed=False, blend_saved=False, export_invoked=False,
                  known_original_file_identities_verified='CALLER_GATE_REQUIRED_NOT_OBSERVED_BY_COLLECTOR',
                  pre_load_dependency_admission='CALLER_GATE_REQUIRED_NOT_OBSERVED_BY_COLLECTOR')
    return private, public, provenance
