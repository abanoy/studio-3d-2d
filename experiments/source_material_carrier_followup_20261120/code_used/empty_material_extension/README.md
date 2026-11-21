# Pinned empty material extensions — explicit opt-in

This successor implements the concrete V8 hook-time facts without widening the default material profile. The old strict material body remains byte-exact as _material_strict. The opt-in copy differs at exactly one predicate: it may recognize six finite empty/default SDK Extension wrappers before the ordinary exporter prunes them. Every other original material, graph, source image, descriptor, cache, shader reachability, slot/reference and serialized-resource guard stays in force.

The verified V8 diagnostic saw one strict material refusal. Its other guard predicates were true, source graph cardinality and positive TextureInfo identity/key matches were1, and repeat counts were0. The sole misfit was six known Extension-like wrappers with empty dictionary payloads. That shape observation did not authenticate their runtime class or required flag. The new opt-in authenticates those additional facts before admission; actual successor export remains unrun. H latch propagation count is not treated as a material hook count.

## Actual API

H.PINS keeps its original17 entries. PinnedSurface gains optional empty_material_extension_module=None. The host supplies its already observed modules['exporter'].gltf2_io_extensions alias. H validates its actual loaded module registration/path, exact1298-byte source pin, module/class identity, plain Extension class shape and original full-module constructor code/defaults/globals. It retains the exact class/method/default/module alias identities and rechecks them. The resulting surface.empty_material_extension_profile is an exact owned H.EmptyMaterialExtensionProfile, never a metadata dictionary or shape-based class substitute. With the binary and extension modules the actual opt-in surface observes19 modules. The old default remains17.

R.SimplePackedResources gains optional empty_material_extension_profile=None. None selects the unchanged strict method. A genuine profile selects the otherwise identical method whose extension predicate admits only exact Extension instances, six finite names, matching wrapper.name, exact empty dict payload and required is False. ChildOfRootExtension, subclasses, dictionaries, arbitrary objects, unknown names, nonempty payloads (including explicit default values), extra/nonstring instance fields, True/0/1 required aliases and runtime class/constructor/module drift remain refused. Strong private wrapper/payload references are retained and rechecked. Ordinary exporter traversal can replace material dictionary values with serialized dictionaries; the observer does not pin those dictionary values and never changes them itself.

After the ordinary export, the parsed final document must have materials as a bounded nonempty list of dicts. Each material's extensions and the root extensions must be absent or exact empty dictionaries. extensionsUsed and extensionsRequired must be absent or exact empty lists. Even a known token mapped to {} in the final JSON is refused. This gate is mandatory for the opt-in route, separate from hook-time admission. Existing nonNORMAL equality and raw unnormalized Euclidean 2e-5 normal checks remain unchanged; the profile does not normalize, correct, relabel or waive a measured normal failure.

The resource report adds the finite profile marker, observed empty-wrapper count, explicit final-absence booleans and extensions_removed_by_this_observer=False. These fields do not claim renderer, complete shader, generic Source, historical saved-B identity or application qualification.

## Primary source and timing

The exact installed io/com/gltf2_io_extensions.py source is1298 bytes, SHA256 a1ee0f0d9eeb2317c9e865d076183628bfbe8bfc95dfdd3e26704db57f345424. Extension has class marker extension=True, constructor(name,extension,required=True), and actual instance fields name/extension/required. ChildOfRootExtension is a separate subclass and is rejected.

The observed six callers explicitly use required=False in these authenticated exporter SOURCE files (SHA256):

- anisotropy.py:45533b8de44b1c6e1f4bc2687a0a86ddd597d3a14c5cf26e39ae4ed7c370bfb9
- clearcoat.py:880eda9bf612180a50fc23ed7b7ad1841d93befcbbcedb42fffb29e578fe1922
- emission.py:41370eae82d68516526a8c7030a391ff129816233761650d27ef04d8bd182252
- ior.py:f871a3a7e1d0cdcfcd65062193804ac3d100158bd435b4b04a8b9d3c5747824b
- specular.py:b882097e499cd7b4f20c86620bb4c842c265527a1e068cfe8096f28833e2604b
- transmission.py:988678afcf44e30b2bfc3ef676c92178d7a96fbdd036c51640a25088c3c6dc47

Pinned materials.py e9660b... dispatches gather_material_hook at158. Pinned export.py d6ae39bf861fc3db7662bc8e7063aadfbe116b8a5de81b40ba027a679f8435a8 traverses extensions then detects/prunes empty unanimated defaults at67–90. No pruning or material/metadata write is performed by this observer. Source links/pins and runtime catalogue qualification remain the actual host's responsibility.

## Controls

The preserved101 controls remain included, not additive with older packets. test_empty_material_extensions.py adds12 source-factory/input/default/runtime ownership controls. test_final_material_extensions.py adds14 independent parsed synthetic-GLB/final resource controls. Expected127 methods:38old+35shared+16negative-probe+12diagnostic+12input+14final. Root alone executes them. The stdlib-only Extension SOURCE is authenticated and executed inside a temporary synthetic module by the pure fixture; no Blender, native asset, NumPy, media buffer, operator or file output is used. These controls cannot qualify an actual exporter run.

Suggested Root command: python -B -m unittest test_export_hook_proposal test_shared_image_cache_proposal test_negative_texture_probes test_material_guard_diagnostic test_empty_material_extensions test_final_material_extensions. Explicit read set: nine local Python files plus installed cache.py, io/exp/binary_data.py, texture_info.py, io/com/gltf2_io_extensions.py. BASES.json identifies unchanged predecessors. Bad unexecuted final-test authoring draft was separately archived by its author; it is not active here.
