"""Author only: preserve legacy fixture bases; no engine/Main/Git operations."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'output/source-import-info-legacy-tests-prep-20261121'

def pin(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

def replace_once(data, old, new):
    old = old.replace('\n', '\r\n').encode()
    new = new.replace('\n', '\r\n').encode()
    assert data.count(old) == 1, old[:120]
    return data.replace(old, new, 1)

def main():
    assert not DEST.exists()
    DEST.mkdir()
    paths = ['tests/source_import_owner_unit.gd', 'tests/mmd_missing_texture_smoke.gd']
    original = {name: (ROOT/name).read_bytes() for name in paths}
    owner = replace_once(original[paths[0]], 'class PoseDouble extends RefCounted:\n\tvar additions: Array = []', '''class InfoDouble extends RefCounted:
	var reports: Array = []
	func notify_import(report: Variant) -> void:
		reports.append(report.duplicate(true) if report is Dictionary or report is Array else report)

class SequenceDouble extends RefCounted:
	var active_owner := ""

class PoseDouble extends RefCounted:
	var import_capabilities := InfoDouble.new()
	var additions: Array = []''')
    owner = replace_once(owner, 'class AppDouble extends Control:\n\tvar exporting := false', '''class AppDouble extends Control:
	var recovery_session := "authored-owner-fixture-session"
	var sequence_editor := SequenceDouble.new()
	var exporting := false''')
    # All original checks, launch/child ownership/release behavior and final53 marker
    # remain exact. Only the collaborator contract used by production was refreshed.
    assert owner[owner.index(b'class ImportDouble'): ] == original[paths[0]][original[paths[0]].index(b'class ImportDouble'): ]
    source = original[paths[1]]
    start = source.index(b'\tvar warning := false\r\n')
    end = source.index(b'\tif not warning or app.renderer.world_runtime.instances.size() != 1:\r\n', start)
    old = source[start:end]
    block = '''	var warning := false
	var closed_dialog: WeakRef
	var info = app.pose_editor.import_capabilities
	if app.renderer.world_runtime.instances.size() == 1:
		app.world_selection.select_entity(app.last_import_id,false)
		var imported: RefCounted = app.renderer.active_model()
		var report: Dictionary = info.report_for(imported)
		var before: Dictionary = app.current_world().duplicate(true)
		var before_keys: Array = app.keys.duplicate(true)
		var before_history: int = app.history.size()
		info.open(false)
		warning = meta.absent in report.get("missing_textures",[]) and report == imported.data.metadata.native_parameters
		warning = warning and is_instance_valid(info.window) and info.matches()
		if is_instance_valid(info.window):
			warning = warning and not info.window.exclusive and not info.window.unresizable
			warning = warning and ("Missing texture: "+str(meta.absent)) in info.summary_text.text
			warning = warning and "Restore the named texture files beside the original model, then import again." in info.summary_text.text
			closed_dialog = weakref(info.window)
			info.window.close_requested.emit()
		await process_frame
		await process_frame
		warning = warning and closed_dialog != null and closed_dialog.get_ref() == null
		warning = warning and app.current_world() == before and app.keys == before_keys and app.history.size() == before_history
'''.replace('\n','\r\n').encode()
    missing = source[:start] + block + source[end:]
    assert missing[missing.index(b'\tif not warning or'): ] == source[end:]
    assert missing[:start] == source[:start]
    outputs = dict(zip(paths,[owner,missing]))
    patches=[]; targets=[]
    for name in paths:
        for prefix, data in [('bases',original[name]),('payload',outputs[name])]:
            dest=DEST/prefix/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        targets.append({'path':name,'operation':'replace',**pin(outputs[name]),'base_bytes':len(original[name]),'base_sha256':pin(original[name])['sha256']})
    write=lambda name,value: (DEST/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    write('TARGETS.json', {'format':'has_import_info_legacy_tests_1','status':'SOURCE_ONLY_UNPARSED_UNRUN','targets':targets})
    write('PRESERVATION.json',{'owner_original_check_body_byte_exact':True,'owner_checks_expected':53,'owner_completed_cases_expected':6,'mmd_pre_import_and_entire_packed_reopen_offline_tail_byte_exact':True,'production_changed':False,'runtime_executed':False,'requires':'qualified Import info five production sources; owner53 actual Root qualification; optional native missing-texture test remains UNRUN'})
    (DEST/'README.md').write_text('''# Import info legacy fixture contracts

Source only; no engine execution or Main edits. The owner fixture now supplies the
read-only report collaborator and stable session/sequence identity read by the
qualified importer. All53 assertions,6 completed cases and the whole child-ownership
body are byte exact. This does not assert native conversion fidelity.

The optional missing-texture fixture inspects the actual imported actor's retained
report and persistent Import info action text, nonexclusive/resizable window,
deferred Close destruction and unchanged World/camera/history. Its pre-import,
portable packed branch and complete save/reopen tail are byte exact. The native
missing-texture run remains UNRUN until Root qualifies it. No modal is expected.

Original fixture bases are preserved. Candidate production files are unchanged.
''',encoding='utf-8')
    (DEST/'code_used').mkdir();shutil.copyfile(__file__,DEST/'code_used'/Path(__file__).name)
    files=[]
    for item in sorted(DEST.rglob('*')):
        if item.is_file():files.append({'path':item.relative_to(DEST).as_posix(),**pin(item.read_bytes())})
    write('SOURCE_PINS.json',{'format':'has_source_only_pins_1','status':'SOURCE_ONLY_UNPARSED_UNRUN_PENDING_PEER','files':files})
    print(json.dumps({'folder':str(DEST),'manifest':pin((DEST/'SOURCE_PINS.json').read_bytes()),'files':len(files)+1,'targets':targets},indent=2))

if __name__ == '__main__':main()
