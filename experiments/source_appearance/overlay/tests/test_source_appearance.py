"""CPU appearance contract; real native metadata and pinned skin-helper code.

Containers/materials are inert stand-ins. No Blender, extraction, GPU or native
scene conversion occurs; rendered native acceptance remains a separate gate.
"""
from pathlib import Path
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import itertools
import json
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import source_appearance as A
import prepare_source as P

CASES = json.loads((ROOT / "docs/benchmarks/sfm_native_feature_inventory_2026-11-12.json").read_bytes())["next_cases"]
NITORI = CASES["multi_skin_glove"]
KEIKI = CASES["keiki_tools_chisels"]
# Exact selected row from the retained complete metadata for this checksum.
# This supplies material labels, never texture bytes or generated geometry.
KEIKI_SKINS = [["models/touhou/tamo/Keiki Haniyashin/props", "box", "blush", "excl mark"]]


class Material:
    def __init__(self, name): self.name = name


class Mesh(dict):
    __hash__ = object.__hash__
    def __init__(self, name, materials, vertices, flexes=0):
        super().__init__(active_skin="0", model_type="s1", skin_groups=materials)
        self.name = name
        self.type = "MESH"
        self.hide_render = False
        self.hidden = False
        self.material_slots = [types.SimpleNamespace(material=m, link="DATA") for m in materials["0"][:2]]
        self.data = types.SimpleNamespace(polygons=[(0, 1, 2)], geometry=(name, vertices), weights=((0, 1.),), shape_keys={"Tools": .375} if flexes else {})
    def hide_set(self, hidden): self.hidden = hidden
    def __eq__(self, other): return self is other


def request(case=NITORI, skin=0, groups=None):
    return {"format": A.FORMAT, "source_sha256": "a" * 64, "native_mdl_sha256": case["sha256"], "skin": skin, "bodygroups": dict(groups or {})}


def container(case, skin_rows=None):
    # Native choice labels/counts/zero geometry come from the actual inventory.
    # Keiki's compact record omits its one skin's material table; use the exact
    # selected row retained above, still with inert Material objects.
    names = skin_rows or case.get("skin_groups") or KEIKI_SKINS
    pool = {name: Material(name) for row in names for name in row}
    skin_groups = [[pool[name] for name in row] for row in names]
    skin_props = {str(i): row for i, row in enumerate(skin_groups)}
    parts, groups, objects = [], {}, []
    for group in case["bodygroups"]:
        models, variants = [], []
        for choice in group["choices"]:
            models.append(types.SimpleNamespace(name=choice["name"], vertex_count=choice["vertices"]))
            obj = None if choice["vertices"] == 0 else Mesh(choice["name"], skin_props, choice["vertices"], choice.get("mesh_flex_records", 0))
            variants.append(obj)
            if obj is not None: objects.append(obj)
        parts.append(types.SimpleNamespace(name=group["name"], models=models))
        groups[group["name"]] = variants
    mdl = types.SimpleNamespace(body_parts=parts, skin_groups=skin_groups, materials=list(pool.values()))
    return types.SimpleNamespace(objects=objects, bodygroups=groups, mdl=mdl, armature=types.SimpleNamespace(parent=None), bones=("unchanged native bindings",))


def state(value):
    return [(obj.name, obj.hidden, obj.hide_render, [slot.material.name for slot in obj.material_slots]) for obj in value.objects]


