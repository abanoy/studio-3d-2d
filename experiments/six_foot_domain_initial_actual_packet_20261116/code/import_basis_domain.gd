extends RefCounted
# UNPARSED/UNRUN domain draft. No classifier or application activation.
# Positive paths below are isolated contract tests, not a qualified HAS runtime.
const FORMAT := "studio_import_basis_1"
const EPS := 0.00002
const BASIS_KEYS := ["format","purpose","source_sha256","measured_from_sha256","factor","target_metres","measured_converted_height","measurement_algorithm","reference_pose","classification","decision"]

static func _trim(value: String) -> String:
	var i := 0
	while i < value.length()-1 and value[i] == "0": i += 1
	return value.substr(i)

static func decimal_record(value,limit: int=96) -> Dictionary:
	if not value is String or value.is_empty() or value.length() > limit: return {"error":"Canonical bounded positive decimal text required"}
	var dot: int = value.find(".")
	var whole: String = value if dot < 0 else value.substr(0,dot)
	var fraction: String = "" if dot < 0 else value.substr(dot+1)
	if whole.is_empty() or whole.length() > 1 and whole[0] == "0" or dot >= 0 and (fraction.is_empty() or fraction[-1] == "0"): return {"error":"Canonical decimal required"}
	for ch in whole+fraction:
		if not ch in "0123456789": return {"error":"Decimal digits required"}
	var digits := _trim(whole+fraction)
	if digits == "0": return {"error":"Positive decimal required"}
	return {"digits":digits,"places":fraction.length()}

static func _compare(a: String,b: String) -> int:
	a = _trim(a); b = _trim(b)
	if a.length() != b.length(): return -1 if a.length() < b.length() else 1
	return 0 if a == b else -1 if a < b else 1

static func _subtract(a: String,b: String) -> String:
	var result := ""
	var borrow := 0
	for offset in range(a.length()):
		var ai: int = a.unicode_at(a.length()-1-offset)-48-borrow
		var bi: int = b.unicode_at(b.length()-1-offset)-48 if offset < b.length() else 0
		if ai < bi: ai += 10; borrow = 1
		else: borrow = 0
		result = str(ai-bi)+result
	return _trim(result)

static func _divide(numerator: String,denominator: String) -> Dictionary:
	var quotient := ""
	var remainder := "0"
	for ch in numerator:
		remainder = _trim(remainder+ch)
		var digit := 0
		while _compare(remainder,denominator) >= 0:
			remainder = _subtract(remainder,denominator); digit += 1
		quotient += str(digit)
	return {"quotient":_trim(quotient),"remainder":remainder}

static func _fraction_digit(remainder: String,denominator: String) -> Dictionary:
	var rest := _trim(remainder+"0")
	var digit := 0
	while _compare(rest,denominator) >= 0:
		rest = _subtract(rest,denominator); digit += 1
	return {"digit":digit,"remainder":rest}

static func _increment(value: String) -> String:
	var result := ""
	var carry := 1
	for offset in range(value.length()):
		var digit: int = value.unicode_at(value.length()-1-offset)-48+carry
		result = str(digit%10)+result; carry = int(digit/10)
	return ("1" if carry else "")+result

