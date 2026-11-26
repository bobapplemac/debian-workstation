"""Exercise continuation completion/retry without a graphical session or root."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name=='posix' and shutil.which('bash'),'Linux shell required')
class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base=Path(self.temp.name)
        self.root=base/'implementation'
        for folder in ('lib','modules','assets','scripts/repositories'):
            (self.root/folder).mkdir(parents=True,exist_ok=True)
        (self.root/'session.conf').write_text('DESKTOP_USER=example\n')
        (self.root/'install.sh').write_text('#!/bin/bash\nprintf "run\\n" >> "$TEST_RUNS"\n')
        (self.root/'scripts/repositories/notify.py').write_text('pass\n')
        self.wrapper=base/'first-login.sh'
        original=(ROOT/'scripts/first-login.sh').read_text()
        self.assertEqual(original.count('root=/usr/local/lib/debian-workstation\n'),1)
        self.wrapper.write_text(original.replace('root=/usr/local/lib/debian-workstation\n','root='+shlex.quote(str(self.root))+'\n',1))
        commands=base/'commands';commands.mkdir()
        for name in ('gdbus','notify-send'):
            command=commands/name
            command.write_text('#!/bin/sh\nexit 0\n');command.chmod(0o755)
        self.runs=base/'runs'
        self.env=dict(os.environ,HOME=str(base/'home'),XDG_STATE_HOME=str(base/'state'),
                      TEST_RUNS=str(self.runs),PATH=str(commands)+os.pathsep+os.environ['PATH'])

    def run_continuation(self):
        result=subprocess.run(['bash',str(self.wrapper),'--terminal'],input='\n',text=True,
                              capture_output=True,env=self.env,timeout=15)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return self.runs.read_text().splitlines()

    def test_completion_changes_with_library_and_bootstrap(self):
        self.assertEqual(len(self.run_continuation()),1)
        self.assertEqual(len(self.run_continuation()),1)
        (self.root/'lib/helper.sh').write_text('# changed shared implementation\n')
        self.assertEqual(len(self.run_continuation()),2)
        with (self.root/'install.sh').open('a') as stream:
            stream.write('# changed entry point\n')
        self.assertEqual(len(self.run_continuation()),3)

    def test_generated_bytecode_does_not_repeat_setup(self):
        self.assertEqual(len(self.run_continuation()),1)
        cache=self.root/'scripts/__pycache__';cache.mkdir()
        (cache/'helper.cpython-313.pyc').write_bytes(b'generated data')
        self.assertEqual(len(self.run_continuation()),1)
