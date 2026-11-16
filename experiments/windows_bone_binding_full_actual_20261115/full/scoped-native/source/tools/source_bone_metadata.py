"""Compact inactive export crosswalk, deterministic integer wire and report fit.

No native rest arrays or geometry enter this metadata. The existing jiggle plan
has priority; refusal preserves its exact report bytes and produces only a small
log note. Hashes describe observed evidence, not a native solver or authentication.
"""
import copy
import hashlib
import math
import re
import struct

import source_jiggle_metadata as J
import source_jiggle_crosswalk as C

KEY = "source_export_crosswalk"
FORMAT = "studio_source_bone_crosswalk_1"
PROFILE = "junko_hair_mdl49_fe242_blender51_1"
SCALE = .01905
METADATA_LIMIT = 32 * 1024
MAX_REST_ERROR = 2e-5
SHA_FIELDS = ("original_source_sha256", "native_mdl_sha256", "glb_sha256",
              "native_bone_catalogue_sha256", "jiggle_wire_sha256")


def _sha(value):
    return type(value) is str and re.fullmatch("[0-9a-f]{64}", value) is not None


def _integer(value, minimum=0, maximum=0x7fffffff):
    C.require(type(value) is int and minimum <= value <= maximum, "crosswalk_integer_domain")
    return str(value)


def _name(value):
    C.require(type(value) is str and 0 < len(value) < 63 and
              all(0x20 <= ord(ch) <= 0x7e for ch in value), "crosswalk_ASCII_name_domain")
    return value


def jiggle_wire_sha256(metadata, native_bones):
    # Reconstructs every prefix and all29 named float32 words before hashing.
    J._inert(metadata, native_bones)
    rules = sorted(metadata["rules"], key=lambda row: row["native_bone_index"])
    lines = ["studio_source_jiggle_binding_1\n",
             "native_mdl_sha256="+metadata["native_mdl_sha256"]+"\n",
             "native_bone_count="+_integer(metadata["native_bone_count"])+"\n",
             "rule_count="+_integer(len(rules))+"\n"]
    for row in rules:
        prefix = row["binary_provenance"]
        values = (_integer(row["native_bone_index"]), _integer(row["native_parent_index"], -1),
                  _name(row["native_bone_name"]), _integer(row["native_bone_flags"], maximum=0xffffffff),
                  _integer(row["native_procedure_type"], maximum=0xffffffff),
                  _integer(row["raw_rule_flags"], maximum=0xffffffff), prefix["prefix_sha256"])
        lines.append("rule="+"\t".join(values)+"\n")
        lines.append("words="+"\t".join(_integer(word, maximum=0xffffffff)
                     for word in prefix["float32_words_uint32"])+"\n")
    return hashlib.sha256("".join(lines).encode("ascii")).hexdigest()


def proof_wire_bytes(metadata):
    """Shared Python/GDS wire: LF ASCII, decimal integers, no floating fields.

    Header; five SHA_FIELDS lines in that exact order; native_bone_count line;
    native-index-sorted bone=index TAB parent TAB gltfNode TAB name TAB skinCount;
    sorted unique skin=skinIndex TAB jointSlot lines immediately after each bone.
    JSON consumers normalize integral parsed numbers before calling this contract.
    """
    C.require(type(metadata) is dict and type(metadata.get("bones")) is list and
              len(metadata["bones"]) == metadata.get("native_bone_count") == 69,
              "complete_crosswalk_count")
    lines = ["studio_source_bone_crosswalk_binding_1\n"]
    for key in SHA_FIELDS:
        C.require(_sha(metadata.get(key)), "crosswalk_SHA_domain")
        lines.append(key+"="+metadata[key]+"\n")
    lines.append("native_bone_count=69\n")
    indices = []; nodes = []; names = []
    for row in sorted(metadata["bones"], key=lambda row: row["native_index"]):
        C.require(type(row) is dict and set(row) == {"native_index", "native_name", "native_parent_index",
                  "gltf_node_index", "skin_memberships"}, "crosswalk_row_fields")
        index = row["native_index"]; parent = row["native_parent_index"]
        index_text = _integer(index, maximum=68); parent_text = _integer(parent, -1, 68)
        C.require(index != parent, "crosswalk_self_parent")
        node = _integer(row["gltf_node_index"]); name = _name(row["native_name"])
        memberships = row["skin_memberships"]
        C.require(type(memberships) is list and 1 <= len(memberships) <= 128,
                  "crosswalk_membership_count")
        tuples = []
        for member in memberships:
            C.require(type(member) is dict and set(member) == {"skin_index", "joint_slot"}, "crosswalk_membership_fields")
            _integer(member["skin_index"]); _integer(member["joint_slot"])
            tuples.append((member["skin_index"], member["joint_slot"]))
        C.require(len(set(tuples)) == len(tuples), "crosswalk_membership_duplicate")
        lines.append("bone="+"\t".join((index_text, parent_text, node, name, str(len(tuples))))+"\n")
        lines.extend("skin="+str(skin)+"\t"+str(slot)+"\n" for skin, slot in sorted(tuples))
        indices.append(index); nodes.append(row["gltf_node_index"]); names.append(name)
    C.require(indices == list(range(69)) and len(set(nodes)) == len(set(names)) == 69,
              "complete_injective_crosswalk")
    return "".join(lines).encode("ascii")


