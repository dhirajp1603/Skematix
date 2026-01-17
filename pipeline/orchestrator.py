"""
BLUEPRINT-TO-3D ORCHESTRATOR
Complete Pipeline Orchestration (Stages 1-9)

Purpose: Coordinate all pipeline stages in strict order.
Enforce semantic-first architecture with explicit validation gates.

Architecture:
1. Semantic Understanding → Wall Mask Refinement → Topology Extraction
2. Room Detection (FAIL FAST if merging)
3. Metric Normalization → 3D Cutaway Construction
4. Openings Generation → Export

This is the main entry point for the entire system.
"""

import os
import sys
import cv2
import numpy as np
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime

# Import all stages
try:
    from pipeline.stage1_semantic_segmentation import (
        stage1_semantic_segmentation,
        SemanticMaskOutput
    )
    from pipeline.stage2_wall_refinement import stage2_wall_mask_refinement
    from pipeline.stage3_topology_extraction import stage3_topology_extraction
    from pipeline.stage4_room_detection import stage4_room_detection
    from pipeline.stage5_metric_normalization import MetricNormalizer
    from pipeline.stage6_3d_construction import create_cutaway_mesh
    from pipeline.stage7_openings import (
        OpeningDetector,
        OpeningGenerator,
        stage7_openings_generation
    )
    from pipeline.stage8_validation import stage8_validation
    from pipeline.stage9_export import stage9_export
except ImportError as e:
    # Fallback if modules not available
    print(f"Warning: Some modules could not be imported: {e}")

log = logging.getLogger(__name__)

# ============================================================================
# PIPELINE ORCHESTRATOR
# ============================================================================

