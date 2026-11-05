extends SceneTree
const P=preload("res://src/expression_presets.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	var rows: Array=[{"node":0,"names":["eye","mouth","brow"]},{"node":1,"names":["eye","mouth","brow"]}]
	var happy: Dictionary={"morphTargetBinds":[{"node":0,"index":0,"weight":.5},{"node":1,"index":1,"weight":.75}],"overrideBlink":"blend"}
	var blink: Dictionary={"morphTargetBinds":[{"node":0,"index":2,"weight":1}]}
	var doc: Dictionary={"nodes":[{"mesh":0},{"mesh":0}],"meshes":[{}],"extensions":{"VRMC_vrm":{"specVersion":"1.0","expressions":{"preset":{"happy":happy,"blink":blink},"custom":{"prop move":{"morphTargetBinds":[{"node":1,"index":2,"weight":1}]}}}}}}
	var source: Dictionary=doc.duplicate(true);var catalogue:=P.capture(doc,rows)
	check(catalogue.error.is_empty() and catalogue.entries.size()==3,"native preset/custom groups remain distinct")
	check(catalogue.entries[0].label=="Happy" and catalogue.entries[2].label=="prop move","standard preset labels keep custom identity")
	var v:=P.evaluate(catalogue,{"preset:happy":.4})
	check(v.error.is_empty() and v.values["0"]["0"]==.2 and is_equal_approx(v.values["1"]["1"],.3),"compound strengths resolve across exact source nodes")
	check(v.values["0"]["2"]==0 and v.values["1"]["2"]==0,"single expression pose clears other embedded controls")
	v=P.evaluate(catalogue,{"preset:happy":.4,"preset:blink":1.})
	check(v.values["0"]["2"]==.6,"blend override attenuates native blink")
	var binary: Dictionary=doc.duplicate(true);binary.extensions.VRMC_vrm.expressions.preset.happy.isBinary=true
	var c:=P.capture(binary,rows)
	check(P.evaluate(c,{"preset:happy":.5,"preset:blink":1.}).values["0"]["2"]==1.,"binary threshold at half does not suppress blink")
	check(P.evaluate(c,{"preset:happy":.5001,"preset:blink":1.}).values["0"]["2"]==0.,"binary output controls override strength")
	binary=doc.duplicate(true);binary.extensions.VRMC_vrm.expressions.preset.blink.isBinary=true;c=P.capture(binary,rows)
	check(P.evaluate(c,{"preset:happy":.01,"preset:blink":1.}).values["0"]["2"]==0.,"any attenuation fully suppresses binary blink")
	binary=doc.duplicate(true);binary.extensions.VRMC_vrm.expressions.preset.happy.overrideBlink="block";c=P.capture(binary,rows)
	check(P.evaluate(c,{"preset:happy":.01,"preset:blink":1.}).values["0"]["2"]==0.,"block overrides active procedural controls")
	binary=doc.duplicate(true);binary.extensions.VRMC_vrm.expressions.preset.blink.overrideBlink="block";c=P.capture(binary,rows)
	check(P.evaluate(c,{"preset:blink":1.}).values["0"]["2"]==1.,"same procedural category does not override itself")
	check(not P.evaluate(catalogue,{"foreign":1.}).error.is_empty() and not P.evaluate(catalogue,{"preset:happy":NAN}).error.is_empty(),"foreign identities and nonfinite values refuse")
	var old: Dictionary={"nodes":doc.nodes,"meshes":doc.meshes,"extensions":{"VRM":{"specVersion":"0.0","blendShapeMaster":{"blendShapeGroups":[{"name":"Joy","presetName":"joy","binds":[{"mesh":0,"index":1,"weight":75}]}]}}}}
	c=P.capture(old,rows);v=P.evaluate(c,{"group:0":.4})
	check(c.entries[0].label=="Happy" and c.entries[0].binds.size()==2 and is_equal_approx(v.values["0"]["1"],.3) and v.values["0"]==v.values["1"],"VRM0 percentage mesh binding resolves every active instance")
	for bad_value in [{"node":0,"index":999,"weight":1},{"node":999,"index":0,"weight":1},{"node":0,"index":0,"weight":NAN},{"node":0,"index":0,"weight":true},{"node":0,"index":0,"weight":1.1}]:
		var bad:=doc.duplicate(true);bad.extensions.VRMC_vrm.expressions.preset.happy.morphTargetBinds=[bad_value];c=P.capture(bad,rows)
		check(not P.evaluate(c,{"preset:happy":1.}).error.is_empty(),"invalid binding refuses without partial pose")
	for field in ["materialColorBinds","textureTransformBinds"]:
		var bad:=doc.duplicate(true);bad.extensions.VRMC_vrm.expressions.preset.happy[field]=[{}];c=P.capture(bad,rows)
		check(not P.evaluate(c,{"preset:happy":1.}).error.is_empty(),"unsupported native effects refuse: "+field)
	var bad:=doc.duplicate(true);bad.extensions.VRMC_vrm.expressions.preset.happy.morphTargetBinds.append(happy.morphTargetBinds[0]);c=P.capture(bad,rows)
	check(not P.evaluate(c,{"preset:happy":1.}).error.is_empty(),"duplicate target binding refuses")
	bad=old.duplicate(true);bad.extensions.VRM.blendShapeMaster.blendShapeGroups[0].materialValues=[{}];c=P.capture(bad,rows)
	check(not P.evaluate(c,{"group:0":1.}).error.is_empty(),"VRM0 material expressions refuse completely")
	bad=doc.duplicate(true);bad.extensions.VRMC_vrm.specVersion="next";check(not P.capture(bad,rows).error.is_empty(),"future native versions remain unsupported")
	check(P.capture({},[]).entries.is_empty(),"ordinary non-VRM assets keep no invented presets")
	check(doc==source and rows[0].names==["eye","mouth","brow"],"native document and binding inventory remain immutable")
	var prepared:={"format":P.FORMAT,"entries":[{"id":"mmd:group:0","native_name":"Native group","label":"Friendly","group":"native group","binds":[{"node":"0","index":"0","native_name":"eye","weight":-.5},{"node":"1","index":"1","native_name":"mouth","weight":.3}],"error":""}],"error":""}
	c=P.capture({"asset":{"extras":{"studio_expression_groups":prepared}}},rows);v=P.evaluate(c,{"mmd:group:0":.6})
	check(c.error.is_empty() and is_equal_approx(v.values["0"]["0"],-.3) and is_equal_approx(v.values["1"]["1"],.18),"prepared native groups feed signed weights into the same standard evaluator")
	for field in ["node","index","native_name","weight"]:
		var invalid:=prepared.duplicate(true);invalid.entries[0].binds[0][field]="foreign" if field!="weight" else NAN
		check(not P.evaluate(P.capture_prepared(invalid,rows),{"mmd:group:0":1.}).error.is_empty(),"prepared binding identity/range refuses: "+field)
	var duplicate:=prepared.duplicate(true);duplicate.entries[0].binds.append(duplicate.entries[0].binds[0]);check(not P.evaluate(P.capture_prepared(duplicate,rows),{"mmd:group:0":1.}).error.is_empty(),"duplicate prepared target refuses as a whole")
	duplicate=prepared.duplicate(true);duplicate.entries.append(duplicate.entries[0]);check(not P.capture_prepared(duplicate,rows).error.is_empty(),"duplicate native group identity refuses")
	duplicate=prepared.duplicate(true);duplicate.entries[0].error="Needs unsupported UV effects";check(not P.evaluate(P.capture_prepared(duplicate,rows),{"mmd:group:0":1.}).error.is_empty(),"unsupported prepared group cannot install a partial vertex pose")
	duplicate=prepared.duplicate(true);duplicate.entries[0].binary=true;check(not P.capture_prepared(duplicate,rows).error.is_empty(),"unimplemented prepared semantics refuse instead of being ignored")
	duplicate=prepared.duplicate(true);duplicate.format="future";check(not P.capture_prepared(duplicate,rows).error.is_empty(),"future prepared group versions refuse")
	var ambiguous:=doc.duplicate(true);ambiguous.asset={"extras":{"studio_expression_groups":prepared}};check(not P.capture(ambiguous,rows).error.is_empty(),"competing native group declarations refuse")
	print("EXPRESSION_PRESETS_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