static func rounded_ratio(numerator: String,denominator: String) -> Dictionary:
	# Exact positive integer division,50 significant digits, round nearest ties-even.
	# Strings stay bounded by the96-character input contract; no float division.
	for value in [numerator,denominator]:
		if value.is_empty() or value.length() > 192 or _trim(value) == "0": return {"error":"Bounded positive integer ratio required"}
		for ch in value:
			if not ch in "0123456789": return {"error":"Integer digits required"}
	var divided := _divide(_trim(numerator),_trim(denominator))
	var coefficient: String = divided.quotient
	var remainder: String = divided.remainder
	var exponent: int = coefficient.length()-1
	if coefficient == "0":
		coefficient = ""; exponent = -1
		var guard := 0
		while coefficient.is_empty():
			var next := _fraction_digit(remainder,denominator); remainder = next.remainder
			if next.digit: coefficient = str(next.digit)
			else: exponent -= 1
			guard += 1
			if guard > 200: return {"error":"Ratio expansion exceeds input bound"}
	while coefficient.length() < 51 and remainder != "0":
		var next := _fraction_digit(remainder,denominator)
		coefficient += str(next.digit); remainder = next.remainder
	if coefficient.length() > 50:
		var digit: int = coefficient.unicode_at(50)-48
		var tail_nonzero: bool = remainder != "0"
		for ch in coefficient.substr(51):
			if ch != "0": tail_nonzero = true
		coefficient = coefficient.substr(0,50)
		var odd: bool = (coefficient.unicode_at(49)-48)%2 == 1
		if digit > 5 or digit == 5 and (tail_nonzero or odd): coefficient = _increment(coefficient)
		if coefficient.length() > 50: coefficient = coefficient.substr(0,50); exponent += 1
	var point: int = exponent+1
	var output: String
	if point <= 0: output = "0."+"0".repeat(-point)+coefficient
	elif point >= coefficient.length(): output = coefficient+"0".repeat(point-coefficient.length())
	else: output = coefficient.substr(0,point)+"."+coefficient.substr(point)
	if output.contains("."):
		while output.ends_with("0"): output = output.left(-1)
		if output.ends_with("."): output = output.left(-1)
	return {"text":output}

static func _decimal_compare(a: String,b: String) -> int:
	# Computed extreme out-of-range ratios may exceed the96-character INPUT
	# contract before this comparison rejects them; never index an error record.
	var aa := decimal_record(a,256); var bb := decimal_record(b,256)
	var places: int = maxi(aa.places,bb.places)
	return _compare(aa.digits+"0".repeat(places-aa.places),bb.digits+"0".repeat(places-bb.places))

static func factor_for(height) -> Dictionary:
	var parsed := decimal_record(height)
	if parsed.has("error"): return parsed
	var computed := rounded_ratio("18288"+"0".repeat(parsed.places),parsed.digits+"0000")
	if computed.has("error"): return computed
	if _decimal_compare(computed.text,"0.001") < 0 or _decimal_compare(computed.text,"10000") > 0: return {"error":"Basis factor outside prototype supported range"}
	return {"factor_text":computed.text}

static func _sha(value) -> bool:
	if not value is String or value.length() != 64: return false
	for ch in value:
		if not ch in "0123456789abcdef": return false
	return true

static func record_error(model) -> String:
	if not model is Dictionary: return "Model dictionary required"
	if not model.has("asset_basis"): return ""
	if model.get("kind","model") != "model": return "Import basis is only for complete character models"
	var record = model.asset_basis
	if not record is Dictionary or record.size() != BASIS_KEYS.size(): return "Unknown import-basis fields"
	for key in record:
		if not key is String or not key in BASIS_KEYS: return "Unknown import-basis fields"
	if record.format != FORMAT or record.purpose != "standard_complete_human_six_feet": return "Unsupported import basis"
	if not _sha(record.source_sha256) or record.source_sha256 != model.get("sha256") or record.measured_from_sha256 != record.source_sha256: return "Basis source changed; authenticated derivative support is not implemented"
	if record.target_metres != "1.8288" or record.measurement_algorithm != "neutral_complete_human_height_1" or record.reference_pose != "neutral_default" or record.classification != "verified_complete_human" or not record.decision in ["automatic_qualified","explicit_complete_human_override"]: return "Unsupported basis measurement facts"
	var computed := factor_for(record.measured_converted_height)
	if computed.has("error"): return computed.error
	if record.factor != computed.factor_text: return "Stored factor differs from the deterministic reviewed height ratio"
	return ""

