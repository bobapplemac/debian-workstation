"""Portable regression tests: no privileged mutations or desktop dependencies."""
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/({'network':'network/migrate.py'}.get(name,f'{name}.py')))
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
config=load('config'); network=load('network'); archive=load('safe-zip'); files=load('files')

class ConfigTests(unittest.TestCase):
    def test_no_shell_execution(self):
        for text in ('UNKNOWN=yes','INSTALL_NOTEPADQQ=$(id)','CREATE_USER=yes\nCREATE_USER=no','DESKTOP_USER=root;id','NEMO_REF=--bad'):
            with self.subTest(text=text),self.assertRaises(ValueError): config.parse(text)
    def test_defaults_and_spaces(self):
        self.assertEqual(config.parse('')['NEMO_REF'],'main')
        self.assertEqual(config.parse('')['GRAPHICS_DRIVERS'],'ask')
        with self.assertRaises(ValueError):config.parse('GRAPHICS_DRIVERS=legacy')
        self.assertEqual(config.parse('FONT_ARCHIVE=/tmp/my fonts.zip')['FONT_ARCHIVE'],'/tmp/my fonts.zip')

class NetworkTests(unittest.TestCase):
    def test_dhcp_multi(self):
        rec=network.parse('auto lo\niface lo inet loopback\nallow-hotplug ens33 ens34\niface ens33 inet dhcp\niface ens34 inet dhcp')
        self.assertEqual(set(rec),{'ens33','ens34'})
        kind,props=network.properties('ens33',rec['ens33'])
        self.assertEqual(kind,'ethernet');self.assertIn('ipv4.dhcp-client-id',props)
    def test_static_dual_vlan(self):
        rec=network.parse('''auto ens33.42
iface ens33.42 inet static
 address 192.0.2.10
 netmask 255.255.255.0
 gateway 192.0.2.1
 dns-nameservers 192.0.2.53 2001:db8::53
 dns-search example.test
 up ip route add 198.51.100.0/24 via 192.0.2.2 metric 5
iface ens33.42 inet6 static
 address 2001:db8::10/64
 gateway 2001:db8::1''')
        kind,props=network.properties('ens33.42',rec['ens33.42'])
        self.assertEqual(kind,'vlan');self.assertIn('192.0.2.10/24',props)
        self.assertIn('2001:db8::10/64',props);self.assertIn('198.51.100.0/24 192.0.2.2 5',props)
    def test_fail_closed(self):
        for text in ('iface ens33 inet dhcp\n pre-up echo bad','iface ens33 inet static\n address 192.0.2.1','iface ens33 inet dhcp\n bridge_ports ens34','iface ens33 inet dhcp\niface ens33 inet dhcp'):
            with self.subTest(text=text),self.assertRaises(ValueError):
                for name,families in network.parse(text).items(): network.properties(name,families)
    def test_vlan_range(self):
        with self.assertRaises(ValueError): network.properties('ens33.4095',{'inet':{'method':'dhcp'}})

class ArchiveTests(unittest.TestCase):
    def test_reject_unsafe(self):
        for name in ('../escape','/absolute','a/../../escape','C:/bad','a\\bad'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as temp:
                path=Path(temp)/'in.zip'
                with zipfile.ZipFile(path,'w') as z:
                    item=zipfile.ZipInfo('placeholder');item.filename=name;z.writestr(item,'bad')
                with self.assertRaises(ValueError):archive.extract(path,Path(temp)/'out')
    def test_regular(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'in.zip'
            with zipfile.ZipFile(path,'w') as z:z.writestr('fonts/font.ttf','test')
            archive.extract(path,Path(temp)/'out')
            self.assertEqual((Path(temp)/'out/fonts/font.ttf').read_text(),'test')
    def test_symlinks_and_case_duplicates(self):
        for mode in ('link','duplicate'):
            with tempfile.TemporaryDirectory() as temp:
                path=Path(temp)/'in.zip'
                with zipfile.ZipFile(path,'w') as z:
                    if mode=='link':
                        item=zipfile.ZipInfo('link'); item.external_attr=0o120777<<16;z.writestr(item,'target')
                    else:z.writestr('a','one');z.writestr('A','two')
                with self.assertRaises(ValueError):archive.extract(path,Path(temp)/'out')

class FileTests(unittest.TestCase):
    def test_preservation_and_idempotence(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(Path,'home',return_value=Path(temp)):
            path=Path(temp)/'gtk.css';path.write_text('/* user css */\n')
            files.write(path,'@import url("test.css");\n'+path.read_text())
            before=path.stat().st_mtime_ns
            files.write(path,path.read_text())
            self.assertEqual(before,path.stat().st_mtime_ns)
            self.assertEqual(path.with_name('gtk.css.before-debian-workstation').read_text(),'/* user css */\n')
    def test_unmanaged_collision(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(Path,'home',return_value=Path(temp)):
            path=Path(temp)/'asset';path.write_text('user data')
            with self.assertRaises(ValueError):files.write(path,'replacement',managed=True)
    def test_managed_changes(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(Path,'home',return_value=Path(temp)):
            path=Path(temp)/'asset';files.write(path,'first',managed=True);files.write(path,'second',managed=True)
            self.assertEqual(path.read_text(),'second')
            path.write_text('user edit')
            with self.assertRaises(ValueError):files.write(path,'third',managed=True)

if __name__=='__main__':unittest.main()
