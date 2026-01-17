# IMPLEMENTATION CHECKLIST & NEXT STEPS

## CURRENT STATE SUMMARY

✅ **COMPLETED (5 modules + 2 docs)**:
- `pipeline/stage1_semantic_segmentation.py` (540 lines)
- `pipeline/stage2_wall_refinement.py` (420 lines)
- `pipeline/stage3_topology_extraction.py` (600 lines)
- `pipeline/stage4_room_detection.py` (480 lines)
- `pipeline/orchestrator.py` (450 lines)
- `ARCHITECTURE_SEMANTIC_PIPELINE.md` (complete architecture design)
- `FLASK_INTEGRATION.md` (web integration plan)

⏳ **NEXT PRIORITY: Stage 5 (Metric Normalization)**

---

## STAGE 5: METRIC NORMALIZATION

**File**: `pipeline/stage5_metric_normalization.py`  
**Purpose**: Convert pixel coordinates to real-world meters  
**Input**: WallTopologyGraph, RoomSet (in pixel units)  
**Output**: Normalized geometry (1 unit = 1 meter)

### Implementation Outline

```python
# pipeline/stage5_metric_normalization.py

class MetricNormalizer:
    """Convert pixel coordinates to metric (meter) scale"""
    
    def __init__(self, target_width_meters=12.0):
        """
        Args:
            target_width_meters: Desired width in real-world meters
                Default 12m is typical floor plan width
        """
        self.target_width_meters = target_width_meters
    
    def normalize(self, wall_graph, room_set):
        """
        Normalize all geometry to metric scale
        
        Returns:
            normalized_geometry dict with:
                - scaled_vertices: {id: (x, y) in meters}
                - scaled_edges: {id: updated WallEdge}
                - scaled_rooms: {id: updated Room with metric centroid}
                - scale_factor: pixels_per_meter
        """
        # 1. Compute bounding box of all vertices
        min_x, max_x, min_y, max_y = self._compute_bounds(wall_graph)
        pixel_width = max_x - min_x
        
        # 2. Compute scale: pixels per meter
        # If floor is 100px wide and should be 12m, scale = 100/12
        scale_factor = pixel_width / self.target_width_meters
        
        # 3. Apply scale to all vertices
        scaled_vertices = {}
        for v_id, vertex in wall_graph.vertices.items():
            meter_x = vertex.position[0] / scale_factor
            meter_y = vertex.position[1] / scale_factor
            scaled_vertices[v_id] = (meter_x, meter_y)
        
        # 4. Apply scale to edges (preserve topology)
        scaled_edges = {}
        for e_id, edge in wall_graph.edges.items():
            # Update length in meters
            edge.length_meters = edge.length_px / scale_factor
            scaled_edges[e_id] = edge
        
        # 5. Apply scale to room centroids
        scaled_rooms = {}
        for room_id, room in room_set.rooms.items():
            # Update centroid
            room.centroid_meters = (
                room.centroid[0] / scale_factor,
                room.centroid[1] / scale_factor
            )
            # Update area in square meters
            room.area_sq_meters = (room.area_px / (scale_factor ** 2))
            scaled_rooms[room_id] = room
        
        return {
            'scaled_vertices': scaled_vertices,
            'scaled_edges': scaled_edges,
            'scaled_rooms': scaled_rooms,
            'scale_factor': scale_factor,  # pixels per meter
            'real_world_width_m': self.target_width_meters,
            'real_world_height_m': self._compute_height(wall_graph, scale_factor)
        }
    
    def _compute_bounds(self, wall_graph):
        """Get bounding box of all wall vertices"""
        vertices = list(wall_graph.vertices.values())
        if not vertices:
            return 0, 0, 0, 0
        
        x_coords = [v.position[0] for v in vertices]
        y_coords = [v.position[1] for v in vertices]
        
        return min(x_coords), max(x_coords), min(y_coords), max(y_coords)
    
    def _compute_height(self, wall_graph, scale_factor):
        """Compute real-world height in meters"""
        _, _, min_y, max_y = self._compute_bounds(wall_graph)
        pixel_height = max_y - min_y
        return pixel_height / scale_factor


def stage5_metric_normalization(wall_graph, room_set, target_width_m=12.0):
    """
    Main interface for metric normalization
    
    Args:
        wall_graph: WallTopologyGraph from stage 3
        room_set: RoomSet from stage 4
        target_width_m: Target real-world width (default 12.0m)
    
    Returns:
        dict with normalized geometry or None if failed
    """
    try:
        normalizer = MetricNormalizer(target_width_m)
        result = normalizer.normalize(wall_graph, room_set)
        return result
    except Exception as e:
        logger.error(f"Metric normalization failed: {e}")
        return None
```

### Integration into Orchestrator

In `orchestrator.py`, update `_stage5_metric_normalization()`:

