"""Run the real shell wrapper with fake Xsession/systemctl, never a live desktop."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('wrapper_check', ROOT/'scripts/session/check-wrapper.py')
wrapper_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper_check)


class ConfigTests(unittest.TestCase):
    def test_shipped_wrapper_and_rerun(self):
        wrapper_check.check('[Seat:*]\nA  session-wrapper=/etc/X11/Xsession\n')
        wrapper_check.check('[Seat:*]\nB session-wrapper='+wrapper_check.WRAPPER+'\n', installed=True)

    def test_custom_missing_or_overridden_wrapper_stops(self):
        for text in ('[Seat:*]\n', 'A session-wrapper=/custom/wrapper\n',
                     'A session-wrapper=/etc/X11/Xsession\nB session-wrapper=/custom/seat\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                wrapper_check.check(text)
        with self.assertRaises(ValueError):
            wrapper_check.check('A session-wrapper=/etc/X11/Xsession\n', installed=True)


def bash_executable():
    git_bash = Path('C:/Program Files/Git/bin/bash.exe')
    return str(git_bash) if os.name == 'nt' and git_bash.exists() else shutil.which('bash')


@unittest.skipUnless(bash_executable(), 'Bash required')
class LifecycleTests(unittest.TestCase):
    def run_wrapper(self, *, active=False, start_fails=False, env_fails=False, session_type='x11', session_status=0):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            (work/'systemctl').write_text('#!/bin/bash\nprintf "systemctl %s\\n" "$*" >>"$TEST_LOG"\n'
                                         'case "$*" in\n'
                                         '  *is-active*) exit "${TEST_ACTIVE_EXIT:-1}";;\n'
                                         '  *start*) exit "${TEST_START_EXIT:-0}";;\n'
                                         'esac\n')
            (work/'dbus-update-activation-environment').write_text('#!/bin/bash\nprintf "environment %s\\n" "$*" >>"$TEST_LOG"\nexit "${TEST_ENV_EXIT:-0}"\n')
            (work/'xsession').write_text('#!/bin/bash\nprintf "session begin: %s | %s\\n" "$1" "$2" >>"$TEST_LOG"\n'
                                        'printf "session end\\n" >>"$TEST_LOG"\nexit "${TEST_SESSION_EXIT:-0}"\n')
            for name in ('systemctl', 'dbus-update-activation-environment', 'xsession'):
                (work/name).chmod(0o755)
            script = '''test_bin=$(cd "$2" && pwd)
export PATH="$test_bin:$PATH" TEST_LOG="$test_bin/calls"
source "$1"
graphical_session "$test_bin/xsession" 'argument with spaces' 'literal;$(untouched)'
'''
            env = {**os.environ, 'XDG_SESSION_TYPE': session_type, 'XDG_RUNTIME_DIR': '/run/user/1000',
                   'DISPLAY': ':0', 'XAUTHORITY': '/home/example/.Xauthority', 'XDG_CURRENT_DESKTOP': 'X-Cinnamon',
                   'TEST_ACTIVE_EXIT': '0' if active else '3', 'TEST_START_EXIT': '1' if start_fails else '0',
                   'TEST_ENV_EXIT': '1' if env_fails else '0', 'TEST_SESSION_EXIT': str(session_status)}
            result = subprocess.run([bash_executable(), '-c', script, 'test-wrapper',
                                     str(ROOT/'scripts/session/lightdm-session.sh'), str(work)],
                                    env=env, capture_output=True, text=True)
            calls = (work/'calls').read_text().splitlines() if (work/'calls').exists() else []
            return result, calls

    def test_login_logout_order_and_argument_preservation(self):
        result, calls = self.run_wrapper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls[0], 'systemctl --user is-active --quiet graphical-session.target')
        self.assertTrue(calls[1].startswith('environment --systemd DISPLAY XAUTHORITY'))
        self.assertEqual(calls[2], 'systemctl --user daemon-reload')
        self.assertEqual(calls[3], 'systemctl --user start debian-workstation-cinnamon-session.target')
        self.assertEqual(calls[4], 'session begin: argument with spaces | literal;$(untouched)')
        self.assertEqual(calls[5], 'session end')
        self.assertEqual(calls[6], 'systemctl --user stop debian-workstation-cinnamon-session.target graphical-session.target')
        self.assertFalse(any('reset-failed' in call or 'restart' in call for call in calls))

    def test_session_failure_still_stops_target_and_preserves_status(self):
        result, calls = self.run_wrapper(session_status=7)
        self.assertEqual(result.returncode, 7)
        self.assertEqual(calls[-1], 'systemctl --user stop debian-workstation-cinnamon-session.target graphical-session.target')

    def test_existing_target_is_not_claimed_or_stopped(self):
        result, calls = self.run_wrapper(active=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[-1], 'session end')

    def test_environment_or_target_failure_does_not_launch_session(self):
        for options in ({'env_fails': True}, {'start_fails': True}):
            with self.subTest(options=options):
                result, calls = self.run_wrapper(**options)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(any(call.startswith('session ') for call in calls))
                self.assertFalse(any('stop graphical-session' in call for call in calls))

    def test_other_session_types_pass_through(self):
        result, calls = self.run_wrapper(session_type='wayland')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0].startswith('session begin:'))


if __name__ == '__main__':
    unittest.main()
