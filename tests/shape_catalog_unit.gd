extends SceneTree
const Catalog=preload("res://src/shape_catalog.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	for pair in [["Sword Shashimi","Accessories"],["Sword","Accessories"],["Mini Skirt","Clothing"],["Sword Mouth","Other"],["Swordfish","Other"]]:
		check(Catalog.estimate(pair[0]).area==pair[1],"sword and clothing estimates respect word boundaries and mixed regions: "+pair[0])
	for pair in [[" blink ","Eyes"],["Eyebrows raise L","Brows"],["Eye brows forward","Brows"],["mouth angry open","Mouth"],["まばたき","Eyes"],["あ","Mouth"],["normal hair","Hair"],["Wing Shrink","Accessories"],["Tools","Accessories"],["Remove Skirt","Clothing"],["Thick legs","Body"]]:check(Catalog.estimate(pair[0]).area==pair[1],"provisional named area: "+pair[0])
	check(Catalog.estimate("Smile").area=="Other" and Catalog.estimate("笑い").area=="Other","ambiguous smile names do not invent a whole-face expression or anatomy")
	check(Catalog.estimate("mystery_087").area=="Other" and Catalog.estimate("eye mouth").area=="Other","unknown or mixed names remain accessible as unassigned")
	for pair in [["OpenJaw","Mouth"],["CloseLidUpL","Eyes"],["OuterSquintR","Eyes"],["TongueOut","Mouth"],["BrowOutV_CloseLidUpL","Other"],["BrowOutV_OuterSquintL","Other"],["OpenJaw_CloseLidUpL","Other"],["KK Mouth_n_nn","Mouth"]]:check(Catalog.estimate(pair[0]).area==pair[1],"native CamelCase separates regions and refuses mixed seeds: "+pair[0])
	var data:={"format":"studio_model_7","metadata":{"native_parameters":{"unchanged":true}},"animation_clips":[{"shape_keys":[{"frame":4,"shapes":{"231":{"88":.5}}}]}]}
	var before:=data.duplicate(true);var mapped:=Catalog.assign(data,231,88,"Eyebrows raise","Mouth","Artist's choice")
	check(not mapped.has("error") and data==before,"manual assignment does not mutate source data")
	check(mapped.data.animation_clips==before.animation_clips and mapped.data.format==before.format and mapped.data.metadata.native_parameters==before.metadata.native_parameters,"classification preserves animation, model version and native metadata")
	var entry:=Catalog.lookup(mapped.data,231,88,"Eyebrows raise")
	check(entry.manual and entry.area=="Mouth" and entry.label=="Artist's choice","explicit manual choice takes precedence over the name estimate")
	var stale:=Catalog.lookup(mapped.data,231,88,"different target")
	check(not stale.manual and stale.has("notice") and stale.area=="Other","changed native identity cannot inherit a stale assignment")
	check(Catalog.clear(mapped.data,231,88).data==before,"clearing the last assignment restores exact original metadata")
	check(Catalog.assign(data,-1,0,"x","Eyes","").has("error") and Catalog.assign(data,0,2048,"x","Eyes","").has("error") and Catalog.assign(data,0,0,"x","Invented","").has("error"),"invalid binding and category choices refuse")
	var newer:=data.duplicate(true);newer.metadata.shape_catalog={"format":"future","controls":{}}
	check(Catalog.assign(newer,0,0,"x","Eyes","").has("error") and Catalog.lookup(newer,0,0,"blink").has("notice"),"unknown catalogue versions remain preserved and are not overwritten")
	var roundtrip: Dictionary=JSON.parse_string(JSON.stringify(mapped.data))
	check(Catalog.lookup(roundtrip,231,88,"Eyebrows raise")==entry,"JSON roundtrip retains canonical source identities and explicit choices")
	print("SHAPE_CATALOG_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
