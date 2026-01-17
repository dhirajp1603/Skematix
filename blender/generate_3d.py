"""
Blender script to create simple wall blocks from detected bounding boxes and export glTF.

Run inside Blender:

blender --background --python blender/generate_3d.py -- input/walls.json output/model.glb

The script reads JSON with structure: {"image": "...", "walls": [{x,y,w,h}, ...]}
and generates a box for each wall bounding box, scaling pixels -> meters via `SCALE`.
"""
import json
import sys
import os

def main(json_in, gltf_out, scale=0.01, wall_height=3.0):
    import bpy
    # Clear existing
    bpy.ops.wm.read_factory_settings(use_empty=True)

    with open(json_in, 'r') as f:
        data = json.load(f)

    walls = data.get('walls', [])

    import math
    def add_prism_from_poly(poly_px, name, scale, height):
        # poly_px: list of [x,y] in pixel coordinates. Create prism extruded along Z
        verts = []
        for x_px, y_px in poly_px:
            # convert pixel -> meters
            vx = x_px * scale
            vy = y_px * scale
            verts.append((vx, vy, 0.0))
        # top verts
        top_offset = len(verts)
        for x_px, y_px in poly_px:
            vx = x_px * scale
            vy = y_px * scale
            verts.append((vx, vy, height))

        faces = []
        n = len(poly_px)
        if n < 3:
            return
        # bottom face (reverse order so normal points down)
        faces.append([i for i in range(n-1, -1, -1)])
        # top face
        faces.append([top_offset + i for i in range(0, n)])
        # side faces
        for i in range(n):
            i2 = (i + 1) % n
            faces.append([i, i2, top_offset + i2, top_offset + i])

        mesh = bpy.data.meshes.new(name + '_mesh')
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        return obj

    for i, w in enumerate(walls):
        # prefer polygon if available
        poly = w.get('poly')
        if poly and len(poly) >= 3:
            obj = add_prism_from_poly(poly, f'wall_{i}', scale, wall_height)
            # apply door boolean cuts if present
            for d in w.get('doors', []):
                # door center and length in pixels
                c = d.get('center_px')
                length_px = d.get('length_px', 50)
                if c is None:
                    continue
                door_w = length_px * scale
                door_h = 2.1  # meters
                # create a cutter cube larger than wall thickness to ensure subtraction
                cutter_name = f'cutter_{i}'
                bpy.ops.mesh.primitive_cube_add(size=1, location=(c[0]*scale, c[1]*scale, door_h/2))
                cutter = bpy.context.active_object
                # set cutter dimensions: X along image X, Y large to span wall, Z = door_h
                cutter.scale = (door_w/2.0, max(1.0, 5.0), door_h/2.0)
                cutter.name = cutter_name
                # boolean modifier
                mod = obj.modifiers.new(name='bool_cut', type='BOOLEAN')
                mod.object = cutter
                mod.operation = 'DIFFERENCE'
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier=mod.name)
                # remove cutter
                bpy.data.objects.remove(cutter, do_unlink=True)
        else:
            # fallback to bbox
            bbox = w.get('bbox') or w
            x = bbox['x']
            y = bbox['y']
            bw = bbox['w']
            bh = bbox['h']
            sx = bw * scale
            sy = bh * scale
            sz = wall_height
            cx = (x + bw / 2.0) * scale
            cy = (y + bh / 2.0) * scale
            bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, sz / 2.0))
            obj = bpy.context.active_object
            obj.scale = (sx / 2.0, sy / 2.0, sz / 2.0)
            obj.name = f'wall_{i}'
            # boolean cut doors for bbox-based walls
            for d in w.get('doors', []):
                c = d.get('center_px')
                length_px = d.get('length_px', 50)
                if c is None:
                    continue
                door_w = length_px * scale
                door_h = 2.1
                bpy.ops.mesh.primitive_cube_add(size=1, location=(c[0]*scale, c[1]*scale, door_h/2))
                cutter = bpy.context.active_object
                cutter.scale = (door_w/2.0, max(1.0, 5.0), door_h/2.0)
                mod = obj.modifiers.new(name='bool_cut', type='BOOLEAN')
                mod.object = cutter
                mod.operation = 'DIFFERENCE'
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier=mod.name)
                bpy.data.objects.remove(cutter, do_unlink=True)

    # Export glTF
    os.makedirs(os.path.dirname(gltf_out), exist_ok=True)
    # Use Draco compression when available to reduce file size
    try:
        bpy.ops.export_scene.gltf(filepath=gltf_out, export_format='GLB', export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=7)
    except Exception:
        # fallback if options not supported
        bpy.ops.export_scene.gltf(filepath=gltf_out, export_format='GLB')


if __name__ == '__main__':
    # Parse args after '--'
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    else:
        argv = argv[1:]
    if len(argv) < 2:
        print('Usage: blender --background --python blender/generate_3d.py -- input.json output.glb')
        sys.exit(1)
    json_in = argv[0]
    gltf_out = argv[1]
    main(json_in, gltf_out)
