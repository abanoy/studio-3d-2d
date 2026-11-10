extends RefCounted
# Recursive split/tab layout. Editors are reparented, never copied or reconstructed.
var owner
var books: Dictionary={}
var members: Dictionary={}
var serial:=0
func _init(manager) -> void:owner=manager
func make_book(edge: String,key: String) -> TabContainer:
	var book:=TabContainer.new();book.name="DockGroup"+key;book.set_meta("dock_key",key);book.set_meta("dock_edge",edge);book.size_flags_horizontal=Control.SIZE_EXPAND_FILL;book.size_flags_vertical=Control.SIZE_EXPAND_FILL;book.all_tabs_in_front=true;book.use_hidden_tabs_for_min_size=true
	book.add_theme_stylebox_override("panel",StyleBoxEmpty.new())
	for styled in [book,book.get_tab_bar()]:
		for state in ["tab_selected","tab_unselected","tab_hovered","tab_disabled"]:styled.add_theme_stylebox_override(state,owner.app.theme.get_stylebox("pressed" if state=="tab_selected" else "normal","Button"))
		for color in ["font_selected_color","font_unselected_color","font_hovered_color"]:styled.add_theme_color_override(color,Color("163854"))
	book.tab_changed.connect(func(_index):owner.save_later())
	book.get_tab_bar().gui_input.connect(func(event):
		if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and event.pressed:
			var index: int=book.get_tab_bar().get_tab_idx_at_point(event.position)
			if index>=0:
				var panel: Control=book.get_tab_control(index)
				for id in owner.panels:
					if owner.panels[id]==panel:owner.header_input(id,event);break)
	books[key]=book
	return book
func seed(edge: String,ids: Array) -> void:
	members[edge]=ids.duplicate();var book:=make_book(edge,edge);owner.slots[edge].add_child(book);owner.tabs[edge]=book
func key_for(id: String) -> String:
	for key in members:
		if id in members[key]:return key
	return ""
func book_for(id: String) -> TabContainer:return books.get(key_for(id))
func edge_for(id: String) -> String:
	var book:=book_for(id);return str(book.get_meta("dock_edge")) if book else ""
func leaf_keys(node: Control) -> Array:
	if node is TabContainer:return [str(node.get_meta("dock_key"))]
	var result:=[]
	for child in node.get_children():result.append_array(leaf_keys(child))
	return result
func empty(node: Control) -> bool:
	for key in leaf_keys(node):
		if not members[key].is_empty():return false
	return true
func forget(node: Control) -> void:
	for key in leaf_keys(node):books.erase(key);members.erase(key)
func prune(node: Control) -> void:
	if not node is SplitContainer:return
	for child in node.get_children().duplicate():prune(child)
	var children:=node.get_children()
	if children.size()!=2:return
	var discarded: Control
	var kept: Control
	if empty(children[0]):discarded=children[0];kept=children[1]
	elif empty(children[1]):discarded=children[1];kept=children[0]
	else:return
	var parent:=node.get_parent();var index:=node.get_index();kept.reparent(parent,false);parent.move_child(kept,index);forget(discarded);parent.remove_child(node);node.queue_free()
func visible_branch(node: Control) -> bool:
	if node is TabContainer:
		node.tabs_visible=node.get_tab_count()>1;node.visible=node.get_tab_count()>0;return node.visible
	var visible:=false
	for child in node.get_children():visible=visible_branch(child) or visible
	node.visible=visible;return visible
func refresh() -> void:
	for edge in owner.EDGES:
		var slot: Control=owner.slots[edge];prune(slot.get_child(0));var keys:=leaf_keys(slot.get_child(0));var ids:=[]
		for key in keys:ids.append_array(members[key])
		owner.groups[edge]=ids;owner.locations[edge]=ids[0] if not ids.is_empty() else "";owner.tabs[edge]=books[keys[0]]
		slot.visible=visible_branch(slot.get_child(0))
func move_membership(id: String,key: String) -> void:
	var old:=key_for(id)
	if old==key:return
	members[old].erase(id);members[key].append(id)
func dock_edge(id: String,edge: String) -> void:
	if not owner.panels.has(id) or not owner.slots.has(edge):return
	var old:=key_for(id);var target: String=leaf_keys(owner.slots[edge].get_child(0))[0]
	if owner.floating.has(id) and edge_for(id)==edge:target=old
	if old==target:
		owner.restore_to_book(id,books[target]);refresh();books[target].current_tab=owner.panels[id].get_index();owner.save_later();return
	var other: String=members[target][0] if not members[target].is_empty() else ""
	members[old].erase(id)
	if not other.is_empty():members[target].erase(other);members[old].append(other);owner.restore_to_book(other,books[old])
	members[target].append(id);owner.restore_to_book(id,books[target]);refresh();books[target].current_tab=owner.panels[id].get_index();owner.save_later()
func tab_into(id: String,other: String) -> void:
	if id==other or not owner.panels.has(id) or not owner.panels.has(other):return
	var target:=key_for(other);move_membership(id,target);owner.restore_to_book(other,books[target]);owner.restore_to_book(id,books[target]);refresh();books[target].current_tab=owner.panels[id].get_index();owner.save_later()
func make_split(axis: String) -> SplitContainer:
	var split: SplitContainer=HSplitContainer.new() if axis=="h" else VSplitContainer.new();split.name="DockSplit";split.size_flags_horizontal=Control.SIZE_EXPAND_FILL;split.size_flags_vertical=Control.SIZE_EXPAND_FILL;split.add_theme_constant_override("separation",10);split.get_drag_area_control().tooltip_text="Drag to resize these dock groups.";split.dragged.connect(func(_offset):owner.save_later());return split
