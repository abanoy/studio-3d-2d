extends SceneTree
const Sprite=preload("res://src/particle_sprite.gd")
const Renderer=preload("res://src/renderer.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Encoder=preload("res://src/encoder.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Particle sprite watchdog");quit(2))
	call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS "if ok else "FAIL ")+label)
	if not ok:failures+=1
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var cold:=OS.get_cmdline_user_args().size()>1
	var plans=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plans.json")))
	var renderer:=Renderer.new();root.add_child(renderer);renderer.setup()
	var room:=folder.path_join("room.glb")
	if not cold:check(SceneIO.make_fixture(room)==OK,"original GLB room fixture")
	check(renderer.import_scene(room).is_empty(),"ordinary shared3D renderer loads original room")
	var original:=FileAccess.get_sha256(room)
	var keys: Array=[Timeline.key(0,Vector3(0,1,7),Quaternion.IDENTITY,60)]
	var ink:=Drawing.blank(1920,1080);Drawing.stroke(ink,Vector2(72,72),Vector2(180,72),5,Color.CYAN,false)
	var ink_bytes:=ink.get_data();var layers: Array=[{"visible":true,"cels":[{"start":0,"duration":48,"image":ink}]}]
	var effects:=[];var initial:=[]
	for i in range(plans.size()):
		var bundle: String=plans[i].bundle
		var data=JSON.parse_string(FileAccess.get_file_as_string(bundle.path_join("effect.json")))
		var sprite:=Sprite.new();var image:=Image.load_from_file(bundle.path_join("sprite.png"))
		check(sprite.setup(data,ImageTexture.create_from_image(image)).is_empty(),"native descriptor and actual texture accepted "+str(i))
		renderer.world.add_child(sprite.root);sprite.root.position=Vector3(-1.6 if i==0 else 1.5,1,1)
		initial.append(JSON.stringify(data,"",true,true));effects.append(sprite)
		var poses:=[]
		for n in range(97):poses.append(sprite.sample(n/48.))
		var exact:=true
		for n in range(96,-1,-1):
			if sprite.evaluate(n/48.)!=poses[n]:exact=false
		check(exact,"97forward/reverse samples are exact and independent of render pacing "+str(i))
		check(sprite.sample(-.1).is_empty() and sprite.sample(2.).is_empty(),"bounded effect starts absent and clips at duration "+str(i))
		var before: Array=sprite.sample(.5);var invalid: Dictionary=data.duplicate(true);invalid.format="unknown"
		check(not sprite.setup(invalid,ImageTexture.create_from_image(image)).is_empty() and sprite.sample(.5)==before,"failed descriptor rebuild retains live effect "+str(i))
		check(JSON.stringify(data,"",true,true)==initial[i],"source descriptor unchanged by queries "+str(i))
		var previous: Array=sprite.evaluate(1./24.);var count: int=sprite.root.multimesh.visible_instance_count
		check(sprite.evaluate(INF)==previous and not sprite.evaluation_error.is_empty() and sprite.root.multimesh.visible_instance_count==count,"invalid time reports an error and retains last GPU state "+str(i))
		sprite.evaluate(1./24.)
		check(sprite.evaluation_error.is_empty(),"finite seek clears evaluation error "+str(i))
	await process_frame
	for effect in effects:effect.root.visible=false
	var baseline: Image=await renderer.capture(keys,layers,1,true)
	for effect in effects:effect.root.visible=true;effect.evaluate(1./24.)
	var flash: Image=await renderer.capture(keys,layers,1,true)
	var changed:=0
	for y in range(100,980,3):
		for x in range(20,950,3):
			if flash.get_pixel(x,y)!=baseline.get_pixel(x,y):changed+=1
	check(changed>100,"actual native SFM flash changes visible left-side GPU pixels")
	flash.save_png(folder.path_join("flash.png"))
	for effect in effects:effect.evaluate(.5)
	var glow: Image=await renderer.capture(keys,layers,12,true)
	for effect in effects:effect.root.visible=false
	var no_glow: Image=await renderer.capture(keys,layers,12,true)
	for effect in effects:effect.root.visible=true
	var glow_changed:=0
	for y in range(100,980,3):
		for x in range(970,1900,3):
			if glow.get_pixel(x,y)!=no_glow.get_pixel(x,y):glow_changed+=1
	check(glow_changed>50,"actual native Workshop glow changes visible right-side GPU pixels")
	glow.save_png(folder.path_join("glow.png"))
	for effect in effects:effect.evaluate(1./24.)
	var repeat: Image=await renderer.capture(keys,layers,1,true)
	check(repeat.get_data()==flash.get_data(),"reverse seek reproduces identical native particle pixels")
	check(ink.get_data()==ink_bytes and flash.get_pixel(100,72).g>.95 and flash.get_pixel(100,72).b>.95,"independent editable cyan drawing survives particle rendering")
	check(FileAccess.get_sha256(room)==original,"particle sampling never edits3D asset")
	if cold:
		check(flash.get_data()==Image.load_from_file(folder.path_join("flash-reference.png")).get_data(),"cold descriptor and PNG-only reader reproduces exact effect picture")
	else:
		flash.save_png(folder.path_join("flash-reference.png"))
		for frame in range(48):
			for effect in effects:effect.evaluate(frame/24.)
			var output: Image=await renderer.capture(keys,layers,frame,true)
			output.save_png(folder.path_join("frame_%06d.png"%(frame+1)))
		var encoder:=Encoder.new();var error: String=await encoder.encode(self,"C:/Program Files/ffmpeg/bin/ffmpeg.exe",folder,{"fps_num":24,"fps_den":1,"duration_frames":48})
		check(error.is_empty() and FileAccess.file_exists(folder.path_join("movie.mp4")),"native effect fixture encodes actual MP4")
		check(Image.load_from_file(folder.path_join("frame_000002.png")).get_data()==flash.get_data(),"same sampled effect frame equals movie PNG")
	# Authored controls exercise the same sprite renderer independently of source
	# material quirks. They are not counted as extra native effects.
	for effect in effects:effect.root.visible=false
	var authored: Dictionary=effects[1].data.duplicate(true)
	authored.particles=[{"birth":0.,"lifetime":2.,"position":[.25,.125,0.],"velocity":[.5,1.,0.],"acceleration":[0.,-2.,0.],"radius":.25,"color":[1.,1.,1.,1.],"rotation":0.,"spin":0.}]
	authored.alpha={"in_start":0.,"in_end":0.,"out_start":1.,"out_end":1.,"start_alpha":1.,"end_alpha":1.}
	authored.radius={"start":0.,"end":1.,"from":1.,"to":1.,"bias":.5,"ease":false};authored.color.enabled=false
	var solid:=Image.create(4,4,false,Image.FORMAT_RGBA8);solid.fill(Color.WHITE)
	var probe:=Sprite.new();check(probe.setup(authored,ImageTexture.create_from_image(solid)).is_empty(),"authored control uses same canonical renderer")
	renderer.world.add_child(probe.root)
	check(probe.sample(.5)[0].position.is_equal_approx(Vector3(.5,.375,0)),"analytic velocity and gravity match independent known position")
	probe.evaluate(0.);probe.root.position=Vector3(.5,.25,0);probe.root.scale=Vector3.ONE*2
	var parent_picture: Image=await renderer.capture(keys,layers,1,true)
	probe.dispose();authored.particles[0].position=[1.,.5,0.];authored.particles[0].radius=.5
	check(probe.setup(authored,ImageTexture.create_from_image(solid)).is_empty(),"rebuild transformed control")
	renderer.world.add_child(probe.root);probe.evaluate(0.)
	var flat_picture: Image=await renderer.capture(keys,layers,1,true)
	check(parent_picture.get_data()==flat_picture.get_data(),"uniform parent scale and translation match equivalent world-space descriptor pixels")
	var direction: Quaternion=Transform3D.IDENTITY.looking_at(Vector3(-1.,-.5,-5.),Vector3.UP).basis.get_rotation_quaternion()
	var angled_keys: Array=[Timeline.key(0,Vector3(2,1,5),direction,60)]
	probe.root.visible=false
	var angled_base: Image=await renderer.capture(angled_keys,layers,1,true)
	probe.root.visible=true
	var angled_effect: Image=await renderer.capture(angled_keys,layers,1,true)
	var changed_angled:=0
	for y in range(300,780,3):
		for x in range(600,1320,3):
			if angled_base.get_pixel(x,y)!=angled_effect.get_pixel(x,y):changed_angled+=1
	check(changed_angled>100,"billboard remains visible through rotated animated camera")
	var blocker:=MeshInstance3D.new();var box:=BoxMesh.new();box.size=Vector3(4,4,.25);blocker.mesh=box;blocker.position=Vector3(1,.5,2);renderer.world.add_child(blocker)
	probe.root.visible=false
	var blocked_base: Image=await renderer.capture(keys,layers,1,true)
	probe.root.visible=true
	var blocked_effect: Image=await renderer.capture(keys,layers,1,true)
	check(blocked_base.get_data()==blocked_effect.get_data(),"opaque3D geometry fully occludes sprites behind it")
	blocker.free();probe.dispose()
	authored.particles[0].position=[5000.,1.,0.]
	check(probe.setup(authored,ImageTexture.create_from_image(solid)).is_empty(),"prepare distant moving-sprite control")
	renderer.world.add_child(probe.root);probe.evaluate(0.)
	var distant_keys: Array=[Timeline.key(0,Vector3(5000,1,7),Quaternion.IDENTITY,60)]
	probe.root.visible=false
	var distant_base: Image=await renderer.capture(distant_keys,layers,1,true)
	probe.root.visible=true
	var distant: Image=await renderer.capture(distant_keys,layers,1,true)
	check(probe.root.multimesh.custom_aabb.has_point(Vector3(5000,1,0)) and distant.get_pixel(960,540)!=distant_base.get_pixel(960,540),"sampled bounds keep distant particles visible beyond the former fixed culling box")
	probe.dispose()
	for effect in effects:effect.dispose()
	renderer.free();await process_frame
	var result: Dictionary={"checks":checks,"failures":failures,"flash_changed_samples":changed,"glow_changed_samples":glow_changed,"cold":cold}
	var file:=FileAccess.open(folder.path_join("cold.json"if cold else "result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("PARTICLE_SPRITE "+JSON.stringify(result));quit(0 if failures==0 else 1)
