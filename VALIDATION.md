# VM validation

The five full Debian VMs passed the instructor integration suite in separate disposable disk overlays. Learner disks remain fresh and unsolved.

Validated for every exercise:

- Hardware-accelerated KVM guest with systemd as PID 1.
- SSH key authentication, passwordless sudo and functioning user systemd session.
- Only problem.md as visible learner material in the trainee home.
- Intended initial failure, successful reference repair, repair durability across a full guest reboot, and restoration of the initial failure after reset.
- Persistent journals with previous boot entries.
- Root process visibility for the exercise listeners where applicable.

A separate native strace attachment check passed. All guests report their own Debian kernel, 6.1.0-53-cloud-amd64. The six local functional tests and the five-layout scaffold check passed, as did Python and shell syntax checks. The initial sandboxed local test attempt could not create sockets; rerunning with host socket access passed.

The final runtime uses localhost SSH ports 2221–2225. The actual launcher start, status and single-exercise reset commands passed; SSH through the generated learner configuration passed. All five learner VMs are running. The old Docker containers are stopped with automatic restart disabled. Temporary test and bootstrap domains were removed. Source image SHA512 verification is recorded in `.lab/vm/base/verified.txt`. Detailed integration logs remain in `.lab/vm/test-results.log` and may expose solutions.

Earlier Docker validation is archived in `.lab/vm-migration/container-VALIDATION.md`. VM testing does not count as learner progress. Host reboot recovery is manual (`./labctl start`); an actual host reboot was not performed.


## Network extension — 2026-09-16

Labs 6, 7 and 8 passed the selected integration suite in separate disposable KVM VMs. Each passed native systemd/user-session checks, intended initial failure, dynamic response validation after reference repair, full reboot persistence, journal persistence and fresh reset failure. Additional checks covered both DNS transports, retention of required client isolation, and rejection of bypassed HTTPS validation. Packet and protocol tools are installed in each new guest.

Only new learner VMs were provisioned. Entries 1–5 in the runtime configuration matched the saved pre-addition configuration, and their running/stopped states were unchanged. No old learner disks were mounted, reset or repaired. New SSH connections were verified through the normal learner configuration on ports 2226–2228. All three new VMs remain fresh and running. No instructor repair was applied to them.

Logs: `.lab/vm/network-addition/tests.log` (can contain spoilers on failure). Tests run with `python3 vm/test_exercises.py 6 7 8`; `./labctl test N` now selects one disposable exercise test. Python and shell syntax checks passed. A package-default startup failure encountered during provisioning was cleared before clean baselines were produced; all finished guests report a running systemd state.


## Portable source checkout — 2026-09-24

The repository now includes a fresh-install path using Lima/QEMU, native ARM64/x86-64 image selection, dedicated guest SSH access, and per-exercise disk snapshots. Existing Linux libvirt state remains separate and unchanged. Image download verification refuses to overwrite an existing unrecognized backing image.

Host-only checks passed: five portability checks, six functional service tests, the scaffold test, Python compilation and shell syntax. A clean export of the staged source passed the same checks and setup help without any existing `.lab/` directory. Staged files were checked to exclude VM state, private keys, large images and personal progress.

Native macOS VM boot has not been tested on this Linux workstation. Architecture-selection checks and macOS source CI are separate from a physical Apple Silicon/Intel VM boot test. The exact installed image is recorded locally with its checksum; package versions follow Debian 12 repositories.

All eight exercises passed fresh installation, intended initial failure, reference repair, full guest restart and snapshot reset on the portable Lima 2.2.0/QEMU backend on x86-64 Linux. Tests used separate disposable Lima homes and ports 4221–4228; learner VMs were not repaired or reset. Early management-agent and SSH-identity/reload issues were corrected before the passing runs.
