# Skematix: Fully Automated Blueprint-to-3D Cutaway Pipeline

## Executive Summary

**Skematix** is a production-grade, deterministic pipeline that converts 2D architectural blueprint images into accurate 3D open-top architectural cutaway models in GLB format.

### Key Features

✅ **Semantic-First Architecture** – Understands blueprint meaning before generating geometry  
✅ **Deterministic Behavior** – No randomness, no manual intervention, no guessing  
✅ **FAIL FAST Gates** – Explicit validation checkpoints halt pipeline if quality thresholds not met  
✅ **Architectural Accuracy** – Preserves wall topology, room separation, dimensions  
✅ **Open-Top Cutaway** – Interior fully visible from above, no roofs or closed boxes  
✅ **Real-World Metrics** – Metric normalization ensures 1 Blender unit = 1 real-world meter  
✅ **Industry-Standard Export** – GLB 2.0 format, directly usable in Blender/Three.js  

---

## 9-Stage Pipeline Architecture

### Stage 1: Semantic Understanding
**Purpose:** Classify blueprint pixels using pretrained deep learning model

- **Input:** Blueprint image (PNG/JPG)
- **Model:** DeepLabV3+ with ResNet50 encoder
- **Output:** Per-pixel semantic masks
  - Class 0: BACKGROUND (empty space, furniture, text)
  - Class 1: WALL (structural walls, partitions)
  - Class 2: DOOR (door openings)
  - Class 3: WINDOW (window openings)

**Why This Matters:** Semantic understanding DEFINES what is architectural and what is decorative. All downstream geometry depends on this classification.

**Failure Mode:** If semantic segmentation fails or misclassifies walls as background, pipeline halts (FAIL FAST).

---

### Stage 2: Wall Mask Refinement
**Purpose:** Clean semantic wall masks while preserving continuity

**Algorithm:**
1. Extract wall pixels from semantic mask
2. Remove door/window regions (they are gaps, not walls)
3. Apply morphological operations (closing, opening)
4. Remove small isolated components
5. Validate continuity

**Key Principle:** Walls must remain continuous even through door openings. A door is a functional gap, not a structural wall absence.

**Output:** Binary wall mask with clean, continuous wall regions

---

### Stage 3: Topology Extraction (CRITICAL)
**Purpose:** Convert wall masks into vector topology

**Algorithm:**
1. Skeletonize wall regions (medial axis transform)
2. Detect junctions, corners, and endpoints
3. Trace edges from skeleton
4. Build wall topology graph

**Output:** WallTopologyGraph with:
- **Vertices:** Junction points (2+ edges meeting)
- **Edges:** Wall segments connecting vertices
- **Adjacency:** Connectivity information

**Why Critical:** This graph is the SINGLE SOURCE OF TRUTH for all 3D geometry. If the graph is broken (disconnected), room detection fails and pipeline halts.

---

### Stage 4: Room Detection (FAIL FAST Gate #1)
**Purpose:** Identify all enclosed rooms using wall topology

**Algorithm:**
1. Use wall mask to define room boundaries
2. Flood-fill from interior to find enclosed regions
3. Label each connected region as a room
4. Validate: no room merging, no overlaps

**FAIL FAST Condition:** If any two rooms share interior space (overlap), pipeline HALTS immediately. This indicates broken wall topology.

**Output:** RoomSet with:
- Room ID, pixel count, area, perimeter
- Centroid and bounding box

**Why FAIL FAST?** Room merging means walls are not properly separated. Continuing would produce incorrect geometry.

---

### Stage 5: Metric Normalization
**Purpose:** Convert pixel coordinates to real-world meters

**Algorithm:**
1. Measure building width from wall graph bounding box
2. Compute scale factor: REFERENCE_WIDTH ÷ detected_width
3. Transform all coordinates to meters
4. Validate normalized dimensions are reasonable

**Reference Standard:** 
- Building width: 12.0 m (typical residential)
- Range: 10.5–13.5 m (acceptable variance)
- 1 Blender unit = 1 meter

**Output:** Normalized wall graph and room set with metric coordinates

**Determinism:** Scale factor is always the same for identical image dimensions. No randomness.

---

### Stage 6: 3D Cutaway Construction
**Purpose:** Generate 3D volumetric geometry from normalized topology

