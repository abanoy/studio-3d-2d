from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'tests/scenario_d_smoke.gd';before=path.read_bytes()
assert before==(ROOT/'output/source-import-off-followup-v3-prep-20261121/payload/tests/scenario_d_smoke.gd').read_bytes()
old=b'   if Vector3(pixel.r,pixel.g,pixel.b).distance_squared_to(color)<.001:return Vector2(x*2+1,y*2+1)'
new='''   if Vector3(pixel.r,pixel.g,pixel.b).distance_squared_to(color)<.001:
    # Scene setup uses its actual variable mask extent; Camera focus uses half HD.
    # Convert a mask-pixel centre through scene UV and the current film rectangle.
    var uv: Vector2=(Vector2(x,y)+Vector2.ONE*.5)/Vector2(image.get_size())
    var area: Rect2=app.canvas.scene_rect();var film: Rect2=app.canvas.image_rect()
    return (area.position+uv*area.size-film.position)/film.size*app.canvas.resolution'''.encode()
assert before.count(old)==1
after=before.replace(old,new,1)
old=b' check(app.world_selection.menu.visible,"D2 actual context menu opens on the frozen humanoid")'
new=old+b'\n check(app.world_selection.selected==id and app.renderer.active_instance_id==id,"D2 context menu targets the intended frozen humanoid after actual mask-coordinate conversion")'
assert after.count(old)==1;after=after.replace(old,new,1)
old=b' app.world_selection.menu.id_pressed.emit(1);await settled();var neutral:=true'
new=b' app.world_selection.menu.id_pressed.emit(1);await settled();actor=app.renderer.world_runtime.instance(id);var neutral:=true'
assert after.count(old)==1;after=after.replace(old,new,1)
prep=ROOT/'output/source-scenario-d-mask-coordinates-prep-20261121';prep.mkdir(exist_ok=False)
(prep/'before.gd').write_bytes(before);(prep/'after.gd').write_bytes(after)
failed=ROOT/'output/import-off-followup-scoped-1795256474017879900'
for name in ('completion.json','scenario-d/stdout.log','scenario-d/stderr.log'):
    target=prep/'failure'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((failed/name).read_bytes())
assert path.read_bytes()==before;path.write_bytes(after);assert path.read_bytes()==after
correction={'format':'has_scenario_d_selection_coordinate_correction_1','status':'APPLIED_RUNTIME_UNRUN',
 'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),
 'failed_writer_checks':29,'failed_writer_failures':3,'old_world_contacts':0,'old_horizontal_displacement':0.000204751137061976,
 'correction':'Replace fixed x2 mask mapping with the inverse of actual scene_uv at a pixel centre; explicitly assert selected and active actor IDs.',
 'contact_or_pose_assertions_removed':False,'numeric_or_pixel_tolerances_changed':False,
 'new_writer_expected_checks':30,'reader_expected_checks':4,'production_code_changed':False}
(prep/'CORRECTION.json').write_text(json.dumps(correction,indent=2)+'\n',encoding='utf-8')
rows=[]
for p in sorted(prep.rglob('*')):
    if p.is_file():
        raw=p.read_bytes();rows.append({'path':p.relative_to(prep).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
(prep/'SOURCE_PINS.json').write_text(json.dumps({'format':'has_scenario_d_coordinate_pins_1','files':rows},indent=2)+'\n',encoding='utf-8')
raw=(ROOT/'output/run_import_off_followup_remaining_20261121.py').read_text()
start=raw.index("      ('first-movie',");end=raw.index("      ('scenario-d',",start);raw=raw[:start]+raw[end:]
raw=raw.replace('has_import_off_remaining_scoped_1','has_import_off_scenario_d_scoped_1').replace("['checks']==29","['checks']==30").replace('29writer+4cold','30writer+4cold').replace('len(rows)==4','len(rows)==2').replace('Expected four remaining actual scoped private jobs','Expected two scenario D actual private jobs')
target=ROOT/'output/run_import_off_scenario_d_scoped_20261121.py';assert not target.exists();target.write_text(raw,encoding='utf-8')
print(json.dumps(correction))
