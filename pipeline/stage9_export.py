"""
GLB EXPORT MODULE
Stage 9: Export to GLB Format

Purpose: Export validated 3D model to industry-standard GLB 2.0 format.

Requirements:
- Correct real-world scale (1 Blender unit = 1 meter)
- Open-top interior visible
- Usable in Blender / Three.js without adjustment
- Optional Draco compression for web delivery
- Proper material/color information

GLB Format:
- glTF 2.0 with embedded assets (textures, buffers)
- Single file with .glb extension
- Binary format (most compact)
- Supports PBR materials

Export includes:
- Mesh geometry (vertices, faces, normals)
- Material definitions (colors per specification)
- Metadata (scale factor, dimensions)
"""

import json
import struct
import numpy as np
from typing import Optional, Dict, Tuple, List
import logging
import os

log = logging.getLogger(__name__)

# ============================================================================
# GLB/GLTF CONSTANTS
# ============================================================================

# GLTF 2.0 magic number and format version
GLTF_MAGIC = 0x46546C67  # "glTF"
GLTF_VERSION = 2

# Buffer view targets
ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963

# Component types
FLOAT = 5126
UNSIGNED_INT = 5125
UNSIGNED_SHORT = 5123

# Material colors (per architectural specification)
COLORS = {
    'wall': [0.92, 0.85, 0.74],    # Warm beige (RGB)
    'floor': [0.45, 0.45, 0.48],   # Neutral gray
    'door_frame': [0.3, 0.3, 0.3], # Dark gray
    'window_frame': [0.6, 0.7, 0.8] # Light blue
}


# ============================================================================
# GLTF STRUCTURE BUILDERS
# ============================================================================

class GLTFAccessor:
    """Represents a GLTF accessor (array of data)"""
    
    def __init__(self, 
                 buffer_view_idx: int,
                 component_type: int,
                 count: int,
                 type_str: str,
                 min_values: Optional[List[float]] = None,
                 max_values: Optional[List[float]] = None):
        """
        Args:
            buffer_view_idx: index into bufferViews array
            component_type: FLOAT, UNSIGNED_INT, etc.
            count: number of elements
            type_str: "SCALAR", "VEC2", "VEC3", "MAT4", etc.
            min_values: per-component minimum values
            max_values: per-component maximum values
        """
        self.bufferView = buffer_view_idx
        self.componentType = component_type
        self.count = count
        self.type = type_str
        self.min = min_values
        self.max = max_values
    
    def to_dict(self) -> Dict:
        """Convert to GLTF JSON"""
        d = {
            'bufferView': self.bufferView,
            'componentType': self.componentType,
            'count': self.count,
            'type': self.type
        }
        if self.min is not None:
            d['min'] = self.min
        if self.max is not None:
            d['max'] = self.max
        return d


class GLTFBufferView:
    """Represents a GLTF bufferView (subset of buffer)"""
    
    def __init__(self, 
                 buffer_idx: int,
                 byte_offset: int,
                 byte_length: int,
                 target: int = ARRAY_BUFFER,
                 byte_stride: Optional[int] = None):
        self.buffer = buffer_idx
        self.byteOffset = byte_offset
        self.byteLength = byte_length
        self.target = target
        self.byteStride = byte_stride
    
    def to_dict(self) -> Dict:
        d = {
            'buffer': self.buffer,
            'byteOffset': self.byteOffset,
            'byteLength': self.byteLength,
            'target': self.target
        }
        if self.byteStride is not None:
            d['byteStride'] = self.byteStride
        return d


class GLTFMaterial:
    """Represents a GLTF material"""
    
    def __init__(self, name: str, color: List[float]):
        """
        Args:
            name: material name
            color: [R, G, B] in 0-1 range
        """
        self.name = name
        self.color = color
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'pbrMetallicRoughness': {
                'baseColorFactor': self.color + [1.0],  # RGBA
                'metallicFactor': 0.0,
                'roughnessFactor': 0.5
            }
        }


class GLTFPrimitive:
    """Represents a mesh primitive"""
    
    def __init__(self, 
                 indices_accessor_idx: int,
                 position_accessor_idx: int,
                 normal_accessor_idx: int,
                 material_idx: Optional[int] = None):
        self.attributes = {
            'POSITION': position_accessor_idx,
            'NORMAL': normal_accessor_idx
        }
        self.indices = indices_accessor_idx
        self.material = material_idx
        self.mode = 4  # TRIANGLES
    
    def to_dict(self) -> Dict:
        d = {
            'attributes': self.attributes,
            'indices': self.indices,
            'mode': self.mode
        }
        if self.material is not None:
            d['material'] = self.material
        return d


class GLTFMesh:
    """Represents a GLTF mesh"""
    
    def __init__(self, name: str, primitives: List[GLTFPrimitive]):
        self.name = name
        self.primitives = primitives
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'primitives': [p.to_dict() for p in self.primitives]
        }