```python
def _stage5_metric_normalization(self):
    """Stage 5: Convert to metric scale"""
    try:
        self.normalized_geometry = stage5_metric_normalization(
            self.wall_graph,
            self.room_set,
            target_width_m=12.0
        )
        
        if not self.normalized_geometry:
            self.errors.append("Metric normalization failed")
            return False
        
        self.execution_log.append(
            f"✓ Stage 5 complete: {len(self.normalized_geometry['scaled_vertices'])} vertices normalized"
        )
        return True
    except Exception as e:
        self.errors.append(f"Stage 5 exception: {e}")
        return False
```

---

## STAGE 6: 3D CUTAWAY CONSTRUCTION

**File**: `pipeline/stage6_3d_construction.py`  
**Purpose**: Generate Blender geometry from wall graph  
**Input**: Normalized geometry (metric scale)  
**Output**: Blender model with walls and floor

### Key Specifications

- **Wall thickness**: 0.22m
- **Wall height**: 1.3m (open-top)
- **Floor thickness**: 0.12m at Z=0
- **No roof**: Never
- **Geometry**: Manifold, watertight

### Implementation Strategy

```python
import bpy
from mathutils import Vector, Matrix

class BlenderCutawayBuilder:
    """Generate 3D Blender model from wall topology"""
    
    def __init__(self, wall_thickness=0.22, wall_height=1.3, floor_thickness=0.12):
        self.wall_thickness = wall_thickness
        self.wall_height = wall_height
        self.floor_thickness = floor_thickness
    
    def build_3d_model(self, normalized_geometry):
        """
        Build complete 3D model
        
        Returns:
            bpy.types.Object - main collection with all geometry
        """
        # Clear default cube
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        # Create collection
        collection = bpy.data.collections.new("Blueprint_Cutaway")
        bpy.context.scene.collection.children.link(collection)
        
        # 1. Build floor
        floor = self._build_floor(normalized_geometry, collection)
        
        # 2. Build walls
        walls = self._build_walls(normalized_geometry, collection)
        
        # 3. Create parent collection
        parent = bpy.data.objects.new("Cutaway_Model", None)
        collection.objects.link(parent)
        
        return parent
    
    def _build_floor(self, normalized_geometry, collection):
        """Create floor from room boundaries"""
        rooms = normalized_geometry['scaled_rooms']
        
        # Merge all room polygons
        floor_vertices = []
        floor_faces = []
        
        for room in rooms.values():
            # Use room bounds for now (TODO: use room outline)
            x_min, y_min = room.bounds[0], room.bounds[1]
            x_max, y_max = room.bounds[2], room.bounds[3]
            
            # Create floor quad
            # TODO: Implement proper room polygon extraction
        
        return floor
    
    def _build_walls(self, normalized_geometry, collection):
        """Create walls from wall graph"""
        vertices = normalized_geometry['scaled_vertices']
        edges = normalized_geometry['scaled_edges']
        
        wall_meshes = []
        
        for edge_id, edge in edges.items():
            # Get edge endpoints
            v_a = vertices[edge.vertex_a]
            v_b = vertices[edge.vertex_b]
            
            # Create wall geometry
            # TODO: Extrude edge into 3D wall
            wall = self._create_wall_segment(
                v_a, v_b,
                thickness=self.wall_thickness,
                height=self.wall_height
            )
            
            collection.objects.link(wall)
            wall_meshes.append(wall)
        
        return wall_meshes
    
    def _create_wall_segment(self, p1, p2, thickness, height):
        """Create single wall segment as 3D box"""
        # TODO: Implement wall extrusion
        pass
```

---

## STAGE 7: OPENINGS GENERATION

**File**: `pipeline/stage7_openings_generation.py`  
**Purpose**: Cut door and window openings into walls

### Implementation Strategy

```python
import bpy

class OpeningsGenerator:
    """Generate door and window openings using boolean operations"""
    
    def __init__(self, door_width=0.9, door_height=1.1,
                 window_width=0.8, window_height=0.5, window_sill=0.65):
        self.door_width = door_width
        self.door_height = door_height
        self.window_width = window_width
        self.window_height = window_height
        self.window_sill = window_sill
    
    def cut_openings(self, blender_model, semantic_output, normalized_geometry):
        """
        Cut doors and windows into walls
        
        Args:
            blender_model: Blender collection with walls
            semantic_output: SemanticMaskOutput with door/window masks
            normalized_geometry: Normalized metric geometry
        
        Returns:
            Modified blender_model with openings
        """
        # 1. Get door positions from semantic mask
        doors = self._detect_doors(semantic_output, normalized_geometry)
        
        # 2. Get window positions from semantic mask
        windows = self._detect_windows(semantic_output, normalized_geometry)
        
        # 3. Create boolean cutout objects
        for door in doors:
            door_box = self._create_door_cutout(door)
            self._apply_boolean_operation(blender_model, door_box, 'DIFFERENCE')
        
        for window in windows:
            window_box = self._create_window_cutout(window)
            self._apply_boolean_operation(blender_model, window_box, 'DIFFERENCE')
        
        return blender_model
    
    def _detect_doors(self, semantic_output, normalized_geometry):
        """Find door positions and sizes"""
        # TODO: Map semantic door pixels to wall positions
        pass
    
    def _detect_windows(self, semantic_output, normalized_geometry):
        """Find window positions and sizes"""
        # TODO: Map semantic window pixels to wall positions
        pass
    
    def _create_door_cutout(self, door_info):
        """Create boolean shape for door"""
        # TODO: Create 0.9m × 1.1m box
        pass
    
    def _create_window_cutout(self, window_info):
        """Create boolean shape for window"""
        # TODO: Create 0.8m × 0.5m box at sill height
        pass
    
    def _apply_boolean_operation(self, model, cutter, operation='DIFFERENCE'):
        """Apply boolean operation to model"""
        # TODO: Use Blender boolean modifier
        pass
```

