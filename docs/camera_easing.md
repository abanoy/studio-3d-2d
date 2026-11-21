# Camera timing

In **Scene / camera**, open **Camera timing / easing…** in the camera controls.
It is available in Simple and Advanced, in both Classic and Neon.

1. Choose a camera key from the frame list. The panel shows the previous and next
   keyframes so you can see which interval each control affects.
2. Set **Arrive (%)** to slow the camera as it reaches that key from the previous
   key. Set **Leave (%)** to start slowly toward the next key. Zero keeps the
   existing timing; 100 gives the slowest start or finish. The first key has no
   Arrive interval, and the last key has no Leave interval.
3. Click **Preview / Recalculate smooth timing**, then scrub or play. Preview
   reads the percentages currently typed into the fields. To stage several keys,
   use **Set timing on selected key** before choosing another key.
4. Adjust and recalculate, or choose **Discard temporary preview** to return to
   the authored camera.
5. Choose **Bake preview into camera keys (one Undo)** when satisfied. This adds
   ordinary camera keys at the affected in-between whole frames. All original
   keys stay intact. Undo restores the original keys; Redo restores the bake.

The preview is temporary. Saving and movie export use the authored camera until
you Bake. A baked result saves and renders through the normal camera track,
without needing the temporary recipe. The recipe is cleared when its project,
camera keys or scene settings change, and after Bake. To try a different recipe
after baking, Undo the bake and reopen the timing panel.

This version works in the parent scene. Stop playback, navigation, live physics
and other active edits before changing timing. A Hold segment needs Linear or
Ease on its starting key before it can be eased. Existing Linear or Ease motion
is retained beneath the timing adjustment.

Bake respects the existing limit of **241 camera keys**. A bake that would exceed
the limit leaves the project unchanged; choose fewer or shorter intervals. The
bake matches preview at integer frames. Subframe matching and editable saved
timing curves are not included in this version.
