extends SceneTree
const Reader=preload("res://src/cel_raster_reader.gd")
const Drawing=preload("res://src/drawing.gd")
const History=preload("res://src/cel_pixel_history.gd")
const Budget=preload("res://src/cel_raster_budget.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func _initialize() -> void:
 var args:=OS.get_cmdline_user_args();var folder: String=args[0];var count:=int(args[1]);var frames:=count/4;DirAccess.make_dir_recursive_absolute(folder);var rows: Array=[];var unique:={};var started:=Time.get_ticks_usec()
 for i in range(count):
  var image:=Drawing.blank(1920,1080);image.fill(Color(.2,.3,.4,0));image.fill_rect(Rect2i(80+(i*7)%1650,60+(i*11)%900,100,60),Color(float(i+1)/float(count+1),.7,.3,.5));var path:=folder.path_join("unique_%04d.png"%i);image.save_png(path);var digest:=Reader.digest_bytes(image.get_data());unique[digest]=true;rows.append({"path":path,"pixels":digest,"file":FileAccess.get_sha256(path)})
  if (i+1)%100==0:print("DENSE_PHASE fixtures ",i+1)
 check(unique.size()==count,"each authored full-HD source has a unique RGBA identity including hidden transparent RGB")
 var fixture_ms:=(Time.get_ticks_usec()-started)/1000.;var before:=OS.get_static_memory_usage();started=Time.get_ticks_usec();var reader:=Reader.new();reader.cold_cels=true;var layers: Array=[];var exact:=true
 for layer in range(4):layers.append({"id":"layer"+str(layer),"name":"Layer "+str(layer),"visible":true,"cels":[]})
 for i in range(count):
  var row: Dictionary=rows[i];var result:=reader.read_record(row.path,1920,1080,row.pixels,true)
  if result.has("error"):check(false,"staging unique source "+str(i)+": "+str(result.error));quit(1);return
  var cel: Dictionary={"id":"cel"+str(i),"start":i%frames,"duration":1};cel.merge(result);layers[i/frames].cels.append(cel)
  if (i+1)%100==0:print("DENSE_PHASE staged ",i+1)
 var cache=reader.adaptive_cache;var decoded_files:=reader.png_decodes;reader.adaptive_entries.clear();reader=null;var budget:=Budget.new();budget.install(cache);var load_ms:=(Time.get_ticks_usec()-started)/1000.;var loaded:=budget.sample();var loaded_tracked:=OS.get_static_memory_usage()-before
 check(decoded_files==count and loaded.owners==count and loaded.hot_owners==0,"all unique PNGs validate once and remain independent cold owners")
 check(loaded.accounted_bytes<=cache.owner_limit and loaded.cold_payload_bytes<count*1920*1080*4/8,"sparse cold ownership remains far below its logical eager reservation and within admission")
 started=Time.get_ticks_usec();var max_cache:=0
 for i in range(count):
  var cel: Dictionary=layers[i/frames].cels[i%frames];var result:=Drawing.read_image(cel);exact=exact and not result.has("error") and Reader.digest_bytes(result.image.get_data())==rows[i].pixels;max_cache=maxi(max_cache,cache.retained_bytes)
  if (i+1)%100==0:print("DENSE_PHASE exact reads ",i+1)
 var sequential_ms:=(Time.get_ticks_usec()-started)/1000.
 check(exact and max_cache<=cache.budget and budget.sample().hot_owners==0,"sequential reads verify every original RGBA without pinning or growing decoded cache")
 started=Time.get_ticks_usec();var sequence:=folder.path_join("composites");DirAccess.make_dir_recursive_absolute(sequence);var seek_frames: Array=[frames-1,0,frames/2,37%frames,12%frames,73%frames,24%frames,frames-1]
 for i in range(seek_frames.size()):
  var at: int=seek_frames[i];var picture:=Drawing.composite_result(layers,at,1920,1080);var eager: Array=[]
  for layer in range(4):
   var index: int=layer*frames+at;var source:=Image.load_from_file(rows[index].path);source.convert(Image.FORMAT_RGBA8);eager.append({"visible":true,"cels":[{"start":0,"duration":1,"image":source}]})
  var reference:=Drawing.composite_result(eager,0,1920,1080)
  check(not picture.has("error") and picture.image.get_data()==reference.image.get_data(),"random/reverse composite matches independent eager-source decoding at frame"+str(at))
  picture.image.save_png(sequence.path_join("frame_%06d.png"%(i+1)))
 var seek_ms:=(Time.get_ticks_usec()-started)/1000.;var edits: Array=[]
 for index in [0,count/3,count*2/3,count-1]:
  var cel: Dictionary=layers[index/frames].cels[index%frames];var writable:=Drawing.edit_image(cel);var rect:=Rect2i(300,200,8,8);var old: Image=writable.image.get_region(rect);writable.image.fill_rect(rect,Color.RED);Drawing.touch(writable.image,rect);var edited:=Reader.digest_bytes(writable.image.get_data());var command:={"type":"pixels","raster_owner":cel.raster_owner,"scene_owner":"","before":{rect.position:old},"after":{rect.position:writable.image.get_region(rect)},"bytes":512}
  var undo:=History.apply(command,"before",layers,"");var undo_exact: bool=not undo.has("error") and Reader.digest_bytes(Drawing.image(cel).get_data())==rows[index].pixels
  var redo:=History.apply(command,"after",layers,"")
  check(undo_exact and not redo.has("error") and Reader.digest_bytes(Drawing.image(cel).get_data())==edited,"dense owner-addressed tile Undo/Redo restores exact authored pixels for source"+str(index));edits.append(command)
 var unchanged:=true
 for row in rows:unchanged=unchanged and FileAccess.get_sha256(row.path)==row.file
 check(unchanged,"all generated source PNGs remain byte-identical after seeks/composition/edit history")
 var final:=budget.sample();check(final.accounted_bytes<=cache.owner_limit and final.decoded_cache_bytes<=cache.budget,"edited dense document retains the same hard ownership and decoded-cache limits")
 var report:={"checks":checks,"failures":failures,"count":count,"layers":4,"frames":frames,"unique_pixel_identities":unique.size(),"logical_eager_pixel_bytes":count*1920*1080*4,"fixture_ms":fixture_ms,"capture_load_ms":load_ms,"loaded_tracked_bytes":loaded_tracked,"loaded":loaded,"sequential_exact_read_ms":sequential_ms,"random_reverse_composite_ms":seek_ms,"maximum_decoded_cache_bytes":max_cache,"final":final,"godot_static_peak_bytes":OS.get_static_memory_peak_usage(),"composite_frames":seek_frames.size(),"sequence":sequence,"original_sources_unchanged":unchanged,"scope":"storage foundation and CPU composites above production32cel cap; no ordinary large-project Save/Open, GPU/native/artist or whole-process guarantee"}
 var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close();print("DENSE_RASTER_BENCHMARK "+JSON.stringify(report));quit(0 if failures==0 else 1)