---

## STAGE 8: VALIDATION

**File**: `pipeline/stage8_validation.py`  
**Purpose**: Programmatic validation before export

### Validation Checklist

```python
class GeometryValidator:
    """Validate complete 3D model"""
    
    def validate(self, blender_model):
        """
        Run all validation checks
        
        Returns:
            (is_valid: bool, report: list[str])
        """
        report = []
        is_valid = True
        
        # 1. Check wall count
        wall_count = len([obj for obj in blender_model.children if 'wall' in obj.name])
        if wall_count < 1:
            report.append("ERROR: No walls found")
            is_valid = False
        else:
            report.append(f"✓ Wall count: {wall_count}")
        
        # 2. Check room count (must have at least 1)
        room_objects = [obj for obj in blender_model.children if 'room' in obj.name]
        if len(room_objects) < 1:
            report.append("ERROR: No rooms detected")
            is_valid = False
        else:
            report.append(f"✓ Room count: {len(room_objects)}")
        
        # 3. Check no single enclosure
        # TODO: Verify not all interior space is sealed
        
        # 4. Check manifold geometry
        # TODO: Run Blender manifold check
        
        # 5. Check interior visibility from top
        # TODO: Raycast from above to verify open-top
        
        return is_valid, report
```

---

## STAGE 9: EXPORT

**File**: `pipeline/stage9_export.py`  
**Purpose**: Export to GLB format

### Implementation Strategy

```python
import bpy
import os

def export_to_glb(blender_model, output_path, use_draco=True):
    """
    Export Blender model to GLB format
    
    Args:
        blender_model: Blender collection
        output_path: Output .glb file path
        use_draco: Use Draco compression (reduces size)
    
    Returns:
        output_path if successful, None otherwise
    """
    try:
        # Select model
        bpy.context.view_layer.objects.active = blender_model
        blender_model.select_set(True)
        
        # Export
        bpy.ops.export_scene.gltf(
            filepath=output_path,
            use_draco_mesh_compression=use_draco,
            export_apply=True,
            export_colors=False,
            export_normals=True,
            export_tangents=False,
            export_materials=False,
            export_textures=False
        )
        
        return output_path
    except Exception as e:
        logger.error(f"GLB export failed: {e}")
        return None
```

---

## TESTING PLAN

### Test Images

- **Simple**: 1-room blueprint (just walls)
- **Complex**: 8+ room blueprint with partitions
- **Edge cases**: T-shaped rooms, circular elements, merged rooms (should FAIL)

### Test Scenarios

```python
# tests/test_pipeline.py

def test_semantic_segmentation():
    """Verify stage 1 produces valid semantic masks"""
    pass

def test_wall_refinement():
    """Verify stage 2 preserves wall continuity"""
    pass

def test_topology_extraction():
    """Verify stage 3 creates connected graph"""
    pass

def test_room_detection():
    """Verify stage 4 fails fast on merged rooms"""
    pass

def test_full_pipeline():
    """Test all stages 1-9 end-to-end"""
    pass

def test_glb_export():
    """Verify output GLB is valid"""
    pass
```

---

## RECOMMENDED EXECUTION ORDER

1. ✅ Stages 1-4 + Orchestrator (DONE)
2. ⏳ Stage 5: Metric Normalization (~30 min)
3. ⏳ Stage 6: 3D Construction (~2 hours) - requires Blender API knowledge
4. ⏳ Stage 7: Openings (~1 hour)
5. ⏳ Stage 8: Validation (~30 min)
6. ⏳ Stage 9: Export (~30 min)
7. ⏳ Flask Integration (~1 hour)
8. ⏳ End-to-end Testing (~2 hours)

**Estimated Total Remaining**: 8-10 hours

---

## IMMEDIATE NEXT STEP

**Start Stage 5: Metric Normalization**

This is the lowest-complexity remaining stage and unblocks Stages 6-9.

Implementation should take ~30 minutes:
1. Create `stage5_metric_normalization.py` (150 lines)
2. Update orchestrator to call Stage 5
3. Test with synthetic data

---
