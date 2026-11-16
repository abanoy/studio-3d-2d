"""Generate unapplied production successor source. No engines/parser/process/Git."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'src/source_secondary.gd'
QUALIFIED = ROOT / 'output/source-0x31-native-chains-20261115-attempt1/Studio/chain_solver.gd'
BASE_SHA = 'd2c04165587ca3bb0f7b9f474b23dc81902cc78c1aa174d593534f0198f689c0'
CHAIN_SHA = '01635f84e05abe0ecc998b71117eed9c7afc6f5b15d04e8743cdf1c22efa362f'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name,value):
    with (HERE / name).open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(value)


def block(source,start,end):
    return source[source.index(start):source.index(end,source.index(start))]


def main():
    raw = BASE.read_bytes(); core = QUALIFIED.read_bytes()
    assert sha(raw) == BASE_SHA and sha(core) == CHAIN_SHA
    source = raw.decode('utf-8-sig')
    chain = core.decode('utf-8-sig')
    old = 'const Math = preload("res://leaf_candidate.gd")'
    new = 'const Math = preload("res://src/source_jiggle_math.gd")'
    assert chain.count(old) == 1
    save('source_chain_math.gd',chain.replace(old,new))
    header = block(source,'extends RefCounted','static func offered(')
    header = header.replace('# source report. The first qualified profile drives FrontHair1 only.',
                            '# source report. SOURCE-ONLY five-rule successor; UNPARSED/UNRUN.')
    header = header.replace('const Bindings =', 'const Chains = preload("res://src/source_chain_math.gd")\nconst Bindings =')
    header = header.replace('var chains: Array = []','var chains: Array = []\nvar _chain_inventory_stamp := PackedByteArray()')
    header = header.replace('var _alive := false','var _alive := false\nvar processing_samples := 0\nvar processing_total_usec := 0\nvar processing_max_usec := 0')
    header = header.replace('const SELECTED_NATIVE := 8',
                            'const SELECTED_NATIVE := 8\nconst SELECTED_NATIVE_IDS := [8,17,18,26,27]\nconst EXPECTED_PARENTS := {8:7,17:7,18:17,26:25,27:26}\nconst CHAIN_PREFIX_SHA := "f2add968c86ab5b5d6de6cc60586f1d57ecbbdd61b86b93eb2a90bcfbe0e06ba"')
    header = header.replace('var _state: Dictionary = {}\nvar _scale := 1.0',
                            'var _bone_specs: Dictionary = {}\nvar _base_scales: Dictionary = {}\nvar _chain: RefCounted\nvar _trial: RefCounted\nvar _configuration_stamp := PackedByteArray()\nvar _size_tokens: Dictionary = {}\nvar _prefix_scale := 1.0\nvar _authored_scale_token := 1.0')
    offered = block(source,'static func offered(','static func anchors(')
    numerical_context = block(source,'static func vector64(','static func create(')
    stamp = block(source,'func binding_stamp(','func step(')
    anchors = '''static func anchors(rig: RefCounted) -> Array:
\tif not offered(rig): return []
\t# Hint only; creation authenticates every numeric crosswalk and binding.
\tvar report: Dictionary = rig.data.metadata.native_parameters.native_parameters.source_export_crosswalk
\tvar mapping = rig.root.get_meta("has_source_bones",{})
\tif not mapping is Dictionary: return []
\tvar result: Array = []
\tvar seen := {}
\tfor native_index in SELECTED_NATIVE_IDS:
\t\tvar matched := false
\t\tfor row in report.bones:
\t\t\tif not row is Dictionary or row.get("native_index") != native_index: continue
\t\t\tif matched: return []
\t\t\tmatched = true
\t\t\tvar node_index = row.get("gltf_node_index")
\t\t\tif not (node_index is int or node_index is float) or not is_finite(float(node_index)) or float(node_index) != floor(float(node_index)): return []
\t\t\tvar id = mapping.get(int(node_index),"")
\t\t\tif not id is String or not rig.bones.has(id) or seen.has(id): return []
\t\t\tseen[id] = true; result.append({"kind":"bone","id":id})
\t\tif not matched: return []
\treturn result

'''
    create = '''static func create(rig: RefCounted) -> Dictionary:
\tif not offered(rig): return {"error":"Imported hair motion is not qualified for this model. Use the loose-part setup instead."}
\tvar bound: RefCounted = Bindings.resolve(rig)
\tif bound.status != "bound_inactive" or bound.bindings.size() != 69 or bound.rule_owner_ids.size() != 49 or bound.source_sha256 != GLB_SHA or bound.jiggle_wire_sha256 != WIRE_SHA: return {"error":"The imported hair bindings changed. Reopen the original model or use loose-part setup."}
\tvar sk: Skeleton3D = bound.bindings[SELECTED_NATIVE].skeleton
\tvar error := context_error(rig,sk)
\tif not error.is_empty(): return {"error":error}
\tif rig.order.size() != 69 or rig.bones.size() != 69: return {"error":"The imported hair binding inventory is incomplete."}
\tvar scale_token = rig.data.get("scale")
\tif not (scale_token is int or scale_token is float) or not is_finite(float(scale_token)) or float(scale_token) <= 0.0: return {"error":"Imported hair needs a positive authored scale."}
\tvar prefix := frame64(sk.global_transform)
\tif prefix.has("error"): return prefix
\tvar candidate = new()
\tcandidate.actor = rig; candidate.resolution = bound; candidate._skeleton = sk
\tcandidate._source_path = str(rig.data.source)
\tcandidate._prefix_scale = prefix.scale; candidate._authored_scale_token = float(scale_token)
\tfor index in range(69):
\t\tvar binding: RefCounted = bound.bindings[index]
\t\tvar id: String = binding.has_id
\t\tif binding.skeleton != sk or not rig.bones.has(id) or rig.bones[id].skeleton != sk or rig.bones[id].index != binding.skeleton_bone_index: candidate.dispose(); return {"error":"The imported hair skeleton bindings changed."}
\t\tvar parent_index: int = binding.native_parent_index
\t\tvar expected_parent: String = "@root" if parent_index < 0 else str(bound.by_native[parent_index])
\t\tif rig.parent_id(id) != expected_parent: candidate.dispose(); return {"error":"The imported hair parent mapping changed."}
\t\tvar base := frame64(rig.bones[id].base)
\t\tif base.has("error"): candidate.dispose(); return base
\t\tcandidate._base_scales[id] = float(base.scale)
\t\tcandidate._bone_specs[id] = {"parent":null if parent_index < 0 else bound.by_native[parent_index],"base":{"origin":base.goal.base.duplicate(true),"basis":base.rotation.duplicate(true),"scale":float(base.scale)}}
\tfor index in SELECTED_NATIVE_IDS:
\t\tvar binding: RefCounted = bound.bindings[index]
\t\tif binding.native_parent_index != EXPECTED_PARENTS[index]: candidate.dispose(); return {"error":"The imported hair parent profile changed."}
\t\tvar children: Array = []
\t\tfor child in range(69):
\t\t\tif bound.bindings[child].native_parent_index == index: children.append(child)
\t\tvar expected: Array = [18] if index == 17 else [27] if index == 26 else []
\t\tif children != expected: candidate.dispose(); return {"error":"The imported hair subtree no longer matches its bounded profile."}
\t\tvar rule: Dictionary = {}
\t\tfor entry in rig.data.metadata.native_parameters.native_parameters.source_jiggle.rules:
\t\t\tif entry.native_bone_index == index: rule = entry
\t\tvar prefix_sha: String = PREFIX_SHA if index == SELECTED_NATIVE else CHAIN_PREFIX_SHA
\t\tif rule.is_empty() or rule.raw_rule_flags != Math.FLAGS or rule.unknown_rule_flag_bits != 0 or rule.binary_provenance.prefix_sha256 != prefix_sha or not rule.parameters is Dictionary: candidate.dispose(); return {"error":"Imported hair coefficients do not match the supported profile."}
\t\tvar overrides := {}
\t\tfor key in Math.defaults():
\t\t\tif key == "raw_rule_flags": continue
\t\t\tif not rule.parameters.has(key): candidate.dispose(); return {"error":"The imported hair coefficients are incomplete."}
\t\t\toverrides[key] = rule.parameters[key]
\t\tvar parameters := Math.parameters(overrides)
\t\tif parameters.has("error"): candidate.dispose(); return parameters
\t\tcandidate._parameters[binding.has_id] = parameters.parameters.duplicate(true)
\t\tcandidate.chains.append({"ids":[binding.has_id],"source":{"joints":[{"binding":{"kind":"bone","id":binding.has_id}}]}})
\t# Both runners own independent configuration/state. Only the authoritative
\t# runner is committed; the trial absorbs all math/output failures.
\tvar primary := Chains.create(candidate._bone_specs,candidate._parameters,SOURCE_SCALE,[0.0,-1.0,0.0])
\tif primary.has("error"): candidate.dispose(); return primary
\tvar trial := Chains.create(candidate._bone_specs,candidate._parameters,SOURCE_SCALE,[0.0,-1.0,0.0])
\tif trial.has("error"): candidate.dispose(); return trial
\tcandidate._chain = primary.actor; candidate._trial = trial.actor
\tvar initial := candidate.capture_baseline()
\tif initial.has("error"): candidate.dispose(); return initial
\tvar seeded: Dictionary = candidate._chain.reset(initial.locals,initial.prefix)
\tif seeded.has("error"): candidate.dispose(); return seeded
\tseeded = candidate._trial.reset(initial.locals,initial.prefix)
\tif seeded.has("error"): candidate.dispose(); return seeded
\tcandidate._size_tokens = candidate._chain.snapshot().sizes.duplicate(true)
\tcandidate._configuration_stamp = candidate.configuration_stamp(candidate._chain)
\tif candidate.configuration_stamp(candidate._trial) != candidate._configuration_stamp: candidate.dispose(); return {"error":"The imported hair trial configuration differs."}
\tvar source := FileAccess.open(candidate._source_path,FileAccess.READ)
\tif source == null: candidate.dispose(); return {"error":"The imported hair source is unavailable."}
\tcandidate._source_length = source.get_length()
\tcandidate._source_header = source.get_buffer(12)
\tsource.close()
\tif candidate._source_header.size() != 12: candidate.dispose(); return {"error":"The imported hair source header is unavailable."}
\tcandidate._source_modified = FileAccess.get_modified_time(candidate._source_path)
\tcandidate._binding_stamp = candidate.binding_stamp()
\tif candidate._binding_stamp.is_empty(): candidate.dispose(); return {"error":"The imported hair binding inventory is incomplete."}
\t# The public chain/airflow inventory is mutable for legacy callers. Freeze
\t# exact order, ids and source.joints.binding as a separate admission stamp.
\tif candidate.chains.size() != SELECTED_NATIVE_IDS.size(): candidate.dispose(); return {"error":"The imported hair airflow inventory is incomplete."}
\tcandidate._chain_inventory_stamp = var_to_bytes(candidate.chains)
\tcandidate._alive = true
\treturn {"runner":candidate}

'''
    capture = '''func airflow_error() -> String:
\t# Shared internal ABI with SecondaryLive: call before reading public chains.
\tif not _alive or chains.size() != SELECTED_NATIVE_IDS.size() or var_to_bytes(chains) != _chain_inventory_stamp: return "The imported hair chain or airflow bindings changed; its preview was stopped."
\treturn ""

func configuration_stamp(value: RefCounted) -> PackedByteArray:
\t# Internal immutable configuration only, never solver states or authored data.
\treturn var_to_bytes([value._bones,value._order,value._parameters,value._source_scale,value._gravity])

func state_error(snapshot: Dictionary, expected_tick: int) -> String:
\tif typeof(snapshot.get("active")) != TYPE_BOOL or snapshot.active != true or typeof(snapshot.get("tick")) != TYPE_INT or snapshot.tick != expected_tick or not snapshot.get("states") is Dictionary or not snapshot.get("sizes") is Dictionary: return "The imported hair simulation inventory changed."
\tif snapshot.states.size() != 5 or var_to_bytes(snapshot.sizes) != var_to_bytes(_size_tokens): return "The imported hair simulation size inventory changed."
\tfor id in _parameters:
\t\tvar state = snapshot.states.get(id)
\t\tif not state is Dictionary or state.size() != 2 or not Math.vector_ok(state.get("tip")) or not Math.vector_ok(state.get("velocity")): return "The imported hair simulation state changed."
\treturn ""

func capture_baseline() -> Dictionary:
\t# SecondaryLive supplies and applies a fresh authored live_pose before each
\t# call. A direct caller must also provide that fresh baseline; this function
\t# only reads the currently applied transforms and never applies an overlay.
\tvar observed_prefix := frame64(_skeleton.global_transform)
\tif observed_prefix.has("error"): return observed_prefix
\tif absf(float(observed_prefix.scale)-_prefix_scale) > EPS*_prefix_scale: return {"error":"Turn imported hair off before resizing the model or its parent."}
\t# The old2e-5 admission gate absorbs observed float32 rotation roundoff;
\t# exact cached scale values keep the unmodified scalar core size invariant.
\t# This never changes a runner size. Sub-threshold ancestor scale drift is
\t# indistinguishable from transform roundoff and is not claimed detected.
\tvar prefix := {"origin":observed_prefix.goal.base.duplicate(true),"basis":observed_prefix.rotation.duplicate(true),"scale":_prefix_scale}
\tvar locals := {}
\tfor id in _bone_specs:
\t\tvar info: Dictionary = actor.bones[id]
\t\tvar local: Transform3D = _skeleton.get_bone_pose(info.index)
\t\tvar mapped := frame64(local)
\t\tif mapped.has("error"): return mapped
\t\tvar stable: float = _base_scales[id]
\t\tif absf(float(mapped.scale)-stable) > EPS*stable: return {"error":"The imported hair local scale changed; turn its preview off."}
\t\tlocals[id] = {"origin":mapped.goal.base.duplicate(true),"basis":mapped.rotation.duplicate(true),"scale":stable}
\t\tvar parent: Variant = _bone_specs[id].parent
\t\tvar parent_world: Transform3D = _skeleton.global_transform if parent == null else actor.bone_transform(parent)
\t\tvar actual: Transform3D = actor.bone_transform(id)
\t\tvar composed: Transform3D = parent_world*local
\t\tvar actual_frame := frame64(actual)
\t\tif actual_frame.has("error"): return actual_frame
\t\tvar guard: float = EPS*maxf(1.0,float(actual_frame.scale))
\t\tif composed.origin.distance_to(actual.origin) > EPS*float(actual_frame.scale): return {"error":"The imported hair parent pose changed."}
\t\tfor i in range(3):
\t\t\tfor j in range(3):
\t\t\t\tif absf(composed.basis[i][j]-actual.basis[i][j]) > guard: return {"error":"The imported hair parent pose changed."}
\tvar worlds: Dictionary = _chain.baseline_worlds(locals,prefix)
\tif worlds.has("error"): return worlds
\tfor id in _bone_specs:
\t\tvar actual := frame64(actor.bone_transform(id))
\t\tif actual.has("error"): return actual
\t\tvar target: Dictionary = worlds.worlds[id]
\t\tif absf(float(actual.scale)-float(target.scale)) > EPS*float(target.scale): return {"error":"The imported hair world scale changed; turn its preview off."}
\t\tvar wanted: Array = target.origin
\t\tif actor.bone_transform(id).origin.distance_to(Vector3(wanted[0],wanted[1],wanted[2])) > EPS*float(target.scale): return {"error":"The imported hair authored parent chain differs from its supported profile."}
\t\tfor i in range(3):
\t\t\tfor j in range(3):
\t\t\t\tif absf(float(actual.rotation[i][j])-float(target.basis[i][j])) > EPS: return {"error":"The imported hair authored orientation differs from its supported profile."}
\treturn {"locals":locals,"prefix":prefix}

'''
    step = block(source,'func step(','func dispose()')
    # Keep all d2 source/header/stat/binding/context guards byte-identical.
    before = step[:step.index('\tvar id: String = chains[0].ids[0]')]
    before = before.replace('func step(delta: float,wind: Vector3,forces: Array = []) -> Dictionary:\n','func step(delta: float,wind: Vector3,forces: Array = []) -> Dictionary:\n\tvar processing_started: int = Time.get_ticks_usec()\n')
    before += '\tif chains.size() != SELECTED_NATIVE_IDS.size() or var_to_bytes(chains) != _chain_inventory_stamp: return {"error":"The imported hair chain or airflow bindings changed; its preview was stopped."}\n'
    after = '''\tvar scale_token = actor.data.get("scale")
\tif not (scale_token is int or scale_token is float) or not is_finite(float(scale_token)) or float(scale_token) != _authored_scale_token: return {"error":"Turn imported hair off before resizing the model."}
\tif not forces.is_empty() and forces.size() != SELECTED_NATIVE_IDS.size(): return {"error":"Imported hair needs one airflow input per selected joint."}
\tvar accelerations := {}
\tvar authored_positions := {}
\tfor i in range(SELECTED_NATIVE_IDS.size()):
\t\tvar index: int = SELECTED_NATIVE_IDS[i]
\t\tvar id: String = resolution.by_native[index]
\t\tvar binding: RefCounted = resolution.bindings[index]
\t\tif not actor.bones.has(id) or actor.bones[id].skeleton != _skeleton or actor.bones[id].index != binding.skeleton_bone_index or not _skeleton.is_bone_enabled(binding.skeleton_bone_index) or actor.parent_id(id) != resolution.by_native[EXPECTED_PARENTS[index]]: return {"error":"The imported hair binding changed; its preview was stopped."}
\t\tvar force = wind if forces.is_empty() else forces[i]
\t\tif not force is Vector3 or not force.is_finite() or force.length() > 1000000.0: return {"error":"Imported hair received an invalid airflow input."}
\t\taccelerations[id] = vector64(force)
\t\tif not actor.live_pose is Dictionary and _skeleton.get_bone_pose(binding.skeleton_bone_index).origin != actor.bones[id].base.origin: return {"error":"Imported hair needs a fresh authored pose baseline before stepping."}
\t\tvar authored: Dictionary = actor.live_pose.get(id,Model.identity()) if actor.live_pose is Dictionary else Model.identity()
\t\tif not authored.get("position") is Array or authored.position.size() != 3: return {"error":"The imported hair authored translation is incomplete."}
\t\tfor value in authored.position:
\t\t\tif not (value is int or value is float) or not is_finite(float(value)): return {"error":"The imported hair authored translation is invalid."}
\t\tauthored_positions[id] = authored.position.duplicate(true)
\t# Snapshot copies include every rule state and exact size/tick/active status.
\t# The two configurations were constructed independently from immutable specs.
\tvar committed: Dictionary = _chain.snapshot()
\tif configuration_stamp(_chain) != _configuration_stamp or configuration_stamp(_trial) != _configuration_stamp: return {"error":"The imported hair simulation configuration changed."}
\tvar invalid := state_error(committed,_tick)
\tif not invalid.is_empty(): return {"error":invalid}
\tvar baseline := capture_baseline()
\tif baseline.has("error"): return baseline
\t_trial._states = committed.states.duplicate(true)
\t_trial._sizes = committed.sizes.duplicate(true)
\t_trial._tick = int(committed.tick); _trial._active = true
\tvar solved: Dictionary = _trial.step(_tick+1,baseline.locals,baseline.prefix,accelerations)
\tif solved.has("error"): return solved
\tinvalid = state_error(_trial.snapshot(),_tick+1)
\tif not invalid.is_empty(): return {"error":invalid}
\tif not solved.get("delta_bases") is Dictionary or solved.delta_bases.size() != 5: return {"error":"The imported hair solver returned an incomplete pose."}
\tvar pose := {}
\tfor index in SELECTED_NATIVE_IDS:
\t\tvar id: String = resolution.by_native[index]
\t\tif not solved.delta_bases.has(id): return {"error":"The imported hair solver missed a selected joint."}
\t\tvar check_goal := Math.goal([0.0,0.0,0.0],solved.delta_bases[id])
\t\tif check_goal.has("error"): return check_goal
\t\tvar q: Quaternion = basis64(solved.delta_bases[id]).get_rotation_quaternion().normalized()
\t\tif not is_finite(q.x) or not is_finite(q.y) or not is_finite(q.z) or not is_finite(q.w): return {"error":"The imported hair solver returned an invalid rotation."}
\t\tpose[id] = {"position":authored_positions[id].duplicate(true),"rotation_xyzw":[q.x,q.y,q.z,q.w]}
\t# This swap is the only state commit. Failure above leaves authoritative
\t# states/sizes/tick/status, authored data and visual overlays untouched.
\tvar previous: RefCounted = _chain
\t_chain = _trial; _trial = previous; _tick += 1
\tvar processing_elapsed: int = maxi(0,Time.get_ticks_usec()-processing_started)
\tprocessing_samples += 1; processing_total_usec += processing_elapsed; processing_max_usec = maxi(processing_max_usec,processing_elapsed)
\treturn {"pose":pose}

'''
    dispose = '''func dispose() -> void:
\t_alive = false
\tif _chain: _chain.stop(); _chain = null
\tif _trial: _trial.stop(); _trial = null
\t_parameters.clear(); _bone_specs.clear(); _base_scales.clear(); _size_tokens.clear(); _configuration_stamp.clear()
\t_binding_stamp.clear(); _source_header.clear(); _chain_inventory_stamp.clear(); chains.clear()
\t_tick = 0; resolution = null; actor = null; _skeleton = null

func active() -> bool:
\treturn _alive
'''
    draft = header+offered+anchors+numerical_context+create+stamp+capture+before+after+dispose
    save('source_secondary.gd',draft)
    live_path = ROOT/'src/secondary_live.gd'
    live_raw = live_path.read_bytes(); live_source = live_raw.decode('utf-8-sig')
    live_newline = '\r\n' if b'\r\n' in live_raw else '\n'
    insertion = '\t\tvar airflow_issue: String=runner.airflow_error()\n\t\tif not airflow_issue.is_empty():return airflow_issue\n'
    anchor = '\tif native_backend:\n\t\tif not recording and frame!=initial_frame:'
    anchor = anchor.replace('\n',live_newline)
    insertion = insertion.replace('\n',live_newline)
    assert live_source.count(anchor)==1
    live_draft = live_source.replace(anchor,'\tif native_backend:'+live_newline+insertion+'\t\tif not recording and frame!=initial_frame:')
    save('secondary_live.gd',live_draft)
    assert sha(BASE.read_bytes()) == BASE_SHA and sha(QUALIFIED.read_bytes()) == CHAIN_SHA
    provenance = {'format':'has_native_five_production_draft_provenance_1','status':'DRAFT_NOT_APPLIED_GDSCRIPT_UNPARSED_UNRUN',
                  'base_source':str(BASE),'base_sha256':BASE_SHA,'qualified_chain_source':str(QUALIFIED),'qualified_chain_sha256':CHAIN_SHA,
                  'source_chain_math_change':'Only preload target leaf_candidate.gd to src/source_jiggle_math.gd; all other bytes unchanged.',
                  'unchanged_blocks':['offered','vector64','basis64','frame64','context_error','binding_stamp','step source/header/stat/binding/context preamble'],
                  'selected_native_indices':[8,17,18,26,27],'selected_parent_indices':{'8':7,'17':7,'18':17,'26':25,'27':26},
                  'actual_implementation_or_runtime_claimed':False,'core_or_frozen_run_files_modified':False}
    provenance['predecessor_sealed_index_sha256'] = '08a423f3c25f8670578b24bc53465388047078acc4d140d2534a5388b3ee272a'
    provenance['v2_correction'] = 'Exact ordered public chains inventory stamp includes ids and source.joints.binding; checked before force validation or trial state transfer.'
    provenance['v2_paired_wrapper_preflight'] = 'Native.airflow_error() is called by the native SecondaryLive branch before visual/state changes or public-chain collection. Generic code remains byte-identical.'
    provenance['wrapper_source'] = str(live_path)
    provenance['wrapper_source_sha256'] = sha(live_raw)
    provenance['timing_scope'] = 'Transient successful full Native.step processing count/sum/max microseconds; future tests report mean/max without an FPS pass claim.'
    save('PROVENANCE.json',json.dumps(provenance,indent=2)+'\n')
    print(json.dumps({'prepared':True,'status':'DRAFT_NOT_APPLIED_GDSCRIPT_UNPARSED_UNRUN',
                      'source_secondary_sha256':sha((HERE/'source_secondary.gd').read_bytes()),
                      'source_chain_math_sha256':sha((HERE/'source_chain_math.gd').read_bytes())}))


if __name__ == '__main__':
    main()
