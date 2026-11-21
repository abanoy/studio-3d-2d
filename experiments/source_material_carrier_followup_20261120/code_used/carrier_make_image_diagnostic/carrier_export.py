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



# These values are fixed call-site labels from the pinned owned H636a collector.
# No SDK exception text, object representation, filename or arbitrary type name
# may cross this public diagnostic boundary.
_PUBLIC_LATCH_STAGES = frozenset((
    'restore_ownership_or_identity', 'pre_export_hook', 'gather_return_wrapper',
    'cache_return_wrapper', 'extractor_observer', 'gather_mesh_hook',
    'gather_material_hook', 'gather_texture_info_hook', 'gather_texture_hook',
    'gather_image_hook', 'pre_encoding_resource_wrapper',
    'shared_image_cache_gather_image', 'shared_image_cache_make_image',
    'shared_image_cache_buffer_view', 'shared_image_cache_uri',
    'shared_image_cache_gather_texture', 'shared_image_cache_texture_info',
    'actual_reference_assignment', 'extractor_complete_class_restoration',
))
_PUBLIC_LATCH_TYPES = frozenset(('Refusal', 'AttributeError', 'TypeError', 'ValueError',
    'KeyError', 'IndexError', 'RuntimeError', 'OverflowError', 'MemoryError', 'AssertionError'))


def public_latch_failure(session):
    """Best-effort bounded metadata only; never inspect an SDK error/message.

    Read owned plain instance dictionaries rather than latch/first properties.
    A caller must never turn this diagnostic into a success or cleanup gate.
    """
    value = dict(format='has_carrier_safe_latch_failure_1', status='NO_LATCHED_FAILURE',
                 latched_failure_observed=False)
    try:
        if session is None:
            value['status'] = 'SESSION_NOT_CREATED'
            return value
        namespace = object.__getattribute__(session, '__dict__')
        if type(namespace) is not dict:
            value['status'] = 'UNADMITTED_LATCH_METADATA'
            return value
        latch = namespace.get('latch')
        if latch is None:
            return value
        fields = object.__getattribute__(latch, '__dict__')
        if type(fields) is not dict:
            value['status'] = 'UNADMITTED_LATCH_METADATA'
            return value
        first, count = fields.get('first'), fields.get('count')
        if first is None:
            return value
        if (type(first) is not tuple or len(first) != 2 or
                type(first[0]) is not str or first[0] not in _PUBLIC_LATCH_STAGES or
                type(first[1]) is not str or type(count) is not int or not 1 <= count <= 65536):
            value['status'] = 'UNADMITTED_LATCH_METADATA'
            return value
        return dict(format=value['format'], status='LATCHED_FAILURE', latched_failure_observed=True,
                    stage=first[0], exception_category=first[1] if first[1] in _PUBLIC_LATCH_TYPES else 'OtherError',
                    failures=count)
    except BaseException:
        # Diagnostics must preserve the original operator/cleanup exception.
        value['status'] = 'UNAVAILABLE_LATCH_METADATA'
        return value


_MATERIAL_REPORT_FORMAT = "has_strict_material_guard_failure_observation_1"
_MATERIAL_CODES = frozenset(["unsupported_gathered_material_profile","material_texture_reachability_missing","unexpected_texture_on_untextured_material","repeated_or_aliased_material_hook","OTHER_MATERIAL_FAILURE"])
_MATERIAL_TYPES = frozenset(["NONE","BOOL","INT","FLOAT","STR","LIST","TUPLE","DICT","OTHER","UNAVAILABLE"])
_MATERIAL_KHR_NAMES = frozenset(["KHR_materials_anisotropy","KHR_materials_clearcoat","KHR_materials_dispersion","KHR_materials_emissive_strength","KHR_materials_ior","KHR_materials_iridescence","KHR_materials_sheen","KHR_materials_specular","KHR_materials_transmission","KHR_materials_unlit","KHR_materials_variants","KHR_materials_volume","KHR_materials_diffuse_transmission","KHR_materials_pbrSpecularGlossiness"])
_MATERIAL_KHR_FIELDS = frozenset(["anisotropyStrength","anisotropyRotation","anisotropyTexture","clearcoatFactor","clearcoatTexture","clearcoatRoughnessFactor","clearcoatRoughnessTexture","clearcoatNormalTexture","dispersion","emissiveStrength","ior","iridescenceFactor","iridescenceTexture","iridescenceIor","iridescenceThicknessMinimum","iridescenceThicknessMaximum","iridescenceThicknessTexture","sheenColorFactor","sheenColorTexture","sheenRoughnessFactor","sheenRoughnessTexture","specularFactor","specularTexture","specularColorFactor","specularColorTexture","transmissionFactor","transmissionTexture","thicknessFactor","thicknessTexture","attenuationDistance","attenuationColor","diffuseTransmissionFactor","diffuseTransmissionTexture","diffuseTransmissionColorFactor","diffuseTransmissionColorTexture","diffuseFactor","diffuseTexture","specularGlossinessTexture","glossinessFactor"])
_MATERIAL_OBS_BOOLS = ["actual_material_type","fields_available","source_graph_has_images"]
_MATERIAL_OBS_COUNTS = ["source_graph_matches","captured_image_socket_count","positive_info_identity_matches","positive_info_graph_key_matches","gathered_material_count","repeated_material_identity_count","repeated_source_identity_count"]
_MATERIAL_FIELD_KEYS = frozenset(["extensions","extras","normal_texture","occlusion_texture","emissive_texture","pbr_metallic_roughness","metallic_roughness_texture","base_color_texture"])
_MATERIAL_GUARD_KEYS = frozenset(["source_graph_is_unique","extensions_is_none","extensions_is_exact_empty_dict","extras_is_none","normal_texture_is_none","occlusion_texture_is_none","emissive_texture_is_none","pbr_is_present","pbr_type_is_expected","pbr_fields_available","metallic_roughness_texture_is_none"])


