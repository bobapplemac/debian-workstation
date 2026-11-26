#!/usr/bin/env python3
"""Prepare/verify two native Cinnamon presentation fixes without executing its code."""
import argparse
import ast
from pathlib import Path
import sys

CLOCK_ANCHOR = '        self.label.set_alignment(0.5, 0.5)\n'
CLOCK_PATCH = CLOCK_ANCHOR + '        self.label.set_justify(Gtk.Justification.CENTER)\n'
NAME_ANCHOR = '        self.entry_box.pack_end(button_box, False, False, 0)\n'
NAME_PATCH = NAME_ANCHOR + '''
        # Center the native account label above the field, excluding side buttons.
        trackers.con_tracker_get().connect(button_box, "size-allocate",
            lambda _widget, allocation: self.realname_label.set_margin_end(allocation.width))
'''
SPECS = (
    ('clock.py', 'ClockWidget', CLOCK_ANCHOR, CLOCK_PATCH,
     ('        self.label = Gtk.Label()', '        self.label.set_line_wrap(True)'),
     'self.label.set_justify('),
    ('unlock.py', 'UnlockDialog', NAME_ANCHOR, NAME_PATCH,
     ('        self.box.pack_start(self.realname_label, False, False, 10)',
      '        self.entry_box.pack_start(self.password_entry, False, False, 15)',
      '        self.realname_label.set_halign(Gtk.Align.CENTER)'),
     'self.realname_label.set_margin_end('),
)


def constructor(text, name):
    tree = ast.parse(text)
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name]
    if len(classes) != 1:
        raise ValueError(f'Expected one native {name} class')
    functions = [node for node in classes[0].body if isinstance(node, ast.FunctionDef) and node.name == '__init__']
    if len(functions) != 1:
        raise ValueError(f'Expected one {name} constructor')
    node = functions[0]
    lines = text.splitlines(keepends=True)
    return ''.join(lines[:node.lineno-1]), ''.join(lines[node.lineno-1:node.end_lineno]), ''.join(lines[node.end_lineno:])


def transform(text, spec, verify=False):
    filename, name, anchor, replacement, context, competing = spec
    before, body, after = constructor(text, name)
    if any(item not in body for item in context) or body.count(anchor) != 1:
        raise ValueError(f'{filename}: native layout changed; review before applying presentation fixes')
    if replacement in body and body.count(competing) == 1:
        return text
    if verify:
        raise ValueError(f'{filename}: native presentation fix is missing or changed; rerun the desktop module')
    if competing in body:
        raise ValueError(f'{filename}: conflicting alignment customization; review before changing it')
    result = before + body.replace(anchor, replacement, 1) + after
    compile(result, filename, 'exec')
    return result


def prepare(directory, verify=False):
    result = {}
    for spec in SPECS:
        path = directory / spec[0]
        if any(part.is_symlink() for part in (path, *path.parents)):
            raise ValueError(f'Refusing symlink in native source path: {path}')
        result[spec[0]] = transform(path.read_text(), spec, verify)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'verify'))
    parser.add_argument('--directory', type=Path, default=Path('/usr/share/cinnamon-screensaver'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare' and args.output is None:
        parser.error('prepare requires --output')
    result = prepare(args.directory, verify=args.action == 'verify')
    # Validate BOTH inputs before producing anything for the root installer.
    if args.action == 'prepare':
        args.output.mkdir(parents=True, exist_ok=True)
        for name, text in result.items():
            (args.output/name).write_text(text)
    print('Native Cinnamon clock/date centering and password-field name alignment verified.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, SyntaxError) as error:
        sys.exit(f'Native lock-screen presentation: {error}')
