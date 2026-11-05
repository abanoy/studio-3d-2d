# Personal keyboard shortcuts

Settings → Keyboard shortcuts is available in Simple and Advanced. Click an
action's current shortcut, then press a key with optional Ctrl and/or Shift.
Changes save immediately. Clear leaves the action unassigned; its normal button
still works. Restore default shortcuts restores all fifteen existing defaults.
Escape cancels capture first; with no capture active it closes the panel.
Closing or leaving the panel also cancels unfinished capture.

Actions: play/pause, previous/next/first/last frame, Undo, Redo and its alternate,
Save, pen, eraser, fill, color sampling, drawing selection, and explicit camera
key insertion. Duplicate assignments refuse with the conflicting action's name;
clear or change it first. Main drawing choices, camera key, transport and
Save/Undo/Redo hints use the effective bindings.

These are logical Latin keycodes, matching the pinned Godot keyboard convention,
not physical keyboard positions. Supported: letters, digits, F1–F12, navigation
keys and common punctuation, optionally Ctrl/Shift. Modifier matching is exact.
Escape, Tab, Enter, Alt/Windows combinations and modifier-only assignments are
reserved. Mouse controls, WASD free-camera motion, Shift speed and hold-Alt bone
reveal are unchanged and are not remappable in this increment. This is the main
keyboard-action increment, not complete device/input remapping or an international
layout/IME/tablet/OS-hotkey certification.

Global shortcuts defer to text input, modal dialogs, Home, active camera
navigation and export, and ignore held-key repeats/releases. Drawing tools only
switch in Draw mode. Camera edits still require an explicit key action and retain
the existing replacement confirmation. Escape remains available for cancellation.

Version1 personal bindings are stored in the existing interface `display.cfg`,
alongside scale/navigation. All fifteen entries must validate together; a corrupt,
unknown or conflicting collection falls back to complete defaults and shows a
reason in the keyboard panel. It does not silently rewrite the invalid file.
Saving preserves unrelated preferences, writes a sibling temporary file then
renames it, and only changes active bindings after success. Read/write failures
retain the current bindings and show an error. No shortcut data enters `.has`,
project Undo, recovery revisions, source models, drawing pixels or movie output.

`python tests/verify_shortcuts.py` exercises all defaults/validation, actual hidden
embedded-window clicks and native key capture, conflicts/Escape, scroll access,
Clear/defaults, routing/text guards, explicit camera key/Undo/alternate Redo,
failed writes, a new-process custom profile, invalid-profile fallback and ordinary
packed HAS/pixel reopening. Other affected suites and actual results are recorded
in the dated memo. The older full656-source run predates this increment.

Primary references: Godot4.6 [InputEventKey](https://docs.godotengine.org/en/4.6/classes/class_inputeventkey.html),
[Window input](https://docs.godotengine.org/en/4.6/classes/class_window.html#signals),
[AcceptDialog Escape behavior](https://docs.godotengine.org/en/4.6/classes/class_acceptdialog.html#class-acceptdialog-property-dialog-close-on-escape)
and [ConfigFile](https://docs.godotengine.org/en/4.6/classes/class_configfile.html).
