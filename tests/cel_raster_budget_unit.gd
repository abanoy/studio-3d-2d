extends SceneTree
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Owner=preload("res://src/cel_raster_owner.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
const Budget=preload("res://src/cel_raster_budget.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func make_owner(cache,index: int):
	var image:=Image.create(32,16,false,Image.FORMAT_RGBA8);image.fill(Color(float(index+1)/8,.4,.7,1));return Owner.from_snapshot(Snapshot.capture(image).raster,cache).owner
func _initialize() -> void:
	var cache:=Cache.new(0);var budget:=Budget.new(4096);budget.install(cache);var owners: Array=[]
	for i in range(5):
		var owner=make_owner(cache,i);owner.pin();owners.append(owner)
	var state:=budget.sample();check(state.owners==5 and state.hot_bytes==5*2048 and state.hot_owners==5,"project registry counts owned hot pixels without retaining Image handles")
	check(not budget.step([],false).released and budget.attempts==0,"busy steps never compress or release editing pixels")
	var protected: Array=[owners[0]];var result:=budget.step(protected)
	check(result.released and budget.releases==1 and budget.attempts==1 and budget.sample().hot_owners==4,"one idle step cools at most one eligible owner")
	check(owners[0].is_pinned(),"protected current/visible owner remains hot")
	budget.step(protected);budget.step(protected);state=budget.sample()
	check(state.hot_bytes==4096 and budget.releases==3,"successive bounded steps reach soft hot target")
	check(budget.step(protected).reason=="within_target" and budget.attempts==3,"within-target steps do no further compression")
	var cold_before: int=state.cold_payload_bytes;var cold=owners.filter(func(owner):return not owner.is_pinned())[0];var old: Array=cold.token();var pixels: Dictionary=cold.read()
	check(cold.token()==old and not cold.is_pinned() and budget.sample().cold_payload_bytes==cold_before,"budget/read sampling preserves cold revision and captured content")
	pixels={};cold=null;owners.clear();check(budget.sample().owners<=1,"weak registry does not retain discarded document owners")
	budget.install(null);check(budget.sample().owners==0 and budget.step().reason=="within_target","installing empty document drops budget context safely")
	var held_cache:=Cache.new(0);budget=Budget.new(0);budget.install(held_cache);var held=make_owner(held_cache,0);var pin: Dictionary=held.pin()
	check(budget.step().reason=="image_borrowed" and held.is_pinned(),"borrowed writable image blocks automatic release despite target pressure")
	pin={};check(budget.step().released and not held.is_pinned(),"release proceeds after active caller drops writable handle")
	var fair_cache:=Cache.new(0);var fair:=Budget.new(0);fair.install(fair_cache);var free_owner=make_owner(fair_cache,0);free_owner.pin();var blocked_owner=make_owner(fair_cache,1);var handle: Dictionary=blocked_owner.pin()
	check(fair.step().reason=="image_borrowed" and fair.step().released and blocked_owner.is_pinned() and not free_owner.is_pinned(),"round-robin attempts prevent a borrowed owner from starving other eligible releases")
	handle={}
	check(Budget.new(-1).target==0 and Budget.new(999999999).target==Budget.DEFAULT_BYTES,"budget configuration cannot exceed prototype target ceiling")
	print("CEL_RASTER_BUDGET_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
