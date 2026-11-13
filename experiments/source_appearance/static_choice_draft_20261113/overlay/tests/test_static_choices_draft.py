"""Authored CPU contracts only. Every child-process call is replaced or forbidden."""
from pathlib import Path
import ast
import contextlib
import copy
import hashlib
import io
import itertools
import json
import os
import runpy
import struct
import sys
import types
import unittest
from unittest import mock
import zlib

OVERLAY = Path(__file__).resolve().parents[1]
TASK = OVERLAY.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(OVERLAY / "tools"))
sys.path.insert(1, str(OVERLAY / "tests"))
import source_appearance as A
import prepare_source as P
import source_choice_io as IO
from test_source_mdl_choices import fixture

RUN = None
BASE_LOAD_MODEL = '''def load_model(path, buffer, scale, parent=None, skin=0):
    container = import_model(TinyPath(str(path)), buffer, cm, model_options(scale), SteamAppId.GARRYS_MOD)
    put_into_collections(container, Path(str(path)).stem)
    from SourceIO.blender_bindings.shared.skins import set_model_skin
    set_model_skin(container, skin)
    active = set()
    for variants in container.bodygroups.values():
        if variants and variants[0] is not None:
            active.add(variants[0])
    for obj in container.objects:
        if container.bodygroups and obj not in active:
            obj.hide_render = True
            obj.hide_set(True)
    if parent:
        if container.armature:
            container.armature.parent = parent
        else:
            for obj in container.objects:
                obj.parent = parent
    return container
'''

def identity(path):
    stat = path.stat()
    return hashlib.sha256(path.read_bytes()).hexdigest(), stat.st_size, stat.st_mtime_ns

def request(skin=0, groups=None):
    return {"format": A.FORMAT, "source_sha256": "a" * 64, "native_mdl_sha256": "b" * 64,
            "skin": skin, "bodygroups": {} if groups is None else groups}

class Mesh:
    def __init__(self, name):
        self.name = name; self.type = "MESH"; self.hide_render = False; self.hidden = False
        self.data = types.SimpleNamespace(polygons=[(0, 1, 2)], vertices=(1, 2, 3),
            weights=((7, 1.),), shape_keys={"authored target": .375})
    def hide_set(self, hidden): self.hidden = hidden

def container(groups=3, skins=None):
    names = skins or [["base", "glow"], ["alt", "glow"], ["last", "glow"]]
    materials = {name: types.SimpleNamespace(name=name) for row in names for name in row}
    skin_groups = [[materials[name] for name in row] for row in names]
    parts, bodygroups, objects = [], {}, []
    for i in range(groups):
        # A visible choice named blank is deliberate: geometry decides visibility.
        models = [types.SimpleNamespace(name="blank", vertex_count=7), types.SimpleNamespace(name="hidden", vertex_count=0)]
        obj = Mesh("part" + str(i)); objects.append(obj)
        parts.append(types.SimpleNamespace(name="group" + str(i), models=models))
        bodygroups[parts[-1].name] = [obj, None]
    return types.SimpleNamespace(mdl=types.SimpleNamespace(body_parts=parts, skin_groups=skin_groups,
        materials=list(materials.values())), objects=objects, bodygroups=bodygroups, armature=None)

def states(value):
    return [(obj.name, obj.hide_render, obj.hidden, copy.deepcopy(obj.data.__dict__)) for obj in value.objects]

def gma(rows):
    header = b"GMAD\x03" + b"\0" * 16 + b"\0Synthetic\0Description\0Author\0" + struct.pack("<I", 1)
    payload = b""; index = b""
    for i, (name, raw) in enumerate(rows):
        index += struct.pack("<I", i + 1) + name.encode() + b"\0" + struct.pack("<qI", len(raw), zlib.crc32(raw) & 0xFFFFFFFF)
        payload += raw
    return header + index + b"\0" * 4 + payload

