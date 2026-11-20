"""UNRUN synthetic proposals only. No Blender/NumPy/native imports, launch or IO.

Root can run: python -B -m unittest discover -s <this-folder> -p test_*.py -v
These fakes exercise lifecycle/identity refusals; they cannot qualify actual APIs.
"""
import hashlib
import sys
import struct
import types
import unittest
import zlib
from types import SimpleNamespace as NS

import export_hook_proposal as H
from resource_gate_proposal import SimplePackedResources, PNG_MAGIC


_next_rna_pointer = 1000


class Identity:
    """No value equality: these stand for actual RNA/glTF object references."""
    def __init__(self, **kw):
        global _next_rna_pointer
        _next_rna_pointer += 1
        self._rna_pointer = _next_rna_pointer
        self.__dict__.update(kw)

    def as_pointer(self): return self._rna_pointer


class Material(Identity): pass
class Mesh(Identity): pass
class Texture(Identity): pass
class Image(Identity): pass
class TextureInfo(Identity): pass
GLTF = NS(Material=Material, Mesh=Mesh, Texture=Texture, Image=Image, TextureInfo=TextureInfo)


class PatchTests(unittest.TestCase):
    def test_foreign_constructor_inventory_refuses_before_calling_it(self):
        module = types.ModuleType('_has_synthetic_foreign_extension')
        calls = []
        module.glTF2ExportUserExtension = lambda: calls.append('foreign constructor')
        sys.modules[module.__name__] = module
        try:
            with self.assertRaises(H.Refusal): H.extension_inventory([module.__name__])
            self.assertEqual(calls, [])
        finally:
            del sys.modules[module.__name__]

    def test_success_restores_exact_original_objects(self):
        original, replacement = object(), object()
        owner, latch = NS(function=original), H.FailureLatch()
        with H.OwnedPatches(latch) as patches:
            patches.replace(owner, 'function', original, replacement)
            self.assertIs(owner.function, replacement)
        self.assertIs(owner.function, original)
        latch.check()

    def test_operator_exception_is_same_object_after_restoration(self):
        original, replacement = object(), object()
        owner, latch, error = NS(function=original), H.FailureLatch(), RuntimeError('synthetic operator')
        with self.assertRaises(RuntimeError) as caught:
            with H.OwnedPatches(latch) as patches:
                patches.replace(owner, 'function', original, replacement)
                raise error
        self.assertIs(caught.exception, error)
        self.assertIs(owner.function, original)

    def test_partial_install_rolls_back_earlier_slot(self):
        first, second, replacement = object(), object(), object()
        owner, latch = NS(first=first, second=second), H.FailureLatch()
        with self.assertRaises(H.Refusal):
            with H.OwnedPatches(latch) as patches:
                patches.replace(owner, 'first', first, replacement)
                patches.replace(owner, 'second', object(), replacement)
        self.assertIs(owner.first, first)
        self.assertIs(owner.second, second)

    def test_foreign_replacement_is_not_clobbered_other_slots_restore(self):
        first, second, replacement, foreign = object(), object(), object(), object()
        owner, latch = NS(first=first, second=second), H.FailureLatch()
        with self.assertRaises(H.Refusal):
            with H.OwnedPatches(latch) as patches:
                patches.replace(owner, 'first', first, replacement)
                patches.replace(owner, 'second', second, replacement)
                owner.second = foreign
        self.assertIs(owner.first, first)
        self.assertIs(owner.second, foreign)
        with self.assertRaises(H.Refusal): latch.check()

    def test_extension_registration_is_single_exact_constructor(self):
        module = types.ModuleType('_has_synthetic_extension')
        collector, latch = object(), H.FailureLatch()
        sys.modules[module.__name__] = module
        try:
            with H.OwnedPatches(latch) as patches:
                patches.register_extension(module, [module.__name__], collector)
                self.assertIs(module.glTF2ExportUserExtension(), collector)
            self.assertFalse(hasattr(module, 'glTF2ExportUserExtension'))
            module.glTF2ExportUserExtensions = []
            with self.assertRaises(H.Refusal):
                with H.OwnedPatches(latch) as patches:
                    patches.register_extension(module, [module.__name__], collector)
        finally:
            del sys.modules[module.__name__]


