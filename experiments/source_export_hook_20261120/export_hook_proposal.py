"""UNRUN, experiment-only actual-export observation proposal.

Importing this module imports no Blender, NumPy, project code or native data and
does no IO.  It does not launch/export/save anything.  A future admitted host must
load the pinned modules and prove the independent current point admission before
constructing a session.  Synthetic use cannot qualify any native identity.
"""
import ast
import copy
import functools
import hashlib
import os
import sys
import types
from contextlib import contextmanager
from pathlib import Path

SOURCE_NORMAL_MAX_ERROR = 2e-5  # Existing independent gate; never applied/relaxed here.
EXPORTER_ROOT = Path(r'C:\Program Files\Blender Foundation\Blender 5.1\5.1\scripts\addons_core\io_scene_gltf2')
PINS = {
    'addon': ('__init__.py', 'dddd7d2362b937f34a5d4a1978259317720a9bc647bb3b4dc113f9d5c38cbf56'),
    'extractor': ('blender/exp/primitive_extract.py', '455a3566d833481b230141b457452b5bf4ff4a1661d4dd6765a568488e0a2769'),
    'primitives': ('blender/exp/primitives.py', '7d7f2c6d9c5e64974f05ee40967d4415a00ee9b4ed91447889cee44d185c68a4'),
    'obj_data': ('blender/exp/obj_data.py', '1d0e3942a5c65dacbba2b51fb89688026a36c3fc81f89da683c9e2eb393203a8'),
    'nodes': ('blender/exp/nodes.py', '6c77f1ec3f13bd4636ca72f766429abc9cd4353ff218fdb088db1e41f184b7c3'),
    'exporter': ('blender/exp/exporter.py', '49c1e0174a65efd6d411b906cd154b6b04502c4840c9b31a7bfac87e0888f242'),
    'cache': ('blender/exp/cache.py', '12fc08e6403c9dd604f6884fdfdcf787ed5a898a2c6f4e2990f1826d6e265d98'),
    'export': ('blender/exp/export.py', 'd6ae39bf861fc3db7662bc8e7063aadfbe116b8a5de81b40ba027a679f8435a8'),
    'gltf': ('io/com/gltf2_io.py', 'd0bad0c89e40c0975ed9e435656151e353240134011f69602e473e0a5f1592f4'),
    'user_extensions': ('io/exp/user_extensions.py', '25d27cebbfce855dd5ac34928582ac5ab7f0e84d9a1d1862492ba3b82f523186'),
    'materials': ('blender/exp/material/materials.py', 'e9660b8325208928317df15c05ed980c04f275a8afad01e1195a1a3f1859c5f6'),
    'texture_info': ('blender/exp/material/texture_info.py', '962d784eefcd81e1f5bfe7cc7f96bb19b2b7725dfa4a00250ecf87db551d144a'),
    'texture': ('blender/exp/material/texture.py', '9abd202b09a224c2cfe14a1ff596be362e1d7e19e11ce71bad68cd56092a0e20'),
    'image': ('blender/exp/material/image.py', 'fc1ce104f15d6168ee959742e2313f668aeb0e8526cf0b4122e796a1a241c509'),
    'encode': ('blender/exp/material/encode_image.py', '1f59e5a2a3116c21afab6c2baf49f9ea1b4c9d663b268d69ec5123d2bf011de1'),
    'search': ('blender/exp/material/search_node_tree.py', '2bafe2b2d24bf6d8087c22a6d3a5fddc9f39eb537a2f052e99c1d9dc92136c59'),
    'utils': ('blender/com/gltf2_blender_utils.py', '7ce3f41dd813e231e810659ed2ce701524b795e8768f16b9e3a2d1601d219eff'),
}
OBSERVER_SHA256 = '15145030fab5b662be490e519ff59f870c4e9c0352766ff59bf3da3f12198f7b'
BINDER_SHA256 = '617c062b516ecefa5fab0a6ec8f98163a3b13f76896969cb22102f859323b850'
NUMPY_UNIQUE_SHA256 = 'd112be99ab44d57b78642fe4606f8b040022549022d319bcea66a89c1fba5ee6'


