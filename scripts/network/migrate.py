#!/usr/bin/env python3
"""Strict ifupdown -> native NM keyfiles, committed at a reboot boundary.

Only recognized netcfg configurations are accepted. Unknown directives fail closed.
"""
import configparser
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import uuid

STATE = Path('/var/lib/debian-workstation/network')
INTERFACES = Path('/etc/network/interfaces')
PROFILES = Path('/etc/NetworkManager/system-connections')
NAME = re.compile(r'[a-zA-Z0-9_-]+(?:\.[0-9]{1,4})?\Z')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def parse(text):
    records = {}
    activated = set()
    current = None
    for n, original in enumerate(text.splitlines(), 1):
        line = original.split('#', 1)[0].strip()
        if not line: continue
        words = shlex.split(line)
        if words[0] in ('auto', 'allow-hotplug'):
            if not all(NAME.fullmatch(i) for i in words[1:]): raise ValueError('Invalid interface name')
            activated.update(words[1:])
            continue
        if words[0] == 'iface':
            if len(words)!=4 or not NAME.fullmatch(words[1]) or words[2] not in ('inet','inet6'):
                raise ValueError(f'Unsupported iface stanza at line {n}')
            name, family, method = words[1:]
            if name == 'lo':
                if method!='loopback': raise ValueError('Unexpected loopback configuration')
                current = None
                continue
            if method not in ('dhcp','static','manual','auto'): raise ValueError(f'Unsupported method {method}')
            if family=='inet' and method=='auto': raise ValueError('inet auto is unsupported')
            current = records.setdefault(name, {})
            if family in current: raise ValueError(f'Duplicate stanza {name} {family}')
            current[family] = {'method':method}
            current = current[family]
            continue
        if current is None: raise ValueError(f'Unexpected directive at line {n}: {words[0]}')
        key, *values = words
        if key in ('up', 'post-up'):
            # Common explicit static routes; reject arbitrary shell and corresponding deletes.
            if len(values)<5 or values[:3] not in (['ip','route','add'],['ip','-6','route']):
                raise ValueError('Only simple ip route add hooks are supported; translate other hooks manually')
            if values[:3]==['ip','-6','route']:
                if len(values)<6 or values[3]!='add': raise ValueError('Unsupported IPv6 route hook')
                route=values[4:]
            else: route=values[3:]
            current.setdefault('routes', []).append(route)
        elif key in ('address','netmask','gateway','dns-nameservers','dns-search','vlan-raw-device'):
            if key in current or not values: raise ValueError(f'Duplicate/empty option {key}')
            current[key] = values
        else: raise ValueError(f'Unsupported ifupdown option: {key}; migrate it explicitly before proceeding')
    for name, families in records.items(): families['_autoconnect'] = name in activated
    return records

def properties(name, families):
    props = ['connection.id', 'dw-'+name, 'connection.uuid', str(uuid.uuid5(uuid.NAMESPACE_DNS,'debian-workstation/'+name)),
             'connection.interface-name',name,'connection.autoconnect','yes' if families.get('_autoconnect',True) else 'no']
    if '.' in name:
        parent, tag = name.rsplit('.',1)
        if not tag.isdigit() or not 1<=int(tag)<=4094: raise ValueError('Invalid VLAN ID')
        props += ['vlan.parent',parent,'vlan.id',tag]
        kind = 'vlan'
    else: kind = 'ethernet'
    for family, prefix, version in [('inet','ipv4',4),('inet6','ipv6',6)]:
        rec = families.get(family)
        if rec is None:
            props += [prefix+'.method', 'auto' if version==6 and families.get('inet',{}).get('method')!='manual' else 'disabled']
            continue
        method=rec['method']
        props += [prefix+'.method', {'dhcp':'auto' if version==4 else 'dhcp','static':'manual','manual':'disabled','auto':'auto'}[method]]
        if rec.get('vlan-raw-device'):
            if kind!='vlan' or rec['vlan-raw-device']!=[parent]: raise ValueError('VLAN parent mismatch')
        if method=='static':
            address=rec.get('address',[])
            if len(address)!=1: raise ValueError('Static addressing requires one address per family')
            address=address[0]
            if '/' not in address:
                mask=rec.get('netmask',[])
                if len(mask)!=1: raise ValueError('Static address needs prefix or netmask')
                address += '/'+mask[0]
            interface=ipaddress.ip_interface(address)
            if interface.version!=version: raise ValueError('Address family mismatch')
            props += [prefix+'.addresses',str(interface)]
        elif any(k in rec for k in ('address','netmask','gateway')):
            raise ValueError('Address options on a non-static stanza')
        if 'gateway' in rec:
            gateway=rec['gateway']
            if len(gateway)!=1 or ipaddress.ip_address(gateway[0]).version!=version: raise ValueError('Invalid gateway')
            props += [prefix+'.gateway',gateway[0]]
        if 'dns-nameservers' in rec:
            for value in rec['dns-nameservers']: ipaddress.ip_address(value)
            # ifupdown resolvconf may contain both families in the same stanza.
            for v,p in [(4,'ipv4'),(6,'ipv6')]:
                values=[i for i in rec['dns-nameservers'] if ipaddress.ip_address(i).version==v]
                if values: props += ['+'+p+'.dns', ','.join(values)]
        if 'dns-search' in rec:
            if not all(re.fullmatch(r'[a-zA-Z0-9_.~-]+',s) for s in rec['dns-search']): raise ValueError('Invalid DNS search domain')
            props += [prefix+'.dns-search',','.join(rec['dns-search'])]
        for route in rec.get('routes',[]):
            dest=route[0]
            if dest=='default': dest='0.0.0.0/0' if version==4 else '::/0'
            net=ipaddress.ip_network(dest,strict=False)
            if net.version!=version or len(route) not in (3,5) or route[1]!='via': raise ValueError('Unsupported route syntax')
            gateway=ipaddress.ip_address(route[2])
            if gateway.version!=version: raise ValueError('Route gateway family mismatch')
            value=f'{net} {gateway}'
            if len(route)==5:
                if route[3]!='metric' or not route[4].isdigit(): raise ValueError('Unsupported route metric')
                value+=' '+route[4]
            props += ['+'+prefix+'.routes',value]
    # Reference netinst uses MAC DHCPv4 identity; preserve leases across migration.
    props += ['ipv4.dhcp-client-id','mac']
    return kind, props