CACHE_SOURCE = '''import functools
def cached_by_key(key):
    def inner(func):
        @functools.wraps(func)
        def wrapper_cached(*args, **kwargs):
            cache_key = key(*args, **kwargs)
            if not hasattr(func, '__cache'):
                func.__cache = {}
            if cache_key not in func.__cache:
                func.__cache[cache_key] = func(*args, **kwargs)
            return func.__cache[cache_key]
        return wrapper_cached
    return inner
def default_key(*args, **kwargs):
    return args
'''


def module_from_source(name, source, initial=None):
    module = types.ModuleType(name)
    module.__file__ = '<synthetic/' + name + '.py>'
    module.__dict__.update(initial or {})
    exec(compile(source, module.__file__, 'exec', dont_inherit=True), module.__dict__)
    return module


class RuntimeCodeTests(unittest.TestCase):
    def test_decorator_first_line_and_complete_original_code_are_preserved(self):
        cache = module_from_source('synthetic_cache', CACHE_SOURCE)
        source = '@cached_by_key(default_key)\ndef observed(x):\n    return x + 3\n'
        module = module_from_source('synthetic_observed', source, dict(
            cached_by_key=cache.cached_by_key, default_key=cache.default_key))
        actual = H._cached(module, source, 'observed', cache.default_key, cache, CACHE_SOURCE)
        self.assertIs(actual, module.observed)
        self.assertEqual(actual.__wrapped__.__code__.co_firstlineno, 1)

    def test_private_name_mangling_and_dunder_constructor_are_distinct(self):
        source = 'class GlTF2Exporter:\n    def __init__(self):\n        pass\n    def __to_reference(self, value):\n        return value\n'
        module = module_from_source('synthetic_exporter', source)
        target = module.GlTF2Exporter.__dict__['_GlTF2Exporter__to_reference']
        self.assertIs(H._plain(module, source, '__to_reference', 'GlTF2Exporter', target), target)
        constructor = module.GlTF2Exporter.__dict__['__init__']
        self.assertIs(H._plain(module, source, '__init__', 'GlTF2Exporter'), constructor)

    def test_changed_key_identity_and_warm_cache_refuse(self):
        cache = module_from_source('synthetic_cache', CACHE_SOURCE)
        source = '@cached_by_key(default_key)\ndef observed(x):\n    return x + 3\n'
        module = module_from_source('synthetic_observed', source, dict(
            cached_by_key=cache.cached_by_key, default_key=cache.default_key))
        with self.assertRaises(H.Refusal):
            H._cached(module, source, 'observed', lambda x: x, cache, CACHE_SOURCE)
        module.observed(2)
        with self.assertRaises(H.Refusal):
            H._cached(module, source, 'observed', cache.default_key, cache, CACHE_SOURCE)

    def test_changed_runtime_body_and_defaults_refuse(self):
        source = 'def observed(x=2):\n    return x + 3\n'
        module = module_from_source('synthetic_body', source)
        module.observed.__defaults__ = (5,)
        with self.assertRaises(H.Refusal): H._plain(module, source, 'observed')
        module.observed.__defaults__ = (2,)
        altered = module_from_source('synthetic_body', 'def observed(x=2):\n    return x + 4\n')
        module.observed.__code__ = altered.observed.__code__
        with self.assertRaises(H.Refusal): H._plain(module, source, 'observed')


class U32:
    def __init__(self, value): self.value, self.ndim = value, 0
    def item(self): return self.value


class DType:
    def __init__(self, scalar): self.scalar = scalar
    def __eq__(self, other): return type(other) is DType and self.scalar is other.scalar


class Array:
    def __init__(self, values, scalar):
        self.values, self.dtype, self.ndim, self.size = list(values), DType(scalar), 1, len(values)
    def __ge__(self, value): return [x >= value for x in self.values]
    def __lt__(self, value): return [x < value for x in self.values]
    def tolist(self): return list(self.values)


class IntP: pass
NP = NS(ndarray=Array, uint32=U32, intp=IntP, dtype=DType, all=all)


class Ledger:
    def __init__(self, admissions): self.admissions, self.events = admissions, []
    def observe_creator(self, *args): self.events.append(('creator', args))
    def bind_gather(self, *args): self.events.append(('bind', args))
    def record_material_reference(self, *args): self.events.append(('material', args))
    def record_mesh_reference(self, *args): self.events.append(('mesh', args))


class EmptyResources:
    def __init__(self): self.bound = None
    def check_unchanged(self): pass
    def bind_primitive_materials(self, *args): self.bound = args


