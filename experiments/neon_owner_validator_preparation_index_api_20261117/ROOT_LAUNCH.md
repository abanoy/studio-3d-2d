# Root cold187 launch and independent closure

Run only after actual activated validator materialization and fresh Root lane ownership. Preserve Main's actual merged HEAD and every protected source/proof identity until the runtime finishes its final admission recheck. Use a new Python process; do not reuse a preparation interpreter containing cached Q/C/A modules.

The actual CLI is approved Python313 `-B -X utf8`, then `<actual new validator>/replay_runtime.py --output <fresh absolute ROOT/output validation directory> --run-gpu --lease-confirmed`. The validation directory must **not exist**. A separate fresh launch-evidence directory must already exist for the retained host's command/start/log/process files. Do not use that evidence directory as `--output`.

Reuse functions from two existing reviewed source files, without invoking their old hardcoded main entries:

| Role | Existing source | Exact SHA256 |
| --- | --- | --- |
| Independent Root scope observer | native_normal_known_factory_blender51_resource_20261117/root_runner.py | 012bef27696dd2752362426b162bfbd7afe9205febe76c489cd5ccab527648f6 |
| Retained coordinator invocation | normal_boundary_probe_actual_20261116/run_owned.py | d6fc7ab7dba85c69658ce01e463f81c95912abbfeb16375e62a34be6db23096b |

The observer's unchanged `closure(evidence, label)` includes scoped Python/native/canonical/replay/cold processes and excludes only its own observer/driver. The unchanged `invoke(evidence, 'cold187', command, 2000)` retains the exact coordinator Popen through communicate/reap and records its timeout/exit. Its failure/timeout cannot authorize a lease release. Neither helper's original main is appropriate for the new review; the old replay PowerShell launchers also hardcode historical revisions/paths.

Root's dedicated host sequence is:

```python
from pathlib import Path
import hashlib, importlib.util, sys
ROOT = Path(r'C:\a\Programming\cloudflare\has-acceptance-session-20261111')
runtime = ROOT / 'experiments/native_normal_known_factory_blender51_resource_20261117'
sys.path.insert(0, str(runtime))
def source_module(name, path, expected_sha):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); sys.modules[name] = value
    spec.loader.exec_module(value); return value
observer = source_module('_root_cold187_observer', runtime / 'root_runner.py',
    '012bef27696dd2752362426b162bfbd7afe9205febe76c489cd5ccab527648f6')
owned = source_module('_root_cold187_retained_host',
    ROOT / 'experiments/normal_boundary_probe_actual_20261116/run_owned.py',
    'd6fc7ab7dba85c69658ce01e463f81c95912abbfeb16375e62a34be6db23096b')
# Root supplies actual_validator/approved_validator_index_sha from materialization,
# a fresh existing evidence folder, and a distinct nonexistent validation_output.
observer.S.packet(runtime, '82727caa443cc58d623463e195fc6220d08c2d878cb93461eb481c722098b6e0')
observer.S.packet(actual_validator, approved_validator_index_sha)
assert evidence.is_dir() and not validation_output.exists() and evidence != validation_output
command = [r'C:\Program Files\Python313\python.exe', '-B', '-X', 'utf8',
           str(actual_validator / 'replay_runtime.py'), '--output', str(validation_output),
           '--run-gpu', '--lease-confirmed']
observer.closure(evidence, 'before-cold187')
process = None
try:
    process, _private_stdout = owned.invoke(evidence, 'cold187', command, 2000)
finally:
    # A failing observation retains Root ownership and all evidence.
    after = observer.closure(evidence, 'after-cold187')
assert process is not None and process['exit'] == 0
assert process['retained_Popen_reaped'] is True and process['timed_out'] is False
```

Root then independently reads the private runtime `verification.json`: passed true, four results, observed and expected totals both187, all preservation values true, no errors. Each result must retain its reaped, non-timed-out exit0 process proof and passing private receipt; inspect its `process-verification.json` and referenced actual `private-receipt.json` for private window, child desktop, job/desktop closure and no foreground/switch. Keep all raw reports, images, movies and logs private. Record the coordinator row/hash and independent zero-scope closure before declaring the lease released. On a timeout, failed receipt, unconfirmed process or nonzero scope, retain every output and keep ownership with Root; do not rerun into the used copy/output or clean it automatically.

These commands/procedures are source instructions only and were not executed during preparation. The observer's scope is the declared workspace/canonical patterns; it is not a universal PC inventory. A fresh current full is already required to be closed, and no concurrent native job may be started during cold187.
