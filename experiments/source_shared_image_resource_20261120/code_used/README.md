# Explicit shared-Image cache observation proposal

Source preparation only. This author did not execute tests, Blender, native
assets/parsers, processes, CIM, Git or an exporter. Root will run the CPU suite
after its separate native job is physically closed. Actual shared-resource
export, strict semantics and normal fidelity remain unrun/unqualified.

The earlier RNA resource proposal's exact sources/tests are retained under
`bases/rna_v2`; its published18-file source/38-test packet is separately retained
under `bases/published_rna_v2`. Those predecessors are unchanged. The38 original
tests are also copied byte-exact at the top level. A passing predecessor test
receipt is not a result for this successor.

## Why an opt-in successor

Root completed inspector2's narrow material-only observation: four native-order
Material graphs reached two genuine Images/two shared references,1709130 packed
bytes and83886080 prospective RGBA-F32 bytes, with one exact owned-source Library
verified. Root confirmed exit0/reaped,35 preservation checksTrue and physical0.
That was not an exporter/cache result. A separate combined fresh-native-ID +
owned-resource no-export binding job is still the next actual prerequisite.

The old default profile continues to reject source Image sharing. This proposal
adds `allow_shared_images=True` only when the future actual host supplies the
extra explicitly source/runtime-attested cache surface. It never infers shared
identity from names, matching bytes, hashes, source IDs copied from B or output.

## Public API and source pins

```text
resources = SimplePackedResources(materials, unique_image_tickets,
    bpy_types, search_module, encode_module, gltf_module,
    allow_shared_images=True)
surface = PinnedSurface(the_original_17_modules, observer_module, binder_module,
    shared_binary_module=actual_io_exp_binary_data_module)
session = ExportHookSession(surface, admissions, numpy_module, resources,
    independent_current_point_admission, exact_export_options)
```

Default `allow_shared_images=False` keeps the previous unshared profile and
receipt format strict. Non-boolean flags refuse. A shared resource cannot use
early descriptor hooks, finalization or an actual session without its explicit
cache observer; source sharing alone does not authorize hook reuse.

All original17 exporter pins remain exact. The additional module is
`io/exp/binary_data.py`,1123B, SHA256
`ed6e29b6557522b6a056a9bb1e3a0b6a8fffe250e9d0afdf47f7f2eef2447dcf`,
already present in the immutable120-file catalogue. PinnedSurface checks its
module aliases and actual __init__/__eq__/__hash__ code/globals/defaults, class
shape and plain-instance fields. It checks identity-only search NodeSocket and
ExportImage keys, glTF equality, and exact cold cached wrappers/closures/key
functions for gather_image, __make_image, __gather_buffer_view, __gather_uri,
gather_texture and the texture-info helper. It never clears/preloads a cache
to manufacture a miss or changes an exporter key.

The new stdlib-only `shared_image_cache_proposal.py` performs no IO/import of
Blender/NumPy/exporter and invokes no operator. Only the actual host's
PinnedSurface-created specifications belong in an actual operation. Synthetic
specifications cannot qualify runtime/native/export facts.

## What is observed

The installed primary cache implementation keys by actual arguments excluding
settings. Ordinary Python search NodeSocket wrapper identity is preserved in
that key, while source RNA provenance retains the existing typed owning-ID/C
pointer rules. ExportImage descriptors remain distinct per body-created socket
binding. BinaryData equality/hash use encoded bytes, so __make_image can
legitimately return the first glTF Image for a later distinct descriptor.

The observer therefore separates unique glTF Images from per-socket bindings:

- One ticket per unique genuine source Image; every material/tree/socket graph
  remains independently admitted. Every planned color/optional-Alpha key must
  be covered exactly once. The default source-sharing rejection is retained.
- The old unique-ticket encoded/PNG/prospective-decoded budgets remain before
  any ImBuf getter. The shared profile additionally charges every planned
  binding's encoded cost, capped at the same128MiB limit. Live actual BinaryData
  buffers are retained/bounded and must match the exact source packed length/
  SHA256 with bufferViewTarget=None.
- Every incoming cache argument is admitted before any key equality/hash:
  actual source wrappers/descriptors, exact strings/settings and the active
  actual BinaryData object. Unknown objects/subclasses never reach the primary
  BinaryData.__eq__, which otherwise reads other.data. Runtime method/code/
  globals/defaults/class-access and BinaryData instance-field descriptors are
  rechecked before retained data reads and lookup.
