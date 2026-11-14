"""Authored adapter semantics/budget tests, no native/converter/runtime imports."""
import copy
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import time
import unittest

sys.dont_write_bytecode = True
import source_jiggle_metadata as M

TASK = Path(__file__).absolute().parents[1]
OUT = TASK / ("cpu-" + str(time.time_ns())); OUT.mkdir(exist_ok=False)
ORIGINAL = hashlib.sha256(b"authored original archive identity").hexdigest()

def authored(count=2, jiggle=True, name_length=12):
    bones = count + 1; start = 408; end = start + bones * 216
    payload_end = end + count * 120
    names = [(("bone%03d_" % i) + "x" * name_length)[:name_length] for i in range(bones)]
    raw = bytearray(payload_end + sum(len(n) + 1 for n in names))
    raw[:4] = b"IDST"; struct.pack_into("<iI", raw, 4, 49, 0x1234)
    struct.pack_into("<I", raw, 76, len(raw)); struct.pack_into("<2I", raw, 156, bones, start)
    pointer = payload_end
    for i, name in enumerate(names):
        at = start + i * 216; encoded = name.encode("ascii")
        struct.pack_into("<2i", raw, at, pointer - at, -1 if i == 0 else 0)
        raw[pointer:pointer + len(encoded) + 1] = encoded + b"\0"; pointer += len(encoded) + 1
        target = end + (count - i) * 120 if i else 0
        struct.pack_into("<3I", raw, at + 160, 1284, 5 if i and jiggle else 0, target - at if i and jiggle else 0)
        if i:
            values = [float(j) for j in range(29)]; values[15], values[16] = -7.25, 8.5
            struct.pack_into("<i29f", raw, target, 0x31, *values)
    native_bones = [{"name": name, "parent": -1 if i == 0 else 0} for i, name in enumerate(names)]
    return bytes(raw), native_bones

def legacy_bytes(value, newline="\r\n"):
    buffer = io.BytesIO()
    stream = io.TextIOWrapper(buffer, encoding="utf-8", newline=newline)
    stream.write(json.dumps(value, ensure_ascii=True, indent=2)); stream.flush()
    raw = buffer.getvalue(); stream.detach(); return raw

def base_report(bones):
    return {"source_sha256": ORIGINAL, "source_file": "authored.mdl", "native_parameters": {"bones": copy.deepcopy(bones), "selected_skin": 0}, "warnings": [], "limits": ["existing static limitation"], "padding": ""}

def inspect(raw=None, bones=None):
    if raw is None: raw, bones = authored()
    return M.inspect(raw, ORIGINAL, hashlib.sha256(raw).hexdigest(), bones, 0.01905)

def padded(base, target, metadata=None):
    result = copy.deepcopy(base)
    candidate = copy.deepcopy(result)
    if metadata is not None: candidate["native_parameters"][M.KEY] = metadata
    count = target - len(legacy_bytes(candidate))
    assert count >= 0
    result["padding"] = "x" * count
    return result

