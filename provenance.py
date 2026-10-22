"""Trace the exact source and exported bytes used for a simulation run."""
import hashlib
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL_VERSION = 'nightwise-simulation-v1'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_output(*args):
    try:
        return subprocess.check_output(['git', '-C', str(ROOT), *args],
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def source_provenance():
    paths = sorted([*ROOT.glob('*.py'), *ROOT.glob('*config.json'), ROOT / 'requirements.txt'])
    hashes = {p.name: sha256(p) for p in paths if p.is_file()}
    # Hash the ordered manifest too, so local edits cannot masquerade as the base commit.
    digest = hashlib.sha256('\n'.join(f'{k}:{v}' for k, v in hashes.items()).encode()).hexdigest()
    dependencies = {}
    for name in ('streamlit', 'pandas', 'plotly'):
        try:
            dependencies[name] = version(name)
        except PackageNotFoundError:
            dependencies[name] = None
    return {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'git_commit': git_output('rev-parse', 'HEAD'),
        'git_worktree_status': git_output('status', '--porcelain', '--untracked-files=all'),
        'source_sha256': hashes,
        'source_manifest_sha256': digest,
        'python_version': sys.version,
        'platform': platform.platform(),
        'dependency_versions': dependencies,
        'reproduction_command': 'python export_results.py --scenario all',
        'note': 'Commit identifies the base revision; nonempty worktree status means local changes. Source hashes identify the actual code/configuration used. Null git fields mean Git was unavailable.',
    }