class Refusal(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise Refusal(code)


def same_refs(left, right):
    return len(left) == len(right) and all(a is b for a, b in zip(left, right))


def extension_inventory(enabled_names, owned_module=None, owned_constructor=None):
    """Pre-operator check: foreign constructors must NEVER be called first.

    The host must supply the authentic bpy preferences enabled-addon names and
    freeze that collection. Exporter construction precedes pre_export_hook, so a
    late sole-collector assertion alone cannot safely establish this inventory.
    """
    need(type(enabled_names) in (list, tuple) and len(enabled_names) <= 256 and
         all(type(name) is str for name in enabled_names) and len(set(enabled_names)) == len(enabled_names),
         'bounded_authentic_enabled_addon_inventory_required')
    rows = []
    fields = ('glTF2ExportUserExtension', 'glTF2ExportUserExtensions',
              'glTF2_pre_export_callback', 'glTF2_post_export_callback')
    for name in enabled_names:
        module = sys.modules.get(name)
        if module is None:
            rows.append((name, None))  # Same skip used by the pinned exporter.
            continue
        need(type(module) is types.ModuleType and '__getattr__' not in vars(module),
             'dynamic_or_nonstandard_enabled_addon_module')
        namespace = vars(module)
        for field in fields:
            if field in namespace:
                need(module is owned_module and field == 'glTF2ExportUserExtension' and
                     namespace[field] is owned_constructor and owned_constructor is not None,
                     'foreign_export_constructor_or_callback_before_operator')
        rows.append((name, module))
    return tuple(rows)


class FailureLatch:
    """Keep failure even when the exporter's extension dispatcher swallows it."""
    def __init__(self):
        self.first = None
        self.count = 0

    def capture(self, code, error):
        self.count += 1
        if self.first is None:
            # Store no exception strings, arrays, paths or private object reprs.
            self.first = (code, type(error).__name__)

    def check(self):
        need(self.first is None, 'latched_extension_or_wrapper_failure')


class OwnedPatches:
    """Transactional exact-object patches; restore owned slots even on failure.

    If a foreign writer replaces a slot, never overwrite it.  That slot's exact
    restoration is then impossible and is a hard refusal, while other owned slots
    are still restored.  The real operator exception stays the primary exception.
    """
    def __init__(self, latch):
        self.latch = latch
        self.rows = []

    def replace(self, owner, name, expected, replacement):
        need(all(o is not owner or n != name for o, n, _, _ in self.rows), 'duplicate_patch_slot')
        need(getattr(owner, name) is expected, 'function_identity_changed_before_install')
        setattr(owner, name, replacement)
        self.rows.append((owner, name, expected, replacement))
        need(getattr(owner, name) is replacement, 'patch_installation_failed')

    def register_extension(self, module, enabled_names, collector):
        need(isinstance(module, types.ModuleType) and sys.modules.get(module.__name__) is module,
             'extension_module_not_actual_registered_module')
        need(module.__name__ in enabled_names, 'extension_module_not_enabled')
        need(not any(hasattr(module, name) for name in (
            'glTF2ExportUserExtension', 'glTF2ExportUserExtensions',
            'glTF2_pre_export_callback', 'glTF2_post_export_callback')),
            'existing_extension_or_callback_registration')
        constructor = lambda: collector
        # None denotes absence, not a previously present None-valued attribute.
        setattr(module, 'glTF2ExportUserExtension', constructor)
        self.rows.append((module, 'glTF2ExportUserExtension', None, constructor))
        need(module.glTF2ExportUserExtension is constructor, 'extension_registration_failed')

    def __enter__(self):
        return self

    def __exit__(self, error_type, error, traceback):
        failures = 0
        for owner, name, original, replacement in reversed(self.rows):
            try:
                need(getattr(owner, name, None) is replacement, 'patch_ownership_lost')
                if original is None:
                    delattr(owner, name)
                    need(not hasattr(owner, name), 'extension_not_removed')
                else:
                    setattr(owner, name, original)
                    need(getattr(owner, name) is original, 'function_not_restored_exactly')
            except Exception as restore_error:
                failures += 1
                self.latch.capture('restore_ownership_or_identity', restore_error)
        if failures and error is not None:
            if hasattr(error, 'add_note'):
                error.add_note('Owned exporter instrumentation restoration failed; latched refusal.')
        elif failures:
            raise Refusal('owned_instrumentation_not_restored')
        return False


def _source(module, path, expected_hash):
    need(isinstance(module, types.ModuleType), 'actual_loaded_module_required')
    need(os.path.normcase(os.path.realpath(module.__file__)) ==
         os.path.normcase(os.path.realpath(path)), 'loaded_module_path_differs')
    raw = Path(path).read_bytes()  # Exporter/helper source only, never native inputs.
    need(len(raw) <= 200_000 and hashlib.sha256(raw).hexdigest() == expected_hash,
         'pinned_source_differs')
    need(sys.modules.get(module.__name__) is module, 'loaded_module_registration_differs')
    return raw.decode('utf-8')


def _definition(source, name, owner=None):
    nodes = ast.parse(source).body
    if owner is not None:
        classes = [x for x in nodes if isinstance(x, ast.ClassDef) and x.name == owner]
        need(len(classes) == 1, 'class_definition_not_unique')
        nodes = classes[0].body
    found = [x for x in nodes if isinstance(x, ast.FunctionDef) and x.name == name]
    need(len(found) == 1, 'function_definition_not_unique')
    node = copy.deepcopy(found[0])
    # CPython uses the FIRST decorator line as co_firstlineno, even for the
    # original wrapped function body. Removing decorators without preserving it
    # falsely rejects the genuine @cached function's complete code object.
    if node.decorator_list:
        node.lineno = min(item.lineno for item in node.decorator_list)
    node.decorator_list = []
    if owner is not None:
        # Preserve mangling and line numbers by compiling a same-named class.
        node = ast.ClassDef(name=owner, bases=[], keywords=[], body=[node], decorator_list=[], type_params=[])
    tree = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    return tree


def _plain(module, source, name, owner=None, runtime=None):
    target = runtime if runtime is not None else (
        module.__dict__[name] if owner is None else module.__dict__[owner].__dict__[name])
    need(type(target) is types.FunctionType and not target.__code__.co_freevars,
         'original_not_plain_closed_function')
    need(target.__globals__ is module.__dict__ and target.__code__.co_filename == module.__file__,
         'runtime_function_globals_or_filename_differs')
    namespace = dict(module.__dict__)
    exec(compile(_definition(source, name, owner), module.__file__, 'exec', dont_inherit=True), namespace)
    is_private = name.startswith('__') and not name.endswith('__')
    compiled_name = '_' + owner.lstrip('_') + name if owner is not None and is_private else name
    compiled = namespace[name] if owner is None else namespace[owner].__dict__[compiled_name]
    need(target.__code__ == compiled.__code__, 'runtime_bytecode_differs_from_pinned_source')
    need(target.__defaults__ == compiled.__defaults__ and target.__kwdefaults__ == compiled.__kwdefaults__,
         'runtime_function_defaults_differ')
    return target


def _nested_codes(code):
    for value in code.co_consts:
        if type(value) is types.CodeType:
            yield value
            yield from _nested_codes(value)


def _cached(module, source, name, key, cache_module, cache_source):
    wrapper = module.__dict__[name]
    need(type(wrapper) is types.FunctionType and hasattr(wrapper, '__wrapped__'), 'actual_cached_function_required')
    need(wrapper.__globals__ is cache_module.__dict__ and
         wrapper.__code__.co_filename == cache_module.__file__, 'cache_wrapper_module_differs')
    candidates = [x for x in _nested_codes(compile(cache_source, cache_module.__file__, 'exec', dont_inherit=True))
                  if x.co_name == 'wrapper_cached']
    need(len(candidates) == 1 and wrapper.__code__ == candidates[0], 'cached_wrapper_bytecode_differs')
    need(wrapper.__code__.co_freevars == ('func', 'key') and len(wrapper.__closure__) == 2,
         'cached_wrapper_closure_shape_differs')
    func, actual_key = (cell.cell_contents for cell in wrapper.__closure__)
    need(wrapper.__wrapped__ is func and actual_key is key, 'cached_function_or_key_identity_differs')
    _plain(module, source, name, runtime=func)
    # A cold host must refuse rather than clear or manufacture a cache miss.
    need(not hasattr(func, '__cache') and not hasattr(func, '__export_settings'), 'warm_export_cache_refused')
    return wrapper


class PinnedSurface:
    """Validate source and runtime identities used by this narrow proposal.

    This is NOT the complete Blender/SourceIO/runtime catalogue admission.  The
    future host must qualify its complete runtime, options, scene and input pins.
    """
    def __init__(self, modules, observer_module, binder_module):
        need(type(modules) is dict and set(modules) == set(PINS), 'exact_module_catalogue_required')
        self.modules = dict(modules)
        self.sources = {key: _source(modules[key], EXPORTER_ROOT / path, digest)
                        for key, (path, digest) in PINS.items()}
        self.observer = observer_module
        self.binder_module = binder_module
        _source(observer_module, observer_module.__file__, OBSERVER_SHA256)
        _source(binder_module, binder_module.__file__, BINDER_SHA256)
        observer_source = Path(observer_module.__file__).read_bytes().decode('utf-8')
        for definition in ast.parse(observer_source).body:
            if isinstance(definition, ast.FunctionDef) and not definition.decorator_list:
                _plain(observer_module, observer_source, definition.name)
        binder_source = Path(binder_module.__file__).read_bytes().decode('utf-8')
        for definition in ast.parse(binder_source).body:
            if isinstance(definition, ast.ClassDef) and definition.name == 'GatherBinding':
                for method in definition.body:
                    if isinstance(method, ast.FunctionDef):
                        _plain(binder_module, binder_source, method.name, 'GatherBinding')
        m, s = self.modules, self.sources
        default_key = _plain(m['cache'], s['cache'], 'default_key')
        for name in ('gather_primitive_cache_key', 'get_primitive_cache_key'):
            _cached(m['primitives'], s['primitives'], name, default_key, m['cache'], s['cache'])
        self.gather = _cached(m['primitives'], s['primitives'], 'gather_primitives',
                              m['primitives'].gather_primitive_cache_key, m['cache'], s['cache'])
        self.cache = _cached(m['primitives'], s['primitives'], '__gather_cache_primitives',
                             m['primitives'].get_primitive_cache_key, m['cache'], s['cache'])
        self.reference = _plain(m['exporter'], s['exporter'], '__to_reference', 'GlTF2Exporter',
                                 m['exporter'].GlTF2Exporter.__dict__['_GlTF2Exporter__to_reference'])
        self.image_data = _plain(m['image'], s['image'], '__get_image_data')
        need(m['obj_data'].gltf2_blender_gather_primitives is m['primitives'] and
             m['primitives'].gltf2_blender_gather_primitives_extract is m['extractor'] and
             m['primitives'].get_final_material is m['materials'].get_final_material and
             m['texture'].image is m['image'] and
             m['texture_info'].gltf2_blender_gather_texture is m['texture'], 'exporter_module_alias_differs')
        need(all(module.gltf2_io is m['gltf'] for key, module in m.items()
                 if key in ('primitives', 'obj_data', 'exporter', 'materials', 'texture_info', 'texture', 'image')),
             'gltf_type_module_alias_differs')
        need(all(module.export_user_extensions is m['user_extensions'].export_user_extensions
                 for key, module in m.items() if key in ('obj_data', 'materials', 'texture_info', 'texture', 'image')),
             'extension_dispatcher_alias_differs')
        _plain(m['user_extensions'], s['user_extensions'], 'export_user_extensions')
        _plain(m['utils'], s['utils'], 'fast_structured_np_unique')
        need(m['extractor'].fast_structured_np_unique is m['utils'].fast_structured_np_unique and
             m['extractor'].np is m['utils'].np, 'numpy_or_unique_helper_alias_differs')

    def observed_methods(self, callback):
        observer, module = self.observer, self.modules['extractor']
        original_ast, changed_ast, proof = observer.instrument_pinned_class(self.sources['extractor'])
        klass = module.PrimitiveCreator
        clean = observer._compiled_class(original_ast, module.__dict__, module.__file__)
        namespace = dict(module.__dict__)
        need(observer.CALLBACK not in namespace, 'observer_global_collision')
        namespace[observer.CALLBACK] = callback
        observed = observer._compiled_class(changed_ast, namespace, module.__file__)
        rows = []
        for name in observer.METHODS:
            original = klass.__dict__[name]
            need(type(original) is types.FunctionType and not original.__code__.co_freevars and
                 original.__globals__ is module.__dict__ and original.__code__.co_filename == module.__file__ and
                 original.__code__ == clean.__dict__[name].__code__, 'extractor_runtime_method_differs')
            rows.append((klass, name, original, observed.__dict__[name]))
        return rows, proof


class ExportHookSession:
    """Single collector + actual call-chain bridge; no operator invocation.

    `point_admission` must independently recheck CURRENT object/mesh point order,
    joins, ownership and unresolved identity before every preflight.  This class
    cannot promote the historical ordered-numeric relation into native identity.
    `resources` is the bounded graph/resource gate in resource_gate_proposal.py.
    Synthetic callers may construct a fake surface, never a qualified receipt.
    """
    def __init__(self, surface, admissions, numpy_module, resources, point_admission, expected_options):
        self.surface = surface
        self.admissions = admissions
        self.np = numpy_module
        need(numpy_module is surface.modules['extractor'].np and
             numpy_module is surface.modules['utils'].np, 'actual_exporter_numpy_module_required')
        self.resources = resources
        self.point_admission = point_admission
        self.options = dict(expected_options)
        need(callable(point_admission) and len(self.options) <= 128, 'host_admission_and_bounded_options_required')
        mandatory = {'gltf_format': 'GLB', 'gltf_shared_accessors': False, 'gltf_attributes': True,
                     'gltf_materials': 'EXPORT', 'gltf_keep_original_textures': False,
                     'gltf_draco_mesh_compression': False, 'gltf_image_format': 'AUTO',
                     'gltf_unused_textures': False, 'gltf_unused_images': False,
                     'gltf_add_webp': False, 'gltf_webp_fallback': False,
                     'gltf_current_frame': True, 'gltf_animations': False}
        need(all(key in self.options and type(self.options[key]) is type(value) and self.options[key] == value
                 for key, value in mandatory.items()), 'mandatory_narrow_export_profile_missing')
        self.binder = surface.binder_module.GatherBinding(admissions)
        self.latch = FailureLatch()
        self.settings = None
        self.active = None
        self.frames = []
        self.bound = []
        self.preflights = 0
        self.finished = False
        self.installed = False

    def _guard(self, code, call):
        try:
            self.latch.check()
            return call()
        except Exception as error:
            self.latch.capture(code, error)
            raise

    def _settings(self, settings):
        self.latch.check()
        need(extension_inventory(self.enabled_names, self.extension_module, self.extension_constructor) == self.extension_modules,
             'enabled_addon_module_inventory_changed')
        need(self.preflights == 1 and settings is self.settings, 'settings_identity_or_preflight_missing')
        need(type(settings.get('gltf_user_extensions')) is list and
             same_refs(settings['gltf_user_extensions'], [self]), 'collector_not_sole_extension')
        need(settings.get('pre_export_callbacks') == [] and type(settings.get('pre_export_callbacks')) is list and
             settings.get('post_export_callbacks') == [] and type(settings.get('post_export_callbacks')) is list,
             'foreign_export_callbacks')
        need(all(key in settings and type(settings[key]) is type(value) and settings[key] == value
                 for key, value in self.options.items()), 'observed_export_options_differ')

    def pre_export_hook(self, settings):
        def action():
            need(self.preflights == 0 and self.installed, 'duplicate_or_uninstalled_preflight')
            self.settings = settings
            self.preflights = 1
            self._settings(settings)
            self.point_admission()  # Must refuse ambiguous/current identity; no success marker substitutes.
            self.resources.check_unchanged()
        return self._guard('pre_export_hook', action)

    def _entry(self, mesh):
        found = [row for row in self.admissions if row['mesh'] is mesh]
        need(len(found) == 1, 'unadmitted_or_aliased_mesh')
        return found[0]

    def _gather(self, original, args, kwargs):
        def action():
            need(not kwargs and len(args) == 6 and self.active is None, 'unexpected_or_nested_gather_signature')
            mesh, uuid, groups, modifiers, materials, settings = args
            self._settings(settings)
            entry = self._entry(mesh)
            need(all(frame['entry'] is not entry for frame in self.frames) and
                 type(materials) is tuple and same_refs(materials, entry['material_slots']),
                 'repeated_gather_or_material_tuple_differs')
            need(uuid is not None and settings['vtree'].nodes[uuid].blender_object is entry['object'],
                 'gather_vtree_object_differs')
            # ORM's image-size getters can precede __get_image_data.  The entire
            # admitted simple graph must remain valid BEFORE genuine gather.
            self.resources.check_unchanged()
            frame = dict(entry=entry, uuid=uuid, groups=groups, modifiers=modifiers,
                         materials=materials, creator=None, cache=None, gathered=None)
            self.active = frame
            try:
                result = original(*args)
                need(frame['creator'] is not None and frame['cache'] is not None,
                     'warm_cache_or_missing_extractor_observation')
                need(type(result) is list, 'gather_return_list_required')
                frame['gathered'] = result
                self.frames.append(frame)
                return result
            finally:
                self.active = None
        return self._guard('gather_return_wrapper', action)

    def _cache(self, original, args, kwargs):
        def action():
            need(not kwargs and len(args) == 6 and self.active is not None, 'cache_outside_cold_gather')
            materials, mesh, uuid, groups, modifiers, settings = args
            self._settings(settings)
            frame = self.active
            need(mesh is frame['entry']['mesh'] and materials is frame['materials'] and uuid == frame['uuid'] and
                 groups is frame['groups'] and modifiers is frame['modifiers'] and frame['cache'] is None,
                 'cache_call_chain_identity_differs')
            result = original(*args)
            need(type(result) is tuple and len(result) == 2 and type(result[0]) is list and
                 type(result[1]) is list and len(result[0]) == len(result[1]) and
                 all(value is None for value in result[1]) and frame['creator'] is not None,
                 'cache_result_udim_or_missing_cold_creator')
            frame['cache'] = result[0]  # Retain actual list, never reconstruct it.
            return result
        return self._guard('cache_return_wrapper', action)

    def observe_creator(self, creator, branch, points, slot, topology, ordinal):
        def action():
            frame = self.active
            need(frame is not None and branch == 'not_shared' and creator.blender_object is frame['entry']['object'] and
                 creator.blender_mesh is frame['entry']['mesh'] and
                 (frame['creator'] is None or frame['creator'] is creator), 'creator_call_chain_differs')
            np = self.np
            need(type(points) is np.ndarray and points.dtype == np.dtype(np.uint32) and
                 points.ndim == 1 and 0 < points.size <= 200_000, 'exact_u32_point_array_required')
            # np.unique(return_inverse=True) is np.intp in this pinned implementation.
            need(type(topology) is np.ndarray and topology.dtype == np.dtype(np.intp) and
                 topology.ndim == 1 and 0 < topology.size <= 1_000_000 and
                 bool(np.all(topology >= 0)) and bool(np.all(topology < points.size)),
                 'exact_nonnegative_intp_inverse_array_required')
            need(type(slot) is np.uint32 and slot.ndim == 0 and 0 <= slot.item() < len(frame['materials']),
                 'exact_u32_material_scalar_required')
            need(bool(np.all(points < len(frame['entry']['joined_source_ids']))), 'point_array_bounds')
            need(type(ordinal) is int, 'exact_python_creation_ordinal_required')
            frame['creator'] = creator
            self.binder.observe_creator(creator, branch, points.tolist(), slot.item(), topology.tolist(), ordinal)
        return self._guard('extractor_observer', action)

    def gather_mesh_hook(self, mesh, blender_mesh, blender_object, groups, modifiers, materials, settings):
        def action():
            self._settings(settings)
            found = [frame for frame in self.frames if frame['entry']['mesh'] is blender_mesh and
                     frame['entry']['object'] is blender_object]
            need(len(found) == 1 and all(frame is not found[0] for frame in self.bound), 'missing_or_repeated_gather_mesh')
            frame = found[0]
            need(groups is frame['groups'] and modifiers is frame['modifiers'] and materials is frame['materials'],
                 'mesh_hook_call_chain_differs')
            self.resources.bind_primitive_materials(materials, frame['cache'], frame['gathered'])
            self.binder.bind_gather(frame['creator'], materials, frame['cache'], frame['gathered'], mesh)
            self.bound.append(frame)
        return self._guard('gather_mesh_hook', action)

    def gather_material_hook(self, material, blender_material, settings):
        return self._guard('gather_material_hook', lambda: (self._settings(settings), self.resources.material(material, blender_material)))

    def gather_texture_info_hook(self, info, sockets, settings):
        return self._guard('gather_texture_info_hook', lambda: (self._settings(settings), self.resources.texture_info(info, sockets)))

    def gather_texture_hook(self, texture, sockets, settings):
        return self._guard('gather_texture_hook', lambda: (self._settings(settings), self.resources.texture(texture, sockets)))

    def gather_image_hook(self, image, descriptor, sockets, settings):
        return self._guard('gather_image_hook', lambda: (self._settings(settings), self.resources.image(image, descriptor, sockets)))

    def _image_data(self, original, args, kwargs):
        def action():
            need(not kwargs and len(args) == 3, 'unexpected_image_data_signature')
            sockets, use_tile, settings = args
            self._settings(settings)
            self.resources.before_image_data(sockets, use_tile)  # BEFORE ordinary traversal/encoding.
            result = original(*args)
            self.resources.after_image_data(sockets, result)
            return result
        return self._guard('pre_encoding_resource_wrapper', action)

    def _reference(self, original, exporter, value):
        # Always call genuine reference assignment exactly once, first.  Real
        # exporter exceptions propagate unchanged, never become a fallback path.
        index = original(exporter, value)
        def action():
            self.latch.check()
            gltf = self.surface.modules['gltf']
            if type(value) is gltf.Material:
                self.resources.reference('material', value, index)
                self.binder.record_material_reference(value, index)
            elif type(value) is gltf.Mesh:
                self.binder.record_mesh_reference(value, index)
            elif type(value) is gltf.Texture:
                self.resources.reference('texture', value, index)
            elif type(value) is gltf.Image:
                self.resources.reference('image', value, index)
            return index
        return self._guard('actual_reference_assignment', action)

    @contextmanager
    def install(self, extension_module, enabled_names):
        need(not self.installed and not self.finished and self.preflights == 0, 'session_reuse_refused')
        rows, self.observer_proof = self.surface.observed_methods(self.observe_creator)
        modules = self.surface.modules
        before_class = dict(modules['extractor'].PrimitiveCreator.__dict__)
        originals = (self.surface.gather, self.surface.cache, self.surface.reference, self.surface.image_data)
        @functools.wraps(originals[0])
        def gather(*args, **kwargs):
            return self._gather(originals[0], args, kwargs)
        @functools.wraps(originals[1])
        def cache(*args, **kwargs):
            return self._cache(originals[1], args, kwargs)
        @functools.wraps(originals[2])
        def reference(exporter, value):
            return self._reference(originals[2], exporter, value)
        @functools.wraps(originals[3])
        def image_data(*args, **kwargs):
            return self._image_data(originals[3], args, kwargs)
        try:
            with OwnedPatches(self.latch) as patches:
                for owner, name, original, observed in rows:
                    patches.replace(owner, name, original, observed)
                patches.replace(modules['primitives'], 'gather_primitives', originals[0], gather)
                patches.replace(modules['primitives'], '__gather_cache_primitives', originals[1], cache)
                patches.replace(modules['exporter'].GlTF2Exporter, '_GlTF2Exporter__to_reference', originals[2], reference)
                patches.replace(modules['image'], '__get_image_data', originals[3], image_data)
                patches.register_extension(extension_module, enabled_names, self)
                self.enabled_names = tuple(enabled_names)
                self.extension_module = extension_module
                self.extension_constructor = extension_module.glTF2ExportUserExtension
                self.extension_modules = extension_inventory(self.enabled_names, extension_module, self.extension_constructor)
                self.installed = True
                yield self
                self._settings(self.settings)
                need(len(self.frames) == len(self.bound) == len(self.admissions) and self.active is None,
                     'missing_final_gather_or_mesh_hook')
                self.point_admission()
                self.resources.check_unchanged()
        finally:
            self.installed = False
            after_class = modules['extractor'].PrimitiveCreator.__dict__
            try:
                need(before_class.keys() == after_class.keys() and
                     all(value is after_class[key] for key, value in before_class.items()),
                     'extractor_class_not_restored_exactly')
            except Exception as error:
                self.latch.capture('extractor_complete_class_restoration', error)
                # Existing export exceptions remain primary.  A successful body
                # reaches the outside-dispatch latch.check immediately below.
        self.latch.check()  # Mandatory OUTSIDE dispatcher's swallowed hook exceptions.

    def finish(self, raw_glb, expected_sha256):
        need(not self.installed and not self.finished and self.preflights == 1, 'finish_lifecycle_differs')
        self.latch.check()
        self.point_admission()
        self.resources.check_unchanged()
        relation, binding = self.binder.finalize(raw_glb, expected_sha256)
        document, _ = self.surface.binder_module.read_glb(raw_glb)
        resources = self.resources.finalize(document)
        self.finished = True
        return relation, dict(format='has_source_export_hook_proposal_1',
                              actual_export_binding=binding, resources=resources,
                              source_normal_max_error_unchanged=SOURCE_NORMAL_MAX_ERROR,
                              native_point_identity_qualified=False,
                              current_B_identity_qualified=False,
                              native_normal_fidelity_qualified=False,
                              non_normal_semantic_equivalence_qualified=False,
                              application_adoption_qualified=False)
