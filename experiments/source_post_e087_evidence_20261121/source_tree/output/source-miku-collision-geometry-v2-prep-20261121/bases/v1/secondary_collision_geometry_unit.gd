extends SceneTree
const G=preload("res://src/secondary_collision_geometry.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1
	if not value: failures+=1
	print(("PASS " if value else "FAIL ")+"collision_geometry."+label)
func _initialize() -> void:
	create_timer(10).timeout.connect(func():push_error("Collision geometry watchdog");quit(2))
	call_deferred("run")
func run() -> void:
	check(is_equal_approx(G.segment_segment(Vector3(-1,0,0),Vector3(1,0,0),Vector3(0,-1,0),Vector3(0,1,0)),0.),"interior_crossing_not_visible_from_endpoints")
	check(is_equal_approx(G.segment_segment(Vector3.ZERO,Vector3.RIGHT,Vector3(0,2,0),Vector3(1,2,0)),2.),"parallel_separated_segments")
	check(is_equal_approx(G.segment_segment(Vector3.ZERO,Vector3.RIGHT,Vector3(2,0,0),Vector3(4,0,0)),1.),"collinear_disjoint_caps")
	check(is_equal_approx(G.segment_segment(Vector3.ZERO,Vector3(3,0,0),Vector3.RIGHT,Vector3(4,0,0)),0.),"collinear_overlap")
	check(is_equal_approx(G.segment_segment(Vector3.ZERO,Vector3.ZERO,Vector3(0,0,2),Vector3(0,0,2)),2.),"both_segments_degenerate")
	check(is_equal_approx(G.segment_segment(Vector3(0,2,0),Vector3(0,2,0),Vector3.ZERO,Vector3.RIGHT),2.),"first_point_second_segment")
	check(is_equal_approx(G.segment_segment(Vector3.ZERO,Vector3.RIGHT,Vector3(0.5,2,0),Vector3(0.5,2,0)),2.),"second_point_first_segment")
	var frames: Array=[Transform3D(Basis.IDENTITY,Vector3.RIGHT),Transform3D(Basis.IDENTITY,Vector3(0,2,0))]
	var row:=G.skin_vertex(Vector3(1,2,3),[0,1,0,0],[0.25,0.75,0.,0.],frames)
	check(not row.has("error") and row.point.distance_to(Vector3(1.25,3.5,3))<0.000001 and not row.normalization_applied,"independent_two_joint_world_lbs")
	var barely:=G.skin_vertex(Vector3.RIGHT,[0,0,0,0],[0.99999,0.,0.,0.],[Transform3D.IDENTITY])
	check(not barely.has("error") and is_equal_approx(barely.point.x,0.99999),"accepted_weight_roundoff_is_not_normalized")
	for kind in ["fractional_index","foreign_index","negative_weight","bad_total","nan_weight","bad_matrix"]:
		var indices: Array=[0,1,0,0]; var weights: Array=[0.25,0.75,0.,0.]; var changed: Array=frames.duplicate()
		match kind:
			"fractional_index": indices[0]=0.0
			"foreign_index": indices[0]=2
			"negative_weight": weights[0]=-0.25
			"bad_total": weights[0]=0.1
			"nan_weight": weights[0]=NAN
			"bad_matrix": changed[0]=Vector3.ZERO
		check(G.skin_vertex(Vector3.ZERO,indices,weights,changed).has("error"),"skin_refusal_"+kind)
	var capsule: Dictionary={"start":Vector3(0,-1,0),"finish":Vector3(0,1,0),"radius":0.1}
	var pivots: Array=[Vector3(-1,0,0),Vector3(1,0,0)]; var radii: Array=[0.01,0.01]
	var vertices: Array=[Vector3(0,0,0),Vector3(2,0,0)]
	var original:=var_to_bytes([pivots,radii,vertices,capsule])
	var report:=G.measure(pivots,radii,vertices,[capsule])
	check(not report.has("error") and report.penetrating_particles==0 and report.penetrating_segments==1 and report.penetrating_skin_vertices==1,"tip_pass_does_not_hide_segment_and_skin_crossing")
	check(is_equal_approx(report.minimum_segment_clearance,-0.11) and is_equal_approx(report.minimum_skin_vertex_clearance,-0.1),"independent_signed_clearance_values")
	check(original==var_to_bytes([pivots,radii,vertices,capsule]),"measurement_inputs_immutable")
	check(not report.body_triangle_contact_qualified and not report.swept_contact_qualified and not report.skin_shader_binding_qualified and not report.application_adopted,"no_body_mesh_sweep_or_binding_overclaim")
	var single:=G.measure([Vector3(2,0,0)],[0.01],[Vector3(2,0,0)],[capsule])
	check(single.minimum_segment_clearance==null and single.segments==0,"single_point_no_fake_segment_measurement")
	for kind in ["empty_vertices","wrong_radius_count","third_collider","nonfinite_pivot","huge_vertex","unknown_capsule_field"]:
		var ps: Array=pivots.duplicate(); var rs: Array=radii.duplicate(); var vs: Array=vertices.duplicate(); var cs: Array=[capsule.duplicate()]
		match kind:
			"empty_vertices": vs.clear()
			"wrong_radius_count": rs.pop_back()
			"third_collider": cs.append(capsule.duplicate());cs.append(capsule.duplicate())
			"nonfinite_pivot": ps[0]=Vector3(INF,0,0)
			"huge_vertex": vs[0]=Vector3(100001,0,0)
			"unknown_capsule_field": cs[0]["name"]="unadmitted"
		check(G.measure(ps,rs,vs,cs).has("error"),"geometry_refusal_"+kind)
	print("COLLISION_GEOMETRY_UNIT ",JSON.stringify({"checks":checks,"failures":failures,"native_asset_tested":false,"engine_contact_tested":false,"application_adopted":false}))
	quit(0 if failures==0 else 1)
