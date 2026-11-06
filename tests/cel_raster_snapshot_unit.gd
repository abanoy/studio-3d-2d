extends SceneTree
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Reader=preload("res://src/cel_raster_reader.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var source:=Image.create(32,16,false,Image.FORMAT_RGBA8);source.fill(Color(.2,.7,.8,.5));source.set_pixel(0,0,Color(1,.2,.3,0));source.set_meta("studio_pixels_revision",7)
	var original:=source.get_data();var snapshot=Snapshot.capture(source).raster
	check(snapshot._compressed and snapshot.storage_bytes()<original.size()/2,"sparse source retains compressed pixels only")
	check(snapshot.materialize().image.get_data()==original,"materialization retains exact straight RGBA including hidden transparent RGB")
	check(source.get_data()==original and source.get_meta("studio_pixels_revision")==7,"capture leaves source pixels and metadata unchanged")
	source.fill(Color.RED);check(snapshot.materialize().image.get_data()==original,"later edits to original source cannot change captured cold pixels")
	var first: Image=snapshot.materialize().image;var second: Image=snapshot.materialize().image;first.fill(Color.BLUE)
	check(not is_same(first,second) and second.get_data()==original and snapshot.materialize().image.get_data()==original,"materialized images and cold backing have independent edit ownership")
	check(not second.has_meta("studio_pixels_revision"),"live edit metadata is not cold pixel content")
	var mipmap_source: Image=second.duplicate();mipmap_source.generate_mipmaps();var mipmap_snapshot=Snapshot.capture(mipmap_source).raster
	check(mipmap_source.has_mipmaps() and not mipmap_snapshot.materialize().image.has_mipmaps() and mipmap_snapshot.materialize().image.get_data()==original,"cold pixels contain only exact base level without changing source mipmaps")
	var random_bytes:=PackedByteArray();random_bytes.resize(32*16*4);var random:=RandomNumberGenerator.new();random.seed=917
	for i in range(random_bytes.size()):random_bytes[i]=random.randi_range(0,255)
	var noisy=Snapshot.capture(Image.create_from_data(32,16,false,Image.FORMAT_RGBA8,random_bytes)).raster
	check(not noisy._compressed and noisy.storage_bytes()==random_bytes.size() and noisy.materialize().image.get_data()==random_bytes,"incompressible source uses exact raw fallback without payload expansion")
	var rgb:=Image.create(4,3,false,Image.FORMAT_RGB8);rgb.fill(Color.GREEN);var rgb_snapshot=Snapshot.capture(rgb).raster
	check(rgb.get_format()==Image.FORMAT_RGB8 and rgb_snapshot.materialize().image.get_format()==Image.FORMAT_RGBA8 and rgb_snapshot.materialize().image.get_pixel(1,1)==Color.GREEN,"format conversion is detached and explicit RGBA8")
	check(Snapshot.capture(null).has("error") and Snapshot.capture(Image.new()).has("error") and Snapshot.new().materialize().has("error"),"missing/uninitialized sources refuse")
	var huge:=Image.create(1921,1,false,Image.FORMAT_RGBA8);check(Snapshot.capture(huge).has("error"),"out-of-canvas source refuses before compression")
	var cache:=Cache.new(4096);var a:=cache.read(snapshot);var b:=cache.read(snapshot)
	check(cache.decodes==1 and cache.hits==1 and not is_same(a.image,b.image) and a.image.get_data()==original,"cache hit returns independent Image resources without another decode")
	a.image.fill(Color.MAGENTA);check(b.image.get_data()==original and cache.read(snapshot).image.get_data()==original,"cache consumers cannot mutate peers or retained source")
	a={};b={};var other=Snapshot.capture(source).raster;cache.read(other);cache.read(noisy)
	check(cache.retained_bytes==4096 and cache._entries.size()==2,"decoded LRU remains within explicit two-raster byte budget")
	var decodes:=cache.decodes;cache.read(snapshot);check(cache.decodes==decodes+1 and cache.retained_bytes==4096,"evicted snapshot rehydrates exactly without exceeding cache budget")
	cache.clear();check(cache.retained_bytes==0 and cache._entries.is_empty(),"explicit clear releases decoded cache ownership")
	var zero:=Cache.new(0);zero.read(snapshot);zero.read(snapshot);check(zero.retained_bytes==0 and zero.decodes==2 and zero.hits==0,"zero-budget reads retain no decoded cache")
	var small:=Cache.new(100);small.read(snapshot);check(small.retained_bytes==0,"oversize item bypasses rather than expands the budget")
	var temporary=Snapshot.capture(source).raster;var weak: WeakRef=weakref(temporary);cache.read(temporary);temporary=null;cache.read(snapshot)
	check(weak.get_ref()==null and cache._entries.size()==1,"cache does not retain old snapshot/document ownership")
	var tampered=Snapshot.capture(source).raster;cache.read(tampered);tampered._payload[0]=tampered._payload[0]^1
	check(cache.read(tampered).has("error") and tampered.materialize().has("error"),"payload corruption refuses even when decoded pixels are cached")
	tampered=Snapshot.capture(source).raster;tampered._size=Vector2i(16,32)
	check(tampered.materialize().has("error"),"descriptor corruption refuses even with equal pixel count")
	check(cache.read(null).has("error") and cache.read({}).has("error"),"mistyped cold handles refuse")
	check(Cache.new(-1).budget==0 and Cache.new(999999999).budget==Cache.DEFAULT_BUDGET,"cache configuration cannot exceed fixed production ceiling")
	var folder: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var path:=folder.path_join("owned.png");second.save_png(path);var file_sha:=FileAccess.get_sha256(path);var reader:=Reader.new();var staged:=reader.read_cold(path,32,16,Snapshot.digest(original),true)
	check(not staged.has("error") and staged.raster.materialize().image.get_data()==original and reader.entries.is_empty(),"opt-in cold reader validates original PNG then releases eager decode ownership")
	check(FileAccess.get_sha256(path)==file_sha,"cold capture never modifies its source file")
	check(reader.read_cold(path,32,16,"0".repeat(64),true).has("error") and reader.entries.is_empty(),"wrong pixel checksum refuses cold adoption and releases staging cache")
	check(reader.read_cold(path,31,16).has("error"),"wrong declared canvas refuses cold adoption")
	DirAccess.remove_absolute(path)
	check(reader.read_cold(path,32,16).has("error") and staged.raster.materialize().image.get_data()==original,"missing later source refuses while captured snapshot remains independent of original disk")
	second.save_png(path);var eager:=reader.read(path,32,16)
	check(not eager.has("error") and eager.image.get_data()==original,"original eager reader API remains compatible")
	print("CEL_RASTER_SNAPSHOT_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