**Geometry Specifications:**
- **Walls:**
  - Thickness: 0.22 m (masonry standard)
  - Height: 1.3 m (open-top cutaway)
  - Continuous at all junctions
  
- **Floor Slab:**
  - Thickness: 0.12 m (structural slab)
  - Positioned at Z=0 (ground plane)
  - Extends slightly beyond walls with padding
  
- **Topology:** 
  - All geometry must be watertight and manifold
  - No floating geometry or cracks
  - Normals recalculated for smooth rendering

**Algorithm:**
1. Build floor slab as rectangular base
2. Extrude each wall edge to 3D volume
3. Create rectangular wall boxes with correct dimensions
4. Ensure continuity at junctions
5. Recalculate vertex normals

**Output:** Mesh object with:
- Vertex positions (x, y, z) in meters
- Per-vertex normals for lighting
- Triangle faces (vertices + indices)

---

### Stage 7: Openings Generation
**Purpose:** Create door and window cutouts in walls

**Door Specification:**
- Width: 0.9 m
- Height: clipped to wall height (1.1 m)
- Positioned: center of wall
- Geometry: clean rectangular cuts

**Window Specification:**
- Width: 0.8 m
- Height: 0.5 m (vision height)
- Sill: 0.65–0.80 m above floor
- Count: distributed along exterior walls

**Algorithm:**
1. Detect door/window locations from Stage 1 semantic masks
2. Map 2D positions to 3D wall locations
3. Create rectangular cutting volumes
4. Apply manifold-safe boolean subtraction
5. Recalculate normals

**Output:** Mesh with doors and windows cut out, preserving manifold property

---

### Stage 8: Comprehensive Validation (FAIL FAST Gate #2)
**Purpose:** Programmatic validation of model correctness

**Validation Checks:**

**Mesh Properties:**
- ✓ Vertex count ≥ 8
- ✓ Face count ≥ 12
- ✓ Manifold topology (each edge shared by exactly 2 faces)
- ✓ No NaN or Inf values
- ✓ Z-range ≥ 0.5 m (height)
- ✓ X, Y ranges > 0 (width and depth)

**Architectural Properties:**
- ✓ Wall count ≥ 1
- ✓ Room count ≥ 1
- ✓ No room merging or overlaps
- ✓ Graph connectivity verified

**Cutaway-Specific:**
- ✓ No roof (max Z < 3.0 m)
- ✓ Open-top (interior visible from above)
- ✓ Floor exists (vertices near z=0 and z<0)

**FAIL FAST Condition:** If ANY critical check fails, pipeline halts immediately with explicit error message.

**Output:** ValidationResult with pass/fail status for each check

---

### Stage 9: Export to GLB
**Purpose:** Export validated model to industry-standard GLB 2.0 format

**GLB Format Details:**
- Binary glTF 2.0 with embedded assets
- Single file with .glb extension
- Includes:
  - Vertex positions (VEC3 float32)
  - Vertex normals (VEC3 float32)
  - Face indices (UNSIGNED_INT)
  - Materials (colors per specification)
  - Metadata (scale factor, room count, etc.)

**Material Colors:**
- Walls: RGB(0.92, 0.85, 0.74) – Warm beige
- Floor: RGB(0.45, 0.45, 0.48) – Neutral gray

**Output:** .glb file ready for:
- Blender (File → Import → glTF 2.0)
- Three.js (THREE.GLTFLoader)
- Babylon.js, Cesium.js, etc.
- No post-processing required

---

## Design Principles

### 1. Semantic-First
**All architecture is defined by semantic understanding, not heuristics.**
- Stage 1 classifies pixels into meaningful categories
- Stages 2-9 process these semantically-defined regions
- No "guessing" about what pixels mean

### 2. Deterministic
**Identical inputs always produce identical outputs.**
- No randomness (fixed random seeds where needed)
- No floating-point ambiguity (proper validation)
- Explicit scale factors for reproducibility

### 3. Fail-Fast
**Validation gates halt pipeline explicitly if quality thresholds not met.**
- Stage 4: Room detection must not merge
- Stage 8: Comprehensive validation or halt
- No silent failures or workarounds

### 4. Architectural Correctness
**Model preserves blueprint topology and dimensions.**
- Wall continuity maintained
- Room separation preserved
- Metric accuracy: 1 unit = 1 meter
- Wall specifications: 0.22 m thick, 1.3 m tall

