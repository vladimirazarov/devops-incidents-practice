# Learner preferences

- This is a troubleshooting practice lab. Do not reveal a cause, solution, diagnostic hint, or contents of instructor material in commentary or final answers unless the learner explicitly requests that level of help.
- Treat accidental solution exposure as an assisted completion, not independent mastery. Record progress in PROGRESS.md.
- When replacing an exercise, test the replacement in the separate disposable test VMs, and recreate only the requested learner VM. Preserve other exercises and their progress.
- Keep problem.md free of root causes and solution-specific terminology. Hints must remain explicitly opt-in.
- Home directories must contain only problem.md as learner material; do not generate skills.md or incident-notes.md, or add notebook workflows. Preserve hidden SSH/shell configuration and existing troubleshooting state.
- The lab now uses real systemd as PID 1. Use actual service units and journal logging; do not replace systemctl with a wrapper or return to Supervisor. Keep start/resume separate from destructive reset.

- Runtime: full Debian KVM VMs managed by user-session libvirt. All progress was reset with explicit learner authorization during the VM migration; prior Docker backups are historical only.

- Portable clones use full Debian VMs through Lima/QEMU on macOS and Linux. Existing Linux libvirt labs retain their backend and state. Keep machine-local progress, disks, credentials and backups out of Git.
