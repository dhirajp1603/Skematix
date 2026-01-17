"""
Type-1 to Type-2 Architectural Model Converter

Transforms a basic box-based GLB model (Type-1) into a construction-ready
architectural model (Type-2) with:
- Wall thickness & height
- Floor & ceiling slabs
- Door & window openings
- Materials & lighting
- Camera for visualization

Usage:
blender --background --python convert_to_type2.py -- input_type1.glb output_type2.glb [--walls-file walls.json]
"""

import bpy
import json
import sys
import os
from mathutils import Vector, Matrix
import math

def log(msg):
    """Print with timestamp for debugging"""
    print(f"[Type2Conv] {msg}")

def clear_scene():
    """Remove all default objects"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)

def import_glb(filepath):
    """Import GLB file"""
    log(f"Importing GLB: {filepath}")
    if not os.path.exists(filepath):
        log(f"ERROR: File not found: {filepath}")
        return []
    
    bpy.ops.import_scene.gltf(filepath=filepath, import_pack_images=True)
    imported = [obj for obj in bpy.context.selected_objects]
    log(f"Imported {len(imported)} objects")
    return imported

def get_walls_from_objects(objects):
    """Extract wall geometry from imported objects
    
    Returns: list of dicts with keys 'obj', 'center', 'bounds'
    """
    walls = []
    for obj in objects:
        if obj.type == 'MESH':
            # Get bounding box
            bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            
            # Calculate center and size
            min_pt = Vector((min(p.x for p in bbox_corners),
                           min(p.y for p in bbox_corners),
                           min(p.z for p in bbox_corners)))
            max_pt = Vector((max(p.x for p in bbox_corners),
                           max(p.y for p in bbox_corners),
                           max(p.z for p in bbox_corners)))
            
            center = (min_pt + max_pt) / 2
            size = max_pt - min_pt
            
            walls.append({
                'obj': obj,
                'center': center,
                'bounds': {'min': min_pt, 'max': max_pt},
                'size': size
            })
    
    log(f"Found {len(walls)} wall objects")
    return walls

def create_material(name, color_rgb, roughness=0.6, metallic=0.0):
    """Create a basic material with PBR properties
    
    Args:
        name: Material name
        color_rgb: Tuple (r, g, b) in 0-1 range
        roughness: 0-1
        metallic: 0-1
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs['Base Color'].default_value = (*color_rgb, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    
    return mat

def apply_wall_thickness(walls_data, wall_thickness=0.23):
    """Apply thickness to wall objects using Solidify modifier
    
    Args:
        walls_data: List of wall dicts from get_walls_from_objects
        wall_thickness: Wall thickness in meters
    """
    log(f"Applying wall thickness: {wall_thickness}m")
    
    for wall_info in walls_data:
        obj = wall_info['obj']
        
        # Add Solidify modifier for thickness
        solidify = obj.modifiers.new(name='Solidify', type='SOLIDIFY')
        solidify.thickness = wall_thickness
        solidify.offset = 0  # Center the thickness
        
        # Apply modifier
        with bpy.context.temp_override(object=obj):
            bpy.ops.object.modifier_apply(modifier='Solidify')
        
        log(f"Applied thickness to {obj.name}")

def create_floor_and_ceiling(walls_data, wall_height=3.0, floor_thickness=0.15, scale_m_per_px=0.01):
    """Create floor and ceiling slabs
    
    Args:
        walls_data: Wall objects list
        wall_height: Height of walls in meters
        floor_thickness: Floor slab thickness
        scale_m_per_px: Conversion factor from pixel to meters
    """
    log(f"Creating floor and ceiling (height: {wall_height}m)")
    
    if not walls_data:
        log("WARNING: No walls to create floor/ceiling from")
        return None, None
    
    # Get overall bounding box of all walls
    all_min = Vector((float('inf'), float('inf'), float('inf')))
    all_max = Vector((float('-inf'), float('-inf'), float('-inf')))
    
    for wall_info in walls_data:
        bounds = wall_info['bounds']
        all_min.x = min(all_min.x, bounds['min'].x)
        all_min.y = min(all_min.y, bounds['min'].y)
        all_min.z = min(all_min.z, bounds['min'].z)
        
        all_max.x = max(all_max.x, bounds['max'].x)
        all_max.y = max(all_max.y, bounds['max'].y)
        all_max.z = max(all_max.z, bounds['max'].z)
    
    # Floor slab at Z=0
    floor_size = (all_max.x - all_min.x, all_max.y - all_min.y, floor_thickness)
    floor_center = Vector((
        (all_min.x + all_max.x) / 2,
        (all_min.y + all_max.y) / 2,
        -floor_thickness / 2
    ))
    
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=floor_center
    )
    floor_obj = bpy.context.active_object
    floor_obj.name = "Floor"
    floor_obj.scale = (floor_size[0]/2, floor_size[1]/2, floor_size[2]/2)
    
    # Ceiling slab
    ceiling_z = all_max.z + wall_height / 2
    ceiling_center = Vector((
        (all_min.x + all_max.x) / 2,
        (all_min.y + all_max.y) / 2,
        ceiling_z
    ))
    
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=ceiling_center
    )
    ceiling_obj = bpy.context.active_object
    ceiling_obj.name = "Ceiling"
    ceiling_obj.scale = (floor_size[0]/2, floor_size[1]/2, floor_thickness/2)
    
    log(f"Created floor and ceiling")
    return floor_obj, ceiling_obj

