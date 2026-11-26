#!/usr/bin/env python3
"""Opt-in live signed-repository APT simulation; never installs packages/drivers.

python3 tests/graphics-repository-simulation.py --keyring /path/to/verified-nvidia.gpg
Requires normal Debian APT, python3-apt and network access. The open-driver test
also requires a verified NVIDIA Debian 13 signing keyring; --flavor debian does
not. Uses isolated sources/lists/cache/empty status.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import gzip
import io
import tarfile
import importlib.util

ROOT = Path(__file__).resolve().parents[1]


def main(keyring, flavor):
    if flavor == 'open':
        if not keyring:
            raise ValueError('--keyring is required for the upstream open-driver test')
        keyring = Path(keyring).resolve(strict=True)
        if any(c.isspace() for c in str(keyring)):
            raise ValueError('Use a keyring path without whitespace for APT sources syntax')
    with tempfile.TemporaryDirectory(prefix='workstation-graphics-apt-') as temp:
        work = Path(temp)
        for directory in ('lists/partial', 'cache/archives/partial', 'preferences.d', 'empty'):
            (work/directory).mkdir(parents=True)
        sources = (
            'deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian trixie main contrib non-free non-free-firmware\n'
            'deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://security.debian.org/debian-security trixie-security main contrib non-free non-free-firmware\n')
        if flavor == 'open':
            sources += f'deb [signed-by={keyring}] https://developer.download.nvidia.com/compute/cuda/repos/debian13/x86_64/ /\n'
        (work/'sources.list').write_text(sources)
        (work/'preferences.d/nvidia.pref').write_text((ROOT/'assets/nvidia.pref').read_text())
        (work/'status').touch()
        values = {
            'Dir::Etc::sourcelist': work/'sources.list', 'Dir::Etc::sourceparts': work/'empty',
            'Dir::Etc::preferences': work/'missing', 'Dir::Etc::preferencesparts': work/'preferences.d',
            'Dir::Etc::main': work/'missing', 'Dir::Etc::parts': work/'empty',
            'Dir::State::lists': work/'lists', 'Dir::State::status': work/'status',
            'Dir::Cache': work/'cache', 'APT::Architecture': 'amd64', 'APT::Architectures::': 'amd64',
            'Debug::NoLocking': 'true', 'Acquire::Languages': 'none'}
        options = []
        for key, value in values.items():
            options += ['-o', key+'='+str(value)]
        config = work/'apt.conf'
        config.write_text('\n'.join(key+' '+json.dumps(str(value))+';' for key, value in values.items())+'\n')
        subprocess.run(['apt-get', *options, 'update'], check=True)
        version = subprocess.check_output([sys.executable, str(ROOT/'scripts/graphics/candidates.py'),
                                          *(['--debian'] if flavor == 'debian' else [])],
                                         env={**os.environ, 'APT_CONFIG': str(config)}, text=True).strip()
        print('Validated candidate:', version)
        targets = ['nvidia-open', 'nvidia-kernel-open-dkms'] if flavor == 'open' else ['nvidia-driver', 'nvidia-kernel-dkms', 'nvidia-smi']
        result = subprocess.run(['apt-get', *options, '-s', '--no-remove', 'install',
                                 *targets, 'linux-image-amd64', 'linux-headers-amd64'],
                                text=True, capture_output=True, check=True)
        names = {line.split()[1].split(':')[0] for line in result.stdout.splitlines() if line.startswith('Inst ')}
        if not set(targets).issubset(names):
            raise ValueError('Selected driver stack missing from transaction')
        wrong_module = 'nvidia-kernel-dkms' if flavor == 'open' else 'nvidia-kernel-open-dkms'
        if any(name.startswith('cuda-toolkit') or name == wrong_module for name in names):
            raise ValueError('Unwanted toolkit or wrong kernel module selected')
        if any(line.startswith('Remv ') for line in result.stdout.splitlines()):
            raise ValueError('Transaction proposes removals')
        subprocess.run(['apt-get', *options, 'download', 'nvidia-driver='+version], cwd=work, check=True)
        archive = next(work.glob('nvidia-driver_*.deb'))
        tar = subprocess.check_output(['dpkg-deb', '--fsys-tarfile', str(archive)])
        with tarfile.open(fileobj=io.BytesIO(tar)) as bundle:
            manifest = json.loads(gzip.decompress(bundle.extractfile('./usr/share/doc/nvidia-driver/supported-gpus.json.gz').read()))
        spec = importlib.util.spec_from_file_location('hardware_probe', ROOT/'scripts/graphics/hardware.py')
        hardware = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hardware)
        probe = {'slot': 'fixture', 'vendor': '0x10de', 'device': '0x2d04' if flavor == 'open' else '0x1b80',
                 'subsystem_vendor': '0x10de', 'subsystem_device': '0x0000'}
        supported = hardware.supported([probe], manifest, require_open=flavor == 'open')
        print('Authenticated manifest supports:', ', '.join(supported))
        print(f'PASS: {len(names)} candidates resolve from authenticated indexes; {flavor} modules, no toolkit/wrong module/removals.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keyring')
    parser.add_argument('--flavor', choices=('open', 'debian'), default='open')
    args = parser.parse_args()
    try:
        main(args.keyring, args.flavor)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
