"""
METRIC NORMALIZATION MODULE
Stage 5: Metric Normalization

Purpose: Normalize geometry scale from image coordinates to real-world meters.

Key Principle: Convert abstract pixel/unit coordinates into metric space.
Ensure realistic residential dimensions (total plan width ≈ 10–15 m).

Algorithm:
1. Measure reference dimension from image (usually building width)
2. Define reference width target (12 m for residential)
3. Compute scale factor: REFERENCE_WIDTH ÷ detected_width
4. Apply scale transform to all geometry
5. Verify normalized dimensions are realistic

This step ensures spatial correctness for all subsequent 3D geometry.
"""

import numpy as np
from typing import Tuple, Dict, Optional
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)

# ============================================================================
# NORMALIZATION CONSTANTS
# ============================================================================

# REFERENCE DIMENSIONS (per architectural specification)
REFERENCE_BUILDING_WIDTH = 12.0  # meters (standard residential)
REFERENCE_WIDTH_MIN = 10.5       # acceptable minimum
REFERENCE_WIDTH_MAX = 13.5       # acceptable maximum

# Tolerance for aspect ratio
ASPECT_RATIO_MIN = 0.4
ASPECT_RATIO_MAX = 2.5


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class NormalizationContext:
    """Context for metric normalization"""
    image_width_px: int           # Original image width in pixels
    image_height_px: int          # Original image height in pixels
    detected_width_px: int        # Detected building width in pixels
    detected_height_px: int       # Detected building height in pixels
    scale_factor: float           # Pixels per meter
    target_width_m: float = REFERENCE_BUILDING_WIDTH  # Target width in meters
    
    @property
    def image_aspect_ratio(self) -> float:
        """Image aspect ratio (width / height)"""
        return self.image_width_px / self.image_height_px if self.image_height_px > 0 else 1.0


# ============================================================================
# METRIC NORMALIZATION
# ============================================================================

