from pathlib import Path
import json
import contextlib
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from source_content import kv_read, child, value, vpk_index, vpk_read, discover, assets, mount_paths, libraries
from source_paths import DEFAULT_WORKSHOP
from asset_audit import AssetError


def vpk(path, payload=b"IDSTnative", version=1, segment=0x7FFF, name="test"):
    preload = payload[:3]; body = payload[3:]
    tree = b"mdl\0models/props\0" + name.encode() + b"\0"
    tree += struct.pack("<IHHIIH", zlib.crc32(payload), len(preload), segment, 0, len(body), 0xFFFF) + preload + b"\0\0\0"
    header = struct.pack("<III", 0x55AA1234, version, len(tree)) + (struct.pack("<IIII", len(body), 0, 0, 0) if version == 2 else b"")
    path.write_bytes(header + tree + (body if segment == 0x7FFF else b""))
    if segment != 0x7FFF: path.with_name(path.name.removesuffix("_dir.vpk") + f"_{segment:03}.vpk").write_bytes(body)


class ContentTests(unittest.TestCase):
    def setUp(self):
        # Fixture discovery must not depend on games installed while tests run.
        isolated = patch.dict(sys.modules, {"winreg": None})
        isolated.start(); self.addCleanup(isolated.stop)
    def root(self, tmp):
        game = Path(tmp) / "Steam/steamapps/common/GarrysMod"
        (game / "garrysmod/cfg").mkdir(parents=True)
        return game

    def test_shallow_game_root_has_no_assumed_steam_ancestor(self):
        self.assertEqual(libraries(Path.cwd().anchor),[])
        with tempfile.TemporaryDirectory() as directory:
            result=discover(Path.cwd().anchor,Path(directory)/'absent')
        self.assertEqual(result['libraries'],[])

    def test_blank_workshop_does_not_discover_current_project_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);game=self.root(root);project=root/'project';project.mkdir();(project/'unrelated.gma').write_bytes(b'fixture')
            with contextlib.chdir(project):result=discover(game,Path('.'))
            self.assertFalse(any(p['path']==str(project/'unrelated.gma') for p in result['providers']))

    def test_vpk1_embedded_preload_crc(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test_dir.vpk"; vpk(path)
            row = vpk_index(path)[0]
            self.assertEqual(row["path"], "models/props/test.mdl")
            self.assertEqual(vpk_read(path, row), b"IDSTnative")

    def test_vpk2_numbered_segment(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test_dir.vpk"; vpk(path, version=2, segment=3)
            self.assertEqual(vpk_read(path, vpk_index(path)[0]), b"IDSTnative")

    def test_vpk_crc_and_truncation_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test_dir.vpk"; vpk(path)
            row = vpk_index(path)[0]
            path.write_bytes(path.read_bytes()[:-1] + b"!")
            with self.assertRaises(AssetError): vpk_read(path, row)
            path.write_bytes(path.read_bytes()[:-2])
            with self.assertRaises(AssetError): vpk_read(path, row)

    def test_vpk_path_and_header_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test_dir.vpk"; vpk(path, name="../escape")
            with self.assertRaises(AssetError): vpk_index(path)
            path.write_bytes(struct.pack("<III", 0x55AA1234, 2, 100000000))
            with self.assertRaises(AssetError): vpk_index(path)

    def test_keyvalues_duplicate_searchpaths_comments_and_backslashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gameinfo.txt"
            path.write_text('"GameInfo" { // ignored\n "FileSystem" { "SearchPaths" { Game "usermod" Game "C:\\test\\models" } } }')
            rows = child(child(child(kv_read(path), "gameinfo"), "filesystem"), "searchpaths")
            self.assertEqual(rows, [("Game", "usermod"), ("Game", r"C:\test\models")])

    def test_keyvalues_broken_nesting_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.cfg"; path.write_text('"a" { "b" "c"')
            with self.assertRaises(AssetError): kv_read(path)

    def test_addons_download_gamemode_and_missing_mount(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = self.root(tmp); content = game / "garrysmod"
            for sub in ("addons/local/models", "download/materials", "gamemodes/my-mode/content/models"):
                (content / sub).mkdir(parents=True)
            (content / "cfg/mount.cfg").write_text('"mountcfg" { "cstrike" "'+str(Path(tmp)/'missing').replace('\\','/')+'" }')
            d = discover(game, Path(tmp) / "no-workshop")
            self.assertTrue(any(p["origin"] == "gamemode" for p in d["providers"]))
            missing = next(p for p in d["providers"] if p["origin"] == "mount.cfg")
            self.assertFalse(missing["present"])
            self.assertTrue(any(p["origin"] == "download" for p in d["providers"]))

    def test_workshop_index_does_not_extract_lua(self):
        from test_source_archive import archive
        with tempfile.TemporaryDirectory() as tmp:
            game = self.root(tmp); workshop = Path(tmp) / "workshop/4000/123"; workshop.mkdir(parents=True)
            path = workshop / "addon.gma"; raw = archive([("models/test.mdl", b"IDST"), ("lua/a.lua", b"execute nothing")]); path.write_bytes(raw)
            d = discover(game, workshop.parent)
            provider = next(p for p in d["providers"] if p["path"] == str(path.resolve()))
            self.assertTrue(provider["enabled"])
            self.assertEqual(assets(provider)["assets"][0]["path"], "models/test.mdl")
            self.assertEqual(path.read_bytes(), raw)
            self.assertFalse((workshop / "lua").exists())

    def test_alternate_library_manifest_and_disabled_depot(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = self.root(tmp); steam = game.parents[2]; library = Path(tmp) / "OtherSteam"
            target = library / "steamapps/common/MyCSS/cstrike"; target.mkdir(parents=True)
            (target / "gameinfo.txt").write_text('"GameInfo" {}')
            (library / "steamapps/appmanifest_240.acf").write_text('"AppState" { "installdir" "MyCSS" }')
            (steam / "steamapps/libraryfolders.vdf").write_text('"libraryfolders" { "1" { "path" "'+str(library).replace('\\','/')+'" } }')
            (game / "garrysmod/cfg/mountdepots.txt").write_text('"gamedepotsystem" { "cstrike" "0" }')
            d = discover(game, Path(tmp)/"missing")
            provider = next(p for p in d["providers"] if p["path"] == str(target.resolve()))
            self.assertFalse(provider["enabled"])
            self.assertTrue(d["games"][0]["installed"])
            self.assertNotIn(provider["path"], mount_paths(d))

    def test_empty_sfm_placeholder_is_not_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = self.root(tmp); (game.parent / "SourceFilmmaker").mkdir()
            self.assertFalse(discover(game, Path(tmp)/"missing")["games"][-1]["installed"])

    def test_synthetic_sfm_searchpath_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = self.root(tmp); sfm = game.parent / "SourceFilmmaker/game"; (sfm / "usermod").mkdir(parents=True)
            (sfm / "custom/models").mkdir(parents=True)
            (sfm / "usermod/gameinfo.txt").write_text('"GameInfo" { "FileSystem" { "SearchPaths" { Game "|gameinfo_path|." Game custom } } }')
            d = discover(game, Path(tmp)/"missing")
            self.assertTrue(d["games"][-1]["installed"])
            custom = next(p for p in d["providers"] if p["path"] == str((sfm/"custom").resolve()))
            self.assertTrue(custom["enabled"])

    def test_sfm_workshop_layouts_and_custom_packs(self):
        from test_source_archive import archive
        with tempfile.TemporaryDirectory() as tmp:
            game = self.root(tmp); sfm = game.parent / "SourceFilmmaker/game"
            (sfm / "usermod").mkdir(parents=True)
            (sfm / "usermod/gameinfo.txt").write_text('"GameInfo" { "FileSystem" { "SearchPaths" { Game "|GAMEINFO_PATH|." Game workshop Game tf } } }')
            (sfm / "workshop/models").mkdir(parents=True)
            (sfm / "workshop/models/installed.mdl").write_bytes(b"IDST")
            (sfm / "custompack/materials").mkdir(parents=True)
            workshop = game.parents[1] / "workshop/content/1840/123"
            workshop.mkdir(parents=True)
            package = workshop / "resources.gma"
            package.write_bytes(archive([("models/shared.mdl", b"IDST"), ("scripts/rig.py", b"not executed")]))
            vpk(workshop / "packed_dir.vpk", version=2, segment=0)
            (workshop / "content/maps").mkdir(parents=True)
            (workshop / "content/maps/map.bsp").write_bytes(b"VBSP")
            d = discover(game, Path(tmp)/"missing")
            by_path = {p["path"]: p for p in d["providers"]}
            self.assertEqual(by_path[str((sfm/"usermod").resolve())]["origin"], "sfm")
            self.assertEqual(assets(by_path[str((sfm/"workshop").resolve())])["assets"][0]["path"], "models/installed.mdl")
            self.assertEqual(by_path[str((sfm/"custompack").resolve())]["origin"], "sfm-custom")
            self.assertTrue(by_path[str(package.resolve())]["enabled"])
            self.assertIn(str((workshop/"packed_dir.vpk").resolve()), by_path)
            self.assertNotIn(str((workshop/"packed_000.vpk").resolve()), by_path)
            self.assertIn(str((workshop/"content").resolve()), by_path)
            self.assertFalse(d["warnings"])

    def test_contextual_dependency_order_and_explicit_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = self.root(tmp); sfm = game.parent / "SourceFilmmaker/game"
            (sfm / "usermod").mkdir(parents=True)
            (sfm / "tf/models").mkdir(parents=True)
            (sfm / "usermod/gameinfo.txt").write_text('"GameInfo" { "FileSystem" { "SearchPaths" { Game usermod Game tf Game workshop } } }')
            d = discover(game, Path(tmp)/"missing")
            gmod_path = str((game/"garrysmod").resolve()); sfm_path = str((sfm/"tf").resolve())
            self.assertLess(mount_paths(d).index(gmod_path), mount_paths(d).index(sfm_path))
            plan = mount_paths(d, sfm/"tf/models/a.mdl")
            self.assertLess(plan.index(sfm_path), plan.index(gmod_path))
            self.assertTrue(any("no local Workshop" in w for w in d["warnings"]))
            next(p for p in d["providers"] if p["path"] == sfm_path)["enabled"] = False
            self.assertNotIn(sfm_path, mount_paths(d, sfm/"tf/models/a.mdl"))

    def test_loose_index_lists_only_importable_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root/"models").mkdir(); (root/"maps").mkdir()
            (root/"models/test.mdl").write_bytes(b"IDST"); (root/"models/a.lua").write_bytes(b"never")
            (root/"maps/test.bsp").write_bytes(b"VBSP")
            result = assets({"path":str(root),"label":"test"})
            self.assertEqual({a["kind"] for a in result["assets"]}, {"model", "map"})
            self.assertEqual(len(result["assets"]), 2)


if __name__ == "__main__": unittest.main()
