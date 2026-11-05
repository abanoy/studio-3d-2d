# Home and recent projects

Normal launch first attempts the existing newest-valid recovery. A recovered
unsaved scene goes straight to editing. Otherwise Home appears over a clean empty
New world. If recovery could not open any candidate, Home retains the quiet failure
message. It does not open a second splash window. The top Home button returns here.

New scene uses the ordinary unsaved-edit confirmation and opens the black empty
world with fading grid/free camera/no selection. Open project uses the ordinary
HAS picker and validation. Return to scene or Escape keeps current data, view and
frame. Opening Home stops playback and finishes active editing gestures, without
creating a separate project or resetting completed edits. Covered-scene shortcuts,
painting and asset drops do not edit behind Home. Controls support keyboard focus.
An active physics recording keeps its workspace/Stop controls visible; finish
recording before opening Home. Unrecorded live physics is not silently frozen.

Recent projects lists up to12 successful normal HAS saves/opens, newest first.
Windows case differences deduplicate. Backups, failed/canceled opens and automatic
recovery do not enter this list. Removing a row changes only preferences, never
the HAS or its assets. Missing files remain visibly unavailable; Open project can
choose their moved location. A failed open stays on Home with feedback while the
old scene remains intact. Native file/worker dialogs remain the existing ones.

When an exact matching recovery revision already has a validated256x144 preview,
Save can reference that managed thumbnail. The preview represents the last recovery
view, which can include a temporary editor camera. It is not a final-film rendering
or file-content identity check. Missing/pruned/corrupt previews fall back to the
original scene icon; they never prevent project opening. Open validates the actual
HAS as before. Thumbnail references are accepted only directly under the current
managed recovery root, with existing hash/PNG-size/dimension checks.

Personal recent metadata is `output/recent-projects.json` beside the normal recovery
root, outside scene/HAS content. It has a version, quiet bounded64KiB JSON reading,
twelve-entry retention and flushed temporary-file/rename writes. Long rows evict
older entries to stay within the size bound. Corrupt/unknown metadata shows an empty
list; a failed write preserves the prior file. There is no recent-list backup,
cross-instance locking, content-identity guarantee for stale thumbnails or dynamic
filesystem watcher. Reopen Home to refresh availability. Automated smoke launches
use separate preference files; explicit test roots isolate normal-startup observers.

Home is a partial implementation of addendum2.1. The course browser/Tutorials entry,
real supplied practice scenes, observed steps/hints, whole-scene Previous checkpoints
and tutorial resume are still required next. There is no placeholder tutorial button.
Tutorial Skip remains OPEN. This screen does not replace the existing editing shell.

`python -u tests/verify_home.py` drives real saves/opens, dirty confirmations and
cancel, actual picker filters, bad/missing files, metadata failure/bounds, a real
thumbnail, original HAS/GLB hashes, twelve valid packed projects/last-row scrolling
and editable reopening. Two fresh ordinary scene launches inherit production
`_ready` unchanged, observing clean Home and valid recovery priority without calling
the recovery method manually. All windows stay on private Windows desktops. See the
latest progress memo for actual completed source/saved-copy checks and limitations.
