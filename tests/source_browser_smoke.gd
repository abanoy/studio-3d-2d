extends SceneTree
const Support = preload("res://tests/world_test_support.gd")
const Timeline = preload("res://src/timeline.gd")
var checks := 0
var failures := 0

func _initialize() -> void:
	create_timer(180).timeout.connect(func(): push_error("Browser watchdog expired"); quit(2))
	call_deferred("run")

func check(ok: bool, text: String) -> void:
	checks += 1; print(("PASS " if ok else "FAIL ") + text)
	if not ok: failures += 1

func wait_scan(browser) -> int:
	var frames := 0
	while browser.job_pid > 0: frames += 1; await process_frame
	return frames

func finish_import(app) -> void:
	# Dismiss only this test app's notices; do not enable physics from the test.
	for child in app.get_children():
		if child is AcceptDialog and child.title in ["Source import warnings","Imported with limitations"]:child.hide();child.queue_free()
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw

func run() -> void:
	var app = load("res://main.tscn").instantiate(); root.add_child(app)
	await process_frame
	var folder := ProjectSettings.globalize_path("res://output/source-browser-smoke")
	DirAccess.make_dir_recursive_absolute(folder)
	app.source_import.paths_file = folder.path_join("paths.cfg")
	app.source_import.mount_overrides = {}; app.source_import.extra_roots = []
	app.source_import.gmod_root = app.source_import.DEFAULT_GMOD; app.source_import.workshop_root = app.source_import.DEFAULT_WORKSHOP
	var browser = app.source_browser
	browser.cache_root = folder.path_join("worker")
	var before_source: String = app.source
	var before_keys := JSON.stringify(app.keys)
	browser.open()
	check(browser.job_pid > 0, "Installed browser starts an asynchronous read-only discovery process")
	var pulses: int = await wait_scan(browser)
	check(pulses > 0 and browser.providers.size() > 10, "editor processes frames while installed packages are discovered")
	var css := {}; var workshop := {}
	for provider in browser.providers:
		if str(provider.path).ends_with("content_cstrike_dir.vpk"): css = provider
		if provider.origin == "workshop" and workshop.is_empty(): workshop = provider
	check(not css.is_empty() and not workshop.is_empty(), "browser finds included CSS content and actual Workshop add-ons")
	var sfm_marker := "C:/Program Files (x86)/Steam/steamapps/common/SourceFilmmaker/game/usermod/gameinfo.txt"
	check(browser.discovery.games[-1].name == "SourceFilmmaker" and browser.discovery.games[-1].installed == FileAccess.file_exists(sfm_marker), "optional SFM detection reflects actual gameinfo presence, including installs added during this session")
	browser.source_filter.text = "content_cstrike_dir"; browser.filter_sources()
	check(browser.source_rows.size() == 1, "source filter isolates the included CSS VPK")
	browser.sources.select(0); browser.sources.item_selected.emit(0)
	await wait_scan(browser)
	check(browser.assets.size() > 1000, "actual VPK index exposes compiled model members without unpacking the archive")
	browser.search.text = "chair_office"; browser.filter_assets()
	check(browser.filtered.size() == 1 and browser.filtered[0].path.ends_with("chair_office.mdl"), "asset search locates the real CSS chair model")
	browser.entries.select(0); browser.entries.item_selected.emit(0)
	check(not browser.import_button.disabled and browser.details.text.contains("content_cstrike_dir"), "selection exposes original source and enables an actionable import")
	await process_frame; await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder.path_join("browser-css.png"))
	check(browser.window.position.x >= 0 and browser.window.position.y + browser.window.size.y <= root.size.y, "content browser and import controls fit the current app window")
	browser.import_button.pressed.emit()
	await process_frame
	check(app.source_import.pid > 0 and app.source == before_source, "browser selection launches the existing native conversion without replacing the environment")
	while app.source_import.pid > 0: await process_frame
	check(Support.rig(app) != null, "selected VPK member installs through the existing standard model slot")
	if Support.rig(app) == null: print(app.status.text); quit(1); return
	var report_path: String = app.source_import.folder.path_join("parameters.json")
	var report = JSON.parse_string(FileAccess.get_file_as_string(report_path))
	check(report.counts.textures > 0 and report.warnings.is_empty(), "included CSS model resolves its actual material and VTF without missing-texture fallbacks")
	check(app.source == before_source and JSON.stringify(app.keys) == before_keys, "browser import preserves the independent environment and camera track")
	app.pose_editor.frame_model()
	var camera: Camera3D = app.renderer.camera
	app.keys = [Timeline.key(0, camera.position, camera.quaternion, camera.fov), Timeline.key(48, camera.position, camera.quaternion, camera.fov)]
	var image: Image = await app.renderer.capture(app.keys, app.layers, 0)
	image.save_png(folder.path_join("css-chair.png"))
	var restored_model: Dictionary = Support.rig(app).data.duplicate(true)
	app.project_folder = folder.path_join("project"); app.save()
	app.renderer.install_model({"model": null})
	check(app.open_project(app.project_folder) and Support.rig(app).data.sha256 == restored_model.sha256, "browsed model survives managed save/reopen through the shared format")
	# Reopen the library and test explicit mount preference persistence and cancellation.
	browser.open(); await wait_scan(browser)
	browser.search.text = "reimu_hakurei"; browser.search_all()
	await wait_scan(browser)
	check(browser.filtered.size() >= 9, "all-source search finds actual Reimu models across installed Workshop packages")
	if browser.filtered.is_empty(): print(browser.state.text); quit(1); return
	workshop = browser.filtered[0].provider
	browser.source_filter.text = workshop.path.get_file(); browser.filter_sources()
	var selected := -1
	for i in range(browser.source_rows.size()):
		if browser.source_rows[i].path == workshop.path: selected = i
	check(selected >= 0, "installed Workshop package can be located independently of the base game")
	if selected >= 0:
		browser.sources.select(selected); browser.sources.item_selected.emit(selected)
		await wait_scan(browser)
		check(browser.assets.size() > 0, "real Workshop archive exposes model/map members in-app")
		browser.mount.button_pressed = false
		browser.mount.button_pressed = true
		app.source_import.load_paths()
		check(app.source_import.mount_overrides.get(workshop.path, false), "explicit dependency checkbox persists without changing game mount.cfg")
		browser.mount.button_pressed = false
		browser.search.text = "ragdoll/reimu_hakurei_bikini_ragdoll"; browser.filter_assets()
		check(browser.filtered.size() == 1, "Workshop model selection retains the exact archive member")
		var previous_actor: String=Support.rig(app).data.id
		browser.entries.select(0); browser.entries.item_selected.emit(0); browser.import_button.pressed.emit()
		await process_frame # Run the library's deferred import action before checking.
		var confirm: ConfirmationDialog
		for control in app.get_children():
			if control is ConfirmationDialog:
				print("BROWSER_DIALOG "+JSON.stringify({"class":control.get_class(),"title":control.title,"text":control.dialog_text,"visible":control.visible,"queued":control.is_queued_for_deletion()}))
				# LayerEditor owns a reusable hidden confirmation. It is not an
				# import prompt and must never be confirmed by this browser test.
				if control.visible: confirm = control
		check(confirm == null, "library Add appends without a misleading replacement prompt")
		while app.source_import.pid > 0: await process_frame
		check(Support.rig(app) != null and Support.rig(app).order.size() == 77 and app.renderer.world_runtime.instances.has(previous_actor), "actual Workshop GMA appends poseable 77-bone model while retaining earlier actor")
		await finish_import(app)
		check(app.physics_editor.active(Support.rig(app).data.id) and Support.rig(app).data.pose_keys.is_empty(),"Installed Workshop ragdoll starts real physics without generating animation keys")
		root.get_texture().get_image().save_png(folder.path_join("workshop-physics.png"))
	var actor_hash: String = Support.rig(app).data.sha256
	browser.open(false); await wait_scan(browser)
	browser.source_filter.text = "Garry's Mod / loose"; browser.filter_sources()
	var loose := -1
	for i in range(browser.source_rows.size()):
		if browser.source_rows[i].kind == "folder": loose = i; break
	check(loose >= 0, "map browsing can locate the installed game's loose map folder beside its VPKs")
	if loose >= 0:
		browser.sources.select(loose); browser.sources.item_selected.emit(loose); await wait_scan(browser)
		browser.search.text = "gm_construct"; browser.filter_assets()
		check(browser.filtered.size() == 1 and browser.filtered[0].kind == "map", "Maps filter finds actual gm_construct BSP")
		browser.entries.select(0); browser.entries.item_selected.emit(0); browser.import_button.pressed.emit()
		await process_frame
		while app.source_import.pid > 0: await process_frame
		check(FileAccess.get_sha256(app.source)==FileAccess.get_sha256(app.source_import.folder.path_join("scene.glb")) and app.source != before_source and app.mode.selected == 1, "browsed BSP appends standard environment and opens Scene navigation")
		check(Support.rig(app) != null and Support.rig(app).data.sha256 == actor_hash, "browsed map replacement preserves the independent poseable actor")
		await finish_import(app)
		check(app.physics_editor.active(Support.rig(app).data.id) and not app.physics_editor.active(app.last_import_id),"Installed map import resumes the live ragdoll and keeps the map static")
	var retained_scene: String = app.source
	browser.open(); await wait_scan(browser)
	browser.search.text = "reimu_hakurei"; browser.search_all()
	check(browser.job_pid > 0, "all-source search runs in a cancellable worker")
	var owned_pid: int = browser.job_pid
	browser.cancel_scan()
	await process_frame
	check(browser.job_pid < 0 and not OS.is_process_running(owned_pid), "cancel stops only the browser's owned read-only scan")
	browser.close()
	check(Support.rig(app) != null and app.source == retained_scene, "closing browser keeps imported project data")
	var result := {"checks": checks, "failures": failures, "providers": browser.providers.size(), "css_bundle": report_path.get_base_dir()}
	var output := FileAccess.open(folder.path_join("result.json"), FileAccess.WRITE); output.store_string(JSON.stringify(result)); output.close()
	print("SOURCE_BROWSER " + JSON.stringify(result))
	quit(0 if failures == 0 else 1)
