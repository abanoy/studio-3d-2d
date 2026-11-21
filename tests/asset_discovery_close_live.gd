extends SceneTree
## Explicit opt-in native HTTP lifecycle probe; closes the real browser window.
const DiscoveryWindow = preload("res://src/discovery/window.gd")
var started := 0

func _initialize() -> void:
	started = Time.get_ticks_msec()
	create_timer(10).timeout.connect(func(): quit(2))
	call_deferred("run")

func run() -> void:
	var studio_quit := "--studio-quit" in OS.get_cmdline_user_args()
	var app
	var window: Window
	if studio_quit:
		var folder := ProjectSettings.globalize_path("res://output/discovery-quit-live-%d" % OS.get_process_id())
		DirAccess.make_dir_recursive_absolute(folder)
		app = load("res://main.tscn").instantiate()
		app.display_prefs_path = folder.path_join("prefs.cfg"); app.recovery_root = folder.path_join("recovery"); app.recent_path = folder.path_join("recent.json")
		root.add_child(app); await process_frame; await process_frame
		app.home.hide(); app.autosave_enabled.button_pressed = false
		var bridge = app.get_node("AssetDiscoveryBridge"); bridge.preferences_path = ""; bridge.open(); window = bridge.window
	else: window = DiscoveryWindow.open(root, Callable(), {"preferences_path":""})
	var panel = window.get_meta("discovery_panel")
	panel.tabs.current_tab = 1; panel.website.select(2)
	panel.expand.set_pressed_no_signal(false); panel.network.button_pressed = true
	panel.search.text = "Hatsune Miku"; panel.search_button.pressed.emit()
	var deadline := Time.get_ticks_msec() + 2000
	while not is_instance_valid(panel.online._http) and panel.online.loading and Time.get_ticks_msec() < deadline: await process_frame
	var service_ref: WeakRef = weakref(panel.online)
	var request_ref: WeakRef
	var phase := -1
	if is_instance_valid(panel.online._http):
		while is_instance_valid(panel.online._http) and panel.online._http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED and Time.get_ticks_msec() < deadline: await process_frame
	if is_instance_valid(panel.online._http):
		request_ref = weakref(panel.online._http)
		phase = panel.online._http.get_http_client_status()
	var was_loading: bool = panel.online.loading
	if studio_quit: await app.quit_studio()
	else: window.close_requested.emit(); await create_timer(0.25).timeout
	var report := {"native_request_existed":request_ref != null, "loading_before_close":was_loading, "native_http_phase_before_close":phase, "window_freed":not is_instance_valid(window), "service_freed":service_ref.get_ref() == null, "request_freed":request_ref == null or request_ref.get_ref() == null, "seconds":(Time.get_ticks_msec() - started) / 1000.0, "scope":"Real production window closed during a native HTTPRequest. Metadata only; no model/image download or source-page launch."}
	report.studio_quit = studio_quit
	var file := FileAccess.open("res://output/asset-discovery-quit-live.json" if studio_quit else "res://output/asset-discovery-close-live.json", FileAccess.WRITE); file.store_string(JSON.stringify(report, "  ")); file.close()
	print("DISCOVERY_CLOSE_LIVE " + JSON.stringify(report))
	quit(0 if report.native_request_existed and report.loading_before_close and report.window_freed and report.service_freed and report.request_freed else 1)
