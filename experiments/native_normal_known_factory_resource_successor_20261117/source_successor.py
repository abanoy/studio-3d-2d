"""Pure narrow source derivation; caller supplies sealed public parent bytes."""
import hashlib

PARENTS = {
    'diagnostic_host.py': ('native_normal_resource_diagnostic_import_fix_20261117/diagnostic_host.py', '1b289ed174b0235c30903375f6bbe195b4bad6cfe0b2e507db4bb4dc255e32da'),
    'diagnostic_support.py': ('native_normal_resource_diagnostic_import_fix_20261117/diagnostic_support.py', '490d70028734f72a758c30ee32eb399afd3915359059cb2f6d308a64c4c9af09'),
    'root_runner.py': ('native_normal_resource_diagnostic_import_fix_20261117/root_runner.py', '6b374ae4ee1f2490fabcb34a096c1c00f345b9ede21a092ed1a4cd79113ca7e7'),
    'known_loaded_survey.py': ('native_normal_resource_survey_20261117/loaded_survey.py', '66f1f33e67ff8d7abb8214484d6fbc9fc43304a58069bdb4bc1848a360638f98'),
    'baseline_predicate.py': ('native_normal_factory_handler_baseline_20261117/baseline_predicate.py', '3fdc78893ca8f9403d22a479eaba2e29c5a6b615b59fe9092d9691b679c1bd7b'),
    'handler_metadata.py': ('native_normal_factory_handler_capture_20261117/handler_metadata.py', '0ea7cac7b9a4c289188e15b7ee826b5ba28dad76df1a080bec6e7d933a2296cc'),
}
OLD_LOOP = """    for name in ('load_pre', 'load_post', 'load_post_fail', 'depsgraph_update_pre', 'depsgraph_update_post',
                 'frame_change_pre', 'frame_change_post', 'render_pre', 'render_post', 'save_pre', 'save_post'):
        S.need(len(getattr(bpy.app.handlers, name)) == 0, 'Unexpected pre-load handler')
"""
OLD_LOADED_LOOP = """    # No handler is executed by this helper. A successor must independently
    # qualify handler admission before the load; this is an additional check.
    for name in ('load_pre', 'load_post', 'load_post_fail', 'depsgraph_update_pre', 'depsgraph_update_post',
                 'frame_change_pre', 'frame_change_post', 'render_pre', 'render_post', 'save_pre', 'save_post'):
        need(len(getattr(bpy.app.handlers, name)) == 0, 'UNEXPECTED_HANDLER_REFUSED')
"""
OBSERVATIONS = ('PRIVATE_HANDLERS_BEFORE.json', 'PRIVATE_HANDLERS_AFTER_LOAD.json', 'PRIVATE_HANDLERS_AFTER_RESOURCES.json')


def need(value, message):
    if not value: raise ValueError(message)


