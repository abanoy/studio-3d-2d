"""Pinned SourceIO structures only; inert metadata, no animation/mesh export."""
from pathlib import Path
import argparse
import collections
import hashlib
import importlib.util
import json
import os
import struct
import sys

sys.dont_write_bytecode = True
os.environ['NO_BPY'] = '1'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--sourceio', type=Path, required=True)
p.add_argument('--inventory', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
args = p.parse_args()
if args.output.exists() or args.output.is_symlink():
    raise FileExistsError(args.output)
owned = args.inventory.resolve(strict=True).parent
if not args.output.resolve().is_relative_to(owned):
    raise ValueError('Keep full native metadata inside the owned inventory output folder')
root = args.sourceio.resolve(strict=True)
EXPECTED_READER_SHA256 = {'__init__.py': '4693edee91a621e43c0524ee0437774d6a3039f270089967306104ba560e9225', 'library/models/mdl/structs/header.py': '03fe4f685c3818785c9b5ff81356f91aa9ab8160d1a17ca27e57520a1c37f57f', 'library/models/mdl/structs/flex.py': '93887e58a4918500a237246243b97b0c9f12126534d6abdc6beed247fc682ca9', 'library/models/mdl/structs/bone.py': 'a61a3e0378e7b2d2d070f2b9ef138b78516db4a9830144cd6a6d907295b7d085', 'library/models/mdl/structs/bodygroup.py': '34d41c35681550fe4512c0541bcb859c076a960d04054efb633c098ff70c17b8'}
for relative, expected in EXPECTED_READER_SHA256.items():
    if hashlib.sha256((root/relative).read_bytes()).hexdigest() != expected:
        raise ValueError('Pinned metadata reader layout differs: '+relative)
spec = importlib.util.spec_from_file_location('SourceIO', root/'__init__.py', submodule_search_locations=[str(root)])
module = importlib.util.module_from_spec(spec)
sys.modules['SourceIO'] = module
spec.loader.exec_module(module)
from SourceIO.library.utils import MemoryBuffer
from SourceIO.library.models.mdl.structs.header import MdlHeaderV49
from SourceIO.library.models.mdl.structs.bone import Bone, ProceduralBoneType
from SourceIO.library.models.mdl.structs.bodygroup import BodyPart
from SourceIO.library.models.mdl.structs.material import MaterialV49
from SourceIO.library.models.mdl.structs.flex import FlexController, FlexControllerUI, FlexRule
from SourceIO.library.models.mdl.structs.attachment import Attachment
from SourceIO.library.models.mdl.structs.sequence import StudioSequence
from SourceIO.library.models.mdl.structs.local_animation import StudioAnimDesc


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def records(buffer, offset, count, reader):
    if not 0 <= offset <= buffer.size() or not 0 <= count <= 8192:
        raise ValueError('Metadata record range exceeds budget')
    buffer.seek(offset)
    return [reader(buffer) for _ in range(count)]


manifest = json.loads(args.inventory.read_bytes())
stage = Path(manifest['stage']).resolve(strict=True)
if stage != (owned/'stage').resolve(strict=True):
    raise ValueError('Inventory stage must be inside its owned output folder')
results = []
for entry in manifest['models']:
    path = (stage/entry['staged_member']).resolve(strict=True)
    if not path.is_relative_to(stage) or path.stat().st_size > 16*1024*1024:
        raise ValueError('Model escaped stage or exceeds16MiB')
    before = (digest(path), path.stat().st_mtime_ns)
    if before[0] != entry['sha256']:
        raise ValueError('Staged definition changed')
    row = {k: entry[k] for k in ['archive', 'member', 'sha256', 'bytes', 'version']}
    raw = path.read_bytes()
    try:
        if len(raw) < 80 or raw[:4] != b'IDST' or struct.unpack_from('<I', raw, 76)[0] != len(raw):
            raise ValueError('Invalid MDL header/size')
        version = struct.unpack_from('<I', raw, 4)[0]
        row['version'] = version
        if version != 49:
            row['refused'] = 'Unsupported actual MDL version; this pass supports49only'
            results.append(row)
            continue
        buffer = MemoryBuffer(raw)
        header = MdlHeaderV49.from_buffer(buffer)
        limits = {'bone_count': 512, 'body_part_count': 256, 'skin_family_count': 256,
                  'skin_reference_count': 2048, 'texture_count': 2048, 'flex_desc_count': 4096,
                  'flex_controller_count': 4096, 'flex_rule_count': 4096, 'flex_controller_ui_count': 4096,
                  'local_attachment_count': 1024, 'local_sequence_count': 1024,
                  'local_animation_count': 1024, 'include_model_count': 128}
        for key, limit in limits.items():
            if not 0 <= getattr(header, key) <= limit:
                raise ValueError('Header budget exceeded: '+key)
        bone_types = []
        def read_bone(b):
            # The pinned constructor fills its type-labelled attribute with the
            # parsed rule object. Read the native uint32 at the same MDL49 field
            # used by that reader; leave the reader/runtime and model unchanged.
            start = b.tell()
            with b.read_from_offset(start+164):
                bone_types.append(b.read_uint32())
            return Bone.from_buffer(b, version)
        bones = records(buffer, header.bone_offset, header.bone_count, read_bone)
        materials = records(buffer, header.texture_offset, header.texture_count, lambda b: MaterialV49.from_buffer(b, version))
        parts = records(buffer, header.body_part_offset, header.body_part_count, lambda b: BodyPart.from_buffer(b, version))
        controllers = records(buffer, header.flex_controller_offset, header.flex_controller_count, lambda b: FlexController.from_buffer(b, version))
        ui = records(buffer, header.flex_controller_ui_offset, header.flex_controller_ui_count, lambda b: FlexControllerUI.from_buffer(b, version))
        rules = records(buffer, header.flex_rule_offset, header.flex_rule_count, lambda b: FlexRule.from_buffer(b, version))
        attachments = records(buffer, header.local_attachment_offset, header.local_attachment_count, lambda b: Attachment.from_buffer(b, version))
        sequences = records(buffer, header.local_sequence_offset, header.local_sequence_count, lambda b: StudioSequence.from_buffer(b, version))
        animation_headers = records(buffer, header.local_animation_offset, header.local_animation_count, StudioAnimDesc.from_buffer)
        buffer.seek(header.flex_desc_offset)
        names = [buffer.read_source1_string(buffer.tell()) for _ in range(header.flex_desc_count)]
        buffer.seek(header.skin_family_offset)
        skin_indices = [[buffer.read_uint16() for _ in range(header.skin_reference_count)] for _ in range(header.skin_family_count)]
        if any(i >= len(materials) for family in skin_indices for i in family):
            raise ValueError('Skin material reference out of range')
        skins = [[materials[i].name for i in family] for family in skin_indices]
        buffer.seek(header.include_model_offset)
        includes = []
        for _ in range(header.include_model_count):
            offset = buffer.tell()
            label = buffer.read_source1_string(offset)
            includes.append({'label': label, 'model': buffer.read_source1_string(offset)})
        parents = [bone.parent_id for bone in bones]
        valid = all(-1 <= parent < len(parents) for parent in parents)
        for index in range(len(parents)):
            at, seen = index, set()
            while at != -1:
                if at in seen or not 0 <= at < len(parents):
                    valid = False
                    break
                seen.add(at)
                at = parents[at]
        if not valid:
            raise ValueError('Invalid bone parent hierarchy')
        bodygroups = [{'index': i, 'name': part.name,
                       'choices': [{'index': j, 'name': model.name, 'vertices': model.vertex_count,
                                    'meshes': len(model.meshes), 'blank': model.vertex_count == 0,
                                    'mesh_flex_records': sum(len(mesh.flexes) for mesh in model.meshes)}
                                   for j, model in enumerate(part.models)]}
                      for i, part in enumerate(parts)]
        ops = collections.Counter(op.op.name for rule in rules for op in rule.flex_ops)
        procedural = [{'index': i, 'name': bone.name, 'type': bone_types[i],
                       'type_name': ProceduralBoneType(bone_types[i]).name,
                       'rule_parsed': bone.procedural_rule is not None}
                      for i, bone in enumerate(bones) if bone_types[i]]
        row.update(bones=[{'index': i, 'name': bone.name, 'parent': bone.parent_id, 'flags': int(bone.flags)} for i, bone in enumerate(bones)],
                   valid_hierarchy=True, bodygroups=bodygroups, skin_family_count=len(skins),
                   distinct_skin_families=len({tuple(family) for family in skin_indices}), skin_groups=skins,
                   material_names=[material.name for material in materials], flex_names=names,
                   controllers=[{'index': i, 'name': c.name, 'group': c.group, 'min': c.min, 'max': c.max} for i, c in enumerate(controllers)],
                   controller_ui=[{'name': c.name, 'controller': c.controller, 'left': c.left_controller,
                                   'right': c.right_controller, 'remap': c.remap_type.name, 'stereo': bool(c.stereo)} for c in ui],
                   flex_rules=[{'target': rule.flex_index, 'target_name': names[rule.flex_index],
                                'ops': [{'op': op.op.name, 'value': op.value} for op in rule.flex_ops]} for rule in rules],
                   rule_op_counts=dict(ops), procedural_bones=procedural,
                   attachments=[{'name': a.name, 'parent_bone': a.parent_bone} for a in attachments],
                   local_pose_parameter_count=header.local_pose_paramater_count, ik_chain_count=header.ik_chain_count,
                   sequences=[{'name': s.name, 'activity': s.activity_name, 'flags': s.flags,
                               'last_frame': s.last_frame, 'events': len(s.events), 'blends': s.blend_count} for s in sequences],
                   animation_headers=[{'name': a.name, 'frames': a.frame_count, 'fps': a.fps, 'flags': int(a.flags)} for a in animation_headers],
                   include_models=includes)
    except Exception as error:
        row['error'] = type(error).__name__+': '+str(error)
    if (digest(path), path.stat().st_mtime_ns) != before:
        raise ValueError('Staged input changed during parsing')
    results.append(row)
    print(json.dumps({'archive': row['archive'], 'member': row['member'], 'error': row.get('error')}), flush=True)
summary = {'definitions': len(results), 'distinct_sha256': len({r['sha256'] for r in results}),
           'parsed': sum('bones' in r for r in results), 'errors': sum('error' in r for r in results),
           'refused_versions': sum('refused' in r for r in results),
           'multi_skin_models': sum(r.get('distinct_skin_families', 0) > 1 for r in results),
           'models_with_procedural_bones': sum(bool(r.get('procedural_bones')) for r in results)}
value = {'format': 'has_sfm_native_feature_metadata_1', 'summary': summary, 'models': results,
         'sourceio_version': list(module.bl_info['version']), 'python_version': sys.version,
         'procedural_type_source': 'Native MDL49 bone-record uint32 at offset164, matching the pinned Bone.from_buffer layout; its type-labelled object attribute is not used as an integer.',
         'scope': 'Pinned native metadata structures only; no animation-frame decoding, scene import, textures, render, scripts or native feature acceptance.'}
encoded = (json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False)+'\n').encode()
if len(encoded) > 16*1024*1024:
    raise ValueError('Metadata exceeds16MiB')
with args.output.open('xb') as stream:
    stream.write(encoded)
print(json.dumps(summary), flush=True)