class AppearanceContract(unittest.TestCase):
    def test_positive_native_counts_and_true_blanks(self):
        self.assertEqual(NITORI["skin_family_count"], 3)
        self.assertEqual([r["vertices"] for r in NITORI["bodygroups"][0]["choices"]], [6544, 0])
        self.assertEqual([r["name"] for r in KEIKI["tools_controllers"]], ["Tools"])
        self.assertEqual([r["name"] for r in KEIKI["bodygroups"]], ["tools", "box", "flame"])
        self.assertEqual(A.catalogue(container(NITORI))["bodygroups"][0]["choices"][1]["blank"], True)

    def test_all_seven_visible_keiki_combinations_and_all_blank_refusal(self):
        for choices in itertools.product([0, 1], repeat=3):
            with self.subTest(choices=choices):
                value = container(KEIKI)
                plan = request(KEIKI, groups={str(i): c for i, c in enumerate(choices)})
                if choices == (1, 1, 1):
                    with self.assertRaisesRegex(ValueError, "no renderable geometry"): A.choose(value, plan)
                else:
                    result = A.choose(value, plan)
                    self.assertEqual({obj.name for obj in result["active"]}, {KEIKI["bodygroups"][i]["choices"][0]["name"] for i, c in enumerate(choices) if c == 0})
                    self.assertEqual(result["selected_native_bodygroup_indices"], plan["bodygroups"])

    def test_single_glove_blank_refuses_without_mutation(self):
        value = container(NITORI); before = state(value)
        callback = mock.Mock()
        with self.assertRaisesRegex(ValueError, "no renderable geometry"): A.apply(value, request(groups={"0": 1}), callback)
        self.assertEqual(state(value), before); callback.assert_not_called()

    def test_partial_bodygroup_request_keeps_native_zero_defaults(self):
        result = A.choose(container(KEIKI), request(KEIKI, groups={"1": 1}))
        self.assertEqual(result["selected_bodygroup_indices"], {"tools": 0, "box": 1, "flame": 0})

    def test_named_blank_with_native_geometry_remains_visible(self):
        case = copy.deepcopy(KEIKI)
        native = CASES["keiki_tools_main"]["bodygroups"][1]["choices"][0]
        self.assertEqual((native["name"], native["vertices"], native["blank"]), ("blank", 14521, False))
        case["bodygroups"] = [{"name": "clamped1", "choices": [native]}]
        self.assertFalse(A.catalogue(container(case))["bodygroups"][0]["choices"][0]["blank"])

    def test_native_out_of_range_choices_fail_before_callback(self):
        for changes in [{"skin": 3}, {"bodygroups": {"1": 0}}, {"bodygroups": {"0": 2}}]:
            with self.subTest(changes=changes):
                value = container(NITORI); before = state(value); callback = mock.Mock()
                with self.assertRaises(ValueError): A.apply(value, {**request(), **changes}, callback)
                callback.assert_not_called(); self.assertEqual(before, state(value))

    def test_ambiguous_default_skin_columns_are_not_guessed(self):
        value = container(NITORI, [["same", "same"], ["different-a", "different-b"]])
        with self.assertRaisesRegex(ValueError, "Ambiguous native skin columns"): A.choose(value, request(skin=1))

    def test_nonidentity_native_skin_table_is_not_inferred_from_material_names(self):
        value = container(NITORI); value.mdl.materials = list(reversed(value.mdl.materials))
        before = state(value); callback = mock.Mock()
        with self.assertRaisesRegex(ValueError, "Nonidentity default skin tables"): A.apply(value, request(skin=1), callback)
        callback.assert_not_called(); self.assertEqual(before, state(value))

    def test_duplicate_or_missing_native_groups_refuse(self):
        for mode in ["duplicate", "missing", "truncated", "wrong_blank"]:
            with self.subTest(mode=mode):
                value = container(KEIKI)
                if mode == "duplicate": value.mdl.body_parts[1].name = value.mdl.body_parts[0].name
                elif mode == "missing": value.bodygroups.pop("box")
                elif mode == "truncated": value.bodygroups["tools"].pop()
                else: value.bodygroups["tools"][1] = value.objects[0]
                with self.assertRaises(ValueError): A.choose(value, request(KEIKI))

    def test_request_rejects_invalid_types_unknown_fields_and_bounds(self):
        invalid = [{**request(), "skin": True}, {**request(), "skin": 1.}, {**request(), "skin": 256}, {**request(), "bodygroups": {"00": 0}}, {**request(), "bodygroups": {"256": 0}}, {**request(), "bodygroups": {"0": -1}}, {**request(), "bodygroups": {"0": False}}, {**request(), "extra": 0}, {**request(), "source_sha256": "A" * 64}]
        for item in invalid:
            with self.subTest(item=item):
                with self.assertRaises(ValueError): A.validate(item)

    def test_request_is_detached(self):
        original = request(); result = A.validate(original); result["bodygroups"]["0"] = 1
        self.assertEqual(original["bodygroups"], {})

    def test_bounded_duplicate_key_and_original_checksum_refusal(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "output") as folder:
            path = Path(folder) / "appearance.json"
            for raw in [b" " * (A.MAX_REQUEST + 1), b'{"format":1,"format":2}', json.dumps(request()).encode()]:
                path.write_bytes(raw)
                with self.assertRaises(ValueError): A.load(path, "b" * 64)


class PinnedSkinAndBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pin = os.environ.get("HYBRID_SOURCEIO")
        if not pin: raise unittest.SkipTest("Set HYBRID_SOURCEIO to the approved pinned runtime for actual skin-helper CPU coverage")
        cls.skin_path = Path(pin) / "blender_bindings/shared/skins.py"
        source = cls.skin_path.read_text(encoding="utf-8")
        functions = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)]
        fake_bpy = types.SimpleNamespace(types=types.SimpleNamespace(Material=Material))
        skin_ns = {"bpy": fake_bpy}
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(cls.skin_path), "exec"), skin_ns)
        cls.set_skin = staticmethod(skin_ns["set_skin"])
        cls.set_model_skin = staticmethod(skin_ns["set_model_skin"])

    def test_actual_pinned_skin_helper_three_families_and_return(self):
        value = container(NITORI); obj = value.objects[0]
        original_geometry = copy.deepcopy(obj.data.__dict__)
        for skin in [1, 2, 0]:
            result = A.apply(value, request(skin=skin), self.set_model_skin)
            self.assertEqual([slot.material.name for slot in obj.material_slots], NITORI["skin_groups"][skin][:2])
            self.assertEqual(obj["skin_slots"], [0, 1])
            self.assertEqual(result["selected_skin"], skin)
            self.assertTrue(all(slot.link == "OBJECT" for slot in obj.material_slots))
        self.assertEqual(obj.data.__dict__, original_geometry)

    def test_keiki_tools_flex_weights_bones_and_native_metadata_untouched(self):
        value = container(KEIKI)
        snapshot = [(obj.data.geometry, obj.data.weights, copy.deepcopy(obj.data.shape_keys)) for obj in value.objects]
        bones = value.bones; metadata = [(p.name, [(m.name, m.vertex_count) for m in p.models]) for p in value.mdl.body_parts]
        result = A.apply(value, request(KEIKI, groups={"1": 1, "2": 1}), self.set_model_skin)
        self.assertEqual([obj.hide_render for obj in value.objects], [False, True, True])
        self.assertEqual([(obj.data.geometry, obj.data.weights, obj.data.shape_keys) for obj in value.objects], snapshot)
        self.assertEqual(value.bones, bones)
        self.assertEqual([(p.name, [(m.name, m.vertex_count) for m in p.models]) for p in value.mdl.body_parts], metadata)
        self.assertEqual(json.loads(json.dumps(result))["selected_native_bodygroup_indices"], {"0": 0, "1": 1, "2": 1})

    def test_actual_bridge_default_and_prop_paths_match_old_function(self):
        baseline = Path(os.environ["HAS_APPEARANCE_BASE_BRIDGE"])
        changed = ROOT / "tools/blender_source_bridge.py"
        module_name = "SourceIO.blender_bindings.shared.skins"
        skin_module = types.ModuleType(module_name); skin_module.set_model_skin = self.set_model_skin
        for case in [NITORI, KEIKI]:
            for skin in [0, min(case["skin_family_count"] - 1, 1)]:
                observations = []
                for path in [baseline, changed]:
                    actor = container(case)
                    node = next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == "load_model")
                    ns = {"import_model": lambda *args: actor, "TinyPath": str, "cm": None, "model_options": lambda scale: scale, "SteamAppId": types.SimpleNamespace(GARRYS_MOD=0), "put_into_collections": lambda *args: None, "Path": Path, "source_appearance": A}
                    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)
                    with mock.patch.dict(sys.modules, {module_name: skin_module}): ns["load_model"]("model.mdl", object(), .01905, parent=object(), skin=skin)
                    observations.append(state(actor))
                self.assertEqual(*observations)


class WorkerRequest(unittest.TestCase):
    def context(self):
        return {"discovery": {"providers": []}, "source_profile": "standalone", "gmod_installation": {}, "sfm_installations": []}

    def run_worker(self, folder, appearance=None, suffix=".mdl"):
        source = folder / ("original" + suffix); source.write_bytes(b"Original inert worker request fixture")
        before = (hashlib.sha256(source.read_bytes()).hexdigest(), source.stat().st_mtime_ns)
        runtime = folder / "inert-runtime-layout/library/utils/pylib"; runtime.mkdir(parents=True)
        output = folder / "bundle"
        argv = ["prepare_source.py", str(source), "--output", str(output), "--sourceio", str(runtime.parents[2]), "--blender", "never-launched.exe"]
        if appearance is not None:
            value = {**request(), "source_sha256": before[0], "native_mdl_sha256": before[0], **appearance}
            path = folder / "appearance.json"; path.write_text(json.dumps(value)); argv += ["--appearance", str(path)]
        called = []
        def worker(args, **kwargs):
            called.append(args)
            (output / "scene.glb").write_bytes(b"glTF inert mocked worker output")
            return types.SimpleNamespace(pid=999999, returncode=0, poll=lambda: 0)
        with mock.patch.object(sys, "argv", argv), mock.patch.object(P, "conversion_context", return_value=self.context()), mock.patch.object(P, "mount_paths", return_value=[]), mock.patch.object(P.subprocess, "Popen", side_effect=worker), contextlib.redirect_stdout(io.StringIO()):
            result = P.main()
        self.assertEqual((hashlib.sha256(source.read_bytes()).hexdigest(), source.stat().st_mtime_ns), before)
        self.assertEqual(result, 0); self.assertEqual(len(called), 1)
        return json.loads((output / "conversion-request.json").read_text())

    def test_default_cli_request_has_no_appearance_property(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "output") as folder:
            self.assertNotIn("appearance", self.run_worker(Path(folder)))

    def test_static_selection_transport_is_exact_and_original_unchanged(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "output") as folder:
            result = self.run_worker(Path(folder), {"skin": 2, "bodygroups": {"0": 0}})
            self.assertEqual(result["appearance"]["skin"], 2)
            self.assertEqual(result["appearance"]["bodygroups"], {"0": 0})
            self.assertEqual(result["appearance"]["source_sha256"], result["sha256"])

    def test_bsp_selection_refuses_before_worker(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "output") as folder:
            with self.assertRaisesRegex(ValueError, "not a BSP"): self.run_worker(Path(folder), {}, suffix=".bsp")


if __name__ == "__main__": unittest.main()
