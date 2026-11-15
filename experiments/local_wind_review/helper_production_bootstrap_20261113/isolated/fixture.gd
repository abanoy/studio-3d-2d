extends SceneTree
const Bridge=preload("res://helper_preview_bridge.gd")
var folder:=""
var config: Dictionary={}
var bridge: Node
var action:=1
var event_count:=0
var started_at:=0

func _initialize() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	folder=args[0];started_at=Time.get_ticks_msec();call_deferred("run")

func publish(name: String,value: Dictionary) -> void:
	var file:=FileAccess.open(folder.path_join(name),FileAccess.WRITE)
	if not file:push_error("Cannot publish isolated fixture evidence");quit(2);return
	file.store_string(JSON.stringify(value));file.close()

func run() -> void:
	if DisplayServer.get_name()!="headless":quit(2);return
	publish("host-ready.json",{"pid":OS.get_process_id(),"display_server":DisplayServer.get_name(),"engine_hash":Engine.get_version_info().hash})
	while not FileAccess.file_exists(folder.path_join("config.json")):
		if Time.get_ticks_msec()-started_at>5000:quit(2);return
		await process_frame
	config=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("config.json")))
	bridge=Bridge.new();root.add_child(bridge)
	bridge.received.connect(func(value):
		event_count+=1
		publish("event-%03d.json" % event_count,value))
	bridge.failed.connect(func(reason):
		publish("bridge-failure.json",{"reason":reason}))
	bridge.ended.connect(func(code):
		publish("node-ended.json",{"exit":code}))
	var error: String=bridge.launch(config)
	if not error.is_empty():publish("bridge-failure.json",{"reason":error,"release":bridge.release_owned_process()});quit(2);return
	while true:
		if Time.get_ticks_msec()-started_at>20000:quit(3);return
		var path:=folder.path_join("action-%03d.json" % action)
		if FileAccess.file_exists(path):
			var request: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(path))
			action+=1
			var op:=str(request.get("op",""))
			if op=="free":
				if is_instance_valid(bridge):bridge.queue_free()
				await process_frame;await process_frame
				publish("node-freed.json",{"freed":not is_instance_valid(bridge),"host_pid":OS.get_process_id()})
			elif op=="tree_exit":
				root.remove_child(bridge);publish("node-left-tree.json",{"inside":bridge.is_inside_tree(),"stopped":bridge.stopped,"release_calls":bridge.release_calls});bridge.free()
			elif op=="quit":quit(0);return
			elif op=="no_read":bridge.set_process(false);publish("node-no-read.json",{"disabled":true})
			elif op=="pause_node":bridge.set_process(false);publish("node-paused.json",{"disabled":true})
			elif op=="close_pipes":bridge.close_pipes();publish("pipes-closed.json",{"stopped":bridge.stopped})
			elif op=="release":publish("release-%03d.json" % (action-1),bridge.release_owned_process())
			elif op=="late_event":publish("late-event.json",{"admitted":bridge.admit("{}".to_ascii_buffer()),"release_calls":bridge.release_calls})
			else:
				var why: String=bridge.send(op,request.get("fields",{}))
				publish("send-%03d.json" % (action-1),{"error":why,"op":op,"control_bytes":bridge.last_send_bytes})
		await process_frame
