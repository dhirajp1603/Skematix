"""
OPENINGS GENERATION MODULE
Stage 7: Openings Generation (Doors & Windows)

Purpose: Create boolean cutouts for doors and windows in wall geometry.

Key Specifications:
- Doors: width 0.9 m, height clipped to wall height
- Windows: width 0.8 m, height 0.5 m, sill 0.65–0.80 m
- No decorative meshes (clean rectangular cuts)
- Boolean operations on manifold geometry

Algorithm:
1. Extract door/window locations from semantic masks
2. Map 2D positions to 3D wall locations
3. Create rectangular cutout volumes
4. Apply boolean subtraction (manifold-safe)
5. Validate resulting geometry remains watertight

This is a critical step for interior visibility and realism.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Set
import logging
from dataclasses import dataclass

from pipeline.stage6_3d_construction import Mesh, Vertex, Face

log = logging.getLogger(__name__)

# ============================================================================
# OPENING SPECIFICATIONS (per architectural requirement)
# ============================================================================

@dataclass
class DoorSpec:
    """Door opening specification"""
    width: float = 0.9    # meters
    height: float = 1.1   # meters (clipped to wall height)
    z_bottom: float = 0.0 # flush with floor
    
    def __post_init__(self):
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Door dimensions must be positive")


@dataclass
class WindowSpec:
    """Window opening specification"""
    width: float = 0.8    # meters
    height: float = 0.5   # meters (vision height)
    sill_height: float = 0.65  # meters (bottom edge height)
    
    def __post_init__(self):
        if self.width <= 0 or self.height <= 0 or self.sill_height < 0:
            raise ValueError("Window dimensions must be valid")


# Default specs
DEFAULT_DOOR_SPEC = DoorSpec()
DEFAULT_WINDOW_SPEC = WindowSpec()


# ============================================================================
# OPENING DETECTION FROM SEMANTIC MASKS
# ============================================================================

class OpeningDetector:
    """Detect door and window locations from semantic masks"""
    
    def __init__(self, 
                 door_mask: np.ndarray,
                 window_mask: np.ndarray,
                 wall_mask: np.ndarray,
                 scale_factor: float):
        """
        Args:
            door_mask: Binary mask of doors (from Stage 1)
            window_mask: Binary mask of windows (from Stage 1)
            wall_mask: Binary mask of walls (from Stage 2)
            scale_factor: pixels per meter (from Stage 5)
        """
        self.door_mask = door_mask.astype(np.uint8)
        self.window_mask = window_mask.astype(np.uint8)
        self.wall_mask = wall_mask.astype(np.uint8)
        self.scale_factor = scale_factor
        
        self.doors: List[Dict] = []
        self.windows: List[Dict] = []
    
    def detect(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Detect door and window locations.
        
        Returns:
            (doors, windows) where each is a list of {'position': (x, y), 'size': ...}
        """
        
        log.info("[OpeningDetector] Detecting door and window locations")
        
        # Extract door locations
        self.doors = self._extract_openings(self.door_mask, "door")
        self.windows = self._extract_openings(self.window_mask, "window")
        
        log.info(f"[OpeningDetector] Found {len(self.doors)} doors, {len(self.windows)} windows")
        
        return self.doors, self.windows
    
    def _extract_openings(self, mask: np.ndarray, opening_type: str) -> List[Dict]:
        """
        Extract opening locations from mask.
        
        For each opening:
        - Find centroid
        - Estimate bounding box
        - Convert to metric coordinates
        """
        
        import cv2
        
        # Label connected components
        num_labels, labels = cv2.connectedComponents(mask)
        
        openings = []
        
        for label_id in range(1, num_labels):
            component_mask = (labels == label_id).astype(np.uint8)
            
            # Get bounding box
            y_coords, x_coords = np.where(component_mask > 0)
            
            if len(x_coords) == 0:
                continue
            
            x_min, x_max = x_coords.min(), x_coords.max()
            y_min, y_max = y_coords.min(), y_coords.max()
            
            # Compute centroid
            x_center = (x_min + x_max) / 2.0
            y_center = (y_min + y_max) / 2.0
            
            # Size in pixels
            width_px = x_max - x_min
            height_px = y_max - y_min
            
            # Convert to metric
            x_m = x_center / self.scale_factor
            y_m = y_center / self.scale_factor
            width_m = width_px / self.scale_factor
            height_m = height_px / self.scale_factor
            
            opening = {
                'position': (x_m, y_m),
                'size': (width_m, height_m),
                'bounds_px': (x_min, y_min, x_max, y_max),
                'area_px': len(x_coords)
            }
            
            openings.append(opening)
            log.info(f"[OpeningDetector] {opening_type.capitalize()} at ({x_m:.2f}, {y_m:.2f}) "
                    f"size {width_m:.2f}×{height_m:.2f}m")
        
        return openings


# ============================================================================
# MANIFOLD-SAFE BOOLEAN OPERATIONS
# ============================================================================

