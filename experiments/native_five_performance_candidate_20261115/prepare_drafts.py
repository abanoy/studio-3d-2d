"""Source-only capture projection variants; never apply or execute GDScript."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
INPUT=ROOT/'experiments/source_native_five_port_candidate_v2_20261115'
SELECTED=[8,17,18,26,27]
EXPECTED=[0,1,2,3,4,5,6,7,8,17,18,25,26,27]
INPUT_PINS={
    'source_secondary.gd':'dcf861f26ff7829ec25e2616e56416dd68fa4bb6a32d5340c969b9c946d84e47',
    'source_chain_math.gd':'31491fbde49b635edadda5e661fa3eecabf0f7e3598f0dc448c0d944ffa6f844',
    'secondary_live.gd':'2613b19ce53b3a50fd001fe4e5b39bca2814165148b036993549490aa96c33a9',
    'INDEX.json':'460b7719c1bab426aebcc1d04d97bf0d6932b0a6bcadb75db9000147fef6c657',
}

ADMISSION=r'''
	# All69 imported bindings/base frames are still authenticated above. Only the
	# exact complete ancestor closure enters the unchanged scalar step core.
	var keep := {}
	for native_index in SELECTED_NATIVE_IDS:
		var current: Variant = bound.by_native[native_index]
		var seen := {}
		while current != null:
			if seen.has(current) or not candidate._bone_specs.has(current): candidate.dispose(); return {"error":"The imported hair ancestor closure changed."}
			seen[current] = true; keep[current] = true
			current = candidate._bone_specs[current].parent
	var observed_native := []
	for native_index in range(69):
		var id: String = bound.by_native[native_index]
		if keep.has(id):
			observed_native.append(native_index)
			candidate._solver_bone_specs[id] = candidate._bone_specs[id].duplicate(true)
	if observed_native != EXPECTED_CAPTURE_NATIVE_IDS: candidate.dispose(); return {"error":"The imported hair ancestor profile changed."}
	var all_order := Chains.parent_order(candidate._bone_specs)
	if all_order.has("error"): candidate.dispose(); return all_order
	for id in all_order.order:
		var parent: Variant = candidate._bone_specs[id].parent
		var parent_size: float = candidate._prefix_scale if parent == null else candidate._expected_world_scales[parent]
		candidate._expected_world_scales[id] = parent_size*float(candidate._base_scales[id])
		if not is_finite(float(candidate._expected_world_scales[id])) or candidate._expected_world_scales[id] < 1e-8 or candidate._expected_world_scales[id] > 1e6: candidate.dispose(); return {"error":"The imported hair world scale is outside its supported profile."}
	candidate._capture_configuration_stamp = var_to_bytes([candidate._bone_specs,candidate._solver_bone_specs,candidate._base_scales,candidate._expected_world_scales])
'''

RAW_GUARD=r'''
static func raw_frame_guard(value: Transform3D) -> Dictionary:
	# Exact scalar-double prefix of frame64; EPS is unchanged. This intentionally
	# does not claim the later Gram-Schmidt/correction/Math.goal rejection domain.
	if not value.origin.is_finite() or not value.basis.is_finite() or value.basis.determinant() <= 0.0: return {"error":"Imported hair needs a finite, positive uniform transform."}
	var raw: Array = [vector64(value.basis.x),vector64(value.basis.y),vector64(value.basis.z)]
	var scales: Array = [Math.v_length(raw[0]),Math.v_length(raw[1]),Math.v_length(raw[2])]
	var size: float = scales[0]
	if not is_finite(size) or size <= 0.00001: return {"error":"Imported hair has a degenerate transform."}
	for i in range(3):
		if not is_finite(scales[i]) or absf(scales[i]-size) > EPS*size: return {"error":"Imported hair currently needs uniform scale."}
	var units: Array = [Math.v_mul(raw[0],1.0/scales[0]),Math.v_mul(raw[1],1.0/scales[1]),Math.v_mul(raw[2],1.0/scales[2])]
	for pair in [[0,1],[0,2],[1,2]]:
		if absf(Math.v_dot(units[pair[0]],units[pair[1]])) > EPS: return {"error":"Imported hair does not support sheared transforms."}
	return {"scale":size}

'''

CAPTURE=r'''
func capture_baseline() -> Dictionary:
	# Fresh synchronous same-call snapshot, never a previous-tick authored pose.
	if var_to_bytes([_bone_specs,_solver_bone_specs,_base_scales,_expected_world_scales]) != _capture_configuration_stamp: return {"error":"The imported hair capture configuration changed."}
	var raw_prefix: Transform3D = _skeleton.global_transform
	var observed_prefix := frame64(raw_prefix)
	if observed_prefix.has("error"): return observed_prefix
	if absf(float(observed_prefix.scale)-_prefix_scale) > EPS*_prefix_scale: return {"error":"Turn imported hair off before resizing the model or its parent."}
	var prefix := {"origin":observed_prefix.goal.base.duplicate(true),"basis":observed_prefix.rotation.duplicate(true),"scale":_prefix_scale}
	var locals := {}
	var raw_locals := {}
	var raw_worlds := {}
	var mapped_worlds := {}
	for id in _bone_specs:
		var info: Dictionary = actor.bones[id]
		var local: Transform3D = _skeleton.get_bone_pose(info.index)
		var actual: Transform3D = actor.bone_transform(id)
		var mapped: Dictionary = LOCAL_MAPPING
		if mapped.has("error"): return mapped
		var actual_frame: Dictionary = WORLD_MAPPING
		if actual_frame.has("error"): return actual_frame
		var stable: float = _base_scales[id]
		if absf(float(mapped.scale)-stable) > EPS*stable: return {"error":"The imported hair local scale changed; turn its preview off."}
		var expected_size: float = _expected_world_scales[id]
		if absf(float(actual_frame.scale)-expected_size) > EPS*expected_size: return {"error":"The imported hair world scale changed; turn its preview off."}
		raw_locals[id] = local; raw_worlds[id] = actual; mapped_worlds[id] = actual_frame
		if KEEP_LOCAL:
			locals[id] = {"origin":mapped.goal.base.duplicate(true),"basis":mapped.rotation.duplicate(true),"scale":stable}
	# Retain actual Transform3D parent/local closure for every one of69 bones.
	for id in _bone_specs:
		var parent: Variant = _bone_specs[id].parent
		var parent_world: Transform3D = raw_prefix if parent == null else raw_worlds[parent]
		var actual: Transform3D = raw_worlds[id]
		var composed: Transform3D = parent_world*raw_locals[id]
		if not composed.origin.is_finite() or not composed.basis.is_finite(): return {"error":"The imported hair parent pose changed."}
		var size: float = mapped_worlds[id].scale
		var guard: float = EPS*maxf(1.0,size)
		if composed.origin.distance_to(actual.origin) > EPS*size: return {"error":"The imported hair parent pose changed."}
		for i in range(3):
			for j in range(3):
				if absf(composed.basis[i][j]-actual.basis[i][j]) > guard: return {"error":"The imported hair parent pose changed."}
	var worlds: Dictionary = BASELINE_CALL
	if worlds.has("error"): return worlds
	for id in CHECK_WORLD_IDS:
		var actual: Dictionary = mapped_worlds[id]
		var target: Dictionary = worlds.worlds[id]
		if absf(float(actual.scale)-float(target.scale)) > EPS*float(target.scale): return {"error":"The imported hair world scale changed; turn its preview off."}
		var wanted: Array = target.origin
		var actual_raw: Transform3D = raw_worlds[id]
		if actual_raw.origin.distance_to(Vector3(wanted[0],wanted[1],wanted[2])) > EPS*float(target.scale): return {"error":"The imported hair authored parent chain differs from its supported profile."}
		for i in range(3):
			for j in range(3):
				if absf(float(actual.rotation[i][j])-float(target.basis[i][j])) > EPS: return {"error":"The imported hair authored orientation differs from its supported profile."}
	var selected_locals := {}
	for id in _solver_bone_specs: selected_locals[id] = locals[id]
	return {"locals":selected_locals,"prefix":prefix}
'''


def sha(body):return hashlib.sha256(body).hexdigest()


def main():
    for name,digest in INPUT_PINS.items():assert sha((INPUT/name).read_bytes())==digest,name
    source=(INPUT/'source_secondary.gd').read_text(encoding='utf-8')
    core=(INPUT/'source_chain_math.gd').read_bytes()
    provenance={'format':'native_five_performance_source_draft_1','status':'SOURCE_ONLY_UNPARSED_UNRUN_UNAPPLIED','inputs':{name:sha((INPUT/name).read_bytes()) for name in ('source_secondary.gd','source_chain_math.gd','secondary_live.gd','INDEX.json')},'selected':SELECTED,'ancestor_closure_native':EXPECTED,'core_bytes_unchanged':True}
    for variant in ('strict','closure'):
        code=source.replace('SOURCE-ONLY five-rule successor; UNPARSED/UNRUN.','SOURCE-ONLY '+variant+' performance candidate; UNPARSED/UNRUN.',1)
        code=code.replace('var _bone_specs: Dictionary = {}','var _bone_specs: Dictionary = {}\nvar _solver_bone_specs: Dictionary = {}\nvar _expected_world_scales: Dictionary = {}\nvar _capture_configuration_stamp := PackedByteArray()\nvar _baseline_guard: RefCounted\nvar _baseline_guard_stamp := PackedByteArray()\nconst EXPECTED_CAPTURE_NATIVE_IDS := '+str(EXPECTED),1)
        marker='\t# Both runners own independent configuration/state.'
        assert marker in code
        code=code.replace(marker,ADMISSION+'\n'+marker,1)
        code=code.replace('Chains.create(candidate._bone_specs,candidate._parameters','Chains.create(candidate._solver_bone_specs,candidate._parameters')
        if variant=='strict':
            anchor='\tvar initial := candidate.capture_baseline()'
            setup='\tvar guard := Chains.create(candidate._bone_specs,candidate._parameters,SOURCE_SCALE,[0.0,-1.0,0.0])\n\tif guard.has("error"): candidate.dispose(); return guard\n\tcandidate._baseline_guard = guard.actor\n\tcandidate._baseline_guard_stamp = candidate.configuration_stamp(candidate._baseline_guard)\n'
            code=code.replace(anchor,setup+anchor,1)
        begin=code.index('func capture_baseline() -> Dictionary:')
        end=code.index('\nfunc step(',begin)
        if variant=='strict':
            capture=CAPTURE.replace('LOCAL_MAPPING','frame64(local)').replace('WORLD_MAPPING','frame64(actual)').replace('KEEP_LOCAL','true').replace('BASELINE_CALL','_baseline_guard.baseline_worlds(locals,prefix)').replace('CHECK_WORLD_IDS','_bone_specs')
            capture=capture.replace('\tvar raw_prefix:', '\tif configuration_stamp(_baseline_guard) != _baseline_guard_stamp: return {"error":"The imported hair baseline guard configuration changed."}\n\tvar raw_prefix:',1)
        else:
            capture=CAPTURE.replace('LOCAL_MAPPING','frame64(local) if _solver_bone_specs.has(id) else raw_frame_guard(local)').replace('WORLD_MAPPING','frame64(actual) if _solver_bone_specs.has(id) else raw_frame_guard(actual)').replace('KEEP_LOCAL','_solver_bone_specs.has(id)').replace('BASELINE_CALL','_chain.baseline_worlds(locals,prefix)').replace('CHECK_WORLD_IDS','_solver_bone_specs')
            capture=RAW_GUARD+capture
        code=code[:begin]+capture.lstrip('\n')+code[end:]
        code=code.replace('\t_parameters.clear(); _bone_specs.clear();','\tif _baseline_guard: _baseline_guard.stop(); _baseline_guard = null\n\t_baseline_guard_stamp.clear(); _capture_configuration_stamp.clear(); _solver_bone_specs.clear(); _expected_world_scales.clear()\n\t_parameters.clear(); _bone_specs.clear();',1)
        target=HERE/('source_secondary_'+variant+'.gd');target.write_text(code,encoding='utf-8',newline='\n')
        diff=''.join(difflib.unified_diff(source.splitlines(keepends=True),code.splitlines(keepends=True),fromfile='sealed_v2/source_secondary.gd',tofile=target.name))
        (HERE/(variant+'.diff')).write_text(diff,encoding='utf-8',newline='\n')
        provenance[variant+'_sha256']=sha(target.read_bytes())
    (HERE/'source_chain_math.gd').write_bytes(core)
    (HERE/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(provenance,indent=2))


if __name__=='__main__':main()
