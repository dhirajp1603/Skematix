"""Process all images in the `input/` folder and write JSON + debug images to `output/`.

Usage: .venv\\Scripts\\python scripts\\batch_process.py
"""
import os
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from backend.image_processing import process_image


def main():
    inp = root / 'input'
    out = root / 'output'
    out.mkdir(exist_ok=True)

    imgs = [p for p in inp.iterdir() if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.tif', '.tiff')]
    if not imgs:
        print('No input images found in', inp)
        return

    summary = {}
    for p in imgs:
        name = p.stem
        json_out = out / f'{name}_walls.json'
        print('Processing', p.name)
        walls = process_image(str(p), str(json_out), debug=True)
        # move debug image if created next to input into output for inspection
        debug_src = p.parent / 'debug_processed.png'
        if debug_src.exists():
            debug_dst = out / f'{name}_debug.png'
            try:
                debug_src.replace(debug_dst)
            except Exception:
                try:
                    import shutil
                    shutil.copy(str(debug_src), str(debug_dst))
                except Exception:
                    pass
        summary[p.name] = len(walls)

    print('\nSummary:')
    for k, v in summary.items():
        print(f'  {k}: {v} walls')


if __name__ == '__main__':
    main()