### 5. No Manual Intervention
**Pipeline is fully automated.**
- No clicks, annotations, or corrections
- No post-hoc "fixing"
- No visual hacks or camera tricks

---

## File Structure

```
pipeline/
├── orchestrator.py                    # Main entry point
├── stage1_semantic_segmentation.py   # Deep learning classification
├── stage2_wall_refinement.py         # Morphological cleanup
├── stage3_topology_extraction.py     # Skeletonization & graph
├── stage4_room_detection.py          # Enclosed region detection
├── stage5_metric_normalization.py    # Pixel → meters conversion
├── stage6_3d_construction.py         # Wall & floor extrusion
├── stage7_openings.py                # Door/window cutouts
├── stage8_validation.py              # Comprehensive checks
└── stage9_export.py                  # GLB export

backend/
├── app.py                            # Flask REST API
├── image_processing.py               # Utility functions
└── __init__.py

output/
├── *.glb                             # Generated models
└── *.json                            # Intermediate outputs

test_pipeline_integration.py           # End-to-end tests
```

---

## Usage

### Command-Line

```bash
# Full pipeline from command-line
python pipeline/orchestrator.py input/blueprint.png

# Output: output/blueprint_cutaway.glb
```

### Python API

```python
from pipeline.orchestrator import BlueprintPipeline

# Create pipeline
pipeline = BlueprintPipeline(
    image_path='input/blueprint.png',
    device='cuda',  # or 'cpu', 'auto'
    verbose=True
)

# Run full pipeline
success, message = pipeline.run_full_pipeline()

if success:
    print(f"✓ Success: {message}")
    summary = pipeline.get_summary()
    print(f"  Rooms: {summary['room_count']}")
    print(f"  Walls: {summary['wall_count']}")
    print(f"  Output: {summary['output_path']}")
else:
    print(f"✗ Failed: {message}")
    for error in pipeline.errors:
        print(f"  - {error}")
```

### Flask REST API

```bash
# Start server
cd backend
python app.py

# Upload blueprint image
curl -F "file=@blueprint.png" http://localhost:5000/process

# Response
{
  "success": true,
  "output_path": "output/blueprint_cutaway.glb",
  "room_count": 5,
  "wall_count": 12,
  "scale_factor": 45.2
}
```

---

## Configuration

### Wall Specifications (stage6_3d_construction.py)
```python
WALL_THICKNESS = 0.22      # meters
WALL_HEIGHT = 1.3          # meters (open-top)
FLOOR_SLAB_THICKNESS = 0.12  # meters
```

### Door/Window Specifications (stage7_openings.py)
```python
DoorSpec:
  width = 0.9 m
  height = 1.1 m (clipped to wall height)
  z_bottom = 0.0 (flush with floor)

WindowSpec:
  width = 0.8 m
  height = 0.5 m
  sill_height = 0.65 m
```

### Metric Normalization (stage5_metric_normalization.py)
```python
REFERENCE_BUILDING_WIDTH = 12.0  # meters
REFERENCE_WIDTH_MIN = 10.5       # meters
REFERENCE_WIDTH_MAX = 13.5       # meters
```

---

## Quality Assurance

### Validation Checklist

- [ ] Stage 1 semantic classification (4 classes: BG, WALL, DOOR, WINDOW)
- [ ] Stage 2 wall continuity preserved through openings
- [ ] Stage 3 topology graph connected and non-empty
- [ ] Stage 4 rooms detected, no overlaps, no merging
- [ ] Stage 5 scale factor reasonable (0.1–100 px/m)
- [ ] Stage 6 wall extrusion produces manifold geometry
- [ ] Stage 7 openings cut cleanly without breaking manifold
- [ ] Stage 8 validation passes all 12+ checks
- [ ] Stage 9 GLB file exists and is valid

### Testing

```bash
# Run integration tests
python test_pipeline_integration.py

# Output: test report with pass/fail for each stage
```

---

## Performance

Typical performance on residential blueprint (12 m × 8 m):
- Stage 1 (Semantic): ~2–3 seconds (GPU) / ~10 seconds (CPU)
- Stage 2 (Refinement): ~0.1 seconds
- Stage 3 (Topology): ~0.2 seconds
- Stage 4 (Rooms): ~0.1 seconds
- Stage 5 (Normalization): ~0.05 seconds
- Stage 6 (3D): ~0.3 seconds
- Stage 7 (Openings): ~0.2 seconds
- Stage 8 (Validation): ~0.1 seconds
- Stage 9 (Export): ~0.5 seconds

