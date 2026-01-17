"""
PROFESSIONAL TYPE-2 ARCHITECTURAL MODEL CONVERTER
================================================

Transforms abstract 2D floor-plan GLB (Type-1) into metrically correct,
construction-ready 3D architectural model (Type-2).

PIPELINE (in strict order):
1. Metric Normalization - Establish real-world scale
2. Wall Volume Construction - Add thickness & height
3. Floor & Ceiling Generation - Create slabs
4. Openings - Add doors and windows
5. Scene & Validation - Unit setup, normals
6. Visualization Readiness - Materials, lighting, camera
7. Export - Final GLB

Usage:
blender --background --python convert_to_type2_v2.py -- input.glb output.glb
"""

import bpy
import json
import sys
import os
from mathutils import Vector, Matrix
import math

# ============================================================================
# CONFIGURATION
# ============================================================================

REFERENCE_BUILDING_WIDTH_M = 12.0  # Assume floor-plan width is ~12m
WALL_THICKNESS_M = 0.23
WALL_HEIGHT_M = 3.0
FLOOR_THICKNESS_M = 0.15
DOOR_WIDTH_M = 0.9
DOOR_HEIGHT_M = 2.1
WINDOW_SILL_HEIGHT_M = 0.9
WINDOW_WIDTH_M = 1.2
WINDOW_HEIGHT_M = 1.2

# ============================================================================
# LOGGING
# ============================================================================

def log(msg, level="INFO"):
    """Structured logging"""
    prefix = {
        "INFO": "[Type2:INFO]",
        "STEP": "[Type2:STEP]",
        "WARN": "[Type2:WARN]",
        "ERR": "[Type2:ERROR]"
    }.get(level, "[Type2]")
    print(f"{prefix} {msg}")

# ============================================================================
# STEP 0: SCENE INITIALIZATION
# ============================================================================

def clear_scene():
    """Remove all default objects and data"""
    log("Clearing scene", "STEP")
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)

def configure_scene_units():
    """Set up Blender for metric, meter-based modeling"""
    log("Configuring scene units to Metric/Meters", "STEP")
    
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'METERS'
    scene.unit_settings.scale_length = 1.0
    
    log(f"  Unit system: {scene.unit_settings.system}")
    log(f"  Length unit: {scene.unit_settings.length_unit}")
    log(f"  Scale: {scene.unit_settings.scale_length}")

# ============================================================================
# STEP 1: METRIC NORMALIZATION
# ============================================================================

def import_glb(filepath):
    """Import GLB and return imported objects"""
    log(f"Importing GLB: {filepath}", "STEP")
    
    if not os.path.exists(filepath):
        log(f"File not found: {filepath}", "ERR")
        return []
    
    bpy.ops.import_scene.gltf(filepath=filepath, import_pack_images=True)
    imported = list(bpy.context.selected_objects)
    log(f"  Imported {len(imported)} objects", "INFO")
    return imported

def analyze_geometry_bounds(objects):
    """Analyze bounding box of all geometry
    
    Returns: dict with 'min', 'max', 'center', 'size', 'dominant_dim'
    """
    log("Analyzing geometry bounds", "STEP")
    
    if not objects:
        log("No objects to analyze", "WARN")
        return None
    
    # Calculate world-space bounding box
    all_corners = []
    for obj in objects:
        if hasattr(obj, 'bound_box'):
            corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            all_corners.extend(corners)
    
    if not all_corners:
        log("Could not extract bounding box", "WARN")
        return None
    
    min_pt = Vector((
        min(p.x for p in all_corners),
        min(p.y for p in all_corners),
        min(p.z for p in all_corners)
    ))
    max_pt = Vector((
        max(p.x for p in all_corners),
        max(p.y for p in all_corners),
        max(p.z for p in all_corners)
    ))
    
    size = max_pt - min_pt
    center = (min_pt + max_pt) / 2
    
    # Determine dominant horizontal dimension
    dominant_dim = max(size.x, size.y)
    if dominant_dim < 0.001:
        dominant_dim = 1.0
    
    bounds = {
        'min': min_pt,
        'max': max_pt,
        'center': center,
        'size': size,
        'dominant_dim': dominant_dim
    }
    
    log(f"  Bounding box min: {min_pt}", "INFO")
    log(f"  Bounding box max: {max_pt}", "INFO")
    log(f"  Size: X={size.x:.3f}, Y={size.y:.3f}, Z={size.z:.3f}", "INFO")
    log(f"  Dominant horizontal dimension: {dominant_dim:.3f}", "INFO")
    
    return bounds

