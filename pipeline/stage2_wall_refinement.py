"""
WALL MASK REFINEMENT MODULE
Stage 2: Wall Mask Refinement (Deterministic)

Purpose: Refine semantic wall mask by removing door/window regions while
preserving wall continuity.

Key Principle: Walls must remain continuous even through door openings.
A door is a functional gap, not a structural wall absence.

Algorithm:
1. Extract wall pixels from semantic mask
2. Extract door/window pixels
3. Morphological operations to preserve continuity
4. Validate refined mask
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import logging

log = logging.getLogger(__name__)

# ============================================================================
# WALL MASK REFINEMENT
# ============================================================================

class WallMaskRefinement:
    """
    Refine semantic wall mask to preserve wall continuity.
    
    Operations:
    - Remove door regions (they are gaps, not walls)
    - Remove window regions (they are gaps, not walls)
    - Preserve wall continuity through openings
    - Apply morphological operations for robustness
    """
    
    def __init__(self, 
                 wall_mask: np.ndarray,
                 door_mask: np.ndarray,
                 window_mask: np.ndarray,
                 min_wall_thickness_px: int = 2):
        """
        Args:
            wall_mask: Binary wall mask from semantic segmentation
            door_mask: Binary door mask from semantic segmentation
            window_mask: Binary window mask from semantic segmentation
            min_wall_thickness_px: Minimum wall thickness in pixels
        """
        self.wall_mask = wall_mask.astype(np.uint8)
        self.door_mask = door_mask.astype(np.uint8)
        self.window_mask = window_mask.astype(np.uint8)
        self.min_wall_thickness = min_wall_thickness_px
        
        self.refined_mask = None
        self.log_info = []
    
    def refine(self) -> np.ndarray:
        """
        Execute wall mask refinement pipeline.
        
        Returns:
            refined_mask: Cleaned binary wall mask
        """
        
        log.info("[WallRefinement] Starting wall mask refinement")
        self.log_info.append("Starting wall mask refinement")
        
        # Step 1: Start with original wall mask
        refined = self.wall_mask.copy()
        initial_wall_pixels = refined.sum()
        log.info(f"[WallRefinement] Initial wall pixels: {initial_wall_pixels}")
        
        # Step 2: Remove door regions (they are gaps, not walls)
        # But preserve wall continuity
        refined = self._remove_openings_preserve_continuity(
            refined, self.door_mask, "doors"
        )
        
        # Step 3: Remove window regions
        refined = self._remove_openings_preserve_continuity(
            refined, self.window_mask, "windows"
        )
        
        # Step 4: Morphological cleanup
        refined = self._morphological_cleanup(refined)
        
        # Step 5: Remove small isolated components
        refined = self._remove_small_components(refined, min_size=20)
        
        self.refined_mask = refined
        
        final_wall_pixels = refined.sum()
        removed_pixels = initial_wall_pixels - final_wall_pixels
        log.info(f"[WallRefinement] Final wall pixels: {final_wall_pixels}")
        log.info(f"[WallRefinement] Removed pixels: {removed_pixels}")
        
        log.info("[WallRefinement] ✓ Refinement complete")
        return refined
    
    def _remove_openings_preserve_continuity(self,
                                           wall_mask: np.ndarray,
                                           opening_mask: np.ndarray,
                                           opening_type: str) -> np.ndarray:
        """
        Remove opening regions while preserving wall continuity.
        
        Strategy: Dilate the opening mask slightly to ensure wall gaps are
        created, but don't break the overall wall structure.
        """
        
        count_before = wall_mask.sum()
        
        # Dilate opening mask slightly to create clean gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        dilated_openings = cv2.dilate(opening_mask, kernel, iterations=1)
        
        # Remove opening regions from wall mask
        result = wall_mask.copy()
        result[dilated_openings > 0] = 0
        
        count_after = result.sum()
        removed = count_before - count_after
        
        log.info(f"[WallRefinement] Removed {opening_type}: {removed} pixels")
        self.log_info.append(f"Removed {opening_type}: {removed} pixels")
        
        return result
    
    def _morphological_cleanup(self, mask: np.ndarray) -> np.ndarray:
        """
        Apply morphological operations to clean up wall mask.
        
        Operations:
        - Closing: Fill small gaps in walls
        - Opening: Remove small noise
        """
        
        log.info("[WallRefinement] Applying morphological cleanup")
        
        # Create kernel for closing (fill gaps)
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        result = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
        
        # Create kernel for opening (remove noise)
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        result = cv2.morphologyEx(result, cv2.MORPH_OPEN, kernel_open)
        
        return result
    
    def _remove_small_components(self,
                                 mask: np.ndarray,
                                 min_size: int = 20) -> np.ndarray:
        """
        Remove connected components smaller than min_size.
        
        Prevents isolated pixels from affecting topology.
        """
        
        # Label connected components
        num_labels, labels = cv2.connectedComponents(mask)
        
        log.info(f"[WallRefinement] Found {num_labels} connected wall components")
        
        result = mask.copy()
        
        # Remove small components
        removed_count = 0
        for label_id in range(1, num_labels):
            component_size = (labels == label_id).sum()
            if component_size < min_size:
                result[labels == label_id] = 0
                removed_count += 1
        
        if removed_count > 0:
            log.info(f"[WallRefinement] Removed {removed_count} small components")
            self.log_info.append(f"Removed {removed_count} small components")
        
        return result
    
    def validate(self) -> Tuple[bool, str]:
        """
        Validate refined wall mask.
        
        Returns:
            (is_valid, message)
        """
        
        if self.refined_mask is None:
            return False, "Refinement not yet executed"
        
        # Check that walls still exist
        wall_pixels = self.refined_mask.sum()
        total_pixels = self.refined_mask.size
        
        if wall_pixels < 100:
            return False, "Too few wall pixels remaining after refinement"
        
        if wall_pixels > 0.95 * total_pixels:
            return False, "Too many wall pixels (refinement likely failed)"
        
        percentage = 100.0 * wall_pixels / total_pixels
        log.info(f"[WallRefinement] Wall coverage: {percentage:.1f}%")
        
        return True, "Refined wall mask valid"

# ============================================================================
# STAGE 2 MAIN INTERFACE
# ============================================================================

def stage2_wall_mask_refinement(
        semantic_output,
        min_wall_thickness_px: int = 2
) -> Optional[np.ndarray]:
    """
    STAGE 2: Wall Mask Refinement (Deterministic)
    
    Input: Semantic segmentation output (WALL, DOOR, WINDOW masks)
    Output: Clean binary wall mask with preserved continuity
    
    Key principle: Walls must remain continuous through door openings.
    
    Args:
        semantic_output: SemanticMaskOutput from Stage 1
        min_wall_thickness_px: Minimum wall thickness in pixels
    
    Returns:
        refined_wall_mask (binary) or None if failed
    """
    
    log.info("="*80)
    log.info("STAGE 2: WALL MASK REFINEMENT (Deterministic)")
    log.info("="*80)
    
    if semantic_output is None:
        log.error("[WallRefinement] No semantic output provided")
        return None
    
    # Extract class masks
    wall_mask = semantic_output.get_wall_mask()
    door_mask = semantic_output.get_door_mask()
    window_mask = semantic_output.get_window_mask()
    
    log.info(f"[WallRefinement] Wall pixels: {wall_mask.sum()}")
    log.info(f"[WallRefinement] Door pixels: {door_mask.sum()}")
    log.info(f"[WallRefinement] Window pixels: {window_mask.sum()}")
    
    # Refine wall mask
    refiner = WallMaskRefinement(wall_mask, door_mask, window_mask, min_wall_thickness_px)
    refined_mask = refiner.refine()
    
    # Validate
    is_valid, message = refiner.validate()
    log.info(f"[WallRefinement] Validation: {message}")
    
    if not is_valid:
        log.error(f"[WallRefinement] ✗ VALIDATION FAILED: {message}")
        return None
    
    log.info("[WallRefinement] ✓ STAGE 2 COMPLETE")
    return refined_mask


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    # Example: This would be called after Stage 1
    print("Wall mask refinement module loaded")
