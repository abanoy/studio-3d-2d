extends RefCounted
# Reference inheritance and independently checked existing-joint derivatives.
const ImportBasis=preload("res://src/import_basis.gd")

static func copy_reference(source: Dictionary,destination: Dictionary) -> Dictionary:
	var problem: String=ImportBasis.record_error(source)
	if not problem.is_empty():return {"error":problem}
	var result:=destination.duplicate(true)
	if not ImportBasis.active(source):return {"model":result}
	if source.get("sha256")!=result.get("sha256"):return {"error":"The height reference belongs to a different model source."}
	result["asset_basis"]=source.asset_basis.duplicate(true)
	if not result.get("metadata") is Dictionary:result["metadata"]={}
	if source.metadata.has("import_basis_lineage"):result.metadata["import_basis_lineage"]=source.metadata.import_basis_lineage.duplicate(true)
	return {"model":result}

static func derivative(source: Dictionary,new_sha: String,proof: Dictionary) -> Dictionary:
	var problem: String=ImportBasis.record_error(source)
	if not problem.is_empty():return {"error":problem}
	if not ImportBasis.active(source):return {"error":"A checked human-height reference is required."}
	var fields: Array=["format","parent_sha256","source_sha256","preservation_sha256","payload"]
	if proof.size()!=fields.size() or fields.any(func(key):return not proof.has(key)) or proof.get("format")!="studio_import_basis_preservation_1" or proof.get("parent_sha256")!=source.sha256 or proof.get("source_sha256")!=new_sha:return {"error":"This helper needs a checked height-reference preservation proof. The current model was kept."}
	var text=proof.get("payload")
	if not text is String or text.length()>8192 or text.sha256_text()!=proof.get("preservation_sha256"):return {"error":"The height-reference preservation proof changed."}
	var payload=JSON.parse_string(text)
	var keys: Array=["format","method","parent_sha256","source_sha256","geometry_root_rest_skin_morph_preserved","exact_binary_preserved","source_document_sha256","source_binary_sha256","original_nodes","appended_unweighted_endpoints","original_springs","candidate_springs"]
	if not payload is Dictionary or payload.size()!=keys.size() or keys.any(func(key):return not payload.has(key)):return {"error":"Invalid height-reference preservation record."}
	if payload.format!="studio_import_basis_preservation_payload_1" or payload.method!="exact_existing_joint_endpoints_1" or payload.parent_sha256!=source.sha256 or payload.source_sha256!=new_sha or not payload.geometry_root_rest_skin_morph_preserved is bool or not payload.geometry_root_rest_skin_morph_preserved or not payload.exact_binary_preserved is bool or not payload.exact_binary_preserved:return {"error":"The helper did not preserve the original height-reference geometry."}
	for key in ["source_document_sha256","source_binary_sha256"]:
		if not payload[key] is String or payload[key].length()!=64 or not payload[key].is_valid_hex_number(false) or payload[key]!=payload[key].to_lower():return {"error":"Invalid height-reference preservation identity."}
	for key in ["original_nodes","appended_unweighted_endpoints","original_springs","candidate_springs"]:
		if not payload[key] is int and not payload[key] is float or not is_finite(float(payload[key])) or payload[key]!=floor(payload[key]):return {"error":"Invalid height-reference preservation counts."}
	if payload.original_nodes<1 or payload.original_nodes+payload.appended_unweighted_endpoints>100000 or payload.appended_unweighted_endpoints<1 or payload.appended_unweighted_endpoints>128 or payload.original_springs<0 or payload.candidate_springs>128 or payload.candidate_springs!=payload.original_springs+payload.appended_unweighted_endpoints:return {"error":"Height-reference preservation exceeds the supported helper profile."}
	return ImportBasis.authenticated_derivative(source,new_sha,proof.preservation_sha256,true)
