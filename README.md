# Local Linux troubleshooting VMs

Eight independent Debian 12 virtual machines, each with its own Linux kernel, systemd, SSH server and persistent journal. Read this file, STUDY.md and the VM’s problem.md to avoid spoilers. Implementation, tests and instructor files can expose causes.

## macOS: clone and install

Install [Homebrew](https://brew.sh/) if it is not already available, then:

```bash
brew install lima qemu python
git clone git@github.com:vladimirazarov/devops-incidents-practice.git
cd devops-incidents-practice
./setup 1
./labctl ssh 1
```

Inside the VM, read `cat ~/problem.md`. Apple Silicon uses native ARM64 guests; Intel uses native x86-64 guests. Python 3.11 or later is required. See [setup details](docs/SETUP.md) for requirements and validation limits.

Install additional exercises when needed: `./setup 6 7 8`, or use `./setup --all`. Repeating setup skips completed installations. Start, stop and restart preserve your work. Only reset deliberately restores the fresh exercise.

Choose incidents 1–8. SSH uses trainee with passwordless sudo and a dedicated local key. Home contains only problem.md as learner material, plus hidden shell/SSH configuration. Start labs manually after a host restart with `./labctl start N`.

## Linux

Existing libvirt installations continue to use their existing VMs. A new clone uses the portable Lima backend by default; install Lima, QEMU and Python 3.11+, then run `./setup 1`. For an x86-64 Linux libvirt installation, use `./setup --backend libvirt 1`; see [setup details](docs/SETUP.md).

## Commands

```bash
./labctl status
./labctl start 2          # start one VM
./labctl stop             # gracefully stop all VMs, preserving disks
./labctl restart 2        # reboot one VM
./labctl verify 2         # also available as verify inside the VM
./labctl durable 2        # verify, reboot, verify again
./labctl reset 2          # restore a fresh exercise; previous disk retained
./labctl hint 2 1         # explicitly request hint level 1, 2 or 3
```

Reset affects only the selected VM. Lima retains a `before-reset-*` snapshot; libvirt retains the prior disk in `.lab/vm/labN/reset-history/`. Verification may temporarily change exercise data; avoid concurrent verifiers on one VM. Scheduled-work checks can take approximately 75 seconds.

Inside a VM, normal Linux commands apply: systemctl, journalctl, sudo ss -ltpn, lsof and strace. Guest reboot and shutdown operate on that VM. After guest shutdown, start it again from the host. Persistent journals support previous-boot inspection.

## Exercises

| # | Incident | Target time |
|---|---|---|
| 1 | The front door is closed | 20–25 min |
| 2 | The delivery desk (revision 2) | 20–30 min |
| 3 | Stock information unavailable | 25–35 min |
| 4 | Small requests look fine | 30–45 min |
| 5 | Yesterday’s numbers | 35–60 min |
| 6 | The order desk has gone quiet | 30–45 min |
| 7 | The branch is waiting | 40–60 min |
| 8 | Checkout is unavailable | 30–45 min |

The original five started fresh at the learner’s request during the VM migration. Labs 6–8 were added on 2026-09-16; previous VM state was preserved. Use STUDY.md for practice and revisit suggestions.

## Architecture and storage

Each exercise is a full Debian 12 VM with 1 virtual CPU, 1 GiB RAM and a 10 GiB sparse disk. Run one or two at a time on a smaller Mac; all eight need roughly 8 GiB RAM plus host/virtualization overhead.

The portable backend uses Lima with QEMU and native architecture virtualization. It uses disk snapshots for fresh resets. The existing Linux backend uses user-session libvirt/KVM, passt networking and qcow2 overlays. Both run real systemd, SSH and guest kernels. No host directories or Docker socket are mounted. SSH ports 2221–2228 bind to localhost; automatic application port forwarding is disabled on Lima.

Git contains the source and instructions, not VM disks, SSH keys, personal progress or backups. A new clone recreates fresh exercises; it does not transfer fixes made inside another machine’s VMs. Local state lives under `.lab/` and must remain intact. Do not move a checkout after creating VMs: hypervisor configuration contains absolute paths. Clone into its intended location and provision there.

Official Debian cloud images are downloaded over HTTPS and checked against Debian’s SHA512 sums. Images and packages are refreshed on a new machine, so builds are reproducible from source, not byte-for-byte identical. Provisioning needs internet; solving an installed exercise does not.

## Development

Run `python3 -m unittest discover -s tests -p 'test_*.py'` and the existing `tests/local.py` / `tests/scaffold.py` checks. `./labctl test N` runs instructor acceptance tests in disposable VMs. Tests, provisioning code and `instructor/` contain spoilers; avoid opening them while practicing. See [validation](VALIDATION.md).

The root Dockerfile and compose.yaml belong to the earlier container runtime and are retained as legacy source. Use `./setup` and `./labctl` for supported full-VM practice on macOS. [Migration notes](MIGRATION.md) describe historical Linux backups, which are not included in Git.

## Network practice

Labs 6–8 extend the curriculum with DNS/service discovery, routing and traffic filtering, and HTTPS/TLS at a reverse proxy. This is a practical selection of three recurring DevOps topics, not a measured universal ranking. See the official [Kubernetes service debugging guide](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/), [DNS debugging guide](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/) and [AWS load-balancer troubleshooting guide](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html) for the production contexts behind the selection. These links teach the broader topics; exercise-specific hints remain opt-in.

Start one exercise with `./labctl start 6`, then connect with `./labctl ssh 6`. Its problem.md defines the customer environment and required outcome. Network tools include tcpdump, dig, traceroute, mtr, ss, conntrack, nft and openssl. Internal client/service environments, where present, live entirely inside that VM; packet capture and internal policy changes do not modify the host network.

Use `probe YOUR_VALUE` to reproduce a request, `verify` to check acceptance and `./labctl durable N` to check reboot persistence. No internet access is required to solve these incidents. Avoid opening provisioning or instructor files during an unassisted attempt. `./labctl test 6` runs only the selected exercise on a disposable VM; it does not repair the learner VM.