def inventory(path=INTERFACES, seen=None):
    seen = set() if seen is None else seen
    path = path.absolute()
    if path in seen: raise ValueError('Duplicate or recursive interfaces include')
    if path.is_symlink() or not path.is_file(): raise ValueError(f'Expected regular interfaces file: {path}')
    if not path.is_relative_to(Path('/etc/network')): raise ValueError('Include outside /etc/network')
    seen.add(path)
    texts={path:path.read_text()}
    combined=[]
    for line in texts[path].splitlines():
        words=line.split('#',1)[0].split()
        if words and words[0] in ('source','source-directory'):
            if len(words)!=2: raise ValueError('Unsupported interfaces include')
            pattern=Path(words[1])
            if not pattern.is_absolute(): pattern=path.parent/pattern
            if '..' in pattern.parts or not pattern.is_relative_to(Path('/etc/network')): raise ValueError('Unsafe interfaces include')
            if words[0]=='source-directory':
                matches=sorted(p for p in pattern.iterdir() if re.fullmatch(r'[a-zA-Z0-9_-]+',p.name)) if pattern.exists() else []
            else: matches=sorted(pattern.parent.glob(pattern.name))
            for child in matches:
                childtexts, childcombined=inventory(child,seen)
                texts.update(childtexts); combined.append(childcombined)
        else: combined.append(line)
    return texts, '\n'.join(combined)

def existing_conflicts(names):
    if not names: return
    for path in PROFILES.glob('*'):
        if not path.is_file() or path.name.endswith('.before-debian-workstation'): continue
        config=configparser.ConfigParser(interpolation=None,strict=False)
        config.read(path)
        section=config['connection'] if config.has_section('connection') else {}
        if section.get('type') in ('ethernet','802-3-ethernet','vlan'):
            interface=section.get('interface-name')
            if not interface or interface in names:
                raise ValueError(f'Existing NetworkManager connection may conflict: {path}; reconcile it explicitly')

def stage():
    if (STATE/'committed').exists():
        print('Network migration already committed; current NM configuration retained.'); return
    texts,combined=inventory()
    records=parse(combined)
    if records and Path('/usr/sbin/NetworkManager').exists():
        actual=subprocess.check_output(['/usr/sbin/NetworkManager','--print-config'],text=True)
        config=configparser.ConfigParser(interpolation=None,strict=False);config.read_string(actual)
        if config.getboolean('ifupdown','managed',fallback=False):
            raise ValueError('NetworkManager already manages ifupdown interfaces; restore managed=false before migration')
    plans={name:properties(name,families) for name,families in records.items()}
    existing_conflicts(records)
    if not records: print('No ifupdown Ethernet interfaces to migrate.'); return
    STATE.mkdir(mode=0o700,parents=True,exist_ok=True)
    os.chmod(STATE,0o700)
    plan={'sources':{str(p):digest(p) for p in texts}, 'profiles':[]}
    for name,(kind,props) in plans.items():
        output=subprocess.check_output(['nmcli','--offline','connection','add','type',kind,'ifname',name,*props])
        # Parse the native output again, checking connection identity.
        config=configparser.ConfigParser(interpolation=None)
        config.read_string(output.decode())
        if config['connection']['interface-name']!=name: raise ValueError('nmcli output identity mismatch')
        dest=STATE/('dw-'+name+'.nmconnection')
        dest.write_bytes(output); dest.chmod(0o600)
        plan['profiles'].append({'path':str(dest),'sha256':digest(dest)})
    for p in texts:
        backup=STATE/('backup-'+str(p).replace('/','_'))
        if backup.exists() and digest(backup)!=digest(p): raise ValueError('Original network backup already differs; inspect before retrying')
        shutil.copyfile(p,backup); backup.chmod(0o600)
    temp=STATE/'plan.tmp'; temp.write_text(json.dumps(plan,indent=2)+'\n'); temp.replace(STATE/'plan.json')
    print('Validated profiles staged. Migration will commit before networking starts at the next boot.')

