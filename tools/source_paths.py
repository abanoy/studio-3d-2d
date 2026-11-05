"""Local GMod installation preflight. Never installs, downloads or launches the game."""
from pathlib import Path
import re

DEFAULT_GMOD = r"C:\Program Files (x86)\Steam\steamapps\common\GarrysMod"
DEFAULT_WORKSHOP = r"C:\Program Files (x86)\Steam\steamapps\workshop\content\4000"


def require_gmod(root):
    root = Path(root).expanduser().resolve()
    marker = root / "garrysmod/gameinfo.txt"
    message = "Garry's Mod must already be installed for native Source imports. Studio does not include or install it. Select your GarrysMod installation folder: "
    if not marker.is_file() or marker.stat().st_size > 1024 * 1024:
        raise ValueError(message + str(root))
    content = re.sub(r"//[^\r\n]*", "", marker.read_text(encoding="utf-8-sig"))
    if not re.search(r'\bSteamAppId"?\s+"?4000\b', content, re.IGNORECASE):
        raise ValueError(message + str(root))
    if not (root / "garrysmod/garrysmod_dir.vpk").is_file():
        raise ValueError("Garry's Mod content is incomplete (garrysmod_dir.vpk missing). Verify the installation in Steam: " + str(root))
    return root