- Actual cache dictionaries, key objects, values and settings identity are
  read-only observations. Exact dictionary size is bounded before either
  items-list snapshot. Unknown/warm/replaced/extra entries refuse. A genuine
  read-only dictionary lookup must agree with the observed key. A miss adds
  exactly one own key/result; a hit retains the exact prior mapping/value.
- The active genuine gather body must produce its early complete descriptor,
  GLB URI observation, bounded pinned BinaryData, then one __make_image event.
  A hit must trace to the same actual source Image ID and full channel mapping.
  Equal bytes on distinct source IDs do not authorize a merge. The cached glTF
  Image keeps the first stored BinaryData object; this is explicitly checked
  against the actual stored key rather than the newer equal argument.
- Each image hook consumes exactly one new active-body make event. A repeated
  hook, missing/event-less hook, foreign/context-changed descriptor, second
  canonical graph gather or unsupported composition refuses. A genuine outer
  cache hit reuses its observed return without inventing another body/hook.
- Texture/TextureInfo/material ownership and uniqueness stay strict. Shared
  source Images do not grant shared material or sampler/context ownership.
  Once references begin, all planned graph bindings must be complete and no
  further gather call is allowed. Unique root-resource indices and serialized
  texture/material incidence retain the old collision/reassignment checks.

Every observer failure remains unqualified, including caught failures;
shared finalization failures cannot be retried into success. Existing session
failure latching still handles swallowed extension exceptions. Six additional
memory-only patch slots use the existing exact owned restoration/partial-install
policy; foreign writers are not clobbered. The genuine original exception stays
the primary exception, including an observer stack failure.

No complete shader evaluator, arbitrary cache warm-up, image recomposition,
UDIM/WebP, texture-coordinate copy, external path retrieval, names-based source
join or source-normal reconstruction is added. All old graph/image/profile
checks still apply; an actual material can correctly refuse another gate even
after this sharing rule is independently qualified.

## Tests, outputs and remaining actual gates

There are73 authored methods: the original38 unchanged plus35 new methods.
The new pure tests read exactly the two source-pinned primary cache.py and
BinaryData source files, execute stdlib-only cache definitions and compile the
BinaryData class AST with a fabricated annotation enum for an unused method.
All source graph/Image/glTF data and hooks are fabricated; no image is decoded,
no Blender/API/operator/native file is loaded and no current point identity is
qualified. They exercise actual primary byte-key cache behavior plus independent
ownership, cross-count, getter-order and failure oracles.

The added cases cover legitimate4graph/2Image sharing with distinct descriptors,
unshared baseline, genuine outer hits without hooks, different source IDs with
equal bytes, cold/warm/replaced/extra cache states, foreign getter/equality/hash
traps before admission, length guards before allocation, complete mapping/key
coverage, source/encoded pins, runtime method/class/field-descriptor mutation,
missing/replayed hooks, settings identity, preserved exceptions, repeat budgets,
final indices/serialization, swallowed failures and partial-slot restoration.

Root-only prospective CPU command, from this directory:

```text
python -B -m unittest test_export_hook_proposal test_shared_image_cache_proposal
```

After source/CPU qualification, a separately reviewed actual host still must
consume the qualified combined current-ID/material relation, run one admitted
ordinary exporter with complete source/runtime/options/private/preservation/
closure proofs, and check all cache/hook/final-root observations. Shared counts
are derived from actual graph/key incidence, not assumed from a synthetic4/2
scenario. This proposal includes no such host or native export receipt.

Its new shared resource report is
`has_narrow_shared_actual_resource_reference_observation_3`, containing unique
source/image/texture/material counts, per-socket binding counts, six cache
hit/miss/entry counts and bounded encoded byte totals. All keys/objects/names/
pointers/packed bytes remain private. Its actual-export/native-fidelity flag
remainsFalse. Existing overall normal/non-NORMAL/app flags remainFalse too.

The strict non-NORMAL comparator and unchanged2e-5 independent normal gate remain
mandatory subsequent actual checks. No exporter observation is itself fidelity
or application adoption. Source lineage/diff and exact source pins are recorded
in BASES.json, SOURCE_DIFF.md and SOURCE_PINS.json.
