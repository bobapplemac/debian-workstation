#!/usr/bin/env python3
"""Use real configured repository indexes with an empty dpkg status, without installing."""
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
def lines(name):
    return [line for raw in (ROOT/'assets'/name).read_text().splitlines() if (line:=raw.strip()) and not line.startswith('#')]
packages=lines('packages.txt'); excluded=lines('exclusions.txt'); available=[]
for package in excluded:
    if subprocess.run(['apt-cache','show',package],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
        available.append(package+'-')
with tempfile.TemporaryDirectory() as temp:
    status=Path(temp)/'status';status.touch()
    result=subprocess.run(['apt-get','-s','--no-remove','-o','Dir::State::status='+str(status),
                           'install',*packages,*available],capture_output=True,text=True,check=True)
    installs={line.split()[1].split(':')[0] for line in result.stdout.splitlines() if line.startswith('Inst ')}
    if installs.intersection(excluded): raise SystemExit('Excluded packages selected: '+str(installs.intersection(excluded)))
    if not set(packages).issubset(installs): raise SystemExit('Requested desktop packages missing from plan')
    if any(line.startswith('Remv ') for line in result.stdout.splitlines()): raise SystemExit('Unexpected removals')
    print(f'PASS: empty-status APT simulation selected {len(installs)} packages; all requested desktop packages present and all {len(excluded)} exclusions absent.')
