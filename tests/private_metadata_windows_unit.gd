extends SceneTree
const Atomic=preload("res://src/atomic_metadata.gd")
const Recovery=preload("res://src/recovery.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	if OS.get_name()!="Windows":print("PRIVATE_METADATA_WINDOWS "+JSON.stringify({"checks":0,"failures":0,"unrun":"Windows filesystem required"}));quit();return
	var folder: String=OS.get_cmdline_user_args()[0].replace("\\","/").simplify_path()
	var base:=folder.path_join("owned metadata — тест");DirAccess.make_dir_recursive_absolute(base)
	var back:=base.replace("/","\\")
	var variants:=[[base,base.path_join("forward.json")],[back,back+"\\back.json"],[base,back+"\\mixed-target.json"],[back,base.path_join("mixed-root.json")],[back+"\\",base.path_join("trailing-root.json")]]
	for i in range(variants.size()):
		var error:=Atomic.write_bytes(variants[i][1],JSON.stringify({"saved":i}).to_utf8_buffer(),variants[i][0])
		check(error.is_empty() and Recovery.read_json(variants[i][1]).get("saved")==i,"Windows separator variant commits exact metadata: "+str(i))
	var original:=folder.path_join("sentinel.json");var expected:=FileAccess.get_sha256(original)
	for target in [original,back+"\\..\\sentinel.json",base+"/../sentinel.json"]:
		check(not Atomic.write_bytes(target,"{}".to_utf8_buffer(),back).is_empty() and FileAccess.get_sha256(original)==expected,"outside/traversal target refuses without touching sentinel")
	check(not Atomic.path_error("Z:/outside.json",back).is_empty(),"other drive is outside the declared owner")
	check(not Atomic.write_bytes(base.path_join("wrong-owner.json"),PackedByteArray(),back+"\\missing-owner").is_empty(),"target outside a nested declared owner refuses")
	var oversized:=PackedByteArray();oversized.resize(Atomic.MAX_BYTES+1)
	var oversized_path:=base.path_join("oversized.json")
	check(not Atomic.write_bytes(oversized_path,oversized,back).is_empty() and not FileAccess.file_exists(oversized_path),"metadata size bound refuses before creating a file")
	var hard:=base.path_join("hard-primary.json")
	check(Atomic.write_bytes(hard,"{\"saved\":12}".to_utf8_buffer(),back).is_empty() and Recovery.read_json(hard).get("saved")==12 and FileAccess.get_sha256(original)==expected,"fresh atomic primary replacement preserves the hard-linked sentinel")
	var redirected:=base.path_join("redirect/progress.json")
	var outside:=folder.path_join("outside-managed/progress.json");var outside_hash:=FileAccess.get_sha256(outside)
	check(not Atomic.write_bytes(redirected.replace("/","\\"),"{}".to_utf8_buffer(),back).is_empty() and FileAccess.get_sha256(outside)==outside_hash,"managed Windows junction refuses without changing the outside sentinel")
	var skipped:=[]
	for target in [base.path_join("primary-link.json"),base.path_join("temporary-link.json")]:
		var link_path: String=target if target.ends_with("primary-link.json") else target+".tmp"
		if FileAccess.file_exists(link_path):
			check(not Atomic.write_bytes(target,"{}".to_utf8_buffer(),back).is_empty() and FileAccess.get_sha256(original)==expected,"linked metadata target/temporary refuses and preserves sentinel")
		else:skipped.append(link_path.get_file())
	var result:={"checks":checks,"failures":failures,"unavailable_link_fixtures":skipped}
	FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result))
	print("PRIVATE_METADATA_WINDOWS "+JSON.stringify(result));quit(1 if failures else 0)
