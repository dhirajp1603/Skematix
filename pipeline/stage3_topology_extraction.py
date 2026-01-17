"""
TOPOLOGY EXTRACTION MODULE
Stage 3: Topology Extraction (CRITICAL)

Purpose: Convert refined wall masks into vector geometry by:
1. Skeletonizing wall regions to obtain wall centerlines
2. Detecting junctions, corners, and intersections
3. Building a topological wall graph

The wall graph is the SINGLE SOURCE OF TRUTH for all geometry.
No room detection is possible without this.

Key Principle: The skeleton represents wall centerlines, not filled regions.
From the skeleton, we extract vertices, edges, and topological relationships.
"""

import cv2
import numpy as np
from scipy import ndimage
from typing import List, Dict, Tuple, Optional, Set
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)

# ============================================================================
# DATA STRUCTURES FOR TOPOLOGY
# ============================================================================

@dataclass
class WallVertex:
    """A vertex (point) in the wall graph"""
    id: int
    position: Tuple[float, float]  # (x, y) in pixels
    is_junction: bool              # True if 3+ edges meet
    is_corner: bool                # True if 2 edges at ~90° angle
    degree: int = 0                # Number of connected edges
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return self.id == other.id


@dataclass
class WallEdge:
    """An edge (wall segment) connecting two vertices"""
    id: int
    vertex_a: WallVertex
    vertex_b: WallVertex
    length_px: float              # Length in pixels
    points: List[Tuple[int, int]] # Pixel points along edge
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return self.id == other.id


class WallTopologyGraph:
    """
    Directed/undirected graph representing wall structure.
    
    Vertices: Junction points, corners, endpoints
    Edges: Wall segments connecting vertices
    
    This graph is the canonical representation of architectural topology.
    """
    
    def __init__(self):
        self.vertices: Dict[int, WallVertex] = {}
        self.edges: Dict[int, WallEdge] = {}
        self.vertex_counter = 0
        self.edge_counter = 0
        self.adjacency: Dict[int, Set[int]] = {}  # vertex_id -> set of adjacent vertex_ids
    
    def add_vertex(self, position: Tuple[float, float],
                   is_junction: bool = False,
                   is_corner: bool = False) -> WallVertex:
        """Add a vertex to the graph"""
        vertex = WallVertex(
            id=self.vertex_counter,
            position=position,
            is_junction=is_junction,
            is_corner=is_corner
        )
        self.vertices[vertex.id] = vertex
        self.adjacency[vertex.id] = set()
        self.vertex_counter += 1
        return vertex
    
    def add_edge(self, vertex_a: WallVertex, vertex_b: WallVertex,
                 length_px: float, points: List[Tuple[int, int]]) -> WallEdge:
        """Add an edge connecting two vertices"""
        edge = WallEdge(
            id=self.edge_counter,
            vertex_a=vertex_a,
            vertex_b=vertex_b,
            length_px=length_px,
            points=points
        )
        self.edges[edge.id] = edge
        
        # Update adjacency
        self.adjacency[vertex_a.id].add(vertex_b.id)
        self.adjacency[vertex_b.id].add(vertex_a.id)
        
        # Update vertex degrees
        vertex_a.degree += 1
        vertex_b.degree += 1
        
        self.edge_counter += 1
        return edge
    
    def get_neighbors(self, vertex: WallVertex) -> List[WallVertex]:
        """Get all adjacent vertices"""
        neighbor_ids = self.adjacency[vertex.id]
        return [self.vertices[vid] for vid in neighbor_ids]
    
    def validate(self) -> Tuple[bool, str]:
        """
        Validate graph structure.
        
        Returns:
            (is_valid, message)
        """
        
        if len(self.vertices) < 2:
            return False, "Graph has fewer than 2 vertices"
        
        if len(self.edges) < 1:
            return False, "Graph has no edges"
        
        # Check connectivity
        if not self._is_connected():
            return False, "Graph is not connected (broken wall topology)"
        
        return True, "Graph structure valid"
    
    def _is_connected(self) -> bool:
        """Check if graph is fully connected (BFS)"""
        if not self.vertices:
            return False
        
        visited = set()
        start_vertex_id = next(iter(self.vertices.keys()))
        queue = [start_vertex_id]
        
        while queue:
            vid = queue.pop(0)
            if vid in visited:
                continue
            visited.add(vid)
            for neighbor_id in self.adjacency[vid]:
                if neighbor_id not in visited:
                    queue.append(neighbor_id)
        
        return len(visited) == len(self.vertices)
    
    def summary(self) -> Dict:
        """Get summary statistics"""
        return {
            'vertex_count': len(self.vertices),
            'edge_count': len(self.edges),
            'total_edge_length': sum(e.length_px for e in self.edges.values()),
            'junction_count': sum(1 for v in self.vertices.values() if v.is_junction),
            'corner_count': sum(1 for v in self.vertices.values() if v.is_corner)
        }

