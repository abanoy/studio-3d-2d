extends SceneTree
# Static test helpers only: do not instantiate the Scenario D application script.
const Oracle=preload("res://tests/scenario_d_smoke.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
 create_timer(25).timeout.connect(func():push_error("Scenario D sample wire watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func f32(bits: int) -> float:
 var raw:=PackedByteArray();raw.resize(4);raw.encode_u32(0,bits);return raw.decode_float(0)
func next32(value: float) -> float:
 var raw:=PackedByteArray();raw.resize(4);raw.encode_float(0,value);raw.encode_u32(0,raw.decode_u32(0)+1);return raw.decode_float(0)
func adjacent64(value: float) -> float:
 var raw:=PackedByteArray();raw.resize(8);raw.encode_double(0,value);raw.encode_u64(0,raw.decode_u64(0)-1);return raw.decode_double(0)
func fixture(scale_value: float) -> Dictionary:
 return {"actor-A":{"root":{"position":[0.25,0.,0.],"rotation_xyzw":[0.25,0.,0.,1.],"scale":scale_value},"body":{"bone-A":{"position":[0.,0.5,0.],"rotation_xyzw":[0.,0.,0.,1.]}}},"enabled":true,"tag":"keep"}
func agrees(a: Dictionary,b: Dictionary) -> bool:
 var left: String=Oracle.sample_wire_stamp(a);var right: String=Oracle.sample_wire_stamp(b)
 return not left.is_empty() and left==right and Oracle.sample_f32_same(a,b)
func run() -> void:
 var original: float=f32(0x3f7ffffd);var shifted: float=adjacent64(original)
 var base: Dictionary=fixture(original);var wire_neighbor: Dictionary=fixture(shifted)
 var before: PackedByteArray=var_to_bytes(base);var neighbor_before: PackedByteArray=var_to_bytes(wire_neighbor)
 check(original!=shifted,"control starts with distinct raw float64 values constructed from exact bits")
 check(JSON.stringify(base,"",true,true)!=JSON.stringify(wire_neighbor,"",true,true),"historical raw sample text mismatch remains observable")
 check(Oracle.sample_wire_stamp(base)==Oracle.sample_wire_stamp(wire_neighbor),"one equal full-precision JSON parse domain resolves measured wire representation")
 check(Oracle.sample_f32_same(base,wire_neighbor),"independent per-field float32 bits retain the original physical sample")
 check(agrees(base,wire_neighbor),"both exact canonical text and independent physical bits are required")
 check(var_to_bytes(base)==before and var_to_bytes(wire_neighbor)==neighbor_before,"wire helpers preserve both original inputs bit-for-bit")
 var roundtrip=Oracle.sample_text_value(Oracle.sample_wire_stamp(base))
 check(roundtrip is Dictionary and Oracle.sample_wire_stamp(roundtrip)==Oracle.sample_wire_stamp(base),"measured fixture canonical stamp remains stable on reopen")
 for field in ["scale","position","quaternion"]:
  var changed: Dictionary=base.duplicate(true)
  match field:
   "scale":changed["actor-A"].root.scale=next32(original)
   "position":changed["actor-A"].root.position[0]=next32(0.25)
   "quaternion":changed["actor-A"].root.rotation_xyzw[0]=next32(0.25)
  check(not agrees(base,changed) and not Oracle.sample_f32_same(base,changed),"adjacent float32 sample change refuses: "+field)
 var same_f32: Dictionary=base.duplicate(true);same_f32["actor-A"].root.scale=original+pow(2.,-30.)
 check(Oracle.sample_f32_same(base,same_f32) and Oracle.sample_wire_stamp(base)!=Oracle.sample_wire_stamp(same_f32) and not agrees(base,same_f32),"float32 equality alone cannot hide a distinct canonical float64 sample")
 var missing: Dictionary=base.duplicate(true);missing["actor-A"].body.erase("bone-A")
 check(not agrees(base,missing),"missing bone state refuses")
 var renamed: Dictionary=base.duplicate(true);renamed["actor-B"]=renamed["actor-A"];renamed.erase("actor-A")
 check(not agrees(base,renamed),"changed actor identity refuses")
 var flag: Dictionary=base.duplicate(true);flag.enabled=1
 check(not agrees(base,flag) and not Oracle.sample_f32_same(base,flag),"boolean versus numeric identity refuses")
 var array_order: Dictionary=base.duplicate(true);array_order["actor-A"].root.position=[0.,0.25,0.]
 check(not agrees(base,array_order),"array component order remains exact")
 var array_length: Dictionary=base.duplicate(true);array_length["actor-A"].root.position.append(0.)
 check(not agrees(base,array_length),"extra array component refuses")
 var extra: Dictionary=base.duplicate(true);extra.extra="state"
 check(not agrees(base,extra),"extra sampled field refuses")
 var text: Dictionary=base.duplicate(true);text.tag="changed"
 check(not agrees(base,text),"string fields remain exact")
 var big_a: Dictionary={"count":9007199254740993};var big_b: Dictionary={"count":9007199254740992}
 check(not Oracle.sample_f32_same(big_a,big_b) and not agrees(big_a,big_b),"large integer identity is not weakened by a float conversion")
 check(not Oracle.sample_f32_same(big_a,{"count":9007199254740992.}),"lossy mixed integer/float identity refuses")
 check(Oracle.sample_f32_same({"count":3},{"count":3.}),"exact integer/float JSON number identity remains supported")
 check(Oracle.sample_wire_stamp({"bad":NAN}).is_empty() and not Oracle.sample_f32_same({"bad":NAN},{"bad":NAN}),"NaN cannot collapse into a passing null stamp")
 check(Oracle.sample_wire_stamp({"bad":INF}).is_empty() and not Oracle.sample_f32_same({"bad":INF},{"bad":INF}),"infinity refuses before JSON encoding")
 check(Oracle.sample_wire_stamp({"bad":Vector3.ONE}).is_empty(),"unsupported typed object cannot become a JSON string surrogate")
 check(Oracle.sample_text_value("{broken")==null and Oracle.sample_text_value("null")==null and Oracle.sample_text_value("[]")==null,"malformed or non-object sample text refuses without parse-string error logging")
 var unknown_key: Dictionary={1:"bad"}
 check(Oracle.sample_wire_stamp(unknown_key).is_empty(),"non-string object keys refuse")
 var deep: Dictionary={};var at: Dictionary=deep
 for i in range(18):at["next"]={};at=at.next
 check(Oracle.sample_wire_stamp(deep).is_empty(),"excessive recursive input refuses")
 check(var_to_bytes(base)==before and var_to_bytes(wire_neighbor)==neighbor_before,"negative controls also preserve original pose/root inputs")
 print("SCENARIO_D_SAMPLE_WIRE_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(1 if failures else 0)
