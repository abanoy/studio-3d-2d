extends SceneTree
const ImportBasis=preload("res://src/import_basis.gd")
const Helpers=preload("res://src/import_basis_helpers.gd")
const Model=preload("res://src/model.gd")
var checks:=0
var failures:=0

func check(value: bool,label: String) -> void:
	checks+=1
	print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1

func proof(parent: String,current: String) -> Dictionary:
	var payload:={"format":"studio_import_basis_preservation_payload_1","method":"exact_existing_joint_endpoints_1","parent_sha256":parent,"source_sha256":current,"geometry_root_rest_skin_morph_preserved":true,"exact_binary_preserved":true,"source_document_sha256":"c".repeat(64),"source_binary_sha256":"d".repeat(64),"original_nodes":5,"appended_unweighted_endpoints":1,"original_springs":0,"candidate_springs":1}
	var text:=JSON.stringify(payload,"",true,true)
	return {"format":"studio_import_basis_preservation_1","parent_sha256":parent,"source_sha256":current,"preservation_sha256":text.sha256_text(),"payload":text}

func _initialize() -> void:
	var first: String="a".repeat(64)
	var second: String="b".repeat(64)
	var third: String="e".repeat(64)
	var source: Dictionary={"sha256":first,"metadata":{"kept":"original"}}
	var destination: Dictionary={"sha256":first,"metadata":{"source_shape":{"enabled":false}}}
	check(Helpers.copy_reference(source,destination).model==destination,"legacy preview definition is unchanged")
	var made:=ImportBasis.create_record(first,"1.5")
	check(not made.has("error"),"complete-human reference fixture is valid")
	source["asset_basis"]=made.record
	var before:=source.duplicate(true)
	var inherited:=Helpers.copy_reference(source,destination)
	check(not inherited.has("error") and inherited.model.asset_basis==source.asset_basis and inherited.model.metadata==destination.metadata,"same-source preview retains reference and its own shape metadata")
	inherited.model.asset_basis.decision="automatic_qualified"
	check(source==before,"preview reference is a deep copy")
	check(Helpers.copy_reference(source,{"sha256":second,"metadata":{}}).has("error"),"foreign source cannot borrow a reference")
	check(Helpers.copy_reference({"sha256":first,"metadata":{"import_basis_lineage":{}}},destination).has("error"),"orphan lineage refuses before preview")
	check(Helpers.derivative(source,second,{}).has("error"),"derivative without actual preservation record refuses")
	var valid:=proof(first,second)
	var derived:=Helpers.derivative(source,second,valid)
	check(not derived.has("error") and derived.model.sha256==second and derived.model.asset_basis.source_sha256==second,"checked existing-joint derivative binds its current SHA")
	check(derived.model.asset_basis.measured_from_sha256==first and derived.model.asset_basis.factor==source.asset_basis.factor and derived.model.asset_basis.measured_converted_height=="1.5","derivative keeps original measurement and exact factor")
	check(derived.model.metadata.import_basis_lineage.steps.size()==1 and derived.model.metadata.import_basis_lineage.steps[0].preservation_sha256==valid.preservation_sha256 and source==before,"lineage adds one checked step without editing source")
	var tampered:=valid.duplicate(true);tampered.preservation_sha256="0".repeat(64)
	check(Helpers.derivative(source,second,tampered).has("error"),"changed proof payload hash refuses")
	tampered=valid.duplicate(true);tampered.parent_sha256=second
	check(Helpers.derivative(source,second,tampered).has("error"),"proof for another parent refuses")
	var payload: Dictionary=JSON.parse_string(valid.payload);payload.geometry_root_rest_skin_morph_preserved=false
	tampered=valid.duplicate(true);tampered.payload=JSON.stringify(payload);tampered.preservation_sha256=tampered.payload.sha256_text()
	check(Helpers.derivative(source,second,tampered).has("error"),"unpreserved geometry cannot obtain lineage even with matching hash")
	payload=JSON.parse_string(valid.payload);payload.original_nodes=true
	tampered=valid.duplicate(true);tampered.payload=JSON.stringify(payload);tampered.preservation_sha256=tampered.payload.sha256_text()
	check(Helpers.derivative(source,second,tampered).has("error"),"Boolean count is not an integer proof")
	var repeated:=Helpers.derivative(derived.model,third,proof(second,third))
	check(not repeated.has("error") and repeated.model.metadata.import_basis_lineage.steps.size()==2 and repeated.model.asset_basis.measured_from_sha256==first,"repeated existing-joint setup extends continuous lineage")
	check(Helpers.derivative(repeated.model,first,proof(third,first)).has("error"),"lineage cannot cycle to an old source")
	var actor:=Model.new();actor.root=Node3D.new();actor.data=source.duplicate(true)
	var raw:=Transform3D(Basis.IDENTITY.scaled(Vector3.ONE*2),Vector3(2,3,4))
	var error: String=actor.capture_import_root(raw)
	var factor: float=ImportBasis.factor(source)
	check(error.is_empty() and actor.raw_import_root==raw and actor.base_root.is_equal_approx(Transform3D(Basis.IDENTITY.scaled(Vector3.ONE*factor),Vector3.ZERO)*raw),"disposable helper import composes reference exactly once around original origin")
	check(not actor.capture_import_root(actor.base_root).is_empty(),"already-normalized root cannot be captured twice")
	actor.root.free()
	print("IMPORT_BASIS_HELPER_UNIT "+JSON.stringify({"checks":checks,"failures":failures}))
	quit(0 if failures==0 else 1)
