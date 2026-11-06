extends SceneTree
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Owner=preload("res://src/cel_raster_owner.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48};var keys: Array=[Timeline.key(0,Vector3(0,1,5),Quaternion.IDENTITY,60)]
	var image:=Drawing.blank(1920,1080);image.fill(Color(.2,.3,.7,.5));var snapshot=Snapshot.capture(image).raster;var cache:=Cache.new();var owner=Owner.from_snapshot(snapshot,cache).owner
	var cel:={"id":"cold","start":0,"duration":48,"raster_owner":owner};var layer:={"id":"ink","name":"Ink","visible":true,"cels":[cel]};var world:=World.empty()
	var error:=Storage.save_project(folder,video,keys,[layer],"",0,{},{},{},true,world);var manifest:=folder.path_join("project.json");var good_sha:=FileAccess.get_sha256(manifest)
	check(error.is_empty() and not owner.is_pinned() and FileAccess.file_exists(manifest),"directory save streams exact cold pixels without write pinning")
	var loaded:=Storage.load_project(folder);check(not loaded.has("error") and Storage.image_hash(loaded.layers[0].cels[0].image)==snapshot.pixel_sha256(),"existing eager reader restores exact cold-written canonical PNG")
	var foreign: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(manifest));foreign.layers[0].cels[0]["raster_owner"]={"image":"untrusted"};foreign.layers[0].cels[0]["image"]="untrusted"
	var sanitized:=Storage.decode_project(foreign,folder)
	check(not sanitized.has("error") and not sanitized.layers[0].cels[0].has("raster_owner") and Storage.image_hash(sanitized.layers[0].cels[0].image)==snapshot.pixel_sha256(),"serialized transient ownership cannot shadow validated PNG pixels during adoption")
	var small:=Drawing.blank(4,3);Drawing.replace_image(cel,small);error=Storage.save_project(folder,video,keys,[layer],"",0,{},{},{},true,world)
	check(not error.is_empty() and FileAccess.get_sha256(manifest)==good_sha,"wrong canvas refuses save before replacing previous manifest")
	var rgb:=Image.create(1920,1080,false,Image.FORMAT_RGB8);Drawing.replace_image(cel,rgb);error=Storage.save_project(folder,video,keys,[layer],"",0,{},{},{},true,world)
	check(not error.is_empty() and FileAccess.get_sha256(manifest)==good_sha,"unsupported editable pixel format refuses rather than writing an unreopenable checksum")
	cel.erase("image");cel.raster_owner=owner;snapshot._payload[0]=snapshot._payload[0]^1;error=Storage.save_project(folder,video,keys,[layer],"",0,{},{},{},true,world)
	check(not error.is_empty() and FileAccess.get_sha256(manifest)==good_sha,"corrupt cold pixels refuse save and keep prior committed manifest")
	loaded=Storage.load_project(folder);check(not loaded.has("error") and Storage.image_hash(loaded.layers[0].cels[0].image)==Storage.image_hash(image),"previous saved pixels stay independently readable after all refused saves")
	print("CEL_RASTER_SAVE_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
