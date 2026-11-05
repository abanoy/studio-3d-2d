extends RefCounted
const RATE := 48000
const MAX_SECONDS := 60
const FORMAT := "studio_audio_2"
const MAX_CLIPS := 16
const MAX_PCM := 64 * 1024 * 1024

static func clips(audio: Dictionary) -> Array:
	if audio.is_empty(): return []
	return audio.clips if audio.get("format") == FORMAT and audio.get("clips") is Array else [audio]

static func document(rows: Array) -> Dictionary:
	if rows.is_empty(): return {}
	return rows[0] if rows.size() == 1 else {"format":FORMAT,"clips":rows}

static func metadata(audio: Dictionary) -> Dictionary:
	var rows := []
	for clip in clips(audio):
		rows.append({"id":clip.id,"source_name":clip.source.name,"sha256":clip.source.sha256,"path":"assets/"+str(clip.source.sha256)+".wav","start_frame":clip.start_frame,"source_in_sample":clip.source_in_sample,"gain_db":clip.gain_db,"muted":clip.muted})
	return document(rows)

static func layout_error(audio: Dictionary) -> String:
	if audio.is_empty(): return ""
	if audio.has("format") or audio.has("clips"):
		if audio.get("format") != FORMAT or audio.size() != 2 or not audio.get("clips") is Array or audio.clips.is_empty() or audio.clips.size() > MAX_CLIPS:
			return "Unsupported audio collection or more than16 clips."
	var ids := {}
	for clip in clips(audio):
		if not clip is Dictionary or not clip.get("id") is String or clip.id.is_empty() or clip.id.length() > 128 or ids.has(clip.id):
			return "Invalid or duplicate audio clip identity."
		ids[clip.id] = true
	return ""

static func memory(audio: Dictionary) -> int:
	var bytes := 0
	for clip in clips(audio):
		if clip.get("source") is Dictionary and clip.source.get("pcm") is PackedByteArray: bytes += clip.source.pcm.size()
	return bytes

static func clip_error(clip: Dictionary, video: Dictionary) -> String:
	if not clip.get("muted") is bool: return "Invalid audio mute value."
	for field in ["start_frame","source_in_sample","gain_db"]:
		var value = clip.get(field)
		if not (value is int or value is float) or not is_finite(float(value)): return "Invalid audio timing/gain."
	if clip.start_frame != floor(clip.start_frame) or clip.start_frame < 0 or clip.start_frame >= video.duration_frames or clip.source_in_sample != floor(clip.source_in_sample) or clip.source_in_sample < 0 or clip.source_in_sample > MAX_SECONDS*96000 or clip.gain_db < -60 or clip.gain_db > 12:
		return "Invalid audio timing/gain."
	return ""

static func mix_document(audio: Dictionary, video: Dictionary) -> Dictionary:
	var error := layout_error(audio)
	if not error.is_empty(): return {"error":error}
	if memory(audio) > MAX_PCM: return {"error":"Audio clips exceed64MiB of decoded source samples."}
	var rows := clips(audio)
	for clip in rows:
		error = clip_error(clip,video)
		if not error.is_empty(): return {"error":error}
		if not clip.get("source") is Dictionary or not clip.source.get("pcm") is PackedByteArray: return {"error":"Missing decoded audio source."}
		var source: Dictionary=clip.source
		if not source.get("rate") is int or source.rate<8000 or source.rate>96000 or not source.get("frames") is int or source.frames<1 or source.frames>source.rate*MAX_SECONDS or not source.get("channels") is int or not source.channels in [1,2] or source.pcm.size()!=source.frames*source.channels*2 or clip.source_in_sample>=source.frames:
			return {"error":"Invalid decoded audio samples or source trim."}
	if rows.size() <= 1:
		var result := mix(rows[0] if not rows.is_empty() else {},video)
		if not result.has("error"): result["clip_peaks"] = [result.peaks] if not rows.is_empty() else []
		return result
	var count := sample_index(video.duration_frames,video)
	if count < 1 or count > RATE * MAX_SECONDS: return {"error":"Audio preview/export supports sequences up to60 seconds."}
	# Sum before clipping/quantization; a loud early clip cannot destroy a later
	# cancelling contribution. Preview, saved mix and encoder use these same bytes.
	var sum := PackedFloat64Array(); sum.resize(count * 2); sum.fill(0)
	var per_clip := []
	for clip in rows:
		var peaks := PackedFloat32Array(); peaks.resize(256); peaks.fill(0)
		if not clip.muted:
			var source: Dictionary = clip.source
			var start := sample_index(clip.start_frame,video)
			var gain := db_to_linear(clip.gain_db)
			for index in range(start,count):
				var at: float = float(index-start)*source.rate/RATE + clip.source_in_sample
				var before := floori(at)
				if before >= source.frames: break
				for channel in range(2):
					var value := lerpf(source_value(source,before,channel),source_value(source,before+1,channel),at-before)*gain
					sum[index*2+channel] += value
					var bucket := mini(255,index*256/count)
					peaks[bucket] = maxf(peaks[bucket],minf(1,absf(value/32768.0)))
		per_clip.append(peaks)
	var pcm := PackedByteArray(); pcm.resize(count*4)
	var peaks := PackedFloat32Array(); peaks.resize(256); peaks.fill(0)
	var clipped := 0
	for index in range(count):
		for channel in range(2):
			var value := roundi(sum[index*2+channel])
			if value < -32768 or value > 32767: clipped += 1
			value = clampi(value,-32768,32767)
			pcm.encode_s16(index*4+channel*2,value)
			var bucket := mini(255,index*256/count)
			peaks[bucket] = maxf(peaks[bucket],absf(value/32768.0))
	var stream := AudioStreamWAV.new(); stream.format=AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate=RATE; stream.stereo=true; stream.data=pcm
	return {"stream":stream,"pcm":pcm,"peaks":peaks,"samples":count,"clip_peaks":per_clip,"clipped_samples":clipped}

