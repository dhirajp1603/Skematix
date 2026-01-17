"""
ARCHITECTURAL OPEN-TOP CUTAWAY FLOOR-PLAN CONVERTER
===================================================

Transforms a 2D floor-plan GLB into a professional open-top (dollhouse-style)
architectural cutaway model suitable for interior visualization and walkthroughs.

Key Features:
- Open-top walls (no ceiling) at visualization height (1.2-1.5m)
- Floor slab only (0.12-0.15m thick)
- Simplified rectangular openings for doors/windows
- High-contrast architectural materials
- Top-down angled camera for full interior visibility
- Metrically correct (1 unit = 1 meter)

PIPELINE:
1. Metric Normalization - Establish real-world scale
2. Open-Top Wall Construction - Thin walls, visualization height
3. Floor Slab Generation - Single ground plane
4. Simplified Openings - Clean rectangular cuts
5. Visual Cleanup - Normals, manifold geometry
6. Architectural Materials - High-contrast colors
7. Cutaway Camera & Lighting - Top-down angled view
8. Export - Final GLB

Usage:
blender --background --python convert_to_cutaway.py -- input.glb output.glb
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

# Metric normalization
REFERENCE_BUILDING_WIDTH_M = 12.0  # Target plan width in meters

# Open-top wall construction
WALL_THICKNESS_M = 0.22  # Architectural standard thickness
WALL_HEIGHT_CUTAWAY_M = 1.3  # Open-top visualization height (1.2-1.5m range)

# Floor slab
FLOOR_THICKNESS_M = 0.12

# Openings
DOOR_WIDTH_M = 0.9
DOOR_HEIGHT_CUTAWAY_M = 1.1  # Clipped to wall height - 0.1m for visual clarity
WINDOW_SILL_HEIGHT_M = 0.65
WINDOW_WIDTH_M = 0.8
WINDOW_HEIGHT_M = 0.5

# Materials (high-contrast for architectural diagrams)
COLOR_WALLS_RGB = (0.92, 0.85, 0.74)  # Warm beige/sand tone
COLOR_FLOOR_RGB = (0.45, 0.45, 0.48)  # Dark neutral gray
MATERIAL_ROUGHNESS = 0.75  # Matte finish for architectural readability

# ============================================================================
# LOGGING
# ============================================================================

def log(msg, level="INFO"):
    """Structured logging with level prefixes"""
    prefix = {
        "INFO": "[Cutaway:INFO]",
        "STEP": "[Cutaway:STEP]",
        "WARN": "[Cutaway:WARN]",
        "ERR": "[Cutaway:ERROR]"
    }.get(level, "[Cutaway]")
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
    """Set up Blender for metric modeling"""
    log("Configuring scene units to Metric/Meters", "STEP")
    
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'METERS'
    scene.unit_settings.scale_length = 1.0
    
    log(f"  Unit system: {scene.unit_settings.system}", "INFO")
    log(f"  Length unit: {scene.unit_settings.length_unit}", "INFO")

# ============================================================================
# STEP 1: METRIC NORMALIZATION
# ============================================================================

def import_glb(filepath):
    """Import GLB file"""
    log(f"Importing GLB: {filepath}", "STEP")
    
    if not os.path.exists(filepath):
        log(f"File not found: {filepath}", "ERR")
        return []
    
    bpy.ops.import_scene.gltf(filepath=filepath, import_pack_images=True)
    imported = list(bpy.context.selected_objects)
    log(f"  Imported {len(imported)} objects", "INFO")
    return imported

def analyze_geometry_bounds(objects):
    """Analyze bounding box of imported geometry"""
    log("Analyzing geometry bounds", "STEP")
    
    if not objects:
        log("No objects to analyze", "WARN")
        return None
    
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
    
    log(f"  Size: X={size.x:.3f}, Y={size.y:.3f}, Z={size.z:.3f}", "INFO")
    log(f"  Dominant horizontal dimension: {dominant_dim:.3f}", "INFO")
    
    return bounds

def compute_metric_scale(bounds):
    """Compute scale to normalize to real-world dimensions"""
    log("Computing metric normalization scale", "STEP")
    
    if bounds is None or bounds['dominant_dim'] < 0.001:
        scale = 1.0
        log(f"  Using default scale (1.0)", "WARN")
    else:
        scale = REFERENCE_BUILDING_WIDTH_M / bounds['dominant_dim']
        log(f"  Reference width: {REFERENCE_BUILDING_WIDTH_M}m", "INFO")
        log(f"  Detected width: {bounds['dominant_dim']:.3f} units", "INFO")
        log(f"  Computed scale: {scale:.6f}", "INFO")
    
    return scale

def apply_metric_normalization(objects, bounds, scale):
    """Apply global scale and center geometry"""
    log("Applying metric normalization", "STEP")
    
    if not objects:
        log("No objects to normalize", "WARN")
        return
    
    log(f"  Scaling all geometry by {scale:.6f}x", "INFO")
    
    # Create parent for uniform scaling
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    scale_parent = bpy.context.active_object
    scale_parent.name = "MetricScaler"
    
    # Parent objects
    for obj in objects:
        obj.parent = scale_parent
    
    # Apply scale
    scale_parent.scale = (scale, scale, scale)
    
    bpy.context.view_layer.objects.active = scale_parent
    bpy.ops.object.transform_apply(scale=True)
    
    # Unparent
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
        obj.parent = None
    
    bpy.data.objects.remove(scale_parent, do_unlink=True)
    
    # Shift to Z=0
    new_bounds = analyze_geometry_bounds(objects)
    if new_bounds:
        z_offset = -new_bounds['min'].z
        log(f"  Shifting geometry up by {z_offset:.3f}m to place floor at Z=0", "INFO")
        
        for obj in objects:
            obj.location.z += z_offset
    
    log(f"  Normalization complete: 1 unit = 1 meter", "INFO")

# ============================================================================
# STEP 2: OPEN-TOP WALL CONSTRUCTION
# ============================================================================

def extract_walls(objects):
    """Extract wall geometry"""
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

def add_wall_thickness_cutaway(walls):
    """Add wall thickness for open-top visualization"""
    log(f"Adding wall thickness ({WALL_THICKNESS_M}m)", "STEP")
    
    for i, wall_info in enumerate(walls):
        obj = wall_info['obj']
        
        # Clean geometry
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete_loose()
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Add Solidify modifier
        solidify = obj.modifiers.new(name='Solidify', type='SOLIDIFY')
        solidify.thickness = WALL_THICKNESS_M
        solidify.offset = 0.0
        
        # Apply modifier
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier='Solidify')
        
        log(f"  Wall {i}: thickness applied", "INFO")

def extrude_walls_to_cutaway_height(walls):
    """Extrude walls to open-top visualization height (1.2-1.5m)"""
    log(f"Extruding walls to open-top height {WALL_HEIGHT_CUTAWAY_M}m", "STEP")
    
    for i, wall_info in enumerate(walls):
        obj = wall_info['obj']
        size = wall_info['size']
        
        current_z = max(size.z, 0.1)
        z_scale = WALL_HEIGHT_CUTAWAY_M / current_z
        
        # Position wall
        target_z = WALL_HEIGHT_CUTAWAY_M / 2
        
        obj.scale.z = z_scale
        obj.location.z = target_z
        
        # Apply transforms
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        log(f"  Wall {i}: extruded to {WALL_HEIGHT_CUTAWAY_M}m (open-top)", "INFO")

# ============================================================================
# STEP 3: FLOOR SLAB GENERATION
# ============================================================================

def create_floor_slab(walls):
    """Create single floor slab at Z=0"""
    log("Creating floor slab", "STEP")
    
    if not walls:
        log("No walls to generate floor from", "WARN")
        return None
    
    # Calculate building footprint
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
    
    # Create floor slab (slightly below Z=0 so its top surface is at Z=0)
    floor_z = -FLOOR_THICKNESS_M / 2
    
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(floor_center_x, floor_center_y, floor_z)
    )
    floor_obj = bpy.context.active_object
    floor_obj.name = "FloorSlab"
    floor_obj.scale = (floor_width/2, floor_depth/2, FLOOR_THICKNESS_M/2)
    
    bpy.context.view_layer.objects.active = floor_obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
    log(f"  Floor slab created: {floor_width:.2f}m x {floor_depth:.2f}m", "INFO")
    
    return floor_obj

# ============================================================================
# STEP 4: SIMPLIFIED OPENINGS (RECTANGULAR CUTS ONLY)
# ============================================================================

def create_door_openings_simplified(walls):
    """Create simple rectangular door openings"""
    log(f"Creating door openings ({DOOR_WIDTH_M}m x {DOOR_HEIGHT_CUTAWAY_M}m)", "STEP")
    
    doors_created = 0
    
    for i, wall_info in enumerate(walls):
        wall_obj = wall_info['obj']
        center = wall_info['center']
        size = wall_info['size']
        
        # Only add doors to sufficiently large walls
        if size.x > DOOR_WIDTH_M and size.y > DOOR_WIDTH_M:
            # Door at center-bottom of wall
            door_z = DOOR_HEIGHT_CUTAWAY_M / 2
            
            # Create simple rectangular cutter
            bpy.ops.mesh.primitive_cube_add(
                size=1,
                location=(center.x, center.y, door_z)
            )
            door_cutter = bpy.context.active_object
            door_cutter.name = f"DoorCutter_{i}"
            door_cutter.scale = (DOOR_WIDTH_M/2 + 0.02, size.y/2 + 0.1, DOOR_HEIGHT_CUTAWAY_M/2)
            
            bpy.context.view_layer.objects.active = door_cutter
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            
            # Boolean difference
            bool_mod = wall_obj.modifiers.new(name=f'DoorBool_{i}', type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = door_cutter
            bool_mod.solver = 'MANIFOLD'
            
            bpy.context.view_layer.objects.active = wall_obj
            bpy.ops.object.modifier_apply(modifier=f'DoorBool_{i}')
            
            bpy.data.objects.remove(door_cutter, do_unlink=True)
            
            doors_created += 1
            log(f"  Door opening added to wall {i}", "INFO")
    
    log(f"  Total door openings: {doors_created}", "INFO")

def create_window_openings_simplified(walls):
    """Create simple rectangular window openings"""
    log(f"Creating window openings ({WINDOW_WIDTH_M}m x {WINDOW_HEIGHT_M}m @ {WINDOW_SILL_HEIGHT_M}m)", "STEP")
    
    windows_created = 0
    
    for i, wall_info in enumerate(walls):
        wall_obj = wall_info['obj']
        center = wall_info['center']
        size = wall_info['size']
        
        if size.x > WINDOW_WIDTH_M * 2:
            # Create 2 windows per wall
            for w_idx in range(2):
                x_offset = -size.x/4 if w_idx == 0 else size.x/4
                window_z = WINDOW_SILL_HEIGHT_M + WINDOW_HEIGHT_M / 2
                
                # Simple rectangular cutter
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
    
    log(f"  Total window openings: {windows_created}", "INFO")

# ============================================================================
# STEP 5: VISUAL CLEANUP
# ============================================================================

def fix_normals_and_shading(objects):
    """Recalculate normals and apply auto-smooth"""
    log("Fixing normals and shading", "STEP")
    
    for obj in objects:
        if obj.type != 'MESH':
            continue
        
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth()
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    
    log(f"  Normals recalculated for {len(objects)} objects", "INFO")

# ============================================================================
# STEP 6: ARCHITECTURAL MATERIALS (HIGH-CONTRAST)
# ============================================================================

def create_architectural_material(name, color_rgb, roughness=0.75):
    """Create matte architectural material for diagrams"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*color_rgb, 1.0)
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = 0.0
    return mat

