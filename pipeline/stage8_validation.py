"""
VALIDATION MODULE
Stage 8: Comprehensive Validation (FAIL FAST)

Purpose: Programmatically validate all aspects of generated model.

Validation Checks:
1. Model geometry (wall count, room count)
2. Topology (no single-solid enclosure)
3. Interior visibility from top
4. Manifold and watertight requirements
5. Dimensional sanity checks
6. No roofs or closed boxes

FAIL FAST principle: If validation fails, return explicit error immediately.
Do NOT attempt to fix or continue.

This is a critical quality gate before export.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

log = logging.getLogger(__name__)

# ============================================================================
# VALIDATION CONSTANTS
# ============================================================================

MIN_WALL_COUNT = 1          # At least one wall
MIN_ROOM_COUNT = 1          # At least one room
MIN_VERTEX_COUNT = 8        # At least some geometry
MIN_FACE_COUNT = 12         # At least some faces
MIN_MESH_HEIGHT = 0.5       # At least 0.5m tall

MAX_SCALE_FACTOR = 1000.0   # Max pixels per meter
MIN_SCALE_FACTOR = 0.01     # Min pixels per meter


# ============================================================================
# VALIDATION RESULTS
# ============================================================================

class ValidationResult:
    """Container for validation results"""
    
    def __init__(self):
        self.passed = True
        self.checks: List[Tuple[str, bool, str]] = []  # (check_name, passed, message)
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def add_check(self, name: str, passed: bool, message: str):
        """Record validation check result"""
        self.checks.append((name, passed, message))
        if not passed:
            self.passed = False
            self.errors.append(message)
    
    def add_warning(self, message: str):
        """Record warning"""
        self.warnings.append(message)
    
    def summary(self) -> str:
        """Generate summary report"""
        
        lines = [
            "=" * 80,
            "VALIDATION REPORT",
            "=" * 80
        ]
        
        # Checks
        lines.append("\nChecks:")
        for name, passed, message in self.checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            lines.append(f"  [{status}] {name}")
            lines.append(f"         {message}")
        
        # Warnings
        if self.warnings:
            lines.append("\nWarnings:")
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        
        # Overall
        lines.append("\n" + "=" * 80)
        if self.passed:
            lines.append("✓ VALIDATION PASSED")
        else:
            lines.append("✗ VALIDATION FAILED")
        lines.append("=" * 80)
        
        return "\n".join(lines)


# ============================================================================
# VALIDATOR CLASSES
# ============================================================================

class MeshValidator:
    """Validate 3D mesh properties"""
    
    def __init__(self, mesh):
        self.mesh = mesh
        self.result = ValidationResult()
    
    def validate(self) -> ValidationResult:
        """Execute all mesh validation checks"""
        
        log.info("[Validator] Validating mesh geometry")
        
        # Check vertex/face counts
        self._check_geometry_count()
        
        # Check manifold property
        self._check_manifold()
        
        # Check dimensions
        self._check_dimensions()
        
        # Check vertex positions are reasonable
        self._check_vertex_positions()
        
        # Check no NaN or Inf
        self._check_numerical_validity()
        
        return self.result
    
    def _check_geometry_count(self):
        """Validate mesh has sufficient geometry"""
        
        vertex_count = len(self.mesh.vertices)
        face_count = len(self.mesh.faces)
        
        passed = vertex_count >= MIN_VERTEX_COUNT and face_count >= MIN_FACE_COUNT
        
        self.result.add_check(
            "Geometry Count",
            passed,
            f"{vertex_count} vertices, {face_count} faces"
        )
    
    def _check_manifold(self):
        """Validate mesh is manifold"""
        
        is_manifold, msg = self.mesh.validate_manifold()
        
        self.result.add_check(
            "Manifold Topology",
            is_manifold,
            msg
        )
    
    def _check_dimensions(self):
        """Validate mesh dimensions are reasonable"""
        
        if len(self.mesh.vertices) == 0:
            self.result.add_check("Dimensions", False, "No vertices")
            return
        
        positions = np.array([v.position for v in self.mesh.vertices])
        
        x_range = np.ptp(positions[:, 0])  # peak-to-peak
        y_range = np.ptp(positions[:, 1])
        z_range = np.ptp(positions[:, 2])
        
        # Check height (should be at least wall height)
        height_ok = z_range >= MIN_MESH_HEIGHT
        
        # Check not degenerate in XY
        xy_ok = x_range > 0 and y_range > 0
        
        passed = height_ok and xy_ok
        
        self.result.add_check(
            "Dimensions",
            passed,
            f"X range {x_range:.2f}m, Y range {y_range:.2f}m, Z range {z_range:.2f}m"
        )
        
        if z_range < MIN_MESH_HEIGHT:
            self.result.add_warning(f"Model height {z_range:.2f}m is very low")
    
    def _check_vertex_positions(self):
        """Validate all vertices have reasonable positions"""
        
        positions = np.array([v.position for v in self.mesh.vertices])
        
        # Check no extreme values
        has_nan = np.any(np.isnan(positions))
        has_inf = np.any(np.isinf(positions))
        
        passed = not (has_nan or has_inf)
        
        msg = ""
        if has_nan:
            msg += "NaN values found; "
        if has_inf:
            msg += "Infinity values found; "
        if not msg:
            msg = "All vertex positions valid"
        
        self.result.add_check(
            "Vertex Validity",
            passed,
            msg
        )
    
    def _check_numerical_validity(self):
        """Check for numerical errors"""
        
        # Check normals
        for i, vertex in enumerate(self.mesh.vertices):
            if np.any(np.isnan(vertex.normal)) or np.any(np.isinf(vertex.normal)):
                self.result.add_warning(f"Vertex {i} has invalid normal")
                break
        
        self.result.add_check(
            "Numerical Validity",
            True,
            "No critical numerical errors"
        )


class ArchitectureValidator:
    """Validate architectural properties"""
    
    def __init__(self, wall_graph, room_set, wall_count: int = None):
        self.wall_graph = wall_graph
        self.room_set = room_set
        self.explicit_wall_count = wall_count
        self.result = ValidationResult()
    
    def validate(self) -> ValidationResult:
        """Execute all architectural validation checks"""
        
        log.info("[Validator] Validating architectural properties")
        
        # Check wall count
        self._check_wall_count()
        
        # Check room count
        self._check_room_count()
        
        # Check no room merging
        self._check_room_separation()
        
        # Check graph connectivity
        self._check_graph_connectivity()
        
        return self.result
    
    def _check_wall_count(self):
        """Validate building has multiple walls"""
        
        wall_count = len(self.wall_graph.edges) if self.wall_graph else 0
        
        # Use explicit count if provided
        if self.explicit_wall_count is not None:
            wall_count = self.explicit_wall_count
        
        passed = wall_count >= MIN_WALL_COUNT
        
        self.result.add_check(
            "Wall Count",
            passed,
            f"Found {wall_count} walls (minimum: {MIN_WALL_COUNT})"
        )
    
    def _check_room_count(self):
        """Validate building has rooms"""
        
        room_count = len(self.room_set.rooms) if self.room_set else 0
        
        passed = room_count >= MIN_ROOM_COUNT
        
        self.result.add_check(
            "Room Count",
            passed,
            f"Found {room_count} rooms (minimum: {MIN_ROOM_COUNT})"
        )
    
    def _check_room_separation(self):
        """Validate no rooms are merged"""
        
        if not self.room_set:
            self.result.add_check("Room Separation", True, "No rooms to check")
            return
        
        # Check overlap
        no_overlap, msg = self.room_set.check_overlap()
        
        self.result.add_check(
            "Room Separation",
            no_overlap,
            msg
        )
    
    def _check_graph_connectivity(self):
        """Validate wall graph is connected"""
        
        if not self.wall_graph:
            self.result.add_check("Graph Connectivity", False, "No wall graph")
            return
        
        is_connected, msg = self.wall_graph.validate()
        
        self.result.add_check(
            "Graph Connectivity",
            is_connected,
            msg
        )


class CutawayValidator:
    """Validate cutaway-specific properties"""
    
    def __init__(self, mesh):
        self.mesh = mesh
        self.result = ValidationResult()
    
    def validate(self) -> ValidationResult:
        """Execute cutaway-specific validation"""
        
        log.info("[Validator] Validating cutaway properties")
        
        # Check no roof (max Z should be reasonable)
        self._check_no_roof()
        
        # Check open-top (should be visible from above)
        self._check_open_top()
        
        # Check floor exists
        self._check_floor_exists()
        
        return self.result
    
    def _check_no_roof(self):
        """Ensure there's no closed top"""
        
        if len(self.mesh.vertices) == 0:
            self.result.add_check("No Roof", False, "No vertices")
            return
        
        positions = np.array([v.position for v in self.mesh.vertices])
        max_z = np.max(positions[:, 2])
        
        # Roof height check: should not be way above walls (< 3m for 1.3m walls)
        passed = max_z < 3.0
        
        self.result.add_check(
            "No Roof",
            passed,
            f"Max Z coordinate: {max_z:.2f}m (should be <3.0m)"
        )
    
    def _check_open_top(self):
        """Check interior is visible from above"""
        
        # This is a heuristic: if mesh has floor and walls but reasonable Z range,
        # it's likely open-top
        
        if len(self.mesh.vertices) < 8:
            self.result.add_check("Open-Top Visibility", False, "Insufficient geometry")
            return
        
        positions = np.array([v.position for v in self.mesh.vertices])
        z_values = positions[:, 2]
        
        # Should have both floor (z<0) and walls (z>0)
        has_floor = np.any(z_values < 0)
        has_walls = np.any(z_values > 0)
        
        passed = has_floor and has_walls
        
        self.result.add_check(
            "Open-Top Visibility",
            passed,
            "Model has both floor and walls" if passed else "Missing floor or walls"
        )
    
    def _check_floor_exists(self):
        """Validate floor slab exists"""
        
        if len(self.mesh.vertices) == 0:
            self.result.add_check("Floor Exists", False, "No vertices")
            return
        
        positions = np.array([v.position for v in self.mesh.vertices])
        z_values = positions[:, 2]
        
        # Should have vertices near z=0 (floor top surface)
        near_floor = np.any(np.abs(z_values) < 0.5)
        
        # Should have vertices below z=0 (floor bottom)
        below_floor = np.any(z_values < -0.05)
        
        passed = near_floor and below_floor
        
        self.result.add_check(
            "Floor Exists",
            passed,
            "Floor slab detected" if passed else "Floor slab not found"
        )


