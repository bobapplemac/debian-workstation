"""Regression for fresh Gear Lever integration names and safe rerun discovery."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('notepadqq_lookup', ROOT/'scripts/notepadqq/find-installed.py')
lookup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lookup)


def inventory(*apps):
    return {'schema_version': 1, 'installed': list(apps)}


def app(name, path='/home/example/AppImages/notepadqq.appimage'):
    return {'name': name, 'path': path, 'desktop_id': 'notepadqq.desktop',
            'current_version': None, 'manager': None}


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
            env = {**os.environ, 'PATH': str(root)+os.pathsep+os.environ['PATH']}
            for _ in range(2):
                subprocess.run(['bash', str(source/'install.sh')], env=env, check=True)
            calls = (root/'calls').read_text()
            self.assertEqual(calls.count('--integrate'), 1)
            self.assertEqual(calls.count('--set-update-source'), 2)
            self.assertEqual(managed.read_bytes(), b'test AppImage')

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
        executable = root/'flatpak'
        executable.write_text('#!/usr/bin/env python3\nimport json,sys\n'
                              f'with open({str(root/"calls")!r}, "a") as f: f.write(" ".join(sys.argv[1:])+"\\n")\n'
                              f'if "--list-installed" in sys.argv and "--json" in sys.argv: print({json.dumps(document)!r})\n'
                              'elif "--set-update-source" not in sys.argv and "--list-installed" not in sys.argv and "--list-updates" not in sys.argv: sys.exit(1)\n')
        executable.chmod(0o755)
        subprocess.run(['bash', str(ROOT/'scripts/notepadqq/install.sh')],
                       env={**os.environ, 'PATH': str(root)+os.pathsep+os.environ['PATH']}, check=True)


if __name__ == '__main__':
    unittest.main()
