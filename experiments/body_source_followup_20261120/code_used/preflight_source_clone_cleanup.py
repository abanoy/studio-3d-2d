from pathlib import Path
import argparse
import hashlib
import json
import os
import stat
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
CLONE = WORKSPACE / 'has-source-weights-prep-20261120'
PWSH = Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
PWSH_SHA = '2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    args = argparse.ArgumentParser()
    args.add_argument('--commit', required=True)
    options = args.parse_args()
    ready_path = ROOT / 'output/source-clone-root-cleanup-preflight.json'
    assert not ready_path.exists(), 'Never reuse a stale READY result'
    assert CLONE.resolve() == Path(r'C:\a\Programming\cloudflare\has-source-weights-prep-20261120')
    assert CLONE.resolve().parent == WORKSPACE.resolve() and CLONE.resolve() != ROOT.resolve()
    for folder in (CLONE, *CLONE.parents):
        assert not folder.is_symlink() and not folder.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, folder
    inventory_raw = (ROOT / 'experiments/source_clone_cleanup_20261120/INVENTORY.json').read_bytes()
    inventory = json.loads(inventory_raw)
    receipt_raw = (ROOT / 'output/body-full-source-remote-receipt.json').read_bytes()
    receipt = json.loads(receipt_raw)
    assert receipt['all_exact'] is True and receipt['commit'] == options.commit
    assert receipt['remote_main_observed'] == options.commit
    published = {r['path']: r for r in receipt['files']}
    packet = ROOT / 'experiments/source_clone_cleanup_20261120'
    for path in packet.rglob('*'):
        if path.is_file():
            relative = path.relative_to(ROOT).as_posix()
            raw = path.read_bytes()
            assert published[relative]['sha256'] == sha(raw) and published[relative]['bytes'] == len(raw), relative
    seen = {}
    directories = 0
    for parent, dirs, files in os.walk(CLONE, followlinks=False):
        for name in dirs:
            path = Path(parent) / name
            info = path.lstat()
            assert stat.S_ISDIR(info.st_mode) and not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, path
            directories += 1
        for name in files:
            path = Path(parent) / name
            before = path.lstat()
            assert stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and not before.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, path
            raw = path.read_bytes()
            after = path.lstat()
            assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_nlink) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_nlink), path
            seen[path.relative_to(CLONE).as_posix()] = dict(bytes=len(raw), sha256=sha(raw), mtime_ns=after.st_mtime_ns, nlink=after.st_nlink)
    expected = inventory['file_identities']
    assert set(seen) == set(expected) and len(seen) == 285
    for name, row in seen.items():
        assert row == {k: expected[name][k] for k in row}, name
    assert directories == inventory['summary']['directories_excluding_root'] == 46
    assert sum(r['bytes'] for r in seen.values()) == 4444966
    assert (CLONE / '.git').is_dir() and not (CLONE / '.git/commondir').exists()
    alternate = (CLONE / '.git/objects/info/alternates').read_text().strip()
    assert alternate == 'C:/a/Programming/cloudflare/has-acceptance-session-20261111/.git/objects'
    assert sha(PWSH.read_bytes()) == PWSH_SHA
    command = '[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); $ErrorActionPreference="Stop"; @(Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine) | ConvertTo-Json -Depth 3 -Compress'
    process = subprocess.Popen([str(PWSH), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        raw, stderr = process.communicate(timeout=45)
    except BaseException:
        if process.poll() is None:
            process.kill()  # This exact retained observer only, never owner processes.
        process.communicate(timeout=10)
        raise
    assert process.returncode == 0 and not stderr, 'CIM observer failed'
    (ROOT / 'output/PRIVATE_source_clone_cleanup_CIM.json').write_bytes(raw)
    rows = json.loads(raw.decode('utf-8-sig'))
    assert type(rows) is list and rows
    assert all(type(row) is dict and type(row.get('ProcessId')) is int and
               type(row.get('ParentProcessId')) is int and type(row.get('Name')) is str and
               all(row.get(k) is None or type(row.get(k)) is str for k in ('ExecutablePath', 'CommandLine'))
               for row in rows)
    assert len({row['ProcessId'] for row in rows}) == len(rows)
    target = str(CLONE).casefold().replace('/', '\\')
    blocked = []
    for row in rows:
        command_line = (row.get('CommandLine') or '').casefold().replace('/', '\\')
        executable = (row.get('ExecutablePath') or '').casefold().replace('/', '\\')
        if target in command_line or target in executable:
            blocked.append(row['ProcessId'])
    assert not blocked, 'Disposable clone is referenced by a live process'
    result = dict(format='has_source_clone_root_cleanup_preflight_1',
                  status='READY_TO_REMOVE_EXACT_OWNED_CLONE', target=str(CLONE.resolve()),
                  observed_ns=time.time_ns(), backup_commit=options.commit,
                  observed_unix_ms=time.time_ns()//1000000,
                  remote_receipt_sha256=sha(receipt_raw), inventory_sha256=sha(inventory_raw),
                  files=285, directories_excluding_root=46, logical_bytes=4444966,
                  all_hash_size_nsmtime_nlink_exact=True, no_links_reparse_or_multilinks=True,
                  path_containment_verified=True, external_alternate_store_not_traversed=True,
                  observer_exit=process.returncode, observer_retained_waited_reaped=True,
                  visible_process_command_path_matches=0, raw_process_rows_private=True,
                  cwd_and_open_handles_queried=False, root_known_owned_clone_work_finished=True,
                  process_inventory_sha256=sha(raw), process_inventory_bytes=len(raw),
                  original_owner_assets_and_shared_tools_untouched=True,
                  actual_delete_performed=False)
    with ready_path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
