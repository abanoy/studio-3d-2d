extends SceneTree
const B=preload("res://src/import_basis.gd")
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_runtime.gd")
var checks:=0
var failures:=0
const A:="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
const Z:="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
const P:="cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"

func check(value: bool,label: String) -> void:
	checks+=1
	print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1

func definition(height: String="2") -> Dictionary:
	var value:={"format":"studio_model_1","id":"basis_fixture","name":"Synthetic basis fixture","kind":"model","parent_id":"","start_frame":0,"source":"res://synthetic-not-read.glb","sha256":A,"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.0,"visible":true,"reference_only":false,"pose":{},"pose_keys":[],"draft_frame":0,"metadata":{}}
	value["asset_basis"]=B.create_record(A,height).record
	return value

func actor(value: Dictionary,raw_root: Transform3D) -> RefCounted:
	var result:=Model.new();result.data=value;result.root=Node3D.new()
	result.root.transform=raw_root
	check(result.capture_import_root(raw_root).is_empty(),"constructor captures immutable raw root")
	result.inventory(result.root)
	return result

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	check(B.factor_for("2").factor_text=="0.9144" and B.factor_for("3").factor_text=="0.6096","exact deterministic six-foot ratios")
	check(B.factor_for("7").factor_text=="0.26125714285714285714285714285714285714285714285714","50-digit nearest-even ratio")
	for value in ["0","2.0","02","2e0","-2",2,true,null]:
		check(B.create_record(A,value).has("error"),"noncanonical height refuses: "+str(value))
	var legacy:={"metadata":{"import_height":{"factor":"9"}}}
	check(B.factor(legacy)==1.0 and not B.active(legacy),"old height diagnostics never become active basis")
	for value in [0,1,"true",null]:
		check(B.model_admission(definition(),value,true).has("error"),"real capability boolean required")
		check(B.model_admission(definition(),true,value).has("error"),"real runtime-ready boolean required")
	check(B.model_admission(definition(),true,false).has("error"),"closed runtime cannot activate basis")
	check(is_nan(B.factor({"asset_basis":{}})),"invalid factor is not silently replaced by identity")
	var raw:=Transform3D(Basis.from_euler(Vector3(0,PI*.5,0)).scaled(Vector3.ONE*2),Vector3(1,2,3))
	var subject:=actor(definition(),raw)
	var expected:=Transform3D(Basis.IDENTITY.scaled(Vector3.ONE*.9144),Vector3.ZERO)*raw
	check(subject.raw_import_root==raw and subject.base_root.is_equal_approx(expected),"base is C times raw B0, including imported origin")
	check(not subject.capture_import_root(Transform3D.IDENTITY).is_empty() and subject.raw_import_root==raw,"second constructor capture refuses double normalization")
	root.add_child(subject.root)
	for amount in [.5,1.,2.]:
		subject.data.scale=amount;subject.apply(0,false,true)
		check(subject.root.transform.is_equal_approx(Transform3D(Basis.IDENTITY.scaled(Vector3.ONE*amount),Vector3.ZERO)*expected),"artist multiplier remains outside immutable basis: "+str(amount))
		check(absf(subject.root.transform.basis.y.length()-1.8288*amount)<.00002,"identity-parent reference height is three/six/twelve feet")
	subject.data.scale=1.
	var parent:=Node3D.new();parent.scale=Vector3.ONE*.5;root.add_child(parent)
	root.remove_child(subject.root);parent.add_child(subject.root);subject.apply(0,false,true)
	check(absf(subject.root.global_basis.y.length()-.9144)<.00002,"intentional parent scale is not compensated away")
	parent.remove_child(subject.root);root.add_child(subject.root);parent.free()
	for unsupported in [Transform3D(Basis.IDENTITY.scaled(Vector3(-1,1,1)),Vector3.ZERO),Transform3D(Basis.IDENTITY.scaled(Vector3(1,2,1)),Vector3.ZERO),Transform3D(Basis(Vector3(1,0,0),Vector3(.1,1,0),Vector3(0,0,1)),Vector3.ZERO)]:
		check(B.configure_import_root(unsupported,definition()).has("error"),"active reflected/nonuniform/sheared root refuses")
		check(B.configure_import_root(unsupported,legacy).base_root==unsupported,"legacy raw root remains exact")
	var world:=World.new();world.root=Node3D.new();world.duration=48
	root.add_child(world.root);root.remove_child(subject.root);world.root.add_child(subject.root)
	world.data={"format":"studio_world_1","objects":[subject.data.duplicate(true)]};world.instances[subject.data.id]=subject;world.order.append(subject.data.id);subject.world_context=weakref(world)
	var valid_edit: Dictionary=subject.data.duplicate(true);valid_edit.scale=.5
	check(world.restore_instance(subject.data.id,valid_edit).is_empty(),"relative scale edit retains basis")
	var changed: Dictionary=subject.data.duplicate(true);changed.asset_basis=B.create_record(A,"1").record
	check(not world.restore_instance(subject.data.id,changed).is_empty(),"ordinary world edit cannot replace a valid intrinsic basis")
	check(subject.data.asset_basis.measured_converted_height=="2","refused basis edit leaves actor unchanged")
	world.dispose();subject=null
	var derived:=B.authenticated_derivative(definition(),Z,P,true)
	check(not derived.has("error") and derived.model.asset_basis.measured_from_sha256==A and derived.model.sha256==Z,"verified derivative retains original measurement")
	for flag in [false,0,1,"true",null]:
		check(B.authenticated_derivative(definition(),Z,P,flag).has("error"),"derivative requires actual verified boolean")
	check(B.authenticated_derivative(derived.model,A,P,true).has("error"),"derivative cycle to measured origin refuses")
	var derivative_actor:=actor(derived.model,Transform3D.IDENTITY)
	var derivative_world:=World.new();derivative_world.root=Node3D.new();root.add_child(derivative_world.root);derivative_world.root.add_child(derivative_actor.root);derivative_world.duration=48
	derivative_world.data={"format":"studio_world_1","objects":[derived.model.duplicate(true)]};derivative_world.instances[derived.model.id]=derivative_actor;derivative_world.order.append(derived.model.id)
	changed=derived.model.duplicate(true);changed.metadata.import_basis_lineage.steps[0].preservation_sha256=A
	check(B.record_error(changed).is_empty(),"opaque chain shape alone cannot authenticate preservation")
	check(not derivative_world.restore_instance(derived.model.id,changed).is_empty(),"ordinary edit cannot replace basis lineage")
	derivative_world.dispose();derivative_actor=null
	var fixtures: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://tests/import_basis_lineage_parity.json"))
	check(fixtures.format=="has_import_basis_lineage_parity_fixture_1" and fixtures.cases.size()==16,"complete authored lineage parity fixture")
	for row in fixtures.cases:
		var error:=B.record_error(row.model)
		check(error.is_empty()==row.accepted,"Python/GDScript lineage admission parity: "+str(row.name))
		if row.accepted:
			var admission:=B.model_admission(row.model,true,true)
			check(not admission.has("error") and admission.factor_text==row.factor_text,"exact factor text parity: "+str(row.name))
	var project:={"schema_version":4,"world":{"format":"studio_world_1","objects":[definition()]}}
	var encoded:=B.encode_capability(project)
	check(not encoded.has("error") and encoded.document.schema_version==9,"active scene gains explicit outer capability")
	var frozen: Dictionary=encoded.document.duplicate(true)
	var peeled:=B.legacy_validation_view(encoded.document)
	check(not peeled.has("error") and peeled.document.schema_version==4 and encoded.document==frozen,"legacy validation peels only transient clone")
	check(peeled.document.world.objects[0].asset_basis==project.world.objects[0].asset_basis,"transient view retains validated asset facts")
	var result:={"checks":checks,"failures":failures}
	print("IMPORT_BASIS_UNIT "+JSON.stringify(result))
	quit(0 if failures==0 else 1)