def create_door_openings(walls_data, door_width=0.9, door_height=2.1):
    """Create door openings using boolean operations
    
    Args:
        walls_data: Wall objects
        door_width: Standard door width in meters
        door_height: Standard door height in meters
    """
    log(f"Creating door openings (W:{door_width}m x H:{door_height}m)")
    
    # For each wall, create one door opening at center bottom
    for i, wall_info in enumerate(walls_data):
        wall_obj = wall_info['obj']
        center = wall_info['center']
        size = wall_info['size']
        
        # Check if wall is large enough for a door
        if size.x > door_width and size.y > door_width:
            # Determine door location (center of wall, bottom)
            door_center = Vector((
                center.x,
                center.y,
                center.z - (size.z / 2) + (door_height / 2)  # Align to bottom
            ))
            
            # Create door cutter (slightly oversized to ensure clean cut)
            bpy.ops.mesh.primitive_cube_add(
                size=1,
                location=door_center
            )
            door_cutter = bpy.context.active_object
            door_cutter.name = f"DoorCutter_{i}"
            door_cutter.scale = (door_width/2 + 0.01, size.y/2 + 0.1, door_height/2)
            
            # Apply boolean difference
            bool_mod = wall_obj.modifiers.new(name=f'BoolDoor_{i}', type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = door_cutter
            bool_mod.solver = 'FAST'
            
            # Apply modifier
            with bpy.context.temp_override(object=wall_obj):
                bpy.ops.object.modifier_apply(modifier=f'BoolDoor_{i}')
            
            # Remove cutter
            bpy.data.objects.remove(door_cutter, do_unlink=True)
            
            log(f"Added door opening to {wall_obj.name}")

def create_window_openings(walls_data, window_width=1.2, window_height=1.2, sill_height=0.9):
    """Create window openings using boolean operations
    
    Args:
        walls_data: Wall objects
        window_width: Window width in meters
        window_height: Window height in meters
        sill_height: Height from floor to window sill
    """
    log(f"Creating window openings (W:{window_width}m x H:{window_height}m @ {sill_height}m sill)")
    
    for i, wall_info in enumerate(walls_data):
        wall_obj = wall_info['obj']
        center = wall_info['center']
        size = wall_info['size']
        
        # Check if wall is large enough for windows
        if size.x > window_width and size.y > window_width:
            # Create 2 window openings per wall
            for w_idx in range(2):
                offset = -size.x/4 if w_idx == 0 else size.x/4
                
                window_center = Vector((
                    center.x + offset,
                    center.y,
                    center.z - (size.z / 2) + sill_height + (window_height / 2)
                ))
                
                # Create window cutter
                bpy.ops.mesh.primitive_cube_add(
                    size=1,
                    location=window_center
                )
                window_cutter = bpy.context.active_object
                window_cutter.name = f"WindowCutter_{i}_{w_idx}"
                window_cutter.scale = (window_width/2 + 0.01, size.y/2 + 0.1, window_height/2)
                
                # Apply boolean
                bool_mod = wall_obj.modifiers.new(name=f'BoolWindow_{i}_{w_idx}', type='BOOLEAN')
                bool_mod.operation = 'DIFFERENCE'
                bool_mod.object = window_cutter
                bool_mod.solver = 'FAST'
                
                with bpy.context.temp_override(object=wall_obj):
                    bpy.ops.object.modifier_apply(modifier=f'BoolWindow_{i}_{w_idx}')
                
                bpy.data.objects.remove(window_cutter, do_unlink=True)
            
            log(f"Added {2} window openings to {wall_obj.name}")

def assign_materials(walls, floor, ceiling):
    """Assign architectural materials to objects"""
    log("Assigning materials")
    
    # Create materials
    mat_wall = create_material("Wall", (0.85, 0.85, 0.85), roughness=0.7)  # Light gray
    mat_floor = create_material("Floor", (0.95, 0.95, 0.93), roughness=0.8)  # Off-white
    mat_ceiling = create_material("Ceiling", (1.0, 1.0, 1.0), roughness=0.5)  # Pure white
    
    # Assign to walls
    for wall_info in walls:
        wall_obj = wall_info['obj']
        if not wall_obj.data.materials:
            wall_obj.data.materials.append(mat_wall)
        else:
            wall_obj.data.materials[0] = mat_wall
    
    # Assign to floor
    if floor:
        if not floor.data.materials:
            floor.data.materials.append(mat_floor)
        else:
            floor.data.materials[0] = mat_floor
    
    # Assign to ceiling
    if ceiling:
        if not ceiling.data.materials:
            ceiling.data.materials.append(mat_ceiling)
        else:
            ceiling.data.materials[0] = mat_ceiling
    
    log("Materials assigned")

def add_lighting_and_camera(walls_data, wall_height=3.0):
    """Add sun light and isometric camera for architectural visualization"""
    log("Adding lighting and camera")
    
    # Calculate scene bounds
    if walls_data:
        center_x = sum(w['center'].x for w in walls_data) / len(walls_data)
        center_y = sum(w['center'].y for w in walls_data) / len(walls_data)
        max_size = max(w['size'].x for w in walls_data)
    else:
        center_x, center_y, max_size = 0, 0, 10
    
    # Add sun light (soft shadows)
    bpy.ops.object.light_add(type='SUN', location=(center_x + max_size, center_y + max_size, wall_height * 2))
    sun = bpy.context.active_object
    sun.name = "SunLight"
    sun.data.energy = 1.5
    sun.data.angle = math.radians(5)  # Soft shadows
    
    # Add isometric camera (45° angle, elevated)
    camera_distance = max_size * 1.5
    camera_height = wall_height * 1.5
    
    bpy.ops.object.camera_add(
        location=(
            center_x + camera_distance * 0.707,
            center_y + camera_distance * 0.707,
            camera_height
        )
    )
    camera = bpy.context.active_object
    camera.name = "ArchCamera"
    
    # Point camera at scene center
    direction = Vector((center_x, center_y, wall_height / 2)) - Vector(camera.location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    
    # Set as active camera
    bpy.context.scene.camera = camera
    
    log("Camera and lighting added")

def apply_transforms(objects):
    """Apply all transforms to ensure clean geometry"""
    log("Applying transforms")
    for obj in objects:
        if obj.type == 'MESH':
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

def set_scene_properties():
    """Configure scene for architectural rendering"""
    log("Configuring scene properties")
    
    scene = bpy.context.scene
    
    # Set units to meters
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'METERS'
    
    # Viewport settings
    scene.display.render_aa = '8'
    try:
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = 'OPTIX' if bpy.app.build_options.cuda else 'OPENIMAGEDENOISE'
    except:
        pass  # Denoising not available
    
    # Use Cycles for better rendering
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 256
    scene.cycles.use_adaptive_sampling = True

def export_glb(filepath):
    """Export scene as GLB with Draco compression"""
    log(f"Exporting to: {filepath}")
    
    # Select all objects
    bpy.ops.object.select_all(action='SELECT')
    
    # Export with correct parameters for Blender 5.0
    try:
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            use_draco_mesh_compression=True,
            draco_mesh_compression_level=7,
            export_format='GLB',
            export_image_format='AUTO',
            export_materials=True,
            export_lights=True,
            export_cameras=True
        )
    except TypeError:
        # Fallback with simpler parameters
        log("Using simplified export parameters")
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format='GLB'
        )
    
    log(f"Export complete: {filepath}")