def vpk(raw, *, archive=0x7FFF):
    # One no-preload MDL entry, with literal known folder/name and CRC.
    tree = b"mdl\0models\0authored\0" + struct.pack("<IHHIIH", zlib.crc32(raw) & 0xFFFFFFFF, 0, archive, 0, len(raw), 0xFFFF) + b"\0\0\0"
    return struct.pack("<III", 0x55AA1234, 1, len(tree)) + tree + (raw if archive == 0x7FFF else b"")

class AuthoredCase(unittest.TestCase):
    def setUp(self):
        self.directory = RUN / (self.id().rsplit(".", 1)[-1])
        self.directory.mkdir(exist_ok=False)

class ValidatorTests(AuthoredCase):
    def test_all_nonempty_three_binary_part_combinations(self):
        for choices in itertools.product((0, 1), repeat=3):
            value = container(); original = states(value); callback = mock.Mock()
            req = request(groups={str(i): c for i, c in enumerate(choices)})
            if choices == (1, 1, 1):
                with self.assertRaisesRegex(ValueError, "no renderable geometry"): A.apply(value, req, callback)
                self.assertEqual(states(value), original); callback.assert_not_called()
            else:
                result = A.apply(value, req, callback)
                self.assertEqual(result["selected_native_bodygroup_indices"], req["bodygroups"])
                self.assertEqual([o.hide_render for o in value.objects], [bool(c) for c in choices])
                self.assertEqual([o.data.__dict__ for o in value.objects], [s[3] for s in original])
                callback.assert_called_once_with(value, 0)

    def test_three_skins_are_exact_numeric_choices(self):
        for skin in range(3):
            value = container(1); result = A.apply(value, request(skin), mock.Mock())
            self.assertEqual(result["selected_skin"], skin)
            self.assertFalse(result["native_appearance_choices"]["bodygroups"][0]["choices"][0]["blank"])

    def test_unknown_or_out_of_range_refuses_before_mutation(self):
        changes = [{"skin": True}, {"skin": 1.}, {"skin": -1}, {"skin": 256}, {"skin": 3},
                   {"bodygroups": {"00": 0}}, {"bodygroups": {"3": 0}}, {"bodygroups": {"0": 2}},
                   {"bodygroups": {"0": False}}, {"bodygroups": {"0": -1}}, {"extra": 0}]
        for change in changes:
            value = container(); before = states(value); callback = mock.Mock()
            with self.assertRaises(ValueError): A.apply(value, {**request(), **change}, callback)
            self.assertEqual(states(value), before); callback.assert_not_called()

    def test_missing_duplicate_or_wrong_blank_correspondence_refuses(self):
        for mode in ("missing", "duplicate", "wrong_blank", "alias"):
            value = container()
            if mode == "missing": value.bodygroups.pop("group0")
            elif mode == "duplicate": value.mdl.body_parts[1].name = "group0"
            elif mode == "wrong_blank": value.bodygroups["group0"][1] = value.objects[0]
            else: value.bodygroups["group1"][0] = value.objects[0]
            with self.assertRaises(ValueError): A.choose(value, request())

    def test_ambiguous_skin_columns_and_nonidentity_slots_refuse(self):
        value = container(skins=[["same", "same"], ["one", "two"]])
        with self.assertRaisesRegex(ValueError, "Ambiguous native skin columns"): A.choose(value, request(1))
        value = container(); value.mdl.materials.reverse()
        with self.assertRaisesRegex(ValueError, "Nonidentity"): A.choose(value, request(1))

    def test_sparse_selection_defaults_and_detaches(self):
        req = request(groups={"1": 1}); validated = A.validate(req); validated["bodygroups"]["0"] = 1
        self.assertEqual(req["bodygroups"], {"1": 1})
        self.assertEqual(A.choose(container(), req)["selected_native_bodygroup_indices"], {"0": 0, "1": 1, "2": 0})

    def test_duplicate_json_keys_size_and_changed_original_refuse(self):
        path = self.directory / "request.json"
        for raw in (b" " * (A.MAX_REQUEST + 1), b'{"skin":0,"skin":1}', json.dumps(request()).encode()):
            path.write_bytes(raw)
            with self.assertRaises(ValueError): A.load(path, "c" * 64)

    def test_request_read_remains_capped_if_it_grows_after_stat(self):
        path = self.directory / "grow.json"; path.write_bytes(b"{}")
        class Grown(io.BytesIO):
            def __init__(self): super().__init__(b" " * (A.MAX_REQUEST + 2)); self.requested = []
            def read(self, count=-1): self.requested.append(count); return super().read(count)
            def close(self): pass
        stream = Grown()
        with mock.patch.object(Path, "open", return_value=stream):
            with self.assertRaisesRegex(ValueError, "exceeds64KiB"): A.load(path, "a" * 64)
        self.assertEqual(stream.requested, [A.MAX_REQUEST + 1]); self.assertEqual(stream.tell(), A.MAX_REQUEST + 1)

    def test_native_binding_hash_and_bsp_refusal(self):
        raw, _ = fixture(); path = self.directory / "authored.mdl"; path.write_bytes(raw)
        req = {**request(), "native_mdl_sha256": hashlib.sha256(raw).hexdigest()}
        self.assertEqual(A.bind(req, "a" * 64, path), req)
        path.write_bytes(raw + b"changed")
        with self.assertRaisesRegex(ValueError, "no longer matches"): A.bind(req, "a" * 64, path)
        with self.assertRaisesRegex(ValueError, "not a BSP"): A.bind(req, "a" * 64, path.with_suffix(".bsp"))

