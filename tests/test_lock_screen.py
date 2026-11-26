"""Guarded native-layout adaptation: preserve unrelated code and reject drift."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'scripts/desktop/lock-screen.py'
spec = importlib.util.spec_from_file_location('lock_screen', SCRIPT)
layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layout)


def fixture(spec):
    _filename, name, anchor, _replacement, context, _competing = spec
    return ('# unrelated package content\nclass '+name+':\n    def __init__(self):\n'
            + ''.join(line+'\n' for line in context)+anchor
            + '\n    def authenticate(self):\n        return "native authentication unchanged"\n')


class LayoutTests(unittest.TestCase):
    def test_preserves_native_methods_and_is_idempotent(self):
        for item in layout.SPECS:
            with self.subTest(file=item[0]):
                original=fixture(item)
                updated=layout.transform(original,item)
                self.assertIn(item[3],updated)
                self.assertEqual(layout.transform(updated,item),updated)
                self.assertEqual(layout.transform(updated,item,verify=True),updated)
                self.assertEqual(updated.split('    def authenticate')[1],original.split('    def authenticate')[1])
                self.assertTrue(updated.startswith('# unrelated package content\n'))

    def test_changed_padding_or_conflicting_alignment_requires_review(self):
        name=layout.SPECS[1]
        with self.assertRaises(ValueError):
            layout.transform(fixture(name).replace('False, False, 15','False, False, 25'),name)
        clock=layout.SPECS[0]
        with self.assertRaises(ValueError):
            layout.transform(fixture(clock).replace(clock[2],clock[2]+'        self.label.set_justify(Gtk.Justification.RIGHT)\n'),clock)

    def test_verifier_detects_package_update_removing_fixes(self):
        for item in layout.SPECS:
            with self.subTest(file=item[0]),self.assertRaises(ValueError):
                layout.transform(fixture(item),item,verify=True)

    def test_all_inputs_checked_before_staging_and_sources_never_modified(self):
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary)
            source=base/'native'; source.mkdir()
            output=base/'prepared'
            for item in layout.SPECS:
                (source/item[0]).write_text(fixture(item))
            original_clock=(source/'clock.py').read_bytes()
            (source/'unlock.py').write_text('class Unknown: pass\n')
            result=subprocess.run([sys.executable,str(SCRIPT),'prepare','--directory',str(source),'--output',str(output)],capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse(output.exists())
            self.assertEqual((source/'clock.py').read_bytes(),original_clock)
            (source/'unlock.py').write_text(fixture(layout.SPECS[1]))
            subprocess.run([sys.executable,str(SCRIPT),'prepare','--directory',str(source),'--output',str(output)],check=True,capture_output=True)
            subprocess.run([sys.executable,str(SCRIPT),'verify','--directory',str(output)],check=True,capture_output=True)
            self.assertEqual((source/'clock.py').read_bytes(),original_clock)

    def test_symlinked_native_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary)
            source=base/'native'; source.mkdir()
            target=base/'original.py'; target.write_text(fixture(layout.SPECS[0]))
            try:
                (source/'clock.py').symlink_to(target)
            except OSError:
                self.skipTest('Symlink creation unavailable')
            with self.assertRaises(ValueError):
                layout.prepare(source)

    @unittest.skipUnless(os.name == 'posix', 'APT hook runs on Linux')
    def test_apt_hook_warns_without_failing_package_upgrade(self):
        command=(ROOT/'assets/99debian-workstation-lock-screen').read_text().split('"')[1]
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary)
            project=base/'project'; native=base/'native'
            helper=project/'scripts/desktop/install-lock-screen.sh'
            helper.parent.mkdir(parents=True)
            helper.write_text('#!/bin/bash\necho "unknown upstream layout" >&2\nexit 1\n')
            native.mkdir()
            for name in ('clock.py','unlock.py'):(native/name).touch()
            adapted=command.replace('/usr/local/lib/debian-workstation',str(project)).replace('/usr/share/cinnamon-screensaver',str(native))
            result=subprocess.run(['/bin/bash','-c',adapted],capture_output=True,text=True)
            self.assertEqual(result.returncode,0)
            self.assertIn('unknown upstream layout',result.stderr)
            self.assertIn('WARNING:',result.stderr)