func split_into(id: String,other: String,side: String) -> void:
	if id==other or not owner.panels.has(id) or not owner.panels.has(other) or not side in owner.EDGES:return
	var target:=book_for(other);var edge:=edge_for(other);var parent:=target.get_parent();var index:=target.get_index()
	serial+=1
	while books.has("leaf_"+str(serial)):serial+=1
	var key:="leaf_"+str(serial);members[key]=[];var added:=make_book(edge,key);move_membership(id,key)
	var split:=make_split("h" if side in ["left","right"] else "v");parent.add_child(split);parent.move_child(split,index);target.reparent(split,false);split.add_child(added)
	if side in ["left","top"]:split.move_child(added,0)
	owner.restore_to_book(other,target);owner.restore_to_book(id,added);refresh();split.split_offset=0;owner.save_later()
func first_other(book: TabContainer,id: String) -> String:
	var current:=book.get_current_tab_control()
	for candidate in members[str(book.get_meta("dock_key"))]:
		if candidate!=id and not owner.floating.has(candidate) and owner.panels[candidate]==current:return candidate
	for candidate in members[str(book.get_meta("dock_key"))]:
		if candidate!=id and not owner.floating.has(candidate):return candidate
	return ""
func target_at(point: Vector2,id: String) -> Dictionary:
	for book in books.values():
		if not book.is_visible_in_tree() or not book.get_global_rect().has_point(point):continue
		var other:=first_other(book,id)
		if other.is_empty():return {"kind":"stay"}
		var rect: Rect2=book.get_global_rect();var offset:=point-rect.position
		if book.tabs_visible and book.get_tab_bar().get_global_rect().has_point(point):return {"kind":"tab","other":other,"rect":rect}
		var distances:={"left":offset.x/maxf(rect.size.x,1),"right":1-offset.x/maxf(rect.size.x,1),"top":offset.y/maxf(rect.size.y,1),"bottom":1-offset.y/maxf(rect.size.y,1)};var nearest: String="left"
		for edge in distances:
			if distances[edge]<distances[nearest]:nearest=edge
		if distances[nearest]<.25:return {"kind":"split","side":nearest,"other":other,"rect":rect}
		return {"kind":"tab","other":other,"rect":rect}
	return {}
func dump_node(node: Control) -> Dictionary:
	if node is TabContainer:
		var key: String=node.get_meta("dock_key");var selected: Control=node.get_current_tab_control();return {"key":key,"tabs":members[key].duplicate(),"selected":str(selected.name) if selected else ""}
	return {"axis":"v" if node is VSplitContainer else "h","offset":node.split_offset,"first":dump_node(node.get_child(0)),"second":dump_node(node.get_child(1))}
func state() -> Dictionary:
	var result:={}
	for edge in owner.EDGES:result[edge]=dump_node(owner.slots[edge].get_child(0))
	return result
func valid_node(value,ids: Array,keys: Array,depth: int) -> bool:
	if not value is Dictionary or depth>8:return false
	if value.has("tabs"):
		if not value.get("key") is String or value.key.length()>80 or not value.key.is_valid_identifier() or value.key in keys or not value.tabs is Array or not value.get("selected") is String:return false
		keys.append(value.key)
		for id in value.tabs:
			if not id is String or not owner.panels.has(id) or id in ids:return false
			ids.append(id)
		return true
	var offset=value.get("offset")
	return value.get("axis") in ["h","v"] and (offset is int or offset is float) and is_finite(float(offset)) and offset==floor(offset) and absf(offset)<=10000 and valid_node(value.get("first"),ids,keys,depth+1) and valid_node(value.get("second"),ids,keys,depth+1)
func validate(value) -> bool:
	if not value is Dictionary or value.size()!=4:return false
	var ids:=[];var keys:=[]
	for edge in owner.EDGES:
		if not valid_node(value.get(edge),ids,keys,0):return false
	return ids.size()==owner.panels.size() and keys.size()<=16
func build(value: Dictionary,parent: Node,edge: String) -> Control:
	if value.has("tabs"):
		var key: String=value.key;members[key]=value.tabs.duplicate();var book:=make_book(edge,key);parent.add_child(book)
		for id in members[key]:owner.restore_to_book(id,book)
		for panel in book.get_children():
			if str(panel.name)==value.selected:book.current_tab=panel.get_index()
		return book
	var split:=make_split(value.axis);parent.add_child(split);build(value.first,split,edge);build(value.second,split,edge);split.split_offset=int(value.offset);return split
func replace(value: Dictionary) -> void:
	var hold:=Control.new();hold.hide();owner.app.add_child(hold)
	for panel in owner.panels.values():panel.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT);panel.reparent(hold,false)
	for window in owner.floating.values():window.hide();window.queue_free()
	owner.floating.clear()
	for slot in owner.slots.values():
		for child in slot.get_children():slot.remove_child(child);child.queue_free()
	books.clear();members.clear()
	for edge in owner.EDGES:build(value[edge],owner.slots[edge],edge)
	hold.queue_free();refresh()
func defaults() -> Dictionary:
	var result:={}
	for edge in owner.EDGES:result[edge]={"key":edge,"tabs":[owner.DEFAULT[edge]] if not owner.DEFAULT[edge].is_empty() else [],"selected":""}
	return result

func value_ids(value: Dictionary) -> Array:
	if value.has("tabs"):return value.tabs.duplicate()
	var result:=value_ids(value.first);result.append_array(value_ids(value.second));return result
