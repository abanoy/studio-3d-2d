# Optional orbit camera navigation

The default remains the existing GMod-style camera scheme. To change it, turn on
**Advanced**, open **Settings**, and choose **Orbit around selection** under
Camera controls. You can return to Simple afterward; this is a personal interface
preference, not another scene engine or a project setting.

- **Ctrl + left drag:** orbit the selected object while keeping its screen
  position and camera distance stable.
- **Ctrl + right drag:** pan the temporary view.
- **Ctrl + wheel:** move nearer/farther without changing FOV. It also works during
  an orbit drag without losing that gesture.
- **Escape, focus loss, or releasing Ctrl:** release the captured mouse.

Ordinary selection/context clicks, Alt bone reveal, middle-click Move/Rotate
switching and the existing unmodified camera gestures remain. WASD translation
is suspended during an orbit/pan gesture; normal fly movement retains its prior
behavior. The modifier scheme deliberately keeps Alt available for bones; these
are orbit-style controls, not a claim to copy Blender's complete keymap.

The pivot uses the selected object's pose-aware world bounds, including a posed
skinned model or a group. The existing bounded geometry query applies; if it has
no usable mesh result, the selected root position is used. With no selection,
each new gesture uses a point five scene units ahead. A target too close to the
camera refuses with framing guidance. The pivot stays fixed during an orbit
gesture; pan moves the temporary pivot with the camera. Large pitch gestures are
prevented from crossing the vertical pole. Camera roll is retained, finite input
is required, and the basis is kept orthonormal. Normal near/far clipping remains.

This only changes the temporary editor camera. Shot keys still require explicit
Save camera key, model/bone auto-keying is unchanged, and rendering continues to
sample the authored shot. Saving/Open/New does not replace the navigation choice.
The choice is stored beside UI scale in the personal display configuration.
Updating either field loads the current file first, preserving the other setting
and unrelated configuration entries. There is no HAS/model format change.

## Verification

`python tests/verify_orbit_navigation.py` uses a separate test preferences file
and hidden Windows desktops. It checks the fly default, actual routed Ctrl
gestures, stable target/radius, repeated basis stability, pan/dolly/combined
wheel, pole limits, Escape/Ctrl/focus release, finite-input guards, Simple/Advanced
visibility, Alt, middle-click, unchanged keys/model/history and unchanged final
shot pixels before/after navigation and packed HAS reopening. A real packed
posed Miku case checks native-model orbiting without joint/key edits. A fresh
process restores the orbit and125% scale settings and an unrelated preference.

The native case requires the retained joint-authoring Miku project or an explicit
`--native-project` packed scene containing it; vendor data is not bundled with
source. The previous scene's checksum is verified unchanged. Headless parse checks
precede graphical work to catch script errors promptly. These are injected app
events, not physical mouse, arbitrary DPI or artistic comfort acceptance.
Existing workspace and camera-range regressions are separate; their actual run
and checkpoint status is recorded in the dated progress memo.
