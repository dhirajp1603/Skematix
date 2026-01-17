#!/usr/bin/env python3
"""
Binary Wall Mask Post-Processing: Text Artifact Removal

Strategy: Connected component analysis + morphological filtering
- Identify connected components in binary mask
- Remove small/thin components (likely text)
- Preserve large/continuous structures (walls)
"""

import cv2
import numpy as np
from pathlib import Path
from scipy import ndimage
import sys


def analyze_component_properties(component_mask, label):
    """Analyze properties of a single connected component"""
    
    # Get binary mask for this component
    comp_binary = (component_mask == label).astype(np.uint8)
    
    # Properties
    area = np.sum(comp_binary)
    
    # Find contours to measure length
    contours, _ = cv2.findContours(comp_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) == 0:
        return None
    
    # Get the main contour
    main_contour = max(contours, key=cv2.contourArea)
    perimeter = cv2.arcLength(main_contour, False)
    
    # Fit bounding rect
    x, y, w, h = cv2.boundingRect(main_contour)
    
    # Aspect ratio
    aspect_ratio = max(w, h) / (min(w, h) + 1e-6)
    
    # Solidity (how filled is the bounding box)
    rect_area = w * h
    solidity = area / (rect_area + 1e-6)
    
    # Circularity (4*pi*area / perimeter^2, closer to 1 = circle, closer to 0 = line)
    circularity = (4 * np.pi * area) / (perimeter ** 2 + 1e-6) if perimeter > 0 else 0
    
    return {
        'label': label,
        'area': area,
        'perimeter': perimeter,
        'width': w,
        'height': h,
        'aspect_ratio': aspect_ratio,
        'solidity': solidity,
        'circularity': circularity,
        'bbox': (x, y, w, h)
    }


def is_text_like(props, area_threshold=200, circularity_threshold=0.15):
    """
    Determine if component is likely text
    
    Text characteristics:
    - Small area
    - High circularity (not elongated like walls)
    - Low solidity (strokes, not filled)
    """
    
    area = props['area']
    circularity = props['circularity']
    solidity = props['solidity']
    
    # Text is typically:
    # - Small area (< threshold)
    # - More circular/round (not elongated like walls)
    # - Not very solid (strokes)
    
    is_small = area < area_threshold
    is_circular = circularity > circularity_threshold
    is_not_solid = solidity < 0.4
    
    # Text detection: small AND (circular OR not solid)
    return is_small and (is_circular or is_not_solid)


