# Historical VM migration

These notes describe backups on the original Linux workstation. They are not required for a new clone and the backup files are intentionally excluded from Git. Use docs/SETUP.md for macOS or a fresh Linux installation.

On 2026-09-09 the learner authorized resetting all progress. The five new Debian VMs therefore begin with fresh exercise state. Lab2 uses its replacement permissions exercise. Historical completions are not counted toward the new run.

The old Docker containers remain available, stopped with restart policies disabled. Their filesystem exports, selected-state archives and old launcher/configuration are in `.lab/vm-migration/`. Earlier snapshots remain in `.lab/systemd-migration/`. Backups are recovery material, not active learner state.

The VMs use KVM, the current user’s libvirt session and localhost SSH ports 2221–2225. All reset baselines were tested using separate disposable VM overlays. No reference fixes are applied to learner disks.

## Return to the retained Docker labs

Stop the VMs first so ports are free. Returning to Docker resumes historical container state, not new VM work:

```bash
./labctl stop
docker compose -p devops-practice start
cp .lab/vm-migration/container-ssh_config .lab/ssh_config
ssh -F .lab/ssh_config lab2
```

Use Docker commands to manage that older runtime. The current labctl manages VMs. To return to VMs, stop the containers with `docker compose -p devops-practice stop`, then run `./labctl start` and `./labctl ssh 2`.

Docker automatic restart remains disabled unless you deliberately restore it. Do not run both runtimes on the same SSH ports. Keep `.lab/` private and retain image backing files; deleting a backing image breaks its dependent disks. Reset archives can be removed when no longer needed, provided the VM uses the normal live-to-baseline backing chain.
