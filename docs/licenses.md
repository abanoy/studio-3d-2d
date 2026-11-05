# Component and asset records

Application license/name remain the owner's decision. No installer or engine/encoder
binary is distributed in this source component. No model or texture was downloaded.

| Component | Version actually used | License/source | Use |
|---|---|---|---|
| Godot Engine | 4.6.stable.official.89cea1439 | MIT, https://godotengine.org/license/ | Installed external runtime, rendering/import/UI/GDScript |
| FFmpeg/ffprobe | N-118448-g43be8d0728-20250208 | GPL/version3-enabled installed build; https://ffmpeg.org/legal.html | External H.264/AAC encoder, metadata and decode tests |
| Python | 3.13.1 | PSF license; https://docs.python.org/3/license.html | Installed launcher/test runtime; standard library only |
| Procedural room | source scene3d.gd, generated room.glb | Original geometry generated in this task; app license undecided | Example import fixture |
| Known-tone WAV/cel fixtures | tests/verify.py and tests/app_smoke.gd | Generated simple synthetic data; no third-party creative assets | Timing and raster tests |

Godot's full MIT text is in THIRD_PARTY_NOTICES.md. The installed build also has its
own third-party components/notices; obtain and preserve the full matching engine
notices when packaging an executable. Linking to Godot's license is accepted by its
own guidance, but does not settle every component's redistribution obligation.

The FFmpeg configure banner reports --enable-gpl and --enable-version3. We invoke
that local executable through process arguments, do not copy/link its libraries into
the app and do not assign it an LGPL-only description. Before distributing binaries,
choose a reviewed distribution, retain exact source/build notices and evaluate codec
distribution/patent issues for the intended countries/use. No conclusion here grants
rights to imported models/music or chooses an app license.

Managed scene manifests retain source name and real checksum and mark provenance
unknown / must verify. An imported file's successful loading does not establish its
ownership or redistribution rights. A richer per-asset provenance editor is deferred.

Checked primary sources: [Godot license](https://godotengine.org/license/),
[Godot compliance guide](https://docs.godotengine.org/en/stable/about/complying_with_licenses.html),
[FFmpeg legal page](https://ffmpeg.org/legal.html).

## Optional legacy preparation

The external MMD adapter was tested with installed Blender5.1.2 and MMD Tools4.5.11.
Blender's installed `license/license.md` identifies GPL-3.0-or-later and lists its
dependency notices. MMD Tools' installed manifest/LICENSE identifies GPL-3.0-or-later
and credits the MMD & Blender Team/UuuNyaa/powroupi/sugiany. Neither package nor any
user-supplied model/texture is bundled or committed. Optional-tool records are in
dependencies.json. No legal conclusion about future bundling/linking is made here.

Ragdoll Mover, SMH and SheepyLord's importer were inspected as workflow references;
SourceIO is now used from a pinned optional local cache for Source preparation;
the other workflow references are not installed or invoked. Repository findings and revisions are
recorded in docs/legacy_compatibility.md. Test artifacts keep supplied asset rights
unknown rather than assigning new ownership or redistribution permission.

SourceIO 5.5.5 @ fe24260b97ac03b899d9b5d4f0fd7b34772f3647 is downloaded as a
local development dependency under ignored output/dependencies, not installed into
Blender's profile or committed as application code. Its root license is MIT,
Copyright(c)2020 REDxEYE. Full root license stays with the cache and is reproduced in
THIRD_PARTY_NOTICES.md. Its README credits additional components (including native
decoder support, equilib and datamodel.py); the root MIT notice is not a claim that
every transitive component has that license. Review their included notices/source
before publicly packaging this optional dependency. Blender remains external GPL.
The owner-requested local progress copy includes this private dependency cache;
no public package, installer or third-party creative assets are being published.