def _material_dict(value, names):
    if type(value) is not dict or len(value) != len(names):
        raise ValueError('Material diagnostic shape')
    for key in value:
        if type(key) is not str or len(key) > 128 or key not in names:
            raise ValueError('Material diagnostic key')
    return value


def _material_bool(value):
    if type(value) is not bool: raise ValueError('Material diagnostic bool')
    return value


def _material_count(value, maximum=65536):
    if type(value) is not int or not 0 <= value <= maximum: raise ValueError('Material diagnostic count')
    return value


def _material_enum(value, options):
    if type(value) is not str or len(value) > 128 or value not in options:
        raise ValueError('Material diagnostic enum')
    return value


def _material_types(value, allowed):
    if type(value) is not dict or len(value) > len(allowed): raise ValueError('Material field types')
    result = {}
    for key, label in value.items():
        if type(key) is not str or len(key) > 128 or key not in allowed:
            raise ValueError('Material field type key')
        result[key] = _material_enum(label, _MATERIAL_TYPES)
    return result


def _material_extensions(value):
    names = ('field_type', 'count', 'count_in_budget', 'known', 'unknown_name_count', 'non_string_name_count')
    row = _material_dict(value, names)
    result = dict(field_type=_material_enum(row['field_type'], _MATERIAL_TYPES),
        count=_material_count(row['count']), count_in_budget=_material_bool(row['count_in_budget']),
        known=[], unknown_name_count=_material_count(row['unknown_name_count']),
        non_string_name_count=_material_count(row['non_string_name_count']))
    known = row['known']
    if type(known) is not list or len(known) > len(_MATERIAL_KHR_NAMES): raise ValueError('Known extension budget')
    seen = set()
    fields = ('name', 'value_type', 'plain_wrapper_fields', 'wrapper_name_matches', 'payload_type',
              'payload_count', 'payload_count_in_budget', 'known_field_types', 'unknown_field_count', 'non_string_field_count')
    for raw in known:
        raw = _material_dict(raw, fields)
        name = _material_enum(raw['name'], _MATERIAL_KHR_NAMES)
        if name in seen: raise ValueError('Duplicate known extension')
        seen.add(name)
        item = dict(name=name, value_type=_material_enum(raw['value_type'], _MATERIAL_TYPES),
            plain_wrapper_fields=_material_bool(raw['plain_wrapper_fields']),
            wrapper_name_matches=_material_bool(raw['wrapper_name_matches']),
            payload_type=_material_enum(raw['payload_type'], _MATERIAL_TYPES),
            payload_count=_material_count(raw['payload_count']),
            payload_count_in_budget=_material_bool(raw['payload_count_in_budget']),
            known_field_types=_material_types(raw['known_field_types'], _MATERIAL_KHR_FIELDS),
            unknown_field_count=_material_count(raw['unknown_field_count']),
            non_string_field_count=_material_count(raw['non_string_field_count']))
        if item['wrapper_name_matches'] and not item['plain_wrapper_fields']:
            raise ValueError('Extension shape flags')
        if item['payload_type'] == 'DICT':
            if item['payload_count_in_budget']:
                if item['payload_count'] > 64 or (len(item['known_field_types']) + item['unknown_field_count'] +
                        item['non_string_field_count']) != item['payload_count']:
                    raise ValueError('Extension payload counts')
            elif (item['payload_count'] <= 64 or item['known_field_types'] or
                  item['unknown_field_count'] or item['non_string_field_count']):
                raise ValueError('Unenumerated extension payload')
        elif (item['payload_count'] or item['payload_count_in_budget'] or item['known_field_types'] or
              item['unknown_field_count'] or item['non_string_field_count']):
            raise ValueError('Non-dict extension payload')
        result['known'].append(item)
    if [item['name'] for item in result['known']] != sorted(seen):
        raise ValueError('Known extension order')
    if result['field_type'] == 'DICT':
        if result['count_in_budget']:
            if result['count'] > 32 or len(known) + result['unknown_name_count'] + result['non_string_name_count'] != result['count']:
                raise ValueError('Extension dictionary counts')
        elif result['count'] <= 32 or known or result['unknown_name_count'] or result['non_string_name_count']:
            raise ValueError('Unenumerated extension dictionary')
    elif result['count'] or result['count_in_budget'] or known or result['unknown_name_count'] or result['non_string_name_count']:
        raise ValueError('Non-dict extensions')
    return result


