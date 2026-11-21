extends SceneTree
# Authored engine controls using generated ArrayMesh/Material objects only.
# No artist/native assets, screenshots, import qualification or runtime IO.
const Schema = preload("res://src/model_variants.gd")
const Runtime = preload("res://src/model_variant_runtime.gd")
const Opacity = preload("res://src/model_opacity.gd")
const OldBoundary = preload("res://src/import_basis.gd")
const Boundary = preload("res://src/import_basis_project.gd")
const Extended = preload("res://src/extended_timing.gd")
var named: Dictionary = {}
class Actor extends RefCounted:
	var root: Node3D
	var data: Dictionary
	var variants: RefCounted
func check(ok: bool, name: String) -> void:
	if named.has(name): ok = false
	named[name] = ok
	print(("PASS " if ok else "FAIL ") + "variant." + name)
func manifest() -> Dictionary:
	return {"format":Schema.FORMAT,"asset_sha256":"a".repeat(64),"default_skin":0,
		"skins":[{"id":0,"name":"Original"},{"id":1,"name":"Green"},{"id":2,"name":"White"}],
		"groups":[{"id":0,"name":"Glove","default":0,"choices":[{"id":0,"name":"blank","blank":false,"nodes":[10]},{"id":1,"name":"","blank":true,"nodes":[]}]}],
		"surfaces":[{"node":10,"surface":0,"materials":[0,1,2]}]}
func inventory() -> Dictionary:
	return {"format":Schema.INVENTORY,"asset_sha256":"a".repeat(64),"material_count":3,"mesh_nodes":[{"node":10,"parent_mesh":null,"surface_materials":[0]}]}
func make_actor(shared_mesh: ArrayMesh = null, shared_materials: Array = [], saved: Dictionary = {}) -> Dictionary:
	var materials: Array = shared_materials
	if materials.is_empty():
		for color in [Color.RED,Color.GREEN,Color.WHITE]:
			var material: StandardMaterial3D = StandardMaterial3D.new(); material.albedo_color = color; materials.append(material)
	var mesh: ArrayMesh = shared_mesh
	if mesh == null:
		var box: BoxMesh = BoxMesh.new(); mesh = ArrayMesh.new(); mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,box.surface_get_arrays(0)); mesh.surface_set_material(0,materials[0])
	var actor: RefCounted = Actor.new(); actor.root = Node3D.new()
	var node: MeshInstance3D = MeshInstance3D.new(); node.mesh = mesh; node.set_meta(Runtime.NODE_META,10); actor.root.add_child(node)
	actor.data = saved.duplicate(true) if not saved.is_empty() else {"sha256":"a".repeat(64),"kind":"model","metadata":{"model_variants":manifest()}}
	var checked: Dictionary = Schema.canonical(actor.data.metadata.model_variants,inventory())
	actor.root.set_meta(Runtime.META,{"root":actor.root,"manifest":checked.manifest,"inventory":inventory(),"materials":materials.duplicate(),"nodes":{10:node}})
	var attached: Dictionary = Runtime.attach(actor)
	if attached.has("error"): return {"error":attached.error,"actor":actor,"node":node}
	actor.variants = attached.runtime
	return {"actor":actor,"node":node,"mesh":mesh,"materials":materials,"runtime":attached.runtime}
func selected(skin: int, choice: int) -> Dictionary:
	return {"format":Schema.SELECTION,"skin":skin,"groups":{"0":choice}}
func commit(fixture: Dictionary, chosen: Dictionary, opacity: RefCounted = null) -> String:
	var value: Dictionary = fixture.actor.data.duplicate(true); value[Schema.FIELD] = chosen
	var error: String = fixture.runtime.sync_record(value,opacity)
	if error.is_empty(): fixture.actor.data = value
	return error