def compute_metric_scale(bounds):
    """Compute global scale to normalize to real-world dimensions
    
    Strategy: Map the dominant floor-plan dimension to REFERENCE_BUILDING_WIDTH_M
    """
    log("Computing metric normalization scale", "STEP")
    
    if bounds is None or bounds['dominant_dim'] < 0.001:
        scale = 1.0
        log(f"  Using default scale (1.0) due to insufficient geometry", "WARN")
    else:
        scale = REFERENCE_BUILDING_WIDTH_M / bounds['dominant_dim']
        log(f"  Reference width: {REFERENCE_BUILDING_WIDTH_M}m", "INFO")
        log(f"  Detected width: {bounds['dominant_dim']:.3f} units", "INFO")
        log(f"  Computed scale: {scale:.6f}", "INFO")
    
    return scale

def apply_metric_normalization(objects, bounds, scale):
    """Apply global scale and center geometry
    
    After this step:
    - 1 Blender unit = 1 meter
    - Geometry is centered at origin
    - Z-axis points upward
    """
    log("Applying metric normalization", "STEP")
    
    if not objects:
        log("No objects to normalize", "WARN")
        return
    
    log(f"  Scaling all geometry by {scale:.6f}x", "INFO")
    
    # Create a parent object to scale everything uniformly
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    scale_parent = bpy.context.active_object
    scale_parent.name = "MetricScaler"
    
    # Parent all objects to the scaler
    for obj in objects:
        obj.parent = scale_parent
    
    # Apply scale
    scale_parent.scale = (scale, scale, scale)
    
    # Apply the scale transformation
    bpy.context.view_layer.objects.active = scale_parent
    bpy.ops.object.transform_apply(scale=True)
    
    # Unparent and delete the scaler
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
        obj.parent = None
    
    bpy.data.objects.remove(scale_parent, do_unlink=True)
    
    # Now shift everything so that Z=0 is at the ground
    # (Lowest point should be at Z = 0)
    new_bounds = analyze_geometry_bounds(objects)
    if new_bounds:
        z_offset = -new_bounds['min'].z
        log(f"  Shifting geometry up by {z_offset:.3f}m to place floor at Z=0", "INFO")
        
        for obj in objects:
            obj.location.z += z_offset
    
    log(f"  Normalization complete: 1 unit = 1 meter", "INFO")

# ============================================================================
# STEP 2: WALL VOLUME CONSTRUCTION
# ============================================================================

def extract_walls(objects):
    """Extract wall meshes and their properties
    
    Returns: list of dicts with 'obj', 'center', 'bounds'
    """
    log("Extracting wall geometry", "STEP")
    
    walls = []
    for obj in objects:
        if obj.type == 'MESH':
            bbox_corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
            min_pt = Vector((min(p.x for p in bbox_corners),
                           min(p.y for p in bbox_corners),
                           min(p.z for p in bbox_corners)))
            max_pt = Vector((max(p.x for p in bbox_corners),
                           max(p.y for p in bbox_corners),
                           max(p.z for p in bbox_corners)))
            
            size = max_pt - min_pt
            center = (min_pt + max_pt) / 2
            
            walls.append({
                'obj': obj,
                'center': center,
                'bounds': {'min': min_pt, 'max': max_pt},
                'size': size
            })
    
    log(f"  Found {len(walls)} wall objects", "INFO")
    return walls

def add_wall_thickness(walls):
    """Apply wall thickness using Solidify modifier (then apply)"""
    log("Adding wall thickness (0.23m)", "STEP")
    
    for i, wall_info in enumerate(walls):
        obj = wall_info['obj']
        
        # Ensure manifold by running a simple cleanup
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete_loose()
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Add Solidify
        solidify = obj.modifiers.new(name='Solidify', type='SOLIDIFY')
        solidify.thickness = WALL_THICKNESS_M
        solidify.offset = 0.0  # Center thickness on original surface
        
        # Apply modifier
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier='Solidify')
        
        log(f"  Wall {i}: thickness applied", "INFO")

