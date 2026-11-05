extends SceneTree
const Audio=preload("res://src/audio_track.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var video:={"duration_frames":48,"fps_num":24,"fps_den":1}
	var pcm:=PackedByteArray();pcm.resize(44100*2)
	for i in range(44100):pcm.encode_s16(i*2,10000)
	var source:={"rate":44100,"channels":1,"frames":44100,"pcm":pcm}
	var clip:=Audio.make_clip(source);clip.id="fade";clip.start_frame=6;clip.source_in_sample=4410;clip["fade_in_ms"]=100;clip["fade_out_ms"]=200
	var before:=clip.duplicate(true);var doc:=Audio.document([clip]);var mixed:=Audio.mix_document(doc,video)
	check(doc.format==Audio.FADE_FORMAT and Audio.clips(doc).size()==1,"single faded sound uses an explicit version4 envelope")
	check(not mixed.has("error"),"faded 44.1kHz sound mixes at48kHz")
	var data: PackedByteArray=mixed.pcm
	check(data.decode_s16(11999*4)==0 and data.decode_s16(12000*4)==0,"frame6 placement and first fade sample are silent")
	check(absi(data.decode_s16(14400*4)-5001)<=1 and data.decode_s16(16799*4)==10000,"100ms fade reaches full level at its inclusive last sample")
	check(data.decode_s16(45599*4)==10000 and absi(data.decode_s16(50399*4)-5001)<=1,"200ms fade out decreases from the trimmed sound's own end")
	check(data.decode_s16(55199*4)==0 and data.decode_s16(55200*4)==0,"last audible extent reaches zero and remaining shot stays silent")
	check(clip==before and clip.source.pcm==pcm,"fades leave source PCM and authored metadata unchanged")
	var meta:=Audio.metadata(Audio.document([dict_source(clip)]))
	check(meta.format==Audio.FADE_FORMAT and meta.clips[0].fade_in_ms==100 and meta.clips[0].fade_out_ms==200,"portable metadata retains both fade durations")
	var peer:=Audio.make_clip(source);peer.id="peer";peer.start_frame=6;peer.source_in_sample=4410;peer.gain_db=-6
	var many:=Audio.mix_document(Audio.document([clip,peer]),video)
	check(absi(many.pcm.decode_s16(12000*4)-5012)<=1 and absi(many.pcm.decode_s16(14400*4)-10013)<=1,"peer sound remains independent of the selected fade")
	var trimmed:=clip.duplicate();trimmed["source_out_sample"]=8820;trimmed.fade_in_ms=200;trimmed.fade_out_ms=200
	var short:=Audio.mix_document(Audio.document([trimmed]),video)
	check(short.pcm.decode_s16(12000*4)==0 and absi(short.pcm.decode_s16(14400*4)-2500)<=1 and short.pcm.decode_s16(16799*4)==0,"overlapping long fades fit a100ms trimmed clip and multiply")
	check(not Audio.layout_error(clip).is_empty() and not Audio.layout_error({"format":Audio.TRIM_FORMAT,"clips":[clip]}).is_empty(),"older audio envelopes cannot conceal fades")
	for value in [0,-1,100.5,NAN,INF,60001,true,"100"]:
		var bad:=clip.duplicate();bad.fade_in_ms=value
		check(Audio.mix_document(Audio.document([bad]),video).has("error"),"invalid fade refuses: "+str(value))
	for rate in [8000,48000,96000]:
		var samples:=PackedByteArray();samples.resize(rate*4)
		for i in range(rate):samples.encode_s16(i*4,10000);samples.encode_s16(i*4+2,-10000)
		var stereo:=Audio.make_clip({"rate":rate,"channels":2,"frames":rate,"pcm":samples});stereo.id="stereo";stereo["fade_in_ms"]=100;stereo["fade_out_ms"]=100
		var result:=Audio.mix_document(Audio.document([stereo]),video)
		check(not result.has("error") and result.pcm.decode_s16(2400*4)==5001 and result.pcm.decode_s16(2400*4+2)==-5001 and result.pcm.decode_s16(47999*4)==0,"stereo channels share source-rate-independent fade timing: "+str(rate))
	var legacy=load(OS.get_cmdline_user_args()[0]);check(not legacy.layout_error(doc).is_empty(),"actual previous reader refuses fades instead of silently dropping them")
	clip.erase("fade_in_ms");clip.erase("fade_out_ms");check(Audio.document([clip])==clip,"removing both fades restores the old single layout")
	clip["source_out_sample"]=8820;check(Audio.document([clip]).format==Audio.TRIM_FORMAT,"remaining end trim retains version3 after fades are removed")
	print("AUDIO_FADE_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
func dict_source(clip: Dictionary) -> Dictionary:
	var result:=clip.duplicate(true);result.source["name"]="tone.wav";result.source["sha256"]="a".repeat(64);return result
