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


def validate_debian(cache):
    versions = []
    for name in ('nvidia-driver', 'nvidia-kernel-dkms', 'nvidia-smi'):
        if name not in cache or cache[name].candidate is None:
            raise ValueError(f'No Debian {name} candidate available')
        candidate = cache[name].candidate
        if (not any(o.origin == 'Debian' and o.trusted for o in candidate.origins)
                or any(o.site == 'developer.download.nvidia.com' for o in candidate.origins)):
            raise ValueError(f'{name} is not a native authenticated Debian candidate; reconcile active repositories first')
        versions.append(candidate.version)
    if len(set(versions)) != 1 or not re.fullmatch(r'(?:[0-9]+:)?[0-9]+\.[0-9]+\.[0-9]+-[0-9A-Za-z.+~]+', versions[0]):
        raise ValueError('Debian NVIDIA driver/kernel/diagnostic candidate versions are inconsistent')
    return versions[0]


def validate_transaction(cache, version, flavor='open'):
    targets = ('nvidia-open', 'nvidia-kernel-open-dkms') if flavor == 'open' else ('nvidia-driver', 'nvidia-kernel-dkms', 'nvidia-smi')
    for name in targets:
        cache[name].mark_install()
    if cache.broken_count:
        raise ValueError('NVIDIA driver dependency plan is broken')
    for package in cache.get_changes():
        wrong_modules = ('nvidia-kernel-dkms',) if flavor == 'open' else ('nvidia-kernel-open-dkms', 'nvidia-open-kernel-dkms')
        if package.marked_delete or package.name in wrong_modules:
            raise ValueError(f'Unwanted removal or wrong kernel-module selection: {package.name}')
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
        if sys.argv[1:] == ['--debian']:
            version = validate_debian(cache)
            validate_transaction(cache, version, 'debian')
        elif not sys.argv[1:]:
            version = validate(cache, allowed)
            validate_transaction(cache, version)
        else:
            raise ValueError('Usage: candidates.py [--debian]')
        print(version)
    except (OSError, ValueError) as error:
        sys.exit(f'NVIDIA candidate check failed: {error}')