def compact_metadata(observed, report, jiggle):
    """Whitelist an entirely observed proof; discard private rest arrays in RAM."""
    native = report["native_parameters"]; bones = native["bones"]
    J._inert(jiggle, bones)
    if observed.get("native_mdl_sha256") != jiggle["native_mdl_sha256"] or \
            report.get("source_sha256") != jiggle["original_source_sha256"]:
        raise C.SourceIdentityError("crosswalk_original_native_identity_differs")
    C.require(observed.get("native_mdl_sha256") == C.JUNKO_SHA256 and
              observed.get("native_bone_count") == len(bones) == 69 and len(jiggle["rules"]) == 49 and
              observed.get("source_scale") == report.get("scale") == jiggle["source_scale"] == SCALE and
              observed.get("status") == "observed_inactive" and observed.get("applied") is False and
              observed.get("HAS_runtime_binding") == "unattempted" and observed.get("native_simulation") is False and
              observed.get("export_extras") is False, "unqualified_crosswalk_profile")
    C.require(type(observed.get("bones")) is list and len(observed["bones"]) == 69,
              "complete_observed_crosswalk")
    projected = []; errors = []
    for row in observed["bones"]:
        projected.append({key: copy.deepcopy(row[key]) for key in
                          ("native_index", "native_name", "native_parent_index", "gltf_node_index", "skin_memberships")})
        error = row["maximum_reference_matrix_error"]
        C.require(type(error) in (int, float) and math.isfinite(error) and 0 <= error <= MAX_REST_ERROR,
                  "crosswalk_absolute_rest_error_profile")
        errors.append(float(error))
    projected.sort(key=lambda row: row["native_index"])
    C.require([{ "name": row["native_name"], "parent": row["native_parent_index"] } for row in projected] == bones,
              "crosswalk_complete_native_catalogue_join")
    C.require(hashlib.sha256(J._compact(bones)).hexdigest() == jiggle["native_bone_catalogue_sha256"],
              "crosswalk_native_catalogue_SHA")
    metadata = {"format": FORMAT, "status": "retained_inert", "applied": False,
                "runtime_binding": "unattempted", "native_solver": "not_implemented", "profile": PROFILE,
                "sourceio_revision": J.SOURCEIO_REVISION,
                "sourceio_source_catalogue_sha256": hashlib.sha256(C.compact(C.SOURCEIO_PINS)).hexdigest(),
                "exporter_source_catalogue_sha256": hashlib.sha256(C.compact(C.EXPORTER_PINS)).hexdigest(),
                "original_source_sha256": jiggle["original_source_sha256"],
                "native_mdl_sha256": jiggle["native_mdl_sha256"], "glb_sha256": observed["glb_sha256"],
                "native_bone_catalogue_sha256": jiggle["native_bone_catalogue_sha256"],
                "jiggle_wire_sha256": jiggle_wire_sha256(jiggle, bones), "source_scale": SCALE,
                "native_bone_count": 69, "bones": projected, "max_rest_matrix_error": max(errors),
                "observed_proof_sha256": hashlib.sha256(C.compact(observed)).hexdigest()}
    metadata["proof_sha256"] = hashlib.sha256(proof_wire_bytes(metadata)).hexdigest()
    C.require(len(C.compact(metadata)) <= METADATA_LIMIT, "compact_crosswalk_metadata_budget")
    return metadata


def omission(reason):
    # Only fixed admission codes are emitted, never raw host paths/error text.
    allowed = {"unsupported_profile", "source_pins_unsupported", "proof_unavailable",
               "jiggle_not_retained", "report_budget", "compact_metadata_budget"}
    C.require(reason in allowed, "unknown_crosswalk_omission")
    encoded = C.compact({"format": FORMAT, "status": "omitted", "reason": reason, "applied": False,
                         "runtime_binding": "unattempted", "native_solver": "not_implemented"})
    C.require(len(encoded) <= J.STATUS_LIMIT, "crosswalk_omission_budget")
    return encoded


def plan_report(jiggle_plan, observed, *, expected_original_sha256, expected_native_sha256,
                expected_glb_sha256, newline="\n"):
    """Append only to a completed jiggle plan and measure the whole final report."""
    base = jiggle_plan["report"]
    # Independent identity checks run before missing metadata or size fallback.
    if not all(_sha(value) for value in (expected_original_sha256, expected_native_sha256, expected_glb_sha256)) or \
            base.get("source_sha256") != expected_original_sha256 or \
            observed.get("native_mdl_sha256") != expected_native_sha256 or \
            observed.get("glb_sha256") != expected_glb_sha256:
        raise C.SourceIdentityError("crosswalk_expected_source_or_GLB_identity_differs")
    def refused(reason):
        return {**jiggle_plan, "crosswalk_note_bytes": omission(reason)}
    native = base.get("native_parameters", {})
    jiggle = native.get(J.KEY, {})
    if jiggle_plan["state"] != "embedded": return refused("jiggle_not_retained")
    C.require(KEY not in native, "crosswalk_already_present")
    try:
        metadata = compact_metadata(observed, base, jiggle)
        candidate = copy.deepcopy(base); candidate["native_parameters"][KEY] = metadata
        encoded = J.report_bytes(candidate, newline)
    except C.SourceIdentityError:
        raise
    except (C.CrosswalkError, ValueError, TypeError, KeyError, OverflowError):
        return refused("proof_unavailable")
    if len(encoded) > J.REPORT_LIMIT: return refused("report_budget")
    return {**jiggle_plan, "report": candidate, "report_bytes": encoded, "crosswalk_note_bytes": None}