**Total:** ~3–13 seconds (depending on GPU availability)

---

## Troubleshooting

### Pipeline Fails at Stage 1 (Semantic Segmentation)
**Symptom:** "Semantic segmentation failed"  
**Solution:** 
- Verify blueprint image is clear and in PNG/JPG format
- Check image contains clear wall lines (not sketches)
- Ensure walls are darker than background
- Model requires architectural blueprints, not hand sketches

### Pipeline Halts at Stage 4 (Room Detection)
**Symptom:** "FAIL FAST: Rooms merged" or "Room overlap detected"  
**Solution:**
- Walls may not be properly separated in Stage 2
- Check refined wall mask is continuous
- Verify door/window masks are accurate
- May indicate blueprint quality issues (thin walls, unclear partitions)

### Pipeline Halts at Stage 8 (Validation)
**Symptom:** "Validation failed: Non-manifold edges" or "No roof check failed"  
**Solution:**
- Mesh topology corrupted during Stage 6 or 7
- Check wall extrusion is not self-intersecting
- Verify opening cuts don't breach wall boundaries
- May indicate edge cases in junction handling

### Export Produces Invalid GLB
**Symptom:** "GLB file not readable in Blender/Three.js"  
**Solution:**
- Check output file size > 1 KB
- Verify vertex and index counts match
- Ensure normals were recalculated (Stage 6)
- Check no NaN or Inf values in geometry

---

## Extension Points

### Custom Materials
Modify [stage9_export.py](stage9_export.py#L28-L35):
```python
COLORS = {
    'wall': [r, g, b],      # Your color
    'floor': [r, g, b],
    ...
}
```

### Custom Dimensions
Modify [stage6_3d_construction.py](stage6_3d_construction.py#L15-L18):
```python
WALL_THICKNESS = 0.25  # Your thickness
WALL_HEIGHT = 1.5      # Your height
```

### Custom Semantic Classes
Extend [stage1_semantic_segmentation.py](stage1_semantic_segmentation.py#L35-L41):
```python
class SemanticClass:
    BACKGROUND = 0
    WALL = 1
    DOOR = 2
    WINDOW = 3
    FURNITURE = 4  # New class
    ...
```

---

## Technical Specifications

### Input Requirements
- Format: PNG, JPG, or other common image formats
- Resolution: 512×512 to 4096×4096 pixels
- Content: Architectural floor plan with clear wall lines
- Contrast: Walls should be distinct from background

### Output Specifications
- Format: glTF 2.0 (GLB binary)
- Scale: 1 Blender unit = 1 real-world meter
- Units: Metric (SI)
- Material: PBR with base color
- Metadata: JSON extensions with scale, room count, etc.

### Computational Requirements
- **CPU:** Intel i5/AMD Ryzen 5 or better (12 seconds)
- **GPU:** NVIDIA/AMD with CUDA/HIP (3 seconds, Semantic Stage only)
- **Memory:** ≥4 GB RAM
- **Disk:** ≥1 GB for models and intermediates

---

## References

### Deep Learning
- DeepLabV3+: Chen et al., "Encoder-Decoder with Atrous Separable Convolution for Semantic Image Segmentation" (2018)
- ResNet50: He et al., "Deep Residual Learning for Image Recognition" (2015)

### Geometry Processing
- Skeletonization: Zhang & Suen medial axis algorithm
- Manifold: Topological validation per OpenGL specifications
- Boolean Operations: Manifold-safe constructive solid geometry

### Standards
- glTF 2.0: https://www.khronos.org/gltf/
- Blender Import: File → Import → glTF 2.0 (.glb/.gltf)

---

## License

[Specify your license here]

## Authors

Skematix Development Team – Architecture & Computer Vision

---

## Changelog

### Version 1.0 (January 2026)
- Complete 9-stage pipeline implementation
- Semantic-first architecture
- FAIL FAST validation gates
- Metric normalization (meters)
- Open-top cutaway generation
- GLB 2.0 export
- Comprehensive validation

---

## Support & Contact

For issues, questions, or contributions, please open an issue or contact the development team.

**Key Contacts:**
- Architecture: [Contact]
- Computer Vision: [Contact]
- Geometry: [Contact]
