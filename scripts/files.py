#!/usr/bin/env python3
"""Small atomic file/INI updates with backups, symlink checks and ownership records."""
import configparser
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile

def safe(path):
    path=Path(path)
    if any(p.is_symlink() for p in [path,*path.parents]): raise ValueError(f'Refusing symbolic link path: {path}')
    if path.exists() and not path.is_file(): raise ValueError(f'Expected a file: {path}')
    return path

def write(path, text, mode=0o644, managed=False):
    path=safe(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    state=Path.home()/'.local/state/debian-workstation/files.json'
    registry={}
    if managed:
        safe(state)
        if state.exists(): registry=json.loads(state.read_text())
        if path.exists() and path.read_text()!=text:
            expected=registry.get(str(path))
            if expected!=hashlib.sha256(path.read_bytes()).hexdigest(): raise ValueError(f'Existing unmanaged or edited file: {path}; move it aside after reviewing')
    if not path.exists() or path.read_text()!=text:
        if path.exists():
            backup=safe(path.with_name(path.name+'.before-debian-workstation'))
            if not backup.exists(): backup.write_bytes(path.read_bytes()); backup.chmod(mode)
        fd,temp=tempfile.mkstemp(dir=path.parent,prefix='.dw-')
        try:
            with os.fdopen(fd,'w',newline='\n') as f: f.write(text)
            os.chmod(temp,mode); os.replace(temp,path)
        finally:
            if os.path.exists(temp): os.unlink(temp)
    if managed:
        registry[str(path)]=hashlib.sha256(text.encode()).hexdigest()
        write(state,json.dumps(registry,indent=2)+'\n',0o600)

def ini(path, section, changes):
    path=safe(path)
    config=configparser.ConfigParser(interpolation=None)
    config.optionxform=str
    if path.exists(): config.read(path)
    if not config.has_section(section): config.add_section(section)
    for key,value in changes.items(): config[section][key]=str(value)
    output=io.StringIO(); config.write(output,space_around_delimiters=False)
    write(path,output.getvalue())

def autostart(root):
    # Exec is a fixed system path, never interpolated user-controlled shell code.
    write(Path.home()/'.config/autostart/debian-workstation.desktop',
          '[Desktop Entry]\nType=Application\nName=Complete Debian Workstation setup\n'
          'OnlyShowIn=X-Cinnamon;\nExec=/bin/bash /usr/local/lib/debian-workstation/scripts/first-login.sh\n'
          'X-GNOME-Autostart-enabled=true\n',managed=True)

def appearance(root):
    root=Path(root)
    for version in ('3.0','4.0'):
        folder=Path.home()/'.config'/('gtk-'+version)
        write(folder/'debian-workstation-window-controls.css',(root/'assets'/('gtk-'+version)/'window-controls.css').read_text(),managed=True)
        entry='@import url("debian-workstation-window-controls.css");'
        path=safe(folder/'gtk.css'); existing=path.read_text() if path.exists() else ''
        if entry not in existing: write(path,entry+'\n'+existing)
    for theme,slot in [('Mint-X','scalable'),('Mint-Y','symbolic')]:
        for source in (root/'assets/glyphs').glob('*.svg'):
            write(Path.home()/'.local/share/icons'/theme/'actions'/slot/source.name,source.read_text(),managed=True)
    write(Path.home()/'.local/bin/mint-y-app-icons.py',(root/'scripts/desktop/mint-y-app-icons.py').read_text(),0o755,managed=True)

def cursor(theme):
    for directory in ('.icons/default','.local/share/icons/default'):
        ini(Path.home()/directory/'index.theme','Icon Theme',{'Inherits':theme})
    import re
    path=safe(Path.home()/'.Xresources'); text=path.read_text() if path.exists() else ''
    lines=[line for line in text.splitlines() if not re.match(r'^\s*Xcursor\.(theme|size)\s*:',line)]
    write(path,'\n'.join(lines+[f'Xcursor.theme: {theme}','Xcursor.size: 32'])+'\n')

def greeter(theme):
    ini('/etc/lightdm/lightdm-gtk-greeter.conf','greeter',dict(
        **{'user-background':'false','theme-name':'Adwaita','icon-theme-name':'Papirus',
           'cursor-theme-name':theme,'cursor-theme-size':'32','default-user-image':'#avatar-default',
           'font-name':'Sans 12','xft-dpi':'96','xft-antialias':'true','xft-hintstyle':'hintslight',
           'xft-rgba':'rgb','position':'50%,center 50%,center','panel-position':'top',
           'indicators':'~host;~spacer;~session;~clock;~power','clock-format':'%a, %-m/%-d/%Y %-I:%M %p'}))

if __name__=='__main__':
    try:
        action=sys.argv[1]
        if action=='autostart': autostart(sys.argv[2])
        elif action=='appearance': appearance(sys.argv[2])
        elif action=='cursor': cursor(sys.argv[2])
        elif action=='greeter': greeter(sys.argv[2])
        else: raise ValueError('Unknown file operation')
    except (ValueError,OSError,configparser.Error) as e: sys.exit(str(e))
