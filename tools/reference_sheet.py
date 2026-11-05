"""Strict optional schema7 reference-sheet metadata; never execute/follow metadata."""
import math
FORMAT='studio_reference_sheet_1'
MAX_FILE=16*1024*1024

def error(value):
    if not isinstance(value,dict) or set(value)!={'format','name','sha256','path'} or value.get('format')!=FORMAT:return 'Invalid project reference sheet identity'
    name=value.get('name');digest=value.get('sha256')
    if not isinstance(name,str) or not 1<=len(name)<=200 or any(ord(c)<32 or ord(c)==127 or 0xd800<=ord(c)<=0xdfff or c in '/\\:' for c in name):return 'Invalid reference sheet name'
    if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):return 'Invalid reference sheet checksum'
    if value.get('path')!='references/'+digest+'.png':return 'Unsafe project reference sheet path'
    return ''

def unwrap(value):
    version=value.get('content_schema_version')
    if type(version) not in (int,float) or not math.isfinite(version) or version not in (3,4,5,6):return None,'Invalid schema7 content version'
    why=error(value.get('reference_sheet'))
    if why:return None,why
    base=dict(value);base['schema_version']=int(base.pop('content_schema_version'));base.pop('reference_sheet')
    return base,''
