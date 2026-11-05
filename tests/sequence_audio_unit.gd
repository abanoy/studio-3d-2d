extends SceneTree
const Audio=preload("res://src/audio_track.gd")
const Nested=preload("res://src/sequence_audio.gd")
const Graph=preload("res://src/sequence_graph.gd")
const World=preload("res://src/world_document.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func scene(duration: int=48,num: int=24,den: int=1) -> Dictionary:
	return {"schema_version":4,"video":{"width":1920,"height":1080,"fps_num":num,"fps_den":den,"duration_frames":duration},"world":World.empty(),"layers":[],"audio":{},"camera_keys":[]}
func sound(amplitude: int) -> Dictionary:
	var pcm:=PackedByteArray();pcm.resize(48000*2);pcm.fill(0);pcm.encode_s16(0,amplitude)
	return Audio.make_clip({"pcm":pcm,"rate":48000,"channels":1,"frames":48000,"name":"Original impulse.wav","path":"procedural.wav","sha256":"a".repeat(64)})
func clip(id: String,asset: String,start:=0,duration:=48,source_in:=0,loop:=false) -> Dictionary:
	return {"id":id,"asset_id":asset,"start":start,"duration":duration,"source_in":source_in,"time_in":0,"key_in":0,"loop":loop,"visible":true,"muted":false,"gain_db":0,"keys":[Graph.key()]}
func _initialize() -> void:
	var root_scene:=scene();var child:=scene(12);child.audio=Audio.document([sound(18000)])
	var wrapper:=scene()
	var graph:={"format":Graph.FORMAT,"assets":[{"id":"child","name":"Source","scene":child,"clips":[]},{"id":"wrapper","name":"Wrapper","scene":wrapper,"clips":[clip("inner","child",12,36,0,true)]}],"clips":[clip("outer","wrapper",12,36,12)]}
	var source: PackedByteArray=Audio.clips(child.audio)[0].source.pcm.duplicate()
	var built:=Nested.build(graph,root_scene)
	check(not built.has("error"),"nested source offset and loop mix builds")
	var pcm: PackedByteArray=built.mixes[""].pcm;var peaks:=[]
	for sample in range(pcm.size()/4):
		if pcm.decode_s16(sample*4)>1000:peaks.append(sample)
	check(peaks==[24000,48000,72000],"nested and parent offsets retain exact frame12/24/36 transients")
	graph.clips[0].visible=false;var hidden:=Nested.build(graph,root_scene)
	check(hidden.mixes[""].pcm==pcm,"visual visibility does not implicitly mute child sound")
	graph.clips[0].muted=true;check(Nested.build(graph,root_scene).mixes[""].is_empty(),"clip mute explicitly removes nested sound")
	graph.clips[0].muted=false;graph.clips[0].gain_db=-6;var quiet:=Nested.build(graph,root_scene)
	check(absi(quiet.mixes[""].pcm.decode_s16(24000*4)-9021)<=1,"parent instance gain applies after the child's editable mix")
	check(Audio.clips(child.audio)[0].source.pcm==source,"mixing leaves source samples unchanged")
	# Sum instances and root audio before final saturation.
	graph.assets=[graph.assets[0]];graph.clips=[clip("one","child",0,48,0,true),clip("two","child",0,48,0,true)];root_scene.audio=Audio.document([sound(-18000)])
	built=Nested.build(graph,root_scene)
	check(built.mixes[""].pcm.decode_s16(0)==18000,"late cancellation survives two loud nested contributions")
	root_scene=scene(240,30000,1001);child=scene(1,30000,1001);child.audio=Audio.document([sound(18000)])
	graph.assets=[{"id":"child","name":"Fractional loop","scene":child,"clips":[]}];graph.clips=[clip("fractional","child",0,240,0,true)]
	built=Nested.build(graph,root_scene);pcm=built.mixes[""].pcm;peaks=[]
	for sample in range(pcm.size()/4):
		if pcm.decode_s16(sample*4)>1000:peaks.append(sample)
	var expected:=[]
	for frame in range(240):expected.append(Audio.sample_index(frame,root_scene.video))
	check(peaks==expected,"240 fractional-rate loops keep every transient on its nearest exact frame sample without drift")
	var original: PackedByteArray=pcm.duplicate()
	var left: Dictionary=graph.clips[0].duplicate(true);var right:=left.duplicate(true)
	left.duration=17;right.id="right";right.start=17;right.duration=223;right.time_in=17;right.key_in=17
	graph.clips=[left,right];built=Nested.build(graph,root_scene)
	check(built.mixes[""].pcm==original,"splitting a fractional-rate looping clip preserves every PCM sample exactly")
	print("SEQUENCE_AUDIO_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