class BlueprintPipeline:
    """
    Complete blueprint-to-3D pipeline orchestrator.
    
    Enforces strict stage ordering and validation gates.
    """
    
    def __init__(self, image_path: str, device: str = 'auto', verbose: bool = True):
        """
        Args:
            image_path: Path to blueprint image
            device: 'cuda', 'cpu', or 'auto'
            verbose: Enable detailed logging
        """
        self.image_path = image_path
        self.device = device
        self.verbose = verbose
        
        # Pipeline state
        self.image = None
        self.image_shape = None
        
        # Stage outputs
        self.semantic_output = None          # Stage 1
        self.refined_wall_mask = None        # Stage 2
        self.wall_graph = None               # Stage 3
        self.room_set = None                 # Stage 4
        self.normalized_wall_graph = None    # Stage 5
        self.normalized_room_set = None      # Stage 5
        self.normalization_context = {}      # Stage 5 context
        self.blender_model = None            # Stage 6
        self.model_with_openings = None      # Stage 7
        self.validation_results = None       # Stage 8
        self.glb_path = None                 # Stage 9
        
        # Execution log
        self.execution_log = []
        self.stage_times = {}
        self.errors = []
    
    def run_full_pipeline(self) -> Tuple[bool, str]:
        """
        Execute complete blueprint-to-3D pipeline.
        
        Enforces strict stage ordering: 1→2→3→4→5→6→7→8→9
        
        Returns:
            (success, message)
        """
        
        self._log("="*80)
        self._log("BLUEPRINT-TO-3D PIPELINE - FULL EXECUTION")
        self._log(f"Input: {self.image_path}")
        self._log(f"Device: {self.device}")
        self._log("="*80)
        
        start_time = datetime.now()
        
        try:
            # Load image
            if not self._load_image():
                return False, "Failed to load image"
            
            # STAGE 1: Semantic Understanding
            if not self._stage1_semantic_understanding():
                return False, "Stage 1 failed (Semantic Understanding)"
            
            # STAGE 2: Wall Mask Refinement
            if not self._stage2_wall_refinement():
                return False, "Stage 2 failed (Wall Mask Refinement)"
            
            # STAGE 3: Topology Extraction
            if not self._stage3_topology():
                return False, "Stage 3 failed (Topology Extraction)"
            
            # STAGE 4: Room Detection (FAIL FAST gate)
            if not self._stage4_room_detection():
                return False, "Stage 4 failed (Room Detection - FAIL FAST)"
            
            # STAGE 5: Metric Normalization
            if not self._stage5_metric_normalization():
                return False, "Stage 5 failed (Metric Normalization)"
            
            # STAGE 6: 3D Cutaway Construction
            if not self._stage6_3d_construction():
                return False, "Stage 6 failed (3D Cutaway Construction)"
            
            # STAGE 7: Openings Generation
            if not self._stage7_openings():
                return False, "Stage 7 failed (Openings Generation)"
            
            # STAGE 8: Validation
            if not self._stage8_validation():
                return False, "Stage 8 failed (Validation)"
            
            # STAGE 9: Export
            if not self._stage9_export():
                return False, "Stage 9 failed (Export)"
            
            elapsed = (datetime.now() - start_time).total_seconds()
            self._log(f"\n✓ PIPELINE COMPLETE in {elapsed:.1f}s")
            self._log(f"Output: {self.glb_path}")
            
            return True, f"Pipeline complete: {self.glb_path}"
        
        except Exception as e:
            self._log(f"\n✗ PIPELINE EXCEPTION: {type(e).__name__}: {e}")
            self.errors.append(str(e))
            return False, str(e)
    
    def _load_image(self) -> bool:
        """Load blueprint image"""
        self._log("[Pipeline] Loading image")
        
        if not os.path.exists(self.image_path):
            self._log(f"[Pipeline] Image not found: {self.image_path}")
            return False
        
        self.image = cv2.imread(self.image_path)
        if self.image is None:
            self._log("[Pipeline] Failed to load image")
            return False
        
        self.image_shape = self.image.shape
        self._log(f"[Pipeline] Image loaded: {self.image_shape}")
        return True
    
    def _stage1_semantic_understanding(self) -> bool:
        """STAGE 1: Semantic Understanding"""
        self._log_stage("1: Semantic Understanding")
        
        try:
            self.semantic_output = stage1_semantic_segmentation(
                self.image_path,
                device=self.device
            )
            
            if self.semantic_output is None:
                self._log("[Stage1] ✗ Semantic segmentation failed")
                return False
            
            self._log("[Stage1] ✓ Complete")
            return True
        except Exception as e:
            self._log(f"[Stage1] Exception: {e}")
            return False
    
    def _stage2_wall_refinement(self) -> bool:
        """STAGE 2: Wall Mask Refinement"""
        self._log_stage("2: Wall Mask Refinement")
        
        try:
            self.refined_wall_mask = stage2_wall_mask_refinement(
                self.semantic_output
            )
            
            if self.refined_wall_mask is None:
                self._log("[Stage2] ✗ Wall refinement failed")
                return False
            
            self._log("[Stage2] ✓ Complete")
            return True
        except Exception as e:
            self._log(f"[Stage2] Exception: {e}")
            return False
    
    def _stage3_topology(self) -> bool:
        """STAGE 3: Topology Extraction"""
        self._log_stage("3: Topology Extraction")
        
        try:
            self.wall_graph = stage3_topology_extraction(
                self.refined_wall_mask
            )
            
            if self.wall_graph is None:
                self._log("[Stage3] ✗ Topology extraction failed")
                return False
            
            self._log("[Stage3] ✓ Complete")
            return True
        except Exception as e:
            self._log(f"[Stage3] Exception: {e}")
            return False
    
    def _stage4_room_detection(self) -> bool:
        """STAGE 4: Room Detection (FAIL FAST gate)"""
        self._log_stage("4: Room Detection (FAIL FAST)")
        
        try:
            self.room_set = stage4_room_detection(
                self.refined_wall_mask,
                self.wall_graph
            )
            
            if self.room_set is None:
                self._log("[Stage4] ✗ Room detection failed or rooms merged")
                self._log("[Stage4] FAIL FAST: Pipeline halted")
                return False
            
            self._log(f"[Stage4] Rooms detected: {len(self.room_set.rooms)}")
            self._log("[Stage4] ✓ Complete (No merging detected)")
            return True
        except Exception as e:
            self._log(f"[Stage4] Exception: {e}")
            return False
    
    def _stage5_metric_normalization(self) -> bool:
        """STAGE 5: Metric Normalization"""
        self._log_stage("5: Metric Normalization")
        
        try:
            normalizer = MetricNormalizer(
                image_shape=self.image_shape,
                wall_graph=self.wall_graph,
                room_set=self.room_set
            )
            
            success, context_dict, normalized_wall_graph, normalized_room_set = \
                normalizer.normalize()
            
            if not success:
                self._log("[Stage5] ✗ Metric normalization failed")
                return False
            
            # Store normalized geometry
            self.normalized_wall_graph = normalized_wall_graph
            self.normalized_room_set = normalized_room_set
            self.normalization_context = context_dict
            
            self._log(f"[Stage5] Scale factor: {context_dict['scale_factor']:.2f} px/m")
            self._log(f"[Stage5] Normalized width: {context_dict['target_width_m']:.2f}m")
            self._log("[Stage5] ✓ Complete")
            
            self.normalized_geometry = True
            return True
        
        except Exception as e:
            self._log(f"[Stage5] Exception: {e}")
            return False
    
    def _stage6_3d_construction(self) -> bool:
        """STAGE 6: 3D Cutaway Construction"""
        self._log_stage("6: 3D Cutaway Construction")
        
        try:
            # Create normalization context for stage 6
            context = type('Context', (), {
                'scale_factor': self.normalization_context['scale_factor']
            })()
            
            mesh = create_cutaway_mesh(
                self.normalized_wall_graph,
                self.normalized_room_set,
                context
            )
            
            if mesh is None:
                self._log("[Stage6] ✗ 3D construction failed")
                return False
            
            self.blender_model = mesh
            
            self._log(f"[Stage6] Created mesh: {len(mesh.vertices)} vertices, "
                     f"{len(mesh.faces)} faces")
            self._log("[Stage6] Wall height: 1.3m (open-top)")
            self._log("[Stage6] ✓ Complete")
            
            return True
        
        except Exception as e:
            self._log(f"[Stage6] Exception: {e}")
            return False
    
    def _stage7_openings(self) -> bool:
        """STAGE 7: Openings Generation"""
        self._log_stage("7: Openings Generation")
        
        try:
            # Get door and window masks from semantic output
            if hasattr(self.semantic_output, 'masks') and isinstance(self.semantic_output.masks, dict):
                door_mask = self.semantic_output.masks.get(2, np.zeros(self.image_shape[:2]))
                window_mask = self.semantic_output.masks.get(3, np.zeros(self.image_shape[:2]))
                wall_mask = self.semantic_output.masks.get(1, np.zeros(self.image_shape[:2]))
            else:
                self._log("[Stage7] Warning: Semantic output structure unexpected, using empty masks")
                door_mask = np.zeros(self.image_shape[:2], dtype=np.uint8)
                window_mask = np.zeros(self.image_shape[:2], dtype=np.uint8)
                wall_mask = np.zeros(self.image_shape[:2], dtype=np.uint8)
            
            scale_factor = self.normalization_context['scale_factor']
            
            success, mesh_with_openings = stage7_openings_generation(
                self.blender_model,
                door_mask,
                window_mask,
                wall_mask,
                self.normalized_wall_graph,
                scale_factor
            )
            
            if not success or mesh_with_openings is None:
                self._log("[Stage7] ✗ Openings generation failed")
                return False
            
            self.model_with_openings = mesh_with_openings
            
            self._log("[Stage7] Generating door openings (0.9m × 1.1m)")
            self._log("[Stage7] Generating window openings (0.8m × 0.5m)")
            self._log("[Stage7] ✓ Complete")
            
            return True
        
        except Exception as e:
            self._log(f"[Stage7] Exception: {e}")
            return False
    
    def _stage8_validation(self) -> bool:
        """STAGE 8: Validation (FAIL FAST gate)"""
        self._log_stage("8: Validation (FAIL FAST)")
        
        try:
            wall_count = len(self.wall_graph.edges) if self.wall_graph else 0
            
            passed, validation_result = stage8_validation(
                self.model_with_openings,
                self.normalized_wall_graph,
                self.normalized_room_set,
                wall_count=wall_count
            )
            
            # Log validation report
            for check_name, check_passed, message in validation_result.checks:
                status = "✓" if check_passed else "✗"
                self._log(f"[Stage8] [{status}] {check_name}: {message}")
            
            if not passed:
                self._log("[Stage8] ✗ VALIDATION FAILED - Pipeline halting")
                self._log("[Stage8] FAIL FAST: Unable to continue")
                return False
            
            self.validation_results = validation_result
            self._log("[Stage8] ✓ All validation checks passed")
            
            return True
        
        except Exception as e:
            self._log(f"[Stage8] Exception: {e}")
            return False
    
    def _stage9_export(self) -> bool:
        """STAGE 9: Export to GLB"""
        self._log_stage("9: Export")
        
        try:
            # Prepare output path
            os.makedirs('output', exist_ok=True)
            
            # Extract filename from input
            input_basename = os.path.splitext(os.path.basename(self.image_path))[0]
            output_path = f"output/{input_basename}_cutaway.glb"
            
            # Prepare metadata
            metadata = {
                'source_image': self.image_path,
                'scale_factor': self.normalization_context['scale_factor'],
                'normalized_width_m': self.normalization_context['target_width_m'],
                'room_count': len(self.room_set.rooms) if self.room_set else 0,
                'wall_count': len(self.wall_graph.edges) if self.wall_graph else 0
            }
            
            success, result = stage9_export(
                self.model_with_openings,
                output_path,
                metadata=metadata
            )
            
            if not success:
                self._log("[Stage9] ✗ Export failed")
                return False
            
            self.glb_path = result
            self._log(f"[Stage9] Exported to GLB format")
            self._log(f"[Stage9] Output: {self.glb_path}")
            self._log("[Stage9] ✓ Complete")
            
            return True
        
        except Exception as e:
            self._log(f"[Stage9] Exception: {e}")
            return False
    
    def _log_stage(self, stage_name: str):
        """Log stage separator"""
        self._log(f"\n[Pipeline] {'='*60}")
        self._log(f"[Pipeline] STAGE {stage_name}")
        self._log(f"[Pipeline] {'='*60}")
    
    def _log(self, message: str):
        """Log message"""
        if self.verbose:
            print(message)
        log.info(message)
        self.execution_log.append(message)
    
    def get_summary(self) -> Dict:
        """Get execution summary"""
        return {
            'success': len(self.errors) == 0,
            'stages_completed': sum([
                self.semantic_output is not None,
                self.refined_wall_mask is not None,
                self.wall_graph is not None,
                self.room_set is not None,
                self.normalized_wall_graph is not None,
                self.blender_model is not None,
                self.model_with_openings is not None,
                self.validation_results is not None,
                self.glb_path is not None
            ]),
            'total_stages': 9,
            'errors': self.errors,
            'output_path': self.glb_path,
            'room_count': len(self.room_set.rooms) if self.room_set else 0,
            'wall_count': len(self.wall_graph.edges) if self.wall_graph else 0
        }

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def process_blueprint(image_path: str, output_dir: str = 'output') -> Tuple[bool, str]:
    """
    Main entry point for blueprint-to-3D processing.
    
    Args:
        image_path: Path to blueprint image
        output_dir: Output directory for GLB file
    
    Returns:
        (success, message)
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    pipeline = BlueprintPipeline(image_path, verbose=True)
    success, message = pipeline.run_full_pipeline()
    
    if success:
        summary = pipeline.get_summary()
        print(f"\n✓ SUCCESS")
        print(f"  Rooms detected: {summary['room_count']}")
        print(f"  Output: {summary['output_path']}")
    else:
        print(f"\n✗ FAILED: {message}")
    
    return success, message


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='[%(name)s] %(message)s'
    )
    
    # Example usage
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        process_blueprint(image_path)
    else:
        print("Usage: python orchestrator.py <blueprint_image.png>")
