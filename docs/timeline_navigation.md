# Timeline zoom and horizontal navigation

Use **+**, **−** and **Fit** above the timeline ruler. The toolbar zooms around the
playhead; **Ctrl + wheel** over the ruler or tracks zooms around the pointer.
**Shift + wheel** pans horizontally, and the scrollbar chooses the visible range.
The caption shows the visible frame boundaries. Zoom is bounded to a minimum
12frame range (or the whole scene when shorter).

The ruler and all tracks share the same range. Camera and model keys, drawing
holds, animation pieces, sound blocks, waveform positions and trim handles use
that same mapping. Track names stay fixed at the left. A hidden block cannot grab
input through the label column. Clicking a sound label selects its sound without
seeking; clicking the Camera label does not seek into offscreen time.

Entering a distant frame numerically or stepping beyond the visible range reveals
the playhead. Manual horizontal panning stays where it is until the playhead
actually changes or another navigation command runs. Fit shows the whole scene
again, including its editable end boundary. Use Fit for moves across the whole
project; edge-triggered scrolling during an active drag is not implemented.

Zoom and pan are editing views, with no project schema, content/history mutation,
source resampling or new preference file. New, Open, recovery and parent/child
scene changes reset the range to Fit. Floating or docking the Timeline panel
carries its navigation controls with it. Active timeline gestures and export
prevent range changes until they finish. The render/composite path is unchanged.

Sound waveforms retain their existing256bin overview. Zoom changes their mapping,
so closely spaced waveform details remain coarse. This does not add a waveform
resampler, source-sample editor or a mixing desk.

`python tests/verify_timeline_navigation.py --isolated-display :101` runs mathematical
mapping and real GUI checks on an explicitly provisioned private Linux display;
Windows uses the existing private-desktop launcher. It covers late adjacent-frame
clicks, anchored wheel zoom, synchronized panning, fixed-label pixels, one-frame
sound moves/trims and model-piece moves with exact Undo, floating/docking, smaller
scaled windows and unchanged HAS bytes on Open. Existing workspace and animated
channel tests also exercise the shared timeline and an actual1080p H.264 movie.
Native fixture skips are reported separately. These checks use original procedural
assets; they do not establish native import fidelity or physical-device feel.
