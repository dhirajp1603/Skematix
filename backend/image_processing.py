import cv2
import numpy as np
import json
import os


def process_image(image_path, json_output_path=None, debug=False, method='hough', normalize=True):
    """
    Process a floorplan image and extract wall information.

    method:
      - 'basic' : contour-based wall detection
      - 'hough' : line-based wall detection (default)
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(image_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h_img, w_img = gray.shape

    # --- Binarization with adaptive approach ---
    # Try to separate walls from background
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Use Otsu's thresholding
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Invert if needed (walls should be white/foreground)
    if np.mean(th == 255) < 0.3:  # More than 70% black - invert
        th = cv2.bitwise_not(th)

    # --- Enhanced Morphology ---
    # Use larger kernel to better connect wall segments
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel_close, iterations=2)
    
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel_open, iterations=1)
    
    # Additional dilation to emphasize walls
    th = cv2.dilate(th, kernel_close, iterations=1)

    walls = []
    processed = th.copy()

    # ======================================================
    # HOUGH LINE DETECTION (improved)
    # ======================================================
    edges = cv2.Canny(processed, 20, 60)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=40,  # Lowered threshold to catch more lines
        minLineLength=15,  # Reduced minimum length
        maxLineGap=20  # Reduced gap tolerance
    )

    mask = np.zeros_like(processed)

    if lines is not None:
        lines = lines.reshape(-1, 4)

        for (x1, y1, x2, y2) in lines:
            cv2.line(mask, (x1, y1), (x2, y2), 255, thickness=3)  # Thinner lines for precision

    # Merge line segments into wall segments
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    # Extract contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 300:  # Adjusted minimum area
            continue

        # Approximate contour to reduce noise
        epsilon = 0.02 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        
        # Get bounding box
        x, y, w, h = cv2.boundingRect(approx)
        
        # Filter out very small walls
        if w < 5 or h < 5:
            continue
        
        walls.append({
            "bbox": {"x": x, "y": y, "w": w, "h": h},
            "area": area
        })

    processed = mask

    # ======================================================
    # WALL MERGING TO CONNECT DISCONNECTED SEGMENTS
    # ======================================================
    def merge_walls(walls_list, merge_threshold=60):
        """
        Merge overlapping or nearby wall bounding boxes with improved logic.
        """
        if not walls_list:
            return walls_list

        merged = []
        used = [False] * len(walls_list)

        for i, w1 in enumerate(walls_list):
            if used[i]:
                continue

            b1 = w1["bbox"]
            x1, y1, w1_w, h1 = b1["x"], b1["y"], b1["w"], b1["h"]
            x1_end, y1_end = x1 + w1_w, y1 + h1

            # Find walls to merge with
            to_merge = [i]
            for j in range(i + 1, len(walls_list)):
                if used[j]:
                    continue

                b2 = walls_list[j]["bbox"]
                x2, y2, w2_w, h2 = b2["x"], b2["y"], b2["w"], b2["h"]
                x2_end, y2_end = x2 + w2_w, y2 + h2

                # Check overlap
                overlap_x = max(0, min(x1_end, x2_end) - max(x1, x2))
                overlap_y = max(0, min(y1_end, y2_end) - max(y1, y2))

                # Check if aligned (horizontal or vertical)
                is_horizontal = abs(y1 - y2) < merge_threshold
                is_vertical = abs(x1 - x2) < merge_threshold

                # Merge if overlapping or aligned and close
                if (overlap_x > 0 and overlap_y > 0) or \
                   (is_horizontal and overlap_x > 0) or \
                   (is_vertical and overlap_y > 0):
                    to_merge.append(j)
                    used[j] = True

            # Create merged wall
            merged_bbox = {
                "x": min(walls_list[k]["bbox"]["x"] for k in to_merge),
                "y": min(walls_list[k]["bbox"]["y"] for k in to_merge),
                "x_end": max(walls_list[k]["bbox"]["x"] + walls_list[k]["bbox"]["w"] for k in to_merge),
                "y_end": max(walls_list[k]["bbox"]["y"] + walls_list[k]["bbox"]["h"] for k in to_merge),
            }
            merged_bbox["w"] = merged_bbox["x_end"] - merged_bbox["x"]
            merged_bbox["h"] = merged_bbox["y_end"] - merged_bbox["y"]

            merged.append({
                "bbox": {k: merged_bbox[k] for k in ["x", "y", "w", "h"]}
            })
            used[i] = True

        return merged

    walls = merge_walls(walls, merge_threshold=60)

    # ======================================================
    # NORMALIZATION + SAVE
    # ======================================================
    output_walls = []

    for w in walls:
        b = w["bbox"]
        if normalize:
            output_walls.append({
                "bbox": {
                    "x": b["x"] / w_img,
                    "y": b["y"] / h_img,
                    "w": b["w"] / w_img,
                    "h": b["h"] / h_img
                }
            })
        else:
            output_walls.append(w)

    if json_output_path:
        os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
        with open(json_output_path, "w") as f:
            json.dump({
                "image": os.path.basename(image_path),
                "walls": output_walls
            }, f, indent=2)

    if debug:
        dbg = os.path.join(os.path.dirname(image_path), "debug_processed.png")
        cv2.imwrite(dbg, processed)

    return output_walls

    # ======================================================
    # WALL MERGING TO CONNECT DISCONNECTED SEGMENTS
    # ======================================================
    def merge_walls(walls_list, merge_threshold=50):
        """
        Merge overlapping or nearby wall bounding boxes to create continuous walls.
        Use a more aggressive merging strategy to connect disconnected segments.
        """
        if not walls_list:
            return walls_list

        merged = []
        used = [False] * len(walls_list)

        for i, w1 in enumerate(walls_list):
            if used[i]:
                continue

            b1 = w1["bbox"]
            x1, y1, w1_w, h1 = b1["x"], b1["y"], b1["w"], b1["h"]
            x1_end, y1_end = x1 + w1_w, y1 + h1

            # Find walls to merge with (recursive merging)
            to_merge = [i]
            stack = [i]
            while stack:
                current = stack.pop()
                if used[current]:
                    continue
                used[current] = True

                cb = walls_list[current]["bbox"]
                cx, cy, cw, ch = cb["x"], cb["y"], cb["w"], cb["h"]
                cx_end, cy_end = cx + cw, cy + ch

                for j, w2 in enumerate(walls_list):
                    if used[j]:
                        continue

                    b2 = w2["bbox"]
                    x2, y2, w2_w, h2 = b2["x"], b2["y"], b2["w"], b2["h"]
                    x2_end, y2_end = x2 + w2_w, y2 + h2

                    # Check for overlap or proximity (more lenient)
                    overlap_x = max(0, min(cx_end, x2_end) - max(cx, x2))
                    overlap_y = max(0, min(cy_end, y2_end) - max(cy, y2))

                    # Distance between centers
                    center_dist = ((cx + cw/2 - x2 - w2_w/2)**2 + (cy + ch/2 - y2 - h2/2)**2)**0.5

                    # Merge if significant overlap, close proximity, or aligned
                    if (overlap_x > 0 and overlap_y > min(ch, h2) * 0.3) or \
                       (overlap_y > 0 and overlap_x > min(cw, w2_w) * 0.3) or \
                       (center_dist < merge_threshold and (abs(cx - x2) < merge_threshold or abs(cy - y2) < merge_threshold)):
                        to_merge.append(j)
                        stack.append(j)

            # Merge all found walls
            if len(to_merge) > 1:
                min_x = min(walls_list[k]["bbox"]["x"] for k in to_merge)
                min_y = min(walls_list[k]["bbox"]["y"] for k in to_merge)
                max_x_end = max(walls_list[k]["bbox"]["x"] + walls_list[k]["bbox"]["w"] for k in to_merge)
                max_y_end = max(walls_list[k]["bbox"]["y"] + walls_list[k]["bbox"]["h"] for k in to_merge)

                merged_wall = {
                    "bbox": {
                        "x": min_x,
                        "y": min_y,
                        "w": max_x_end - min_x,
                        "h": max_y_end - min_y
                    }
                }
                merged.append(merged_wall)
            else:
                merged.append(w1)
                used[i] = True

        return merged

    walls = merge_walls(walls, merge_threshold=50)

    # ======================================================
    # NORMALIZATION + SAVE
    # ======================================================
    output_walls = []

    for w in walls:
        b = w["bbox"]
        if normalize:
            output_walls.append({
                "bbox": {
                    "x": b["x"] / w_img,
                    "y": b["y"] / h_img,
                    "w": b["w"] / w_img,
                    "h": b["h"] / h_img
                }
            })
        else:
            output_walls.append(w)

    if json_output_path:
        os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
        with open(json_output_path, "w") as f:
            json.dump({
                "image": os.path.basename(image_path),
                "walls": output_walls
            }, f, indent=2)

    if debug:
        dbg = os.path.join(os.path.dirname(image_path), "debug_processed.png")
        cv2.imwrite(dbg, processed)

    return output_walls


def precise_process(image_path, json_output_path=None, thickness_m=0.2, wall_height=3.0, orthogonal=True, debug=False):
    """
    Higher-precision pipeline that estimates scale and outputs 3D-ready data.
    """
    walls_px = process_image(image_path, None, debug=False, method='hough', normalize=False)

    if not walls_px:
        raise RuntimeError("No walls detected")

    # Estimate thickness in pixels
    thickness_vals = [min(w["bbox"]["w"], w["bbox"]["h"]) for w in walls_px]
    thickness_px = max(4, int(np.median(thickness_vals)))

    scale = thickness_m / thickness_px

    h_img, w_img = cv2.imread(image_path).shape[:2]
    norm_walls = []

    for w in walls_px:
        b = w["bbox"]
        norm_walls.append({
            "bbox": {
                "x": b["x"] / w_img,
                "y": b["y"] / h_img,
                "w": b["w"] / w_img,
                "h": b["h"] / h_img
            }
        })

    if json_output_path:
        os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
        with open(json_output_path, "w") as f:
            json.dump({
                "image": os.path.basename(image_path),
                "walls": norm_walls,
                "scale_m_per_px": scale,
                "thickness_m": thickness_m,
                "wall_height_m": wall_height
            }, f, indent=2)

    return norm_walls, scale


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python image_processing.py <image>")
        sys.exit(1)

    walls = process_image(sys.argv[1], debug=True)
    print("Detected walls:", len(walls))
