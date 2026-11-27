from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
version='0.3.1'
required=['CHANGELOG.md','HANDOVER.md','TASKS.md','AGENTS.md','README.md','SECURITY.md','docs']
missing=[x for x in required if not (root/x).exists()]
errors=[]
if missing: errors.append('Missing required root entries: '+', '.join(missing))
for name in ['CHANGELOG.md','HANDOVER.md']:
    p=root/name
    if p.exists() and version not in p.read_text(encoding='utf-8'):
        errors.append(f'{name} does not mention current version {version}')
if (root/'adaptive-fitness-os').exists(): errors.append('Unexpected nested adaptive-fitness-os source root')
if errors:
    print('\n'.join(errors)); sys.exit(1)
print(f'Fitness AI v{version} package structure: OK')