class Tests(unittest.TestCase):
    def setUp(self):
        self.raw, self.bones = authored(); self.attempt = inspect(self.raw, self.bones); self.base = base_report(self.bones)

    def test_exact_inert_metadata_namespaces_and_binary_fields(self):
        value = self.attempt["metadata"]; rule = value["rules"][0]
        self.assertEqual(self.attempt["state"], "retained")
        self.assertIs(value["applied"], False); self.assertEqual(value["runtime_support"], "not_implemented")
        self.assertEqual(value["binding_status"], "unattempted"); self.assertFalse(value["full_native_rule_layout_verified"])
        self.assertEqual((rule["native_bone_flags"], rule["native_procedure_type"], rule["raw_rule_flags"]), (1284, 5, 49))
        self.assertEqual(rule["parameters"]["pitch_friction"], -7.25); self.assertEqual(rule["parameters"]["pitch_bounce"], 8.5)
        self.assertEqual(len(rule["parameters"]), 29)

    def test_original_archive_hash_is_distinct_from_native_mdl_hash(self):
        value = self.attempt["metadata"]
        self.assertNotEqual(value["original_source_sha256"], value["native_mdl_sha256"])
        self.assertEqual(M.plan_report(self.base, self.attempt)["state"], "embedded")

    def test_changed_native_hash_is_integrity_error_not_optional_success(self):
        with self.assertRaises(M.SourceIdentityError): M.inspect(self.raw, ORIGINAL, "0" * 64, self.bones, 1.0)

    def test_invalid_original_hash_is_integrity_error(self):
        for value in (True, None, "A" * 64, "0" * 63):
            with self.assertRaises(M.SourceIdentityError): M.inspect(self.raw, value, hashlib.sha256(self.raw).hexdigest(), self.bones, 1.0)

    def test_no_jiggle_preserves_baseline_and_no_artifact_writer_path(self):
        raw, bones = authored(jiggle=False); baseline = base_report(bones); before = copy.deepcopy(baseline)
        result = M.plan_report(baseline, inspect(raw, bones), "\r\n")
        self.assertEqual(result["state"], "unchanged"); self.assertEqual(result["report"], before)
        self.assertIsNone(result["report_bytes"]); self.assertIsNone(result["status_bytes"])
        self.assertEqual(result["artifacts"], {}); self.assertEqual(result["notes"], []); self.assertEqual(baseline, before)

    def test_bsp_absent_branch_remains_opaque_baseline(self):
        base = {"native_parameters": {"props_loaded": 4}, "warnings": []}
        result = M.plan_report(base, {"state": "none"})
        self.assertEqual(result["report"], base); self.assertIsNone(result["report_bytes"])

    def test_unsupported_layout_does_not_change_static_fields(self):
        raw = bytearray(self.raw); struct.pack_into("<i", raw, 4, 48)
        result = M.plan_report(self.base, inspect(bytes(raw), self.bones))
        self.assertEqual(result["report"]["native_parameters"][M.KEY]["reason"], "layout_unsupported")
        self.assertEqual(result["report"]["native_parameters"]["bones"], self.base["native_parameters"]["bones"])

    def test_bad_parent_inventory_and_bool_parent_not_admitted(self):
        for value in (1, False):
            bones = copy.deepcopy(self.bones); bones[1]["parent"] = value
            self.assertEqual(inspect(self.raw, bones)["status"]["reason"], "native_inventory_mismatch")

    def test_nonfinite_and_large_native_values_never_clamped(self):
        at = 408 + len(self.bones) * 216
        for value, reason in ((float("nan"), "layout_unsupported"), (float("inf"), "layout_unsupported"), (2000000.0, "metadata_value_budget")):
            raw = bytearray(self.raw); struct.pack_into("<f", raw, at + 4, value)
            attempt = inspect(bytes(raw), self.bones)
            self.assertEqual(attempt["state"], "unavailable"); self.assertEqual(attempt["status"]["reason"], reason)
            self.assertNotIn("metadata", attempt)

    def test_unknown_bits_are_retained_unapplied_without_boing_fields(self):
        raw = bytearray(self.raw); at = 408 + len(self.bones) * 216; struct.pack_into("<I", raw, at, 0x800000B1)
        attempt = inspect(bytes(raw), self.bones)
        self.assertEqual(attempt["state"], "retained")
        rule = next(r for r in attempt["metadata"]["rules"] if r["binary_provenance"]["rule_absolute_offset"] == at)
        self.assertEqual(rule["unknown_rule_flag_bits"], 0x80000080); self.assertEqual(len(rule["parameters"]), 29)
        self.assertFalse(rule["applied"])

    def test_all_three_caller_inputs_unchanged(self):
        baseline = copy.deepcopy(self.base); attempt = copy.deepcopy(self.attempt); bones = copy.deepcopy(self.bones)
        M.plan_report(self.base, self.attempt, "\r\n")
        self.assertEqual(self.base, baseline); self.assertEqual(self.attempt, attempt); self.assertEqual(self.bones, bones)

    def test_windows_bytes_match_actual_textio_translation_not_lf_measurement(self):
        value = {"native_parameters": {"word": "初音ミク"}, "line": "a\nb"}
        self.assertEqual(M.report_bytes(value, "\r\n"), legacy_bytes(value, "\r\n"))
        self.assertEqual(M.report_bytes(value, "\n"), legacy_bytes(value, "\n"))
        self.assertGreater(len(M.report_bytes(value, "\r\n")), len(M.report_bytes(value, "\n")))
        self.assertNotIn(b"\r\r\n", M.report_bytes(value, "\r\n"))

    def test_full_nested_report_exact_inclusive256KiB_boundary(self):
        baseline = padded(self.base, M.REPORT_LIMIT, self.attempt["metadata"])
        result = M.plan_report(baseline, self.attempt, "\r\n")
        self.assertEqual(result["state"], "embedded"); self.assertEqual(len(result["report_bytes"]), 262144)
        self.assertEqual(result["report_bytes"], legacy_bytes(result["report"]))

    def test_one_byte_over_fullreport_becomes_external_only_not_truncated(self):
        baseline = padded(self.base, M.REPORT_LIMIT + 1, self.attempt["metadata"])
        result = M.plan_report(baseline, self.attempt, "\r\n")
        self.assertEqual(result["state"], "external_pending_confirmation")
        self.assertLessEqual(len(result["report_bytes"]), M.REPORT_LIMIT)
        status = result["report"]["native_parameters"][M.KEY]
        self.assertEqual(status["retention"], "external_bundle_only_unmanaged")
        stored = json.loads(result["artifacts"][M.METADATA_FILE])
        self.assertEqual(stored, self.attempt["metadata"]); self.assertEqual(len(stored["rules"]), 2)
        self.assertEqual(status["external_metadata"]["packed_project_retention"], "not_managed")

    def test_status_itself_cannot_fit_preserves_original_exact_report(self):
        baseline = padded(self.base, M.REPORT_LIMIT)
        result = M.plan_report(baseline, self.attempt, "\r\n")
        self.assertIsNone(result["report_bytes"]); self.assertEqual(result["report"], baseline)
        self.assertNotIn(M.KEY, result["report"]["native_parameters"])
        self.assertLessEqual(len(result["status_bytes"]), 4096)
        self.assertEqual(json.loads(result["status_bytes"])["reason"], "report_budget")

    def test_existing_overbudget_base_not_misreported_fixed_or_trimmed(self):
        baseline = padded(self.base, M.REPORT_LIMIT + 1)
        result = M.plan_report(baseline, self.attempt, "\r\n")
        self.assertEqual(result["report"], baseline); self.assertIsNone(result["report_bytes"])
        self.assertEqual(json.loads(result["status_bytes"])["reason"], "baseline_report_over_budget")

    def test_unserializable_base_not_silently_sanitized(self):
        baseline = copy.deepcopy(self.base); baseline["existing"] = float("nan")
        result = M.plan_report(baseline, self.attempt)
        self.assertIsNone(result["report_bytes"]); self.assertEqual(json.loads(result["status_bytes"])["reason"], "baseline_unserializable")

    def test_metadata128KiB_overflow_has_status_only_and_no_partial_rule_array(self):
        raw, bones = authored(128, name_length=220)
        attempt = inspect(raw, bones)
        self.assertEqual(attempt["state"], "unavailable"); self.assertEqual(attempt["status"]["reason"], "metadata_budget")
        result = M.plan_report(base_report(bones), attempt)
        self.assertEqual(result["artifacts"], {}); self.assertNotIn("rules", result["report"]["native_parameters"][M.KEY])

    def test_metadata_rule_count_overflow_not_silently_truncated(self):
        raw, bones = authored(129)
        attempt = inspect(raw, bones)
        self.assertEqual(attempt["state"], "unavailable"); self.assertNotIn("metadata", attempt)

    def external(self):
        return M.plan_report(padded(self.base, M.REPORT_LIMIT + 1, self.attempt["metadata"]), self.attempt, "\r\n")

    def test_external_metadata_requires_exact_actual_write_receipt(self):
        result = self.external(); payload = result["artifacts"][M.METADATA_FILE]
        receipt = {M.METADATA_FILE: {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}}
        final = M.confirm_artifacts(result, receipt)
        self.assertEqual(final["state"], "external_confirmed"); self.assertEqual(final["artifacts"], {})
        self.assertEqual(json.loads(final["status_bytes"])["external_metadata"]["sha256"], receipt[M.METADATA_FILE]["sha256"])

    def test_missing_wrong_sha_or_bool_size_cannot_claim_external_retention(self):
        for receipts in ({}, {M.METADATA_FILE: {"sha256": "0" * 64, "bytes": 1}}, {M.METADATA_FILE: {"sha256": "0" * 64, "bytes": True}}):
            final = M.confirm_artifacts(self.external(), receipts)
            status = json.loads(final["status_bytes"])
            self.assertEqual(status["reason"], "sidecar_not_published"); self.assertNotIn("external_metadata", status)
            self.assertEqual(final["artifacts"], {})

    def test_tampered_activation_binding_bool_index_or_values_refused(self):
        for mutation in (lambda m: m.update(applied=True), lambda m: m.update(runtime_support="native"),
                         lambda m: m["rules"][0].update(binding_status="bound"), lambda m: m["rules"][0].update(native_bone_index=True),
                         lambda m: m["rules"][0]["parameters"].update(length=True), lambda m: m["rules"][0]["parameters"].update(length=float("nan")),
                         lambda m: m["rules"][0]["binary_provenance"].update(prefix_sha256="0" * 64)):
            attempt = copy.deepcopy(self.attempt); mutation(attempt["metadata"])
            with self.assertRaises(ValueError): M.plan_report(self.base, attempt)

    def test_original_report_and_native_catalogue_context_cannot_be_relabelled(self):
        baseline = copy.deepcopy(self.base); baseline["source_sha256"] = self.attempt["metadata"]["native_mdl_sha256"]
        with self.assertRaises(M.SourceIdentityError): M.plan_report(baseline, self.attempt)
        baseline = copy.deepcopy(self.base); baseline["native_parameters"]["bones"][1]["name"] = "different"
        with self.assertRaises(ValueError): M.plan_report(baseline, self.attempt)

    def test_unknown_publication_state_and_fake_failure_activation_refused(self):
        with self.assertRaises(ValueError): M.plan_report(self.base, {"state": "guessed"})
        attempt = {"state": "unavailable", "status": {"reason": "layout_unsupported", "applied": True}}
        with self.assertRaises(ValueError): M.plan_report(self.base, attempt)

    def test_no_secondary_rig_hairclothes_or_runtime_sourceio_import(self):
        result = M.plan_report(self.base, self.attempt)
        self.assertEqual(set(result["report"]["native_parameters"]) - set(self.base["native_parameters"]), {M.KEY})
        self.assertFalse(any(name == "SourceIO" or name.startswith("SourceIO.") or name == "bpy" for name in sys.modules))

if __name__ == "__main__":
    protected = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(M.__file__), Path(M.Raw.__file__), Path(__file__))}
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    unchanged = all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == sha for path, sha in protected.items())
    report = {"format": "has_inert_jiggle_adapter_cpu_1", "checks": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "passed": result.wasSuccessful() and unchanged, "sources_sha256_before_after": protected, "sources_unchanged": unchanged,
        "native_files_SourceIO_Blender_Godot_GPU_imported_or_launched": False, "actual_Junko_full_report_fit": "UNRUN_requires_fresh_conversion",
        "main_source_or_Git_mutated": False, "run": str(OUT)}
    (OUT / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("checks", "failures", "errors", "passed", "run")}))
    raise SystemExit(0 if report["passed"] else 1)
