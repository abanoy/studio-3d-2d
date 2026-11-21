"""UNRUN one bounded carrier export on genuinely observed fresh objects.

No Blender/NumPy import or operator at module import. Actual host supplies
authenticated modules, refs/facts and the verified packed-buffer admission.
"""
import hashlib
import importlib
import json
import math
import os
import stat
import struct
import sys
import types

CARRIER = '_HAS_NATIVE_NORMAL_ID'
MAX_GLB = 128 * 1024 * 1024


class Refusal(ValueError):
    pass


def need(value, code):
    if not value:
        raise Refusal(code)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def matrix_words(matrix):
    rows=tuple(tuple(row) for row in matrix)
    need(len(rows)==4 and all(len(row)==4 for row in rows) and
         all(type(value) is float and math.isfinite(value) for row in rows for value in row),'BOUNDED_ACTUAL_MATRIX_REQUIRED')
    return tuple(tuple(value.hex() for value in row) for row in rows)


def rna_key(value, owner, bpy):
    actual_type=type(value)
    need(value.id_data is owner and getattr(bpy.types,actual_type.__name__,None) is actual_type,
         'ACTUAL_OWNED_ATTRIBUTE_RNA_REQUIRED')
    pointer=value.as_pointer()
    need(type(pointer) is int and 0<pointer<2**64,'ATTRIBUTE_POINTER_REQUIRED')
    return actual_type,owner,pointer


def same_key(a,b):
    return a[0] is b[0] and a[1] is b[1] and a[2]==b[2]


def attribute_inventory(mesh,bpy):
    need(len(mesh.attributes)<=256,'ATTRIBUTE_INVENTORY_BUDGET')
    return tuple((attribute.name,attribute.data_type,attribute.domain,rna_key(attribute,mesh,bpy))
                 for attribute in mesh.attributes)


class CarrierScene:
    def __init__(self,bpy,np,container,ledger,facts,snapshot,primitive_counts):
        self.bpy,self.np,self.container,self.ledger,self.facts,self.snapshot=bpy,np,container,ledger,facts,snapshot
        need(type(primitive_counts) is dict and set(primitive_counts)==set(facts),'INDEPENDENT_PRIMITIVE_COUNTS_REQUIRED')
        self.entries=[]
        self.selection=tuple(obj for obj in bpy.context.selected_objects)
        self.active=bpy.context.view_layer.objects.active
        self.linked=[]
        self.installed=[]
        self.armature=container.armature
        self.armature_world=matrix_words(self.armature.matrix_world)
        for name,record in ledger.records.items():
            obj,mesh=record['obj'],record['mesh']
            ids=facts[name]['ids']
            need(type(ids) is tuple and 0<len(ids)<=200000 and len(set(ids))==len(ids) and
                 all(type(value) is int and 0<=value<200000 for value in ids),'NATIVE_ID_POINT_DOMAIN')
            need(type(primitive_counts[name]) is int and 1<=primitive_counts[name]<=4,'NATIVE_PRIMITIVE_DOMAIN')
            inventory=attribute_inventory(mesh,bpy)
            need(not any(row[0].casefold()==CARRIER.casefold() for row in inventory),'RESERVED_CARRIER_COLLISION')
            self.entries.append(dict(name=name,object=obj,mesh=mesh,ids=ids,inventory=inventory,
                world=matrix_words(obj.matrix_world),primitive_count=primitive_counts[name],attribute=None,key=None))
        need(len(self.entries)==2 and sum(row['primitive_count'] for row in self.entries)==4,'CLOSED_TWO_MESH_FOUR_PRIMITIVE_PROFILE')

    def point_admission(self):
        need(self.container.armature is self.armature and matrix_words(self.armature.matrix_world)==self.armature_world,
             'ARMATURE_ID_OR_WORLD_CHANGED')
        for row in self.entries:
            obj,mesh=row['object'],row['mesh']
            need(obj.data is mesh and obj.original is obj and mesh.original is mesh and
                 matrix_words(obj.matrix_world)==row['world'],'CURRENT_OBJECT_MESH_OR_WORLD_CHANGED')
            self.ledger._snapshot(self.facts[row['name']],self.snapshot(obj,mesh),False)
            current=attribute_inventory(mesh,self.bpy)
            original=[item for item in current if item[0].casefold()!=CARRIER.casefold()]
            need(len(original)==len(row['inventory']) and all(
                a[:3]==b[:3] and same_key(a[3],b[3]) for a,b in zip(original,row['inventory'])),
                'SOURCE_ATTRIBUTE_INVENTORY_CHANGED')
            owned=[item for item in current if item[0].casefold()==CARRIER.casefold()]
            if row['attribute'] is None:
                need(not owned,'UNOWNED_CARRIER_PRESENT')
            else:
                need(len(owned)==1 and owned[0][:3]==(CARRIER,'FLOAT','POINT') and
                     same_key(owned[0][3],row['key']),'OWNED_CARRIER_REFERENCE_CHANGED')
                attribute=mesh.attributes.get(CARRIER)
                data=self.np.empty(len(row['ids']),dtype=self.np.float32)
                need(len(attribute.data)==len(row['ids']),'CARRIER_POINT_COUNT_CHANGED')
                attribute.data.foreach_get('value',data)
                expected=struct.pack('<'+'f'*len(row['ids']),*(value+1 for value in row['ids']))
                need(data.tobytes()==expected,'CARRIER_F32_ID_WORDS_CHANGED')
        return True

    def install(self):
        self.point_admission()
        if not any(value is self.armature for value in self.bpy.context.scene.objects):
            self.bpy.context.scene.collection.objects.link(self.armature)
            self.linked.append(self.armature)
        for row in self.entries:
            obj,mesh=row['object'],row['mesh']
            if not any(value is obj for value in self.bpy.context.scene.objects):
                self.bpy.context.scene.collection.objects.link(obj)
                self.linked.append(obj)
            attribute=mesh.attributes.new(name=CARRIER,type='FLOAT',domain='POINT')
            row['attribute'],row['key']=attribute,rna_key(attribute,mesh,self.bpy)
            self.installed.append(row)
            data=self.np.asarray([value+1 for value in row['ids']],dtype=self.np.float32)
            attribute.data.foreach_set('value',data)
        for obj in self.bpy.context.scene.objects:obj.select_set(False)
        for obj in [row['object'] for row in self.entries]+[self.armature]:obj.select_set(True)
        self.bpy.context.view_layer.objects.active=self.armature
        self.bpy.context.view_layer.update()
        self.point_admission()

    def admissions(self):
        return [dict(object=row['object'],mesh=row['mesh'],joined_source_ids=list(row['ids']),
                     material_slots=tuple(row['mesh'].materials),primitive_count=row['primitive_count'])
                for row in self.entries]

    def close(self):
        errors=[]
        for row in reversed(self.installed):
            try:
                current=row['mesh'].attributes.get(CARRIER)
                need(current is not None and same_key(rna_key(current,row['mesh'],self.bpy),row['key']),
                     'FOREIGN_CARRIER_NOT_REMOVED')
                row['mesh'].attributes.remove(current)
                row['attribute']=None
            except BaseException as error:errors.append(type(error).__name__)
        for obj in self.linked:
            try:self.bpy.context.scene.collection.objects.unlink(obj)
            except BaseException as error:errors.append(type(error).__name__)
        try:
            for obj in self.bpy.context.scene.objects:obj.select_set(False)
            for obj in self.selection:obj.select_set(True)
            self.bpy.context.view_layer.objects.active=self.active
            self.bpy.context.view_layer.update()
            self.point_admission()
        except BaseException as error:errors.append(type(error).__name__)
        need(not errors,'OWNED_CARRIER_SCENE_RESTORATION_FAILED')


