extends SceneTree
## Explicit opt-in probe of real metadata endpoints. Reports observations, not
## guaranteed catalogue availability. Never requests model files or thumbnails.
const Service = preload("res://src/discovery/service.gd")
var service
var started := 0

func _initialize() -> void:
	started = Time.get_ticks_msec()
	call_deferred("_run")

func _process(_delta: float) -> bool:
	if Time.get_ticks_msec() - started > 45000:
		printerr("Live metadata probe exceeded 45 seconds."); quit(1)
	return false

func _run() -> void:
	service = Service.new(); root.add_child(service)
	service.set_network(true)
	service.search("")
	while service.loading: await process_frame
	var report := {"listings":service.rows.size(), "statuses":service.statuses, "message":service.message, "seconds":(Time.get_ticks_msec() - started) / 1000.0}
	print("LIVE_METADATA_OBSERVATION " + JSON.stringify(report))
	var file := FileAccess.open("res://output/asset-discovery-live.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ")); file.close()
	service.queue_free(); await process_frame
	quit()
