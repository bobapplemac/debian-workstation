#!/usr/bin/env python3
"""Validate effective LightDM wrapper settings, not just one config fragment."""
import re
import sys

WRAPPER = '/usr/local/lib/debian-workstation/scripts/session/lightdm-session.sh'


def check(text, installed=False):
    wrappers = re.findall(r'^\s*(?:[A-Z]+\s+)?session-wrapper\s*=\s*(.*?)\s*$', text, re.MULTILINE)
    if not wrappers:
        raise ValueError('No explicit effective LightDM session-wrapper found; inspect sudo lightdm --show-config')
    allowed = {WRAPPER} if installed else {'/etc/X11/Xsession', WRAPPER}
    if any(wrapper not in allowed for wrapper in wrappers):
        raise ValueError('Custom or unsupported LightDM session wrapper: '+', '.join(wrappers)+
                         '. Retain it and integrate its lifecycle explicitly; refusing to replace it.')


if __name__ == '__main__':
    try:
        if sys.argv[1:] not in ([], ['--installed']):
            raise ValueError('Usage: check-wrapper.py [--installed]')
        check(sys.stdin.read(), installed=bool(sys.argv[1:]))
    except ValueError as error:
        sys.exit(str(error))
