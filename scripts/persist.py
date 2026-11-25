#!/usr/bin/env python3
"""Copy only implementation inputs to root-owned durable storage."""
import os
from pathlib import Path
import sys
from files import safe, write

def main(source,destination):
    source,destination=Path(source).resolve(),Path(destination)
    if os.geteuid()!=0: raise ValueError('Persisting the implementation requires root')
    if any(p.is_symlink() for p in [destination,*destination.parents]): raise ValueError('Symlink in persistent implementation path')
    destination.mkdir(mode=0o755,parents=True,exist_ok=True)
    paths=[Path('install.sh')]
    for name in ('README.md','LICENSE'):
        if (source/name).is_file(): paths.append(Path(name))
    for directory in ('lib','modules','scripts','assets','docs'):
        for path in (source/directory).rglob('*'):
            if '__pycache__' in path.parts or path.name.endswith(('.pyc','.before-debian-workstation')): continue
            if directory=='docs' and ('history' in path.parts or path.suffix!='.md'): continue
            if path.is_symlink(): raise ValueError(f'Symlink in implementation inputs: {path}')
            if path.is_file(): paths.append(path.relative_to(source))
    for relative in paths:
        target=destination/relative
        if source/relative==target: continue
        # Write text with controlled permissions, ignoring Windows/Git archive mode bits.
        write(target,(source/relative).read_text(),0o644)
        os.chown(target,0,0)
    for root,dirs,files in os.walk(destination):
        path=Path(root)
        if path.is_symlink(): raise ValueError('Symlink in installed implementation')
        os.chmod(path,0o755);os.chown(path,0,0)

if __name__=='__main__':
    try: main(*sys.argv[1:])
    except (OSError,ValueError) as e: sys.exit(str(e))
