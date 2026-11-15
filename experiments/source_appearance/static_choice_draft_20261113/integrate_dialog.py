"""Output-only source seam edits; GDScript is deliberately not launched here."""
from pathlib import Path
import json

from build_candidate import ROOT, TASK, BASE, stamp, replace_once

path = TASK / "overlay/src/source_import.gd"
text = path.read_text(encoding="utf-8")
text = replace_once(text, "\tbox.add_child(members)\n", "\tbox.add_child(members)\n"
    "\tvar appearance_ui = null\n"
    "\tif as_model:\n"
    "\t\tappearance_ui = preload(\"res://src/source_choice_dialog.gd\").new()\n"
    "\t\tdialog.add_child(appearance_ui)\n"
    "\t\tappearance_ui.attach(dialog, box, path, members, python())\n")
text = replace_once(text, "\tdialog.confirmed.connect(func():\n\t\tgmod_root = game_field.text.strip_edges()", "\tdialog.confirmed.connect(func():\n"
    "\t\tif appearance_ui != null and not appearance_ui.selection_valid(): return\n"
    "\t\tvar appearance: Dictionary = appearance_ui.request() if appearance_ui != null else {}\n"
    "\t\tgmod_root = game_field.text.strip_edges()")
text = replace_once(text, 'launch(path, str(choices[members.selected]), as_model, scale.value, content.text.strip_edges(),null,"","Y",at_frame,placement)',
    'launch(path, str(choices[members.selected]), as_model, scale.value, content.text.strip_edges(),null,"","Y",at_frame,placement,appearance)')
text = replace_once(text, 'obj_up := "Y", at_frame := 0, placement := {}) -> void:\n\tif app.height_review',
    'obj_up := "Y", at_frame := 0, placement := {}, appearance := {}) -> void:\n\tif app.height_review')
text = replace_once(text, '\tif not content.is_empty(): args.append_array(["--content", content])',
    '\tif not appearance.is_empty():\n'
    '\t\tif generic or not native_family.is_empty() or not as_model:\n'
    '\t\t\tapp.message("Appearance choices apply only to one Source model."); return\n'
    '\t\tvar appearance_path := folder + "-appearance.json"\n'
    '\t\tvar appearance_json := JSON.stringify(appearance)\n'
    '\t\tif appearance_json.to_utf8_buffer().size() > 64 * 1024:\n'
    '\t\t\tapp.message("Appearance request is too large."); return\n'
    '\t\tvar appearance_file := FileAccess.open(appearance_path, FileAccess.WRITE)\n'
    '\t\tif appearance_file == null: app.message("Cannot write the appearance request."); return\n'
    '\t\tappearance_file.store_string(appearance_json); appearance_file.close()\n'
    '\t\targs.append_array(["--appearance", appearance_path])\n'
    '\tif not content.is_empty(): args.append_array(["--content", content])')
path.write_text(text, encoding="utf-8")
print(json.dumps({"source": str(path), "draft": stamp(path), "base_revision": BASE,
                  "parse_runtime": "UNRUN by canonical source/GPU freeze"}))