# ============================================================================
# SKELETONIZATION & TOPOLOGY EXTRACTION
# ============================================================================

class TopologyExtractor:
    """
    Extract topological structure from refined wall mask.
    
    Algorithm:
    1. Skeletonize wall mask (medial axis transform)
    2. Detect junctions and endpoints
    3. Trace edges from skeleton
    4. Build wall topology graph
    """
    
    def __init__(self, wall_mask: np.ndarray):
        """
        Args:
            wall_mask: Binary wall mask from Stage 2
        """
        self.wall_mask = wall_mask.astype(np.uint8)
        self.skeleton = None
        self.graph = None
    
    def extract(self) -> Optional[WallTopologyGraph]:
        """
        Extract topological wall graph.
        
        Returns:
            WallTopologyGraph or None if failed
        """
        
        log.info("[Topology] Extracting wall topology")
        
        # Step 1: Skeletonize
        self.skeleton = self._skeletonize_wall_mask()
        log.info(f"[Topology] Skeleton extracted, {self.skeleton.sum()} pixels")
        
        # Step 2: Detect key points (junctions, corners, endpoints)
        junctions, corners, endpoints = self._detect_key_points()
        log.info(f"[Topology] Found {len(junctions)} junctions, {len(corners)} corners, {len(endpoints)} endpoints")
        
        # Step 3: Build graph
        self.graph = self._build_graph(junctions, corners, endpoints)
        
        return self.graph
    
    def _skeletonize_wall_mask(self) -> np.ndarray:
        """
        Skeletonize wall mask using Zhang-Suen or Medial Axis Transform.
        
        Returns:
            Binary skeleton image
        """
        
        log.info("[Topology] Running skeletonization (Zhang-Suen)")
        
        # Use scipy's binary_erosion to compute medial axis
        from scipy.ndimage import binary_erosion, distance_transform_edt
        
        # Medial axis transform
        _, skeleton = ndimage.distance_transform_edt(
            255 - self.wall_mask, return_indices=True
        )
        
        # Alternative: Thinning using Zhang-Suen
        skeleton = cv2.ximgproc.thinning(self.wall_mask)
        
        return skeleton.astype(np.uint8)
    
    def _detect_key_points(self) -> Tuple[List, List, List]:
        """
        Detect junctions (3+ connections), corners (2 connections at ~90°),
        and endpoints (1 connection).
        
        Returns:
            (junctions, corners, endpoints) as lists of (x, y) coordinates
        """
        
        skeleton = self.skeleton
        junctions = []
        corners = []
        endpoints = []
        
        # Find all skeleton pixels
        skeleton_points = np.argwhere(skeleton > 0)
        
        for y, x in skeleton_points:
            # Count neighbors
            neighborhood = skeleton[max(0, y-1):y+2, max(0, x-1):x+2]
            neighbor_count = neighborhood.sum() - 1  # Exclude self
            
            if neighbor_count == 1:
                # Endpoint
                endpoints.append((x, y))
            elif neighbor_count == 2:
                # Could be straight line or corner - check angle
                neighbors = self._get_neighbor_directions(skeleton, x, y)
                if self._is_corner(neighbors):
                    corners.append((x, y))
            elif neighbor_count >= 3:
                # Junction (3+ connections)
                junctions.append((x, y))
        
        log.info(f"[Topology] Key points: junctions={len(junctions)}, corners={len(corners)}, endpoints={len(endpoints)}")
        
        return junctions, corners, endpoints
    
    def _get_neighbor_directions(self, skeleton: np.ndarray,
                                x: int, y: int) -> List[Tuple[int, int]]:
        """Get direction vectors to skeleton neighbors"""
        directions = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < skeleton.shape[1] and 0 <= ny < skeleton.shape[0]:
                    if skeleton[ny, nx] > 0:
                        directions.append((dx, dy))
        return directions
    
    def _is_corner(self, directions: List[Tuple[int, int]]) -> bool:
        """Check if two directions form approximately 90° angle"""
        if len(directions) != 2:
            return False
        
        dx1, dy1 = directions[0]
        dx2, dy2 = directions[1]
        
        # Dot product (normalized)
        dot = dx1*dx2 + dy1*dy2
        
        # Approximately perpendicular if dot product close to 0
        return abs(dot) < 0.5
    
    def _build_graph(self, junctions: List, corners: List, endpoints: List) -> WallTopologyGraph:
        """
        Build topological graph from key points.
        
        Strategy:
        1. Create vertices from junctions, corners, endpoints
        2. Trace edges between vertices along skeleton
        3. Validate connectivity
        """
        
        log.info("[Topology] Building wall topology graph")
        
        graph = WallTopologyGraph()
        
        # Create vertices
        all_points = junctions + corners + endpoints
        point_to_vertex = {}
        
        for x, y in all_points:
            is_junction = (x, y) in junctions
            is_corner = (x, y) in corners
            vertex = graph.add_vertex(
                position=(float(x), float(y)),
                is_junction=is_junction,
                is_corner=is_corner
            )
            point_to_vertex[(x, y)] = vertex
        
        log.info(f"[Topology] Created {len(graph.vertices)} vertices")
        
        # Trace edges (simplified: connect junctions/endpoints directly)
        # In production, would use sophisticated edge tracing
        edges_added = 0
        for i, v1 in enumerate(graph.vertices.values()):
            for v2 in list(graph.vertices.values())[i+1:]:
                # Simple heuristic: if both are key points, might be connected
                # In production: use Dijkstra/BFS on skeleton
                # For now, compute distance in skeleton space
                dist = np.sqrt((v1.position[0] - v2.position[0])**2 +
                             (v1.position[1] - v2.position[1])**2)
                
                if dist < 50:  # If close enough, likely connected
                    # Trace actual path on skeleton
                    path = self._trace_skeleton_path(
                        (int(v1.position[0]), int(v1.position[1])),
                        (int(v2.position[0]), int(v2.position[1]))
                    )
                    
                    if path is not None:
                        graph.add_edge(v1, v2, dist, path)
                        edges_added += 1
        
        log.info(f"[Topology] Created {edges_added} edges")
        
        return graph
    
    def _trace_skeleton_path(self, start: Tuple[int, int],
                            end: Tuple[int, int]) -> Optional[List]:
        """
        Trace actual path on skeleton between two points.
        (Simplified version - production would use sophisticated pathfinding)
        """
        # This is a placeholder - real implementation would trace skeleton
        return [(start[0], start[1]), (end[0], end[1])]

