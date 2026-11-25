#!/usr/bin/env python3
"""Validate optional artwork archives before extracting bounded regular files."""
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile

def extract(archive, destination):
    destination=Path(destination)
    if Path(archive).stat().st_size>128*1024*1024: raise ValueError('ZIP exceeds 128 MiB compressed limit')
    if destination.exists() and any(destination.iterdir()): raise ValueError('Extraction directory must be empty')
    with zipfile.ZipFile(archive) as bundle:
        total=0; names=set()
        entries=bundle.infolist()
        if len(entries)>10000: raise ValueError('Too many archive entries')
        for item in entries:
            name=item.orig_filename.rstrip('/')
            parts=name.split('/')
            mode=item.external_attr>>16
            if (not name or PurePosixPath(name).is_absolute() or '\\' in name or ':' in name
                or any(p in ('','.','..') for p in parts) or name.casefold() in names
                or (stat.S_IFMT(mode) not in (0,stat.S_IFREG,stat.S_IFDIR))): raise ValueError('Unsafe ZIP member')
            names.add(name.casefold()); total+=item.file_size
            if item.file_size>64*1024*1024 or total>512*1024*1024: raise ValueError('ZIP exceeds extraction limits')
        destination.mkdir(parents=True,exist_ok=True)
        for item in entries:
            path=destination/item.filename
            if item.is_dir(): path.mkdir(parents=True,exist_ok=True)
            else:
                path.parent.mkdir(parents=True,exist_ok=True)
                with bundle.open(item) as source, path.open('xb') as target:
                    while chunk:=source.read(1024*1024): target.write(chunk)
                path.chmod(0o644)

if __name__=='__main__':
    try: extract(*sys.argv[1:])
    except (ValueError,OSError,zipfile.BadZipFile) as e: sys.exit(f'Invalid optional asset archive: {e}')