class GLTFNode:
    """Represents a GLTF node"""
    
    def __init__(self, name: str, mesh_idx: Optional[int] = None):
        self.name = name
        self.mesh = mesh_idx
    
    def to_dict(self) -> Dict:
        d = {'name': self.name}
        if self.mesh is not None:
            d['mesh'] = self.mesh
        return d


# ============================================================================
# GLB EXPORTER
# ============================================================================

class GLBExporter:
    """Export 3D mesh to GLB format"""
    
    def __init__(self, mesh, metadata: Optional[Dict] = None):
        """
        Args:
            mesh: Mesh object from stage 6/7
            metadata: optional metadata dict
        """
        self.mesh = mesh
        self.metadata = metadata or {}
        
        # GLTF structure
        self.buffer_data = bytearray()
        self.buffer_views: List[GLTFBufferView] = []
        self.accessors: List[GLTFAccessor] = []
        self.materials: List[GLTFMaterial] = []
        self.primitives: List[GLTFPrimitive] = []
        self.meshes: List[GLTFMesh] = []
        self.nodes: List[GLTFNode] = []
    
    def export(self, output_path: str) -> bool:
        """
        Export mesh to GLB file.
        
        Args:
            output_path: path to output .glb file
        
        Returns:
            success
        """
        
        log.info(f"[GLBExporter] Exporting to {output_path}")
        
        try:
            # Step 1: Prepare materials
            self._prepare_materials()
            
            # Step 2: Prepare geometry
            self._prepare_geometry()
            
            # Step 3: Build GLTF JSON
            gltf_dict = self._build_gltf_dict()
            
            # Step 4: Create GLB file
            success = self._write_glb_file(output_path, gltf_dict)
            
            if success:
                log.info(f"[GLBExporter] ✓ Export complete: {output_path}")
            else:
                log.error("[GLBExporter] Export failed")
            
            return success
        
        except Exception as e:
            log.error(f"[GLBExporter] Exception: {e}")
            return False
    
    def _prepare_materials(self):
        """Create material definitions"""
        
        log.info("[GLBExporter] Preparing materials")
        
        # Wall material
        wall_mat = GLTFMaterial("Wall", COLORS['wall'])
        self.materials.append(wall_mat)
        
        # Floor material
        floor_mat = GLTFMaterial("Floor", COLORS['floor'])
        self.materials.append(floor_mat)
    
    def _prepare_geometry(self):
        """Prepare mesh geometry for export"""
        
        log.info("[GLBExporter] Preparing geometry")
        
        if not self.mesh.vertices or not self.mesh.faces:
            log.error("[GLBExporter] Mesh has no geometry")
            return
        
        # Extract positions (VEC3 floats)
        positions = np.array([v.position for v in self.mesh.vertices], dtype=np.float32)
        
        # Extract normals (VEC3 floats)
        normals = np.array([v.normal for v in self.mesh.vertices], dtype=np.float32)
        
        # Extract indices (UNSIGNED_INT)
        indices_list = []
        for face in self.mesh.faces:
            indices_list.extend(face.vertex_indices)
        indices = np.array(indices_list, dtype=np.uint32)
        
        # Add position data to buffer
        pos_byte_offset = len(self.buffer_data)
        pos_bytes = positions.tobytes()
        self.buffer_data.extend(pos_bytes)
        
        pos_accessor = GLTFAccessor(
            buffer_view_idx=len(self.buffer_views),
            component_type=FLOAT,
            count=len(positions),
            type_str="VEC3",
            min_values=positions.min(axis=0).tolist(),
            max_values=positions.max(axis=0).tolist()
        )
        self.accessors.append(pos_accessor)
        
        pos_buffer_view = GLTFBufferView(
            buffer_idx=0,
            byte_offset=pos_byte_offset,
            byte_length=len(pos_bytes),
            target=ARRAY_BUFFER
        )
        self.buffer_views.append(pos_buffer_view)
        
        # Add normal data to buffer
        norm_byte_offset = len(self.buffer_data)
        norm_bytes = normals.tobytes()
        self.buffer_data.extend(norm_bytes)
        
        norm_accessor = GLTFAccessor(
            buffer_view_idx=len(self.buffer_views),
            component_type=FLOAT,
            count=len(normals),
            type_str="VEC3"
        )
        self.accessors.append(norm_accessor)
        
        norm_buffer_view = GLTFBufferView(
            buffer_idx=0,
            byte_offset=norm_byte_offset,
            byte_length=len(norm_bytes),
            target=ARRAY_BUFFER
        )
        self.buffer_views.append(norm_buffer_view)
        
        # Add index data to buffer
        idx_byte_offset = len(self.buffer_data)
        idx_bytes = indices.tobytes()
        self.buffer_data.extend(idx_bytes)
        
        idx_accessor = GLTFAccessor(
            buffer_view_idx=len(self.buffer_views),
            component_type=UNSIGNED_INT,
            count=len(indices),
            type_str="SCALAR"
        )
        self.accessors.append(idx_accessor)
        
        idx_buffer_view = GLTFBufferView(
            buffer_idx=0,
            byte_offset=idx_byte_offset,
            byte_length=len(idx_bytes),
            target=ELEMENT_ARRAY_BUFFER
        )
        self.buffer_views.append(idx_buffer_view)
        
        # Create primitive
        # Use first material by default
        primitive = GLTFPrimitive(
            indices_accessor_idx=len(self.accessors) - 1,
            position_accessor_idx=0,
            normal_accessor_idx=1,
            material_idx=0 if len(self.materials) > 0 else None
        )
        self.primitives.append(primitive)
        
        # Create mesh
        mesh_obj = GLTFMesh(
            name=self.mesh.name or "mesh",
            primitives=[primitive]
        )
        self.meshes.append(mesh_obj)
        
        # Create node
        node = GLTFNode(name="root", mesh_idx=0)
        self.nodes.append(node)
        
        log.info(f"[GLBExporter] Prepared {len(positions)} vertices, "
                f"{len(indices)} indices")
    
    def _build_gltf_dict(self) -> Dict:
        """Build GLTF JSON structure"""
        
        log.info("[GLBExporter] Building GLTF structure")
        
        gltf = {
            'asset': {
                'version': '2.0',
                'generator': 'Skematix Blueprint-to-3D Pipeline'
            },
            'scene': 0,
            'scenes': [
                {'nodes': [0]}
            ],
            'nodes': [n.to_dict() for n in self.nodes],
            'meshes': [m.to_dict() for m in self.meshes],
            'materials': [m.to_dict() for m in self.materials],
            'accessors': [a.to_dict() for a in self.accessors],
            'bufferViews': [bv.to_dict() for bv in self.buffer_views],
            'buffers': [
                {
                    'byteLength': len(self.buffer_data)
                }
            ]
        }
        
        # Add metadata extensions if available
        if self.metadata:
            gltf['extensions'] = {
                'Skematix': self.metadata
            }
        
        return gltf
    
    def _write_glb_file(self, output_path: str, gltf_dict: Dict) -> bool:
        """Write GLB file to disk"""
        
        log.info("[GLBExporter] Writing GLB file")
        
        # Convert GLTF to JSON
        gltf_json = json.dumps(gltf_dict)
        gltf_json_bytes = gltf_json.encode('utf-8')
        
        # Pad JSON to 4-byte boundary
        json_padding = (4 - (len(gltf_json_bytes) % 4)) % 4
        gltf_json_bytes += b'\x20' * json_padding
        
        # Create file chunks
        # JSON chunk
        json_chunk_type = 0x4E4F534A  # "JSON"
        json_chunk_data = gltf_json_bytes
        json_chunk = struct.pack('<II', len(json_chunk_data), json_chunk_type) + json_chunk_data
        
        # Binary chunk (geometry)
        bin_chunk_type = 0x004E4942  # "BIN\x00"
        bin_chunk_data = bytes(self.buffer_data)
        
        # Pad binary to 4-byte boundary
        bin_padding = (4 - (len(bin_chunk_data) % 4)) % 4
        bin_chunk_data += b'\x00' * bin_padding
        
        bin_chunk = struct.pack('<II', len(bin_chunk_data), bin_chunk_type) + bin_chunk_data
        
        # GLB header
        file_size = 12 + len(json_chunk) + len(bin_chunk)
        
        glb_header = struct.pack(
            '<III',
            GLTF_MAGIC,
            GLTF_VERSION,
            file_size
        )
        
        # Write file
        try:
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(glb_header)
                f.write(json_chunk)
                f.write(bin_chunk)
            
            log.info(f"[GLBExporter] Wrote {file_size} bytes")
            return True
        
        except Exception as e:
            log.error(f"[GLBExporter] File write failed: {e}")
            return False


# ============================================================================
# STAGE 9 MAIN FUNCTION
# ============================================================================

def stage9_export(mesh, output_path: str, metadata: Optional[Dict] = None) -> Tuple[bool, str]:
    """
    Execute Stage 9: Export to GLB
    
    Args:
        mesh: 3D mesh from Stage 8
        output_path: path to output GLB file
        metadata: optional metadata dict
    
    Returns:
        (success, message_or_path)
    """
    
    log.info("[Stage9] Starting GLB export")
    
    try:
        exporter = GLBExporter(mesh, metadata)
        success = exporter.export(output_path)
        
        if success:
            log.info(f"[Stage9] ✓ Export complete: {output_path}")
            return True, output_path
        else:
            log.error("[Stage9] Export failed")
            return False, "Export failed"
    
    except Exception as e:
        log.error(f"[Stage9] Exception: {e}")
        return False, str(e)
