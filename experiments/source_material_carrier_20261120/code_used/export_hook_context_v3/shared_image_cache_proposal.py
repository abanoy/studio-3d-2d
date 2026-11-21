"""UNRUN shared-Image cache observation; no IO, Blender, exporter or NumPy import.

Only PinnedSurface's genuine cold cache specifications belong in an actual
host. Fabricated specifications in pure tests never qualify an actual export.
This observer never edits a cache/key/result or creates an exporter resource.
"""
import hashlib
import types

import resource_gate_proposal as R

MAX_CALLS = 1024
MAX_ENTRIES = 128
COUNTS = {'gather_image': 3, 'make_image': 7, 'buffer_view': 4,
          'uri': 4, 'gather_texture': 3, 'texture_info': 5}


def need(ok, code):
    R.need(ok, code)


def _components(wrapper):
    need(type(wrapper) is types.FunctionType and wrapper.__code__.co_freevars == ('func', 'key') and
         wrapper.__closure__ is not None and len(wrapper.__closure__) == 2,
         'shared_cache_wrapper_closure_shape')
    func, key = (cell.cell_contents for cell in wrapper.__closure__)
    need(type(func) is types.FunctionType and type(key) is types.FunctionType and wrapper.__wrapped__ is func,
         'shared_cache_wrapper_function_or_key')
    return func, key