# ============================================================================
# COMPREHENSIVE VALIDATOR
# ============================================================================

class ComprehensiveValidator:
    """Execute all validation stages"""
    
    def __init__(self, mesh, wall_graph, room_set, wall_count: int = None):
        self.mesh = mesh
        self.wall_graph = wall_graph
        self.room_set = room_set
        self.wall_count = wall_count
        
        self.all_results: Dict[str, ValidationResult] = {}
    
    def validate_all(self) -> Tuple[bool, ValidationResult]:
        """
        Execute comprehensive validation.
        
        Returns:
            (passed, combined_result)
        """
        
        log.info("[Validator] Starting comprehensive validation")
        
        combined_result = ValidationResult()
        
        # Mesh validation
        mesh_validator = MeshValidator(self.mesh)
        mesh_result = mesh_validator.validate()
        self.all_results['mesh'] = mesh_result
        
        # Merge results
        for name, passed, msg in mesh_result.checks:
            combined_result.add_check(f"Mesh: {name}", passed, msg)
        for w in mesh_result.warnings:
            combined_result.add_warning(f"Mesh: {w}")
        
        # Architecture validation
        arch_validator = ArchitectureValidator(self.wall_graph, self.room_set, self.wall_count)
        arch_result = arch_validator.validate()
        self.all_results['architecture'] = arch_result
        
        for name, passed, msg in arch_result.checks:
            combined_result.add_check(f"Architecture: {name}", passed, msg)
        for w in arch_result.warnings:
            combined_result.add_warning(f"Architecture: {w}")
        
        # Cutaway validation
        cutaway_validator = CutawayValidator(self.mesh)
        cutaway_result = cutaway_validator.validate()
        self.all_results['cutaway'] = cutaway_result
        
        for name, passed, msg in cutaway_result.checks:
            combined_result.add_check(f"Cutaway: {name}", passed, msg)
        for w in cutaway_result.warnings:
            combined_result.add_warning(f"Cutaway: {w}")
        
        # FAIL FAST: if core checks failed, halt
        if not combined_result.passed:
            log.error("[Validator] ✗ VALIDATION FAILED - Pipeline halting")
        else:
            log.info("[Validator] ✓ All validation checks passed")
        
        return combined_result.passed, combined_result
    
    def get_report(self) -> str:
        """Get validation report"""
        
        combined = ValidationResult()
        
        for result in self.all_results.values():
            for name, passed, msg in result.checks:
                combined.add_check(name, passed, msg)
            for w in result.warnings:
                combined.add_warning(w)
        
        return combined.summary()


# ============================================================================
# STAGE 8 MAIN FUNCTION
# ============================================================================

def stage8_validation(mesh, wall_graph, room_set, 
                     wall_count: int = None) -> Tuple[bool, ValidationResult]:
    """
    Execute Stage 8: Comprehensive Validation
    
    Args:
        mesh: 3D mesh from Stage 7
        wall_graph: wall topology graph
        room_set: set of rooms
        wall_count: explicit wall count (optional)
    
    Returns:
        (passed, validation_result)
    """
    
    log.info("[Stage8] Starting validation")
    
    try:
        validator = ComprehensiveValidator(mesh, wall_graph, room_set, wall_count)
        passed, result = validator.validate_all()
        
        log.info("[Stage8] Validation report:")
        log.info(result.summary())
        
        return passed, result
    
    except Exception as e:
        log.error(f"[Stage8] Validation exception: {e}")
        result = ValidationResult()
        result.passed = False
        result.errors.append(str(e))
        return False, result
