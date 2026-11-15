"""Minimal inline-or-omission contract; authored fixtures and CPU only."""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import time
import unittest

sys.dont_write_bytecode = True
import source_jiggle_metadata as M
from authored_fixture import authored, base_report, legacy_bytes, padded, ORIGINAL

TASK = Path(__file__).absolute().parents[1]
OUT = TASK / ("minimal-cpu-" + str(time.time_ns())); OUT.mkdir(exist_ok=False)

def inspect(raw, bones): return M.inspect(raw, ORIGINAL, hashlib.sha256(raw).hexdigest(), bones, 0.01905)

class Tests(unittest.TestCase):
    def setUp(self):
        self.raw, self.bones = authored(); self.base = base_report(self.bones); self.attempt = inspect(self.raw, self.bones)

    def plan(self, baseline, attempt, newline="\n", *, native_raw=None):
        # Expected identity comes from this fixture's frozen input bytes, not
        # from a field in the candidate metadata being tested.
        raw = self.raw if native_raw is None else native_raw
        expected = hashlib.sha256(raw).hexdigest()
        return M.plan_report(baseline, attempt, newline, expected_native_mdl_sha256=expected)

    def test_inert_values_prefix_words_and_distinct_namespaces(self):
        meta = self.attempt["metadata"]; row = meta["rules"][0]
        self.assertEqual(self.attempt["state"], "retained")
        self.assertEqual((row["native_bone_flags"], row["native_procedure_type"], row["raw_rule_flags"]), (1284, 5, 49))
        self.assertEqual((row["parameters"]["pitch_friction"], row["parameters"]["pitch_bounce"]), (-7.25, 8.5))
        self.assertEqual(len(row["parameters"]), 29)
        self.assertIs(meta["applied"], False); self.assertEqual(meta["runtime_support"], "not_implemented")
        self.assertEqual(meta["binding_status"], "unattempted"); self.assertFalse(meta["full_native_rule_layout_verified"])

    def test_original_container_and_native_mdl_hashes_remain_distinct(self):
        meta = self.attempt["metadata"]
        self.assertNotEqual(meta["original_source_sha256"], meta["native_mdl_sha256"])
        self.assertEqual(self.plan(self.base, self.attempt)["state"], "embedded")

    def test_invalid_original_or_changed_native_sha_is_integrity_error(self):
        for original, native in ((True, hashlib.sha256(self.raw).hexdigest()), ("A" * 64, hashlib.sha256(self.raw).hexdigest()), (ORIGINAL, "0" * 64)):
            with self.assertRaises(M.SourceIdentityError): M.inspect(self.raw, original, native, self.bones, 0.01905)

    def test_mismatched_identity_is_checked_before_overbudget_or_invalid_base(self):
        for baseline in (padded(self.base, M.REPORT_LIMIT + 1), {**copy.deepcopy(self.base), "existing_bad": float("nan")}):
            baseline["source_sha256"] = "0" * 64
            with self.assertRaises(M.SourceIdentityError): self.plan(baseline, self.attempt, "\r\n")

    def test_changed_native_catalogue_or_conversion_scale_cannot_be_relabelled(self):
        for change in (lambda b: b["native_parameters"]["bones"][1].update(name="other"), lambda b: b.update(scale=1.0)):
            base = copy.deepcopy(self.base); change(base)
            with self.assertRaises(ValueError): self.plan(base, self.attempt)

    def test_no_jiggle_keeps_exact_legacy_writer_without_status(self):
        raw, bones = authored(jiggle=False); baseline = base_report(bones)
        result = self.plan(baseline, inspect(raw, bones), "\r\n", native_raw=raw)
        self.assertEqual(result["state"], "unchanged"); self.assertEqual(result["report"], baseline)
        self.assertIsNone(result["report_bytes"]); self.assertIsNone(result["note_bytes"]); self.assertIsNone(result["omission"])

    def test_bsp_path_does_not_need_inspection_or_new_writer(self):
        baseline = {"native_parameters": {"props_loaded": 7}}
        result = M.plan_report(baseline, {"state": "none"})
        self.assertEqual(result["report"], baseline); self.assertIsNone(result["report_bytes"])

    def test_unsupported_layout_is_explicit_optional_omission(self):
        raw = bytearray(self.raw); struct.pack_into("<i", raw, 4, 48)
        result = self.plan(self.base, inspect(bytes(raw), self.bones), native_raw=bytes(raw))
        self.assertEqual(result["omission"]["reason"], "layout_unsupported")
        self.assertEqual(result["omission"]["candidate_state"], "not_formed")
        self.assertIsNone(result["omission"]["metadata_candidate_sha256"])
        self.assertEqual(result["report"]["native_parameters"]["bones"], self.bones)

    def test_source_context_mismatch_in_unavailable_status_is_integrity_error(self):
        raw = bytearray(self.raw); struct.pack_into("<i", raw, 4, 48)
        unavailable = inspect(bytes(raw), self.bones); baseline = copy.deepcopy(self.base); baseline["source_sha256"] = "0" * 64
        with self.assertRaises(M.SourceIdentityError): self.plan(baseline, unavailable, native_raw=bytes(raw))

    def test_parent_bool_or_wrong_parent_disables_optional_branch(self):
        for parent in (False, 1):
            bones = copy.deepcopy(self.bones); bones[1]["parent"] = parent
            self.assertEqual(inspect(self.raw, bones)["status"]["reason"], "native_inventory_mismatch")

    def test_nonfinite_and_unbounded_values_are_never_clamped(self):
        at = 408 + len(self.bones) * 216
        for number, reason in ((float("nan"), "layout_unsupported"), (float("inf"), "layout_unsupported"), (2000000.0, "metadata_value_budget")):
            raw = bytearray(self.raw); struct.pack_into("<f", raw, at + 4, number)
            attempt = inspect(bytes(raw), self.bones)
            self.assertEqual(attempt["status"]["reason"], reason); self.assertNotIn("metadata", attempt)

    def test_unknown_flag_bits_retained_without_new_motion_support(self):
        raw = bytearray(self.raw); at = 408 + len(self.bones) * 216; struct.pack_into("<I", raw, at, 0x800000B1)
        attempt = inspect(bytes(raw), self.bones)
        row = next(r for r in attempt["metadata"]["rules"] if r["binary_provenance"]["rule_absolute_offset"] == at)
        self.assertEqual(row["unknown_rule_flag_bits"], 0x80000080); self.assertEqual(len(row["parameters"]), 29)
        self.assertIs(row["applied"], False)

    def test_inputs_are_not_mutated(self):
        before = copy.deepcopy((self.base, self.attempt, self.bones))
        self.plan(self.base, self.attempt, "\r\n")
        self.assertEqual((self.base, self.attempt, self.bones), before)

    def test_windows_serialization_matches_textio_translation_exactly(self):
        value = {"native_parameters": {"word": "初音ミク"}, "line": "a\nb"}
        for newline in ("\n", "\r\n"): self.assertEqual(M.report_bytes(value, newline), legacy_bytes(value, newline))
        self.assertNotIn(b"\r\r\n", M.report_bytes(value, "\r\n"))

    def test_final_nested_report_inclusive256KiB_boundary(self):
        baseline = padded(self.base, M.REPORT_LIMIT, self.attempt["metadata"])
        result = self.plan(baseline, self.attempt, "\r\n")
        self.assertEqual(result["state"], "embedded"); self.assertEqual(len(result["report_bytes"]), 262144)
        self.assertEqual(result["report_bytes"], legacy_bytes(result["report"]))

    def test_one_byte_over_report_cap_omits_entire_metadata_with_exact_digest_counts(self):
        baseline = padded(self.base, M.REPORT_LIMIT + 1, self.attempt["metadata"])
        result = self.plan(baseline, self.attempt, "\r\n"); status = result["omission"]
        candidate = json.dumps(self.attempt["metadata"], ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"
        self.assertEqual(result["state"], "omitted_status_inline")
        self.assertLessEqual(len(result["report_bytes"]), 262144)
        self.assertEqual((status["reason"], status["retained_rule_count"], status["rule_count"]), ("report_budget", 0, 2))
        self.assertEqual(status["metadata_candidate_sha256"], hashlib.sha256(candidate).hexdigest())
        self.assertEqual(status["metadata_candidate_bytes"], len(candidate))
        self.assertEqual(status["full_report_candidate_bytes"], 262145)
        self.assertNotIn("rules", result["report"]["native_parameters"][M.KEY])

    def test_no_status_headroom_keeps_original_bytes_and_bounded_log_reason(self):
        baseline = padded(self.base, M.REPORT_LIMIT)
        result = self.plan(baseline, self.attempt, "\r\n")
        self.assertEqual(result["state"], "omitted_log_only"); self.assertEqual(result["report"], baseline)
        self.assertIsNone(result["report_bytes"]); self.assertNotIn(M.KEY, result["report"]["native_parameters"])
        self.assertLessEqual(len(result["note_bytes"]), 4096)
        self.assertEqual(json.loads(result["note_bytes"])["metadata_candidate_sha256"], result["omission"]["metadata_candidate_sha256"])

    def test_preexisting_oversize_or_invalid_report_is_not_compacted_or_sanitized(self):
        large = padded(self.base, M.REPORT_LIMIT + 1)
        result = self.plan(large, self.attempt, "\r\n")
        self.assertIsNone(result["report_bytes"]); self.assertEqual(result["report"], large)
        self.assertEqual(result["omission"]["reason"], "baseline_report_over_budget")
        invalid = copy.deepcopy(self.base); invalid["bad"] = float("nan")
        result = self.plan(invalid, self.attempt)
        self.assertIsNone(result["report_bytes"]); self.assertEqual(result["omission"]["reason"], "baseline_unserializable")

    def test_metadata128KiB_overflow_reports_candidate_not_partial_rules(self):
        raw, bones = authored(128, name_length=220)
        attempt = inspect(raw, bones); status = attempt["status"]
        self.assertEqual(status["reason"], "metadata_budget"); self.assertGreater(status["metadata_candidate_bytes"], 131072)
        self.assertEqual(status["rule_count"], 128); self.assertRegex(status["metadata_candidate_sha256"], "^[0-9a-f]{64}$")
        result = self.plan(base_report(bones), attempt, native_raw=raw)
        self.assertEqual(result["omission"]["retained_rule_count"], 0); self.assertNotIn("rules", result["report"]["native_parameters"][M.KEY])

    def test_rule_count_overflow_is_explicit_without_a_truncated_candidate(self):
        raw, bones = authored(129); attempt = inspect(raw, bones)
        self.assertEqual(attempt["state"], "unavailable"); self.assertNotIn("metadata", attempt)
        self.assertEqual(attempt["status"]["declared_jiggle_rule_count"], 129)

    def test_tampered_activation_binding_bool_ids_nan_or_prefix_hash_rejected(self):
        for mutate in (lambda m: m.update(applied=True), lambda m: m.update(runtime_support="native"), lambda m: m["rules"][0].update(binding_status="bound"),
            lambda m: m["rules"][0].update(native_bone_index=True), lambda m: m["rules"][0]["parameters"].update(length=True),
            lambda m: m["rules"][0]["parameters"].update(length=float("nan")), lambda m: m["rules"][0]["binary_provenance"].update(prefix_sha256="0" * 64)):
            attempt = copy.deepcopy(self.attempt); mutate(attempt["metadata"])
            with self.assertRaises(ValueError): self.plan(self.base, attempt)

    def test_no_sidecar_or_confirmation_API_and_no_physics_mutation_fields(self):
        self.assertFalse(hasattr(M, "confirm_artifacts")); self.assertFalse(hasattr(M, "METADATA_FILE"))
        result = self.plan(self.base, self.attempt)
        self.assertNotIn("artifacts", result)
        self.assertEqual(set(result["report"]["native_parameters"]) - set(self.base["native_parameters"]), {M.KEY})
        self.assertFalse(any(name == "SourceIO" or name.startswith("SourceIO.") or name == "bpy" for name in sys.modules))


    def test_surrogate_imported_name_is_explicit_optional_inventory_mismatch(self):
        bones = copy.deepcopy(self.bones); bones[0]["name"] = "bad\ud800"
        before = copy.deepcopy(bones)
        attempt = inspect(self.raw, bones)
        self.assertEqual((attempt["state"], attempt["status"]["reason"]), ("unavailable", "native_inventory_mismatch"))
        self.assertNotIn("metadata", attempt); self.assertEqual(bones, before)
        result = self.plan(self.base, attempt)
        self.assertEqual(result["state"], "omitted_status_inline")
        self.assertEqual(result["omission"]["retained_rule_count"], 0)
        self.assertEqual(result["report"]["native_parameters"]["bones"], self.bones)

    def test_publication_requires_independently_frozen_native_sha_before_fallback(self):
        expected = hashlib.sha256(self.raw).hexdigest()
        poisoned = copy.deepcopy(self.attempt); poisoned["metadata"]["native_mdl_sha256"] = "0" * 64
        for baseline in (self.base, padded(self.base, M.REPORT_LIMIT + 1), {**copy.deepcopy(self.base), "bad": float("nan")}):
            with self.assertRaises(M.SourceIdentityError):
                M.plan_report(baseline, poisoned, expected_native_mdl_sha256=expected)
        for context in (None, "0" * 64, True):
            with self.assertRaises(M.SourceIdentityError):
                M.plan_report(self.base, self.attempt, expected_native_mdl_sha256=context)
        raw = bytearray(self.raw); struct.pack_into("<i", raw, 4, 48)
        raw = bytes(raw); expected_unavailable = hashlib.sha256(raw).hexdigest()
        unavailable = inspect(raw, self.bones)
        unavailable["status"]["native_mdl_sha256"] = "0" * 64
        with self.assertRaises(M.SourceIdentityError):
            M.plan_report(padded(self.base, M.REPORT_LIMIT + 1), unavailable, expected_native_mdl_sha256=expected_unavailable)
        # Altering only the inspection cannot alter this trusted caller value.
        self.assertEqual(expected, hashlib.sha256(self.raw).hexdigest())

    def test_metadata_scale_rejects_bool_nonfinite_and_invalid_numeric_values(self):
        baseline = copy.deepcopy(self.base); baseline["scale"] = 1.0
        attempt = M.inspect(self.raw, ORIGINAL, hashlib.sha256(self.raw).hexdigest(), self.bones, 1.0)
        self.assertEqual(self.plan(baseline, attempt)["state"], "embedded")
        for value in (True, False, float("nan"), float("inf"), 0.0, -1.0, 1000001.0):
            poisoned = copy.deepcopy(attempt); poisoned["metadata"]["source_scale"] = value
            for base in (baseline, padded(baseline, M.REPORT_LIMIT + 1)):
                with self.assertRaises(ValueError): self.plan(base, poisoned)

if __name__ == "__main__":
    paths = (Path(__file__), Path(M.__file__), Path(M.Raw.__file__), Path(__file__).with_name("authored_fixture.py"))
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    unchanged = all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest for path, digest in before.items())
    report = {"format": "has_minimal_inert_jiggle_adapter_cpu_1", "checks": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "passed": result.wasSuccessful() and unchanged, "source_sha256_before_after": before, "sources_unchanged": unchanged,
        "fixtures": "Self-authored native bytes and baseline reports only", "native_SourceIO_runtime_converter_GPU_import_or_launch": False,
        "actual_Junko_full_report_fit_adoption": "UNRUN_requires_fresh_conversion", "main_or_Git_changed": False, "run": str(OUT)}
    (OUT / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("checks", "failures", "errors", "passed", "run")}))
    raise SystemExit(0 if report["passed"] else 1)
