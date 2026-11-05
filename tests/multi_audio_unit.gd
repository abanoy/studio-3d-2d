extends SceneTree
const Audio=preload("res://src/audio_track.gd")
var checks:=0
var failures:=0
var video:={"duration_frames":24,"fps_num":24,"fps_den":1}
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func source(value: int,rate:=48000,channels:=1) -> Dictionary:
	var pcm:=PackedByteArray();pcm.resize(rate*channels*2)
	for i in range(rate*channels):pcm.encode_s16(i*2,value)
	return {"frames":rate,"rate":rate,"channels":channels,"pcm":pcm}
func clip(id: String,value: int) -> Dictionary:
	var result:=Audio.make_clip(source(value));result.id=id;return result
func _initialize() -> void:
	var a:=clip("a",30000);var b:=clip("b",30000);var c:=clip("c",-30000)
	var legacy:=Audio.mix(a,video);var single:=Audio.mix_document(a,video)
	check(legacy.pcm==single.pcm and legacy.peaks==single.peaks,"legacy single-clip PCM and waveform stay byte-exact")
	var many:=Audio.mix_document(Audio.document([a,b,c]),video)
	check(not many.has("error") and many.pcm.decode_s16(0)==30000,"all overlaps sum before clipping and quantization")
	var reversed:=Audio.mix_document(Audio.document([c,b,a]),video)
	check(many.pcm==reversed.pcm,"cancelling overlap does not depend on early clipping order")
	var hot:=Audio.mix_document(Audio.document([a,b]),video)
	check(hot.pcm.decode_s16(0)==32767 and hot.clipped_samples==96000,"over-range mix saturates without wrap and reports clipping")
	b.muted=true;var mute:=Audio.mix_document(Audio.document([a,b]),video)
	check(mute.pcm==legacy.pcm and mute.clip_peaks[1][0]==0,"mute affects only its clip; peers and per-clip waveform remain")
	b.muted=false;b.start_frame=12;b.gain_db=-6;b.source=source(10000,44100,2);b.source_in_sample=22050
	var timed:=Audio.mix_document(Audio.document([c,b]),video)
	check(timed.pcm.decode_s16(0)==-30000 and absi(timed.pcm.decode_s16(24000*4)+24988)<=1,"rational frame start, source-sample trim, stereo resample and independent gain")
	check(timed.clip_peaks.size()==2 and timed.clip_peaks[1][0]==0,"each timeline row has project-time waveform silence")
	check(not Audio.layout_error({"format":"future_audio","clips":[a]}).is_empty(),"unknown collection version refuses")
	check(not Audio.layout_error(Audio.document([a,a])).is_empty(),"duplicate clip identity refuses")
	check(not Audio.layout_error({"format":Audio.FORMAT,"clips":[]}).is_empty(),"invalid empty collection refuses")
	var excess:=[]
	for i in range(17):var row:=a.duplicate();row.id=str(i);excess.append(row)
	check(not Audio.layout_error(Audio.document(excess)).is_empty(),"more than16 clips refuses before mixing")
	var bad:=b.duplicate(true);bad.start_frame=INF
	check(Audio.mix_document(Audio.document([a,bad]),video).has("error"),"nonfinite timing refuses without allocation of a mix")
	bad=b.duplicate(true);bad.gain_db=100
	check(Audio.mix_document(Audio.document([a,bad]),video).has("error"),"out-of-range gain refuses")
	check(Audio.document([a])==a and Audio.document([]).is_empty(),"single and silent documents keep existing layout")
	var large:=PackedByteArray();large.resize(5*1024*1024);var budget:=[]
	for i in range(16):
		var row:=a.duplicate();row.id="budget-"+str(i);row.source={"pcm":large};budget.append(row)
	check(Audio.mix_document(Audio.document(budget),video).get("error","").contains("64MiB"),"decoded sample budget refuses before oversized mixing")
	bad=b.duplicate(true);bad.source_in_sample=bad.source.frames
	check(Audio.mix_document(Audio.document([a,bad]),video).has("error"),"trim past decoded source end refuses")
	bad=b.duplicate(true);bad.source.pcm=PackedByteArray([0,0])
	check(Audio.mix_document(Audio.document([a,bad]),video).has("error"),"incomplete decoded PCM refuses")
	print("MULTI_AUDIO_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
