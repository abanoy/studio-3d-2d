"""Read-only exact review and private schema4/capture validation; no launch APIs."""
from pathlib import Path,PurePosixPath
import hashlib,json,os,re,stat,zipfile
PREP_PIN=(123121,'41f9cb3ff0bd38083f2f1ff990ab5ec83b922db0bbfbd30db33090206b64a410')
SEAL_PIN=(381563,'80db2e273e1b583040d0db9f52f27b23c7f632943dee7431ff9df17af2c99a7a')
LABELS=('Junko hair review','Saved face scene','Saved fan scene')
def identity(p):
 s=p.lstat();return [str(v) for v in (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink,s.st_mode,getattr(s,'st_file_attributes',0))]
def tree(H,root):
 found=set();aliases=set()
 def error(e):raise e
 for here,dirs,names in os.walk(H.safe(root),followlinks=False,onerror=error):
  for n in dirs+names:
   p=H.safe(Path(here)/n);relative=p.relative_to(root).as_posix();H.need(relative.casefold() not in aliases,'REVIEW_CASE_ALIAS');aliases.add(relative.casefold())
  for n in names:found.add((Path(here)/n).relative_to(root).as_posix())
 return found
def exact_pin(H,p,row):
 b=H.read(p,row['bytes'],row['sha256'],limit=64*1024*1024)
 H.need(identity(p)==row['identity'],'PROTECTED_NATIVE_IDENTITY_CHANGED');return b
def admit_review(H,review,seal_path,revision,frozen):
 seal=H.parse(H.read(seal_path,*SEAL_PIN,limit=4*1024*1024))
 H.need(seal.get('format')=='has_private_c315_review_readonly_seal_1' and seal.get('private_do_not_publish') is True
        and Path(seal.get('review',''))==review,'EXACT_PRIVATE_REVIEW_SEAL')
 prep=H.parse(H.read(review/'PREPARATION.json',*PREP_PIN))
 H.need(prep.get('format')=='has_editor_camera_c315_owner_review_prepared_1' and prep.get('source_commit')==revision
        and prep.get('status')=='PREPARED_NOT_RUNTIME_VERIFIED' and prep.get('source_mode')=='git_revision_runtime_scope'
        and prep.get('source_file_count')==1106 and len(frozen)==1106
        and prep.get('experimental_overlays') is False and prep.get('owner_originals_modified') is False
        and prep.get('installed_studio_replaced') is False,'EXACT_C315_PREPARED_REVIEW')
 H.need(all(prep.get(k) is False for k in ('graphics_launched','normal_startup_verified','package_replay_verified')),'PREPARATION_HISTORICAL_HOLD_FLAGS')
 hashes=prep.get('source_hashes');H.need(type(hashes) is dict and set(hashes)==set(frozen),'REVIEW_EXACT_COMMITTED_RUNTIME_DOMAIN')
 for name,b in frozen.items():
  H.need(hashes[name]==H.sha(b),'REVIEW_MANIFEST_GIT_RUNTIME_BYTES')
  H.read(review/'Studio'/H.rel(name),len(b),H.sha(b))
 H.need(tree(H,review)==set(seal['files']) and len(seal['files'])==1116,'EXACT_ORIGINAL_REVIEW_MEMBERSHIP')
 for name,row in seal['files'].items():exact_pin(H,review/H.rel(name),row)
 for name,saved in seal['directories'].items():
  p=review if name=='.' else review/H.rel(name)
  H.need(identity(H.safe(p))==saved,'REVIEW_DIRECTORY_IDENTITY_CHANGED')
 expected_override=('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(prep['profile'])+'\n').encode()
 H.need(H.read(review/'Studio/override.cfg')==expected_override,'UNCHANGED_OWNER_INTERACTIVE_PROFILE_OVERRIDE')
 projects=prep.get('projects');launchers=prep.get('launchers')
 H.need(type(projects) is list and [r.get('label') for r in projects]==list(LABELS)
        and type(launchers) is list and len(launchers)==4,'EXACT_THREE_PROJECTS_FOUR_LAUNCHERS')
 for row in projects:
  H.need(Path(row['copy'])==review/'Examples'/(row['label']+'.has') and row.get('original_preflight_passed') is True
         and row.get('copy_preflight_passed') is True,'EXACT_PREPARED_PACKAGE_PATH')
  for key,pin in (('source','source_pin'),('older_review_copy','older_review_copy_pin'),('copy','copy_pin')):exact_pin(H,Path(row[key]),row[pin])
 for row in seal['protected_projects_and_older_copies']:exact_pin(H,Path(row['path']),row['pin'])
 for row in launchers:
  name=H.rel(row['path']);H.need(Path(name).name==name and name.endswith('.bat') and row.get('owner_operated_only') is True,'PREPARED_OWNER_ONLY_LAUNCHER')
  H.read(review/name,row['bytes'],row['sha256'])
 exact_pin(H,Path(prep['pythonw']['path']),prep['pythonw']['pin'])
 return prep,seal
def member_path(H,name):
 H.rel(name)
 for p in PurePosixPath(name).parts:
  H.need(p==p.rstrip(' .') and not re.search(r'[<>"|?*\x00-\x1f]',p)
         and p.split('.')[0].upper() not in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]},'UNSAFE_PACKED_MEMBER')
 return name
