"""Isolated Blender worker. SourceIO decodes resources; this adapter emits standard PBR/GLB."""
import hashlib
import importlib.util
import json
import os
import math
import struct
import zlib
import fnmatch
from pathlib import Path
import sys
from types import SimpleNamespace
from dataclasses import asdict, is_dataclass

sys.dont_write_bytecode = True
os.environ["NO_BPY"] = "1"
import bpy

request = json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text(encoding="utf-8"))
out = Path(request["output"])
root = Path(request["sourceio"])
spec = importlib.util.spec_from_file_location("SourceIO", root / "__init__.py", submodule_search_locations=[str(root)])
module = importlib.util.module_from_spec(spec)
sys.modules["SourceIO"] = module
spec.loader.exec_module(module)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_appearance
from asset_audit import gma_index, AssetError
from source_archive import resource_path, write_resource
from source_texture import blender_rgba
from source_case import CaseResolver
from source_eyes import plan as neutral_eye_plan
from source_lights import plan as light_plan, create as create_lights
from source_lightmaps import capture as capture_lightmaps, bake as bake_lightmaps, tag_glb as tag_lightmap_glb

from SourceIO.library.utils import TinyPath, FileBuffer, MemoryBuffer
from SourceIO.library.shared.app_id import SteamAppId
from SourceIO.library.shared.content_manager import ContentManager
from SourceIO.library.shared.content_manager.providers.loose_files import LooseFilesContentProvider
from SourceIO.library.shared.content_manager.providers.vpk_provider import VPKContentProvider
from SourceIO.library.shared.content_manager.providers.zip_content_provider import ZIPContentProvider
from SourceIO.library.shared.content_manager.providers.gma_provider import GMAContentProvider
from SourceIO.blender_bindings.models import import_model
from SourceIO.blender_bindings.models.common import put_into_collections
from SourceIO.blender_bindings.operators.import_settings_base import ModelOptions, Source1BSPSettings
from SourceIO.library.source1.vmt import VMT
from SourceIO.library.source1.vtf import load_texture

dependencies, missing, warnings = {}, set(), []
mount_warnings = []
map_lights = []
lightmap_jobs, lightmap_cache = [], {}
failed_lookups = set()
dependency_bytes = 0
mounts = [Path(p).resolve() for p in request["mounts"]]


class VTXBuffer(MemoryBuffer):
    def seek(self, *args):
        # Pinned SourceIO retries SFM's extended VTX7 layout on struct.error,
        # but its current buffer raises BufferError for out-of-range seeks.
        # Normalize that error at this boundary; the decoder still validates
        # the alternate layout and malformed files still fail if both fail.
        try: return super().seek(*args)
        except BufferError as error: raise struct.error(str(error)) from error


def relative_name(value):
    name = str(value).replace("\\", "/")
    if Path(name).is_absolute():
        resolved = Path(name).resolve()
        for mount in mounts:
            if mount.is_dir() and resolved.is_relative_to(mount):
                return resolved.relative_to(mount).as_posix()
        raise ValueError("Resource outside explicit content mounts")
    parts = name.split("/")
    if any(p in {"..", ""} or ":" in p for p in parts):
        raise ValueError("Unsafe Source resource path: " + name)
    return name


class DirectFiles(LooseFilesContentProvider):
    def find_file(self, filepath):
        name = relative_name(filepath)
        base = Path(str(self.root)).resolve()
        if not hasattr(self, "_studio_case_resolver"):
            self._studio_case_resolver = CaseResolver(base)
        path = self._studio_case_resolver.find(name)
        return FileBuffer(TinyPath(str(path))) if path is not None else None

    def check(self, filepath):
        buffer = self.find_file(filepath)
        return buffer is not None