def fake_session():
    mesh, obj, source_material = object(), object(), object()
    groups, modifiers = object(), object()
    materials = (source_material,)
    gltf_material = Material()
    primitives, image_module = NS(), NS()
    class PrimitiveCreator:
        def primitive_creation_shared(self): raise AssertionError('shared branch not expected')
        def primitive_creation_not_shared(self):
            return [dict(material=U32(0), attributes={'POSITION': object()}, indices=object())]
    def original_cache(mats, data, uuid, vertex_groups, mods, settings):
        creator = PrimitiveCreator()
        creator.blender_object, creator.blender_mesh = obj, mesh
        return creator.primitive_creation_not_shared(), [None]
    def original_gather(data, uuid, vertex_groups, mods, mats, settings):
        internal, _ = primitives.__gather_cache_primitives(mats, data, uuid, vertex_groups, mods, settings)
        return [Identity(attributes=row['attributes'], indices=row['indices'], material=gltf_material)
                for row in internal]
    class GlTF2Exporter:
        def __to_reference(self, value): return 0
    def original_image_data(*args): raise AssertionError('image not expected')
    primitives.gather_primitives, primitives.__gather_cache_primitives = original_gather, original_cache
    image_module.__get_image_data = original_image_data
    surface = NS(modules=dict(primitives=primitives, extractor=NS(PrimitiveCreator=PrimitiveCreator, np=NP), utils=NS(np=NP),
                               exporter=NS(GlTF2Exporter=GlTF2Exporter), image=image_module, gltf=GLTF),
                 gather=original_gather, cache=original_cache,
                 reference=GlTF2Exporter.__dict__['_GlTF2Exporter__to_reference'], image_data=original_image_data,
                 binder_module=NS(GatherBinding=Ledger))
    def observed_methods(callback):
        def observed(creator):
            callback(creator, 'not_shared', Array([0, 1, 2], U32), U32(0), Array([0, 1, 2], IntP), 0)
            return original(creator)
        original = PrimitiveCreator.primitive_creation_not_shared
        return [(PrimitiveCreator, 'primitive_creation_not_shared', original, observed)], {'synthetic_only': True}
    surface.observed_methods = observed_methods
    admission = dict(object=obj, mesh=mesh, joined_source_ids=[0, 1, 2],
                     material_slots=materials, primitive_count=1)
    options = dict(gltf_format='GLB', gltf_shared_accessors=False, gltf_attributes=True,
                   gltf_materials='EXPORT', gltf_keep_original_textures=False,
                   gltf_draco_mesh_compression=False, gltf_image_format='AUTO',
                   gltf_unused_textures=False, gltf_unused_images=False,
                   gltf_add_webp=False, gltf_webp_fallback=False,
                   gltf_current_frame=True, gltf_animations=False)
    resources = EmptyResources()
    session = H.ExportHookSession(surface, [admission], NP, resources, lambda: None, options)
    settings = dict(options, gltf_user_extensions=[session], pre_export_callbacks=[], post_export_callbacks=[],
                    vtree=NS(nodes={'object-uuid': NS(blender_object=obj)}))
    extension = types.ModuleType('_has_synthetic_session_extension')
    return NS(session=session, surface=surface, settings=settings, extension=extension,
              args=(mesh, 'object-uuid', groups, modifiers, materials, settings), obj=obj, resources=resources)


