"""Resolved Source cache writes preserve logical names and original payloads."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from source_archive import AssetError, write_resource


def io_path(path):
    """Read test evidence through Windows extended syntax, independently of writer."""
    name = str(path)
    if os.name == "nt" and not name.startswith("\\\\?\\"):
        name = "\\\\?\\UNC\\" + name[2:] if name.startswith("\\\\") else "\\\\?\\" + name
    return Path(name)


def identity(path):
    path = io_path(path)
    before = path.stat()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise AssertionError("Payload changed while recording its identity")
    return {"bytes": after.st_size, "mtime_ns": after.st_mtime_ns, "sha256": digest}


def inventory(root):
    """Include directory layout and file identities without following symlinks."""
    root = io_path(root)
    rows = {}
    for directory, names, files in os.walk(root, followlinks=False):
        parent = Path(directory)
        for name in sorted(names + files):
            path = parent / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                rows[relative] = {"symlink": os.readlink(path)}
            elif path.is_dir():
                rows[relative] = {"directory": True}
            else:
                rows[relative] = identity(path)
    return rows


class OversizedBytes(bytes):
    def __len__(self):
        return 128 * 1024 * 1024 + 1


class SourceResourceWriteTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="has-source-resource-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.cache = self.root / "resolved-native"
        self.cache.mkdir()
        self.source = self.root / "original.mdl"
        self.source.write_bytes(b"Synthetic original Source input\0\xff")
        os.utime(self.source, ns=(1600000000123456700, 1600000000123456700))
        before = identity(self.source)
        self.addCleanup(lambda: self.assertEqual(identity(self.source), before))

    def assert_logical_path(self, actual, relative):
        expected = self.cache.joinpath(*relative.split("/")).resolve()
        self.assertIsInstance(actual, Path)
        self.assertEqual(actual, expected)
        self.assertTrue(actual.is_absolute())
        self.assertFalse(str(actual).startswith("\\\\?\\"))
        self.assertEqual(actual.relative_to(self.cache.resolve()).as_posix(), relative)

    def test_short_binary_empty_and_bytearray_payloads(self):
        payloads = [b"", b"\0\xff\x80IDST\r\n", bytearray(range(256))]
        for index, payload in enumerate(payloads):
            with self.subTest(index=index):
                relative = f"materials/payload-{index}.vtf"
                actual = write_resource(self.cache, relative, payload)
                self.assert_logical_path(actual, relative)
                self.assertEqual(io_path(actual).read_bytes(), bytes(payload))
                self.assertEqual(identity(actual)["bytes"], len(payload))
        self.assertEqual(
            sorted(path.relative_to(self.cache).as_posix() for path in self.cache.rglob("*.vtf")),
            [f"materials/payload-{index}.vtf" for index in range(3)],
        )

    def test_nested_unicode_and_backslash_names_keep_exact_layout(self):
        relative = "materials/東方/Keiki tools/texture — あ.vmt"
        data = b'"VertexLitGeneric" { "$basetexture" "touhou/keiki" }\n'
        actual = write_resource(self.cache, relative.replace("/", "\\"), data)
        self.assert_logical_path(actual, relative)
        self.assertEqual(io_path(actual).read_bytes(), data)
        self.assertEqual(
            set(inventory(self.cache)),
            {"materials", "materials/東方", "materials/東方/Keiki tools", relative},
        )

    def test_existing_cache_payload_refuses_without_replacement(self):
        relative = "materials/touhou/keep.vtf"
        target = write_resource(self.cache, relative, b"Existing cache payload\0\xff")
        os.utime(io_path(target), ns=(1600000000765432100, 1600000000765432100))
        before = inventory(self.cache)
        with self.assertRaises(FileExistsError):
            write_resource(self.cache, relative, b"replacement")
        self.assertEqual(inventory(self.cache), before)

    def test_invalid_logical_names_refuse_before_any_layout_change(self):
        write_resource(self.cache, "materials/keep.vtf", b"protected existing cache payload")
        before = inventory(self.cache)
        names = [
            "", ".", "..", "../escape.vtf", "materials/../escape.vtf",
            "materials\\..\\escape.vtf", "/materials/escape.vtf", "\\materials\\escape.vtf",
            "\\\\server\\share\\escape.vtf", "C:/materials/escape.vtf", "C:\\materials\\escape.vtf",
            "C:materials/escape.vtf", "materials/keep.vtf:stream", "materials//new.vtf",
            "materials/./new.vtf", "materials/a. /new.vtf", "materials/a./new.vtf",
            "materials/a /new.vtf", "models/CON.mdl", "materials/nUl/escape.vtf",
            "maps/LpT1.bsp", "materials/COM9.vtf", "materials/a\0.vtf", "materials/a\x1f.vtf",
        ]
        for name in names:
            with self.subTest(name=name):
                with self.assertRaises(AssetError):
                    write_resource(self.cache, name, b"must never replace anything")
                self.assertEqual(inventory(self.cache), before)
        self.assertFalse((self.root / "escape.vtf").exists())

    def test_invalid_payloads_refuse_before_parent_directories(self):
        missing_root = self.root / "not-created"
        before = inventory(self.root)
        for data in [None, "text", memoryview(b"binary"), [1, 2], 7, OversizedBytes(b"small allocation")]:
            with self.subTest(payload_type=type(data).__name__):
                with self.assertRaises(AssetError):
                    write_resource(missing_root, "materials/new/nested.vtf", data)
                self.assertFalse(missing_root.exists())
                self.assertEqual(inventory(self.root), before)

    def test_symlink_parent_escape_refuses_and_preserves_outside_payload(self):
        outside = self.root / "outside"
        outside.mkdir()
        protected = outside / "keep.vtf"
        protected.write_bytes(b"outside payload must remain unchanged")
        os.utime(protected, ns=(1600000000444444400, 1600000000444444400))
        link = self.cache / "linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest("Directory symbolic links unavailable: " + str(error))
        outside_before = inventory(outside)
        cache_before = inventory(self.cache)
        for name in ["linked/keep.vtf", "linked/new/deep.vtf"]:
            with self.subTest(name=name):
                with self.assertRaisesRegex(AssetError, "escaped"):
                    write_resource(self.cache, name, b"replacement")
                self.assertEqual(inventory(outside), outside_before)
                self.assertEqual(inventory(self.cache), cache_before)

    @unittest.skipUnless(os.name == "nt", "Real extended-length write requires Windows")
    def test_real_windows_path_over_320_characters_and_exclusive_refusal(self):
        parts = ["materials", "touhou", "keiki"]
        filename = "haniyashin chisels texture — あ.vtf"
        while len(str(self.cache.joinpath(*parts, filename))) <= 340:
            parts.append("native-material-" + "a" * 60 + "-" + str(len(parts)))
        relative = "/".join([*parts, filename])
        expected = self.cache.joinpath(*parts, filename)
        self.assertGreater(len(str(expected)), 320)
        self.assertLessEqual(max(map(len, [*parts, filename])), 255)
        data = bytes(range(256)) * 17 + b"\0exact long resource bytes\xff"
        actual = write_resource(self.cache, relative, data)
        self.assert_logical_path(actual, relative)
        self.assertEqual(io_path(actual).read_bytes(), data)
        os.utime(io_path(actual), ns=(1600000000333333300, 1600000000333333300))
        before = inventory(self.cache)
        with self.assertRaises(FileExistsError):
            write_resource(self.cache, relative, b"must not replace long-path payload")
        self.assertEqual(inventory(self.cache), before)
        proof = {
            "format": "has_source_resource_long_path_1", "platform": sys.platform,
            "logical_path_characters": len(str(actual)), "relative": relative,
            "normal_returned_path": not str(actual).startswith("\\\\?\\"),
            "exact_layout": actual.relative_to(self.cache).as_posix() == relative,
            "payload": identity(actual), "exclusive_refusal_preserved": True,
        }
        print("SOURCE_RESOURCE_LONG_PATH " + json.dumps(proof, ensure_ascii=True), flush=True)


if __name__ == "__main__":
    unittest.main()
