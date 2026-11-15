"""Bounded, read-only Source content discovery and indexes. No game/add-on code runs."""
from pathlib import Path
import io
import os
import re
import struct
import zlib

from asset_audit import AssetError, Reader, gma_index, legacy_prefix
from source_archive import resource_path

MAX_ENTRIES = 100000
MAX_RESOURCE = 128 * 1024 * 1024
MAX_TREE = 32 * 1024 * 1024


def kv_read(path):
    """Small KeyValues data reader retaining order/duplicate keys; never executes includes."""
    path = Path(path)
    if not path.is_file(): return []
    if path.stat().st_size > 1024 * 1024: raise AssetError("Config exceeds 1 MiB: " + str(path))
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    tokens = []
    for match in re.finditer(r'//[^\r\n]*|"((?:\\.|[^"\\])*)"|([{}])|([^\s{}"]+)', text):
        if match[0].startswith("//"): continue
        token = match[1].replace('\\"', '"').replace('\\\\', '\\') if match[1] is not None else match[2] or match[3]
        tokens.append(token)
        if len(tokens) > 100000: raise AssetError("Excessive config tokens")
    cursor = 0
    def block(depth=0, closing=False):
        nonlocal cursor
        if depth > 16: raise AssetError("Excessive config nesting")
        rows = []
        while cursor < len(tokens):
            key = tokens[cursor]; cursor += 1
            if key == "}":
                if not closing: raise AssetError("Unexpected config brace")
                return rows
            if cursor >= len(tokens): raise AssetError("Incomplete config key/value")
            value = tokens[cursor]; cursor += 1
            if value == "{": value = block(depth + 1, True)
            rows.append((key, value))
        if closing: raise AssetError("Unclosed config block")
        return rows
    return block()


def child(rows, key):
    return next((v for k, v in rows if k.lower() == key.lower() and isinstance(v, list)), [])


def value(rows, key, default=""):
    return next((v for k, v in rows if k.lower() == key.lower() and isinstance(v, str)), default)


def vpk_index(path):
    """Valve VPK1/2 directory tree; payload remains in its original segments."""
    path = Path(path)
    with path.open("rb") as stream:
        header = stream.read(12)
        if len(header) != 12: raise AssetError("Short VPK header")
        magic, version, tree_size = struct.unpack("<III", header)
        if magic != 0x55AA1234 or version not in (1, 2) or not 1 <= tree_size <= MAX_TREE:
            raise AssetError("Unsupported/broken VPK directory")
        header_size = 28 if version == 2 else 12
        stream.seek(header_size)
        tree = stream.read(tree_size)
        if len(tree) != tree_size: raise AssetError("Truncated VPK tree")
    data = io.BytesIO(tree); reader = Reader(data); rows = []; names = set()
    while extension := reader.zero():
        while folder := reader.zero():
            while basename := reader.zero():
                crc, preload, archive, offset, length, terminator = reader.unpack("IHHIIH")
                if terminator != 0xFFFF: raise AssetError("Invalid VPK entry terminator")
                name = resource_path(("" if folder == " " else folder + "/") + basename + ("" if extension == " " else "." + extension))
                if name.casefold() in names: raise AssetError("Duplicate VPK resource path")
                names.add(name.casefold())
                preload_offset = data.tell()
                reader.read(preload)
                rows.append({"path": name, "crc32": crc, "preload": preload, "preload_offset": header_size + preload_offset,
                             "archive": archive, "offset": offset, "length": length, "bytes": preload + length,
                             "data_offset": header_size + tree_size})
                if len(rows) > MAX_ENTRIES: raise AssetError("VPK index exceeds 100000 entries")
    return rows


