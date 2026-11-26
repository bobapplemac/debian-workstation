#!/usr/bin/env python3
"""Find one managed Notepadqq, including Gear Lever's KEEP-mode name suffix."""
import json
import re
import sys


def find_installed(document):
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
            matches.append(path)
    if len(matches) > 1:
        raise ValueError('Multiple managed Notepadqq entries found; review them in Gear Lever before retrying')
    return matches[0] if matches else ''


if __name__ == '__main__':
    try:
        print(find_installed(json.load(sys.stdin)))
    except (ValueError, OSError) as error:
        sys.exit(f'Notepadqq lookup failed: {error}')