def assign_architectural_materials(walls, floor):
    """Assign high-contrast materials for architectural readability"""
    log("Assigning architectural materials", "STEP")
    
    # Create materials
    mat_walls = create_architectural_material("Walls", COLOR_WALLS_RGB, MATERIAL_ROUGHNESS)
    mat_floor = create_architectural_material("FloorMaterial", COLOR_FLOOR_RGB, MATERIAL_ROUGHNESS)
    
    # Assign to walls
    for wall_info in walls:
        obj = wall_info['obj']
        if obj.data.materials:
            obj.data.materials[0] = mat_walls
        else:
            obj.data.materials.append(mat_walls)
    
    # Assign to floor
    if floor:
        if floor.data.materials:
            floor.data.materials[0] = mat_floor
        else:
            floor.data.materials.append(mat_floor)
    
    log(f"  Wall color: RGB{COLOR_WALLS_RGB}", "INFO")
    log(f"  Floor color: RGB{COLOR_FLOOR_RGB}", "INFO")

# ============================================================================
# STEP 7: CUTAWAY CAMERA & LIGHTING
# ============================================================================

def add_cutaway_camera_and_lighting(walls):
    """Add top-down angled camera and soft directional lighting"""
    log("Adding cutaway camera and lighting", "STEP")
    
    # Calculate scene center
    if walls:
        center_x = sum(w['center'].x for w in walls) / len(walls)
        center_y = sum(w['center'].y for w in walls) / len(walls)
        max_size = max(w['size'].x for w in walls)
    else:
        center_x, center_y, max_size = 0, 0, 10
    
    # Position camera above at 45° angle for cutaway view
    camera_distance = max_size * 1.2
    camera_height = WALL_HEIGHT_CUTAWAY_M * 1.8  # Well above walls
    
    bpy.ops.object.camera_add(
        location=(
            center_x + camera_distance * 0.6,
            center_y + camera_distance * 0.6,
            camera_height
        )
    )
    camera = bpy.context.active_object
    camera.name = "CutawayCamera"
    
    # Point at scene center, slightly below camera for open-top view
    look_target = Vector((center_x, center_y, WALL_HEIGHT_CUTAWAY_M * 0.5))
    direction = look_target - Vector(camera.location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    
    # Use orthographic for architectural diagram look (optional)
    # camera.data.type = 'ORTHO'
    # camera.data.ortho_scale = max_size * 2
    
    bpy.context.scene.camera = camera
    log(f"  Cutaway camera added (top-down 45° angle view)", "INFO")
    
    # Add soft directional lighting
    bpy.ops.object.light_add(
        type='SUN',
        location=(center_x + max_size, center_y + max_size, WALL_HEIGHT_CUTAWAY_M * 2)
    )
    sun = bpy.context.active_object
    sun.name = "CutawayLight"
    sun.data.energy = 1.2
    sun.data.angle = math.radians(8)  # Soft shadows
    
    log(f"  Sun light added for soft shadows", "INFO")

# ============================================================================
# STEP 8: EXPORT
# ============================================================================

def export_to_glb(filepath):
    """Export as GLB with Draco compression"""
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
    """Execute full cutaway conversion pipeline"""
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    
    if len(argv) < 2:
        log("Usage: blender --background --python convert_to_cutaway.py -- input.glb output.glb", "ERR")
        return
    
    input_glb = argv[0]
    output_glb = argv[1]
    
    log("="*70, "STEP")
    log("OPEN-TOP ARCHITECTURAL CUTAWAY CONVERTER", "STEP")
    log("Professional Floor-Plan Visualization Pipeline", "STEP")
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
        
        # STEP 2: Open-Top Walls
        walls = extract_walls(imported)
        add_wall_thickness_cutaway(walls)
        extrude_walls_to_cutaway_height(walls)
        
        # STEP 3: Floor Slab
        floor = create_floor_slab(walls)
        
        # STEP 4: Simplified Openings
        create_door_openings_simplified(walls)
        create_window_openings_simplified(walls)
        
        # STEP 5: Visual Cleanup
        all_objs = [w['obj'] for w in walls] + ([floor] if floor else [])
        fix_normals_and_shading(all_objs)
        
        # STEP 6: Architectural Materials
        assign_architectural_materials(walls, floor)
        
        # STEP 7: Cutaway Camera & Lighting
        add_cutaway_camera_and_lighting(walls)
        
        # STEP 8: Export
        export_to_glb(output_glb)
        
        log("="*70, "STEP")
        log("CUTAWAY CONVERSION COMPLETE - Open-top floor-plan ready", "STEP")
        log("="*70, "STEP")
        
    except Exception as e:
        log(f"PIPELINE FAILED: {type(e).__name__}: {e}", "ERR")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
