#!/usr/bin/env python3
"""Strict non-executable configuration. Emits NUL-separated key/value pairs."""
import pathlib
import re
import sys

DEFAULTS = dict(DESKTOP_USER='', CREATE_USER='yes', PASSWORDLESS_SUDO='no',
                HYPERVISOR='auto', INSTALL_NOTEPADQQ='yes', INSTALL_1PASSWORD='yes',
                INSTALL_1PASSWORD_CLI='yes', INSTALL_CORE_FONTS='yes',
                CURSOR_ARCHIVE='', FONT_ARCHIVE='', NEMO_REF='main', GRAPHICS_DRIVERS='ask')

def parse(text):
    result = DEFAULTS.copy()
    seen = set()
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, sep, value = line.partition('=')
        if not sep or key not in result or key in seen or '\x00' in value:
            raise ValueError(f'Invalid or duplicate configuration key at line {number}')
        seen.add(key)
        result[key] = value
    for key, value in result.items():
        if key.startswith('INSTALL_') or key in ('CREATE_USER', 'PASSWORDLESS_SUDO'):
            if value not in ('yes', 'no'): raise ValueError(f'{key} must be yes or no')
    if result['HYPERVISOR'] not in ('auto', 'none', 'vmware', 'kvm', 'microsoft'):
        raise ValueError('HYPERVISOR must be auto, none, vmware, kvm or microsoft')
    if result['GRAPHICS_DRIVERS'] not in ('ask', 'yes', 'no'):
        raise ValueError('GRAPHICS_DRIVERS must be ask, yes or no')
    if result['DESKTOP_USER'] and not re.fullmatch(r'[a-z_][a-z0-9_-]{0,31}', result['DESKTOP_USER']):
        raise ValueError('Invalid desktop username')
    if not re.fullmatch(r'[a-zA-Z0-9_./-]+', result['NEMO_REF']) or result['NEMO_REF'].startswith('-'):
        raise ValueError('Invalid Nemo repository revision')
    for key in ('CURSOR_ARCHIVE', 'FONT_ARCHIVE'):
        if result[key] and not result[key].startswith('/'): raise ValueError(f'{key} requires an absolute path')
    return result

if __name__ == '__main__':
    try:
        config = parse(pathlib.Path(sys.argv[1]).read_text() if len(sys.argv)>1 else '')
        sys.stdout.buffer.write(b''.join(k.encode()+b'\0'+v.encode()+b'\0' for k,v in config.items()))
    except (ValueError, OSError) as e:
        sys.exit(str(e))