class MetadataIOTests(AuthoredCase):
    def test_hashing_grown_file_stops_at_admitted_length_plus_one(self):
        path = self.directory / "grow.mdl"; path.write_bytes(b"abc")
        class Growing(io.BytesIO):
            def __init__(self): super().__init__(b"abcd" + b"unread trailer"); self.read_sizes = []
            def read(self, count=-1): self.read_sizes.append(count); return super().read(count)
            def close(self): pass
        stream = Growing()
        with mock.patch.object(Path, "open", return_value=stream):
            with self.assertRaisesRegex(ValueError, "grew beyond"): IO.identity(path)
        self.assertEqual(stream.tell(), 4); self.assertEqual(stream.read_sizes, [4])

    def test_gma_index_window_refuses_reads_outside_admitted_size(self):
        stream = io.BytesIO(b"unread owner payload")
        window = IO._IndexWindow(stream, 3)
        self.assertEqual(window.read(3), b"unr")
        with self.assertRaisesRegex(ValueError, "admitted input"): window.read(1)
        self.assertEqual(stream.tell(), 3)

    def test_loose_metadata_reads_no_converter_and_writes_nothing(self):
        raw, _ = fixture(); path = self.directory / "authored.mdl"; path.write_bytes(raw); before = identity(path)
        with mock.patch.object(P.subprocess, "Popen", side_effect=AssertionError("process prohibited")), mock.patch.object(Path, "write_bytes", side_effect=AssertionError("write prohibited")):
            result = IO.inspect_choices(path, path.name)
        self.assertEqual(result["native_mdl_sha256"], before[0]); self.assertEqual(identity(path), before)

    def test_loose_member_mismatch_and_legacy_bin_refuse(self):
        path = self.directory / "authored.mdl"; path.write_bytes(fixture()[0])
        with self.assertRaisesRegex(ValueError, "filename"): IO.inspect_choices(path, "other.mdl")
        legacy = self.directory / "authored.bin"; legacy.write_bytes(b"not decompressed")
        with self.assertRaisesRegex(ValueError, "default preparation"): IO.inspect_choices(legacy, "models/a.mdl")

    def test_gma_single_member_exact_hash_crc_and_no_extraction(self):
        raw, _ = fixture(); path = self.directory / "authored.gma"
        path.write_bytes(gma([("models/authored.mdl", raw), ("lua/never.lua", b"never executed")]))
        before = identity(path); files = sorted(self.directory.iterdir())
        result = IO.inspect_choices(path, "models/authored.mdl")
        self.assertEqual(result["original_source_sha256"], before[0]); self.assertEqual(result["native_mdl_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(sorted(self.directory.iterdir()), files); self.assertEqual(identity(path), before)

    def test_gma_duplicate_and_unsafe_unselected_names_refuse(self):
        raw, _ = fixture(); path = self.directory / "authored.gma"
        for rows in [[("models/authored.mdl", raw), ("Models/AUTHORED.mdl", raw)],
                     [("models/authored.mdl", raw), ("materials/CON.vmt", b"x")],
                     [("models/authored.mdl", raw), ("lua/../x.lua", b"x")]]:
            path.write_bytes(gma(rows))
            with self.assertRaises(ValueError): IO.inspect_choices(path, "models/authored.mdl")

    def test_gma_crc_corruption_and_unlisted_member_refuse(self):
        raw, _ = fixture(); path = self.directory / "authored.gma"; blob = gma([("models/authored.mdl", raw)])
        path.write_bytes(blob[:-1] + bytes([blob[-1] ^ 1]))
        with self.assertRaisesRegex(ValueError, "CRC"): IO.inspect_choices(path, "models/authored.mdl")
        path.write_bytes(blob)
        with self.assertRaisesRegex(ValueError, "absent"): IO.inspect_choices(path, "models/unlisted.mdl")

    def test_vpk_inline_and_segmented_payloads(self):
        raw, _ = fixture(); path = self.directory / "authored_dir.vpk"
        for archive in (0x7FFF, 0):
            path.write_bytes(vpk(raw, archive=archive))
            if archive == 0: (self.directory / "authored_000.vpk").write_bytes(raw)
            result = IO.inspect_choices(path, "models/authored.mdl")
            self.assertEqual(result["native_mdl_sha256"], hashlib.sha256(raw).hexdigest())

    def test_vpk_segment_changed_during_read_fails_finally(self):
        raw, _ = fixture(); path = self.directory / "authored_dir.vpk"; path.write_bytes(vpk(raw, archive=0))
        segment = self.directory / "authored_000.vpk"; segment.write_bytes(raw)
        original_read = IO.vpk_read
        def changing(*args):
            result = original_read(*args); segment.write_bytes(raw + b"changed"); return result
        with mock.patch.object(IO, "vpk_read", side_effect=changing):
            with self.assertRaisesRegex(ValueError, "changed during metadata"): IO.inspect_choices(path, "models/authored.mdl")

    def test_loose_input_changed_by_parser_fails_finally(self):
        raw, _ = fixture(); path = self.directory / "authored.mdl"; path.write_bytes(raw)
        def changing(*args): path.write_bytes(raw + b"changed"); raise ValueError("initial parser refusal")
        with mock.patch.object(IO, "catalogue", side_effect=changing):
            with self.assertRaisesRegex(ValueError, "changed during metadata"): IO.inspect_choices(path)

    def test_metadata_cli_returns_before_conversion_discovery(self):
        raw, _ = fixture(); path = self.directory / "authored.mdl"; path.write_bytes(raw)
        status = self.directory / "result.json"
        with mock.patch.object(sys, "argv", ["prepare_source.py", str(path), "--appearance-catalogue", "--status-file", str(status)]), mock.patch.object(P, "conversion_context", side_effect=AssertionError("discovery forbidden")), mock.patch.object(P.subprocess, "Popen", side_effect=AssertionError("process forbidden")):
            self.assertEqual(P.main(), 0)
        self.assertTrue(json.loads(status.read_bytes())["ok"])

    def test_metadata_entrypoint_never_overwrites_existing_result_or_original(self):
        raw, _ = fixture(); source = self.directory / "authored.mdl"; source.write_bytes(raw)
        result = self.directory / "existing.json"; result.write_bytes(b"existing owner result")
        for target in (source, result):
            before = identity(target)
            argv = ["prepare_source.py", str(source), "--appearance-catalogue", "--status-file", str(target)]
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    runpy.run_path(str(OVERLAY / "tools/prepare_source.py"), run_name="__main__")
            self.assertEqual(raised.exception.code, 1); self.assertEqual(identity(target), before)

    def test_metadata_error_result_uses_exclusive_create(self):
        source = self.directory / "malformed.mdl"; source.write_bytes(b"not an MDL")
        result = self.directory / "fresh.json"
        argv = ["prepare_source.py", str(source), "--appearance-catalogue", "--status-file", str(result)]
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                runpy.run_path(str(OVERLAY / "tools/prepare_source.py"), run_name="__main__")
        self.assertEqual(raised.exception.code, 1)
        self.assertFalse(json.loads(result.read_bytes())["ok"])

class WorkerAndSourceSeams(AuthoredCase):
    def worker(self, appearance=None, suffix=".mdl"):
        source = self.directory / ("original" + suffix); source.write_bytes(b"inert worker bytes")
        before = identity(source); output = self.directory / "bundle"
        addon = self.directory / "fake-addon"; (addon / "library/utils/pylib").mkdir(parents=True)
        argv = ["prepare_source.py", str(source), "--output", str(output), "--sourceio", str(addon), "--blender", "must-never-launch.exe"]
        if appearance is not None:
            req = {**request(), "source_sha256": before[0], "native_mdl_sha256": before[0], **appearance}
            req_path = self.directory / "request.json"; req_path.write_text(json.dumps(req), encoding="utf-8")
            argv += ["--appearance", str(req_path)]
        def fake_worker(*args, **kwargs):
            (output / "scene.glb").write_bytes(b"inert mocked result")
            return types.SimpleNamespace(pid=999999, returncode=0, poll=lambda: 0)
        context = {"discovery": {"providers": []}, "source_profile": "standalone", "gmod_installation": {}, "sfm_installations": []}
        with mock.patch.object(sys, "argv", argv), mock.patch.object(P, "conversion_context", return_value=context), mock.patch.object(P, "mount_paths", return_value=[]), mock.patch.object(P.subprocess, "Popen", side_effect=fake_worker) as process, contextlib.redirect_stdout(io.StringIO()):
            try: result = P.main()
            finally: self.assertEqual(identity(source), before)
        self.assertEqual(result, 0); self.assertEqual(process.call_count, 1)
        return json.loads((output / "conversion-request.json").read_bytes())

    def test_default_request_omits_optional_field(self):
        self.assertNotIn("appearance", self.worker())

    def test_explicit_selected_request_is_exact(self):
        value = self.worker({"skin": 2, "bodygroups": {"0": 0}})
        self.assertEqual(value["appearance"], {**request(2, {"0": 0}), "source_sha256": value["sha256"], "native_mdl_sha256": value["sha256"]})

    def test_explicit_map_request_refuses_before_process(self):
        with mock.patch.object(P.subprocess, "Popen", side_effect=AssertionError("real process forbidden")):
            with self.assertRaisesRegex(ValueError, "not a BSP"): self.worker({}, ".bsp")

    def test_default_bsp_request_preserved(self):
        self.assertNotIn("appearance", self.worker(suffix=".bsp"))

    def test_default_and_prop_load_model_match_base_using_inert_objects(self):
        module_name = "SourceIO.blender_bindings.shared.skins"
        fake_skins = types.ModuleType(module_name)
        observations = []
        changed = OVERLAY / "tools/blender_source_bridge.py"
        for label, source in (("base1236796.load_model", BASE_LOAD_MODEL), (str(changed), changed.read_text(encoding="utf-8"))):
            value = container(); skin_calls = []
            fake_skins.set_model_skin = lambda actor, skin: skin_calls.append(skin)
            node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "load_model")
            ns = {"import_model": lambda *args: value, "TinyPath": str, "cm": None, "model_options": lambda scale: scale,
                  "SteamAppId": types.SimpleNamespace(GARRYS_MOD=0), "put_into_collections": lambda *args: None, "Path": Path, "source_appearance": A}
            exec(compile(ast.Module(body=[node], type_ignores=[]), label, "exec"), ns)
            with mock.patch.dict(sys.modules, {module_name: fake_skins}):
                ns["load_model"]("test.mdl", object(), .01905, parent="prop-parent", skin=2)
            observations.append((states(value), skin_calls, [obj.parent for obj in value.objects]))
        self.assertEqual(*observations)

    def test_bridge_explicit_branch_applies_selection_without_touching_geometry(self):
        path = OVERLAY / "tools/blender_source_bridge.py"
        value = container(); before = [copy.deepcopy(o.data.__dict__) for o in value.objects]
        module_name = "SourceIO.blender_bindings.shared.skins"
        fake_skins = types.ModuleType(module_name); fake_skins.set_model_skin = mock.Mock()
        node = next(n for n in ast.parse(path.read_text(encoding="utf-8")).body if isinstance(n, ast.FunctionDef) and n.name == "load_model")
        ns = {"import_model": lambda *args: value, "TinyPath": str, "cm": None, "model_options": lambda scale: scale,
              "SteamAppId": types.SimpleNamespace(GARRYS_MOD=0), "put_into_collections": lambda *args: None, "Path": Path, "source_appearance": A}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)
        with mock.patch.dict(sys.modules, {module_name: fake_skins}):
            ns["load_model"]("authored.mdl", object(), .01905, appearance=request(2, {"1": 1}))
        fake_skins.set_model_skin.assert_called_once_with(value, 2)
        self.assertEqual(value.has_selected_appearance["selected_native_bodygroup_indices"], {"0": 0, "1": 1, "2": 0})
        self.assertEqual([o.hide_render for o in value.objects], [False, True, False])
        self.assertEqual([o.data.__dict__ for o in value.objects], before)

    def test_ui_default_map_and_nondefault_source_seams_are_present(self):
        # Source contract only, never claims a parsed/running Godot UI.
        importer = (OVERLAY / "src/source_import.gd").read_text(encoding="utf-8")
        chooser = (OVERLAY / "src/source_choice_dialog.gd").read_text(encoding="utf-8")
        self.assertIn('if as_model:\n\t\tappearance_ui = preload', importer)
        self.assertIn('if not appearance.is_empty():', importer)
        self.assertIn('args.append_array(["--appearance", appearance_path])', importer)
        self.assertIn('if not changed: return {}', chooser)
        self.assertIn('if not enabled.button_pressed: return true', chooser)
        self.assertIn('dialog.tree_exiting.connect(invalidate)', chooser)
        self.assertIn('generation += 1', chooser)
        # Godot JSON numbers are floats; canonical numeric group keys require
        # an explicit integer cast at the UI->strict Python request boundary.
        self.assertIn('bodygroups[str(int(group.index))] = value', chooser)
        self.assertNotIn('bodygroups[str(group.index)]', chooser)

def main():
    import time
    global RUN
    RUN = TASK / "runs" / (str(time.time_ns()) + "-cpu")
    RUN.mkdir(parents=True, exist_ok=False)
    protected = [*sorted((OVERLAY / "tools").glob("*.py")), *sorted((OVERLAY / "src").glob("*.gd")),
                 *sorted((OVERLAY / "tests").glob("*.py"))]
    before = {str(p): identity(p) for p in protected}
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    preserved = {str(p): identity(p) for p in protected} == before
    (RUN / "unittest.log").write_text(stream.getvalue(), encoding="utf-8")
    report = {"format": "studio_static_choices_draft_cpu_1", "passed": result.wasSuccessful() and preserved,
              "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "source_preserved": preserved, "sources": before, "run": str(RUN),
              "runtime_scope": "Python authored fixtures and mocked subprocesses only; no Godot/Blender/conversion/GPU/native reads"}
    (RUN / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("passed", "tests", "failures", "errors", "source_preserved", "run")}))
    if not report["passed"]: print(stream.getvalue())
    return 0 if report["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
