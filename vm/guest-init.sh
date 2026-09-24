#!/bin/bash
set -euo pipefail
n=$1
for user in app reporter; do
 if ! id "$user" >/dev/null 2>&1; then useradd -m -s /usr/sbin/nologin "$user"; fi
done
mkdir -p /opt/service /var/log/lab
if (( n >= 6 )); then
 python3 /tmp/lab/network/seed.py "$n"
 rm -rf /tmp/lab
 mkdir -p /var/lib/devops-lab
 printf '%s\n' "$n" > /var/lib/devops-lab/ready
 exit 0
fi
install -m 755 /tmp/lab/service.py /opt/service/service.py
install -m 755 /tmp/lab/verify.py /usr/local/bin/verify
install -m 755 /tmp/lab/export-report /usr/local/bin/export-report
install -m 755 /tmp/lab/publish-report /usr/local/bin/publish-report
systemctl stop nginx cron || true
LAB_RUNTIME=vm python3 /tmp/lab/seed.py "$n"
printf '\n127.0.0.1 inventory.internal\n' >> /etc/hosts
chown -R trainee:trainee /home/trainee
systemctl daemon-reload
systemctl restart systemd-journald
# Start only the exercise units which this seed installed.
for unit in application nginx reports inventory gateway processor cron; do
 if [[ -f /etc/systemd/system/$unit.service ]]; then systemctl start "$unit"; fi
done
sshd -t
systemctl reload ssh
rm -rf /tmp/lab
mkdir -p /var/lib/devops-lab
printf '%s\n' "$n" > /var/lib/devops-lab/ready
