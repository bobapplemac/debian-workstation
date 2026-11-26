#!/usr/bin/env python3
"""Opt-in live signed-repository APT simulation; never installs packages/drivers.

python3 tests/graphics-repository-simulation.py --keyring /path/to/verified-nvidia.gpg
Requires normal Debian APT, python3-apt, network access, and a previously verified
NVIDIA Debian 13 signing keyring. Uses isolated sources/lists/cache/empty status.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main(keyring):
    keyring = Path(keyring).resolve(strict=True)
    if any(c.isspace() for c in str(keyring)):
        raise ValueError('Use a keyring path without whitespace for APT sources syntax')
    with tempfile.TemporaryDirectory(prefix='workstation-graphics-apt-') as temp:
        work = Path(temp)
        for directory in ('lists/partial', 'cache/archives/partial', 'preferences.d', 'empty'):
            (work/directory).mkdir(parents=True)
        (work/'sources.list').write_text(
            'deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian trixie main contrib non-free non-free-firmware\n'
            'deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://security.debian.org/debian-security trixie-security main contrib non-free non-free-firmware\n'
            f'deb [signed-by={keyring}] https://developer.download.nvidia.com/compute/cuda/repos/debian13/x86_64/ /\n')
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
        subprocess.run([sys.executable, str(ROOT/'scripts/graphics/candidates.py')],
                       env={**os.environ, 'APT_CONFIG': str(config)}, check=True)
        result = subprocess.run(['apt-get', *options, '-s', '--no-remove', 'install',
                                 'nvidia-open', 'nvidia-kernel-open-dkms', 'linux-image-amd64', 'linux-headers-amd64'],
                                text=True, capture_output=True, check=True)
        names = {line.split()[1].split(':')[0] for line in result.stdout.splitlines() if line.startswith('Inst ')}
        if not {'nvidia-open', 'nvidia-kernel-open-dkms'}.issubset(names):
            raise ValueError('Open driver stack missing from transaction')
        if any(name.startswith('cuda-toolkit') or name == 'nvidia-kernel-dkms' for name in names):
            raise ValueError('Unwanted toolkit or closed kernel module selected')
        if any(line.startswith('Remv ') for line in result.stdout.splitlines()):
            raise ValueError('Transaction proposes removals')
        print(f'PASS: {len(names)} package candidates resolve from authenticated indexes; open modules, no toolkit/closed module/removals.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keyring', required=True)
    args = parser.parse_args()
    try:
        main(args.keyring)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