func _initialize() -> void:
	var declared: Dictionary = manifest(); var actual: Dictionary = inventory()
	var canonical: Dictionary = Schema.canonical(declared,actual)
	check(not canonical.has("error"),"declaration")
	check(Schema.defaults(canonical.manifest) == selected(0,0),"default_selection")
	var hidden: Dictionary = Schema.plan(canonical.manifest,selected(2,1))
	check(hidden.visibility == [{"node":10,"visible":false}] and hidden.materials == [{"node":10,"surface":0,"material":2}],"skin_and_blank_full_plan")
	check(declared == manifest() and actual == inventory(),"pure_inputs_unchanged")
	var bad: Dictionary = declared.duplicate(true); bad.groups[0].choices[1] = {"id":1,"name":"duplicate","blank":false,"nodes":[10]}
	check(Schema.canonical(bad,actual).has("error"),"duplicate_ownership_refused")
	bad = declared.duplicate(true); bad.surfaces[0].materials[0] = 1
	check(Schema.canonical(bad,actual).has("error"),"default_material_refused")
	bad = actual.duplicate(true); bad.mesh_nodes[0].surface_materials.append(0)
	check(Schema.canonical(declared,bad).has("error"),"complete_surface_coverage")
	check(Schema.selection({"format":Schema.SELECTION,"skin":true,"groups":{"0":0}},canonical.manifest).has("error"),"bool_selection_refused")
	check(Schema.selection({"format":Schema.SELECTION,"skin":1.5,"groups":{"0":0}},canonical.manifest).has("error"),"fraction_selection_refused")
	check(Schema.selection({"format":Schema.SELECTION,"skin":1.0,"groups":{"0":0.0}},canonical.manifest).selection == selected(1,0),"json_integer_values")
	check(Schema.record_error({"sha256":"b".repeat(64),"metadata":{"model_variants":declared}}) != "","wrong_asset_refused")
	check(Schema.record_error({"metadata":{},"variant_selection":selected(0,0)}) != "","selection_without_manifest_refused")
	check(Schema.record_error({"metadata":{}}).is_empty(),"legacy_unchanged")
	var record: Dictionary = {"id":"m","sha256":"a".repeat(64),"kind":"model","metadata":{"model_variants":manifest()},"variant_selection":selected(2,1)}
	var project: Dictionary = {"schema_version":4,"world":{"format":"studio_world_1","objects":[record]}}
	var encoded: Dictionary = Schema.encode_project(project)
	check(not encoded.has("error") and encoded.document.schema_version == 10 and encoded.document.variant_content_schema_version == 4,"capability_promoted")
	check(OldBoundary.legacy_validation_view(encoded.document).has("error"),"actual_old_reader_rejects_new_document")
	var stripped: Dictionary = Schema.project_view(encoded.document)
	check(not stripped.has("error") and stripped.document.schema_version == 4 and not stripped.document.world.objects[0].metadata.has(Schema.META) and not stripped.document.world.objects[0].has(Schema.FIELD),"temporary_legacy_view_only")
	var resolved: Dictionary = stripped.document.duplicate(true); resolved.world.objects[0]["source"] = "owned-cache/asset.glb"
	var restored: Dictionary = Schema.restore_project(encoded.document,resolved)
	check(restored.schema_version == 10 and restored.world.objects[0].variant_selection == selected(2,1) and restored.world.objects[0].source == "owned-cache/asset.glb","capability_restore_preserves_resolved_paths")
	check(Schema.project_view(project).has("error"),"unversioned_variant_document_refused")
	var legacy: Dictionary = {"schema_version":4,"world":{"format":"studio_world_1","objects":[]}}
	check(Schema.encode_project(legacy).document == legacy,"legacy_document_not_promoted")
	var malformed: Dictionary = encoded.document.duplicate(true); malformed.variant_capability = "unknown"
	check(Schema.project_view(malformed).has("error"),"wrong_project_capability_refused")
	malformed = encoded.document.duplicate(true); malformed.world.objects.clear()
	check(Schema.project_view(malformed).has("error"),"redundant_project_capability_refused")
	var sequence: Dictionary = {"schema_version":6,"world":{"format":"studio_world_1","objects":[]},"sequence_graph":{"assets":[{"id":"child","scene":project}]}}
	var sequence_encoded: Dictionary = Schema.encode_project(sequence)
	check(not sequence_encoded.has("error") and sequence_encoded.document.schema_version == 10 and sequence_encoded.document.sequence_graph.assets[0].scene.schema_version == 10,"nested_scene_promoted")
	check(Extended.child_schema(sequence_encoded.document.sequence_graph.assets[0].scene) == 4,"sequence_runtime_child_schema")
	var nested_bad: Dictionary = sequence_encoded.document.duplicate(true); nested_bad.sequence_graph.assets[0].scene = project
	check(Schema.project_view(nested_bad).has("error"),"nested_unversioned_variant_refused")
	var basis_record: Dictionary = OldBoundary.create_record("a".repeat(64),"1.8288")
	var with_basis: Dictionary = project.duplicate(true); with_basis.world.objects[0]["asset_basis"] = basis_record.record
	var basis_encoded: Dictionary = OldBoundary.encode_capability(with_basis)
	var double_encoded: Dictionary = Schema.encode_project(basis_encoded.document)
	check(not double_encoded.has("error") and double_encoded.document.variant_content_schema_version == 9 and not Boundary.validation_view(double_encoded.document).has("error"),"six_foot_capability_composes")
	check(Boundary.decoded_content_schema(double_encoded.document) == 4,"content_schema_after_both_capabilities")
	var one: Dictionary = make_actor()
	check(not one.has("error"),"first_actor_bind")
	if one.has("error"): quit(1); return
	var two: Dictionary = make_actor(one.mesh,one.materials)
	check(not two.has("error"),"shared_resource_second_actor_bind")
	if two.has("error"): one.actor.root.free(); quit(1); return
	check(one.node.get_surface_override_material(0) == one.materials[0] and one.node.visible,"default_applied")
	var initial: Dictionary = one.actor.data.duplicate(true)
	check(commit(one,selected(2,1)).is_empty(),"transaction_apply")
	check(one.node.get_surface_override_material(0) == one.materials[2] and not one.node.visible,"transaction_exact_refs")
	check(two.node.get_surface_override_material(0) == two.materials[0] and two.node.visible,"other_actor_unchanged")
	check(one.mesh.surface_get_material(0) == one.materials[0] and one.materials[0].albedo_color == Color.RED,"shared_resources_unchanged")
	check(Runtime.hidden_for_bounds(one.node) and not Runtime.hidden_for_bounds(two.node),"hidden_part_bounds_only")
	var after: Dictionary = one.actor.data.duplicate(true)
	check(one.runtime.sync_record(initial).is_empty(),"undo_runtime")
	one.actor.data = initial
	check(one.node.visible and one.node.get_surface_override_material(0) == one.materials[0],"undo_exact")
	check(one.runtime.sync_record(after).is_empty(),"redo_runtime")
	one.actor.data = after
	check(not one.node.visible and one.node.get_surface_override_material(0) == one.materials[2],"redo_exact")
	var saved: Dictionary = JSON.parse_string(JSON.stringify(after,"",true,true))
	var cold: Dictionary = make_actor(one.mesh,one.materials,saved)
	check(not cold.has("error") and cold.runtime.current == selected(2,1),"document_cold_selection")
	check(not cold.node.visible and cold.node.get_surface_override_material(0) == one.materials[2],"document_cold_exact_refs")
	var opacity: RefCounted = Opacity.new(); opacity.inventory(two.actor.root); opacity.set_appearance(0.5,true)
	check(commit(two,selected(1,0),opacity).is_empty(),"fade_flat_composed")
	check(opacity.authored_material(two.node,0) == two.materials[1] and opacity.last_alpha == 0.5 and opacity.unshaded,"fade_flat_current_skin")
	var before: Dictionary = two.actor.data.duplicate(true)
	var old_copy: Material = two.node.get_surface_override_material(0)
	two.runtime.material_refs[2] = StandardMaterial3D.new()
	check(not commit(two,selected(2,0),opacity).is_empty(),"replaced_inactive_material_refused")
	check(two.actor.data == before and two.node.get_surface_override_material(0) == old_copy,"refusal_no_data_or_visual_mutation")
	two.runtime.material_refs[2] = two.materials[2]
	var old_parent: Node = two.node.get_parent()
	var new_parent: Node3D = Node3D.new(); old_parent.add_child(new_parent); two.node.reparent(new_parent,false)
	check(not commit(two,selected(2,0),opacity).is_empty() and two.actor.data == before,"reparented_part_refused_before_mutation")
	two.node.reparent(old_parent,false); new_parent.free()
	two.node.skin = Skin.new()
	check(not commit(two,selected(2,0),opacity).is_empty() and two.actor.data == before,"replaced_skin_refused_before_mutation")
	two.node.skin = null
	var old_owner: WeakRef = weakref(cold.actor)
	var cold_root: Node3D = cold.actor.root
	cold.actor = null
	check(old_owner.get_ref() == null and cold.runtime.actor.get_ref() == null,"runtime_does_not_retain_actor_cycle")
	check(not cold.runtime.check_record(saved).is_empty(),"released_actor_refused")
	one.actor.root.free(); two.actor.root.free(); cold_root.free()
	var failures: int = 0
	for value in named.values():
		if value != true: failures += 1
	print("MODEL_VARIANT_RUNTIME_UNIT ",JSON.stringify({"checks":named.size(),"expected_checks":48,"complete_assertion_set":named.size()==48,"failures":failures,"artist_or_native_assets_loaded":false,"actual_export_or_HAS_cold_qualified":false}))
	quit(0 if failures == 0 and named.size() == 48 else 1)