def commit():
    plan=json.loads((STATE/'plan.json').read_text())
    if (STATE/'committed').exists(): return
    # A power loss may occur between writing profiles and the single ownership
    # switch. Restore the original side before retrying; no daemon has started yet.
    if (STATE/'committing').exists(): rollback(plan)
    for path,sha in plan['sources'].items():
        if digest(Path(path))!=sha: raise ValueError(f'Network source changed: {path}; no migration performed')
    for entry in plan['profiles']:
        if digest(Path(entry['path']))!=entry['sha256']: raise ValueError('Staged profile changed')
    PROFILES.mkdir(parents=True,exist_ok=True)
    # Original sources remain authoritative until all keyfiles are ready.
    for entry in plan['profiles']:
        source=Path(entry['path']); dest=PROFILES/source.name
        if dest.exists() or dest.is_symlink(): raise ValueError(f'Profile appeared after staging: {dest}')
    (STATE/'committing').write_text('Network ownership transaction in progress\n')
    try:
        for entry in plan['profiles']:
            source=Path(entry['path']); dest=PROFILES/source.name
            shutil.copyfile(source,dest); dest.chmod(0o600)
        # Removing includes from the main file is sufficient. Included files are
        # preserved verbatim, but become inactive; only one ownership switch occurs.
        if any(p.is_symlink() for p in [INTERFACES,*INTERFACES.parents]): raise ValueError('Network path became a symlink')
        tmp=INTERFACES.with_name('interfaces.dw-new')
        with tmp.open('x') as f: f.write('auto lo\niface lo inet loopback\n')
        tmp.chmod(0o644); tmp.replace(INTERFACES)
        (STATE/'committed').write_text('Migration committed; verify connectivity and DNS.\n')
        (STATE/'committing').unlink()
    except BaseException:
        rollback(plan)
        raise
    print('Network migration committed. Original files retained for console recovery.')

def rollback(plan):
    original=STATE/('backup-'+str(INTERFACES).replace('/','_'))
    if digest(original)!=plan['sources'][str(INTERFACES)]: raise ValueError('Original network backup differs; use console recovery')
    for entry in plan['profiles']:
        dest=PROFILES/Path(entry['path']).name
        if dest.exists():
            if dest.is_symlink() or digest(dest)!=entry['sha256']: raise ValueError('Network profile changed during commit; use console recovery')
            dest.unlink()
    if INTERFACES.is_symlink(): raise ValueError('Original network path became a symlink')
    tmp=INTERFACES.with_name('interfaces.dw-recover')
    if tmp.exists() or tmp.is_symlink(): raise ValueError('Recovery staging path already exists')
    shutil.copyfile(original,tmp); tmp.chmod(0o644); tmp.replace(INTERFACES)
    marker=STATE/'committing'
    if marker.exists(): marker.unlink()
    stale=INTERFACES.with_name('interfaces.dw-new')
    if stale.exists() and not stale.is_symlink(): stale.unlink()

if __name__=='__main__':
    try:
        if os.geteuid()!=0: raise ValueError('Network operations require root')
        if sys.argv[1]=='inspect':
            if (STATE/'committed').exists(): print('Already migrated')
            else:
                _,text=inventory(); records=parse(text)
                for name,families in records.items(): properties(name,families)
                existing_conflicts(records)
                print('Recognized interfaces: '+', '.join(records))
        elif sys.argv[1]=='stage': stage()
        elif sys.argv[1]=='commit': commit()
        else: raise ValueError('Use inspect, stage or commit')
    except (ValueError,OSError,subprocess.CalledProcessError,configparser.Error) as e:
        sys.exit(f'Network migration stopped: {e}. Original backups and console recovery: docs/networking.md')