static func read_wav(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null or file.get_length() < 44 or file.get_length() > 32 * 1024 * 1024:
		return {"error": "WAV missing, too short, or larger than 32 MiB."}
	var bytes := file.get_buffer(file.get_length())
	if bytes.slice(0, 4).get_string_from_ascii() != "RIFF" or bytes.slice(8, 12).get_string_from_ascii() != "WAVE" or bytes.decode_u32(4) + 8 != bytes.size():
		return {"error": "Invalid RIFF/WAVE file or truncated length."}
	var cursor := 12
	var channels := 0
	var rate := 0
	var pcm := PackedByteArray()
	var found_fmt := false
	var found_data := false
	while cursor + 8 <= bytes.size():
		var kind := bytes.slice(cursor, cursor + 4).get_string_from_ascii()
		var length := bytes.decode_u32(cursor + 4)
		cursor += 8
		if length > bytes.size() - cursor:
			return {"error": "Truncated WAV chunk."}
		if kind == "fmt ":
			if found_fmt or length < 16:
				return {"error": "Invalid or duplicate WAV format chunk."}
			found_fmt = true
			channels = bytes.decode_u16(cursor + 2)
			rate = bytes.decode_u32(cursor + 4)
			if bytes.decode_u16(cursor) != 1 or bytes.decode_u16(cursor + 14) != 16 or not channels in [1, 2] or rate < 8000 or rate > 96000 or bytes.decode_u16(cursor + 12) != channels * 2 or bytes.decode_u32(cursor + 8) != rate * channels * 2:
				return {"error": "Use PCM 16-bit mono/stereo WAV, 8–96 kHz. Float/24-bit/compressed WAV is not supported yet."}
		elif kind == "data":
			if found_data: return {"error": "Multiple WAV data chunks are unsupported."}
			found_data = true
			pcm = bytes.slice(cursor, cursor + length)
		cursor += length + (length % 2)
	if not found_fmt or not found_data or pcm.is_empty() or pcm.size() % (channels * 2) != 0:
		return {"error": "WAV is missing complete PCM samples."}
	var frames := pcm.size() / (channels * 2)
	if frames > rate * MAX_SECONDS:
		return {"error": "This audio slice supports WAV clips up to 60 seconds."}
	return {"path": path, "name": path.get_file(), "sha256": FileAccess.get_sha256(path), "pcm": pcm, "channels": channels, "rate": rate, "frames": frames}

static func sample_index(frame: int, video: Dictionary) -> int:
	# Nearest sample from exact rational time, with no cumulative delta/float drift.
	return (frame * RATE * int(video.fps_den) + int(video.fps_num) / 2) / int(video.fps_num)

static func source_value(source: Dictionary, frame: int, channel: int) -> float:
	var index := (clampi(frame, 0, source.frames - 1) * int(source.channels) + mini(channel, source.channels - 1)) * 2
	return source.pcm.decode_s16(index)

static func mix(clip: Dictionary, video: Dictionary) -> Dictionary:
	var count := sample_index(video.duration_frames, video)
	if count < 1 or count > RATE * MAX_SECONDS:
		return {"error": "Audio preview/export supports sequences up to 60 seconds."}
	var pcm := PackedByteArray()
	pcm.resize(count * 4)
	pcm.fill(0)
	var peaks := PackedFloat32Array()
	peaks.resize(256)
	peaks.fill(0)
	if not clip.is_empty() and not clip.muted:
		var source: Dictionary = clip.source
		var start := sample_index(clip.start_frame, video)
		var gain := db_to_linear(clip.gain_db)
		for index in range(start, count):
			var source_time: float = float(index - start) * source.rate / RATE + clip.source_in_sample
			var before := floori(source_time)
			if before >= source.frames: break
			var fraction := source_time - before
			var peak := 0.0
			for channel in range(2):
				var value := lerpf(source_value(source, before, channel), source_value(source, before + 1, channel), fraction) * gain
				var sample := clampi(roundi(value), -32768, 32767)
				pcm.encode_s16(index * 4 + channel * 2, sample)
				peak = maxf(peak, absf(sample / 32768.0))
			var bucket := mini(255, index * 256 / count)
			peaks[bucket] = maxf(peaks[bucket], peak)
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = RATE
	stream.stereo = true
	stream.data = pcm
	return {"stream": stream, "pcm": pcm, "peaks": peaks, "samples": count}

static func make_clip(source: Dictionary) -> Dictionary:
	return {"id": str(ResourceUID.create_id()), "source": source, "start_frame": 0, "source_in_sample": 0, "gain_db": 0.0, "muted": false}
