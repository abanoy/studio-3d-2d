"""Create a narrow output-only completion ownership overlay; never port main."""
from pathlib import Path
import difflib,hashlib,json,shutil
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
original=ROOT/'src/source_import.gd'
old=original.read_bytes();baseline=hashlib.sha256(old).hexdigest()
history=BASE/'old-context';history.mkdir(exist_ok=False)
shutil.copy2(original,history/'source_import.gd')
target=BASE/'source/src/source_import.gd';target.parent.mkdir(parents=True,exist_ok=True)
text=old.decode('utf-8').replace('\r\n','\n')
def change(old,new):
 global text
 assert text.count(old)==1,(old,text.count(old))
 text=text.replace(old,new)
change('var pid := -1\n','''var pid := -1
const PREPARATION_PROCESS_ENGINE := "89cea143987d564363e15d207438530651d943ac"
var _preparation_map_pid := -1
var _preparation_map_reserved := false
''')
change('''func _spawn_preparation(args: PackedStringArray) -> int:
	return OS.create_process(python(),args,false)
''','''func _spawn_preparation(args: PackedStringArray) -> int:
	var created := OS.create_process(python(),args,false)
	# Only this actual creator reserves the pinned Windows process-map entry.
	# Test overrides which bypass it must not claim ownership of their fake PID.
	if created > 0 and OS.get_name() == "Windows" and str(Engine.get_version_info().get("hash", "")) == PREPARATION_PROCESS_ENGINE:
		_preparation_map_pid = created
		_preparation_map_reserved = true
	return created

func _release_preparation_map_entry(owned: int) -> Error:
	return OS.kill(owned)

func _release_completed_preparation() -> void:
	if not _preparation_map_reserved: return
	var owned := _preparation_map_pid
	if owned <= 0 or OS.is_process_running(owned): return
	if OS.get_process_exit_code(owned) == -1: return
	# A completed mapped child may report FAILED from TerminateProcess while
	# still erasing its entry and closing both handles. Consume once; never retry.
	_preparation_map_reserved = false
	_preparation_map_pid = -1
	_release_preparation_map_entry(owned)

func _exit_tree() -> void:
	# A live preparer retains its cooperative cancellation/child-cleanup path.
	_release_completed_preparation()
''')
change('''func _process(_delta: float) -> void:
	if pid <= 0 or OS.is_process_running(pid): return
	pid = -1''','''func _process(_delta: float) -> void:
	if pid <= 0 or OS.is_process_running(pid): return
	_release_completed_preparation()
	pid = -1''')
target.write_text(text,encoding='utf-8')
assert hashlib.sha256(original.read_bytes()).hexdigest()==baseline
(BASE/'candidate.patch').write_text(''.join(difflib.unified_diff(old.decode('utf-8').splitlines(keepends=True),text.splitlines(keepends=True),fromfile='old-context/src/source_import.gd',tofile='source/src/source_import.gd')),encoding='utf-8')
(BASE/'BASELINE.json').write_text(json.dumps({'format':'has_source_import_completion_owner_candidate_1','production_source':str(original),'production_before_sha256':baseline,'production_after_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'runtime_Godot_parse_or_execution':'UNRUN_until_canonical_lease_ends','scope':'Pinned Windows completed-map release only; no live-preparer termination, nested-tree reaper, or other-platform behavior change'},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'candidate':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'production_unchanged':True,'runtime_parse_execution':'UNRUN'},indent=2))