def _copy_material_report(value):
    names = ('format', 'status', 'failures', 'failure_count_capped', 'first_refusal_code', 'observation',
             'original_strict_failure_preserved', 'material_admission_changed', 'resource_equivalence_qualified')
    value = _material_dict(value, names)
    result = dict(format=_material_enum(value['format'], {_MATERIAL_REPORT_FORMAT}),
        status=_material_enum(value['status'], {'OBSERVED', 'UNAVAILABLE'}),
        failures=_material_count(value['failures'], 128),
        failure_count_capped=_material_bool(value['failure_count_capped']),
        first_refusal_code=_material_enum(value['first_refusal_code'], _MATERIAL_CODES),
        observation=None, original_strict_failure_preserved=True, material_admission_changed=False,
        resource_equivalence_qualified=False)
    if not result['failures'] or (result['failure_count_capped'] and result['failures'] != 128):
        raise ValueError('Material failure count')
    if (value['original_strict_failure_preserved'] is not True or value['material_admission_changed'] is not False or
            value['resource_equivalence_qualified'] is not False):
        raise ValueError('Material diagnostic claims')
    observation = value['observation']
    if result['status'] == 'UNAVAILABLE':
        if observation is not None: raise ValueError('Unavailable material observation')
        return result
    row = _material_dict(observation, (*_MATERIAL_OBS_BOOLS, *_MATERIAL_OBS_COUNTS, 'field_types', 'guards', 'extensions'))
    copied = {key: _material_bool(row[key]) for key in _MATERIAL_OBS_BOOLS}
    copied.update((key, _material_count(row[key])) for key in _MATERIAL_OBS_COUNTS)
    copied['field_types'] = _material_types(row['field_types'], _MATERIAL_FIELD_KEYS)
    guards = row['guards']
    if copied['fields_available']:
        if set(copied['field_types']) != _MATERIAL_FIELD_KEYS: raise ValueError('Complete material field types')
        _material_dict(guards, _MATERIAL_GUARD_KEYS)
        copied['guards'] = {key: _material_bool(guards[key]) for key in _MATERIAL_GUARD_KEYS}
    else:
        if copied['field_types'] or type(guards) is not dict or guards: raise ValueError('Uninspected material fields')
        copied['guards'] = {}
    copied['extensions'] = _material_extensions(row['extensions'])
    result['observation'] = copied
    return result


def _owned_material_fields(value):
    klass = type(value)
    if type(klass) is not type or klass.__getattribute__ is not object.__getattribute__:
        return None
    bases = klass.__mro__
    if len(bases) > 32 or any(type(base) is not type or '__getattr__' in base.__dict__ for base in bases):
        return None
    for base in bases:
        if '__dict__' in base.__dict__:
            descriptor = base.__dict__['__dict__']
            if type(descriptor) is not types.GetSetDescriptorType or descriptor.__objclass__ is not base:
                return None
            result = descriptor.__get__(value, klass)
            return result if type(result) is dict and len(result) <= 128 and all(type(key) is str for key in result) else None
    return None


def public_material_failure(session):
    """Copy only the closed safe schema; absence is not a fabricated diagnosis."""
    try:
        fields = _owned_material_fields(session)
        if fields is None or 'resources' not in fields:
            return None
        resource_fields = _owned_material_fields(fields['resources'])
        if resource_fields is None or resource_fields.get('public_material_failure') is None:
            return None
        return _copy_material_report(resource_fields['public_material_failure'])
    except BaseException:
        # No error text, unknown key/name/value or mutable source payload escapes.
        return dict(format='has_carrier_material_diagnostic_admission_1',
                    status='UNADMITTED_RESOURCE_DIAGNOSTIC', copied=False)


