"""Isolated Blender worker. No preferences are saved and source scripts never execute."""
from pathlib import Path
import json
import sys
sys.dont_write_bytecode = True
import bpy


def run():
    request = json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text(encoding="utf-8"))
    output = Path(request["output"])
    sys.path.insert(0, str(Path(request["mmd_tools"]).parent))
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from blender_addon_runtime import add_bundled_wheels
    dependency_wheels=add_bundled_wheels(request["mmd_tools"],output/"blender-dependencies")
    import mmd_tools
    mmd_tools.register()
    bpy.context.preferences.filepaths.file_preview_type = 'NONE'
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.mmd_tools.import_model(filepath=request["source"], scale=request["scale"],
                                   clean_model=False, remove_doubles=False, rename_bones=False,
                                   fix_bone_order=False, save_log=False)
    objects = list(bpy.context.scene.objects)
    meshes = [obj for obj in objects if obj.type == "MESH" and getattr(obj, "mmd_type", "NONE") == "NONE" and len(obj.data.vertices)>0 and len(obj.data.polygons)>0]
    rigs = [obj for obj in objects if obj.type == "ARMATURE"]
    roots = [obj for obj in objects if getattr(obj, "mmd_type", "NONE") == "ROOT"]
    if not meshes:
        raise RuntimeError("MMD Tools returned no renderable mesh. See importer messages.")
    missing = []
    absent_names = request.get("missing_textures", [])
    absent_paths = {(Path(request["source"]).parent / name).resolve() for name in absent_names}
    absent_paths.update(output / name for name in request.get("absent_shared_toons", []))
    for image in list(bpy.data.images):
        if image.source != "FILE": continue
        image_path = Path(bpy.path.abspath(image.filepath)).resolve()
        image_path.relative_to(output)  # no hidden dependency reads outside the staged asset
        if not image_path.is_file():
            if image_path in absent_paths:
                bpy.data.images.remove(image, do_unlink=True)
                continue
            missing.append(image.filepath)
            continue
        image.reload()
        if len(image.pixels): image.pixels[0]  # force lazy image decoding before checking
        if not image.has_data: missing.append(image.filepath)
    if missing:
        raise RuntimeError("Unresolved textures: " + str(missing))
    report = {"schema_version": 1, "kind": "mmd_preparation", "source_file": request["original_name"],
              "source_sha256": request["sha256"], "scale": request["scale"],
              "tools": {"blender": bpy.app.version_string, "mmd_tools": mmd_tools.MMD_TOOLS_VERSION, "dependency_wheels": dependency_wheels},
              "meshes": [{"name": o.name, "vertices": len(o.data.vertices),
                          "shape_keys": [k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else []} for o in meshes],
              "rigs": [{"name": o.name, "bones": [{"name": b.name, "parent": b.parent.name if b.parent else None} for b in o.data.bones]} for o in rigs],
              "materials": [{"name": mat.name, "diffuse": list(mat.mmd_material.diffuse_color),
                             "alpha": mat.mmd_material.alpha} for mat in bpy.data.materials if mat.users],
              "mmd_morphs": {}, "texture_dependencies": request["dependency_hashes"],
              "preserved": ["native model/textures", "packed editable.blend with MMD properties", "GLB mesh, skin/bone and vertex morph data where exportable"],
              "limitations": ["MMD toon/sphere/edge shading approximated by simple PBR for GLB",
                              "Supported MMD IK declarations are retained for pose/motion baking; native live IK, inherited bone transforms, physics, display frames and material/bone morphs are not reproduced by GLB alone",
                              "Studio uses its own posing/physics; exported vertex morphs and compatible vertex expression groups use shared deform controls",
                              "No PMD/PMX round-trip or broad asset compatibility claim"],
              "rights": "User-supplied asset; distribution rights not inferred"}
    report["warnings"] = report["limitations"][:3]
    if request.get("absent_shared_toons"):
        report["absent_shared_toons"] = request["absent_shared_toons"]
        report["warnings"].append("Shared MMD toon shading files were unavailable. Studio uses the converted material colors and base textures.")
    if absent_names:
        report["missing_textures"] = absent_names
        examples = ", ".join(absent_names[:3])
        extra = f" (+{len(absent_names)-3} more)" if len(absent_names)>3 else ""
        report["warnings"].insert(0, f"Missing textures: {examples}{extra}. Affected surfaces use their material color. Restore the files beside the original model and import again.")
    for root in roots:
        for category in ["vertex_morphs", "bone_morphs", "material_morphs", "uv_morphs", "group_morphs"]:
            report["mmd_morphs"].setdefault(category, []).extend(item.name for item in getattr(root.mmd_root, category, []))
    groups = []
    group_count = sum(len(root.mmd_root.group_morphs) for root in roots)
    binding_count = sum(len(group.data) for root in roots for group in root.mmd_root.group_morphs)
    group_limit = group_count > 256 or binding_count > 16384
    if not group_limit:
        for root in roots:
            for group in root.mmd_root.group_morphs:
                groups.append({"name": group.name, "english_name": group.name_e,
                               "binds": [{"kind": item.morph_type, "name": item.name,
                                          "weight": float(item.factor)} for item in group.data]})
    report['mmd_expression_source_counts'] = {'groups': group_count, 'bindings': binding_count}
    report['mmd_expression_groups'] = groups
    # Snapshot preserves original imported materials/MMD properties before export approximation.
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "editable.blend"), check_existing=False, compress=True)
    material_map = {}
    for mesh in meshes:
        for slot in mesh.material_slots:
            original = slot.material
            if original is None: continue
            if original.name not in material_map:
                exported = original.copy()
                exported.name = original.name + "_GLTF"
                base = original.node_tree.nodes.get("mmd_base_tex") if original.node_tree else None
                image = base.image if base and base.type == "TEX_IMAGE" else None
                rgba = list(original.mmd_material.diffuse_color) + [original.mmd_material.alpha]
                exported.use_nodes = True
                nodes = exported.node_tree.nodes
                nodes.clear()
                shader = nodes.new("ShaderNodeBsdfPrincipled")
                shader.inputs["Base Color"].default_value = rgba
                shader.inputs["Alpha"].default_value = rgba[3]
                shader.inputs["Metallic"].default_value = 0
                shader.inputs["Roughness"].default_value = 0.9
                terminal = nodes.new("ShaderNodeOutputMaterial")
                exported.node_tree.links.new(shader.outputs["BSDF"], terminal.inputs["Surface"])
                if image:
                    texture = nodes.new("ShaderNodeTexImage")
                    texture.image = image
                    exported.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
                    # Opaque materials remain opaque; transparent MMD material alpha stays explicit.
                exported.diffuse_color = rgba
                material_map[original.name] = exported
            slot.material = material_map[original.name]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes + rigs + roots: obj.select_set(True)
    # Important compatibility identity stays inside GLB as well as the readable sidecar.
    if roots:
        roots[0]["studio_source_format"] = Path(request["source"]).suffix.lower()[1:]
        roots[0]["studio_source_sha256"] = request["sha256"]
        roots[0]["studio_native_parameters"] = json.dumps(report["mmd_morphs"], ensure_ascii=True)
    bpy.ops.export_scene.gltf(filepath=str(output / "scene.glb"), export_format="GLB",
                              use_selection=True, export_extras=True, export_animations=False,
                              export_skins=True, export_morph=True, export_yup=True)
    # Inspect the standard result instead of assuming the exporter retained every channel.
    import struct
    with (output / "scene.glb").open("rb") as stream:
        header = stream.read(20)
        document = json.loads(stream.read(struct.unpack_from("<I", header, 12)[0]))
    # Add only standard binding metadata. Preserve every exported geometry chunk.
    sys.path.insert(0, str(Path(__file__).parent))
    from mmd_expression_groups import normalize, EXTRA
    from mmd_ik import capture,EXTRA as IK_EXTRA
    ik=capture(request["source"],rigs,document)
    report["ik_constraints"]=ik
    if ik["chains"] or ik["skipped"]:
        document.setdefault('asset',{}).setdefault('extras',{})[IK_EXTRA]=ik
    if ik["skipped"]:report["warnings"].append("Some native joint chains are unsupported. Their declarations are reported rather than guessed.")
    expressions = normalize(groups, document)
    if group_limit:
        expressions = {"format": "studio_expression_presets_1", "entries": [],
                       "error": "MMD expression groups exceed the preparation budget."}
    if groups and len(roots) != 1:
        expressions = {"format": "studio_expression_presets_1", "entries": [],
                       "error": "Multiple MMD roots have ambiguous expression ownership."}
    if group_count:
        document.setdefault('asset', {}).setdefault('extras', {})[EXTRA] = expressions
    if group_count or ik["chains"] or ik["skipped"]:
        glb = output / 'scene.glb'
        original = glb.read_bytes()
        tail = original[20 + struct.unpack_from('<I', original, 12)[0]:]
        text = json.dumps(document, ensure_ascii=True, separators=(',', ':')).encode('utf-8')
        text += b' ' * (-len(text) % 4)
        glb.write_bytes(struct.pack('<4sIIII', b'glTF', 2, 20 + len(text) + len(tail), len(text), 0x4e4f534a) + text + tail)
        import hashlib
        report['expression_geometry_tail_sha256'] = hashlib.sha256(tail).hexdigest()
        if ik["chains"] or ik["skipped"]:report['ik_geometry_tail_sha256']=hashlib.sha256(tail).hexdigest()
        assert glb.read_bytes()[20 + len(text):] == tail
    report['expression_presets'] = expressions
    if expressions['error']:
        report['warnings'].append(expressions['error'])
    elif any(entry['error'] for entry in expressions['entries']):
        report['warnings'].append('Some expression groups require unsupported effects. Shapes / expressions explains each group.')
    report["glb"] = {"meshes": len(document.get("meshes", [])), "materials": len(document.get("materials", [])),
                     "embedded_images": len(document.get("images", [])),
                     "skin_joint_counts": [len(s["joints"]) for s in document.get("skins", [])],
                     "morph_target_counts": [len(p.get("targets", [])) for m in document.get("meshes", []) for p in m["primitives"]]}
    (output / "parameters.json").write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    print("STUDIO_MMD_PREPARED", json.dumps(report["glb"]))


if __name__ == "__main__":
    run()
