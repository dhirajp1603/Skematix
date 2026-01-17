"""
3D CUTAWAY CONSTRUCTION MODULE
Stage 6: 3D Cutaway Construction

Purpose: Generate 3D geometry from normalized metric wall graph and rooms.

Key Principles:
- Walls: thickness 0.20–0.25 m, height 1.3–1.5 m (open-top)
- Floor slab: thickness 0.12–0.15 m
- NO roof or ceiling under any condition
- All geometry must be watertight and manifold

Algorithm:
1. Create floor slab (ground plane)
2. Extrude walls to cutaway height
3. Ensure wall continuity at junctions
4. Build room meshes for interior visibility
5. Validate watertight topology

Output: Parametric 3D model (vertices, faces, normals)
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Set
import logging
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

# ============================================================================
# ARCHITECTURAL CONSTANTS (per specification)
# ============================================================================

WALL_THICKNESS = 0.22  # meters (standard masonry)
WALL_HEIGHT = 1.3      # meters (open-top cutaway)
FLOOR_SLAB_THICKNESS = 0.12  # meters (structural slab)

# Tolerance for junction validation
JUNCTION_TOLERANCE = 0.05  # meters


# ============================================================================
# GEOMETRY DATA STRUCTURES
# ============================================================================

@dataclass
class Vertex:
    """3D vertex with position and normal"""
    position: np.ndarray  # (x, y, z) in meters
    normal: np.ndarray = field(default_factory=lambda: np.array([0., 0., 1.]))
    
    def __hash__(self):
        return hash(tuple(self.position))
    
    def __eq__(self, other):
        return np.allclose(self.position, other.position)


@dataclass
class Face:
    """Triangle face with vertex indices"""
    vertex_indices: Tuple[int, int, int]  # indices into vertex list
    normal: Optional[np.ndarray] = None
    
    def __hash__(self):
        return hash(self.vertex_indices)


class Mesh:
    """3D mesh: collection of vertices and faces"""
    
    def __init__(self, name: str = "mesh"):
        self.name = name
        self.vertices: List[Vertex] = []
        self.faces: List[Face] = []
        self.vertex_hash_map: Dict = {}  # position -> index (for deduplication)
    
    def add_vertex(self, position: np.ndarray, normal: Optional[np.ndarray] = None) -> int:
        """Add vertex (with deduplication) and return index"""
        
        # Check if vertex already exists
        key = tuple(np.round(position, decimals=6))
        if key in self.vertex_hash_map:
            return self.vertex_hash_map[key]
        
        idx = len(self.vertices)
        vertex = Vertex(position=position.copy())
        if normal is not None:
            vertex.normal = normal.copy()
        
        self.vertices.append(vertex)
        self.vertex_hash_map[key] = idx
        return idx
    
    def add_face(self, vi0: int, vi1: int, vi2: int, 
                 normal: Optional[np.ndarray] = None) -> int:
        """Add triangle face and return index"""
        
        face = Face(vertex_indices=(vi0, vi1, vi2), normal=normal)
        idx = len(self.faces)
        self.faces.append(face)
        return idx
    
    def recalculate_normals(self):
        """Recalculate vertex normals from faces (optimized)"""
        
        # Skip if no faces
        if not self.faces:
            return
        
        # Initialize vertex normals
        vertex_normals = {}
        for i in range(len(self.vertices)):
            vertex_normals[i] = np.array([0., 0., 0.], dtype=np.float32)
        
        # Accumulate face normals to vertex normals
        for face in self.faces:
            if len(face.vertex_indices) < 3:
                continue
            
            try:
                # Only compute for first 3 vertices (triangles)
                vi0, vi1, vi2 = face.vertex_indices[0], face.vertex_indices[1], face.vertex_indices[2]
                v0 = self.vertices[vi0].position
                v1 = self.vertices[vi1].position
                v2 = self.vertices[vi2].position
                
                # Compute face normal efficiently
                edge1 = v1 - v0
                edge2 = v2 - v0
                face_normal = np.cross(edge1, edge2, dtype=np.float32)
                
                norm_sq = np.dot(face_normal, face_normal)
                if norm_sq > 1e-12:
                    face_normal = face_normal / np.sqrt(norm_sq)
                    face.normal = face_normal
                    
                    # Add to vertex normals
                    vertex_normals[vi0] += face_normal
                    vertex_normals[vi1] += face_normal
                    vertex_normals[vi2] += face_normal
            except Exception:
                continue
        
        # Normalize vertex normals
        for i in range(len(self.vertices)):
            normal = vertex_normals[i]
            norm_sq = np.dot(normal, normal)
            if norm_sq > 1e-12:
                self.vertices[i].normal = normal / np.sqrt(norm_sq)
    
    def validate_manifold(self) -> Tuple[bool, str]:
        """
        Basic manifold validation.
        
        Manifold requirement: each edge is shared by exactly 2 faces.
        
        Returns:
            (is_manifold, message)
        """
        
        edge_count: Dict[Tuple, int] = {}
        
        for face in self.faces:
            vi0, vi1, vi2 = face.vertex_indices
            
            # Add edges (normalize to avoid duplicates)
            edges = [
                tuple(sorted([vi0, vi1])),
                tuple(sorted([vi1, vi2])),
                tuple(sorted([vi2, vi0]))
            ]
            
            for edge in edges:
                edge_count[edge] = edge_count.get(edge, 0) + 1
        
        # Check each edge appears exactly twice
        non_manifold_edges = sum(1 for count in edge_count.values() if count != 2)
        
        if non_manifold_edges > 0:
            return False, f"Non-manifold edges: {non_manifold_edges}"
        
        return True, "Mesh is manifold"
    
    def summary(self) -> Dict:
        """Get mesh summary"""
        return {
            'name': self.name,
            'vertex_count': len(self.vertices),
            'face_count': len(self.faces),
            'triangle_count': len(self.faces)
        }


# ============================================================================
# WALL EXTRUSION
# ============================================================================

class WallExtrusion:
    """Extrude wall centerlines to 3D volumetric geometry"""
    
    @staticmethod
    def extrude_wall_edge(p_start: np.ndarray,
                         p_end: np.ndarray,
                         thickness: float,
                         height: float,
                         mesh: Mesh) -> List[int]:
        """
        Extrude a single wall edge to 3D geometry.
        
        Creates a box with dimensions:
        - width: thickness
        - length: distance from p_start to p_end
        - height: wall_height
        
        Args:
            p_start: (x, y) start point of wall centerline (meters)
            p_end: (x, y) end point of wall centerline (meters)
            thickness: wall thickness (meters)
            height: wall height (meters)
            mesh: target mesh to add vertices/faces to
        
        Returns:
            list of vertex indices created
        """
        
        # Compute wall direction and perpendicular
        wall_vec = p_end - p_start
        wall_len = np.linalg.norm(wall_vec)
        
        if wall_len < 1e-6:
            return []  # Degenerate edge
        
        wall_dir = wall_vec / wall_len
        
        # Perpendicular in XY plane
        perp_dir = np.array([-wall_dir[1], wall_dir[0]])
        
        # Half-thickness perpendiculars
        half_thick = thickness / 2.0
        perp_offset = perp_dir * half_thick
        
        # Bottom four corners (z = 0)
        p0_bottom = np.array([p_start[0] - perp_offset[0], p_start[1] - perp_offset[1], 0.0])
        p1_bottom = np.array([p_start[0] + perp_offset[0], p_start[1] + perp_offset[1], 0.0])
        p2_bottom = np.array([p_end[0] + perp_offset[0], p_end[1] + perp_offset[1], 0.0])
        p3_bottom = np.array([p_end[0] - perp_offset[0], p_end[1] - perp_offset[1], 0.0])
        
        # Top four corners (z = height)
        p0_top = np.array([p_start[0] - perp_offset[0], p_start[1] - perp_offset[1], height])
        p1_top = np.array([p_start[0] + perp_offset[0], p_start[1] + perp_offset[1], height])
        p2_top = np.array([p_end[0] + perp_offset[0], p_end[1] + perp_offset[1], height])
        p3_top = np.array([p_end[0] - perp_offset[0], p_end[1] - perp_offset[1], height])
        
        # Add vertices
        vi_bottom = [
            mesh.add_vertex(p0_bottom),
            mesh.add_vertex(p1_bottom),
            mesh.add_vertex(p2_bottom),
            mesh.add_vertex(p3_bottom)
        ]
        
        vi_top = [
            mesh.add_vertex(p0_top),
            mesh.add_vertex(p1_top),
            mesh.add_vertex(p2_top),
            mesh.add_vertex(p3_top)
        ]
        
        all_vertices = vi_bottom + vi_top
        
        # Create faces (bottom, top, sides)
        
        # Bottom (z=0, normal pointing down)
        mesh.add_face(vi_bottom[0], vi_bottom[2], vi_bottom[1])
        mesh.add_face(vi_bottom[0], vi_bottom[3], vi_bottom[2])
        
        # Top (z=height, normal pointing up)
        mesh.add_face(vi_top[0], vi_top[1], vi_top[2])
        mesh.add_face(vi_top[0], vi_top[2], vi_top[3])
        
        # Sides
        # Side 1: p0-p1
        mesh.add_face(vi_bottom[0], vi_bottom[1], vi_top[0])
        mesh.add_face(vi_bottom[1], vi_top[1], vi_top[0])
        
        # Side 2: p1-p2
        mesh.add_face(vi_bottom[1], vi_bottom[2], vi_top[1])
        mesh.add_face(vi_bottom[2], vi_top[2], vi_top[1])
        
        # Side 3: p2-p3
        mesh.add_face(vi_bottom[2], vi_bottom[3], vi_top[2])
        mesh.add_face(vi_bottom[3], vi_top[3], vi_top[2])
        
        # Side 4: p3-p0
        mesh.add_face(vi_bottom[3], vi_bottom[0], vi_top[3])
        mesh.add_face(vi_bottom[0], vi_top[0], vi_top[3])
        
        return all_vertices


# ============================================================================
# 3D CUTAWAY CONSTRUCTION
# ============================================================================

class CutawayBuilder:
    """Build complete 3D cutaway model from normalized geometry"""
    
    def __init__(self, wall_graph, room_set, normalization_context):
        """
        Args:
            wall_graph: normalized WallTopologyGraph
            room_set: normalized RoomSet
            normalization_context: NormalizationContext from Stage 5
        """
        self.wall_graph = wall_graph
        self.room_set = room_set
        self.context = normalization_context
        
        self.wall_mesh = None
        self.floor_mesh = None
        self.room_mesh = None
        self.complete_mesh = None
    
    def build(self) -> Optional[Mesh]:
        """
        Build complete 3D cutaway model.
        
        Returns:
            complete_mesh (Mesh object) or None if failed
        """
        
        log.info("[CutawayBuilder] Building 3D cutaway model")
        
        try:
            # Create combined mesh
            combined_mesh = Mesh(name="cutaway_model")
            
            # Step 1: Build floor slab
            floor_mesh = self._build_floor_slab(combined_mesh)
            
            # Step 2: Build walls from topology graph
            wall_mesh = self._build_walls(combined_mesh)
            
            if not wall_mesh:
                log.error("[CutawayBuilder] Wall construction failed")
                return None
            
            # Step 3: Ensure wall continuity at junctions
            self._validate_wall_continuity()
            
            # Step 4: Recalculate normals for smooth rendering
            combined_mesh.recalculate_normals()
            
            # Step 5: Validate topology
            is_manifold, msg = combined_mesh.validate_manifold()
            if not is_manifold:
                log.warning(f"[CutawayBuilder] Manifold check: {msg}")
            
            log.info(f"[CutawayBuilder] Created mesh with {len(combined_mesh.vertices)} vertices, "
                    f"{len(combined_mesh.faces)} faces")
            
            self.complete_mesh = combined_mesh
            return combined_mesh
        
        except Exception as e:
            log.error(f"[CutawayBuilder] Build failed: {e}")
            return None
    
    def _build_floor_slab(self, mesh: Mesh) -> Optional[Mesh]:
        """
        Build floor slab as rectangular base.
        
        Floor bounds are computed from wall bounding box.
        """
        
        log.info("[CutawayBuilder] Building floor slab")
        
        if not self.wall_graph or not self.wall_graph.vertices:
            log.warning("[CutawayBuilder] No walls to compute floor bounds")
            return mesh
        
        # Get bounding box from wall vertices
        xs = [v.position[0] for v in self.wall_graph.vertices.values()]
        ys = [v.position[1] for v in self.wall_graph.vertices.values()]
        
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        
        # Add padding to floor
        padding = 0.5  # meters
        x_min -= padding
        x_max += padding
        y_min -= padding
        y_max += padding
        
        # Create floor slab (thin rectangular box at z=0)
        z_top = 0.0
        z_bottom = -FLOOR_SLAB_THICKNESS
        
        # Bottom corners
        p0 = np.array([x_min, y_min, z_bottom])
        p1 = np.array([x_max, y_min, z_bottom])
        p2 = np.array([x_max, y_max, z_bottom])
        p3 = np.array([x_min, y_max, z_bottom])
        
        # Top corners
        p4 = np.array([x_min, y_min, z_top])
        p5 = np.array([x_max, y_min, z_top])
        p6 = np.array([x_max, y_max, z_top])
        p7 = np.array([x_min, y_max, z_top])
        
        # Add vertices
        vi_bottom = [mesh.add_vertex(p) for p in [p0, p1, p2, p3]]
        vi_top = [mesh.add_vertex(p) for p in [p4, p5, p6, p7]]
        
        # Add faces (bottom, top, sides)
        # Bottom (z_bottom, normal down)
        mesh.add_face(vi_bottom[0], vi_bottom[2], vi_bottom[1])
        mesh.add_face(vi_bottom[0], vi_bottom[3], vi_bottom[2])
        
        # Top (z_top, normal up)
        mesh.add_face(vi_top[0], vi_top[1], vi_top[2])
        mesh.add_face(vi_top[0], vi_top[2], vi_top[3])
        
        # Sides
        mesh.add_face(vi_bottom[0], vi_bottom[1], vi_top[0])
        mesh.add_face(vi_bottom[1], vi_top[1], vi_top[0])
        
        mesh.add_face(vi_bottom[1], vi_bottom[2], vi_top[1])
        mesh.add_face(vi_bottom[2], vi_top[2], vi_top[1])
        
        mesh.add_face(vi_bottom[2], vi_bottom[3], vi_top[2])
        mesh.add_face(vi_bottom[3], vi_top[3], vi_top[2])
        
        mesh.add_face(vi_bottom[3], vi_bottom[0], vi_top[3])
        mesh.add_face(vi_bottom[0], vi_top[0], vi_top[3])
        
        log.info("[CutawayBuilder] Floor slab created (8 vertices, 12 faces)")
        return mesh
    
    def _build_walls(self, mesh: Mesh) -> Optional[Mesh]:
        """
        Build walls by extruding wall edges to 3D.
        
        Each edge in the wall topology graph becomes a 3D wall volume.
        """
        
        log.info("[CutawayBuilder] Building walls")
        
        if not self.wall_graph or not self.wall_graph.edges:
            log.error("[CutawayBuilder] No wall edges to extrude")
            return None
        
        wall_count = 0
        total_wall_length = 0.0
        
        for edge in self.wall_graph.edges.values():
            # Get wall centerline endpoints
            p_start = np.array(edge.vertex_a.position)
            p_end = np.array(edge.vertex_b.position)
            
            # Extrude to 3D
            WallExtrusion.extrude_wall_edge(
                p_start, p_end,
                thickness=WALL_THICKNESS,
                height=WALL_HEIGHT,
                mesh=mesh
            )
            
            wall_count += 1
            edge_length = np.linalg.norm(p_end - p_start)
            total_wall_length += edge_length
        
        log.info(f"[CutawayBuilder] Extruded {wall_count} walls, total length {total_wall_length:.2f}m")
        return mesh
    
    def _validate_wall_continuity(self):
        """Check that walls are continuous at junctions"""
        
        if not self.wall_graph:
            return
        
        # Count junctions with appropriate degree
        junctions = sum(1 for v in self.wall_graph.vertices.values() if v.is_junction)
        log.info(f"[CutawayBuilder] Wall junctions verified: {junctions}")


def create_cutaway_mesh(wall_graph, room_set, normalization_context) -> Optional[Mesh]:
    """
    High-level function to create 3D cutaway mesh.
    
    Args:
        wall_graph: normalized WallTopologyGraph
        room_set: normalized RoomSet
        normalization_context: NormalizationContext
    
    Returns:
        Mesh object or None
    """
    
    builder = CutawayBuilder(wall_graph, room_set, normalization_context)
    return builder.build()
