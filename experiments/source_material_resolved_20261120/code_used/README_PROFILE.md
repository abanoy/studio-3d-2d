# Read-only preloaded native-material path profile

This is the concrete successor to the v2 bare-path compatibility refusal.
It selects no new material, rewrites no B property and opens no material file.
The ordinary SourceIO resolver is given a bounded provider that can recognize
only the independently derived native path of an already inspected actual B
Material. The genuine ordinary lookup then reuses that exact current ref.

Source/test authoring only: this author ran no tests, native parser/assets,
Blender, processes, CIM or Git. Root owns the focused CPU and actual trial.
The base0e material_binding.py and its34 default tests are unchanged. A passing
synthetic result cannot qualify actual SourceIO/B/native/normal behavior.

## API and integration

`ResolvedMaterialPaths(native, material_metadata, mdl, materials, *,
source_material_type, material_type, tiny_path_type, material_domain_supplier)`
accepts the unchanged cbb4/c04 candidates, the freshly parsed genuine MDL,
the exact four native-order B Material refs, genuine API classes and a supplier
of the complete current material-domain tuple. Constructor failures expose
`ProfileRefusal.summary`; successful `witness.summary` returns a safe copy.
All four selected metadata rows are accounted before rejecting missing,
nonstring, foreign or ambiguous full_path values. Oversized full_path strings
are rejected before any matching/casefold; no raw paths/names/refs are public.

Before calling the actual import clone, the host authenticates the genuine
runtime code and binds:

```text
witness.bind_resolver(resolve_model_material, get_model_material_names,
                      get_or_create_material, actual_observed_import_clone)
```

The host passes `witness.provider` as content_manager. Only `.check(TinyPath)`
is supported. `.find_file` or another provider IO method refuses. A True result
means the path corresponds to the selected in-memory Material, **not** that a
VMT exists. No resolver, lookup or importer function is patched by this module.
The initial MDL resolver cache must be absent; only the genuine resolver creates
it. The host proves those functions' complete source/code before binding;
the witness retains/rechecks their exact code/globals/defaults/aliases.

`witness.check(require_resolution=False)` supports initial preflight before
binding and partial resolution afterward. Queries require a bound resolver.
`check(True)` requires the actual complete four-entry cache, exact selected
TinyPath objects and all four actual NativeMaterial.bpy_material refs equal to
the selected B refs. It is used at all four actual engine callback stages,
returned-container checks and final resource checks.

`ResolvedMaterialBinding(native, material_metadata, *, witness, **base_classes)`
keeps the base constructor and all its typed source/skin/model/slot/polygon/
object/ref checks. Its complete _source method is copied from exact0e with only
the bare-path equality replaced by `witness.source_row(...)`. The old actual
name/raw full_path snapshot checks remain. The subclass records actual phase
and returned cache/ref snapshots privately and latches failures as the base
collector does; it performs no geometry reconstruction or metadata repair.

The opt-in returned format is
`has_fresh_sourceio_resolved_material_slot_skin_observation_1`, with
`native_path_witness`, `explicit_read_only_preloaded_path_profile=True`,
`external_material_file_existence_qualified=False` and
`B_material_properties_written=False`. The default bare binder format/behavior
is unchanged.

## Exact native/resolver contract

Candidates preserve the genuine order: bare native material name, then each
nonempty relative native MDL search path joined to that name, with the same
casefolded VMT-query deduplication. The independent c04 names/search_paths and
genuine parsed MDL fields must agree exactly. The B full_path must match exactly
one candidate under the genuine lookup's casefold-then-TinyPath lexical rule.
No guessed directory, suffix stripping, nearest name, first-match ambiguity or
filesystem normalization is added.

TinyPath's Windows equality is case-insensitive while its hash uses raw text.
The witness therefore uses bounded ordered sequences and genuine TinyPath
equality for lookup equivalence, with string query-dedup keys matching the
resolver. No TinyPath-keyed hash table is used. A selected True query must not
belong to another native material's candidate domain. Every selected lookup
must have exactly one matching ref in the whole current material domain.
The domain refs/order and each raw full_path presence/value stay frozen.

The provider records only actual ordered queries. False queries are the known
preceding candidates; True queries are the chosen inspected B paths. Unexpected
order/domain/type, replay, missing/nonstring/conflicting metadata, source ref
substitution, cache replacement/path-ref drift or namespace drift refuses.
It neither prepopulates the MDL cache nor assigns NativeMaterial.bpy_material;
those mutations belong only to the ordinary importer and are observed afterward.

Summary format is `has_finite_native_preloaded_material_path_witness_1`.
It reports scalar metadata/domain/candidate/query/cache/phase counts and flags.
The stable comparison fields are candidate_order_sha256,
native_path_provenance_sha256, current_reference_witness_sha256 (job-local
actual-reference digest) and, after full resolution, resolved_cache_witness_sha256.
The validation-call counters can legitimately increase between nested and final
reports; compare the stable digests/core state rather than every counter.
Normal/resource/point-identity/export/application qualifications remainFalse.

## Primary source and prospective tests

The approved SourceIO fe24260 tree supplies these source pins:

| Source | Bytes | SHA256 |
| --- | ---: | --- |
| library/utils/tiny_path.py |6259|630299955d9becd10021774cf759f2070436c777e4218f8ef016a3c26a11784e|
| blender_bindings/models/materials.py |1940|d0ef0bb1fa338d59b481fd1e12f607feab66606b21ab5d3be53233e734602979|
| blender_bindings/utils/bpy_utils.py |7221|4c8bb4a31ed7cac3278567632673acf53befd84dc852635dff813a20f38332e4|

Pure tests compile those lexical/resolver/lookup source definitions using
fabricated current Material/domain/MDL refs and a small fake import caller.
No filesystem TinyPath method or Material creation/write is allowed. They cover
the concrete prefix-path reuse, all-four refusal diagnostics, global aliases,
missing/nonstring/oversized/foreign metadata, genuine cache/order/actual-ref
observations, substitution/drift, stable digests and all unchanged binder checks.
An AST comparison independently verifies that only the one _source predicate
differs. Actual SourceIO runtime is still a separate Root qualification.

Root-only prospective focused command, in this folder:

```text
python -B -m unittest test_material_binding_default test_resolved_profile
```

No actual success is claimed until Root's fresh bounded ordinary import proves
the provider/cache/ref relation and all original/current-ID/RNA/material/skin/
slot/resource/preservation/private-closure checks. No export is attempted here;
the strict non-NORMAL comparator and2e-5 normal acceptance threshold stay intact.
