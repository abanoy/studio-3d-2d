extends SceneTree
const Palette=preload("res://src/color_palette.gd")
const Storage=preload("res://src/storage.gd")
const SceneIO=preload("res://src/scene3d.gd")
const T=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var colors: Array=[{"name":"Skin / 肌","rgba":"f4dfbdff"},{"name":"Transparent","rgba":"12345600"}]
	var too_many: Array=[]
	for i in range(33):too_many.append({"name":"Color%d"%i,"rgba":"000000ff"})
	var cases: Array=[]
	for value in [[],colors,too_many.slice(0,32),too_many,null,true,"bad",{},[false],[{"name":"","rgba":"000000ff"}],[{"name":"x".repeat(49),"rgba":"000000ff"}],[{"name":"A\nB","rgba":"000000ff"}],[{"name":"x","rgba":"abcdef"}],[{"name":"x","rgba":"FFFFFFff"}],[{"name":"x","rgba":"000000gg"}],[{"name":"x","rgba":"000000ff","extra":1}]]:
		var valid:=Palette.error(value).is_empty();cases.append({"value":value,"valid":valid})
	check(cases[0].valid and cases[1].valid and cases[2].valid,"empty, named Unicode/alpha and32-color palettes validate")
	var invalid:=true
	for i in range(3,cases.size()):invalid=invalid and not cases[i].valid
	check(invalid,"excess count/types/name/control/hex/unknown fields refuse")
	var asset:=folder.path_join("room.glb");check(SceneIO.make_fixture(asset)==OK,"original room fixture is created")
	var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48}
	var keys: Array=[T.key(0,Vector3.ZERO,Quaternion.IDENTITY,60)];var layers: Array=[{"id":"ink","name":"Ink","visible":true,"cels":[]}]
	var project:=folder.path_join("project")
	check(Storage.save_project(project,video,keys,layers,asset,0,{}, {},{},false,{}, {},colors).is_empty(),"ordinary writer accepts a named project palette")
	var saved:=Storage.load_project(project);check(not saved.has("error") and saved.palette==colors,"ordinary reader preserves ordered RGBA/name values")
	var manifest:=project.path_join("project.json");var before:=FileAccess.get_sha256(manifest)
	check(not Storage.save_project(project,video,keys,layers,asset,0,{}, {},{},false,{}, {},too_many).is_empty() and FileAccess.get_sha256(manifest)==before,"invalid palette cannot replace a valid saved project")
	var data: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(manifest));data.palette=[{"name":"bad","rgba":"red"}];FileAccess.open(manifest,FileAccess.WRITE).store_string(JSON.stringify(data))
	check(Storage.load_project(project).has("error") and not Storage.readable_manifest(manifest),"invalid imported palette refuses Open and cannot qualify as a good backup")
	data.erase("palette");FileAccess.open(manifest,FileAccess.WRITE).store_string(JSON.stringify(data));check(not Storage.load_project(project).has("error"),"older files without a palette remain valid")
	FileAccess.open(folder.path_join("palette-cases.json"),FileAccess.WRITE).store_string(JSON.stringify(cases));print("PALETTE_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
