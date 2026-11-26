"""Regression for fresh Gear Lever integration names and safe rerun discovery."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('notepadqq_lookup', ROOT/'scripts/notepadqq/find-installed.py')
lookup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lookup)


def inventory(*apps):
    return {'schema_version': 1, 'installed': list(apps)}


def app(name, path='/home/example/AppImages/notepadqq.appimage'):
    return {'name': name, 'path': path, 'desktop_id': 'notepadqq.desktop',
            'current_version': None, 'manager': None}


def launcher(root, managed):
    path = root/'.local/share/applications/notepadqq.desktop'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('[Desktop Entry]\nType=Application\nName=Notepadqq (543d74)\n'
                    'Name[en_US]=Notepadqq (543d74)\n# preserve comment\n'
                    f'TryExec={managed}\nExec=env DESKTOPINTEGRATION=1 "{managed}" %F\n'
                    'Icon=/existing/icon.png\nX-AppImage-Name=Notepadqq\n'
                    'X-Custom-Key=keep me\n\n[Desktop Action NewWindow]\nName=Notepadqq (action)\nExec=keep-action\n')
    return path


class MenuNameTests(unittest.TestCase):
    def test_repair_preserves_launcher_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            managed = root/'notepadqq.appimage'
            managed.write_bytes(b'unchanged AppImage')
            path = launcher(root, managed)
            before = path.read_bytes()
            entry = app('Notepadqq (543d74)', str(managed))
            with patch.object(Path, 'home', return_value=root):
                lookup.repair_name(entry)
                changed = path.read_bytes()
                self.assertEqual(changed, before.replace(b'Name=Notepadqq (543d74)', b'Name=Notepadqq')
                                 .replace(b'Name[en_US]=Notepadqq (543d74)', b'Name[en_US]=Notepadqq'))
                stamp = path.stat().st_mtime_ns
                lookup.repair_name(entry)
                self.assertEqual(path.stat().st_mtime_ns, stamp)
            self.assertEqual(managed.read_bytes(), b'unchanged AppImage')
            self.assertEqual((root/'.local/state/debian-workstation/backups/notepadqq/notepadqq.desktop').read_bytes(), before)

    def test_rejects_unrelated_launcher_and_custom_name(self):
        for old, new in [('X-AppImage-Name=Notepadqq', 'X-AppImage-Name=Other'),
                         ('Name=Notepadqq (543d74)', 'Name=My editor')]:
            with self.subTest(new=new), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                managed = root/'notepadqq.appimage'
                managed.touch()
                path = launcher(root, managed)
                path.write_text(path.read_text().replace(old, new))
                before = path.read_bytes()
                with patch.object(Path, 'home', return_value=root), self.assertRaises(ValueError):
                    lookup.repair_name(app('Notepadqq (543d74)', str(managed)))
                self.assertEqual(path.read_bytes(), before)

    def test_rejects_unsafe_desktop_id(self):
        entry = app('Notepadqq')
        entry['desktop_id'] = '../other.desktop'
        with self.assertRaises(ValueError):
            lookup.repair_name(entry)


class LookupTests(unittest.TestCase):
    def test_fresh_install_hash_suffix_reported_by_user(self):
        item = app('Notepadqq (543d74)')
        self.assertEqual(lookup.find_installed(inventory(item)), item['path'])

    def test_plain_and_versioned_names(self):
        for name in ('Notepadqq', 'notepadqq', 'Notepadqq (2.1.1)', 'Notepadqq (v2.1.1 beta)'):
            with self.subTest(name=name):
                self.assertEqual(lookup.find_installed(inventory(app(name))), app(name)['path'])

    def test_unrelated_and_empty(self):
        self.assertEqual(lookup.find_installed(inventory()), '')
        for name in ('Notepadqq Tools', 'Other Notepadqq', 'Notepadqq ()', 'Notepadqq (abc) trailing'):
            with self.subTest(name=name):
                self.assertEqual(lookup.find_installed(inventory(app(name))), '')

    def test_ambiguity_stops(self):
        with self.assertRaisesRegex(ValueError, 'Multiple managed'):
            lookup.find_installed(inventory(app('Notepadqq'), app('Notepadqq (543d74)', '/other/notepadqq.appimage')))

    def test_malformed_inventory_stops(self):
        for document in ({'installed': []}, inventory({'path': '/tmp/app'}), inventory(app('Notepadqq', 'relative')),
                         inventory(app('Notepadqq', '/tmp/a\nother')), {'schema_version': 2, 'installed': []}):
            with self.subTest(document=document), self.assertRaises(ValueError):
                lookup.find_installed(document)


@unittest.skipUnless(shutil.which('bash') and Path('/bin/bash').exists(), 'Linux Bash required')
class InstallerTests(unittest.TestCase):
    def test_fresh_install_then_rerun_with_generated_suffix(self):
        import os
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root/'source'
            source.mkdir()
            for name in ('install.sh', 'find-installed.py'):
                shutil.copyfile(ROOT/'scripts/notepadqq'/name, source/name)
            (source/'github-release.py').write_text('from pathlib import Path\nimport sys\nPath(sys.argv[1]).write_bytes(b"test AppImage")\n')
            managed = root/'AppImages/notepadqq.appimage'
            launcher(root, managed)
            document = inventory(app('Notepadqq (543d74)', str(managed)))
            executable = root/'flatpak'
            executable.write_text('#!/usr/bin/env python3\nfrom pathlib import Path\nimport json,sys\n'
                                  f'managed=Path({str(managed)!r})\n'
                                  f'with open({str(root/"calls")!r}, "a") as f: f.write(" ".join(sys.argv[1:])+"\\n")\n'
                                  f'if "--json" in sys.argv: print(json.dumps({document!r} if managed.exists() else {{"schema_version":1,"installed":[]}}))\n'
                                  'elif "--integrate" in sys.argv:\n'
                                  '    assert "--yes" in sys.argv and "--replace" in sys.argv\n'
                                  '    managed.parent.mkdir(parents=True,exist_ok=True)\n'
                                  '    managed.write_bytes(Path(sys.argv[sys.argv.index("--integrate")+1]).read_bytes())\n')
            executable.chmod(0o755)
            env = {**os.environ, 'HOME': str(root), 'PATH': str(root)+os.pathsep+os.environ['PATH']}
            for _ in range(2):
                subprocess.run(['bash', str(source/'install.sh')], env=env, check=True)
            calls = (root/'calls').read_text()
            self.assertEqual(calls.count('--integrate'), 1)
            self.assertEqual(calls.count('--set-update-source'), 2)
            self.assertEqual(managed.read_bytes(), b'test AppImage')
            self.assertIn('\nName=Notepadqq\n', (root/'.local/share/applications/notepadqq.desktop').read_text())

    def test_existing_suffixed_app_resumes_without_download_or_integration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            managed = root/'notepadqq.appimage'
            managed.touch()
            document = inventory(app('Notepadqq (543d74)', str(managed)))
            self.run_installer(root, document)
            calls = (root/'calls').read_text()
            self.assertNotIn('--integrate', calls)
            self.assertIn('--set-update-source', calls)
            self.assertIn('--list-updates', calls)

    def run_installer(self, root, document):
        import os
        launcher(root, Path(document['installed'][0]['path']))
        executable = root/'flatpak'
        executable.write_text('#!/usr/bin/env python3\nimport json,sys\n'
                              f'with open({str(root/"calls")!r}, "a") as f: f.write(" ".join(sys.argv[1:])+"\\n")\n'
                              f'if "--list-installed" in sys.argv and "--json" in sys.argv: print({json.dumps(document)!r})\n'
                              'elif "--set-update-source" not in sys.argv and "--list-installed" not in sys.argv and "--list-updates" not in sys.argv: sys.exit(1)\n')
        executable.chmod(0o755)
        subprocess.run(['bash', str(ROOT/'scripts/notepadqq/install.sh')],
                       env={**os.environ, 'HOME': str(root), 'PATH': str(root)+os.pathsep+os.environ['PATH']}, check=True)


if __name__ == '__main__':
    unittest.main()