class BoundedGMA(GMAContentProvider):
    def _init(self):
        if self._initialized: return
        path = Path(str(self.filepath))
        self.entries = {}
        self._initialized = True
        try:
            if path.stat().st_size > 512 * 1024 * 1024: raise ValueError("GMA dependency exceeds 512 MiB")
            with path.open("rb") as stream: index = gma_index(stream, path.stat().st_size)
            entries = {}
            for row in index["entries"]:
                name = resource_path(row["name"]).lower()
                if name in entries: raise ValueError("Duplicate GMA dependency path")
                entries[name] = row
        except (AssetError, ValueError, OSError, EOFError, struct.error) as error:
            mount_warnings.append("Dependency package skipped: " + str(path) + ": " + str(error))
            return
        self.entries = entries
        self.payload_start = index["payload_start"]

    def check(self, path):
        self._init()
        return relative_name(path).lower() in self.entries

    def find_file(self, path):
        self._init()
        name = relative_name(path).lower()
        row = self.entries.get(name)
        if not row: return None
        if row["size"] > 128 * 1024 * 1024: raise ValueError("GMA dependency resource exceeds 128 MiB")
        with Path(str(self.filepath)).open("rb") as stream:
            stream.seek(self.payload_start + row["relative_offset"])
            blob = stream.read(row["size"])
        if len(blob) != row["size"] or zlib.crc32(blob) & 0xFFFFFFFF != row["crc32"]: raise ValueError("GMA dependency CRC differs: " + name)
        return MemoryBuffer(blob)

    def glob(self, pattern):
        self._init()
        for name in self.entries:
            if fnmatch.fnmatch(name, pattern): yield TinyPath(name), self.find_file(name)


cm = ContentManager()
cm.clean()
providers = []
for mount in mounts:
    provider_class = DirectFiles if mount.is_dir() else BoundedGMA if mount.suffix.lower() == ".gma" else VPKContentProvider
    provider = provider_class(TinyPath(str(mount)), SteamAppId.GARRYS_MOD)
    providers.append(provider)
    cm.add_child(provider)
provider_ids = {id(provider) for provider in providers}

# Deterministic explicit order: archive/loose resources, then selected game mounts.
# BSP pak providers added during import take precedence over installed resources.
def find_file(value, *args, **kwargs):
    global dependency_bytes
    name = relative_name(value)
    lookup = (name.lower(), len(cm.children))
    if lookup in failed_lookups: return None
    if len(dependencies) + len(missing) > 25000:
        raise ValueError("Source dependency request budget exceeded")
    ordered = [p for p in cm.children if id(p) not in provider_ids] + providers
    for provider in ordered:
        if isinstance(provider, BoundedGMA):
            provider._init()
            if name.lower() not in provider.entries: continue
        if isinstance(provider, ZIPContentProvider):
            entry = provider._cache.get(name.lower())
            if entry and provider._zip_file.getinfo(entry).file_size > 128 * 1024 * 1024:
                raise ValueError("Embedded pak resource exceeds 128 MiB: " + name)
        data = provider.find_file(TinyPath(name))
        if data is not None:
            if data.size() > 128 * 1024 * 1024:
                raise ValueError("Resource exceeds 128 MiB: " + name)
            data.seek(0)
            blob = data.read()
            if len(blob) > 128 * 1024 * 1024:
                raise ValueError("Resource exceeds 128 MiB: " + name)
            key = name.lower()
            if key not in dependencies:
                dependency_bytes += len(blob)
                if dependency_bytes > 512 * 1024 * 1024:
                    raise ValueError("Resolved native dependencies exceed 512 MiB")
                write_resource(out / "resolved-native", name, blob)
                dependencies[key] = {"path": name, "provider": str(provider.filepath), "bytes": len(blob),
                                     "sha256": hashlib.sha256(blob).hexdigest()}
            return VTXBuffer(blob) if name.lower().endswith(".vtx") else MemoryBuffer(blob)
    missing.add(name)
    failed_lookups.add(lookup)
    return None


cm.find_file = find_file
cm.check = lambda value: find_file(value) is not None
cm.get_steamid_from_asset = lambda value: SteamAppId.GARRYS_MOD
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def model_options(scale):
    options = ModelOptions.default()
    options.scale = scale
    for key in ("import_textures", "create_flex_drivers", "bodygroup_vis_switches", "bodygroup_grouping",
                "generate_wrinkle_map_node_group", "import_physics", "import_animations", "import_include_animations", "load_refpose"):
        setattr(options, key, False)
    return options


def load_model(path, buffer, scale, parent=None, skin=0, appearance=None):
    container = import_model(TinyPath(str(path)), buffer, cm, model_options(scale), SteamAppId.GARRYS_MOD)
    put_into_collections(container, Path(str(path)).stem)
    from SourceIO.blender_bindings.shared.skins import set_model_skin
    if appearance is not None:
        container.has_selected_appearance = source_appearance.apply(container, appearance, set_model_skin)
    else:
        # Preserve the original default and BSP-prop path byte-for-byte in meaning.
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


