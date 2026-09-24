# Recreate the labs on another machine

## macOS

Use a supported macOS/Homebrew installation, either Apple Silicon or Intel. Install:

```bash
brew install lima qemu python
python3 --version
limactl --version
```

Use Python 3.11+ and Lima 2.2+. If python3 still resolves to an older Apple installation, put Homebrew’s bin directory first in PATH. The setup script prints a clear version error before provisioning.

Authenticate GitHub on the Mac before cloning this private repository (for the SSH URL, add your Mac’s GitHub SSH public key to your account). The separate lab SSH key is generated automatically during setup.

Clone this repository into its final location. Run `./setup 1` to download a checksum-verified Debian image, create a dedicated SSH key, provision lab 1 and record its fresh disk snapshot. The command leaves the VM running. Install other incidents with `./setup N` or all eight with `./setup --all`.

Lima runs in SSH-only plain mode, without shared host folders or an application-forwarding guest agent. It uses QEMU here because the reset workflow needs QEMU disk snapshots. Apple Silicon selects ARM64 images; Intel selects x86-64 images. Hardware virtualization runs native architecture guests; Rosetta and Docker Desktop are not required. The guest services, fault setup and acceptance checks are shared with the Linux labs.

Allow several minutes for the first image download and package installation. The default installs only one lab to limit memory consumption. Each VM reserves 1 GiB RAM and has a sparse 10 GiB disk; snapshots and cached images need additional disk space. Reserve at least 20 GiB free space for initial practice and more if retaining many resets.

## Linux

The portable backend needs Lima 2.2+, QEMU with user-mode networking, firmware for the native architecture, OpenSSH client and Python 3.11+. Install these using the Lima documentation and your distribution’s packages. Ensure hardware virtualization is available to your user. Run `./setup 1`.

The original backend is also available on x86-64 Linux:

```bash
./setup --backend libvirt 1
```

It requires a working `virsh -c qemu:///session`, access to `/dev/kvm`, qemu-system-x86_64, qemu-img, passt, genisoimage and SSH. Setup does not silently install host packages or change host permissions. Existing `.lab/vm/config.json` selects this backend automatically. No existing lab is reset by setup.

## Daily use

```bash
./labctl start 1
./labctl ssh 1
./labctl verify 1
./labctl durable 1
./labctl stop 1
./labctl reset 1
```

`start` resumes installed labs and does not install missing ones. `reset` discards the active exercise changes while retaining a recovery snapshot/disk. Repeating `setup` skips completed installations; it does not update or reset them. To check status, use `./labctl status`.

If SSH ports 2221–2228 are already occupied, stop the conflicting application before setup. A failed setup can be retried with the same command. Provisioning errors remain visible; do not count an incomplete setup as a ready lab.

The Lima configuration and snapshots live under `.lab/lima/`, with a checkout-specific `LIMA_HOME`. For advanced inspection:

```bash
LIMA_HOME="$PWD/.lab/lima" limactl list
LIMA_HOME="$PWD/.lab/lima" limactl snapshot list lab1
```

For an explicit backend choice, prefix a command with `LAB_BACKEND=lima` or `LAB_BACKEND=libvirt`. Keep one active backend per checkout to avoid shared SSH-port collisions. The setup and test commands must run as your normal user, not root.

## Portability and validation

The portable path uses the same provisioning on both architectures. Linux/QEMU integration results are recorded in VALIDATION.md. Physical macOS and Apple Silicon boot tests require a Mac and have not been performed on the current Linux workstation. Do not interpret Linux test results as a completed Mac hardware test.

Only source is synchronized through Git. VM changes, snapshots, private keys, generated TLS keys and personal PROGRESS.md remain local and are ignored. Pulling new source does not modify running guest files. Existing migration backups remain on the original workstation and are not required for a new install.

References: [Lima QEMU backend](https://lima-vm.io/docs/config/vmtype/qemu/), [configuration](https://github.com/lima-vm/lima/blob/master/templates/default.yaml), [snapshots](https://lima-vm.io/docs/reference/limactl_snapshot_create/), [Debian images](https://cloud.debian.org/images/cloud/bookworm/).
