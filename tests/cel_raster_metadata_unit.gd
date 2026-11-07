extends SceneTree
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Owner=preload("res://src/cel_raster_owner.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
const Drawing=preload("res://src/drawing.gd")
const TimingEditor=preload("res://src/cel_timing_editor.gd")
const Patch=preload("res://src/cel_patch.gd")
const SequenceEditor=preload("res://src/sequence_editor.gd")
const World=preload("res://src/world_document.gd")
const Recovery=preload("res://src/recovery.gd")
class Host extends RefCounted:
	var video: Dictionary={}
	var keys: Array=[]
	var layers: Array=[]
	var palette: Array=[]
	var frame:=0
	var history: Array=[]
	var redo_history: Array=[]
	var history_bytes:=0
	func current_world() -> Dictionary:return preload("res://src/world_document.gd").empty()
	func audio_document() -> Dictionary:return {}
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var source:=Drawing.blank(32,16);source.fill(Color(.3,.5,.7,.5));var snapshot=Snapshot.capture(source).raster;var cache:=Cache.new(2048);var layer:={"id":"ink","name":"Ink","visible":true,"cels":[]}
	for i in range(32):layer.cels.append({"id":"cel"+str(i),"start":i,"duration":1,"raster_owner":Owner.from_snapshot(snapshot,cache).owner})
	var editor:=TimingEditor.new();var shape:=editor.shape(layer)
	check(shape.size()==32 and shape[0].size()==5 and shape==editor.shape(layer) and cache.decodes==0,"32cold timing signatures remain stable without any pixel hydration")
	var before: Array=layer.cels.duplicate(true);var remaining: Array=layer.cels.duplicate();remaining.remove_at(7);var command:=Patch.create(layer.id,"",before,remaining)
	check(command.before.size()==1 and command.after.is_empty() and command.bytes>=2048 and command.bytes<8192 and cache.decodes==0,"cold cut history retains/charges only affected cel with conservative full decoded reserve")
	var restored:=Patch.apply(remaining,command,"before",48)
	check(not restored.has("error") and restored.cels.size()==32 and is_same(restored.cels[7].raster_owner,before[7].raster_owner) and cache.decodes==0,"Undo restores same cold owner without decoding source or peers")
	var redone:=Patch.apply(restored.cels,command,"after",48)
	check(not redone.has("error") and redone.cels==remaining and cache.decodes==0,"Redo cut stays cold and exact")
	check(Recovery.drawing_reserve([layer])==32*2048 and cache.decodes==0,"recovery reserves all uncompressed pixels without materializing cold cels")
	var graph:={"assets":[{"scene":{"layers":[layer]}}]}
	check(Recovery.drawing_reserve([layer],graph)==64*2048 and cache.decodes==0,"nested recovery reservation includes child pixels without hydration or dedup undercount")
	var host:=Host.new();host.layers=[layer];var sequence:=SequenceEditor.new();sequence.app=host;sequence.graph={"assets":[],"clips":[]}
	var retired:={"id":"retired","start":0,"duration":1,"raster_owner":Owner.from_snapshot(snapshot,cache).owner}
	var old_asset:={"id":"retired-asset","scene":{"layers":[{"cels":[layer.cels[0],retired,retired]}],"audio":{}}}
	var graph_command:={"type":"sequence_graph","before":{"assets":[old_asset]},"after":{"assets":[]},"bytes":1024}
	host.history=[graph_command];host.history_bytes=1024;sequence.trim_history()
	check(graph_command.bytes==1024+2048 and host.history_bytes==3072 and cache.decodes==0,"sequence history charges retired cold raster once, excluding live peers, without hydration")
	sequence.trim_history();check(graph_command.bytes==3072 and cache.decodes==0,"repeated sequence budget pass does not accumulate charges or decode pixels")
	sequence.free()
	var eager:={"id":"eager","start":0,"duration":1,"image":source};var eager_layer:={"id":"old","cels":[eager]}
	check(editor.shape(eager_layer)==[["eager",0,1,source.get_instance_id(),0]],"legacy eager timing signature keeps exact previous shape")
	check(Recovery.drawing_reserve([eager_layer])==2048,"eager recovery reservation stays unchanged")
	var unchanged: Dictionary=before[7].duplicate(true);unchanged.start=float(unchanged.start);unchanged.duration=float(unchanged.duration)
	check(Patch.same(before[7],unchanged) and cache.decodes==0,"canonical JSON whole-frame numbers compare cold owner identity without decoding")
	var other: Dictionary=before[7].duplicate(true);other.raster_owner=Owner.from_snapshot(snapshot,cache).owner
	check(Patch.same(before[7],other) and cache.decodes==1,"rebuilt independent owner can prove exact equal pixels on demand")
	var moved: Dictionary=before[7].duplicate(true);moved.duration=2
	check(not Patch.same(before[7],moved),"metadata differences remain stale-history refusal")
	var encoded:=Recovery.encoded_drawing_reserve([layer],graph,1024*1024)
	check(not encoded.has("error") and encoded.bytes==64*source.save_png_to_buffer().size(),"large cold recovery reservation measures exact persisted PNG bytes including child scenes")
	var limited:=Recovery.encoded_drawing_reserve([layer],{},1)
	check(limited.has("error") and not layer.cels[0].raster_owner.is_pinned(),"encoded recovery preflight refuses over-budget without pinning or changing artwork")
	var old_shape:=editor.shape(layer);var pin:=Drawing.edit_image(layer.cels[7]);Drawing.stroke(pin.image,Vector2(3,3),Vector2(9,8),2,Color.RED,false)
	check(editor.shape(layer)!=old_shape and editor.shape(layer)[6]==old_shape[6] and not layer.cels[6].raster_owner.is_pinned(),"editing one cold owner changes only its timing revision token")
	editor.free();print("CEL_RASTER_METADATA_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
