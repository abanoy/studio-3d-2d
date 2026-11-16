# Audio projection correction for the fresh SFM review

Source preparation only. **GDScript is UNPARSED and replay execution UNRUN.**
The complete default run at f0dd57a passed separately. No application source,
installed tool, original asset, old review or previous output changed here.

The first final-location replay failed its outer saved-state comparison after
all 41 engine assertions passed. Its process exited 0 without error markers,
and its private desktop/job closed normally. Before, after and extra snapshots
each had exactly one dictionary-key difference: runtime `audio.source` was
included by the observer although it is absent from portable project metadata.
That field contains the **decoded PCM cache**, not an empty/default string.
The failure remains FAILED; successful engine assertions do not relabel it.

`src/audio_track.gd` makes the boundary explicit: `document()` returns runtime
clips; `metadata()` constructs portable clip records without decoded `source`.
The corrected observer copies every authored field unchanged and removes only
that runtime cache from the portable projection. It does not regenerate saved
timing/gain/name/SHA fields from the cache or hide arbitrary mismatches.

Before removing that cache from each observed document, three independent
phase checks bind it at **before**, **after** and **extra**:

- Exact seven-field decoded-source shape and original clip identity/order.
- The managed WAV path in the newly owned unpack cache and exact file SHA256.
- Exact original display name, channels, sample rate and frame count.
- Decoded PCM length/SHA256 matching an independent Python `wave` read of the
  SHA/CRC-verified WAV member inside the original packed package.

The Python driver independently checks the reported file/PCM/sample proof
against its package-derived reference. Neither the helper nor this packet
extracts, copies or publishes audio. The strict original `1e-12` absolute JSON
comparison, dictionary keys/order, strings, booleans, saved native controls,
pixel checks, all named checks, process/private isolation and preservation
gates remain. Three additional common checks per four packages change the
**proposed** total from 168 to **180**; no runtime total has been observed here.

`CPU_AUDIT.json` records actual read-only diagnosis: each of the three retained
states differs only by this cache; after that precise portable projection the
entire authored document compares exactly. All three file/PCM/sample references
match. Twenty-seven cache negative controls (wrong SHA/path/name/rate/channel/
frame/extra field/file digest/PCM bit) and nine authored timing/gain/mute changes
are refused. These are CPU checks, not an engine parser or replay pass.

First-failure logs, comparison, process/private receipt and aggregate failed
verification are retained in `first-failure`. The old observations contain PCM
and remain LOCAL; this packet stores only their byte counts and hashes. No PNG,
WAV, GLB, HAS, private model coordinates or decoded PCM appears in this packet.

## Root sequence after independent source review

1. Verify that the old replay's exact processes/jobs closed. Retain the old
   `HAS-Review-20261115-SFM-Joints-f0dd57a` and its generated files unchanged.
2. While HEAD remains the exact tested f0dd revision, use `builder/command.json`
   to create the fresh sibling
   `C:\a\Programming\cloudflare\HAS-Review-20261115-SFM-Joints-f0dd57a-replay2`.
   The only builder code change is that exact new target name. Input/runtime/
   native locks, immutable snapshot and EOL/preservation gates remain intact.
3. Review the produced build, then grant a fresh separate root private runtime
   lease before invoking `replay/command.json`. No authority comes from this
   packet. Root must record real coordinator identity, parser/runtime outcomes,
   private closure and exact observed counts. Any failure stays separate.
4. Publish reviewed source, compact actual results and limitations; verify
   retrieval before considering any separately authorized disposable cleanup.

`ORIGINS.json`, logical source diffs and `INDEX.json` bind the preparation.
`prepare_successor.py` reproduces the original one-time source transformations
only into fresh paths and refuses existing files. It is not an app runner.
`audit_audio_contract_cpu.py` reproduces the bounded diagnosis using retained
private inputs and writes only hashes/counts. The source catalog does not claim
new Source dynamics, artist approval, listening/tablet evidence or clean install.