source = Path(request["source"])
native_parameters = {}
props_loaded = 0
suggested_view = None
if source.suffix.lower() == ".mdl":
    appearance = request.get("appearance")
    if appearance is not None:
        appearance = source_appearance.bind(appearance, request["sha256"], source)
    container = load_model(source, FileBuffer(TinyPath(str(source))), request["scale"], appearance=appearance)
    mdl = getattr(container, "mdl", None)
    native_physics = CaseResolver(source.parent).find(source.with_suffix(".phy").name)
    if native_physics:
        with native_physics.open("rb") as stream:
            physics_sha=hashlib.file_digest(stream,"sha256").hexdigest()
        warnings.append("Source physics file retained in the preparation folder, but its collision shapes and constraints are not reproduced. HAS Physics uses its own generated bodies.")
    native_parameters = {
        "bones": [{"name": b.name, "parent": b.parent_id} for b in mdl.bones] if mdl else [],
        "bodygroups": {k: [o.name if o else None for o in v] for k, v in container.bodygroups.items()},
        "skin_groups": [[m.name for m in group] for group in mdl.skin_groups] if mdl else [],
        "flex_names": list(mdl.flex_names) if mdl else [],
        "flex_controllers": [asdict(c) for c in mdl.flex_controllers if is_dataclass(c)] if mdl else [],
        "selected_skin": 0, "selected_bodygroup_indices": {k: 0 for k in container.bodygroups},
        "eyeballs": [asdict(eye) for part in mdl.body_parts for model in part.models for eye in model.eyeballs] if mdl else []}
    if appearance is not None:
        native_parameters.update(container.has_selected_appearance)
        native_parameters["appearance_request"] = appearance
    if native_physics:
        native_parameters["source_physics"]={"file":native_physics.name,"sha256":physics_sha,"bytes":native_physics.stat().st_size,"applied":False}
else:
    if request.get("appearance") is not None:
        raise ValueError("Appearance choices apply only to one MDL model, not a BSP map")
    from SourceIO.blender_bindings.source1.bsp.import_bsp import import_bsp
    from SourceIO.blender_bindings.source1.bsp.entities.abstract_entity_handlers import AbstractEntityHandler
    original_brush_loader = AbstractEntityHandler._load_brush_model
    def lightmapped_brush(self, model_id, model_name):
        obj = original_brush_loader(self, model_id, model_name)
        try: lightmap_jobs.append(capture_lightmaps(self, model_id, obj, lightmap_cache))
        except (ValueError, IndexError, KeyError, AttributeError, ArithmeticError, struct.error) as error:
            warnings.append(model_name + ": baked lighting unavailable: " + str(error))
        return obj
    AbstractEntityHandler._load_brush_model = lightmapped_brush
    original_handler = AbstractEntityHandler.handle_entity
    def geometry_entity(self, entity):
        classname = entity.get("classname", "")
        if classname == "worldspawn":
            world = self._load_brush_model(0, "world_geometry")
            self._world_geometry_name = world.name
            self.parent_collection.objects.link(world)
            return True
        if classname != "worldspawn" and not classname.startswith(("func_", "prop_")):
            return True
        return original_handler(self, entity)
    AbstractEntityHandler.handle_entity = geometry_entity
    # Editor icons are irrelevant and their cache helper expects an installed add-on.
    AbstractEntityHandler._set_icon_if_present = lambda *args, **kwargs: None
    defaults = {}
    for cls in reversed(Source1BSPSettings.__mro__):
        defaults.update({k: prop.keywords["default"] for k, prop in getattr(cls, "__annotations__", {}).items()})
    defaults.update(scale=request["scale"], import_textures=False, load_lights=False, load_decals=False)
    import_bsp(TinyPath(str(source)), FileBuffer(TinyPath(str(source))), cm, SimpleNamespace(**defaults), SteamAppId.GARRYS_MOD)
    for text in bpy.data.texts:
        if not text.name.endswith("_entities.json"): continue
        entities = json.loads(text.as_string())
        planned_lights = light_plan(entities, request["scale"])
        create_lights(bpy, planned_lights)
        map_lights.extend(planned_lights["lights"])
        if len(map_lights)>64:raise ValueError("Source map exceeds64supported static lights")
        warnings.extend(planned_lights["warnings"])
        (out / "entities.json").write_text(json.dumps(entities, indent=2), encoding="utf-8")
        for entity in entities:
            if not entity.get("classname", "").startswith("info_player_"): continue
            xyz = [float(x) for x in entity.get("origin", "0 0 0").split()]
            angles = [math.radians(float(x)) for x in entity.get("angles", "0 0 0").split()]
            if len(xyz) != 3 or len(angles) != 3: continue
            scale = request["scale"]
            position = [xyz[0] * scale, (xyz[2] + 64) * scale, -xyz[1] * scale]
            direction = [math.cos(angles[1]) * math.cos(angles[0]), -math.sin(angles[0]), -math.sin(angles[1]) * math.cos(angles[0])]
            suggested_view = {"position": position, "target": [p + d for p, d in zip(position, direction)], "source": entity["classname"]}
            break
    # Compile-time tool surfaces are not visible game geometry. SourceIO retains them
    # when shader importing is disabled; remove just those polygons in our intermediate.
    import bmesh
    removed_tool_faces = 0
    for mesh in bpy.data.meshes:
        tools = {i for i, m in enumerate(mesh.materials) if m and str(m.get("full_path", "")).lower().startswith("tools/")}
        if not tools: continue
        bm = bmesh.new(); bm.from_mesh(mesh)
        faces = [face for face in bm.faces if face.material_index in tools]
        removed_tool_faces += len(faces)
        bmesh.ops.delete(bm, geom=faces, context="FACES")
        bm.to_mesh(mesh); bm.free()
    placeholders = [obj for obj in bpy.data.objects if obj.type == "EMPTY" and obj.get("entity_data", {}).get("prop_path")]
    if len(placeholders) > 5000:
        raise ValueError("Map exceeds the 5000 prop limit")
    for obj in placeholders:
        data = obj["entity_data"]
        path = TinyPath(data["prop_path"])
        buffer = find_file(path)
        if buffer is None:
            warnings.append("Missing prop: " + str(path))
            continue
        try:
            load_model(path, buffer, 1.0, obj, int(data.get("skin", 0)))
            props_loaded += 1
        except Exception as error:
            warnings.append("Prop failed: " + str(path) + ": " + str(error))
    native_parameters = {"props_found": len(placeholders), "props_loaded": props_loaded, "removed_tool_faces": removed_tool_faces, "static_entity_lights": map_lights}