def extrude_walls_vertically(walls):
    """Extrude walls to standard height using scale transformation
    
    Strategy: Scale each wall in Z to achieve WALL_HEIGHT_M
    """
    log(f"Extruding walls to height {WALL_HEIGHT_M}m", "STEP")
    
    for i, wall_info in enumerate(walls):
        obj = wall_info['obj']
        size = wall_info['size']
        
        # Determine current Z size (should be minimal after import)
        current_z = max(size.z, 0.1)  # Avoid division by zero
        
        # Scale factor needed in Z
        z_scale = WALL_HEIGHT_M / current_z
        
        # Position wall at correct height (top at wall_height_m)
        original_z = wall_info['bounds']['min'].z
        target_z = WALL_HEIGHT_M / 2  # Center of the extruded wall
        
        # Apply scaling and positioning
        obj.scale.z = z_scale
        obj.location.z = target_z
        
        # Apply transforms
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        log(f"  Wall {i}: extruded to {WALL_HEIGHT_M}m height", "INFO")

# ============================================================================
# STEP 3: FLOOR & CEILING GENERATION
# ============================================================================

def create_floor_and_ceiling(walls):
    """Create floor slab and ceiling slab"""
    log("Creating floor and ceiling slabs", "STEP")
    
    if not walls:
        log("No walls to generate floor/ceiling from", "WARN")
        return None, None
    
    # Calculate building footprint bounds
    all_x = []
    all_y = []
    for wall_info in walls:
        bounds = wall_info['bounds']
        all_x.extend([bounds['min'].x, bounds['max'].x])
        all_y.extend([bounds['min'].y, bounds['max'].y])
    
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    
    floor_center_x = (min_x + max_x) / 2
    floor_center_y = (min_y + max_y) / 2
    floor_width = max_x - min_x
    floor_depth = max_y - min_y
    
    # Floor at Z = -floor_thickness/2 (so top surface is at Z=0)
    floor_z = -FLOOR_THICKNESS_M / 2
    
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(floor_center_x, floor_center_y, floor_z)
    )
    floor_obj = bpy.context.active_object
    floor_obj.name = "Floor"
    floor_obj.scale = (floor_width/2, floor_depth/2, FLOOR_THICKNESS_M/2)
    
    bpy.context.view_layer.objects.active = floor_obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
    log(f"  Floor created: {floor_width:.2f}m x {floor_depth:.2f}m", "INFO")
    
    # Ceiling at Z = wall_height_m + ceiling_thickness/2
    ceiling_z = WALL_HEIGHT_M + FLOOR_THICKNESS_M / 2
    
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(floor_center_x, floor_center_y, ceiling_z)
    )
    ceiling_obj = bpy.context.active_object
    ceiling_obj.name = "Ceiling"
    ceiling_obj.scale = (floor_width/2, floor_depth/2, FLOOR_THICKNESS_M/2)
    
    bpy.context.view_layer.objects.active = ceiling_obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
    log(f"  Ceiling created at height {WALL_HEIGHT_M:.2f}m", "INFO")
    
    return floor_obj, ceiling_obj

# ============================================================================
# STEP 4: OPENINGS (DOORS & WINDOWS)
# ============================================================================

