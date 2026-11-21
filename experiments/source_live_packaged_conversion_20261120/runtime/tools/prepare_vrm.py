"""Normalize VRM0/1 containers into the shared HAS GLB/model contract, offline."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import struct

MAX_FILE = 128 * 1024 * 1024
MAX_JSON = 16 * 1024 * 1024


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError("Duplicate VRM JSON key")
        result[key] = value
    return result


def read_vrm(source):
    if source.stat().st_size > MAX_FILE: raise ValueError("VRM exceeds128MiB")
    raw = source.read_bytes()
    if len(raw) < 28 or len(raw) > MAX_FILE: raise ValueError("Invalid VRM length")
    magic, version, size = struct.unpack_from("<4sII", raw)
    if (magic, version, size) != (b"glTF", 2, len(raw)): raise ValueError("VRM must be a glTF2 binary container")
    chunks, position = [], 12
    while position < len(raw):
        if len(raw) - position < 8: raise ValueError("Truncated VRM chunk")
        size, kind = struct.unpack_from("<II", raw, position)
        position += 8
        if size % 4 or size > len(raw) - position: raise ValueError("Invalid VRM chunk bounds")
        chunks.append((kind, raw[position:position + size]))
        position += size
        if len(chunks) > 2: raise ValueError("Only embedded JSON/BIN VRM supported")
    if len(chunks) != 2 or [kind for kind, _ in chunks] != [0x4e4f534a, 0x004e4942]:
        raise ValueError("VRM requires JSON followed by embedded BIN")
    if len(chunks[0][1]) > MAX_JSON: raise ValueError("VRM JSON exceeds16MiB")
    def reject_constant(value): raise ValueError("Non-finite VRM JSON number")
    doc = json.loads(chunks[0][1], object_pairs_hook=unique_object, parse_constant=reject_constant)
    if not isinstance(doc, dict) or doc.get("asset", {}).get("version") != "2.0": raise ValueError("Invalid VRM glTF asset")
    for name in ("images", "buffers"):
        items = doc.get(name, [])
        if not isinstance(items, list) or any(not isinstance(item, dict) or "uri" in item for item in items):
            raise ValueError("VRM must embed all buffers and textures; external resources are not read")
    buffers = doc.get("buffers", [])
    if len(buffers) != 1 or type(buffers[0].get("byteLength")) is not int or not 0 <= buffers[0]["byteLength"] <= len(chunks[1][1]):
        raise ValueError("Invalid VRM embedded buffer")
    extensions = doc.get("extensions", {})
    if not isinstance(extensions, dict) or ("VRM" in extensions) == ("VRMC_vrm" in extensions):
        raise ValueError("Expected exactly one VRM0 or VRM1 avatar extension")
    family = "1.0" if "VRMC_vrm" in extensions else "0.x"
    native = extensions["VRMC_vrm" if family == "1.0" else "VRM"]
    if not isinstance(native, dict) or native.get("specVersion") not in (["1.0"] if family == "1.0" else ["0.0"]):
        raise ValueError("Unsupported VRM specification version")
    nodes, scenes = doc.get("nodes"), doc.get("scenes")
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 100000 or not isinstance(scenes, list) or not 1 <= len(scenes) <= 128:
        raise ValueError("Invalid VRM node/scene inventory")
    def node_index(index):
        return type(index) is int and 0 <= index < len(nodes) and isinstance(nodes[index], dict)
    for scene in scenes:
        if not isinstance(scene, dict) or not isinstance(scene.get("nodes"), list) or not all(node_index(index) for index in scene["nodes"]):
            raise ValueError("Invalid VRM scene root")
    humanoid = native.get("humanoid", {})
    human_bones = humanoid.get("humanBones", {} if family == "1.0" else [])
    if family == "0.x":
        if not isinstance(human_bones, list): raise ValueError("Invalid VRM0 humanoid map")
        mapped = {}
        for bone in human_bones:
            if not isinstance(bone, dict) or not isinstance(bone.get("bone"), str) or bone["bone"] in mapped:
                raise ValueError("Invalid or duplicate VRM humanoid bone")
            mapped[bone["bone"]] = {"node": bone.get("node")}
        human_bones = mapped
    if not isinstance(human_bones, dict) or not 1 <= len(human_bones) <= 128: raise ValueError("Missing VRM humanoid map")
    mapped = {}
    for name, bone in human_bones.items():
        if not isinstance(bone, dict) or not node_index(bone.get("node")): raise ValueError("VRM humanoid bone refers to missing node")
        mapped[name] = {"node": bone["node"], "node_name": nodes[bone["node"]].get("name", "")}
    return raw, doc, chunks[1][1], family, native, mapped


def prepare(source, output, scale=1.0, cancel_file=None):
    source = Path(source).resolve(strict=True)
    if not math.isfinite(scale) or not .0001 <= scale <= 10000: raise ValueError("Invalid VRM scale")
    raw, doc, binary, family, native, humanoid = read_vrm(source)
    sha = hashlib.sha256(raw).hexdigest()
    if cancel_file and cancel_file.exists(): raise RuntimeError("VRM import cancelled before staging")
    # Appending wrapper nodes leaves every source node/morph/material index intact.
    # VRM0 faces -Z; canonical HAS avatars face +Z, as VRM1 does.
    wrappers = {}
    for scene in doc["scenes"]:
        roots = []
        for index in scene["nodes"]:
            if index not in wrappers:
                root = {"name": "HASAvatarRoot" + str(index), "children": [index], "scale": [scale] * 3}
                if family == "0.x": root["rotation"] = [0, 1, 0, 0]
                wrappers[index] = len(doc["nodes"])
                doc["nodes"].append(root)
            roots.append(wrappers[index])
        scene["nodes"] = roots
    encoded = json.dumps(doc, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()
    encoded += b" " * (-len(encoded) % 4)
    glb = struct.pack("<4sII", b"glTF", 2, 28 + len(encoded) + len(binary)) + struct.pack("<II", len(encoded), 0x4e4f534a) + encoded + struct.pack("<II", len(binary), 0x004e4942) + binary
    if len(glb) > MAX_FILE: raise ValueError("Normalized VRM exceeds128MiB")
    warnings = ["Base textures and rig imported. VRM toon lighting/outline appearance is approximated.",
                "VRM spring data is retained. Hair & clothes can simulate supported chains; native behavior is approximated. Gaze and first-person settings remain data only.",
                "Facial morph geometry is retained. Studio supports embedded expression poses and limb posing; native constraints, procedural expression animation and material/texture expression effects remain unsupported."]
    report = {"schema_version": 1, "kind": "vrm_preparation", "source_file": source.name,
              "source_sha256": sha, "vrm_version": family, "scale": scale,
              "orientation": "HAS +Z forward; VRM0 rotated180degrees aroundY" if family == "0.x" else "HAS +Z forward",
              "humanoid": humanoid, "native_meta": native.get("meta", {}),
              "expressions": native.get("expressions", native.get("blendShapeMaster", {})),
              "extensions": doc.get("extensionsUsed", []), "warnings": warnings,
              "counts": {"meshes": len(doc.get("meshes", [])), "skins": len(doc.get("skins", [])), "textures": len(doc.get("images", []))},
              "preserved": ["embedded geometry, skin, texture and morph buffers", "native VRM extension data and provenance"],
              "limitations": warnings}
    report_bytes = json.dumps(report, ensure_ascii=True, indent=2).encode()
    if len(report_bytes) > 256 * 1024: raise ValueError("VRM parameter report exceeds256KiB; nothing imported")
    if cancel_file and cancel_file.exists(): raise RuntimeError("VRM import cancelled before staging")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "native").mkdir()
    (output / "native" / source.name).write_bytes(raw)
    (output / "scene.glb").write_bytes(glb)
    (output / "parameters.json").write_bytes(report_bytes)
    if hashlib.sha256(source.read_bytes()).hexdigest() != sha: raise RuntimeError("VRM source changed during import")
    if cancel_file and cancel_file.exists(): raise RuntimeError("VRM import cancelled; previous scene preserved")
    return {"ok": True, "glb": str(output / "scene.glb")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scale", type=float, default=1)
    parser.add_argument("--status-file", type=Path)
    parser.add_argument("--cancel-file", type=Path)
    args = parser.parse_args()
    try: result = prepare(args.source, args.output, args.scale, args.cancel_file)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError, struct.error) as error:
        result = {"ok": False, "error": str(error)}
    except RuntimeError as error: result = {"ok": False, "error": str(error)}
    if args.status_file: args.status_file.write_text(json.dumps(result), encoding="utf-8")
    print(json.dumps(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__": raise SystemExit(main())
