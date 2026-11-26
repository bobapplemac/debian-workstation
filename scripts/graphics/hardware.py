#!/usr/bin/env python3
"""Read PCI display adapters and validate them against signed-package GPU metadata."""
import json
from pathlib import Path
import sys


def detect(root=Path('/sys/bus/pci/devices')):
    devices = []
    for path in sorted(root.iterdir()):
        if int((path/'class').read_text().strip(), 16) >> 16 != 3:
            continue
        entry = {'slot': path.name}
        for field in ('vendor', 'device', 'subsystem_vendor', 'subsystem_device'):
            entry[field] = f'0x{int((path/field).read_text().strip(), 16):04x}'
        entry['driver'] = (path/'driver').resolve().name if (path/'driver').is_symlink() else 'unbound'
        devices.append(entry)
    return devices


def supported(devices, manifest):
    chips = manifest.get('chips')
    if not isinstance(chips, list):
        raise ValueError('Invalid NVIDIA supported-GPU manifest')
    result = []
    for device in devices:
        if device['vendor'] != '0x10de':
            continue
        candidates = [chip for chip in chips if int(chip['devid'], 16) == int(device['device'], 16)
                      and ('subvendorid' not in chip or int(chip['subvendorid'], 16) == int(device['subsystem_vendor'], 16))
                      and ('subdevid' not in chip or int(chip['subdevid'], 16) == int(device['subsystem_device'], 16))]
        matches = [chip for chip in candidates if not chip.get('legacybranch') and 'kernelopen' in chip.get('features', [])]
        if not matches:
            raise ValueError(f'NVIDIA {device["device"]} at {device["slot"]} is not supported by this candidate open module; '
                             'older/proprietary-only and unknown GPUs require a separate reviewed installation')
        result.append(matches[0]['name'])
    if not result:
        raise ValueError('No NVIDIA display adapter detected')
    return result


def native_packages(devices):
    vendors = {device['vendor'] for device in devices}
    packages = []
    if '0x1002' in vendors:
        packages.append('firmware-amd-graphics')
    if '0x8086' in vendors:
        packages.append('firmware-intel-graphics')
    if packages:
        packages += ['libgl1-mesa-dri', 'mesa-vulkan-drivers']
    return packages


if __name__ == '__main__':
    try:
        action = sys.argv[1]
        if action == 'detect':
            print(json.dumps(detect(), indent=2))
        elif action == 'report':
            for device in json.loads(Path(sys.argv[2]).read_text()):
                print(f'{device["slot"]}: PCI {device["vendor"]}:{device["device"]}, driver={device["driver"]}')
        elif action == 'kind':
            devices = json.loads(Path(sys.argv[2]).read_text())
            print('nvidia-open' if any(d['vendor'] == '0x10de' for d in devices)
                  else 'native' if native_packages(devices) else 'none')
        elif action == 'native-packages':
            print('\n'.join(native_packages(json.loads(Path(sys.argv[2]).read_text()))))
        elif action == 'supported':
            print('\n'.join(supported(json.loads(Path(sys.argv[2]).read_text()), json.loads(Path(sys.argv[3]).read_text()))))
        else:
            raise ValueError('Unknown hardware operation')
    except (ValueError, OSError, KeyError) as error:
        sys.exit(f'Graphics check stopped: {error}')
