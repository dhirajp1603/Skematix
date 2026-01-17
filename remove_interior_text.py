#!/usr/bin/env python3
"""
Interior Text Removal with Structure Awareness

Strategy: Remove room labels/text while preserving door/window openings
- Connected component analysis
- Identify which components touch wall boundaries (likely walls/doors/windows)
- Remove components fully enclosed in room interiors (likely text)
- Preserve elongated components (likely wall breaks/openings)
"""

import cv2
import numpy as np
from pathlib import Path
from scipy import ndimage
import sys


def get_distance_to_boundary(mask_shape, component_mask, label):
    """
    Calculate minimum distance from component to image boundary
    
    Returns:
        (min_dist_to_boundary, touches_boundary)
    """
    # Get component pixels
    component_pixels = np.where(component_mask == label)
    
    if len(component_pixels[0]) == 0:
        return float('inf'), False
    
    rows, cols = component_pixels
    
    # Distance to image boundary
    dist_to_top = np.min(rows)
    dist_to_bottom = mask_shape[0] - np.max(rows) - 1
    dist_to_left = np.min(cols)
    dist_to_right = mask_shape[1] - np.max(cols) - 1
    
    min_dist = min(dist_to_top, dist_to_bottom, dist_to_left, dist_to_right)
    touches_boundary = min_dist < 3  # Within 3 pixels of edge
    
    return min_dist, touches_boundary