class SharedImageCaches:
    """Read the genuine cached-call relation and bind each hook to one event."""
    def __init__(self, resources, specs, binary_type, gltf_image_type):
        need(resources.shared_images_enabled is True and resources.shared_cache is None,
             'shared_cache_attachment_requires_fresh_opt_in')
        need(type(specs) is dict and set(specs) == set(COUNTS), 'exact_shared_cache_specifications')
        need(isinstance(binary_type, type) and isinstance(gltf_image_type, type), 'actual_shared_cache_types')
        self.resources, self.binary_type, self.image_type = resources, binary_type, gltf_image_type
        self.binary_methods = {}
        for name in ('__init__', '__eq__', '__hash__'):
            method = binary_type.__dict__.get(name)
            need(type(method) is types.FunctionType, 'shared_binary_methods_not_plain')
            self.binary_methods[name] = (method, method.__code__, method.__globals__, method.__defaults__, method.__kwdefaults__)
        self.identity_classes = (resources.search.NodeSocket, resources.encode.ExportImage, gltf_image_type)
        self.identity_bases = tuple(klass.__bases__ for klass in self.identity_classes)
        need(all(klass.__eq__ is object.__eq__ and klass.__hash__ is object.__hash__ for klass in self.identity_classes),
             'shared_cache_identity_class_changed')
        self.specs = {}
        for name, wrapper in specs.items():
            func, key = _components(wrapper)
            need(not hasattr(func, '__cache') and not hasattr(func, '__export_settings'), 'shared_warm_cache_refused')
            self.specs[name] = dict(wrapper=wrapper, func=func, key=key,
                wrapper_code=wrapper.__code__, func_code=func.__code__, key_code=key.__code__,
                wrapper_globals=wrapper.__globals__, func_globals=func.__globals__, key_globals=key.__globals__,
                func_defaults=func.__defaults__, func_kwdefaults=func.__kwdefaults__,
                cache=None, entries=[], calls=0, hits=0, misses=0)
        self.stack, self.gathers, self.makes, self.buffers = [], [], [], []
        self.active = None
        self.settings = None
        self.reference_phase = False
        self.calls = 0
        self.encoded_bytes = 0
        self.failed = False
        resources.shared_cache = self

    def _runtime(self, row):
        need(type(self.binary_type) is type and self.binary_type.__bases__ == (object,) and
             self.binary_type.__getattribute__ is object.__getattribute__ and
             '__getattr__' not in self.binary_type.__dict__, 'shared_binary_attribute_access_changed')
        need('data' not in self.binary_type.__dict__ and 'bufferViewTarget' not in self.binary_type.__dict__,
             'shared_binary_instance_field_descriptor_changed')
        need(self.resources.search.NodeSocket is self.identity_classes[0] and
             self.resources.encode.ExportImage is self.identity_classes[1] and
             self.resources.gltf.Image is self.identity_classes[2] and all(
                 klass.__bases__ == bases and klass.__eq__ is object.__eq__ and klass.__hash__ is object.__hash__ and
                 klass.__getattribute__ is object.__getattribute__ and '__getattr__' not in klass.__dict__
                 for klass, bases in zip(self.identity_classes, self.identity_bases)), 'shared_cache_identity_class_changed')
        for name, prior in self.binary_methods.items():
            method = self.binary_type.__dict__.get(name)
            need(method is prior[0] and method.__code__ is prior[1] and method.__globals__ is prior[2] and
                 method.__defaults__ is prior[3] and method.__kwdefaults__ is prior[4], 'shared_binary_runtime_method_changed')
        for buffer in self.buffers:
            need(type(buffer['buffer']) is self.binary_type and buffer['buffer'].data is buffer['data'] and
                 buffer['buffer'].bufferViewTarget is None, 'shared_retained_binary_data_changed')
        func, key = _components(row['wrapper'])
        need(func is row['func'] and key is row['key'] and row['wrapper'].__code__ is row['wrapper_code'] and
             func.__code__ is row['func_code'] and key.__code__ is row['key_code'] and
             row['wrapper'].__globals__ is row['wrapper_globals'] and func.__globals__ is row['func_globals'] and
             key.__globals__ is row['key_globals'] and func.__defaults__ is row['func_defaults'] and
             func.__kwdefaults__ is row['func_kwdefaults'], 'shared_cache_runtime_function_changed')

    def _state(self, row):
        self._runtime(row)
        func = row['func']
        present = hasattr(func, '__cache'), hasattr(func, '__export_settings')
        if row['cache'] is None:
            need(present == (False, False), 'shared_unobserved_cache_creation')
            return None, []
        need(present == (True, True) and getattr(func, '__cache') is row['cache'] and
             getattr(func, '__export_settings') is self.settings and type(row['cache']) is dict,
             'shared_cache_or_settings_object_changed')
        need(len(row['cache']) <= MAX_ENTRIES, 'shared_cache_entry_budget_before_snapshot')
        items = list(row['cache'].items())
        need(len(items) == len(row['entries']) and
             all(actual[0] is expected[0] and actual[1] is expected[1]
                 for actual, expected in zip(items, row['entries'])), 'shared_cache_entries_changed')
        return row['cache'], items

    def _key(self, name, args):
        key = self.specs[name]['key'](*args)
        need(type(key) is tuple and 1 <= len(key) <= 6, 'shared_cache_actual_key_schema')
        return key

    def _hit(self, entries, key):
        # Entries are already exact observed keys/results. Inputs are admitted
        # concrete classes; BinaryData equality/hash are source-attested by H.
        found = [row for row in entries if row[0] == key]
        need(len(found) <= 1, 'shared_cache_ambiguous_key')
        return None if not found else found[0]

    def _source(self, key):
        images = [image for _socket, image, _kind in key]
        need(images and all(image is images[0] for image in images), 'shared_cross_image_composition_refused')
        found = [row for row in self.resources.tickets if row['image'] is images[0]]
        need(len(found) == 1, 'shared_unadmitted_actual_source_image')
        return found[0]

    def _buffer(self, value, frame):
        need(type(value) is self.binary_type and value.bufferViewTarget is None and type(value.data) is bytes,
             'shared_actual_binary_data_required')
        ticket = self._source(frame['key'])
        need(len(value.data) == ticket['encoded_bytes'] and
             hashlib.sha256(value.data).hexdigest() == ticket['packed_sha256'], 'shared_encoded_bytes_differ_from_pin')
        if all(prior['buffer'] is not value for prior in self.buffers):
            self.encoded_bytes += len(value.data)
            need(self.encoded_bytes <= R.MAX_TOTAL_BYTES, 'shared_actual_encoded_buffer_budget')
            self.buffers.append(dict(buffer=value, data=value.data))
        return value

    def _same_sockets(self, frame, sockets):
        need(sockets is frame['sockets'] and R._same_key(self.resources._socket_key(sockets), frame['key']),
             'shared_gather_socket_arguments_changed')

    def before_descriptor(self, sockets):
        need(self.active is not None and self.active['descriptor'] is None and not self.reference_phase,
             'shared_descriptor_without_genuine_gather_body')
        self._same_sockets(self.active, sockets)

    def after_descriptor(self, sockets, descriptor, mapping):
        self.before_descriptor(sockets)
        self.active['descriptor'], self.active['mapping'] = descriptor, mapping

    def image_hook(self, image, descriptor, sockets):
        frame = self.active
        need(frame is not None and not self.reference_phase and frame['descriptor'] is descriptor and
             frame['event'] is not None and frame['event']['image'] is image and frame['hook'] is None,
             'shared_image_hook_without_once_owned_make_event')
        self._same_sockets(frame, sockets)
        need(R._same_mapping(self.resources._descriptor(descriptor, frame['key']), frame['mapping']),
             'shared_descriptor_changed_before_hook')
        frame['hook'] = image

    def _before(self, name, args, hit):
        if name in ('gather_image', 'gather_texture'):
            sockets, tile, _settings = args
            need(tile is None, 'shared_udim_not_admitted')
            key = self.resources._socket_key(sockets)
            if name == 'gather_image':
                need(self.active is None, 'shared_nested_image_gather')
                need(sum(R._same_key(key, graph['socket_keys']) for graph in self.resources.graphs) == 1,
                     'shared_incomplete_planned_socket_key')
                prior = [row for row in self.gathers if R._same_key(row['key'], key)]
                if hit is not None:
                    need(len(prior) == 1 and prior[0]['result'] is hit[1], 'shared_gather_hit_without_observed_binding')
                    return dict(hit=True, prior=prior[0])
                need(not prior, 'shared_repeated_canonical_socket_gather')
                frame = dict(key=key, sockets=sockets, descriptor=None, mapping=None, event=None,
                             hook=None, uri=False, buffer=None, result=None)
                self.active = frame
                return dict(hit=False, frame=frame)
            return dict(key=key)
        if name == 'texture_info':
            primary, sockets, kind, filter_type, _settings = args
            key = self.resources._socket_key(sockets)
            primary_key = self.resources._socket_key((primary,))
            need(kind == 'DEFAULT' and filter_type == 'ALL' and
                 R._same_key(primary_key, key[:1]), 'shared_texture_info_profile_or_primary_socket')
            return dict(key=key)
        frame = self.active
        need(frame is not None and frame['descriptor'] is not None, 'shared_image_cache_without_early_descriptor')
        need(R._same_mapping(self.resources._descriptor(frame['descriptor'], frame['key']), frame['mapping']),
             'shared_descriptor_changed_before_cache_call')
        if name in ('uri', 'buffer_view'):
            descriptor, mime, image_name, _settings = args
            need(descriptor is frame['descriptor'] and mime == 'image/png' and type(image_name) is str and
                 0 < len(image_name) <= 512 and hit is None, 'shared_early_encoding_key_or_cache_differs')
            if name == 'uri':
                need(not frame['uri'] and frame['buffer'] is None and frame['event'] is None,
                     'shared_duplicate_or_late_uri_call')
            else:
                need(frame['uri'] and frame['buffer'] is None and frame['event'] is None,
                     'shared_duplicate_or_early_buffer_call')
            return dict(frame=frame, image_name=image_name)
        need(name == 'make_image' and frame['uri'] and frame['buffer'] is not None and frame['event'] is None,
             'shared_make_image_missing_early_encoding_observation')
        buffer, extensions, extras, mime, image_name, uri, _settings = args
        need(buffer is frame['buffer'] and extensions is None and extras is None and mime == 'image/png' and
             image_name == frame['image_name'] and uri is None, 'shared_complete_make_image_fields_differ')
        self._buffer(buffer, frame)
        ticket = self._source(frame['key'])
        if hit is not None:
            prior = [event for event in self.makes if event['stored_key'] is hit[0] and event['image'] is hit[1]]
            need(len(prior) == 1 and prior[0]['source'] is ticket['image'] and
                 R._same_mapping(prior[0]['mapping'], frame['mapping']), 'shared_cache_merge_without_same_source_and_mapping')
        return dict(frame=frame, source=ticket['image'])

    def _admit_args(self, name, args):
        """Admit every key component BEFORE equality/hash on any cached key.

        BinaryData.__eq__ reads other.data, so unknown incoming objects must
        never be offered to it, even when a genuine make-image cache is warm.
        """
        if name in ('gather_image', 'gather_texture'):
            need(args[1] is None, 'shared_udim_not_admitted')
            self.resources._socket_key(args[0])
            return
        if name == 'texture_info':
            primary, sockets, kind, filter_type, _settings = args
            self.resources._socket_key(sockets)
            self.resources._socket_key((primary,))
            need(type(kind) is str and type(filter_type) is str and kind == 'DEFAULT' and filter_type == 'ALL',
                 'shared_texture_info_argument_types')
            return
        frame = self.active
        need(frame is not None and frame['descriptor'] is not None, 'shared_image_cache_without_early_descriptor')
        if name in ('uri', 'buffer_view'):
            descriptor, mime, image_name, _settings = args
            need(descriptor is frame['descriptor'] and type(descriptor) is self.resources.encode.ExportImage and
                 type(mime) is str and mime == 'image/png' and type(image_name) is str and 0 < len(image_name) <= 512,
                 'shared_encoding_argument_types')
            return
        buffer, extensions, extras, mime, image_name, uri, _settings = args
        need(buffer is frame['buffer'] and type(buffer) is self.binary_type and
             extensions is None and extras is None and uri is None and type(mime) is str and mime == 'image/png' and
             type(image_name) is str and 0 < len(image_name) <= 512, 'shared_make_image_argument_types')
        self._buffer(buffer, frame)

    def _after(self, name, args, result, context, stored_key, hit):
        if name == 'gather_image':
            if context['hit']:
                need(result is context['prior']['result'], 'shared_gather_cached_return_changed')
                return
            frame = context['frame']
            need(type(result) is tuple and len(result) == 4 and result[0] is frame['hook'] and
                 result[1] is frame['descriptor'] and result[2] is None and result[3] is None and
                 frame['event'] is not None and frame['hook'] is not None, 'shared_gather_return_or_hook_coverage')
            frame['result'] = result
            self.gathers.append(frame)
            return
        if name in ('gather_texture', 'texture_info'):
            size, field, table = (3, 'texture', self.resources.textures) if name == 'gather_texture' else (
                4, 'info', self.resources.infos)
            need(type(result) is tuple and len(result) == size and
                 len([row for row in table if row[field] is result[0] and R._same_key(row['key'], context['key'])]) == 1,
                 'shared_cache_return_without_exact_resource_hook')
            if name == 'gather_texture':
                need(result[1:] == (None, None), 'shared_texture_factor_or_udim')
            else:
                need(type(result[1]) is dict and type(result[2]) is dict and not result[2] and result[3] is None,
                     'shared_texture_info_udim_or_factor')
            return
        frame = context['frame']
        if name == 'uri':
            need(type(result) is tuple and len(result) == 2 and result == (None, None), 'shared_glb_uri_result_differs')
            frame['uri'], frame['image_name'] = True, context['image_name']
        elif name == 'buffer_view':
            need(type(result) is tuple and len(result) == 2 and result[1] is None and
                 context['image_name'] == frame['image_name'], 'shared_buffer_result_or_name_differs')
            frame['buffer'] = self._buffer(result[0], frame)
        else:
            # A legitimate make-image cache hit preserves the *first* equal
            # BinaryData object in the cached Image, not this call's new buffer.
            expected_buffer = frame['buffer'] if hit is None else stored_key[0]
            need(type(expected_buffer) is self.binary_type and
                 any(row['buffer'] is expected_buffer for row in self.buffers) and
                 type(result) is self.image_type and result.buffer_view is expected_buffer and
                 result.mime_type == 'image/png' and result.uri is None and result.extensions is None and
                 result.extras is None and result.name == frame['image_name'], 'shared_make_image_return_differs')
            if hit is None:
                need(all(event['image'] is not result for event in self.makes), 'shared_uncached_image_alias_refused')
            event = dict(image=result, stored_key=stored_key, source=context['source'],
                         mapping=frame['mapping'], hit=hit is not None)
            frame['event'] = event
            # One source cache entry may have multiple authorized hit events.
            # Retain only its first event as the causal origin for later hits.
            if hit is None:
                self.makes.append(event)

    def call(self, name, original, args, kwargs):
        try:
            need(not self.failed, 'shared_prior_cache_failure')
            return self._call(name, original, args, kwargs)
        except BaseException:
            self.failed = True
            raise

    def _call(self, name, original, args, kwargs):
        need(type(name) is str and name in self.specs and original is self.specs[name]['wrapper'] and
             type(args) is tuple and type(kwargs) is dict and not kwargs and
             len(args) == COUNTS[name] and not self.reference_phase, 'shared_cache_call_contract')
        self.calls += 1
        need(self.calls <= MAX_CALLS and len(self.stack) < 16, 'shared_cache_call_budget')
        settings = args[-1]
        need(type(settings) is dict, 'shared_actual_settings_dictionary_required')
        if self.settings is None: self.settings = settings
        need(settings is self.settings, 'shared_cache_settings_identity')
        self.resources.check_unchanged()
        row = self.specs[name]
        _cache, before = self._state(row)
        self._admit_args(name, args)
        key = self._key(name, args)
        hit = self._hit(before, key)
        if _cache is not None:
            need((key in _cache) is (hit is not None) and (hit is None or _cache[key] is hit[1]),
                 'shared_genuine_dictionary_lookup_differs')
        context = self._before(name, args, hit)
        token = object()
        self.stack.append(token)
        primary = None
        try:
            result = original(*args)
            self._runtime(row)
            func = row['func']
            need(hasattr(func, '__cache') and hasattr(func, '__export_settings') and
                 type(getattr(func, '__cache')) is dict and getattr(func, '__export_settings') is settings,
                 'shared_missing_original_cache_after_call')
            cache = getattr(func, '__cache')
            need(row['cache'] is None or cache is row['cache'], 'shared_cache_dictionary_replaced')
            need(len(cache) <= MAX_ENTRIES, 'shared_cache_entry_budget_before_snapshot')
            after = list(cache.items())
            expected_count = len(before) + (1 if hit is None else 0)
            need(len(after) == expected_count <= MAX_ENTRIES and all(a[0] is b[0] and a[1] is b[1]
                 for a, b in zip(after[:len(before)], before)), 'shared_cache_unexpected_transition')
            stored = after[-1] if hit is None else hit
            need(stored[0] == key and stored[1] is result, 'shared_original_cache_result_or_key_differs')
            row['cache'], row['entries'] = cache, after
            row['calls'] += 1
            row['hits' if hit is not None else 'misses'] += 1
            self._after(name, args, result, context, stored[0], hit)
            self.resources.check_unchanged()
            return result
        except BaseException as error:
            primary = error
            raise
        finally:
            if not self.stack or self.stack.pop() is not token:
                self.failed = True
                if primary is None:
                    need(False, 'shared_cache_call_stack_changed')
                elif hasattr(primary, 'add_note'):
                    primary.add_note('Shared cache call stack changed; observation remains unqualified.')
            if name == 'gather_image' and not context.get('hit', False):
                self.active = None

    def begin_references(self):
        need(not self.stack and self.active is None, 'shared_reference_during_gather')
        self._coverage()
        self.reference_phase = True

    def _coverage(self):
        need(not self.failed, 'shared_prior_cache_failure')
        need(not self.stack and self.active is None, 'shared_unclosed_cache_call')
        for row in self.specs.values(): self._state(row)
        expected = [graph for graph in self.resources.graphs if graph['images']]
        need(len(self.gathers) == len(self.resources.image_bindings) == len(expected), 'shared_missing_planned_graph_binding')
        for graph in expected:
            found = [frame for frame in self.gathers if R._same_key(frame['key'], graph['socket_keys'])]
            need(len(found) == 1 and found[0]['hook'] is not None and found[0]['event'] is not None,
                 'shared_planned_graph_binding_coverage')

    def finish(self):
        self._coverage()
        need(self.reference_phase, 'shared_no_final_resource_references')

    def summary(self):
        self.finish()
        return dict(format='has_observed_shared_image_cache_relation_1', calls=self.calls,
                    image_bindings=len(self.gathers), unique_glTF_images=len(self.resources.images),
                    observed_encoded_buffer_bytes=self.encoded_bytes,
                    caches={name: dict(calls=row['calls'], hits=row['hits'], misses=row['misses'],
                                       entries=len(row['entries'])) for name, row in sorted(self.specs.items())},
                    actual_export_or_native_fidelity_qualified=False)
