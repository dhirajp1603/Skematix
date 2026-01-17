# QUICK START GUIDE
## Running the Semantic Blueprint Pipeline

---

## PREREQUISITES

### Python Environment
```bash
python --version
# Python 3.10+ required
```

### Required Packages
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install opencv-python scipy numpy pillow
pip install torch-geometric  # Optional: for future graph operations
```

### Optional: GPU Acceleration
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"
# Should return True if GPU is available
```

---

## RUNNING STAGES 1-4

### Option A: Using Orchestrator (All Stages)

```python
from pipeline.orchestrator import BlueprintPipeline

# Create pipeline
pipeline = BlueprintPipeline(
    image_path='path/to/blueprint.png',
    device='cuda',  # or 'cpu'
    verbose=True
)

# Run stages 1-4
success, message = pipeline.run_full_pipeline()

if success:
    print("Success!")
    print(f"Rooms detected: {len(pipeline.room_set.rooms)}")
    print(f"Walls: {len(pipeline.wall_graph.edges)}")
else:
    print(f"Failed: {message}")
    print(f"Errors: {pipeline.errors}")
```

### Option B: Running Individual Stages

```python
from pipeline.stage1_semantic_segmentation import stage1_semantic_segmentation
from pipeline.stage2_wall_refinement import stage2_wall_mask_refinement
from pipeline.stage3_topology_extraction import stage3_topology_extraction
from pipeline.stage4_room_detection import stage4_room_detection

# Stage 1
semantic_output = stage1_semantic_segmentation('blueprint.png', device='cuda')
if not semantic_output:
    print("Semantic segmentation failed")
    exit(1)

print(f"Walls: {(semantic_output.wall_mask > 0).sum()} pixels")

# Stage 2
refined_mask = stage2_wall_mask_refinement(semantic_output)
if refined_mask is None:
    print("Wall refinement failed")
    exit(1)

# Stage 3
wall_graph = stage3_topology_extraction(refined_mask)
if wall_graph is None:
    print("Topology extraction failed")
    exit(1)

print(f"Vertices: {len(wall_graph.vertices)}, Edges: {len(wall_graph.edges)}")

# Stage 4
rooms = stage4_room_detection(refined_mask, wall_graph)
if rooms is None:
    print("Room detection failed - rooms may have merged")
    exit(1)

print(f"Rooms detected: {len(rooms.rooms)}")
```

---

## INTERPRETING RESULTS

### SemanticMaskOutput (Stage 1)

```python
semantic_output.wall_mask        # (H, W) binary mask of walls
semantic_output.door_mask        # (H, W) binary mask of doors
semantic_output.window_mask      # (H, W) binary mask of windows
semantic_output.background_mask  # (H, W) binary mask of background

semantic_output.is_valid         # bool: passes validation
semantic_output.validation_msg   # str: validation message
```

### WallTopologyGraph (Stage 3)

```python
graph.vertices        # dict[id] -> WallVertex
# Each vertex has:
#   - position: (x, y) in pixels
#   - is_junction: bool (3+ connections)
#   - is_corner: bool (2 connections at ~90°)
#   - degree: int (number of connections)

graph.edges           # dict[id] -> WallEdge
# Each edge has:
#   - vertex_a, vertex_b: connected vertices
#   - length_px: length in pixels
#   - points: list of (x, y) coordinates along edge

graph.is_connected    # bool: graph is topologically connected
```

### RoomSet (Stage 4)

```python
rooms.rooms           # dict[id] -> Room
# Each room has:
#   - pixels: set of (x, y) coordinates
#   - centroid: (x, y) center
#   - area_px: area in pixels
#   - perimeter_px: perimeter in pixels
#   - bounds: (x_min, y_min, x_max, y_max)

rooms.room_mask       # (H, W) labeled mask (room_id per pixel)
rooms.validation_errors  # list[str]: any validation issues
```

---

## DEBUGGING COMMON ISSUES

### Issue: "Semantic segmentation failed"

