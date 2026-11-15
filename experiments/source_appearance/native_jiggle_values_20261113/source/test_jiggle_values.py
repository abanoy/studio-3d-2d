"""Authored byte fixtures only: no native reader import or physics tools."""
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
import jiggle_values as J

TASK = Path(__file__).absolute().parents[1]
OUT = TASK / ("cpu-" + str(time.time_ns())); OUT.mkdir(exist_ok=False)

def authored():
    # Three records, two disjoint prefixes deliberately reversed in bone order.
    raw = bytearray(1400); raw[:4] = b"IDST"
    struct.pack_into("<iI", raw, 4, 49, 0x12345678)
    struct.pack_into("<I", raw, 76, len(raw))
    struct.pack_into("<2I", raw, 156, 3, 408)
    for index, (name, parent, target) in enumerate(((b"first", 2, 1176), (b"second", 0, 1056), (b"root", -1, 0))):
        at = 408 + index * 216; name_at = 1320 + index * 10
        struct.pack_into("<2i", raw, at, name_at - at, parent)
        raw[name_at:name_at + len(name) + 1] = name + b"\0"
        struct.pack_into("<3I", raw, at + 160, 1284, 5 if target else 0, target - at if target else 0)
        if target:
            values = [float(i + index * 40) for i in range(29)]
            values[15], values[16] = -7.25 - index, 8.5 + index
            struct.pack_into("<i29f", raw, target, 0x31, *values)
    return raw

