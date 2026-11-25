#!/usr/bin/env python3
"""Notify on package inventory changes at graphical login, without a second updater."""
import hashlib
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from files import write

status=Path('/var/lib/debian-workstation/security-status.json')
if status.exists():
    digest=hashlib.sha256(status.read_bytes()).hexdigest()
    marker=Path.home()/'.local/state/debian-workstation/security-notified'
    if not marker.exists() or marker.read_text()!=digest:
        subprocess.run(['notify-send','--urgency=normal','Workstation package security review',
                        'Debian/Mint library inventory changed. Review /var/lib/debian-workstation/security-status.json. Debian security packages take precedence; accent styling may change.'],check=True)
        write(marker,digest,0o600)
