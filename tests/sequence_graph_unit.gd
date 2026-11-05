extends SceneTree
const Graph=preload("res://src/sequence_graph.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1
	if not value:failures+=1;print("FAIL ",label)
func _initialize() -> void:
	var rows=JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
	for row in rows:check(Graph.error(row.value,row.root).is_empty()==row.valid,Graph.error(row.value,row.root))
	var clip: Dictionary=rows[0].value.clips[0].duplicate(true);clip.start=2;clip.duration=6;clip.source_in=1;clip.loop=true
	var mapped:=[]
	for i in range(10):mapped.append(Graph.local_frame(clip,i,4))
	check(mapped==[-1,-1,1,2,3,0,1,2,-1,-1],"exact local mapping and exclusive end")
	clip.keys=[Graph.key(),Graph.key(6)];clip.keys[1].offset=[120,60];clip.keys[1].rotation=360;clip.keys[1].scale=2;clip.keys[1].opacity=0
	var p:=Graph.placement(clip,5)
	check(p.offset==Vector2(60,30) and p.rotation==180 and p.scale==1.5 and p.opacity==.5,"placement keys interpolate locally and retain full rotations")
	clip.keys[0].interpolation="hold";check(Graph.placement(clip,7).opacity==1,"hold placement keeps previous value")
	clip=rows[0].value.clips[0].duplicate(true);clip.keys=[Graph.key(),Graph.key(48)];clip.keys[0].interpolation="ease";clip.keys[1].offset=[120,60]
	var left:=clip.duplicate(true);left.duration=17
	var right:=clip.duplicate(true);right.start=17;right.duration=31;right.key_in=17;right.time_in=17
	var exact:=true
	for frame in range(48):
		var piece: Dictionary=left if frame<17 else right
		exact=exact and Graph.placement(piece,frame).offset==Graph.placement(clip,frame).offset
	check(exact,"split windows preserve every original eased placement sample")
	print("SEQUENCE_GRAPH_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
