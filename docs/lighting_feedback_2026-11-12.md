# Lighting direction and shared illumination — deferred feedback

Recorded November 12, 2026. Work remains paused. Only requested public-reference
research and documentation were performed; no app changes, installs, launches
or rendering tests. The following is future work, not current HAS capability or
a new acceptance result.

## Owner's priority: illuminate models as well as the map

The owner especially likes RTX-style bounced/reflected illumination reaching
**items and character models**, rather than lighting only the map. Treat that
as the central visual goal: characters, their hair/accessories, props and the
environment should respond coherently to their shared scene illumination in
the selected lit style. For example, a nearby lit red wall should be able to
tint white clothing through bounced light. A glossy reflection is a related
but different effect; adding bloom or a map-only lightmap does not satisfy this.

Separate receiving indirect light from contributing to it: models receiving
the environment's bounce is the explicit priority. Fully dynamic model-to-map
and model-to-model bounce is a more demanding quality goal to evaluate, not a
claimed feature. Preserve deliberate Unshaded behavior and authored animation.

## Requested appearance/control references

- Owner's later proposed range: **flat light, simple light, GMod-like,
  MMD-like and RTX-like lighting**. Preserve these as requested appearance
  choices; do not assume the current Unshaded/Lit/Studio modes implement them
  all. The owner is unsure whether SFM has a default lighting style; no SFM
  default or preset has been established by this report.
- **GMod-style and MMD-style lighting**: retain the owner's terms as future
  directions. These involve material/shader response as well as light controls;
  exact native appearance is not established by a preset name.
- **"Raycasting lighting"**: possibly refers to Ray-MMD/Raycast rather than a
  specific ray-tracing algorithm. Do not silently resolve that ambiguity. The
  [Ray-MMD project](https://github.com/ray-cast/ray-mmd) describes a DirectX 9
  shader-based PBR extension with soft shadows, environment lighting and
  screen-space effects, so it is a useful non-RTX appearance reference.
- **[Advanced Light Entities](https://steamcommunity.com/workshop/filedetails/?id=493751477)**:
  the author's description lists shadowed and inexpensive point lights,
  projected lights and spot lights, editable properties/color/projection
  textures, and control over shadow updating. Use as a light-editing reference;
  the page does not describe a global-illumination renderer. Its Source-specific
  shadow-texture restrictions are not a HAS design requirement.
- **[Xenthio/garrys-mod-rtx-remixed](https://github.com/Xenthio/garrys-mod-rtx-remixed)**:
  explicitly supplied as the shared-illumination example. Its current README
  lists runtime PBR material conversion, hardware skinning for HL2 RTX assets
  and Remix integration. It now marks the project deprecated and directs users
  to [SourcePT](https://github.com/sambow23/SourcePT), whose README describes a
  Source shader-API/D3D9 wrapper submitting rendering to OpenRemix. These are
  renderer/material/model integration references, not evidence of a simple
  portable lighting toggle or a non-RTX fallback. No runtime was installed and
  no project was audited or tested for fidelity/hardware compatibility.

Keep the NVIDIA brand distinction separate from ray-tracing capability:
[NVIDIA's Remix runtime requirements](https://docs.omniverse.nvidia.com/kit/docs/rtx_remix/1.2.4/docs/introduction/intro-requirements.html)
specify an RTX GPU. The successor
[OpenRemix](https://github.com/OpenRenderCollective/OpenRemix) describes
vendor-agnostic path tracing, but that does not establish compatibility with
arbitrary GPUs lacking ray-tracing support. Its exact Windows hardware boundary
was not established here. These references do not prove a ready-made non-RT
backend for HAS.

## Feasibility without RTX — research, not a benchmark

An RTX-like appearance is feasible without RTX hardware; exact quality and
speed depend on scene, technique and GPU. Godot's
[GI comparison](https://docs.godotengine.org/en/4.6/tutorials/3d/global_illumination/introduction_to_global_illumination.html)
describes baked GI, VoxelGI, SDFGI and screen-space indirect lighting. SDFGI
lets dynamic objects receive GI but does not treat them as dynamic contributors;
VoxelGI supports dynamic contributions within its own approximation limits.
Avoid claiming that all skinned/native materials will work without adaptation.

[LightmapGI probes](https://docs.godotengine.org/en/4.6/tutorials/3d/global_illumination/using_lightmap_gi.html#dynamic-objects)
can give moving objects baked indirect light, providing a route beyond map-only
lighting. This is not fully updating bounce from moving lights or geometry.
Lightmap baking also needs an authoring pipeline; it is not simply a runtime
checkbox in the shipped application.

[Screen-space reflections](https://docs.godotengine.org/en/4.6/tutorials/3d/environment_and_post_processing.html#screen-space-reflections-ssr)
need other reflection sources for things outside the visible screen. Probes and
voxel approximations have their own accuracy and performance limits; they do
not establish path-traced parity in animated scenes. Do not promise a percentage
of RTX quality, frame rate or 4K performance without actual measurements.

HAS currently sets `renderer/rendering_method="gl_compatibility"` in
`project.godot`. Godot's
[renderer matrix](https://docs.godotengine.org/en/4.6/tutorials/rendering/renderers.html)
places VoxelGI, SDFGI, SSIL, SSR and volumetric fog in Forward+. An optional higher
quality rendering path therefore needs real engineering and validation; these
features are not already exposed by HAS. The
[hardware requirements](https://docs.godotengine.org/en/4.6/about/system_requirements.html)
do not require RTX for Forward+, but minimum engine support is not a heavy-GI
performance guarantee.

## On an explicit resume

### Render quality versus real-time preview

Owner explicitly emphasizes **rendering to video**: demanding lighting may be
too slow during real-time editing, but final export can spend longer rendering
each frame. Keep output playback timing tied to the intended frame rate rather
than the wall-clock speed of generating frames. Explore economical preview
settings and a more demanding final lighting/render quality setting, with a
way to inspect the intended final appearance before exporting. Slower export
does not remove memory limits or automatically create a path-tracing backend.

Distinguish scene-render quality from encoder compression. Existing
[movie quality profiles](export_profiles.md) change compression while keeping
the renderer's PNG inputs identical; they do not add GI or improve light-bounce
accuracy. The existing [PNG sequence timing contract](png_export.md) and
[output-size controls](output_size.md) should inform future work. Preserve
synchronized sound, camera/physics/animation sampling and independent drawing
layers when spending longer per frame. No slower-quality lighting mode or
preview/export switch was implemented or tested for this feedback.

Design light editing and material/style choices separately from rendering-quality
choices. Evaluate a responsive preview and potentially slower high-quality final
render; do not silently add a new renderer dependency. First demonstrate shared
lighting on a native skinned character and props next to a colored wall, including
motion, shadowed areas and hair cutouts. Check light changes, off-screen influences,
preview/export agreement, project persistence, independent 2D layers and source
preservation. Document limitations and measure quality/performance before choosing
a technique. Keep Simple controls approachable and advanced parameters optional.

No goal resumption, implementation commitment, installation authorization or
ledger-count change follows from this note. Existing deferred bugs remain pending.
