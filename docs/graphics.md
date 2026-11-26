# Graphics detection and driver installation

The graphics module runs immediately after desktop/hypervisor provisioning and
before the planned reboot. It reads PCI display adapters from sysfs. Virtual GPUs
retain Debian kernel/Mesa drivers and guest integration; the host GPU is not assumed
to be exposed inside a VM. A real passed-through GPU is detected normally.

`GRAPHICS_DRIVERS=ask` is the default. For physical NVIDIA or Intel/AMD adapters the
installer explains the package/source choice and asks through the terminal. The
default answer is no. Without a terminal it warns and skips, rather than treating
silence as permission. Use `yes` for an explicitly authorized unattended install,
or `no` to skip. A completed selection is recorded to avoid repeatedly asking for
the same driver family on rerun. Skipping later does not uninstall drivers.

Intel/AMD use native Debian firmware and Mesa: firmware-amd-graphics or
firmware-intel-graphics, libgl1-mesa-dri and mesa-vulkan-drivers. No AMDGPU-Pro,
Intel out-of-tree kernel replacements or custom Xorg layouts are installed.

## NVIDIA open kernel modules

This is NVIDIA's modern **open GPU kernel module**, not Nouveau or the older
proprietary kernel module. Matching NVIDIA firmware and desktop libraries remain
proprietary. The offer explicitly states this.

Debian Trixie/backports package pages inspected on 2026-11-25 listed a 550-series
driver predating the RTX 5060 Ti. NVIDIA's official Debian 13 repository provides
newer packages. Its authenticated GPU manifest explicitly marks PCI 10de:2d04,
GeForce RTX 5060 Ti, with kernelopen support. Current candidates observed during
validation were 620.70.10-1; that version is **not** hardcoded or held.

On consent, the installer configures the official signed amd64 source:

```
https://developer.download.nvidia.com/compute/cuda/repos/debian13/x86_64/
```

Although NVIDIA hosts it in the CUDA repository, only the exact driver/runtime
names in assets/nvidia.pref have priority 600. All other packages from that host
have priority -1. The nvidia-open meta-package includes driver runtime/diagnostic
and compute runtime libraries, but not the CUDA development toolkit. No Ubuntu,
testing/unstable, .run installer, or general replacement source is introduced.
Existing NVIDIA/CUDA sources or unmanaged drivers stop for migration review.

The official repository's 8793F200.pub must match fingerprint
`02182E60104FCDC26EAE1B8597A5D4CB8793F200`. This was observed from NVIDIA's current
Debian 13 publication and verified against its signed InRelease during development.
HTTPS and trust in NVIDIA's repository remain necessary; this is not independent
certification of key identity. Unexpected key rotation fails for review. The older
commonly documented 3BF863CC key was absent from this Debian 13 repository and is
not guessed or substituted.

Coherent authenticated nvidia-open, nvidia-driver and nvidia-kernel-open-dkms
candidates are required. The installer reads supported-gpus.json.gz from a fixed
member of the exact APT-authenticated nvidia-driver package. Every detected NVIDIA
display adapter must match its kernelopen flag and any subsystem IDs. Unsupported,
legacy-only or mixed incompatible GPUs stop before installing drivers. No PCI range
or model-name guess selects support. Versioned metadata is cached to avoid
repeated downloads for an unchanged candidate.

The transaction is simulated and removals rejected. Pre-install validation failure
restores previous key/source/preferences. Once driver installation begins the source
is retained for partial-run recovery.
An in-progress installation marker distinguishes this project's interrupted package
transaction from a pre-existing unmanaged stack, so it can be retried safely.
Debian kernel/header meta-packages supply
headers for the default next-boot kernel. modinfo must confirm matching version and
MIT/GPL open-module license for the kernel selected by Debian's /vmlinuz symlink.
No automatic reboot, explicit driver unload, display-manager restart or generated
xorg.conf is performed. Existing custom Xorg settings may need administrator review.

Normal signed-repository upgrades keep the matching packages updatable; no branch
hold/pinning package is installed. NVIDIA supplies security updates for these
packages. Debian advisory versions for its older driver do not certify NVIDIA's
newer builds. The exact allowlist may need review when vendor package names change.

## Secure Boot

Secure Boot is never disabled. On UEFI its state must be readable. If enabled,
the default DKMS MOK is generated if needed and must already be enrolled before
the driver transaction proceeds. Otherwise installation stops with instructions:

```bash
sudo mokutil --import /var/lib/dkms/mok.pub
```

Choose a temporary enrollment password, reboot through the physical MOK screen,
enroll the key, then rerun graphics provisioning. A script cannot complete this
console trust decision unattended. Custom DKMS signing-key arrangements require
administrator review. No enrollment password is stored in project configuration.

## Rerun and verification

Accept the offer during system provisioning. If X cannot start on the RTX 5060 Ti,
the installer can run from the initial console or SSH; no graphical session is
needed. To run only graphics from an updated complete checkout:

```bash
bash install.sh --module graphics --config config.local.conf
```

After reboot, the verifier checks a project-managed NVIDIA stack using modinfo,
nvidia-smi and glxinfo. Also inspect:

```bash
nvidia-smi
modinfo -F license nvidia
dkms status
glxinfo -B
journalctl -b -k --no-pager | grep -Ei 'nvidia|nouveau|verification|key was rejected'
```

Confirm the GPU, open module and accelerated renderer, then test resolution changes
and logout/login. Hybrid/multi-GPU routing remains native; the installer does not
force an NVIDIA-only Xorg configuration.

Hardware fixtures, candidate checks and actual signed-repository APT simulations
passed. DKMS installation, Secure Boot enrollment and RTX 5060 Ti display boot are
**not yet hardware validated**. They must be tested on the target workstation.

Optional read-only live dependency test (APT, python3-apt, network and a verified
keyring required):

```bash
python3 tests/graphics-repository-simulation.py \
  --keyring /etc/apt/keyrings/debian-workstation-nvidia.gpg
```

It uses isolated sources/lists/cache and empty dpkg status; it never installs drivers.

Primary sources: [NVIDIA Debian installation](https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/latest/debian.html),
[open module compatibility](https://github.com/NVIDIA/open-gpu-kernel-modules),
[Debian Trixie open module](https://packages.debian.org/trixie/nvidia-open-kernel-dkms),
[Debian backports driver](https://packages.debian.org/trixie-backports/nvidia-driver),
[NVIDIA Debian 13 repository](https://developer.download.nvidia.com/compute/cuda/repos/debian13/x86_64/).
