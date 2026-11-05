extends SceneTree
const Journal=preload("res://src/recovery_journal.gd")
const Recovery=preload("res://src/recovery.gd")
const Storage=preload("res://src/storage.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(35).timeout.connect(func():push_error("Journal unit watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func write(path: String,data: PackedByteArray) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE);file.store_buffer(data);file.close()
func run() -> void:
	var base:=ProjectSettings.globalize_path("res://output/recovery-journal-unit/%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(base)
	var source:=base.path_join("fixture.glb");check(SceneIO.make_fixture(source)==OK,"original fixture created")
	var hash:=FileAccess.get_sha256(source);var folder:=base.path_join("session")
	var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48}
	var keys: Array=[Timeline.key(0,Vector3.ZERO,Quaternion.IDENTITY,60)]
	var layers: Array=[{"id":"ink","name":"Ink","visible":true,"cels":[]}]
	for i in range(2):check(Storage.save_project(folder,video,keys,layers,source,i,{}, {"origin":"manual.has","revision":i,"saved_at":1000+i}).is_empty(),"create legacy generation %d" % i)
	check(Recovery.checkpoint(base,"session",video,keys,layers,source,2,{},"manual.has",2).is_empty() and Journal.entries(folder).size()==3,"first journal checkpoint adopts BOTH legacy generations before rotation")
	for i in range(3,18):check(Recovery.checkpoint(base,"session",video,keys,layers,source,i,{},"manual.has",i).is_empty(),"commit bounded state %d" % i)
	var entries:=Journal.entries(folder);check(entries.size()==Journal.MAX_ENTRIES,"catalog retains twelve states")
	var candidates:=Recovery.candidates(base,"",true)
	check(candidates.size()==12 and candidates[0].frame==17 and candidates[-1].frame==6,"alias deduplication and chronological history retain the correct window")
	var snapshots:=0
	for name in DirAccess.get_files_at(folder):
		if Journal.is_manifest(name):snapshots+=1
	check(snapshots<=13,"metadata files are bounded including rollback catalog references")
	write(folder.path_join("history_notes.json"),"owner notes".to_utf8_buffer());write(folder.path_join("preview_art.png"),"owner data".to_utf8_buffer())
	var image:=Image.create(256,144,false,Image.FORMAT_RGBA8);image.fill(Color.CYAN)
	var digest: String=entries[0].sha256;var bytes:=FileAccess.get_file_as_bytes(folder.path_join("project.json"))
	check(Journal.attach_preview(folder,digest,image).is_empty() and FileAccess.get_file_as_bytes(folder.path_join("project.json"))==bytes,"preview attachment cannot change checkpoint data")
	entries=Journal.entries(folder);var preview_hash: String=entries[0].preview
	check(Journal.preview(folder,preview_hash).get_pixel(0,0)==Color.CYAN,"checksummed low-resolution preview decodes")
	var png:=folder.path_join(Journal.preview_name(preview_hash));var png_bytes:=FileAccess.get_file_as_bytes(png);write(png,"corrupt".to_utf8_buffer())
	check(Journal.preview(folder,preview_hash)==null and not Storage.load_project(folder,Journal.manifest_name(digest)).has("error"),"damaged preview does not invalidate a recoverable state")
	write(png,png_bytes)
	var excessive:=png_bytes.duplicate();excessive[16]=127;var excessive_hash:=Journal.sha(excessive)
	Journal.write_bytes(folder.path_join(Journal.preview_name(excessive_hash)),excessive)
	check(Journal.preview(folder,excessive_hash)==null,"preview header dimensions are bounded before any image decoding")
	var catalog:=folder.path_join("journal.json");var catalog_bytes:=FileAccess.get_file_as_bytes(catalog)
	var envelope:=Journal.read_json(catalog);envelope.payload+=" ";write(catalog,JSON.stringify(envelope).to_utf8_buffer())
	check(Journal.read_catalog(catalog).is_empty() and not Journal.entries(folder).is_empty(),"bad index checksum falls back to the prior committed catalog")
	var malformed:="{";envelope.payload=malformed;envelope.sha256=malformed.sha256_text();write(catalog,JSON.stringify(envelope).to_utf8_buffer())
	check(Journal.read_catalog(catalog).is_empty() and not Journal.entries(folder).is_empty(),"checksum-valid malformed catalog payload also falls back without logging an engine error")
	write(catalog,catalog_bytes)
	var backup_bytes:=FileAccess.get_file_as_bytes(folder.path_join("project.backup.json"));var damaged:={}
	for i in range(2):
		var name:=Journal.manifest_name(entries[i].sha256);damaged[name]=FileAccess.get_file_as_bytes(folder.path_join(name));write(folder.path_join(name),"{".to_utf8_buffer())
	write(folder.path_join("project.json"),"{".to_utf8_buffer());write(folder.path_join("project.backup.json"),"{".to_utf8_buffer())
	candidates=Recovery.candidates(base,"",true)
	check(not candidates.is_empty() and candidates[0].frame==15 and not Storage.load_project(folder,candidates[0].manifest).has("error"),"two damaged recent states fall back beyond the legacy two-generation limit")
	check(Storage.load_project(folder,Journal.manifest_name(digest)).has("error") and Storage.load_project(folder,"../project.json").has("error"),"changed immutable names and path escapes are refused")
	for name in damaged:write(folder.path_join(name),damaged[name])
	write(folder.path_join("project.json"),bytes);write(folder.path_join("project.backup.json"),backup_bytes)
	var primary_hash:=FileAccess.get_sha256(catalog);DirAccess.make_dir_recursive_absolute(catalog+".tmp")
	var error:=Recovery.checkpoint(base,"session",video,keys,layers,source,20,{},"manual.has",20)
	check(not error.is_empty() and FileAccess.get_sha256(catalog)==primary_hash and not Storage.load_project(folder).has("error"),"failed catalog commit retains prior history and valid latest project data")
	DirAccess.remove_absolute(catalog+".tmp")
	check(FileAccess.get_file_as_string(folder.path_join("history_notes.json"))=="owner notes" and FileAccess.get_file_as_string(folder.path_join("preview_art.png"))=="owner data" and FileAccess.get_sha256(source)==hash,"retention never deletes unrelated filenames or changes original geometry")
	var tied:=base.path_join("ties")
	for i in range(5):
		Storage.save_project(tied,video,keys,layers,source,i,{}, {"origin":"ties.has","revision":i,"saved_at":1000})
		Journal.record(tied)
	var tied_entries: Array=Recovery.candidates(base,"",true).filter(func(entry):return entry.folder==tied)
	check(tied_entries.size()==5 and tied_entries[0].frame==4 and tied_entries[-1].frame==0,"equal timestamps order by revision rather than arbitrary archive names")
	print("RECOVERY_JOURNAL_UNIT "+JSON.stringify({"checks":checks,"failures":failures,"folder":base}));quit(0 if failures==0 else 1)
