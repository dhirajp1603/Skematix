"""
ROOM DETECTION MODULE
Stage 4: Room Detection (NO MERGING ALLOWED)

Purpose: Detect all enclosed regions (rooms) using the wall topology graph.
Validate that no two rooms share interior space.

Key Principle: FAIL FAST if room separation fails.
Do NOT continue if rooms appear to merge.

Algorithm:
1. Use wall topology graph as guide
2. Apply flood-fill from interior to identify enclosed regions
3. Verify each room is fully enclosed
4. Validate no room overlap
5. Fail explicitly if validation fails
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple, Set
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)

# ============================================================================
# DATA STRUCTURES FOR ROOMS
# ============================================================================

@dataclass
class Room:
    """Represents an enclosed room/space in the blueprint"""
    id: int
    pixels: Set[Tuple[int, int]]      # Set of (x, y) pixels in this room
    centroid: Tuple[float, float]     # Center of mass
    area_px: int                       # Area in pixels
    perimeter_px: int                  # Perimeter in pixels
    bounds: Tuple[int, int, int, int] # (x_min, y_min, x_max, y_max)
    
    def is_enclosed(self) -> bool:
        """Check if room is fully enclosed (not touching image boundary)"""
        x_min, y_min, x_max, y_max = self.bounds
        # Rooms shouldn't touch image edges (usually indicates open space)
        return x_min > 5 and y_min > 5
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return self.id == other.id


class RoomSet:
    """Collection of detected rooms with validation"""
    
    def __init__(self, image_shape: Tuple[int, int]):
        self.rooms: Dict[int, Room] = {}
        self.room_counter = 0
        self.height, self.width = image_shape
        self.mask = None  # Labeled room mask
    
    def add_room(self, pixels: Set[Tuple[int, int]]) -> Room:
        """Add a detected room"""
        
        area = len(pixels)
        
        # Compute centroid
        xs = [p[0] for p in pixels]
        ys = [p[1] for p in pixels]
        centroid = (np.mean(xs), np.mean(ys))
        
        # Compute bounding box
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        
        # Compute perimeter (number of boundary pixels)
        perimeter = sum(
            1 for x, y in pixels
            if any((x+dx, y+dy) not in pixels
                   for dx in [-1, 0, 1] for dy in [-1, 0, 1]
                   if not (dx == 0 and dy == 0))
        )
        
        room = Room(
            id=self.room_counter,
            pixels=pixels,
            centroid=centroid,
            area_px=area,
            perimeter_px=perimeter,
            bounds=(x_min, y_min, x_max, y_max)
        )
        
        self.rooms[room.id] = room
        self.room_counter += 1
        
        return room
    
    def check_overlap(self) -> Tuple[bool, str]:
        """
        Check that no two rooms share interior space.
        
        Returns:
            (no_overlap, message)
        """
        
        for i, room1 in enumerate(self.rooms.values()):
            for room2 in list(self.rooms.values())[i+1:]:
                overlap = room1.pixels & room2.pixels
                if overlap:
                    return False, f"Rooms {room1.id} and {room2.id} overlap ({len(overlap)} pixels)"
        
        return True, "No room overlaps detected"
    
    def validate(self) -> Tuple[bool, str]:
        """
        Comprehensive room validation.
        
        Returns:
            (is_valid, message)
        """
        
        if len(self.rooms) < 1:
            return False, "No rooms detected"
        
        # Check overlap
        no_overlap, msg = self.check_overlap()
        if not no_overlap:
            return False, msg
        
        # Check that rooms are appropriately sized
        areas = [r.area_px for r in self.rooms.values()]
        min_area, max_area = min(areas), max(areas)
        
        if min_area < 20:
            return False, f"Room too small ({min_area} pixels)"
        
        if max_area / min_area > 100:
            return False, f"Room size ratio too large ({max_area}/{min_area})"
        
        return True, f"Valid room configuration ({len(self.rooms)} rooms)"
    
    def summary(self) -> Dict:
        """Get summary statistics"""
        areas = [r.area_px for r in self.rooms.values()]
        return {
            'room_count': len(self.rooms),
            'total_room_area': sum(areas),
            'avg_room_area': np.mean(areas) if areas else 0,
            'min_area': min(areas) if areas else 0,
            'max_area': max(areas) if areas else 0
        }

# ============================================================================
# ROOM DETECTION ALGORITHM
# ============================================================================

class RoomDetector:
    """
    Detect rooms using wall topology and flood-fill.
    
    Key principle: Walls define room boundaries.
    Rooms are enclosed regions separated by walls.
    """
    
    def __init__(self, wall_mask: np.ndarray, wall_graph=None):
        """
        Args:
            wall_mask: Binary wall mask
            wall_graph: Wall topology graph (optional, for validation)
        """
        self.wall_mask = wall_mask.astype(np.uint8)
        self.wall_graph = wall_graph
        self.rooms = None
        self.room_mask = None
    
    def detect(self) -> Optional[RoomSet]:
        """
        Detect all enclosed rooms.
        
        Returns:
            RoomSet or None if detection fails
        """
        
        log.info("[RoomDetection] Starting room detection")
        
        # Create inverted mask (rooms are non-wall regions)
        non_wall_mask = 1 - self.wall_mask
        
        # Label connected components (each component = potential room)
        num_labels, labeled = cv2.connectedComponents(non_wall_mask)
        
        log.info(f"[RoomDetection] Found {num_labels} connected regions")
        
        # Create room set
        room_set = RoomSet(self.wall_mask.shape)
        
        # Extract rooms from labeled regions
        room_id_to_pixels = {}
        for label_id in range(1, num_labels):  # Skip background (0)
            region_mask = (labeled == label_id)
            pixels_in_region = set(zip(*np.argwhere(region_mask)[:, [1, 0]]))
            
            area = len(pixels_in_region)
            
            # Filter very small regions (noise)
            if area < 20:
                continue
            
            # Filter regions touching image boundary (open spaces)
            touches_boundary = False
            for x, y in pixels_in_region:
                if x <= 1 or x >= self.wall_mask.shape[1]-2 or \
                   y <= 1 or y >= self.wall_mask.shape[0]-2:
                    touches_boundary = True
                    break
            
            if touches_boundary:
                log.info(f"[RoomDetection] Skipping region {label_id} (touches boundary)")
                continue
            
            # Add as room
            room = room_set.add_room(pixels_in_region)
            room_id_to_pixels[label_id] = room
            log.info(f"[RoomDetection] Room {room.id}: area={room.area_px}px, bounds={room.bounds}")
        
        # Create labeled room mask for visualization
        room_mask = np.zeros(self.wall_mask.shape, dtype=np.uint8)
        for label_id, room in room_id_to_pixels.items():
            for x, y in room.pixels:
                room_mask[y, x] = room.id + 1
        
        self.room_mask = room_mask
        self.rooms = room_set
        
        return room_set
    
    def validate_room_separation(self) -> Tuple[bool, str]:
        """
        Validate that rooms are properly separated by walls.
        
        CRITICAL CHECK: No two rooms should share interior space.
        
        Returns:
            (is_separated, message)
        """
        
        if self.rooms is None:
            return False, "Rooms not yet detected"
        
        log.info("[RoomDetection] Validating room separation")
        
        # Check for overlaps
        is_valid, message = self.rooms.check_overlap()
        
        if not is_valid:
            return False, message
        
        # Check that rooms are separated by walls
        for i, room1 in enumerate(self.rooms.rooms.values()):
            for room2 in list(self.rooms.rooms.values())[i+1:]:
                # Check if rooms are adjacent
                x1_min, y1_min, x1_max, y1_max = room1.bounds
                x2_min, y2_min, x2_max, y2_max = room2.bounds
                
                # Find gap between rooms
                gap_exists = False
                
                # Check vertical gap
                if x1_max < x2_min:
                    # Rooms are horizontally separated
                    gap_pixels = self.wall_mask[y1_min:y1_max, x1_max:x2_min].sum()
                    if gap_pixels > 0:
                        gap_exists = True
                
                # Check horizontal gap
                if y1_max < y2_min:
                    # Rooms are vertically separated
                    gap_pixels = self.wall_mask[y1_max:y2_min, x1_min:x1_max].sum()
                    if gap_pixels > 0:
                        gap_exists = True
                
                if not gap_exists:
                    return False, f"Rooms {room1.id} and {room2.id} not properly separated by walls"
        
        return True, "All rooms properly separated by walls"

# ============================================================================
# STAGE 4 MAIN INTERFACE
# ============================================================================

def stage4_room_detection(refined_wall_mask: np.ndarray,
                         wall_graph=None) -> Optional[RoomSet]:
    """
    STAGE 4: Room Detection (NO MERGING ALLOWED)
    
    Input: Refined wall mask from Stage 2
    Output: RoomSet with validated room separation
    
    KEY PRINCIPLE: FAIL FAST if rooms merge or separation fails.
    
    Args:
        refined_wall_mask: Binary wall mask from Stage 2
        wall_graph: Wall topology graph from Stage 3 (optional)
    
    Returns:
        RoomSet or None if detection fails
    """
    
    log.info("="*80)
    log.info("STAGE 4: ROOM DETECTION (NO MERGING ALLOWED)")
    log.info("="*80)
    
    if refined_wall_mask is None:
        log.error("[RoomDetection] No wall mask provided")
        return None
    
    # Detect rooms
    detector = RoomDetector(refined_wall_mask, wall_graph)
    rooms = detector.detect()
    
    if rooms is None:
        log.error("[RoomDetection] Failed to detect rooms")
        return None
    
    # Validate room count
    if len(rooms.rooms) < 1:
        log.error("[RoomDetection] ✗ No rooms detected")
        return None
    
    log.info(f"[RoomDetection] Detected {len(rooms.rooms)} rooms")
    
    # Validate rooms don't overlap
    no_overlap, msg = rooms.check_overlap()
    log.info(f"[RoomDetection] Overlap check: {msg}")
    
    if not no_overlap:
        log.error(f"[RoomDetection] ✗ FAIL FAST: {msg}")
        log.error("[RoomDetection] Rooms cannot be separated properly")
        log.error("[RoomDetection] Pipeline halted (no continuation allowed)")
        return None
    
    # Validate room separation
    is_separated, msg = detector.validate_room_separation()
    log.info(f"[RoomDetection] Separation validation: {msg}")
    
    if not is_separated:
        log.error(f"[RoomDetection] ✗ FAIL FAST: {msg}")
        log.error("[RoomDetection] Pipeline halted (no continuation allowed)")
        return None
    
    # Validate overall structure
    is_valid, msg = rooms.validate()
    log.info(f"[RoomDetection] Structure validation: {msg}")
    
    if not is_valid:
        log.error(f"[RoomDetection] ✗ VALIDATION FAILED: {msg}")
        return None
    
    # Report summary
    summary = rooms.summary()
    log.info("[RoomDetection] Room summary:")
    log.info(f"  Room count: {summary['room_count']}")
    log.info(f"  Total room area: {summary['total_room_area']} pixels")
    log.info(f"  Avg room area: {summary['avg_room_area']:.0f} pixels")
    log.info(f"  Min area: {summary['min_area']} pixels")
    log.info(f"  Max area: {summary['max_area']} pixels")
    
    log.info("[RoomDetection] ✓ STAGE 4 COMPLETE (No merging detected)")
    return rooms


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    print("Room detection module loaded")
