extends RefCounted
# One worker owns only detached CPU images and journal files, never scene/GPU data.
const Journal=preload("res://src/recovery_journal.gd")
const Drawing=preload("res://src/drawing.gd")
var thread: Thread
var context: Dictionary={}

func busy() -> bool:
	return thread!=null and thread.is_started()

func start(folder: String,digest: String,background: Image,overlays: Array) -> String:
	if busy():return "A recovery preview is already being prepared."
	if not Journal.valid_hash(digest) or not background or background.is_empty():return "Invalid recovery preview snapshot."
	context={"folder":folder,"digest":digest}
	thread=Thread.new()
	var error:=thread.start(_run.bind(folder,digest,background,overlays),Thread.PRIORITY_LOW)
	if error!=OK:thread=null;context={};return "Cannot start recovery preview worker."
	return ""

func poll() -> Dictionary:
	if not busy() or thread.is_alive():return {}
	return finish()

func finish() -> Dictionary:
	if not busy():return {}
	var result: Dictionary=thread.wait_to_finish()
	thread=null;context={}
	return result

func _run(folder: String,digest: String,background: Image,overlays: Array) -> Dictionary:
	var started:=Time.get_ticks_usec()
	background.convert(Image.FORMAT_RGBA8)
	background.resize(Journal.PREVIEW_SIZE.x,Journal.PREVIEW_SIZE.y,Image.INTERPOLATE_BILINEAR)
	for image: Image in overlays:
		image.convert(Image.FORMAT_RGBA8)
		image.resize(Journal.PREVIEW_SIZE.x,Journal.PREVIEW_SIZE.y,Image.INTERPOLATE_BILINEAR)
		image=Drawing.faded(image,float(image.get_meta("studio_layer_opacity",1.0)))
		background.blend_rect(image,Rect2i(Vector2i.ZERO,background.get_size()),Vector2i.ZERO)
	var error:=persist(folder,digest,background)
	return {"folder":folder,"digest":digest,"error":error,"worker_ms":(Time.get_ticks_usec()-started)/1000.0,"background_thread":not Thread.is_main_thread()}

func persist(folder: String,digest: String,image: Image) -> String:
	return Journal.attach_preview(folder,digest,image)
