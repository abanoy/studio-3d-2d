extends "res://tests/audio_sparse_unit.gd"
func levels_ok(result: Dictionary) -> bool:
	if result.clip_waveform_levels.size()!=result.clip_peaks.size():return false
	for row in range(result.clip_waveform_levels.size()):
		var levels: Array=result.clip_waveform_levels[row]
		if levels.size()!=6 or levels[0]!=result.clip_peaks[row]:return false
		for i in range(levels.size()):
			if levels[i].size()!=256*(1<<i):return false
			for value in levels[i]:
				if not is_finite(value) or value<0 or value>1:return false
			if i==levels.size()-1:continue
			for bucket in range(levels[i].size()):
				if levels[i][bucket]!=maxf(levels[i+1][bucket*2],levels[i+1][bucket*2+1]):return false
	return true
func _initialize() -> void:
	for rate in [[24,1],[30000,1001]]:
		for mode in ["disjoint","overlap","muted","fades"]:
			var result:=Audio.mix_document(fixture(1440,mode),{"fps_num":rate[0],"fps_den":rate[1],"duration_frames":1440})
			check(not result.has("error") and levels_ok(result),"every cached level preserves exact per-clip maxima: "+str(rate)+" "+mode)
	var pcm:=PackedByteArray();pcm.resize(9600*2);pcm.fill(0)
	var impulses:=[[0,26000],[2400,18000],[4800,-10000],[7200,3200]]
	for pair in impulses:pcm.encode_s16(pair[0]*2,pair[1])
	var source:={"pcm":pcm,"rate":48000,"channels":1,"frames":9600,"path":"procedural.wav","name":"Four impulses","sha256":"0".repeat(64)}
	var clip:=Audio.make_clip(source);clip.start_frame=1296
	var video:={"fps_num":24,"fps_den":1,"duration_frames":1440};var result:=Audio.mix_document(Audio.document([clip]),video)
	check(levels_ok(result),"single-clip quantized overview has the same exact max pyramid")
	var fine: PackedFloat32Array=result.clip_waveform_levels[0][-1];var expected:={}
	for pair in impulses:expected[(Audio.sample_index(1296,video)+pair[0])*8192/result.samples]=absf(pair[1]/32768.)
	var exact:=true;var live:=0
	for i in range(fine.size()):
		if fine[i]>0:live+=1
		exact=exact and absf(fine[i]-expected.get(i,0.))<.0000001
	check(exact and live==4,"four short late transients retain independent exact times and amplitudes")
	var overview: PackedFloat32Array=result.clip_peaks[0];var coarse_live:=0
	for value in overview:
		if value>0:coarse_live+=1
	check(coarse_live==2,"same four transients occupied only two original overview bins")
	var bytes:=0
	for level in result.clip_waveform_levels[0]:bytes+=level.size()*4
	check(bytes==64512 and bytes*Audio.MAX_CLIPS==1032192,"cached peak payload stays bounded near1MiB for16clips")
	clip.muted=true;result=Audio.mix_document(Audio.document([clip]),video)
	check(levels_ok(result) and result.clip_waveform_levels[0][-1].count(0.0)==8192,"muted single clip has zero peaks at every resolution")
	result=Audio.mix_document({},video);check(result.clip_waveform_levels.is_empty(),"empty scene does not own unnecessary clip waveform levels")
	var view:=preload("res://src/timeline_view.gd").new();view.size=Vector2(1200,160);view.duration=1440
	clip.muted=false;result=Audio.mix_document(Audio.document([clip]),video)
	view.clip_waveforms=result.clip_peaks;view.clip_waveform_levels=result.clip_waveform_levels
	check(view.visible_waveform(0).size()==256,"Fit retains original waveform overview")
	view.window_span=22.5;check(view.visible_waveform(0).size()==8192,"short visible range chooses detailed cached peaks")
	view.window_span=720;check(view.visible_waveform(0).size()>256 and view.visible_waveform(0).size()<8192,"intermediate zoom chooses bounded intermediate detail")
	view.clip_waveform_levels=[];check(view.visible_waveform(0).size()==256,"missing optional cache falls back to existing overview");view.free()
	var child_video:=video.duplicate();child_video.duration_frames=48
	var child_audio:=Audio.document([Audio.make_clip(source)])
	var child:={"schema_version":4,"video":child_video,"layers":[],"world":{"format":"studio_world_1","objects":[]},"audio":child_audio}
	var graph:={"format":"studio_sequences_1","assets":[{"id":"child","name":"Child audio","scene":child,"clips":[]}],"clips":[{"id":"nested","asset_id":"child","start":1296,"duration":48,"source_in":0,"time_in":0,"key_in":0,"loop":false,"visible":true,"muted":false,"gain_db":0,"keys":[preload("res://src/sequence_graph.gd").key()]}]}
	video["width"]=1920;video["height"]=1080;child_video["width"]=1920;child_video["height"]=1080
	var nested:=preload("res://src/sequence_audio.gd").build(graph,{"video":video,"layers":[],"world":{"format":"studio_world_1","objects":[]},"audio":Audio.document([clip])})
	check(not nested.has("error") and nested.mixes[""].clip_waveform_levels[0][-1]==result.clip_waveform_levels[0][-1],"nested parent retains its own independent waveform cache")
	check(not nested.has("error") and nested.mixes.child.clip_waveform_levels[0].size()==6,"child keeps its local waveform levels for entering its timeline")
	print("WAVEFORM_LEVELS_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