**Cause**: Model loading error or image format issue

**Solutions**:
1. Check image exists and is readable
   ```python
   from PIL import Image
   img = Image.open('blueprint.png')
   print(img.size)  # Should print dimensions
   ```

2. Verify image is RGB (not RGBA)
   ```python
   if img.mode != 'RGB':
       img = img.convert('RGB')
       img.save('blueprint_rgb.png')
   ```

3. Check CUDA if using GPU
   ```python
   import torch
   print(torch.cuda.is_available())
   print(torch.cuda.get_device_name(0))
   ```

### Issue: "Rooms merged - architectural error"

**Cause**: Blueprint has ambiguous walls or merged rooms

**Solutions**:
1. Check source image for clarity
2. Verify walls are distinct from room boundaries
3. Increase wall refinement sensitivity (not yet implemented)

### Issue: "Room detection failed"

**Cause**: Walls not properly separated or isolated rooms too small

**Solutions**:
1. Check refined wall mask visually
2. Verify walls form closed loops
3. Check for small regions (<20px) to remove

### Issue: "Topology extraction failed"

**Cause**: Wall mask is disconnected or too fragmented

**Solutions**:
1. Check wall refinement output
2. Verify morphological closing filled gaps
3. Increase wall connectivity in refinement

---

## VISUALIZING OUTPUTS

### Semantic Masks

```python
import cv2
import numpy as np

# Visualize semantic output
wall_display = (semantic_output.wall_mask * 255).astype(np.uint8)
door_display = (semantic_output.door_mask * 255).astype(np.uint8)

cv2.imwrite('wall_mask.png', wall_display)
cv2.imwrite('door_mask.png', door_display)
```

### Wall Topology Graph

```python
import cv2
import numpy as np

# Create visualization
canvas = np.zeros((h, w, 3), dtype=np.uint8)

# Draw edges
for edge in graph.edges.values():
    for i in range(len(edge.points) - 1):
        p1 = tuple(map(int, edge.points[i]))
        p2 = tuple(map(int, edge.points[i + 1]))
        cv2.line(canvas, p1, p2, (0, 255, 0), 2)

# Draw vertices
for vertex in graph.vertices.values():
    pos = tuple(map(int, vertex.position))
    color = (0, 0, 255) if vertex.is_junction else (255, 0, 0)
    cv2.circle(canvas, pos, 5, color, -1)

cv2.imwrite('topology.png', canvas)
```

### Room Detection

```python
import cv2
import numpy as np
from matplotlib import cm

# Create labeled visualization
canvas = np.zeros((h, w, 3), dtype=np.uint8)
colormap = cm.get_cmap('tab20')

for room_id, room in rooms.rooms.items():
    color = tuple(int(x * 255) for x in colormap(room_id)[:3])
    mask = rooms.room_mask == room_id
    canvas[mask] = color

cv2.imwrite('rooms.png', canvas)
```

---

## VALIDATION CHECKS

### Stage 1 Validation
```python
if not semantic_output.is_valid:
    print(semantic_output.validation_msg)
    # Example: "Wall detection is 12.5% (expected 1-95%)"
```

### Stage 3 Validation
```python
if not graph.is_connected:
    print("ERROR: Wall topology is disconnected")
    print("This indicates broken wall segments")
```

### Stage 4 Validation
```python
if rooms.validation_errors:
    for error in rooms.validation_errors:
        print(f"Room validation error: {error}")
```

---

## PERFORMANCE MONITORING

### Stage Timing

```python
import time

# Stage 1
t1 = time.time()
semantic_output = stage1_semantic_segmentation('blueprint.png', device='cuda')
print(f"Stage 1: {time.time() - t1:.2f}s")

# Stage 2
t2 = time.time()
refined_mask = stage2_wall_mask_refinement(semantic_output)
print(f"Stage 2: {time.time() - t2:.2f}s")

# Continue for stages 3-4...
```

