"""Run the image-processing pipeline on the test plan and optionally invoke Blender.

Usage:
  python scripts/run_pipeline.py

Set environment variable `BLENDER_PATH` to the blender executable to auto-run the Blender script.
"""
import os
import json
import subprocess
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
input_img = root / 'input' / 'test_plan.png'
output_json = root / 'output' / 'walls.json'


def run():
    # Ensure project root is on sys.path so `backend` package is importable
    sys.path.insert(0, str(root))
    from backend.image_processing import process_image

    if not input_img.exists():
        print('Test plan not found; generating one...')
        from scripts.generate_test_plan import make_test_plan
        make_test_plan(str(input_img))

    print('Processing:', input_img)
    walls = process_image(str(input_img), str(output_json), debug=True)
    print('Detected walls:', len(walls))
    print('Wrote JSON to', output_json)

    blender_path = os.environ.get('BLENDER_PATH')
    if blender_path:
        print('BLENDER_PATH found, invoking Blender to build glTF...')
        script = root / 'blender' / 'generate_3d.py'
        out_glb = root / 'output' / 'model.glb'
        cmd = [blender_path, '--background', '--python', str(script), '--', str(output_json), str(out_glb)]
        try:
            subprocess.check_call(cmd)
            print('Blender export completed:', out_glb)
        except Exception as e:
            print('Blender invocation failed:', e)
    else:
        print('BLENDER_PATH not set; skipping Blender step. Set BLENDER_PATH env var to run it.')


if __name__ == '__main__':
    run()
