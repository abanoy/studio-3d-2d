extends SceneTree
const Audio=preload("res://src/audio_track.gd")
const Nested=preload("res://src/sequence_audio.gd")
const Graph=preload("res://src/sequence_graph.gd")
const World=preload("res://src/world_document.gd")
var checks:=0
var failures:=0
var video:={"duration_frames":24,"fps_num":24,"fps_den":1}
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func sound(id: String,level: int) -> Dictionary:
	var pcm:=PackedByteArray();pcm.resize(96000)
	for i in range(48000):pcm.encode_s16(i*2,level)
	var row:=Audio.make_clip({"frames":48000,"rate":48000,"channels":1,"pcm":pcm,"name":id+".wav","path":id+".wav","sha256":id.sha256_text()});row.id=id;return row
func scene(audio: Dictionary) -> Dictionary:return {"schema_version":4,"video":{"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":24},"world":World.empty(),"layers":[],"audio":audio,"camera_keys":[]}
func nested_clip(id: String,asset: String) -> Dictionary:return {"id":id,"asset_id":asset,"start":0,"duration":24,"source_in":0,"time_in":0,"key_in":0,"loop":false,"visible":true,"muted":false,"gain_db":0,"keys":[Graph.key()]}
func _initialize() -> void:
	var a:=sound("a",1000);var b:=sound("b",2000);var c:=sound("c",-500);var original: Array=[a.duplicate(true),b.duplicate(true),c.duplicate(true)]
	var ordinary:=Audio.mix_document(Audio.document([a,b,c]),video)
	check(ordinary.pcm.decode_s16(0)==2500,"ordinary clips retain their previous summed PCM")
	a.solo=true;var doc:=Audio.document([a,b,c]);var isolated:=Audio.mix_document(doc,video)
	check(doc.format==Audio.SOLO_FORMAT and isolated.pcm.decode_s16(0)==1000,"one solo isolates its clip through the ordinary mixer")
	check(not b.muted and not c.muted and b==original[1] and c==original[2],"solo leaves peer settings and source samples unchanged")
	b.solo=true;check(Audio.mix_document(Audio.document([a,b,c]),video).pcm.decode_s16(0)==3000,"several soloed clips sum together")
	a.muted=true;check(Audio.mix_document(Audio.document([a,b,c]),video).pcm.decode_s16(0)==2000,"mute remains authoritative over a soloed clip")
	b.muted=true;check(Audio.mix_document(Audio.document([a,b,c]),video).pcm.decode_s16(0)==0,"all muted solos produce silence instead of playing peers")
	a.erase("solo");b.erase("solo");a.muted=false;b.muted=false
	check(Audio.document([a,b,c]).format==Audio.FORMAT and Audio.mix_document(Audio.document([a,b,c]),video).pcm==ordinary.pcm,"clearing all solo fields restores legacy format and exact mix")
	a.solo=false;check(Audio.mix_document(Audio.document([a,b,c]),video).pcm==ordinary.pcm,"explicit versioned false does not filter sound")
	a.solo=true;var metadata:=Audio.metadata(Audio.document([a,b,c]));check(metadata.format==Audio.SOLO_FORMAT and metadata.clips[0].solo==true,"managed metadata retains the versioned boolean")
	var cases: Array=[]
	for version in [Audio.FORMAT,Audio.TRIM_FORMAT,Audio.FADE_FORMAT,Audio.SOLO_FORMAT]:
		for value in [true,false,0,1,"yes",null]:
			var candidate: Dictionary=metadata.duplicate(true);candidate.format=version;candidate.clips[0].solo=value;var valid: bool=version==Audio.SOLO_FORMAT and value is bool
			check(Audio.layout_error(candidate).is_empty()==valid,"solo type/version validation is explicit")
			cases.append({"audio":candidate,"valid":valid})
	var direct: Dictionary=metadata.clips[0].duplicate(true);check(not Audio.layout_error(direct).is_empty(),"an unversioned single clip cannot hide a solo setting")
	cases.append({"audio":direct,"valid":false})
	var root_scene:=scene(Audio.document([a,b]));var child:=scene(Audio.document([c]));var graph:={"format":Graph.FORMAT,"assets":[{"id":"child","name":"Original child","scene":child,"clips":[]}],"clips":[nested_clip("instance","child")]}
	var built:=Nested.build(graph,root_scene);check(not built.has("error") and built.mixes[""].pcm.decode_s16(0)==1000,"a scene solo also isolates it from nested sequence sound")
	a.muted=true;root_scene.audio=Audio.document([a,b]);built=Nested.build(graph,root_scene);check(built.mixes[""].pcm.decode_s16(0)==0,"a muted scene solo keeps nested sound suppressed")
	a.muted=false;a.erase("solo");c.solo=true;var d:=sound("d",8000);child.audio=Audio.document([c,d]);root_scene.audio=Audio.document([a,b]);graph.assets[0].scene=child;built=Nested.build(graph,root_scene)
	check(built.mixes[""].pcm.decode_s16(0)==2500 and built.mixes.child.pcm.decode_s16(0)==-500,"child solo stays local to the child mix and leaves parent sound intact")
	var one:=Audio.document([c]);one.clips[0].muted=true;check(Audio.mix_document(one,video).pcm.decode_s16(0)==0,"single soloed muted clip remains silent")
	var args:=OS.get_cmdline_user_args()
	if not args.is_empty():var file:=FileAccess.open(args[0].path_join("solo-cases.json"),FileAccess.WRITE);file.store_string(JSON.stringify(cases,"",true,true));file.close()
	print("AUDIO_SOLO_UNIT ",JSON.stringify({"checks":checks,"failures":failures,"cross_runtime_cases":cases.size()}));quit(0 if failures==0 else 1)