def rules(name, parent):
    text = parent.decode('utf-8')
    if name == 'diagnostic_support.py':
        begin = text.index('def validate_admission(')
        end = text.index('def check_snapshot(', begin)
        old_tail = """    validate_failed_full_lane(value, proof_data)
    need(safe(value['proofs']['review_functional_snapshot']['path']) == REVIEW / 'output' / FULL_RUN / 'source-after.json',
         'Exact failed Review source-after role required')
    check_snapshot(ROOT, proof_data['functional_snapshot'], ROOT_FUNCTIONAL_COMMIT, 1019)
    check_snapshot(REVIEW, proof_data['review_functional_snapshot'], CANDIDATE, 1029)
"""
        return [
            ("import re\n", "import re\nimport known_handler_policy as H\n"),
            ("PROFILE = 'SESSION_B_READONLY_RESOURCE_DIAGNOSTIC_AFTER_FAILED_FULL'\nCANDIDATE = '00bf0f916a549f5e858cb39dd91a149071fd5181'\nFULL_RUN = 'windows-neon-00bf0f9-replay2-20261117T155709412051'\n",
             "PROFILE = 'SESSION_B_READONLY_KNOWN_FACTORY_RESOURCE_DIAGNOSTIC'\n"),
            ("PROOFS = {'full_release', 'functional_snapshot', 'review_functional_snapshot', 'cold187_not_started_root_record'}",
             "PROOFS = {'functional_snapshot', 'review_functional_snapshot', 'closed_lane_root_record'}"),
            (text[begin:end], 'from current_context import validate_admission, validate_current_closed_lane\n\n\n'),
            (old_tail, """    validate_current_closed_lane(value, proof_data)
    check_snapshot(ROOT, proof_data['functional_snapshot'], value['functional_commit'], 1019)
    check_snapshot(REVIEW, proof_data['review_functional_snapshot'], value['candidate_commit'], 1029)
    H.read_bound_baseline(value['factory_baseline'], r, safe, ROOT)
"""),
        ]
    if name == 'diagnostic_host.py':
        return [
            ('from loaded_survey import inspect_loaded_owned_scene', 'from known_loaded_survey import inspect_loaded_owned_scene'),
            (OLD_LOOP, """    bound = S.H.read_bound_baseline(admitted[0]['factory_baseline'], r, S.safe, S.ROOT)
    observed = S.H.check_live(bpy.app.handlers, bound, 'BEFORE_OWNED_B_OPEN')
    S.save(stage / 'PRIVATE_HANDLERS_BEFORE.json', observed)
"""),
            ("        private, survey, provenance = inspect_loaded_owned_scene(bpy, str(original), str(owned), request['public_reference'])",
             """        # Opening the owned B can invoke the matched installed factory callbacks.
        observed = S.H.check_live(bpy.app.handlers, bound, 'AFTER_OWNED_B_OPEN')
        S.save(stage / 'PRIVATE_HANDLERS_AFTER_LOAD.json', observed)
        private, survey, provenance = inspect_loaded_owned_scene(bpy, str(original), str(owned), request['public_reference'], factory_baseline=bound)
    observed = S.H.check_live(bpy.app.handlers, bound, 'AFTER_RESOURCE_COLLECTION')
    S.save(stage / 'PRIVATE_HANDLERS_AFTER_RESOURCES.json', observed)"""),
            ("              'claims': {key: False for key in S.QUALIFICATIONS}, 'blend_saved': False, 'export_invoked': False}",
             """              'claims': {key: False for key in S.QUALIFICATIONS}, 'blend_saved': False, 'export_invoked': False,
              'factory_handlers': S.H.public_summary()}
    public['factory_handlers']['private_observations'] = {}
    for name in ('PRIVATE_HANDLERS_BEFORE.json', 'PRIVATE_HANDLERS_AFTER_LOAD.json', 'PRIVATE_HANDLERS_AFTER_RESOURCES.json'):
        raw = (stage / name).read_bytes()
        public['factory_handlers']['private_observations'][name] = {'bytes': len(raw), 'sha256': S.digest(raw)}"""),
        ]
    if name == 'known_loaded_survey.py':
        return [
            ('from export_provenance import classify_public_reference', 'import known_handler_policy as H\nfrom export_provenance import classify_public_reference'),
            ('def inspect_loaded_owned_scene(bpy, original_blend, owned_blend, public_reference, limits=Limits()):',
             'def inspect_loaded_owned_scene(bpy, original_blend, owned_blend, public_reference, limits=Limits(), *, factory_baseline):'),
            (OLD_LOADED_LOOP, """    # This helper collects metadata without invoking handlers. The owned load
    # may already have invoked the exact matched installed factory callbacks.
    H.check_live(bpy.app.handlers, factory_baseline, 'AFTER_OWNED_B_OPEN')
"""),
        ]
    if name == 'root_runner.py':
        anchor = "        S.need(all(typed_equal(sidecar['placement'].get(k), v) for k, v in PLACEMENT.items()), 'Hidden sentinel cleanup/policy failed')\n"
        return [(anchor, anchor + """        handlers = dict(public['factory_handlers']); observations = handlers.pop('private_observations')
        S.need(typed_equal(handlers, S.H.public_summary()), 'Exact known-factory public profile required')
        S.need(type(observations) is dict and set(observations) == {
            'PRIVATE_HANDLERS_BEFORE.json', 'PRIVATE_HANDLERS_AFTER_LOAD.json', 'PRIVATE_HANDLERS_AFTER_RESOURCES.json'}, 'Exact three private observation roles required')
        for name, descriptor in observations.items():
            S.need(type(descriptor) is dict and set(descriptor) == {'bytes', 'sha256'}
                   and type(descriptor['bytes']) is int and 0 < descriptor['bytes'] <= 524288, 'Bounded private handler observation required')
            path = stage / name
            S.need(path.stat().st_size == descriptor['bytes'] and S.digest(path.read_bytes()) == descriptor['sha256'], 'Private handler observation binding differs')
""")]
    need(name in ('baseline_predicate.py', 'handler_metadata.py'), 'Unknown successor source')
    return []


def render(name, parent):
    need(name in PARENTS and hashlib.sha256(parent).hexdigest() == PARENTS[name][1], 'Exact sealed public parent source required')
    text = parent.decode('utf-8')
    substitutions = rules(name, parent)
    for old, new in substitutions:
        need(text.count(old) == 1, 'Unique original substitution required')
        text = text.replace(old, new, 1)
    inverse = text
    for old, new in reversed(substitutions):
        need(inverse.count(new) == 1, 'Unique inverse substitution required')
        inverse = inverse.replace(new, old, 1)
    need(inverse.encode('utf-8') == parent, 'Whole-source inverse must restore exact parent bytes')
    compile(text, name, 'exec')  # Syntax only, never execution/import of host code.
    return text.encode('utf-8')
