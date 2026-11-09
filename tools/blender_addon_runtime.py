"""Load declared pure Python wheels from a separately selected Blender addon.

Extension-manager installs normally provide these modules. Factory-startup
workers also need their data files on disk, so zipimport alone is insufficient.
Never discovers dependencies from the model or downloads packages at runtime.
"""
from pathlib import Path, PurePosixPath
import hashlib
import stat
import sys
import tomllib
import zipfile


def add_bundled_wheels(addon, output):
    addon=Path(addon).resolve(strict=True)
    wheels=tomllib.loads((addon/'blender_manifest.toml').read_text(encoding='utf-8')).get('wheels',[])
    if not isinstance(wheels,list) or len(wheels)>16:raise ValueError('Invalid addon wheel inventory')
    reports=[]
    for name in wheels:
        if not isinstance(name,str):raise ValueError('Invalid addon wheel name')
        wheel=(addon/name).resolve(strict=True);wheel.relative_to(addon)
        if not wheel.name.endswith('-none-any.whl') or not wheel.is_file() or wheel.stat().st_size>32*1024**2:raise ValueError('Addon dependency requires an installed compatible platform wheel')
        digest=hashlib.sha256(wheel.read_bytes()).hexdigest()
        target=Path(output)/('wheel-'+digest);target.mkdir(parents=True,exist_ok=False)
        with zipfile.ZipFile(wheel) as archive:
            entries=archive.infolist()
            if len(entries)>4096 or sum(x.file_size for x in entries)>64*1024**2:raise ValueError('Addon wheel exceeds extraction budget')
            seen=set()
            for entry in entries:
                path=PurePosixPath(entry.filename)
                if not entry.filename.rstrip('/') or path.is_absolute() or any(x in ('','..','.') or ':' in x for x in entry.filename.rstrip('/').split('/')) or '\\' in entry.filename or stat.S_ISLNK(entry.external_attr>>16):raise ValueError('Unsafe addon wheel path')
                folded=entry.filename.casefold()
                if folded in seen:raise ValueError('Duplicate addon wheel path')
                seen.add(folded)
            archive.extractall(target)
        sys.path.insert(0,str(target))
        reports.append({'name':wheel.name,'sha256':digest})
    return reports
