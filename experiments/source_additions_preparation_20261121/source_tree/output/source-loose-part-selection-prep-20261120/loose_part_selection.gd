extends RefCounted
# Pure row selection. It never edits inclusion plans, wind groups, meshes or poses.
var keys: Array[String] = []
var disabled: Dictionary = {}
var chosen: Dictionary = {}
var focus := -1
var anchor := -1
var dragging := false
var before: Dictionary = {}
var drag_start := -1
var drag_mode := "replace"

func eligible(index: int) -> bool:
	return index >= 0 and index < keys.size() and not disabled.has(index)
func snapshot() -> Dictionary:
	var selected: Array = chosen.keys(); selected.sort()
	return {"selected":selected,"focus":focus,"anchor":anchor}
func configure(rows: Array, blocked: Array = []) -> String:
	if rows.is_empty() or rows.size() > 4096: return "Invalid part selection inventory."
	var next: Array[String] = []; var seen := {}; var off := {}
	for key in rows:
		if not key is String or key.is_empty() or key.length() > 256 or seen.has(key): return "Invalid part selection identity."
		seen[key] = true; next.append(key)
	for index in blocked:
		if not index is int or index < 0 or index >= rows.size(): return "Invalid disabled part index."
		off[index] = true
	keys = next; disabled = off; chosen.clear(); focus = -1; anchor = -1; dragging = false; before.clear()
	return ""
func restore(value: Dictionary) -> void:
	chosen.clear()
	for index in value.selected: chosen[index] = true
	focus = value.focus; anchor = value.anchor
func range_rows(first: int, last: int) -> Array:
	var result := []
	for index in range(mini(first,last),maxi(first,last)+1):
		if eligible(index): result.append(index)
	return result
func click(index: int, control: bool = false, shift: bool = false) -> bool:
	if dragging or not eligible(index): return false
	if shift and eligible(anchor):
		if not control: chosen.clear()
		for row in range_rows(anchor,index): chosen[row] = true
	elif control:
		if chosen.has(index): chosen.erase(index)
		else: chosen[index] = true
		anchor = index
	else:
		chosen = {index:true}; anchor = index
	focus = index
	return true
func begin(index: int, control: bool = false, shift: bool = false) -> bool:
	if dragging or not eligible(index): return false
	before = snapshot(); drag_start = anchor if shift and eligible(anchor) else index
	drag_mode = "remove" if control and not shift and chosen.has(index) else "add" if control else "replace"
	if not click(index,control,shift): before.clear(); return false
	dragging = true
	return true
func update(index: int) -> bool:
	if not dragging or index < 0 or index >= keys.size(): return false
	var selected: Dictionary = {}
	if drag_mode != "replace":
		for row in before.selected: selected[row] = true
	for row in range_rows(drag_start,index):
		if drag_mode == "remove": selected.erase(row)
		else: selected[row] = true
	chosen = selected
	if eligible(index): focus = index
	return true
func finish() -> Dictionary:
	var result := snapshot()
	result["changed"] = not before.is_empty() and result != before
	dragging = false; before.clear(); drag_start = -1
	return result
func cancel() -> void:
	if dragging: restore(before)
	dragging = false; before.clear(); drag_start = -1
func selected_keys() -> Array[String]:
	var result: Array[String] = []
	for index in snapshot().selected: result.append(keys[index])
	return result
func clear() -> void:
	keys.clear(); disabled.clear(); chosen.clear(); focus = -1; anchor = -1; dragging = false; before.clear()