### Expected Times
- **Stage 1**: 2-5s (GPU dependent)
- **Stage 2**: <1s
- **Stage 3**: 1-3s
- **Stage 4**: <1s
- **Total**: 4-10s

---

## NEXT STEPS

### Once Stages 1-4 Work

1. **Implement Stage 5** (Metric Normalization)
   - Convert pixel coords to meters
   - Target: 12.0m width
   - ETA: 30 min

2. **Implement Stage 6** (3D Construction)
   - Generate Blender geometry
   - Requires Blender Python API
   - ETA: 2 hours

3. **Stages 7-9** (Openings, Validation, Export)
   - Implement sequentially
   - Total ETA: 1.5 hours

4. **Flask Integration**
   - Create `/api/v2/blueprint/*` endpoints
   - Connect pipeline to web UI
   - ETA: 1 hour

---

## TROUBLESHOOTING

### Memory Issues

If running out of VRAM:

```python
# Use CPU instead
pipeline = BlueprintPipeline(image_path, device='cpu')

# Or reduce image size
from PIL import Image
img = Image.open('blueprint.png')
img.thumbnail((2048, 2048))  # Resize if larger
img.save('blueprint_small.png')
```

### Import Errors

If modules not found:

```bash
# Add pipeline to path
import sys
sys.path.insert(0, 'c:/Users/Avani/Desktop/Skematix')

from pipeline.orchestrator import BlueprintPipeline
```

### Model Download Issues

If DeepLabV3+ model won't download:

```python
# Download manually:
import torch
import torchvision
torchvision.models.segmentation.deeplabv3_resnet50(
    pretrained=True
)
# This will cache the model locally
```

---

## GETTING HELP

### Check Logs

```python
# Access execution log
pipeline = BlueprintPipeline(...)
success, message = pipeline.run_full_pipeline()
print('\n'.join(pipeline.execution_log))
```

### Access Error Details

```python
if not success:
    for error in pipeline.errors:
        print(f"Error: {error}")
```

### Enable Verbose Mode

```python
pipeline = BlueprintPipeline(
    image_path,
    device='cuda',
    verbose=True  # Prints detailed logging
)
```

---

## EXAMPLE: Complete Workflow

```python
#!/usr/bin/env python3
"""Example: Process blueprint from start to finish"""

from pipeline.orchestrator import BlueprintPipeline
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python process_blueprint.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Create pipeline
    print(f"Processing: {image_path}")
    pipeline = BlueprintPipeline(
        image_path=image_path,
        device='cuda',  # Auto-detect GPU
        verbose=True
    )
    
    # Run pipeline
    success, message = pipeline.run_full_pipeline()
    
    # Print results
    print("\n" + "="*50)
    if success:
        print("✓ Pipeline completed successfully!")
        summary = pipeline.get_summary()
        print(f"  Stages completed: {summary['stages_completed']}")
        print(f"  Rooms detected: {summary['rooms_detected']}")
        if summary['output_path']:
            print(f"  Output: {summary['output_path']}")
    else:
        print(f"✗ Pipeline failed: {message}")
        for error in pipeline.errors:
            print(f"  - {error}")
        sys.exit(1)
    
    print("="*50)

if __name__ == '__main__':
    main()
```

**Usage**:
```bash
python process_blueprint.py input/sample_blueprint.png
```

---

## SUCCESS INDICATORS

✅ **Pipeline working correctly if**:
- Semantic segmentation detects 5-80% walls
- Wall refinement preserves continuity
- Topology graph has >5 vertices
- Room detection finds 1+ rooms
- No errors in execution log

❌ **Something wrong if**:
- Semantic masks all zeros or all ones
- Wall graph disconnected
- Rooms reported as merged
- CUDA out of memory errors

---

**Ready to process blueprints!**

For detailed documentation, see:
- `ARCHITECTURE_SEMANTIC_PIPELINE.md` - System design
- `IMPLEMENTATION_CHECKLIST.md` - Implementation details
- `STATUS_REPORT.md` - Project status

---