class CallChainTests(unittest.TestCase):
    def setUp(self):
        self.case = fake_session()
        sys.modules[self.case.extension.__name__] = self.case.extension
    def tearDown(self):
        del sys.modules[self.case.extension.__name__]
    def installed(self):
        c = self.case
        return c.session.install(c.extension, [c.extension.__name__])
    def gather(self):
        c = self.case
        result = c.surface.modules['primitives'].gather_primitives(*c.args)
        c.session.gather_mesh_hook(Mesh(primitives=result), c.args[0], c.obj,
                                   c.args[2], c.args[3], c.args[4], c.settings)
        return result

    def test_one_cold_call_binds_actual_return_lists_and_restores(self):
        c = self.case
        with self.installed():
            c.session.pre_export_hook(c.settings)
            result = self.gather()
            binding = [args for event, args in c.session.binder.events if event == 'bind'][0]
            self.assertIs(binding[3], result)
            self.assertIs(binding[2], c.resources.bound[1])
        self.assertIs(c.surface.modules['primitives'].gather_primitives, c.surface.gather)
        self.assertFalse(hasattr(c.extension, 'glTF2ExportUserExtension'))
        self.assertEqual(c.session.preflights, 1)

    def test_swallowed_extension_failure_remains_latched_after_operator(self):
        c = self.case
        with self.assertRaises(H.Refusal):
            with self.installed():
                c.session.pre_export_hook(c.settings)
                result = c.surface.modules['primitives'].gather_primitives(*c.args)
                try:
                    c.session.gather_mesh_hook(Mesh(primitives=result), c.args[0], object(),
                                               c.args[2], c.args[3], c.args[4], c.settings)
                except Exception:
                    pass  # Deliberately mimic actual exporter dispatcher.
        self.assertIsNotNone(c.session.latch.first)

    def test_cache_hit_without_creator_refuses(self):
        c = self.case
        c.surface.cache = lambda *args: ([], [])
        setattr(c.surface.modules['primitives'], '__gather_cache_primitives', c.surface.cache)
        with self.assertRaises(H.Refusal):
            with self.installed():
                c.session.pre_export_hook(c.settings)
                self.gather()

    def test_repeated_object_gather_refuses(self):
        c = self.case
        with self.assertRaises(H.Refusal):
            with self.installed():
                c.session.pre_export_hook(c.settings)
                self.gather()
                self.gather()

    def test_equal_but_distinct_settings_refuse(self):
        c = self.case
        with self.assertRaises(H.Refusal):
            with self.installed():
                c.session.pre_export_hook(c.settings)
                args = c.args[:-1] + (dict(c.settings),)
                c.surface.modules['primitives'].gather_primitives(*args)

    def test_boolean_option_is_not_integer_equivalent(self):
        c = self.case
        c.settings['gltf_attributes'] = 1
        with self.assertRaises(H.Refusal):
            with self.installed():
                c.session.pre_export_hook(c.settings)

    def test_real_original_exception_calls_once_and_is_preserved(self):
        c, calls, error = self.case, [], RuntimeError('actual original failure')
        def failed(*args):
            calls.append(1)
            raise error
        c.surface.gather = failed
        c.surface.modules['primitives'].gather_primitives = failed
        with self.assertRaises(RuntimeError) as caught:
            with self.installed():
                c.session.pre_export_hook(c.settings)
                self.gather()
        self.assertIs(caught.exception, error)
        self.assertEqual(calls, [1])

    def test_signed_intp_inverse_is_admitted_without_coercing_float_or_bool(self):
        c = self.case
        creator = NS(blender_object=c.obj, blender_mesh=c.args[0])
        frame = dict(entry=c.session.admissions[0], materials=c.args[4], creator=None)
        c.session.active = frame
        c.session.observe_creator(creator, 'not_shared', Array([0, 1, 2], U32), U32(0), Array([0, 1, 2], IntP), 0)
        self.assertEqual(c.session.binder.events[0][1][4], [0, 1, 2])
        for slot, topology in ((True, Array([0, 1, 2], IntP)), (U32(0), Array([0, 1, 2], float)),
                               (U32(0), Array([-1, 1, 2], IntP))):
            c.session.latch = H.FailureLatch()
            with self.assertRaises(H.Refusal):
                c.session.observe_creator(creator, 'not_shared', Array([0, 1, 2], U32), slot, topology, 1)


class Socket(Identity): pass
class OutputNode(Identity): pass
class PrincipledNode(Identity): pass
class ImageNode(Identity): pass
class Link(Identity): pass
class PackedFile(Identity): pass
class ImagePackedFile(Identity):
    @property
    def packed_file(self):
        value = self.__dict__['packed_file']
        return fresh_rna(value) if self.__dict__.get('_fresh_wrappers') else value
class NodeSocket:
    def __init__(self, socket, group_path): self.socket, self.group_path = socket, group_path
class ExportImage:
    def __init__(self): self.fills, self.stored, self.original, self.numpy_calc = {}, {}, None, None
class FillImage:
    def __init__(self, image, src_chan): self.image, self.src_chan = image, src_chan
class FillWhite: pass
class Channel(int): pass
ENCODE = NS(ExportImage=ExportImage, FillImage=FillImage, FillWhite=FillWhite, Channel=Channel)


