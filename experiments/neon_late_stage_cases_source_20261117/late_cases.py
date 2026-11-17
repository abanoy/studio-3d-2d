"""Source-only late-stage cases for the unchanged 07e37 root host; no launcher."""
import ast
import hashlib

VERIFY_RAW_SHA256 = '192aa4b889a367787f2368f58c95de5813628dbff80b01a5f7e640efdf1f2f0f'
VERIFY_LF_SHA256 = '004a368bb77147c40cf67e640a7070b30b00418b05148b20959f601fea0b0856'
ROOT_HOST_SHA256 = '07e37aa4ddba05e31658f2fe14bda53a25ce0f7646f2c966961a635ef6b85255'

# (canonical results label, tests/ basename, extra arguments, report, deadline)
# The host itself supplies REVIEW / 'tests' / script and retained hidden Popen.
CASES = (
    ('foot_hold', 'verify_foot_hold.py', (), 'foot-hold-verification.json', 180),
    ('foot_contacts_experiment', 'verify_foot_contacts.py', (), 'foot-contacts-verification.json', 180),
    ('contact_animation', 'verify_contact_animation.py', (), 'contact-animation-verification.json', 180),
    ('contact_editor', 'verify_contact_editor.py', (), 'contact-editor-verification.json', 180),
    ('contact_clipboard', 'verify_contact_clipboard.py', (), 'contact-clipboard-verification.json', 200),
    ('component_contact_clipboard', 'verify_contact_clipboard.py', ('--components',), 'component-contact-clipboard-verification.json', 200),
    ('contact_physics', 'verify_contact_physics.py', (), 'contact-physics-verification.json', 240),
    ('component_contact_physics', 'verify_contact_physics.py', ('--components',), 'component-contact-physics-verification.json', 240),
    ('contact_parent', 'verify_contact_parent.py', (), 'contact-parent-verification.json', 180),
    ('contact_correction', 'verify_contact_correction.py', (), 'contact-correction-verification.json', 200),
    ('contact_persistence', 'verify_contact_persistence.py', (), 'contact-persistence-verification.json', 1000),
    ('contact_bindings', 'verify_contact_bindings.py', (), 'contact-bindings-verification.json', 220),
    ('contact_identity', 'verify_contact_identity.py', (), 'contact-identity-verification.json', 360),
    ('contact_selection', 'verify_contact_selection.py', (), 'contact-selection-verification.json', 240),
    ('contact_transform', 'verify_contact_transform.py', (), 'contact-transform-verification.json', 240),
    ('contact_viewport', 'verify_contact_viewport.py', (), 'contact-viewport-verification.json', 340),
    ('multi_audio', 'verify_multi_audio.py', (), 'multi-audio-verification.json', 1000),
    ('project_duration', 'verify_project_duration.py', (), 'project-duration-verification.json', 1000),
    ('motion_assist', 'verify_motion_assist.py', (), 'motion-assist-verification.json', 90),
    ('motion_tracks', 'verify_motion_assist_tracks.py', (), 'motion-assist-tracks-verification.json', 90),
    ('motion_native_preview', 'verify_motion_assist_native.py', (), 'motion-assist-native-verification.json', 240),
    ('motion_model', 'verify_motion_animation.py', (), 'motion-animation-unit-verification.json', 90),
    ('motion_editor', 'verify_motion_animation_app.py', (), 'motion-animation-app-verification.json', 360),
    ('opacity', 'verify_opacity.py', (), 'opacity-verification.json', 220),
    ('brush_opacity', 'verify_brush_opacity.py', (), 'brush-opacity-verification.json', 380),
    ('brush_pressure', 'verify_brush_pressure.py', (), 'brush-pressure-verification.json', 400),
    ('layers', 'verify_layers.py', (), 'layers-verification.json', 200),
    ('onion', 'verify_onion.py', (), 'onion-verification.json', 200),
    ('fill', 'verify_fill.py', (), 'fill-verification.json', 240),
    ('fill_gaps', 'verify_fill_gaps.py', (), 'fill-gaps-verification.json', 500),
    ('fill_expand', 'verify_fill_expand.py', (), 'fill-expand-verification.json', 500),
    ('fill_connections', 'verify_fill_connections.py', (), 'fill-connections-verification.json', 500),
    ('palette', 'verify_palette.py', (), 'palette-verification.json', 500),
    ('drawing_history', 'verify_drawing_history.py', (), 'drawing-history-verification.json', 400),
    ('drawing_selection', 'verify_drawing_selection.py', (), 'drawing-selection-verification.json', 500),
    ('drawing_transform', 'verify_drawing_transform.py', (), 'drawing-transform-verification.json', 600),
    ('recovery_identity', 'verify_recovery_identity.py', (), 'recovery-identity-verification.json', 90),
    ('recovery_startup', 'verify_recovery_startup.py', (), 'recovery-startup-verification.json', 300),
    ('recovery_history', 'verify_recovery_history.py', (), 'recovery-history-verification.json', 300),
    ('recovery_schedule', 'verify_recovery_schedule.py', (), 'recovery-schedule-verification.json', 180),
    ('recovery_preview', 'verify_recovery_preview.py', (), 'recovery-preview-verification.json', 180),
    ('home', 'verify_home.py', (), 'home-verification.json', 240),
    ('tutorials', 'verify_tutorials.py', (), 'tutorials-verification.json', 260),
    ('first_movie', 'verify_first_movie.py', (), 'first-movie-verification.json', 300),
)


