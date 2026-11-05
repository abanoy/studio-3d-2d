# Movie quality profiles

**Advanced → Movie encoder → Movie quality** offers three delivery choices:

| Profile | Intended use | Video encoder | AAC audio |
|---|---|---|---|
| Standard (default) | Existing balanced output | libx264 CRF18, fast |192kbit/s |
| Smaller file | Easier sharing, reduced detail | libx264 CRF24, fast |128kbit/s |
| High quality | More detail, larger/slower output | libx264 CRF14, slow |256kbit/s |

Simple Export movie keeps Standard. The profile is captured when export starts,
so changing a setting during rendering cannot change that attempt midway. Project
resolution, rational frame rate, duration, artwork, rendering and synchronized
source audio remain independent. Profiles change final compression, not the
rendered PNG inputs. PNG-only output does not need a valid MP4 quality selection.

After an interrupted or failed encode with complete saved frames/audio, choose a
quality and use **Retry MP4**. It encodes those same inputs into a separately named
file. Previous movies, PNGs and WAV are preserved. An invalid profile refuses
before creating a normal render folder or consuming retry state. Logs include the
profile and exact arguments, and are flushed/closed before completion is reported.

This selection is a session choice for an export operation, like the existing
encoder-location control. It is not saved into scene content or a new project
format. Reopening in a new session starts with Standard. This does not resolve the
addendum's tentative project-versus-personal settings policy or add load prompts.

Run `python tests/verify_export_profiles.py --isolated-display :99` on Linux using
an explicitly provisioned private display and pinned Godot/FFmpeg. Windows keeps
private-desktop receipts. Fresh private llvmpipe checks:17 app +3 cold reader,
real Standard/Small/High encoding, captured selection, API/normal/retry refusal,
cancel Standard then retry High, input/prior-movie preservation, ordinary HAS and
PNG independence. All three movies decode as H2641920×1080/24fps/48frames/2seconds
with AAC; the frame24 cue starts at1.0008958seconds. Encoded frame pixels differ
across quality choices while original renderer input remains exact.

For this original procedural two-second sample, files measured156946bytes
Standard,106544 Smaller file and188363 High quality. First-frame RGB mean-square
errors were10.455,10.950 and10.355 respectively, including color-subsampling effects.
These measurements describe this fixture/build, not universal sizes or a promise
of identical compressed files across encoder versions. Artist quality preference,
native material fidelity and hardware rendering remain separate acceptance gates.