def main():
    """Main conversion pipeline"""
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    
    if len(argv) < 2:
        log("Usage: blender --background --python convert_to_type2.py -- input.glb output.glb [--walls-file walls.json]")
        return
    
    input_glb = argv[0]
    output_glb = argv[1]
    
    log(f"="*60)
    log("TYPE-1 TO TYPE-2 ARCHITECTURAL MODEL CONVERTER")
    log(f"="*60)
    
    try:
        # Clear scene
        clear_scene()
        
        # Set scene properties
        set_scene_properties()
        
        # Import Type-1 model
        imported_objs = import_glb(input_glb)
        if not imported_objs:
            log("ERROR: No objects imported")
            return
        
        # Extract walls
        walls_data = get_walls_from_objects(imported_objs)
        if not walls_data:
            log("ERROR: No walls found")
            return
        
        # Apply wall thickness
        apply_wall_thickness(walls_data, wall_thickness=0.23)
        
        # Create floor and ceiling
        floor_obj, ceiling_obj = create_floor_and_ceiling(walls_data, wall_height=3.0)
        
        # Create openings
        create_door_openings(walls_data, door_width=0.9, door_height=2.1)
        create_window_openings(walls_data, window_width=1.2, window_height=1.2, sill_height=0.9)
        
        # Apply materials
        assign_materials(walls_data, floor_obj, ceiling_obj)
        
        # Add lighting and camera
        add_lighting_and_camera(walls_data, wall_height=3.0)
        
        # Apply transforms
        all_objs = [w['obj'] for w in walls_data]
        if floor_obj:
            all_objs.append(floor_obj)
        if ceiling_obj:
            all_objs.append(ceiling_obj)
        apply_transforms(all_objs)
        
        # Export
        export_glb(output_glb)
        
        log(f"="*60)
        log("CONVERSION SUCCESSFUL")
        log(f"="*60)
        
    except Exception as e:
        log(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
