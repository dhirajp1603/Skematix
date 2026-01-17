"""Build a static `docs/` folder for GitHub Pages.

Copies viewer, index, review, and generated `output/model.glb` into `docs/`.
Run: .venv\Scripts\python scripts\build_docs.py
"""
import shutil
from pathlib import Path
import os

root = Path(__file__).resolve().parents[1]
docs = root / 'docs'
frontend = root / 'frontend'
output = root / 'output'

def build():
    if docs.exists():
        shutil.rmtree(docs)
    docs.mkdir()

    # copy frontend files
    for fname in ['index.html', 'viewer.html', 'review.html']:
        src = frontend / fname
        if src.exists():
            shutil.copy(src, docs / fname)

    # copy other assets in frontend (none currently)

    # copy model files
    for g in output.glob('*.glb'):
        shutil.copy(g, docs / g.name)

    # copy sample JSON outputs for reference
    for j in output.glob('*_walls.json'):
        shutil.copy(j, docs / j.name)

    print('Built docs/ with contents:')
    for p in sorted(docs.iterdir()):
        print(' -', p.name)

if __name__ == '__main__':
    build()