class Sockets:
    def __init__(self, node, names, output=False):
        self.values = [Socket(node=node, default_value=None, identifier=name, is_output=output) for name in names]
        self.named = dict(zip(names, self.values))
    def __iter__(self): return iter(self.values)
    def __getitem__(self, key): return self.named[key]


def rna_types():
    return NS(ID=Identity, Image=Identity, NodeTree=Identity, NodeSocket=Socket, NodeLink=Link,
              PackedFile=PackedFile, ImagePackedFile=ImagePackedFile,
              ShaderNodeOutputMaterial=OutputNode, ShaderNodeBsdfPrincipled=PrincipledNode, ShaderNodeTexImage=ImageNode,
              OutputNode=OutputNode, PrincipledNode=PrincipledNode, ImageNode=ImageNode, Socket=Socket, Link=Link)


def adopt_image_owner(image):
    image.original = image
    image.packed_file.id_data = image
    for part in image.packed_files:
        part.id_data = image
        part.packed_file.id_data = image
    return image


def fresh_rna(value):
    result = type(value).__new__(type(value))
    result.__dict__ = value.__dict__
    return result


class FreshSequence:
    def __init__(self, values): self.values = values
    def __iter__(self): return (fresh_rna(value) for value in self.values)


class FreshSockets:
    def __init__(self, value): self.values, self.named = value.values, value.named
    def __iter__(self): return (fresh_rna(value) for value in self.values)
    def __getitem__(self, key): return fresh_rna(self.named[key])


class FreshImage(Identity):
    @property
    def packed_file(self): return fresh_rna(self.__dict__['packed_file'])
    @property
    def packed_files(self): return [fresh_rna(part) for part in self.__dict__['packed_files']]


def png_header(width, height):
    # Valid bounded IHDR/CRC, deliberately synthetic non-image remainder. No
    # decoder is used, and these packets cannot qualify a real encoded image.
    chunk = b'IHDR' + struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    return PNG_MAGIC + struct.pack('>I', 13) + chunk + struct.pack('>I', zlib.crc32(chunk)) + b'synthetic-only'


def graph_fixture():
    raw = png_header(32, 32)
    packed = PackedFile(size=len(raw), data=raw)
    part = ImagePackedFile(packed_file=packed, filepath='', view=0, tile_number=1001)
    image = adopt_image_owner(Identity(name='source-png', filepath='', filepath_raw='', library=None,
                     source='FILE', type='IMAGE', is_dirty=False, has_data=True, animation_data=None,
                     alpha_mode='STRAIGHT', colorspace_settings=NS(name='sRGB'), size=(32, 32), channels=4,
                     packed_files=[part], packed_file=packed))
    shader, output, tex = PrincipledNode(mute=False), OutputNode(mute=False, is_active_output=True, target='ALL'), ImageNode(
        mute=False, image=image, interpolation='Linear', extension='REPEAT', projection='FLAT')
    shader.inputs, shader.outputs = Sockets(shader, ['Base Color', 'Alpha', 'Roughness']), Sockets(shader, ['BSDF'], True)
    output.inputs, output.outputs = Sockets(output, ['Surface', 'Volume', 'Displacement']), Sockets(output, [], True)
    tex.inputs, tex.outputs = Sockets(tex, ['Vector']), Sockets(tex, ['Color', 'Alpha'], True)
    tree = Identity(library=None, animation_data=None, nodes=[shader, output, tex], links=[])
    tree.original = tree
    for node in tree.nodes:
        node.id_data = tree
        for socket in tuple(node.inputs) + tuple(node.outputs): socket.id_data = tree
    def link(start, end):
        return Link(id_data=start.id_data, from_node=start.node, from_socket=start, to_node=end.node, to_socket=end, is_valid=True)
    tree.links = [
        link(shader.outputs['BSDF'], output.inputs['Surface']),
        link(tex.outputs['Color'], shader.inputs['Base Color']), link(tex.outputs['Alpha'], shader.inputs['Alpha'])]
    material = Identity(library=None, use_nodes=True, node_tree=tree, animation_data=None, use_backface_culling=False)
    material.original = material
    tickets = [dict(image=image, packed_sha256=hashlib.sha256(raw).hexdigest(), encoded_bytes=len(raw))]
    types_ = rna_types()
    def gate(): return SimplePackedResources((material,), tickets, types_, NS(NodeSocket=NodeSocket), ENCODE, GLTF)
    sockets = (NodeSocket(shader.inputs['Base Color'], [tree]), NodeSocket(shader.inputs['Alpha'], [tree]))
    descriptor = ExportImage()
    descriptor.fills = {channel: FillImage(image, channel) for channel in range(4)}
    return NS(gate=gate, material=material, tickets=tickets, image=image, shader=shader, tex=tex,
              tree=tree, sockets=sockets, descriptor=descriptor, link=link)


