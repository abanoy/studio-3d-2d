extends SceneTree
# Source-only regression: root runs the same script on original and proposed source.
const StudioTheme = preload("res://src/studio_theme.gd")
var folder := ""
var checks := 0
var failures := 0

func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("World rail lifecycle watchdog");quit(2))
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	print(("PASS " if ok else "FAIL ") + label)
	if not ok:failures += 1

func settled() -> void:
	for i in range(6):await process_frame
	await RenderingServer.frame_post_draw

func fresh_app(label: String):
	var app=load("res://main.tscn").instantiate()
	app.recovery_root=folder.path_join(label+"-recovery")
	app.recent_path=folder.path_join(label+"-recent.json")
	app.display_prefs_path=folder.path_join(label+"-display.cfg")
	root.add_child(app);await settled()
	app.home.hide();app.autosave_enabled.button_pressed=false
	app.apply_theme_style("neon");app.set_advanced(false)
	app.workspace_layout.path=folder.path_join(label+"-workspace.json")
	await settled()
	return app

func font_profile(selection, neon: bool, label: String) -> void:
	var font: Font=selection.tree.get_theme_font("font")
	var system: SystemFont=font as SystemFont
	check(system!=null,label+" keeps the real SystemFont override")
	check(system!=null and system.font_names==PackedStringArray(StudioTheme.UI_FONTS if neon else ["Yu Gothic UI","Segoe UI","Arial"]),label+" keeps the approved font family order")
	var fallback_ok:=not neon
	if neon and system!=null and system.fallbacks.size()==1:
		var fallback: SystemFont=system.fallbacks[0] as SystemFont
		fallback_ok=fallback!=null and fallback.font_names==PackedStringArray(["Yu Gothic UI","Segoe UI","Arial"]) and system.font_weight==500
	check(fallback_ok,label+" preserves the Neon weight500 and Japanese fallback")

func world_connections(ws) -> int:
	var count:=0
	for row in ws.panels.world.resized.get_connections():
		if row.callable==Callable(ws,"refresh_world_mode"):count+=1
	return count

func reentry_and_fonts() -> void:
	var app=await fresh_app("reentry")
	var ws=app.workspace_layout
	var selection=app.world_selection
	font_profile(selection,true,"Neon startup")
	app.apply_theme_style("light");await settled();font_profile(selection,false,"Classic switch")
	app.apply_theme_style("neon");await settled();font_profile(selection,true,"Neon return")
	check(world_connections(ws)==1,"live World resize has exactly one owner callback")
	ws.timer.stop();ws.save_later();app.remove_child(ws)
	check(not ws.is_inside_tree() and world_connections(ws)==0,"layout exit disconnects World before sibling controls are removed")
	check(FileAccess.file_exists(ws.path),"layout exit still flushes its pending preference save")
	var font_id: int=selection.tree.get_theme_font("font").get_instance_id()
	ws.refresh_world_mode(true);ws.panels.world.resized.emit()
	check(selection.tree.get_theme_font("font").get_instance_id()==font_id,"off-tree layout and resize cannot replace a live sibling Tree font")
	app.add_child(ws);await settled()
	check(world_connections(ws)==1,"layout reentry reconnects its World callback exactly once")
	ws.dock("world","right");await settled()
	check(not ws.world_rail and not selection.rail_mode and selection.tree.visible,"real docking after reentry still updates the World list")
	app.remove_child(selection)
	var before_mode: bool=selection.rail_mode
	selection.set_rail(not before_mode,true)
	check(not selection.is_inside_tree() and selection.rail_mode==before_mode,"off-tree selection rejects a direct rail restyle")
	app.add_child(selection);selection.set_rail(not before_mode,true)
	check(selection.rail_mode!=before_mode,"selection reentry permits a genuine live rail update")
	selection.set_rail(before_mode,true)
	var holder:=Control.new();root.add_child(holder);holder.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	app.reparent(holder);await settled()
	check(world_connections(ws)==1,"whole-application reparent keeps exactly one World resize callback")
	ws.reset();await settled();ws.dock("world","right");await settled()
	check(not ws.world_rail and not selection.rail_mode and selection.tree.visible,"real docking after application reparent still reaches the live hierarchy")
	font_profile(selection,true,"Reparented Neon")
	var owner_ref: WeakRef=weakref(app);var layout_ref: WeakRef=weakref(ws);var selection_ref: WeakRef=weakref(selection)
	app.free();await settled()
	check(owner_ref.get_ref()==null and layout_ref.get_ref()==null and selection_ref.get_ref()==null,"direct free releases the reparented owner and both presentation managers")
	holder.free()

