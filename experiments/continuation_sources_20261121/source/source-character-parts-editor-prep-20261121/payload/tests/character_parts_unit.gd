extends SceneTree
const Parts=preload("res://src/character_parts.gd")
const F=preload("res://tests/character_parts_fixture.gd")
const World=preload("res://src/world_document.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1
	print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var original: Dictionary=World.empty();original["unknown_user_field"]={"keep":7}
	var group: Dictionary=F.row("junko","group")
	var incoming: Dictionary=F.inputs();incoming.hair.row.pose={"arm":{"position":[0,0,0],"rotation_xyzw":[0,0,0,1]}}
	var before: Dictionary=incoming.duplicate(true);var group_before: Dictionary=group.duplicate(true)
	var plan: Dictionary=Parts.assemble(original,group,incoming,F.policy(),48,2.)
	check(not plan.has("error"),"six reviewed families create a valid static assembly")
	if plan.has("error"):quit(1);return
	var world: Dictionary=plan.world;var ids: Dictionary=Parts.indexed(world)
	check(world.objects.size()==7 and World.validate(world,48).is_empty(),"real World model/group contract admits seven entries")
	check(incoming==before and group==group_before and original.objects.is_empty(),"assembly leaves every input untouched")
	check(world.unknown_user_field==original.unknown_user_field,"unrelated document data survives")
	check(ids.junko.scale==2. and ids.junko.position==[0,0,0],"one explicit factor belongs to root only")
	check(ids.junko.metadata.character_parts.unit_policy==F.policy(),"converted source units are recorded without applying them twice")
	check(not ids.junko.has("asset_basis") and not ids.hair.has("asset_basis"),"static grouping forges no human import-basis capability")
	for role in Parts.ROLES:
		check(ids[role].parent_id=="junko" and ids[role].scale==1 and ids[role].position==[0,0,0],"shared origin and unit local scale retained: "+role)
		check(ids[role].metadata==incoming[role].row.metadata and ids[role].pose==incoming[role].row.pose,"native/morph/solver ownership data retained: "+role)
		check(ids[role].visible==(role in ["body","hair"]),"conservative initial visibility: "+role)
	check(Parts.describe(world,"hair",48).root_id=="junko" and Parts.describe(world,"junko",48).parts.size()==6,"root/member selection resolves one explicit parts list")
	var body_scale: Dictionary=Parts.suggest_body_scale(1.6)
	check(body_scale.root_scale_suggestion==1.8288/1.6 and not body_scale.applied and not body_scale.classification_qualified,"six-foot suggestion measures body once without claiming standardization")
	check(Parts.suggest_body_scale(0).has("error") and Parts.suggest_body_scale(true).has("error") and Parts.suggest_body_scale(INF).has("error"),"invalid body measurements refuse")
	var missing: Dictionary=F.inputs();missing.erase("mask")
	check(Parts.assemble(World.empty(),group,missing,F.policy(),48).has("error"),"missing sixth family refuses atomically")
	var extra: Dictionary=F.inputs();extra["junko.vvd"]={}
	check(Parts.assemble(World.empty(),group,extra,F.policy(),48).has("error"),"dependencies cannot become extra actors")
	var bad: Dictionary=F.inputs();bad.hair.source_mdl_sha256=Parts.MDL.body
	check(Parts.assemble(World.empty(),group,bad,F.policy(),48).has("error"),"wrong reviewed native family refuses")
	bad=F.inputs();bad.hair.unit_policy.metres_per_source_unit=0.01
	check(Parts.assemble(World.empty(),group,bad,F.policy(),48).has("error"),"mixed unit conversion refuses instead of guessing")
	for field in ["position","scale","parent_id","asset_basis"]:
		bad=F.inputs()
		match field:
			"position":bad.hair.row.position=[1,0,0]
			"scale":bad.hair.row.scale=2.
			"parent_id":bad.hair.row.parent_id="elsewhere"
			"asset_basis":bad.hair.row.asset_basis={}
		check(Parts.assemble(World.empty(),group,bad,F.policy(),48).has("error"),"independent recenter/scale/basis/attachment refuses: "+field)
	bad=F.inputs();bad.hair.row.id="body"
	check(Parts.assemble(World.empty(),group,bad,F.policy(),48).has("error"),"duplicate actor identities refuse")
	check(Parts.assemble(World.empty(),group,F.inputs(),F.policy(),48,true).has("error"),"boolean root scale refuses")
	var occupied: Dictionary=World.empty();occupied.objects=[group.duplicate(true)]
	check(Parts.assemble(occupied,group,F.inputs(),F.policy(),48).has("error"),"existing root ID collision leaves installed world unchanged")
	var full_world: Dictionary=World.empty()
	for i in range(58):full_world.objects.append(F.row("existing-%d" % i))
	check(Parts.assemble(full_world,group,F.inputs(),F.policy(),48).has("error") and full_world.objects.size()==58,"capacity refusal preserves the complete existing world")
	var stale: Dictionary=world.duplicate(true);stale.objects[2].sha256="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
	check(Parts.describe(stale,"junko",48).has("error"),"changed asset identity invalidates parts binding")
	stale=world.duplicate(true);stale.objects[2].parent_id=""
	check(Parts.describe(stale,"junko",48).has("error"),"detached member is not silently recaptured")
	stale=world.duplicate(true);stale.objects[0].metadata.character_parts="bad"
	check(Parts.describe(stale,"junko",48).has("error"),"malformed metadata refuses without a typed assignment error")
	stale=world.duplicate(true);var unlisted: Dictionary=F.row("unlisted");unlisted.parent_id="junko";stale.objects.append(unlisted)
	check(Parts.describe(stale,"junko",48).has("error"),"unlisted direct attachments require a membership review")
	var world_before: Dictionary=world.duplicate(true)
	var edit: Dictionary=Parts.visibility_edit(world,"hair",{"hair":false,"mask":true},12,48)
	check(not edit.has("error") and edit.type=="world_objects" and edit.before.size()==2 and edit.after.size()==2,"multi-part toggle is one ordinary history transaction")
	check(world==world_before and world.objects[2].visible,"visibility proposal does not mutate world")
	check(Parts.Visibility.target(edit.after.hair,11) and not Parts.Visibility.target(edit.after.hair,12) and Parts.Visibility.target(edit.after.mask,12),"exact frame boundary changes only requested parts")
	check(edit.after.hair.pose==ids.hair.pose and edit.after.hair.metadata==ids.hair.metadata and edit.after.hair.parent_id=="junko" and edit.after.hair.sha256==ids.hair.sha256,"part visibility preserves pose/native metadata/parent/source")
	var outfit: Dictionary=Parts.outfit_edit(world,"junko",["dress","skirt"],24,48)
	check(not outfit.has("error") and outfit.after.size()==2 and outfit.after.has("dress") and outfit.after.has("skirt"),"explicit layered outfit is one transaction without stacking defaults")
	check(not outfit.after.has("body") and not outfit.after.has("hair") and not outfit.after.has("mask"),"outfit preset cannot overwrite body/hair/mask state")
	check(Parts.outfit_edit(world,"junko",["dress","dress"],0,48).has("error") and Parts.outfit_edit(world,"junko",["hair"],0,48).has("error"),"unknown/duplicate outfit choices refuse")
	check(Parts.visibility_edit(world,"junko",{"hair":true},0,48).after.is_empty(),"unchanged visibility produces no history entry")
	check(Parts.visibility_edit(world,"junko",{"foreign":false},0,48).has("error") and Parts.visibility_edit(world,"junko",{"hair":1},0,48).has("error"),"foreign ID and nonboolean visibility refuse")
	for frame in [-1,49,12.5,true]:check(Parts.visibility_edit(world,"junko",{"hair":false},frame,48).has("error"),"invalid frame refuses: "+str(frame))
	var wire: Dictionary=JSON.parse_string(JSON.stringify(world,"",true,true))
	check(not Parts.describe(wire,"mask",48).has("error"),"ordinary full-precision JSON wire retains static bundle membership")
	print("CHARACTER_PARTS_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(1 if failures else 0)