class MetricNormalizer:
    """
    Normalize wall graph and room geometry to metric space.
    
    Transforms all coordinates from image pixels to real-world meters.
    """
    
    def __init__(self, 
                 image_shape: Tuple[int, int],
                 wall_graph,
                 room_set):
        """
        Args:
            image_shape: (height, width) of blueprint image
            wall_graph: WallTopologyGraph from Stage 3
            room_set: RoomSet from Stage 4
        """
        self.image_height, self.image_width = image_shape
        self.wall_graph = wall_graph
        self.room_set = room_set
        
        self.context: Optional[NormalizationContext] = None
        self.normalized_wall_graph = None
        self.normalized_room_set = None
    
    def normalize(self) -> Tuple[bool, Dict, object, object]:
        """
        Execute metric normalization.
        
        Returns:
            (success, context_dict, normalized_wall_graph, normalized_room_set)
        """
        
        log.info("[MetricNorm] Starting metric normalization")
        
        if not self.wall_graph or not self.room_set:
            log.error("[MetricNorm] Missing wall_graph or room_set")
            return False, {}, None, None
        
        # Step 1: Detect building width from wall graph
        detected_width_px = self._estimate_building_width()
        detected_height_px = self._estimate_building_height()
        
        log.info(f"[MetricNorm] Detected building: {detected_width_px}×{detected_height_px} px")
        
        if detected_width_px <= 0 or detected_height_px <= 0:
            log.error("[MetricNorm] Failed to detect building dimensions")
            return False, {}, None, None
        
        # Step 2: Create normalization context
        self.context = NormalizationContext(
            image_width_px=self.image_width,
            image_height_px=self.image_height,
            detected_width_px=detected_width_px,
            detected_height_px=detected_height_px,
            scale_factor=detected_width_px / REFERENCE_BUILDING_WIDTH,
            target_width_m=REFERENCE_BUILDING_WIDTH
        )
        
        # Step 3: Validate context
        valid, msg = self._validate_context()
        if not valid:
            log.error(f"[MetricNorm] Validation failed: {msg}")
            return False, {}, None, None
        
        log.info(f"[MetricNorm] Scale factor: {self.context.scale_factor:.2f} px/m")
        log.info(f"[MetricNorm] Normalized width: {self.context.target_width_m:.2f} m")
        
        # Step 4: Transform wall graph
        self.normalized_wall_graph = self._transform_wall_graph()
        
        # Step 5: Transform room set
        self.normalized_room_set = self._transform_room_set()
        
        log.info("[MetricNorm] ✓ Metric normalization complete")
        
        return True, self._context_to_dict(), self.normalized_wall_graph, self.normalized_room_set
    
    def _estimate_building_width(self) -> int:
        """
        Estimate building width from wall graph bounding box.
        
        Returns:
            width in pixels
        """
        
        if not self.wall_graph or not self.wall_graph.vertices:
            log.warning("[MetricNorm] No wall vertices to estimate width")
            return self.image_width
        
        xs = [v.position[0] for v in self.wall_graph.vertices.values()]
        ys = [v.position[1] for v in self.wall_graph.vertices.values()]
        
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        
        width = x_max - x_min
        height = y_max - y_min
        
        # Use maximum dimension (assuming building is roughly square)
        return max(width, height)
    
    def _estimate_building_height(self) -> int:
        """
        Estimate building height from wall graph.
        
        Returns:
            height in pixels
        """
        
        if not self.wall_graph or not self.wall_graph.vertices:
            return self.image_height
        
        ys = [v.position[1] for v in self.wall_graph.vertices.values()]
        return max(ys) - min(ys) if ys else self.image_height
    
    def _validate_context(self) -> Tuple[bool, str]:
        """
        Validate normalization context.
        
        Returns:
            (is_valid, message)
        """
        
        if not self.context:
            return False, "Context not created"
        
        # Check scale factor is reasonable (building shouldn't be < 1m or > 100m)
        if self.context.scale_factor < 0.1 or self.context.scale_factor > 100:
            return False, f"Scale factor out of range: {self.context.scale_factor:.2f}"
        
        # Check normalized width is reasonable
        normalized_width = self.image_width / self.context.scale_factor
        if normalized_width < REFERENCE_WIDTH_MIN or normalized_width > REFERENCE_WIDTH_MAX:
            log.warning(f"[MetricNorm] Normalized width {normalized_width:.2f}m is outside typical range")
            # Still continue, just warn
        
        # Check aspect ratio is reasonable
        aspect = self.context.image_aspect_ratio
        if aspect < ASPECT_RATIO_MIN or aspect > ASPECT_RATIO_MAX:
            log.warning(f"[MetricNorm] Image aspect ratio {aspect:.2f} is unusual")
        
        return True, "Context valid"
    
    def _transform_wall_graph(self):
        """
        Transform wall graph vertices to metric coordinates.
        
        Returns:
            transformed_wall_graph (same structure, different coordinates)
        """
        
        log.info("[MetricNorm] Transforming wall graph to metric space")
        
        # Create new graph (reuse structure)
        from pipeline.stage3_topology_extraction import WallTopologyGraph
        
        new_graph = WallTopologyGraph()
        
        # Transform vertices
        vertex_mapping = {}  # old_vertex_id -> new_vertex
        
        for old_id, old_vertex in self.wall_graph.vertices.items():
            # Convert from pixels to meters
            x_m = old_vertex.position[0] / self.context.scale_factor
            y_m = old_vertex.position[1] / self.context.scale_factor
            
            new_vertex = new_graph.add_vertex(
                position=(x_m, y_m),
                is_junction=old_vertex.is_junction,
                is_corner=old_vertex.is_corner
            )
            vertex_mapping[old_id] = new_vertex
        
        # Transform edges
        for old_edge in self.wall_graph.edges.values():
            new_va = vertex_mapping[old_edge.vertex_a.id]
            new_vb = vertex_mapping[old_edge.vertex_b.id]
            
            # Scale length
            new_length_m = old_edge.length_px / self.context.scale_factor
            
            # Transform points
            new_points = [
                (p[0] / self.context.scale_factor, p[1] / self.context.scale_factor)
                for p in old_edge.points
            ]
            
            new_graph.add_edge(new_va, new_vb, new_length_m, new_points)
        
        log.info(f"[MetricNorm] Transformed {len(new_graph.vertices)} vertices, "
                 f"{len(new_graph.edges)} edges")
        
        return new_graph
    
    def _transform_room_set(self):
        """
        Transform room set to metric space.
        
        Returns:
            transformed_room_set
        """
        
        log.info("[MetricNorm] Transforming room set to metric space")
        
        from pipeline.stage4_room_detection import RoomSet
        
        new_room_set = RoomSet((self.room_set.height, self.room_set.width))
        
        # Transform each room
        for old_room in self.room_set.rooms.values():
            # Transform pixel set to metric coordinates
            new_pixels = set()
            for x_px, y_px in old_room.pixels:
                x_m = x_px / self.context.scale_factor
                y_m = y_px / self.context.scale_factor
                new_pixels.add((x_m, y_m))
            
            # Create new room with transformed pixels
            new_room = new_room_set.add_room(new_pixels)
            
            # Update derived properties
            xs = [p[0] for p in new_pixels]
            ys = [p[1] for p in new_pixels]
            new_room.centroid = (np.mean(xs), np.mean(ys))
            new_room.bounds = (min(xs), min(ys), max(xs), max(ys))
            new_room.area_px = len(new_pixels)  # Now in m² approximately
        
        log.info(f"[MetricNorm] Transformed {len(new_room_set.rooms)} rooms")
        
        return new_room_set
    
    def _context_to_dict(self) -> Dict:
        """Convert context to dict for serialization"""
        
        if not self.context:
            return {}
        
        return {
            'image_width_px': self.context.image_width_px,
            'image_height_px': self.context.image_height_px,
            'detected_width_px': self.context.detected_width_px,
            'detected_height_px': self.context.detected_height_px,
            'scale_factor': self.context.scale_factor,
            'target_width_m': self.context.target_width_m,
            'normalized_image_aspect': self.context.image_aspect_ratio
        }
    
    def get_context(self) -> Optional[NormalizationContext]:
        """Get normalization context"""
        return self.context


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def scale_coordinate(pixel_coord: Tuple[float, float], 
                    scale_factor: float) -> Tuple[float, float]:
    """Convert pixel coordinate to metric coordinate"""
    return (pixel_coord[0] / scale_factor, pixel_coord[1] / scale_factor)


def scale_length(pixel_length: float, scale_factor: float) -> float:
    """Convert pixel length to metric length"""
    return pixel_length / scale_factor
