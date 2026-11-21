extends SceneTree
# SOURCE ONLY UNPARSED/UNRUN. Inert request/intent fixtures; real import lives in smoke.
const Actions = preload("res://src/import_actions.gd")
const Physics = preload("res://src/physics_editor.gd")
const Secondary = preload("res://src/secondary_live.gd")
var checks := 0
var failures := 0

class FixtureCamera extends RefCounted:
	var global_transform := Transform3D(Basis(Vector3.UP,0.31),Vector3(4.0,5.0,6.0))
	var fov := 63.0
	var near := 0.02
	var far := 700.0
class FixtureViewport extends RefCounted:
	var size := Vector2i(1600,900)
class FixtureActor extends RefCounted:
	var root := Node3D.new()
	var order: Array = ["root","arm","hand"]
	var data: Dictionary = {}
class FixtureWorld extends RefCounted:
	var actors: Dictionary = {}
	func instance(id: String) -> RefCounted: return actors.get(id)
class FixtureRenderer extends RefCounted:
	var camera := FixtureCamera.new()
	var viewport := FixtureViewport.new()
	var world_runtime: RefCounted = FixtureWorld.new()
class FixtureApp extends RefCounted:
	var renderer := FixtureRenderer.new()
	var frame := 12

func _initialize() -> void: call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks += 1
	if not ok: failures += 1
	print(("PASS " if ok else "FAIL ")+"import_defaults_off."+label)

func run() -> void:
	var app := FixtureApp.new()
	var actions := Actions.new(); actions.app = app
	var physics := Physics.new(); physics.app = app
	var initial: Dictionary = actions.placement()
	check(initial.has("physics_on_import") and typeof(initial.physics_on_import) == TYPE_BOOL and not initial.physics_on_import,"new_request_explicitly_defaults_body_off")
	check(not initial.get("hair_on_import",false),"new_request_does_not_add_automatic_hair_intent")
	check(initial.camera == app.renderer.camera.global_transform and initial.fov == 63.0 and initial.near == 0.02 and initial.far == 700.0 and initial.aspect == float(1600)/900,"placement_camera_values_preserved")
	check(not initial.review_height,"ordinary_height_policy_preserved")
	actions.offer_height = true
	var reviewed: Dictionary = actions.placement()
	check(reviewed.review_height and not reviewed.physics_on_import,"height_review_also_preserves_off_default")
	initial.physics_on_import = true
	check(not actions.placement().physics_on_import,"caller_request_mutation_cannot_change_later_default")
	for id in ["body","hair","combined","new"]:
		var actor := FixtureActor.new(); actor.data = {"id":id,"kind":"model","metadata":{"native_parameters":{"retained":"unchanged"}},"pose_keys":[]}
		app.renderer.world_runtime.actors[id] = actor
	var authored_before: PackedByteArray = var_to_bytes(app.renderer.world_runtime.instance("new").data)
	physics.simulations["body"] = RefCounted.new()
	var hair: RefCounted = Secondary.new(); hair.primary = null
	var combined: RefCounted = Secondary.new(); combined.primary = RefCounted.new()
	physics.simulations["hair"] = hair; physics.simulations["combined"] = combined
	var intent: Dictionary = physics.import_intents()
	check(intent.body.body and not intent.body.hair and not intent.body.ragdoll_only,"explicit_body_peer_intent_captured")
	check(not intent.hair.body and intent.hair.hair,"explicit_hair_peer_intent_captured")
	check(intent.combined.body and intent.combined.hair,"explicit_combined_peer_intent_captured")
	var retained: PackedByteArray = var_to_bytes(intent)
	physics.simulations.clear(); physics.restore_import_intents(intent)
	check(physics.import_starts.size() == 3 and not physics.import_starts.has("new"),"restoration_only_queues_existing_explicit_peers")
	check(physics.import_starts.body.body and not physics.import_starts.body.hair,"body_peer_restoration_is_not_reset_by_new_default")
	check(not physics.import_starts.hair.body and physics.import_starts.hair.hair,"hair_peer_restoration_is_not_reset_by_new_default")
	check(physics.import_starts.combined.body and physics.import_starts.combined.hair,"combined_peer_restoration_is_not_reset_by_new_default")
	check(var_to_bytes(intent) == retained and var_to_bytes(app.renderer.world_runtime.instance("new").data) == authored_before,"defaults_do_not_rewrite_intent_or_retained_native_setup")
	var pending: Dictionary = physics.import_intents()
	check(pending == intent,"queued_restoration_retains_exact_existing_intent")
	physics.import_starts.clear(); physics.restore_import_intents({})
	check(physics.import_starts.is_empty() and physics.simulations.is_empty(),"no_implicit_intent_created_for_an_empty_project")
	for actor in app.renderer.world_runtime.actors.values(): actor.root.free()
	physics.free(); actions.free()
	print("Import OFF default controls: "+str(checks)+"; failures: "+str(failures))
	quit(0 if failures == 0 else 1)
