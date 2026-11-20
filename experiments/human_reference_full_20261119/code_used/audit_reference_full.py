from pathlib import Path
from collections import Counter
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'output/windows-human-reference-1795143503737924800'
def load(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
completion=load(RUN/'completion.json');launch=load(RUN/'launch.json')
assert completion['whole_verifier_pass'] and completion['exit']==0 and completion['child_reaped'] and completion['functional_sources_unchanged'] and completion['revision_unchanged']
assert load(RUN/'source-before.json')==load(RUN/'source-after.json')
report_path=ROOT/'output/verification.json'
assert report_path.stat().st_mtime_ns>=launch['started_ns']
report=load(report_path)
formats=Counter();classifications=Counter();receipts=[];skipped=[]
for row in completion['new_private_receipts']:
    path=Path(row['path']);assert path.is_file() and sha(path)==row['sha256']
    data=load(path);formats[str(data.get('format'))]+=1
    relative=path.relative_to(ROOT).as_posix()
    if '/experiments/' in relative:
        classifications['archived experiment copies']+=1;skipped.append(relative);continue
    if data.get('format')!='studio_private_desktop_1' or not re.fullmatch('HAS_Test_[a-f0-9]{32}',str(data.get('desktop',''))):
        classifications['not launcher receipt']+=1;skipped.append(relative);continue
    classifications['current launcher receipt candidate']+=1
    receipts.append({'path':relative,'sha256':sha(path),**{key:data.get(key) for key in ('desktop','child_pid','exit','seconds','job_closed','desktop_closed','private_window_seen','child_desktop_confirmed','foreground_child_observed','desktop_switch_requested','cancelled','error')}})
desktops=Counter(row['desktop'] for row in receipts)
result={'report_groups':len(report),'core_keys':list(report.get('core',{})),'report_top_keys':list(report),'collector_rows':len(completion['new_private_receipts']),'formats':dict(formats),'classification':dict(classifications),'launcher_candidates':len(receipts),'unique_desktops':len(desktops),'duplicates':{key:value for key,value in desktops.items() if value>1},'exit_counts':dict(Counter(str(row['exit']) for row in receipts)),'unclosed':[row for row in receipts if not row['job_closed'] or not row['desktop_closed']],'unconfirmed':[row for row in receipts if not row['child_desktop_confirmed'] or not row['private_window_seen']],'foreground':[row for row in receipts if row['foreground_child_observed'] or row['desktop_switch_requested']],'nonzero':[row for row in receipts if row['exit']!=0],'seconds':completion['seconds'],'functional_sources':completion['functional_source_count'],'report_sha256':sha(report_path),'receipt_candidates':receipts,'excluded_paths':skipped}
(RUN/'receipt-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:value for key,value in result.items() if key not in ('receipt_candidates','excluded_paths','report_top_keys','core_keys')},indent=2))
print(json.dumps({'top_keys':list(report)},separators=(',',':')))