static func model_admission(model,scene_capability=false,runtime_basis_ready=false) -> Dictionary:
	if not scene_capability is bool or not runtime_basis_ready is bool: return {"error":"Actual internal boolean capability/readiness required"}
	if not model is Dictionary: return {"error":"Model dictionary required"}
	if not model.has("asset_basis"): return {"factor":1.0,"factor_text":"1","legacy_identity":true}
	if not scene_capability: return {"error":"Active import basis requires project schema9 capability"}
	var error := record_error(model)
	if not error.is_empty(): return {"error":error}
	if not runtime_basis_ready: return {"error":"Active import basis is unavailable until the matching HAS runtime is qualified"}
	var value: float = model.asset_basis.factor.to_float()
	if not is_finite(value) or value < 0.001 or value > 10000: return {"error":"Bounded positive runtime factor required"}
	return {"factor":value,"factor_text":model.asset_basis.factor,"legacy_identity":false}

static func _whole(value,minimum: int,maximum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value >= minimum and value <= maximum and float(value) == floorf(float(value))

static func _content_version(document) -> Dictionary:
	if not document is Dictionary or not _whole(document.get("schema_version"),3,9): return {"error":"Unsupported project schema"}
	var version: int = int(document.schema_version)
	var wrapped: bool = version == 9
	if wrapped:
		if document.get("import_basis_capability") != FORMAT or not _whole(document.get("basis_content_schema_version"),3,8): return {"error":"Invalid basis capability wrapper"}
		version = int(document.basis_content_schema_version)
	elif document.has("basis_content_schema_version") or document.has("import_basis_capability"): return {"error":"Basis wrapper marker requires schema9"}
	if version == 8:
		if not _whole(document.get("timing_content_schema_version"),3,7): return {"error":"Invalid timing wrapper"}
		version = int(document.timing_content_schema_version)
	elif document.has("timing_content_schema_version"): return {"error":"Timing marker requires timing wrapper"}
	if version == 7:
		if not _whole(document.get("content_schema_version"),3,6) or not document.get("reference_sheet") is Dictionary: return {"error":"Invalid reference wrapper"}
		version = int(document.content_schema_version)
	elif document.has("content_schema_version") or document.has("reference_sheet"): return {"error":"Reference fields require reference wrapper"}
	return {"content":version,"wrapped":wrapped}

static func _existing_child_schema(document: Dictionary) -> int:
	var version: int = int(document.basis_content_schema_version) if document.schema_version == 9 else int(document.schema_version)
	return int(document.timing_content_schema_version) if version == 8 else version

static func _slots(document: Dictionary,content: int) -> Dictionary:
	if content == 3:
		if document.has("world"): return {"error":"Schema3 cannot contain a world"}
		var scene = document.get("scene",{})
		var model = document.get("model",{})
		if not scene is Dictionary or scene.has("asset_basis") or not model is Dictionary: return {"error":"Invalid legacy model/map slots"}
		return {"models":[] if model.is_empty() else [model]}
	var world = document.get("world")
	if not world is Dictionary or not world.get("objects") is Array or world.objects.size() > 64 or document.has("model") or document.has("scene"): return {"error":"Bounded world required"}
	return {"models":world.objects}

static func _children(document: Dictionary,content: int,child: bool) -> Dictionary:
	var graph = document.get("sequence_graph")
	if content != 6: return {"scenes":[]} if graph == null else {"error":"Sequence graph requires schema6 content"}
	if child or not graph is Dictionary or not graph.get("assets") is Array or graph.assets.is_empty() or graph.assets.size() > 4: return {"error":"Bounded existing sequence graph required"}
	var result: Array = []
	for asset in graph.assets:
		if not asset is Dictionary or not asset.get("scene") is Dictionary: return {"error":"Invalid sequence scene"}
		result.append(asset.scene)
	return {"scenes":result}

static func inspect_capability(document,child: bool=false) -> Dictionary:
	var schema := _content_version(document)
	if schema.has("error"): return schema
	if child and not _existing_child_schema(document) in [4,5]: return {"error":"Child scenes must retain existing world4/5 schema admission"}
	var slots := _slots(document,schema.content)
	if slots.has("error"): return slots
	var own := false
	var count := 0
	for model in slots.models:
		if not model is Dictionary: return {"error":"Model dictionary required"}
		if model.has("asset_basis") and not schema.wrapped: return {"error":"Active import basis requires scene-local schema9 capability"}
		var error := record_error(model)
		if not error.is_empty(): return {"error":error}
		own = own or model.has("asset_basis"); count += 1
	var children := _children(document,schema.content,child)
	if children.has("error"): return children
	var nested := false
	for scene in children.scenes:
		var inspected := inspect_capability(scene,true)
		if inspected.has("error"): return inspected
		nested = nested or inspected.basis_required; count += inspected.object_count
	if count > 64: return {"error":"Existing shared64-object budget exceeded"}
	var active: bool = own or nested
	if schema.wrapped != active: return {"error":"Missing or redundant schema9 capability"}
	return {"basis_required":active,"content_schema":schema.content,"object_count":count,"own_scene_permission":schema.wrapped}

static func encode_capability(document,child: bool=false) -> Dictionary:
	var schema := _content_version(document)
	if schema.has("error"): return schema
	if schema.wrapped:
		var inspected := inspect_capability(document,child)
		return inspected if inspected.has("error") else {"document":document.duplicate(true)}
	if child and not _existing_child_schema(document) in [4,5]: return {"error":"Child scenes must retain existing world4/5 schema admission"}
	var result: Dictionary = document.duplicate(true)
	var slots := _slots(result,schema.content)
	if slots.has("error"): return slots
	var own := false
	for model in slots.models:
		var error := record_error(model)
		if not error.is_empty(): return {"error":error}
		own = own or model.has("asset_basis")
	var children := _children(result,schema.content,child)
	if children.has("error"): return children
	var nested := false
	for scene in children.scenes:
		var encoded := encode_capability(scene,true)
		if encoded.has("error"): return encoded
		scene.clear(); scene.merge(encoded.document,true)
		nested = nested or scene.schema_version == 9
	if own or nested:
		result["basis_content_schema_version"] = result.schema_version
		result.schema_version = 9
		result["import_basis_capability"] = FORMAT
	var inspected := inspect_capability(result,child)
	return inspected if inspected.has("error") else {"document":result}

static func configure_import_root(raw_root,model,scene_capability=false,runtime_basis_ready=false) -> Dictionary:
	# A future constructor calls once with immutable rawB0, before inventory.
	# Never pass a previously adjusted base_root back as raw_root.
	var admitted := model_admission(model,scene_capability,runtime_basis_ready)
	if admitted.has("error"): return admitted
	if not raw_root is Transform3D: return {"error":"Raw imported Transform3D required"}
	if admitted.legacy_identity: return {"raw_root":raw_root,"base_root":raw_root,"factor":1.0}
	if not raw_root.is_finite() or raw_root.basis.determinant() <= 0.0: return {"error":"Positive finite imported root required"}
	var size: float = raw_root.basis.x.length()
	if not is_finite(size) or size <= 0.0: return {"error":"Positive uniform imported root required"}
	for axis in [raw_root.basis.x,raw_root.basis.y,raw_root.basis.z]:
		if absf(axis.length()-size) > EPS*size: return {"error":"Uniform imported root required"}
	for pair in [[0,1],[0,2],[1,2]]:
		if absf(raw_root.basis[pair[0]].dot(raw_root.basis[pair[1]])/(size*size)) > EPS: return {"error":"Unsheared imported root required"}
	var intrinsic := Transform3D(Basis.IDENTITY.scaled(Vector3.ONE*admitted.factor),Vector3.ZERO)
	return {"raw_root":raw_root,"base_root":intrinsic*raw_root,"factor":admitted.factor}
