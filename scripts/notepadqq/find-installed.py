#!/usr/bin/env python3
"""Find one managed Notepadqq, including Gear Lever's KEEP-mode name suffix."""
import json
import re
import sys
import configparser
import os
from pathlib import Path
import stat
import tempfile


def find_entry(document):
    if not isinstance(document, dict) or document.get('schema_version') != 1:
        raise ValueError('Unsupported Gear Lever JSON schema; expected schema_version 1')
    installed = document.get('installed')
    if not isinstance(installed, list):
        raise ValueError('Invalid Gear Lever installed-app inventory')
    matches = []
    for app in installed:
        if not isinstance(app, dict) or not isinstance(app.get('name'), str):
            raise ValueError('Invalid Gear Lever installed-app entry')
        # KEEP mode appends a version, or a content hash when version is absent.
        # Match the complete name, never a substring such as "Notepadqq Tools".
        if re.fullmatch(r'Notepadqq(?: \([^()\r\n]+\))?', app['name'], re.IGNORECASE):
            path = app.get('path')
            if not isinstance(path, str) or not path.startswith('/') or any(c in path for c in '\x00\r\n'):
                raise ValueError('Invalid managed Notepadqq path in Gear Lever inventory')
            matches.append(app)
    if len(matches) > 1:
        raise ValueError('Multiple managed Notepadqq entries found; review them in Gear Lever before retrying')
    return matches[0] if matches else None


def find_installed(document):
    entry = find_entry(document)
    return entry['path'] if entry else ''


def regular_path(path):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError(f'Refusing symbolic link in launcher/backup path: {path}')
    if path.exists() and not path.is_file():
        raise ValueError(f'Expected a regular file: {path}')


def repair_name(entry):
    if entry is None:
        raise ValueError('No managed Notepadqq entry found')
    desktop_id = entry.get('desktop_id')
    if not isinstance(desktop_id, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+\.desktop', desktop_id):
        raise ValueError('Missing or unsafe Gear Lever desktop_id')
    launcher = Path.home()/'.local/share/applications'/desktop_id
    regular_path(launcher)
    original = launcher.read_bytes()
    text = original.decode('utf-8')
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str
    config.read_string(text)
    section = config['Desktop Entry']
    if (section.get('TryExec') != entry['path'] or section.get('X-AppImage-Name') != 'Notepadqq'
            or not Path(entry['path']).is_file()):
        raise ValueError('Launcher does not match the managed Notepadqq AppImage; refusing to edit it')
    name = section.get('Name', '')
    if name != 'Notepadqq' and not re.fullmatch(r'Notepadqq \([^()\r\n]+\)', name):
        raise ValueError('Launcher has a custom name; review it before changing it')
    # Change only generated Name values in the primary group. Preserve Exec,
    # TryExec, icon, update metadata, comments, actions and unrelated localized text.
    primary = False
    lines = []
    for line in text.splitlines(keepends=True):
        if line.strip().startswith('['):
            primary = line.strip() == '[Desktop Entry]'
        if primary and re.fullmatch(r'Name(?:\[[^\]\r\n]+\])?=Notepadqq \([^()\r\n]+\)\r?\n?', line):
            ending = '\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''
            line = line.split('=', 1)[0] + '=Notepadqq' + ending
        lines.append(line)
    replacement = ''.join(lines).encode('utf-8')
    if replacement == original:
        print('Notepadqq menu name is already correct.')
        return
    backup = Path.home()/'.local/state/debian-workstation/backups/notepadqq'/desktop_id
    regular_path(backup)
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        with backup.open('xb') as output:
            output.write(original)
        backup.chmod(0o600)
    mode = stat.S_IMODE(launcher.stat().st_mode)
    descriptor, temporary = tempfile.mkstemp(prefix='.notepadqq-', dir=launcher.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(replacement)
        os.chmod(temporary, mode)
        os.replace(temporary, launcher)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print('Restored menu name: Notepadqq (launcher and update configuration retained).')


if __name__ == '__main__':
    try:
        document = json.load(sys.stdin)
        if sys.argv[1:] == ['--repair-name']:
            repair_name(find_entry(document))
        elif not sys.argv[1:]:
            print(find_installed(document))
        else:
            raise ValueError('Usage: find-installed.py [--repair-name]')
    except (ValueError, OSError, KeyError, configparser.Error) as error:
        sys.exit(f'Notepadqq lookup failed: {error}')
