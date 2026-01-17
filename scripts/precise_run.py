import os
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from backend.image_processing import precise_process

# choose image
img = root / 'input' / 'images (2).png'
out = root / 'output' / (img.stem + '_precise.json')
walls, scale = precise_process(str(img), str(out), thickness_m=0.2, wall_height=3.0, orthogonal=True, debug=True)
print('Wrote precise JSON:', out)
print('Detected walls:', len(walls), 'scale m/px:', scale)

# optionally run blender to export
blender_path = os.environ.get('BLENDER_PATH')
if blender_path:
    script = root / 'blender' / 'generate_3d.py'
    glb_out = root / 'output' / (img.stem + '_precise.glb')
    import subprocess
    cmd = [blender_path, '--background', '--python', str(script), '--', str(out), str(glb_out)]
    try:
        subprocess.check_call(cmd)
        print('Blender export:', glb_out)
    except Exception as e:
        print('Blender failed:', e)
else:
    print('BLENDER_PATH not set; skipped 3D export')
