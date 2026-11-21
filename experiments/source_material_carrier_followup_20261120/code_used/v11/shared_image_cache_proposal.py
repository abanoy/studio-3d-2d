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
MAKE_IMAGE_DIAGNOSTIC_FORMAT = 'has_strict_make_image_return_failure_observation_1'
MAKE_IMAGE_DIAGNOSTIC_BOOLEANS = frozenset((
    'cache_hit', 'expected_buffer_is_binary_data', 'expected_buffer_is_retained',
    'result_is_expected_image_type', 'result_buffer_is_expected_buffer', 'result_mime_is_png',
    'result_uri_is_none', 'result_extensions_is_none', 'result_extras_is_none', 'result_name_matches_frame',
    'result_fields_observed', 'result_buffer_is_binary_data', 'result_buffer_is_exact_int',
    'result_buffer_is_none', 'result_buffer_is_incoming_buffer', 'result_buffer_is_stored_key_buffer',
    'result_buffer_is_retained', 'result_buffer_hash_matches_authorized_source',
    'incoming_buffer_is_retained', 'incoming_buffer_hash_matches_authorized_source',
    'stored_buffer_is_binary_data', 'stored_buffer_is_retained', 'stored_buffer_hash_matches_authorized_source',
    'expected_buffer_hash_matches_authorized_source', 'authorized_source_ticket_observed',
    'all_strict_return_predicates_pass'))


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
        self.absences = []
        self.absence_hits = 0
        self.public_make_image_failure = None
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
        for event in self.makes:
            if event['hook_extensions_observed']:
                need(self._origin_extensions_unchanged(event), 'shared_recorded_image_extensions_changed')
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
        extensions = image.extensions
        need(extensions is None or type(extensions) is dict and not extensions,
             'shared_owned_image_hook_extensions_not_empty')
        event = frame['event']
        origin = event if not event['hit'] else event['origin']
        if event['hit']:
            need(origin is not None and self._origin_extensions_unchanged(origin),
                 'shared_image_hit_extensions_not_prior_owned_state')
        else:
            need(not origin['hook_extensions_observed'], 'shared_image_extensions_hook_already_observed')
            origin['hook_extensions'] = extensions
            origin['hook_extensions_observed'] = True
        frame['hook'] = image

    def _origin_extensions_unchanged(self, origin):
        if origin['hook_extensions_observed'] is not True or type(origin['image']) is not self.image_type:
            return False
        prior = origin['hook_extensions']
        current = origin['image'].extensions
        return ((prior is None and current is None) or
                type(prior) is dict and not prior and current is prior and type(current) is dict and not current)

    def _return_extensions_ok(self, result, context, hit):
        if hit is None:
            return result.extensions is None
        origin = context['origin']
        return (origin is not None and origin['image'] is result and origin['source'] is context['source'] and
                R._same_mapping(origin['mapping'], context['frame']['mapping']) and
                self._origin_extensions_unchanged(origin))

    def _absence_state(self):
        """Only texture_info's own genuine cache may change for an absence."""
        tables = []
        for name in ('descriptors', 'images', 'image_bindings', 'textures', 'infos', 'gathered_materials'):
            values = getattr(self.resources, name)
            need(type(values) is list and len(values) <= MAX_ENTRIES, 'negative_probe_resource_table_budget')
            tables.append((name, values, tuple(values)))
        references = []
        need(type(self.resources.references) is dict and set(self.resources.references) == {'image', 'texture', 'material'},
             'negative_probe_reference_tables')
        for name, values in sorted(self.resources.references.items()):
            need(type(values) is list and len(values) <= MAX_ENTRIES, 'negative_probe_reference_budget')
            references.append((name, values, tuple(values)))
        caches = []
        for name, row in sorted(self.specs.items()):
            if name == 'texture_info': continue
            cache, entries = self._state(row)
            caches.append((name, cache, tuple(entries), row['calls'], row['hits'], row['misses']))
        return dict(tables=tables, references=references, caches=caches,
                    gathers=tuple(self.gathers), makes=tuple(self.makes), buffers=tuple(self.buffers),
                    active=self.active, encoded_bytes=self.encoded_bytes, calls=self.calls)

    def _check_absence_state(self, before):
        after = self._absence_state()
        def same_refs(a, b):
            return len(a) == len(b) and all(x is y for x, y in zip(a, b))
        for field in ('tables', 'references'):
            need(len(before[field]) == len(after[field]) and all(
                a[0] == b[0] and a[1] is b[1] and same_refs(a[2], b[2])
                for a, b in zip(before[field], after[field])), 'negative_probe_created_or_replaced_resource')
        need(len(before['caches']) == len(after['caches']) and all(
            a[0] == b[0] and a[1] is b[1] and len(a[2]) == len(b[2]) and all(
                old[0] is new[0] and old[1] is new[1] for old, new in zip(a[2], b[2])) and a[3:] == b[3:]
            for a, b in zip(before['caches'], after['caches'])), 'negative_probe_changed_another_cache')
        need(all(same_refs(before[key], after[key]) for key in ('gathers', 'makes', 'buffers')) and
             before['active'] is after['active'] and before['encoded_bytes'] == after['encoded_bytes'] and
             before['calls'] == after['calls'], 'negative_probe_nested_gather_or_encoding')

    def _absent_result(self, result):
        need(type(result) is tuple and len(result) == 4 and result[0] is None and result[3] is None and
             type(result[1]) is dict and type(result[2]) is dict and not result[1] and not result[2],
             'negative_probe_exact_absent_result_required')

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
            context = self.resources._texture_info_request(primary, sockets, kind, filter_type)
            if context['probe']:
                need(self.active is None and not self.stack, 'negative_probe_inside_resource_gather')
                if hit is not None:
                    prior = [row for row in self.absences if row['stored_key'] is hit[0] and row['result'] is hit[1]]
                    need(len(prior) == 1 and R._same_probe_key(prior[0]['probe_key'], context['probe_key']) and
                         prior[0]['kind'] == kind, 'negative_probe_hit_without_observed_absence')
                context['absence_state'] = self._absence_state()
            return context
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
        origin = None
        if hit is not None:
            prior = [event for event in self.makes if event['stored_key'] is hit[0] and event['image'] is hit[1]]
            need(len(prior) == 1 and prior[0]['source'] is ticket['image'] and
                 R._same_mapping(prior[0]['mapping'], frame['mapping']), 'shared_cache_merge_without_same_source_and_mapping')
            origin = prior[0]
        return dict(frame=frame, source=ticket['image'], origin=origin)

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
            self.resources._texture_info_request(primary, sockets, kind, filter_type)
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

    def _make_image_return_diagnostic(self, result, frame, expected_buffer, stored_key, hit):
        values = {name: False for name in MAKE_IMAGE_DIAGNOSTIC_BOOLEANS}
        values['cache_hit'] = hit is not None
        values['expected_buffer_is_binary_data'] = type(expected_buffer) is self.binary_type
        values['expected_buffer_is_retained'] = any(row['buffer'] is expected_buffer for row in self.buffers)
        values['result_is_expected_image_type'] = type(result) is self.image_type
        fields = None
        if values['result_is_expected_image_type']:
            observed = object.__getattribute__(result, '__dict__')
            if type(observed) is dict and len(observed) <= 64 and all(type(key) is str for key in observed):
                fields = observed
        names = ('buffer_view', 'mime_type', 'uri', 'extensions', 'extras', 'name')
        values['result_fields_observed'] = fields is not None and all(name in fields for name in names)
        missing = object()
        viewed = fields['buffer_view'] if values['result_fields_observed'] else missing
        incoming, stored = frame['buffer'], stored_key[0]
        values.update(result_buffer_is_binary_data=type(viewed) is self.binary_type,
            result_buffer_is_exact_int=type(viewed) is int, result_buffer_is_none=viewed is None,
            result_buffer_is_incoming_buffer=viewed is incoming,
            result_buffer_is_stored_key_buffer=viewed is stored,
            result_buffer_is_retained=any(row['buffer'] is viewed for row in self.buffers),
            incoming_buffer_is_retained=any(row['buffer'] is incoming for row in self.buffers),
            stored_buffer_is_binary_data=type(stored) is self.binary_type,
            stored_buffer_is_retained=any(row['buffer'] is stored for row in self.buffers))
        if values['result_fields_observed']:
            values.update(result_buffer_is_expected_buffer=viewed is expected_buffer,
                result_mime_is_png=type(fields['mime_type']) is str and fields['mime_type'] == 'image/png',
                result_uri_is_none=fields['uri'] is None,
                result_extensions_is_none=fields['extensions'] is None,
                result_extras_is_none=fields['extras'] is None,
                result_name_matches_frame=type(fields['name']) is str and type(frame['image_name']) is str and
                    fields['name'] == frame['image_name'])
        ticket = self._source(frame['key'])
        values['authorized_source_ticket_observed'] = True
        checks = []
        def authorized(value):
            for prior, answer in checks:
                if value is prior: return answer
            answer = False
            if type(value) is self.binary_type:
                fields = object.__getattribute__(value, '__dict__')
                if type(fields) is dict and len(fields) <= 16 and all(type(key) is str for key in fields):
                    raw = fields.get('data')
                    if type(raw) is bytes and len(raw) == ticket['encoded_bytes'] <= R.MAX_TOTAL_BYTES:
                        answer = hashlib.sha256(raw).hexdigest() == ticket['packed_sha256']
            checks.append((value, answer))
            return answer
        values.update(result_buffer_hash_matches_authorized_source=authorized(viewed),
            incoming_buffer_hash_matches_authorized_source=authorized(incoming),
            stored_buffer_hash_matches_authorized_source=authorized(stored),
            expected_buffer_hash_matches_authorized_source=authorized(expected_buffer))
        strict = ('expected_buffer_is_binary_data', 'expected_buffer_is_retained',
                  'result_is_expected_image_type', 'result_buffer_is_expected_buffer', 'result_mime_is_png',
                  'result_uri_is_none', 'result_extensions_is_none', 'result_extras_is_none', 'result_name_matches_frame')
        values['all_strict_return_predicates_pass'] = all(values[name] for name in strict)
        return values

    def _record_make_image_failure(self, result, frame, expected_buffer, stored_key, hit):
        if self.public_make_image_failure is not None:
            prior = self.public_make_image_failure
            if type(prior) is dict and type(prior.get('failures')) is int:
                prior['failure_count_capped'] = prior['failure_count_capped'] or prior['failures'] >= 128
                prior['failures'] = min(128, prior['failures'] + 1)
            return
        value = dict(format=MAKE_IMAGE_DIAGNOSTIC_FORMAT, status='UNAVAILABLE', failures=1,
            failure_count_capped=False, first_refusal_code='shared_make_image_return_differs', observation=None,
            original_strict_failure_preserved=True, make_image_admission_changed=True,
            resource_equivalence_qualified=False)
        self.public_make_image_failure = value
        value['observation'] = self._make_image_return_diagnostic(result, frame, expected_buffer, stored_key, hit)
        value['status'] = 'OBSERVED'

    def _after(self, name, args, result, context, stored_key, hit):
        if name == 'texture_info' and context['probe']:
            self._absent_result(result)
            self._check_absence_state(context['absence_state'])
            if hit is None:
                need(len(self.absences) < MAX_ENTRIES, 'negative_probe_observation_budget')
                self.absences.append(dict(stored_key=stored_key, result=result,
                                          probe_key=context['probe_key'], kind=args[2], arguments=args[:-1]))
            else:
                self.absence_hits += 1
            return
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
            try:
                need(type(expected_buffer) is self.binary_type and
                     any(row['buffer'] is expected_buffer for row in self.buffers) and
                     type(result) is self.image_type and result.buffer_view is expected_buffer and
                     result.mime_type == 'image/png' and result.uri is None and self._return_extensions_ok(result, context, hit) and
                     result.extras is None and result.name == frame['image_name'], 'shared_make_image_return_differs')
            except BaseException as error:
                try:
                    if type(error) is R.Refusal and error.args == ('shared_make_image_return_differs',):
                        self._record_make_image_failure(result, frame, expected_buffer, stored_key, hit)
                except BaseException:
                    pass  # Never replace the original strict failure with diagnostics.
                raise
            if hit is None:
                need(all(event['image'] is not result for event in self.makes), 'shared_uncached_image_alias_refused')
            event = dict(image=result, stored_key=stored_key, source=context['source'],
                         mapping=frame['mapping'], hit=hit is not None, origin=context['origin'],
                         hook_extensions_observed=False, hook_extensions=None)
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
        need(all(self._origin_extensions_unchanged(event) for event in self.makes),
             'shared_missing_or_changed_owned_image_extensions')
        for absent in self.absences:
            self._absent_result(absent['result'])
            current = self.resources._texture_info_request(*absent['arguments'])
            need(current['probe'] and R._same_probe_key(current['probe_key'], absent['probe_key']) and
                 sum(key is absent['stored_key'] and result is absent['result']
                     for key, result in self.specs['texture_info']['entries']) == 1,
                 'negative_probe_retained_absence_changed')
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
                    observed_negative_texture_probe_misses=len(self.absences),
                    observed_negative_texture_probe_hits=self.absence_hits,
                    caches={name: dict(calls=row['calls'], hits=row['hits'], misses=row['misses'],
                                       entries=len(row['entries'])) for name, row in sorted(self.specs.items())},
                    actual_export_or_native_fidelity_qualified=False)
