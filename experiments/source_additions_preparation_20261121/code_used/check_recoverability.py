"""Verify only an explicitly pinned additions source-recovery packet; never run it."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import re
import stat

class Refusal(RuntimeError): pass

ALLOWED_LOGS = {
    "source_tree/output/source-sfm-variant-export-v2-prep-20261121/bases/cpu-v1/exporter.stderr.log": (1174,"f60f2760c3ff58f9046493af245e45d2beeb490520321cecc743bac4ca757ed9"),
    "evidence/components_v3_passed/default_off/import-stdout.log": (41275,"fc00b4f150fab0b90b217c09910015dedbe0691419c3fca304958bb81c66fc69"),
    "evidence/components_v3_passed/default_off/import-stderr.log": (0,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "evidence/components_v3_passed/default_off/unit-stdout.log": (1247,"6f004527d51b48e576d29d71ae39801e9a1461d9de04747214222ca444a9f746"),
    "evidence/components_v3_passed/default_off/unit-stderr.log": (0,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "evidence/components_v3_passed/selection/import-stdout.log": (41393,"49bac29f8855efe83503d8b72db8d0c278442037246e3069b90318b3198ef2a9"),
    "evidence/components_v3_passed/selection/import-stderr.log": (0,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "evidence/components_v3_passed/selection/unit-stdout.log": (1832,"b8c57643ee275573d80b9dba4aed4e3480233986935bfa6c39d9254fb04d72cd"),
    "evidence/components_v3_passed/selection/unit-stderr.log": (0,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "evidence/components_v3_passed/radial/import-stdout.log": (41393,"49bac29f8855efe83503d8b72db8d0c278442037246e3069b90318b3198ef2a9"),
    "evidence/components_v3_passed/radial/import-stderr.log": (0,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "evidence/components_v3_passed/radial/unit-stdout.log": (3429,"6a568ef62c03f68cd375e546be163f1868f4fedbd5bf6760e813eb8867705cb4"),
    "evidence/components_v3_passed/radial/unit-stderr.log": (0,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "evidence/components_v3_passed/all49/import-stdout.log": (41334,"57b48d7d43b473b04806ddd5834171520ed6e6c625c03a60c9a39a4558d257ac"),
    "evidence/components_v3_passed/all49/import-stderr.log": (0,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "evidence/components_v3_passed/all49/unit-stdout.log": (1363,"1b11acb50ae0a08c7cfe1c2b3f525f733404badc018962a318400b76d7342845"),
    "evidence/components_v3_passed/all49/unit-stderr.log": (0,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
}


def need(value, code):
    if not value: raise Refusal(code)

def sha(raw): return hashlib.sha256(raw).hexdigest()

def parse(raw):
    def pairs(rows):
        out={}
        for key,value in rows:
            need(key not in out,'DUPLICATE_JSON_KEY');out[key]=value
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _v: (_ for _ in ()).throw(Refusal('NONFINITE_JSON')))

def relative(name):
    need(type(name) is str and name and ':' not in name and '\\' not in name,'INVALID_RELATIVE_PATH')
    p=PurePosixPath(name)
    need(not p.is_absolute() and '..' not in p.parts and p.as_posix()==name,'INVALID_RELATIVE_PATH')
    return name

def identity(info):
    mode=info.st_mode & ~0o111 if os.name=='nt' and stat.S_ISREG(info.st_mode) else info.st_mode
    return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_nlink,mode,getattr(info,'st_file_attributes',0)&~0x40000)

def read(path, count=None, digest=None):
    before=path.lstat()
    need(stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode) and before.st_nlink==1
        and not getattr(before,'st_file_attributes',0)&0x400 and before.st_size<=8*1024*1024,'UNSAFE_OR_OVERSIZED_FILE')
    with path.open('rb') as stream:
        need(identity(os.fstat(stream.fileno()))==identity(before),'FILE_CHANGED_BEFORE_READ')
        raw=stream.read(before.st_size+1)
        need(identity(os.fstat(stream.fileno()))==identity(before),'FILE_CHANGED_DURING_READ')
    need(len(raw)==before.st_size and identity(path.lstat())==identity(before),'FILE_CHANGED_AFTER_READ')
    need((count is None or len(raw)==count) and (digest is None or sha(raw)==digest),'FILE_PIN_DIFFERS')
    return raw,identity(before)

def paths(root):
    result=set();pending=[root]
    while pending:
        current=pending.pop();info=current.lstat()
        need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'DIRECTORY_ALIAS')
        for path in current.iterdir():
            info=path.lstat()
            need(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'PATH_ALIAS')
            if stat.S_ISDIR(info.st_mode):pending.append(path)
            else:need(stat.S_ISREG(info.st_mode),'NONREGULAR_ENTRY');result.add(path.relative_to(root).as_posix())
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet-root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--manifest-sha256',required=True)
    args=parser.parse_args();root=args.packet_root.absolute()
    need(re.fullmatch('[0-9a-f]{64}',args.manifest_sha256),'MANIFEST_SHA_REQUIRED')
    raw,manifest_identity=read(root/'CONTENTS.json',digest=args.manifest_sha256);doc=parse(raw)
    need(doc.get('format')=='has_source_additions_recovery_contents_1' and doc.get('application_adopted') is False,'CONTENTS_SCOPE')
    rows=doc.get('files');need(type(rows) is list and rows,'CONTENTS_ROWS')
    allowed={};folded=set();verified={}
    for row in rows:
        need(type(row) is dict and set(row)=={'path','bytes','sha256','kind','proposed_repository_path'},'CONTENTS_ROW_SCHEMA')
        name=relative(row['path']);need(name!='CONTENTS.json' and name not in allowed and name.casefold() not in folded,'PATH_COLLISION')
        need(type(row['bytes']) is int and 0<=row['bytes']<=8*1024*1024 and re.fullmatch('[0-9a-f]{64}',row['sha256']),'ROW_PIN_SCHEMA')
        need(row['proposed_repository_path']==doc['proposed_repository_prefix']+'/'+name,'PROPOSED_PATH_DIFFERS')
        need(not re.search(r'(?:^|/)(?:\.git|\.godot|__pycache__)(?:/|$)|\.(?:glb|gltf|blend|has|zip|gma|mdl|vvd|vtx|phy|pmx|vmd|vpd|vrm|png|jpe?g|webp|exr|tga|bmp|dds|vmt|vtf|exe|dll|so|pyc|pyo)$',name,re.I),'FORBIDDEN_ASSET_OR_CACHE')
        if name.endswith('.log'):
            need(ALLOWED_LOGS.get(name)==(row['bytes'],row['sha256']),'UNAPPROVED_LOG')
        allowed[name]=row;folded.add(name.casefold())
    need(paths(root)==set(allowed)|{'CONTENTS.json'},'EXACT_PACKET_PATHSET_DIFFERS')
    for name,row in allowed.items():
        value,stamp=read(root/name,row['bytes'],row['sha256']);verified[name]=(value,stamp)
    for group in doc['frozen_source_folders']:
        prefix='source_tree/'+relative(group['folder'])+'/'
        manifest_name=prefix+'SOURCE_PINS.json'
        source_raw=verified[manifest_name][0]
        need(len(source_raw)==group['manifest_bytes'] and sha(source_raw)==group['manifest_sha256'],'ORIGINAL_MANIFEST_PIN')
        source_doc=parse(source_raw);need(source_doc.get('format')==group['format'],'ORIGINAL_MANIFEST_FORMAT')
        entries=source_doc.get('files')
        if type(entries) is not list:entries=source_doc.get('entries')
        need(type(entries) is list,'ORIGINAL_MANIFEST_ROWS')
        expected={manifest_name}
        for entry in entries:
            name=prefix+relative(entry['path']);need(name in allowed,'MISSING_ARCHIVED_SOURCE_DEPENDENCY')
            need((allowed[name]['bytes'],allowed[name]['sha256'])==(entry['bytes'],entry['sha256']),'SOURCE_MANIFEST_ROW_DIFFERS')
            expected.add(name)
        need(expected=={name for name in allowed if name.startswith(prefix)},'SOURCE_FOLDER_RECOVERY_PATHSET')
        need(len(expected)==group['files'],'SOURCE_FOLDER_COUNT')
    recovery=parse(verified['DEPENDENCY_RECOVERY.json'][0])
    need(recovery['variant_cpu_dependency_count']==10 and len(recovery['variant_cpu_dependencies'])==10,'VARIANT_DEPENDENCY_COUNT')
    for dependency in recovery['variant_cpu_dependencies']:
        row=allowed.get(dependency['archive'])
        need(row is not None and (row['bytes'],row['sha256'])==(dependency['bytes'],dependency['sha256']),'VARIANT_PURE_TEST_DEPENDENCY_MISSING')
    need(sha(verified['evidence/e087_remote_verification.json'][0])=='efd05703177f6fce1a188414ad1491fb24ecc69d6726ad94cd4cd8ecda7f8b9a','E087_REMOTE_RECEIPT_PIN')
    prior=verified['owner_notes/OWNER_REVIEW_FOLLOWUP_2026-11-21.md'][0]
    latest=verified['owner_notes/OWNER_REVIEW_FOLLOWUP_2026-11-21-v2.md'][0]
    need(latest.startswith(prior),'OWNER_NOTE_PREFIX_DIFFERS')
    for name,(value,stamp) in verified.items():
        again,after=read(root/name,len(value),sha(value));need(stamp==after,'ARCHIVE_IDENTITY_CHANGED')
    need(read(root/'CONTENTS.json',digest=args.manifest_sha256)[1]==manifest_identity,'MANIFEST_IDENTITY_CHANGED')
    print(json.dumps({'format':'has_source_additions_recoverability_result_1','status':'PASS','payload_files':len(rows),
        'payload_bytes':sum(row['bytes'] for row in rows),'frozen_source_folders':len(doc['frozen_source_folders']),
        'variant_pure_test_dependencies':10,'application_adopted':False,'unit_tests_or_native_or_Git_executed':False}))
    return 0

if __name__=='__main__':raise SystemExit(main())
