"""One-time switch from retained Docker labs to the tested VM runtime."""
import concurrent.futures
from runtime import *
if not (STATE/'vm-tests-passed').exists():raise RuntimeError('Complete VM integration tests before switching')
config=read_config()
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 list(pool.map(lambda lab:shutdown(lab['name']),config.values()))
run(['sg','docker','-c','docker compose -p devops-practice stop'],cwd=ROOT)
run(['sg','docker','-c','docker update --restart=no '+' '.join(f'devops-practice-lab{n}-1' for n in range(1,6))],cwd=ROOT)
for n,lab in config.items():
 lab['port']=2220+int(n)
 directory=pathlib.Path(lab['directory'])
 define(lab['name'],directory/'live.qcow2',directory/'seed/seed.iso',lab['port'])
(STATE/'config.json').write_text(json.dumps(config,indent=2)+'\n')
write_ssh(config)
for lab in config.values():virsh('start',lab['name'],capture_output=True)
for lab in config.values():wait_ssh(lab['port'])
(ROOT/'labctl').write_text('#!/usr/bin/env bash\nset -euo pipefail\ncd -- "$(dirname -- "${BASH_SOURCE[0]}")"\nexec python3 vm/labctl.py "$@"\n')
(ROOT/'labctl').chmod(0o755)
print('All five VMs are ready on SSH ports 2221–2225.')
