extends SceneTree
const Choice=preload("res://src/source_choice_dialog.gd")
const Model=preload("res://src/model.gd")
var app
var folder: String
var checks:=0
var failures:=0
var jobs: Array=[]
func _initialize() -> void:
 create_timer(150).timeout.connect(func():push_error("Source choices UI watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func settled() -> void:
 for _i in range(3):await process_frame
 await RenderingServer.frame_post_draw
func snapshot() -> String:return JSON.stringify(app.project_snapshot(),"",true,true)
func open_choices(path: String) -> Dictionary:
 app.source_import.start(path,true)
 for child in app.get_children():
  if child is ConfirmationDialog and child.title=="Import Source model":
   for controller in child.get_children():
    if controller.get_script()==Choice:return {"dialog":child,"choice":controller}
 return {}
func wait_metadata(choice) -> int:
 var frames:=0
 while choice.pid>0:await process_frame;frames+=1
 await settled();return frames
func close_dialog(row: Dictionary) -> void:
 row.dialog.canceled.emit();await settled()
func run() -> void:
 folder=OS.get_cmdline_user_args()[0]
 app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=folder.path_join("display.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.source_import.paths_file=folder.path_join("source-paths.cfg")
 app.new_project();var placement: Dictionary=app.import_actions.placement();placement.physics_on_import=false;placement.review_height=false
 check(app.pose_editor.add_model(ProjectSettings.globalize_path("res://examples/tutorials/Practice figure.glb"),0,placement).is_empty(),"independent existing model enters the normal scene")
 await settled();var before:=snapshot();var history: int=app.history.size();var pixels: Image=await app.renderer.capture(app.keys,app.layers,0,true)
 var path:=folder.path_join("choices.mdl");var original:=FileAccess.get_sha256(path)
 var row:=open_choices(path);check(not row.is_empty(),"ordinary Source import opens actual optional appearance controls")
 if row.is_empty():await app.quit_studio();quit(1);return
 var choice=row.choice;var live_pid: int=choice.pid
 check(live_pid>0 and choice.worker_map_reserved,"real metadata Python child is retained through the pinned process map")
 var frames: int=await wait_metadata(choice)
 check(frames>0 and not choice.enabled.disabled and choice.worker_exit==0,"real metadata finishes while the private editor continues frames")
 check(choice.release_calls==1 and not choice.worker_map_reserved and choice.worker_stdio==null and choice.worker_stderr==null,"successful inspection drains pipes and releases its exact process entry once")
 jobs.append({"phase":"success","pid":live_pid,"frames":frames,"exit":choice.worker_exit,"release_calls":choice.release_calls,"release_result":choice.release_result})
 check(choice.skin.item_count==3 and choice.groups.size()==2,"hand-authored native tables populate actual skin and part controls")
 check(choice.request().is_empty() and not row.dialog.get_ok_button().disabled,"unchecked default remains the ordinary import route")
 choice.enabled.button_pressed=true
 check(choice.request().is_empty(),"enabling unchanged defaults still omits an appearance override")
 choice.skin.select(1);choice.skin.item_selected.emit(1)
 choice.groups[0].option.select(1);choice.groups[0].option.item_selected.emit(1)
 var selected: Dictionary=choice.request()
 check(selected.get("format")=="studio_source_appearance_request_1" and selected.get("skin")==1 and selected.bodygroups=={"0":1,"1":0},"actual widgets emit integer identities and canonical group keys")
 check(selected.source_sha256==original and selected.native_mdl_sha256==original,"real inspection binds both loose original and selected native bytes")
 check(choice.groups[0].option.get_item_text(0)=="blank" and not choice.groups[0].choices[0].true_blank,"a nonempty native choice named blank stays visible")
 choice.groups[1].option.select(1);choice.groups[1].option.item_selected.emit(1)
 check(not choice.selection_valid() and row.dialog.get_ok_button().disabled and not row.dialog.dialog_hide_on_ok,"all-hidden selection disables confirmation without auto-hiding the editor")
 row.dialog.confirmed.emit();await settled()
 check(row.dialog.visible and app.source_import.pid<0 and snapshot()==before and app.history.size()==history,"invalid explicit confirmation starts no converter and changes no existing project")
 root.get_texture().get_image().save_png(folder.path_join("all-hidden-ui.png"))
 await close_dialog(row)
 check(snapshot()==before and app.history.size()==history,"closing reviewed choices preserves existing authored state and Undo")
 # Cancel immediately, before a process-frame poll can race normal completion.
 row=open_choices(path);choice=row.choice;live_pid=choice.pid
 row.dialog.canceled.emit()
 check(choice.pid<0 and choice.release_calls==1 and not choice.worker_map_reserved,"immediate cancel consumes one owned entry without a raw PID fallback")
 jobs.append({"phase":"cancel","pid":live_pid,"release_calls":choice.release_calls,"release_result":choice.release_result})
 await settled();check(snapshot()==before and app.history.size()==history,"cancelled inspection cannot adopt a late model or edit the project")
 row=open_choices(folder.path_join("bad.mdl"));choice=row.choice;live_pid=choice.pid;await wait_metadata(choice)
 check(choice.enabled.disabled and not row.dialog.get_ok_button().disabled and choice.catalogue.is_empty(),"a real malformed native header leaves only the explained default path")
 check(choice.worker_exit!=0 and choice.release_calls==1 and not choice.worker_map_reserved,"metadata refusal retains its nonzero result and closes process ownership")
 jobs.append({"phase":"refusal","pid":live_pid,"exit":choice.worker_exit,"release_calls":choice.release_calls,"release_result":choice.release_result})
 await close_dialog(row)
 var after: Image=await app.renderer.capture(app.keys,app.layers,0,true)
 check(after.get_data()==pixels.get_data() and snapshot()==before and app.history.size()==history,"metadata success/cancel/refusal leave final scene pixels and authored project exact")
 check(FileAccess.get_sha256(path)==original,"metadata controls preserve original MDL bytes")
 var result:={"checks":checks,"failures":failures,"actual_app":true,"actual_metadata_children":jobs,"native_conversion":false,"render_and_project_preserved":after.get_data()==pixels.get_data() and snapshot()==before}
 FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SOURCE_CHOICES_UI "+JSON.stringify(result));await app.quit_studio();quit(0 if failures==0 else 1)
