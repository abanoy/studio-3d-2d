from pathlib import Path
import json,hashlib,sys,subprocess,time
r=Path.cwd();sys.path.insert(0,str(r));from run import command
folder=r/'output'/('native-pick-diagnostic-'+str(time.time_ns()));folder.mkdir();source=(r/'tests/world_selection_smoke.gd').read_text(encoding='utf-8')
source=source.replace('var failures := 0','''var failures := 0
var diagnostic_app
func diagnostic_pending() -> void:
	var a=diagnostic_app;var selection=a.world_selection;var now=a.scene_view.pick_state()
	for pending in selection.pick_requests.values():
		var d: Dictionary=pending.data
		var image: Image=selection.viewport.get_texture().get_image();var uv: Vector2=d.uv
		var pixel:=image.get_pixel(clampi(int(uv.x*image.get_width()),0,image.get_width()-1),clampi(int(uv.y*image.get_height()),0,image.get_height()-1))
		print("NATIVE_PICK_PENDING ",JSON.stringify({"serial":selection.serial,"request_serial":d.serial,"same_view":d.view==now,"saved_view":str(d.view),"current_view":str(now),"mode":a.mode.selected,"exporting":a.exporting,"playing":a.playing,"navigating":a.navigating,"pending_button":selection.pending_button,"selected":selection.selected,"pixel":str(pixel),"colors":str(selection.colors)}))''')
needle='''		var native_point:=id_point(native_mask,selection.color_for(model_key));selection.select_entity("")
		await click(app,native_point)'''
assert source.count(needle)==1
replacement='''		var native_point:=id_point(native_mask,selection.color_for(model_key))
		print("NATIVE_PICK_BEFORE_CLEAR ",JSON.stringify({"sample":sample.path,"point":str(native_point),"selected":selection.selected,"mode":app.mode.selected,"view":str(app.scene_view.pick_state()),"actor_visible":Support.rig(app).root.is_visible_in_tree(),"actor_data":Support.rig(app).data}))
		selection.select_entity("");diagnostic_app=app
		print("NATIVE_PICK_AFTER_CLEAR ",JSON.stringify({"mode":app.mode.selected,"view":str(app.scene_view.pick_state()),"selected":selection.selected}))
		RenderingServer.frame_post_draw.connect(diagnostic_pending,CONNECT_ONE_SHOT)
		await click(app,native_point)
		print("NATIVE_PICK_AFTER_CLICK ",JSON.stringify({"mode":app.mode.selected,"view":str(app.scene_view.pick_state()),"selected":selection.selected,"expected":model_key,"picking":selection.picking}))'''
source=source.replace(needle,replacement)
needle2='''		check(native_point.x>=0 and selection.selected==model_key,"GPU picking selects actual native skinned model: "+str(sample.path))'''
assert source.count(needle2)==1
source=source.replace(needle2,needle2+'''
		if selection.selected!=model_key:
			print("NATIVE_PICK_DIAGNOSTIC_STOP ",sample.path);app.free();quit(1);return''')
script=folder/'native_pick_diagnostic.gd';script.write_text(source,encoding='utf-8');args=command(str(script),extra=['--verbose']);(folder/'command.json').write_text(json.dumps(args,indent=2),encoding='utf-8');p=subprocess.run(args,cwd=r,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=140);(folder/'process.log').write_text(p.stdout+p.stderr,encoding='utf-8');receipt=json.loads(Path(args[args.index('--receipt')+1]).read_bytes());(folder/'verification.json').write_text(json.dumps({'exit':p.returncode,'receipt':receipt,'original_test_sha256':hashlib.sha256((r/'tests/world_selection_smoke.gd').read_bytes()).hexdigest(),'diagnostic_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'scope':'Footer/state logging and explicit stop after failed original native pick predicate; no production changes or full-pass claim'},indent=2)+'\n',encoding='utf-8');print(json.dumps({'folder':str(folder),'exit':p.returncode}))