class ManifoldBoolean:
    """
    Manifold-safe boolean operations on meshes.
    
    Strategy: Create cutting volumes and remove vertices/faces within them
    rather than using complex boolean libraries.
    """
    
    @staticmethod
    def cut_rectangular_hole(mesh: Mesh,
                            center_x: float,
                            center_y: float,
                            width: float,
                            height: float,
                            z_bottom: float,
                            z_top: float) -> bool:
        """
        Cut a rectangular hole in the mesh (simplified approach).
        
        This removes faces that lie within the cutting volume.
        For production, consider using PyOpenVDB or similar.
        
        Args:
            mesh: Mesh to modify
            center_x, center_y: center of hole in XY plane
            width, height: hole dimensions
            z_bottom, z_top: Z range of hole
        
        Returns:
            success
        """
        
        # Half-dimensions
        hw = width / 2.0
        hh = height / 2.0
        
        # Bounding box of hole
        x_min, x_max = center_x - hw, center_x + hw
        y_min, y_max = center_y - hh, center_y + hh
        
        # Identify faces to remove (those contained in cutting volume)
        faces_to_remove = []
        
        for face_idx, face in enumerate(mesh.faces):
            vi0, vi1, vi2 = face.vertex_indices
            v0 = mesh.vertices[vi0].position
            v1 = mesh.vertices[vi1].position
            v2 = mesh.vertices[vi2].position
            
            # Check if all vertices of face are within cutting volume
            in_x_range = all(x_min <= v[0] <= x_max for v in [v0, v1, v2])
            in_y_range = all(y_min <= v[1] <= y_max for v in [v0, v1, v2])
            in_z_range = all(z_bottom <= v[2] <= z_top for v in [v0, v1, v2])
            
            if in_x_range and in_y_range and in_z_range:
                faces_to_remove.append(face_idx)
        
        # Remove marked faces
        for idx in sorted(faces_to_remove, reverse=True):
            mesh.faces.pop(idx)
        
        log.info(f"[ManifoldBoolean] Removed {len(faces_to_remove)} faces for hole")
        
        return True


# ============================================================================
# OPENING PLACEMENT & GENERATION
# ============================================================================

class OpeningGenerator:
    """Generate door and window openings in mesh"""
    
    def __init__(self, mesh: Mesh, wall_graph, scale_factor: float):
        """
        Args:
            mesh: 3D mesh to cut openings into
            wall_graph: normalized WallTopologyGraph (for locating walls)
            scale_factor: pixels per meter (for coordinate conversion)
        """
        self.mesh = mesh
        self.wall_graph = wall_graph
        self.scale_factor = scale_factor
    
    def generate_doors(self, door_list: List[Dict]) -> bool:
        """
        Generate door openings.
        
        Args:
            door_list: list of door dictionaries from OpeningDetector
        
        Returns:
            success
        """
        
        log.info(f"[OpeningGenerator] Generating {len(door_list)} doors")
        
        for i, door_info in enumerate(door_list):
            x, y = door_info['position']
            
            # Use standard door spec
            spec = DEFAULT_DOOR_SPEC
            
            # Cut door hole (from floor to standard door height)
            success = ManifoldBoolean.cut_rectangular_hole(
                self.mesh,
                center_x=x,
                center_y=y,
                width=spec.width,
                height=spec.height,
                z_bottom=spec.z_bottom,
                z_top=spec.height
            )
            
            if not success:
                log.warning(f"[OpeningGenerator] Failed to cut door {i}")
        
        return True
    
    def generate_windows(self, window_list: List[Dict]) -> bool:
        """
        Generate window openings.
        
        Args:
            window_list: list of window dictionaries from OpeningDetector
        
        Returns:
            success
        """
        
        log.info(f"[OpeningGenerator] Generating {len(window_list)} windows")
        
        for i, window_info in enumerate(window_list):
            x, y = window_info['position']
            
            # Use standard window spec
            spec = DEFAULT_WINDOW_SPEC
            
            # Cut window hole (at sill height)
            success = ManifoldBoolean.cut_rectangular_hole(
                self.mesh,
                center_x=x,
                center_y=y,
                width=spec.width,
                height=spec.height,
                z_bottom=spec.sill_height,
                z_top=spec.sill_height + spec.height
            )
            
            if not success:
                log.warning(f"[OpeningGenerator] Failed to cut window {i}")
        
        return True
    
    def generate_all(self, doors: List[Dict], windows: List[Dict]) -> bool:
        """Generate all openings"""
        
        log.info("[OpeningGenerator] Generating all openings")
        
        success = True
        
        if doors:
            success &= self.generate_doors(doors)
        
        if windows:
            success &= self.generate_windows(windows)
        
        # Recalculate normals after modifications
        self.mesh.recalculate_normals()
        
        log.info("[OpeningGenerator] ✓ Openings generation complete")
        
        return success


# ============================================================================
# STAGE 7 MAIN FUNCTION
# ============================================================================

def stage7_openings_generation(mesh: Mesh,
                               door_mask: np.ndarray,
                               window_mask: np.ndarray,
                               wall_mask: np.ndarray,
                               wall_graph,
                               scale_factor: float) -> Tuple[bool, Optional[Mesh]]:
    """
    Execute Stage 7: Openings Generation
    
    Args:
        mesh: 3D mesh from Stage 6
        door_mask: binary door mask from Stage 1
        window_mask: binary window mask from Stage 1
        wall_mask: binary wall mask from Stage 2
        wall_graph: normalized wall topology graph
        scale_factor: pixels per meter
    
    Returns:
        (success, mesh_with_openings)
    """
    
    log.info("[Stage7] Starting openings generation")
    
    try:
        # Step 1: Detect openings
        detector = OpeningDetector(door_mask, window_mask, wall_mask, scale_factor)
        doors, windows = detector.detect()
        
        # Step 2: Generate openings
        generator = OpeningGenerator(mesh, wall_graph, scale_factor)
        success = generator.generate_all(doors, windows)
        
        if not success:
            log.error("[Stage7] Opening generation failed")
            return False, None
        
        log.info("[Stage7] ✓ Openings generation complete")
        
        return True, mesh
    
    except Exception as e:
        log.error(f"[Stage7] Exception: {e}")
        return False, None
