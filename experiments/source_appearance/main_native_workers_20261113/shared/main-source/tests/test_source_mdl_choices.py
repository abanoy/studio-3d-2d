"""Hand-authored MDL49 table controls. Never opens a model/archive or converter."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import time
import unittest
import uuid

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent / "tools"))
import source_mdl_choices as C

SOURCE = "a" * 64
_DEFAULT_RAW = object()


class Bytes:
    def __init__(self):
        self.data = bytearray(240)
        self.data[:4] = b"IDST"
        self.put("iI", 4, 49, 0xFEDCBA98)

    def put(self, fmt, offset, *values):
        struct.pack_into("<" + fmt, self.data, offset, *values)

    def alloc(self, size):
        while len(self.data) % 4:
            self.data.append(0)
        offset = len(self.data)
        self.data.extend(b"\0" * size)
        return offset

    def text(self, raw):
        offset = len(self.data)
        self.data.extend(raw + b"\0")
        return offset

    def finish(self):
        self.put("I", 76, len(self.data))
        return bytes(self.data)


def fixture(materials=None, skins=None, groups=None, *, backward_models=False):
    """The disk offsets/values here are literal fixture knowledge, not parser output."""
    materials = [b"base", b"glow", b"alt"] if materials is None else materials
    skins = [[0, 1], [2, 1], [0, 1]] if skins is None else skins
    groups = [(b"tools", [(b"blank", 7), (b"", 0)]),
              (b"hat", [(b"hat.dmx", 11)])] if groups is None else groups
    b = Bytes()
    textures = b.alloc(64 * len(materials)) if materials else 0
    skin = b.alloc(2 * sum(map(len, skins))) if skins and skins[0] else 0
    model_tables = []
    if backward_models:
        model_tables = [b.alloc(148 * len(choices)) if choices else 0 for _, choices in groups]
    group_table = b.alloc(16 * len(groups)) if groups else 0
    if not backward_models:
        model_tables = [b.alloc(148 * len(choices)) if choices else 0 for _, choices in groups]
    b.put("2i", 204, len(materials), textures)
    b.put("3i", 220, len(skins[0]) if skins else 0, len(skins), skin)
    b.put("2i", 232, len(groups), group_table)
    for i, name in enumerate(materials):
        at = textures + i * 64
        b.put("i", at, b.text(name) - at)
    cursor = skin
    for row in skins:
        for value in row:
            b.put("H", cursor, value)
            cursor += 2
    for i, (name, choices) in enumerate(groups):
        at = group_table + i * 16
        b.put("4i", at, b.text(name) - at, len(choices), i + 1,
              model_tables[i] - at if choices else 0)
        for j, (choice_name, vertex_count) in enumerate(choices):
            model_at = model_tables[i] + j * 148
            if len(choice_name) >= 64:
                raise ValueError("Fixture fixed name is too long")
            b.data[model_at:model_at + len(choice_name)] = choice_name
            b.put("i", model_at + 80, vertex_count)
    return b.finish(), {"textures": textures, "skin": skin, "groups": group_table,
                        "models": model_tables}


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.raw, self.at = fixture()

    def mutate(self, fmt, at, *values):
        changed = bytearray(self.raw)
        struct.pack_into("<" + fmt, changed, at, *values)
        return bytes(changed)

    def catalogue(self, raw=_DEFAULT_RAW, source=SOURCE, member="models/test model.mdl"):
        return C.catalogue(self.raw if raw is _DEFAULT_RAW else raw, source, member)

    def refused(self, raw, code=None, **kwargs):
        with self.assertRaises(C.CatalogueError) as caught:
            self.catalogue(raw, **kwargs)
        if code:
            self.assertEqual(caught.exception.code, code)
        self.assertIsInstance(caught.exception, ValueError)

    def test_known_skin_indices_and_material_names(self):
        value = self.catalogue()
        self.assertEqual(value["skins"], [
            {"index": 0, "material_indices": [0, 1], "material_names": ["base", "glow"]},
            {"index": 1, "material_indices": [2, 1], "material_names": ["alt", "glow"]},
            {"index": 2, "material_indices": [0, 1], "material_names": ["base", "glow"]}])
        self.assertEqual(value["skin_reference_count"], 2)

    def test_true_blank_is_vertex_count_not_name(self):
        choices = self.catalogue()["bodygroups"][0]["choices"]
        self.assertEqual([(x["index"], x["name"], x["vertex_count"], x["true_blank"]) for x in choices],
                         [(0, "blank", 7, False), (1, "", 0, True)])
        self.assertEqual(choices[1]["display_name"], "Choice 2 (empty name)")

    def test_fixed_and_variable_raw_names_are_not_stripped_or_recoded(self):
        raw, _ = fixture(materials=[b" material \xff "], skins=[[0]],
                         groups=[(b" part \xfe ", [(b" name \xfd ", 1)])])
        value = self.catalogue(raw)
        rows = [value["materials"][0], value["bodygroups"][0], value["bodygroups"][0]["choices"][0]]
        for row, native in zip(rows, [b" material \xff ", b" part \xfe ", b" name \xfd "]):
            self.assertEqual(row["name"].encode("latin-1"), native)
            self.assertEqual(row["raw_name_sha256"], hashlib.sha256(native).hexdigest())
            self.assertEqual(row["display_name"], row["name"])

    def test_native_bytes_checksum_and_supplied_source_context_are_distinct(self):
        value = self.catalogue()
        self.assertEqual(value["original_source_sha256"], SOURCE)
        self.assertEqual(value["native_mdl_sha256"], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(value["native_checksum"], 0xFEDCBA98)
        self.assertEqual(value["native_mdl_bytes"], len(self.raw))
        self.assertEqual(value["native_version"], 49)

    def test_digest_covers_exact_canonical_payload(self):
        value = self.catalogue()
        digest = value.pop("catalogue_sha256")
        known = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
        self.assertEqual(digest, hashlib.sha256(known).hexdigest())

    def test_member_and_original_source_change_digest_even_for_same_mdl(self):
        a = self.catalogue()
        b = self.catalogue(member="models/other.mdl")
        c = self.catalogue(source="b" * 64)
        self.assertEqual(a["native_mdl_sha256"], b["native_mdl_sha256"])
        self.assertEqual(len({a["catalogue_sha256"], b["catalogue_sha256"], c["catalogue_sha256"]}), 3)

    def test_output_is_detached_plain_json_and_deterministic(self):
        a = self.catalogue()
        self.assertEqual(a, self.catalogue())
        self.assertEqual(json.loads(C.json_bytes(a)), a)
        self.assertLessEqual(len(C.json_bytes(a)), 256 * 1024)
        a["bodygroups"][0]["choices"][0]["index"] = 999
        self.assertEqual(self.catalogue()["bodygroups"][0]["choices"][0]["index"], 0)

    def test_no_bodygroups_is_a_skin_only_catalogue(self):
        raw, _ = fixture(groups=[])
        self.assertEqual(self.catalogue(raw)["bodygroups"], [])

    def test_exact_duplicate_skin_rows_remain_separate_numeric_families(self):
        rows = self.catalogue()["skins"]
        self.assertEqual(rows[0]["material_indices"], rows[2]["material_indices"])
        self.assertNotEqual(rows[0]["index"], rows[2]["index"])

    def test_identical_material_names_and_choice_names_remain_indexed(self):
        raw, _ = fixture(materials=[b"same", b"same"], skins=[[1, 0]],
                         groups=[(b"g", [(b"same", 2), (b"same", 0)])])
        value = self.catalogue(raw)
        self.assertEqual([x["index"] for x in value["materials"]], [0, 1])
        self.assertEqual([x["index"] for x in value["bodygroups"][0]["choices"]], [0, 1])

    def test_signed_backward_relative_model_table_is_bounded_and_supported(self):
        raw, _ = fixture(backward_models=True)
        self.assertEqual(self.catalogue(raw)["bodygroups"][0]["choices"][0]["vertex_count"], 7)

    def test_exact_pooled_material_string_is_supported(self):
        pointer = struct.unpack_from("<i", self.raw, self.at["textures"])[0]
        target = self.at["textures"] + pointer
        raw = self.mutate("i", self.at["textures"] + 64, target - (self.at["textures"] + 64))
        self.assertEqual(self.catalogue(raw)["materials"][1]["name"], "base")

    def test_unrelated_bone_mesh_flex_runtime_fields_are_not_dereferenced(self):
        raw = bytearray(self.raw)
        # Deliberately impossible unrelated bone/mesh/flex offsets: metadata is not geometry validation.
        struct.pack_into("2i", raw, 156, -900, 2**31 - 1)
        struct.pack_into("2i", raw, self.at["models"][0] + 72, -900, 2**31 - 1)
        self.assertEqual(self.catalogue(bytes(raw))["bodygroups"][0]["choices"][0]["vertex_count"], 7)

    def test_empty_member_is_permitted_for_a_loose_source(self):
        self.assertEqual(self.catalogue(member="")["selected_member"], "")

    def test_refuses_non_bytes_input(self):
        for raw in [bytearray(self.raw), memoryview(self.raw), "IDST", None]:
            with self.subTest(kind=type(raw).__name__):
                self.refused(raw, "input_type")

    def test_refuses_short_inspected_prefix(self):
        self.refused(b"IDST" + b"\0" * 235, "file_size")

    def test_refuses_over_16_mib_without_parsing(self):
        self.refused(b"\0" * (16 * 1024 * 1024 + 1), "file_size")

    def test_refuses_wrong_magic(self):
        self.refused(b"IDAG" + self.raw[4:], "magic")

    def test_refuses_other_version(self):
        for version in [48, 50, -1]:
            with self.subTest(version=version):
                self.refused(self.mutate("i", 4, version), "version")

    def test_refuses_changed_declared_length_and_truncated_tables(self):
        self.refused(self.mutate("I", 76, len(self.raw) - 1), "declared_length")
        raw = bytearray(self.raw[:self.at["models"][1] + 147])
        struct.pack_into("I", raw, 76, len(raw))
        self.refused(bytes(raw), "table_range")

    def test_refuses_invalid_source_sha(self):
        for source in [None, "A" * 64, "a" * 63, "g" * 64, 0]:
            with self.subTest(source=source):
                self.refused(self.raw, "source_sha256", source=source)

    def test_refuses_unsafe_or_noncanonical_member(self):
        bad = ["/a.mdl", "../a.mdl", "a/../b.mdl", "a/./b.mdl", "a//b.mdl", "a\\b.mdl",
               "C:/a.mdl", "a:stream.mdl", "a/CON.mdl", "a/LPT1", "a /b.mdl", "a./b.mdl",
               "a\0.mdl", "a\n.mdl", "a/", "é" * 513, 2, "\ud800",
               "a/*.mdl", "a/q?.mdl", "a/a|b.mdl", 'a/a"b.mdl', "a/a<b.mdl",
               "a/CON .mdl", "a/COM¹.mdl", "a/CONIN$.mdl"]
        for member in bad:
            with self.subTest(member=repr(member)):
                self.refused(self.raw, "member", member=member)

    def test_refuses_negative_and_excessive_material_count(self):
        for count in [-1, 2049]:
            self.refused(self.mutate("i", 204, count), "count")

    def test_refuses_zero_material_layout_explicitly(self):
        self.refused(self.mutate("i", 204, 0), "unsupported_materials")

    def test_refuses_skin_dimension_bounds(self):
        for offset, values in [(220, [-1, 2049]), (224, [-1, 257])]:
            for count in values:
                self.refused(self.mutate("i", offset, count), "count")

    def test_refuses_empty_skin_layout_explicitly(self):
        for offset in [220, 224]:
            self.refused(self.mutate("i", offset, 0), "unsupported_skins")

    def test_refuses_group_count_bounds(self):
        for count in [-1, 257]:
            self.refused(self.mutate("i", 232, count), "count")

    def test_refuses_model_count_bounds(self):
        for count in [-1, 0, 257]:
            self.refused(self.mutate("i", self.at["groups"] + 4, count), "count")

    def test_refuses_excessive_total_choices(self):
        raw, _ = fixture(groups=[(str(i).encode(), [(b"a", 1)] * 241) for i in range(17)])
        self.refused(raw, "total_choices")

    def test_refuses_negative_vertex_count(self):
        self.refused(self.mutate("i", self.at["models"][0] + 80, -1), "vertex_count")

    def test_large_vertex_count_is_metadata_not_claimed_geometry(self):
        value = self.catalogue(self.mutate("i", self.at["models"][0] + 80, 2**31 - 1))
        self.assertEqual(value["bodygroups"][0]["choices"][0]["vertex_count"], 2**31 - 1)
        self.assertFalse(value["bodygroups"][0]["choices"][0]["true_blank"])

    def test_refuses_nonpositive_group_base(self):
        for base in [-1, 0]:
            self.refused(self.mutate("i", self.at["groups"] + 8, base), "bodygroup_base")

    def test_refuses_absolute_tables_inside_header_or_outside_file(self):
        for offset in [208, 228, 236]:
            for target in [-1, 0, 239, len(self.raw), 2**31 - 1]:
                with self.subTest(offset=offset, target=target):
                    self.refused(self.mutate("i", offset, target), "table_range")

    def test_refuses_nonzero_offset_for_empty_bodygroup_table(self):
        raw, _ = fixture(groups=[])
        changed = bytearray(raw)
        struct.pack_into("i", changed, 236, 240)
        self.refused(bytes(changed), "empty_table_offset")

    def test_refuses_relative_model_table_outside_file_or_header(self):
        for relative in [-self.at["groups"], 0, len(self.raw), 2**31 - 1]:
            self.refused(self.mutate("i", self.at["groups"] + 12, relative), "table_range")

    def test_refuses_aliased_texture_and_skin_tables(self):
        self.refused(self.mutate("i", 228, self.at["textures"]), "table_overlap")

    def test_refuses_partial_structural_overlap(self):
        self.refused(self.mutate("i", 236, self.at["textures"] + 4), "table_overlap")

    def test_refuses_shared_and_partially_shared_model_tables(self):
        second = self.at["groups"] + 16
        for start in [self.at["models"][0], self.at["models"][0] + 4]:
            self.refused(self.mutate("i", second + 12, start - second), "table_overlap")

    def test_refuses_material_name_inside_any_structural_table(self):
        start = self.at["textures"]
        self.refused(self.mutate("i", start, 4), "string_table_overlap")

    def test_reserves_future_model_tables_before_reading_group_strings(self):
        group = self.at["groups"]
        self.refused(self.mutate("i", group, self.at["models"][1] - group), "string_table_overlap")

    def test_refuses_name_pointer_outside_file(self):
        for pointer in [-2**31, len(self.raw), 2**31 - 1]:
            self.refused(self.mutate("i", self.at["textures"], pointer), "string_range")

    def test_refuses_unterminated_variable_name(self):
        raw = bytearray(self.raw)
        at = len(raw)
        raw.extend(b"X" * 1024)
        struct.pack_into("i", raw, self.at["textures"], at - self.at["textures"])
        struct.pack_into("I", raw, 76, len(raw))
        self.refused(bytes(raw), "string_termination")

    def test_longest_supported_variable_name_is_exact(self):
        name = b"x" * 1023
        raw, _ = fixture(materials=[name], skins=[[0]])
        self.assertEqual(self.catalogue(raw)["materials"][0]["name"], name.decode())

    def test_refuses_empty_material_name(self):
        raw, _ = fixture(materials=[b""], skins=[[0]])
        self.refused(raw, "material_name")

    def test_refuses_unterminated_fixed_model_name(self):
        raw = bytearray(self.raw)
        raw[self.at["models"][0]:self.at["models"][0] + 64] = b"X" * 64
        self.refused(bytes(raw), "string_termination")

    def test_fixed_model_name_63_bytes_is_supported(self):
        name = b"m" * 63
        raw, _ = fixture(groups=[(b"g", [(name, 1)])])
        self.assertEqual(self.catalogue(raw)["bodygroups"][0]["choices"][0]["name"], name.decode())

    def test_refuses_skin_reference_outside_material_table(self):
        for index in [3, 65535]:
            self.refused(self.mutate("H", self.at["skin"], index), "material_index")

    def test_refuses_duplicate_exact_group_identity(self):
        raw, _ = fixture(groups=[(b"g", [(b"a", 1)]), (b"g", [(b"b", 1)])])
        self.refused(raw, "duplicate_bodygroup")

    def test_case_and_whitespace_distinct_group_names_are_not_collapsed(self):
        raw, _ = fixture(groups=[(b"g", [(b"a", 1)]), (b"G", [(b"b", 1)]),
                                 (b" g", [(b"c", 1)])])
        self.assertEqual([x["name"] for x in self.catalogue(raw)["bodygroups"]], ["g", "G", " g"])

    def test_empty_group_name_has_a_separate_display_label(self):
        raw, _ = fixture(groups=[(b"", [(b"a", 1)])])
        group = self.catalogue(raw)["bodygroups"][0]
        self.assertEqual(group["name"], "")
        self.assertEqual(group["display_name"], "Part 1 (empty name)")

    def test_refuses_result_over_budget_instead_of_truncating(self):
        materials = [(str(i).encode() + b"X" * 100) for i in range(200)]
        raw, _ = fixture(materials=materials, skins=[list(range(200))] * 16)
        self.assertLess(len(raw), 16 * 1024 * 1024)
        self.refused(raw, "result_too_large")

    def test_scope_does_not_claim_native_fidelity_or_resource_completeness(self):
        scope = self.catalogue()["scope"]
        self.assertEqual(scope["kind"], "mdl49_static_table_metadata_only")
        self.assertFalse(scope["native_fidelity_verified"])
        self.assertFalse(scope["resources_verified"])
        self.assertFalse(scope["converted_object_correspondence_verified"])

    def test_parser_has_no_file_or_converter_imports(self):
        self.assertFalse(any(name == "bpy" or name.startswith("SourceIO") or name == "numpy"
                             for name in sys.modules))
        self.assertNotIn("native_reader", sys.modules)


def run():
    destination = HERE.parent / "output/source-mdl-choices-cpu" / (str(time.time_ns()) + "-catalogue-" + uuid.uuid4().hex[:8])
    destination.mkdir(parents=True, exist_ok=False)
    sources = [HERE.parent / "tools/source_mdl_choices.py", Path(__file__).resolve()]
    def records():
        return {str(path): {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            "bytes": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns}
                for path in sources}
    before = records()
    started = time.time_ns()
    with (destination / "unittest.log").open("w", encoding="utf-8", newline="\n") as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(CatalogueTests))
    after = records()
    report = {"format": "studio_mdl_choices_synthetic_proof_1", "tests": result.testsRun,
              "failures": len(result.failures), "errors": len(result.errors),
              "started_ns": started, "finished_ns": time.time_ns(),
              "source_before": before, "source_after": after, "source_preserved": before == after,
              "actual_native_inputs_read": False, "actual_models_tested": 0,
              "scope": "hand-authored synthetic common-prefix/table controls only"}
    report["passed"] = result.wasSuccessful() and before == after
    (destination / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"folder": str(destination), "tests": result.testsRun,
                      "failures": len(result.failures), "errors": len(result.errors),
                      "source_preserved": before == after, "passed": report["passed"]}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
