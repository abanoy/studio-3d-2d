extends SceneTree
const Audio=preload("res://src/audio_track.gd")
var checks:=0
var failures:=0
func digest_bytes(bytes: PackedByteArray) -> String:
	var context:=HashingContext.new();context.start(HashingContext.HASH_SHA256);context.update(bytes);return context.finish().hex_encode()
func source(rate: int,channels: int,phase: int,negative:=false) -> Dictionary:
	var pcm:=PackedByteArray();pcm.resize(4099*channels*2)
	for i in range(4099):
		for channel in range(channels):
			var value:=posmod(i*73+channel*913+phase,50001)-25000
			pcm.encode_s16((i*channels+channel)*2,-value if negative else value)
	return {"pcm":pcm,"rate":rate,"channels":channels,"frames":4099,"path":"procedural-audio.wav","name":"Procedural audio","sha256":"0".repeat(64)}
func fixture(duration: int,mode: String) -> Dictionary:
	var rows:=[]
	for i in range(3):
		var input:=source([48000,44100,8000][i],[1,2,1][i],37*i,mode=="overlap" and i==2)
		var clip:=Audio.make_clip(input);clip.id="clip"+str(i)
		clip.start_frame=[0,duration/2,duration-1][i] if mode!="overlap" else 0
		if mode=="muted":clip.muted=true
		if mode=="fades":clip.source_in_sample=17;clip["source_out_sample"]=3001;clip["fade_in_ms"]=40;clip["fade_out_ms"]=40
		rows.append(clip)
	return Audio.document(rows)
func signature(result: Dictionary) -> Dictionary:
	var all_peaks:=PackedByteArray()
	for peaks: PackedFloat32Array in result.clip_peaks:all_peaks.append_array(peaks.to_byte_array())
	return {"samples":result.samples,"pcm_sha256":digest_bytes(result.pcm),"peaks_sha256":digest_bytes(result.peaks.to_byte_array()),"clip_peaks_sha256":digest_bytes(all_peaks),"clipped_samples":result.clipped_samples}
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	var args:=OS.get_cmdline_user_args();var golden_path: String=args[0] if not args.is_empty() else "res://tests/audio_sparse_golden.json"
	var cases:=[];var times:=[]
	for rate in [[24,1],[30000,1001]]:
		for duration in [24,1440]:
			for mode in ["disjoint","overlap","muted","fades"]:
				var video:={"fps_num":rate[0],"fps_den":rate[1],"duration_frames":duration};var started:=Time.get_ticks_usec();var result:=Audio.mix_document(fixture(duration,mode),video);var elapsed:=(Time.get_ticks_usec()-started)/1000.
				if result.has("error"):push_error(result.error);quit(1);return
				cases.append({"fps":rate,"duration":duration,"mode":mode,"signature":signature(result)});times.append({"fps":rate,"duration":duration,"mode":mode,"elapsed_ms":elapsed})
	var expected=JSON.parse_string(FileAccess.get_file_as_string(golden_path));check(expected is Dictionary and cases.all(func(row):return row.signature.pcm_sha256 is String and row.signature.pcm_sha256.length()==64 and row.signature.peaks_sha256 is String and row.signature.peaks_sha256.length()==64 and row.signature.clip_peaks_sha256 is String and row.signature.clip_peaks_sha256.length()==64) and expected.get("format")=="studio_audio_sparse_golden_1" and expected.get("cases",[]).size()==cases.size(),"frozen original mixer corpus is present")
	if not expected is Dictionary or expected.get("cases",[]).size()!=cases.size():quit(1);return
	for i in range(cases.size()):
		var actual: Dictionary=cases[i];var prior: Dictionary=expected.cases[i]
		check(actual.mode==prior.mode and actual.duration==prior.duration and int(actual.fps[0])==int(prior.fps[0]) and actual.signature.pcm_sha256==prior.signature.pcm_sha256 and actual.signature.peaks_sha256==prior.signature.peaks_sha256 and actual.signature.clip_peaks_sha256==prior.signature.clip_peaks_sha256 and actual.signature.samples==prior.signature.samples and actual.signature.clipped_samples==prior.signature.clipped_samples,"exact dense-mixer PCM/peaks/clipping: "+str(actual.fps)+" "+str(actual.duration)+" "+actual.mode)
	print("AUDIO_SPARSE_UNIT ",JSON.stringify({"checks":checks,"failures":failures,"times":times,"peak_static_bytes":OS.get_static_memory_peak_usage()}));quit(0 if failures==0 else 1)
