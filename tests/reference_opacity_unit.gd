extends SceneTree
const Model=preload("res://src/model.gd")
const SceneIO=preload("res://src/scene3d.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var source:="res://examples/tutorials/Practice figure.glb";var sha:=FileAccess.get_sha256(source);var loaded:=SceneIO.load_glb(source);var node: Node3D=loaded.scene;root.add_child(node)
	var actor:=Model.new();actor.root=node;actor.base_root=node.transform;actor.data=Model.definition(source);actor.inventory(node);var original:=actor.data.duplicate(true)
	actor.apply(0);check(actor.evaluated_opacity==1 and not actor.data.has("reference_opacity"),"old projects retain full working opacity without adding a field")
	actor.data.reference_only=true;actor.data["reference_opacity"]=.25;actor.apply(0,false,false)
	check(actor.evaluated_opacity==.25 and actor.root.visible,"reference working preview uses independent opacity")
	actor.apply(0,false,true);check(actor.evaluated_opacity==1 and not actor.root.visible,"final render excludes reference independently of working opacity")
	actor.data.reference_only=false;actor.apply(0);check(actor.evaluated_opacity==1 and actor.root.visible,"ordinary output model ignores retained reference-only opacity")
	actor.data.reference_only=true;actor.data.reference_opacity=0.;actor.apply(0);check(actor.evaluated_opacity==0 and not actor.root.visible,"zero reference opacity hides only working reference geometry")
	actor.data.reference_opacity=.5;actor.apply(0,false,false,{},.4);check(is_equal_approx(actor.evaluated_opacity,.2),"reference opacity composes with inherited scene fades")
	for bad in [-.1,1.1,NAN,INF,true,".5",null]:
		var value:=original.duplicate(true);value["reference_opacity"]=bad;check(not Model.validate(value,48).is_empty(),"invalid optional opacity refuses: "+str(bad))
	var component: Dictionary=preload("res://src/movement_path.gd").change(original,0,Vector3.ZERO,48).data;component["reference_opacity"]=NAN;check(not Model.validate(component,48).is_empty(),"component-model validation keeps the same opacity guard")
	check(FileAccess.get_sha256(source)==sha,"working opacity never rewrites original model bytes")
	node.free();print("REFERENCE_OPACITY_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