def vpk_read(path, entry):
    path = Path(path)
    if entry["bytes"] > MAX_RESOURCE: raise AssetError("VPK resource exceeds 128 MiB")
    with path.open("rb") as stream:
        stream.seek(entry["preload_offset"]); blob = stream.read(entry["preload"])
    if len(blob) != entry["preload"]: raise AssetError("Truncated VPK preload")
    segment = path if entry["archive"] == 0x7FFF else path.with_name(path.name.removesuffix("_dir.vpk") + f'_{entry["archive"]:03}.vpk')
    if entry["length"]:
        offset = entry["offset"] + (entry["data_offset"] if entry["archive"] == 0x7FFF else 0)
        with segment.open("rb") as stream:
            if offset + entry["length"] > segment.stat().st_size: raise AssetError("VPK payload exceeds segment")
            stream.seek(offset); blob += stream.read(entry["length"])
    if len(blob) != entry["bytes"] or zlib.crc32(blob) & 0xFFFFFFFF != entry["crc32"]:
        raise AssetError("VPK resource length/CRC differs: " + entry["path"])
    return blob


def archive_index(path):
    path = Path(path)
    if path.suffix.lower() == ".vpk": return {"title": path.stem, "entries": vpk_index(path)}
    if path.suffix.lower() == ".bin":
        prefix, size = legacy_prefix(path)
        return gma_index(prefix, size if size is not None else 512 * 1024 * 1024)
    with path.open("rb") as stream:
        return gma_index(stream, path.stat().st_size)


def content_files(root,include_particles=False):
    root = Path(root).resolve(); count = 0
    for directory in [root / "models", root / "maps"]+([root / "particles"]if include_particles else []):
        if not directory.is_dir(): continue
        for parent, dirs, files in os.walk(directory, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not (Path(parent) / d).is_symlink())
            for name in sorted(files):
                count += 1
                if count > MAX_ENTRIES: raise AssetError("Loose content scan exceeds 100000 files")
                path = Path(parent) / name
                if path.suffix.lower() not in ({".mdl", ".bsp", ".pcf"}if include_particles else {".mdl", ".bsp"}) or path.is_symlink(): continue
                if not path.resolve().is_relative_to(root): continue
                yield path


def assets(provider,include_particles=False):
    source = Path(provider["path"])
    if not source.exists(): raise AssetError("Content location is missing")
    if source.is_dir():
        return {"title": provider["label"], "assets": [{"path": p.relative_to(source).as_posix(), "bytes": p.stat().st_size,
                "kind": "particle"if p.suffix.lower()==".pcf"else "model" if p.suffix.lower() == ".mdl" else "map"} for p in content_files(source,include_particles)]}
    index = archive_index(source)
    return {"title": str(index.get("title", source.stem))[:200], "assets": [{"path": r.get("path", r.get("name")), "bytes": r.get("bytes", r.get("size", 0)),
            "kind": "particle"if r.get("path", r.get("name", "")).lower().endswith(".pcf")else "model" if r.get("path", r.get("name", "")).lower().endswith(".mdl") else "map"} for r in index["entries"]
            if r.get("path", r.get("name", "")).lower().endswith((".mdl", ".bsp", ".pcf")if include_particles else(".mdl", ".bsp"))]}


def libraries(game_root):
    game = Path(game_root).resolve()
    roots = [game.parents[2]] if len(game.parents)>2 else []
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            roots.append(Path(winreg.QueryValueEx(key, "SteamPath")[0]))
    except (ImportError, OSError): pass
    for root in list(roots):
        rows = child(kv_read(root / "steamapps/libraryfolders.vdf"), "libraryfolders")
        for _, block in rows:
            candidate = value(block, "path") if isinstance(block, list) else block
            if candidate: roots.append(Path(candidate))
    return list(dict.fromkeys(str(p.resolve()) for p in roots if p.is_dir()))