def analyze_component_structure(component_mask, label, mask_shape):
    """Analyze properties of a single connected component"""
    
    # Get binary mask for this component
    comp_binary = (component_mask == label).astype(np.uint8)
    
    # Properties
    area = np.sum(comp_binary)
    
    # Bounding box
    rows, cols = np.where(comp_binary)
    if len(rows) == 0:
        return None
    
    y_min, y_max = rows.min(), rows.max()
    x_min, x_max = cols.min(), cols.max()
    width = x_max - x_min + 1
    height = y_max - y_min + 1
    
    # Aspect ratio (1=square, >2=elongated)
    aspect_ratio = max(width, height) / (min(width, height) + 1e-6)
    
    # Solidity (area / bounding_box_area)
    bbox_area = width * height
    solidity = area / (bbox_area + 1e-6)
    
    # Perimeter (boundary length)
    contours, _ = cv2.findContours(comp_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return None
    
    main_contour = max(contours, key=cv2.contourArea)
    perimeter = cv2.arcLength(main_contour, False)
    
    # Circularity
    circularity = (4 * np.pi * area) / (perimeter ** 2 + 1e-6) if perimeter > 0 else 0
    
    # Distance to image boundary
    dist_to_boundary, touches_boundary = get_distance_to_boundary(mask_shape, component_mask, label)
    
    # Check if component touches any wall boundary (not just image edge)
    # This helps identify text that's fully enclosed in room interior
    
    return {
        'label': label,
        'area': area,
        'perimeter': perimeter,
        'width': width,
        'height': height,
        'aspect_ratio': aspect_ratio,
        'solidity': solidity,
        'circularity': circularity,
        'bbox': (x_min, y_min, width, height),
        'dist_to_boundary': dist_to_boundary,
        'touches_boundary': touches_boundary,
    }


def is_interior_text(props, area_threshold=300, aspect_threshold=2.5):
    """
    Determine if component is likely interior text (room label)
    
    Interior text characteristics:
    - Moderate area (not tiny like noise, not huge like walls)
    - Moderate solidity (letters have strokes)
    - NOT elongated (text is compact)
    - Does NOT touch boundary (fully enclosed in room)
    
    Wall/Door/Window characteristics:
    - Touches boundary OR
    - Elongated (aspect ratio > threshold) OR
    - Low solidity (openings/strokes)
    """
    
    area = props['area']
    aspect_ratio = props['aspect_ratio']
    solidity = props['solidity']
    touches_boundary = props['touches_boundary']
    circularity = props['circularity']
    
    # Rules for keeping components (likely walls/doors/windows)
    keep_if_elongated = aspect_ratio > aspect_threshold
    keep_if_low_solidity = solidity < 0.3
    keep_if_touches_boundary = touches_boundary
    keep_if_linear = circularity < 0.2
    
    # If any "keep" rule is true, preserve it
    if keep_if_elongated or keep_if_touches_boundary or keep_if_linear or keep_if_low_solidity:
        return False
    
    # Otherwise, if area is reasonable for text, remove it
    is_text_sized = 50 < area < area_threshold
    is_compact = aspect_ratio < aspect_threshold
    is_solid_enough = solidity > 0.3
    
    return is_text_sized and is_compact and is_solid_enough


def remove_interior_text(clean_mask_path, output_path, clean_overlay_path=None):
    """
    Remove interior text artifacts while preserving door/window openings
    
    Args:
        clean_mask_path: Path to cleaned binary wall mask PNG
        output_path: Output path for final mask
        clean_overlay_path: Optional path for visual verification overlay
    """
    
    print("=" * 80)
    print("INTERIOR TEXT REMOVAL: STRUCTURE-AWARE POST-PROCESSING")
    print("=" * 80)
    print()
    
    clean_mask_path = Path(clean_mask_path)
    if not clean_mask_path.exists():
        print(f"[ERROR] Mask not found: {clean_mask_path}")
        return False
    
    # Load cleaned binary mask
    print(f"[1/6] Loading cleaned binary wall mask: {clean_mask_path.name}")
    mask = cv2.imread(str(clean_mask_path), cv2.IMREAD_GRAYSCALE)
    
    if mask is None:
        print(f"[ERROR] Failed to load mask")
        return False
    
    original_shape = mask.shape
    wall_pixels_original = np.sum(mask > 0)
    
    print(f"      Dimensions: {original_shape[1]}×{original_shape[0]}")
    print(f"      Wall pixels (original): {wall_pixels_original:,}")
    print()
    
    # Connected component labeling
    print(f"[2/6] Connected component analysis...")
    
    binary_mask = (mask > 127).astype(np.uint8) * 255
    labeled_array, num_components = ndimage.label(binary_mask)
    
    print(f"      Components found: {num_components}")
    print()
    
    # Analyze components
    print(f"[3/6] Analyzing component structure...")
    
    components_properties = []
    for label in range(1, num_components + 1):
        props = analyze_component_structure(labeled_array, label, original_shape)
        if props is not None:
            components_properties.append(props)
    
    print(f"      Total components: {len(components_properties)}")
    print()
    
    # Classify components
    print(f"[4/6] Classifying components...")
    print(f"      Classification rules:")
    print(f"        - KEEP: touches boundary OR elongated OR low solidity")
    print(f"        - REMOVE: interior text (compact, enclosed, moderate area)")
    print()
    
    wall_components = []
    text_components = []
    boundary_touching_count = 0
    elongated_count = 0
    low_solidity_count = 0
    
    for props in components_properties:
        if is_interior_text(props):
            text_components.append(props)
        else:
            wall_components.append(props)
            
            # Track why we kept it
            if props['touches_boundary']:
                boundary_touching_count += 1
            if props['aspect_ratio'] > 2.5:
                elongated_count += 1
            if props['solidity'] < 0.3:
                low_solidity_count += 1
    
    print(f"      Wall components: {len(wall_components)}")
    print(f"        ├─ Touching boundary: {boundary_touching_count}")
    print(f"        ├─ Elongated (aspect ratio > 2.5): {elongated_count}")
    print(f"        └─ Low solidity (< 0.3): {low_solidity_count}")
    print()
    print(f"      Text components (to remove): {len(text_components)}")
    
    # Show details on text components
    if text_components:
        print(f"      Text component details:")
        text_components_sorted = sorted(text_components, key=lambda x: x['area'], reverse=True)
        for i, comp in enumerate(text_components_sorted[:5]):
            print(f"        - Component {comp['label']}: area={comp['area']}, "
                  f"aspect_ratio={comp['aspect_ratio']:.2f}, solidity={comp['solidity']:.2f}")
        if len(text_components) > 5:
            print(f"        ... and {len(text_components) - 5} more")
        print()
    
    # Create final mask
    print(f"[5/6] Creating final mask...")
    
    final_mask = np.zeros_like(binary_mask)
    
    # Add only wall components
    for comp in wall_components:
        label = comp['label']
        final_mask[labeled_array == label] = 255
    
    wall_pixels_final = np.sum(final_mask > 0)
    pixels_removed = wall_pixels_original - wall_pixels_final
    removal_percentage = (pixels_removed / wall_pixels_original * 100) if wall_pixels_original > 0 else 0
    
    print(f"      Wall pixels (final): {wall_pixels_final:,}")
    print(f"      Pixels removed: {pixels_removed:,} ({removal_percentage:.2f}%)")
    print()
    
    # Save final mask
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cv2.imwrite(str(output_path), final_mask)
    print(f"[OUTPUT] Final mask saved: {output_path.name}")
    print(f"         Path: {output_path.absolute()}")
    print()
    
    # Create overlay for visual verification if requested
    if clean_overlay_path:
        print(f"[6/6] Creating verification overlay...")
        
        overlay = np.zeros((original_shape[0], original_shape[1], 3), dtype=np.uint8)
        
        # Walls = gray
        overlay[final_mask > 127] = [100, 100, 100]
        
        # Removed text = red
        removed_mask = binary_mask - final_mask
        overlay[removed_mask > 127] = [0, 0, 255]
        
        clean_overlay_path = Path(clean_overlay_path)
        clean_overlay_path.parent.mkdir(parents=True, exist_ok=True)
        
        cv2.imwrite(str(clean_overlay_path), overlay)
        print(f"[OUTPUT] Verification overlay saved: {clean_overlay_path.name}")
        print(f"         Path: {clean_overlay_path.absolute()}")
        print(f"         (Gray=walls, Red=removed text)")
        print()
    
    print("=" * 80)
    print("INTERIOR TEXT REMOVAL COMPLETE")
    print("=" * 80)
    print()
    
    return True


def process_batch(output_folder):
    """Process all cleaned masks to remove interior text"""
    
    print("\n" + "=" * 80)
    print("BATCH INTERIOR TEXT REMOVAL")
    print("=" * 80)
    print()
    
    output_base = Path(output_folder)
    
    # Find all cleaned mask files
    mask_files = sorted(output_base.glob("*_*/*_walls_mask_clean.png"))
    if not mask_files:
        mask_files = sorted(output_base.glob("*/*_walls_mask_clean.png"))
    
    if not mask_files:
        print(f"No cleaned masks found in {output_base}")
        return
    
    print(f"Found {len(mask_files)} cleaned wall mask(s)")
    print()
    
    for idx, mask_file in enumerate(mask_files, 1):
        print(f"\n[{idx}/{len(mask_files)}]")
        print("-" * 80)
        
        # Output paths
        output_folder_path = mask_file.parent
        image_name = mask_file.stem.replace("_walls_mask_clean", "")
        
        final_mask_path = output_folder_path / f"{image_name}_walls_mask_final.png"
        final_overlay_path = output_folder_path / f"{image_name}_walls_overlay_final.png"
        
        remove_interior_text(
            mask_file,
            final_mask_path,
            final_overlay_path
        )


if __name__ == "__main__":
    
    # Get mode from command line
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        # Batch mode: process all cleaned masks
        output_dir = Path(__file__).parent / "output"
        process_batch(str(output_dir))
    else:
        # Single file mode (if provided)
        if len(sys.argv) > 1:
            mask_path = sys.argv[1]
            output_path = sys.argv[2] if len(sys.argv) > 2 else "final_output.png"
            overlay_path = sys.argv[3] if len(sys.argv) > 3 else "final_overlay.png"
            
            remove_interior_text(mask_path, output_path, overlay_path)
        else:
            print("Interior Text Removal - Structure-Aware Post-Processing")
            print()
            print("Usage:")
            print("  python remove_interior_text.py <cleaned_mask.png> <output.png> [overlay.png]")
            print("  python remove_interior_text.py batch")
            print()
            print("Input: Cleaned binary wall masks (*_walls_mask_clean.png)")
            print("Output: Final masks with interior text removed (*_walls_mask_final.png)")
            print()
            print("Strategy:")
            print("  - Remove components fully enclosed in room interiors (text labels)")
            print("  - Preserve elongated components (walls, door/window openings)")
            print("  - Preserve components touching boundaries (structural walls)")