_MAKE_IMAGE_REPORT_FORMAT = 'has_strict_make_image_return_failure_observation_1'
_MAKE_IMAGE_BOOL_FIELDS = (
    'cache_hit', 'expected_buffer_is_binary_data', 'expected_buffer_is_retained',
    'result_is_expected_image_type', 'result_buffer_is_expected_buffer',
    'result_mime_is_png', 'result_uri_is_none', 'result_extensions_is_none',
    'result_extras_is_none', 'result_name_matches_frame', 'result_fields_observed',
    'result_buffer_is_binary_data', 'result_buffer_is_exact_int', 'result_buffer_is_none',
    'result_buffer_is_incoming_buffer', 'result_buffer_is_stored_key_buffer',
    'result_buffer_is_retained', 'result_buffer_hash_matches_authorized_source',
    'incoming_buffer_is_retained', 'incoming_buffer_hash_matches_authorized_source',
    'stored_buffer_is_binary_data', 'stored_buffer_is_retained',
    'stored_buffer_hash_matches_authorized_source',
    'expected_buffer_hash_matches_authorized_source',
    'authorized_source_ticket_observed', 'all_strict_return_predicates_pass',
)


def _copy_make_image_report(value):
    names = ('format', 'status', 'failures', 'failure_count_capped', 'first_refusal_code',
             'observation', 'original_strict_failure_preserved', 'make_image_admission_changed',
             'resource_equivalence_qualified')
    value = _material_dict(value, names)
    result = dict(format=_material_enum(value['format'], {_MAKE_IMAGE_REPORT_FORMAT}),
        status=_material_enum(value['status'], {'OBSERVED', 'UNAVAILABLE'}),
        failures=_material_count(value['failures'], 128),
        failure_count_capped=_material_bool(value['failure_count_capped']),
        first_refusal_code=_material_enum(value['first_refusal_code'], {'shared_make_image_return_differs'}),
        observation=None, original_strict_failure_preserved=True,
        make_image_admission_changed=False, resource_equivalence_qualified=False)
    if not result['failures'] or (result['failure_count_capped'] and result['failures'] != 128):
        raise ValueError('Make image failure count')
    if (value['original_strict_failure_preserved'] is not True or
            value['make_image_admission_changed'] is not False or
            value['resource_equivalence_qualified'] is not False):
        raise ValueError('Make image diagnostic claims')
    if result['status'] == 'UNAVAILABLE':
        if value['observation'] is not None: raise ValueError('Unavailable make image observation')
    else:
        row = _material_dict(value['observation'], _MAKE_IMAGE_BOOL_FIELDS)
        result['observation'] = {key: _material_bool(row[key]) for key in _MAKE_IMAGE_BOOL_FIELDS}
    return result


def public_make_image_failure(session):
    """Copy owned S boolean metadata only; never inspect an SDK image or error."""
    try:
        fields = _owned_material_fields(session)
        if fields is None or 'shared_cache' not in fields:
            return None
        cache_fields = _owned_material_fields(fields['shared_cache'])
        if cache_fields is None:
            raise ValueError('Unadmitted shared cache instance')
        report = cache_fields.get('public_make_image_failure')
        if report is None:
            return None
        return _copy_make_image_report(report)
    except BaseException:
        return dict(format='has_carrier_make_image_diagnostic_admission_1',
                    status='UNADMITTED_SHARED_CACHE_DIAGNOSTIC', copied=False)


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
    session=None
    try:
        if own_enable:bpy.ops.preferences.addon_enable(module='io_scene_gltf2')
        addon=importlib.import_module('io_scene_gltf2')
        modules={}
        for key,(relative,_pin) in hook.PINS.items():
            name='io_scene_gltf2' if key=='addon' else 'io_scene_gltf2.'+relative[:-3].replace('/','.')
            modules[key]=importlib.import_module(name)
        binary=importlib.import_module('io_scene_gltf2.io.exp.binary_data')
        surface=hook.PinnedSurface(modules,observer,binder,shared_binary_module=binary,
            empty_material_extension_module=modules['exporter'].gltf2_io_extensions)
        resources=resource_module.SimplePackedResources(materials,tickets,bpy.types,modules['search'],modules['encode'],
                                                        modules['gltf'],allow_shared_images=True,
            empty_material_extension_profile=surface.empty_material_extension_profile)
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
        try:
            activity['export_failure_latch']=public_latch_failure(session)
            material_failure=public_material_failure(session)
            if material_failure is not None:
                activity['export_material_failure']=material_failure
        except BaseException:
            pass  # Even diagnostic allocation/property failures cannot replace the primary.
        try:
            make_image_failure=public_make_image_failure(session)
            if make_image_failure is not None:
                activity['export_make_image_failure']=make_image_failure
        except BaseException:
            pass  # Independent bounded S diagnostics never replace the original failure.
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
