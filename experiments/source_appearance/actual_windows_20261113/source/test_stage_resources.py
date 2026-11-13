"""CPU safety boundaries; no real extraction, 7-Zip, Blender, GPU or cleanup."""
import copy
import hashlib
import io
import json
from pathlib import Path
import stat
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zlib

sys.dont_write_bytecode = True
import stage_resources as stage

ARTIFACTS = stage.TASK / ("cpu-tests-" + str(time.time_ns()))
ARTIFACTS.mkdir(exist_ok=False)


def record(name="package/materials/a.vtf", **changes):
    value = {"Path": name, "Folder": "-", "Size": "3", "CRC": "352441C2", "Attributes": "A",
             "Encrypted": "-", "Alternate Stream": "-", "Symbolic Link": "", "Hard Link": "", "Copy Link": ""}
    value.update(changes)
    return ("\n".join(key + " = " + val for key, val in value.items()) + "\n\n").encode()


class SafetyTests(unittest.TestCase):
    def folder(self):
        path = ARTIFACTS / self._testMethodName
        path.mkdir(exist_ok=False)
        return path

    def test_reviewed_plan_exact_budget(self):
        cases = stage.load_plan(stage.TASK / "plan.json", stage.PLAN_SHA)
        self.assertEqual(sum(len(case["entries"]) for case in cases), 296)
        self.assertEqual(sum(row["bytes"] for case in cases for row in case["entries"]), 181460484)

    def test_actual_saved_indexes_match_all_296(self):
        cases = stage.load_plan(stage.TASK / "plan.json", stage.PLAN_SHA)
        inventory = stage.CHECKOUT / "output/sfm-extra-native-inventory/portable-root-639301165838922272"
        for case, index in zip(cases, [10, 11]):
            rows = stage.parse_index((inventory / f"archive-{index:02d}-index.log").read_bytes())
            self.assertEqual(len(stage.match_index(case, rows)), stage.CASE_COUNTS[case["case"]][0])

    def test_plan_raw_hash_refuses_changed_bytes(self):
        folder = self.folder()
        target = folder / "plan.json"
        target.write_bytes((stage.TASK / "plan.json").read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "reviewed byte hash"):
            stage.load_plan(target, stage.PLAN_SHA)

    def test_json_duplicate_and_nonfinite_refuse(self):
        folder = self.folder()
        for index, raw in enumerate([b'{"format":1,"format":2}', b'{"value":NaN}']):
            target = folder / f"bad-{index}.json"
            target.write_bytes(raw)
            with self.assertRaises(ValueError):
                stage.load_plan(target, hashlib.sha256(raw).hexdigest())

    def test_bad_windows_names_refuse(self):
        names = ["../bad.vtf", "a/../b.vtf", "a//b.vtf", "/a.vtf", "C:/a.vtf", "a/b:ads.vtf",
                 "a/NUL.vtf", "a/com1.vtf", "a/dir./a.vtf", "a/dir /a.vtf", "a/./b.vtf",
                 "a/a?.vtf", "a/a*.vtf", "a/a|.vtf", "a/\x01.vtf", "\\\\host\\share\\a.vtf"]
        for name in names:
            with self.subTest(name=name), self.assertRaises(ValueError):
                stage.safe_name(name)

    def test_backslashes_normalize_without_flattening(self):
        self.assertEqual(stage.safe_name(r"package\materials\nested\a.vtf"), "package/materials/nested/a.vtf")

    def test_index_link_stream_encryption_flags_refuse(self):
        for key in ["Symbolic Link", "Hard Link", "Copy Link", "Reparse Point", "Encrypted", "Anti", "Alternate Stream", "Split Before", "Split After"]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                stage.parse_index(record(**{key: "+"}))
        with self.assertRaises(ValueError):
            stage.parse_index(record(Attributes="lrwxrwxrwx"))

    def test_index_case_aliases_and_duplicate_fields_refuse(self):
        with self.assertRaisesRegex(ValueError, "case-insensitive"):
            stage.parse_index(record("package/materials/A.vtf") + record("package/materials/a.vtf"))
        with self.assertRaisesRegex(ValueError, "Duplicate archive index field"):
            stage.parse_index(record().replace(b"Size = 3", b"Size = 3\nSize = 3"))

    def test_index_missing_bad_size_crc_and_oversize_refuse(self):
        for changes in [{"Size": "-1"}, {"Size": str(512 * 1024 * 1024 + 1)}, {"CRC": ""}, {"CRC": "invalid"}, {"Folder": "?"}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                stage.parse_index(record(**changes))
        with self.assertRaisesRegex(ValueError, "4MiB"):
            stage.parse_index(b"a" * (stage.MAX_INDEX + 1))

    def test_index_missing_or_changed_allowlisted_resource_refuses(self):
        case = {"archive": {"index_entries": 1}, "entries": [{"member": "package/materials/a.vtf", "bytes": 3, "crc32": "352441C2", "category": "materials"}]}
        rows = stage.parse_index(record())
        self.assertEqual(stage.match_index(case, rows)[0]["bytes"], 3)
        for key, value in [("bytes", 4), ("crc32", "00000000"), ("member", "package/materials/b.vtf"), ("directory", True)]:
            changed = copy.deepcopy(rows)
            changed[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                stage.match_index(case, changed)

    def test_plan_unlisted_category_suffix_or_sidecar_refuses(self):
        original = json.loads((stage.TASK / "plan.json").read_bytes())
        for name in ["Takane and Nitori/materials/a.lua", "Takane and Nitori/other/a.vtf", "other/materials/a.vtf"]:
            value = copy.deepcopy(original)
            value["cases"][0]["material_allowlist"][0]["member"] = name
            with self.subTest(name=name), self.assertRaises(ValueError):
                stage.validate_plan(value)
        value = copy.deepcopy(original)
        value["cases"][0]["model_allowlist"].pop()
        with self.assertRaises(ValueError):
            stage.validate_plan(value)

    def test_plan_boolean_size_and_duplicate_case_refuse(self):
        value = json.loads((stage.TASK / "plan.json").read_bytes())
        value["cases"][0]["material_allowlist"][0]["bytes"] = True
        with self.assertRaises(ValueError):
            stage.validate_plan(value)
        value = json.loads((stage.TASK / "plan.json").read_bytes())
        value["cases"][1] = value["cases"][0]
        with self.assertRaises(ValueError):
            stage.validate_plan(value)

    def test_safe_target_and_existing_target_refusal(self):
        folder = self.folder()
        target = stage.checked_target(folder, "multi_skin_glove", "package/materials/a.vtf")
        self.assertEqual(target, folder / "multi_skin_glove/package/materials/a.vtf")
        target.parent.mkdir(parents=True)
        target.write_bytes(b"abc")
        with self.assertRaisesRegex(ValueError, "overwrite"):
            stage.checked_target(folder, "multi_skin_glove", "package/materials/a.vtf")
        with self.assertRaises(ValueError):
            stage.checked_target(folder, "multi_skin_glove", "../escaped.vtf")
        with self.assertRaisesRegex(ValueError, "Unknown staged case"):
            stage.checked_target(folder, "../outside", "package/materials/a.vtf")

    def test_reparse_and_symlink_stat_refuse_without_creating_links(self):
        folder = self.folder()
        with patch.object(Path, "lstat", return_value=SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0x400)):
            with self.assertRaisesRegex(ValueError, "reparse"):
                stage.no_reparse(folder / "file")
        with patch.object(Path, "lstat", return_value=SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0)):
            with self.assertRaisesRegex(ValueError, "reparse"):
                stage.no_reparse(folder / "file")

    def test_sink_oversize_refuses_before_writing_excess(self):
        target = io.BytesIO()
        sink = stage.ResourceSink(target, 3)
        sink.write(b"ab")
        with self.assertRaisesRegex(ValueError, "byte budget"):
            sink.write(b"cd")
        self.assertEqual(target.getvalue(), b"ab")
        self.assertEqual(sink.count, 2)

    def test_resource_short_crc_or_postwrite_changes_refuse(self):
        folder = self.folder()
        target = folder / "a.vmt"
        target.write_bytes(b"abc")
        result = {"bytes": 3, "crc32": "352441C2", "sha256": hashlib.sha256(b"abc").hexdigest()}
        entry = {"member": "a.vmt", "bytes": 3, "crc32": "352441C2"}
        self.assertEqual(stage.verify_resource(target, entry, result)["bytes"], 3)
        for changed in [dict(result, bytes=2), dict(result, crc32="00000000")]:
            with self.assertRaises(ValueError):
                stage.verify_resource(target, entry, changed)
        target.write_bytes(b"def")
        with self.assertRaisesRegex(ValueError, "changed"):
            stage.verify_resource(target, entry, result)

    def test_selected_mdl_checksum_and_header_refuse(self):
        folder = self.folder()
        target = folder / "a.mdl"
        payload = b"not an MDL"
        target.write_bytes(payload)
        result = {"bytes": len(payload), "crc32": f"{zlib.crc32(payload):08X}", "sha256": hashlib.sha256(payload).hexdigest()}
        entry = {"member": "a.mdl", "bytes": result["bytes"], "crc32": result["crc32"]}
        with self.assertRaisesRegex(ValueError, "SHA differs"):
            stage.verify_resource(target, entry, result, "0" * 64)
        with self.assertRaisesRegex(ValueError, "header differs"):
            stage.verify_resource(target, entry, result, result["sha256"])

    def run_child(self, code, stdout_limit=16, timeout=5):
        folder = self.folder()
        target = folder / "stdout.bin"
        with target.open("xb") as output:
            sink = stage.ResourceSink(output, stdout_limit)
            stage.run_tool([sys.executable, "-B", "-c", code], sink, folder / "stderr.log", timeout)
        return target.read_bytes(), sink.result()

    def test_process_normal_streams_and_exit(self):
        data, result = self.run_child("import sys;sys.stdout.buffer.write(b'abcd');sys.stderr.buffer.write(b'ok')")
        self.assertEqual(data, b"abcd")
        self.assertEqual(result["bytes"], 4)

    def test_process_stdout_budget_kills(self):
        with self.assertRaisesRegex(ValueError, "byte budget"):
            self.run_child("import sys;sys.stdout.buffer.write(b'x'*65536)", stdout_limit=8)

    def test_process_stderr_budget_kills(self):
        with self.assertRaisesRegex(ValueError, "byte budget"):
            self.run_child("import sys;sys.stderr.buffer.write(b'x'*131072)")

    def test_process_failure_code_refuses(self):
        with self.assertRaisesRegex(ValueError, "failed: 7"):
            self.run_child("raise SystemExit(7)")

    def test_process_timeout_kills(self):
        with self.assertRaisesRegex(ValueError, "timed out"):
            self.run_child("import time;time.sleep(10)", timeout=.3)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SafetyTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"format": "has_sfm_resource_stager_cpu_safety_1", "checks": result.testsRun,
              "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
              "artifact_folder": str(ARTIFACTS), "real_archive_extraction": False,
              "seven_zip_blender_gpu_network": False, "automatic_cleanup": False}
    stage.save(ARTIFACTS / "verification.json", report)
    print(json.dumps(report), flush=True)
    raise SystemExit(0 if result.wasSuccessful() else 1)