images = {}
decoded_texture_bytes = 0
material_report = []
bpy.context.view_layer.update()
used_materials = {slot.material for obj in bpy.context.scene.objects if obj.type == "MESH" for slot in obj.material_slots if slot.material}
for material in used_materials:
    native_name = material.get("source1_material", material.get("full_path", material.name))
    # SourceIO records the original VMT path separately from Blender's short display name.
    native_name = str(native_name).replace("\\", "/")
    if not native_name.startswith("materials/"):
        native_name = "materials/" + native_name
    if not native_name.lower().endswith(".vmt"):
        native_name += ".vmt"
    row = {"material": material.name, "vmt": native_name}
    material.use_nodes = True
    material.node_tree.nodes.clear()
    shader = material.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    output = material.node_tree.nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    shader.inputs["Metallic"].default_value = 0
    shader.inputs["Roughness"].default_value = 0.8
    shader.inputs["Base Color"].default_value = (0.65, 0.65, 0.65, 1)
    try:
        data = find_file(native_name)
        if data is None:
            raise ValueError("VMT unavailable")
        vmt = VMT(data, TinyPath(native_name), cm)
        row["shader"] = vmt.shader
        eye_plan = neutral_eye_plan(material, bpy.context.scene.objects) if vmt.shader.lower() == "eyerefract" else None
        texture = vmt.get_string("$iris" if eye_plan else "$basetexture", "")
        if eye_plan and not texture: raise ValueError("Native eye iris texture unavailable")
        material.use_backface_culling = not bool(vmt.get_int("$nocull", 0))
        if texture:
            texture = "materials/" + texture.removeprefix("materials/").removesuffix(".vtf") + ".vtf"
            if texture not in images:
                data = find_file(texture)
                if data is None:
                    raise ValueError("VTF unavailable: " + texture)
                header = data.read(20)
                data.seek(0)
                if len(header) != 20 or header[:4] != b"VTF\0":
                    raise ValueError("Not a supported VTF texture")
                width_hint, height_hint = struct.unpack_from("<HH", header, 16)
                image_bytes = width_hint * height_hint * 16
                if not width_hint or not height_hint or width_hint * height_hint > 16777216 or decoded_texture_bytes + image_bytes > 512 * 1024 * 1024:
                    raise ValueError("Texture dimension / decoded memory budget exceeded")
                decoded_texture_bytes += image_bytes
                pixels, height, width = load_texture(data)
                if pixels is None or not width or not height:
                    raise ValueError("VTF decode failed: " + texture)
                if width * height > 16777216:
                    raise ValueError("Texture exceeds 16 megapixels")
                image = bpy.data.images.new(Path(texture).stem, width=width, height=height, alpha=True)
                image.pixels.foreach_set(blender_rgba(pixels, width, height))
                image.pack()
                images[texture] = image
            node = material.node_tree.nodes.new("ShaderNodeTexImage")
            node.image = images[texture]
            if eye_plan: node.extension = "EXTEND"
            material.node_tree.links.new(node.outputs["Color"], shader.inputs["Base Color"])
            if not eye_plan and (vmt.get_int("$translucent", 0) or vmt.get_int("$alphatest", 0)):
                material.node_tree.links.new(node.outputs["Alpha"], shader.inputs["Alpha"])
                material.surface_render_method = "DITHERED"
            row["base_texture"] = texture
        if eye_plan:
            for loop, uv in eye_plan['changes']: eye_plan['object'].data.uv_layers.active.data[loop].uv = uv
            row['neutral_eye'] = eye_plan['report']
            row['warning'] = 'Neutral eye appearance imported; gaze, dilation and refraction remain unsupported.'
            warnings.append(native_name + ': ' + row['warning'])
        row["status"] = "neutral iris approximation" if eye_plan else "PBR approximation"
    except Exception as error:
        row["status"] = "fallback gray"
        row["warning"] = str(error)
        warnings.append(native_name + ": " + str(error))
    material_report.append(row)

