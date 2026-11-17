"""Retain the actual native-channel failure and reveal its requested row."""
from pathlib import Path
import difflib,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
RUN=REVIEW/'output/windows-neon-381d5a9-20261117T003337'
state=json.loads((RUN/'state.json').read_bytes());assert state['status']=='failed' and state['source_unchanged']
report=REVIEW/'output/animated-channels-result.json';data=json.loads(report.read_bytes())
assert data['checks']==47 and data['failures']==1 and len(data['native_samples'])==3
retained=RUN/'animated-channels-original-result.json';assert not retained.exists();shutil.copy2(report,retained)
source=REVIEW/'tests/animated_channels_smoke.gd';old=source.read_bytes()
before=json.loads((RUN/'source-before.json').read_bytes())['source_sha256']
assert hashlib.sha256(old).hexdigest()==before['tests/animated_channels_smoke.gd']
body=old.decode('utf-8')
token='\t\t\tvar scroll: ScrollContainer=timeline.get_parent();scroll.scroll_vertical=100000;await settled()\r\n\t\t\tvar dense_rows:=Channels.describe(rig.data);var last: String=dense_rows[-1].id'
replacement='\t\t\tvar dense_rows:=Channels.describe(rig.data);var last: String=dense_rows[-1].id\r\n\t\t\t# Reveal this native channel; compact tracks can keep drawing/audio lanes below it.\r\n\t\t\tvar scroll: ScrollContainer=timeline.get_parent();scroll.scroll_vertical=int(timeline.channel_y(row.id,last));await settled()'
assert body.count(token)==1;body=body.replace(token,replacement)
click='\t\t\tawait click(app,Vector2(45,timeline.channel_y(row.id,last)+12),MOUSE_BUTTON_LEFT,true)'
assert body.count(click)==1
body=body.replace(click,'\t\t\tcheck(scroll.get_global_rect().has_point(timeline.get_global_transform()*Vector2(45,timeline.channel_y(row.id,last)+12)),"requested native channel lies inside the scrolled track viewport before input")\r\n'+click)
folder=ROOT/'experiments/neon_timeline_fixture_followup_20261117';folder.mkdir(exist_ok=False)
(folder/'animated_channels_original.gd').write_bytes(old)
(folder/'animated_channels_smoke.gd').write_bytes(body.encode('utf-8'))
patch=''.join(difflib.unified_diff(old.decode().splitlines(True),body.splitlines(True),fromfile='a/tests/animated_channels_smoke.gd',tofile='b/tests/animated_channels_smoke.gd'))
(folder/'animated_channels.patch').write_text(patch,encoding='utf-8',newline='')
old_checks=[line for line in old.decode().splitlines() if 'check(' in line]
new_checks=[line for line in body.splitlines() if 'check(' in line]
assert all(line in new_checks for line in old_checks) and len(new_checks)==len(old_checks)+1
record={'format':'has_neon_native_channel_fixture_successor_1','original_source_sha256':hashlib.sha256(old).hexdigest(),'successor_sha256':hashlib.sha256(body.encode()).hexdigest(),'original_report_sha256':hashlib.sha256(retained.read_bytes()).hexdigest(),'original_actual_checks':47,'original_actual_failures':1,'all_original_assertion_lines_retained':True,'new_visibility_assertions':1,'scroll_input':'requested native channel coordinate instead of all-content end','product_source_changed':False,'successor_runtime':'UNRUN'}
(folder/'PREPARATION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record))