def output_stamp(info):
    return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_nlink,
            getattr(info,'st_file_attributes',0)&~0x40000)


def fresh_owned_carrier_path(path,owned_output):
    need(path.parent==owned_output and path.name=='carrier.glb','EXACT_OWNED_CARRIER_PATH_REQUIRED')
    for parent in (owned_output,*owned_output.parents):
        info=parent.lstat()
        need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode) and
             not getattr(info,'st_file_attributes',0)&0x400,'CARRIER_PARENT_LINK_OR_REPARSE')
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise Refusal('CARRIER_OUTPUT_ALREADY_EXISTS_OR_LINK')


def read_owned_carrier(path,owned_output):
    need(path.parent==owned_output and path.name=='carrier.glb','EXACT_OWNED_CARRIER_PATH_REQUIRED')
    before=path.lstat()
    need(stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode) and before.st_nlink==1 and
         not getattr(before,'st_file_attributes',0)&0x400 and 28<=before.st_size<=MAX_GLB,
         'CARRIER_OUTPUT_TYPE_LINK_OR_BUDGET')
    with path.open('rb') as stream:
        need(output_stamp(os.fstat(stream.fileno()))==output_stamp(before),'CARRIER_OUTPUT_CHANGED_BEFORE_READ')
        raw=stream.read(MAX_GLB+1)
        opened=os.fstat(stream.fileno())
    need(len(raw)==before.st_size and output_stamp(opened)==output_stamp(before)==output_stamp(path.lstat()),
         'CARRIER_OUTPUT_CHANGED_DURING_READ')
    return raw


