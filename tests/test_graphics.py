"""Graphics detection and authenticated-metadata selection without driver changes."""
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts/graphics'/f'{name}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


hardware = module('hardware')
candidates = module('candidates')


def gpu(device='0x2d04', vendor='0x10de'):
    return {'slot': '0000:01:00.0', 'vendor': vendor, 'device': device,
            'subsystem_vendor': '0x10de', 'subsystem_device': '0x1234'}


class HardwareTests(unittest.TestCase):
    def test_pci_detection_skips_audio_and_retains_all_display_adapters(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for slot, category, vendor, device in [('0000:01:00.0', '0x030000', '0x10de', '0x2d04'),
                                                    ('0000:01:00.1', '0x040300', '0x10de', '0xabcd'),
                                                    ('0000:02:00.0', '0x030200', '0x8086', '0x1234')]:
                path = root/slot.replace(':', '_')
                path.mkdir()
                for name, value in dict(vendor=vendor, device=device, subsystem_vendor=vendor,
                                        subsystem_device='0x0000', **{'class': category}).items():
                    (path/name).write_text(value+'\n')
            devices = hardware.detect(root)
            self.assertEqual(len(devices), 2)
            self.assertEqual(devices[0]['device'], '0x2d04')
            self.assertEqual(hardware.native_packages(devices), ['firmware-intel-graphics', 'libgl1-mesa-dri', 'mesa-vulkan-drivers'])

    def test_rtx5060ti_requires_explicit_open_support_in_candidate_manifest(self):
        manifest = {'chips': [{'devid': '0x2D04', 'name': 'NVIDIA GeForce RTX 5060 Ti', 'features': ['kernelopen']}]}
        self.assertEqual(hardware.supported([gpu()], manifest), ['NVIDIA GeForce RTX 5060 Ti'])
        for unsupported in ({'chips': []}, {'chips': [{'devid': '0x2D04', 'features': []}]},
                            {'chips': [{'devid': '0x2D04', 'legacybranch': '550.xx', 'features': ['kernelopen']}]}):
            with self.subTest(manifest=unsupported), self.assertRaises(ValueError):
                hardware.supported([gpu()], unsupported)

    def test_mixed_unsupported_nvidia_prevents_partial_install(self):
        manifest = {'chips': [{'devid': '0x2D04', 'name': 'RTX 5060 Ti', 'features': ['kernelopen']}]}
        with self.assertRaises(ValueError):
            hardware.supported([gpu(), gpu('0x1b80')], manifest)

    def test_subsystem_specific_support_is_respected(self):
        chip = {'devid': '0x2D04', 'name': 'specific adapter', 'features': ['kernelopen'],
                'subvendorid': '0x10DE', 'subdevid': '0x9999'}
        with self.assertRaises(ValueError):
            hardware.supported([gpu()], {'chips': [chip]})
        chip['subdevid'] = '0x1234'
        self.assertEqual(hardware.supported([gpu()], {'chips': [chip]}), ['specific adapter'])

    def test_virtual_gpu_does_not_request_physical_drivers(self):
        self.assertEqual(hardware.native_packages([gpu('0x0405', '0x15ad')]), [])
        self.assertEqual(hardware.native_packages([gpu(vendor='0x1002')])[0], 'firmware-amd-graphics')


class CandidateTests(unittest.TestCase):
    def cache(self, *, module_version='620.70.10-1', trusted=True, extra=False):
        result = {}
        for name in ('nvidia-open', 'nvidia-driver', 'nvidia-kernel-open-dkms'):
            result[name] = SimpleNamespace(name=name, candidate=SimpleNamespace(
                version=module_version if name == 'nvidia-kernel-open-dkms' else '620.70.10-1',
                origins=[SimpleNamespace(site='developer.download.nvidia.com', trusted=trusted)]))
        if extra:
            result['cuda-toolkit'] = SimpleNamespace(name='cuda-toolkit', candidate=SimpleNamespace(
                version='99', origins=[SimpleNamespace(site='developer.download.nvidia.com', trusted=True)]))
        class Cache(dict):
            def __iter__(self):
                return iter(self.values())
        return Cache(result)

    def test_coherent_trusted_driver(self):
        allowed = {'nvidia-open', 'nvidia-driver', 'nvidia-kernel-open-dkms'}
        self.assertEqual(candidates.validate(self.cache(), allowed), '620.70.10-1')

    def test_untrusted_mixed_or_unapproved_candidate_stops(self):
        allowed = {'nvidia-open', 'nvidia-driver', 'nvidia-kernel-open-dkms'}
        for values in ({'trusted': False}, {'module_version': '550.163.01-1'}, {'extra': True}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                candidates.validate(self.cache(**values), allowed)

    def test_selected_runtime_versions_must_match_but_egl_helpers_are_independent(self):
        class Package:
            def __init__(self, name, version, source, deleted=False):
                self.name = name
                self.marked_delete = deleted
                self.candidate = SimpleNamespace(version=version, source_name=source)
            def mark_install(self):
                pass
        class Cache(dict):
            broken_count = 0
            def get_changes(self):
                return self.values()
        cache = Cache({name: Package(name, '620.70.10-1', 'nvidia-graphics-drivers')
                       for name in ('nvidia-open', 'nvidia-kernel-open-dkms', 'libnvidia-glcore')})
        cache['egl-helper'] = Package('libnvidia-egl-gbm1', '1.1.4-2', 'eglexternalplatform')
        candidates.validate_transaction(cache, '620.70.10-1')
        cache['libnvidia-glcore'].candidate.version = '625.1.1-1'
        with self.assertRaisesRegex(ValueError, 'Mixed NVIDIA'):
            candidates.validate_transaction(cache, '620.70.10-1')
        cache['libnvidia-glcore'].candidate.version = '620.70.10-1'
        cache['egl-helper'].marked_delete = True
        with self.assertRaisesRegex(ValueError, 'Unwanted removal'):
            candidates.validate_transaction(cache, '620.70.10-1')


if __name__ == '__main__':
    unittest.main()
