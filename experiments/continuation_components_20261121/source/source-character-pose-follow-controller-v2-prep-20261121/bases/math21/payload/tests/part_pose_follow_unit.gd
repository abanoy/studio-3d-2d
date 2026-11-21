extends SceneTree
const Follow=preload("res://src/part_pose_follow_math.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func same(a: Transform3D,b: Transform3D) -> bool:
	return a.origin.distance_to(b.origin)<0.00001 and a.basis.x.distance_to(b.basis.x)<0.00001 and a.basis.y.distance_to(b.basis.y)<0.00001 and a.basis.z.distance_to(b.basis.z)<0.00001
func _initialize() -> void:
	check(DisplayServer.get_name()=="headless","synthetic proposal is a headless math test")
	var rest:=Transform3D(Basis(Vector3.UP,.3),Vector3(1,2,3))
	var authored:=Transform3D(Basis(Vector3.RIGHT,.4),Vector3(4,5,6))
	var retained: Dictionary=Follow.goal(rest,rest,authored)
	check(not retained.has("error") and same(retained.world_goal,authored),"master rest preserves different target rest and authored refinement")
	check(same(rest,Transform3D(Basis(Vector3.UP,.3),Vector3(1,2,3))) and same(authored,Transform3D(Basis(Vector3.RIGHT,.4),Vector3(4,5,6))),"follow calculation does not mutate either input frame")
	var shifted: Dictionary=Follow.goal(Transform3D.IDENTITY,Transform3D(Basis.IDENTITY,Vector3(2,-1,3)),Transform3D(Basis.IDENTITY,Vector3(4,5,6)))
	check(not shifted.has("error") and shifted.world_goal.origin.distance_to(Vector3(6,4,9))<.00001,"master translation follows without recentering the part")
	var quarter:=Basis(Vector3.BACK,PI/2.)
	var pivot_rest:=Transform3D(Basis.IDENTITY,Vector3.RIGHT)
	var pivot_posed:=Transform3D(quarter,Vector3.RIGHT)
	var offset:=Transform3D(Basis(Vector3.UP,.35),Vector3(4,0,0))
	var turn: Dictionary=Follow.goal(pivot_rest,pivot_posed,offset)
	check(not turn.has("error") and turn.world_goal.origin.distance_to(Vector3(1,3,0))<.00001,"rotation follows the source joint pivot rather than the world origin")
	check(turn.world_goal.basis.x.distance_to(Vector3(0,cos(.35),-sin(.35)))<.00001,"target authored rotation survives the master turn")
	check(turn.world_goal.basis.y.distance_to(Vector3.LEFT)<.00001,"follow retains the independently expected perpendicular orientation")
	var repeated: Dictionary=Follow.goal(pivot_rest,pivot_posed,offset)
	check(same(turn.world_goal,repeated.world_goal),"repeated evaluation from authored input does not accumulate a previous goal")
	var parent_authored:=Transform3D(Basis.IDENTITY,Vector3(3,0,0))
	var child_local:=Transform3D(Basis(Vector3.RIGHT,.2),Vector3(0,2,0))
	var child_authored: Transform3D=parent_authored*child_local
	var parent_goal: Dictionary=Follow.goal(Transform3D.IDENTITY,Transform3D(quarter,Vector3.ZERO),parent_authored)
	var child_goal: Dictionary=Follow.goal(Transform3D.IDENTITY,Transform3D(quarter,Vector3.ZERO),child_authored)
	check(parent_goal.world_goal.origin.distance_to(Vector3(0,3,0))<.00001 and child_goal.world_goal.origin.distance_to(Vector3(-2,3,0))<.00001,"all linked world goals use the same pre-follow authored snapshot")
	var solved: Dictionary=Follow.local_goal(parent_goal.world_goal,child_goal.world_goal)
	check(not solved.has("error") and same(solved.local_goal,child_local),"solved parent avoids applying the same master delta twice")
	check(same(parent_goal.world_goal*solved.local_goal,child_goal.world_goal),"solved local transform recomposes to the intended child world goal")
	var loose_local:=Transform3D(Basis(Vector3.UP,.15),Vector3(0,-1,0))
	var loose_world: Transform3D=parent_goal.world_goal*loose_local
	check(loose_world.origin.distance_to(Vector3(1,3,0))<.00001,"an unlinked loose descendant inherits the moved anchor position")
	check(same(Follow.local_goal(parent_goal.world_goal,loose_world).local_goal,loose_local),"loose descendant authored local motion remains separate")
	var bundle:=Transform3D(Basis(Vector3.UP,.6).scaled(Vector3.ONE*2.),Vector3(-3,1,7))
	var converted: Dictionary=Follow.goal(bundle*pivot_rest,bundle*pivot_posed,bundle*offset)
	check(not converted.has("error") and same(converted.world_goal,bundle*turn.world_goal),"one common bundle root rotation and scale commutes with following")
	var reverted: Dictionary=Follow.goal(pivot_rest,pivot_rest,offset)
	check(same(reverted.world_goal,offset),"returning the master to rest restores the original part refinement")
	var bad:=Transform3D(Basis(Vector3.ZERO,Vector3.UP,Vector3.BACK),Vector3.ZERO)
	check(Follow.goal(bad,Transform3D.IDENTITY,authored).has("error"),"singular master rest refuses before inversion")
	check(Follow.goal(rest,bad,authored).has("error"),"singular posed frame is outside this proposal")
	check(Follow.goal(rest,rest,bad).has("error"),"singular target frame is outside this proposal")
	check(Follow.local_goal(bad,authored).has("error"),"singular solved parent refuses before local inversion")
	var invalid:=Transform3D(Basis.IDENTITY,Vector3(NAN,0,0))
	check(Follow.goal(rest,rest,invalid).has("error"),"nonfinite authored frame refuses")
	check(Follow.local_goal(Transform3D.IDENTITY,invalid).has("error"),"nonfinite desired frame refuses")
	if checks!=21:push_error("Expected21 synthetic follow controls");quit(2);return
	print("PART_POSE_FOLLOW_MATH "+JSON.stringify({"checks":checks,"failures":failures,"synthetic_only":true,"actual_native_alignment_qualified":false,"actual_pose_following_qualified":false,"application_adopted":false}))
	quit(1 if failures else 0)
