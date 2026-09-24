ARG BASE_IMAGE=debian:bookworm-slim
FROM ${BASE_IMAGE}
ENV DEBIAN_FRONTEND=noninteractive container=docker
RUN apt-get update && apt-get install -y --no-install-recommends systemd systemd-sysv dbus openssh-server sudo nginx-light python3 curl iproute2 iputils-ping dnsutils netcat-openbsd procps lsof strace less vim-tiny nano cron ca-certificates logrotate && rm -rf /var/lib/apt/lists/*
RUN if ! id trainee >/dev/null 2>&1; then useradd -m -s /bin/bash trainee && usermod -p '*' trainee; fi && if ! id app >/dev/null 2>&1; then useradd -m -s /usr/sbin/nologin app; fi && if ! id reporter >/dev/null 2>&1; then useradd -m -s /usr/sbin/nologin reporter; fi && echo 'trainee ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/trainee && chmod 440 /etc/sudoers.d/trainee && mkdir -p /opt/service /etc/lab /var/log/lab /home/trainee/.ssh && chmod 700 /home/trainee/.ssh && usermod -aG systemd-journal trainee
COPY lab/ /tmp/lab/
RUN install -m 755 /tmp/lab/entrypoint /usr/local/bin/lab-entrypoint && install -m 755 /tmp/lab/prepare /usr/local/bin/lab-prepare && install -m 755 /tmp/lab/verify.py /usr/local/bin/verify
ARG SCENARIO
ARG MIGRATE=0
RUN if [ "$MIGRATE" = 1 ]; then python3 /tmp/lab/migrate.py; else install -m 755 /tmp/lab/service.py /opt/service/service.py && install -m 755 /tmp/lab/export-report /usr/local/bin/export-report && install -m 755 /tmp/lab/publish-report /usr/local/bin/publish-report && python3 /tmp/lab/seed.py "$SCENARIO" && rm -f /etc/ssh/ssh_host_*; fi && if dpkg -s supervisor >/dev/null 2>&1; then apt-get purge -y supervisor; fi && rm -rf /tmp/lab /etc/supervisor && chown -R trainee:trainee /home/trainee
RUN apt-get update && apt-get install -y --no-install-recommends libpam-systemd dbus-user-session && rm -rf /var/lib/apt/lists/*
EXPOSE 22
STOPSIGNAL SIGRTMIN+3
ENTRYPOINT ["/usr/local/bin/lab-entrypoint"]
