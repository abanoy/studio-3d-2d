extends "res://src/source_import.gd"
# Real preparer process/PID routing; generated GLB handoff, not native conversion.
func _spawn_preparation(args: PackedStringArray) -> int:
	var changed:=PackedStringArray([ProjectSettings.globalize_path("res://tests/character_parts_prepare_relay.py")])
	changed.append_array(args.slice(1))
	return super._spawn_preparation(changed)
