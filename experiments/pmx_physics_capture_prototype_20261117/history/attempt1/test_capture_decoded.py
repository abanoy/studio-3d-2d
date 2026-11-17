"""Synthetic CPU data only. Installed reader source is hashed/AST-read, not run."""
import ast
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import struct
from types import SimpleNamespace as NS
import unittest

import capture_decoded as C


READER = (Path(os.environ["APPDATA"]) /
          "Blender Foundation/Blender/5.1/extensions/user_default/mmd_tools/core/pmx/__init__.py")
PARSER_SOURCE = READER.read_bytes()


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def vector(start):
    return tuple(f32(start + i / 4) for i in range(3))


def header(version="2.0", payload=b"authored synthetic fingerprint payload, not a complete PMX"):
    return b"PMX " + {"2.0": bytes.fromhex("00000040"), "2.1": bytes.fromhex("66660640")}[version] + bytes([8, 1, 0, 1, 1, 1, 1, 1, 1]) + payload


def body(index=0):
    return NS(name="髪 Body " + str(index), name_e="Hair " + str(index), bone=index,
              collision_group_number=15, collision_group_mask=0x8001, type=index % 3,
              size=vector(1), location=vector(2), rotation=vector(-1), mass=f32(1.25),
              velocity_attenuation=f32(.25), rotation_attenuation=f32(.5),
              bounce=f32(.75), friction=f32(.125), mode=index % 3)


def joint():
    return NS(name="接続 Joint", name_e="Spring", mode=0, src_rigid=0, dest_rigid=1,
              location=vector(3), rotation=vector(4), minimum_location=vector(-5),
              maximum_location=vector(5), minimum_rotation=vector(-6),
              maximum_rotation=vector(6), spring_constant=vector(7),
              spring_rotation_constant=vector(8))


def model():
    return NS(bones=[NS(name="髪", name_e="Hair"), NS(name="髪", name_e="Hair duplicate"),
                     NS(name="HEAD", name_e="Head")],
              rigids=[body(i) for i in range(3)], joints=[joint()], header=None)


def normalized(value):
    if type(value) is tuple:
        return [normalized(v) for v in value]
    if type(value) is list:
        return [normalized(v) for v in value]
    if type(value) is dict:
        return {k: normalized(v) for k, v in value.items()}
    return value


