import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from source_paths import DEFAULT_GMOD, DEFAULT_WORKSHOP, require_gmod


class SourcePathTests(unittest.TestCase):
    def install(self, directory, marker='"GameInfo" { FileSystem { SteamAppId 4000 } }'):
        game = Path(directory) / "Steam library/GarrysMod"
        (game / "garrysmod").mkdir(parents=True)
        (game / "garrysmod/gameinfo.txt").write_text(marker, encoding="utf-8")
        (game / "garrysmod/garrysmod_dir.vpk").write_bytes(b"fixture")
        return game

    def test_owner_defaults(self):
        self.assertEqual(DEFAULT_GMOD, r"C:\Program Files (x86)\Steam\steamapps\common\GarrysMod")
        self.assertEqual(DEFAULT_WORKSHOP, r"C:\Program Files (x86)\Steam\steamapps\workshop\content\4000")

    def test_custom_library_presence_and_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = self.install(tmp)
            files = {p: p.read_bytes() for p in game.rglob("*") if p.is_file()}
            self.assertEqual(require_gmod(game), game.resolve())
            self.assertEqual(files, {p: p.read_bytes() for p in game.rglob("*") if p.is_file()})

    def test_missing_game_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError, "must already be installed"):
            require_gmod(tmp)

    def test_wrong_game_and_commented_id_rejected(self):
        for marker in ('SteamAppId 220', '// SteamAppId 4000\nSteamAppId 220'):
            with tempfile.TemporaryDirectory() as tmp:
                game = self.install(tmp, marker)
                with self.assertRaises(ValueError): require_gmod(game)

    def test_incomplete_installation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = self.install(tmp)
            (game / "garrysmod/garrysmod_dir.vpk").unlink()
            with self.assertRaisesRegex(ValueError, "incomplete"): require_gmod(game)

    def test_cli_external_file_reaches_converter_without_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "own-model.mdl"; source.write_bytes(b"IDST")
            output = Path(tmp) / "prepared"
            addon = Path(tmp) / "sourceio"; (addon / "library/utils/pylib").mkdir(parents=True)
            result = subprocess.run([sys.executable, str(ROOT / "tools/prepare_source.py"), str(source),
                                     "--gmod", str(Path(tmp) / "missing-game"), "--sourceio", str(addon),
                                     "--blender", sys.executable, "--output", str(output)],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("must already be installed", result.stderr)
            self.assertIn("Conversion failed", result.stderr)
            request = json.loads((output / "conversion-request.json").read_text())
            self.assertEqual(request['source_profile'], 'standalone')
            self.assertEqual(request['gmod_installation'], '')
            self.assertEqual(source.read_bytes(), b'IDST')


if __name__ == "__main__": unittest.main()
