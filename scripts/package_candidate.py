"""Package an explicit file allowlist; smoke-test only in a fresh temporary folder."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'release-files.json'


def main():
    names = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if len(names) != len(set(names)):
        raise ValueError('Duplicate release path')
    records = []
    patterns = {
        'private_key': r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',
        'github_token': r'gh[pousr]_[A-Za-z0-9]{30,}',
        'personal_path': r'[A-Za-z]:[/\\](?:Users|Projects)[/\\]',
        'email': r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',
        'mobile': r'(?<!\d)1[3-9]\d{9}(?!\d)',
    }
    for name in names:
        path = ROOT / name
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT) or not path.is_file():
            raise ValueError('Unsafe or missing release file: ' + name)
        if any(part in {'.env', '.git', '.venv', 'private', 'output', 'workspaces', '__pycache__'} for part in path.relative_to(ROOT).parts):
            raise ValueError('Forbidden release path: ' + name)
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        for label, pattern in patterns.items():
            if re.search(pattern, text):
                raise ValueError(f'Privacy review required: {name} ({label})')
        records.append({'path':name, 'size':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()})
    out = ROOT / 'output/release'
    out.mkdir(parents=True, exist_ok=True)
    archive = out / 'Resume-Engineering-0.5.0.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for row in records:
            z.write(ROOT / row['path'], 'Resume-Engineering/' + row['path'])
    with tempfile.TemporaryDirectory(prefix='resume-skill-check-') as tmp:
        with zipfile.ZipFile(archive) as z:
            if z.testzip(): raise ValueError('Corrupt archive')
            z.extractall(tmp)  # Entries above are fixed, reviewed relative allowlist paths.
        extracted = Path(tmp) / 'Resume-Engineering'
        subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-q'], cwd=extracted, check=True)
        pipeline = extracted / 'skill/resume-engineering/scripts/pipeline.py'
        workspace = Path(tmp) / 'isolated-workspace'
        subprocess.run([sys.executable, str(pipeline), 'init-demo', '--workspace', str(workspace), '--fixture', str(extracted / 'examples/synthetic-person/workflow.json')], check=True)
        subprocess.run([sys.executable, str(pipeline), 'build', '--workspace', str(workspace), '--targets', 'website', 'resume:process', 'assistant'], check=True)
    report = {'status':'local_release_ready', 'license':'MIT', 'files':records, 'count':len(records), 'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(), 'extracted_tests':'passed', 'isolated_generation':'passed', 'privacy_scan':'listed_patterns_passed_not_exhaustive'}
    (out / 'package-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='files'}))


if __name__ == '__main__': main()
