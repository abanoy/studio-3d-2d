extends RefCounted
const Audio=preload("res://src/audio_track.gd")
const Graph=preload("res://src/sequence_graph.gd")
static func build(graph: Dictionary,root: Dictionary) -> Dictionary:
	var why:=Graph.error(graph,root)
	if not why.is_empty():return {"error":why}
	var state:={"scenes":{"":root},"clips":{"":graph.clips},"cache":{}}
	var bytes:=Audio.memory(root.get("audio",{}))
	for asset in graph.assets:
		state.scenes[asset.id]=asset.scene;state.clips[asset.id]=asset.clips
		bytes+=Audio.memory(asset.scene.get("audio",{}))
	if bytes>Audio.MAX_PCM:return {"error":"Nested audio sources exceed64MiB."}
	# Resolve children before allocating a parent's sum buffer. Scratch memory
	# does not multiply with nesting depth; cached PCM is bounded separately.
	for id in state.scenes:
		var result:=mix_scene(id,state)
		if result.has("error"):return result
	var cached_bytes:=0
	for result in state.cache.values():cached_bytes+=result.get("pcm",PackedByteArray()).size()
	if cached_bytes>Audio.MAX_PCM:return {"error":"Nested audio mixes exceed64MiB."}
	return {"mixes":state.cache,"bytes":cached_bytes}
static func origin_sample(frame: int,video: Dictionary) -> int:
	var numerator:=int(video.fps_num);var units:=frame*Audio.RATE*int(video.fps_den)
	var value: int=(absi(units)+numerator/2)/numerator
	return -value if units<0 else value
static func mix_scene(owner: String,state: Dictionary) -> Dictionary:
	if state.cache.has(owner):return state.cache[owner]
	var scene: Dictionary=state.scenes[owner];var video: Dictionary=scene.video
	var own: Dictionary={} if scene.get("audio",{}).is_empty() else Audio.mix_document(scene.audio,video)
	if own.has("error"):return own
	var parts: Array=[]
	for clip in state.clips[owner]:
		if clip.muted:continue
		var child:=mix_scene(clip.asset_id,state)
		if child.has("error"):return child
		if not child.is_empty():parts.append({"clip":clip,"mix":child,"duration":state.scenes[clip.asset_id].video.duration_frames})
	if parts.is_empty():state.cache[owner]=own;return own
	var count:=Audio.sample_index(int(video.duration_frames),video)
	if count<1 or count>Audio.RATE*Audio.MAX_SECONDS:return {"error":"Nested audio supports at most60seconds."}
	var sum:=PackedFloat64Array();sum.resize(count*2);sum.fill(0)
	if not own.is_empty():
		for sample in range(count*2):sum[sample]=own.pcm.decode_s16(sample*2)
	var numerator:=int(video.fps_num);var frame_units:=Audio.RATE*int(video.fps_den)
	for part in parts:
		var clip: Dictionary=part.clip;var mix: Dictionary=part.mix
		var start:=Audio.sample_index(int(clip.start),video)
		var origin:=origin_sample(int(clip.start)-int(clip.time_in),video)
		var end:=mini(count,Audio.sample_index(int(clip.start+clip.duration),video))
		var period:=int(part.duration)*frame_units;var gain:=db_to_linear(clip.gain_db)
		for sample in range(start,end):
			var units: int=(sample-origin)*numerator+int(clip.source_in)*frame_units
			if clip.loop:units=units%period
			var source: int=(units+numerator/2)/numerator
			# A fractional loop boundary can fall between samples. Round the
			# boundary itself, instead of losing a one-sample transient at wraps.
			if clip.loop and units>=period-numerator/2:source=0
			source=clampi(source,0,int(mix.samples)-1)
			for channel in range(2):sum[sample*2+channel]+=mix.pcm.decode_s16(source*4+channel*2)*gain
	var pcm:=PackedByteArray();pcm.resize(count*4)
	var peaks:=PackedFloat32Array();peaks.resize(256);peaks.fill(0)
	var clipped:=0
	for sample in range(count):
		for channel in range(2):
			var raw:=roundi(sum[sample*2+channel])
			if raw < -32768 or raw>32767:clipped+=1
			var value:=clampi(raw,-32768,32767);pcm.encode_s16(sample*4+channel*2,value)
			var bucket:=mini(255,sample*256/count);peaks[bucket]=maxf(peaks[bucket],absf(value/32768.0))
	var stream:=AudioStreamWAV.new();stream.format=AudioStreamWAV.FORMAT_16_BITS;stream.mix_rate=Audio.RATE;stream.stereo=true;stream.data=pcm
	var result:={"pcm":pcm,"stream":stream,"samples":count,"peaks":peaks,"clip_peaks":own.get("clip_peaks",[]),"clipped_samples":clipped}
	state.cache[owner]=result;return result