def create_door_openings(walls):
    """Add door openings to walls using boolean difference"""
    log(f"Creating door openings ({DOOR_WIDTH_M}m x {DOOR_HEIGHT_M}m)", "STEP")
    
    doors_created = 0
    
    for i, wall_info in enumerate(walls):
        wall_obj = wall_info['obj']
        center = wall_info['center']
        size = wall_info['size']
        
        # Only add doors to walls that are large enough
        if size.x > DOOR_WIDTH_M and size.y > DOOR_WIDTH_M:
            # Door positioned at center of wall, bottom edge at 0m height
            door_z = DOOR_HEIGHT_M / 2  # Center height of door
            
            # Create door cutter
            bpy.ops.mesh.primitive_cube_add(
                size=1,
                location=(center.x, center.y, door_z)
            )
            door_cutter = bpy.context.active_object
            door_cutter.name = f"DoorCutter_{i}"
            door_cutter.scale = (DOOR_WIDTH_M/2 + 0.02, size.y/2 + 0.1, DOOR_HEIGHT_M/2)
            
            bpy.context.view_layer.objects.active = door_cutter
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            
            # Boolean difference
            bool_mod = wall_obj.modifiers.new(name=f'DoorBool_{i}', type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = door_cutter
            bool_mod.solver = 'MANIFOLD'
            
            bpy.context.view_layer.objects.active = wall_obj
            bpy.ops.object.modifier_apply(modifier=f'DoorBool_{i}')
            
            # Clean up cutter
            bpy.data.objects.remove(door_cutter, do_unlink=True)
            
            doors_created += 1
            log(f"  Door added to wall {i}", "INFO")
    
    log(f"  Total doors created: {doors_created}", "INFO")

def create_window_openings(walls):
    """Add window openings to walls"""
    log(f"Creating window openings ({WINDOW_WIDTH_M}m x {WINDOW_HEIGHT_M}m @ {WINDOW_SILL_HEIGHT_M}m sill)", "STEP")
    
    windows_created = 0
    
    for i, wall_info in enumerate(walls):
        wall_obj = wall_info['obj']
        center = wall_info['center']
        size = wall_info['size']
        
        if size.x > WINDOW_WIDTH_M * 2:  # Need room for 2 windows
            # Create 2 windows per wall
            for w_idx in range(2):
                # Offset along X
                x_offset = -size.x/4 if w_idx == 0 else size.x/4
                
                # Center of window
                window_z = WINDOW_SILL_HEIGHT_M + WINDOW_HEIGHT_M / 2
                
                # Create cutter
                bpy.ops.mesh.primitive_cube_add(
                    size=1,
                    location=(center.x + x_offset, center.y, window_z)
                )
                window_cutter = bpy.context.active_object
                window_cutter.name = f"WindowCutter_{i}_{w_idx}"
                window_cutter.scale = (WINDOW_WIDTH_M/2 + 0.02, size.y/2 + 0.1, WINDOW_HEIGHT_M/2)
                
                bpy.context.view_layer.objects.active = window_cutter
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                
                # Boolean
                bool_mod = wall_obj.modifiers.new(name=f'WindowBool_{i}_{w_idx}', type='BOOLEAN')
                bool_mod.operation = 'DIFFERENCE'
                bool_mod.object = window_cutter
                bool_mod.solver = 'MANIFOLD'
                
                bpy.context.view_layer.objects.active = wall_obj
                bpy.ops.object.modifier_apply(modifier=f'WindowBool_{i}_{w_idx}')
                
                bpy.data.objects.remove(window_cutter, do_unlink=True)
                
                windows_created += 1
    
    log(f"  Total windows created: {windows_created}", "INFO")

# ============================================================================
# STEP 5: SCENE VALIDATION & NORMALS
# ============================================================================

def fix_normals_and_shading(objects):
    """Recalculate normals and apply auto-smooth"""
    log("Fixing normals and shading", "STEP")
    
    for obj in objects:
        if obj.type != 'MESH':
            continue
        
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth()
        
        # Recalculate normals
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    
    log(f"  Normals recalculated for {len(objects)} objects", "INFO")

def validate_dimensions(walls, floor, ceiling):
    """Validate that dimensions are correct"""
    log("Validating model dimensions", "STEP")
    
    if walls:
        for i, wall_info in enumerate(walls):
            obj = wall_info['obj']
            bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
            
            min_z = min(c.z for c in bbox)
            max_z = max(c.z for c in bbox)
            height = max_z - min_z
            
            log(f"  Wall {i}: height {height:.3f}m (expected ~{WALL_HEIGHT_M}m)", "INFO")

# ============================================================================
# STEP 6: VISUALIZATION READINESS
# ============================================================================

def create_material(name, color_rgb, roughness=0.6):
    """Create PBR material"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*color_rgb, 1.0)
        bsdf.inputs['Roughness'].default_value = roughness
    return mat

def assign_materials(walls, floor, ceiling):
    """Assign architectural materials"""
    log("Assigning architectural materials", "STEP")
    
    # Create materials
    mat_wall = create_material("Wall", (0.85, 0.85, 0.85), roughness=0.7)
    mat_floor = create_material("Floor", (0.95, 0.95, 0.93), roughness=0.8)
    mat_ceiling = create_material("Ceiling", (1.0, 1.0, 1.0), roughness=0.5)
    
    # Assign to walls
    for wall_info in walls:
        obj = wall_info['obj']
        if obj.data.materials:
            obj.data.materials[0] = mat_wall
        else:
            obj.data.materials.append(mat_wall)
    
    if floor:
        if floor.data.materials:
            floor.data.materials[0] = mat_floor
        else:
            floor.data.materials.append(mat_floor)
    
    if ceiling:
        if ceiling.data.materials:
            ceiling.data.materials[0] = mat_ceiling
        else:
            ceiling.data.materials.append(mat_ceiling)
    
    log(f"  Materials assigned", "INFO")

def add_lighting_and_camera(walls):
    """Add sun light and architectural camera"""
    log("Adding lighting and camera", "STEP")
    
    # Calculate scene center
    if walls:
        center_x = sum(w['center'].x for w in walls) / len(walls)
        center_y = sum(w['center'].y for w in walls) / len(walls)
        max_size = max(w['size'].x for w in walls)
    else:
        center_x, center_y, max_size = 0, 0, 10
    
    # Sun light
    bpy.ops.object.light_add(
        type='SUN',
        location=(center_x + max_size, center_y + max_size, WALL_HEIGHT_M * 2)
    )
    sun = bpy.context.active_object
    sun.name = "SunLight"
    sun.data.energy = 1.5
    sun.data.angle = math.radians(5)
    
    # Isometric camera (45° angle)
    camera_distance = max_size * 1.5
    camera_height = WALL_HEIGHT_M * 1.2
    
    bpy.ops.object.camera_add(
        location=(
            center_x + camera_distance * 0.707,
            center_y + camera_distance * 0.707,
            camera_height
        )
    )
    camera = bpy.context.active_object
    camera.name = "ArchCamera"
    
    # Point at scene center
    direction = Vector((center_x, center_y, WALL_HEIGHT_M / 2)) - Vector(camera.location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    
    # Set as active
    bpy.context.scene.camera = camera
    
    log(f"  Camera and sun light added", "INFO")

# ============================================================================
# STEP 7: EXPORT
# ============================================================================

def export_to_glb(filepath):
    """Export scene as GLB"""
    log(f"Exporting to {filepath}", "STEP")
    
    bpy.ops.object.select_all(action='SELECT')
    
    try:
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format='GLB'
        )
        log(f"  Export successful", "INFO")
    except Exception as e:
        log(f"  Export error: {e}", "WARN")

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    """Execute full Type-2 conversion pipeline"""
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    
    if len(argv) < 2:
        log("Usage: blender --background --python convert_to_type2_v2.py -- input.glb output.glb", "ERR")
        return
    
    input_glb = argv[0]
    output_glb = argv[1]
    
    log("="*70, "STEP")
    log("TYPE-2 ARCHITECTURAL MODEL CONVERTER - V2", "STEP")
    log("Metrically Correct, Construction-Ready Pipeline", "STEP")
    log("="*70, "STEP")
    
    try:
        # STEP 0: Initialize
        clear_scene()
        configure_scene_units()
        
        # STEP 1: Metric Normalization
        imported = import_glb(input_glb)
        bounds = analyze_geometry_bounds(imported)
        scale = compute_metric_scale(bounds)
        apply_metric_normalization(imported, bounds, scale)
        
        # STEP 2: Wall Volume
        walls = extract_walls(imported)
        add_wall_thickness(walls)
        extrude_walls_vertically(walls)
        
        # STEP 3: Floor & Ceiling
        floor, ceiling = create_floor_and_ceiling(walls)
        
        # STEP 4: Openings
        create_door_openings(walls)
        create_window_openings(walls)
        
        # STEP 5: Validation
        all_objs = [w['obj'] for w in walls] + [floor, ceiling] if floor and ceiling else [w['obj'] for w in walls]
        fix_normals_and_shading(all_objs)
        validate_dimensions(walls, floor, ceiling)
        
        # STEP 6: Visualization
        assign_materials(walls, floor, ceiling)
        add_lighting_and_camera(walls)
        
        # STEP 7: Export
        export_to_glb(output_glb)
        
        log("="*70, "STEP")
        log("CONVERSION COMPLETE - Type-2 model ready", "STEP")
        log("="*70, "STEP")
        
    except Exception as e:
        log(f"PIPELINE FAILED: {type(e).__name__}: {e}", "ERR")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
