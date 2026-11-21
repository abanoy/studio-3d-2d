"""UNRUN read-only native-path witness/provider; no IO or Blender import.

An actual host authenticates cbb4/c04 inputs, genuine SourceIO/TinyPath/API
classes and the ordinary resolver/lookup/importer code. B contributes only the
already inspected actual Material refs, never geometry or native point labels.
"""
import hashlib
import json
import types

import material_binding as B
from material_binding import need, tuple_of, MAX_MATERIALS, MAX_MODELS, MAX_PARTS, MAX_MESHES

Refusal = B.Refusal
FORMAT = 'has_finite_native_preloaded_material_path_witness_1'
MAX_DOMAIN = 4096
MAX_PATHS = 256
MAX_CANDIDATES = 4 * (MAX_PATHS + 1)


class ProfileRefusal(Refusal):
    def __init__(self, code, summary):
        super().__init__(code)
        self.summary = dict(summary)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                     allow_nan=False, separators=(',', ':')).encode()).hexdigest()


class _Provider:
    def __init__(self, witness):
        self._witness = witness

    def check(self, path):
        return self._witness._query(path)

    def __getattr__(self, _name):
        self._witness._fail('UNSUPPORTED_PRELOADED_PROVIDER_IO_METHOD')


class ResolvedMaterialPaths:
    def __init__(self, native, material_metadata, mdl, materials, *, source_material_type,
                 material_type, tiny_path_type, material_domain_supplier):
        self._summary = dict(format=FORMAT, status='REFUSED', selected_material_records=0,
            metadata_rows_observed=0, genuine_material_rows=0, full_path_present=0, full_path_missing=0,
            full_path_string=0, full_path_nonstring=0, selected_domain_memberships=0,
            candidate_membership_matches=0, candidate_membership_missing=0, candidate_membership_ambiguous=0,
            global_lookup_matches=0, global_lookup_conflicts=0, native_candidates=0,
            native_material_records=0, domain_material_records=0, provider_queries=0, provider_true=0,
            provider_false=0, cache_materials_observed=0, source_B_refs_observed=0, check_calls=0,
            complete_check_calls=0, phase_observations=0, returned_observations=0,
            preflight_admitted=False, resolver_bound=False, resolution_complete=False,
            returned_binding_observed=False, no_metadata_writes=True, no_material_file_IO=True,
            no_file_existence_claim=True, native_or_historical_point_identity_qualified=False,
            resource_or_normal_fidelity_qualified=False, exporter_invoked=False,
            application_adoption_qualified=False)
        self.failed = False
        self.mdl, self.materials, self.source_type, self.material_type = mdl, materials, source_material_type, material_type
        self.path_type, self.domain_supplier = tiny_path_type, material_domain_supplier
        self.functions = None
        self.cache = None
        self.cache_rows = ()
        self.query_rows, self.phase_rows, self.returned_rows = [], [], []
        self.source_assigned = [False] * 4
        try:
            self._need(type(materials) is tuple and len(materials) == 4 and
                       all(isinstance(value, type) for value in (source_material_type, material_type, tiny_path_type)) and
                       callable(material_domain_supplier), 'EXACT_FOUR_PRELOADED_MATERIAL_API_REQUIRED')
            self._summary['selected_material_records'] = 4
            # Account for ALL four rows before rejecting missing/type/path data.
            self.rows = []
            for material in materials:
                self._summary['metadata_rows_observed'] += 1
                genuine = type(material) is material_type and material.original is material
                if genuine:
                    self._summary['genuine_material_rows'] += 1
                    presence, raw = self._metadata(material)
                    self._summary['full_path_present' if presence else 'full_path_missing'] += 1
                    if presence: self._summary['full_path_string' if type(raw) is str else 'full_path_nonstring'] += 1
                    self.rows.append(dict(material=material, present=presence, raw=raw, name=material.name,
                                          local=material.library is None))
                else:
                    self.rows.append(dict(material=material, present=False, raw=None, name=None, local=False))
            self.facts = B.facts_from_independent(native, material_metadata)
            self._summary['native_material_records'] = len(self.facts['materials'])
            self._need(len(self.facts['materials']) == 4, 'EXACT_FOUR_NATIVE_MATERIAL_FACTS_REQUIRED')
            paths = material_metadata['metadata'].get('search_paths')
            self._need(type(paths) is list and len(paths) <= MAX_PATHS and
                       all(type(path) is str and len(path) <= 1024 and all(32 <= ord(c) < 127 for c in path)
                           for path in paths), 'BOUNDED_INDEPENDENT_NATIVE_SEARCH_PATHS_REQUIRED')
            self.names = tuple(row[0] for row in self.facts['materials'])
            self.paths = tuple(paths)
            self.source_refs = tuple(mdl.materials) if type(mdl.materials) is list else ()
            self._source_table(initial=True)
            self.candidates = tuple(self._candidates(name) for name in self.names)
            self._summary['native_candidates'] = sum(map(len, self.candidates))
            self._need(self._summary['native_candidates'] <= MAX_CANDIDATES, 'FINITE_NATIVE_CANDIDATE_BUDGET')
            self.domain = self._domain()
            self._summary['domain_material_records'] = len(self.domain)
            self.domain_rows = tuple(self._domain_metadata(value) for value in self.domain)
            for row in self.rows:
                self._summary['selected_domain_memberships'] += sum(value is row['material'] for value in self.domain)
            self.selected = []
            for index, row in enumerate(self.rows):
                matches = [] if not row['present'] or type(row['raw']) is not str or len(row['raw']) > 4096 else [
                    candidate for candidate in self.candidates[index] if self._lookup_equal(row['raw'], candidate['lookup'])]
                self._summary['candidate_membership_matches' if len(matches) == 1 else
                              'candidate_membership_missing' if not matches else 'candidate_membership_ambiguous'] += 1
                self.selected.append(matches[0] if len(matches) == 1 else None)
                if len(matches) == 1:
                    global_matches = [entry[0] for entry in self.domain_rows if type(entry[2]) is str and len(entry[2]) <= 4096 and
                                      self._lookup_equal(entry[2], matches[0]['lookup'])]
                    self._summary['global_lookup_matches' if len(global_matches) == 1 and
                                  global_matches[0] is row['material'] else 'global_lookup_conflicts'] += 1
            self._need(self._summary['genuine_material_rows'] == 4 and all(row['local'] for row in self.rows),
                       'GENUINE_LOCAL_ORIGINAL_PRELOADED_MATERIALS_REQUIRED')
            self._need(len({id(value) for value in materials}) == 4 and
                       all(sum(value is material for value in self.domain) == 1 for material in materials),
                       'DISTINCT_CURRENT_DOMAIN_PRELOADED_REFS_REQUIRED')
            self._need(all(type(row['name']) is str and row['name'] == name for row, name in zip(self.rows, self.names)),
                       'PRELOADED_MATERIAL_NATIVE_NAMES_DIFFER')
            self._need(self._summary['full_path_present'] == 4, 'PRELOADED_FULL_PATH_MISSING')
            self._need(self._summary['full_path_string'] == 4, 'PRELOADED_FULL_PATH_NOT_STRING')
            self._need(all(len(row['raw']) <= 4096 for row in self.rows), 'BOUNDED_PRELOADED_FULL_PATH_REQUIRED')
            self._need(all(type(row[2]) is str for row in self.domain_rows), 'CURRENT_DOMAIN_FULL_PATH_NOT_STRING')
            self._need(all(len(row[2]) <= 4096 for row in self.domain_rows), 'BOUNDED_CURRENT_DOMAIN_FULL_PATH_REQUIRED')
            self._need(self._summary['candidate_membership_matches'] == 4,
                       'PRELOADED_FULL_PATH_NOT_ONE_NATIVE_CANDIDATE')
            self._need(self._summary['global_lookup_matches'] == 4, 'PRELOADED_LOOKUP_DOMAIN_ALIAS_OR_CONFLICT')
            # A True key must not make another material stop at the wrong path.
            for index, selected in enumerate(self.selected):
                owners = {owner for owner, candidates in enumerate(self.candidates)
                          if any(candidate['query_key'] == selected['query_key'] for candidate in candidates)}
                self._need(owners == {index}, 'SELECTED_QUERY_AMBIGUOUS_ACROSS_NATIVE_MATERIALS')
            self.expected_queries = tuple((index, candidate) for index, candidates in enumerate(self.candidates)
                for candidate in candidates[:next(ordinal for ordinal, actual in enumerate(candidates)
                                                   if actual is self.selected[index]) + 1])
            self._need(not hasattr(mdl, '_resolved_material_paths'), 'RESOLVER_CACHE_NOT_FRESH_BEFORE_IMPORT')
            self.provider = _Provider(self)
            self._summary.update(status='PREFLIGHT_ADMITTED', preflight_admitted=True,
                candidate_order_sha256=_digest([[row['query_key'] for row in group] for group in self.candidates]),
                native_path_provenance_sha256=_digest(dict(identities=self.facts['identities'], checksum=self.facts['checksum'],
                    names=self.names, paths=self.paths,
                    selected=[(row['path_text'], row['query_key'], metadata['raw'])
                              for row, metadata in zip(self.selected, self.rows)])),
                current_reference_witness_sha256=_digest(dict(mdl=id(mdl), source=[id(ref) for ref in self.source_refs],
                    selected=[id(ref) for ref in materials], domain=[id(ref) for ref in self.domain])))
        except Exception as error:
            if isinstance(error, ProfileRefusal): raise
            self._fail(str(error) if isinstance(error, Refusal) else 'PRELOADED_NATIVE_PATH_API_REFUSAL')

    @property
    def summary(self):
        return dict(self._summary)

    def _need(self, ok, code):
        if not ok: self._fail(code)

    def _fail(self, code):
        self.failed = True
        self._summary.update(status='REFUSED', refusal_code=code)
        raise ProfileRefusal(code, self._summary)

    def _metadata(self, material):
        keys = material.keys()
        self._need(len(keys) <= 1024, 'BOUNDED_MATERIAL_METADATA_KEYS_REQUIRED')
        present = 'full_path' in keys
        return present, material.get('full_path') if present else None

    def _domain_metadata(self, material):
        self._need(type(material) is self.material_type and material.original is material and material.library is None,
                   'GENUINE_LOCAL_CURRENT_MATERIAL_DOMAIN_REQUIRED')
        present, raw = self._metadata(material)
        return material, present, raw if present else '', material.name

    def _domain(self):
        value = self.domain_supplier()
        self._need(type(value) is tuple and 4 <= len(value) <= MAX_DOMAIN and len({id(row) for row in value}) == len(value),
                   'BOUNDED_DISTINCT_COMPLETE_CURRENT_MATERIAL_DOMAIN_REQUIRED')
        return value

    def _source_table(self, initial=False):
        self._need(type(self.mdl.materials) is list and len(self.mdl.materials) == 4 and
                   all(actual is expected for actual, expected in zip(self.mdl.materials, self.source_refs)),
                   'ACTUAL_MDL_MATERIAL_REFERENCE_TABLE_CHANGED')
        self._need(type(self.mdl.materials_paths) is list and all(type(value) is str for value in self.mdl.materials_paths) and
                   tuple(self.mdl.materials_paths) == self.paths, 'ACTUAL_MDL_NATIVE_SEARCH_PATHS_DIFFER')
        observed = 0
        for index, (ref, expected) in enumerate(zip(self.source_refs, self.facts['materials'])):
            self._need(type(ref) is self.source_type and type(ref.name) is str and type(ref.flags) is int and
                       type(ref.used) is int and (ref.name, ref.flags, ref.used) == expected,
                       'ACTUAL_NATIVE_MATERIAL_FIELDS_DIFFER')
            actual = ref.bpy_material
            if initial:
                self._need(actual is None, 'FRESH_SOURCE_MATERIAL_ALREADY_ASSIGNED')
            else:
                self._need(actual is self.materials[index] or actual is None and not self.source_assigned[index],
                           'ACTUAL_NATIVE_B_MATERIAL_REFERENCE_SUBSTITUTED')
                if actual is self.materials[index]:
                    self.source_assigned[index] = True
                    observed += 1
        self._summary['source_B_refs_observed'] = observed

    def _candidates(self, name):
        T = self.path_type
        paths = [T(name)]
        for directory in self.paths:
            if directory:
                path = T(directory)
                if not path.is_absolute(): paths.append(path / name)
        result, seen = [], set()
        for path in paths:
            self._need(type(path) is T and type(path.as_posix()) is str and len(path.as_posix()) <= 2048,
                       'BOUNDED_GENUINE_NATIVE_PATH_CANDIDATE_REQUIRED')
            query = 'materials' / T(path.as_posix() + '.vmt')
            key = query.as_posix().casefold()
            if key in seen: continue
            seen.add(key)
            self._need(type(query) is T and not query.is_absolute() and len(key) <= 2064,
                       'BOUNDED_RELATIVE_NATIVE_MATERIAL_QUERY_REQUIRED')
            result.append(dict(path=path, path_text=path.as_posix(), query=query, query_key=key,
                               lookup=path.as_posix().lstrip('/').casefold()))
        return tuple(result)

    def _lookup_equal(self, raw, expected):
        # Exactly the lookup's casefold-then-TinyPath relation, without its hash
        # mismatch for Windows case-insensitive equality or any filesystem call.
        self._need(type(raw) is str and len(raw) <= 4096 and type(expected) is str and len(expected) <= 4096,
                   'BOUNDED_LOOKUP_FULL_PATH_STRINGS_REQUIRED')
        return self.path_type(raw.casefold()) == self.path_type(expected)

    def bind_resolver(self, resolve_func, get_names_func, lookup_func, importer_func):
        try:
            self._need(not self.failed and self.functions is None and not hasattr(self.mdl, '_resolved_material_paths'),
                       'RESOLVER_BINDING_REUSE_OR_WARM_CACHE')
            funcs = (resolve_func, get_names_func, lookup_func, importer_func)
            self._need(all(type(func) is types.FunctionType for func in funcs), 'GENUINE_RESOLVER_FUNCTIONS_REQUIRED')
            self.functions = tuple((func, func.__code__, func.__globals__, func.__defaults__, func.__kwdefaults__) for func in funcs)
            self._function_aliases()
            self._summary.update(resolver_bound=True, status='RESOLVER_BOUND')
        except Exception as error:
            if isinstance(error, ProfileRefusal): raise
            self._fail('RESOLVER_BINDING_API_REFUSAL')

    def _function_aliases(self):
        self._need(self.functions is not None, 'ORDINARY_RESOLVER_NOT_BOUND')
        for func, code, namespace, defaults, kwdefaults in self.functions:
            self._need(func.__code__ is code and func.__globals__ is namespace and func.__defaults__ is defaults and
                       func.__kwdefaults__ is kwdefaults, 'ORDINARY_RESOLVER_RUNTIME_METADATA_CHANGED')
        resolve, names, lookup, importer = (row[0] for row in self.functions)
        self._need(resolve.__globals__ is names.__globals__ and resolve.__globals__.get('TinyPath') is self.path_type and
                   names.__globals__.get('resolve_model_material') is resolve and
                   lookup.__globals__.get('TinyPath') is self.path_type and
                   importer.__globals__.get('get_model_material_names') is names and
                   importer.__globals__.get('get_or_create_material') is lookup,
                   'ORDINARY_RESOLVER_LOOKUP_IMPORTER_ALIAS_CHANGED')
        actual_collection = lookup.__globals__['bpy'].data.materials
        self._need(4 <= len(actual_collection) <= MAX_DOMAIN, 'BOUNDED_LOOKUP_CURRENT_DOMAIN_REQUIRED')
        actual_domain = tuple(actual_collection)
        self._need(len(actual_domain) == len(self.domain) and all(a is b for a, b in zip(actual_domain, self.domain)),
                   'LOOKUP_CURRENT_BPY_MATERIAL_DOMAIN_DIFFERS')

    def _cache_check(self, complete):
        cache = getattr(self.mdl, '_resolved_material_paths', None)
        if cache is None:
            self._need(not complete and self.cache is None and not self.query_rows, 'ORDINARY_RESOLVER_CACHE_MISSING')
            return
        self._need(type(cache) is dict and len(cache) <= 4 and (self.cache is None or cache is self.cache),
                   'ORDINARY_RESOLVER_CACHE_OBJECT_CHANGED')
        self.cache = cache
        keys = tuple(cache)
        self._need(all(type(key) is str for key in keys) and keys == self.names[:len(keys)],
                   'ORDINARY_RESOLVER_CACHE_DOMAIN_OR_ORDER_CHANGED')
        rows = []
        for index, name in enumerate(keys):
            path = cache[name]
            self._need(type(path) is self.path_type and path.as_posix() == self.selected[index]['path_text'],
                       'ORDINARY_RESOLVER_SELECTED_PATH_DIFFERS')
            self._need(any(owner == index and chosen is self.selected[index] and answer for owner, chosen, answer in self.query_rows),
                       'UNOBSERVED_RESOLVER_CACHE_ENTRY')
            rows.append((name, path))
        self._need(len(rows) >= len(self.cache_rows) and all(a[0] == b[0] and a[1] is b[1]
                   for a, b in zip(rows, self.cache_rows)), 'ORDINARY_RESOLVER_CACHE_PATH_REFERENCE_CHANGED')
        self.cache_rows = tuple(rows)
        self._summary['cache_materials_observed'] = len(rows)
        if complete:
            self._need(len(rows) == 4 and len(self.query_rows) == len(self.expected_queries),
                       'ORDINARY_RESOLUTION_NOT_COMPLETE')
            self._summary['resolved_cache_witness_sha256'] = _digest(dict(cache=id(cache),
                entries=[(name, id(path), path.as_posix()) for name, path in rows],
                matched_B=[id(ref.bpy_material) for ref in self.source_refs]))

    def check(self, require_resolution=False):
        try:
            self._need(not self.failed and type(require_resolution) is bool, 'PATH_WITNESS_FAILED_OR_CHECK_SCHEMA')
            self._summary['check_calls'] += 1
            if self.functions is None:
                self._need(not require_resolution and not hasattr(self.mdl, '_resolved_material_paths') and not self.query_rows,
                           'ORDINARY_RESOLVER_NOT_BOUND')
            else:
                self._function_aliases()
            domain = self._domain()
            self._need(len(domain) == len(self.domain) and all(a is b for a, b in zip(domain, self.domain)),
                       'CURRENT_MATERIAL_DOMAIN_REFERENCE_OR_ORDER_CHANGED')
            for actual, expected in zip(domain, self.domain_rows):
                row = self._domain_metadata(actual)
                self._need(type(row[2]) is str and len(row[2]) <= 4096 and row[0] is expected[0] and row[1:] == expected[1:],
                           'CURRENT_MATERIAL_FULL_PATH_METADATA_CHANGED')
            self._source_table()
            self._cache_check(require_resolution)
            if require_resolution:
                self._need(self._summary['source_B_refs_observed'] == 4, 'ORDINARY_NATIVE_MATERIAL_B_REUSE_INCOMPLETE')
                self._summary['complete_check_calls'] += 1
                self._summary['resolution_complete'] = True
                if not self._summary['returned_binding_observed']: self._summary['status'] = 'RESOLUTION_OBSERVED'
            return True
        except Exception as error:
            if isinstance(error, ProfileRefusal): raise
            self._fail('PATH_WITNESS_CHECK_API_REFUSAL')

    def _query(self, path):
        try:
            self._need(self.functions is not None, 'ORDINARY_RESOLVER_NOT_BOUND')
            self.check(False)
            self._need(type(path) is self.path_type and not path.is_absolute(), 'GENUINE_RELATIVE_PROVIDER_QUERY_REQUIRED')
            text = path.as_posix()
            self._need(type(text) is str and len(text) <= 2064 and len(self.query_rows) < len(self.expected_queries),
                       'FINITE_PROVIDER_QUERY_BUDGET')
            owner, expected = self.expected_queries[len(self.query_rows)]
            self._need(text.casefold() == expected['query_key'], 'PROVIDER_QUERY_OUTSIDE_NATIVE_ORDERED_DOMAIN')
            answer = expected is self.selected[owner]
            self.query_rows.append((owner, expected, answer))
            self._summary['provider_queries'] += 1
            self._summary['provider_true' if answer else 'provider_false'] += 1
            return answer
        except Exception as error:
            if isinstance(error, ProfileRefusal): raise
            self._fail('PRELOADED_PROVIDER_QUERY_API_REFUSAL')

    def source_row(self, source, material, name, full_path):
        self.check(True)
        matches = [index for index, actual in enumerate(self.source_refs) if actual is source]
        self._need(len(matches) == 1, 'SNAPSHOT_SOURCE_MATERIAL_OUTSIDE_ACTUAL_MDL')
        index = matches[0]
        self._need(material is self.materials[index] and name == self.names[index] and
                   type(full_path) is str and full_path == self.rows[index]['raw'],
                   'SNAPSHOT_PRELOADED_REFERENCE_OR_RAW_FULL_PATH_CHANGED')
        return True

    def record_phase(self, phase, model):
        self.check(True)
        self._need(phase in B.PHASES and len(self.phase_rows) < 4 * len(self.facts['models']),
                   'BOUNDED_ACTUAL_RESOLVED_BINDING_PHASES')
        self.phase_rows.append((phase, model, self.cache, self.cache_rows, tuple(ref.bpy_material for ref in self.source_refs)))
        self._summary['phase_observations'] = len(self.phase_rows)

    def record_returned(self):
        self.check(True)
        self._need(not self.returned_rows and len(self.phase_rows) == 4 * len(self.facts['models']),
                   'COMPLETE_ACTUAL_RESOLVED_BINDING_PHASE_COVERAGE_REQUIRED')
        self.returned_rows.append((self.cache, self.cache_rows, tuple(ref.bpy_material for ref in self.source_refs)))
        self._summary.update(returned_observations=1, returned_binding_observed=True, status='RETURNED_BINDING_OBSERVED')


