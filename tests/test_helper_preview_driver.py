"""Pure-Python domain controls for the adjacent helper-preview QA driver.

No runtime subprocess, Git mutation, original model or native input is used.
Every fake project and failed snapshot is retained in a fresh owned folder.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import os
import sys
import time
import traceback
import types
import uuid
from unittest.mock import patch

sys.dont_write_bytecode = True
SOURCE = Path(__file__).resolve()
DRIVER = SOURCE.with_name('verify_helper_preview.py')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stamp(path):
    path = Path(path); value = path.stat()
    return {'path': str(path), 'bytes': value.st_size, 'mtime_ns': value.st_mtime_ns,
            'sha256': sha(path)}


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


class Domain:
    def __init__(self, driver, folder):
        self.driver = driver; self.folder = folder
        self.checks = []; self.failures = []; self.refusals = []
        self.projects = []

    def need(self, ok, label):
        self.checks.append(label)
        if not ok:
            self.failures.append(label)

    def refuses(self, call, label, marker=None):
        try:
            call()
        except (RuntimeError, ValueError, OSError) as error:
            self.refusals.append({'label': label, 'type': type(error).__name__, 'message': str(error)})
            self.need(marker is None or marker in str(error), label)
        else:
            self.need(False, label)

    def project(self, name, *, changed=None, omitted=None, manifest_change=None, extras=None):
        root = self.folder / name; root.mkdir(parents=True, exist_ok=False)
        omitted = set(omitted or []); changed = changed or {}; extras = extras or {}
        required = list(dict.fromkeys(self.driver.RUNTIME_FILES + self.driver.TEST_FILES))
        rows = []
        for relative in required:
            reviewed = ('# self-authored reviewed fixture: ' + relative + '\nline two\n').encode()
            actual = changed.get(relative, reviewed)
            if relative not in omitted:
                target = root / relative; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(actual)
            rows.append({'path': relative, 'sha256': hashlib.sha256(reviewed).hexdigest(),
                         'lf_sha256': hashlib.sha256(reviewed.replace(b'\r\n', b'\n')).hexdigest()})
        for relative, values in extras.items():
            reviewed, actual = values
            target = root / relative; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(actual)
            rows.append({'path': relative, 'sha256': hashlib.sha256(reviewed).hexdigest(),
                         'lf_sha256': hashlib.sha256(reviewed.replace(b'\r\n', b'\n')).hexdigest()})
        for name in self.driver.TOP:
            path = root / name
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'owned self-authored top-level fixture\n')
        doc = {'format': 'has_helper_preview_main_port_files_1', 'files': rows}
        if manifest_change:
            manifest_change(doc)
        write(root / 'tests/helper_preview_port_files.json', doc)
        self.projects.append(root)
        return root

    def path_controls(self):
        driver = self.driver
        for valid in ['src/app.gd', 'tests/name with spaces.py', 'data/unicode-' + chr(39080) + '.json']:
            self.need(driver.relative(valid).as_posix() == valid, 'canonical relative path accepts ' + valid)
        for invalid in ['', '../src/app.gd', 'src/../app.gd', '/absolute.gd', 'C:/drive.gd',
                        'C:relative.gd', 'src\\app.gd', 'src/app.gd:ads', 'src//app.gd', './src/app.gd', '//server/share.gd']:
            self.refuses(lambda invalid=invalid: driver.relative(invalid), 'relative path rejects ' + repr(invalid))
        boundary = self.folder / 'owned paths'; boundary.mkdir()
        target = boundary / 'inside/deeper/file.json'
        self.need(driver.owned(target, boundary) == target, 'owned accepts a fresh contained nested target')
        self.need(driver.owned(boundary, boundary, True) == boundary, 'owned equality is available only by explicit opt-in')
        self.refuses(lambda: driver.owned(boundary, boundary), 'owned equal boundary refuses by default')
        self.refuses(lambda: driver.owned(boundary.parent / 'outside', boundary), 'owned outside sibling refuses')
        self.refuses(lambda: driver.owned(boundary / 'child/../escape', boundary), 'owned lexical traversal refuses')
        self.refuses(lambda: driver.owned(boundary / 'file.gd:ads', boundary), 'owned ADS component refuses')
        marked = boundary / 'marked'; marked.mkdir()
        original = Path.lstat

        def reparse(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            if path == marked:
                return types.SimpleNamespace(st_mode=result.st_mode, st_file_attributes=0x400)
            return result

        with patch.object(Path, 'lstat', reparse):
            self.refuses(lambda: driver.owned(marked, boundary), 'owned real path with Windows reparse attribute refuses', 'reparse')

    def manifest_controls(self):
        driver = self.driver
        root = self.project('manifest-source')
        cache = root / 'src/__pycache__'; cache.mkdir()
        (cache / 'ignored.pyc').write_bytes(b'not executable; generated fixture')
        (root / 'src/also-ignored.pyc').write_bytes(b'not executable; generated fixture')
        (root / 'src/genuine.pyc.gd').write_bytes(b'# an ordinary source extension\n')
        (root / 'src/nested').mkdir(); (root / 'src/nested/value.gd').write_bytes(b'# nested source\n')
        (root / 'output').mkdir(); (root / 'output/not-source.gd').write_bytes(b'# generated output\n')
        before = driver.source_manifest(root)
        self.need('src/nested/value.gd' in before and 'src/genuine.pyc.gd' in before,
                  'source manifest includes nested and genuine source files')
        self.need(not any('__pycache__' in key or key.endswith('.pyc') for key in before),
                  'source manifest excludes generated bytecode only')
        self.need(not any(key.startswith('output/') for key in before) and all(name in before for name in driver.TOP),
                  'source manifest includes approved top-level files and excludes generated output')
        self.need(before['src/nested/value.gd'] == driver.identity(root / 'src/nested/value.gd'),
                  'source manifest binds actual byte size, nsmtime and SHA')
        marked = root / 'src/nested/value.gd'; original = Path.lstat

        def reparse(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            if path == marked:
                return types.SimpleNamespace(st_mode=result.st_mode, st_file_attributes=0x400)
            return result

        with patch.object(Path, 'lstat', reparse):
            self.refuses(lambda: driver.source_manifest(root), 'source manifest rejects a reparse member rather than silently copying it', 'reparse')

    def reviewed_controls(self):
        driver = self.driver; required = list(dict.fromkeys(driver.RUNTIME_FILES + driver.TEST_FILES))
        root = self.project('reviewed-exact')
        proof = driver.validate_port(root)
        self.need(set(proof) == set(required) and all(row['reconstruction'] == 'exact bytes' for row in proof.values()),
                  'reviewed exact main pins admit the complete required source set')
        duplicate = self.project('reviewed-duplicate', manifest_change=lambda doc: doc['files'].append(dict(doc['files'][0])))
        self.refuses(lambda: driver.validate_port(duplicate), 'duplicate reviewed source pin refuses', 'Repeated reviewed')
        missing = self.project('reviewed-missing-pin', manifest_change=lambda doc: doc['files'].pop())
        self.refuses(lambda: driver.validate_port(missing), 'missing required reviewed source pin refuses', 'omits required')
        absent = self.project('reviewed-missing-file', omitted=[required[0]])
        self.refuses(lambda: driver.validate_port(absent), 'advertised reviewed file missing on disk refuses', 'Missing reviewed')

        def wrong(doc):
            doc['files'][0]['sha256'] = '0' * 64; doc['files'][0]['lf_sha256'] = '0' * 64

        mismatch = self.project('reviewed-wrong-pin', manifest_change=wrong)
        self.refuses(lambda: driver.validate_port(mismatch), 'wrong reviewed SHA refuses', 'Unreviewed helper main bytes')
        relative = required[0]; reviewed = ('# self-authored reviewed fixture: ' + relative + '\nline two\n').encode()
        crlf = self.project('reviewed-crlf', changed={relative: reviewed.replace(b'\n', b'\r\n')})
        self.refuses(lambda: driver.validate_port(crlf), 'CRLF bytes require explicit normalized opt-in', 'Unreviewed helper main bytes')
        proof = driver.validate_port(crlf, True)
        self.need(proof[relative]['actual_sha256'] != proof[relative]['reviewed_sha256'] and 'CRLF-to-LF only' in proof[relative]['reconstruction'],
                  'explicit CRLF-only opt-in records actual and reviewed hashes separately')
        before = driver.source_manifest(crlf)
        copy = crlf / 'output/Studio'
        copied = driver.copy_snapshot(crlf, copy, before)
        self.need(copied == before and (copy / relative).read_bytes() == (crlf / relative).read_bytes(),
                  'CRLF admission never normalizes copied bytes or relaxes preservation')
        edited = self.project('reviewed-crlf-edited', changed={relative: b'changed content\r\n' + reviewed.replace(b'\n', b'\r\n')})
        self.refuses(lambda: driver.validate_port(edited, True), 'CRLF opt-in cannot hide an actual content edit', 'Unreviewed helper main bytes')
        lone = self.project('reviewed-lone-cr', changed={relative: reviewed.replace(b'\n', b'\r')})
        self.refuses(lambda: driver.validate_port(lone, True), 'CRLF opt-in does not normalize lone carriage returns', 'Unreviewed helper main bytes')
        binary = self.project('reviewed-binary-eol', extras={'data/payload.bin': (b'payload\n', b'payload\r\n')})
        self.refuses(lambda: driver.validate_port(binary, True), 'normalized opt-in does not apply to binary suffixes', 'Unreviewed helper main bytes')

    def snapshot_controls(self):
        driver = self.driver
        root = self.project('snapshot-positive'); before = driver.source_manifest(root)
        result = driver.copy_snapshot(root, root / 'output/Studio', before)
        self.need(result == before and driver.source_manifest(root) == before,
                  'fresh snapshot preserves the exact full source set and source bytes')
        protected = {str(root / key): value for key, value in before.items()}
        self.need(driver.records_unchanged(protected), 'identity records accept unchanged real files')
        self.refuses(lambda: driver.copy_snapshot(root, root / 'output/Studio', before), 'snapshot never replaces an existing destination', 'must be fresh')
        self.refuses(lambda: driver.copy_snapshot(root, self.folder / 'outside-snapshot', before), 'snapshot output outside project output refuses', 'escapes owned boundary')
        early = self.project('snapshot-early-edit'); old = driver.source_manifest(early); target = early / 'src/app.gd'
        (early / 'before-app.gd.txt').write_bytes(target.read_bytes()); target.write_bytes(target.read_bytes() + b'# early edit\n')
        self.refuses(lambda: driver.copy_snapshot(early, early / 'output/Studio', old), 'early source edit refuses snapshot', 'Source changed before snapshot copy')
        self.need(not driver.records_unchanged({str(early / key): value for key, value in old.items()}),
                  'records detect a real early source edit')
        late = self.project('snapshot-late-edit'); old = driver.source_manifest(late); copied_source = late / 'src/app.gd'
        (late / 'before-app.gd.txt').write_bytes(copied_source.read_bytes()); real_copy = driver.shutil.copy2; changed = []

        def late_edit(src, dst, *args, **kwargs):
            result = real_copy(src, dst, *args, **kwargs)
            if Path(src) == copied_source:
                copied_source.write_bytes(copied_source.read_bytes() + b'# edit after this file was copied\n'); changed.append(True)
            return result

        with patch.object(driver.shutil, 'copy2', late_edit):
            self.refuses(lambda: driver.copy_snapshot(late, late / 'output/Studio', old), 'late source edit fails final complete-set gate', 'source set changed during snapshot')
        self.need(changed == [True], 'late-edit negative really executes after the source was copied')
        added = self.project('snapshot-late-addition'); old = driver.source_manifest(added); first = added / 'src/app.gd'

        def late_add(src, dst, *args, **kwargs):
            result = real_copy(src, dst, *args, **kwargs)
            if Path(src) == first:
                (added / 'src/late-added.gd').write_bytes(b'# new source after manifest capture\n')
            return result

        with patch.object(driver.shutil, 'copy2', late_add):
            self.refuses(lambda: driver.copy_snapshot(added, added / 'output/Studio', old), 'late source addition fails complete-set gate', 'source set changed during snapshot')
        self.need(driver.records_unchanged({str(added / key): value for key, value in old.items()}),
                  'late-addition control preserves every old file, proving set comparison adds coverage')
        corrupt = self.project('snapshot-corrupt-copy'); old = driver.source_manifest(corrupt)

        def corrupt_copy(src, dst, *args, **kwargs):
            result = real_copy(src, dst, *args, **kwargs)
            if Path(src) == corrupt / 'src/app.gd':
                Path(dst).write_bytes(Path(dst).read_bytes() + b'# wrong copied bytes\n')
            return result

        with patch.object(driver.shutil, 'copy2', corrupt_copy):
            self.refuses(lambda: driver.copy_snapshot(corrupt, corrupt / 'output/Studio', old), 'wrong copied bytes refuse before launch', 'Snapshot bytes/size/mtime differ')
        touched = self.project('snapshot-nsmtime'); target = touched / 'src/app.gd'; old_identity = driver.identity(target)
        os.utime(target, ns=(target.stat().st_atime_ns, old_identity['mtime_ns'] + 1_000_000))
        self.need(sha(target) == old_identity['sha256'] and not driver.records_unchanged({str(target): old_identity}),
                  'nsmtime-only change remains a preservation failure despite identical bytes')

    def status_controls(self):
        driver = self.driver
        kept, ignored = driver.functional_status(b' M src/__pycache__/a.cpython-313.pyc\0?? tests/cache.pyc\0')
        self.need(kept == [] and len(ignored) == 2, 'bytecode-only Git status is explicitly ignored')
        kept, ignored = driver.functional_status(b' M src/app.gd\0')
        self.need(len(kept) == 1 and ignored == [], 'ordinary functional source edit stays dirty')
        kept, ignored = driver.functional_status(b'R  src/__pycache__/app.pyc\0src/app.gd\0')
        self.need(len(kept) == 1 and kept[0]['paths'] == ['src/__pycache__/app.pyc', 'src/app.gd'] and ignored == [],
                  'rename from real source into bytecode cache stays functional-dirty')
        kept, ignored = driver.functional_status(b'C  tests/cache.pyc\0tests/source.py\0')
        self.need(len(kept) == 1 and ignored == [], 'copy from real source into generated destination stays functional-dirty')
        kept, ignored = driver.functional_status(b'R  src/new.pyc\0src/old.pyc\0')
        self.need(kept == [] and len(ignored) == 1, 'rename wholly within bytecode remains generated-only')
        kept, ignored = driver.functional_status(b' M src/name with spaces.gd\0')
        self.need(kept[0]['paths'] == ['src/name with spaces.gd'], 'NUL porcelain keeps unquoted filenames with spaces')
        self.refuses(lambda: driver.functional_status(b'R  src/new.gd\0'), 'missing renamed origin refuses malformed porcelain', 'Missing Git renamed source path')
        self.refuses(lambda: driver.functional_status(b'X\0'), 'malformed source status refuses', 'Malformed Git porcelain')

    def command_controls(self):
        driver = self.driver; project = self.folder / 'command actual project'; project.mkdir()
        target = project / 'output/job with spaces'; script = 'res://tests/owned_case.gd'
        arguments = [str(project / 'request with spaces.json'), '--display-driver', 'headless']
        calls = []

        def runner(path, _name):
            self.need(Path(path) == project / 'run.py', 'command imports the staged run.py rather than a cached runner')

            def command(name, headless, extra):
                calls.append({'script': name, 'headless': headless,
                              'environment': os.environ.get('HYBRID_GODOT')})
                engine = [str(driver.GODOT), '--path', str(project), '--log-file', str(project / 'output/default-engine.log'), '--script', name]
                if headless:engine.append('--headless')
                engine += extra
                if headless:return engine
                return [str(driver.PYTHONW), str(project / 'tools/private_desktop.py'), '--receipt', str(project / 'output/default-receipt.json'), '--', *engine]

            return types.SimpleNamespace(ROOT=project, __file__=str(project / 'run.py'), command=command)

        def actual(graphical):
            with patch.object(driver, 'load_module', runner):
                return driver.command(project, script, target, arguments, graphical)

        with patch.dict(os.environ, {'HYBRID_GODOT': 'preexisting-test-value'}):
            cmd = actual(False)
            self.need(os.environ['HYBRID_GODOT'] == 'preexisting-test-value', 'command restores an existing engine environment choice')
        old = os.environ.pop('HYBRID_GODOT', None)
        try:
            graphics = actual(True)
            self.need('HYBRID_GODOT' not in os.environ, 'command restores an absent engine environment choice')
        finally:
            if old is not None:os.environ['HYBRID_GODOT'] = old
        self.need(cmd[0] == str(driver.GODOT) and cmd[cmd.index('--path') + 1] == str(project),
                  'CPU command uses approved absolute engine and actual project root')
        self.need('--headless' in cmd[:cmd.index('--')] and cmd[cmd.index('--') + 1:] == arguments,
                  'CPU command keeps headless engine selection separate from user arguments')
        logs = [cmd[index + 1] for index, value in enumerate(cmd) if value == '--log-file']
        self.need(logs[-1] == str(target / 'engine.log') and cmd[cmd.index('--script') + 1] == script,
                  'CPU command binds actual owned log and script')
        cmd = graphics
        separator = cmd.index('--'); engine = cmd[separator + 1:]; user = engine.index('--')
        self.need(cmd[:2] == [str(driver.PYTHONW), str(project / 'tools/private_desktop.py')] and cmd[cmd.index('--receipt') + 1] == str(target / 'private-receipt.json'),
                  'graphical command uses approved private launcher from the actual project and owned receipt')
        self.need(engine[0] == str(driver.GODOT) and engine[engine.index('--path') + 1] == str(project) and '--headless' not in engine[:user],
                  'graphical engine remains absolute and private-project bound without a headless fallback')
        self.need(engine[user + 1:] == arguments and cmd.count('--') == 2,
                  'argument-like display flags remain data after both wrapper and engine boundaries')
        self.need(len(calls) == 2 and all(row['environment'] == str(driver.GODOT) for row in calls) and calls[0]['headless'] and not calls[1]['headless'],
                  'real command seam requests pinned staged runner headless/graphical modes without executing it')
        for field in ['ROOT', '__file__']:
            fake = runner(project / 'run.py', 'negative')
            setattr(fake, field, project.parent / ('foreign-' + field))
            with patch.object(driver, 'load_module', return_value=fake):
                self.refuses(lambda: driver.command(project, script, target, arguments), 'foreign staged runner ' + field + ' refuses', 'Runner differs')
        for label, graphical, mutate, marker in [
                ('wrong engine', False, lambda values: values.__setitem__(0, str(project / 'wrong.exe')), 'Approved headless'),
                ('missing headless', False, lambda values: values.remove('--headless'), 'Approved headless'),
                ('wrong project', False, lambda values: values.__setitem__(values.index('--path') + 1, str(project.parent)), 'Actual command path'),
                ('duplicate project', False, lambda values: values.extend(['--path', str(project)]), 'Actual command path'),
                ('wrong private launcher', True, lambda values: values.__setitem__(0, str(project / 'wrong-pythonw.exe')), 'Approved private'),
                ('wrong private helper', True, lambda values: values.__setitem__(1, str(project / 'wrong-helper.py')), 'Approved private'),
                ('duplicate receipt', True, lambda values: values.extend(['--receipt', str(target / 'extra.json')]), 'Approved private'),
                ('wrong wrapped engine', True, lambda values: values.__setitem__(values.index('--') + 1, str(project / 'wrong-engine.exe')), 'Private runner selected')]:
            fake = runner(project / 'run.py', 'negative'); real_command = fake.command

            def bad_command(*args, _real=real_command, _mutate=mutate, **kwargs):
                value = _real(*args, **kwargs); _mutate(value); return value

            fake.command = bad_command
            with patch.object(driver, 'load_module', return_value=fake):
                self.refuses(lambda graphical=graphical: driver.command(project, script, target, arguments, graphical), 'command rejects ' + label, marker)

    def result_controls(self):
        driver = self.driver
        main = self.folder / 'metadata-main'; project = main / 'output/Studio'; project.mkdir(parents=True)
        expected = {'source_context': 'main_source_snapshot', 'source_manifest_sha256': 'a' * 64,
                    'main_revision': 'b' * 40, 'main_root': str(main), 'project_root': str(project)}
        cpu = dict(expected, mode='adapter', checks=['first', 'second'], failures=[])
        graphics = {'mode': 'focused', 'checks': 2, 'failures': 0, 'metrics': dict(expected)}
        self.need(driver.result_binding(cpu, expected, 'adapter'), 'CPU result binds exact required main source metadata')
        self.need(driver.result_binding(graphics, expected, 'focused', True), 'graphical result binds source metadata inside actual metrics')
        working = dict(expected, source_context='main_working_source_snapshot')
        self.need(driver.result_binding(dict(working, mode='adapter'), working, 'adapter'), 'explicit working-source result remains distinguishable and bindable')
        alias = copy.deepcopy(cpu); alias['main_root'] = str(main).replace('\\', '/') + '/.'
        self.need(driver.result_binding(alias, expected, 'adapter'), 'absolute equivalent resolved root spelling is accepted')
        for key in expected:
            missing = dict(cpu); del missing[key]
            self.need(not driver.result_binding(missing, expected, 'adapter'), 'missing CPU result field refuses: ' + key)
            wrong = dict(cpu)
            wrong[key] = str(main / 'foreign') if key.endswith('_root') else 'wrong-value'
            self.need(not driver.result_binding(wrong, expected, 'adapter'), 'wrong CPU result field refuses: ' + key)
        for label, value, graphical, mode in [
                ('missing mode', {k: v for k, v in cpu.items() if k != 'mode'}, False, 'adapter'),
                ('wrong mode', dict(cpu, mode='host'), False, 'adapter'),
                ('relative main root', dict(cpu, main_root='relative-main'), False, 'adapter'),
                ('nonstring project root', dict(cpu, project_root=17), False, 'adapter'),
                ('missing GPU metrics', {'mode': 'focused', **expected}, True, 'focused'),
                ('non-dictionary GPU metrics', {'mode': 'focused', 'metrics': []}, True, 'focused'),
                ('CPU metadata hidden in metrics', {'mode': 'adapter', 'metrics': expected}, False, 'adapter'),
                ('nondictionary result', [], False, 'adapter')]:
            self.need(not driver.result_binding(value, expected, mode, graphical), 'result binding refuses ' + label)
        # Exercise the actual run_job gate with a pure fake invoke. No process
        # or runtime is called; count/exit0 alone must not admit stale metadata.
        for label, graphical, change, clean, exit_code in [
                ('cpu-bound', False, False, True, 0), ('cpu-unbound', False, True, True, 0),
                ('gpu-bound', True, False, True, 0), ('gpu-unbound', True, True, True, 0),
                ('gpu-unclean', True, False, False, 0), ('cpu-nonzero', False, False, True, 2)]:
            def invoke(_args, _project, target, _timeout, _graphical=False, label=label,
                       graphical=graphical, change=change, clean=clean, exit_code=exit_code):
                target.mkdir(parents=True, exist_ok=False)
                context = dict(expected)
                if change:context['main_revision'] = 'c' * 40
                value = {'mode': label, 'checks': 2, 'failures': 0}
                if graphical:value['metrics'] = context
                else:value.update(context)
                write(target / 'result.json', value)
                if graphical:write(target / 'private-receipt.json', {'exit': 0, 'job_closed': clean, 'desktop_closed': True,
                                   'child_desktop_confirmed': True, 'private_window_seen': True,
                                   'foreground_child_observed': False, 'desktop_switch_requested': False})
                return {'exit': exit_code, 'timed_out': False, 'retained_Popen_reaped': True, 'error_markers': []}

            with patch.object(driver, 'command', return_value=['not-executed']), patch.object(driver, 'invoke', invoke):
                row = driver.run_job(project, label, 'res://tests/not-executed.gd', [], 2, expected, graphical)
            self.need(row['passed'] == (not change and clean and exit_code == 0), 'actual run_job combines metadata/count/exit/private gates: ' + label)

    def preparation_drift_control(self):
        driver = self.driver; root = self.project('main-preparation-drift')
        runtime = root / 'fake-runtime.data'; runtime.write_bytes(b'owned nonexecutable test token\n')
        invocations = []; mutated = []

        class Factory:
            @staticmethod
            def build(project, destination, _hashes, _native):
                destination.mkdir(parents=True)
                target = project / 'src/app.gd'; target.write_bytes(target.read_bytes() + b'# counterfactual fixture-prep drift\n'); mutated.append(str(target))
                source = destination / 'host.glb'; source.write_bytes(b'not a model; no parser/runtime is invoked\n')
                plan = destination / 'plan.json'; write(plan, {'cases': []})
                return {'plan_path': str(plan), 'host_source': str(source), 'expected_adapter_checks': 128, 'protected_native': []}

        def load(path, _name):
            if Path(path).name != 'helper_preview_fixtures.py':
                raise AssertionError('No runner may load after preparation drift')
            return Factory

        def invoke(*_args, **_kwargs):
            invocations.append(True); raise AssertionError('No runtime may launch after preparation drift')

        state = {'revision': 'b' * 40, 'working_status': [], 'ignored_generated_status': [], 'source_context': 'main_source_snapshot'}
        with patch.object(driver, 'ROOT', root), patch.object(driver, 'RUNTIMES', {str(runtime): sha(runtime)}), \
                patch.object(driver, 'source_state', return_value=state), patch.object(driver, 'git', return_value=state['revision']), \
                patch.object(driver, 'load_module', load), patch.object(driver, 'invoke', invoke):
            result = driver.main(['--mode', 'prepare'])
        reports = list((root / 'output/helper-preview').glob('*/verification.json'))
        self.need(result == 1 and len(reports) == 1 and mutated and not invocations,
                  'counterfactual fixture preparation drift fails before every runtime launch')
        report = json.loads(reports[0].read_bytes())
        self.need(not report['passed'] and 'Preparation changed functional main snapshot bytes before execution' in report['error'],
                  'preparation drift records an explicit failed verification rather than a new accepted baseline')

    def run(self):
        self.path_controls(); self.manifest_controls(); self.reviewed_controls()
        self.snapshot_controls(); self.status_controls(); self.command_controls()
        self.result_controls()
        self.preparation_drift_control()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    installed_root = SOURCE.parents[1]
    family = (installed_root / 'output/helper-preview-driver-domain'
              if (installed_root / 'project.godot').is_file()
              else SOURCE.parents[2] / 'driver-domain')
    family = family.resolve()
    output = args.output if args.output is not None else family / (str(time.time_ns()) + '-' + uuid.uuid4().hex[:8])
    if not output.is_absolute() or output.resolve() == family or not output.resolve().is_relative_to(family) or '..' in output.parts or output.exists():
        parser.error('Use a fresh absolute owned folder inside ' + str(family))
    output.mkdir(parents=True, exist_ok=False)
    protected = [stamp(SOURCE), stamp(DRIVER)]
    domain = None; error = None; blocked = []

    def no_process(*args, **kwargs):
        blocked.append(repr(args[:1])); raise AssertionError('Domain controls may not launch a runtime/Git subprocess')

    try:
        with patch('subprocess.Popen', no_process), patch('subprocess.run', no_process), patch('subprocess.check_output', no_process), patch('subprocess.call', no_process):
            spec = importlib.util.spec_from_file_location('owned_helper_preview_driver_domain', DRIVER)
            driver = importlib.util.module_from_spec(spec); spec.loader.exec_module(driver)
            domain = Domain(driver, output); domain.run()
    except Exception as failure:
        error = {'type': type(failure).__name__, 'message': str(failure), 'traceback': traceback.format_exc()}
        if domain is not None:
            domain.failures.append('unexpected domain exception')
    unchanged = all(Path(row['path']).is_file() and stamp(row['path']) == row for row in protected)
    if domain is not None:
        domain.need(unchanged, 'domain source and adjacent driver stay hash/size/nsmtime exact')
        domain.need(blocked == [], 'all controls complete without any subprocess attempt')
    result = {'format': 'has_helper_preview_driver_domain_1', 'checks': domain.checks if domain else [],
              'failures': domain.failures if domain else ['driver import failed'],
              'refusals': domain.refusals if domain else [], 'error': error,
              'source_preservation': unchanged, 'protected_sources': protected,
              'subprocess_attempts': blocked, 'runtime_processes': 0, 'native_inputs': False,
              'graphical_acceptance': 'UNRUN'}
    write(output / 'result.json', result)
    print(json.dumps({'folder': str(output), 'checks': len(result['checks']),
                      'failures': result['failures'], 'error': error,
                      'source_preservation': unchanged}), flush=True)
    return 0 if not result['failures'] and error is None and unchanged and not blocked else 1


if __name__ == '__main__':
    raise SystemExit(main())
