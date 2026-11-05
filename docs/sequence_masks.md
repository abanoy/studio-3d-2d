# Sequence picture masks

In **Sequences…**, select an instance, enable **Picture mask**, enter left/top/
width/height in child-canvas pixels and choose **Apply mask**. The normal mask
keeps that rectangle. **Cut out this rectangle instead** removes it and keeps
the surrounding picture. Disable and Apply to restore the full child picture.

Coordinates use the1920×1080 child canvas before placement. Rectangles contain
whole pixels, have positive size and must fit inside that canvas. The right and
bottom bounds are exclusive. The mask follows clip movement, rotation, scale
and opacity. Repeated instances have independent masks; copying and splitting
retain their mask data. A mask changes the composited picture, leaving the full
child world, editable drawings, camera and synchronized sound independent.

Masking happens before shadow mip generation, so the shadow follows the cropped
silhouette or cutout, including a feathered shadow edge. Undo of the first mask
restores the previous graph version and full appearance. Apply without a change
adds no history. Disabling restores the full picture while retaining the promoted
format, as with sequence shadows. Invalid rectangles refuse atomically.

The first enabled mask promotes to `studio_sequences_3`, still project schema6 /
HAS container1. Each clip has its existing shadow field plus `mask`: disabled `{}`
or exactly `{"rect":[x,y,width,height],"invert":false}`. Older sequence formats
remain readable and unchanged until opt-in. Readers without graph3 support reject
it explicitly. Whole-number JSON values retain their meaning across reopen; an
unchanged inspector does not convert their representation or add an Undo step.
Shadow edits in graph3 preserve the mask contract.

Source picture caching remains shared across asset instances. A runtime holds at
most4 source pictures and8 derived mask textures, one per clip, alongside its
existing picture/shadow sprite pairs. Masks derive from detached pixels before
premultiplication/mips; derived textures never replace saved source cels. They
are rebuilt at source changes and reused across held frames. These are per-runtime
bounds, not a guarantee for arbitrary project size or hardware VRAM usage.

This first mask tool is a rectangular crop/cutout on a sequence picture. General
painted or lasso drawing-layer masks and animated mask-shape tracks remain future
work. Movie output reveals the parent world through cut regions. Drawing-only PNG
output keeps transparent cut regions and the same masked shadow.

Run `python tests/verify_sequence_masks.py --isolated-display :99` on Linux with
an already provisioned private display and pinned Godot/FFmpeg. Windows keeps
private-desktop receipt checks. Fresh private llvmpipe acceptance:26 app +10 cold
reader, strict source/PCM preservation, actual controls and no-ops, shared-instance
independence, split/copy, packed/linked HAS and recovery, normal close, exact MP4
input and transparent PNG. H2641920×1080/24fps/48frames/2sec +AAC decodes the frame6
cue at0.2508958sec. Manual HAS files remain byte-identical through reopen/recovery.

`python tests/verify_sequences.py --mask-recovery --isolated-display :99` adds a
full-frame mask to the original editable skinned-rig workflow, preserves two
parent backgrounds and then SIGKILLs its writer. Fresh graph106/audio9/storage8/
runtime23/writer48/cold19/startup5 checks pass: ordinary startup restores graph3,
active child/frame, parametric rig, art and audio; graceful hooks did not run and
manual HAS bytes remain unchanged. Decoded synthetic transient onset is
0.2500208sec in that separate fixture. Python290run/289pass/1 independent-MMD-reader
skip also passes, including malformed geometry/version refusal preserving old files.
These are procedural software checks, separate from native Windows/GPU/tablet and
artist acceptance.
