"""Exercise the exact embedded remote bootstrap without network or privilege."""
import gzip
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=(ROOT/'install.sh').read_text().split("<<'PY'\n",1)[1].split('\nPY\n',1)[0]

def bundle(extra=(), truncate=False):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as t:
        for name,data,kind in [('repo/install.sh',b'#!/bin/bash\n',tarfile.REGTYPE),
                               ('repo/lib/runner.sh',b'# runner\n',tarfile.REGTYPE),
                               ('repo/scripts/config.py',b'# config\n',tarfile.REGTYPE),*extra]:
            item=tarfile.TarInfo(name);item.size=len(data);item.type=kind
            if kind==tarfile.SYMTYPE:item.linkname='/etc/shadow';item.size=0
            t.addfile(item,io.BytesIO(data) if item.isfile() else None)
    data=stream.getvalue();return data[:-8] if truncate else data

class BootstrapTests(unittest.TestCase):
    def run_source(self,data,target):
        def request(req,timeout):
            return io.BytesIO(json.dumps({'sha':'a'*40}).encode() if '/commits/' in req.full_url else data)
        with patch('urllib.request.urlopen',side_effect=request),patch.object(sys,'argv',['-', 'main',str(target)]):
            exec(compile(SCRIPT,'install.sh bootstrap','exec'),{'__name__':'__main__'})
    def test_valid_commit_and_source(self):
        with tempfile.TemporaryDirectory() as temp:
            self.run_source(bundle(),temp)
            self.assertEqual((Path(temp)/'source/REVISION').read_text(),'a'*40+'\n')
            self.assertTrue((Path(temp)/'source/lib/runner.sh').is_file())
    def test_bad_inventory(self):
        for extra in [[('../escape',b'x',tarfile.REGTYPE)],[('repo/a',b'',tarfile.SYMTYPE)],
                      [('other/a',b'x',tarfile.REGTYPE)],[('repo/install.sh',b'duplicate',tarfile.REGTYPE)]]:
            with self.subTest(extra=extra),tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(ValueError):self.run_source(bundle(extra),temp)
                self.assertFalse((Path(temp)/'source').exists())
    def test_gzip_footer(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(EOFError):self.run_source(bundle(truncate=True),temp)

if __name__=='__main__':unittest.main()
