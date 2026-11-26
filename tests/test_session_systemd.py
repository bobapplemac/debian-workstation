"""Opt-in isolated native systemd lifecycle test; never touch desktop targets.

Run as the regular user with DW_SYSTEMD_TESTS=1 python3 -m unittest discover -s tests.
Uses unique runtime-only fixture units and removes them afterward.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import uuid


@unittest.skipUnless(os.environ.get('DW_SYSTEMD_TESTS') == '1' and shutil.which('systemctl'),
                     'Opt-in native systemd user-manager test')
class NativeLifecycleTests(unittest.TestCase):
    def test_native_session_target_keeps_graphical_target_alive_and_stops_backend(self):
        runtime = Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/'+str(os.getuid())))/'systemd/user'
        prefix = 'dw-lifecycle-test-'+uuid.uuid4().hex
        graphical = prefix+'-graphical.target'
        session = prefix+'-session.target'
        backend = prefix+'-backend.service'

        def run(*args, check=True):
            return subprocess.run(['systemctl', '--user', *args], check=check,
                                  capture_output=True, text=True)

        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            units = {
                graphical: '[Unit]\nDescription=Isolated graphical fixture\nRefuseManualStart=yes\nStopWhenUnneeded=yes\n',
                session: f'[Unit]\nDescription=Isolated session fixture\nBindsTo={graphical}\nAfter={graphical}\n',
                backend: f'[Unit]\nDescription=Isolated portal fixture\nPartOf={graphical}\nAfter={graphical}\n'
                         '[Service]\nExecStart=/usr/bin/sleep 60\n',
            }
            try:
                for name, contents in units.items():
                    (directory/name).write_text(contents)
                run('link', '--runtime', *(str(directory/name) for name in units))
                run('daemon-reload')
                self.assertNotEqual(run('start', graphical, check=False).returncode, 0)
                run('start', session)
                self.assertEqual(run('is-active', graphical).stdout.strip(), 'active')
                run('start', backend)
                self.assertEqual(run('is-active', backend).stdout.strip(), 'active')
                run('stop', session, graphical)
                for name in units:
                    self.assertEqual(run('show', name, '-p', 'ActiveState', '--value').stdout.strip(), 'inactive')
                self.assertEqual(run('show', backend, '-p', 'Result', '--value').stdout.strip(), 'success')
            finally:
                run('stop', backend, session, graphical, check=False)
                for name in units:
                    link = runtime/name
                    if link.is_symlink() and link.resolve() == directory/name:
                        link.unlink()
                run('daemon-reload', check=False)


if __name__ == '__main__':
    unittest.main()
