extends RefCounted
static func create(path: String) -> Error:
	var base:=path+".original.glb";var error:=preload("res://src/tutorial_assets.gd").figure(base)
	if error!=OK:return error
	var doc:=GLTFDocument.new();var state:=GLTFState.new();error=doc.append_from_file(base,state)
	if error!=OK:return error
	var root:=doc.generate_scene(state);var skeletons:=root.find_children("*","Skeleton3D",true,false)
	if skeletons.size()!=1:root.free();return ERR_INVALID_DATA
	var rig: Skeleton3D=skeletons[0]
	var index:=0
	for name in ["forearm.L","hand.L","forearm.R","hand.R","shin.L","foot.L","shin.R","foot.R"]:
		var joint:=-1
		for i in range(rig.get_bone_count()):
			if preload("res://src/limb_ik.gd").normalized(rig.get_bone_name(i))==preload("res://src/limb_ik.gd").normalized(name):joint=i
		if joint<0:root.free();return ERR_INVALID_DATA
		var parent:=rig.get_bone_parent(joint);var local:=rig.get_bone_rest(joint)
		var helper:=rig.get_bone_count();rig.add_bone("AuthoredHelper"+str(index));rig.set_bone_parent(helper,parent)
		var transform:=Transform3D(Basis(Vector3.UP,.17 if index%2==0 else -.13),local.origin*.4)
		rig.set_bone_rest(helper,transform);rig.set_bone_parent(joint,helper);rig.set_bone_rest(joint,transform.affine_inverse()*local);index+=1
	rig.reset_bone_poses();doc=GLTFDocument.new();state=GLTFState.new();error=doc.append_from_scene(root,state)
	if error==OK:error=doc.write_to_filesystem(state,path)
	root.free();return error
