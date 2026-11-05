# Simple body names and Advanced internal names

Simple uses familiar names in both the tree and expanded timeline: **Left hand**,
**Pelvis**, **Mouth**, **Left index finger 1**. Advanced shows the body name beside
the exact internal name; hover additionally reveals the binding ID. Switching modes
refreshes labels without changing selection, filters, poses, camera, pixels or Undo.
Simple tooltips omit internal names and IDs.

The local UTF-8 vocabulary `data/bone_names.en.json` covers common Japanese parts,
exact ValveBiped/SFM/English aliases and declared VRM humanoid roles. Side and numbered
segments remain distinct. Search accepts standard names, descriptive estimates and
original names. A VRM role can label an otherwise opaque internal node name.
Unknown bones say **Other part** in Simple; Advanced reveals their source names.
Duplicate body labels remain separate selectable bones. This conservative vocabulary
does not certify anatomy or determine IK bindings.

Native skeleton names, binding IDs, pose keys, parameter reports, source GLBs and
HAS data stay unchanged. Identical display labels never become object/bone identity.
To extend the vocabulary, add a known exact alias/part/role in the JSON file, then
restart Studio. No online service or extra package is used.

Tests cover English/native search, role mapping, live mode switches and timeline
cache refresh, skin posing/native keys, identical pixels and packed HAS reopen.
Optional actual Miku and native IK samples retain source hashes. Physical mouse feel,
all rigs/languages and native anatomy are not certified by vocabulary tests.