def metadata(H,package):
 H.read(package,limit=64*1024*1024)
 with zipfile.ZipFile(package) as z:
  entries=z.infolist();H.need(2<=len(entries)<=2048,'BOUNDED_PACKED_MEMBER_COUNT')
  indexed={};total=0
  for e in entries:
   member_path(H,e.filename);H.need(e.filename.casefold() not in indexed and not e.is_dir() and not e.flag_bits&1
       and not stat.S_ISLNK(e.external_attr>>16) and e.compress_type in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED),'PLAIN_UNIQUE_PACKED_MEMBERS')
   indexed[e.filename.casefold()]=e;total+=e.file_size
   H.need(0<=e.file_size<=128*1024*1024 and total<=512*1024*1024,'PACKED_EXPANDED_SIZE_BOUNDS')
  for n in ('has.json','project.json'):H.need(n in indexed and indexed[n].file_size<=1024*1024,'BOUNDED_PACKED_PROJECT_METADATA')
  header=H.parse(z.read('has.json'));project=H.parse(z.read('project.json'))
  H.need(header.get('format')=='hybrid_animation_studio' and type(header.get('version')) is int and header['version']==1
         and header.get('storage')=='packed','EXACT_PACKED_CONTAINER')
  H.need(type(project) is dict and type(project.get('schema_version')) is int and project['schema_version']==4
         and set(project)<={'schema_version','world','camera_keys','video','editor','layers','audio','palette'},'EXACT_OBSERVED_SCHEMA4_NO_IMPLICIT_MIGRATION')
  payload=header.get('payload');assets=header.get('assets')
  H.need(type(payload) is list and type(assets) is list and 1<=len(payload)<=2047,'EXACT_PACKED_PAYLOAD_LIST')
  names=set()
  for row in payload:
   n=member_path(H,row['path']);H.need(n not in names and type(row.get('bytes')) is int and row['bytes']>=0
       and re.fullmatch('[0-9a-f]{64}',row.get('sha256','')) is not None,'TYPED_PACKED_PAYLOAD_PIN');names.add(n)
   H.need(n.casefold() in indexed and indexed[n.casefold()].filename==n and indexed[n.casefold()].file_size==row['bytes'],'EXACT_PACKED_ENTRY_SIZE_NAME')
   digest=hashlib.sha256();count=0
   with z.open(n) as f:
    for b in iter(lambda:f.read(1024*1024),b''):digest.update(b);count+=len(b)
   H.need(count==row['bytes'] and digest.hexdigest()==row['sha256'],'ALL_PACKED_PAYLOAD_SHA_CRC_READBACK')
  H.need({e.filename for e in entries}==names|{'has.json'},'NO_UNDECLARED_PACKED_PAYLOAD')
  for row in assets:
   H.need(type(row) is dict and any(row.get('path')==r['path'] and row.get('sha256')==r['sha256'] and row.get('bytes')==r['bytes'] for r in payload),'EVERY_ASSET_IS_EXACT_PACKED_PAYLOAD')
 project.setdefault('palette',[])
 objects=project['world']['objects'];cels=sum(len(l['cels']) for l in project['layers'])
 return project,payload,20+len(objects)+cels
