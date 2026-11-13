from pathlib import Path
import sys
p = Path(sys.argv[1])
data = p.read_bytes()
t = data.decode('utf-8')
checks = {
    'git_heading': '## 3. Git 记录' in t,
    'granularity_heading': '### 3.1 提交边界与拆分规则' in t,
    'traceability_heading': '### 3.2 提交命名与可追溯性' in t,
    'precommit_heading': '### 3.3 提交前门禁' in t,
    'handoff_heading': '### 3.4 修正、暂停与远端' in t,
}
print(f'path={p.resolve()}')
print(f'bytes={len(data)}')
for name, ok in checks.items():
    print(f'{name}={int(ok)}')
sys.exit(0 if all(checks.values()) else 1)
