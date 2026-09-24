"""Preserve existing files and translate process definitions into service units."""
import configparser, pathlib
from systemd_common import setup, program
setup()
for file in pathlib.Path('/etc/supervisor/conf.d').glob('*.conf'):
 parser=configparser.ConfigParser(interpolation=None);parser.read(file)
 for section in parser.sections():
  if section.startswith('program:'):
   cfg=parser[section]
   program(section.split(':',1)[1],cfg['command'],cfg.get('user','root'),cfg.get('environment',''))
p=pathlib.Path('/home/trainee/problem.md')
s=p.read_text().replace('`sudo supervisorctl restart all`','a service restart').replace('Services use Supervisor, not systemd.','Services are managed by systemd.').replace('Use `sudo supervisorctl status` to inspect managed processes.','Use `systemctl` to manage services and `journalctl` to inspect their logs.').replace('Logs are in /var/log/lab; standard Linux configuration paths apply.','Service logs are in the journal; application-specific files may also be in /var/log/lab.').replace('Your notebook is incident-notes.md. ','')
p.write_text(s)
for name in ('skills.md','incident-notes.md'):(p.parent/name).unlink(missing_ok=True)
