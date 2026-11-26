#!/usr/bin/env python3
"""Require a coherent upstream open driver candidate and a closed repo allowlist."""
import re
from pathlib import Path
import sys


def validate(cache, allowed):
    for package in cache:
        candidate = package.candidate
        if candidate and any(o.site == 'developer.download.nvidia.com' for o in candidate.origins) and package.name not in allowed:
            raise ValueError(f'Unapproved NVIDIA repository candidate: {package.name}')
    versions = []
    for name in ('nvidia-open', 'nvidia-driver', 'nvidia-kernel-open-dkms'):
        if name not in cache or cache[name].candidate is None:
            raise ValueError(f'Missing {name} candidate')
        candidate = cache[name].candidate
        if not any(o.site == 'developer.download.nvidia.com' and o.trusted for o in candidate.origins):
            raise ValueError(f'{name} candidate is not from the authenticated NVIDIA repository')
        versions.append(candidate.version)
    if len(set(versions)) != 1 or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+-[0-9]+', versions[0]):
        raise ValueError('NVIDIA open module and user-space candidate versions differ or use an unreviewed version format')
    return versions[0]


def validate_transaction(cache, version):
    for name in ('nvidia-open', 'nvidia-kernel-open-dkms'):
        cache[name].mark_install()
    if cache.broken_count:
        raise ValueError('NVIDIA open driver dependency plan is broken')
    for package in cache.get_changes():
        if package.marked_delete or package.name == 'nvidia-kernel-dkms':
            raise ValueError(f'Unwanted removal or closed-module selection: {package.name}')
        candidate = package.candidate
        if candidate and candidate.source_name in ('nvidia-graphics-drivers', 'nvidia-kmod-open'):
            if candidate.version != version:
                raise ValueError(f'Mixed NVIDIA driver/kernel/firmware runtime: {package.name}={candidate.version}, expected {version}')


if __name__ == '__main__':
    try:
        import apt
        preference = Path(__file__).resolve().parents[2]/'assets/nvidia.pref'
        package_line = next(line for line in preference.read_text().splitlines() if line.startswith('Package: '))
        allowed = set(package_line.removeprefix('Package: ').split())
        cache = apt.Cache()
        version = validate(cache, allowed)
        validate_transaction(cache, version)
        print(version)
    except (OSError, ValueError) as error:
        sys.exit(f'NVIDIA candidate check failed: {error}')
