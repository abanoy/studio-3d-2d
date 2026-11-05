extends SceneTree
const D=preload("res://src/root_component_document.gd")
const Channels=preload("res://src/animated_channels.gd")
func _initialize() -> void:
	var checks:=0;var failures:=0
	var data: Dictionary=D.put_component(D.Model.definition("res://project.godot"),12,"position",[3.,0.,0.],"ease",48).data
	data=D.put_component(data,6,"rotation_xyzw",[0.,0.,0.,1.],"linear",48).data
	var model:=D.Model.new();model.data=data;checks+=1
	if not model.has_animation():failures+=1;print("FAIL component-only movement reports animation")
	var saved:=data.duplicate(true);var basic:=Channels.describe(data,false);var advanced:=Channels.describe(data,true)
	checks+=1
	if not Channels.has_data(data) or basic.size()!=1 or basic[0].id!="@root" or basic[0].frames!=[6,12]:failures+=1;print("FAIL simple root catalogue")
	var mapped:={}
	for row in advanced:mapped[row.id]=row
	checks+=1
	if mapped.size()!=2 or mapped.get("@root/position",{}).get("frames")!=[12] or mapped.get("@root/rotation_xyzw",{}).get("frames")!=[6]:failures+=1;print("FAIL independent advanced frames")
	advanced[0].frames.clear();checks+=1
	if data!=saved or Channels.describe(data,true)[0].frames.is_empty():failures+=1;print("FAIL catalogue isolation")
	var empty: Dictionary=D.remove_component(data,12,"position",48).data
	empty=D.remove_component(empty,6,"rotation_xyzw",48).data
	model.data=empty;checks+=1
	if model.has_animation() or Channels.has_data(empty):failures+=1;print("FAIL deleted component-only keys still report animation")
	var boned: Dictionary=D.put_bones(empty,20,{"hand":D.Model.identity()},"ease",48).data
	model.data=boned;checks+=1
	if not model.has_animation():failures+=1;print("FAIL deleting root keys hides retained bone animation")
	var legacy:=D.Model.definition("res://project.godot");var transform:=D.Model.identity();transform["scale"]=1.
	legacy.pose_keys=[{"frame":0,"pose":{},"transform":transform,"interpolation":"ease"}]
	var fallback: Dictionary=D.promote(legacy,48).data;fallback.root_components.clear();model.data=fallback;checks+=1
	if not D.validate(fallback,48).is_empty() or not model.has_animation() or Channels.describe(fallback,true).size()!=3:failures+=1;print("FAIL valid legacy fallback lacks root channels")
	print("ROOT_COMPONENT_CHANNELS "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
