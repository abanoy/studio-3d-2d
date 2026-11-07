# Basic and Advanced course browser

Home → Tutorials opens Basic first. **Start here → Your first movie** is the full
beginner route; **Drawing and posing → Pose and draw** is a focused practice.
Advanced provides topic entry points under **Camera and rendering**, **Animation
and posing**, and **Physics**. Each topic explains what its practice covers.
Both tabs scroll within the available window height.

| Section | Existing practice |
|---|---|
| Basic / Start here | First movie: ordinary map/model import, selection, camera, bones/auto-key, physics, drawing, timeline and render; optional personal Save |
| Basic / Drawing and posing | Pose and draw |
| Advanced / Camera and rendering | Camera shots; Lighting and export |
| Advanced / Animation and posing | Interpolation and cuts; Rig posing and foot constraints |
| Advanced / Physics | Physics recording |

A topic starts its existing validated practice at its first task. It does not
skip a task or synthesize a mid-course scene. Continue, Start fresh, finished
practice and Saved practices keep their existing versioned identities and
checkpoint contracts. Unsaved-edit replacement still asks through the ordinary
confirmation. Browsing and changing tabs leave the current scene/history intact.
The included original assets stay offline and unchanged.

This reconciles the browser with addendum12.1: a logical Basic route and optional
focused Advanced sections. Rig posing/constraints is supported practice; this
browser does not create a new rig-authoring or weight-painting course. Further
course depth, teacher demonstrations, retention and novice/physical-device
acceptance are tracked separately. Tutorial Skip remains OPEN.

Reproduce using an owned private display and activated pinned tools:

```sh
python tests/verify_tutorial_catalog.py --isolated-display :107 --output /absolute/new/result
```

The browser verifier checks actual Home entry, Basic/Advanced and named sections,
all seven stable course IDs exactly once,1100×700 fit, unchanged scene/history
while browsing, actual topic startup, unsaved-edit confirmation/cancel, saved
Continue, beginner entry and original source hashes. It also runs the existing
focused and full first-movie verifiers for real state grading, Previous,
fresh-process Continue, input controls, ordinary HAS, movie/audio and encoder
cancel/retry. Screenshots are captured from the private test window.

Evidence: [course-browser receipt](benchmarks/tutorial_catalog_2026-11-06.json).


Fresh results:17 browser,52 focused writer+5 fresh reader,79 beginner writer+8
fresh reader checks pass. The beginner run exposed a real guide-card overlap;
edge-aligned candidates now preserve the28px joint marker plus4px clearance.
The existing overlap assertion is unchanged. No source asset or lesson identity
changed. The receipt maps these results to COURSE-01 acceptance.
