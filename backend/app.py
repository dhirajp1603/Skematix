from flask import Flask, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
import json
from image_processing import process_image
import subprocess
from pathlib import Path

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'input')
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'output')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/upload', methods=['POST'])
def upload_floorplan():
    if 'file' not in request.files:
        return jsonify({'error': 'no file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'no selected file'}), 400
    filename = secure_filename(file.filename)
    saved_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(saved_path)

    # Validate the image can be loaded
    import cv2
    img = cv2.imread(saved_path)
    if img is None:
        os.remove(saved_path)  # Remove invalid file
        return jsonify({'error': 'Invalid image file. Please upload a valid PNG or JPG image.'}), 400

    # Run precise image processing to extract wall coordinates (normalized coordinates)
    # Use unique filename based on input image name
    base_name = os.path.splitext(filename)[0]
    json_out = os.path.join(OUTPUT_FOLDER, f'{base_name}_walls.json')
    print(f"Processing image: {saved_path}, exists: {os.path.exists(saved_path)}")
    walls = []
    scale = None
    try:
        from image_processing import precise_process
        walls, scale = precise_process(saved_path, json_out, debug=False)
        print(f"Precise process succeeded, walls: {len(walls) if walls else 0}")
    except Exception as e:
        print(f"Precise process failed: {e}, falling back")
        try:
            walls = process_image(saved_path, json_out)
            print(f"Fallback process succeeded, walls: {len(walls) if walls else 0}")
        except Exception as e2:
            print(f"Fallback process also failed: {e2}")
            walls = []
            scale = None

    # Optionally run Blender to generate 3D (requires Blender installed)
    # Check common Blender installation paths
    blender_candidates = [
        os.environ.get('BLENDER_PATH'),  # From environment variable
        r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
        r"C:\Program Files (x86)\Blender Foundation\Blender\blender.exe",
    ]
    
    blender_path = None
    for candidate in blender_candidates:
        if candidate and os.path.exists(candidate):
            blender_path = candidate
            print(f"✓ Found Blender at: {blender_path}")
            break
    
    gltf_out = os.path.join(OUTPUT_FOLDER, f'{base_name}_model.glb')
    gltf_out_type2 = os.path.join(OUTPUT_FOLDER, f'{base_name}_model_type2.glb')
    gltf_url = None
    
    if blender_path:
        script_path = os.path.join(os.path.dirname(__file__), '..', 'blender', 'generate_3d.py')
        print(f"Script path: {script_path}, exists: {os.path.exists(script_path)}")
        print(f"JSON input: {json_out}, exists: {os.path.exists(json_out)}")
        
        cmd = [blender_path, '--background', '--python', script_path, '--', json_out, gltf_out]
        print(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            print(f"Blender stdout: {result.stdout}")
            if result.stderr:
                print(f"Blender stderr: {result.stderr}")
            print(f"Return code: {result.returncode}")
            
            if result.returncode == 0:
                if os.path.exists(gltf_out):
                    gltf_url = f'output/{base_name}_model.glb'
                    print(f"✓ Blender generation succeeded: {gltf_url}")
                    
                    # Now convert to production-grade professional cutaway model (open-top architectural visualization)
                    print(f"\n--- Converting to PRODUCTION-GRADE Cutaway model (open-top floor-plan visualization) ---")
                    cutaway_script = os.path.join(os.path.dirname(__file__), '..', 'blender', 'convert_to_cutaway_prod.py')
                    gltf_out_prod = os.path.join(OUTPUT_FOLDER, f'{base_name}_model_prod.glb')
                    cutaway_cmd = [blender_path, '--background', '--python', cutaway_script, '--', gltf_out, gltf_out_prod]
                    print(f"Production cutaway conversion command: {' '.join(cutaway_cmd)}")
                    
                    try:
                        cutaway_result = subprocess.run(cutaway_cmd, capture_output=True, text=True, timeout=300)
                        print(f"Production cutaway conversion stdout:\n{cutaway_result.stdout}")
                        if cutaway_result.stderr:
                            print(f"Production cutaway conversion stderr: {cutaway_result.stderr}")
                        print(f"Production cutaway return code: {cutaway_result.returncode}")
                        
                        if cutaway_result.returncode == 0 and os.path.exists(gltf_out_prod):
                            gltf_url = f'output/{base_name}_model_prod.glb'
                            print(f"✓ PRODUCTION-GRADE CUTAWAY CONVERSION SUCCEEDED: {gltf_url}")
                        else:
                            print(f"WARNING: Production cutaway conversion failed or output not found, using Type-1")
                            gltf_url = f'output/{base_name}_model.glb'
                    except Exception as e:
                        print(f"WARNING: Production cutaway conversion error: {type(e).__name__}: {e}")
                        print(f"Falling back to Type-1 model")
                        gltf_url = f'output/{base_name}_model.glb'
                else:
                    print(f"ERROR: Blender completed but output file not found: {gltf_out}")
            else:
                print(f"ERROR: Blender failed with return code {result.returncode}")
        except subprocess.TimeoutExpired:
            print(f"ERROR: Blender execution timed out (>300 seconds)")
        except Exception as e:
            print(f"ERROR: Blender execution failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("WARNING: Blender not found in any common installation path.")

    return jsonify({'walls': walls, 'scale': scale, 'filename': filename, 'gltf': gltf_url})


@app.route('/input/<path:filename>')
def serve_input(filename):
    base = os.path.join(os.path.dirname(__file__), '..', 'input')
    return send_from_directory(base, filename)


@app.route('/output/<path:filename>')
def serve_output(filename):
    base = os.path.join(os.path.dirname(__file__), '..', 'output')
    return send_from_directory(base, filename)


@app.route('/vendor/<path:filename>')
def serve_vendor(filename):
    # serve three.js and loader modules placed in docs/vendor
    base = os.path.join(os.path.dirname(__file__), '..', 'docs', 'vendor')
    return send_from_directory(base, filename)


@app.route('/frontend/<path:filename>')
def serve_frontend(filename):
    base = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_from_directory(base, filename)


# Serve static assets (CSS, JS, etc)
@app.route('/static/<path:filename>')
def serve_static(filename):
    base = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_from_directory(base, filename)


@app.route('/detections', methods=['GET'])
def list_detections():
    out_dir = Path(os.path.join(os.path.dirname(__file__), '..', 'output'))
    files = list(out_dir.glob('*_walls.json'))
    data = {}
    for f in files:
        try:
            with open(f, 'r') as fh:
                data[f.stem.replace('_walls','')] = json.load(fh)
        except Exception:
            continue
    return jsonify(data)


@app.route('/detections/save', methods=['POST'])
def save_detections():
    payload = request.get_json()
    if not payload or 'image' not in payload or 'data' not in payload:
        return jsonify({'error': 'invalid payload'}), 400
    image = payload['image']
    data = payload['data']
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f'{image}_walls.json')
    with open(out_file, 'w') as fh:
        json.dump(data, fh, indent=2)
    return jsonify({'ok': True})


if __name__ == '__main__':
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 5000))
    print(f'Starting Skematix backend on http://{host}:{port} (press CTRL+C to stop)')
    app.run(debug=True, host=host, port=port)
