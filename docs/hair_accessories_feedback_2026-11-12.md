# Hair and accessories — deferred owner feedback

Recorded November 12, 2026. Owner instruction: **"Don't work on it yet, just
record it for yourself when you get the option to resume."** Work remains
paused. These are owner-reported problems and requested refinements, not
reproduced findings, implemented changes or new test results.

**Resume update, November 12:** the owner has explicitly resumed work. The
toggle-off restoration defect now has a software fix: isolated old/new comparison
8checks/4failures versus8/0; final fan63, focused8 and import-physics41 checks pass,
including five native models. Body Physics keeps running and cancelled setup
does not dispose its borrowed body. See
[restoration evidence](benchmarks/hair_disable_restoration_2026-11-12.json).
Back hair and the selection/refinement requests remain separate open work.
No owner visual/device approval or complete aggregate is inferred.

Back hair now also has a reviewed **Use existing joints** path, with native26
and ribbon-composition29 checks. It keeps skin/weights unchanged and discloses
the3shared regions affected. See [evidence](benchmarks/back_hair_existing_joints_2026-11-12.json).
This resolves the unavailable-attachment route in software, while direct picking,
multiple selection, blow inclusion and Simple refinements remain open.

## Report and requested behavior

- **Deformation persists after disabling Hair & Cloth:** with a joint configured
  and enabled, deformation behaves as intended while the feature is on. Turning
  "Hair & Cloth" off leaves that deformation in place. The owner expects it to
  return instead of remaining deformed. Record this as a separate toggle-off
  restoration bug; its cause has not been investigated. On resume, restore the
  appropriate authored/current-frame pose when removing live simulation offsets,
  preserving manual posing and any explicitly recorded animation. Do not treat
  this report as a request to delete saved keys or reset the entire model.
- **Joint assignment:** some items will not add to joints. Specific target:
  **Bikini Reimu's Back hair**. Investigate this actual case on resume; existing
  helper-generation tests do not establish that this part works.
- **Automatic choices with correction:** best-effort selection/assignment is
  welcome. Keep single-item selection for precise manual refinement.
- **Local-blow inclusion:** "Try a local blow" helps reveal parts the user wants
  to keep still. Let the user deselect/uncheck unwanted parts from the effect,
  with clear individual inclusion/exclusion. Clarify the relationship between
  editing selection and affected-part membership rather than silently treating
  them as the same thing.
- **Direct 3D picking:** clicking a visible part should try to infer the intended
  hair/accessory item, select it in the panel and leave the guess easy to correct.
- **Multiple selection:** allow selecting more than one item in the relevant
  picker/list and handling them together. Exact gestures and how group editing
  relates to per-item blow inclusion remain design details for the next resume;
  the owner did not prescribe particular keyboard modifiers.
- **Simple-mode refinement:** the owner can see the idea working, but the
  ordinary workflow needs to feel simpler and less jarring. Preserve the useful
  Advanced-mode behavior, which the owner says works fine.

## Next steps, only after an explicit resume

1. Reproduce the Back hair assignment failure using the actual Bikini Reimu
   input in an owned review. Preserve originals, poses and recovery. Trace the
   clicked/selected part, inferred item, offered joints and actual assignment
   before choosing a fix.
2. Refine selection, assignment and local-blow preview around that case, with
   direct picking, multiple selection, per-item correction and clear control
   over which parts respond. Implement in small runnable increments on resume.
3. Verify Back hair assignment, individual and group edits, and unaffected
   excluded parts. Check Undo/Redo, cancellation, saved/reopened assignments and
   the Advanced workflow as relevant to the changes, using private desktops.
4. Reproduce the toggle-off restoration bug: configure a joint, enable Hair &
   Cloth, allow visible deformation, then disable it and compare with the
   expected authored pose at the current frame. Check a non-rest manual pose,
   recorded animation, repeated on/off cycles and re-enabling without accumulated
   offsets. Preserve configured joints, saved animation and other live physics.
   No such checks have been run for this report.
5. Then continue the unfinished aggregate and refresh the separate review.

No implementation, app launch or tests were performed for this report. Ledger
counts and the incomplete aggregate remain unchanged. Do not request further
owner testing while participation is deferred. This note does not resume the
goal or authorize installed-app/tool replacement or changes to original assets.