def remove_text_artifacts(mask_path, output_path, clean_overlay_path=None):
    """
    Remove text artifacts from binary wall mask
    
    Args:
        mask_path: Path to binary wall mask PNG
        output_path: Output path for cleaned mask
        clean_overlay_path: Optional path for visual verification overlay
    """
    
    print("=" * 80)
    print("BINARY WALL MASK POST-PROCESSING: TEXT ARTIFACT REMOVAL")
    print("=" * 80)
    print()
    
    mask_path = Path(mask_path)
    if not mask_path.exists():
        print(f"[ERROR] Mask not found: {mask_path}")
        return False
    
    # Load binary mask
    print(f"[1/5] Loading binary mask: {mask_path.name}")
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    
    if mask is None:
        print(f"[ERROR] Failed to load mask")
        return False
    
    original_shape = mask.shape
    wall_pixels_original = np.sum(mask > 0)
    
    print(f"      Dimensions: {original_shape[1]}x{original_shape[0]}")
    print(f"      Wall pixels (original): {wall_pixels_original:,}")
    print()
    
    # Connected component labeling
    print(f"[2/5] Connected component analysis...")
    
    # Binary threshold if needed
    binary_mask = (mask > 127).astype(np.uint8) * 255
    
    # Label connected components
    labeled_array, num_components = ndimage.label(binary_mask)
    
    print(f"      Components found: {num_components}")
    print()
    
    # Analyze components
    print(f"[3/5] Analyzing component properties...")
    
    components_properties = []
    for label in range(1, num_components + 1):
        props = analyze_component_properties(labeled_array, label)
        if props is not None:
            components_properties.append(props)
    
    print(f"      Total components: {len(components_properties)}")
    print()
    
    # Classify components
    print(f"[4/5] Classifying components...")
    
    text_components = []
    wall_components = []
    
    for props in components_properties:
        if is_text_like(props):
            text_components.append(props)
        else:
            wall_components.append(props)
    
    print(f"      Wall components: {len(wall_components)}")
    print(f"      Text components: {len(text_components)} (to remove)")
    print()
    
    # Show details on text components
    if text_components:
        print(f"      Text component details:")
        text_components_sorted = sorted(text_components, key=lambda x: x['area'], reverse=True)
        for i, comp in enumerate(text_components_sorted[:5]):
            print(f"        - Component {comp['label']}: area={comp['area']}, "
                  f"circularity={comp['circularity']:.3f}, solidity={comp['solidity']:.3f}")
        if len(text_components) > 5:
            print(f"        ... and {len(text_components) - 5} more")
        print()
    
    # Create cleaned mask
    print(f"[5/5] Creating cleaned mask...")
    
    cleaned_mask = np.zeros_like(binary_mask)
    
    # Add only wall components
    for comp in wall_components:
        label = comp['label']
        cleaned_mask[labeled_array == label] = 255
    
    wall_pixels_cleaned = np.sum(cleaned_mask > 0)
    pixels_removed = wall_pixels_original - wall_pixels_cleaned
    removal_percentage = (pixels_removed / wall_pixels_original * 100) if wall_pixels_original > 0 else 0
    
    print(f"      Wall pixels (cleaned): {wall_pixels_cleaned:,}")
    print(f"      Pixels removed: {pixels_removed:,} ({removal_percentage:.2f}%)")
    print()
    
    # Save cleaned mask
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cv2.imwrite(str(output_path), cleaned_mask)
    print(f"[OUTPUT] Cleaned mask saved: {output_path.name}")
    print(f"          Path: {output_path.absolute()}")
    print()
    
    # Create overlay for visual verification if requested
    if clean_overlay_path:
        print(f"[VERIFY] Creating overlay for visual verification...")
        
        # Load original floor plan (if available) - for now, just visualize the mask
        overlay = np.zeros((original_shape[0], original_shape[1], 3), dtype=np.uint8)
        
        # Wall = gray
        overlay[cleaned_mask > 127] = [100, 100, 100]
        
        # Removed text = red (for visualization of what was removed)
        removed_mask = binary_mask - cleaned_mask
        overlay[removed_mask > 127] = [0, 0, 255]
        
        clean_overlay_path = Path(clean_overlay_path)
        clean_overlay_path.parent.mkdir(parents=True, exist_ok=True)
        
        cv2.imwrite(str(clean_overlay_path), overlay)
        print(f"[OUTPUT] Verification overlay saved: {clean_overlay_path.name}")
        print(f"          Path: {clean_overlay_path.absolute()}")
        print(f"          (Gray=walls, Red=removed artifacts)")
        print()
    
    print("=" * 80)
    print("POST-PROCESSING COMPLETE")
    print("=" * 80)
    print()
    
    return True


def process_batch(output_folder):
    """Process all wall masks in output folders"""
    
    print("\n" + "=" * 80)
    print("BATCH TEXT ARTIFACT REMOVAL")
    print("=" * 80)
    print()
    
    output_base = Path(output_folder)
    
    # Find all mask files (try different patterns)
    mask_files = sorted(output_base.glob("*_*/*_walls_mask.png"))
    if not mask_files:
        mask_files = sorted(output_base.glob("*/*_walls_mask.png"))
    
    if not mask_files:
        print(f"No masks found in {output_base}")
        return
    
    print(f"Found {len(mask_files)} wall mask(s)")
    print()
    
    for idx, mask_file in enumerate(mask_files, 1):
        print(f"\n[{idx}/{len(mask_files)}]")
        print("-" * 80)
        
        # Output paths
        output_folder_path = mask_file.parent
        image_name = mask_file.stem.replace("_walls_mask", "")
        
        clean_mask_path = output_folder_path / f"{image_name}_walls_mask_clean.png"
        clean_overlay_path = output_folder_path / f"{image_name}_walls_overlay_clean.png"
        
        remove_text_artifacts(
            mask_file,
            clean_mask_path,
            clean_overlay_path
        )


if __name__ == "__main__":
    
    # Get mode from command line
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        # Batch mode: process all masks
        output_dir = Path(__file__).parent / "output"
        process_batch(str(output_dir))
    else:
        # Single file mode (if provided)
        if len(sys.argv) > 1:
            mask_path = sys.argv[1]
            output_path = sys.argv[2] if len(sys.argv) > 2 else "output_clean.png"
            overlay_path = sys.argv[3] if len(sys.argv) > 3 else "overlay_clean.png"
            
            remove_text_artifacts(mask_path, output_path, overlay_path)
        else:
            print("Usage:")
            print("  python remove_text_artifacts.py <mask.png> <output.png> [overlay.png]")
            print("  python remove_text_artifacts.py batch")
            print()
            print("Run in batch mode to process all masks in output/ folders")