class Tests(unittest.TestCase):
    def reject(self, edit, pattern=None):
        raw = authored(); edit(raw)
        if pattern:
            with self.assertRaisesRegex(J.DecodeError, pattern): J.parse(bytes(raw))
        else:
            with self.assertRaises(J.DecodeError): J.parse(bytes(raw))

    def test_handcomputed_values_offsets_flags_and_nonmonotonic_parent_order(self):
        report = J.parse(bytes(authored())); a, b = report["rules"]
        self.assertEqual((report["bone_count"], len(report["rules"])), (3, 2))
        self.assertEqual((a["index"], a["parent"], a["payload_offset"]), (0, 2, 1176))
        self.assertEqual((b["index"], b["parent"], b["payload_offset"]), (1, 0, 1056))
        self.assertEqual(a["parameters"]["pitch_friction"], -7.25)
        self.assertEqual(a["parameters"]["pitch_bounce"], 8.5)
        self.assertEqual(a["parameters"]["base_forward_friction"], 28.0)
        self.assertEqual(a["known_flags"], ["IS_FLEXIBLE", "HAS_ANGLE_CONSTRAINT", "HAS_LENGTH_CONSTRAINT"])
        self.assertEqual(a["prefix_sha256"], hashlib.sha256(bytes(authored())[1176:1296]).hexdigest())

    def test_bad_magic(self): self.reject(lambda r: r.__setitem__(slice(0, 4), b"NOPE"))
    def test_version48_refused(self): self.reject(lambda r: struct.pack_into("<i", r, 4, 48))
    def test_declared_length_mismatch(self): self.reject(lambda r: struct.pack_into("<I", r, 76, len(r) - 1))
    def test_bone_table_overflow(self): self.reject(lambda r: struct.pack_into("<2I", r, 156, 4096, 408))
    def test_bone_table_overlaps_header(self): self.reject(lambda r: struct.pack_into("<I", r, 160, 400))
    def test_bone_table_alignment(self): self.reject(lambda r: struct.pack_into("<I", r, 160, 409))
    def test_parent_out_of_range(self): self.reject(lambda r: struct.pack_into("<i", r, 412, 3))
    def test_self_parent(self): self.reject(lambda r: struct.pack_into("<i", r, 412, 0))
    def test_parent_cycle(self): self.reject(lambda r: struct.pack_into("<i", r, 408 + 2 * 216 + 4, 1), "cycle")
    def test_name_points_into_records(self): self.reject(lambda r: struct.pack_into("<i", r, 408, 4))
    def test_missing_name_terminator(self): self.reject(lambda r: (struct.pack_into("<i", r, 408, 1350 - 408), r.__setitem__(slice(1350, 1400), b"x" * 50)))
    def test_duplicate_name_refused(self): self.reject(lambda r: struct.pack_into("<i", r, 624, 1320 - 624), "Duplicate")
    def test_zero_kind_with_offset_refused(self): self.reject(lambda r: struct.pack_into("<I", r, 408 + 164, 0))
    def test_nonzero_kind_with_zero_offset_refused(self): self.reject(lambda r: struct.pack_into("<I", r, 408 + 168, 0))
    def test_negative_relative_offset_refused(self): self.reject(lambda r: struct.pack_into("<i", r, 408 + 168, -4))
    def test_payload_inside_bone_table_refused(self): self.reject(lambda r: struct.pack_into("<I", r, 408 + 168, 216))
    def test_payload_truncated(self): self.reject(lambda r: struct.pack_into("<I", r, 408 + 168, 1396 - 408))
    def test_payload_alias_refused(self): self.reject(lambda r: struct.pack_into("<I", r, 624 + 168, 1176 - 624), "overlap")
    def test_payload_name_overlap_refused(self): self.reject(lambda r: struct.pack_into("<i", r, 408, 1176 - 408), "aliases")
    def test_nonfinite_nan_refused(self): self.reject(lambda r: struct.pack_into("<f", r, 1176 + 4, float("nan")), "Nonfinite")
    def test_nonfinite_infinity_refused(self): self.reject(lambda r: struct.pack_into("<f", r, 1176 + 8, float("inf")), "Nonfinite")

    def test_unknown_bits_retained_without_inventing_boing_fields(self):
        raw = authored(); struct.pack_into("<I", raw, 1176, 0x800000B1)
        rule = J.parse(bytes(raw))["rules"][0]
        self.assertEqual(rule["flags_uint32"], 0x800000B1)
        self.assertLess(rule["flags_signed_int32"], 0)
        self.assertEqual(rule["unknown_flags_mask"], 0x80000080)
        self.assertEqual(len(rule["parameters"]), 29)
        self.assertFalse(rule["full_native_rule_layout_verified"])

    def test_finite_large_values_preserved_and_labelled_not_clamped(self):
        raw = authored(); struct.pack_into("<f", raw, 1176 + 4, 2000000.0)
        rule = J.parse(bytes(raw))["rules"][0]
        self.assertEqual(rule["parameters"]["length"], 2000000.0)
        self.assertEqual(rule["fields_above_proposed_abs1e6_budget"], ["length"])

    def test_signed_zero_binary_provenance_preserved(self):
        raw = authored(); struct.pack_into("<I", raw, 1176 + 4, 0x80000000)
        rule = J.parse(bytes(raw))["rules"][0]
        self.assertEqual(rule["float32_words_uint32"][0], 0x80000000)
        self.assertEqual(math.copysign(1.0, rule["parameters"]["length"]), -1.0)

    def test_other_procedure_kind_is_explicitly_unsupported_not_jiggle(self):
        raw = authored(); struct.pack_into("<I", raw, 408 + 164, 2)
        report = J.parse(bytes(raw))
        self.assertEqual(len(report["rules"]), 1)
        self.assertEqual(report["unsupported"][0]["procedure_type"], 2)

if __name__ == "__main__":
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(J.__file__), Path(__file__))}
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    unchanged = all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == sha for p, sha in before.items())
    report = {"format": "has_raw_jiggle_prefix_cpu_1", "checks": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "passed": result.wasSuccessful() and unchanged, "source_sha256_before_after": before, "sources_unchanged": unchanged,
        "fixtures": "Authored bytes only; unequal pitch friction/bounce and nonmonotonic bone/payload order", "native_runtime_gpu_or_SourceIO_import": False,
        "run": str(OUT)}
    (OUT / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("checks", "failures", "errors", "passed", "run")}))
    raise SystemExit(0 if report["passed"] else 1)