def discover(game_root, workshop_root, extra=()):
    game_root = Path(game_root).resolve(); content = game_root / "garrysmod"
    providers, warnings, seen = [], [], set()
    steam_libraries = libraries(game_root)
    def add(path, label, origin, enabled=True, installation=None):
        path = Path(path).resolve(); key = str(path).casefold()
        if key in seen: return
        if len(providers) >= 4096: raise AssetError("Content discovery exceeds 4096 locations")
        seen.add(key)
        providers.append({"path": str(path), "label": label, "origin": origin, "present": path.exists(), "enabled": enabled and path.exists(),
                          "kind": "folder" if path.is_dir() or not path.suffix else path.suffix.lower()[1:]})
        if installation is not None: providers[-1]['installation'] = str(Path(installation).resolve())
    def folder(path, label, origin, enabled=True, installation=None):
        path = Path(path)
        add(path, label, origin, enabled, installation)
        if path.is_dir():
            for archive in sorted(path.glob("*_dir.vpk")): add(archive, label + " / " + archive.stem, origin, enabled, installation)
    def expanded(path, label, origin, enabled=True):
        folder(path, label, origin, enabled)
        if Path(path).is_dir():
            for sub in sorted(Path(path).iterdir()):
                if sub.is_dir() and not sub.is_symlink() and any((sub / key).is_dir() for key in ("models", "materials", "maps")):
                    folder(sub, label + " / " + sub.name, origin, enabled)
    folder(content, "Garry's Mod / loose", "game")
    for name in ("sourceengine", "platform"): folder(game_root / name, name, "game")
    workshop_locations = ([] if str(workshop_root) in ("", ".") else [Path(workshop_root)]) + [Path(library) / "steamapps/workshop/content/4000" for library in steam_libraries]
    directories = list(dict.fromkeys([content / "addons", content / "cache/workshop", content / "workshop", *workshop_locations]))
    for directory in directories:
        if not directory.is_dir(): continue
        for item in sorted(directory.iterdir()):
            if item.is_symlink(): continue
            if item.is_file() and item.suffix.lower() in {".gma", ".bin"}: add(item, item.stem, "addon", item.suffix.lower() == ".gma")
            elif item.is_dir():
                if (item / "models").is_dir() or (item / "materials").is_dir() or (item / "maps").is_dir(): folder(item, item.name, "addon")
                for archive in sorted(item.iterdir()):
                    if archive.is_file() and archive.suffix.lower() in {".gma", ".bin"}: add(archive, item.name + " / " + archive.stem, "workshop", archive.suffix.lower() == ".gma")
    for name in ("download", "downloads"):
        if (content / name).is_dir(): folder(content / name, "Downloaded content / " + name, "download")
    if (content / "gamemodes").is_dir():
        for mode in sorted((content / "gamemodes").iterdir()):
            if (mode / "content").is_dir(): folder(mode / "content", "Gamemode / " + mode.name, "gamemode")
    config = content / "cfg/mount.cfg"
    for key, path in child(kv_read(config), "mountcfg"):
        if isinstance(path, str):
            location = Path(path)
            if not location.is_absolute(): location = game_root / location
            expanded(location, "mount.cfg / " + key, "mount.cfg")
    depots = dict(child(kv_read(content / "cfg/mountdepots.txt"), "gamedepotsystem"))
    status = []
    games = [("240", "Counter-Strike Source", "cstrike"), ("440", "Team Fortress 2", "tf"), ("220", "Half-Life 2", "hl2"), ("1840", "SourceFilmmaker", "game")]
    for appid, title, subdir in games:
        found = []
        for library in steam_libraries:
            steamapps = Path(library) / "steamapps"
            manifest = child(kv_read(steamapps / f"appmanifest_{appid}.acf"), "AppState")
            install = value(manifest, "installdir")
            base = steamapps / "common" / (install or title)
            if not base.is_dir(): continue
            target = base / subdir
            if not target.is_dir(): continue
            if appid == "1840" and not (target / "usermod/gameinfo.txt").is_file(): continue
            if appid != "1840" and not (target / "gameinfo.txt").is_file() and not any(target.glob("*_dir.vpk")): continue
            found.append(str(base))
            if appid == "1840":
                sfm = base / "game"
                search = child(child(child(kv_read(sfm / "usermod/gameinfo.txt"), "GameInfo"), "FileSystem"), "SearchPaths")
                for key, path in search:
                    if key.lower() != "game" or not isinstance(path, str) or "*" in path: continue
                    path = re.sub(r"\|gameinfo_path\|", lambda _: str(sfm / "usermod") + "/", path, flags=re.I)
                    path = re.sub(r"\|all_source_engine_paths\|", lambda _: str(sfm) + "/", path, flags=re.I)
                    if "|" in path: continue
                    resolved = Path(path) if Path(path).is_absolute() else sfm / path
                    folder(resolved, "SFM search path / " + resolved.name, "sfm", installation=base)
                for mod in ("usermod", "workshop", "tf_movies", "tf", "left4dead2_movies", "hl2"):
                    if (sfm / mod).is_dir(): folder(sfm / mod, "SFM / " + mod, "sfm", installation=base)
                # Custom content packs need not have been added to gameinfo yet.
                for mod in sorted(sfm.iterdir()):
                    if mod.is_dir() and not mod.is_symlink() and any((mod / key).is_dir() for key in ("models", "materials", "maps")):
                        folder(mod, "SFM custom / " + mod.name, "sfm-custom", installation=base)
            else:
                enabled = depots.get(subdir, "1") != "0"
                folder(base / subdir, title, "steam", enabled)
                if subdir == "hl2":
                    for episode in ("episodic", "ep2", "lostcoast"):
                        if (base / episode).is_dir(): folder(base / episode, "Half-Life 2 / " + episode, "steam", depots.get(episode, "1") != "0")
        status.append({"name": title, "appid": appid, "installed": bool(found), "locations": found})
    sfm_workshops = [Path(library) / "steamapps/workshop/content/1840" for library in steam_libraries]
    if status[-1]["installed"] and not any((Path(location) / "game/workshop").is_dir() for location in status[-1]["locations"]) and not any(p.is_dir() for p in sfm_workshops):
        warnings.append("SFM is installed, but no local Workshop content folder exists. Refresh after items are available locally.")
    for workshop in sfm_workshops:
        if not workshop.is_dir(): continue
        for addon in sorted(workshop.iterdir()):
            if addon.is_symlink(): continue
            if addon.is_dir():
                expanded(addon, "SFM Workshop / " + addon.name, "sfm-workshop")
                for package in sorted(addon.iterdir()):
                    if package.is_file() and package.suffix.lower() in {".gma", ".bin", ".vpk"}:
                        # Numbered VPK segments belong to their directory index.
                        if package.suffix.lower() == ".vpk" and re.search(r"_\d{3}\.vpk$", package.name, re.I): continue
                        add(package, "SFM Workshop / " + addon.name + " / " + package.name, "sfm-workshop", package.suffix.lower() != ".bin")
    for path in extra: expanded(path, "Additional / " + Path(path).name, "manual")
    if (game_root / "sourceengine/content_cstrike_dir.vpk").is_file():
        status[0]["included_in_gmod"] = True
    return {"providers": providers, "games": status, "libraries": steam_libraries, "warnings": warnings,
            "note": "Offline discovery approximates mount.cfg/depot paths; it cannot inspect a running game's mount state. First enabled path wins; selected asset takes priority."}


def mount_paths(discovery, source=None):
    """Contextual stable order. Selected content is mounted separately before this plan.

    SFM's declared mod order wins for SFM assets; GMod's configured base wins for
    other assets. Additional packs are fallbacks, and explicit disabled rows stay out.
    No Steam subscription state or scripts are evaluated.
    """
    rows = discovery["providers"]
    source = Path(source).resolve() if source else None
    sfm_source = source and any(p["origin"].startswith("sfm") and
        (source == Path(p["path"]) or p["kind"] == "folder" and source.is_relative_to(Path(p["path"]))) for p in rows)
    def priority(p):
        if p["origin"] == "manual": return 0
        if sfm_source and p["origin"] == "sfm": return 1
        if p["origin"] in {"game", "download", "gamemode", "mount.cfg", "steam"}: return 2
        if p["origin"] == "sfm": return 3
        return 4
    return [p["path"] for p in sorted(rows, key=priority) if p["enabled"] and p["present"] and p["kind"] in {"folder", "vpk", "gma"}]