class ResolvedMaterialBinding(B.MaterialBinding):
    def __init__(self, native, material_metadata, *, witness, **classes):
        super().__init__(native, material_metadata, **classes)
        need(type(witness) is ResolvedMaterialPaths and witness.facts == self.facts and
             witness.source_type is self.source_material_type and witness.material_type is self.material_type,
             'EXACT_QUALIFIED_NATIVE_PATH_WITNESS_REQUIRED')
        self.witness = witness

    def _source(self, snapshot):
        material_rows = tuple_of(snapshot['source_materials'], MAX_MATERIALS, 'SOURCE_MATERIAL_SNAPSHOT', 1)
        need(len(material_rows) == len(self.facts['materials']), 'SOURCE_MATERIAL_CARDINALITY_DIFFERS')
        source_refs, placeholders = [], []
        for row, expected in zip(material_rows, self.facts['materials']):
            need(type(row) is tuple and len(row) == 7, 'SOURCE_MATERIAL_ROW_SCHEMA')
            ref, name, flags, used, placeholder, actual_name, full_path = row
            need(type(ref) is self.source_material_type and type(placeholder) is self.material_type and
                 placeholder.original is placeholder, 'GENUINE_SOURCE_AND_NEW_MATERIAL_REFS_REQUIRED')
            need(type(name) is str and type(flags) is int and type(used) is int and (name, flags, used) == expected and
                 type(ref.name) is str and ref.name == name and type(ref.flags) is int and ref.flags == flags and
                 type(ref.used) is int and ref.used == used and ref.bpy_material is placeholder,
                 'SOURCE_MATERIAL_FIELDS_OR_PLACEHOLDER_DIFFERS')
            need(type(actual_name) is str and actual_name == name and placeholder.name == actual_name and
                 type(full_path) is str and self.witness.source_row(ref, placeholder, name, full_path) and
                 placeholder.get('full_path') == full_path, 'NO_MATERIAL_IO_PLACEHOLDER_NAME_OR_PATH_DIFFERS')
            need(all(prior is not ref for prior in source_refs) and all(prior is not placeholder for prior in placeholders),
                 'ALIASED_NATIVE_OR_PLACEHOLDER_MATERIAL_OUTSIDE_PROFILE')
            source_refs.append(ref); placeholders.append(placeholder)
        source_skins = tuple_of(snapshot['source_skins'], MAX_MATERIALS, 'SOURCE_SKIN_SNAPSHOT')
        need(len(source_skins) == len(self.facts['skins']), 'SOURCE_SKIN_FAMILY_CARDINALITY_DIFFERS')
        for actual, expected in zip(source_skins, self.facts['skins']):
            tuple_of(actual, MAX_MATERIALS, 'SOURCE_SKIN_ROW_SCHEMA')
            need(len(actual) == len(expected) and all(ref is source_refs[index] for ref, index in zip(actual, expected)),
                 'SOURCE_SKIN_MATERIAL_IDENTITY_DIFFERS')
        actual_parts = tuple_of(snapshot['source_parts'], MAX_PARTS, 'SOURCE_BODY_SNAPSHOT', 1)
        need(len(actual_parts) == len(self.facts['parts']), 'SOURCE_BODY_CARDINALITY_DIFFERS')
        body_refs, model_refs, mesh_refs, renderable = [], [], [], {}
        for actual_part, (part_name, expected_models) in zip(actual_parts, self.facts['parts']):
            need(type(actual_part) is tuple and len(actual_part) == 3, 'SOURCE_BODY_ROW_SCHEMA')
            part, actual_name, models = actual_part
            need(type(part) is self.source_body_type and type(actual_name) is str and actual_name == part_name and
                 part.name == actual_name and all(prior is not part for prior in body_refs), 'SOURCE_BODY_REF_OR_NAME_DIFFERS')
            body_refs.append(part)
            tuple_of(models, MAX_MODELS, 'SOURCE_MODEL_SNAPSHOT')
            need(len(models) == len(expected_models) == len(part.models), 'SOURCE_MODEL_CARDINALITY_DIFFERS')
            for model_index, (actual_model, expected_model) in enumerate(zip(models, expected_models)):
                need(type(actual_model) is tuple and len(actual_model) == 5, 'SOURCE_MODEL_ROW_SCHEMA')
                model, name, start, count, meshes = actual_model
                expected_name, expected_start, expected_count, expected_meshes = expected_model
                need(type(model) is self.source_model_type and part.models[model_index] is model and
                     all(prior is not model for prior in model_refs) and type(name) is str and
                     type(start) is int and type(count) is int and (name, start, count) ==
                     (expected_name, expected_start, expected_count) and model.name == name and
                     type(model.vertex_offset) is int and model.vertex_offset == start and
                     type(model.vertex_count) is int and model.vertex_count == count, 'SOURCE_MODEL_IDENTITY_OR_RANGE_DIFFERS')
                model_refs.append(model)
                tuple_of(meshes, MAX_MESHES, 'SOURCE_MESH_SNAPSHOT')
                need(len(meshes) == len(expected_meshes) == len(model.meshes), 'SOURCE_MESH_CARDINALITY_DIFFERS')
                for mesh_index, (actual_mesh, expected_mesh) in enumerate(zip(meshes, expected_meshes)):
                    need(type(actual_mesh) is tuple and len(actual_mesh) == 4, 'SOURCE_MESH_ROW_SCHEMA')
                    mesh, raw, start_in_model, vertices = actual_mesh
                    need(type(mesh) is self.source_mesh_type and model.meshes[mesh_index] is mesh and
                         all(prior is not mesh for prior in mesh_refs) and all(type(value) is int for value in (raw, start_in_model, vertices)) and
                         (raw, start_in_model, vertices) == expected_mesh and
                         type(mesh.material_index) is int and mesh.material_index == raw and
                         type(mesh.vertex_index_start) is int and mesh.vertex_index_start == start_in_model and
                         type(mesh.vertex_count) is int and mesh.vertex_count == vertices, 'SOURCE_MESH_IDENTITY_OR_FIELDS_DIFFER')
                    mesh_refs.append(mesh)
                if count:
                    renderable[name] = model
        refs = tuple(source_refs), tuple(placeholders), tuple(body_refs), tuple(model_refs), tuple(mesh_refs)
        if self.source_refs is None:
            self.source_refs = refs
        else:
            need(all(len(a) == len(b) and all(left is right for left, right in zip(a, b))
                     for a, b in zip(refs, self.source_refs)), 'SOURCE_OR_PLACEHOLDER_REFERENCE_CHANGED')
        return tuple(placeholders), renderable

    def observe(self, phase, model, obj, mesh, snapshot):
        try:
            result = super().observe(phase, model, obj, mesh, snapshot)
            self.witness.record_phase(phase, model)
            return result
        except Exception as error:
            self.failed = str(error) if isinstance(error, Refusal) else 'RESOLVED_MATERIAL_OBSERVER_API_FAILURE'
            raise

    def returned(self, container, snapshots):
        try:
            self.witness.check(True)
            result = super().returned(container, snapshots)
            self.witness.record_returned()
            result.update(format='has_fresh_sourceio_resolved_material_slot_skin_observation_1',
                          native_path_witness=self.witness.summary, explicit_read_only_preloaded_path_profile=True,
                          external_material_file_existence_qualified=False, B_material_properties_written=False)
            return result
        except Exception as error:
            self.failed = str(error) if isinstance(error, Refusal) else 'RESOLVED_MATERIAL_RETURNED_API_FAILURE'
            raise