class CaptureTests(unittest.TestCase):
    def capture(self, item=None, source=None, **kwargs):
        return C.capture_decoded(item if item is not None else model(),
                                 source if source is not None else header(),
                                 parser_source_bytes=PARSER_SOURCE, **kwargs)

    def typed_equal(self, actual, expected):
        self.assertIs(type(actual), type(expected))
        if type(actual) is float:
            self.assertEqual(struct.pack("<d", actual), struct.pack("<d", expected))
        elif type(actual) is dict:
            self.assertEqual(actual.keys(), expected.keys())
            for key in actual:
                self.typed_equal(actual[key], expected[key])
        elif type(actual) is list:
            self.assertEqual(len(actual), len(expected))
            for left, right in zip(actual, expected):
                self.typed_equal(left, right)
        else:
            self.assertEqual(actual, expected)

    def test_exact_pinned_field_contract_without_executing_reader(self):
        self.assertEqual(len(PARSER_SOURCE), C.PINNED_READER_BYTES)
        self.assertEqual(hashlib.sha256(PARSER_SOURCE).hexdigest(), C.PINNED_READER_SHA256)
        tree = ast.parse(PARSER_SOURCE.decode("utf-8"))
        for class_name, expected in [("Rigid", C.RIGID_FIELDS), ("Joint", C.JOINT_FIELDS)]:
            cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
            init = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
            actual = [target.attr for node in init.body if isinstance(node, ast.Assign)
                      for target in node.targets if isinstance(target, ast.Attribute)
                      and isinstance(target.value, ast.Name) and target.value.id == "self"]
            self.assertEqual(actual, list(expected))

    def test_roundtrip_every_rigid_and_joint_field_without_coercion(self):
        item = model()
        result = self.capture(item)
        transported = json.loads(C.canonical_bytes(result))
        self.typed_equal(transported, result)
        for i, original in enumerate(item.rigids):
            self.typed_equal(transported["rigids"][i], {"index": i, **normalized(vars(original))})
        for i, original in enumerate(item.joints):
            self.typed_equal(transported["joints"][i], {"index": i, **normalized(vars(original))})
        self.assertTrue(result["decoded_supported_fields_complete"])
        self.assertFalse(result["applied"])
        self.assertFalse(result["native_file_preservation_complete"])
        self.assertEqual(result["native_file_join"], "UNQUALIFIED")
        self.assertEqual(result["runtime_support"], "NONE")

    def test_signed_zero_and_extreme_binary32_values_survive_json(self):
        item = model()
        item.rigids[0].rotation = (-0.0, f32(1e-40), C.F32_MAX)
        item.joints[0].spring_constant = (f32(-1e30), -0.0, f32(1e-30))
        result = self.capture(item)
        restored = json.loads(C.canonical_bytes(result))
        self.typed_equal(restored["rigids"][0]["rotation"], list(item.rigids[0].rotation))
        self.typed_equal(restored["joints"][0]["spring_constant"], list(item.joints[0].spring_constant))

    def test_inputs_unchanged_and_output_detached(self):
        item = model()
        original = copy.deepcopy(item)
        result = self.capture(item)
        self.assertEqual(item, original)
        result["rigids"][0]["size"][0] = 987.0
        result["bones"][0]["name"] = "changed"
        self.assertEqual(item, original)

    def test_original_indices_and_duplicate_names_stay_unresolved(self):
        result = self.capture()
        self.assertEqual([row["index"] for row in result["bones"]], [0, 1, 2])
        self.assertEqual([row["bone"] for row in result["rigids"]], [0, 1, 2])
        self.assertEqual([row["reason"] for row in result["bone_bindings"]],
                         ["DUPLICATE_NATIVE_NAME", "DUPLICATE_NATIVE_NAME", "NO_HAS_CROSSWALK"])
        self.assertTrue(all(row["status"] == "UNRESOLVED" for row in result["bone_bindings"]))

    def test_names_not_fuzzy_matched_or_normalized(self):
        item = model()
        item.bones = [NS(name="Hair", name_e=""), NS(name="hair", name_e=""), NS(name="Ｈａｉｒ", name_e="")]
        result = self.capture(item)
        self.assertEqual([row["name"] for row in result["bones"]], ["Hair", "hair", "Ｈａｉｒ"])
        self.assertTrue(all(row["reason"] == "NO_HAS_CROSSWALK" for row in result["bone_bindings"]))
        item.bones[0].name = ""
        self.assertEqual(self.capture(item)["bone_bindings"][0]["reason"], "EMPTY_NATIVE_NAME")

    def test_decoded_none_sentinels_preserved(self):
        item = model()
        item.rigids[0].bone = None
        item.joints[0].src_rigid = None
        item.joints[0].dest_rigid = None
        result = self.capture(item)
        self.assertIsNone(result["rigids"][0]["bone"])
        self.assertIsNone(result["joints"][0]["src_rigid"])
        self.assertIsNone(result["joints"][0]["dest_rigid"])
        self.assertTrue(any("negative bone" in text for text in result["limitations"]))

    def test_bad_sentinels_and_references_refuse_without_partial_result(self):
        for attr, values, category in [("bone", [-2, -1, 3, True, 1.0], "rigid"),
                                       ("src_rigid", [-2, -1, 3, True, 0.0], "joint")]:
            for value in values:
                with self.subTest(attr=attr, value=value):
                    item = model()
                    setattr(item.rigids[0] if category == "rigid" else item.joints[0], attr, value)
                    with self.assertRaises(C.CaptureError): self.capture(item)
        item = model();item.bones = []
        with self.assertRaises(C.CaptureError): self.capture(item)

    def test_unsigned_mask_and_group_domains(self):
        for mask in [0, 1, 0x8000, 65535]:
            item = model();item.rigids[0].collision_group_mask = mask
            self.assertEqual(self.capture(item)["rigids"][0]["collision_group_mask"], mask)
        for mask in [-1, 65536, True, 1.0, "65535"]:
            item = model();item.rigids[0].collision_group_mask = mask
            with self.assertRaises(C.CaptureError): self.capture(item)
        for group in [-1, 16, False, 1.0]:
            item = model();item.rigids[0].collision_group_number = group
            with self.assertRaises(C.CaptureError): self.capture(item)

    def test_all_known_shapes_and_modes_retained(self):
        result = self.capture()
        self.assertEqual([row["type"] for row in result["rigids"]], [0, 1, 2])
        self.assertEqual([row["mode"] for row in result["rigids"]], [0, 1, 2])

    def test_unknown_types_explicitly_incomplete_not_silently_dropped(self):
        item = model();item.rigids[0].type = 127;item.rigids[1].mode = -128;item.joints[0].mode = 1
        result = self.capture(item)
        self.assertFalse(result["decoded_supported_fields_complete"])
        self.assertEqual(result["rigids"][0]["type"], 127)
        self.assertEqual(result["rigids"][1]["mode"], -128)
        self.assertEqual(result["joints"][0]["mode"], 1)
        self.assertEqual(len(result["issues"]), 3)
        for value in [-129, 128, True, .0]:
            item = model();item.joints[0].mode = value
            with self.assertRaises(C.CaptureError): self.capture(item)

    def test_float_type_nonfinite_and_non_binary32_refuse(self):
        for value in [True, 1, "1", math.nan, math.inf, -math.inf, 1e40, .1]:
            item = model();item.rigids[0].mass = value
            with self.subTest(value=value):
                with self.assertRaises(C.CaptureError): self.capture(item)
        item = model();item.joints[0].spring_constant = (1.0, math.nan, 2.0)
        with self.assertRaises(C.CaptureError): self.capture(item)

    def test_vector_missing_field_and_collection_types_refuse(self):
        for value in [None, [1.0, 2.0], [1.0] * 4, "abc", [1.0, True, 3.0]]:
            item = model();item.rigids[0].size = value
            with self.assertRaises(C.CaptureError): self.capture(item)
        item = model();del item.joints[0].minimum_rotation
        with self.assertRaises(C.CaptureError): self.capture(item)
        item = model();item.rigids = iter(item.rigids)
        with self.assertRaises(C.CaptureError): self.capture(item)

    def test_name_and_attribute_budgets_refuse(self):
        for value in ["髪" * 342, "\ud800", None, b"hair"]:
            item = model();item.rigids[0].name = value
            with self.assertRaises(C.CaptureError): self.capture(item)
        item = model()
        for i in range(130): setattr(item.rigids[0], "extra" + str(i), 0)
        with self.assertRaises(C.CaptureError): self.capture(item)

    def test_count_byte_and_limit_budgets_refuse_no_truncation(self):
        for limits in [C.Limits(bones=2), C.Limits(rigids=2), C.Limits(joints=0),
                       C.Limits(name_bytes=1), C.Limits(capsule_bytes=1)]:
            with self.assertRaises(C.CaptureError): self.capture(limits=limits)
        for limits in [C.Limits(rigids=513), C.Limits(bones=True), C.Limits(capsule_bytes=-1)]:
            with self.assertRaises(C.CaptureError): self.capture(limits=limits)
        item = model();item.rigids = [body(0)] * 513
        with self.assertRaises(C.CaptureError): self.capture(item)

    def test_unknown_soft_table_attributes_report_values_not_captured(self):
        item = model();item.soft_bodies = [NS(native_unknown=True), NS(native_unknown=False)]
        result = self.capture(item)
        self.assertFalse(result["decoded_supported_fields_complete"])
        issue = next(row for row in result["issues"] if row["path"] == "model.soft_bodies")
        self.assertEqual(issue["item_count"], 2)
        self.assertFalse(issue["values_captured"])
        self.assertNotIn("soft_bodies", result)
        item.soft_bodies = [None] * 1025
        with self.assertRaises(C.CaptureError): self.capture(item)

    def test_unknown_body_joint_fields_cannot_claim_complete(self):
        item = model();item.rigids[0].new_native_parameter = 1;item.joints[0].new_joint_parameter = "unknown"
        result = self.capture(item)
        self.assertFalse(result["decoded_supported_fields_complete"])
        self.assertEqual(len(result["issues"]), 2)
        self.assertTrue(all(row["values_captured"] is False for row in result["issues"]))

    def test_exact_version_word_and_source_sha(self):
        for version, word in [("2.0", "00000040"), ("2.1", "66660640")]:
            source = header(version)
            result = self.capture(source=source)
            self.assertEqual(result["source_fingerprint"]["sha256"], hashlib.sha256(source).hexdigest())
            self.assertEqual(result["source_fingerprint"]["version_word_le_hex"], word)
        source = bytearray(header());source[4:8] = bytes.fromhex("01000040")
        with self.assertRaises(C.CaptureError): self.capture(source=bytes(source))

    def test_pmx21_soft_body_count_unknown_even_without_attribute(self):
        result = self.capture(source=header("2.1"))
        self.assertFalse(result["decoded_supported_fields_complete"])
        issue = next(row for row in result["issues"] if row["code"] == "pmx_2_1_unsupported_by_pinned_reader")
        self.assertIsNone(issue["soft_body_count"])
        self.assertEqual(issue["soft_body_table"], "UNSUPPORTED_NOT_DECODED")
        self.assertFalse(result["native_file_preservation_complete"])

    def test_bad_header_and_decoded_version_mismatch_refuse(self):
        good = header()
        for source in [b"", b"notPMX" + good[6:], good[:8] + b"\x07" + good[9:],
                       good[:10] + b"\x05" + good[11:], good[:11] + b"\x03" + good[12:], bytearray(good)]:
            with self.assertRaises(C.CaptureError): self.capture(source=source)
        item = model();item.header = NS(version=2.0)
        with self.assertRaises(C.CaptureError): self.capture(item, header("2.1"))
        self.assertTrue(self.capture(item)["decoded_supported_fields_complete"])

    def test_parser_source_mismatch_refuses(self):
        with self.assertRaises(C.CaptureError):
            C.capture_decoded(model(), header(), parser_source_bytes=PARSER_SOURCE[:-1] + b"!")

    def test_fingerprint_is_explicitly_not_a_native_join(self):
        left = model();right = model();right.rigids[0].mass = 99.0
        a, b = self.capture(left), self.capture(right)
        self.assertEqual(a["source_fingerprint"], b["source_fingerprint"])
        self.assertNotEqual(a["rigids"], b["rigids"])
        for result in (a, b):
            self.assertEqual(result["native_file_join"], "UNQUALIFIED")
            self.assertFalse(result["native_file_preservation_complete"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
