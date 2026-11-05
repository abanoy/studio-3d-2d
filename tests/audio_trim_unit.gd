extends SceneTree
const Audio=preload("res://src/audio_track.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var pcm:=PackedByteArray();pcm.resize(44100*2)
	for i in range(44100):pcm.encode_s16(i*2,10000)
	pcm.encode_s16(101*2,30000)
	var source:={"frames":44100,"rate":44100,"channels":1,"pcm":pcm}
	var clip:=Audio.make_clip(source);clip.id="trim";clip["source_out_sample"]=101
	var original:=clip.duplicate(true);var video:={"duration_frames":24,"fps_num":24,"fps_den":1}
	var document:=Audio.document([clip])
	check(document.format==Audio.TRIM_FORMAT and Audio.clips(document).size()==1,"a single end trim carries a version3 envelope")
	var full:=clip.duplicate();full.erase("source_out_sample")
	check(Audio.end_at_frame(full,0,video).sample==1837,"shared pointer/dialog conversion rounds a one-frame exclusive end down")
	check(Audio.end_at_frame(full,23,video).sample==44100,"shared conversion restores complete source at its natural last frame")
	check(Audio.end_at_frame(clip,0,video).sample==101,"unchanged enclosing frame preserves an existing partial endpoint")
	check(Audio.end_at_frame(clip,-1,video).has("error") and Audio.end_at_frame(clip,24,video).has("error"),"out-of-shot frame endpoints refuse")
	check(not Audio.layout_error(clip).is_empty(),"an unversioned end trim refuses")
	check(not Audio.layout_error({"format":Audio.FORMAT,"clips":[clip]}).is_empty(),"version2 cannot conceal an end trim")
	var mixed:=Audio.mix_document(document,video)
	check(not mixed.has("error") and mixed.pcm.decode_s16(109*4)==10000,"last resampled value cannot leak a hidden following source sample")
	check(mixed.pcm.decode_s16(110*4)==0 and mixed.pcm.decode_s16(480*4)==0,"single mix becomes silent at the exclusive source endpoint")
	check(clip==original and clip.source.pcm==pcm,"mixing does not crop or rewrite source samples")
	var peer:=Audio.make_clip(source);peer.id="peer";peer.gain_db=-6
	var many:=Audio.mix_document(Audio.document([clip,peer]),video)
	check(not many.has("error") and absi(many.pcm.decode_s16(480*4)-5012)<=1,"peer sound continues beyond the trimmed clip")
	check(many.clip_peaks[0][1]==0 and many.clip_peaks[1][1]>.1,"each waveform honors its own trim")
	var untrimmed:=clip.duplicate();untrimmed.erase("source_out_sample")
	check(Audio.document([untrimmed])==untrimmed and Audio.document([untrimmed,peer]).format==Audio.FORMAT,"restoring the end preserves old single/multi formats")
	for ending in [0,-1,INF,NAN,100.5,44101]:
		var bad:=clip.duplicate();bad.source_out_sample=ending
		check(Audio.mix_document(Audio.document([bad]),video).has("error"),"invalid endpoint refuses: "+str(ending))
	var rational:=clip.duplicate();rational.source_out_sample=3528
	check(Audio.last_frame(rational,{"fps_num":25,"fps_den":2})==0,"rational inclusive frame count retains the exact boundary")
	rational.source_out_sample=3529
	check(Audio.last_frame(rational,{"fps_num":25,"fps_den":2})==1,"partial next frame remains visible")
	var view:=preload("res://src/timeline_view.gd").new()
	view.size=Vector2(1400,900)
	var exact:=Audio.make_clip({"frames":8000,"rate":8000});exact["source_out_sample"]=2240
	view.audio_clips=[exact];view.audio_rate={"fps_num":25,"fps_den":1}
	check(view.audio_rect(0).end.x==view.x(7),"25fps exact seven-frame endpoint avoids floating-point ceil expansion")
	exact.source_out_sample=4480;view.audio_rate={"fps_num":25,"fps_den":2}
	check(view.audio_rect(0).end.x==view.x(7),"rational timeline uses the same integer endpoint")
	view.free()
	var legacy_path: String=OS.get_cmdline_user_args()[0]
	var legacy=load(legacy_path)
	check(not legacy.layout_error(document).is_empty(),"actual previous source rejects version3 instead of ignoring the trim")
	print("AUDIO_TRIM_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