class ResourceTests(unittest.TestCase):
    def test_fresh_node_socket_link_and_packed_wrappers_preserve_same_actual_keys(self):
        c = graph_fixture()
        image = adopt_image_owner(FreshImage(**c.image.__dict__))
        image.__dict__['packed_files'][0]._fresh_wrappers = True
        c.tex.image = image
        c.tickets[0]['image'] = image
        for node in c.tree.nodes:
            node.inputs, node.outputs = FreshSockets(node.inputs), FreshSockets(node.outputs)
        c.tree.nodes, c.tree.links = FreshSequence(c.tree.nodes), FreshSequence(c.tree.links)
        self.assertIsNot(tuple(c.tree.nodes)[0], tuple(c.tree.nodes)[0])
        self.assertIsNot(c.shader.inputs['Base Color'], c.shader.inputs['Base Color'])
        self.assertIsNot(image.packed_file, image.packed_file)
        self.assertIsNot(image.packed_files[0], image.packed_files[0])
        gate = c.gate()
        gate.check_unchanged()
        wrappers = tuple(NodeSocket(fresh_rna(value.socket), list(value.group_path)) for value in c.sockets)
        gate.before_image_data(wrappers, None)

    def test_same_pointer_wrong_owner_refuses_socket_and_packed_alias(self):
        c = graph_fixture(); gate = c.gate()
        foreign = Identity(library=None); foreign.original = foreign
        socket = Socket(**c.sockets[0].socket.__dict__)
        socket.id_data = foreign
        with self.assertRaises(H.Refusal): gate.before_image_data((NodeSocket(socket, [c.tree]),), None)
        c = graph_fixture(); gate = c.gate()
        c.image.packed_file.id_data = foreign
        with self.assertRaises(H.Refusal): gate.check_unchanged()

    def test_same_pointer_different_registered_concrete_socket_type_refuses(self):
        c = graph_fixture(); gate = c.gate()
        class OtherSocket(Socket): pass
        gate.types.OtherSocket = OtherSocket
        old = c.shader.inputs['Base Color']
        other = OtherSocket(**old.__dict__)
        c.shader.inputs.named['Base Color'] = other
        c.shader.inputs.values[0] = other
        with self.assertRaises(H.Refusal): gate.check_unchanged()

    def test_missing_registry_class_and_bool_zero_out_of_range_pointers_refuse(self):
        c = graph_fixture()
        types_ = rna_types(); del types_.Socket
        with self.assertRaises(H.Refusal):
            SimplePackedResources((c.material,), c.tickets, types_, NS(NodeSocket=NodeSocket), ENCODE, GLTF)
        for pointer in (True, False, 0, -1, 2**64, '123'):
            c = graph_fixture(); c.shader._rna_pointer = pointer
            with self.assertRaises(H.Refusal): c.gate()

    def test_changed_pointer_foreign_socket_and_duplicate_membership_refuse(self):
        c = graph_fixture(); gate = c.gate()
        c.shader.inputs['Base Color']._rna_pointer += 100000
        with self.assertRaises(H.Refusal): gate.check_unchanged()
        c = graph_fixture(); gate = c.gate()
        foreign = Socket(**c.sockets[0].socket.__dict__)
        foreign.node = c.tex
        with self.assertRaises(H.Refusal): gate.before_image_data((NodeSocket(foreign, [c.tree]),), None)
        c = graph_fixture()
        c.shader.inputs.values.append(fresh_rna(c.shader.inputs.values[0]))
        with self.assertRaises(H.Refusal): c.gate()

    def test_fresh_alias_payload_drift_or_pointer_change_refuses(self):
        c = graph_fixture(); gate = c.gate()
        original = c.image.packed_file
        changed = PackedFile(**original.__dict__)
        changed.data = changed.data[:-1] + b'!'
        c.image.packed_files[0].__dict__['packed_file'] = changed
        with self.assertRaises(H.Refusal): gate.check_unchanged()
        c = graph_fixture(); gate = c.gate()
        c.image.packed_files[0]._rna_pointer += 100000
        with self.assertRaises(H.Refusal): gate.check_unchanged()

    def test_link_endpoint_and_socket_identifier_direction_defaults_drift_refuse(self):
        c = graph_fixture(); gate = c.gate()
        c.tree.links[1].to_socket = c.shader.inputs['Alpha']
        with self.assertRaises(H.Refusal): gate.check_unchanged()
        for field, value in (('identifier', 'different'), ('is_output', True), ('default_value', .125)):
            c = graph_fixture(); gate = c.gate()
            setattr(c.shader.inputs['Base Color'], field, value)
            with self.assertRaises(H.Refusal): gate.check_unchanged()

    def test_ID_and_plain_descriptor_lookalikes_remain_strict_reference_failures(self):
        c = graph_fixture(); gate = c.gate()
        foreign_tree = Identity(**c.tree.__dict__); foreign_tree.original = foreign_tree
        c.material.node_tree = foreign_tree
        with self.assertRaises(H.Refusal): gate.check_unchanged()
        c = graph_fixture(); gate = c.gate()
        gate.after_image_data(c.sockets, (c.descriptor, None))
        lookalike = ExportImage(); lookalike.fills = dict(c.descriptor.fills)
        image = Image(mime_type='image/png', uri=None, buffer_view=object(), extensions={}, extras=None)
        with self.assertRaises(H.Refusal): gate.image(image, lookalike, c.sockets)
    def test_exporter_read_backface_culling_change_is_detected(self):
        c = graph_fixture()
        gate = c.gate()
        c.material.use_backface_culling = True
        with self.assertRaises(H.Refusal): gate.check_unchanged()

    def test_source_image_shared_across_materials_refuses_in_preflight(self):
        first, second = graph_fixture(), graph_fixture()
        second.tex.image = first.image
        types_ = rna_types()
        with self.assertRaises(H.Refusal):
            SimplePackedResources((first.material, second.material), first.tickets, types_,
                                  NS(NodeSocket=NodeSocket), ENCODE, GLTF)

    def test_large_png_header_refuses_before_image_size_getter(self):
        c = graph_fixture()
        class GuardedImage(Identity):
            @property
            def size(self):
                self.size_reads += 1
                return self.__dict__['size']
        image = adopt_image_owner(GuardedImage(**c.image.__dict__, size_reads=0))
        c.tex.image = image
        c.tickets[0]['image'] = image
        raw = png_header(16384, 16384)
        image.packed_file.data, image.packed_file.size = raw, len(raw)
        c.tickets[0]['encoded_bytes'], c.tickets[0]['packed_sha256'] = len(raw), hashlib.sha256(raw).hexdigest()
        with self.assertRaises(H.Refusal): c.gate()
        self.assertEqual(image.size_reads, 0)
        # Three individually admitted 64-MiB prospective buffers exceed the
        # aggregate cap. All headers must be checked before even the first getter.
        cases, images = [graph_fixture() for _ in range(3)], []
        for ordinal, case in enumerate(cases):
            guarded = adopt_image_owner(GuardedImage(**case.image.__dict__, size_reads=0))
            guarded.name = 'source-' + str(ordinal)
            case.tex.image, case.tickets[0]['image'] = guarded, guarded
            raw = png_header(2048, 2048)
            guarded.packed_file.data, guarded.packed_file.size = raw, len(raw)
            case.tickets[0]['encoded_bytes'] = len(raw)
            case.tickets[0]['packed_sha256'] = hashlib.sha256(raw).hexdigest()
            images.append(guarded)
        types_ = rna_types()
        with self.assertRaises(H.Refusal):
            SimplePackedResources(tuple(case.material for case in cases), [row for case in cases for row in case.tickets],
                                  types_, NS(NodeSocket=NodeSocket), ENCODE, GLTF)
        self.assertEqual([image.size_reads for image in images], [0, 0, 0])

    def test_exact_source_refs_and_complete_mapping_survive_distinct_socket_wrappers(self):
        c, gate = graph_fixture(), None
        gate = c.gate()
        gate.before_image_data(c.sockets, None)
        gate.after_image_data(c.sockets, (c.descriptor, None))
        repeated = tuple(NodeSocket(wrapper.socket, list(wrapper.group_path)) for wrapper in c.sockets)
        image = Image(mime_type='image/png', uri=None, buffer_view=object(), extensions={}, extras=None)
        gate.image(image, c.descriptor, repeated)
        self.assertIs(gate.images[0]['image'], image)
        self.assertIs(gate.images[0]['key'][0][1], c.image)

    def test_same_valued_foreign_image_cannot_supply_descriptor(self):
        c = graph_fixture()
        gate = c.gate()
        c.descriptor.fills[1] = FillImage(Identity(**c.image.__dict__), 1)
        with self.assertRaises(H.Refusal): gate.after_image_data(c.sockets, (c.descriptor, None))

    def test_unsupported_orm_link_refuses_before_gather(self):
        c = graph_fixture()
        c.tree.links.append(c.link(c.tex.outputs['Color'], c.shader.inputs['Roughness']))
        with self.assertRaises(H.Refusal): c.gate()

    def test_foreign_group_context_and_reversed_alpha_order_refuse(self):
        c = graph_fixture()
        gate = c.gate()
        with self.assertRaises(H.Refusal): gate.before_image_data((NodeSocket(c.sockets[0].socket, [object()]),), None)
        with self.assertRaises(H.Refusal): gate.before_image_data(tuple(reversed(c.sockets)), None)

    def test_udim_stored_computation_and_rgb_to_bw_fill_refuse(self):
        c = graph_fixture()
        gate = c.gate()
        with self.assertRaises(H.Refusal): gate.before_image_data(c.sockets, True)
        c.descriptor.numpy_calc = lambda: None
        with self.assertRaises(H.Refusal): gate.after_image_data(c.sockets, (c.descriptor, None))
        c.descriptor.numpy_calc = None
        c.descriptor.fills[3] = object()
        with self.assertRaises(H.Refusal): gate.after_image_data(c.sockets, (c.descriptor, None))

    def test_alpha_only_refuses_before_unhappy_pixel_encoding(self):
        c = graph_fixture()
        gate = c.gate()
        with self.assertRaises(H.Refusal): gate.before_image_data((c.sockets[1],), None)

    def test_packed_png_with_jpeg_or_webp_raw_name_refuses_before_encoding(self):
        for path in ('source.jpg', 'source.jpeg', 'source.webp'):
            c = graph_fixture()
            c.image.filepath_raw = path
            with self.assertRaises(H.Refusal): c.gate()

    def test_packed_data_mutation_and_missing_hooks_refuse(self):
        c = graph_fixture()
        gate = c.gate()
        with self.assertRaises(H.Refusal): gate.finalize({})
        c.image.packed_file.data = c.image.packed_file.data[:-1] + b'!'
        with self.assertRaises(H.Refusal): gate.check_unchanged()

    def test_final_material_copy_and_resource_index_alias_refuse(self):
        c = graph_fixture()
        gate = c.gate()
        gate.after_image_data(c.sockets, (c.descriptor, None))
        image = Image(mime_type='image/png', uri=None, buffer_view=object(), extensions={}, extras=None)
        gate.image(image, c.descriptor, c.sockets)
        texture = Texture(source=image, extensions={}, extras=None)
        gate.texture(texture, c.sockets)
        info = TextureInfo(index=texture, tex_coord=None, extensions={}, extras=None)
        gate.texture_info(info, c.sockets)
        material = Material(extensions={}, extras=None, normal_texture=None, occlusion_texture=None,
                            emissive_texture=None, pbr_metallic_roughness=Identity(
                                metallic_roughness_texture=None, base_color_texture=info))
        gate.material(material, c.material)
        with self.assertRaises(H.Refusal):
            gate.bind_primitive_materials((c.material,), [dict(material=0)], [Identity(material=Material())])
        gate.bind_primitive_materials((c.material,), [dict(material=0)], [Identity(material=material)])
        gate.reference('image', image, 0)
        texture.source = 0
        gate.reference('texture', texture, 0)
        info.index = 0
        gate.reference('material', material, 0)
        report = gate.finalize(dict(images=[{}], textures=[dict(source=0)], materials=[dict(
            pbrMetallicRoughness=dict(baseColorTexture=dict(index=0)))]))
        self.assertFalse(report['full_semantic_equivalence'])
        foreign = Image(mime_type='image/png', uri=None, buffer_view=object(), extensions={}, extras=None)
        gate.images.append(dict(image=foreign, key=gate.images[0]['key']))
        with self.assertRaises(H.Refusal): gate.reference('image', foreign, 0)


if __name__ == '__main__':
    unittest.main()
