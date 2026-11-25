"""Native nmcli parsing and isolated boot-transaction tests; never touch live NICs."""
import configparser
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from test_core import network

@unittest.skipUnless(shutil.which('nmcli'),'NetworkManager CLI required')
class NativeNetworkTests(unittest.TestCase):
    def render(self,name,text):
        rec=network.parse(text);kind,props=network.properties(name,rec[name])
        data=subprocess.check_output(['nmcli','--offline','connection','add','type',kind,'ifname',name,*props],text=True)
        config=configparser.ConfigParser(interpolation=None);config.read_string(data);return config
    def test_vlan_dual_stack_native(self):
        config=self.render('ens33.42','''iface ens33.42 inet static
 address 192.0.2.10/24
 gateway 192.0.2.1
 dns-nameservers 192.0.2.53 2001:db8::53
 dns-search example.test
 up ip route add 198.51.100.0/24 via 192.0.2.2 metric 5
iface ens33.42 inet6 static
 address 2001:db8::10/64
 gateway 2001:db8::1''')
        self.assertEqual(config['vlan']['id'],'42');self.assertIn('192.0.2.10/24',config['ipv4']['address1'])
        self.assertIn('198.51.100.0/24',config['ipv4']['route1'])
    def test_dhcp_native(self):
        config=self.render('ens33','iface ens33 inet dhcp')
        self.assertEqual(config['ipv4']['method'],'auto');self.assertEqual(config['ipv4']['dhcp-client-id'],'mac')
        self.assertEqual(config['connection']['autoconnect'],'false')
    def test_hotplug_native(self):
        config=self.render('ens33','allow-hotplug ens33\niface ens33 inet dhcp')
        self.assertEqual(config['connection'].get('autoconnect','true'),'true')
    def environment(self,temp):
        root=Path(temp); state=root/'state';profiles=root/'profiles';interfaces=root/'interfaces'
        interfaces.write_text('auto ens33\niface ens33 inet dhcp\n')
        return root,state,profiles,interfaces
    def test_stage_commit_idempotence(self):
        with tempfile.TemporaryDirectory() as temp:
            _,state,profiles,interfaces=self.environment(temp)
            with patch.multiple(network,STATE=state,PROFILES=profiles,INTERFACES=interfaces),patch.object(network,'inventory',return_value=({interfaces:interfaces.read_text()},interfaces.read_text())):
                network.stage();network.stage()
                self.assertIn('inet dhcp',interfaces.read_text());self.assertFalse(profiles.exists())
                network.commit();self.assertEqual(interfaces.read_text(),'auto lo\niface lo inet loopback\n')
                network.commit();self.assertEqual(len(list(profiles.glob('*.nmconnection'))),1)
    def test_change_after_staging_stops(self):
        with tempfile.TemporaryDirectory() as temp:
            _,state,profiles,interfaces=self.environment(temp)
            with patch.multiple(network,STATE=state,PROFILES=profiles,INTERFACES=interfaces),patch.object(network,'inventory',return_value=({interfaces:interfaces.read_text()},interfaces.read_text())):
                network.stage();interfaces.write_text('# admin changed this\n')
                with self.assertRaises(ValueError):network.commit()
                self.assertFalse(profiles.exists());self.assertEqual(interfaces.read_text(),'# admin changed this\n')
    def test_power_loss_recovers(self):
        with tempfile.TemporaryDirectory() as temp:
            _,state,profiles,interfaces=self.environment(temp)
            with patch.multiple(network,STATE=state,PROFILES=profiles,INTERFACES=interfaces),patch.object(network,'inventory',return_value=({interfaces:interfaces.read_text()},interfaces.read_text())):
                network.stage();profiles.mkdir()
                source=next(state.glob('*.nmconnection'));shutil.copyfile(source,profiles/source.name)
                (state/'committing').write_text('power loss')
                interfaces.write_text('auto lo\niface lo inet loopback\n')
                network.commit();self.assertTrue((state/'committed').exists());self.assertFalse((state/'committing').exists())

if __name__=='__main__':unittest.main()