def operator_profile(path):
    kwargs=dict(filepath=str(path),export_format='GLB',use_selection=True,export_animations=False,
        export_current_frame=True,export_cameras=False,export_lights=False,export_extras=False,export_yup=True,
        export_apply=False,export_skins=True,export_normals=True,export_texcoords=True,export_tangents=False,
        export_morph=False,export_attributes=True,export_shared_accessors=False,export_materials='EXPORT',
        export_keep_originals=False,export_draco_mesh_compression_enable=False,export_image_format='AUTO',
        export_unused_textures=False,export_unused_images=False,export_image_add_webp=False,export_image_webp_fallback=False)
    options=dict(gltf_format='GLB',gltf_selected=True,gltf_animations=False,gltf_current_frame=True,
        gltf_extras=False,gltf_yup=True,gltf_apply=False,gltf_skins=True,gltf_normals=True,gltf_texcoords=True,
        gltf_tangents=False,gltf_attributes=True,gltf_shared_accessors=False,gltf_materials='EXPORT',
        gltf_keep_original_textures=False,gltf_draco_mesh_compression=False,gltf_image_format='AUTO',
        gltf_unused_textures=False,gltf_unused_images=False,gltf_add_webp=False,gltf_webp_fallback=False)
    return kwargs,options


def export_once(bpy,np,container,ledger,facts,snapshot,primitive_counts,materials,tickets,
                hook,resource_module,observer,binder,path,*,owned_output,activity):
    need(type(activity) is dict,'ACTUAL_EXPORT_ACTIVITY_RECORD_REQUIRED')
    fresh_owned_carrier_path(path,owned_output)
    addon=importlib.import_module('io_scene_gltf2')
    enabled_before=tuple(bpy.context.preferences.addons.keys())
    own_enable='io_scene_gltf2' not in enabled_before
    scene=CarrierScene(bpy,np,container,ledger,facts,snapshot,primitive_counts)
    primary=None
    try:
        if own_enable:bpy.ops.preferences.addon_enable(module='io_scene_gltf2')
        addon=importlib.import_module('io_scene_gltf2')
        modules={}
        for key,(relative,_pin) in hook.PINS.items():
            name='io_scene_gltf2' if key=='addon' else 'io_scene_gltf2.'+relative[:-3].replace('/','.')
            modules[key]=importlib.import_module(name)
        binary=importlib.import_module('io_scene_gltf2.io.exp.binary_data')
        surface=hook.PinnedSurface(modules,observer,binder,shared_binary_module=binary)
        resources=resource_module.SimplePackedResources(materials,tickets,bpy.types,modules['search'],modules['encode'],
                                                        modules['gltf'],allow_shared_images=True)
        enabled_names=tuple(bpy.context.preferences.addons.keys())
        hook.extension_inventory(enabled_names)
        kwargs,options=operator_profile(path)
        scene.install()
        class ObservedSession(hook.ExportHookSession):
            def pre_export_hook(self,settings):
                activity['exporter_invoked']=True
                activity['operator_preflight_observed']=True
                return super().pre_export_hook(settings)
        session=ObservedSession(surface,scene.admissions(),np,resources,scene.point_admission,options)
        with session.install(addon,enabled_names):
            activity['operator_call_attempted']=True
            result=bpy.ops.export_scene.gltf(**kwargs)
            need(type(result) is set and result=={'FINISHED'},'ORDINARY_GLTF_OPERATOR_NOT_FINISHED')
        raw=read_owned_carrier(path,owned_output)
        activity['carrier_written']=True
        relation,report=session.finish(raw,sha(raw))
        private=[dict(mesh=mesh,primitive=primitive,one_based_source_ids=list(ids))
                 for (mesh,primitive),ids in sorted(relation.items())]
        relation_raw=(json.dumps(private,sort_keys=True,separators=(',',':'))+'\n').encode()
        return dict(carrier_glb_bytes=len(raw),carrier_glb_sha256=sha(raw),private_relation_bytes=relation_raw,
            private_relation_sha256=sha(relation_raw),export_observation=report,
            operator_invocations=1,own_carrier_attributes=len(scene.entries),ordinary_operator_finished=True,
            exact_owned_attribute_scene_and_registration_restoration_required=True)
    except BaseException as error:
        primary=error
        raise
    finally:
        # Report an owned output even if an operator/hook failed after writing it.
        try:
            present_raw=read_owned_carrier(path,owned_output)
            activity['carrier_output_present_unqualified']=True
            activity['carrier_output_bytes_unqualified']=len(present_raw)
            activity['carrier_output_sha256_unqualified']=sha(present_raw)
        except FileNotFoundError:
            activity['carrier_output_present_unqualified']=False
        except BaseException:
            activity['carrier_output_presence_check_failed']=True
        cleanup_error=None
        try:scene.close()
        except BaseException as error:cleanup_error=error
        try:
            if own_enable and 'io_scene_gltf2' in bpy.context.preferences.addons:
                bpy.ops.preferences.addon_disable(module='io_scene_gltf2')
            need(tuple(bpy.context.preferences.addons.keys())==enabled_before,'ENABLED_ADDON_INVENTORY_NOT_RESTORED')
        except BaseException as error:
            if cleanup_error is None:cleanup_error=error
        activity['scene_or_registration_restoration_failed']=cleanup_error is not None
        if cleanup_error is not None:activity['secondary_cleanup_code']='OWNED_EXPORT_SCENE_OR_REGISTRATION_RESTORATION_FAILED'
        if primary is None and cleanup_error is not None:raise cleanup_error
