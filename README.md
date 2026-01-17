# Skematix — 2D Floorplan to 3D (Rule-based, No ML)

Skematix converts 2D architectural floor plan images into 3D models using OpenCV-based image processing and Blender Python scripting — strictly NO ML.

Quick steps:

- Install Python deps: `pip install -r requirements.txt`
- Run the Flask backend: `python backend/app.py`
- Open `frontend/index.html` in a browser and upload a floorplan to the backend.
- Use Blender to run the provided Blender script to convert detected wall coordinates into a glTF file:

  ```bash
  blender --background --python blender/generate_3d.py -- input/walls.json output/model.glb
  ```

Notes:
- Blender must be installed separately. The Blender script (`blender/generate_3d.py`) uses `bpy` and must be run with Blender's Python.
- The pipeline is strictly rule-based (thresholding, morphology, contour detection, bounding-box approximation, extrusion).

Viewer:

- Open the 3D viewer at `frontend/viewer.html` (it loads `output/model.glb` from the backend). Start the Flask backend with `python backend/app.py` so the viewer can fetch the generated `.glb`.

Optimize & Deploy (GLB Draco + GitHub Pages):

1. Ensure you've run the pipeline and generated `output/model.glb` (Blender must be available as `BLENDER_PATH` or run `scripts/run_pipeline.py` with Blender installed).

2. Build `docs/` (this copies the viewer and `model.glb` into `docs/`):

```bash
.venv\Scripts\python scripts\build_docs.py
```

3. Commit and push to GitHub (the `pages.yml` workflow will deploy `docs/` to GitHub Pages on `main`):

```bash
git add docs/ .github/workflows/pages.yml
git commit -m "Prepare docs for GitHub Pages"
git push origin main
```

Notes:
- The workflow builds `docs/` on GitHub Actions and publishes it using `peaceiris/actions-gh-pages`.
- GitHub Pages will serve the site at `https://<your-username>.github.io/<repo-name>/` (or project pages URL depending on repo settings).

Quick demo (local):

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/generate_test_plan.py
python scripts/run_pipeline.py
python backend/app.py
```



See docstrings in `backend/image_processing.py` and `blender/generate_3d.py` for detailed usage.
