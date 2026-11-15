extends SceneTree

class Observer extends Node:
	var seen:=0
	func _input(_event: InputEvent) -> void:seen+=1

func _initialize() -> void:call_deferred("run")

func run() -> void:
	var app:=Observer.new();root.add_child(app)
	var popup:=Window.new();app.add_child(popup)
	var popup_child:=Observer.new();popup.add_child(popup_child)
	await process_frame
	var key:=InputEventKey.new();key.keycode=KEY_ESCAPE;key.pressed=true
	popup.push_input(key)
	print("WINDOW_INPUT_PROBE ",JSON.stringify({"app_seen":app.seen,"popup_child_seen":popup_child.seen,"app_viewport":app.get_viewport().get_instance_id(),"popup_viewport":popup.get_instance_id()}))
	app.free();quit(0)
