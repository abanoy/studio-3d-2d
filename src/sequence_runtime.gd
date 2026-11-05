extends Node
const Graph=preload("res://src/sequence_graph.gd")
const Renderer=preload("res://src/renderer.gd")
const Drawing=preload("res://src/drawing.gd")
const Pixels=preload("res://src/sequence_pixels.gd")
const Audio=preload("res://src/sequence_audio.gd")
var graph: Dictionary={}
var root_scene: Dictionary={}
var owners: Dictionary={}
var renderers: Dictionary={}
var frames: Dictionary={}
var audio_mixes: Dictionary={}
var compositor: SubViewport
var sprites: Array=[]
var shadows: Array=[]
var busy:=false
var requests:=0
var cancelled:=false
var last_error:=""
var builds:=0
func prepare(incoming: Dictionary,root: Dictionary,active_owner: String="") -> String:
	var why:=Graph.error(incoming,root)
	if not why.is_empty():return why
	var mixed:=Audio.build(incoming,root)
	if mixed.has("error"):return mixed.error
	graph=incoming;root_scene=root;audio_mixes=mixed.mixes
	owners[""]={"scene":root,"clips":graph.clips}
	for asset in graph.assets:owners[asset.id]=asset
	for asset in graph.assets:
		if asset.id==active_owner:continue
		var renderer:=Renderer.new();add_child(renderer);renderer.setup()
		renderer.sequence_instance=true;renderer.viewport.transparent_bg=true
		renderer.world_environment.environment.background_color=Color(0,0,0,0)
		renderer.video_settings=asset.scene.video
		var prepared:=renderer.prepare_world(asset.scene.world,int(asset.scene.video.duration_frames))
		if prepared.has("error"):return "Sequence %s: %s" % [asset.name,prepared.error]
		renderer.install_world(prepared);renderer.editor_grid.hide()
		renderer.viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED
		renderers[asset.id]=renderer
	compositor=SubViewport.new();compositor.size=Vector2i(1920,1080);compositor.transparent_bg=true;compositor.disable_3d=true
	compositor.render_target_update_mode=SubViewport.UPDATE_DISABLED;add_child(compositor)
	return ""
func render(owner: String,frame: int,final: bool=false,drawings_only: bool=false) -> Image:
	requests+=1
	while busy and not cancelled:await get_tree().process_frame
	if cancelled:requests-=1;return null
	busy=true;last_error=""
	var image: Image=await render_clips(owner,frame,final,drawings_only)
	busy=false;requests-=1;return image
func render_clips(owner: String,frame: int,final: bool,drawings_only: bool) -> Image:
	if cancelled:return null
	if not owners.has(owner):last_error="Missing sequence owner.";return null
	var pictures: Array=[]
	for clip in owners[owner].clips:
		if not clip.visible:continue
		var asset: Dictionary=owners[clip.asset_id]
		var local:=Graph.local_frame(clip,frame,int(asset.scene.video.duration_frames))
		if local<0:continue
		var placed:=Graph.placement(clip,frame)
		if placed.opacity==0:continue
		var stamp:="%d:%s:%s" % [local,final,drawings_only]
		var cached: Dictionary=frames.get(clip.asset_id,{})
		if cached.get("stamp")!=stamp:
			var image: Image=Drawing.blank(1920,1080)
			if not drawings_only:
				if not renderers.has(clip.asset_id):last_error="Sequence renderer is unavailable.";return null
				var renderer=renderers[clip.asset_id]
				image=await renderer.capture(asset.scene.camera_keys,[],local,final)
				renderer.viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED
				if image==null:last_error=renderer.last_capture_error;return null
			var children: Image=await render_clips(clip.asset_id,local,final,drawings_only)
			if children==null:return null
			image.blend_rect(children,Rect2i(0,0,1920,1080),Vector2i.ZERO)
			var ink:=Drawing.composite(asset.scene.layers,local,1920,1080)
			image.blend_rect(ink,Rect2i(0,0,1920,1080),Vector2i.ZERO)
			var premultiplied: Image=image.duplicate();premultiplied.premultiply_alpha()
			if graph.format==Graph.SHADOW_FORMAT:premultiplied.generate_mipmaps()
			cached={"stamp":stamp,"image":image,"texture":ImageTexture.create_from_image(premultiplied)}
			frames[clip.asset_id]=cached;builds+=1
		pictures.append({"texture":cached.texture,"placement":placed,"shadow":clip.get("shadow",{})})
	if cancelled:return null
	if pictures.is_empty():return Drawing.blank(1920,1080)
	while sprites.size()<pictures.size():
		var shadow:=Sprite2D.new();shadow.texture_filter=CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		var shadow_material:=ShaderMaterial.new();shadow_material.shader=preload("res://src/sequence_shadow.gdshader");shadow.material=shadow_material
		compositor.add_child(shadow);shadows.append(shadow)
		var sprite:=Sprite2D.new();sprite.texture_filter=CanvasItem.TEXTURE_FILTER_LINEAR
		var material:=CanvasItemMaterial.new();material.blend_mode=CanvasItemMaterial.BLEND_MODE_PREMULT_ALPHA;sprite.material=material
		compositor.add_child(sprite);sprites.append(sprite)
	for i in range(sprites.size()):
		var sprite: Sprite2D=sprites[i];sprite.visible=i<pictures.size()
		var shadow: Sprite2D=shadows[i];shadow.visible=false
		if not sprite.visible:continue
		var p: Dictionary=pictures[i].placement;sprite.texture=pictures[i].texture
		sprite.position=Vector2(960,540)+p.offset;sprite.scale=Vector2.ONE*p.scale;sprite.rotation_degrees=p.rotation
		sprite.modulate=Color(p.opacity,p.opacity,p.opacity,p.opacity)
		var style: Dictionary=pictures[i].shadow
		if not style.is_empty() and style.color[3]>0:
			shadow.visible=true;shadow.texture=sprite.texture;shadow.position=sprite.position+Vector2(style.offset[0],style.offset[1]);shadow.scale=sprite.scale;shadow.rotation=sprite.rotation
			shadow.material.set_shader_parameter("shadow_color",Color(style.color[0],style.color[1],style.color[2],style.color[3]*p.opacity))
			shadow.material.set_shader_parameter("softness_lod",log(maxf(1.0,style.softness))/log(2.0))
	compositor.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	# Texture uploads and changed child visibility need a complete draw boundary.
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	if cancelled:return null
	var image:=compositor.get_texture().get_image();image.convert(Image.FORMAT_RGBA8)
	compositor.render_target_update_mode=SubViewport.UPDATE_DISABLED
	return Pixels.straight(image)
func shutdown() -> void:
	cancelled=true
	# Queued render callers also own suspended continuations. Do not free this
	# node between its current render completing and a waiting preview resuming.
	while requests>0:await get_tree().process_frame
	queue_free()
