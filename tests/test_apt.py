"""Actual libapt policy and solver tests using isolated synthetic repository indexes.

No network, root, dpkg operations, or changes to host APT configuration.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(shutil.which('apt-cache') and shutil.which('apt-get'),'Debian APT required')
class AptPolicyTests(unittest.TestCase):
    def setUp(self):
        self.work=tempfile.TemporaryDirectory(); self.root=Path(self.work.name)
        for d in ('lists/partial','cache/archives/partial','empty','preferences.d'): (self.root/d).mkdir(parents=True)
        (self.root/'preferences.d/linuxmint.pref').write_text((ROOT/'assets/linuxmint.pref').read_text())
        (self.root/'sources.list').write_text('deb [trusted=yes] https://fastly.linuxmint.io/ gigi main\n'
            'deb [trusted=yes] https://deb.debian.org/debian trixie main\n'
            'deb [trusted=yes] https://security.debian.org/debian-security trixie-security main\n')
        (self.root/'status').write_text('Package: libadwaita-1-0\nStatus: install ok installed\nArchitecture: amd64\nVersion: 1.7.6+mint2+gigi\nDescription: test\n\n')
        self.opts=[]
        values={'Dir::Etc::sourcelist':str(self.root/'sources.list'),'Dir::Etc::sourceparts':str(self.root/'empty'),
                'Dir::Etc::preferences':str(self.root/'missing'),'Dir::Etc::preferencesparts':str(self.root/'preferences.d'),
                'Dir::State::lists':str(self.root/'lists'),'Dir::State::status':str(self.root/'status'),
                'Dir::Cache':str(self.root/'cache'),'APT::Architecture':'amd64','APT::Architectures::':'amd64',
                'Debug::NoLocking':'true','Dir::Etc::main':str(self.root/'missing'),'Dir::Etc::parts':str(self.root/'empty')}
        for k,v in values.items(): self.opts+=['-o',k+'='+v]
    def tearDown(self): self.work.cleanup()
    def repo(self,site,path,suite,origin,versions):
        prefix=site+('_'+path.replace('/','_') if path else '')+'_dists_'+suite
        (self.root/'lists'/(prefix+'_Release')).write_text(f'Origin: {origin}\nLabel: {origin}\nSuite: {suite}\nCodename: {suite}\nArchitectures: amd64\nComponents: main\n')
        content=''
        for name,version in versions:
            content+=f'Package: {name}\nVersion: {version}\nArchitecture: amd64\nMaintainer: Test <test@example.invalid>\nFilename: pool/{name}.deb\nSize: 1\nDescription: test fixture\n\n'
        (self.root/'lists'/(prefix+'_main_binary-amd64_Packages')).write_text(content)
    def run_apt(self,command,*args):
        return subprocess.check_output([command,*self.opts,*args],text=True,stderr=subprocess.STDOUT)
    def fixture(self,security=None):
        self.repo('fastly.linuxmint.io','','gigi','linuxmint',[('libadwaita-1-0','1.7.6+mint2+gigi'),('unapproved','99')])
        self.repo('deb.debian.org','debian','trixie','Debian',[('libadwaita-1-0','1.7.6-1~deb13u1')])
        self.repo('security.debian.org','debian-security','trixie-security','Debian',[] if security is None else [('libadwaita-1-0',security)])
    def test_mint_integration_and_allowlist(self):
        self.fixture()
        self.assertIn('Candidate: 1.7.6+mint2+gigi',self.run_apt('apt-cache','policy','libadwaita-1-0'))
        self.assertIn('Candidate: (none)',self.run_apt('apt-cache','policy','unapproved'))
        self.assertNotIn('Remv ',self.run_apt('apt-get','-s','install','libadwaita-1-0'))
    def test_lower_sorting_security_update_wins(self):
        self.fixture('1.7.6-1~deb13u2')
        self.assertIn('Candidate: 1.7.6-1~deb13u2',self.run_apt('apt-cache','policy','libadwaita-1-0'))
        result=self.run_apt('apt-get','-s','install','libadwaita-1-0')
        self.assertIn('DOWNGRADED',result); self.assertNotIn('Remv ',result)
    def test_future_security_version_wins(self):
        self.fixture('1.7.7-1~deb13u1')
        self.assertIn('Candidate: 1.7.7-1~deb13u1',self.run_apt('apt-cache','policy','libadwaita-1-0'))

if __name__=='__main__': unittest.main()