def verify_case(H,case,report,expected,payload,package,studio,profile,compare):
 H.need(report.get('format')=='has_owner_review_replay_1' and type(report.get('failures')) is int
        and report['failures']==0 and report.get('native_readbacks_at_finish')==0,'REPLAY_ALL_NATIVE_CHECKS_AND_ZERO_READBACKS')
 H.need(report.get('package')==str(package).replace('\\','/') and Path(report.get('project_root','')).resolve()==studio.resolve(),
        'ACTUAL_REVIEW_RES_ROOT_AND_PACKAGE')
 user_profile=H.safe(Path(report.get('profile','')))
 H.need(user_profile.is_relative_to(case/'User') and profile in str(user_profile),'ISOLATED_REPLAY_PROFILE_NOT_OWNER_INTERACTIVE')
 startup=report.get('normal_startup',{});recovery=startup.get('result',{})
 H.need(all(startup.get(k) is True for k in ('signal_seen','home_visible','empty','simple'))
        and recovery.get('restored') is False and recovery.get('cancelled') is False,'REAL_NORMAL_AUTOMATIC_RECOVERY_HOME_STARTUP')
 checks=report.get('checks');expected_count=20+len(expected['world']['objects'])+sum(len(l['cels']) for l in expected['layers'])
 H.need(type(checks) is list and len(checks)==expected_count and all(type(r) is dict and r.get('ok') is True for r in checks),'EXACT_DYNAMIC_REPLAY_ASSERTION_COUNT')
 cache=H.safe(Path(report['project_folder']));cache_root=H.safe(case/'has-cache')
 H.need(cache.is_dir() and cache!=cache_root and cache.is_relative_to(cache_root),'FRESH_CONTAINED_UNPACKED_CACHE')
 for row in payload:H.read(cache/H.rel(row['path']),row['bytes'],row['sha256'],limit=128*1024*1024)
 differences={}
 for phase in ('before','after'):
  actual=H.parse(H.read(case/('observed-'+phase+'.json'),limit=4*1024*1024));differences[phase]=compare(expected,actual)
 H.json_new(case/'PRIVATE_STATE_COMPARISON.json',{'contract':'Unchanged committed owner-review compare: exact tree/IDs/bools/strings; finite numeric absolute1e-12/no relative tolerance; only absent schema4 palette becomes[].',
           'differences':differences})
 H.need(not any(differences.values()),'ALL_SAVED_PROJECT_FIELDS_PRESERVED')
 H.need(report.get('camera_before')==report.get('camera_after'),'EXACT_SHOT_CAMERA_PRESERVED')
 hashes=[]
 for key,filename in (('setup_image','setup.png'),('focus_image','focus.png'),('native_setup','native-setup.png'),('native_focus','native-focus.png')):
  image=report.get(key,{});H.need(image.get('empty') is False and type(image.get('save_error')) is int and image['save_error']==0
       and Path(image.get('png','')).resolve()==(case/filename).resolve()
       and re.fullmatch('[0-9a-f]{64}',image.get('pixel_sha256','')) is not None,'FOUR_PRIVATE_CAPTURE_FILES')
  b=H.read(case/filename,limit=32*1024*1024);hashes.append(H.sha(b))
 H.need(report['native_setup']['pixel_sha256']==report['native_focus']['pixel_sha256']
        and all(report[k]['width']==expected['video']['width'] and report[k]['height']==expected['video']['height'] for k in ('native_setup','native_focus')),
        'EXACT_NATIVE_SETUP_FOCUS_PIXELS_AND_OUTPUT_DIMENSIONS')
 H.need(len(report.get('runtime_objects',[]))==len(expected['world']['objects']) and all(r.get('asset_sha256')==r.get('stored_sha256') for r in report['runtime_objects']),
        'EVERY_REAL_RUNTIME_ASSET_SHA')
 return {'checks':expected_count,'package_sha256':H.sha(H.read(package,limit=64*1024*1024)),
         'payloads_sha_verified':len(payload),'saved_objects':len(expected['world']['objects']),
         'saved_cels':sum(len(l['cels']) for l in expected['layers']),'private_image_count':4,'private_image_sha256':hashes,
         'normal_startup_and_cold_worker_verified':True,'source_root_is_actual_review':True,'saved_state_unchanged':True,
         'native_Setup_Focus_pixels_equal':True,'native_readbacks_at_finish':0}