func queued_owner() -> void:
	var app=await fresh_app("queued")
	var ws=app.workspace_layout
	var selection=app.world_selection
	var mode: bool=selection.rail_mode
	var font_id: int=selection.tree.get_theme_font("font").get_instance_id()
	var owner_ref: WeakRef=weakref(app)
	app.queue_free()
	check(app.is_queued_for_deletion(),"queue-free case reaches an actual pending deletion")
	selection.set_rail(not mode,true)
	check(selection.rail_mode==mode,"queued owner blocks direct World selection restyling before the next frame")
	ws.refresh_world_mode(true);ws.panels.world.resized.emit()
	check(selection.tree.get_theme_font("font").get_instance_id()==font_id,"queued owner blocks resize-triggered font replacement")
	await settled();check(owner_ref.get_ref()==null,"queued owner is actually freed on the following frame")

func immediate_owner() -> void:
	var app=await fresh_app("immediate")
	var selection=app.world_selection
	for i in range(6):
		app.workspace_layout.refresh_world_mode(true)
		app.get_window().size=Vector2i(1200+i*2,760+i*2)
	check(selection.tree.is_inside_tree(),"immediate-free control has a real styled Tree with pending layout work")
	var owner_ref: WeakRef=weakref(app);var selection_ref: WeakRef=weakref(selection)
	app.free();await settled()
	check(owner_ref.get_ref()==null and selection_ref.get_ref()==null,"immediate free after real resize/restyle releases owner and selection")

func withheld_control_transaction() -> void:
	var app=await fresh_app("withheld")
	var ws=app.workspace_layout
	var selection=app.world_selection
	ws.reset();await settled()
	ws.horizontal.clamp_split_offset()
	ws.horizontal.split_offset+=int(roundf(64.0-ws.slots.left.size.x))
	ws.horizontal.clamp_split_offset();await settled()
	ws.refresh_world_mode(true)
	var before_layout: bool=ws.world_rail
	var before_selection: bool=selection.rail_mode
	var kept_help: Label=selection.help_label
	var saved_parent: Node=kept_help.get_parent()
	var saved_index: int=kept_help.get_index()
	saved_parent.remove_child(kept_help)
	var accepted: bool=selection.set_rail(false,true)
	check(before_layout and before_selection and not kept_help.is_inside_tree() and not accepted,"withheld help control makes the different-mode setter refuse explicitly")
	ws.dock("world","right")
	ws.refresh_world_mode(true)
	check(not ws.want_full_left() and ws.world_rail==before_layout and selection.rail_mode==before_selection,"refused right-dock transition preserves both accepted mode caches")
	print("NEON_WORLD_RAIL_TRANSACTION_STATE ",JSON.stringify({"phase":"withheld","setter_accepted":accepted,"requested_rail":false,"layout_rail":ws.world_rail,"selection_rail":selection.rail_mode,"help_inside":kept_help.is_inside_tree()}))
	saved_parent.add_child(kept_help);saved_parent.move_child(kept_help,saved_index)
	ws.refresh_world_mode(true)
	check(kept_help==selection.help_label and kept_help.get_parent()==saved_parent and kept_help.get_index()==saved_index and kept_help.is_inside_tree() and not ws.world_rail and not selection.rail_mode and selection.tree.visible,"same help control and index restored: one explicit refresh reaches the full World list")
	print("NEON_WORLD_RAIL_TRANSACTION_STATE ",JSON.stringify({"phase":"restored","requested_rail":false,"layout_rail":ws.world_rail,"selection_rail":selection.rail_mode,"tree_visible":selection.tree.visible,"help_inside":kept_help.is_inside_tree()}))
	app.free();await settled()

func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=1:push_error("Provide one fresh owned output directory");quit(2);return
	folder=ProjectSettings.globalize_path(args[0]).simplify_path()
	var boundary:=ProjectSettings.globalize_path("res://output").simplify_path().trim_suffix("/")+"/"
	if not folder.begins_with(boundary) or DirAccess.dir_exists_absolute(folder):push_error("Fresh owned output required");quit(2);return
	DirAccess.make_dir_recursive_absolute(folder)
	root.size=Vector2i(1400,900)
	await reentry_and_fonts();await queued_owner();await immediate_owner();await withheld_control_transaction()
	var report:={"format":"has_neon_world_rail_transaction_lifecycle_1","checks":checks,"failures":failures,"cases":["theme-detach-reentry-reparent-free","queued-owner","immediate-free-resize","withheld-control-transaction"],"source_only_fixture_uses_native_models":false}
	var encoded:=JSON.stringify(report,"",true,true)
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(encoded);file.close()
	print("NEON_WORLD_RAIL_TRANSACTION_LIFECYCLE ",encoded);quit(0 if failures==0 else 1)
