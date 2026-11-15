from pathlib import Path
import hashlib,json,subprocess,sys,time
root=Path.cwd();sys.path.insert(0,str(root));from run import command
out=root/'output/drawing-selection-crash-20261113';out.mkdir(exist_ok=True)
source=root/'tests/drawing_selection_smoke.gd';raw=source.read_bytes();text=raw.decode('utf-8')
needle='print("DRAWING_SELECTION_SMOKE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)'
assert text.count(needle)==1
replacement='''print("DRAWING_SELECTION_SMOKE ",JSON.stringify(result));print("SHUTDOWN_DIAGNOSTIC ",JSON.stringify({"objects":Performance.get_monitor(Performance.OBJECT_COUNT),"resources":Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT),"orphans":Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT),"native_readbacks":app.renderer.native_readbacks,"native_callbacks":app.renderer.native_frame_ready.get_connections().size(),"picking":app.world_selection.picking,"frame_connections":str(RenderingServer.get_signal_connection_list("frame_post_draw")),"project_pid":app.has_project.pid,"physics":app.physics_editor.simulations.size(),"selection_reveal":process_frame.is_connected(editor.reveal),"transform_reveal":process_frame.is_connected(editor.transforms.reveal),"editor_context":editor.context.size(),"preview":app.canvas.selection_preview!=null}));app.free();print("SHUTDOWN_DIAGNOSTIC_AFTER_FREE ",Performance.get_monitor(Performance.OBJECT_COUNT));quit(0 if failures==0 else 1)'''
script=out/'selection_verbose_pick_diagnostic.gd';script.write_text(text.replace(needle,replacement),encoding='utf-8',newline='\n')
case=out/('verbose-'+str(time.time_ns()));case.mkdir();args=command(str(script),extra=['--verbose','--',str(case),'--demo-room'])
start=time.time_ns();p=subprocess.run(args,cwd=root,capture_output=True,encoding='utf-8',errors='replace',timeout=220)
(case/'process.log').write_text(p.stdout+p.stderr,encoding='utf-8')
receipt=Path(args[args.index('--receipt')+1]);result={'source_sha256':hashlib.sha256(raw).hexdigest(),'script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'case':str(case),'command':args,'start_ns':start,'end_ns':time.time_ns(),'exit':p.returncode,'receipt':json.loads(receipt.read_bytes())}
(case/'diagnostic-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
