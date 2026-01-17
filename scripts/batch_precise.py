"""Batch precise processing and optional Blender export for all input images.

Usage:
  Set `BLENDER_PATH` env var to Blender executable to enable GLB export, then:
    .venv\Scripts\python scripts\batch_precise.py

This will write `<name>_precise.json` and `<name>_precise.glb` (if Blender available) to `output/`.
"""
import os
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from backend.image_processing import precise_process

def main():
    inp = root / 'input'
    out = root / 'output'
    out.mkdir(exist_ok=True)

    imgs = [p for p in inp.iterdir() if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.tif', '.tiff')]
    if not imgs:
        print('No input images found in', inp)
        return

    blender_path = os.environ.get('BLENDER_PATH')
    for p in imgs:
        name = p.stem
        json_out = out / f'{name}_precise.json'
        print('Processing', p.name)
        walls, scale = precise_process(str(p), str(json_out), thickness_m=0.2, wall_height=3.0, orthogonal=True, debug=True)
        print('  -> walls:', len(walls), 'scale m/px:', scale)

        if blender_path:
            glb_out = out / f'{name}_precise.glb'
            script = root / 'blender' / 'generate_3d.py'
            cmd = [blender_path, '--background', '--python', str(script), '--', str(json_out), str(glb_out)]
            try:
                import subprocess
                subprocess.check_call(cmd)
                print('  -> Blender exported', glb_out.name)
            except Exception as e:
                print('  -> Blender failed:', e)

    print('Batch precise processing complete.')

if __name__ == '__main__':
    main()
