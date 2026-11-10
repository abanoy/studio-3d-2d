"""Bounded, read-only case-insensitive lookup for loose Source resources.

Source paths are case-insensitive; Linux filesystems may preserve differing case.
Ambiguous names and paths leaving an explicit mount are refused, never guessed.
"""
from pathlib import Path,PurePosixPath
import os

SIDECARS=('.vvd','.dx90.vtx','.dx80.vtx','.sw.vtx','.vtx','.phy','.ani')
MAX_NAMES=100000

class CaseResolver:
 def __init__(self,root):
  self.root=Path(root).resolve(strict=True)
  if not self.root.is_dir():raise ValueError('Loose Source mount must be a directory')
  self.cache={};self.names=0
 def _entries(self,directory):
  stamp=directory.stat();identity=(stamp.st_dev,stamp.st_ino,stamp.st_mtime_ns);old=self.cache.get(directory)
  # NTFS can defer directory last-write updates after a child is created. A
  # matching timestamp cannot certify this name inventory on Windows; refresh
  # it within the same per-directory and total cached-name budgets.
  if old and old[0]==identity and os.name!='nt':return old[1]
  rows={};count=0
  with os.scandir(directory) as entries:
   for entry in entries:
    count+=1
    if count>MAX_NAMES:raise ValueError('Loose Source directory exceeds100000names')
    key=entry.name.casefold();rows[key]=None if key in rows else entry.name
  total=self.names-(old[2] if old else 0)+count
  if total>MAX_NAMES:raise ValueError('Loose Source lookup exceeds100000cached names')
  self.names=total;self.cache[directory]=(identity,rows,count);return rows
 def find(self,relative):
  relative=str(relative).replace('\\','/');parts=PurePosixPath(relative).parts
  if not relative or relative.startswith('/') or ':' in relative or any(p in ('','..','.') for p in relative.split('/')) or '//' in relative or len(relative)>512:raise ValueError('Unsafe loose Source resource path')
  current=self.root
  for part in parts:
   if not current.is_dir():return None
   rows=self._entries(current);key=part.casefold()
   if key not in rows:return None
   if rows[key] is None:raise ValueError('Ambiguous case-insensitive Source resource: '+relative)
   current=(current/rows[key]).resolve()
   if not current.is_relative_to(self.root):raise ValueError('Source resource escaped its explicit content mount')
  return current if current.is_file() else None

def sidecars(source):
 source=Path(source);resolver=CaseResolver(source.parent)
 return {suffix:path for suffix in SIDECARS if (path:=resolver.find(source.with_suffix(suffix).name)) is not None}