lightmap_report = bake_lightmaps(bpy, lightmap_jobs, 512 * 1024 * 1024 - decoded_texture_bytes)
decoded_texture_bytes += lightmap_report["decoded_bytes"]
if lightmap_report["downsampled_faces"]:
    warnings.append("Baked lightmap textures were reduced to the512pixel-per-face bound on%d surfaces." % lightmap_report["downsampled_faces"])
if lightmap_report["skipped"]:
    warnings.append("Some Source brush lighting was not baked: " + json.dumps(lightmap_report["skipped"], sort_keys=True))
if lightmap_jobs:
    native_parameters["static_brush_lightmaps"] = lightmap_report

# Save the complete native intermediate; GLB exports only active mesh variants and rigs.
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out / "editable.blend"))
bpy.ops.object.select_all(action="DESELECT")
exported = []
for obj in bpy.context.scene.objects:
    if obj.type in {"MESH", "ARMATURE", "EMPTY", "LIGHT"} and not obj.hide_render and not obj.hide_get():
        obj.select_set(True)
        exported.append(obj)
if not any(o.type == "MESH" and len(o.data.polygons) for o in exported):
    raise ValueError("No renderable geometry imported")
bpy.ops.export_scene.gltf(filepath=str(out / "scene.glb"), export_format="GLB", use_selection=True,
                          export_animations=False, export_cameras=False, export_lights=True,
                          export_extras=False, export_yup=True, export_image_format="AUTO")
tag_lightmap_glb(out / "scene.glb", lightmap_report["materials"])
report = {"adapter": "studio_source_1", "standard": "studio_model_1", "original_source": request["original_source"],
          "source_file": source.name, "source_member": request.get("source_member"),
          "case_resolved_sidecars": request.get("case_resolved_sidecars", {}),
          "source_profile": request.get("source_profile", "gmod"),
          "source_sha256": request["sha256"], "sourceio_revision": request["sourceio_revision"],
          "sourceio_version": list(module.bl_info["version"]), "scale": request["scale"],
          "axes": "Source Z-up to glTF Y-up via Blender exporter", "native_parameters": native_parameters,
          "mount_warnings": mount_warnings,
          "suggested_view": suggested_view,
          "materials": material_report, "warnings": warnings,
          "limits": ["PBR approximation; bounded static LDR brush lightmaps; no HDR-only/styled/displacement lighting, Source shader/proxy execution or 3D skybox",
                     "One selected static skin/bodygroup appearance in GLB; all imported variants retained in editable.blend; no runtime variant switching" if request.get("appearance") is not None else "Default skin/bodygroup only in GLB; all imported variants retained in editable.blend",
                     "No Source physics, IK, gameplay, native sequence playback or lossless roundtrip"],
          "counts": {"meshes": sum(o.type == "MESH" for o in exported), "textures": len(images) + lightmap_report["atlases"],
                     "bones": sum(len(o.data.bones) for o in exported if o.type == "ARMATURE"), "static_lights": len(map_lights)}}
(out / "parameters.json").write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
(out / "dependencies.json").write_text(json.dumps({"resolved": list(dependencies.values()), "missing_requests": sorted(missing)}, indent=2), encoding="utf-8")
print("STUDIO_SOURCE_READY", json.dumps(report["counts"]), flush=True)