# ============================================================================
# STAGE 3 MAIN INTERFACE
# ============================================================================

def stage3_topology_extraction(refined_wall_mask: np.ndarray) -> Optional[WallTopologyGraph]:
    """
    STAGE 3: Topology Extraction (CRITICAL)
    
    Input: Refined wall mask from Stage 2
    Output: Wall topology graph (vertices + edges)
    
    The wall graph is the SINGLE SOURCE OF TRUTH for all geometry.
    
    Args:
        refined_wall_mask: Binary wall mask from Stage 2
    
    Returns:
        WallTopologyGraph or None if failed
    """
    
    log.info("="*80)
    log.info("STAGE 3: TOPOLOGY EXTRACTION (CRITICAL)")
    log.info("="*80)
    
    if refined_wall_mask is None:
        log.error("[Topology] No wall mask provided")
        return None
    
    # Extract topology
    extractor = TopologyExtractor(refined_wall_mask)
    graph = extractor.extract()
    
    if graph is None:
        log.error("[Topology] Failed to extract topology")
        return None
    
    # Validate
    is_valid, message = graph.validate()
    log.info(f"[Topology] Validation: {message}")
    
    if not is_valid:
        log.error(f"[Topology] ✗ VALIDATION FAILED: {message}")
        return None
    
    # Report summary
    summary = graph.summary()
    log.info("[Topology] Graph summary:")
    log.info(f"  Vertices: {summary['vertex_count']}")
    log.info(f"  Edges: {summary['edge_count']}")
    log.info(f"  Total wall length: {summary['total_edge_length']:.1f} pixels")
    log.info(f"  Junctions: {summary['junction_count']}")
    log.info(f"  Corners: {summary['corner_count']}")
    
    log.info("[Topology] ✓ STAGE 3 COMPLETE")
    return graph


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    print("Topology extraction module loaded")