def _value(node, names):
    """Only source literals, loop names and the verifier's f-string expansion."""
    if isinstance(node, ast.Name):
        return names[node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        return tuple(_value(item, names) for item in node.elts)
    if isinstance(node, ast.JoinedStr):
        return ''.join(str(_value(item.value, names)) if isinstance(item, ast.FormattedValue)
                       else item.value for item in node.values)
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'sys' and node.attr == 'executable':
        return '<sys.executable>'
    return ast.literal_eval(node)


def _is_run(node):
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'run'


def cases_from_verify_ast(raw):
    """Extract only the canonical main() interval after color and before media.

    Does not import or execute verify.py or any wrapper. Contact and motion loops
    are expanded in source order; a newly introduced unsupported shape refuses.
    """
    tree = ast.parse(raw.decode('utf-8-sig'))
    main, = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main']
    color, = [node for node in ast.walk(main) if _is_run(node) and any(
        isinstance(part, ast.Constant) and part.value == 'tests/verify_color_sampler.py'
        for part in ast.walk(node))]
    media, = [node for node in main.body if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
              and isinstance(node.value.func, ast.Name) and node.value.func.id == 'verify_media']
    statements = [node for node in main.body if color.end_lineno < node.lineno < media.lineno]
    rows, pending = [], None

    def walk(statements, names):
        nonlocal pending
        for node in statements:
            if isinstance(node, ast.For):
                values = _value(node.iter, names)
                for item in values:
                    local = dict(names)
                    targets = node.target.elts if isinstance(node.target, ast.Tuple) else (node.target,)
                    items = item if isinstance(node.target, ast.Tuple) else (item,)
                    assert len(targets) == len(items)
                    for target, value in zip(targets, items):
                        assert isinstance(target, ast.Name)
                        local[target.id] = value
                    walk(node.body, local)
                assert not node.orelse
            elif isinstance(node, ast.If) and any(_is_run(part) for part in ast.walk(node)):
                test = node.test
                assert isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.In)
                assert len(test.comparators) == 1
                take = _value(test.left, names) in _value(test.comparators[0], names)
                walk(node.body if take else node.orelse, dict(names))
            elif isinstance(node, ast.Assign):
                if _is_run(node.value):
                    assert pending is None and len(node.value.args) == 1
                    command = _value(node.value.args[0], names)
                    assert command[:2] == ('<sys.executable>', '-u') and command[2].startswith('tests/')
                    assert all(isinstance(item, str) for item in command[2:])
                    assert len(node.value.keywords) == 1 and node.value.keywords[0].arg == 'timeout'
                    pending = [None, command[2].removeprefix('tests/'), tuple(command[3:]), None,
                               _value(node.value.keywords[0].value, names)]
                elif pending is not None:
                    reports = [part for part in ast.walk(node.value) if isinstance(part, ast.BinOp)
                               and isinstance(part.op, ast.Div) and isinstance(part.left, ast.Name)
                               and part.left.id == 'output']
                    if reports:
                        report, = reports
                        pending[3] = _value(report.right, names)
                    for target in node.targets:
                        if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == 'results':
                            pending[0] = _value(target.slice, names)
                            assert all(item is not None for item in pending)
                            rows.append(tuple(pending))
                            pending = None
                elif len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    try:
                        names[node.targets[0].id] = _value(node.value, names)
                    except (ValueError, KeyError, TypeError):
                        pass
    walk(statements, {})
    assert pending is None
    return tuple(rows)


def check_source(raw_verify, raw_host, cases=CASES):
    assert hashlib.sha256(raw_verify).hexdigest() == VERIFY_RAW_SHA256, 'canonical verifier raw bytes changed'
    assert hashlib.sha256(raw_verify.replace(b'\r\n', b'\n')).hexdigest() == VERIFY_LF_SHA256
    assert hashlib.sha256(raw_host).hexdigest() == ROOT_HOST_SHA256, 'root host changed'
    extracted = cases_from_verify_ast(raw_verify)
    assert len(extracted) == 44 and tuple(cases) == extracted, 'late cases differ from canonical order/fields'
    return extracted


def assert_canonical_report(label, report):
    """Retain only the additional report assertions present in canonical main().

    The original wrappers still execute unchanged and own their own assertions.
    Root can call this for each successful row's parsed report before accepting
    the targeted run. This helper performs no I/O and makes no full-pass claim.
    """
    assert label in {row[0] for row in CASES}
    if label.startswith('contact_'):
        if label == 'contact_persistence':
            assert report['writer']['failures'] == 0 and all(row['failures'] == 0 for row in report['readers'].values())
        else:
            assert report['failures'] == 0
        if label == 'contact_viewport':
            assert report['reader']['failures'] == 0
    elif label.startswith('component_contact_'):
        assert report['failures'] == 0
    elif label == 'project_duration':
        assert report['failures'] == 0 and len(report['fresh_readers']) == 4
    elif label.startswith('motion_'):
        assert report['failures'] == 0
        if label == 'motion_editor':
            assert report['reader']['failures'] == 0
