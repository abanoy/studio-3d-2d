"""Blender-only runtime probe; no Source model import or installed-host bypass."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys

import bpy
import numpy

PIN = 'fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
CODEC_SHA256 = 'a3ef1d98f3a9489e23b591ec052eaa051467ec3cd7d4f58f6be029474ef58d7f'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sourceio', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    root = args.sourceio.resolve(strict=True)
    codec = root / 'library/utils/pylib/linux/pylib.abi3.so'
    assert hashlib.sha256(codec.read_bytes()).hexdigest() == CODEC_SHA256
    os.environ['NO_BPY'] = '1'
    spec = importlib.util.spec_from_file_location('SourceIO', root / '__init__.py', submodule_search_locations=[str(root)])
    module = importlib.util.module_from_spec(spec)
    sys.modules['SourceIO'] = module
    spec.loader.exec_module(module)
    from SourceIO.blender_bindings.models import import_model
    from SourceIO.blender_bindings.models.common import put_into_collections
    from SourceIO.blender_bindings.operators.import_settings_base import ModelOptions, Source1BSPSettings
    from SourceIO.library.source1.vtf import load_texture
    from SourceIO.library.source1.vmt import VMT
    assert all(callable(x) for x in [import_model, put_into_collections, ModelOptions, Source1BSPSettings, load_texture, VMT])
    # An original standard asset exercises this runtime's real GLB exporter.
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    mesh = bpy.data.meshes.new('OriginalTriangle')
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 0, 1)], [], [(0, 1, 2)])
    actor = bpy.data.objects.new('OriginalRuntimeProbe', mesh)
    bpy.context.collection.objects.link(actor)
    bpy.context.view_layer.objects.active = actor
    actor.select_set(True)
    actor.shape_key_add(name='Basis')
    lift = actor.shape_key_add(name='OriginalLift')
    lift.data[2].co.z += .25
    lift.value = 0
    lift.keyframe_insert(data_path='value', frame=1)
    lift.value = 1
    lift.keyframe_insert(data_path='value', frame=24)
    armature = bpy.data.armatures.new('OriginalRig')
    rig = bpy.data.objects.new('OriginalRig', armature)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    bone = armature.edit_bones.new('OriginalRoot')
    bone.head = (0, 0, 0)
    bone.tail = (0, 0, 1)
    bpy.ops.object.mode_set(mode='OBJECT')
    actor.vertex_groups.new(name='OriginalRoot').add([0, 1, 2], 1, 'REPLACE')
    modifier = actor.modifiers.new('OriginalSkin', 'ARMATURE')
    modifier.object = rig
    actor.parent = rig
    material = bpy.data.materials.new('OriginalMaterial')
    material.use_nodes = True
    material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (.2, .4, .8, 1)
    actor.data.materials.append(material)
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 24
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / 'original-runtime-probe.glb'
    result = bpy.ops.export_scene.gltf(filepath=str(target), export_format='GLB', export_animations=True, export_skins=True, export_morph=True)
    assert result == {'FINISHED'} and target.stat().st_size > 1000
    receipt = dict(format='has_sourceio_worker_probe_1', sourceio_revision=PIN, codec_sha256=CODEC_SHA256,
                   blender=bpy.app.version_string, python=platform.python_version(), libc=platform.libc_ver(), numpy=numpy.__version__,
                   sourceio_blender_bindings_imported=True, original_glb=str(target), original_glb_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                   native_model_conversion=False, installed_host_guard_bypassed=False)
    (args.output / 'runtime.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('SOURCEIO_WORKER_PROBE ' + json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
